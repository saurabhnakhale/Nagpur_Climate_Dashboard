import streamlit as st
import pandas as pd

from climate_core import (
    load_active_location_feeds,
    compute_indian_cpcb_aqi,
    render_echarts_gauge,
)

zone, ward, loc, _, _, air_w, _, _ = load_active_location_feeds()
air_comp = air_w.get("list", [{}])[0].get("components", {}) if air_w else {}
cpcb = compute_indian_cpcb_aqi(air_comp)

pm25 = round(float(air_comp.get("pm2_5", 0) or 0), 1)
pm10 = round(float(air_comp.get("pm10", 0) or 0), 1)
co_mg = round(float(air_comp.get("co", 0) or 0) / 1000.0, 2)
no2 = round(float(air_comp.get("no2", 0) or 0), 1)
so2 = round(float(air_comp.get("so2", 0) or 0), 1)
o3 = round(float(air_comp.get("o3", 0) or 0), 1)

st.caption(f"CPCB National Air Quality Index (0–500 scale) for **{ward}** ({zone}) · Dominant pollutant: **{cpcb['primary_pollutant']}**")

aqi_val = cpcb["aqi"] if cpcb["aqi"] is not None else 0

if aqi_val > 200:
    st.error(f"Poor air quality ({aqi_val} — {cpcb['category']}). Sensitive groups should wear N95 masks outdoors.", title="Air Quality Alert", icon=":material/masks:")
elif aqi_val > 100:
    st.warning(f"Moderate air quality ({aqi_val} — {cpcb['category']}). Monitor PM2.5 and PM10 exposure.", title="Moderate Pollution", icon=":material/air:")
else:
    st.success(f"Satisfactory air quality ({aqi_val} — {cpcb['category']}). Within CPCB 24-hour standards.", title="Clean Air Status", icon=":material/check_circle:")

# Primary + Gaseous Pollutants Grid
with st.grid(4, min_column_width=190, gap="small"):
    st.metric(
        "CPCB AQI",
        f"{aqi_val if cpcb['aqi'] is not None else 'N/A'}",
        delta=cpcb["category"],
        delta_color=cpcb["delta_color"],
        icon=":material/air:",
        border=True,
        height="stretch",
    )
    st.metric(
        "PM2.5",
        f"{pm25} µg/m³",
        delta=f"{pm25 - 60:+.1f} vs 60 std",
        delta_color="red" if pm25 > 60 else ("yellow" if pm25 > 30 else "green"),
        icon=":material/grain:",
        border=True,
        height="stretch",
    )
    st.metric(
        "PM10",
        f"{pm10} µg/m³",
        delta=f"{pm10 - 100:+.1f} vs 100 std",
        delta_color="red" if pm10 > 100 else ("yellow" if pm10 > 50 else "green"),
        icon=":material/blur_on:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Classification",
        cpcb["category"],
        delta=f"Lead: {cpcb['primary_pollutant']}",
        delta_color=cpcb["delta_color"],
        icon=":material/verified:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Carbon monoxide (CO)",
        f"{co_mg:.2f} mg/m³",
        delta="Limit: 2.0 mg/m³",
        delta_color="red" if co_mg > 2.0 else "green",
        icon=":material/co2:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Nitrogen dioxide (NO2)",
        f"{no2} µg/m³",
        delta="Limit: 80 µg/m³",
        delta_color="red" if no2 > 80 else ("yellow" if no2 > 40 else "green"),
        icon=":material/cloud:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Sulphur dioxide (SO2)",
        f"{so2} µg/m³",
        delta="Limit: 80 µg/m³",
        delta_color="red" if so2 > 80 else ("yellow" if so2 > 40 else "green"),
        icon=":material/science:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Ozone (O3)",
        f"{o3} µg/m³",
        delta="Limit: 100 µg/m³",
        delta_color="red" if o3 > 100 else ("yellow" if o3 > 50 else "green"),
        icon=":material/wb_twilight:",
        border=True,
        height="stretch",
    )

col_bar, col_gauge = st.columns([1.45, 1], gap="small")

with col_bar:
    with st.container(border=True, height="stretch"):
        st.subheader("Pollutants vs CPCB 24-hour limits", anchor=False)
        pol_df = pd.DataFrame([
            {"Pollutant": "PM2.5", "Recorded": pm25, "Limit": 60},
            {"Pollutant": "PM10", "Recorded": pm10, "Limit": 100},
            {"Pollutant": "NO2", "Recorded": no2, "Limit": 80},
            {"Pollutant": "SO2", "Recorded": so2, "Limit": 80},
            {"Pollutant": "O3", "Recorded": o3, "Limit": 100},
        ])
        st.echarts_chart(
            {
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                "grid": {"left": 42, "right": 18, "top": 36, "bottom": 28},
                "dataset": {"source": pol_df},
                "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8"}},
                "yAxis": {"type": "value", "name": "µg/m³", "axisLabel": {"color": "#94a3b8"}},
                "series": [
                    {"type": "bar", "name": "Recorded (µg/m³)", "encode": {"x": "Pollutant", "y": "Recorded"}, "itemStyle": {"color": "#2dd4bf"}},
                    {"type": "line", "name": "CPCB Standard", "encode": {"x": "Pollutant", "y": "Limit"}, "lineStyle": {"type": "dashed"}, "itemStyle": {"color": "#ef4444"}},
                ],
            },
            height=290,
            alt="Recorded pollutant concentrations compared against CPCB 24-hour standards",
        )

with col_gauge:
    with st.container(border=True, height="stretch"):
        st.subheader("CPCB NAQI gauge", anchor=False)
        render_echarts_gauge(
            title="Indian NAQI",
            value=aqi_val,
            min_val=0,
            max_val=500,
            unit="AQI",
            segments=[(0.10, "#10b981"), (0.20, "#84cc16"), (0.40, "#f59e0b"), (0.60, "#f97316"), (0.80, "#ef4444"), (1.0, "#991b1b")],
            alt="CPCB National Air Quality Index gauge from 0 to 500",
            height=240,
        )
        if cpcb["sub_indices"]:
            sub_df = pd.DataFrame([{"Pollutant": k, "Sub-Index": round(v, 1)} for k, v in cpcb["sub_indices"].items()])
            st.dataframe(sub_df, hide_index=True, alt="CPCB pollutant sub-index breakdown")
