"""Preflight validation and sample data initialization script.

Queries OpenStreetMap via OSMnx 2.x for the study area bounding box:
- Hospitals and clinics
- Shelter candidates (schools, community centres, places of worship)
- Settlements (place=*)
- Drive network graph (motorway, trunk, primary, secondary, tertiary, residential, unclassified)

Saves clean vector GeoJSON and GraphML into data/sample/ for offline app execution.
"""

import os
import sys
import logging
import time
import yaml
import osmnx as ox
import geopandas as gpd
import networkx as nx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preflight")


def run_preflight(config_path: str = "config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    b = cfg.get("bbox", {})
    # OSMnx 2.x bbox format: (left, bottom, right, top) = (lon_min, lat_min, lon_max, lat_max)
    lon_min = float(b.get("lon_min", 80.03))
    lat_min = float(b.get("lat_min", 12.80))
    lon_max = float(b.get("lon_max", 80.22))
    lat_max = float(b.get("lat_max", 12.98))
    bbox = (lon_min, lat_min, lon_max, lat_max)

    logger.info("Starting Preflight OSM extraction for bbox: %s", bbox)
    out_dir = "data/sample"
    os.makedirs(out_dir, exist_ok=True)

    ox.settings.timeout = 300
    ox.settings.use_cache = True
    ox.settings.log_console = False

    # 1. Hospitals and Clinics
    hosp_file = os.path.join(out_dir, "hospitals.geojson")
    logger.info("Step 1/4: Fetching Hospitals and Clinics...")
    try:
        raw_hosp = ox.features_from_bbox(bbox=bbox, tags={"amenity": ["hospital", "clinic"]})
        raw_hosp["geometry"] = raw_hosp["geometry"].centroid
        raw_hosp["name"] = raw_hosp["name"].fillna("Medical Facility")
        cols = [c for c in ["name", "amenity", "healthcare", "emergency", "geometry"] if c in raw_hosp.columns]
        gdf_hosp = raw_hosp[cols].copy()
        gdf_hosp["facility_id"] = [f"hosp_{i}" for i in range(len(gdf_hosp))]
        gdf_hosp.to_file(hosp_file, driver="GeoJSON")
        num_hosp = len(gdf_hosp[gdf_hosp["amenity"] == "hospital"])
        num_clinics = len(gdf_hosp[gdf_hosp["amenity"] == "clinic"])
        logger.info("Found %d hospitals and %d clinics. Saved to %s", num_hosp, num_clinics, hosp_file)
    except Exception as e:
        logger.error("Error fetching hospitals: %s", e)
        num_hosp, num_clinics = 0, 0

    # 2. Candidate Shelters
    shelt_file = os.path.join(out_dir, "shelters.geojson")
    logger.info("Step 2/4: Fetching Candidate Shelters...")
    try:
        shelter_tags = {"amenity": ["school", "community_centre", "townhall", "place_of_worship"]}
        raw_shelt = ox.features_from_bbox(bbox=bbox, tags=shelter_tags)
        raw_shelt["geometry"] = raw_shelt["geometry"].centroid
        raw_shelt["name"] = raw_shelt["name"].fillna("Designated Public Shelter")
        cols = [c for c in ["name", "amenity", "building", "geometry"] if c in raw_shelt.columns]
        gdf_shelt = raw_shelt[cols].copy()
        gdf_shelt["shelter_id"] = [f"shelt_{i}" for i in range(len(gdf_shelt))]
        gdf_shelt.to_file(shelt_file, driver="GeoJSON")
        logger.info("Found %d shelters. Saved to %s", len(gdf_shelt), shelt_file)
        num_shelters = len(gdf_shelt)
    except Exception as e:
        logger.error("Error fetching shelters: %s", e)
        num_shelters = 0

    # 3. Settlements (place=*)
    sett_file = os.path.join(out_dir, "settlements.geojson")
    logger.info("Step 3/4: Fetching Settlements...")
    try:
        raw_sett = ox.features_from_bbox(bbox=bbox, tags={"place": True})
        raw_sett["geometry"] = raw_sett["geometry"].centroid
        raw_sett["name"] = raw_sett["name"].fillna("Local Settlement")
        cols = [c for c in ["name", "place", "population", "geometry"] if c in raw_sett.columns]
        gdf_sett = raw_sett[cols].copy()
        gdf_sett["settlement_id"] = [f"sett_{i}" for i in range(len(gdf_sett))]
        gdf_sett.to_file(sett_file, driver="GeoJSON")
        logger.info("Found %d settlements. Saved to %s", len(gdf_sett), sett_file)
        num_settlements = len(gdf_sett)
    except Exception as e:
        logger.error("Error fetching settlements: %s", e)
        num_settlements = 0

    # 4. Drive Network Graph
    graph_file = os.path.join(out_dir, "drive_network.graphml")
    logger.info("Step 4/4: Downloading drive network (motorway, trunk, primary, secondary, tertiary, residential)...")
    try:
        # Filter for actual vehicle passable roads to keep graph concise, fast, and avoid unpaved footpaths
        filter_str = (
            '["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified"]'
        )
        t0 = time.time()
        G = ox.graph_from_bbox(bbox=bbox, custom_filter=filter_str, simplify=True)
        t_fetch = time.time() - t0
        logger.info("Downloaded graph in %.1f seconds: %d nodes, %d edges", t_fetch, len(G.nodes), len(G.edges))

        # Add free-flow edge speeds and travel times
        G = ox.routing.add_edge_speeds(G)
        G = ox.routing.add_edge_travel_times(G)

        # Save to disk
        ox.save_graphml(G, graph_file)
        logger.info("Serialized graph to %s (size: %.2f MB)", graph_file, os.path.getsize(graph_file) / (1024 * 1024))
        num_nodes = len(G.nodes)
        num_edges = len(G.edges)
    except Exception as e:
        logger.error("Error downloading drive network: %s", e)
        num_nodes, num_edges = 0, 0

    print("\n" + "=" * 60)
    print("PREFLIGHT SUMMARY - OPENSTREETMAP DATA COUNTS")
    print("=" * 60)
    print(f"Hospitals:                {num_hosp}")
    print(f"Clinics:                  {num_clinics}")
    print(f"Total Medical Facilities: {num_hosp + num_clinics}")
    print(f"Shelter Candidates:       {num_shelters}")
    print(f"Settlements (place=*):    {num_settlements}")
    print(f"Drive Network Nodes:      {num_nodes}")
    print(f"Drive Network Edges:      {num_edges}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_preflight()
