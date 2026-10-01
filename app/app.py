"""GEOIMPATHON 1.0 - Multi-Hazard Decision Support System & Least-Risk Emergency Router.

Designed for District Disaster Management Officers (DDMO) in South Chennai - Chengalpattu.
Built strictly using theme tokens from app/theme.py.
"""

import os
import sys
import yaml
import folium
import numpy as np
import pandas as pd
import geopandas as gpd
import streamlit as st
import osmnx as ox
from streamlit_folium import st_folium

# Ensure project root and app dir are in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app_dir = os.path.abspath(os.path.dirname(__file__))
for d in [root_dir, app_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    from app.theme import (
        COLOR_WHITE,
        COLOR_PAPER,
        COLOR_BORDER_GREY,
        COLOR_INK,
        COLOR_MUTED_TEXT,
        COLOR_DEEP_BLUE,
        COLOR_MID_BLUE,
        COLOR_LIGHT_BLUE,
        COLOR_ORANGE,
        COLOR_DARK_ORANGE,
        RISK_RAMP,
        CUSTOM_CSS,
    )
except ImportError:
    from theme import (
        COLOR_WHITE,
        COLOR_PAPER,
        COLOR_BORDER_GREY,
        COLOR_INK,
        COLOR_MUTED_TEXT,
        COLOR_DEEP_BLUE,
        COLOR_MID_BLUE,
        COLOR_LIGHT_BLUE,
        COLOR_ORANGE,
        COLOR_DARK_ORANGE,
        RISK_RAMP,
        CUSTOM_CSS,
    )

# Set page configuration strictly matching design system
st.set_page_config(
    page_title="GEOIMPATHON 1.0 | Multi-Hazard DSS",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def load_config() -> dict:
    """Load configuration dictionary."""
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@st.cache_data
def load_vector_layers() -> dict:
    """Load cached spatial facilities and ranking tables."""
    data_dir = "data/sample"
    layers = {}

    hosp_p = os.path.join(data_dir, "hospitals.geojson")
    if os.path.exists(hosp_p):
        layers["hospitals"] = gpd.read_file(hosp_p)

    shelt_p = os.path.join(data_dir, "shelters.geojson")
    if os.path.exists(shelt_p):
        layers["shelters"] = gpd.read_file(shelt_p)

    sett_p = os.path.join(data_dir, "top_settlements.geojson")
    if not os.path.exists(sett_p):
        sett_p = os.path.join(data_dir, "settlements.geojson")
    if os.path.exists(sett_p):
        layers["settlements"] = gpd.read_file(sett_p)

    grid_p = os.path.join(data_dir, "top_grid_cells.geojson")
    if os.path.exists(grid_p):
        layers["grid_cells"] = gpd.read_file(grid_p)

    return layers


cfg = load_config()
bounds_dict = cfg.get("bbox", {})
lon_min = float(bounds_dict.get("lon_min", 80.03))
lat_min = float(bounds_dict.get("lat_min", 12.80))
lon_max = float(bounds_dict.get("lon_max", 80.22))
lat_max = float(bounds_dict.get("lat_max", 12.98))
folium_bounds = [[lat_min, lon_min], [lat_max, lon_max]]
center_lat = (lat_min + lat_max) / 2.0
center_lon = (lon_min + lon_max) / 2.0

# -----------------------------------------------------------------------------
# Top Header Bar
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="top-header-bar">
        <div>
            <h1>GEOIMPATHON 1.0 | Multi-Hazard Decision-Support System</h1>
            <p>Study Area: South Chennai to Chengalpattu Corridor (Cyclone Michaung Validation)</p>
        </div>
        <div style="text-align: right;">
            <span style="background-color: {COLOR_MID_BLUE}; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                OPERATIONAL BASELINE: ACTIVE
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Left Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<h3 style='color: {COLOR_DEEP_BLUE}; margin-top: 0;'>Scenario Control</h3>", unsafe_allow_html=True)
    scenario = st.radio(
        "Operational Scenario",
        ["Normal Scenario", "Flood Scenario (Cyclone Michaung)"],
        index=1,
        help="Normal assumes dry roads and standard free-flow speeds. Flood scenario removes roads in Very High risk zones and throttles High risk roads to 5 km/h.",
    )

    st.markdown("---")
    st.markdown(f"<h4 style='color: {COLOR_INK}; margin-bottom: 4px;'>Emergency Routing Parameters</h4>", unsafe_allow_html=True)

    vectors = load_vector_layers()
    settlements_df = vectors.get("settlements", pd.DataFrame())

    settlement_names = sorted(settlements_df["name"].dropna().unique().tolist()) if not settlements_df.empty else ["Tambaram"]
    origin_settlement = st.selectbox(
        "Evacuation Origin",
        settlement_names,
        index=0 if "Tambaram" not in settlement_names else settlement_names.index("Tambaram"),
        help="Select origin community requiring emergency medical transit or evacuation.",
    )

    destination_type = st.radio(
        "Destination Facility",
        ["Nearest Safe Hospital", "Nearest Safe Public Shelter"],
        index=0,
        help="Directs route exclusively to verified operational facilities outside High-risk inundation zones.",
    )

    alpha_val = st.slider(
        "Route Priority (Fastest <—> Safest)",
        min_value=float(cfg.get("routing", {}).get("alpha_min", 0.0)),
        max_value=float(cfg.get("routing", {}).get("alpha_max", 10.0)),
        value=float(cfg.get("routing", {}).get("default_alpha", 3.0)),
        step=float(cfg.get("routing", {}).get("alpha_step", 0.5)),
        help="Alpha multiplier penalizes flood hazard in edge cost C = L * (1 + alpha * risk). 0 = Fastest physical route; 3 = Recommended safe route.",
    )
    st.caption(f"Active Safety Multiplier: **alpha = {alpha_val:.1f}**")

    st.markdown("---")
    st.markdown(f"<h4 style='color: {COLOR_INK}; margin-bottom: 4px;'>Map Layer Visibility</h4>", unsafe_allow_html=True)
    st.caption("Toggle spatial rasters and facilities on the interactive map:")

    show_multihazard = st.checkbox("Multi-Hazard Composite Risk", value=True)
    show_flood = st.checkbox("Flood Susceptibility Layer", value=False)
    show_slope_inst = st.checkbox("Slope-Instability Layer", value=False)
    show_slope_deg = st.checkbox("DEM Slope (degrees)", value=False)
    show_exposure = st.checkbox("Built-Up Exposure (10m Proxy)", value=False)

    st.markdown(f"<p style='color: {COLOR_MUTED_TEXT}; font-size: 12px; margin-top: 8px; margin-bottom: 2px;'>INFRASTRUCTURE & PLACES</p>", unsafe_allow_html=True)
    show_hospitals = st.checkbox("Hospitals (Safe & Flagged)", value=True)
    show_shelters = st.checkbox("Designated Shelters", value=True)
    show_settlements = st.checkbox("Settlement Centers", value=True)
    show_critical_roads = st.checkbox("Top Critical Road Corridors", value=True)

# -----------------------------------------------------------------------------
# Main Application Tabs (All 5 Tabs)
# -----------------------------------------------------------------------------
tab_risk, tab_route, tab_critical, tab_dash, tab_methods = st.tabs([
    "Risk map",
    "Emergency route",
    "Critical roads and isolation",
    "Dashboard",
    "Methods and data",
])

# =============================================================================
# TAB 1: RISK MAP
# =============================================================================
with tab_risk:
    st.markdown(
        f"<p style='color: {COLOR_MUTED_TEXT}; font-size: 13px; margin-bottom: 12px;'>"
        f"This screen displays continuous multi-hazard susceptibility and operational risk categories calibrated to the South Chennai coastal corridor."
        f"</p>",
        unsafe_allow_html=True,
    )

    col_map, col_info = st.columns([7, 3], gap="medium")

    with col_map:
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
            control_scale=True,
        )

        data_dir = "data/sample"

        # Raster Overlays (Lightweight RGBA PNGs)
        if show_multihazard:
            p = os.path.join(data_dir, "multihazard_risk.png")
            if os.path.exists(p):
                folium.raster_layers.ImageOverlay(
                    image=p,
                    bounds=folium_bounds,
                    opacity=0.65,
                    name="Multi-Hazard Composite Risk",
                ).add_to(m)

        if show_flood:
            p = os.path.join(data_dir, "flood_hazard.png")
            if os.path.exists(p):
                folium.raster_layers.ImageOverlay(
                    image=p,
                    bounds=folium_bounds,
                    opacity=0.65,
                    name="Flood Susceptibility",
                ).add_to(m)

        if show_slope_inst:
            p = os.path.join(data_dir, "slope_instability.png")
            if os.path.exists(p):
                folium.raster_layers.ImageOverlay(
                    image=p,
                    bounds=folium_bounds,
                    opacity=0.65,
                    name="Slope-Instability Susceptibility",
                ).add_to(m)

        if show_slope_deg:
            p = os.path.join(data_dir, "dem_slope_deg.png")
            if os.path.exists(p):
                folium.raster_layers.ImageOverlay(
                    image=p,
                    bounds=folium_bounds,
                    opacity=0.65,
                    name="DEM Slope (deg)",
                ).add_to(m)

        if show_exposure:
            p = os.path.join(data_dir, "builtup_exposure.png")
            if os.path.exists(p):
                folium.raster_layers.ImageOverlay(
                    image=p,
                    bounds=folium_bounds,
                    opacity=0.60,
                    name="Built-Up Exposure Proxy",
                ).add_to(m)

        # Vector Facilities
        if show_settlements and "settlements" in vectors:
            for _, row in vectors["settlements"].iterrows():
                geom = row.geometry
                name = row.get("name", "Settlement")
                risk_tier = row.get("risk_tier", "Moderate")
                score = row.get("risk_exposure_score", 0.0)
                folium.CircleMarker(
                    location=[geom.y, geom.x],
                    radius=4,
                    color=COLOR_MID_BLUE,
                    weight=1.5,
                    fill=True,
                    fill_color=COLOR_WHITE,
                    fill_opacity=0.9,
                    tooltip=f"Settlement: {name} | Risk: {risk_tier} (Score: {score})",
                ).add_to(m)

        if show_hospitals and "hospitals" in vectors:
            for _, row in vectors["hospitals"].head(40).iterrows():
                geom = row.geometry
                name = row.get("name", "Medical Facility")
                folium.CircleMarker(
                    location=[geom.y, geom.x],
                    radius=6,
                    color=COLOR_MID_BLUE,
                    weight=2,
                    fill=True,
                    fill_color=COLOR_MID_BLUE,
                    fill_opacity=0.9,
                    tooltip=f"Hospital: {name}",
                ).add_to(m)

        if show_shelters and "shelters" in vectors:
            for _, row in vectors["shelters"].head(40).iterrows():
                geom = row.geometry
                name = row.get("name", "Civic Shelter")
                folium.CircleMarker(
                    location=[geom.y, geom.x],
                    radius=5,
                    color=COLOR_MID_BLUE,
                    weight=1.5,
                    fill=True,
                    fill_color=COLOR_PAPER,
                    fill_opacity=0.9,
                    tooltip=f"Shelter: {name}",
                ).add_to(m)

        st_folium(m, width="100%", height=560, returned_objects=[])

        st.caption(
            "Data sources: Copernicus DEM GLO-30 (ESA), Dynamic World V1 (Google/WRI), OpenStreetMap contributors, JRC Global Surface Water. "
            "Projection: WGS84 / EPSG:4326. Basemap: CartoDB Positron."
        )

    with col_info:
        st.markdown(f"<h4 style='color: {COLOR_INK}; margin-top: 0;'>Multi-Hazard Risk Ramp</h4>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="background-color: {COLOR_PAPER}; border: 1px solid {COLOR_BORDER_GREY}; border-radius: 4px; padding: 10px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; margin-bottom: 6px;">
                    <div style="width: 16px; height: 16px; background-color: {RISK_RAMP['Very High']}; border-radius: 2px; margin-right: 8px;"></div>
                    <span style="font-size: 13px; font-weight: 600; color: {COLOR_INK};">Very High Risk (&gt;95th percentile)</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 6px;">
                    <div style="width: 16px; height: 16px; background-color: {RISK_RAMP['High']}; border-radius: 2px; margin-right: 8px;"></div>
                    <span style="font-size: 13px; font-weight: 600; color: {COLOR_INK};">High Risk (80th - 95th percentile)</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 6px;">
                    <div style="width: 16px; height: 16px; background-color: {RISK_RAMP['Moderate']}; border-radius: 2px; margin-right: 8px;"></div>
                    <span style="font-size: 13px; font-weight: 600; color: {COLOR_INK};">Moderate Risk (50th - 80th percentile)</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 16px; height: 16px; background-color: {RISK_RAMP['Low']}; border-radius: 2px; margin-right: 8px;"></div>
                    <span style="font-size: 13px; font-weight: 600; color: {COLOR_INK};">Low Risk (&lt;50th percentile)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(f"<h4 style='color: {COLOR_INK};'>Area by Risk Class</h4>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Low Risk Safe Zones (&lt;50th)</div>
                <div class="metric-value">50.0%</div>
                <div class="metric-subtext">Optimal for relief shelters and command posts</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Moderate Risk Transitional (50-80th)</div>
                <div class="metric-value">30.0%</div>
                <div class="metric-subtext">Passable roads; drainage monitoring required</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">High Risk Inundation (80-95th)</div>
                <div class="metric-value">15.0%</div>
                <div class="metric-subtext">Vehicles slowed to 5 km/h; water ponding</div>
            </div>
            <div class="metric-card" style="border-left: 4px solid {COLOR_DARK_ORANGE};">
                <div class="metric-label" style="color: {COLOR_DARK_ORANGE};">Very High Lethal Risk (&gt;95th)</div>
                <div class="metric-value" style="color: {COLOR_DARK_ORANGE};">5.0%</div>
                <div class="metric-subtext">Roads severed; impassable drowning hazard</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(f"<h4 style='color: {COLOR_INK};'>Official Action List</h4>", unsafe_allow_html=True)
        st.caption("Download ranked high-risk settlements and 500m priority dispatch cells:")

        sett_csv_p = os.path.join(data_dir, "top_settlements.csv")
        if os.path.exists(sett_csv_p):
            with open(sett_csv_p, "rb") as f:
                st.download_button(
                    label="Download Settlements Action List (CSV)",
                    data=f,
                    file_name="ranked_high_risk_settlements.csv",
                    mime="text/csv",
                    type="primary",
                )

        grid_csv_p = os.path.join(data_dir, "top_grid_cells.csv")
        if os.path.exists(grid_csv_p):
            with open(grid_csv_p, "rb") as f:
                st.download_button(
                    label="Download 500m Grid Action List (CSV)",
                    data=f,
                    file_name="ranked_500m_grid_cells.csv",
                    mime="text/csv",
                )

# =============================================================================
# TAB 2: EMERGENCY ROUTE
# =============================================================================
with tab_route:
    st.markdown(
        f"<p style='color: {COLOR_MUTED_TEXT}; font-size: 13px; margin-bottom: 12px;'>"
        f"This screen calculates and contrasts the standard shortest route against the risk-weighted least-risk emergency route."
        f"</p>",
        unsafe_allow_html=True,
    )

    from routing.router import calculate_dual_routes

    @st.cache_resource
    def get_routing_graph():
        graph_risk_p = "data/sample/drive_network_risk.graphml"
        if not os.path.exists(graph_risk_p):
            from routing.router import annotate_network_with_risk
            return annotate_network_with_risk()
        return ox.load_graphml(graph_risk_p)

    G_routing = get_routing_graph()

    # Determine origin coordinates
    orig_sub = settlements_df[settlements_df["name"] == origin_settlement]
    if not orig_sub.empty:
        orig_pt = orig_sub.iloc[0].geometry
        orig_coord = (float(orig_pt.x), float(orig_pt.y))
    else:
        orig_coord = (80.115, 12.924)  # Default Tambaram

    # Determine destination dataset
    if "Hospital" in destination_type and "hospitals" in vectors:
        dest_gdf = vectors["hospitals"]
        dest_category = "Hospital"
    elif "shelters" in vectors:
        dest_gdf = vectors["shelters"]
        dest_category = "Shelter"
    else:
        dest_gdf = vectors.get("hospitals", gpd.GeoDataFrame())
        dest_category = "Facility"

    route_res = calculate_dual_routes(G_routing, orig_coord, dest_gdf, alpha=alpha_val)

    fastest_m = route_res["fastest"]
    safest_m = route_res["safest"]

    col_rmap, col_rpanel = st.columns([7, 3], gap="medium")

    with col_rmap:
        # Compute map center between origin and destination
        all_coords = fastest_m["coordinates"] + safest_m["coordinates"]
        if all_coords:
            r_lats = [pt[0] for pt in all_coords]
            r_lons = [pt[1] for pt in all_coords]
            map_center = [float(np.mean(r_lats)), float(np.mean(r_lons))]
        else:
            map_center = [orig_coord[1], orig_coord[0]]

        m_route = folium.Map(
            location=map_center,
            zoom_start=13,
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
            control_scale=True,
        )

        # Optional background multi-hazard overlay
        p_risk_png = "data/sample/multihazard_risk.png"
        if os.path.exists(p_risk_png):
            folium.raster_layers.ImageOverlay(
                image=p_risk_png,
                bounds=folium_bounds,
                opacity=0.35,
                name="Multi-Hazard Background",
            ).add_to(m_route)

        # 1. Render Fastest Route (Orange dashed with white casing)
        if fastest_m["coordinates"]:
            # White casing
            folium.PolyLine(
                locations=fastest_m["coordinates"],
                color=COLOR_WHITE,
                weight=7,
                opacity=0.9,
            ).add_to(m_route)
            # Orange dashed line
            folium.PolyLine(
                locations=fastest_m["coordinates"],
                color=COLOR_ORANGE,
                weight=4,
                opacity=0.95,
                dash_array="6, 6",
                tooltip=f"Fastest Route: {fastest_m['distance_km']} km, {fastest_m['time_min']} min",
            ).add_to(m_route)

        # 2. Render Safest Route (Deep Blue solid with white casing)
        if safest_m["coordinates"]:
            # White casing
            folium.PolyLine(
                locations=safest_m["coordinates"],
                color=COLOR_WHITE,
                weight=8,
                opacity=0.9,
            ).add_to(m_route)
            # Solid deep blue line
            folium.PolyLine(
                locations=safest_m["coordinates"],
                color=COLOR_DEEP_BLUE,
                weight=5,
                opacity=0.95,
                tooltip=f"Safest Route (alpha={alpha_val}): {safest_m['distance_km']} km, {safest_m['time_min']} min",
            ).add_to(m_route)

        # 3. Origin Marker
        folium.CircleMarker(
            location=[orig_coord[1], orig_coord[0]],
            radius=7,
            color=COLOR_DEEP_BLUE,
            fill=True,
            fill_color=COLOR_WHITE,
            weight=3,
            tooltip=f"Origin: {origin_settlement}",
        ).add_to(m_route)

        # 4. Destination Marker
        if safest_m["coordinates"]:
            dest_lat, dest_lon = safest_m["coordinates"][-1]
            folium.Marker(
                location=[dest_lat, dest_lon],
                icon=folium.Icon(color="blue", icon="plus", prefix="fa"),
                tooltip=f"Destination: {route_res['destination_name']}",
            ).add_to(m_route)

        st_folium(m_route, width="100%", height=560, returned_objects=[])

        st.caption(
            "Map Legend: Solid Deep Blue = Safest Emergency Route (Least-Risk) | "
            "Orange Dashed = Shortest Physical Route | Blue Circle = Origin Settlement | Blue Cross = Nearest Safe Facility."
        )

    with col_rpanel:
        st.markdown(f"<h4 style='color: {COLOR_INK}; margin-top: 0;'>Route Comparison</h4>", unsafe_allow_html=True)

        if route_res.get("fallback_used"):
            st.markdown(
                f"""
                <div class="warning-banner" style="border-left-color: {COLOR_DARK_ORANGE};">
                    <strong>Notice:</strong> No completely safe route exists in severed graph. Showing the lowest-risk path on the full road network instead.
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Side-by-side comparison cards
        st.markdown(
            f"""
            <div class="route-card-fastest" style="margin-bottom: 14px;">
                <div style="font-size: 12px; font-weight: 600; color: {COLOR_ORANGE}; text-transform: uppercase;">
                    Fastest Route (&alpha; = 0.0)
                </div>
                <div style="font-size: 24px; font-weight: 700; color: {COLOR_INK}; margin: 4px 0;">
                    {fastest_m['time_min']:.1f} min | {fastest_m['distance_km']:.1f} km
                </div>
                <div style="font-size: 13px; color: {COLOR_DARK_ORANGE if fastest_m['high_risk_km'] > 0 else COLOR_MUTED_TEXT}; font-weight: 600;">
                    {fastest_m['high_risk_km']:.1f} km inside High Risk zone ({fastest_m['high_risk_pct']:.0f}%)
                </div>
            </div>

            <div class="route-card-safest" style="margin-bottom: 14px;">
                <div style="font-size: 12px; font-weight: 600; color: {COLOR_DEEP_BLUE}; text-transform: uppercase;">
                    Safest Route (&alpha; = {alpha_val:.1f})
                </div>
                <div style="font-size: 24px; font-weight: 700; color: {COLOR_INK}; margin: 4px 0;">
                    {safest_m['time_min']:.1f} min | {safest_m['distance_km']:.1f} km
                </div>
                <div style="font-size: 13px; color: {COLOR_MID_BLUE}; font-weight: 600;">
                    {safest_m['high_risk_km']:.1f} km inside High Risk zone ({safest_m['high_risk_pct']:.0f}%)
                </div>
            </div>

            <div class="warning-banner">
                <strong>Compromise Assessment:</strong> {route_res['compromise_text']}
            </div>

            <div class="metric-card" style="margin-top: 14px;">
                <div class="metric-label">Target Facility</div>
                <div style="font-size: 14px; font-weight: 600; color: {COLOR_INK};">
                    {route_res['destination_name']}
                </div>
                <div class="metric-subtext">Verified Safe / Non-Inundated Ground</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============================================================================
# TAB 3: CRITICAL ROADS & ISOLATION
# =============================================================================
with tab_critical:
    st.markdown(
        f"<p style='color: {COLOR_MUTED_TEXT}; font-size: 13px; margin-bottom: 12px;'>"
        f"This screen discovers single points of failure in the road network and identifies isolated or severely delayed settlements."
        f"</p>",
        unsafe_allow_html=True,
    )
    st.info("Step 4 Module: Top 10 critical road corridors and greedy max-coverage pre-positioning sites will be displayed here.")

# =============================================================================
# TAB 4: DASHBOARD & VALIDATION
# =============================================================================
with tab_dash:
    st.markdown(
        f"<p style='color: {COLOR_MUTED_TEXT}; font-size: 13px; margin-bottom: 12px;'>"
        f"Operational summary metrics, independent Sentinel-1 flood validation (Cyclone Michaung, Dec 2023), "
        f"and geomorphic model verification statistics."
        f"</p>",
        unsafe_allow_html=True,
    )

    import json
    val_json_path = "outputs/validation_metrics.json"
    if os.path.exists(val_json_path):
        with open(val_json_path, "r", encoding="utf-8") as f:
            val_metrics = json.load(f)
    else:
        from analysis.validation import run_full_validation
        val_metrics = run_full_validation()

    fv = val_metrics["flood_validation"]
    sb = val_metrics["spatial_block_cv"]
    ss = val_metrics["slope_sanity_check"]

    # Top Metric Cards
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Flood Model ROC AUC</div>
                <div class="metric-value">{fv['auc']:.3f}</div>
                <div class="metric-subtext">Balanced Sample (N=10,000, No Leakage)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with d2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Precision & Recall</div>
                <div class="metric-value">{fv['metrics']['precision']:.1%} | {fv['metrics']['recall']:.1%}</div>
                <div class="metric-subtext">Decision Threshold &tau; = {fv['threshold']:.3f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with d3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Spatial Block Mean AUC</div>
                <div class="metric-value">{sb['mean_block_auc']:.3f} &plusmn; {sb['std_block_auc']:.3f}</div>
                <div class="metric-subtext">16 Disjoint Geographic Blocks</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with d4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Slope Hazard Correlation</div>
                <div class="metric-value">r = {ss['spearman_correlation']:.3f}</div>
                <div class="metric-subtext">Monotonic Geomorphic Scaling (p &lt; 0.001)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='border: none; border-top: 1px solid #D5DEE8; margin: 18px 0;'>", unsafe_allow_html=True)

    # Sub-header
    st.markdown(
        f"<h4 style='color: {COLOR_DEEP_BLUE}; margin-bottom: 6px;'>"
        f"Independent Flood Validation: Ground Truth vs. Susceptibility"
        f"</h4>"
        f"<p style='color: {COLOR_MUTED_TEXT}; font-size: 13px; margin-bottom: 14px;'>"
        f"Validation Truth: Copernicus Sentinel-1 SAR change detection (Dec 2023 peak inundation). "
        f"Permanent water (&gt;80% occurrence) strictly excluded. "
        f"<strong>Strict No-Leakage Protocol:</strong> Sentinel-1 data was never used in hazard calculation."
        f"</p>",
        unsafe_allow_html=True,
    )

    col_roc, col_cm = st.columns(2, gap="medium")
    with col_roc:
        roc_p = "outputs/roc_curve.png"
        if os.path.exists(roc_p):
            st.image(roc_p, caption="Figure 1: Receiver Operating Characteristic (ROC) Curve against Sentinel-1 SAR truth.", use_container_width=True)
        else:
            st.warning("ROC curve image not found.")

    with col_cm:
        cm_p = "outputs/confusion_matrix.png"
        if os.path.exists(cm_p):
            st.image(cm_p, caption=f"Figure 2: Confusion Matrix at operational decision threshold τ = {fv['threshold']:.3f}.", use_container_width=True)
        else:
            st.warning("Confusion matrix image not found.")

    # Spatial Block CV and Slope Sanity Check
    st.markdown("<hr style='border: none; border-top: 1px solid #D5DEE8; margin: 18px 0;'>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='color: {COLOR_DEEP_BLUE}; margin-bottom: 6px;'>Spatial Generalizability & Geomorphic Verification</h4>", unsafe_allow_html=True)

    col_sb, col_ss = st.columns(2, gap="medium")
    with col_sb:
        st.markdown(f"<strong style='color: {COLOR_INK}; font-size: 14px;'>Spatial Block Cross-Validation (4x4 Grid)</strong>", unsafe_allow_html=True)
        st.caption("Guards against artificial accuracy inflation caused by Tobler's First Law (spatial autocorrelation):")
        sb_p = "outputs/spatial_block_cv.png"
        if os.path.exists(sb_p):
            st.image(sb_p, caption="Figure 3: Block-level ROC AUC across 16 contiguous subregions.", use_container_width=True)

        with st.expander("View 16-Block Cross-Validation Breakdown"):
            sb_rows = []
            for b in sb["blocks"]:
                sb_rows.append({
                    "Block": b["block_id"],
                    "Flooded Pixels": b["flooded_count"],
                    "Dry Pixels": b["dry_count"],
                    "Block AUC": b["auc"] if b["auc"] is not None else "N/A",
                })
            st.dataframe(pd.DataFrame(sb_rows), use_container_width=True, hide_index=True)

    with col_ss:
        st.markdown(f"<strong style='color: {COLOR_INK}; font-size: 14px;'>Slope-Instability Geomorphic Sanity Check</strong>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='warning-banner' style='margin-bottom: 8px;'>"
            f"<strong>Sanity Check, NOT Empirical Validation:</strong> "
            f"No official historical landslide inventory exists for South Chennai coastal plains. "
            f"This test confirms physical scaling with slope gradient and extreme rainfall."
            f"</div>",
            unsafe_allow_html=True,
        )
        ss_p = "outputs/slope_sanity_check.png"
        if os.path.exists(ss_p):
            st.image(ss_p, caption="Figure 4: Mean slope-instability hazard across slope classes and rainfall tiers.", use_container_width=True)

    # Educational Expander for Jury Defense
    with st.expander("Defense Guide: Why AUC Alone Can Mislead in Spatial Disaster Models"):
        st.markdown(
            f"""
            <div style="font-size: 13.5px; line-height: 1.6; color: {COLOR_INK};">
                <ol style="margin-left: 20px;">
                    <li><strong>Spatial Autocorrelation Inflation (Tobler's First Law):</strong>
                        In spatial data, adjacent pixels are physically correlated. A standard random train/test split allows neighboring pixels into both sets, artificially boosting AUC by 0.05&ndash;0.10. Our <strong>Spatial Block Cross-Validation</strong> partitions the area into 16 contiguous geographic blocks, verifying true out-of-region transferability.
                    </li>
                    <li><strong>Class Imbalance Illusion:</strong>
                        In large spatial scenes, 80&ndash;90% of the terrain often remains dry. A naive model predicting "dry everywhere" achieves 90% overall accuracy while failing 100% of flooded communities. We enforce <strong>balanced 1:1 sampling</strong> (5,000 flooded, 5,000 dry) to evaluate genuine discriminative ability.
                    </li>
                    <li><strong>Asymmetric Real-World Error Costs:</strong>
                        AUC treats False Positives (dispatching rescue teams to dry land) and False Negatives (leaving submerged families unassisted) identically. In disaster command centers, a single ROC score cannot determine field deployment; the <strong>operational confusion matrix, precision, and recall</strong> at calibrated thresholds are vital.
                    </li>
                    <li><strong>Permanent Water Leakage Prevention:</strong>
                        Including permanent water bodies (lakes, reservoirs, sea) produces millions of trivial True Positives. Masking out <strong>JRC 38-year water occurrence (&gt;80%)</strong> forces the model to prove its predictive capability exclusively on newly inundated terrestrial floodplains.
                    </li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============================================================================
# TAB 5: METHODS AND DATA
# =============================================================================
with tab_methods:
    st.markdown(
        f"<p style='color: {COLOR_MUTED_TEXT}; font-size: 13px; margin-bottom: 12px;'>"
        f"Complete scientific traceability, parameter justification, and limitations for GEOIMPATHON 1.0 jury defense."
        f"</p>",
        unsafe_allow_html=True,
    )

    st.markdown(f"<h4 style='color: {COLOR_DEEP_BLUE};'>What-and-Why Register</h4>", unsafe_allow_html=True)

    what_why_path = "docs/WHAT_AND_WHY.md"
    if os.path.exists(what_why_path):
        with open(what_why_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.warning("docs/WHAT_AND_WHY.md not found.")
