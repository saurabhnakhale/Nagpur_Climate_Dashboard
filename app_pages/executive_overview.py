import streamlit as st
import pandas as pd

from climate_core import (
    load_active_location_feeds,
    parse_forecast_df,
    compute_indian_cpcb_aqi,
    evaluate_imd_heat,
)

zone, ward, loc, current_w, forecast_w, air_w, _ = load_active_location_feeds()

if not current_w:
    st.error("Unable to retrieve live telemetry for the selected location.", icon=":material/cloud_off:")
    st.stop()

# ── Parse live atmospheric, AQI, rainfall, and vector metrics ─────────────────
main = current_w.get("main", {})
temp = round(float(main.get("temp", 0)) + loc["temp_offset"], 1)
feels = round(float(main.get("feels_like", 0)) + loc["temp_offset"], 1)
humidity = int(main.get("humidity", 0))

f_df = parse_forecast_df(forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
temp_trend = f_df.head(8)["Temperature (°C)"].tolist() if not f_df.empty else [temp]
rain_total = round(float(f_df["Rainfall (mm/3h)"].sum()), 1) if not f_df.empty else 0.0
rain_peak_3h = round(float(f_df["Rainfall (mm/3h)"].max()), 1) if not f_df.empty else 0.0
rain_trend = f_df.head(8)["Rainfall (mm/3h)"].tolist() if not f_df.empty else [rain_total]

air_comp = air_w.get("list", [{}])[0].get("components", {}) if air_w else {}
cpcb = compute_indian_cpcb_aqi(air_comp)
aqi_val = cpcb["aqi"] if cpcb["aqi"] is not None else 0

# ── Compute 5 Integrated Risk Scores (0–100) ──────────────────────────────────
# 1. Heat stress (0–100)
heat_meta = evaluate_imd_heat(temp)
heat_score = round(max(0, min(100, ((max(temp, feels) - 22.0) / 26.0) * 100)))
if heat_score >= 70:
    heat_level, heat_col = "Severe", "red"
elif heat_score >= 50:
    heat_level, heat_col = "High", "orange"
elif heat_score >= 35:
    heat_level, heat_col = "Moderate", "yellow"
else:
    heat_level, heat_col = "Low", "green"

# 2. Air pollution (CPCB NAQI 0–500 mapped to 0–100, with 300+ near 100)
air_score = round(max(0, min(100, (aqi_val / 300.0) * 100)))

# 3. Urban flooding (rainfall + ward drainage baseline)
drain_base = {"Low": 8, "Moderate": 18, "High": 32, "Critical": 45}.get(loc["drainage_risk"], 18)
rain_load = min(55, (rain_peak_3h * 1.5) + (rain_total * 0.35))
flood_score = round(max(0, min(100, drain_base + rain_load)))
if flood_score >= 70:
    flood_level, flood_col = "Critical", "red"
elif flood_score >= 45:
    flood_level, flood_col = "High", "orange"
elif flood_score >= 28:
    flood_level, flood_col = "Moderate", "yellow"
else:
    flood_level, flood_col = "Low", "green"

# 4. Vector-borne diseases (Environmental Suitability Index 0–100)
temp_suit = max(0.0, min(1.0, 1.0 - abs(temp - 27.0) / 15.0))
hum_suit = min(1.0, humidity / 70.0)
rain_suit = min(1.0, rain_total / 25.0)
vector_score = round(((temp_suit * 0.4) + (hum_suit * 0.4) + (rain_suit * 0.2)) * 100)
if vector_score >= 70:
    vector_level, vector_col = "High", "red"
elif vector_score >= 40:
    vector_level, vector_col = "Moderate", "orange"
else:
    vector_level, vector_col = "Low", "green"

# 5. Water scarcity (heat + dryness + low rain)
dryness = max(0.0, (70.0 - humidity) / 50.0)
rain_deficit = max(0.0, 1.0 - (rain_total / 20.0))
heat_evap = max(0.0, (temp - 25.0) / 20.0)
scarcity_score = round(max(5, min(100, ((dryness * 0.45) + (rain_deficit * 0.35) + (heat_evap * 0.20)) * 100)))

# Active Weather Alerts count
active_alerts = []
if heat_score >= 50:
    active_alerts.append("High Heat")
if aqi_val > 100:
    active_alerts.append("Elevated AQI")
if flood_score >= 45:
    active_alerts.append("Flood / Drainage")
if vector_score >= 40:
    active_alerts.append("Vector Risk")
alert_count = len(active_alerts)
alert_col = "red" if alert_count >= 3 else ("orange" if alert_count == 2 else ("yellow" if alert_count == 1 else "green"))
alert_desc = ", ".join(active_alerts) if active_alerts else "All clear"

# ── Command Center Subheader Row ──────────────────────────────────────────────
with st.container(horizontal=True, vertical_alignment="center"):
    st.markdown(f"**Nagpur Climate Command Center** · Integrated environmental and public health surveillance for **{ward}** ({zone})")
    st.badge("Live telemetry", icon=":material/sensors:", color="green")

# ── 3x2 Executive Summary KPI Grid ────────────────────────────────────────────
with st.grid(3, min_column_width=230, gap="small"):
    st.metric(
        "Temperature",
        f"{temp:.1f} °C",
        delta=f"{temp - feels:+.1f} °C vs apparent",
        delta_color=heat_meta["delta_color"],
        icon=":material/thermostat:",
        chart_data=temp_trend,
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Air Quality Index",
        f"{aqi_val if cpcb['aqi'] is not None else 'N/A'}",
        delta=f"{cpcb['category']} · {cpcb['primary_pollutant']}",
        delta_color=cpcb["delta_color"],
        icon=":material/air:",
        chart_data=[max(10, aqi_val - 14), max(10, aqi_val - 6), max(10, aqi_val - 18), max(10, aqi_val - 4), aqi_val],
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Heat Risk",
        heat_level,
        delta=f"Index {heat_score}/100 · IMD",
        delta_color=heat_col,
        icon=":material/local_fire_department:",
        chart_data=[heat_score, max(10, heat_score - 5), min(100, heat_score + 4), heat_score],
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "Flood Risk",
        flood_level,
        delta=f"Drainage: {loc['drainage_risk']}",
        delta_color=flood_col,
        icon=":material/flood:",
        chart_data=rain_trend,
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "Vector-Borne Disease Risk",
        vector_level,
        delta=f"Suitability {vector_score}/100",
        delta_color=vector_col,
        icon=":material/coronavirus:",
        chart_data=[max(5, vector_score - 8), max(5, vector_score - 3), vector_score],
        chart_type="area",
        border=True,
        height="stretch",
    )
    st.metric(
        "Active Weather Alerts",
        f"{alert_count:02d}",
        delta=alert_desc,
        delta_color=alert_col,
        icon=":material/notifications_active:",
        border=True,
        height="stretch",
    )

# ── Integrated Risk Assessment (Horizontal Progress Bars 0–100) ───────────────
def _bar_color(score: int) -> str:
    if score >= 70:
        return "#ef4444"
    if score >= 35:
        return "#f59e0b"
    return "#10b981"

risk_items = [
    ("Water scarcity", scarcity_score),
    ("Vector-borne diseases", vector_score),
    ("Urban flooding", flood_score),
    ("Air pollution", air_score),
    ("Heat stress", heat_score),
]

with st.container(border=True):
    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader("Integrated risk assessment", anchor=False)
        st.caption("Live composite scores (0–100)")

    categories = [name for name, _ in risk_items]
    bar_data = [
        {"value": score, "itemStyle": {"color": _bar_color(score), "borderRadius": 6}}
        for _, score in risk_items
    ]

    st.echarts_chart(
        {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "none"}, "formatter": "{b}: {c}/100"},
            "grid": {"left": 155, "right": 64, "top": 8, "bottom": 8},
            "xAxis": {"type": "value", "min": 0, "max": 100, "show": False},
            "yAxis": {
                "type": "category",
                "data": categories,
                "axisLine": {"show": False},
                "axisTick": {"show": False},
                "axisLabel": {"color": "#e2edf8", "fontSize": 13, "fontWeight": 500},
            },
            "series": [
                {
                    "type": "bar",
                    "data": bar_data,
                    "barWidth": 11,
                    "showBackground": True,
                    "backgroundStyle": {"color": "rgba(148, 163, 184, 0.14)", "borderRadius": 6},
                    "label": {
                        "show": True,
                        "position": "right",
                        "formatter": "{c}/100",
                        "color": "#cbd5e1",
                        "fontSize": 12,
                        "fontWeight": 600,
                    },
                }
            ],
        },
        height=215,
        alt="Integrated risk assessment bars for heat stress, air pollution, urban flooding, vector-borne diseases, and water scarcity",
    )

# ── Quick Module Navigation Links ─────────────────────────────────────────────
with st.container(horizontal=True, gap="small"):
    st.page_link("app_pages/live_weather.py", label="Live Weather", icon=":material/partly_cloudy_day:", width="stretch")
    st.page_link("app_pages/heat_impact.py", label="Heat Impact", icon=":material/thermostat:", width="stretch")
    st.page_link("app_pages/rainfall_flood.py", label="Rainfall & Flood", icon=":material/water_drop:", width="stretch")
    st.page_link("app_pages/vector_disease.py", label="Vector Risk", icon=":material/coronavirus:", width="stretch")
    st.page_link("app_pages/air_quality.py", label="Air Quality", icon=":material/air:", width="stretch")
    st.page_link("app_pages/climate_risk_map.py", label="Risk Map", icon=":material/map:", width="stretch")
