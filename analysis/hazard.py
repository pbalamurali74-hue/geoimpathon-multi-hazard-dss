"""Multi-hazard modeling, AHP weighting, risk classification, and ranking.

Executes:
1. Normalization of flood and slope-instability indicators (cost vs benefit)
2. AHP principal eigenvector calculation (asserting CR < 0.10)
3. Shannon Entropy weight cross-check & Spearman rank correlation
4. Multi-hazard weighted linear combination (0.70 flood / 0.30 slope)
5. Percentile-based risk classification (Low, Moderate, High, Very High)
6. Ranking of settlements and 500m grid cells by Risk x Exposure
7. Exporting GeoTIFFs and colorized RGBA PNGs using theme.py palette
"""

import os
import logging
from typing import Dict, Tuple, Any, List, Optional
import yaml
import numpy as np
import rasterio
import geopandas as gpd
import pandas as pd

from app.theme import RISK_COLOR_LIST, COLOR_DEEP_BLUE, COLOR_LIGHT_BLUE
from analysis.mcdm import (
    calculate_ahp_weights,
    normalize_minmax,
    fuzzy_sigmoidal_membership,
    calculate_entropy_weights,
    compare_ahp_and_entropy_maps,
)
from analysis.raster_ops import (
    save_geotiff,
    export_rgba_png,
    create_vector_grid,
    sample_raster_at_points,
)

logger = logging.getLogger(__name__)


# 7x7 AHP Comparison Matrix for Flood Susceptibility
# Order: HAND, Slope, Built-Up, DistWater, Elevation, NDVI, Rain
AHP_FLOOD_MATRIX = np.array([
    [1.0,   2.0,   3.0,   4.0,   4.0,   5.0,   6.0],  # HAND
    [1/2,   1.0,   2.0,   3.0,   3.0,   4.0,   5.0],  # Slope
    [1/3,   1/2,   1.0,   2.0,   2.0,   3.0,   4.0],  # Built-Up
    [1/4,   1/3,   1/2,   1.0,   1.0,   3.0,   3.0],  # Dist Water
    [1/4,   1/3,   1/2,   1.0,   1.0,   2.0,   3.0],  # Elevation
    [1/5,   1/4,   1/3,   1/3,   1/2,   1.0,   2.0],  # NDVI
    [1/6,   1/5,   1/4,   1/3,   1/3,   1/2,   1.0],  # Rain
], dtype=np.float64)

FLOOD_CRITERIA = ["HAND", "Slope", "Built-Up", "DistWater", "Elevation", "NDVI", "Rainfall"]


# 7x7 AHP Comparison Matrix for Slope-Instability & Erosion Susceptibility
# Order: Slope, Curvature, DistCutSlope (roads), Relief, DistStreams, LandCover, Rain
AHP_SLOPE_MATRIX = np.array([
    [1.0,   3.0,   3.0,   4.0,   5.0,   6.0,   7.0],  # Slope
    [1/3,   1.0,   1.0,   2.0,   3.0,   4.0,   5.0],  # Curvature
    [1/3,   1.0,   1.0,   2.0,   3.0,   4.0,   5.0],  # DistCutSlope
    [1/4,   1/2,   1/2,   1.0,   2.0,   3.0,   4.0],  # Relief
    [1/5,   1/3,   1/3,   1/2,   1.0,   2.0,   3.0],  # DistStreams
    [1/6,   1/4,   1/4,   1/3,   1/2,   1.0,   2.0],  # LandCover
    [1/7,   1/5,   1/5,   1/4,   1/3,   1/2,   1.0],  # Rain
], dtype=np.float64)

SLOPE_CRITERIA = ["Slope", "Curvature", "CutSlopes", "Relief", "DistStreams", "LandCover", "Rainfall"]


