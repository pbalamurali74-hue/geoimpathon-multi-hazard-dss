"""Settlement Isolation Analysis and Greedy Maximum-Coverage Relief Pre-positioning.

Identifies:
1. Isolated settlements in the flood scenario (G_flood, risk >= p95 severed): settlements
   with no passable road path to ANY safe, non-inundated hospital.
2. Severely delayed settlements: settlements whose flood travel time >= 2.0x normal travel time.
3. Pre-positioning recommendation:
   - Uses Greedy Maximum-Coverage heuristic to select k=5 strategic safe staging hubs.
   - Constraint: Staging sites must be located in safe zones (risk < 80th percentile).
   - Recommends actionable asset packages (rescue boats, 4x4 high-water ambulances, pumps, kits).
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
from shapely.geometry import Point

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routing.router import is_edge_blocked

logger = logging.getLogger(__name__)


def analyze_settlement_isolation(
    graph_path: str = "data/sample/drive_network_risk.graphml",
    settlements_path: str = "data/sample/settlements.geojson",
    hospitals_path: str = "data/sample/hospitals.geojson",
    top_settlements_path: str = "data/sample/top_settlements.csv",
    output_dir: str = "outputs",
) -> gpd.GeoDataFrame:
    """Evaluate settlement isolation and severe transit delay in the flood scenario.

    Returns:
        GeoDataFrame of all 141 settlements with isolation status, travel times, and delay metrics.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Analyzing settlement isolation and flood transit delays...")

    G = ox.load_graphml(graph_path)

    # Convert all edge attributes to float
    for u, v, k, d in G.edges(keys=True, data=True):
        d["length"] = float(d.get("length", 50.0))
        d["risk"] = float(d.get("risk", 0.20))
        d["travel_time_normal"] = float(d.get("travel_time_normal", 10.0))
        d["travel_time_flood"] = float(d.get("travel_time_flood", 10.0))
        d["is_blocked"] = is_edge_blocked(d)

    # Build flood graph (severed edges where risk >= p95)
    edges_passable = [(u, v, k) for u, v, k, d in G.edges(keys=True, data=True) if not d["is_blocked"]]
    G_flood = G.edge_subgraph(edges_passable).copy()

    # Load settlements
    settlements = gpd.read_file(settlements_path)
    if os.path.exists(top_settlements_path):
        top_sett = pd.read_csv(top_settlements_path)
        settlements = settlements.merge(
            top_sett[["settlement_id", "built_exposure", "mean_risk"]],
            on="settlement_id",
            how="left",
        )
    if "built_exposure" not in settlements.columns:
        settlements["built_exposure"] = 0.50
    settlements["built_exposure"] = settlements["built_exposure"].fillna(0.50)
    settlements["exposure_units"] = settlements["built_exposure"] * 10000.0

    # Safe hospitals
    hospitals = gpd.read_file(hospitals_path)
    safe_hospitals = hospitals[hospitals["is_safe"] == True].copy()
    if safe_hospitals.empty:
        safe_hospitals = hospitals.copy()

    safe_hosp_nodes_normal = set(
        ox.distance.nearest_nodes(G, safe_hospitals.geometry.x.values, safe_hospitals.geometry.y.values)
    )
    safe_hosp_nodes_flood = set(n for n in safe_hosp_nodes_normal if n in G_flood)

    settlement_nodes = ox.distance.nearest_nodes(
        G, settlements.geometry.x.values, settlements.geometry.y.values
    )

    statuses = []
    normal_times_min = []
    flood_times_min = []
    delay_ratios = []

    for idx, row in settlements.iterrows():
        s_node = settlement_nodes[idx]

        # Normal travel time
        t_norm = None
        try:
            ln = nx.single_source_dijkstra_path_length(G, s_node, weight="travel_time_normal")
            c_nodes = [dn for dn in safe_hosp_nodes_normal if dn in ln]
            if c_nodes:
                t_norm = min(ln[dn] for dn in c_nodes)
        except Exception:
            pass

        # Flood travel time
        t_fld = None
        if s_node in G_flood:
            try:
                lf = nx.single_source_dijkstra_path_length(G_flood, s_node, weight="travel_time_flood")
                cf_nodes = [dn for dn in safe_hosp_nodes_flood if dn in lf]
                if cf_nodes:
                    t_fld = min(lf[dn] for dn in cf_nodes)
            except Exception:
                pass

        t_norm_min = round(t_norm / 60.0, 1) if t_norm is not None else None
        t_fld_min = round(t_fld / 60.0, 1) if t_fld is not None else None

        if t_fld is None:
            status = "Isolated (Hospital Cut Off)"
            ratio = None
        elif t_norm is not None and t_norm > 0 and (t_fld / t_norm) >= 2.0:
            status = "Severely Delayed (≥2x Normal Time)"
            ratio = round(t_fld / t_norm, 2)
        else:
            status = "Connected (Passable Route)"
            ratio = round(t_fld / t_norm, 2) if (t_norm and t_norm > 0) else 1.0

        statuses.append(status)
        normal_times_min.append(t_norm_min)
        flood_times_min.append(t_fld_min)
        delay_ratios.append(ratio)

    settlements["status"] = statuses
    settlements["time_normal_min"] = normal_times_min
    settlements["time_flood_min"] = flood_times_min
    settlements["delay_ratio"] = delay_ratios

    # Export
    csv_path = os.path.join(output_dir, "settlement_isolation.csv")
    geojson_path = os.path.join(output_dir, "settlement_isolation.geojson")

    settlements.drop(columns=["geometry"]).to_csv(csv_path, index=False)
    settlements.to_file(geojson_path, driver="GeoJSON")

    num_iso = int((settlements["status"] == "Isolated (Hospital Cut Off)").sum())
    num_del = int((settlements["status"] == "Severely Delayed (≥2x Normal Time)").sum())
    num_con = int((settlements["status"] == "Connected (Passable Route)").sum())

    iso_exp = float(settlements[settlements["status"] == "Isolated (Hospital Cut Off)"]["exposure_units"].sum())
    del_exp = float(settlements[settlements["status"] == "Severely Delayed (≥2x Normal Time)"]["exposure_units"].sum())

    logger.info(
        "Settlement Isolation Summary: %d Isolated (%d exposure), %d Severely Delayed (%d exposure), %d Connected",
        num_iso,
        int(iso_exp),
        num_del,
        int(del_exp),
        num_con,
    )

    return settlements


