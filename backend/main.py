import os
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="AURA (Air Quality Urban Response Agent) API",
    description="Backend services for hyperlocal urban air quality forecasting, source attribution, and enforcement routing.",
    version="1.0.0"
)

# Enable CORS for local developer setups
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 1. DATABASE & DOMAIN MODELS (Mock Data for Bengaluru)
# ---------------------------------------------------------

# Detailed ward shapes (approximate boundaries for Leaflet mapping representation)
WARDS_DATA = [
    {
        "id": 1,
        "name": "Peenya Industrial Area",
        "zone_name": "Dasarahalli Zone",
        "centroid": [13.0285, 77.5193],
        "vulnerability_score": 0.65, # school & hospital proximity weight
        "population_density": 18500,
        "active_construction": 2,
        "industrial_stacks": 12,
        "traffic_congestion": 4.5, # scale 1-10
        "base_aqi": 180,
        "coordinates": [
            [13.045, 77.505], [13.045, 77.530], [13.015, 77.530], [13.015, 77.505], [13.045, 77.505]
        ]
    },
    {
        "id": 2,
        "name": "Whitefield IT Corridor",
        "zone_name": "Mahadevapura Zone",
        "centroid": [12.9698, 77.7499],
        "vulnerability_score": 0.82,
        "population_density": 22000,
        "active_construction": 14, # Heavy commercial development
        "industrial_stacks": 2,
        "traffic_congestion": 8.5, # High tailpipe emissions
        "base_aqi": 165,
        "coordinates": [
            [12.985, 77.735], [12.985, 77.765], [12.955, 77.765], [12.955, 77.735], [12.985, 77.735]
        ]
    },
    {
        "id": 3,
        "name": "Majestic Transit Hub",
        "zone_name": "West Zone",
        "centroid": [12.9779, 77.5724],
        "vulnerability_score": 0.90,
        "population_density": 34000,
        "active_construction": 5,
        "industrial_stacks": 0,
        "traffic_congestion": 9.5, # Peak bus and auto-rickshaw density
        "base_aqi": 195,
        "coordinates": [
            [12.990, 77.558], [12.990, 77.585], [12.965, 77.585], [12.965, 77.558], [12.990, 77.558]
        ]
    },
    {
        "id": 4,
        "name": "Electronic City Phase 1",
        "zone_name": "Bommanahalli Zone",
        "centroid": [12.8485, 77.6760],
        "vulnerability_score": 0.70,
        "population_density": 15000,
        "active_construction": 6,
        "industrial_stacks": 4,
        "traffic_congestion": 7.0,
        "base_aqi": 140,
        "coordinates": [
            [12.865, 77.660], [12.865, 77.690], [12.830, 77.690], [12.830, 77.660], [12.865, 77.660]
        ]
    },
    {
        "id": 5,
        "name": "Koramangala Commercial Hub",
        "zone_name": "South Zone",
        "centroid": [12.9352, 77.6245],
        "vulnerability_score": 0.88,
        "population_density": 28000,
        "active_construction": 4,
        "industrial_stacks": 0,
        "traffic_congestion": 7.8,
        "base_aqi": 130,
        "coordinates": [
            [12.950, 77.610], [12.950, 77.640], [12.920, 77.640], [12.920, 77.610], [12.950, 77.610]
        ]
    },
    {
        "id": 6,
        "name": "Hebbal Outer Ring Road",
        "zone_name": "Yelahanka Zone",
        "centroid": [13.0354, 77.5988],
        "vulnerability_score": 0.78,
        "population_density": 19000,
        "active_construction": 10, # Flyover and metro expansions
        "industrial_stacks": 1,
        "traffic_congestion": 8.0,
        "base_aqi": 150,
        "coordinates": [
            [13.050, 77.585], [13.050, 77.615], [13.020, 77.615], [13.020, 77.585], [13.050, 77.585]
        ]
    }
]

# Real-time meteorological states (affects dispersion calculations)
METEOROLOGY = {
    "temperature_c": 28.5,
    "wind_speed_ms": 3.2,
    "wind_direction_deg": 240, # Southwest wind (blowing to NE)
    "humidity_pct": 62.0,
    "planetary_boundary_layer_meters": 450.0
}

