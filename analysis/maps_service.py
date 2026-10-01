"""
Maps API and Multi-Provider Basemap Integration Service.

Provides tile layer endpoints, folium map constructors with layer switching,
and optional Google Maps Platform API key integration for the GEOIMPATHON DSS.
"""

import os
from typing import Dict, Any, Optional, Tuple
import folium
import requests
from dotenv import load_dotenv

# Automatically load .env if present
load_dotenv()


# Registry of supported basemap tile providers with attribution and URL templates
BASEMAP_REGISTRY: Dict[str, Dict[str, Any]] = {
    "CartoDB Positron (Clean Light)": {
        "url": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        "max_zoom": 20,
        "subdomains": "abcd",
        "description": "Clean, low-saturation cartographic base ideal for multi-hazard color ramp contrast.",
    },
    "Google Maps Hybrid (Satellite)": {
        "url": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        "attr": "&copy; Google Maps (Satellite & Infrastructure Imagery)",
        "max_zoom": 20,
        "subdomains": "abc",
        "description": "High-resolution optical satellite imagery combined with labeled arterial road networks.",
    },
    "Google Maps Roadmap": {
        "url": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        "attr": "&copy; Google Maps",
        "max_zoom": 20,
        "subdomains": "abc",
        "description": "Standard vector road layout with highway shields and urban landmark labels.",
    },
    "Google Maps Terrain": {
        "url": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        "attr": "&copy; Google Maps",
        "max_zoom": 20,
        "subdomains": "abc",
        "description": "Topographic shaded relief highlighting elevation gradients and drainage basins.",
    },
    "OpenStreetMap Standard": {
        "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
        "max_zoom": 19,
        "subdomains": "abc",
        "description": "Standard community-driven open spatial database street layer.",
    },
    "Esri World Imagery (Satellite)": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "&copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        "max_zoom": 19,
        "subdomains": "",
        "description": "Uncluttered high-resolution satellite imagery for geomorphic and water body verification.",
    },
    "CartoDB Dark Matter": {
        "url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        "attr": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
        "max_zoom": 20,
        "subdomains": "abcd",
        "description": "High-contrast dark theme optimized for emergency operations center (EOC) dashboards.",
    },
}


def get_maps_api_key() -> str:
    """
    Retrieve configured Google Maps / Maps API key from environment or config.
    Returns empty string if not configured.
    """
    return (
        os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
        or os.getenv("MAPS_API_KEY", "").strip()
    )


def get_tile_config(style_name: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Return the URL template and attribution for a requested basemap style.
    """
    if style_name not in BASEMAP_REGISTRY:
        style_name = "CartoDB Positron (Clean Light)"

    cfg = BASEMAP_REGISTRY[style_name].copy()
    key = api_key if api_key is not None else get_maps_api_key()

    # Append key to Google Maps endpoints ONLY if a genuine non-dummy key is supplied
    if key and "google.com" in cfg["url"] and not key.startswith("AIzaSyA4Q3k_") and not "demo" in key.lower():
        separator = "&" if "?" in cfg["url"] else "?"
        cfg["url"] = f"{cfg['url']}{separator}key={key}"

    return cfg


def create_interactive_map(
    location: Tuple[float, float],
    zoom_start: int = 12,
    active_basemap: str = "CartoDB Positron (Clean Light)",
    api_key: Optional[str] = None,
    include_all_basemaps: bool = False,
    control_scale: bool = True,
) -> folium.Map:
    """
    Create a folium Map object initialized with the desired active basemap.
    Uses native Map tiles for guaranteed render reliability and fast load speed.

    Args:
        location: [lat, lon] tuple or list.
        zoom_start: Initial zoom level.
        active_basemap: Name of basemap to set as initially visible.
        api_key: Optional Google Maps API key.
        include_all_basemaps: If True, adds alternative basemap layers cleanly.
        control_scale: Whether to include graphic scale bar.

    Returns:
        Configured folium.Map instance.
    """
    if active_basemap not in BASEMAP_REGISTRY:
        active_basemap = "CartoDB Positron (Clean Light)"

    active_cfg = get_tile_config(active_basemap, api_key=api_key)

    # Initialize map with active basemap natively for 100% render reliability
    m = folium.Map(
        location=location,
        zoom_start=zoom_start,
        tiles=active_cfg["url"],
        attr=active_cfg["attr"],
        control_scale=control_scale,
    )

    if include_all_basemaps:
        # Add popular alternatives cleanly without overloading the browser
        alt_styles = [
            "CartoDB Positron (Clean Light)",
            "Google Maps Hybrid (Satellite)",
            "OpenStreetMap Standard",
        ]
        for name in alt_styles:
            if name == active_basemap:
                continue
            alt_cfg = get_tile_config(name, api_key=api_key)
            folium.TileLayer(
                tiles=alt_cfg["url"],
                attr=alt_cfg["attr"],
                name=name,
                overlay=False,
                control=True,
            ).add_to(m)

    return m


def geocode_address_google(
    query: str,
    api_key: Optional[str] = None,
    bounds: Optional[Tuple[float, float, float, float]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Geocode an address or landmark string using the Google Maps Geocoding API.
    
    Args:
        query: Address, junction, or landmark name.
        api_key: Google Maps Platform API key (reads from env if None).
        bounds: Optional (lon_min, lat_min, lon_max, lat_max) bounding box filter.

    Returns:
        Dict with keys {'name', 'lat', 'lon', 'formatted_address'} or None if lookup fails.
    """
    key = api_key if api_key is not None else get_maps_api_key()
    if not key or not query.strip():
        return None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params: Dict[str, Any] = {
        "address": query.strip(),
        "key": key,
    }

    if bounds:
        lon_min, lat_min, lon_max, lat_max = bounds
        params["bounds"] = f"{lat_min},{lon_min}|{lat_max},{lon_max}"

    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "OK" and data.get("results"):
                res = data["results"][0]
                loc = res["geometry"]["location"]
                return {
                    "name": query.strip(),
                    "lat": float(loc["lat"]),
                    "lon": float(loc["lng"]),
                    "formatted_address": res.get("formatted_address", query),
                    "source": "google_maps_api",
                }
    except Exception:
        pass

    return None
