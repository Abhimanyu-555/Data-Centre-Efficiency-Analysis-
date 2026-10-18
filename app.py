import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

st.set_page_config(page_title="Interactive SQL Dashboards", page_icon="📊", layout="wide")
st.title("📊 Interactive SQL Analytics")
st.caption("Power BI-style interactive dashboard connected to PostgreSQL • Schema-compatible build 2026.10.18")

def setting(k, default=""):
    try:
        return str(st.secrets.get("postgres", {}).get(k, os.getenv("PG_" + k.upper(), default)))
    except Exception:
        return os.getenv("PG_" + k.upper(), default)

with st.sidebar:
    st.header("PostgreSQL connection")
    st.caption("pgAdmin manages the database; this app connects to the PostgreSQL server.")
    host = st.text_input("Host", setting("host", "localhost"))
    port = st.text_input("Port", setting("port", "5432"))
    database = st.text_input("Database", setting("database", "Data_Center_Efficiency"))
    username = st.text_input("Username", setting("username", "postgres"))
    password = st.text_input("Password", setting("password"), type="password")
    if st.button("Connect / refresh", type="primary"):
        st.cache_data.clear()
    dashboard = "Data Centre Efficiency"

if not password:
    st.info("Enter your PostgreSQL password in the sidebar to load your live data.")
    st.stop()

@st.cache_resource
def engine_for(host, port, database, username, password):
    url = URL.create("postgresql+psycopg2", username=username, password=password,
                     host=host, port=int(port), database=database)
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})

try:
    engine = engine_for(host, port, database, username, password)
    with engine.connect() as con:
        con.execute(text("SELECT 1"))
except Exception as e:
    st.error("PostgreSQL connection failed. Check the server, port, database and credentials.")
    st.code(str(e))
    st.stop()

def read_table(table, host_key, port_key, database_key, username_key, password_key):
    # Deliberately read fresh data using this dashboard's current connection.
    # This avoids stale schema/data being reused across database connections.
    active_engine = engine_for(host_key, port_key, database_key, username_key, password_key)
    with active_engine.connect() as con:
        return pd.read_sql_query(text(f'SELECT * FROM "{table}"'), con)

def canonical_column(name):
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())

def map_columns(df, aliases):
    # Map source column names independent of capitalization, spaces, and underscores.
    original_by_key = {}
    for original in df.columns:
        original_by_key.setdefault(canonical_column(original), original)
    for target, candidates in aliases.items():
        if target in df.columns:
            continue
        for candidate in [target, *candidates]:
            source = original_by_key.get(canonical_column(candidate))
            if source is not None:
                df = df.rename(columns={source: target})
                break
    return df

def load_table(table):
    try:
        df = read_table(table, host, port, database, username, password)
        df.columns = [str(c).lower() for c in df.columns]
        if df.empty:
            st.warning(f"The table **{table}** exists but has no rows yet. Import your dataset through pgAdmin.")
            st.stop()
        return df
    except Exception as e:
        st.error(f"Could not read **{table}**. Run the corresponding SQL file in pgAdmin and import its dataset.")
        with st.expander("Technical details"):
            st.code(str(e))
        st.stop()

def filters(df, mapping):
    out = df.copy()
    cols = st.columns(len(mapping))
    for col, (label, field) in zip(cols, mapping.items()):
        vals = sorted(out[field].dropna().unique().tolist(), key=str)
        selected = col.multiselect(label, vals, key=f"{field}_filter")
        if selected:
            out = out[out[field].isin(selected)]
    return out

def metrics(items):
    cols = st.columns(len(items))
    for c, (label, value, help_text) in zip(cols, items):
        c.metric(label, value, help=help_text)

