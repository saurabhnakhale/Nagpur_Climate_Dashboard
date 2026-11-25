import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

IST = ZoneInfo("Asia/Kolkata")
BASE = "https://api.openweathermap.org/data/2.5"

# ══════════════════════════════════════════════════════════════════════════════
# ZONE-WISE & WARD-WISE LOCATION CATALOG (10 NMC ADMINISTRATIVE ZONES)
# ══════════════════════════════════════════════════════════════════════════════
NAGPUR_ZONES_WARDS = {
    "All Nagpur (City Core)": {
        "All Wards (Central Observatory)": {
            "lat": 21.1458, "lon": 79.0882, "elev_m": 310,
            "type": "Metropolitan Core", "temp_offset": 0.0, "rain_offset": 0.0,
            "drainage_risk": "Moderate",
        },
    },
    "Zone 1 - Laxmi Nagar": {
        "Laxmi Nagar": {"lat": 21.1180, "lon": 79.0620, "elev_m": 315, "type": "Green Canopy / Residential", "temp_offset": -1.2, "rain_offset": 0.0, "drainage_risk": "Low"},
        "Ambazari Lake": {"lat": 21.1290, "lon": 79.0440, "elev_m": 318, "type": "Lake Catchment / Forest", "temp_offset": -2.1, "rain_offset": 0.4, "drainage_risk": "Low"},
        "Pratap Nagar": {"lat": 21.1120, "lon": 79.0550, "elev_m": 314, "type": "Residential", "temp_offset": -0.8, "rain_offset": 0.0, "drainage_risk": "Low"},
        "Trimurti Nagar": {"lat": 21.1160, "lon": 79.0420, "elev_m": 316, "type": "Suburban Residential", "temp_offset": -0.9, "rain_offset": 0.2, "drainage_risk": "Low"},
    },
    "Zone 2 - Dharampeth": {
        "Dharampeth": {"lat": 21.1420, "lon": 79.0650, "elev_m": 312, "type": "Dense Commercial / Residential", "temp_offset": 0.9, "rain_offset": 0.5, "drainage_risk": "Moderate"},
        "Civil Lines": {"lat": 21.1530, "lon": 79.0720, "elev_m": 315, "type": "Tree-Lined Administrative", "temp_offset": -1.4, "rain_offset": 0.2, "drainage_risk": "Low"},
        "Ramdaspeth": {"lat": 21.1355, "lon": 79.0760, "elev_m": 309, "type": "Medical / Commercial", "temp_offset": 1.1, "rain_offset": 0.8, "drainage_risk": "Moderate"},
        "Seminary Hills": {"lat": 21.1640, "lon": 79.0610, "elev_m": 332, "type": "Urban Forest Hilltop", "temp_offset": -2.0, "rain_offset": 0.0, "drainage_risk": "Low"},
    },
    "Zone 3 - Hanuman Nagar": {
        "Hanuman Nagar": {"lat": 21.1210, "lon": 79.0980, "elev_m": 308, "type": "Institutional / Residential", "temp_offset": 0.5, "rain_offset": 0.3, "drainage_risk": "Moderate"},
        "Ajni": {"lat": 21.1260, "lon": 79.0890, "elev_m": 306, "type": "Rail Corridor / Residential", "temp_offset": 1.0, "rain_offset": 0.7, "drainage_risk": "Moderate"},
        "Manish Nagar": {"lat": 21.0950, "lon": 79.0720, "elev_m": 305, "type": "Developing Urban Sprawl", "temp_offset": 1.4, "rain_offset": 1.0, "drainage_risk": "Moderate"},
    },
    "Zone 4 - Dhantoli": {
        "Dhantoli": {"lat": 21.1320, "lon": 79.0850, "elev_m": 302, "type": "Medical Hub / Nag Nadi Basin", "temp_offset": 1.5, "rain_offset": 1.8, "drainage_risk": "High"},
        "Congress Nagar": {"lat": 21.1335, "lon": 79.0815, "elev_m": 303, "type": "Commercial / Transit", "temp_offset": 1.6, "rain_offset": 1.5, "drainage_risk": "High"},
        "Imambada": {"lat": 21.1300, "lon": 79.0960, "elev_m": 301, "type": "Low-Lying Residential", "temp_offset": 1.3, "rain_offset": 2.0, "drainage_risk": "High"},
    },
    "Zone 5 - Nehru Nagar": {
        "Nehru Nagar": {"lat": 21.1350, "lon": 79.1250, "elev_m": 305, "type": "Residential / Commercial", "temp_offset": 1.2, "rain_offset": 1.2, "drainage_risk": "Moderate"},
        "Nandanvan": {"lat": 21.1400, "lon": 79.1200, "elev_m": 304, "type": "Dense Residential", "temp_offset": 1.3, "rain_offset": 1.4, "drainage_risk": "Moderate"},
        "Sakkardara": {"lat": 21.1270, "lon": 79.1150, "elev_m": 303, "type": "Lake Basin / Residential", "temp_offset": 0.8, "rain_offset": 1.6, "drainage_risk": "High"},
    },
    "Zone 6 - Gandhi Bagh": {
        "Sitabuldi": {"lat": 21.1445, "lon": 79.0830, "elev_m": 303, "type": "High-Density Commercial Core", "temp_offset": 2.9, "rain_offset": 2.1, "drainage_risk": "High"},
        "Gandhi Bagh": {"lat": 21.1550, "lon": 79.1050, "elev_m": 300, "type": "Old City Wholesale Core", "temp_offset": 2.7, "rain_offset": 2.4, "drainage_risk": "High"},
        "Itwari": {"lat": 21.1580, "lon": 79.1100, "elev_m": 301, "type": "Dense Trade Market", "temp_offset": 2.8, "rain_offset": 2.2, "drainage_risk": "High"},
    },
    "Zone 7 - Satranjipura": {
        "Satranjipura": {"lat": 21.1680, "lon": 79.1150, "elev_m": 303, "type": "High-Density Trade / Industrial", "temp_offset": 2.5, "rain_offset": 2.0, "drainage_risk": "High"},
        "Mominpura": {"lat": 21.1610, "lon": 79.1020, "elev_m": 302, "type": "Dense Urban Core", "temp_offset": 2.4, "rain_offset": 1.8, "drainage_risk": "High"},
        "Pachpaoli": {"lat": 21.1670, "lon": 79.1080, "elev_m": 304, "type": "Mixed Residential / Transit", "temp_offset": 2.0, "rain_offset": 1.5, "drainage_risk": "Moderate"},
    },
    "Zone 8 - Lakadganj": {
        "Lakadganj": {"lat": 21.1520, "lon": 79.1380, "elev_m": 298, "type": "Pili Nadi Catchment / Industrial", "temp_offset": 2.2, "rain_offset": 3.0, "drainage_risk": "Critical"},
        "MIDC Hingna (Industrial)": {"lat": 21.1160, "lon": 79.0020, "elev_m": 307, "type": "Industrial Asphalt / Metal Roofs", "temp_offset": 3.0, "rain_offset": 1.0, "drainage_risk": "Moderate"},
        "Kalamna": {"lat": 21.1690, "lon": 79.1520, "elev_m": 297, "type": "Market Yard / Low-Lying", "temp_offset": 2.3, "rain_offset": 3.2, "drainage_risk": "Critical"},
    },
    "Zone 9 - Ashi Nagar": {
        "Ashi Nagar": {"lat": 21.1850, "lon": 79.1200, "elev_m": 306, "type": "North Urban Sprawl", "temp_offset": 0.6, "rain_offset": 1.0, "drainage_risk": "Moderate"},
        "Jaripatka": {"lat": 21.1820, "lon": 79.1020, "elev_m": 308, "type": "Dense Commercial / Residential", "temp_offset": 1.1, "rain_offset": 0.9, "drainage_risk": "Moderate"},
        "Kamptee Road": {"lat": 21.1920, "lon": 79.1320, "elev_m": 304, "type": "Transit Corridor", "temp_offset": 1.2, "rain_offset": 1.1, "drainage_risk": "Moderate"},
    },
    "Zone 10 - Mangalwari": {
        "Mangalwari": {"lat": 21.1750, "lon": 79.0780, "elev_m": 318, "type": "Urban Forest / Outer Residential", "temp_offset": -1.0, "rain_offset": 0.0, "drainage_risk": "Low"},
        "Sadar": {"lat": 21.1605, "lon": 79.0790, "elev_m": 313, "type": "Cantonment / Commercial", "temp_offset": 0.4, "rain_offset": 0.4, "drainage_risk": "Low"},
        "Gorewada": {"lat": 21.1940, "lon": 79.0510, "elev_m": 324, "type": "Reservoir & Bio-Park", "temp_offset": -2.3, "rain_offset": 0.0, "drainage_risk": "Low"},
    },
}

