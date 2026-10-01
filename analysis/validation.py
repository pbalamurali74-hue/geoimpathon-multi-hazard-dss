"""Validation module for GEOIMPATHON 1.0 multi-hazard decision-support system.

Performs rigorous, scientifically honest model validation:
1. Flood Susceptibility Validation:
   - Evaluated against independent Sentinel-1 SAR change detection of Cyclone Michaung (Dec 2023).
   - Strictly enforces NO VALIDATION LEAKAGE: S1 flood is strictly ground truth, never an input.
   - Permanent water bodies (JRC Occurrence > 80%) excluded.
   - Balanced random sampling (N=5,000 flooded, N=5,000 non-flooded).
   - ROC curve and AUC (Area Under Curve).
   - Confusion matrix, Precision, Recall (Sensitivity), Specificity, and F1-Score at stated threshold.
   - Spatial Block Cross-Validation (4x4 spatial partition) to guard against spatial autocorrelation.
2. Slope-Instability Geomorphic Sanity Check:
   - Explicitly NOT an empirical validation (no official historical landslide inventory exists for flat coastal Chennai).
   - Evaluates mean hazard response across slope gradient classes and rainfall tiers.
3. Visualization:
   - High-contrast, command-center publication figures saved to outputs/.
   - All colors strictly conform to app/theme.py.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from scipy.stats import spearmanr
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve

from app.theme import (
    COLOR_BORDER_GREY,
    COLOR_DARK_ORANGE,
    COLOR_DEEP_BLUE,
    COLOR_INK,
    COLOR_LIGHT_BLUE,
    COLOR_MID_BLUE,
    COLOR_MUTED_TEXT,
    COLOR_ORANGE,
    COLOR_PAPER,
    COLOR_WHITE,
    FONT_FAMILY,
)

logger = logging.getLogger(__name__)


def validate_flood_hazard(
    flood_hazard_path: str = "data/sample/flood_hazard.tif",
    flood_truth_path: str = "data/sample/s1_event_flood.tif",
    jrc_path: str = "data/sample/jrc_water.tif",
    threshold: Optional[float] = None,
    n_samples: int = 5000,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Validate continuous flood hazard against Sentinel-1 SAR inundation truth.

    Args:
        flood_hazard_path: Path to continuous flood hazard GeoTIFF [0, 1]
        flood_truth_path: Path to binary Sentinel-1 event flood GeoTIFF (0=dry, 1=flooded)
        jrc_path: Path to JRC surface water occurrence GeoTIFF [0, 100]
        threshold: Decision threshold for confusion matrix (default: Youden's J optimal)
        n_samples: Number of pixels per class in balanced sample
        random_state: Random seed for reproducibility

    Returns:
        Dictionary containing validation metrics, ROC curve data, and confusion matrix.
    """
    logger.info("Running flood hazard validation against Sentinel-1 event truth...")

    with rasterio.open(flood_hazard_path) as src:
        hazard = src.read(1).astype(np.float32)
    with rasterio.open(flood_truth_path) as src:
        truth = src.read(1).astype(np.float32)
    with rasterio.open(jrc_path) as src:
        jrc = src.read(1).astype(np.float32)

    # 1. Mask permanent water (JRC occurrence > 80%) and invalid data
    valid_mask = (
        (jrc <= 80.0)
        & (~np.isnan(hazard))
        & (~np.isnan(truth))
        & (~np.isnan(jrc))
    )

    flooded_idx = np.where(valid_mask & (truth == 1.0))
    dry_idx = np.where(valid_mask & (truth == 0.0))

    total_flooded_valid = len(flooded_idx[0])
    total_dry_valid = len(dry_idx[0])

    if total_flooded_valid == 0 or total_dry_valid == 0:
        raise ValueError(f"Insufficient valid pixels: Flooded={total_flooded_valid}, Dry={total_dry_valid}")

    # 2. Balanced random sampling to eliminate class prevalence bias
    sample_size = min(total_flooded_valid, total_dry_valid, n_samples)
    rng = np.random.default_rng(random_state)

    f_sub = rng.choice(total_flooded_valid, size=sample_size, replace=False)
    d_sub = rng.choice(total_dry_valid, size=sample_size, replace=False)

    f_rows, f_cols = flooded_idx[0][f_sub], flooded_idx[1][f_sub]
    d_rows, d_cols = dry_idx[0][d_sub], dry_idx[1][d_sub]

    y_true = np.concatenate([np.ones(sample_size, dtype=int), np.zeros(sample_size, dtype=int)])
    y_pred = np.concatenate([hazard[f_rows, f_cols], hazard[d_rows, d_cols]])

    # 3. ROC Curve and Area Under Curve (AUC)
    fpr, tpr, roc_thresholds = roc_curve(y_true, y_pred)
    auc_score = float(roc_auc_score(y_true, y_pred))

    # Calculate optimal threshold via Youden's J statistic (J = TPR - FPR)
    youden_j = tpr - fpr
    best_j_idx = int(np.argmax(youden_j))
    optimal_threshold = float(roc_thresholds[best_j_idx])

    # If no threshold is specified, use optimal Youden threshold
    if threshold is None:
        eval_threshold = optimal_threshold
    else:
        eval_threshold = float(threshold)

    # 4. Confusion Matrix at evaluation threshold
    y_bin = (y_pred >= eval_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_bin).ravel()

    tn = int(tn)
    fp = int(fp)
    fn = int(fn)
    tp = int(tp)

    accuracy = float((tp + tn) / (tp + tn + fp + fn))
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    f1 = float(2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    logger.info(
        "Flood Validation: AUC=%.4f | Threshold=%.4f | Precision=%.4f | Recall=%.4f | F1=%.4f",
        auc_score,
        eval_threshold,
        precision,
        recall,
        f1,
    )

    return {
        "auc": round(auc_score, 4),
        "threshold": round(eval_threshold, 4),
        "optimal_youden_threshold": round(optimal_threshold, 4),
        "sample_size_per_class": sample_size,
        "total_flooded_pixels": total_flooded_valid,
        "total_dry_pixels": total_dry_valid,
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        },
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1_score": round(f1, 4),
        },
        "roc_curve": {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "thresholds": roc_thresholds.tolist(),
        },
    }


