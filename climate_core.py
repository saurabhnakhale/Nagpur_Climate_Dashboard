import math
import os
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

IST = ZoneInfo("Asia/Kolkata")
BASE = "https://api.openweathermap.org/data/2.5"
OPENMETEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

# Nagpur 30-year IMD monthly climatological normals (°C) for climate deviation analysis
NAGPUR_CLIMATE_NORMALS = {
    1: {"mean": 20.8, "max": 28.6, "min": 12.9},
    2: {"mean": 23.6, "max": 31.6, "min": 15.5},
    3: {"mean": 28.2, "max": 36.4, "min": 19.9},
    4: {"mean": 33.1, "max": 40.9, "min": 25.2},
    5: {"mean": 35.8, "max": 42.8, "min": 28.7},
    6: {"mean": 32.1, "max": 37.9, "min": 26.3},
    7: {"mean": 27.9, "max": 31.8, "min": 24.0},
    8: {"mean": 27.3, "max": 30.8, "min": 23.7},
    9: {"mean": 27.8, "max": 32.2, "min": 23.4},
    10: {"mean": 26.5, "max": 32.6, "min": 20.4},
    11: {"mean": 23.1, "max": 30.5, "min": 15.7},
    12: {"mean": 20.4, "max": 28.4, "min": 12.4},
}

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
# API KEY, TIME RANGE & CACHED DATA FETCHERS
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


def get_time_range_config() -> dict:
    """Resolve the active sidebar time-range filter into dates and horizon mode."""
    tr = st.session_state.get("time_range", "7 Days")
    today = datetime.now(IST).date()

    if tr == "24 Hours":
        return {"label": "24 Hours", "mode": "hourly", "hours": 24, "start": today, "end": today + timedelta(days=1)}
    if tr == "7 Days":
        return {"label": "7 Days", "mode": "forecast_7d", "hours": 168, "start": today, "end": today + timedelta(days=6)}
    if tr == "30 Days":
        return {"label": "30 Days", "mode": "historical", "hours": 720, "start": today - timedelta(days=30), "end": today - timedelta(days=1)}
    if tr == "1 Year":
        return {"label": "1 Year", "mode": "historical", "hours": 8760, "start": today - timedelta(days=365), "end": today - timedelta(days=1)}

    custom = st.session_state.get("custom_dates", (today - timedelta(days=14), today - timedelta(days=1)))
    if isinstance(custom, (list, tuple)) and len(custom) == 2:
        s_dt, e_dt = custom[0], custom[1]
    else:
        s_dt, e_dt = today - timedelta(days=14), today - timedelta(days=1)
    if s_dt > e_dt:
        s_dt, e_dt = e_dt, s_dt
    return {"label": f"{s_dt:%d %b} – {e_dt:%d %b %y}", "mode": "historical", "hours": max(24, (e_dt - s_dt).days * 24), "start": s_dt, "end": e_dt}


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


@st.cache_data(ttl=600, show_spinner=False)
def fetch_openmeteo_forecast(lat: float, lon: float) -> dict | None:
    """Fetch 7-day daily + 168-hour forecast (UV, Dew Point, Wind Dir, Precip Prob)."""
    try:
        r = requests.get(
            OPENMETEO_FORECAST,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation_probability,precipitation,uv_index,wind_speed_10m,wind_direction_10m,surface_pressure",
                "daily": "temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_sum,precipitation_probability_max,sunrise,sunset",
                "timezone": "Asia/Kolkata",
                "forecast_days": 7,
            },
            timeout=12,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_openmeteo_history(lat: float, lon: float, start_dt: date, end_dt: date) -> pd.DataFrame:
    """Fetch historical daily climate data from Open-Meteo Archive for deviation analysis."""
    today = datetime.now(IST).date()
    safe_end = min(end_dt, today - timedelta(days=1))
    safe_start = min(start_dt, safe_end)
    try:
        r = requests.get(
            OPENMETEO_ARCHIVE,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": safe_start.isoformat(),
                "end_date": safe_end.isoformat(),
                "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum",
                "timezone": "Asia/Kolkata",
            },
            timeout=15,
        )
        r.raise_for_status()
        daily = r.json().get("daily", {})
        if not daily or not daily.get("time"):
            return pd.DataFrame()
        df = pd.DataFrame({
            "Date": pd.to_datetime(daily["time"]),
            "Max Temp (°C)": daily.get("temperature_2m_max", []),
            "Min Temp (°C)": daily.get("temperature_2m_min", []),
            "Mean Temp (°C)": daily.get("temperature_2m_mean", []),
            "Rainfall (mm)": daily.get("precipitation_sum", []),
        })
        df["DateLabel"] = df["Date"].dt.strftime("%d %b %y")
        df["Normal Mean (°C)"] = df["Date"].dt.month.map(lambda m: NAGPUR_CLIMATE_NORMALS[m]["mean"])
        df["Normal Max (°C)"] = df["Date"].dt.month.map(lambda m: NAGPUR_CLIMATE_NORMALS[m]["max"])
        df["Deviation (°C)"] = (df["Mean Temp (°C)"] - df["Normal Mean (°C)"]).round(2)
        return df.dropna(subset=["Mean Temp (°C)"])
    except Exception:
        return pd.DataFrame()


