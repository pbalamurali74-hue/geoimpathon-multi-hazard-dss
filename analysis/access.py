"""Golden-Hour Emergency Access Collapse Analysis.

Measures the proportion of built-up exposure that can reach a safe, operational
hospital within 60 minutes (Golden-Hour trauma standard) and 30 minutes (Acute Emergency),
comparing the Normal Baseline against the Flood Scenario.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.theme import (
    COLOR_BORDER_GREY,
    COLOR_DARK_ORANGE,
    COLOR_DEEP_BLUE,
    COLOR_INK,
    COLOR_MID_BLUE,
    COLOR_MUTED_TEXT,
    COLOR_ORANGE,
    COLOR_PAPER,
    COLOR_WHITE,
)

logger = logging.getLogger(__name__)


def compute_golden_hour_access(
    settlement_isolation_path: str = "outputs/settlement_isolation.csv",
    output_dir: str = "outputs",
) -> Dict[str, Any]:
    """Compute 30-min and 60-min emergency hospital reachability and access collapse.

    Returns:
        Dictionary of accessibility percentages, collapse rates, and plot path.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Computing Golden-Hour emergency hospital access metrics...")

    if not os.path.exists(settlement_isolation_path):
        from routing.preposition import analyze_settlement_isolation
        analyze_settlement_isolation(output_dir=output_dir)

    df = pd.read_csv(settlement_isolation_path)
    tot_exp = float(df["exposure_units"].sum())

    # Normal Scenario: 30m and 60m
    norm_30_exp = float(df[df["time_normal_min"] <= 30.0]["exposure_units"].sum())
    norm_60_exp = float(df[df["time_normal_min"] <= 60.0]["exposure_units"].sum())

    norm_30_pct = (norm_30_exp / tot_exp * 100.0) if tot_exp > 0 else 0.0
    norm_60_pct = (norm_60_exp / tot_exp * 100.0) if tot_exp > 0 else 0.0

    # Flood Scenario: 30m and 60m (Isolated settlements have time_flood_min == NaN)
    flood_30_exp = float(df[(df["time_flood_min"].notna()) & (df["time_flood_min"] <= 30.0)]["exposure_units"].sum())
    flood_60_exp = float(df[(df["time_flood_min"].notna()) & (df["time_flood_min"] <= 60.0)]["exposure_units"].sum())

    flood_30_pct = (flood_30_exp / tot_exp * 100.0) if tot_exp > 0 else 0.0
    flood_60_pct = (flood_60_exp / tot_exp * 100.0) if tot_exp > 0 else 0.0

    collapse_30 = norm_30_pct - flood_30_pct
    collapse_60 = norm_60_pct - flood_60_pct

    # Severely disconnected population
    isolated_exp = float(df[df["status"] == "Isolated (Hospital Cut Off)"]["exposure_units"].sum())
    delayed_exp = float(df[df["status"] == "Severely Delayed (≥2x Normal Time)"]["exposure_units"].sum())

    results = {
        "total_exposure_units": round(tot_exp, 1),
        "golden_hour_60min": {
            "normal_access_pct": round(norm_60_pct, 1),
            "flood_access_pct": round(flood_60_pct, 1),
            "access_collapse_pct": round(collapse_60, 1),
            "normal_exposure_reached": round(norm_60_exp, 1),
            "flood_exposure_reached": round(flood_60_exp, 1),
        },
        "acute_emergency_30min": {
            "normal_access_pct": round(norm_30_pct, 1),
            "flood_access_pct": round(flood_30_pct, 1),
            "access_collapse_pct": round(collapse_30, 1),
            "normal_exposure_reached": round(norm_30_exp, 1),
            "flood_exposure_reached": round(flood_30_exp, 1),
        },
        "isolated_exposure_units": round(isolated_exp, 1),
        "delayed_exposure_units": round(delayed_exp, 1),
    }

    # Generate Comparative Access Collapse Figure
    plot_path = os.path.join(output_dir, "golden_hour_access.png")
    plot_golden_hour_access(results, output_path=plot_path)
    results["plot_path"] = plot_path

    # Export JSON
    json_path = os.path.join(output_dir, "access_metrics.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(
        "Golden-Hour (60m) Access: %.1f%% -> %.1f%% (-%.1f%% collapse) | 30m: %.1f%% -> %.1f%% (-%.1f%% collapse)",
        norm_60_pct,
        flood_60_pct,
        collapse_60,
        norm_30_pct,
        flood_30_pct,
        collapse_30,
    )
    return results


def plot_golden_hour_access(
    access_data: Dict[str, Any],
    output_path: str = "outputs/golden_hour_access.png",
) -> None:
    """Render high-contrast comparative accessibility bar chart according to app/theme.py."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    gh = access_data["golden_hour_60min"]
    ac = access_data["acute_emergency_30min"]

    categories = ["Acute Emergency\n(30 Minutes)", "Golden-Hour Standard\n(60 Minutes)"]
    normal_vals = [ac["normal_access_pct"], gh["normal_access_pct"]]
    flood_vals = [ac["flood_access_pct"], gh["flood_access_pct"]]
    collapses = [ac["access_collapse_pct"], gh["access_collapse_pct"]]

    x = np.arange(len(categories))
    width = 0.32

    fig, ax = plt.subplots(figsize=(7.0, 5.0), dpi=200, facecolor=COLOR_WHITE)
    ax.set_facecolor(COLOR_PAPER)

    bars_norm = ax.bar(
        x - width / 2,
        normal_vals,
        width,
        label="Normal Pre-Disaster Baseline",
        color=COLOR_DEEP_BLUE,
        edgecolor=COLOR_BORDER_GREY,
        linewidth=1.2,
    )

    bars_flood = ax.bar(
        x + width / 2,
        flood_vals,
        width,
        label="Flood Scenario (Cyclone Michaung)",
        color=COLOR_ORANGE,
        edgecolor=COLOR_BORDER_GREY,
        linewidth=1.2,
    )

    # Annotate bar values
    for bar in bars_norm:
        h = bar.get_height()
        ax.annotate(
            f"{h:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=COLOR_INK,
        )

    for i, bar in enumerate(bars_flood):
        h = bar.get_height()
        ax.annotate(
            f"{h:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=COLOR_INK,
        )
        # Collapse callout badge
        collapse_text = f"▼ -{collapses[i]:.1f}% Collapse"
        ax.annotate(
            collapse_text,
            xy=(bar.get_x() + bar.get_width() / 2, h / 2),
            ha="center",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=COLOR_WHITE,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=COLOR_DARK_ORANGE, edgecolor=COLOR_WHITE, linewidth=1),
        )

    ax.set_ylabel("Built-Up Exposure with Safe Hospital Access (%)", fontsize=10.5, fontweight="bold", color=COLOR_INK)
    ax.set_title(
        "Emergency Hospital Access Collapse in Flood Conditions\n"
        "Comparative Analysis: Pre-Disaster Free Flow vs. Cyclone Michaung Inundation",
        fontsize=11.5,
        fontweight="bold",
        color=COLOR_INK,
        pad=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10.5, fontweight="bold", color=COLOR_INK)
    ax.set_ylim(0, 115)

    ax.grid(True, linestyle=":", color=COLOR_BORDER_GREY, axis="y", alpha=0.8)
    for spine in ax.spines.values():
        spine.set_color(COLOR_BORDER_GREY)

    ax.legend(loc="upper right", frameon=True, facecolor=COLOR_WHITE, edgecolor=COLOR_BORDER_GREY, fontsize=9.5)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved golden hour access plot to %s", output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    compute_golden_hour_access()
