# Solution Overview: AURA (Air Quality Urban Response Agent)

**AURA** is an enterprise-grade, multi-agent AI system designed for municipal corporations (e.g., BBMP, BMC, MCD) and State Pollution Control Boards. It bridges the gap between passive sensor readings and active city enforcement, transforming air quality management from a retrospective monitoring exercise into a proactive, localized smart city operation.

---

## 1. Core Data Fusion Architecture
AURA achieves its predictive and attribution accuracy by fusing five distinct real-time and static datasets:
1. **IoT Sensor Feeds (CAAQMS & Low-Cost Sensors):** Continuous 15-minute readings of PM2.5, PM10, NO2, SO2, CO, and O3.
2. **Meteorological Data:** Real-time and 72-hour forecasts of wind velocity, wind direction (which controls dispersion), temperature, relative humidity, and planetary boundary layer (PBL) height.
3. **Mobility/Traffic Density:** Congestion indices and average vehicle speeds around hotspots to estimate tailpipe emissions.
4. **Satellite Imagery & Remote Sensing:** Active thermal anomalies (MODIS/VIIRS) to identify open waste burning and Sentinel-5P column density to identify industrial plumes.
5. **Smart City GIS & Land Use Maps:** Ward boundaries, locations of active construction permits, registered industrial stacks, and sensitive receptors (schools, hospitals).

---

## 2. Multi-Agent AI System
Instead of a single monolithic ML pipeline, AURA utilizes a decentralized team of specialized AI agents:

```
                  ┌───────────────────────┐
                  │ Data Collection Agent │
                  └───────────┬───────────┘
                              ▼
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Forecasting  │     │  Attribution  │     │   Copilot     │
│     Agent     │     │     Agent     │     │    Agent      │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────┴─────────────────────┴───────┐
│               Enforcement Recommendation Agent             │
└─────────────────────────────┬─────────────────────────────┘
                              ▼
               ┌──────────────────────────────┐
               │    Citizen Advisory Agent    │
               └──────────────────────────────┘
```

1. **Data Ingestion & Cleaning Agent:** Regularly scrapes, normalizes, and cleans noisy spatial-temporal feeds, filling missing values using kriging spatial interpolation.
2. **AQI Forecasting Agent:** Utilizes a hybrid XGBoost-LSTM model to forecast ward-level AQI for 24h, 48h, and 72h horizons, predicting confidence bands based on wind-dispersion projections.
3. **Pollution Source Attribution Agent:** A chemical mass balance and random forest model that attributes local PM2.5 levels to 5 major sources: Traffic, Construction Dust, Industrial Stacks, Waste Burning, and Regional/Background.
4. **Enforcement Intelligence Agent:** Analyzes the outputs of the forecasting and attribution agents, correlates them with industrial licenses/permits, and flags "interventions" (e.g., dispatch water mist cannons, route sanitary inspectors, or issue halt orders).
5. **Citizen Health Advisory Agent:** Formulates personalized warnings (for school children, the elderly, outdoor workers, and asthmatics) and translates them into regional Indian languages (Hindi, Kannada, Tamil, Marathi, Bengali) using LLM pipelines.
6. **Report Generation Agent:** Compiles PDF action reports complete with geospatial maps, historic trends, source attribution pie-charts, and evidence of construction violations for municipal action.

---

## 3. High-Impact Interactive Features
* **Interactive Hotspot Map:** Ward-level AQI choropleth map overlaid with live construction markers, industrial chimneys, and traffic bottlenecks.
* **Smart Policy "What-If" Simulator:** Allows administrators to slide variables (e.g., "Reduce traffic by 30%", "Pause construction in Zone B", "Increase mist spraying") to instantly run the dispersion model in the background and preview estimated AQI reduction.
* **Natural Language AI Copilot:** A chatbot interface where admins can ask: *"Who is responsible for the AQI spike in Peenya?"* or *"Generate an enforcement plan for ward 140 for tomorrow morning."*