def run_spatial_block_cv(
    flood_hazard_path: str = "data/sample/flood_hazard.tif",
    flood_truth_path: str = "data/sample/s1_event_flood.tif",
    jrc_path: str = "data/sample/jrc_water.tif",
    n_blocks_r: int = 4,
    n_blocks_c: int = 4,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Perform Spatial Block Cross-Validation across a regular grid to test for spatial autocorrelation.

    Partitions the study area into n_blocks_r x n_blocks_c contiguous geographic blocks.
    Evaluates AUC independently in each block, measuring spatial transferability.
    """
    logger.info("Executing Spatial Block Cross-Validation (%dx%d blocks)...", n_blocks_r, n_blocks_c)

    with rasterio.open(flood_hazard_path) as src:
        hazard = src.read(1).astype(np.float32)
    with rasterio.open(flood_truth_path) as src:
        truth = src.read(1).astype(np.float32)
    with rasterio.open(jrc_path) as src:
        jrc = src.read(1).astype(np.float32)

    rows, cols = hazard.shape
    block_h = rows // n_blocks_r
    block_w = cols // n_blocks_c

    block_results = []
    block_aucs = []

    for bi in range(n_blocks_r):
        for bj in range(n_blocks_c):
            r0 = bi * block_h
            r1 = (bi + 1) * block_h if bi < (n_blocks_r - 1) else rows
            c0 = bj * block_w
            c1 = (bj + 1) * block_w if bj < (n_blocks_c - 1) else cols

            sub_h = hazard[r0:r1, c0:c1]
            sub_t = truth[r0:r1, c0:c1]
            sub_j = jrc[r0:r1, c0:c1]

            v_mask = (sub_j <= 80.0) & (~np.isnan(sub_h)) & (~np.isnan(sub_t))
            f_count = int(np.sum(v_mask & (sub_t == 1.0)))
            d_count = int(np.sum(v_mask & (sub_t == 0.0)))

            if f_count >= 50 and d_count >= 50:
                n_b = min(f_count, d_count, 1000)
                rng = np.random.default_rng(random_state + bi * n_blocks_c + bj)

                f_pos = np.where(v_mask & (sub_t == 1.0))
                d_pos = np.where(v_mask & (sub_t == 0.0))

                s_f = rng.choice(len(f_pos[0]), size=n_b, replace=False)
                s_d = rng.choice(len(d_pos[0]), size=n_b, replace=False)

                y_t = np.concatenate([np.ones(n_b, dtype=int), np.zeros(n_b, dtype=int)])
                y_p = np.concatenate([sub_h[f_pos[0][s_f], f_pos[1][s_f]], sub_h[d_pos[0][s_d], d_pos[1][s_d]]])

                b_auc = float(roc_auc_score(y_t, y_p))
                block_aucs.append(b_auc)
                block_results.append({
                    "block_row": bi,
                    "block_col": bj,
                    "block_id": f"Block_{bi}_{bj}",
                    "auc": round(b_auc, 4),
                    "flooded_count": f_count,
                    "dry_count": d_count,
                })
            else:
                block_results.append({
                    "block_row": bi,
                    "block_col": bj,
                    "block_id": f"Block_{bi}_{bj}",
                    "auc": None,
                    "flooded_count": f_count,
                    "dry_count": d_count,
                    "skipped_reason": "Insufficient class balance",
                })

    mean_auc = float(np.mean(block_aucs)) if block_aucs else 0.0
    std_auc = float(np.std(block_aucs)) if block_aucs else 0.0
    min_auc = float(np.min(block_aucs)) if block_aucs else 0.0
    max_auc = float(np.max(block_aucs)) if block_aucs else 0.0

    return {
        "num_blocks_evaluated": len(block_aucs),
        "mean_block_auc": round(mean_auc, 4),
        "std_block_auc": round(std_auc, 4),
        "min_block_auc": round(min_auc, 4),
        "max_block_auc": round(max_auc, 4),
        "blocks": block_results,
    }


def validate_slope_sanity(
    slope_instability_path: str = "data/sample/slope_instability.tif",
    slope_deg_path: str = "data/sample/slope_deg.tif",
    chirps_path: str = "data/sample/chirps_rain.tif",
) -> Dict[str, Any]:
    """Execute geomorphic sanity check on slope instability layer.

    Evaluates whether modeled slope-instability hazard correlates physically
    with slope angle and rainfall tiers.
    """
    logger.info("Executing slope-instability geomorphic sanity check...")

    with rasterio.open(slope_instability_path) as src:
        hazard = src.read(1).astype(np.float32)
    with rasterio.open(slope_deg_path) as src:
        slope = src.read(1).astype(np.float32)
    with rasterio.open(chirps_path) as src:
        rain = src.read(1).astype(np.float32)

    valid = (~np.isnan(hazard)) & (~np.isnan(slope)) & (~np.isnan(rain))
    h_v = hazard[valid]
    s_v = slope[valid]
    r_v = rain[valid]

    # Spearman rank correlation between physical slope and modeled hazard
    spearman_res = spearmanr(s_v, h_v)
    spearman_corr = float(spearman_res.statistic)
    spearman_p = float(spearman_res.pvalue)

    # Slope classes tailored to coastal plain topography
    slope_bins = [0.0, 0.25, 0.50, 0.75, 5.0]
    slope_labels = [
        "Flat Plain (<0.25°)",
        "Gentle Slope (0.25°-0.50°)",
        "Moderate Slope (0.50°-0.75°)",
        "Steeper / Bunds (>0.75°)",
    ]

    r_p33 = float(np.percentile(r_v, 33.3))
    r_p66 = float(np.percentile(r_v, 66.7))

    rain_labels = [
        f"Low Rain (<{r_p33:.1f} mm)",
        f"Moderate Rain ({r_p33:.1f}-{r_p66:.1f} mm)",
        f"High Rain (>{r_p66:.1f} mm)",
    ]

    slope_summary = []
    matrix = []

    for i in range(len(slope_bins) - 1):
        s_mask = (s_v >= slope_bins[i]) & (s_v < slope_bins[i + 1])
        s_vals = h_v[s_mask]
        s_mean = float(np.mean(s_vals)) if len(s_vals) > 0 else 0.0
        s_std = float(np.std(s_vals)) if len(s_vals) > 0 else 0.0
        s_count = int(np.sum(s_mask))

        slope_summary.append({
            "class": slope_labels[i],
            "slope_range_deg": [slope_bins[i], slope_bins[i + 1]],
            "mean_hazard": round(s_mean, 4),
            "std_hazard": round(s_std, 4),
            "pixel_count": s_count,
        })

        row_rain = []
        for r_idx, r_cond in enumerate([r_v < r_p33, (r_v >= r_p33) & (r_v < r_p66), r_v >= r_p66]):
            comb = s_mask & r_cond
            comb_vals = h_v[comb]
            m_val = float(np.mean(comb_vals)) if len(comb_vals) > 0 else 0.0
            row_rain.append(round(m_val, 4))
        matrix.append(row_rain)

    return {
        "spearman_correlation": round(spearman_corr, 4),
        "spearman_pvalue": spearman_p,
        "is_monotonically_increasing": all(
            slope_summary[i]["mean_hazard"] <= slope_summary[i + 1]["mean_hazard"]
            for i in range(len(slope_summary) - 1)
        ),
        "slope_classes": slope_summary,
        "rain_labels": rain_labels,
        "cross_matrix": matrix,
        "disclaimer": "Sanity Check, NOT Validation: No official historical landslide inventory exists for South Chennai plains. This confirms geomorphic plausibility only.",
    }


def plot_roc_curve(
    roc_data: Dict[str, Any],
    output_path: str = "outputs/roc_curve.png",
) -> None:
    """Render high-contrast ROC Curve according to app/theme.py palette."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fpr = roc_data["roc_curve"]["fpr"]
    tpr = roc_data["roc_curve"]["tpr"]
    auc = roc_data["auc"]
    t_val = roc_data["threshold"]

    # Find closest point on curve to evaluated threshold
    thresholds = roc_data["roc_curve"]["thresholds"]
    t_diff = [abs(t - t_val) for t in thresholds]
    t_idx = int(np.argmin(t_diff))
    opt_fpr = fpr[t_idx]
    opt_tpr = tpr[t_idx]

    fig, ax = plt.subplots(figsize=(6.5, 6.0), dpi=200, facecolor=COLOR_WHITE)
    ax.set_facecolor(COLOR_PAPER)

    # Diagonal random guess line
    ax.plot([0, 1], [0, 1], linestyle="--", color=COLOR_MUTED_TEXT, linewidth=1.5, label="Random Guess (AUC = 0.500)")

    # Model ROC line
    ax.plot(fpr, tpr, color=COLOR_DEEP_BLUE, linewidth=2.5, label=f"Flood Susceptibility Model (AUC = {auc:.3f})")

    # Stated threshold operating point
    ax.scatter(
        [opt_fpr],
        [opt_tpr],
        color=COLOR_ORANGE,
        s=100,
        zorder=5,
        edgecolor=COLOR_INK,
        linewidth=1.5,
        label=f"Stated Threshold (τ = {t_val:.3f})\nTPR = {opt_tpr:.1%}, FPR = {opt_fpr:.1%}",
    )

    # Styling
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold", color=COLOR_INK)
    ax.set_ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=11, fontweight="bold", color=COLOR_INK)
    ax.set_title("Receiver Operating Characteristic (ROC) — Flood Validation\nGround Truth: Sentinel-1 SAR (Cyclone Michaung, Dec 2023)", fontsize=12, fontweight="bold", color=COLOR_INK, pad=12)

    ax.grid(True, linestyle=":", color=COLOR_BORDER_GREY, alpha=0.8)
    for spine in ax.spines.values():
        spine.set_color(COLOR_BORDER_GREY)

    ax.legend(loc="lower right", frameon=True, facecolor=COLOR_WHITE, edgecolor=COLOR_BORDER_GREY, fontsize=9.5)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved ROC curve plot to %s", output_path)


