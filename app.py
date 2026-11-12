import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Nagpur Climate Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

LAT, LON = 21.1458, 79.0882
BASE = "https://api.openweathermap.org/data/2.5"
IST = ZoneInfo("Asia/Kolkata")

# ---------- Premium visual system ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --bg:#07111f; --surface:#0d1b2d; --surface2:#12243a;
  --border:rgba(148,184,220,.15); --muted:#91a7c1;
  --text:#edf5ff; --cyan:#35c6df; --blue:#5797ff;
  --green:#48d6a2; --amber:#ffbf69; --red:#ff7185;
}
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp {
  background:
    radial-gradient(ellipse at 8% 0%, rgba(29,116,160,.19), transparent 32%),
    radial-gradient(ellipse at 92% 5%, rgba(77,83,180,.16), transparent 28%),
    linear-gradient(145deg,#07111f 0%,#091727 55%,#07111f 100%);
  color:var(--text);
}
[data-testid="stHeader"] { background:rgba(7,17,31,.78); }
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#0b1a2c 0%,#091524 100%);
  border-right:1px solid var(--border);
}
[data-testid="stSidebar"] * { color:#dceaff; }
.block-container { max-width:1660px; padding:1.35rem 2.1rem 2.5rem; }
h1,h2,h3,h4 { color:var(--text)!important; font-family:'Manrope',sans-serif!important; letter-spacing:-.35px; }
p, label, .stCaption { color:var(--muted); }
small { color:var(--muted); }
hr { border-color:var(--border); }
[data-testid="stMetric"] {
  background:linear-gradient(145deg,rgba(21,45,69,.95),rgba(12,28,46,.96));
  border:1px solid rgba(114,171,214,.20);
  border-radius:17px; padding:17px 19px;
  box-shadow:0 10px 28px rgba(0,0,0,.13);
  min-height:112px;
}
[data-testid="stMetricLabel"] { color:#a9bdd4!important; font-size:12px!important; font-weight:600!important; }
[data-testid="stMetricValue"] { color:#f2f8ff!important; font-weight:800!important; font-size:27px!important; }
[data-testid="stMetricDelta"] { font-size:11px!important; }
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"] {
  color:#a9bdd4; background:rgba(17,37,59,.75);
  border:1px solid var(--border); border-radius:10px 10px 0 0;
  padding:10px 16px; font-weight:600;
}
.stTabs [aria-selected="true"] { background:linear-gradient(90deg,#16445a,#19395a)!important; color:white!important; }
div.stButton>button, div.stDownloadButton>button {
  border:1px solid rgba(53,198,223,.42); border-radius:10px;
  background:linear-gradient(110deg,#12405a,#17436a);
  color:#effaff; font-weight:700; transition:all .2s ease;
}
div.stButton>button:hover, div.stDownloadButton>button:hover {
  border-color:#35c6df; box-shadow:0 0 18px rgba(53,198,223,.17); color:white;
}
[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:12px; overflow:hidden; }
[data-testid="stAlert"] { border-radius:13px; }
[data-baseweb="select"] > div { background:#11243a; border-color:#29445e; }
input, textarea { background:#102239!important; color:#edf5ff!important; }
.hero {
  position:relative; overflow:hidden; padding:25px 28px 22px; border-radius:21px;
  border:1px solid rgba(104,190,220,.26);
  background:
    radial-gradient(circle at 86% 25%,rgba(54,198,223,.20),transparent 22%),
    radial-gradient(circle at 72% 100%,rgba(77,130,255,.17),transparent 30%),
    linear-gradient(112deg,#102b43 0%,#122641 52%,#172b4b 100%);
  box-shadow:0 18px 45px rgba(0,0,0,.20); margin-bottom:17px;
}
.hero:after {
  content:""; position:absolute; width:230px;height:230px;right:8%;top:-125px;
  border:1px solid rgba(125,220,239,.16);border-radius:50%;
  box-shadow:0 0 0 25px rgba(125,220,239,.025),0 0 0 52px rgba(125,220,239,.02);
}
.hero-kicker { color:#71d8e8; font-size:10px; font-weight:800; letter-spacing:2.1px; }
.hero-title { color:#f4f9ff; font-family:'Manrope',sans-serif; font-size:29px; font-weight:800; letter-spacing:-.8px; margin:7px 0 4px; }
.hero-sub { color:#b5c9de; font-size:12px; }
.hero-meta { display:flex; gap:9px; flex-wrap:wrap; margin-top:15px; }
.pill { display:inline-block; padding:6px 10px; border-radius:30px; font-size:10px; color:#d9f7ff; background:rgba(49,178,204,.13); border:1px solid rgba(78,201,221,.24); }
.section-kicker { color:#68cfe0; font-size:10px; font-weight:800; letter-spacing:1.8px; margin:8px 0 3px; }
.section-title { color:#edf5ff; font-size:19px; font-weight:800; margin:0 0 12px; }
.panel {
  background:linear-gradient(145deg,rgba(18,38,61,.94),rgba(12,27,45,.96));
  border:1px solid var(--border); border-radius:16px; padding:16px 18px;
  box-shadow:0 9px 25px rgba(0,0,0,.12);
}
.panel-label { color:#8fa8c4; font-size:10px; font-weight:700; letter-spacing:1.3px; }
.panel-value { color:#f2f8ff; font-size:25px; font-weight:800; margin-top:7px; }
.panel-note { color:#8fa8c4; font-size:10px; margin-top:3px; }
.status-dot { display:inline-block; width:7px;height:7px;border-radius:50%;background:#48d6a2;margin-right:6px;box-shadow:0 0 9px #48d6a2; }
div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] { gap: .85rem; }
</style>
""", unsafe_allow_html=True)


def get_key():
    try:
        return st.secrets["OPENWEATHER_API_KEY"]
    except Exception:
        return os.getenv("OPENWEATHER_API_KEY")


def api_get(endpoint, key):
    response = requests.get(
        f"{BASE}/{endpoint}",
        params={"lat": LAT, "lon": LON, "appid": key, "units": "metric"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=600, show_spinner=False)
def load_current(key):
    return api_get("weather", key)


@st.cache_data(ttl=600, show_spinner=False)
def load_forecast(key):
    return api_get("forecast", key)


@st.cache_data(ttl=600, show_spinner=False)
def load_air(key):
    return api_get("air_pollution", key)


def forecast_frame(payload):
    rows = []
    for item in payload.get("list", []):
        rows.append({
            "Date & time": pd.to_datetime(item["dt"], unit="s", utc=True).tz_convert(IST),
            "Temperature (°C)": item.get("main", {}).get("temp"),
            "Feels like (°C)": item.get("main", {}).get("feels_like"),
            "Humidity (%)": item.get("main", {}).get("humidity"),
            "Rainfall (mm / 3h)": item.get("rain", {}).get("3h", 0) or 0,
            "Wind (m/s)": item.get("wind", {}).get("speed"),
        })
    return pd.DataFrame(rows)


def polish(fig, height=340):
    fig.update_layout(
        height=height, template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d5e4f5", family="DM Sans"),
        margin=dict(l=12,r=12,t=48,b=12),
        legend=dict(orientation="h",y=1.13,x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(150,180,210,.18)")
    fig.update_yaxes(gridcolor="rgba(150,180,210,.12)", zerolinecolor="rgba(150,180,210,.12)")
    return fig


# Sidebar navigation
with st.sidebar:
    st.markdown("## 🌍 NAGPUR")
    st.markdown("**CLIMATE INTELLIGENCE**")
    st.caption("SMART CITY MONITORING SUITE")
    st.divider()
    page = st.radio(
        "WORKSPACE",
        ["Command Center", "Weather Intelligence", "Heat Risk", "Rainfall Insights",
         "Air Quality", "Public Health", "Map & Data Export"],
        label_visibility="visible",
    )
    st.divider()
    st.markdown("**📍 MONITORING AREA**")
    st.write("Nagpur, Maharashtra")
    st.caption(f"{LAT:.4f}° N · {LON:.4f}° E")
    if st.button("↻ Refresh live feeds", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.caption("OpenWeather data · 10-minute cache")
    st.caption("Prototype build 03 · Climate analytics")

# Header
st.markdown(f"""
<div class="hero">
  <div class="hero-kicker">NAGPUR MUNICIPAL · ENVIRONMENT & PUBLIC HEALTH</div>
  <div class="hero-title">Climate Impact Intelligence</div>
  <div class="hero-sub">A unified command view of weather conditions, climate stress indicators and disease surveillance</div>
  <div class="hero-meta">
    <span class="pill">📍 Nagpur, India</span>
    <span class="pill">🌐 Live environmental feed</span>
    <span class="pill">📊 Analytics workspace</span>
  </div>
</div>
""", unsafe_allow_html=True)

key = get_key()
if not key:
    st.error("OpenWeather API key not found. Add OPENWEATHER_API_KEY to your .env file.")
    st.stop()

try:
    with st.spinner("Synchronizing Nagpur climate feeds..."):
        current = load_current(key)
        forecast = load_forecast(key)
except requests.HTTPError as exc:
    st.error(f"OpenWeather request failed: {exc}. Check API key activation and endpoint access.")
    st.stop()
except requests.RequestException as exc:
    st.error(f"Unable to connect to OpenWeather: {exc}")
    st.stop()

main = current.get("main", {})
temp = main.get("temp")
feels = main.get("feels_like")
humidity = main.get("humidity")
wind_ms = current.get("wind", {}).get("speed")
wind_kmh = wind_ms * 3.6 if wind_ms is not None else None
pressure = main.get("pressure")
desc = current.get("weather", [{}])[0].get("description", "Unavailable").title()
rain_now = current.get("rain", {}).get("1h", 0) or 0
observed = datetime.fromtimestamp(current.get("dt", datetime.now(IST).timestamp()), IST)
df = forecast_frame(forecast)

st.markdown(
    f'<span class="status-dot"></span><span style="color:#a9bfd5;font-size:11px">LIVE FEED CONNECTED</span>'
    f'<span style="color:#5d7896"> &nbsp;·&nbsp; </span><span style="color:#d8e8f8;font-size:11px">Conditions: {desc}</span>'
    f'<span style="color:#5d7896"> &nbsp;·&nbsp; </span><span style="color:#a9bfd5;font-size:11px">Updated {observed:%d %b %Y, %I:%M %p} IST</span>',
    unsafe_allow_html=True
)
st.write("")

metrics = st.columns(5)
metrics[0].metric("🌡️ Temperature", f"{temp:.1f} °C" if temp is not None else "—")
metrics[1].metric("♨️ Feels Like", f"{feels:.1f} °C" if feels is not None else "—")
metrics[2].metric("💧 Humidity", f"{humidity}%" if humidity is not None else "—")
metrics[3].metric("💨 Wind Speed", f"{wind_kmh:.1f} km/h" if wind_kmh is not None else "—")
metrics[4].metric("🌧️ Rain · 1 hour", f"{rain_now:.1f} mm")

st.write("")

# Command center
if page == "Command Center":
    st.markdown('<div class="section-kicker">CITY CLIMATE SNAPSHOT</div><div class="section-title">Executive command center</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1.7, 1])
    with col1:
        st.markdown('<div class="panel-label">SHORT-RANGE OUTLOOK</div>', unsafe_allow_html=True)
        if not df.empty:
            fig = px.line(df, x="Date & time", y=["Temperature (°C)", "Feels like (°C)"],
                          markers=True, color_discrete_sequence=["#35c6df", "#ffbf69"])
            st.plotly_chart(polish(fig, 365), use_container_width=True)
    with col2:
        st.markdown('<div class="panel-label">CURRENT CONDITIONS</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel"><div class="panel-label">WEATHER CONDITION</div><div class="panel-value">{desc}</div><div class="panel-note">Nagpur city reference point</div></div>', unsafe_allow_html=True)
        st.write("")
        st.metric("Atmospheric pressure", f"{pressure} hPa" if pressure is not None else "—")
        st.metric("Forecast rainfall total", f"{df['Rainfall (mm / 3h)'].sum():.1f} mm" if not df.empty else "—")
    st.markdown('<div class="section-kicker">MONITORING NOTES</div><div class="section-title">Operational context</div>', unsafe_allow_html=True)
    n1,n2,n3 = st.columns(3)
    n1.info("Heat indicators are screening signals. Refer to official IMD advisories for action.")
    n2.info("Rainfall values are forecast intervals, not measured ward rainfall.")
    n3.info("One city-center coordinate cannot represent every municipal zone.")

elif page == "Weather Intelligence":
    st.markdown('<div class="section-kicker">ATMOSPHERIC CONDITIONS</div><div class="section-title">Weather intelligence</div>', unsafe_allow_html=True)
    if not df.empty:
        choice = st.multiselect("Select indicators", ["Temperature (°C)", "Feels like (°C)", "Humidity (%)"], default=["Temperature (°C)", "Feels like (°C)"])
        if choice:
            fig = px.line(df, x="Date & time", y=choice, markers=True,
                          color_discrete_sequence=["#35c6df", "#ffbf69", "#48d6a2"])
            st.plotly_chart(polish(fig, 430), use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "Heat Risk":
    st.markdown('<div class="section-kicker">THERMAL STRESS MONITORING</div><div class="section-title">Heat impact & exposure indicators</div>', unsafe_allow_html=True)
    a,b,c = st.columns(3)
    a.metric("Air temperature", f"{temp:.1f} °C")
    b.metric("Feels-like temperature", f"{feels:.1f} °C")
    c.metric("Relative humidity", f"{humidity}%")
    if feels is not None and feels >= 40:
        st.error("Elevated apparent-temperature screening flag — review official IMD advisories.")
    elif feels is not None and feels >= 35:
        st.warning("Warm apparent-temperature screening flag — continue monitoring.")
    else:
        st.success("No elevated flag under the illustrative screening thresholds.")
    if not df.empty:
        fig = px.area(df, x="Date & time", y="Feels like (°C)", markers=True,
                      color_discrete_sequence=["#ff9f68"])
        st.plotly_chart(polish(fig, 390), use_container_width=True)
    st.caption("Illustrative screening only; not official IMD heatwave classification or medical heat-index assessment.")

elif page == "Rainfall Insights":
    st.markdown('<div class="section-kicker">PRECIPITATION MONITORING</div><div class="section-title">Rainfall outlook & accumulation</div>', unsafe_allow_html=True)
    if not df.empty:
        r1,r2 = st.columns(2)
        r1.metric("Forecast total", f"{df['Rainfall (mm / 3h)'].sum():.1f} mm")
        r2.metric("Periods with forecast rain", int((df["Rainfall (mm / 3h)"] > 0).sum()))
        fig = px.bar(df, x="Date & time", y="Rainfall (mm / 3h)",
                     color="Rainfall (mm / 3h)", color_continuous_scale=["#17385b","#35c6df","#b5f2ff"])
        st.plotly_chart(polish(fig, 420), use_container_width=True)
        st.dataframe(df[["Date & time","Rainfall (mm / 3h)"]], use_container_width=True, hide_index=True)
    st.caption("Forecast rainfall is not observed rainfall, flood measurement or ward-level rainfall.")

elif page == "Air Quality":
    st.markdown('<div class="section-kicker">ATMOSPHERIC POLLUTION</div><div class="section-title">Air quality intelligence</div>', unsafe_allow_html=True)
    try:
        air = load_air(key)
        item = air.get("list", [{}])[0]
        aqi = item.get("main", {}).get("aqi")
        components = item.get("components", {})
        labels = {1:"Good",2:"Fair",3:"Moderate",4:"Poor",5:"Very Poor"}
        x1,x2,x3 = st.columns(3)
        x1.metric("OpenWeather AQI", aqi if aqi is not None else "—")
        x2.metric("Provider category", labels.get(aqi, "Unavailable"))
        x3.metric("PM2.5", f"{components['pm2_5']:.2f} µg/m³" if "pm2_5" in components else "—")
        pdf = pd.DataFrame([{"Pollutant": k.upper(), "Concentration (µg/m³)": v} for k,v in components.items()])
        if not pdf.empty:
            fig = px.bar(pdf, x="Pollutant", y="Concentration (µg/m³)",
                         color="Concentration (µg/m³)", color_continuous_scale=["#1b9e77","#f6bd60","#ef6f6c"])
            st.plotly_chart(polish(fig, 390), use_container_width=True)
            st.dataframe(pdf, use_container_width=True, hide_index=True)
        st.caption("OpenWeather AQI is a 1–5 scale, not India's CPCB AQI scale (0–500).")
    except requests.HTTPError as exc:
        st.error(f"Air quality endpoint unavailable: {exc}")

elif page == "Public Health":
    st.markdown('<div class="section-kicker">EPIDEMIOLOGY & ENVIRONMENT</div><div class="section-title">Public health surveillance</div>', unsafe_allow_html=True)
    st.write("Upload authorized, aggregated and de-identified surveillance records.")
    st.caption("Required CSV columns: date, zone, disease, cases")
    sample = pd.DataFrame([
        {"date":"2026-07-01","zone":"Zone 1","disease":"Dengue","cases":3},
        {"date":"2026-07-01","zone":"Zone 2","disease":"Malaria","cases":2},
    ])
    st.download_button("⬇ Download sample CSV", sample.to_csv(index=False), "sample_surveillance.csv", "text/csv")
    uploaded = st.file_uploader("Upload surveillance CSV", type=["csv"])
    if uploaded:
        try:
            health = pd.read_csv(uploaded)
            health.columns = [str(c).strip().lower() for c in health.columns]
            missing = {"date","zone","disease","cases"} - set(health.columns)
            if missing:
                st.error("Missing columns: " + ", ".join(sorted(missing)))
            else:
                health["date"] = pd.to_datetime(health["date"], errors="coerce")
                health["cases"] = pd.to_numeric(health["cases"], errors="coerce")
                health = health.dropna(subset=["date","zone","disease","cases"])
                health["cases"] = health["cases"].clip(lower=0)
                f1,f2 = st.columns(2)
                disease = f1.selectbox("Disease", sorted(health["disease"].astype(str).unique()))
                zone = f2.selectbox("Zone", ["All zones"] + sorted(health["zone"].astype(str).unique()))
                view = health[health["disease"].astype(str) == disease]
                if zone != "All zones":
                    view = view[view["zone"].astype(str) == zone]
                st.metric("Cases in selected data", int(view["cases"].sum()))
                monthly = view.assign(month=view["date"].dt.to_period("M").astype(str)).groupby("month",as_index=False)["cases"].sum()
                st.plotly_chart(polish(px.line(monthly,x="month",y="cases",markers=True),350),use_container_width=True)
                st.dataframe(view,use_container_width=True,hide_index=True)
                st.download_button("⬇ Export filtered data",view.to_csv(index=False),"filtered_surveillance.csv","text/csv")
                st.info("This is trend analysis, not outbreak prediction or proof of climate causation.")
        except Exception as exc:
            st.error(f"Unable to process CSV: {exc}")
    else:
        st.info("Upload a CSV file to activate disease-wise and zone-wise analytics.")

elif page == "Map & Data Export":
    st.markdown('<div class="section-kicker">GEOSPATIAL VIEW</div><div class="section-title">Nagpur monitoring location</div>', unsafe_allow_html=True)
    st.map(pd.DataFrame({"lat":[LAT],"lon":[LON]}), latitude="lat", longitude="lon", zoom=10)
    st.caption("The pin is the city-center API reference coordinate, not zone-wise weather coverage.")
    if not df.empty:
        st.download_button("⬇ Export forecast data (CSV)", df.to_csv(index=False),
                           "nagpur_climate_forecast.csv", "text/csv")
        st.dataframe(df,use_container_width=True,hide_index=True)

st.divider()
st.caption("NAGPUR CLIMATE INTELLIGENCE · PREMIUM UI PROTOTYPE · DATA SOURCE: OPENWEATHER")