def get_active_location():
    zone = st.session_state.get("selected_zone", "All Nagpur (City Core)")
    wards = NAGPUR_ZONES_WARDS.get(zone, NAGPUR_ZONES_WARDS["All Nagpur (City Core)"])
    ward = st.session_state.get("selected_ward")
    if ward not in wards:
        ward = next(iter(wards.keys()))
    return zone, ward, wards[ward]


def load_active_location_feeds():
    zone, ward, loc = get_active_location()
    key = get_key()
    current_w, ts_w = fetch_weather_with_ts(loc["lat"], loc["lon"], key)
    forecast_w, ts_f = fetch_forecast_with_ts(loc["lat"], loc["lon"], key)
    air_w, ts_a = fetch_air_with_ts(loc["lat"], loc["lon"], key)
    om_w = fetch_openmeteo_forecast(loc["lat"], loc["lon"])
    fetched_at = min(ts_w, ts_f, ts_a)
    st.session_state["last_fetch_epoch"] = fetched_at
    st.session_state["feed_live"] = bool(current_w)
    return zone, ward, loc, current_w, forecast_w, air_w, om_w, fetched_at


def parse_hourly_df(om_w: dict | None, forecast_w: dict | None, temp_offset: float = 0.0, rain_offset: float = 0.0) -> pd.DataFrame:
    """Build unified hourly forecast DataFrame (168h from Open-Meteo, fallback to OpenWeather 3h)."""
    if om_w and "hourly" in om_w and om_w["hourly"].get("time"):
        h = om_w["hourly"]
        df = pd.DataFrame({
            "Timestamp": pd.to_datetime(h["time"]),
            "Temperature (°C)": [round((x or 0) + temp_offset, 2) for x in h.get("temperature_2m", [])],
            "Feels Like (°C)": [round((x or 0) + temp_offset, 2) for x in h.get("apparent_temperature", [])],
            "Dew Point (°C)": [round((x or 0) + temp_offset * 0.4, 2) for x in h.get("dew_point_2m", [])],
            "Humidity (%)": [int(x or 0) for x in h.get("relative_humidity_2m", [])],
            "Rainfall (mm)": [round(max(0.0, float(x or 0) + (rain_offset / 168.0 if (x or 0) > 0 else 0.0)), 2) for x in h.get("precipitation", [])],
            "Rain Prob (%)": [int(x or 0) for x in h.get("precipitation_probability", [])],
            "UV Index": [round(float(x or 0), 1) for x in h.get("uv_index", [])],
            "Wind Speed (km/h)": [round(float(x or 0), 1) for x in h.get("wind_speed_10m", [])],
            "Wind Dir (°)": [int(x or 0) for x in h.get("wind_direction_10m", [])],
            "Pressure (hPa)": [round(float(x or 1013), 1) for x in h.get("surface_pressure", [])],
        })
        df["TimeLabel"] = df["Timestamp"].dt.strftime("%d %b %H:%M")
        df["Date"] = df["Timestamp"].dt.strftime("%d %b")
        return df

    if not forecast_w or "list" not in forecast_w:
        return pd.DataFrame()
    rows = []
    for it in forecast_w["list"]:
        ts = pd.to_datetime(it["dt"], unit="s", utc=True).tz_convert(IST)
        m = it.get("main", {})
        t_val = round(float(m.get("temp", 0)) + temp_offset, 2)
        rh_val = int(m.get("humidity", 0))
        rows.append({
            "Timestamp": ts,
            "TimeLabel": ts.strftime("%d %b %H:%M"),
            "Date": ts.strftime("%d %b"),
            "Temperature (°C)": t_val,
            "Feels Like (°C)": round(float(m.get("feels_like", 0)) + temp_offset, 2),
            "Dew Point (°C)": compute_dew_point(t_val, rh_val),
            "Humidity (%)": rh_val,
            "Rainfall (mm)": round(float(it.get("rain", {}).get("3h", 0) or 0), 2),
            "Rain Prob (%)": int(round((it.get("pop", 0) or 0) * 100)),
            "UV Index": 0.0,
            "Wind Speed (km/h)": round(float(it.get("wind", {}).get("speed", 0) or 0) * 3.6, 1),
            "Wind Dir (°)": int(it.get("wind", {}).get("deg", 0) or 0),
            "Pressure (hPa)": int(m.get("pressure", 1013)),
        })
    return pd.DataFrame(rows)


