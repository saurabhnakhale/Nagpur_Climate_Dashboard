import streamlit as st
import pandas as pd
import plotly.express as px

from climate_core import (
    NAGPUR_ZONES_WARDS,
    load_active_location_feeds,
    parse_hourly_df,
)

sel_zone, sel_ward, sel_loc, current_w, forecast_w, _, om_w, _ = load_active_location_feeds()

if not current_w:
    st.error("Unable to retrieve baseline telemetry for risk mapping.", icon=":material/cloud_off:")
    st.stop()

base_temp = float(current_w.get("main", {}).get("temp", 0))
h_df = parse_hourly_df(om_w, forecast_w)
base_rain = float(h_df.head(120)["Rainfall (mm)"].sum()) if not h_df.empty else 0.0

rows = []
for z_name, wards_dict in NAGPUR_ZONES_WARDS.items():
    if z_name == "All Nagpur (City Core)":
        continue
    for w_name, meta in wards_dict.items():
        w_temp = round(base_temp + meta["temp_offset"], 1)
        w_rain = round(max(0.0, base_rain + meta["rain_offset"]), 1)
        if meta["drainage_risk"] == "Critical" or w_temp >= 43.0:
            comp_risk = "Critical"
        elif meta["drainage_risk"] == "High" or w_temp >= 40.0:
            comp_risk = "High"
        elif meta["drainage_risk"] == "Moderate":
            comp_risk = "Moderate"
        else:
            comp_risk = "Low"

        rows.append({
            "Zone": z_name,
            "Ward": w_name,
            "Land Use": meta["type"],
            "Elevation (m)": meta["elev_m"],
            "Temperature (°C)": w_temp,
            "5D Rain (mm)": w_rain,
            "Drainage Risk": meta["drainage_risk"],
            "Composite Risk": comp_risk,
            "Marker Size": max(6.0, w_rain + 8.0),
            "lat": meta["lat"],
            "lon": meta["lon"],
        })

z_df = pd.DataFrame(rows)
view_df = z_df if sel_zone == "All Nagpur (City Core)" else z_df[z_df["Zone"] == sel_zone]

st.caption(f"Ward-level climate risk & live weather radar / satellite tracking across **{len(view_df)} Nagpur wards** (active: **{sel_ward}**)")

hottest_row = view_df.sort_values(by="Temperature (°C)", ascending=False).iloc[0]
coolest_row = view_df.sort_values(by="Temperature (°C)", ascending=True).iloc[0]
crit_count = int((view_df["Composite Risk"].isin(["Critical", "High"])).sum())
uhi_delta = round(float(view_df["Temperature (°C)"].max() - view_df["Temperature (°C)"].min()), 1)

with st.grid(4, min_column_width=200, gap="small"):
    st.metric("Peak thermal ward", hottest_row["Ward"], delta=f"{hottest_row['Temperature (°C)']:.1f} °C", delta_color="red" if hottest_row["Temperature (°C)"] >= 40 else "orange", icon=":material/local_fire_department:", border=True, height="stretch")
    st.metric("Coolest ward", coolest_row["Ward"], delta=f"{coolest_row['Temperature (°C)']:.1f} °C", delta_color="green", icon=":material/park:", border=True, height="stretch")
    st.metric("High / critical risk wards", f"{crit_count} / {len(view_df)}", delta="Flood & heat exposure", delta_color="red" if crit_count > 5 else "yellow", icon=":material/warning:", border=True, height="stretch")
    st.metric("Urban heat island delta", f"{uhi_delta:.1f} °C", delta="Spatial variance", delta_color="orange" if uhi_delta >= 3.5 else "blue", icon=":material/thermostat:", border=True, height="stretch")

map_mode = st.segmented_control(
    "Geospatial view mode",
    ["Ward Risk Map", "Live Weather Radar & Satellite"],
    default="Ward Risk Map",
    label_visibility="collapsed",
) or "Ward Risk Map"

if map_mode == "Ward Risk Map":
    col_map, col_table = st.columns([1.35, 1], gap="small")
    with col_map:
        with st.container(border=True, height="stretch"):
            layer_choice = st.segmented_control(
                "Map metric layer",
                ["Temperature (°C)", "5D Rain (mm)", "Composite Risk"],
                default="Temperature (°C)",
                label_visibility="collapsed",
            ) or "Temperature (°C)"

            map_func = getattr(px, "scatter_map", getattr(px, "scatter_mapbox", None))
            center_lat = float(view_df["lat"].mean())
            center_lon = float(view_df["lon"].mean())
            zoom_lvl = 11.3 if sel_zone == "All Nagpur (City Core)" else 12.6

            fig_map = map_func(
                view_df,
                lat="lat",
                lon="lon",
                hover_name="Ward",
                hover_data=["Zone", "Land Use", "Temperature (°C)", "5D Rain (mm)", "Drainage Risk", "Composite Risk"],
                color=layer_choice,
                size="Marker Size",
                color_continuous_scale="Turbo" if layer_choice != "5D Rain (mm)" else "Blues",
                size_max=20,
                zoom=zoom_lvl,
                center={"lat": center_lat, "lon": center_lon},
            )
            fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=410)
            st.plotly_chart(fig_map, alt="Interactive ward-level Nagpur climate risk map")

    with col_table:
        with st.container(border=True, height="stretch"):
            st.subheader("Zone & ward risk ledger", anchor=False)
            st.dataframe(
                view_df[["Ward", "Zone", "Temperature (°C)", "5D Rain (mm)", "Drainage Risk", "Composite Risk"]],
                hide_index=True,
                height=410,
                alt="Zone and ward climate risk classification table",
            )

else:
    with st.container(border=True):
        overlay_choice = st.segmented_control(
            "Satellite & radar overlay",
            ["radar", "satellite", "rain", "wind", "temp"],
            default="radar",
            format_func=lambda x: {"radar": "Weather Radar", "satellite": "Satellite Imagery", "rain": "Precipitation", "wind": "Wind Streams", "temp": "Temperature"}[x],
        ) or "radar"

        lat, lon = sel_loc["lat"], sel_loc["lon"]
        windy_url = (
            f"https://embed.windy.com/embed2.html?lat={lat:.3f}&lon={lon:.3f}"
            f"&detailLat={lat:.3f}&detailLon={lon:.3f}&width=900&height=460&zoom=7"
            f"&level=surface&overlay={overlay_choice}&product=ecmwf&menu=&message=true"
            f"&marker=true&calendar=now&pressure=true&type=map&location=coordinates"
            f"&detail=&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1"
        )
        st.iframe(windy_url, height=460, alt=f"Live weather radar and satellite imagery centered on {sel_ward}")
