from datetime import datetime
import streamlit as st
import pandas as pd

from climate_core import (
    load_active_location_feeds,
    parse_forecast_df,
    render_echarts_gauge,
)

zone, ward, loc, current_w, forecast_w, _, _ = load_active_location_feeds()

if not current_w:
    st.error("Unable to retrieve environmental data for vector risk modeling.", icon=":material/cloud_off:")
    st.stop()

main = current_w.get("main", {})
temp = round(float(main.get("temp", 0)) + loc["temp_offset"], 1)
humidity = int(main.get("humidity", 0))
f_df = parse_forecast_df(forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
total_rain = round(float(f_df["Rainfall (mm/3h)"].sum()), 1) if not f_df.empty else 0.0

# Environmental Suitability Index (0–100) for Aedes & Anopheles
temp_suit = max(0.0, min(1.0, 1.0 - abs(temp - 27.0) / 15.0))
hum_suit = min(1.0, humidity / 70.0)
rain_suit = min(1.0, total_rain / 25.0)
esi_score = round(((temp_suit * 0.4) + (hum_suit * 0.4) + (rain_suit * 0.2)) * 100)

if esi_score >= 70:
    esi_label, esi_col, alert_kind = "High risk", "red", "error"
elif esi_score >= 40:
    esi_label, esi_col, alert_kind = "Moderate risk", "orange", "warning"
else:
    esi_label, esi_col, alert_kind = "Low risk", "green", "success"

st.caption(f"Aedes aegypti (Dengue) & Anopheles (Malaria) environmental suitability for **{ward}** ({zone})")

if alert_kind == "error":
    st.error(f"High vector suitability ({esi_score}/100): Temperature ({temp:.1f} °C) and humidity ({humidity}%) favor rapid mosquito breeding.", title="Vector Proliferation Alert", icon=":material/coronavirus:")
elif alert_kind == "warning":
    st.warning(f"Moderate vector suitability ({esi_score}/100): Preventive larvicide and source reduction advised in {ward}.", title="Moderate Vector Risk", icon=":material/biotech:")
else:
    st.success(f"Low vector suitability ({esi_score}/100): Current dryness or thermal conditions limit mosquito breeding.", title="Low Vector Risk", icon=":material/check_circle:")

with st.grid(4, min_column_width=210, gap="small"):
    st.metric(
        "Temperature window",
        f"{temp:.1f} °C",
        delta="Optimum 24–30 °C",
        delta_color="red" if 22 <= temp <= 32 else "green",
        icon=":material/thermostat:",
        chart_data=f_df.head(10)["Temperature (°C)"].tolist() if not f_df.empty else [temp],
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Humidity condition",
        f"{humidity}%",
        delta="Breeding > 60%",
        delta_color="red" if humidity >= 65 else ("yellow" if humidity >= 50 else "green"),
        icon=":material/humidity_percentage:",
        chart_data=f_df.head(10)["Humidity (%)"].tolist() if not f_df.empty else [humidity],
        chart_type="area",
        border=True,
        height="stretch",
    )
    st.metric(
        "Rainfall stagnation",
        f"{total_rain:.1f} mm",
        delta="5-day accumulation",
        delta_color="orange" if total_rain >= 15 else "green",
        icon=":material/water_drop:",
        chart_data=f_df.head(10)["Rainfall (mm/3h)"].tolist() if not f_df.empty else [total_rain],
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "Suitability index",
        f"{esi_score} / 100",
        delta=esi_label,
        delta_color=esi_col,
        icon=":material/coronavirus:",
        border=True,
        height="stretch",
    )

col_epi, col_gauge = st.columns([1.5, 1], gap="small")

with col_epi:
    with st.container(border=True, height="stretch"):
        st.subheader("Dengue and malaria surveillance comparison", anchor=False)
        dates = pd.date_range(end=datetime.now(), periods=12, freq="ME")
        epi_df = pd.DataFrame({
            "Month": [d.strftime("%b %y") for d in dates],
            "Dengue": [12, 8, 5, 4, 9, 32, 110, 195, 240, 145, 60, 22],
            "Malaria": [18, 12, 8, 6, 11, 45, 88, 130, 155, 92, 42, 25],
            "Rainfall": [5, 2, 8, 12, 22, 180, 310, 280, 160, 45, 10, 2],
        })
        st.echarts_chart(
            {
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                "grid": {"left": 42, "right": 45, "top": 36, "bottom": 28},
                "dataset": {"source": epi_df},
                "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8"}},
                "yAxis": [
                    {"type": "value", "name": "Cases", "axisLabel": {"color": "#94a3b8"}},
                    {"type": "value", "name": "Rain mm", "axisLabel": {"color": "#94a3b8"}},
                ],
                "series": [
                    {"type": "line", "name": "Dengue", "smooth": True, "encode": {"x": "Month", "y": "Dengue"}, "itemStyle": {"color": "#ef4444"}},
                    {"type": "line", "name": "Malaria", "smooth": True, "encode": {"x": "Month", "y": "Malaria"}, "itemStyle": {"color": "#f59e0b"}},
                    {"type": "bar", "name": "Rainfall (mm)", "yAxisIndex": 1, "encode": {"x": "Month", "y": "Rainfall"}, "itemStyle": {"color": "rgba(59, 130, 246, 0.30)"}},
                ],
            },
            height=290,
            alt="12-month Dengue and Malaria surveillance comparison against rainfall",
        )

with col_gauge:
    with st.container(border=True, height="stretch"):
        st.subheader("Vector suitability gauge", anchor=False)
        render_echarts_gauge(
            title="Suitability Index",
            value=esi_score,
            min_val=0,
            max_val=100,
            unit="pts",
            segments=[(0.40, "#10b981"), (0.70, "#f59e0b"), (1.0, "#ef4444")],
            alt="Environmental suitability index gauge for vector-borne disease",
            height=240,
        )
        st.caption("Composite weighting: 40% temperature suitability, 40% relative humidity, 20% 5-day precipitation.")
