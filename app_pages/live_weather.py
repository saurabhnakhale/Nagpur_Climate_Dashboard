import streamlit as st
import pandas as pd

from climate_core import (
    load_active_location_feeds,
    parse_forecast_df,
    render_echarts_gauge,
    evaluate_imd_heat,
    risk_color_humidity,
    risk_color_wind,
    risk_color_pressure,
)

zone, ward, loc, current_w, forecast_w, air_w, _ = load_active_location_feeds()

if not current_w:
    st.error("Unable to retrieve live weather feed for the selected zone.", icon=":material/cloud_off:")
    st.stop()

main = current_w.get("main", {})
temp = round(float(main.get("temp", 0)) + loc["temp_offset"], 1)
feels = round(float(main.get("feels_like", 0)) + loc["temp_offset"], 1)
humidity = int(main.get("humidity", 0))
pressure = int(main.get("pressure", 0))
wind_kmh = round(float(current_w.get("wind", {}).get("speed", 0) or 0) * 3.6, 1)
wind_gust = round(float(current_w.get("wind", {}).get("gust", current_w.get("wind", {}).get("speed", 0)) or 0) * 3.6, 1)
clouds = int(current_w.get("clouds", {}).get("all", 0))
vis_km = round(float(current_w.get("visibility", 10000) or 10000) / 1000.0, 1)
cond = current_w.get("weather", [{}])[0].get("description", "Clear").title()

f_df = parse_forecast_df(forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
next_24 = f_df.head(8) if not f_df.empty else pd.DataFrame()

heat_meta = evaluate_imd_heat(temp)
hum_col = risk_color_humidity(humidity)
wind_col = risk_color_wind(wind_kmh)
pres_col = risk_color_pressure(pressure)

temp_trend = next_24["Temperature (°C)"].tolist() if not next_24.empty else [temp]
feels_trend = next_24["Feels Like (°C)"].tolist() if not next_24.empty else [feels]
hum_trend = next_24["Humidity (%)"].tolist() if not next_24.empty else [humidity]
wind_trend = next_24["Wind Speed (km/h)"].tolist() if not next_24.empty else [wind_kmh]
pres_trend = next_24["Pressure (hPa)"].tolist() if not next_24.empty else [pressure]

st.caption(f"Microclimate telemetry for **{ward}** ({zone}) · {loc['type']} · Elevation {loc['elev_m']} m")

# Dynamic KPI grid with mini trend sparklines and conditional risk colors
with st.grid(3, min_column_width=220, gap="small"):
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
        "Feels-like temperature",
        f"{feels:.1f} °C",
        delta=heat_meta["label"].split(" (")[0],
        delta_color=evaluate_imd_heat(feels)["delta_color"],
        icon=":material/device_thermostat:",
        chart_data=feels_trend,
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Humidity percentage",
        f"{humidity}%",
        delta="High moisture" if humidity >= 70 else ("Dry air" if humidity <= 30 else "Balanced"),
        delta_color=hum_col,
        icon=":material/humidity_percentage:",
        chart_data=hum_trend,
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "Wind speed",
        f"{wind_kmh:.1f} km/h",
        delta=f"Gusts {wind_gust:.1f} km/h",
        delta_color=wind_col,
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
        delta_color=pres_col,
        icon=":material/speed:",
        chart_data=pres_trend,
        chart_type="line",
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

# Main analytical row: 24-hour trend + responsive threshold gauges
col_chart, col_gauges = st.columns([1.45, 1], gap="small")

with col_chart:
    with st.container(border=True, height="stretch"):
        st.subheader("24-hour atmospheric trend", anchor=False)
        if not next_24.empty:
            chart_df = next_24[["TimeLabel", "Temperature (°C)", "Feels Like (°C)", "Humidity (%)"]].copy()
            st.echarts_chart(
                {
                    "tooltip": {"trigger": "axis"},
                    "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                    "grid": {"left": 42, "right": 45, "top": 36, "bottom": 32},
                    "dataset": {"source": chart_df},
                    "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "fontSize": 10}},
                    "yAxis": [
                        {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                        {"type": "value", "name": "%", "min": 0, "max": 100, "axisLabel": {"color": "#94a3b8"}},
                    ],
                    "series": [
                        {"type": "line", "name": "Temp (°C)", "smooth": True, "encode": {"x": "TimeLabel", "y": "Temperature (°C)"}, "itemStyle": {"color": "#2dd4bf"}},
                        {"type": "line", "name": "Feels Like (°C)", "smooth": True, "lineStyle": {"type": "dashed"}, "encode": {"x": "TimeLabel", "y": "Feels Like (°C)"}, "itemStyle": {"color": "#f59e0b"}},
                        {"type": "bar", "name": "Humidity (%)", "yAxisIndex": 1, "encode": {"x": "TimeLabel", "y": "Humidity (%)"}, "itemStyle": {"color": "rgba(59, 130, 246, 0.35)"}},
                    ],
                },
                height=290,
                alt="24-hour temperature, apparent temperature, and humidity trend",
            )

with col_gauges:
    with st.container(border=True, height="stretch"):
        st.subheader("Threshold gauges", anchor=False)
        g1, g2 = st.columns(2, gap="small")
        with g1:
            render_echarts_gauge(
                title="Humidity",
                value=humidity,
                min_val=0,
                max_val=100,
                unit="%",
                segments=[(0.30, "#f59e0b"), (0.65, "#10b981"), (0.80, "#f59e0b"), (1.0, "#ef4444")],
                alt="Humidity comfort threshold gauge",
                height=250,
            )
        with g2:
            render_echarts_gauge(
                title="Pressure",
                value=pressure,
                min_val=980,
                max_val=1040,
                unit="hPa",
                segments=[(0.33, "#ef4444"), (0.45, "#f59e0b"), (0.75, "#10b981"), (1.0, "#3b82f6")],
                alt="Atmospheric pressure threshold gauge",
                height=250,
            )
