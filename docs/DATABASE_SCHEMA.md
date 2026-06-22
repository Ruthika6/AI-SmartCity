# Database Schema: PostgreSQL + PostGIS

To handle geospatial shapes (wards, coordinates) and temporal telemetry data (sensor readings, traffic logs), the recommended stack is **PostgreSQL** with the **PostGIS** extension enabled, and optionally **TimescaleDB** for efficient partition management of real-time telemetry.

---

## 1. Extension Setup
Ensure PostGIS is active in your database instance:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

---

## 2. Table Definitions

### 2.1. `wards`
Stores boundary shapes of municipal wards along with demographic risk factors.
```sql
CREATE TABLE Wards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    zone_name VARCHAR(50) NOT NULL, -- e.g., Mahadevapura, Peenya, Indiranagar
    geom GEOMETRY(Polygon, 4326) NOT NULL,
    population_density INTEGER, -- people/sq km
    vulnerability_score REAL DEFAULT 0.5, -- scale 0-1 based on count of schools and hospitals
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_wards_geom ON Wards USING GIST (geom);
```

### 2.2. `monitoring_stations`
Tracks CAAQMS location details.
```sql
CREATE TABLE Monitoring_Stations (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE, -- e.g., KA_001
    name VARCHAR(150) NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    operator VARCHAR(100), -- e.g., CPCB, KSPCB
    status VARCHAR(20) DEFAULT 'ACTIVE' -- ACTIVE, INACTIVE, MAINTENANCE
);
CREATE INDEX idx_stations_geom ON Monitoring_Stations USING GIST (geom);
```

### 2.3. `aqi_telemetry`
TimeSeries table tracking AQI metrics. In production, this should be partitioned by time (e.g. monthly).
```sql
CREATE TABLE AQI_Telemetry (
    id BIGSERIAL,
    station_id INTEGER REFERENCES Monitoring_Stations(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    pm25 REAL,
    pm10 REAL,
    no2 REAL,
    so2 REAL,
    co REAL,
    o3 REAL,
    aqi_value INTEGER,
    primary_pollutant VARCHAR(10),
    PRIMARY KEY (id, timestamp)
);
CREATE INDEX idx_telemetry_station_time ON AQI_Telemetry (station_id, timestamp DESC);
```

### 2.4. `traffic_logs`
Tracks mobility indexes at ward level.
```sql
CREATE TABLE Traffic_Logs (
    id BIGSERIAL,
    ward_id INTEGER REFERENCES Wards(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    congestion_index REAL, -- scale 0-10
    avg_speed_kmh REAL,
    PRIMARY KEY (id, timestamp)
);
CREATE INDEX idx_traffic_ward_time ON Traffic_Logs (ward_id, timestamp DESC);
```

### 2.5. `industrial_sources`
Tracks factories and production stack locations.
```sql
CREATE TABLE Industrial_Sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    industry_type VARCHAR(100), -- e.g., Chemical, Cement, Metallurgy
    stack_height_meters REAL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    emission_factor_pm25 REAL, -- kg/hr estimate
    operating_status VARCHAR(20) DEFAULT 'OPERATIONAL', -- OPERATIONAL, HALTED
    last_inspection_date DATE
);
CREATE INDEX idx_industry_geom ON Industrial_Sources USING GIST (geom);
```

### 2.6. `construction_sites`
Tracks municipal building/infra permits to compute dust anomalies.
```sql
CREATE TABLE Construction_Sites (
    id SERIAL PRIMARY KEY,
    permit_number VARCHAR(100) UNIQUE,
    developer_name VARCHAR(150),
    site_type VARCHAR(50), -- e.g., Residential, Metro Line, Roadwork
    geom GEOMETRY(Point, 4326) NOT NULL,
    permit_start DATE NOT NULL,
    permit_end DATE NOT NULL,
    mitigation_score REAL DEFAULT 0.5, -- scale 0-1 (1 = fully compliance wet sprays & wind fences)
    status VARCHAR(20) DEFAULT 'ACTIVE' -- ACTIVE, SUSPENDED, COMPLETED
);
CREATE INDEX idx_construction_geom ON Construction_Sites USING GIST (geom);
```

### 2.7. `enforcement_cases`
Actionable records created by the Enforcement Intelligence Agent.
```sql
CREATE TABLE Enforcement_Cases (
    id SERIAL PRIMARY KEY,
    ward_id INTEGER REFERENCES Wards(id),
    hotspot_score REAL NOT NULL, -- 0-100 prioritization scale
    primary_source VARCHAR(50) NOT NULL, -- e.g., Construction, Traffic, Industry
    source_attribution_json JSONB NOT NULL, -- detailed % breakdown
    evidence_summary TEXT, -- lists active factors e.g. "Peenya Stack Operating + High Wind direction"
    assigned_officer VARCHAR(100),
    case_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, DISPATCHED, COMPLIED, CITATION_ISSUED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_enforcement_status ON Enforcement_Cases (case_status, created_at DESC);
```

---

## 3. High-Value Spatial Queries
To demonstrate technical excellence to hackathon judges, here are spatial queries executed by the backend:

### 3.1. Identify Industries/Construction Sites near an AQI Spike
When a ward registers high AQI, AURA finds active pollution contributors within a 3-kilometer buffer of the ward centroid:
```sql
SELECT 
    'Industry' AS source_type, id, name AS label, ST_Distance(geom, (SELECT ST_Centroid(geom) FROM Wards WHERE id = 5)) AS distance_meters
FROM Industrial_Sources
WHERE ST_DWithin(geom, (SELECT ST_Centroid(geom) FROM Wards WHERE id = 5), 3000) AND operating_status = 'OPERATIONAL'
UNION ALL
SELECT 
    'Construction' AS source_type, id, developer_name AS label, ST_Distance(geom, (SELECT ST_Centroid(geom) FROM Wards WHERE id = 5)) AS distance_meters
FROM Construction_Sites
WHERE ST_DWithin(geom, (SELECT ST_Centroid(geom) FROM Wards WHERE id = 5), 3000) AND status = 'ACTIVE';
```