def parse_daily_7d_df(om_w: dict | None, hourly_df: pd.DataFrame, temp_offset: float = 0.0, rain_offset: float = 0.0) -> pd.DataFrame:
    """Build 7-day daily forecast DataFrame with min/max temp, UV max, rain sum, prob, sunrise/sunset."""
    if om_w and "daily" in om_w and om_w["daily"].get("time"):
        d = om_w["daily"]
        df = pd.DataFrame({
            "DateRaw": pd.to_datetime(d["time"]),
            "Max Temp (°C)": [round((x or 0) + temp_offset, 1) for x in d.get("temperature_2m_max", [])],
            "Min Temp (°C)": [round((x or 0) + temp_offset, 1) for x in d.get("temperature_2m_min", [])],
            "UV Max": [round(float(x or 0), 1) for x in d.get("uv_index_max", [])],
            "Rainfall (mm)": [round(max(0.0, float(x or 0) + (rain_offset / 7.0 if (x or 0) > 0 else 0.0)), 1) for x in d.get("precipitation_sum", [])],
            "Rain Prob (%)": [int(x or 0) for x in d.get("precipitation_probability_max", [])],
            "Sunrise": [s.split("T")[1] if "T" in str(s) else str(s) for s in d.get("sunrise", [])],
            "Sunset": [s.split("T")[1] if "T" in str(s) else str(s) for s in d.get("sunset", [])],
        })
        df["Date"] = df["DateRaw"].dt.strftime("%a %d %b")
        df["Normal Max (°C)"] = df["DateRaw"].dt.month.map(lambda m: NAGPUR_CLIMATE_NORMALS[m]["max"])
        df["Normal Min (°C)"] = df["DateRaw"].dt.month.map(lambda m: NAGPUR_CLIMATE_NORMALS[m]["min"])
        return df

    if hourly_df.empty:
        return pd.DataFrame()
    agg = hourly_df.groupby("Date", sort=False, as_index=False).agg(
        **{
            "Max Temp (°C)": ("Temperature (°C)", "max"),
            "Min Temp (°C)": ("Temperature (°C)", "min"),
            "UV Max": ("UV Index", "max"),
            "Rainfall (mm)": ("Rainfall (mm)", "sum"),
            "Rain Prob (%)": ("Rain Prob (%)", "max"),
        }
    )
    return agg


# ══════════════════════════════════════════════════════════════════════════════
# METEOROLOGICAL HELPERS & RISK COLOR ENGINES
# ══════════════════════════════════════════════════════════════════════════════
def compute_dew_point(temp_c: float, rh: float) -> float:
    rh = max(1.0, min(100.0, float(rh)))
    a, b = 17.625, 243.04
    alpha = math.log(rh / 100.0) + (a * temp_c) / (b + temp_c)
    return round((b * alpha) / (a - alpha), 1)


def compute_wbgt(temp_c: float, rh: float, uv_index: float = 4.0) -> dict:
    """Compute Wet-Bulb Globe Temperature (WBGT) using Stull wet-bulb + solar globe estimate."""
    rh_c = max(5.0, min(100.0, float(rh)))
    t = float(temp_c)
    tw = (
        t * math.atan(0.151977 * math.sqrt(rh_c + 8.313659))
        + math.atan(t + rh_c)
        - math.atan(rh_c - 1.676331)
        + 0.00391838 * (rh_c ** 1.5) * math.atan(0.023101 * rh_c)
        - 4.686035
    )
    solar_boost = min(6.0, max(0.0, float(uv_index) * 0.65))
    tg = t + solar_boost
    wbgt = round(0.7 * tw + 0.2 * tg + 0.1 * t, 1)
    if wbgt >= 30.0:
        return {"wbgt": wbgt, "level": "Extreme (Work Halt)", "delta_color": "red"}
    if wbgt >= 28.0:
        return {"wbgt": wbgt, "level": "High Occupational Stress", "delta_color": "orange"}
    if wbgt >= 25.0:
        return {"wbgt": wbgt, "level": "Moderate Stress", "delta_color": "yellow"}
    return {"wbgt": wbgt, "level": "Safe Work Window", "delta_color": "green"}