MAHARASHTRA_CITIES = {
    "Nagpur": {"lat": 21.1458, "lon": 79.0882, "region": "Vidarbha", "role": "Winter Capital / Industrial Core"},
    "Mumbai": {"lat": 18.9388, "lon": 72.8354, "region": "Konkan Coastal", "role": "Financial Capital / Coastal"},
    "Pune": {"lat": 18.5204, "lon": 73.8567, "region": "Western Maharashtra", "role": "IT & Industrial Hub"},
    "Nashik": {"lat": 19.9975, "lon": 73.7898, "region": "North Maharashtra", "role": "Agri & Industrial"},
    "Chh. Sambhajinagar": {"lat": 19.8762, "lon": 75.3433, "region": "Marathwada", "role": "Arid / Drought-Prone"},
    "Amravati": {"lat": 20.9320, "lon": 77.7523, "region": "Vidarbha", "role": "Cotton Belt"},
    "Solapur": {"lat": 17.6599, "lon": 75.9064, "region": "Western Maharashtra", "role": "Semiarid South"},
    "Kolhapur": {"lat": 16.7050, "lon": 74.2433, "region": "Southern Maharashtra", "role": "Sugarcane Belt"},
    "Chandrapur": {"lat": 19.9615, "lon": 79.2961, "region": "Vidarbha", "role": "Thermal & Coal Mining Hub"},
}

