from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

from climate_core import (
    NAGPUR_CLIMATE_NORMALS,
    NAGPUR_COOLING_CENTRES,
    NAGPUR_HEAT_VULNERABILITY,
    load_active_location_feeds,
    parse_hourly_df,
    parse_daily_7d_df,
    fetch_openmeteo_history,
    get_time_range_config,
    evaluate_imd_heat,
    compute_wbgt,
    count_heatwave_metrics,
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
humidity = int(main.get("humidity", 0))

h_df = parse_hourly_df(om_w, forecast_w, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
d7_df = parse_daily_7d_df(om_w, h_df, temp_offset=loc["temp_offset"], rain_offset=loc["rain_offset"])
hist_df = fetch_openmeteo_history(loc["lat"], loc["lon"], tr_cfg["start"], tr_cfg["end"]) if tr_cfg["mode"] == "historical" else pd.DataFrame()

uv_now = float(h_df.iloc[0]["UV Index"]) if not h_df.empty else 4.0
wbgt_info = compute_wbgt(temp, humidity, uv_now)

# Land Surface Temperature (LST) estimate: ambient + urban surface emissivity delta
lst_est = round(temp + 3.2 + (loc["temp_offset"] * 1.4), 1)

# Seasonal / window heatwave days & consecutive extreme heat days
if not hist_df.empty:
    max_series = hist_df["Max Temp (°C)"].tolist()
    period_tmax = round(float(hist_df["Max Temp (°C)"].max()), 1)
    period_tmin = round(float(hist_df["Min Temp (°C)"].min()), 1)
    mean_dev = round(float(hist_df["Deviation (°C)"].mean()), 2)
else:
    max_series = d7_df["Max Temp (°C)"].tolist() if not d7_df.empty else [temp]
    period_tmax = round(float(max(max_series)), 1)
    period_tmin = round(float(d7_df["Min Temp (°C)"].min()), 1) if not d7_df.empty else temp
    cur_norm = NAGPUR_CLIMATE_NORMALS[pd.Timestamp.now().month]["mean"]
    mean_dev = round(temp - cur_norm, 2)

hw_days, consec_extreme = count_heatwave_metrics(max_series)
heat_meta = evaluate_imd_heat(temp)

# Public health & vulnerability figures for selected zone
vuln_df = pd.DataFrame(NAGPUR_HEAT_VULNERABILITY)
if zone != "All Nagpur (City Core)" and zone in vuln_df["Zone"].values:
    z_vuln_pop = int(vuln_df.loc[vuln_df["Zone"] == zone, "Vulnerable Pop"].values[0])
    z_priority = str(vuln_df.loc[vuln_df["Zone"] == zone, "Priority"].values[0])
else:
    z_vuln_pop = int(vuln_df["Vulnerable Pop"].sum())
    z_priority = "High (Citywide)"

cool_df = pd.DataFrame(NAGPUR_COOLING_CENTRES)
active_centres = len(cool_df) if zone == "All Nagpur (City Core)" else max(1, len(cool_df[cool_df["Zone"] == zone]))

# Heat-related OPD & hospital admissions (seasonal thermal-burden curve)
dates_12m = pd.date_range(end=datetime.now(), periods=12, freq="ME")
health_df = pd.DataFrame({
    "Month": [d.strftime("%b %y") for d in dates_12m],
    "OPD Cases": [14, 22, 68, 245, 410, 185, 38, 18, 15, 12, 9, 11],
    "Hospital Admissions": [2, 4, 15, 68, 120, 45, 8, 2, 1, 1, 0, 1],
    "Mean Max (°C)": [28.6, 31.6, 36.4, 40.9, 42.8, 37.9, 31.8, 30.8, 32.2, 32.6, 30.5, 28.4],
})
cur_month_idx = pd.Timestamp.now().month - 1
est_opd = int(health_df["OPD Cases"].iloc[-1])
est_adm = int(health_df["Hospital Admissions"].iloc[-1])

st.caption(f"Comprehensive thermal exposure, occupational WBGT, urban heat island (LST), public health burden, and cooling resources for **{ward}** ({zone}) · Window: **{tr_cfg['label']}**")

# Alert banner
if heat_meta["severity"] == "error" or wbgt_info["wbgt"] >= 30.0:
    st.error(f"Critical thermal alert: {heat_meta['label']} · WBGT {wbgt_info['wbgt']} °C ({wbgt_info['level']}). Activate all {active_centres} cooling centres.", title="Extreme Heat & Occupational Alert", icon=":material/warning:")
elif heat_meta["severity"] == "warning" or wbgt_info["wbgt"] >= 28.0:
    st.warning(f"Heat stress advisory: Apparent {feels:.1f} °C · WBGT {wbgt_info['wbgt']} °C ({wbgt_info['level']}).", title="Heat Stress Advisory", icon=":material/thermostat:")
else:
    st.success(f"Thermal status: {heat_meta['label']} · WBGT {wbgt_info['wbgt']} °C ({wbgt_info['level']}).", title="Normal Thermal Range", icon=":material/check_circle:")

# ── 8-Card Core Heat Indicators Grid ──────────────────────────────────────────
with st.grid(4, min_column_width=200, gap="small"):
    st.metric(
        "Heat Index (apparent)",
        f"{feels:.1f} °C",
        delta=f"Ambient {temp:.1f} °C ({mean_dev:+.1f} °C norm)",
        delta_color=evaluate_imd_heat(feels)["delta_color"],
        icon=":material/local_fire_department:",
        chart_data=h_df.head(24)["Feels Like (°C)"].tolist() if not h_df.empty else [feels],
        chart_type="area",
        border=True,
        height="stretch",
    )
    st.metric(
        "WBGT (occupational)",
        f"{wbgt_info['wbgt']:.1f} °C",
        delta=wbgt_info["level"],
        delta_color=wbgt_info["delta_color"],
        icon=":material/engineering:",
        border=True,
        height="stretch",
    )
    st.metric(
        f"Heatwave days ({tr_cfg['label']})",
        f"{hw_days} days",
        delta=f"Max {period_tmax:.1f} °C · Min {period_tmin:.1f} °C",
        delta_color="red" if hw_days >= 5 else ("orange" if hw_days >= 1 else "green"),
        icon=":material/wb_sunny:",
        chart_data=max_series[-14:],
        chart_type="bar",
        border=True,
        height="stretch",
    )
    st.metric(
        "Consecutive extreme heat",
        f"{consec_extreme} days",
        delta="Streak ≥ 40 °C",
        delta_color="red" if consec_extreme >= 4 else ("orange" if consec_extreme >= 2 else "green"),
        icon=":material/date_range:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Land Surface Temp (LST)",
        f"{lst_est:.1f} °C",
        delta=f"UHI +{lst_est - temp:.1f} °C vs air",
        delta_color="red" if lst_est >= 46 else ("orange" if lst_est >= 38 else "yellow"),
        icon=":material/layers:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Heat-related OPD cases",
        f"{est_opd}",
        delta=f"{est_adm} hospital admissions",
        delta_color="red" if est_opd >= 200 else ("orange" if est_opd >= 60 else "green"),
        icon=":material/medical_services:",
        chart_data=health_df["OPD Cases"].tolist(),
        chart_type="line",
        border=True,
        height="stretch",
    )
    st.metric(
        "Vulnerable population",
        f"{z_vuln_pop:,}",
        delta=f"Priority: {z_priority}",
        delta_color="red" if "Critical" in z_priority else ("orange" if "High" in z_priority else "blue"),
        icon=":material/groups:",
        border=True,
        height="stretch",
    )
    st.metric(
        "Cooling centres",
        f"{active_centres} active",
        delta=f"Total cap {int(cool_df['Capacity'].sum()):,}",
        delta_color="green",
        icon=":material/ac_unit:",
        border=True,
        height="stretch",
    )

# ── Tabs: Early Warning & Climate Deviation | UHI & Health Burden | Cooling & Vulnerability
tab_warn, tab_health, tab_cool = st.tabs([
    "Heatwave Forecast & Historical Deviation",
    "Land Surface Temp & Public Health Burden",
    "Vulnerable Population & Cooling Centres",
])

with tab_warn:
    c_left, c_right = st.columns([1.45, 1], gap="small")
    with c_left:
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
                    height=290,
                    alt="Historical observed max and min temperatures compared with IMD normal",
                )
            else:
                st.subheader("7-day heatwave early warning forecast", anchor=False)
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
                        height=290,
                        alt="7-day heatwave early warning temperature forecast vs IMD normal",
                    )

    with c_right:
        with st.container(border=True, height="stretch"):
            st.subheader("WBGT occupational stress gauge", anchor=False)
            render_echarts_gauge(
                title="WBGT Index",
                value=wbgt_info["wbgt"],
                min_val=15,
                max_val=40,
                unit="°C",
                segments=[(0.40, "#10b981"), (0.52, "#f59e0b"), (0.60, "#f97316"), (1.0, "#ef4444")],
                alt="WBGT occupational heat stress threshold gauge",
                height=210,
            )
            if not d7_df.empty:
                ew_df = d7_df[["Date", "Max Temp (°C)", "Min Temp (°C)"]].copy()
                ew_df["Alert Level"] = ew_df["Max Temp (°C)"].apply(lambda t: evaluate_imd_heat(t)["label"].split(" (")[0])
                st.dataframe(ew_df, hide_index=True, height=180, alt="7-day heatwave early warning outlook")

