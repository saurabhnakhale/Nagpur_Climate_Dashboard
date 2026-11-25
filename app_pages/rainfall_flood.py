import streamlit as st
import pandas as pd

from climate_core import (
    load_active_location_feeds,
    parse_hourly_df,
    parse_daily_7d_df,
    fetch_openmeteo_history,
    get_time_range_config,
    risk_color_rain,
    render_echarts_gauge,
)

zone, ward, loc, _, forecast_w, _, om_w, _ = load_active_location_feeds()
tr_cfg = get_time_range_config()

h_df = parse_hourly_df(om_w, forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
d7_df = parse_daily_7d_df(om_w, h_df, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
hist_df = fetch_openmeteo_history(loc["lat"], loc["lon"], tr_cfg["start"], tr_cfg["end"]) if tr_cfg["mode"] == "historical" else pd.DataFrame()

horizon_h = 24 if tr_cfg["mode"] == "hourly" else 168
view_h = h_df.head(horizon_h)

if not hist_df.empty:
    total_rain = round(float(hist_df["Rainfall (mm)"].sum()), 1)
    peak_daily = round(float(hist_df["Rainfall (mm)"].max()), 1)
    max_prob = int(d7_df["Rain Prob (%)"].max()) if not d7_df.empty else 0
    rain_series = hist_df["Rainfall (mm)"].tail(14).tolist()
    cum_series = hist_df["Rainfall (mm)"].cumsum().tail(14).tolist()
else:
    total_rain = round(float(view_h["Rainfall (mm)"].sum()), 1) if not view_h.empty else 0.0
    peak_daily = round(float(view_h["Rainfall (mm)"].max()), 1) if not view_h.empty else 0.0
    max_prob = int(view_h["Rain Prob (%)"].max()) if not view_h.empty else 0
    rain_series = view_h.head(24)["Rainfall (mm)"].tolist() if not view_h.empty else [0.0]
    cum_series = view_h.head(24)["Rainfall (mm)"].cumsum().tolist() if not view_h.empty else [0.0]

if peak_daily >= 30.0:
    flood_status, flood_col, alert_type = "Critical waterlogging", "red", "error"
elif peak_daily >= 15.0:
    flood_status, flood_col, alert_type = "High inundation risk", "orange", "warning"
elif total_rain >= 20.0:
    flood_status, flood_col, alert_type = "Moderate runoff", "yellow", "warning"
else:
    flood_status, flood_col, alert_type = "Normal drainage", "green", "success"

st.caption(f"Precipitation probability, accumulation & flood risk for **{ward}** ({zone}) · Window: **{tr_cfg['label']}** · Drainage: **{loc['drainage_risk']}**")

if alert_type == "error":
    st.error(f"Heavy rainfall alert: Peak {peak_daily:.1f} mm expected. Low-lying wards in {zone} face flash flooding.", title="Critical Rainfall Alert", icon=":material/flood:")
elif alert_type == "warning":
    st.warning(f"Elevated rainfall advisory: {total_rain:.1f} mm accumulation ({max_prob}% peak probability). Monitor Nag Nadi & Pili Nadi drains.", title="Runoff Advisory", icon=":material/rainy:")
else:
    st.success(f"Normal precipitation outlook ({total_rain:.1f} mm total, {max_prob}% peak probability). Stormwater drains within capacity.", title="Normal Hydrology", icon=":material/check_circle:")

with st.grid(4, min_column_width=200, gap="small"):
    st.metric(
        "Rainfall probability (peak)",
        f"{max_prob}%",
        delta="Next 24h–7d chance" if max_prob >= 30 else "Low likelihood",
        delta_color="red" if max_prob >= 70 else ("orange" if max_prob >= 40 else "green"),
        icon=":material/umbrella:",
        chart_data=view_h.head(24)["Rain Prob (%)"].tolist() if not view_h.empty else [max_prob],
        chart_type="area",
        border=True,
        height="stretch",
    )
    st.metric(
        f"Accumulation ({tr_cfg['label']})",
        f"{total_rain:.1f} mm",
        delta=f"Peak {peak_daily:.1f} mm",
        delta_color=risk_color_rain(peak_daily),
        icon=":material/water_drop:",
        chart_data=cum_series,
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Heavy rainfall alert",
        "Downpour" if peak_daily >= 15 else "Normal",
        delta="Threshold: 15 mm",
        delta_color="red" if peak_daily >= 15 else "green",
        icon=":material/thunderstorm:",
        chart_data=rain_series,
        chart_type="bar",
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
        if not hist_df.empty:
            st.subheader(f"Historical daily rainfall ({tr_cfg['label']})", anchor=False)
            hist_plot = hist_df[["DateLabel", "Rainfall (mm)"]].copy()
            hist_plot["Cumulative (mm)"] = hist_plot["Rainfall (mm)"].cumsum().round(1)
            st.echarts_chart(
                {
                    "tooltip": {"trigger": "axis"},
                    "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                    "grid": {"left": 45, "right": 45, "top": 36, "bottom": 36},
                    "dataZoom": [{"type": "inside"}],
                    "dataset": {"source": hist_plot},
                    "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "fontSize": 10}},
                    "yAxis": [
                        {"type": "value", "name": "Daily mm", "axisLabel": {"color": "#94a3b8"}},
                        {"type": "value", "name": "Cum mm", "axisLabel": {"color": "#94a3b8"}},
                    ],
                    "series": [
                        {"type": "bar", "name": "Daily Rain (mm)", "encode": {"x": "DateLabel", "y": "Rainfall (mm)"}, "itemStyle": {"color": "#3b82f6"}},
                        {"type": "line", "name": "Cumulative (mm)", "yAxisIndex": 1, "smooth": True, "showSymbol": False, "encode": {"x": "DateLabel", "y": "Cumulative (mm)"}, "itemStyle": {"color": "#2dd4bf"}},
                    ],
                },
                height=300,
                alt="Historical daily and cumulative rainfall",
            )
        else:
            st.subheader(f"Rainfall & probability forecast ({tr_cfg['label']})", anchor=False)
            if not view_h.empty:
                rain_df = view_h[["TimeLabel", "Rainfall (mm)", "Rain Prob (%)"]].copy()
                st.echarts_chart(
                    {
                        "tooltip": {"trigger": "axis"},
                        "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                        "grid": {"left": 45, "right": 45, "top": 36, "bottom": 36},
                        "dataZoom": [{"type": "inside"}],
                        "dataset": {"source": rain_df},
                        "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "fontSize": 10}},
                        "yAxis": [
                            {"type": "value", "name": "mm/h", "axisLabel": {"color": "#94a3b8"}},
                            {"type": "value", "name": "Prob %", "min": 0, "max": 100, "axisLabel": {"color": "#94a3b8"}},
                        ],
                        "series": [
                            {"type": "bar", "name": "Rainfall (mm)", "encode": {"x": "TimeLabel", "y": "Rainfall (mm)"}, "itemStyle": {"color": "#3b82f6"}},
                            {"type": "line", "name": "Rain Prob (%)", "yAxisIndex": 1, "smooth": True, "showSymbol": False, "encode": {"x": "TimeLabel", "y": "Rain Prob (%)"}, "itemStyle": {"color": "#2dd4bf"}},
                        ],
                    },
                    height=300,
                    alt="Hourly rainfall volume and precipitation probability forecast",
                )

with col_side:
    with st.container(border=True, height="stretch"):
        st.subheader("Rainfall probability gauge", anchor=False)
        render_echarts_gauge(
            title="Peak Prob",
            value=max_prob,
            min_val=0,
            max_val=100,
            unit="%",
            segments=[(0.30, "#10b981"), (0.60, "#f59e0b"), (1.0, "#ef4444")],
            alt="Peak rainfall probability gauge",
            height=210,
        )
        ward_risk = pd.DataFrame([
            {"Basin / Ward": "Dhantoli (Nag Nadi)", "Threshold": "15 mm/3h", "Status": "Critical"},
            {"Basin / Ward": "Lakadganj (Pili Nadi)", "Threshold": "18 mm/3h", "Status": "Critical"},
            {"Basin / Ward": "Gandhi Bagh / Sitabuldi", "Threshold": "22 mm/3h", "Status": "High"},
            {"Basin / Ward": "Laxmi Nagar / Ambazari", "Threshold": "45 mm/3h", "Status": "Low"},
        ])
        st.dataframe(ward_risk, hide_index=True, alt="Waterlogging vulnerability by Nagpur drainage basin")