if dashboard == "Zepto Inventory":
    st.header("Zepto | Inventory & Pricing")
    df = load_table("zepto")
    needed = {"sku_id","category","name","mrp","discount","availablequantity",
              "discountedsellingprice","weightingrms","outofstock","quantity"}
    if needed - set(df.columns):
        st.error("Missing required columns: " + ", ".join(sorted(needed - set(df.columns))))
        with st.expander("Columns found in your database"):
            st.code("\\n".join(map(str, df.columns.tolist())))
        st.info("This diagnostic lists the exact column names read from public.data_centre_hybrid. No database changes are needed.")
        st.stop()
    for c in ["mrp","discount","availablequantity","discountedsellingprice","weightingrms","quantity"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["outofstock"] = df["outofstock"].astype(str).str.lower().map({"true":True,"false":False,"1":True,"0":False})
    df["estimated_stock_value"] = df["discountedsellingprice"].fillna(0) * df["availablequantity"].fillna(0)
    df["price_per_gram"] = df["discountedsellingprice"] / df["weightingrms"].replace(0, pd.NA)
    with st.expander("Filters", expanded=True):
        f1,f2,f3 = st.columns(3)
        cats = f1.multiselect("Category", sorted(df.category.dropna().unique().tolist()))
        status = f2.multiselect("Stock status", ["In stock","Out of stock"])
        dmin = float(max(0, df.discount.min(skipna=True) or 0))
        dmax = float(min(100, df.discount.max(skipna=True) if pd.notna(df.discount.max(skipna=True)) else 100))
        discount_range = f3.slider("Discount range (%)", 0.0, 100.0, (dmin,dmax))
    d = df.copy()
    if cats: d = d[d.category.isin(cats)]
    if status:
        wants = (False if "In stock" in status else None, True if "Out of stock" in status else None)
        wanted = [x for x in wants if x is not None]
        d = d[d.outofstock.isin(wanted)]
    d = d[d.discount.between(*discount_range) | d.discount.isna()]
    if d.empty: st.warning("No products match these filters."); st.stop()
    metrics([
        ("Products / SKUs", f"{d.sku_id.nunique():,}", "Unique SKUs after filtering"),
        ("Out of stock", f"{d.loc[d.outofstock == True,'sku_id'].nunique():,}", "Unique out-of-stock SKUs"),
        ("Average discount", f"{d.discount.mean():.1f}%" if d.discount.notna().any() else "—", "Mean listed discount"),
        ("Estimated stock value", f"₹{d.estimated_stock_value.sum():,.0f}", "Selling price × available quantity; estimated, not audited revenue")
    ])
    left,right = st.columns(2)
    with left:
        cat = d.groupby("category", dropna=False).agg(skus=("sku_id","nunique"), value=("estimated_stock_value","sum")).reset_index().sort_values("value",ascending=False)
        st.plotly_chart(px.bar(cat,x="category",y="value",color="skus",title="Estimated inventory value by category",labels={"value":"Estimated value (₹)","category":"Category","skus":"SKUs"}),use_container_width=True)
    with right:
        stock = d.assign(status=d.outofstock.map({True:"Out of stock",False:"In stock"})).groupby("status")["sku_id"].nunique().reset_index(name="SKUs")
        st.plotly_chart(px.pie(stock,names="status",values="SKUs",hole=.5,title="Stock availability mix"),use_container_width=True)
    left,right = st.columns(2)
    with left:
        avg = d.groupby("category",dropna=False).discount.mean().reset_index().sort_values("discount",ascending=False)
        st.plotly_chart(px.bar(avg,x="category",y="discount",title="Average discount by category",labels={"discount":"Average discount (%)"}),use_container_width=True)
    with right:
        top = d.dropna(subset=["price_per_gram"]).nsmallest(15,"price_per_gram").sort_values("price_per_gram")
        st.plotly_chart(px.bar(top,x="price_per_gram",y="name",orientation="h",title="Best value by price per gram",labels={"price_per_gram":"₹ per gram","name":"Product"},hover_data=["category","weightingrms"]),use_container_width=True)
    st.subheader("Filtered product data")
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.download_button("Download filtered CSV",d.to_csv(index=False).encode(), "zepto_filtered.csv","text/csv")

else:
    st.header("Data Centre | Energy, Water & Efficiency")
    df = load_table("data_centre_hybrid")
    aliases = {
        "facility_id": ["facilityid"],
        "facility_name": ["facilityname"],
        "owner_company": ["ownercompany"],
        "facility_type": ["facilitytype"],
        "estimated_capacity_mw": ["estimatedcapacitymw"],
        "cooling_system_type": ["coolingsystemtype"],
        "wue_l_per_kw_type": ["wue_l_per_kw", "wuelperkwtype", "wue"],
        "daily_electricity_usage_mwh": ["daily_electicity_usage_mwh", "dailyelectricityusagemwh", "dailyelecticityusagemwh"],
        "daily_water_usage_gallons": ["dailywaterusagegallons"],
        "surrounding_water_stress_tier": ["surroundingwaterstresstier"],
    }
    df = map_columns(df, aliases)
    needed = {"year","facility_id","facility_name","owner_company","city","country","facility_type",
              "estimated_capacity_mw","pue","cooling_system_type","wue_l_per_kw_type",
              "daily_electricity_usage_mwh","daily_water_usage_gallons","surrounding_water_stress_tier"}
    if needed - set(df.columns):
        st.error("Missing columns: " + ", ".join(sorted(needed - set(df.columns))))
        st.stop()
    for c in ["year","estimated_capacity_mw","pue","wue_l_per_kw_type","daily_electricity_usage_mwh","daily_water_usage_gallons"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    with st.expander("Filters", expanded=True):
        f1,f2,f3,f4 = st.columns(4)
        selected_country = f1.multiselect("Country", sorted(df.country.dropna().unique().tolist()))
        selected_owner = f2.multiselect("Owner company", sorted(df.owner_company.dropna().unique().tolist()))
        selected_cooling = f3.multiselect("Cooling system", sorted(df.cooling_system_type.dropna().unique().tolist()))
        selected_stress = f4.multiselect("Water-stress tier", sorted(df.surrounding_water_stress_tier.dropna().unique().tolist()))
        years = sorted(df.year.dropna().astype(int).unique().tolist())
        yrange = st.slider("Year range", min(years), max(years), (min(years),max(years))) if years else None
    d = df.copy()
    for col, vals in [("country",selected_country),("owner_company",selected_owner),("cooling_system_type",selected_cooling),("surrounding_water_stress_tier",selected_stress)]:
        if vals: d = d[d[col].isin(vals)]
    if yrange: d = d[d.year.between(*yrange)]
    if d.empty: st.warning("No facilities match these filters."); st.stop()
    metrics([
        ("Facilities", f"{d.facility_id.nunique():,}", "Unique facilities after filtering"),
        ("Average PUE", f"{d.pue.mean():.3f}" if d.pue.notna().any() else "—", "Lower is generally better"),
        ("Average WUE", f"{d.wue_l_per_kw_type.mean():.3f}" if d.wue_l_per_kw_type.notna().any() else "—", "Lower generally indicates less water use per stated unit"),
        ("Daily electricity", f"{d.daily_electricity_usage_mwh.sum():,.1f} MWh", "Sum of filtered facility values")
    ])
    metrics([
        ("Daily water", f"{d.daily_water_usage_gallons.sum():,.0f} gal", "Sum of filtered facility values"),
        ("Total capacity", f"{d.estimated_capacity_mw.sum():,.1f} MW", "Sum of estimated capacity"),
        ("High water-stress sites", f"{(d.surrounding_water_stress_tier.astype(str).str.lower()=='high').sum():,}", "Facilities marked High")
    ])
    left,right = st.columns(2)
    with left:
        energy = d.groupby("country",dropna=False).daily_electricity_usage_mwh.sum().reset_index().sort_values("daily_electricity_usage_mwh",ascending=False)
        st.plotly_chart(px.bar(energy,x="country",y="daily_electricity_usage_mwh",title="Daily electricity by country",labels={"country":"Country","daily_electricity_usage_mwh":"Daily electricity (MWh)"}),use_container_width=True)
    with right:
        cool = d.groupby("cooling_system_type",dropna=False).agg(avg_pue=("pue","mean"),avg_wue=("wue_l_per_kw_type","mean")).reset_index()
        st.plotly_chart(px.scatter(cool,x="avg_pue",y="avg_wue",color="cooling_system_type",hover_name="cooling_system_type",title="Cooling systems: PUE vs WUE",labels={"avg_pue":"Average PUE","avg_wue":"Average WUE"}),use_container_width=True)
    left,right = st.columns(2)
    with left:
        annual = d.groupby("year",dropna=False).pue.mean().reset_index().sort_values("year")
        st.plotly_chart(px.line(annual,x="year",y="pue",markers=True,title="Annual average PUE trend",labels={"year":"Year","pue":"Average PUE"}),use_container_width=True)
    with right:
        water = d.groupby("country",dropna=False).daily_water_usage_gallons.sum().reset_index().sort_values("daily_water_usage_gallons",ascending=False)
        st.plotly_chart(px.bar(water,x="country",y="daily_water_usage_gallons",title="Daily water by country",labels={"country":"Country","daily_water_usage_gallons":"Daily water (gallons)"}),use_container_width=True)
    st.subheader("Filtered facility data")
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.download_button("Download filtered CSV",d.to_csv(index=False).encode(), "data_centre_filtered.csv","text/csv")

st.caption("PostgreSQL query results refresh every 60 seconds. Use Connect / refresh to clear cached results.")
