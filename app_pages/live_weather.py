from datetime import datetime
import streamlit as st
import pandas as pd

from climate_core import (
    IST,
    load_active_location_feeds,
    parse_hourly_df,
    parse_daily_7d_df,
    fetch_openmeteo_history,
    get_time_range_config,
    compute_dew_point,
    deg_to_compass,
    evaluate_imd_heat,
    risk_color_humidity,
    risk_color_wind,
    risk_color_pressure,
    risk_color_uv,
    risk_color_dewpoint,
    render_echarts_gauge,
    render_wind_rose,
)

zone, ward, loc, current_w, forecast_w, _, om_w, _ = load_active_location_feeds()
tr_cfg = get_time_range_config()

if not current_w:
    st.error("Unable to retrieve live weather feed for the selected zone.", icon=":material/cloud_off:")
    st.stop()

main = current_w.get("main", {})
sys_info = current_w.get("sys", {})
wind_info = current_w.get("wind", {})

temp = round(float(main.get("temp", 0)) + loc["temp_offset"], 1)
feels = round(float(main.get("feels_like", 0)) + loc["temp_offset"], 1)
humidity = int(main.get("humidity", 0))
pressure = int(main.get("pressure", 0))
wind_kmh = round(float(wind_info.get("speed", 0) or 0) * 3.6, 1)
wind_gust = round(float(wind_info.get("gust", wind_info.get("speed", 0)) or 0) * 3.6, 1)
wind_deg = int(wind_info.get("deg", 0) or 0)
wind_dir_str = f"{deg_to_compass(wind_deg)} ({wind_deg}°)"
clouds = int(current_w.get("clouds", {}).get("all", 0))
vis_km = round(float(current_w.get("visibility", 10000) or 10000) / 1000.0, 1)
cond = current_w.get("weather", [{}])[0].get("description", "Clear").title()

# Sunrise / Sunset in IST
sr_epoch = sys_info.get("sunrise")
ss_epoch = sys_info.get("sunset")
sunrise_str = datetime.fromtimestamp(sr_epoch, IST).strftime("%I:%M %p") if sr_epoch else "06:15 AM"
sunset_str = datetime.fromtimestamp(ss_epoch, IST).strftime("%I:%M %p") if ss_epoch else "05:45 PM"
daylight_hrs = round((ss_epoch - sr_epoch) / 3600.0, 1) if (sr_epoch and ss_epoch) else 11.5

h_df = parse_hourly_df(om_w, forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
d7_df = parse_daily_7d_df(om_w, h_df, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])

# Dew Point & UV Index (current hour)
dew_pt = float(h_df.iloc[0]["Dew Point (°C)"]) if not h_df.empty else compute_dew_point(temp, humidity)
uv_now = float(h_df.iloc[0]["UV Index"]) if not h_df.empty else 0.0
uv_max_today = float(d7_df.iloc[0]["UV Max"]) if not d7_df.empty else uv_now
rain_prob_next = int(h_df.head(24)["Rain Prob (%)"].max()) if not h_df.empty else 0

dp_label, dp_col = risk_color_dewpoint(dew_pt)
uv_label, uv_col = risk_color_uv(max(uv_now, uv_max_today))
heat_meta = evaluate_imd_heat(temp)

next_24 = h_df.head(24) if not h_df.empty else pd.DataFrame()
temp_trend = next_24["Temperature (°C)"].tolist() if not next_24.empty else [temp]
dp_trend = next_24["Dew Point (°C)"].tolist() if not next_24.empty else [dew_pt]
uv_trend = next_24["UV Index"].tolist() if not next_24.empty else [uv_now]
hum_trend = next_24["Humidity (%)"].tolist() if not next_24.empty else [humidity]
wind_trend = next_24["Wind Speed (km/h)"].tolist() if not next_24.empty else [wind_kmh]

st.caption(f"Operational & advance telemetry for **{ward}** ({zone}) · Window: **{tr_cfg['label']}** · Elev {loc['elev_m']} m")

# 8-card responsive KPI grid covering all live & environmental indicators
with st.grid(4, min_column_width=200, gap="small"):
    st.metric(
        "Current temperature",
        f"{temp:.1f} °C",
        delta=f"{temp - feels:+.1f} °C vs apparent",
        delta_color=heat_meta["delta_color"],
        icon=":material/thermostat:",
        chart_data=temp_trend,
        chart_type="area",
        border=True,
        height="stretch",
    )
    st.metric(
        "Dew point temperature",
        f"{dew_pt:.1f} °C",
        delta=dp_label,
        delta_color=dp_col,
        icon=":material/dew_point:",
        chart_data=dp_trend,
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "UV index (now / peak)",
        f"{uv_now:.1f} / {uv_max_today:.1f}",
        delta=f"{uv_label} exposure",
        delta_color=uv_col,
        icon=":material/wb_sunny:",
        chart_data=uv_trend,
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "Humidity & rain prob",
        f"{humidity}%",
        delta=f"Rain prob {rain_prob_next}% (24h)",
        delta_color=risk_color_humidity(humidity),
        icon=":material/humidity_percentage:",
        chart_data=hum_trend,
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "Wind speed & direction",
        f"{wind_kmh:.1f} km/h",
        delta=f"{wind_dir_str} · Gust {wind_gust:.0f}",
        delta_color=risk_color_wind(wind_kmh),
        icon=":material/air:",
        chart_data=wind_trend,
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Atmospheric pressure",
        f"{pressure} hPa",
        delta="Low trough" if pressure < 1006 else "Stable ridge",
        delta_color=risk_color_pressure(pressure),
        icon=":material/speed:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Sunrise & sunset",
        sunrise_str,
        delta=f"Sunset {sunset_str} ({daylight_hrs}h)",
        delta_color="blue",
        icon=":material/wb_twilight:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Weather conditions",
        cond,
        delta=f"Cloud {clouds}% · Vis {vis_km} km",
        delta_color="blue",
        icon=":material/partly_cloudy_day:",
        border=True,
        height="stretch",
    )

