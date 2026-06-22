# API Design: REST API Specifications

The AURA backend exposes a set of REST endpoints for the client-side single-page application dashboard. The backend is built using FastAPI, and data structures are enforced using Pydantic models.

---

## 1. Ward Operations

### 1.1. Get Wards and GeoJSON Outline
* **Endpoint:** `GET /api/wards`
* **Description:** Returns all wards, their centroids, current AQI, and brief attribution summary.
* **Response Example (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Peenya Industrial Area",
    "zone_name": "Dasarahalli",
    "centroid": [13.0285, 77.5193],
    "current_aqi": 210,
    "status": "POOR",
    "primary_pollutant": "PM10",
    "coordinates": [
      [13.035, 77.510], [13.035, 77.525], [13.020, 77.525], [13.020, 77.510], [13.035, 77.510]
    ]
  }
]
```

### 1.2. Get Ward Forecasts
* **Endpoint:** `GET /api/wards/{ward_id}/forecast`
* **Description:** Retrieves 24h, 48h, and 72h forecasts with confidence bounds.
* **Response Example (200 OK):**
```json
{
  "ward_id": 1,
  "ward_name": "Peenya Industrial Area",
  "forecast": [
    {"hour": 12, "aqi": 215, "confidence_lower": 200, "confidence_upper": 230},
    {"hour": 24, "aqi": 235, "confidence_lower": 210, "confidence_upper": 260},
    {"hour": 48, "aqi": 180, "confidence_lower": 150, "confidence_upper": 210},
    {"hour": 72, "aqi": 140, "confidence_lower": 110, "confidence_upper": 170}
  ]
}
```

---

## 2. Intelligence & Agent Operations

### 2.1. Source Attribution
* **Endpoint:** `GET /api/wards/{ward_id}/attribution`
* **Description:** Retrieves percentage source attribution factors.
* **Response Example (200 OK):**
```json
{
  "ward_id": 1,
  "attribution": {
    "Traffic": 28.5,
    "Construction Dust": 12.0,
    "Industrial Stacks": 42.5,
    "Waste Burning": 10.0,
    "Regional/Background": 7.0
  },
  "confidence_score": 0.89,
  "updated_at": "2026-06-22T15:30:00Z"
}
```

### 2.2. Enforcement Hotspots and Recommendations
* **Endpoint:** `GET /api/enforcement/hotspots`
* **Description:** Returns categorized hotspots requiring inspector dispatches.
* **Response Example (200 OK):**
```json
[
  {
    "id": 101,
    "ward_id": 1,
    "ward_name": "Peenya Industrial Area",
    "hotspot_score": 92.5,
    "primary_source": "Industrial Stacks",
    "assigned_inspector": "Officer R. K. Sharma",
    "case_status": "PENDING",
    "recommended_action": "Mandate temporary production reduction in Peenya Metallurgy plants & enforce dry scrubber audits.",
    "evidence": "Fused data indicates wind direction is dispersing particulates from metal casting factories directly towards residential clusters. Sentinel-5P shows a high tropospheric NO2 column anomaly."
  }
]
```

### 2.3. Citizen Health Advisory
* **Endpoint:** `GET /api/advisory`
* **Query Parameters:**
  * `ward_id` (int) - Target ward
  * `role` (string) - `CHILDREN`, `ELDERLY`, `ASTHMATIC`, `OUTDOOR_WORKER`
  * `language` (string) - `EN` (English), `HI` (Hindi), `KN` (Kannada), `TA` (Tamil)
* **Response Example (200 OK):**
```json
{
  "role": "ASTHMATIC",
  "language": "KN",
  "advisory": "ಎಚ್ಚರಿಕೆ: ಪೀಣ್ಯ ಇಂಡಸ್ಟ್ರಿಯಲ್ ಏರಿಯಾದಲ್ಲಿ ವಾಯು ಮಾಲಿನ್ಯ ತೀವ್ರವಾಗಿದೆ. ದಯವಿಟ್ಟು ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆಗಳನ್ನು ತಪ್ಪಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಇನ್ಹೇಲರ್ ಅನ್ನು ಯಾವಾಗಲೂ ನಿಮ್ಮ ಬಳಿ ಇಟ್ಟುಕೊಳ್ಳಿ."
}
```

---

## 3. Simulator & Copilot Operations

### 3.1. What-If Policy Simulation
* **Endpoint:** `POST /api/simulate`
* **Description:** Accepts city-wide simulation weights and returns forecasted reductions.
* **Request Body:**
```json
{
  "traffic_reduction": 30.0,
  "construction_ban": true,
  "industrial_halt": false,
  "mist_spraying": true
}
```
* **Response Example (200 OK):**
```json
{
  "simulation_summary": "Implementing a 30% traffic cut, halting active building sites, and starting mechanical mist sprayers.",
  "average_aqi_reduction": 42.8,
  "carbon_offset_co2_kg": 18200.0,
  "ward_reductions": [
    {"ward_id": 1, "before_aqi": 210, "after_aqi": 155, "reduction_percentage": 26.2},
    {"ward_id": 2, "before_aqi": 180, "after_aqi": 130, "reduction_percentage": 27.7}
  ]
}
```

### 3.2. Copilot Query Chat
* **Endpoint:** `POST /api/copilot`
* **Request Body:**
```json
{
  "query": "Why is the AQI spike high in Zone 1?"
}
```
* **Response Example (200 OK):**
```json
{
  "answer": "Zone 1 (Peenya) is experiencing a spike due to a combination of: 1) Local industrial metal casting stacks operating at peak capacity, and 2) Low wind velocity (under 2 m/s) preventing dispersion, trapping PM10 particles. I recommend dispatching an inspection team to check scrubber compliance at casting units.",
  "context": {
    "focused_ward_id": 1,
    "suggested_actions": ["Verify industrial scrubber logs", "Coordinate road sweeping"]
  }
}
```
