import streamlit as st
import pandas as pd

from climate_core import (
    load_active_location_feeds,
    parse_forecast_df,
    risk_color_rain,
    render_echarts_gauge,
)

zone, ward, loc, current_w, forecast_w, _, _ = load_active_location_feeds()
f_df = parse_forecast_df(forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])

total_5d = round(float(f_df["Rainfall (mm/3h)"].sum()), 1) if not f_df.empty else 0.0
peak_3h = round(float(f_df["Rainfall (mm/3h)"].max()), 1) if not f_df.empty else 0.0
peak_1h = round(peak_3h / 3.0, 2)
rain_series = f_df.head(12)["Rainfall (mm/3h)"].tolist() if not f_df.empty else [0.0]

if peak_3h >= 30.0:
    flood_status, flood_col, alert_type = "Critical waterlogging", "red", "error"
elif peak_3h >= 15.0:
    flood_status, flood_col, alert_type = "High inundation risk", "orange", "warning"
elif total_5d >= 20.0:
    flood_status, flood_col, alert_type = "Moderate runoff", "yellow", "warning"
else:
    flood_status, flood_col, alert_type = "Normal drainage", "green", "success"

st.caption(f"Hydrological accumulation & drainage risk for **{ward}** ({zone}) · Baseline drainage vulnerability: **{loc['drainage_risk']}**")

if alert_type == "error":
    st.error(f"Heavy rainfall alert: Peak {peak_3h:.1f} mm/3h expected. Low-lying wards in {zone} face flash flooding.", title="Critical Rainfall Alert", icon=":material/flood:")
elif alert_type == "warning":
    st.warning(f"Elevated rainfall alert: {total_5d:.1f} mm 5-day accumulation. Monitor Nag Nadi & Pili Nadi drains.", title="Runoff Advisory", icon=":material/rainy:")
else:
    st.success(f"Normal precipitation outlook ({total_5d:.1f} mm over 5 days). Stormwater drains within capacity.", title="Normal Hydrology", icon=":material/check_circle:")

with st.grid(4, min_column_width=210, gap="small"):
    st.metric(
        "Peak hourly rainfall",
        f"{peak_1h:.1f} mm/h",
        delta=f"Peak 3h: {peak_3h:.1f} mm",
        delta_color=risk_color_rain(peak_3h),
        icon=":material/rainy:",
        chart_data=rain_series,
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "5-day accumulation",
        f"{total_5d:.1f} mm",
        delta="Total projected",
        delta_color="blue" if total_5d < 20 else "orange",
        icon=":material/water_drop:",
        chart_data=f_df["Rainfall (mm/3h)"].cumsum().head(12).tolist() if not f_df.empty else [0.0],
        chart_type="area",
        border=True,
        height="stretch",
    )
    st.metric(
        "Heavy rainfall alert",
        "Downpour" if peak_3h >= 15 else "Normal",
        delta="Threshold: 15 mm/3h",
        delta_color="red" if peak_3h >= 15 else "green",
        icon=":material/thunderstorm:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Waterlogging indicator",
        flood_status.split()[0],
        delta=f"Zone risk: {loc['drainage_risk']}",
        delta_color=flood_col,
        icon=":material/flood:",
        border=True,
        height="stretch",
    )

col_rain, col_side = st.columns([1.5, 1], gap="small")

with col_rain:
    with st.container(border=True, height="stretch"):
        st.subheader("Hourly & cumulative rainfall trend", anchor=False)
        if not f_df.empty:
            rain_df = f_df[["TimeLabel", "Rainfall (mm/3h)"]].copy()
            rain_df["Cumulative (mm)"] = rain_df["Rainfall (mm/3h)"].cumsum().round(2)
            st.echarts_chart(
                {
                    "tooltip": {"trigger": "axis"},
                    "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                    "grid": {"left": 45, "right": 45, "top": 36, "bottom": 36},
                    "dataZoom": [{"type": "inside"}],
                    "dataset": {"source": rain_df},
                    "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "fontSize": 10}},
                    "yAxis": [
                        {"type": "value", "name": "3h mm", "axisLabel": {"color": "#94a3b8"}},
                        {"type": "value", "name": "Cum mm", "axisLabel": {"color": "#94a3b8"}},
                    ],
                    "series": [
                        {"type": "bar", "name": "3h Rainfall (mm)", "encode": {"x": "TimeLabel", "y": "Rainfall (mm/3h)"}, "itemStyle": {"color": "#3b82f6"}},
                        {"type": "line", "name": "Cumulative (mm)", "yAxisIndex": 1, "smooth": True, "encode": {"x": "TimeLabel", "y": "Cumulative (mm)"}, "itemStyle": {"color": "#2dd4bf"}},
                    ],
                },
                height=300,
                alt="3-hourly rainfall and cumulative precipitation trend",
            )

with col_side:
    with st.container(border=True, height="stretch"):
        st.subheader("Peak intensity gauge", anchor=False)
        render_echarts_gauge(
            title="3h Intensity",
            value=peak_3h,
            min_val=0,
            max_val=50,
            unit="mm",
            segments=[(0.10, "#10b981"), (0.30, "#f59e0b"), (0.60, "#f97316"), (1.0, "#ef4444")],
            alt="Peak 3-hour rainfall intensity gauge",
            height=210,
        )
        ward_risk = pd.DataFrame([
            {"Basin / Ward": "Dhantoli (Nag Nadi)", "Threshold": "15 mm/3h", "Status": "Critical"},
            {"Basin / Ward": "Lakadganj (Pili Nadi)", "Threshold": "18 mm/3h", "Status": "Critical"},
            {"Basin / Ward": "Gandhi Bagh / Sitabuldi", "Threshold": "22 mm/3h", "Status": "High"},
            {"Basin / Ward": "Laxmi Nagar / Ambazari", "Threshold": "45 mm/3h", "Status": "Low"},
        ])
        st.dataframe(ward_risk, hide_index=True, alt="Waterlogging vulnerability by Nagpur drainage basin")