# ── Dynamic Time-Range Chart + Wind Rose ──────────────────────────────────────
col_main, col_rose = st.columns([1.5, 1], gap="small")

with col_main:
    with st.container(border=True, height="stretch"):
        if tr_cfg["mode"] == "historical":
            st.subheader(f"Historical weather trend ({tr_cfg['label']})", anchor=False)
            hist_df = fetch_openmeteo_history(loc["lat"], loc["lon"], tr_cfg["start"], tr_cfg["end"])
            if not hist_df.empty:
                st.echarts_chart(
                    {
                        "tooltip": {"trigger": "axis"},
                        "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                        "grid": {"left": 42, "right": 18, "top": 36, "bottom": 32},
                        "dataZoom": [{"type": "inside"}],
                        "dataset": {"source": hist_df[["DateLabel", "Max Temp (°C)", "Min Temp (°C)", "Mean Temp (°C)"]]},
                        "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "fontSize": 10}},
                        "yAxis": {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                        "series": [
                            {"type": "line", "name": "Max (°C)", "showSymbol": False, "encode": {"x": "DateLabel", "y": "Max Temp (°C)"}, "itemStyle": {"color": "#ef4444"}},
                            {"type": "line", "name": "Mean (°C)", "showSymbol": False, "encode": {"x": "DateLabel", "y": "Mean Temp (°C)"}, "itemStyle": {"color": "#2dd4bf"}},
                            {"type": "line", "name": "Min (°C)", "showSymbol": False, "encode": {"x": "DateLabel", "y": "Min Temp (°C)"}, "itemStyle": {"color": "#3b82f6"}},
                        ],
                    },
                    height=290,
                    alt="Historical daily maximum, mean, and minimum temperature trend",
                )
            else:
                st.info("Historical archive unavailable for this window; showing 7-day forecast instead.")
        else:
            horizon_h = 24 if tr_cfg["mode"] == "hourly" else 168
            view_h = h_df.head(horizon_h)
            st.subheader(f"Hourly forecast ({tr_cfg['label']})", anchor=False)
            if not view_h.empty:
                st.echarts_chart(
                    {
                        "tooltip": {"trigger": "axis"},
                        "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                        "grid": {"left": 42, "right": 45, "top": 36, "bottom": 32},
                        "dataZoom": [{"type": "inside"}],
                        "dataset": {"source": view_h[["TimeLabel", "Temperature (°C)", "Dew Point (°C)", "Rain Prob (%)"]]},
                        "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "fontSize": 10}},
                        "yAxis": [
                            {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                            {"type": "value", "name": "Prob %", "min": 0, "max": 100, "axisLabel": {"color": "#94a3b8"}},
                        ],
                        "series": [
                            {"type": "line", "name": "Temp (°C)", "smooth": True, "showSymbol": False, "encode": {"x": "TimeLabel", "y": "Temperature (°C)"}, "itemStyle": {"color": "#2dd4bf"}},
                            {"type": "line", "name": "Dew Point (°C)", "smooth": True, "showSymbol": False, "lineStyle": {"type": "dashed"}, "encode": {"x": "TimeLabel", "y": "Dew Point (°C)"}, "itemStyle": {"color": "#a78bfa"}},
                            {"type": "bar", "name": "Rain Prob (%)", "yAxisIndex": 1, "encode": {"x": "TimeLabel", "y": "Rain Prob (%)"}, "itemStyle": {"color": "rgba(59, 130, 246, 0.30)"}},
                        ],
                    },
                    height=290,
                    alt="Hourly temperature, dew point, and rainfall probability forecast",
                )

with col_rose:
    with st.container(border=True, height="stretch"):
        st.subheader("Wind direction & wind rose", anchor=False)
        render_wind_rose(h_df.head(168), height=290)

# ── 7-Day Forecast Table & Threshold Gauges ───────────────────────────────────
col_7d, col_gauges = st.columns([1.25, 1], gap="small")

with col_7d:
    with st.container(border=True, height="stretch"):
        st.subheader("7-day weather forecast", anchor=False)
        if not d7_df.empty:
            cols_show = [c for c in ["Date", "Max Temp (°C)", "Min Temp (°C)", "UV Max", "Rain Prob (%)", "Rainfall (mm)", "Sunrise", "Sunset"] if c in d7_df.columns]
            st.dataframe(d7_df[cols_show], hide_index=True, height=260, alt="7-day daily weather forecast table")

with col_gauges:
    with st.container(border=True, height="stretch"):
        st.subheader("Exposure & moisture gauges", anchor=False)
        g1, g2 = st.columns(2, gap="small")
        with g1:
            render_echarts_gauge(
                title="UV Index",
                value=max(uv_now, uv_max_today),
                min_val=0,
                max_val=13,
                unit="UV",
                segments=[(0.23, "#10b981"), (0.46, "#f59e0b"), (0.62, "#f97316"), (0.85, "#ef4444"), (1.0, "#a855f7")],
                alt="UV index outdoor exposure threshold gauge",
                height=240,
            )
        with g2:
            render_echarts_gauge(
                title="Dew Point",
                value=dew_pt,
                min_val=0,
                max_val=35,
                unit="°C",
                segments=[(0.28, "#3b82f6"), (0.46, "#10b981"), (0.57, "#f59e0b"), (0.69, "#f97316"), (1.0, "#ef4444")],
                alt="Dew point atmospheric moisture threshold gauge",
                height=240,
            )