INDIA_METROS = {
    "Nagpur": {"lat": 21.1458, "lon": 79.0882, "state": "Maharashtra", "zone": "Central"},
    "New Delhi": {"lat": 28.6139, "lon": 77.2090, "state": "Delhi NCR", "zone": "North"},
    "Mumbai": {"lat": 18.9388, "lon": 72.8354, "state": "Maharashtra", "zone": "West"},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka", "zone": "South"},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639, "state": "West Bengal", "zone": "East"},
    "Chennai": {"lat": 13.0827, "lon": 80.2707, "state": "Tamil Nadu", "zone": "South"},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867, "state": "Telangana", "zone": "South-Central"},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714, "state": "Gujarat", "zone": "West"},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan", "zone": "North-West"},
    "Lucknow": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh", "zone": "North Gangetic"},
}

# ══════════════════════════════════════════════════════════════════════════════
# API KEY & CACHED DATA FETCHERS (WITH FRESHNESS TIMESTAMPS)
# ══════════════════════════════════════════════════════════════════════════════
def get_key() -> str:
    if st.session_state.get("OPENWEATHER_API_KEY"):
        return str(st.session_state["OPENWEATHER_API_KEY"])
    try:
        if "OPENWEATHER_API_KEY" in st.secrets:
            return str(st.secrets["OPENWEATHER_API_KEY"])
    except Exception:
        pass
    env_val = os.getenv("OPENWEATHER_API_KEY")
    if env_val:
        return env_val.strip(' "\'')
    return "846b8fe88713e04d96f4fc0433482ae2"


@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather_with_ts(lat: float, lon: float, key: str):
    try:
        r = requests.get(
            f"{BASE}/weather",
            params={"lat": lat, "lon": lon, "appid": key, "units": "metric"},
            timeout=12,
        )
        r.raise_for_status()
        return r.json(), time.time()
    except Exception:
        return None, time.time()