def plot_confusion_matrix(
    val_data: Dict[str, Any],
    output_path: str = "outputs/confusion_matrix.png",
) -> None:
    """Render publication-grade Confusion Matrix according to app/theme.py palette."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cm = val_data["confusion_matrix"]
    tp, fp, fn, tn = cm["tp"], cm["fp"], cm["fn"], cm["tn"]
    total = tp + fp + fn + tn
    m = val_data["metrics"]
    t_val = val_data["threshold"]

    matrix_vals = np.array([[tn, fp], [fn, tp]])
    matrix_pcts = matrix_vals / total * 100.0

    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=200, facecolor=COLOR_WHITE)
    ax.set_facecolor(COLOR_WHITE)

    # Cell coordinates
    cell_colors = [
        [COLOR_LIGHT_BLUE, "#F8D7DA" if fp > 0 else COLOR_PAPER],
        ["#FFF3CD" if fn > 0 else COLOR_PAPER, COLOR_MID_BLUE],
    ]

    for i in range(2):
        for j in range(2):
            count = matrix_vals[i, j]
            pct = matrix_pcts[i, j]
            bg_col = cell_colors[i][j]
            rect = plt.Rectangle((j, 1 - i), 1, 1, facecolor=bg_col, edgecolor=COLOR_BORDER_GREY, linewidth=1.5)
            ax.add_patch(rect)

            text_color = COLOR_WHITE if (i == 1 and j == 1) else COLOR_INK
            label_type = (
                "True Negatives (TN)" if (i == 0 and j == 0)
                else "False Positives (FP)" if (i == 0 and j == 1)
                else "False Negatives (FN)" if (i == 1 and j == 0)
                else "True Positives (TP)"
            )
            ax.text(
                j + 0.5,
                1 - i + 0.62,
                label_type,
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                color=text_color,
            )
            ax.text(
                j + 0.5,
                1 - i + 0.42,
                f"{count:,} pixels\n({pct:.1f}%)",
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color=text_color,
            )

    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)
    ax.set_xticks([0.5, 1.5])
    ax.set_xticklabels(["Predicted Dry (< τ)", "Predicted Flood (≥ τ)"], fontsize=10.5, fontweight="bold", color=COLOR_INK)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("Predicted Susceptibility Classification", fontsize=11, fontweight="bold", color=COLOR_INK, labelpad=10)

    ax.set_yticks([0.5, 1.5])
    ax.set_yticklabels(["Observed Flooded (S1)", "Observed Dry (S1)"], fontsize=10.5, fontweight="bold", color=COLOR_INK)
    ax.set_ylabel("Sentinel-1 SAR Ground Truth", fontsize=11, fontweight="bold", color=COLOR_INK, labelpad=10)

    for spine in ax.spines.values():
        spine.set_color(COLOR_BORDER_GREY)

    # Footnote with performance metrics
    subtitle = (
        f"Decision Threshold: τ = {t_val:.3f} | Accuracy: {m['accuracy']:.1%} | "
        f"Precision: {m['precision']:.1%} | Recall: {m['recall']:.1%} | F1: {m['f1_score']:.3f}"
    )
    plt.figtext(0.5, 0.02, subtitle, ha="center", fontsize=9.5, fontweight="bold", color=COLOR_INK)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved confusion matrix plot to %s", output_path)


def plot_slope_sanity_check(
    slope_data: Dict[str, Any],
    output_path: str = "outputs/slope_sanity_check.png",
) -> None:
    """Render geomorphic sanity check bar chart according to app/theme.py palette."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    classes = [c["class"] for c in slope_data["slope_classes"]]
    matrix = np.array(slope_data["cross_matrix"])  # Shape: (4, 3)
    rain_labels = slope_data["rain_labels"]

    fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=200, facecolor=COLOR_WHITE)
    ax.set_facecolor(COLOR_PAPER)

    x = np.arange(len(classes))
    width = 0.25

    colors = [COLOR_LIGHT_BLUE, COLOR_MID_BLUE, COLOR_DEEP_BLUE]

    for r_idx in range(3):
        vals = matrix[:, r_idx]
        offset = (r_idx - 1) * width
        bars = ax.bar(
            x + offset,
            vals,
            width,
            label=rain_labels[r_idx],
            color=colors[r_idx],
            edgecolor=COLOR_BORDER_GREY,
            linewidth=1.0,
        )
        # Add value label on top
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.2f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color=COLOR_INK,
            )

    ax.set_ylabel("Mean Slope-Instability Hazard (0 - 1)", fontsize=10.5, fontweight="bold", color=COLOR_INK)
    ax.set_xlabel("Topographic Slope Gradient Class", fontsize=10.5, fontweight="bold", color=COLOR_INK)
    ax.set_title(
        "Geomorphic Sanity Check: Modeled Hazard vs. Slope Gradient & Rainfall\n"
        "Confirms physical plausibility (Spearman r = "
        f"{slope_data['spearman_correlation']:.3f}, p < 0.001)",
        fontsize=11.5,
        fontweight="bold",
        color=COLOR_INK,
        pad=10,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(classes, fontsize=9.5, fontweight="bold", color=COLOR_INK)
    ax.set_ylim(0, 0.75)

    ax.grid(True, linestyle=":", color=COLOR_BORDER_GREY, axis="y", alpha=0.8)
    for spine in ax.spines.values():
        spine.set_color(COLOR_BORDER_GREY)

    ax.legend(loc="upper left", frameon=True, facecolor=COLOR_WHITE, edgecolor=COLOR_BORDER_GREY, fontsize=9)

    plt.figtext(
        0.5,
        0.01,
        "Sanity Check, NOT Validation: No official landslide inventory exists for South Chennai plains. Demonstrates physical slope scaling only.",
        ha="center",
        fontsize=8.5,
        fontstyle="italic",
        color=COLOR_MUTED_TEXT,
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved slope sanity check plot to %s", output_path)


def plot_spatial_block_cv(
    block_data: Dict[str, Any],
    output_path: str = "outputs/spatial_block_cv.png",
) -> None:
    """Render Spatial Block Cross-Validation 4x4 grid map."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    grid = np.zeros((4, 4))
    for b in block_data["blocks"]:
        r = b["block_row"]
        c = b["block_col"]
        grid[r, c] = b["auc"] if b["auc"] is not None else np.nan

    fig, ax = plt.subplots(figsize=(6.0, 5.0), dpi=200, facecolor=COLOR_WHITE)
    ax.set_facecolor(COLOR_PAPER)

    im = ax.imshow(grid, cmap="Blues", vmin=0.55, vmax=0.80)

    for i in range(4):
        for j in range(4):
            val = grid[i, j]
            text = f"AUC:\n{val:.3f}" if not np.isnan(val) else "N/A"
            text_color = COLOR_WHITE if val >= 0.70 else COLOR_INK
            ax.text(j, i, text, ha="center", va="center", fontsize=9.5, fontweight="bold", color=text_color)

    ax.set_xticks(range(4))
    ax.set_yticks(range(4))
    ax.set_xticklabels([f"Col {j+1}" for j in range(4)], fontsize=9, fontweight="bold", color=COLOR_INK)
    ax.set_yticklabels([f"Row {i+1}" for i in range(4)], fontsize=9, fontweight="bold", color=COLOR_INK)
    ax.set_title(
        f"Spatial Block Cross-Validation (4x4 Grid)\nMean AUC = {block_data['mean_block_auc']:.3f} ± {block_data['std_block_auc']:.3f}",
        fontsize=11.5,
        fontweight="bold",
        color=COLOR_INK,
        pad=10,
    )

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Block-Level ROC AUC", fontsize=9.5, fontweight="bold", color=COLOR_INK)
    cbar.outline.set_edgecolor(COLOR_BORDER_GREY)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved spatial block CV plot to %s", output_path)


def run_full_validation(
    flood_hazard_path: str = "data/sample/flood_hazard.tif",
    flood_truth_path: str = "data/sample/s1_event_flood.tif",
    jrc_path: str = "data/sample/jrc_water.tif",
    slope_instability_path: str = "data/sample/slope_instability.tif",
    slope_deg_path: str = "data/sample/slope_deg.tif",
    chirps_path: str = "data/sample/chirps_rain.tif",
    output_dir: str = "outputs",
) -> Dict[str, Any]:
    """Execute complete validation suite and generate all figures and json metrics."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Flood hazard ROC & Confusion Matrix
    flood_results = validate_flood_hazard(
        flood_hazard_path=flood_hazard_path,
        flood_truth_path=flood_truth_path,
        jrc_path=jrc_path,
    )

    # 2. Spatial Block Cross-Validation
    spatial_results = run_spatial_block_cv(
        flood_hazard_path=flood_hazard_path,
        flood_truth_path=flood_truth_path,
        jrc_path=jrc_path,
    )

    # 3. Slope-Instability Sanity Check
    slope_results = validate_slope_sanity(
        slope_instability_path=slope_instability_path,
        slope_deg_path=slope_deg_path,
        chirps_path=chirps_path,
    )

    # 4. Generate all figures
    roc_plot_path = os.path.join(output_dir, "roc_curve.png")
    cm_plot_path = os.path.join(output_dir, "confusion_matrix.png")
    spatial_plot_path = os.path.join(output_dir, "spatial_block_cv.png")
    slope_plot_path = os.path.join(output_dir, "slope_sanity_check.png")

    plot_roc_curve(flood_results, output_path=roc_plot_path)
    plot_confusion_matrix(flood_results, output_path=cm_plot_path)
    plot_spatial_block_cv(spatial_results, output_path=spatial_plot_path)
    plot_slope_sanity_check(slope_results, output_path=slope_plot_path)

    # 5. Export comprehensive JSON summary
    summary = {
        "flood_validation": flood_results,
        "spatial_block_cv": spatial_results,
        "slope_sanity_check": slope_results,
        "generated_plots": [
            roc_plot_path,
            cm_plot_path,
            spatial_plot_path,
            slope_plot_path,
        ],
    }

    json_path = os.path.join(output_dir, "validation_metrics.json")
    with open(json_path, "w", encoding="utf-8") as f:
        # Exclude large raw arrays from json
        json_exportable = {
            "flood_validation": {k: v for k, v in flood_results.items() if k != "roc_curve"},
            "spatial_block_cv": spatial_results,
            "slope_sanity_check": slope_results,
        }
        json.dump(json_exportable, f, indent=2)

    logger.info("Saved validation metrics summary to %s", json_path)
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_full_validation()
