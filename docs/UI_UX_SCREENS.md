# UI/UX Screens: Dashboard Interfaces

AURA is designed with a premium, command-center aesthetic. It features a dark-themed, glassmorphic layout using high-contrast neon status rings to grab the administrator's attention.

---

## 1. Unified Interface Layout Grid
The frontend operates as a Single-Page Application (SPA) with a persistent sidebar and top metrics bar:

```
┌────────────────────────────────────────────────────────────────────────┐
│  LOGO  │  City Avg AQI: 145 [MODERATE]  │  Hotspots: 3  │  Inspectors: 4│
├────────┴──────────────────────────────────────────────────────────────┤
│ 👤 Map  │                                                              │
│        │                 MAIN CONTENT AREA                            │
│ 🛠️ Enforce  (Tab-swapped dynamically based on navigation selection)   │
│        │                                                              │
│ 🎛️ Sim   │                                                              │
│        │                                                              │
│ 📢 Alert│                                                              │
│        │                                                              │
│ 💬 Chat│                                                              │
└────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. Navigational Views & Panels

### 2.1. Screen 1: Hyperlocal Map & Forecasting Panel
* **Purpose:** Core spatial monitoring interface.
* **Layout:** Split-pane grid (65% Map, 35% Detailed Analytics).
* **Left Sub-Panel (Interactive Map):**
  * Leaflet map loading OpenStreetMap vector tiles styled in a dark navy wash.
  * Municipal wards overlayed as semi-transparent polygons colored by AQI severity (Green = Good, Yellow = Moderate, Orange = Unhealthy for Sensitive Groups, Red = Poor, Purple = Severe).
  * Toggle controls for layer visibility: **Hotspots**, **Traffic congestion lines**, **Factory locations (stacks)**, and **Active construction projects**.
* **Right Sub-Panel (Ward Analytics Panel):**
  * Displays details for the clicked ward (e.g., "Ward 140 - Peenya").
  * **Forecast Chart (Chart.js):** Interactive line chart plotting predicted AQI levels for the next 24, 48, and 72 hours, enclosed in a shaded semi-transparent ribbon representing the 90% ML model confidence interval.
  * **Source Attribution Doughnut Chart:** Interactive breakdown of PM2.5 contributors.

### 2.2. Screen 2: Enforcement Intelligence Dashboard
* **Purpose:** Direct operational command.
* **Hotspot Prioritization Queue:** A data table sorting target wards by their **Hotspot Risk Score** (calculated by combining the AQI forecast, population density, and presence of hospitals/schools).
* **Evidence Panel:** Clicking a row opens the case profile containing:
  * Dynamic timeline showing *when* the spike occurred.
  * Correlated satellite detection notes (e.g., "Tropospheric NO2 plume detected at 13.02 N, 77.51 E").
  * Recommended Action card: *"Dispatch mist spraying cannon to Outer Ring Road construction sector. Notify Site Manager to cover dust heaps."*
  * Operational Buttons: `Dispatch Inspector`, `Generate Legal Order`, `Download PDF Dossier`.

### 2.3. Screen 3: "What-If" Policy Simulator
* **Purpose:** Predictive intervention playground.
* **Policy Input Controls:**
  * **Traffic Congestion Cap Slider:** Adjusts vehicular emissions (0% to -50%).
  * **Construction Halt Toggle:** Halts dust emissions in the dispersion model.
  * **Industrial Production Output Slider:** Controls factory stack rates (100% down to 20%).
  * **Fog Cannon Spraying Coverage Slider:** Simulates settling rate acceleration.
* **Simulation Result Panels:**
  * **Comparison Bar Chart:** Renders side-by-side bars for every ward comparing *Current Projected AQI* vs *Simulated AQI post-policy*.
  * **Carbon Offset Indicator:** Large numeric panel displaying computed $CO_2$ equivalent offset (in kilograms/day) as a secondary benefit of traffic and industrial cutbacks.

### 2.4. Screen 4: Citizen Advisory Translator
* **Purpose:** Communicating risks to the general public.
* **Interactive Selector Grid:**
  * Interactive buttons to choose the **Vulnerable Role** (Children, Elderly, Asthmatics, Outdoor Manual Workers).
  * Interactive buttons to choose the **Target Language** (English, Hindi, Kannada, Tamil).
* **Advisory Display Card:** Displays localized advice styled like an SMS / Public Information screen, ready to be sent to WhatsApp alerts or municipal display boards.

### 2.5. Screen 5: AI Copilot Console
* **Purpose:** Natural language interaction terminal.
* **Chat Log:** Renders responses from AURA's LLM engine.
* **Quick Query Triggers:** Buttons for one-click prompts:
  * *"Which wards are forecasted to breach AQI 200 tomorrow?"*
  * *"Why is the AQI increasing in Zone 4?"*
  * *"Draft an advisory warning for Peenya asthmatics."*