# ---------------------------------------------------------
# 2. PYDANTIC SCHEMAS FOR API TYPING
# ---------------------------------------------------------

class SimulationInput(BaseModel):
    traffic_reduction: float = Field(..., ge=0.0, le=100.0, description="Percentage reduction in traffic congestion")
    construction_ban: bool = Field(..., description="Whether to temporarily freeze active construction sites")
    industrial_halt: bool = Field(..., description="Whether to reduce industrial stack output by 50%")
    mist_spraying: bool = Field(..., description="Whether to deploy localized mist spraying cannons")

class CopilotQuery(BaseModel):
    query: str = Field(..., description="Natural language query from administrator")

# ---------------------------------------------------------
# 3. HELPER INTELLIGENCE ALGORITHMS
# ---------------------------------------------------------

def calculate_dynamic_aqi(ward: Dict[str, Any], met: Dict[str, Any], modifiers: Optional[Dict[str, Any]] = None) -> int:
    """
    Computes a realistic spatial-temporal AQI based on base ward profiles, active construction,
    industrial stacks, traffic congestion, and meteorological dispersion.
    """
    traffic = ward["traffic_congestion"]
    construction = ward["active_construction"]
    industry = ward["industrial_stacks"]
    
    # Apply policy modifiers (What-If Simulator adjustments)
    if modifiers:
        traffic = traffic * (1.0 - modifiers.get("traffic_reduction", 0.0) / 100.0)
        if modifiers.get("construction_ban", False):
            construction = 0
        if modifiers.get("industrial_halt", False):
            industry = industry * 0.3
            
    # Basic emissions calculation
    emissions_load = (traffic * 8.0) + (construction * 6.5) + (industry * 12.0)
    
    # Dispersion factors (Low wind or low boundary layer traps pollutants, increasing AQI)
    wind_factor = max(0.5, 6.0 / (met["wind_speed_ms"] + 1.0))
    pbl_factor = max(0.6, 600.0 / met["planetary_boundary_layer_meters"])
    
    # Spraying settles dust particles
    settling_effect = 0.85 if (modifiers and modifiers.get("mist_spraying", False)) else 1.0
    
    calculated_aqi = int((ward["base_aqi"] * 0.4) + (emissions_load * wind_factor * pbl_factor * settling_effect))
    
    # Keep within logical AQI boundaries
    return min(500, max(25, calculated_aqi))

def get_attribution_breakdown(ward: Dict[str, Any]) -> Dict[str, float]:
    """
    Computes source attribution based on local emissions footprint.
    """
    traffic_factor = ward["traffic_congestion"] * 8.0
    construction_factor = ward["active_construction"] * 6.5
    industry_factor = ward["industrial_stacks"] * 12.0
    waste_burning_factor = 10.0 + random.randint(-3, 4)
    background_factor = 25.0
    
    total = traffic_factor + construction_factor + industry_factor + waste_burning_factor + background_factor
    
    return {
        "Traffic": round((traffic_factor / total) * 100.0, 1),
        "Construction Dust": round((construction_factor / total) * 100.0, 1),
        "Industrial Stacks": round((industry_factor / total) * 100.0, 1),
        "Waste Burning": round((waste_burning_factor / total) * 100.0, 1),
        "Regional/Background": round((background_factor / total) * 100.0, 1)
    }

# ---------------------------------------------------------
# 4. REST ENDPOINTS
# ---------------------------------------------------------

@app.get("/api/wards")
def get_wards():
    """
    Returns list of wards, their centroids, current calculated AQI, and threat status.
    """
    response_wards = []
    for w in WARDS_DATA:
        current_aqi = calculate_dynamic_aqi(w, METEOROLOGY)
        
        # Categorize threat status
        if current_aqi <= 50:
            status = "GOOD"
        elif current_aqi <= 100:
            status = "MODERATE"
        elif current_aqi <= 150:
            status = "POOR"
        elif current_aqi <= 200:
            status = "VERY POOR"
        else:
            status = "SEVERE"
            
        attrib = get_attribution_breakdown(w)
        primary_pollutant = "PM2.5" if attrib["Traffic"] > attrib["Industrial Stacks"] else "PM10"
        
        response_wards.append({
            "id": w["id"],
            "name": w["name"],
            "zone_name": w["zone_name"],
            "centroid": w["centroid"],
            "current_aqi": current_aqi,
            "status": status,
            "primary_pollutant": primary_pollutant,
            "coordinates": w["coordinates"],
            "vulnerability_score": w["vulnerability_score"],
            "industrial_stacks": w["industrial_stacks"],
            "active_construction": w["active_construction"],
            "traffic_congestion": w["traffic_congestion"]
        })
    return response_wards

