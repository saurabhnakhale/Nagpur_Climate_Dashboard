import streamlit as st
import pandas as pd

from climate_core import (
    NAGPUR_CLIMATE_NORMALS,
    load_active_location_feeds,
    parse_hourly_df,
    parse_daily_7d_df,
    fetch_openmeteo_history,
    get_time_range_config,
    evaluate_imd_heat,
    risk_color_uv,
    render_echarts_gauge,
)

zone, ward, loc, current_w, forecast_w, _, om_w, _ = load_active_location_feeds()
tr_cfg = get_time_range_config()

if not current_w:
    st.error("Unable to retrieve thermal feed for the selected zone.", icon=":material/cloud_off:")
    st.stop()

main = current_w.get("main", {})
temp = round(float(main.get("temp", 0)) + loc["temp_offset"], 1)
feels = round(float(main.get("feels_like", 0)) + loc["temp_offset"], 1)

h_df = parse_hourly_df(om_w, forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
d7_df = parse_daily_7d_df(om_w, h_df, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
hist_df = fetch_openmeteo_history(loc["lat"], loc["lon"], tr_cfg["start"], tr_cfg["end"]) if tr_cfg["mode"] == "historical" else pd.DataFrame()

if not hist_df.empty:
    period_tmax = round(float(hist_df["Max Temp (°C)"].max()), 1)
    period_tmin = round(float(hist_df["Min Temp (°C)"].min()), 1)
    mean_dev = round(float(hist_df["Deviation (°C)"].mean()), 2)
    max_trend = hist_df["Max Temp (°C)"].tail(14).tolist()
    min_trend = hist_df["Min Temp (°C)"].tail(14).tolist()
else:
    period_tmax = round(float(d7_df["Max Temp (°C)"].max()), 1) if not d7_df.empty else temp
    period_tmin = round(float(d7_df["Min Temp (°C)"].min()), 1) if not d7_df.empty else temp
    cur_month_norm = NAGPUR_CLIMATE_NORMALS[pd.Timestamp.now().month]["mean"]
    mean_dev = round(temp - cur_month_norm, 2)
    max_trend = d7_df["Max Temp (°C)"].tolist() if not d7_df.empty else [period_tmax]
    min_trend = d7_df["Min Temp (°C)"].tolist() if not d7_df.empty else [period_tmin]

uv_peak = round(float(d7_df["UV Max"].max()), 1) if not d7_df.empty and "UV Max" in d7_df.columns else 0.0
uv_label, uv_col = risk_color_uv(uv_peak)
heat_meta = evaluate_imd_heat(temp)
peak_meta = evaluate_imd_heat(period_tmax)

st.caption(f"Daily min/max, historical climate deviation, and UV exposure for **{ward}** ({zone}) · Window: **{tr_cfg['label']}**")

if heat_meta["severity"] == "error":
    st.error(f"High-temperature alert: {heat_meta['label']} ({temp:.1f} °C). Activate NMC cooling shelters.", title="Severe Heatwave", icon=":material/warning:")
elif heat_meta["severity"] == "warning":
    st.warning(f"Thermal advisory: {heat_meta['label']} ({temp:.1f} °C). Limit peak midday outdoor exposure.", title="Heat Stress Advisory", icon=":material/thermostat:")
else:
    st.success(f"Thermal status: {heat_meta['label']} ({temp:.1f} °C). Within safe Vidarbha baseline.", title="Normal Thermal Range", icon=":material/check_circle:")

with st.grid(4, min_column_width=200, gap="small"):
    st.metric(
        f"Max temperature ({tr_cfg['label']})",
        f"{period_tmax:.1f} °C",
        delta=f"{period_tmax - 40.0:+.1f} °C vs 40°C limit",
        delta_color=peak_meta["delta_color"],
        icon=":material/wb_sunny:",
        chart_data=max_trend,
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        f"Min temperature ({tr_cfg['label']})",
        f"{period_tmin:.1f} °C",
        delta=f"Spread {period_tmax - period_tmin:.1f} °C",
        delta_color="blue" if period_tmin < 25 else "yellow",
        icon=":material/nights_stay:",
        chart_data=min_trend,
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Historical climate deviation",
        f"{mean_dev:+.1f} °C",
        delta="vs 30-year IMD normal",
        delta_color="red" if mean_dev >= 2.0 else ("orange" if mean_dev >= 0.8 else "green"),
        icon=":material/history:",
        chart_data=hist_df["Deviation (°C)"].tail(14).tolist() if not hist_df.empty else [mean_dev],
        chart_type="area",
        border=True,
        height="stretch",
    )
    st.metric(
        "Peak UV exposure",
        f"{uv_peak:.1f}",
        delta=f"{uv_label} · {heat_meta['label'].split(' (')[0]}",
        delta_color=uv_col,
        icon=":material/flare:",
        border=True,
        height="stretch",
    )

col_trend, col_gauge = st.columns([1.5, 1], gap="small")

with col_trend:
    with st.container(border=True, height="stretch"):
        if not hist_df.empty:
            st.subheader(f"Historical temperature comparison ({tr_cfg['label']})", anchor=False)
            st.echarts_chart(
                {
                    "tooltip": {"trigger": "axis"},
                    "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                    "grid": {"left": 42, "right": 18, "top": 36, "bottom": 32},
                    "dataZoom": [{"type": "inside"}],
                    "dataset": {"source": hist_df[["DateLabel", "Max Temp (°C)", "Min Temp (°C)", "Normal Max (°C)"]]},
                    "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "fontSize": 10}},
                    "yAxis": {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                    "series": [
                        {"type": "line", "name": "Observed Max (°C)", "showSymbol": False, "encode": {"x": "DateLabel", "y": "Max Temp (°C)"}, "itemStyle": {"color": "#ef4444"}},
                        {"type": "line", "name": "Observed Min (°C)", "showSymbol": False, "encode": {"x": "DateLabel", "y": "Min Temp (°C)"}, "itemStyle": {"color": "#3b82f6"}},
                        {"type": "line", "name": "IMD Normal Max (°C)", "showSymbol": False, "lineStyle": {"type": "dashed"}, "encode": {"x": "DateLabel", "y": "Normal Max (°C)"}, "itemStyle": {"color": "#f59e0b"}},
                    ],
                },
                height=300,
                alt="Historical observed max and min temperatures compared with IMD monthly normal",
            )
        else:
            st.subheader("7-day daily min/max vs IMD normal", anchor=False)
            if not d7_df.empty:
                st.echarts_chart(
                    {
                        "tooltip": {"trigger": "axis"},
                        "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                        "grid": {"left": 42, "right": 18, "top": 36, "bottom": 28},
                        "dataset": {"source": d7_df},
                        "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8"}},
                        "yAxis": {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                        "series": [
                            {"type": "bar", "name": "Forecast Max (°C)", "encode": {"x": "Date", "y": "Max Temp (°C)"}, "itemStyle": {"color": "#ef4444"}},
                            {"type": "bar", "name": "Forecast Min (°C)", "encode": {"x": "Date", "y": "Min Temp (°C)"}, "itemStyle": {"color": "#3b82f6"}},
                            {"type": "line", "name": "IMD Normal Max (°C)", "lineStyle": {"type": "dashed"}, "encode": {"x": "Date", "y": "Normal Max (°C)"}, "itemStyle": {"color": "#f59e0b"}},
                        ],
                    },
                    height=300,
                    alt="7-day daily maximum and minimum temperature forecast compared with IMD normal",
                )

with col_gauge:
    with st.container(border=True, height="stretch"):
        st.subheader("Heat stress gauge", anchor=False)
        render_echarts_gauge(
            title="IMD Heat Index",
            value=feels,
            min_val=15,
            max_val=55,
            unit="°C",
            segments=[(0.45, "#10b981"), (0.625, "#3b82f6"), (0.75, "#f59e0b"), (0.80, "#f97316"), (1.0, "#ef4444")],
            alt="IMD heat stress threshold gauge",
            height=230,
        )
        thresh_df = pd.DataFrame([
            {"Level": "Normal", "Range": "< 35 °C", "Action": "Standard advisory"},
            {"Level": "Elevated (Yellow)", "Range": "40–44 °C", "Action": "Hydration alerts"},
            {"Level": "Heatwave (Amber)", "Range": "45–46 °C", "Action": "Cooling centers open"},
            {"Level": "Severe (Red)", "Range": "≥ 47 °C", "Action": "Emergency response"},
        ])
        st.dataframe(thresh_df, hide_index=True, alt="IMD heatwave classification thresholds")