def run_hazard_pipeline(
    config_path: str = "config.yaml",
    data_dir: str = "data/sample",
    output_dir: str = "outputs",
) -> Dict[str, Any]:
    """Execute the complete multi-hazard analysis and export all layers."""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    b = cfg.get("bbox", {})
    bounds = (float(b["lon_min"]), float(b["lat_min"]), float(b["lon_max"]), float(b["lat_max"]))
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # 1. Load Base Rasters from data_dir
    def load_raster(name: str) -> np.ndarray:
        p = os.path.join(data_dir, f"{name}.tif")
        with rasterio.open(p) as src:
            return src.read(1).astype(np.float32)

    dem = load_raster("dem")
    slope_deg = load_raster("slope_deg")
    curvature = load_raster("curvature")
    hand = load_raster("hand")
    dist_to_water = load_raster("dist_to_water")
    built_up = load_raster("built_up")
    ndvi = load_raster("ndvi")
    chirps_rain = load_raster("chirps_rain")

    # Local relief: max minus min in moving window
    from scipy.ndimage import maximum_filter, minimum_filter
    relief = maximum_filter(dem, size=5) - minimum_filter(dem, size=5)

    # 2. Normalize Indicators
    logger.info("Normalizing flood indicators...")
    norm_hand_flood = normalize_minmax(hand, cost_direction=False)        # Lower HAND = Higher risk
    norm_slope_flood = normalize_minmax(slope_deg, cost_direction=False)  # Flatter slope = Higher risk
    norm_built_flood = normalize_minmax(built_up, cost_direction=True)     # More built = Higher runoff
    norm_water_flood = normalize_minmax(dist_to_water, cost_direction=False) # Closer to water = Higher risk
    norm_elev_flood = normalize_minmax(dem, cost_direction=False)         # Lower elevation = Higher risk
    norm_ndvi_flood = normalize_minmax(ndvi, cost_direction=False)        # Lower NDVI = Higher risk
    norm_rain_flood = normalize_minmax(chirps_rain, cost_direction=True)  # Higher rain = Higher risk

    # Benchmark: Fuzzy sigmoidal membership for HAND (midpoint=3.0m, beta=1.2)
    fuzzy_hand = fuzzy_sigmoidal_membership(hand, midpoint=3.0, beta=1.2, decreasing=True)

    # 3. Calculate AHP Weights & Assert CR < 0.10
    w_flood, lmax_f, ci_f, cr_f = calculate_ahp_weights(AHP_FLOOD_MATRIX, FLOOD_CRITERIA)
    assert cr_f < 0.10, f"Flood AHP CR {cr_f:.4f} exceeds 0.10!"

    # 4. Compute Flood Susceptibility Index
    flood_indicators = np.stack([
        norm_hand_flood,
        norm_slope_flood,
        norm_built_flood,
        norm_water_flood,
        norm_elev_flood,
        norm_ndvi_flood,
        norm_rain_flood,
    ], axis=0)

    flood_hazard = np.tensordot(w_flood, flood_indicators, axes=(0, 0)).astype(np.float32)

    # 5. Normalize Slope-Instability Indicators
    logger.info("Normalizing slope-instability indicators...")
    norm_slope_inst = normalize_minmax(slope_deg, cost_direction=True)     # Steeper slope = Higher risk
    norm_curv_inst = normalize_minmax(curvature, cost_direction=True)      # Concave = Higher risk
    # Cut slopes proxy (proximity to roads and quarries)
    norm_cuts_inst = normalize_minmax(dist_to_water, cost_direction=False) # Proxy
    norm_relief_inst = normalize_minmax(relief, cost_direction=True)       # Higher relief = Higher energy
    norm_stream_inst = normalize_minmax(dist_to_water, cost_direction=False)
    norm_bare_inst = normalize_minmax(1.0 - ndvi, cost_direction=True)     # Lower vegetation = Higher erosion
    norm_rain_inst = normalize_minmax(chirps_rain, cost_direction=True)

    w_slope, lmax_s, ci_s, cr_s = calculate_ahp_weights(AHP_SLOPE_MATRIX, SLOPE_CRITERIA)
    assert cr_s < 0.10, f"Slope AHP CR {cr_s:.4f} exceeds 0.10!"

    slope_indicators = np.stack([
        norm_slope_inst,
        norm_curv_inst,
        norm_cuts_inst,
        norm_relief_inst,
        norm_stream_inst,
        norm_bare_inst,
        norm_rain_inst,
    ], axis=0)

    slope_hazard = np.tensordot(w_slope, slope_indicators, axes=(0, 0)).astype(np.float32)

    # 6. Objective Entropy Weight Method Cross-Check
    logger.info("Computing Shannon Entropy weights cross-check...")
    w_entropy_flood = calculate_entropy_weights(flood_indicators)
    flood_hazard_entropy = np.tensordot(w_entropy_flood, flood_indicators, axes=(0, 0)).astype(np.float32)
    rho_spearman, pval_spearman = compare_ahp_and_entropy_maps(flood_hazard, flood_hazard_entropy)

    # 7. Multi-Hazard Composite Risk Index
    hw = cfg.get("hazard_weights", {"flood": 0.70, "slope_instability": 0.30})
    w_f_comp = float(hw.get("flood", 0.70))
    w_s_comp = float(hw.get("slope_instability", 0.30))
    assert np.isclose(w_f_comp + w_s_comp, 1.0), "Multi-hazard weights must sum to 1.0!"

    multihazard_risk = (w_f_comp * flood_hazard + w_s_comp * slope_hazard).astype(np.float32)

    # 8. Percentile-based Risk Categorization
    p_cfg = cfg.get("risk_percentiles", {"low_max": 50.0, "moderate_max": 80.0, "high_max": 95.0})
    p50 = float(np.percentile(multihazard_risk, p_cfg["low_max"]))
    p80 = float(np.percentile(multihazard_risk, p_cfg["moderate_max"]))
    p95 = float(np.percentile(multihazard_risk, p_cfg["high_max"]))

    logger.info("Risk Percentile Breaks: Low < %.4f <= Moderate < %.4f <= High < %.4f <= Very High", p50, p80, p95)

    risk_classified = np.zeros_like(multihazard_risk, dtype=np.uint8)
    risk_classified[multihazard_risk < p50] = 1   # Low
    risk_classified[(multihazard_risk >= p50) & (multihazard_risk < p80)] = 2  # Moderate
    risk_classified[(multihazard_risk >= p80) & (multihazard_risk < p95)] = 3  # High
    risk_classified[multihazard_risk >= p95] = 4  # Very High

    # Assert all pixels classified
    assert np.all(risk_classified >= 1) and np.all(risk_classified <= 4), "Risk classification must cover 100% of cells!"

    # Area distribution
    total_cells = risk_classified.size
    area_pct = {
        "Low": float(np.sum(risk_classified == 1) / total_cells * 100.0),
        "Moderate": float(np.sum(risk_classified == 2) / total_cells * 100.0),
        "High": float(np.sum(risk_classified == 3) / total_cells * 100.0),
        "Very High": float(np.sum(risk_classified == 4) / total_cells * 100.0),
    }
    logger.info("Area Distribution: %s", area_pct)

    # 9. Save GeoTIFFs and RGBA PNGs
    def export_layer(arr: np.ndarray, name: str, cmap: List[str], vmin: float = 0.0, vmax: float = 1.0):
        # Save to outputs/
        gtiff_out = os.path.join(output_dir, f"{name}.tif")
        png_out = os.path.join(output_dir, f"{name}.png")
        save_geotiff(arr, gtiff_out, bounds)
        export_rgba_png(arr, png_out, cmap, vmin=vmin, vmax=vmax)

        # Also copy PNG and GeoTIFF into data/sample/ for Streamlit app
        gtiff_sample = os.path.join(data_dir, f"{name}.tif")
        png_sample = os.path.join(data_dir, f"{name}.png")
        save_geotiff(arr, gtiff_sample, bounds)
        export_rgba_png(arr, png_sample, cmap, vmin=vmin, vmax=vmax)

    export_layer(flood_hazard, "flood_hazard", RISK_COLOR_LIST, 0.0, 1.0)
    export_layer(slope_hazard, "slope_instability", RISK_COLOR_LIST, 0.0, 1.0)
    export_layer(slope_deg, "dem_slope_deg", [COLOR_LIGHT_BLUE, "#8DB8E0", "#F4A259", "#B8470C"], 0.0, 30.0)
    export_layer(multihazard_risk, "multihazard_risk", RISK_COLOR_LIST, 0.0, 1.0)
    export_layer(built_up, "builtup_exposure", ["#FFFFFF", COLOR_LIGHT_BLUE, "#2E75B6", COLOR_DEEP_BLUE], 0.0, 1.0)

    # 10. Risk Ranking: 500m Grid Cells
    logger.info("Ranking 500m vector grid cells by Risk x Exposure...")
    grid_gdf = create_vector_grid(bounds, cell_size_m=float(cfg.get("ranking_grid_size_m", 500.0)))
    grid_centroids = gpd.GeoDataFrame(geometry=grid_gdf.geometry.centroid, crs=4326)

    grid_risk = sample_raster_at_points(multihazard_risk, bounds, grid_centroids)
    grid_expo = sample_raster_at_points(built_up, bounds, grid_centroids)

    grid_gdf["mean_risk"] = np.round(grid_risk, 4)
    grid_gdf["built_exposure"] = np.round(grid_expo, 4)
    grid_gdf["risk_exposure_score"] = np.round(grid_risk * grid_expo, 4)
    grid_gdf["risk_tier"] = np.where(
        grid_risk >= p95, "Very High",
        np.where(grid_risk >= p80, "High",
        np.where(grid_risk >= p50, "Moderate", "Low"))
    )

    ranked_grid = grid_gdf.sort_values(by="risk_exposure_score", ascending=False).reset_index(drop=True)
    ranked_grid["rank"] = range(1, len(ranked_grid) + 1)

    # Export Top 50 Grid Cells
    top_grid = ranked_grid.head(50)
    top_grid.to_file(os.path.join(output_dir, "top_grid_cells.geojson"), driver="GeoJSON")
    top_grid.drop(columns="geometry").to_csv(os.path.join(output_dir, "top_grid_cells.csv"), index=False)
    top_grid.to_file(os.path.join(data_dir, "top_grid_cells.geojson"), driver="GeoJSON")
    top_grid.drop(columns="geometry").to_csv(os.path.join(data_dir, "top_grid_cells.csv"), index=False)

    # 11. Risk Ranking: Settlements
    logger.info("Ranking settlements by Risk x Exposure...")
    sett_path = os.path.join(data_dir, "settlements.geojson")
    if os.path.exists(sett_path):
        sett_gdf = gpd.read_file(sett_path)
        sett_risk = sample_raster_at_points(multihazard_risk, bounds, sett_gdf)
        sett_expo = sample_raster_at_points(built_up, bounds, sett_gdf)

        sett_gdf["mean_risk"] = np.round(sett_risk, 4)
        sett_gdf["built_exposure"] = np.round(sett_expo, 4)
        sett_gdf["risk_exposure_score"] = np.round(sett_risk * sett_expo, 4)
        sett_gdf["risk_tier"] = np.where(
            sett_risk >= p95, "Very High",
            np.where(sett_risk >= p80, "High",
            np.where(sett_risk >= p50, "Moderate", "Low"))
        )

        ranked_sett = sett_gdf.sort_values(by="risk_exposure_score", ascending=False).reset_index(drop=True)
        ranked_sett["rank"] = range(1, len(ranked_sett) + 1)

        # Export Ranked Settlements
        ranked_sett.to_file(os.path.join(output_dir, "top_settlements.geojson"), driver="GeoJSON")
        ranked_sett.drop(columns="geometry").to_csv(os.path.join(output_dir, "top_settlements.csv"), index=False)
        ranked_sett.to_file(os.path.join(data_dir, "top_settlements.geojson"), driver="GeoJSON")
        ranked_sett.drop(columns="geometry").to_csv(os.path.join(data_dir, "top_settlements.csv"), index=False)

    return {
        "cr_flood": float(cr_f),
        "cr_slope": float(cr_s),
        "spearman_rho": float(rho_spearman),
        "spearman_pval": float(pval_spearman),
        "percentile_breaks": {"p50": p50, "p80": p80, "p95": p95},
        "area_pct": area_pct,
        "flood_weights": {k: float(v) for k, v in zip(FLOOD_CRITERIA, w_flood)},
        "slope_weights": {k: float(v) for k, v in zip(SLOPE_CRITERIA, w_slope)},
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = run_hazard_pipeline()
    print("Hazard Pipeline Results:", results)
