import streamlit as st
import pandas as pd

from climate_core import (
    load_active_location_feeds,
    parse_forecast_df,
    evaluate_imd_heat,
    render_echarts_gauge,
)

zone, ward, loc, current_w, forecast_w, _, _ = load_active_location_feeds()

if not current_w:
    st.error("Unable to retrieve thermal feed for the selected zone.", icon=":material/cloud_off:")
    st.stop()

main = current_w.get("main", {})
temp = round(float(main.get("temp", 0)) + loc["temp_offset"], 1)
feels = round(float(main.get("feels_like", 0)) + loc["temp_offset"], 1)
t_min_now = round(float(main.get("temp_min", temp)) + loc["temp_offset"], 1)
t_max_now = round(float(main.get("temp_max", temp)) + loc["temp_offset"], 1)

f_df = parse_forecast_df(forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
fc_tmax = round(float(f_df["Temperature (°C)"].max()), 1) if not f_df.empty else t_max_now
fc_tmin = round(float(f_df["Temperature (°C)"].min()), 1) if not f_df.empty else t_min_now

heat_meta = evaluate_imd_heat(temp)
peak_meta = evaluate_imd_heat(fc_tmax)

max_trend = f_df.groupby("Date", sort=False)["Max Temp (°C)"].max().tolist() if not f_df.empty else [fc_tmax]
min_trend = f_df.groupby("Date", sort=False)["Min Temp (°C)"].min().tolist() if not f_df.empty else [fc_tmin]
hi_trend = f_df.head(12)["Feels Like (°C)"].tolist() if not f_df.empty else [feels]

st.caption(f"IMD Vidarbha thermal risk & diurnal analysis for **{ward}** ({zone}) · UHI offset {loc['temp_offset']:+.1f} °C")

# Alert banner driven by actual risk
if heat_meta["severity"] == "error":
    st.error(f"High-temperature alert: {heat_meta['label']} ({temp:.1f} °C). Activate NMC cooling shelters.", title="Severe Heatwave", icon=":material/warning:")
elif heat_meta["severity"] == "warning":
    st.warning(f"Thermal advisory: {heat_meta['label']} ({temp:.1f} °C). Limit peak midday outdoor exposure.", title="Heat Stress Advisory", icon=":material/thermostat:")
else:
    st.success(f"Thermal status: {heat_meta['label']} ({temp:.1f} °C). Within safe Vidarbha baseline.", title="Normal Thermal Range", icon=":material/check_circle:")

with st.grid(4, min_column_width=210, gap="small"):
    st.metric(
        "Maximum temperature (5D)",
        f"{fc_tmax:.1f} °C",
        delta=f"{fc_tmax - 40.0:+.1f} °C vs 40°C limit",
        delta_color=peak_meta["delta_color"],
        icon=":material/wb_sunny:",
        chart_data=max_trend,
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "Minimum temperature (5D)",
        f"{fc_tmin:.1f} °C",
        delta=f"Diurnal spread {fc_tmax - fc_tmin:.1f} °C",
        delta_color="blue" if fc_tmin < 25 else "yellow",
        icon=":material/nights_stay:",
        chart_data=min_trend,
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Heat index / apparent",
        f"{feels:.1f} °C",
        delta=f"{feels - temp:+.1f} °C moisture load",
        delta_color=evaluate_imd_heat(feels)["delta_color"],
        icon=":material/local_fire_department:",
        chart_data=hi_trend,
        chart_type="area",
        border=True,
        height="stretch",
    )
    st.metric(
        "Heat-risk classification",
        heat_meta["label"].split(" (")[0],
        delta=f"Current {temp:.1f} °C",
        delta_color=heat_meta["delta_color"],
        icon=":material/shield:",
        border=True,
        height="stretch",
    )

col_trend, col_gauge = st.columns([1.5, 1], gap="small")

with col_trend:
    with st.container(border=True, height="stretch"):
        st.subheader("Daily temperature trends", anchor=False)
        if not f_df.empty:
            daily_agg = f_df.groupby("Date", sort=False, as_index=False).agg(
                Max_Temp=("Max Temp (°C)", "max"),
                Min_Temp=("Min Temp (°C)", "min"),
                Apparent_Max=("Feels Like (°C)", "max"),
            )
            st.echarts_chart(
                {
                    "tooltip": {"trigger": "axis"},
                    "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                    "grid": {"left": 42, "right": 18, "top": 36, "bottom": 28},
                    "dataset": {"source": daily_agg},
                    "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8"}},
                    "yAxis": {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                    "series": [
                        {"type": "bar", "name": "Max (°C)", "encode": {"x": "Date", "y": "Max_Temp"}, "itemStyle": {"color": "#ef4444"}},
                        {"type": "bar", "name": "Min (°C)", "encode": {"x": "Date", "y": "Min_Temp"}, "itemStyle": {"color": "#3b82f6"}},
                        {"type": "line", "name": "Apparent Max (°C)", "smooth": True, "encode": {"x": "Date", "y": "Apparent_Max"}, "itemStyle": {"color": "#f59e0b"}},
                    ],
                },
                height=290,
                alt="Daily maximum, minimum, and apparent temperature trends",
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
            height=240,
        )
        thresh_df = pd.DataFrame([
            {"Level": "Normal", "Range": "< 35 °C", "Action": "Standard advisory"},
            {"Level": "Elevated (Yellow)", "Range": "40–44 °C", "Action": "Hydration alerts"},
            {"Level": "Heatwave (Amber)", "Range": "45–46 °C", "Action": "Cooling centers open"},
            {"Level": "Severe (Red)", "Range": "≥ 47 °C", "Action": "Emergency response"},
        ])
        st.dataframe(thresh_df, hide_index=True, alt="IMD heatwave classification thresholds")
