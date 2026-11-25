import streamlit as st
import pandas as pd
import plotly.express as px

from climate_core import (
    MAHARASHTRA_CITIES,
    INDIA_METROS,
    get_key,
    fetch_weather_with_ts,
    fetch_air_with_ts,
    compute_indian_cpcb_aqi,
)

api_key = get_key()

st.caption("Simultaneous synoptic comparison across Maharashtra districts and All-India metro corridors.")

scope_tab = st.segmented_control(
    "Regional benchmark scale",
    ["Maharashtra State", "All-India Metros"],
    default="Maharashtra State",
    label_visibility="collapsed",
) or "Maharashtra State"

if scope_tab == "Maharashtra State":
    state_rows = []
    for city, meta in MAHARASHTRA_CITIES.items():
        w, _ = fetch_weather_with_ts(meta["lat"], meta["lon"], api_key)
        a, _ = fetch_air_with_ts(meta["lat"], meta["lon"], api_key)
        if w:
            m = w.get("main", {})
            air_c = a.get("list", [{}])[0].get("components", {}) if a else {}
            cpcb = compute_indian_cpcb_aqi(air_c)
            state_rows.append({
                "City": city,
                "Region": meta["region"],
                "Temperature (°C)": round(float(m.get("temp", 0)), 1),
                "Feels Like (°C)": round(float(m.get("feels_like", 0)), 1),
                "Humidity (%)": int(m.get("humidity", 0)),
                "Wind (km/h)": round(float(w.get("wind", {}).get("speed", 0) or 0) * 3.6, 1),
                "CPCB AQI": cpcb["aqi"] if cpcb["aqi"] is not None else 0,
                "AQI Category": cpcb["category"],
                "Condition": w.get("weather", [{}])[0].get("description", "").title(),
                "lat": meta["lat"],
                "lon": meta["lon"],
            })
    s_df = pd.DataFrame(state_rows)

    if not s_df.empty:
        hottest = s_df.sort_values(by="Temperature (°C)", ascending=False).iloc[0]
        nag_t = s_df.loc[s_df["City"] == "Nagpur", "Temperature (°C)"].values[0]
        mum_t = s_df.loc[s_df["City"] == "Mumbai", "Temperature (°C)"].values[0]
        cleanest = s_df[s_df["CPCB AQI"] > 0].sort_values(by="CPCB AQI", ascending=True)
        clean_row = cleanest.iloc[0] if not cleanest.empty else hottest

        with st.grid(4, min_column_width=200, gap="small"):
            st.metric("Monitored hubs", f"{len(s_df)} Cities", delta="4 divisions", delta_color="blue", icon=":material/location_city:", border=True, height="stretch")
            st.metric("Thermal peak", hottest["City"], delta=f"{hottest['Temperature (°C)']:.1f} °C", delta_color="red" if hottest["Temperature (°C)"] >= 40 else "orange", icon=":material/thermostat:", border=True, height="stretch")
            st.metric("Nagpur vs Mumbai", f"{nag_t - mum_t:+.1f} °C", delta="Vidarbha vs Konkan", delta_color="orange" if abs(nag_t - mum_t) >= 4 else "blue", icon=":material/compare_arrows:", border=True, height="stretch")
            st.metric("Cleanest air hub", clean_row["City"], delta=f"AQI {clean_row['CPCB AQI']}", delta_color="green", icon=":material/air:", border=True, height="stretch")

        c1, c2 = st.columns(2, gap="small")
        with c1:
            with st.container(border=True, height="stretch"):
                st.subheader("Temperature across districts", anchor=False)
                st.echarts_chart(
                    {
                        "tooltip": {"trigger": "axis"},
                        "grid": {"left": 42, "right": 16, "top": 24, "bottom": 56},
                        "dataset": {"source": s_df.sort_values(by="Temperature (°C)", ascending=False)},
                        "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "rotate": 25}},
                        "yAxis": {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                        "series": [{"type": "bar", "encode": {"x": "City", "y": "Temperature (°C)"}, "itemStyle": {"color": "#f59e0b"}}],
                    },
                    height=290,
                    alt="Temperature comparison across Maharashtra cities",
                )
        with c2:
            with st.container(border=True, height="stretch"):
                st.subheader("CPCB AQI across districts", anchor=False)
                st.echarts_chart(
                    {
                        "tooltip": {"trigger": "axis"},
                        "grid": {"left": 42, "right": 16, "top": 24, "bottom": 56},
                        "dataset": {"source": s_df.sort_values(by="CPCB AQI", ascending=False)},
                        "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "rotate": 25}},
                        "yAxis": {"type": "value", "name": "AQI", "axisLabel": {"color": "#94a3b8"}},
                        "series": [{"type": "bar", "encode": {"x": "City", "y": "CPCB AQI"}, "itemStyle": {"color": "#2dd4bf"}}],
                    },
                    height=290,
                    alt="CPCB AQI comparison across Maharashtra cities",
                )

        with st.container(border=True):
            st.subheader("Maharashtra state ledger", anchor=False)
            st.dataframe(
                s_df[["City", "Region", "Temperature (°C)", "Feels Like (°C)", "Humidity (%)", "Wind (km/h)", "CPCB AQI", "AQI Category", "Condition"]],
                hide_index=True,
                alt="Maharashtra state multi-city climate data table",
            )

else:
    in_rows = []
    for city, meta in INDIA_METROS.items():
        w, _ = fetch_weather_with_ts(meta["lat"], meta["lon"], api_key)
        a, _ = fetch_air_with_ts(meta["lat"], meta["lon"], api_key)
        if w:
            m = w.get("main", {})
            air_c = a.get("list", [{}])[0].get("components", {}) if a else {}
            cpcb = compute_indian_cpcb_aqi(air_c)
            in_rows.append({
                "City": city,
                "State": meta["state"],
                "Zone": meta["zone"],
                "Temperature (°C)": round(float(m.get("temp", 0)), 1),
                "Humidity (%)": int(m.get("humidity", 0)),
                "CPCB AQI": cpcb["aqi"] if cpcb["aqi"] is not None else 0,
                "AQI Category": cpcb["category"],
                "Condition": w.get("weather", [{}])[0].get("description", "").title(),
                "lat": meta["lat"],
                "lon": meta["lon"],
            })
    in_df = pd.DataFrame(in_rows)

    if not in_df.empty:
        avg_t = round(float(in_df["Temperature (°C)"].mean()), 1)
        nag_t = float(in_df.loc[in_df["City"] == "Nagpur", "Temperature (°C)"].values[0])
        hot_city = in_df.sort_values(by="Temperature (°C)", ascending=False).iloc[0]
        worst_aqi = in_df.sort_values(by="CPCB AQI", ascending=False).iloc[0]

        with st.grid(4, min_column_width=200, gap="small"):
            st.metric("National metro avg", f"{avg_t:.1f} °C", delta=f"{len(in_df)} metros", delta_color="blue", icon=":material/public:", border=True, height="stretch")
            st.metric("Nagpur vs national", f"{nag_t - avg_t:+.1f} °C", delta=f"Nagpur {nag_t:.1f} °C", delta_color="orange" if nag_t > avg_t else "green", icon=":material/compare_arrows:", border=True, height="stretch")
            st.metric("Hottest metro", hot_city["City"], delta=f"{hot_city['Temperature (°C)']:.1f} °C", delta_color="red" if hot_city["Temperature (°C)"] >= 40 else "orange", icon=":material/local_fire_department:", border=True, height="stretch")
            st.metric("Highest AQI hotspot", worst_aqi["City"], delta=f"AQI {worst_aqi['CPCB AQI']}", delta_color="red" if worst_aqi["CPCB AQI"] > 200 else "yellow", icon=":material/air:", border=True, height="stretch")

        c1, c2 = st.columns(2, gap="small")
        with c1:
            with st.container(border=True, height="stretch"):
                st.subheader("Metro temperature ranking", anchor=False)
                st.echarts_chart(
                    {
                        "tooltip": {"trigger": "axis"},
                        "grid": {"left": 42, "right": 16, "top": 24, "bottom": 56},
                        "dataset": {"source": in_df.sort_values(by="Temperature (°C)", ascending=False)},
                        "xAxis": {"type": "category", "axisLabel": {"color": "#94a3b8", "rotate": 25}},
                        "yAxis": {"type": "value", "name": "°C", "axisLabel": {"color": "#94a3b8"}},
                        "series": [{"type": "bar", "encode": {"x": "City", "y": "Temperature (°C)"}, "itemStyle": {"color": "#3b82f6"}}],
                    },
                    height=300,
                    alt="All-India metro temperature ranking",
                )
        with c2:
            with st.container(border=True, height="stretch"):
                st.subheader("National AQI distribution", anchor=False)
                map_func = getattr(px, "scatter_map", getattr(px, "scatter_mapbox", None))
                fig_in = map_func(
                    in_df,
                    lat="lat",
                    lon="lon",
                    hover_name="City",
                    hover_data=["State", "Temperature (°C)", "CPCB AQI", "Condition"],
                    color="CPCB AQI",
                    size="Temperature (°C)",
                    color_continuous_scale="Viridis",
                    size_max=18,
                    zoom=3.6,
                    center={"lat": 22.0, "lon": 79.0},
                )
                fig_in.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
                st.plotly_chart(fig_in, alt="All-India metro climate and AQI map")

        with st.container(border=True):
            st.subheader("National comparative matrix", anchor=False)
            st.dataframe(
                in_df[["City", "State", "Zone", "Temperature (°C)", "Humidity (%)", "CPCB AQI", "AQI Category", "Condition"]],
                hide_index=True,
                alt="All-India metro comparative climate table",
            )
