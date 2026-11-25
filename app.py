import time
import streamlit as st

from climate_core import (
    NAGPUR_ZONES_WARDS,
    render_live_status_strip,
)

st.set_page_config(
    page_title="Nagpur Climate Intelligence",
    page_icon=":material/partly_cloudy_day:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialize session state ──────────────────────────────────────────────────
if "selected_zone" not in st.session_state:
    st.session_state["selected_zone"] = "All Nagpur (City Core)"
if "selected_ward" not in st.session_state:
    st.session_state["selected_ward"] = "All Wards (Central Observatory)"
if "auto_refresh_sec" not in st.session_state:
    st.session_state["auto_refresh_sec"] = 300
if "last_fetch_epoch" not in st.session_state:
    st.session_state["last_fetch_epoch"] = time.time()
if "feed_live" not in st.session_state:
    st.session_state["feed_live"] = True

# ── Professional navigation menu with Material icons ──────────────────────────
page = st.navigation(
    {
        "Nagpur Urban Modules": [
            st.Page(
                "app_pages/executive_overview.py",
                title="Executive Climate Overview",
                icon=":material/dashboard:",
                default=True,
                help="Command center summary across temperature, AQI, heat, flood, vector risk, and integrated scores.",
            ),
            st.Page(
                "app_pages/live_weather.py",
                title="Live Weather Monitoring",
                icon=":material/partly_cloudy_day:",
                help="Real-time temperature, humidity, wind, pressure, and threshold gauges.",
            ),
            st.Page(
                "app_pages/heat_impact.py",
                title="Heat Impact Analysis",
                icon=":material/thermostat:",
                help="Diurnal max/min trends, heat index, and IMD Vidarbha heatwave alerts.",
            ),
            st.Page(
                "app_pages/rainfall_flood.py",
                title="Rainfall & Flood Impact",
                icon=":material/water_drop:",
                help="Hourly/daily precipitation, accumulation, and waterlogging indicators.",
            ),
            st.Page(
                "app_pages/vector_disease.py",
                title="Vector-Borne Disease Risk",
                icon=":material/coronavirus:",
                help="Environmental suitability index and Dengue/Malaria surveillance.",
            ),
            st.Page(
                "app_pages/air_quality.py",
                title="Air Quality Monitoring",
                icon=":material/air:",
                help="Official CPCB NAQI (0–500), PM2.5, PM10, and gaseous pollutants.",
            ),
            st.Page(
                "app_pages/climate_risk_map.py",
                title="Climate Risk Map",
                icon=":material/map:",
                help="Zone-wise and ward-wise thermal, rainfall, and drainage risk map.",
            ),
        ],
        "Regional & National": [
            st.Page(
                "app_pages/multi_scale.py",
                title="Maharashtra & All-India",
                icon=":material/public:",
                help="Synoptic climate benchmarking across Maharashtra and India metros.",
            ),
        ],
    },
    position="sidebar",
)

# ── Sidebar: global location selector + auto-refresh controls only ────────────
with st.sidebar:
    st.divider()
    st.markdown("**Location scope**")

    zone_list = list(NAGPUR_ZONES_WARDS.keys())
    selected_zone = st.selectbox(
        "NMC Zone",
        zone_list,
        index=zone_list.index(st.session_state["selected_zone"])
        if st.session_state["selected_zone"] in zone_list
        else 0,
        key="zone_selector_widget",
    )
    st.session_state["selected_zone"] = selected_zone

    ward_list = list(NAGPUR_ZONES_WARDS[selected_zone].keys())
    current_ward = st.session_state["selected_ward"]
    ward_idx = ward_list.index(current_ward) if current_ward in ward_list else 0
    selected_ward = st.selectbox(
        "Ward / Station",
        ward_list,
        index=ward_idx,
        key="ward_selector_widget",
    )
    st.session_state["selected_ward"] = selected_ward

    st.divider()
    st.markdown("**Auto-refresh**")
    refresh_map = {"Off": 0, "1m": 60, "5m": 300, "10m": 600}
    rev_map = {v: k for k, v in refresh_map.items()}
    choice = st.segmented_control(
        "Refresh interval",
        list(refresh_map.keys()),
        default=rev_map.get(st.session_state["auto_refresh_sec"], "5m"),
        label_visibility="collapsed",
    ) or "5m"
    st.session_state["auto_refresh_sec"] = refresh_map[choice]

# ── Compact header + live status / freshness / countdown fragment ─────────────
st.title(page.title, icon=page.icon)

run_every = 1 if st.session_state["auto_refresh_sec"] > 0 else None


@st.fragment(run_every=run_every)
def _live_status_fragment():
    render_live_status_strip()


_live_status_fragment()

# ── Run active module page ────────────────────────────────────────────────────
page.run()