def count_heatwave_metrics(max_temps: list[float], normal_max: float = 40.0) -> tuple[int, int]:
    """Return (heatwave_days, max_consecutive_extreme_heat_days) for a series of daily max temps."""
    hw_days = 0
    cur_streak = 0
    max_streak = 0
    for tmax in max_temps:
        if tmax >= 45.0 or (tmax >= 40.0 and (tmax - normal_max) >= 4.5):
            hw_days += 1
        if tmax >= 40.0:
            cur_streak += 1
            max_streak = max(max_streak, cur_streak)
        else:
            cur_streak = 0
    return hw_days, max_streak


NAGPUR_COOLING_CENTRES = [
    {"Centre": "Sitabuldi Variety Square Shelter", "Zone": "Zone 6 - Gandhi Bagh", "Capacity": 180, "Status": "Standby / Ready", "lat": 21.1445, "lon": 79.0830},
    {"Centre": "Cotton Market / Railway Hub", "Zone": "Zone 6 - Gandhi Bagh", "Capacity": 220, "Status": "Standby / Ready", "lat": 21.1495, "lon": 79.0915},
    {"Centre": "Dhantoli Medical Cooling Kiosk", "Zone": "Zone 4 - Dhantoli", "Capacity": 150, "Status": "Standby / Ready", "lat": 21.1320, "lon": 79.0850},
    {"Centre": "Lakadganj Pili Nadi Shade Hub", "Zone": "Zone 8 - Lakadganj", "Capacity": 140, "Status": "Standby / Ready", "lat": 21.1520, "lon": 79.1380},
    {"Centre": "MIDC Hingna Worker Rest Shelter", "Zone": "Zone 8 - Lakadganj", "Capacity": 250, "Status": "Active (Industrial)", "lat": 21.1160, "lon": 79.0020},
    {"Centre": "Dharampeth Civic Cooling Point", "Zone": "Zone 2 - Dharampeth", "Capacity": 120, "Status": "Standby / Ready", "lat": 21.1420, "lon": 79.0650},
    {"Centre": "Ambazari Lakefront Mist Zone", "Zone": "Zone 1 - Laxmi Nagar", "Capacity": 160, "Status": "Standby / Ready", "lat": 21.1290, "lon": 79.0440},
    {"Centre": "Ashi Nagar Transit Cooling Hub", "Zone": "Zone 9 - Ashi Nagar", "Capacity": 130, "Status": "Standby / Ready", "lat": 21.1850, "lon": 79.1200},
]

NAGPUR_HEAT_VULNERABILITY = [
    {"Zone": "Zone 6 - Gandhi Bagh", "Vulnerable Pop": 68400, "Outdoor Workers (%)": 34, "Priority": "Critical", "LST Offset": 5.8},
    {"Zone": "Zone 8 - Lakadganj", "Vulnerable Pop": 61200, "Outdoor Workers (%)": 38, "Priority": "Critical", "LST Offset": 5.4},
    {"Zone": "Zone 7 - Satranjipura", "Vulnerable Pop": 54900, "Outdoor Workers (%)": 31, "Priority": "High", "LST Offset": 5.1},
    {"Zone": "Zone 4 - Dhantoli", "Vulnerable Pop": 42300, "Outdoor Workers (%)": 22, "Priority": "High", "LST Offset": 3.6},
    {"Zone": "Zone 5 - Nehru Nagar", "Vulnerable Pop": 46800, "Outdoor Workers (%)": 26, "Priority": "Moderate", "LST Offset": 3.1},
    {"Zone": "Zone 9 - Ashi Nagar", "Vulnerable Pop": 49500, "Outdoor Workers (%)": 28, "Priority": "Moderate", "LST Offset": 2.4},
    {"Zone": "Zone 3 - Hanuman Nagar", "Vulnerable Pop": 38100, "Outdoor Workers (%)": 20, "Priority": "Moderate", "LST Offset": 2.2},
    {"Zone": "Zone 2 - Dharampeth", "Vulnerable Pop": 31200, "Outdoor Workers (%)": 16, "Priority": "Moderate", "LST Offset": 1.8},
    {"Zone": "Zone 1 - Laxmi Nagar", "Vulnerable Pop": 27400, "Outdoor Workers (%)": 14, "Priority": "Low", "LST Offset": -1.4},
    {"Zone": "Zone 10 - Mangalwari", "Vulnerable Pop": 29800, "Outdoor Workers (%)": 15, "Priority": "Low", "LST Offset": -1.2},
]