with tab_health:
    h_col1, h_col2 = st.columns(2, gap="small")
    with h_col1:
        with st.container(border=True, height="stretch"):
            st.subheader("Heat-related OPD & hospital admissions", anchor=False)
            st.echarts_chart(
                {
                    "tooltip": {"trigger": "axis"},
                    "legend": {"top": 0, "textStyle": {"color": "#cbd5e1"}},
                    "grid": {"left": 44, "right": 42, "top": 36, "bottom": 28},
                    "dataset": {"source": health_df},
                    "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8"}},
                    "yAxis": [
                        {"type": "value", "name": "Cases", "axisLabel": {"color": "#94a3b8"}},
                        {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                    ],
                    "series": [
                        {"type": "bar", "name": "OPD Cases", "encode": {"x": "Month", "y": "OPD Cases"}, "itemStyle": {"color": "#f59e0b"}},
                        {"type": "bar", "name": "Hospital Admissions", "encode": {"x": "Month", "y": "Hospital Admissions"}, "itemStyle": {"color": "#ef4444"}},
                        {"type": "line", "name": "Mean Max (°C)", "yAxisIndex": 1, "smooth": True, "encode": {"x": "Month", "y": "Mean Max (°C)"}, "itemStyle": {"color": "#2dd4bf"}},
                    ],
                },
                height=310,
                alt="Monthly heat-related OPD cases and hospital admissions against mean max temperature",
            )
    with h_col2:
        with st.container(border=True, height="stretch"):
            st.subheader("Land Surface Temperature (UHI) by zone", anchor=False)
            lst_df = vuln_df[["Zone", "LST Offset"]].copy()
            lst_df["ZoneShort"] = lst_df["Zone"].str.split(" - ").str[1]
            lst_df["Est LST (°C)"] = (temp + 3.2 + lst_df["LST Offset"]).round(1)
            st.echarts_chart(
                {
                    "tooltip": {"trigger": "axis"},
                    "grid": {"left": 42, "right": 18, "top": 24, "bottom": 52},
                    "dataset": {"source": lst_df.sort_values(by="Est LST (°C)", ascending=False)},
                    "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "rotate": 25}},
                    "yAxis": {"type": "value", "name": "LST °C", "axisLabel": {"color": "#94a3b8"}},
                    "series": [{"type": "bar", "name": "LST (°C)", "encode": {"x": "ZoneShort", "y": "Est LST (°C)"}, "itemStyle": {"color": "#ef4444"}}],
                },
                height=310,
                alt="Estimated Land Surface Temperature across Nagpur NMC zones",
            )

with tab_cool:
    c_map, c_tbl = st.columns([1.2, 1], gap="small")
    with c_map:
        with st.container(border=True, height="stretch"):
            st.subheader("Emergency cooling centres map", anchor=False)
            map_func = getattr(px, "scatter_map", getattr(px, "scatter_mapbox", None))
            fig_cool = map_func(
                cool_df,
                lat="lat",
                lon="lon",
                hover_name="Centre",
                hover_data=["Zone", "Capacity", "Status"],
                color="Status",
                size="Capacity",
                size_max=18,
                zoom=11.3,
                center={"lat": 21.1458, "lon": 79.0882},
            )
            fig_cool.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=320)
            st.plotly_chart(fig_cool, alt="Map of Nagpur NMC emergency cooling centres")
    with c_tbl:
        with st.container(border=True, height="stretch"):
            st.subheader("Priority intervention & cooling centres", anchor=False)
            st.dataframe(vuln_df[["Zone", "Vulnerable Pop", "Outdoor Workers (%)", "Priority"]], hide_index=True, height=160, alt="Vulnerable population priority zones")
            st.dataframe(cool_df[["Centre", "Zone", "Capacity", "Status"]], hide_index=True, height=150, alt="NMC cooling centres directory")
