"""Unit and integration tests for Step 3: Validation, ROC, Confusion Matrix, Spatial Block CV, and Sanity Checks."""

import json
import os
import pytest
import numpy as np

from analysis.validation import (
    validate_flood_hazard,
    run_spatial_block_cv,
    validate_slope_sanity,
    run_full_validation,
)


@pytest.fixture
def validation_summary():
    """Run full validation suite if not already cached."""
    metrics_path = "outputs/validation_metrics.json"
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return run_full_validation()


def test_flood_validation_balanced_sampling(validation_summary):
    """Verify that flood validation uses a balanced sample and produces valid metrics."""
    fv = validation_summary["flood_validation"]

    # 1. Balanced sampling check
    assert fv["sample_size_per_class"] == 5000, "Balanced sample must contain 5,000 pixels per class"

    # 2. Confusion matrix sum check
    cm = fv["confusion_matrix"]
    total_eval = cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"]
    assert total_eval == 10000, "Confusion matrix elements must sum to 10,000"

    # 3. AUC range check
    auc = fv["auc"]
    assert 0.65 <= auc <= 0.85, f"AUC ({auc}) should reflect realistic out-of-sample flood discrimination"

    # 4. Metrics validity
    m = fv["metrics"]
    for k in ["accuracy", "precision", "recall", "specificity", "f1_score"]:
        assert 0.0 <= m[k] <= 1.0, f"Metric {k} must be in [0, 1]"
        assert m[k] > 0.40, f"Metric {k} ({m[k]}) should be significantly better than random"


def test_no_validation_leakage():
    """Verify strictly NO VALIDATION LEAKAGE: S1 event flood is never an input to hazard layers."""
    hazard_code_path = "analysis/hazard.py"
    with open(hazard_code_path, "r", encoding="utf-8") as f:
        content = f.read()

    # The S1 event flood must never appear in hazard calculation code
    assert "s1_event_flood" not in content, (
        "CRITICAL LEAKAGE: s1_event_flood must NEVER be an input to hazard calculation!"
    )
    assert "event_flood" not in content, (
        "CRITICAL LEAKAGE: event flood extent must NEVER be an input to hazard calculation!"
    )


def test_spatial_block_cross_validation(validation_summary):
    """Verify that 4x4 spatial block partitioning evaluates geographic generalizability."""
    sb = validation_summary["spatial_block_cv"]

    assert sb["num_blocks_evaluated"] == 16, "Must evaluate all 16 spatial blocks"
    assert 0.55 <= sb["mean_block_auc"] <= 0.85, "Mean block AUC must be statistically sound"
    assert sb["std_block_auc"] > 0.0, "Block AUCs must exhibit real spatial variation across regions"


def test_slope_geomorphic_sanity_check(validation_summary):
    """Verify that slope instability behaves as a sensible physical sanity check."""
    ss = validation_summary["slope_sanity_check"]

    # Must confirm positive correlation with terrain slope
    corr = ss["spearman_correlation"]
    assert corr > 0.70, f"Spearman correlation with slope ({corr}) must be strongly positive"
    assert ss["spearman_pvalue"] < 0.001, "Spearman correlation must be statistically significant"

    # Hazard must increase monotonically across slope bins
    assert ss["is_monotonically_increasing"], "Modeled slope hazard must scale monotonically with slope class"

    # Honest disclaimer must be present
    assert "Sanity Check, NOT Validation" in ss["disclaimer"]


def test_validation_figures_exported():
    """Verify that all required validation figures exist in outputs/ and are non-empty."""
    expected_plots = [
        "outputs/roc_curve.png",
        "outputs/confusion_matrix.png",
        "outputs/spatial_block_cv.png",
        "outputs/slope_sanity_check.png",
    ]
    for plot_path in expected_plots:
        assert os.path.exists(plot_path), f"Missing plot: {plot_path}"
        assert os.path.getsize(plot_path) > 10000, f"Plot file {plot_path} is suspiciously small"
