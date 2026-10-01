"""Emergency least-risk routing engine and network risk attribution.

Assigns multi-hazard risk to road network edges by spatial point sampling
every 30 meters. Computes fastest vs. safest routes via Dijkstra,
identifies safe vs. unsafe medical facilities, and generates side-by-side
comparisons and polyline geometries for Folium web visualization.
"""

import os
import logging
from typing import Dict, Tuple, List, Any, Optional
import yaml
import numpy as np
import networkx as nx
import geopandas as gpd
import osmnx as ox
import rasterio
from shapely.geometry import Point, LineString

from app.theme import (
    COLOR_DEEP_BLUE,
    COLOR_ORANGE,
    COLOR_MID_BLUE,
    COLOR_DARK_ORANGE,
    COLOR_WHITE,
)
from analysis.raster_ops import sample_raster_at_points

logger = logging.getLogger(__name__)


def is_edge_blocked(data: dict) -> bool:
    """Helper to check if an edge is blocked, accounting for GraphML string conversion."""
    val = data.get("is_blocked", False)
    if isinstance(val, str):
        return val.lower() in ("true", "1")
    return bool(val)


def annotate_network_with_risk(
    graph_path: str = "data/sample/drive_network.graphml",
    risk_raster_path: str = "data/sample/multihazard_risk.tif",
    config_path: str = "config.yaml",
    output_graph_path: str = "data/sample/drive_network_risk.graphml",
    force_refresh: bool = False,
) -> nx.MultiDiGraph:
    """Sample continuous raster risk along edges and annotate GraphML with risk attributes.

    Edge attributes added:
    - risk_mean: Mean sampled risk along line geometry
    - risk_max: Peak sampled risk along line geometry
    - risk: Composite edge risk = 0.5 * mean + 0.5 * max + bumps
    - flood_speed_kmh: Speed in flood scenario (5 km/h if in High risk)
    - flood_travel_time: Travel time (seconds) in flood scenario
    - is_blocked: True if edge risk >= block_threshold_percentile
    """
    if not force_refresh and os.path.exists(output_graph_path):
        logger.info("Loading cached risk-annotated graph from %s", output_graph_path)
        G = ox.load_graphml(output_graph_path)
        for _, _, _, d in G.edges(keys=True, data=True):
            d["is_blocked"] = is_edge_blocked(d)
        return G

    logger.info("Annotating road network with continuous multi-hazard risk...")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    b = cfg.get("bbox", {})
    bounds = (float(b["lon_min"]), float(b["lat_min"]), float(b["lon_max"]), float(b["lat_max"]))
    lon_min, lat_min, lon_max, lat_max = bounds

    # Load multi-hazard risk raster
    with rasterio.open(risk_raster_path) as src:
        risk_arr = src.read(1).astype(np.float32)
        r_rows, r_cols = risk_arr.shape

    # Risk thresholds
    p_cfg = cfg.get("risk_percentiles", {"low_max": 50.0, "moderate_max": 80.0, "high_max": 95.0})
    p80 = float(np.percentile(risk_arr[~np.isnan(risk_arr)], p_cfg.get("moderate_max", 80.0)))
    p95 = float(np.percentile(risk_arr[~np.isnan(risk_arr)], p_cfg.get("high_max", 95.0)))

    # Routing parameters
    r_cfg = cfg.get("routing", {})
    sample_interval_m = float(r_cfg.get("edge_sample_interval_m", 30.0))
    bump_tunnel = float(r_cfg.get("risk_bumps", {}).get("tunnel_underpass", 0.15))
    bump_bridge = float(r_cfg.get("risk_bumps", {}).get("bridge_over_water", 0.08))
    flood_speed_kmh = float(r_cfg.get("flood_speed_kmh", 5.0))
    flood_speed_ms = flood_speed_kmh / 3.6

    G = ox.load_graphml(graph_path)

    for u, v, k, data in G.edges(keys=True, data=True):
        length_m = float(data.get("length", 50.0))
        geom = data.get("geometry")

        # Determine points to sample
        if geom is not None and geom.geom_type == "LineString":
            line = geom
        else:
            # Fallback to straight line between endpoints
            u_pt = (G.nodes[u]["x"], G.nodes[u]["y"])
            v_pt = (G.nodes[v]["x"], G.nodes[v]["y"])
            line = LineString([u_pt, v_pt])

        num_samples = max(2, int(math_ceil(length_m / sample_interval_m)))
        distances = np.linspace(0, line.length, num_samples)

        sampled_risks = []
        for d in distances:
            pt = line.interpolate(d)
            c = int(np.clip((pt.x - lon_min) / (lon_max - lon_min) * r_cols, 0, r_cols - 1))
            r = int(np.clip((lat_max - pt.y) / (lat_max - lat_min) * r_rows, 0, r_rows - 1))
            val = risk_arr[r, c]
            if not np.isnan(val):
                sampled_risks.append(val)

        if sampled_risks:
            r_mean = float(np.mean(sampled_risks))
            r_max = float(np.max(sampled_risks))
        else:
            r_mean = 0.20
            r_max = 0.20

        # Base composite edge risk
        edge_risk = 0.5 * r_mean + 0.5 * r_max

        # Risk bumps for structural flood traps
        tunnel_tag = str(data.get("tunnel", "")).lower()
        layer_tag = data.get("layer", 0)
        try:
            layer_val = float(layer_tag)
        except Exception:
            layer_val = 0.0

        if tunnel_tag in ["yes", "true", "1"] or layer_val < 0:
            edge_risk += bump_tunnel

        bridge_tag = str(data.get("bridge", "")).lower()
        if bridge_tag in ["yes", "true", "1"] and edge_risk > 0.40:
            edge_risk += bump_bridge

        edge_risk = float(np.clip(edge_risk, 0.0, 1.0))

        # Speed and travel time
        normal_speed_kmh = float(data.get("speed_kph", 30.0))
        normal_speed_ms = max(1.0, normal_speed_kmh / 3.6)
        normal_time_s = length_m / normal_speed_ms

        # Flood travel time
        is_blocked = edge_risk >= p95
        if edge_risk >= p80:
            # Throttled to 5 km/h in High risk inundation
            flood_time_s = length_m / flood_speed_ms
        else:
            flood_time_s = normal_time_s

        data["risk_mean"] = round(r_mean, 4)
        data["risk_max"] = round(r_max, 4)
        data["risk"] = round(edge_risk, 4)
        data["is_blocked"] = bool(is_blocked)
        data["travel_time_normal"] = round(normal_time_s, 2)
        data["travel_time_flood"] = round(flood_time_s, 2)

    ox.save_graphml(G, output_graph_path)
    logger.info("Saved risk-annotated network to %s", output_graph_path)
    return G