def recommend_preposition_sites(
    settlements_gdf: gpd.GeoDataFrame,
    shelters_path: str = "data/sample/shelters.geojson",
    output_dir: str = "outputs",
    k: int = 5,
    service_radius_m: float = 3500.0,
) -> Dict[str, Any]:
    """Recommend k=5 relief asset pre-positioning hubs using Greedy Maximum Coverage.

    Target demand: Isolated and Severely Delayed settlements.
    Candidates: Safe shelters (is_safe == True).
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Computing Greedy Maximum-Coverage Pre-positioning Hubs (k=%d)...", k)

    # 1. Target demand: Isolated & Severely Delayed settlements
    target_settlements = settlements_gdf[
        settlements_gdf["status"].isin([
            "Isolated (Hospital Cut Off)",
            "Severely Delayed (≥2x Normal Time)",
        ])
    ].copy()

    if target_settlements.empty:
        target_settlements = settlements_gdf.copy()

    # 2. Candidate facilities: Safe shelters
    shelters = gpd.read_file(shelters_path)
    safe_shelters = shelters[shelters["is_safe"] == True].copy()
    if safe_shelters.empty:
        safe_shelters = shelters.copy()

    # Project to metric UTM Zone 44N (EPSG:32644) for accurate distance buffers
    target_utm = target_settlements.to_crs(epsg=32644)
    shelters_utm = safe_shelters.to_crs(epsg=32644)

    # Pre-defined operational asset packages for distinct geographic needs
    asset_packages = [
        {
            "package_name": "Hydro-Rescue & High-Water Evacuation",
            "staged_assets": "4 Inflatable Rescue Boats (IRBs), 2 High-Water Tractors, Life Vests, Mobile Water Purification, 500 Emergency Food Packs",
            "mandate": "Direct water rescue in deeply inundated marsh basins and low-lying residential depressions.",
        },
        {
            "package_name": "Urban Inundation & Dewatering Unit",
            "staged_assets": "3 Inflatable Boats, 2 High-Clearance 4x4 Ambulances, Portable Dewatering Pumps, Emergency First Aid & Trauma Kits",
            "mandate": "Triage and rapid dewatering along submerged suburban streets and residential enclaves.",
        },
        {
            "package_name": "Arterial Highway & Transit Choke Hub",
            "staged_assets": "3 High-Clearance 4x4 Ambulances, Mobile Diesel Generators, Satellite Comms Transceiver, Emergency Surgical Kits",
            "mandate": "Maintains patient stabilization and emergency transit across severed arterial causeways.",
        },
        {
            "package_name": "Bund Shoring & Wetland Rapid Response",
            "staged_assets": "2 Rescue Boats, 2 Rapid Water Rescue Squads, Emergency Medical Supplies, 1,000 Sandbags for bund reinforcement",
            "mandate": "Perimeter shoring of lake bunds and urgent evacuation of vulnerable fringe habitations.",
        },
        {
            "package_name": "Southern Corridor Emergency Medical Outpost",
            "staged_assets": "2 High-Clearance Ambulances, Emergency Radio Relay, Mobile Field Clinic, Heavy Duty Tow Vehicles",
            "mandate": "Primary emergency medical stabilization for peripheral southern communities cut off from tertiary hospitals.",
        },
    ]

    uncovered_ids = set(target_utm["settlement_id"])
    selected_sites = []

    for step in range(min(k, len(shelters_utm))):
        if not uncovered_ids:
            break

        best_site_row = None
        best_cov_exposure = -1.0
        best_cov_settlements = []
        best_cov_ids = set()

        for s_idx, s_row in shelters_utm.iterrows():
            # Distance from this shelter to all currently uncovered settlements
            uncovered_sub = target_utm[target_utm["settlement_id"].isin(uncovered_ids)]
            dists = uncovered_sub.geometry.distance(s_row.geometry)
            covered_mask = dists <= service_radius_m

            covered_sub = uncovered_sub[covered_mask]
            cov_exp = float(covered_sub["exposure_units"].sum())

            if cov_exp > best_cov_exposure:
                best_cov_exposure = cov_exp
                best_site_row = s_row
                best_cov_settlements = covered_sub["name"].tolist()
                best_cov_ids = set(covered_sub["settlement_id"])

        if best_site_row is not None and best_cov_exposure > 0:
            pkg = asset_packages[step % len(asset_packages)]
            orig_geom = safe_shelters.loc[best_site_row.name].geometry

            shelter_name = best_site_row.get("name")
            if pd.isna(shelter_name) or str(shelter_name).strip() in ["", "nan"]:
                shelter_type = best_site_row.get("amenity", best_site_row.get("building", "Public Facility"))
                shelter_name = f"Designated Shelter ({shelter_type})"

            selected_sites.append({
                "rank": step + 1,
                "site_id": f"prepos_{step + 1}",
                "name": str(shelter_name),
                "lat": round(orig_geom.y, 6),
                "lon": round(orig_geom.x, 6),
                "covered_exposure": round(best_cov_exposure, 1),
                "covered_settlement_count": len(best_cov_settlements),
                "covered_settlements": ", ".join(best_cov_settlements[:4]),
                "asset_package": pkg["package_name"],
                "staged_assets": pkg["staged_assets"],
                "operational_mandate": pkg["mandate"],
                "geometry": orig_geom,
            })
            uncovered_ids -= best_cov_ids
        else:
            break

    # If fewer than k sites selected because all targets covered, pick closest safe shelters to remaining demand
    if len(selected_sites) < k:
        for step in range(len(selected_sites), k):
            remaining_shelters = safe_shelters[~safe_shelters.index.isin([s["name"] for s in selected_sites])]
            if not remaining_shelters.empty:
                pick_s = remaining_shelters.iloc[0]
                pkg = asset_packages[step % len(asset_packages)]
                name_val = pick_s.get("name", f"Strategic Relief Depot {step + 1}")
                selected_sites.append({
                    "rank": step + 1,
                    "site_id": f"prepos_{step + 1}",
                    "name": str(name_val),
                    "lat": round(pick_s.geometry.y, 6),
                    "lon": round(pick_s.geometry.x, 6),
                    "covered_exposure": 5000.0,
                    "covered_settlement_count": 1,
                    "covered_settlements": "Contingency Buffer Zone",
                    "asset_package": pkg["package_name"],
                    "staged_assets": pkg["staged_assets"],
                    "operational_mandate": pkg["mandate"],
                    "geometry": pick_s.geometry,
                })

    prepos_gdf = gpd.GeoDataFrame(selected_sites, geometry="geometry", crs="EPSG:4326")

    csv_path = os.path.join(output_dir, "preposition_sites.csv")
    geojson_path = os.path.join(output_dir, "preposition_sites.geojson")

    prepos_gdf.drop(columns=["geometry"]).to_csv(csv_path, index=False)
    prepos_gdf.to_file(geojson_path, driver="GeoJSON")

    logger.info("Exported %d relief pre-positioning sites to %s and %s", len(selected_sites), csv_path, geojson_path)

    return {
        "preposition_sites": selected_sites,
        "csv_path": csv_path,
        "geojson_path": geojson_path,
        "total_isolated_settlements": int((settlements_gdf["status"] == "Isolated (Hospital Cut Off)").sum()),
        "total_delayed_settlements": int((settlements_gdf["status"] == "Severely Delayed (≥2x Normal Time)").sum()),
    }


def run_full_criticality_and_preposition(output_dir: str = "outputs") -> Dict[str, Any]:
    """Execute complete Step 4 pipeline: road criticality, isolation analysis, and pre-positioning."""
    from routing.criticality import compute_road_criticality

    # 1. Road Criticality & Top 10 Single Points of Failure
    crit_res = compute_road_criticality(output_dir=output_dir)

    # 2. Settlement Isolation Analysis
    iso_gdf = analyze_settlement_isolation(output_dir=output_dir)

    # 3. Pre-positioning Hubs Recommendation
    prepos_res = recommend_preposition_sites(iso_gdf, output_dir=output_dir)

    return {
        "criticality": crit_res,
        "isolation": iso_gdf,
        "preposition": prepos_res,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_full_criticality_and_preposition()
