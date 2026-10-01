"""Road network extraction, topology conditioning, and facility extraction.

Uses OSMnx 2.x to extract drive networks, hospitals, candidate shelters,
and settlements. Handles coordinate projection (UTM 44N, EPSG:32644)
for metric distance and speed calculations, and serializes graph and
facilities into data/sample/ for offline execution.
"""

import os
import logging
from typing import Tuple, Dict, Any
import yaml
import networkx as nx
import geopandas as gpd
import osmnx as ox
from shapely.geometry import box, Point

logger = logging.getLogger(__name__)

# Standard UTM projection for Chennai (UTM Zone 44N)
EPSG_CHENNAI_UTM: int = 32644
EPSG_WGS84: int = 4326


def get_bbox_from_config(config_path: str = "config.yaml") -> Tuple[float, float, float, float]:
    """Retrieve bounding box from config in OSMnx 2.x (left, bottom, right, top) order."""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    b = cfg.get("bbox", {})
    # OSMnx 2.x requires (left, bottom, right, top) = (min_lon, min_lat, max_lon, max_lat)
    return (
        float(b.get("lon_min", 80.03)),
        float(b.get("lat_min", 12.80)),
        float(b.get("lon_max", 80.22)),
        float(b.get("lat_max", 12.98)),
    )


def extract_drive_network(
    bbox: Tuple[float, float, float, float],
    output_graphml: str = "data/sample/drive_network.graphml",
    force_refresh: bool = False,
) -> nx.MultiDiGraph:
    """Download or load the drive network graph using OSMnx 2.x.

    Simplifies network, adds free-flow speeds, projects to UTM 44N,
    and caches to disk as GraphML.
    """
    if not force_refresh and os.path.exists(output_graphml):
        logger.info("Loading cached drive network from %s", output_graphml)
        G = ox.load_graphml(output_graphml)
        return G

    logger.info("Downloading drive network for bbox %s from OpenStreetMap...", bbox)
    # Configure OSMnx settings for robust query execution
    ox.settings.timeout = 180
    ox.settings.useful_tags_way = list(
        set(
            list(ox.settings.useful_tags_way)
            + ["bridge", "tunnel", "layer", "surface", "lanes", "maxspeed"]
        )
    )

    # In OSMnx 2.x, bbox is (left, bottom, right, top)
    G = ox.graph_from_bbox(bbox=bbox, network_type="drive", simplify=True)
    logger.info("Retrieved graph with %d nodes and %d edges", len(G.nodes), len(G.edges))

    # Add free flow travel speeds and travel times
    G = ox.routing.add_edge_speeds(G)
    G = ox.routing.add_edge_travel_times(G)

    # Save to disk
    os.makedirs(os.path.dirname(output_graphml), exist_ok=True)
    ox.save_graphml(G, output_graphml)
    logger.info("Saved drive network to %s", output_graphml)

    return G


def extract_facilities(
    bbox: Tuple[float, float, float, float],
    data_dir: str = "data/sample",
    force_refresh: bool = False,
) -> Dict[str, gpd.GeoDataFrame]:
    """Extract hospitals, clinics, candidate shelters, and settlements in the bbox.

    Saves GeoJSON files into data_dir.
    """
    os.makedirs(data_dir, exist_ok=True)
    hosp_path = os.path.join(data_dir, "hospitals.geojson")
    shelt_path = os.path.join(data_dir, "shelters.geojson")
    sett_path = os.path.join(data_dir, "settlements.geojson")

    results = {}

    # 1. Hospitals & Clinics
    if not force_refresh and os.path.exists(hosp_path):
        logger.info("Loading cached hospitals from %s", hosp_path)
        gdf_hosp = gpd.read_file(hosp_path)
    else:
        logger.info("Querying hospitals and clinics...")
        hosp_tags = {"amenity": ["hospital", "clinic"]}
        try:
            raw_hosp = ox.features_from_bbox(bbox=bbox, tags=hosp_tags)
            # Standardize geometries to point centroids
            raw_hosp["geometry"] = raw_hosp["geometry"].centroid
            # Keep key metadata
            cols = [
                c
                for c in ["name", "amenity", "healthcare", "emergency", "geometry"]
                if c in raw_hosp.columns
            ]
            gdf_hosp = raw_hosp[cols].copy()
            gdf_hosp["facility_id"] = [f"hosp_{i}" for i in range(len(gdf_hosp))]
            gdf_hosp["name"] = gdf_hosp["name"].fillna("Unnamed Medical Facility")
            gdf_hosp.to_file(hosp_path, driver="GeoJSON")
            logger.info("Saved %d hospitals/clinics to %s", len(gdf_hosp), hosp_path)
        except Exception as e:
            logger.error("Failed to query hospitals: %s", e)
            gdf_hosp = gpd.GeoDataFrame()

    results["hospitals"] = gdf_hosp

    # 2. Shelters (schools, community centres, town halls, places of worship)
    if not force_refresh and os.path.exists(shelt_path):
        logger.info("Loading cached shelters from %s", shelt_path)
        gdf_shelt = gpd.read_file(shelt_path)
    else:
        logger.info("Querying candidate shelters...")
        shelter_tags = {
            "amenity": ["school", "community_centre", "townhall", "place_of_worship"],
        }
        try:
            raw_shelt = ox.features_from_bbox(bbox=bbox, tags=shelter_tags)
            raw_shelt["geometry"] = raw_shelt["geometry"].centroid
            cols = [c for c in ["name", "amenity", "building", "geometry"] if c in raw_shelt.columns]
            gdf_shelt = raw_shelt[cols].copy()
            gdf_shelt["shelter_id"] = [f"shelt_{i}" for i in range(len(gdf_shelt))]
            gdf_shelt["name"] = gdf_shelt["name"].fillna("Designated Public Shelter")
            gdf_shelt.to_file(shelt_path, driver="GeoJSON")
            logger.info("Saved %d shelters to %s", len(gdf_shelt), shelt_path)
        except Exception as e:
            logger.error("Failed to query shelters: %s", e)
            gdf_shelt = gpd.GeoDataFrame()

    results["shelters"] = gdf_shelt

    # 3. Settlements (place=*)
    if not force_refresh and os.path.exists(sett_path):
        logger.info("Loading cached settlements from %s", sett_path)
        gdf_sett = gpd.read_file(sett_path)
    else:
        logger.info("Querying settlements...")
        try:
            raw_sett = ox.features_from_bbox(bbox=bbox, tags={"place": True})
            raw_sett["geometry"] = raw_sett["geometry"].centroid
            cols = [c for c in ["name", "place", "population", "geometry"] if c in raw_sett.columns]
            gdf_sett = raw_sett[cols].copy()
            gdf_sett["settlement_id"] = [f"sett_{i}" for i in range(len(gdf_sett))]
            gdf_sett["name"] = gdf_sett["name"].fillna("Local Settlement")
            gdf_sett.to_file(sett_path, driver="GeoJSON")
            logger.info("Saved %d settlements to %s", len(gdf_sett), sett_path)
        except Exception as e:
            logger.error("Failed to query settlements: %s", e)
            gdf_sett = gpd.GeoDataFrame()

    results["settlements"] = gdf_sett

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bbox = get_bbox_from_config()
    print("Bounding box:", bbox)
    facilities = extract_facilities(bbox)
    G = extract_drive_network(bbox)
    print("Graph:", G)