@st.cache_data(ttl=600, show_spinner=False)
def fetch_forecast_with_ts(lat: float, lon: float, key: str):
    try:
        r = requests.get(
            f"{BASE}/forecast",
            params={"lat": lat, "lon": lon, "appid": key, "units": "metric"},
            timeout=12,
        )
        r.raise_for_status()
        return r.json(), time.time()
    except Exception:
        return None, time.time()


@st.cache_data(ttl=600, show_spinner=False)
def fetch_air_with_ts(lat: float, lon: float, key: str):
    try:
        r = requests.get(
            f"{BASE}/air_pollution",
            params={"lat": lat, "lon": lon, "appid": key},
            timeout=12,
        )
        r.raise_for_status()
        return r.json(), time.time()
    except Exception:
        return None, time.time()


def get_active_location():
    """Return currently selected zone, ward, and metadata from session_state."""
    zone = st.session_state.get("selected_zone", "All Nagpur (City Core)")
    wards = NAGPUR_ZONES_WARDS.get(zone, NAGPUR_ZONES_WARDS["All Nagpur (City Core)"])
    ward = st.session_state.get("selected_ward")
    if ward not in wards:
        ward = next(iter(wards.keys()))
    return zone, ward, wards[ward]


def load_active_location_feeds():
    """Fetch live weather, forecast, and air quality for the selected Zone & Ward."""
    zone, ward, loc = get_active_location()
    key = get_key()
    current_w, ts_w = fetch_weather_with_ts(loc["lat"], loc["lon"], key)
    forecast_w, ts_f = fetch_forecast_with_ts(loc["lat"], loc["lon"], key)
    air_w, ts_a = fetch_air_with_ts(loc["lat"], loc["lon"], key)
    fetched_at = min(ts_w, ts_f, ts_a)
    st.session_state["last_fetch_epoch"] = fetched_at
    st.session_state["feed_live"] = bool(current_w)
    return zone, ward, loc, current_w, forecast_w, air_w, fetched_at


