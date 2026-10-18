# Data Centre Efficiency Dashboard

This is a standalone interactive dashboard for the project. It connects directly to PostgreSQL; pgAdmin is used to manage the database and load the data.

## Connect the correct database
Enter the PostgreSQL server and database that contain the `data_centre_hybrid` table.

You do **not** need to remember the database name now. When you launch the dashboard, enter the host, port, database name, username, and password in the sidebar. If the table is not found, the connection may be pointing to the wrong database/server or the SQL/data has not been loaded there.

## Prepare data in pgAdmin
1. Connect to the intended PostgreSQL server in pgAdmin.
2. Select the intended database and open Query Tool.
3. Run the corresponding SQL analysis file.
4. Import the dataset into the table expected by this dashboard. SQL scripts define the tables/queries but do not necessarily contain the original dataset rows.

Expected table: `data_centre_hybrid`

## Run on Windows
Open Command Prompt in this folder and run:

```bat
py -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The dashboard normally opens at `http://localhost:8501`.

## What it includes
- Country, owner, cooling system, water-stress tier, and year filters
- Facility count, PUE, WUE, electricity/water usage, capacity KPIs
- Country comparisons, cooling-system PUE/WUE scatter plot, annual PUE trend
- Filtered data table and CSV export

## Notes
- Charts and KPIs respond dynamically to filters.
- Query results are cached for up to 60 seconds; use **Connect / refresh** to clear the cache.
- Do not expose this local app publicly or commit database credentials.


## Quick start (Windows)

1. Open this folder in File Explorer.
2. Double-click `START_DASHBOARD.bat`.
3. The dashboard opens on `http://localhost:8503`. This uses a separate port so an older Streamlit session cannot show the old code.
4. In the sidebar, connect to database `Data_Center_Efficiency` using your PostgreSQL host, port, username, and password.
5. Keep the terminal window open while using the dashboard.

The app reads the existing table and does not alter database contents. If a required field cannot be mapped, expand **Columns found in your database** to see the exact names the app received.
