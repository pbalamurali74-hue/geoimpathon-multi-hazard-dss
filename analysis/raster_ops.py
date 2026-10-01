"""Geospatial raster operations, GeoTIFF I/O, and Folium overlay rendering.

Provides utilities for:
- Writing georeferenced GeoTIFFs using rasterio
- Exporting RGBA PNGs using the exact design theme color ramp
- Sampling raster values at vector points and along line geometries
- Creating 500m regular hexagonal/square vector analysis grids
"""

import os
import logging
from typing import Tuple, List, Optional
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
import matplotlib.colors as mcolors
from PIL import Image
import geopandas as gpd
from shapely.geometry import box, Polygon, Point

logger = logging.getLogger(__name__)


def create_raster_profile(
    bounds: Tuple[float, float, float, float],
    shape: Tuple[int, int],
    crs: str = "EPSG:4326",
    dtype: str = "float32",
    nodata: float = -9999.0,
) -> dict:
    """Create a rasterio profile dictionary from bounding box and array shape.

    Args:
        bounds: (lon_min, lat_min, lon_max, lat_max)
        shape: (rows, cols)
        crs: Coordinate Reference System (default EPSG:4326)
    """
    rows, cols = shape
    lon_min, lat_min, lon_max, lat_max = bounds
    transform = from_bounds(lon_min, lat_min, lon_max, lat_max, cols, rows)
    return {
        "driver": "GTiff",
        "height": rows,
        "width": cols,
        "count": 1,
        "dtype": dtype,
        "crs": CRS.from_string(crs),
        "transform": transform,
        "nodata": nodata,
        "compress": "lzw",
    }


def save_geotiff(
    arr: np.ndarray,
    output_path: str,
    bounds: Tuple[float, float, float, float],
    nodata: float = -9999.0,
) -> str:
    """Save a 2D numpy array as a georeferenced GeoTIFF."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    profile = create_raster_profile(bounds, arr.shape, dtype=str(arr.dtype), nodata=nodata)

    # Replace NaNs with nodata
    data = arr.copy()
    data[np.isnan(data)] = nodata

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data, 1)

    logger.info("Saved GeoTIFF: %s (shape: %s, size: %.2f MB)", output_path, arr.shape, os.path.getsize(output_path) / (1024 * 1024))
    return output_path


def export_rgba_png(
    arr: np.ndarray,
    output_path: str,
    cmap_colors: List[str],
    vmin: float = 0.0,
    vmax: float = 1.0,
    opacity: float = 0.70,
    nodata_mask: Optional[np.ndarray] = None,
) -> str:
    """Convert a 2D continuous raster into an RGBA PNG with alpha transparency.

    Used by Folium ImageOverlay for lightweight, responsive web display.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Construct continuous colormap
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_ramp", cmap_colors)

    # Normalize values between vmin and vmax
    norm_arr = np.clip((arr - vmin) / (vmax - vmin + 1e-12), 0.0, 1.0)

    # Map to RGBA in [0, 1]
    rgba = cmap(norm_arr)

    # Scale to [0, 255] uint8
    rgba_uint8 = (rgba * 255).astype(np.uint8)

    # Set alpha channel: opacity for valid pixels, 0 for NaNs / nodata
    alpha_channel = (np.ones_like(arr) * (opacity * 255)).astype(np.uint8)
    alpha_channel[np.isnan(arr)] = 0
    if nodata_mask is not None:
        alpha_channel[nodata_mask] = 0

    rgba_uint8[:, :, 3] = alpha_channel

    img = Image.fromarray(rgba_uint8, mode="RGBA")
    img.save(output_path, format="PNG", optimize=True)
    logger.info("Exported RGBA PNG overlay: %s (size: %.1f KB)", output_path, os.path.getsize(output_path) / 1024)
    return output_path


def create_vector_grid(
    bounds: Tuple[float, float, float, float],
    cell_size_m: float = 500.0,
    crs_metric: int = 32644,
) -> gpd.GeoDataFrame:
    """Generate a regular square grid across the study bounding box.

    Returns:
        GeoDataFrame with grid polygons and unique cell_id in EPSG:4326.
    """
    lon_min, lat_min, lon_max, lat_max = bounds
    box_geom = box(lon_min, lat_min, lon_max, lat_max)
    gdf_bound = gpd.GeoDataFrame(geometry=[box_geom], crs=4326).to_crs(crs_metric)

    minx, miny, maxx, maxy = gdf_bound.total_bounds

    x_coords = np.arange(minx, maxx + cell_size_m, cell_size_m)
    y_coords = np.arange(miny, maxy + cell_size_m, cell_size_m)

    polygons = []
    cell_ids = []
    idx = 0
    for x in x_coords[:-1]:
        for y in y_coords[:-1]:
            poly = box(x, y, x + cell_size_m, y + cell_size_m)
            polygons.append(poly)
            cell_ids.append(f"cell_{idx:05d}")
            idx += 1

    grid_gdf = gpd.GeoDataFrame({"cell_id": cell_ids, "geometry": polygons}, crs=crs_metric)
    grid_wgs84 = grid_gdf.to_crs(4326)
    return grid_wgs84


def sample_raster_at_points(
    arr: np.ndarray,
    bounds: Tuple[float, float, float, float],
    points_gdf: gpd.GeoDataFrame,
) -> np.ndarray:
    """Sample 2D raster values at point locations in points_gdf (EPSG:4326)."""
    lon_min, lat_min, lon_max, lat_max = bounds
    rows, cols = arr.shape

    xs = points_gdf.geometry.x.values
    ys = points_gdf.geometry.y.values

    col_indices = np.clip(((xs - lon_min) / (lon_max - lon_min) * cols).astype(int), 0, cols - 1)
    # Latitude is inverted (top to bottom)
    row_indices = np.clip(((lat_max - ys) / (lat_max - lat_min) * rows).astype(int), 0, rows - 1)

    return arr[row_indices, col_indices]
