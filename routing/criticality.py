r"""Road Criticality Index and Single Points of Failure Analysis.

Implements two-stage vulnerability analysis:
Stage 1: Path-exposure flow accumulation along safest routes from all 141 settlements
         to nearest safe hospital, screening top candidate edges by Flow x Risk.
Stage 2: Removal impact simulation on candidate edges (G \ {e*}), measuring newly isolated
         built-up exposure and added travel delay (minutes).
Extracts top 10 single points of failure with plain-language operational summaries.
Exports results to CSV and GeoJSON.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely.geometry import LineString, Point

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routing.router import is_edge_blocked

logger = logging.getLogger(__name__)


def compute_road_criticality(
    graph_path: str = "data/sample/drive_network_risk.graphml",
    settlements_path: str = "data/sample/settlements.geojson",
    hospitals_path: str = "data/sample/hospitals.geojson",
    top_settlements_path: str = "data/sample/top_settlements.csv",
    output_dir: str = "outputs",
    alpha: float = 3.0,
    n_candidates: int = 40,
    top_n: int = 10,
) -> Dict[str, Any]:
    """Compute Road Criticality Index and Removal Impact for top single points of failure.

    Args:
        graph_path: Path to risk-annotated road network GraphML
        settlements_path: Path to settlements GeoJSON
        hospitals_path: Path to hospitals GeoJSON
        top_settlements_path: Path to CSV containing built_exposure values
        output_dir: Directory to save exported CSV and GeoJSON
        alpha: Safety penalty multiplier used in safest route Dijkstra
        n_candidates: Number of top edges screened for removal impact
        top_n: Number of final distinct single points of failure to report

    Returns:
        Dictionary containing top critical roads, isolated exposure stats, and file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Computing Road Criticality Index and Removal Impact...")

    # 1. Load Graph and clean edge attributes
    G = ox.load_graphml(graph_path)
    for u, v, k, d in G.edges(keys=True, data=True):
        d["length"] = float(d.get("length", 50.0))
        d["risk"] = float(d.get("risk", 0.20))
        d["travel_time_normal"] = float(d.get("travel_time_normal", 10.0))
        d["travel_time_flood"] = float(d.get("travel_time_flood", 10.0))
        d["cost_safest"] = d["length"] * (1.0 + alpha * d["risk"])
        d["is_blocked"] = is_edge_blocked(d)

    # 2. Load Settlements and attach built-up exposure
    settlements = gpd.read_file(settlements_path)
    if os.path.exists(top_settlements_path):
        top_sett = pd.read_csv(top_settlements_path)
        settlements = settlements.merge(
            top_sett[["settlement_id", "built_exposure"]],
            on="settlement_id",
            how="left",
        )
    if "built_exposure" not in settlements.columns:
        settlements["built_exposure"] = 0.50
    settlements["built_exposure"] = settlements["built_exposure"].fillna(0.50)
    # Scale exposure to tangible human footprint units
    settlements["exposure_units"] = settlements["built_exposure"] * 10000.0

    # 3. Load Safe Hospitals
    hospitals = gpd.read_file(hospitals_path)
    safe_hospitals = hospitals[hospitals["is_safe"] == True].copy()
    if safe_hospitals.empty:
        safe_hospitals = hospitals.copy()

    safe_hosp_nodes = set(
        ox.distance.nearest_nodes(
            G, safe_hospitals.geometry.x.values, safe_hospitals.geometry.y.values
        )
    )

    # Snap settlements to graph nodes
    settlement_nodes = ox.distance.nearest_nodes(
        G, settlements.geometry.x.values, settlements.geometry.y.values
    )

    # 4. Stage 1: Path-Exposure Flow Accumulation
    edge_settlements: Dict[Tuple[int, int, int], List[Dict[str, Any]]] = {}
    settlement_baselines: Dict[str, Dict[str, Any]] = {}

    for idx, row in settlements.iterrows():
        s_node = settlement_nodes[idx]
        s_id = row["settlement_id"]
        s_name = row["name"]
        s_exp = float(row["exposure_units"])

        try:
            lengths, paths = nx.single_source_dijkstra(G, s_node, weight="cost_safest")
            best_dest = None
            min_cost = float("inf")
            for dn in safe_hosp_nodes:
                if dn in lengths and lengths[dn] < min_cost:
                    min_cost = lengths[dn]
                    best_dest = dn

            if best_dest is not None:
                path = paths[best_dest]
                # Calculate baseline travel time
                tot_time_s = 0.0
                for i in range(len(path) - 1):
                    u_n, v_n = path[i], path[i + 1]
                    ed = G.get_edge_data(u_n, v_n)
                    k_idx = 0 if 0 in ed else list(ed.keys())[0]
                    tot_time_s += float(ed[k_idx]["travel_time_normal"])

                    edge_key = (u_n, v_n, k_idx)
                    if edge_key not in edge_settlements:
                        edge_settlements[edge_key] = []
                    edge_settlements[edge_key].append({
                        "settlement_id": s_id,
                        "name": s_name,
                        "origin_node": s_node,
                        "exposure": s_exp,
                        "baseline_time_s": tot_time_s,
                    })

                settlement_baselines[s_id] = {
                    "origin_node": s_node,
                    "exposure": s_exp,
                    "baseline_time_s": tot_time_s,
                }
        except Exception:
            continue

    # Score candidate edges: Flow Exposure * Edge Risk
    candidate_edges = []
    for e_key, s_list in edge_settlements.items():
        u_n, v_n, k_idx = e_key
        flow_exp = sum(item["exposure"] for item in s_list)
        r_val = float(G.edges[e_key]["risk"])
        cand_score = flow_exp * r_val
        candidate_edges.append((e_key, cand_score, flow_exp, r_val, s_list))

    candidate_edges.sort(key=lambda x: x[1], reverse=True)
    top_candidates = candidate_edges[:n_candidates]
    logger.info("Stage 1 screened %d candidate edges. Running Stage 2 removal impact...", len(top_candidates))

    # 5. Stage 2: Removal Impact Verification
    removal_results = []
    for e_key, cand_score, flow_exp, r_val, s_list in top_candidates:
        u_n, v_n, k_idx = e_key
        orig_cost = G.edges[e_key]["cost_safest"]
        # Sever the edge
        G.edges[e_key]["cost_safest"] = float("inf")

        isolated_exp = 0.0
        weighted_delay_min = 0.0
        isolated_names = []
        delayed_info = []

        for item in s_list:
            s_node = item["origin_node"]
            s_name = item["name"]
            s_exp = item["exposure"]
            base_time_s = item["baseline_time_s"]

            try:
                lengths_new, paths_new = nx.single_source_dijkstra(G, s_node, weight="cost_safest")
                best_d = None
                min_c = float("inf")
                for dn in safe_hosp_nodes:
                    if dn in lengths_new and lengths_new[dn] < min_c:
                        min_c = lengths_new[dn]
                        best_d = dn

                if best_d is None or min_c == float("inf"):
                    # Settlement is isolated
                    isolated_exp += s_exp
                    isolated_names.append(s_name)
                else:
                    p_new = paths_new[best_d]
                    new_time_s = 0.0
                    for i in range(len(p_new) - 1):
                        nu, nv = p_new[i], p_new[i + 1]
                        ned = G.get_edge_data(nu, nv)
                        nk = 0 if 0 in ned else list(ned.keys())[0]
                        new_time_s += float(ned[nk]["travel_time_normal"])

                    detour_min = max(0.0, (new_time_s - base_time_s) / 60.0)
                    weighted_delay_min += detour_min * s_exp
                    if detour_min >= 1.5:
                        delayed_info.append(f"{s_name} (+{detour_min:.1f}m)")
            except Exception:
                isolated_exp += s_exp
                isolated_names.append(s_name)

        # Restore edge
        G.edges[e_key]["cost_safest"] = orig_cost

        # Verified Composite Criticality Index
        # Prioritizes complete isolation, then weighted detour delay
        composite_score = isolated_exp + (weighted_delay_min / 60.0)

        edge_data = G.edges[e_key]
        road_name = edge_data.get("name", "Unnamed Arterial")
        if isinstance(road_name, list):
            road_name = road_name[0]
        hway = edge_data.get("highway", "road")
        if isinstance(hway, list):
            hway = hway[0]

        # Geometry
        geom = edge_data.get("geometry")
        if geom is None:
            pt_u = Point(G.nodes[u_n]["x"], G.nodes[u_n]["y"])
            pt_v = Point(G.nodes[v_n]["x"], G.nodes[v_n]["y"])
            geom = LineString([pt_u, pt_v])

        # Centroid for marker placement
        centroid = geom.centroid

        # One-line explanation
        if isolated_names:
            explanation = (
                f"Severance isolates {len(isolated_names)} settlements "
                f"({', '.join(isolated_names[:3])}), cutting {isolated_exp:,.0f} exposure units from hospital access."
            )
        elif delayed_info:
            explanation = (
                f"Severance forces detours for {len(s_list)} communities "
                f"({', '.join(delayed_info[:3])}), adding acute medical transit delays."
            )
        else:
            explanation = (
                f"High-traffic arterial carrying {flow_exp:,.0f} exposure units through high flood hazard ({r_val:.2f})."
            )

        removal_results.append({
            "edge_id": f"{u_n}_{v_n}_{k_idx}",
            "name": road_name,
            "highway": hway,
            "risk": round(r_val, 4),
            "flow_exposure": round(flow_exp, 1),
            "isolated_exposure": round(isolated_exp, 1),
            "isolated_count": len(isolated_names),
            "isolated_settlements": ", ".join(isolated_names),
            "composite_criticality": round(composite_score, 2),
            "explanation": explanation,
            "geometry": geom,
            "lat": round(centroid.y, 6),
            "lon": round(centroid.x, 6),
        })

    # Sort by verified removal impact score
    removal_results.sort(key=lambda x: x["composite_criticality"], reverse=True)

    # 6. Deduplicate contiguous segments to select Top N distinct bottlenecks
    seen_corridors = set()
    distinct_critical = []

    for r in removal_results:
        # Key on road name and rounded spatial location (approx 1 km grid)
        corr_key = (r["name"], round(r["lat"], 2), round(r["lon"], 2))
        if corr_key not in seen_corridors:
            seen_corridors.add(corr_key)
            r["rank"] = len(distinct_critical) + 1
            distinct_critical.append(r)
        if len(distinct_critical) == top_n:
            break

    # If fewer than top_n distinct, fill remaining
    if len(distinct_critical) < top_n:
        for r in removal_results:
            if r not in distinct_critical:
                r["rank"] = len(distinct_critical) + 1
                distinct_critical.append(r)
            if len(distinct_critical) == top_n:
                break

    # 7. Export CSV and GeoJSON
    crit_gdf = gpd.GeoDataFrame(distinct_critical, geometry="geometry", crs="EPSG:4326")

    csv_path = os.path.join(output_dir, "top_critical_roads.csv")
    geojson_path = os.path.join(output_dir, "top_critical_roads.geojson")

    # CSV without geometry object
    csv_df = crit_gdf.drop(columns=["geometry"])
    csv_df.to_csv(csv_path, index=False)

    # GeoJSON
    crit_gdf.to_file(geojson_path, driver="GeoJSON")

    logger.info("Saved top %d critical roads to %s and %s", len(distinct_critical), csv_path, geojson_path)

    return {
        "top_critical_roads": distinct_critical,
        "csv_path": csv_path,
        "geojson_path": geojson_path,
        "total_screened": len(removal_results),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    compute_road_criticality()