def deg_to_compass(deg: float | int) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((float(deg) + 11.25) / 22.5) % 16
    return dirs[idx]


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


def risk_color_rain(mm_val: float) -> str:
    if mm_val >= 30: return "red"
    if mm_val >= 15: return "orange"
    if mm_val >= 5:  return "yellow"
    return "green"


def risk_color_uv(uv: float) -> tuple[str, str]:
    if uv >= 11: return "Extreme", "red"
    if uv >= 8:  return "Very High", "red"
    if uv >= 6:  return "High", "orange"
    if uv >= 3:  return "Moderate", "yellow"
    return "Low", "green"


def risk_color_dewpoint(dp: float) -> tuple[str, str]:
    if dp >= 24: return "Oppressive", "red"
    if dp >= 20: return "Muggy", "orange"
    if dp >= 16: return "Noticeable", "yellow"
    if dp >= 10: return "Comfortable", "green"
    return "Dry", "blue"


# ══════════════════════════════════════════════════════════════════════════════
# RESPONSIVE ECHARTS GAUGE, WIND ROSE & LIVE STATUS BAR
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


def render_wind_rose(hourly_df: pd.DataFrame, height: int = 280):
    """Render an ECharts 16-point polar wind rose from hourly wind speed & direction."""
    compass_16 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    bins = {d: [0, 0, 0] for d in compass_16}  # <10, 10-20, >20 km/h

    if not hourly_df.empty and "Wind Dir (°)" in hourly_df.columns:
        for _, row in hourly_df.iterrows():
            c = deg_to_compass(row["Wind Dir (°)"])
            spd = float(row["Wind Speed (km/h)"])
            if spd < 10:
                bins[c][0] += 1
            elif spd < 20:
                bins[c][1] += 1
            else:
                bins[c][2] += 1

    s_low = [bins[d][0] for d in compass_16]
    s_mid = [bins[d][1] for d in compass_16]
    s_high = [bins[d][2] for d in compass_16]

    st.echarts_chart(
        {
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": 0, "textStyle": {"color": "#cbd5e1", "fontSize": 10}},
            "polar": {"radius": ["14%", "74%"]},
            "angleAxis": {
                "type": "category",
                "data": compass_16,
                "startAngle": 90,
                "axisLabel": {"color": "#94a3b8", "fontSize": 10},
            },
            "radiusAxis": {"axisLabel": {"show": False}},
            "series": [
                {"type": "bar", "data": s_low, "coordinateSystem": "polar", "name": "< 10 km/h", "stack": "w", "itemStyle": {"color": "#2dd4bf"}},
                {"type": "bar", "data": s_mid, "coordinateSystem": "polar", "name": "10–20 km/h", "stack": "w", "itemStyle": {"color": "#3b82f6"}},
                {"type": "bar", "data": s_high, "coordinateSystem": "polar", "name": "> 20 km/h", "stack": "w", "itemStyle": {"color": "#f59e0b"}},
            ],
        },
        height=height,
        alt="16-point compass wind rose showing frequency and wind speed bands",
    )


def render_live_status_strip():
    """Live status, data source, active time range, freshness, and refresh countdown."""
    interval_sec = st.session_state.get("auto_refresh_sec", 300)
    last_epoch = st.session_state.get("last_fetch_epoch", time.time())
    is_live = st.session_state.get("feed_live", True)
    zone, ward, loc = get_active_location()
    tr_cfg = get_time_range_config()

    elapsed = max(0, int(time.time() - last_epoch))
    fresh_str = f"{elapsed}s ago" if elapsed < 60 else f"{elapsed // 60}m {elapsed % 60}s ago"

    if interval_sec > 0 and elapsed >= interval_sec:
        st.cache_data.clear()
        st.rerun(scope="app")

    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
            if is_live:
                st.badge("Live", icon=":material/sensors:", color="green")
            else:
                st.badge("Offline", icon=":material/cloud_off:", color="red")

            st.caption(f":material/location_on: **{zone}** · {ward}")
            st.caption(f":material/date_range: Window: **{tr_cfg['label']}**")
            st.caption(":material/database: OpenWeather · Open-Meteo · IMD · CPCB")
            st.caption(f":material/schedule: Updated {fresh_str}")

            if interval_sec > 0:
                remaining = max(0, interval_sec - elapsed)
                st.caption(f":material/autorenew: Next refresh in **{remaining // 60:02d}:{remaining % 60:02d}**")
            else:
                st.caption(":material/pause_circle: Auto-refresh paused")