@app.get("/api/wards/{ward_id}/forecast")
def get_ward_forecast(ward_id: int):
    """
    Predicts hyperlocal AQI for 24h, 48h, and 72h horizons based on weather forecast trends.
    """
    ward = next((w for w in WARDS_DATA if w["id"] == ward_id), None)
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
        
    base_aqi = calculate_dynamic_aqi(ward, METEOROLOGY)
    forecast_points = []
    
    # Generate spatial temporal forecasting sequence curves (diurnal cycles + meteorology adjustments)
    # Hour 0 to 72
    hours = [2, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 56, 64, 72]
    
    for h in hours:
        # Simulate weather shifts: Temperature rises in mid-day, PBL height increases (lowering AQI)
        # Night temperature falls, PBL decreases (trapping particles, raising AQI)
        diurnal_cycle = 20.0 * math.sin((h - 8.0) * (2 * math.pi / 24.0))
        
        # Add slight upward regional drift over days (to simulate building winter smog)
        smog_trend = (h / 24.0) * 12.0
        
        # Modulate forecast based on simulated weather profiles
        hour_aqi = int(base_aqi - diurnal_cycle + smog_trend + random.randint(-5, 5))
        hour_aqi = min(500, max(20, hour_aqi))
        
        # Calculate forecasting confidence bands
        uncertainty = int(5 + (h / 24.0) * 15.0)
        
        forecast_points.append({
            "hour": h,
            "aqi": hour_aqi,
            "confidence_lower": max(0, hour_aqi - uncertainty),
            "confidence_upper": min(500, hour_aqi + uncertainty)
        })
        
    return {
        "ward_id": ward_id,
        "ward_name": ward["name"],
        "forecast": forecast_points
    }