def parse_forecast_df(forecast_w: dict | None, temp_offset: float = 0.0, rain_offset: float = 0.0) -> pd.DataFrame:
    if not forecast_w or "list" not in forecast_w:
        return pd.DataFrame()
    rows = []
    per_step_rain_adj = rain_offset / max(1, len(forecast_w["list"]))
    for it in forecast_w["list"]:
        ts = pd.to_datetime(it["dt"], unit="s", utc=True).tz_convert(IST)
        raw_rain = float(it.get("rain", {}).get("3h", 0) or 0)
        adj_rain = round(max(0.0, raw_rain + (per_step_rain_adj if raw_rain > 0 else 0.0)), 2)
        m = it.get("main", {})
        rows.append({
            "Timestamp": ts,
            "TimeLabel": ts.strftime("%d %b %H:%M"),
            "Date": ts.strftime("%d %b"),
            "Hour": ts.strftime("%H:%M"),
            "Temperature (°C)": round(float(m.get("temp", 0)) + temp_offset, 2),
            "Feels Like (°C)": round(float(m.get("feels_like", 0)) + temp_offset, 2),
            "Min Temp (°C)": round(float(m.get("temp_min", 0)) + temp_offset, 2),
            "Max Temp (°C)": round(float(m.get("temp_max", 0)) + temp_offset, 2),
            "Humidity (%)": int(m.get("humidity", 0)),
            "Rainfall (mm/3h)": adj_rain,
            "Rainfall (mm/h)": round(adj_rain / 3.0, 2),
            "Pressure (hPa)": int(m.get("pressure", 0)),
            "Wind Speed (km/h)": round(float(it.get("wind", {}).get("speed", 0) or 0) * 3.6, 1),
            "Condition": it.get("weather", [{}])[0].get("description", "").title(),
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICAL ENGINES & CONDITIONAL RISK COLOR HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _sub_index(conc: float, breakpoints: list) -> float:
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= conc <= c_high:
            return ((i_high - i_low) / (c_high - c_low)) * (conc - c_low) + i_low
    if conc > breakpoints[-1][1]:
        return 500.0
    return 0.0


def compute_indian_cpcb_aqi(components: dict) -> dict:
    if not components:
        return {"aqi": None, "category": "Unavailable", "delta_color": "gray", "hex": "#64748b", "primary_pollutant": "None", "sub_indices": {}}

    pm25_bp = [(0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200), (91, 120, 201, 300), (121, 250, 301, 400), (251, 500, 401, 500)]
    pm10_bp = [(0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200), (251, 350, 201, 300), (351, 430, 301, 400), (431, 600, 401, 500)]
    no2_bp  = [(0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200), (181, 280, 201, 300), (281, 400, 301, 400), (401, 600, 401, 500)]
    so2_bp  = [(0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200), (381, 800, 201, 300), (801, 1600, 301, 400), (1601, 2000, 401, 500)]
    co_bp   = [(0, 1.0, 0, 50), (1.1, 2.0, 51, 100), (2.1, 10.0, 101, 200), (10.1, 17.0, 201, 300), (17.1, 34.0, 301, 400), (34.1, 50.0, 401, 500)]
    o3_bp   = [(0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200), (169, 208, 201, 300), (209, 748, 301, 400), (749, 1000, 401, 500)]

    subs = {}
    if "pm2_5" in components: subs["PM2.5"] = _sub_index(components["pm2_5"], pm25_bp)
    if "pm10" in components:  subs["PM10"]  = _sub_index(components["pm10"], pm10_bp)
    if "no2" in components:   subs["NO2"]   = _sub_index(components["no2"], no2_bp)
    if "so2" in components:   subs["SO2"]   = _sub_index(components["so2"], so2_bp)
    if "co" in components:    subs["CO"]    = _sub_index(components["co"] / 1000.0, co_bp)
    if "o3" in components:    subs["O3"]    = _sub_index(components["o3"], o3_bp)

    if not subs:
        return {"aqi": None, "category": "Unavailable", "delta_color": "gray", "hex": "#64748b", "primary_pollutant": "None", "sub_indices": {}}

    lead = max(subs, key=subs.get)
    val = round(subs[lead])

    if val <= 50:    cat, dcol, hx = "Good", "green", "#10b981"
    elif val <= 100: cat, dcol, hx = "Satisfactory", "green", "#84cc16"
    elif val <= 200: cat, dcol, hx = "Moderate", "yellow", "#f59e0b"
    elif val <= 300: cat, dcol, hx = "Poor", "orange", "#f97316"
    elif val <= 400: cat, dcol, hx = "Very Poor", "red", "#ef4444"
    else:            cat, dcol, hx = "Severe", "red", "#b91c1c"

    return {
        "aqi": val,
        "category": cat,
        "delta_color": dcol,
        "hex": hx,
        "primary_pollutant": lead,
        "sub_indices": subs,
    }


def evaluate_imd_heat(temp_c: float, normal_temp_c: float = 40.0) -> dict:
    if temp_c is None:
        return {"label": "Unavailable", "severity": "info", "delta_color": "gray", "hex": "#64748b"}
    if temp_c >= 47.0 or (temp_c >= 40.0 and (temp_c - normal_temp_c) > 6.4):
        return {"label": "Severe Heat Wave (Red)", "severity": "error", "delta_color": "red", "hex": "#ef4444"}
    if temp_c >= 45.0 or (temp_c >= 40.0 and (temp_c - normal_temp_c) >= 4.5):
        return {"label": "Heat Wave Warning (Amber)", "severity": "warning", "delta_color": "orange", "hex": "#f97316"}
    if temp_c >= 40.0:
        return {"label": "Elevated Heat Stress (Yellow)", "severity": "warning", "delta_color": "yellow", "hex": "#f59e0b"}
    if temp_c >= 33.0:
        return {"label": "Warm Summer Range", "severity": "info", "delta_color": "blue", "hex": "#3b82f6"}
    return {"label": "Comfortable / Moderate", "severity": "success", "delta_color": "green", "hex": "#10b981"}


def risk_color_humidity(rh: float) -> str:
    if rh >= 80 or rh <= 20: return "orange"
    if rh >= 65 or rh <= 30: return "yellow"
    return "green"


def risk_color_wind(kmh: float) -> str:
    if kmh >= 40: return "red"
    if kmh >= 25: return "orange"
    if kmh >= 15: return "yellow"
    return "green"


def risk_color_pressure(hpa: float) -> str:
    if hpa < 1000: return "red"
    if hpa < 1006: return "orange"
    if hpa > 1025: return "yellow"
    return "green"


def risk_color_rain(mm_3h: float) -> str:
    if mm_3h >= 30: return "red"
    if mm_3h >= 15: return "orange"
    if mm_3h >= 5:  return "yellow"
    return "green"


# ══════════════════════════════════════════════════════════════════════════════
# RESPONSIVE ECHARTS GAUGE & LIVE STATUS BAR
# ══════════════════════════════════════════════════════════════════════════════
def render_echarts_gauge(
    title: str,
    value: float,
    min_val: float,
    max_val: float,
    unit: str,
    segments: list[tuple[float, str]],
    alt: str,
    height: int = 230,
):
    """Render a responsive ECharts gauge with meaningful color-coded threshold bands."""
    option = {
        "tooltip": {"formatter": f"{{b}}: {{c}} {unit}"},
        "series": [
            {
                "name": title,
                "type": "gauge",
                "min": min_val,
                "max": max_val,
                "splitNumber": 5,
                "radius": "92%",
                "center": ["50%", "56%"],
                "axisLine": {"lineStyle": {"width": 12, "color": segments}},
                "pointer": {"itemStyle": {"color": "auto"}, "width": 4, "length": "58%"},
                "axisTick": {"distance": -12, "length": 5, "lineStyle": {"color": "#94a3b8", "width": 1}},
                "splitLine": {"distance": -14, "length": 12, "lineStyle": {"color": "#cbd5e1", "width": 1.5}},
                "axisLabel": {"color": "#94a3b8", "distance": 16, "fontSize": 10},
                "title": {"offsetCenter": [0, "66%"], "fontSize": 12, "color": "#94a3b8"},
                "detail": {
                    "valueAnimation": True,
                    "formatter": f"{{value}} {unit}",
                    "color": "#f0f7ff",
                    "fontSize": 18,
                    "fontWeight": "bold",
                    "offsetCenter": [0, "34%"],
                },
                "data": [{"value": round(float(value), 1), "name": title}],
            }
        ],
    }
    st.echarts_chart(option, height=height, alt=alt)


def render_live_status_strip():
    """Live status, data source, freshness, and automatic refresh countdown."""
    interval_sec = st.session_state.get("auto_refresh_sec", 300)
    last_epoch = st.session_state.get("last_fetch_epoch", time.time())
    is_live = st.session_state.get("feed_live", True)
    zone, ward, loc = get_active_location()

    elapsed = max(0, int(time.time() - last_epoch))
    if elapsed < 60:
        fresh_str = f"{elapsed}s ago"
    else:
        fresh_str = f"{elapsed // 60}m {elapsed % 60}s ago"

    if interval_sec > 0 and elapsed >= interval_sec:
        st.cache_data.clear()
        st.rerun(scope="app")

    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
            if is_live:
                st.badge("Live", icon=":material/sensors:", color="green")
            else:
                st.badge("Offline", icon=":material/cloud_off:", color="red")

            st.caption(f":material/location_on: **{zone}** · {ward} ({loc['lat']:.4f}°N, {loc['lon']:.4f}°E)")
            st.caption(":material/database: Source: OpenWeatherMap · IMD · CPCB")
            st.caption(f":material/schedule: Updated {fresh_str}")

            if interval_sec > 0:
                remaining = max(0, interval_sec - elapsed)
                st.caption(f":material/autorenew: Next refresh in **{remaining // 60:02d}:{remaining % 60:02d}**")
            else:
                st.caption(":material/pause_circle: Auto-refresh paused")
