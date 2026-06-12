create table Data_Centre_Hybrid (
Year INTEGER,
Facility_ID VARCHAR(150),
Facility_Name VARCHAR(150),
Owner_Company VARCHAR(150),
City VARCHAR(150),
Country VARCHAR(150),
Facility_Type VARCHAR(150),
Estimated_Capacity_MW NUMERIC(5,2),
PUE NUMERIC(4,3),
Cooling_System_Type VARCHAR(150),
WUE_L_per_kW_Type NUMERIC(4,3),
Daily_Electicity_Usage_MWh NUMERIC(7,2),
Daily_Water_Usage_Gallons NUMERIC(9,2),
Surrounding_Water_Stress_Tier VARCHAR(150)
);

--Most Efficient Data Centers by PUE
SELECT Facility_Name, Owner_Company, pue
FROM Data_Centre_Hybrid
ORDER BY pue ASC
LIMIT 10;

--Most Water Efficient Data Centers
SELECT Facility_Name, Owner_Company, WUE_L_per_kW_Type
FROM Data_Centre_Hybrid
ORDER BY WUE_L_per_kW_Type ASC
LIMIT 10;

--Top Companies By Average PUE
SELECT Owner_Company,
       ROUND(AVG(pue),2) AS Avg_PUE
FROM Data_Centre_Hybrid
GROUP BY Owner_Company
ORDER BY Avg_PUE;

--Electricity By Consumption
SELECT Country,
       SUM(Daily_Electicity_Usage_MWh) AS total_energy
FROM Data_Centre_Hybrid
GROUP BY Country
ORDER BY total_energy DESC;

--Water Consumption by Country
SELECT country,
       SUM(Daily_Water_Usage_Gallons) AS total_water
FROM Data_Centre_Hybrid
GROUP BY country
ORDER BY total_water DESC;

--Best Cooling Technology By PUE
SELECT Cooling_System_Type,
       ROUND(AVG(pue)::NUMERIC, 2) AS avg_pue
FROM Data_Centre_Hybrid
GROUP BY Cooling_System_Type
ORDER BY avg_pue;

--Best Cooling Technology By WUE
SELECT Cooling_System_Type,
       ROUND(AVG(WUE_L_per_kW_Type),2) AS avg_wue
FROM Data_Centre_Hybrid
GROUP BY Cooling_System_Type
ORDER BY avg_wue;

--Annual Trernd in PUE
SELECT year,
       ROUND(AVG(pue),2) AS avg_pue
FROM Data_Centre_Hybrid
GROUP BY year
ORDER BY year;

--Annual Trend in WUE 
SELECT year,
       ROUND(AVG(WUE_L_per_kW_Type),2) AS avg_wue
FROM Data_Centre_Hybrid
GROUP BY year
ORDER BY year;

--Facilities Operatin in HIgh Water-Stress Regions
SELECT facility_name,
       Owner_Company,
       country,
       Surrounding_Water_Stress_Tier
FROM Data_Centre_Hybrid
WHERE Surrounding_Water_Stress_Tier = 'High';

--Top 10 Highest Capacity Data Centers 
SELECT facility_name,
       Owner_Company,
       Estimated_Capacity_MW
FROM Data_Centre_Hybrid
ORDER BY Estimated_Capacity_MW DESC
LIMIT 10;

--Energy Consumption per MW Capacity
SELECT facility_name,
       ROUND(
       Daily_Electicity_Usage_MWh /
       NULLIF(Estimated_Capacity_MW,0),2)
       AS energy_per_mw
FROM Data_Centre_Hybrid
ORDER BY energy_per_mw;

--Rank Facilities By Overall Efficiency
SELECT facility_name,
       Owner_Company,
       pue,
       WUE_L_per_kW_Type,
       RANK() OVER (
           ORDER BY pue ASC, WUE_L_per_kW_Type ASC
       ) AS efficiency_rank
FROM Data_Centre_Hybrid;

--Identify Operational Outliers
WITH stats AS (
SELECT
AVG(Daily_Electicity_Usage_MWh) avg_energy,
STDDEV(Daily_Electicity_Usage_MWh) sd_energy
FROM Data_Centre_Hybrid
)

SELECT d.*
FROM Data_Centre_Hybrid d
CROSS JOIN stats s
WHERE d.Daily_Electicity_Usage_MWh >
      s.avg_energy + 2*s.sd_energy;

--Top Sustainability Leaders 
SELECT facility_name,
       Owner_Company,
       pue,
       WUE_L_per_kW_Type,
       Daily_Electicity_Usage_MWh,
       Daily_Water_Usage_Gallons
FROM Data_Centre_Hybrid
ORDER BY pue ASC,
         WUE_L_per_kW_Type ASC,
         Daily_Electicity_Usage_MWh ASC
LIMIT 10;