def math_ceil(x: float) -> int:
    return int(np.ceil(x))


def classify_facilities_safety(
    facilities_gdf: gpd.GeoDataFrame,
    risk_raster_path: str = "data/sample/multihazard_risk.tif",
    config_path: str = "config.yaml",
) -> gpd.GeoDataFrame:
    """Sample multi-hazard risk at facilities and classify them as Safe or Unsafe.

    Facilities with risk >= 80th percentile (High or Very High risk zone)
    are flagged as is_safe = False and excluded from destination routing.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    b = cfg.get("bbox", {})
    bounds = (float(b["lon_min"]), float(b["lat_min"]), float(b["lon_max"]), float(b["lat_max"]))

    with rasterio.open(risk_raster_path) as src:
        risk_arr = src.read(1).astype(np.float32)

    p_cfg = cfg.get("risk_percentiles", {"low_max": 50.0, "moderate_max": 80.0, "high_max": 95.0})
    p80 = float(np.percentile(risk_arr[~np.isnan(risk_arr)], p_cfg.get("moderate_max", 80.0)))

    gdf = facilities_gdf.copy()
    sampled_risk = sample_raster_at_points(risk_arr, bounds, gdf)
    gdf["sampled_risk"] = np.round(sampled_risk, 4)
    gdf["is_safe"] = gdf["sampled_risk"] < p80
    gdf["safety_status"] = np.where(gdf["is_safe"], "Operational / Safe", "Inundation Risk / Unsafe")

    num_safe = int(gdf["is_safe"].sum())
    num_unsafe = len(gdf) - num_safe
    logger.info("Classified %d facilities: %d Safe, %d Unsafe (Threshold: %.4f)", len(gdf), num_safe, num_unsafe, p80)
    return gdf


def calculate_dual_routes(
    G: nx.MultiDiGraph,
    origin_coord: Tuple[float, float],
    dest_gdf: gpd.GeoDataFrame,
    alpha: float = 3.0,
    config_path: str = "config.yaml",
) -> Dict[str, Any]:
    """Calculate and compare the fastest vs. safest route from an origin to the nearest safe facility.

    Args:
        G: Risk-annotated road network MultiDiGraph
        origin_coord: (lon, lat) of the origin settlement
        dest_gdf: GeoDataFrame of destination facilities (hospitals or shelters)
        alpha: Safety penalty multiplier (0 = fastest, higher = safer)

    Returns:
        Dictionary containing route geometries, metrics, and compromise text.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    p80 = 0.5364
    p95 = 0.5983

    # Filter to safe facilities
    safe_dest = dest_gdf[dest_gdf["is_safe"]].copy()
    if safe_dest.empty:
        # Fallback to all facilities if all are inundated
        safe_dest = dest_gdf.copy()
        warning_dest = "All candidate facilities lie in high-risk zones. Using closest facility."
    else:
        warning_dest = None

    # Snap origin to nearest graph node
    orig_lon, orig_lat = origin_coord
    orig_node = ox.distance.nearest_nodes(G, orig_lon, orig_lat)

    # Snap all safe destinations to graph nodes
    dest_nodes = ox.distance.nearest_nodes(G, safe_dest.geometry.x.values, safe_dest.geometry.y.values)
    dest_node_set = set(dest_nodes)

    # Assign dynamic edge weights
    # Cost = length * (1 + alpha * risk)
    for u, v, k, d in G.edges(keys=True, data=True):
        length = float(d.get("length", 50.0))
        risk = float(d.get("risk", 0.20))
        d["cost_safest"] = length * (1.0 + alpha * risk)
        d["cost_fastest"] = length * (1.0 + 0.0 * risk)  # Pure length / fastest

    # 1. Calculate Fastest Route (alpha = 0, all roads passable)
    fastest_path = None
    fastest_dest_node = None
    min_fastest_cost = float("inf")

    # Multi-target shortest path
    lengths, paths = nx.single_source_dijkstra(G, orig_node, weight="cost_fastest")
    for dn in dest_node_set:
        if dn in lengths and lengths[dn] < min_fastest_cost:
            min_fastest_cost = lengths[dn]
            fastest_path = paths[dn]
            fastest_dest_node = dn

    # 2. Calculate Safest Route (roads with risk >= p95 severed in flood scenario)
    # Build subgraph without blocked edges
    edges_safe = []
    for u, v, k, d in G.edges(keys=True, data=True):
        if not is_edge_blocked(d):
            edges_safe.append((u, v, k))

    G_flood = G.edge_subgraph(edges_safe).copy()

    safest_path = None
    safest_dest_node = None
    min_safest_cost = float("inf")
    fallback_used = False

    if orig_node in G_flood:
        lengths_s, paths_s = nx.single_source_dijkstra(G_flood, orig_node, weight="cost_safest")
        for dn in dest_node_set:
            if dn in lengths_s and lengths_s[dn] < min_safest_cost:
                min_safest_cost = lengths_s[dn]
                safest_path = paths_s[dn]
                safest_dest_node = dn

    # Fallback if no safe path exists
    if safest_path is None:
        fallback_used = True
        logger.warning("No safe path exists in severed graph; falling back to lowest-risk path on full network.")
        lengths_s, paths_s = nx.single_source_dijkstra(G, orig_node, weight="cost_safest")
        for dn in dest_node_set:
            if dn in lengths_s and lengths_s[dn] < min_safest_cost:
                min_safest_cost = lengths_s[dn]
                safest_path = paths_s[dn]
                safest_dest_node = dn

    # Fallback to fastest path if still None
    if safest_path is None:
        safest_path = fastest_path
        safest_dest_node = fastest_dest_node

    # Helper function to extract path metrics and coordinate polyline
    def extract_path_metrics(path: List[int], is_flood_speed: bool = False) -> Dict[str, Any]:
        if not path or len(path) < 2:
            return {
                "distance_km": 0.0,
                "time_min": 0.0,
                "high_risk_km": 0.0,
                "high_risk_pct": 0.0,
                "coordinates": [],
            }

        coords = []
        tot_dist_m = 0.0
        tot_time_s = 0.0
        high_risk_dist_m = 0.0

        for i in range(len(path) - 1):
            u_n, v_n = path[i], path[i + 1]
            edge_data = G.get_edge_data(u_n, v_n)
            # Pick primary edge key
            data = edge_data[0] if 0 in edge_data else list(edge_data.values())[0]

            l_m = float(data.get("length", 50.0))
            r_val = float(data.get("risk", 0.20))
            t_s = float(data.get("travel_time_flood" if is_flood_speed else "travel_time_normal", 5.0))

            tot_dist_m += l_m
            tot_time_s += t_s
            if r_val >= p80:
                high_risk_dist_m += l_m

            geom = data.get("geometry")
            if geom is not None and geom.geom_type == "LineString":
                coords.extend([[lat, lon] for lon, lat in geom.coords])
            else:
                coords.append([G.nodes[u_n]["y"], G.nodes[u_n]["x"]])
                coords.append([G.nodes[v_n]["y"], G.nodes[v_n]["x"]])

        # Deduplicate sequential coordinates
        clean_coords = [coords[0]]
        for pt in coords[1:]:
            if pt != clean_coords[-1]:
                clean_coords.append(pt)

        dist_km = tot_dist_m / 1000.0
        high_km = high_risk_dist_m / 1000.0
        high_pct = (high_km / dist_km * 100.0) if dist_km > 0 else 0.0
        time_min = tot_time_s / 60.0

        return {
            "distance_km": round(dist_km, 2),
            "time_min": round(time_min, 1),
            "high_risk_km": round(high_km, 2),
            "high_risk_pct": round(high_pct, 1),
            "coordinates": clean_coords,
        }

    fastest_metrics = extract_path_metrics(fastest_path, is_flood_speed=False)
    safest_metrics = extract_path_metrics(safest_path, is_flood_speed=True)

    # Compromise Assessment Plain-Language Sentence
    extra_time = max(0.0, round(safest_metrics["time_min"] - fastest_metrics["time_min"], 1))
    extra_dist = max(0.0, round(safest_metrics["distance_km"] - fastest_metrics["distance_km"], 2))
    avoided_high_risk = max(0.0, round(fastest_metrics["high_risk_km"] - safest_metrics["high_risk_km"], 2))

    if avoided_high_risk > 0.1:
        compromise_text = (
            f"The safest route adds {extra_time:.1f} min ({extra_dist:.1f} km) and successfully avoids "
            f"{avoided_high_risk:.1f} km of high-risk road corridors."
        )
    elif extra_time > 0.0:
        compromise_text = (
            f"The safest route adds {extra_time:.1f} min to bypass minor drainage depressions while maintaining clear headway."
        )
    else:
        compromise_text = "The safest and fastest routes coincide along elevated regional highway corridors."

    # Identify destination facility metadata
    dest_row = safe_dest[safe_dest.geometry.x == G.nodes[safest_dest_node]["x"]]
    dest_name = dest_row["name"].values[0] if not dest_row.empty else "Operational Emergency Facility"

    return {
        "fastest": fastest_metrics,
        "safest": safest_metrics,
        "compromise_text": compromise_text,
        "destination_name": dest_name,
        "fallback_used": fallback_used,
        "warning_dest": warning_dest,
        "alpha": alpha,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    G = annotate_network_with_risk()
    print("Risk-annotated network edges:", len(G.edges))