@app.get("/api/wards/{ward_id}/attribution")
def get_ward_attribution(ward_id: int):
    """
    Returns percentage source attribution indicators.
    """
    ward = next((w for w in WARDS_DATA if w["id"] == ward_id), None)
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
        
    return {
        "ward_id": ward_id,
        "ward_name": ward["name"],
        "attribution": get_attribution_breakdown(ward),
        "confidence_score": round(0.85 + (random.random() * 0.1), 2),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/enforcement/hotspots")
def get_enforcement_hotspots():
    """
    Calculates operational priorites and lists recommended inspection dispatch routes.
    """
    hotspots = []
    
    for w in WARDS_DATA:
        current_aqi = calculate_dynamic_aqi(w, METEOROLOGY)
        attrib = get_attribution_breakdown(w)
        
        # Priority score incorporates base hazard value, public vulnerability (schools/hospitals),
        # and active source counts.
        priority_score = round(
            max(0.0, (current_aqi - 80) * w["vulnerability_score"] * (1.0 + (w["active_construction"] * 0.08))), 1
        )
        
        if priority_score > 20.0:
            # Determine dominant violating source
            primary_source = max(attrib, key=attrib.get)
            
            # Formulate action logs
            if primary_source == "Industrial Stacks":
                action = f"Deploy enforcement patrol to check scrubbers on 4 chemical stacks in {w['name']}. Mandate production cut if AQI > 200."
                evidence = f"Sensor records PM10 exceeding 200. Wind is blowing southwest at {METEOROLOGY['wind_speed_ms']}m/s, distributing industrial plumes toward local school clusters."
                officer = "Inspector R. K. Gowda"
            elif primary_source == "Construction Dust":
                action = f"Enforce water-sprinkling and wind fences at the {w['active_construction']} active building projects in {w['name']}. Issue temporary stop-work notice."
                evidence = f"Attribution models trace 35%+ of PM10 load to dust dispersion. Satellite overlays show thermal anomalies near development tracts."
                officer = "Officer Sunita Sen"
            else:
                action = f"Request Traffic Police to deploy mechanical sweepers on Outer Ring Road corridors and divert heavy trucks away from {w['name']} hubs."
                evidence = f"Local congestion index exceeds {w['traffic_congestion']}/10. High diurnal tailpipe PM2.5 signature detected."
                officer = "Admin Traffic Command"
                
            hotspots.append({
                "ward_id": w["id"],
                "ward_name": w["name"],
                "hotspot_score": priority_score,
                "current_aqi": current_aqi,
                "primary_source": primary_source,
                "recommended_action": action,
                "evidence": evidence,
                "assigned_officer": officer,
                "case_status": "PENDING"
            })
            
    # Sort by risk priority score descending
    hotspots.sort(key=lambda x: x["hotspot_score"], reverse=True)
    return hotspots

@app.get("/api/advisory")
def get_citizen_advisory(
    ward_id: int = Query(..., description="Target ward ID"),
    role: str = Query("GENERAL", description="CHILDREN, ELDERLY, ASTHMATIC, OUTDOOR_WORKER, GENERAL"),
    language: str = Query("EN", description="EN, HI, KN, TA")
):
    """
    Formulates context-specific citizen warnings and translates them into selected languages.
    """
    ward = next((w for w in WARDS_DATA if w["id"] == ward_id), None)
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
        
    aqi = calculate_dynamic_aqi(ward, METEOROLOGY)
    
    # Pre-baked translations representing our Gemini LLM translation agent pipeline
    advisories = {
        "EN": {
            "ASTHMATIC": f"Warning: AQI in {ward['name']} is {aqi} (POOR). Limit outdoor exercises. Ensure you carry your relief inhaler at all times.",
            "ELDERLY": f"Health Alert: Air quality is hazardous ({aqi}) in {ward['name']}. Seniors are advised to remain indoors and run air purifiers if available.",
            "CHILDREN": f"School Alert: AQI is {aqi}. Parents are advised to keep children indoors during recess. Avoid prolonged exposure.",
            "OUTDOOR_WORKER": f"Occupational Warning: AQI is {aqi}. Mandatory use of N95 masks is recommended. Limit heavy physical labor outdoors today.",
            "GENERAL": f"AQI Status: {ward['name']} is at {aqi}. Wear face masks if traveling outdoors. Close windows to prevent ambient dust intake."
        },
        "HI": {
            "ASTHMATIC": f"चेतावनी: {ward['name']} में एक्यूआई {aqi} (खराब) है। बाहरी गतिविधियों को सीमित करें। अपना इनहेलर हमेशा साथ रखें।",
            "ELDERLY": f"स्वास्थ्य चेतावनी: {ward['name']} में हवा हानिकारक ({aqi}) है। बुजुर्गों को घर के अंदर रहने की सलाह दी जाती है।",
            "CHILDREN": f"बाल स्वास्थ्य चेतावनी: एक्यूआई {aqi} है। माता-पिता बच्चों को बाहरी खेल से दूर रखें।",
            "OUTDOOR_WORKER": f"श्रमिक सुरक्षा चेतावनी: एक्यूआई {aqi} है। बाहरी कामगार N95 मास्क का उपयोग करें। शारीरिक श्रम सीमित करें।",
            "GENERAL": f"वायु गुणवत्ता अपडेट: {ward['name']} में एक्यूआई {aqi} है। बाहर निकलते समय मास्क का प्रयोग करें।"
        },
        "KN": {
            "ASTHMATIC": f"ಎಚ್ಚರಿಕೆ: {ward['name']} ನಲ್ಲಿ ವಾಯು ಮಾಲಿನ್ಯ ಸೂಚ್ಯಂಕ {aqi} ಆಗಿದೆ. ದಯವಿಟ್ಟು ಹೊರಾಂಗಣ ಚಟುವಟಿಕೆ ನಿಲ್ಲಿಸಿ, ಇನ್ಹೇಲರ್ ಧರಿಸಿ.",
            "ELDERLY": f"ಹಿರಿಯ ನಾಗರಿಕರ ಗಮನಕ್ಕೆ: {ward['name']} ವಾಯು ಗುಣಮಟ್ಟ ಅತ್ಯಂತ ಕೆಟ್ಟದಾಗಿದೆ ({aqi}). ದಯವಿಟ್ಟು ಮನೆಯಲ್ಲೇ ಇರಲು ವಿನಂತಿ.",
            "CHILDREN": f"ಮಕ್ಕಳ ಸುರಕ್ಷತೆ ಎಚ್ಚರಿಕೆ: {ward['name']} ವಾಯು ಸೂಚ್ಯಂಕ {aqi} ತಲುಪಿದೆ. ಮಕ್ಕಳನ್ನು ಹೊರಗಡೆ ಆಟವಾಡಲು ಕಳುಹಿಸಬೇಡಿ.",
            "OUTDOOR_WORKER": f"ಕಾರ್ಮಿಕರ ಎಚ್ಚರಿಕೆ: ಗಾಳಿ ಗುಣಮಟ್ಟ {aqi} ಆಗಿದೆ. ದಯವಿಟ್ಟು ಕಡ್ಡಾಯವಾಗಿ N95 ಮಾಸ್ಕ್ ಧರಿಸಿ ಕೆಲಸ ಮಾಡಿ.",
            "GENERAL": f"ವಾಯು ಗುಣಮಟ್ಟ ಮಾಹಿತಿ: {ward['name']} ನಲ್ಲಿ ಮಾಲಿನ್ಯ ಮಟ್ಟ {aqi} ತಲುಪಿದೆ. ಹೊರಹೋಗುವಾಗ ಮಾಸ್ಕ್ ಧರಿಸಲು ವಿನಂತಿ."
        },
        "TA": {
            "ASTHMATIC": f"எச்சரிக்கை: {ward['name']} பகுதியில் காற்று குறியீடு {aqi} (மோசம்). வெளிப்புற உடற்பயிற்சிகளை தவிர்க்கவும். இன்ஹேலரை உடன் வைத்திருக்கவும்.",
            "ELDERLY": f"முதியோர் எச்சரிக்கை: {ward['name']} பகுதியில் காற்று மாசு {aqi} ஆக உள்ளது. தயவுசெய்து வீட்டிற்குள் பாதுகாப்பாக இருக்கவும்.",
            "CHILDREN": f"குழந்தைகள் பாதுகாப்பு: காற்று மாசு {aqi} ஆக உள்ளது. பெற்றோர்கள் குழந்தைகளை வெளியே விளையாட அனுமதிக்க வேண்டாம்.",
            "OUTDOOR_WORKER": f"தொழிலாளர்கள் எச்சரிக்கை: காற்று மாசு {aqi} ஆக உள்ளது. வெளியில் வேலை செய்யும் போது N95 முகக்கவசம் அணியவும்.",
            "GENERAL": f"காற்று தர அறிக்கை: {ward['name']} பகுதியில் காற்று தரம் {aqi} ஆக உள்ளது. வெளியே செல்லும் போது முகக்கவசம் அணியவும்."
        }
    }
    
    lang_set = advisories.get(language, advisories["EN"])
    advisory_text = lang_set.get(role, lang_set["GENERAL"])
    
    return {
        "role": role,
        "language": language,
        "advisory": advisory_text
    }

@app.post("/api/simulate")
def post_simulate(sim: SimulationInput):
    """
    Downwind Gaussian dispersion simulator. Recalculates all ward AQIs based on policy sliders.
    """
    modifiers = {
        "traffic_reduction": sim.traffic_reduction,
        "construction_ban": sim.construction_ban,
        "industrial_halt": sim.industrial_halt,
        "mist_spraying": sim.mist_spraying
    }
    
    ward_reductions = []
    total_before_aqi = 0
    total_after_aqi = 0
    
    for w in WARDS_DATA:
        before_aqi = calculate_dynamic_aqi(w, METEOROLOGY)
        after_aqi = calculate_dynamic_aqi(w, METEOROLOGY, modifiers)
        
        reduction = before_aqi - after_aqi
        reduction_pct = round((reduction / before_aqi) * 100.0, 1) if before_aqi > 0 else 0.0
        
        total_before_aqi += before_aqi
        total_after_aqi += after_aqi
        
        ward_reductions.append({
            "ward_id": w["id"],
            "ward_name": w["name"],
            "before_aqi": before_aqi,
            "after_aqi": after_aqi,
            "reduction_percentage": reduction_pct
        })
        
    avg_reduction = round(((total_before_aqi - total_after_aqi) / total_before_aqi) * 100.0, 1) if total_before_aqi > 0 else 0.0
    
    # Calculate carbon offset ($CO2 equivalent offset):
    # Traffic cuts and industrial halts directly lower carbon footprint
    traffic_offset = (sim.traffic_reduction / 100.0) * 12500.0 # kg CO2 per day
    industrial_offset = 6800.0 if sim.industrial_halt else 0.0
    construction_offset = 1200.0 if sim.construction_ban else 0.0
    total_offset = round(traffic_offset + industrial_offset + construction_offset, 1)
    
    summary = f"Simulating policy: Traffic cut by {sim.traffic_reduction}%"
    if sim.construction_ban:
        summary += ", construction frozen"
    if sim.industrial_halt:
        summary += ", factory outputs halved"
    if sim.mist_spraying:
        summary += ", mist sprayers active"
        
    return {
        "simulation_summary": summary,
        "average_aqi_reduction": avg_reduction,
        "carbon_offset_co2_kg": total_offset,
        "ward_reductions": ward_reductions
    }

@app.post("/api/copilot")
def post_copilot_query(payload: CopilotQuery):
    """
    AI Copilot natural language processor. Connects administrators to spatial database metrics.
    """
    query = payload.query.lower()
    
    # Predefined semantic responses for key smart city query intents
    if "peenya" in query or "industry" in query or "factory" in query:
        answer = (
            "Peenya Industrial Area currently registers an AQI of 210 (POOR). "
            "Our source attribution models trace 42.5% of this particulate loading to industrial stacks, "
            "compounded by the southwest wind dispersing emission plumes toward local residential boundaries. "
            "I recommend: 1) Initiating particulate scrubber inspections at metal casting foundries, and "
            "2) Activating high-pressure mist spraying along Peenya main road corridors."
        )
        focused_ward = 1
        actions = ["Check industrial scrubbers", "Deploy mist cannons to Peenya"]
    elif "whitefield" in query or "construction" in query or "dust" in query:
        answer = (
            "Whitefield is experiencing an AQI of 178 (POOR). "
            "The dominant pollutant contributor is Construction Dust (38%), driven by the 14 active "
            "commercial and metro rail expansion sites. High wind velocities are suspending fine silica particles. "
            "Recommended action: Enforce immediate wet-sprinkling and halt excavation at metro lines."
        )
        focused_ward = 2
        actions = ["Audit dust control compliance", "Distribute N95 masks to site laborers"]
    elif "forecast" in query or "tomorrow" in query or "highest" in query or "worst" in query:
        answer = (
            "Based on the hybrid XGBoost-LSTM forecast, Majestic Transit Hub and Peenya Industrial Area "
            "are predicted to exceed AQI 230 within the next 24 hours. The spike is driven by a meteorological "
            "temperature inversion predicted for tomorrow morning, trapping exhaust particles under a 300m boundary layer. "
            "I suggest scheduling water misting cannons between 6:00 AM and 10:00 AM."
        )
        focused_ward = 3
        actions = ["Pre-schedule morning mist cannons", "Restrict heavy commercial traffic"]
    elif "zone 4" in query or "traffic" in query or "congestion" in query:
        answer = (
            "Wards surrounding Transit Zones (Majestic, Hebbal ORR) show high traffic contribution (exceeding 45%). "
            "Congestion indexes are averaging 8.5/10. We estimate that implementing a temporary truck ban "
            "would reduce localized PM2.5 levels by 18-22%."
        )
        focused_ward = 3
        actions = ["Deploy mechanical road sweepers", "Enable temporary traffic diversions"]
    else:
        answer = (
            "AURA Copilot active. I can analyze ward-level AQI forecasts, calculate pollution source "
            "attribution, prioritize hotspots for enforcement patrols, or simulate the impact of policy "
            "interventions (like traffic cuts or construction bans). How can I assist you today?"
        )
        focused_ward = None
        actions = []
        
    return {
        "answer": answer,
        "context": {
            "focused_ward_id": focused_ward,
            "suggested_actions": actions
        }
    }

# ---------------------------------------------------------
# 5. STATIC FRONTEND HOSTING
# ---------------------------------------------------------

# Serve static dashboard assets from the frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    
    @app.get("/")
    def read_root():
         return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "message": "FastAPI is running. Note: Frontend assets folder not found at /frontend. Please verify workspace directory structure."
        }
