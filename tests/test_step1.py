"""Unit and integration tests for Step 1: Hazard layers, AHP MCDM, and theme design.
"""

import os
import re
import pytest
import numpy as np

from analysis.mcdm import (
    calculate_ahp_weights,
    normalize_minmax,
    fuzzy_sigmoidal_membership,
    calculate_entropy_weights,
)
from analysis.hazard import AHP_FLOOD_MATRIX, AHP_SLOPE_MATRIX
import app.theme as theme


def test_ahp_flood_consistency():
    """Verify Flood AHP matrix achieves CR < 0.10 and weights sum to 1.0."""
    w, lmax, ci, cr = calculate_ahp_weights(AHP_FLOOD_MATRIX)
    assert cr < 0.10, f"Flood CR {cr} must be strictly less than 0.10"
    assert np.isclose(np.sum(w), 1.0), "Weights must sum to 1.0"
    assert len(w) == 7, "Must have 7 flood criteria"


def test_ahp_slope_consistency():
    """Verify Slope-Instability AHP matrix achieves CR < 0.10 and weights sum to 1.0."""
    w, lmax, ci, cr = calculate_ahp_weights(AHP_SLOPE_MATRIX)
    assert cr < 0.10, f"Slope CR {cr} must be strictly less than 0.10"
    assert np.isclose(np.sum(w), 1.0), "Weights must sum to 1.0"
    assert len(w) == 7, "Must have 7 slope criteria"


def test_normalization_directions():
    """Verify normalization directions for cost (direct) and benefit (inverse) indicators."""
    arr = np.array([10.0, 20.0, 30.0, 40.0, 50.0], dtype=np.float32)

    # Cost direction: higher value = higher risk
    cost_norm = normalize_minmax(arr, cost_direction=True)
    assert np.isclose(cost_norm[0], 0.0), "Lowest value must be 0.0 in cost direction"
    assert np.isclose(cost_norm[-1], 1.0), "Highest value must be 1.0 in cost direction"
    assert np.all(np.diff(cost_norm) >= 0), "Cost normalization must be monotonically non-decreasing"

    # Benefit direction: higher value = lower risk (e.g. elevation in flood)
    benefit_norm = normalize_minmax(arr, cost_direction=False)
    assert np.isclose(benefit_norm[0], 1.0), "Lowest elevation must have highest risk (1.0)"
    assert np.isclose(benefit_norm[-1], 0.0), "Highest elevation must have lowest risk (0.0)"
    assert np.all(np.diff(benefit_norm) <= 0), "Benefit normalization must be monotonically non-increasing"


def test_normalization_zero_variance():
    """Verify zero variance array does not cause division by zero."""
    arr = np.full((10, 10), 42.0, dtype=np.float32)
    norm = normalize_minmax(arr, cost_direction=True)
    assert np.all(norm == 0.0), "Zero variance array should safely return zeros"


def test_fuzzy_sigmoidal_membership():
    """Verify non-linear fuzzy membership function."""
    hand = np.array([0.5, 3.0, 10.0], dtype=np.float32)
    # At midpoint (3.0), membership must equal exactly 0.50
    fuzzy = fuzzy_sigmoidal_membership(hand, midpoint=3.0, beta=1.2, decreasing=True)
    assert np.isclose(fuzzy[1], 0.50, atol=1e-3), "Membership at midpoint must be 0.50"
    assert fuzzy[0] > 0.85, "Low HAND must have high risk membership"
    assert fuzzy[2] < 0.05, "High HAND must have low risk membership"


def test_theme_palette_compliance():
    """Verify all required design tokens exist and are valid 6-digit hex codes."""
    hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")

    required_tokens = [
        "COLOR_WHITE",
        "COLOR_PAPER",
        "COLOR_BORDER_GREY",
        "COLOR_INK",
        "COLOR_MUTED_TEXT",
        "COLOR_DEEP_BLUE",
        "COLOR_MID_BLUE",
        "COLOR_LIGHT_BLUE",
        "COLOR_ORANGE",
        "COLOR_DARK_ORANGE",
    ]

    for token in required_tokens:
        assert hasattr(theme, token), f"theme.py missing token {token}"
        val = getattr(theme, token)
        assert hex_pattern.match(val), f"Token {token}={val} is not a valid hex code"

    for level, color in theme.RISK_RAMP.items():
        assert hex_pattern.match(color), f"Risk ramp color for {level}={color} is invalid"


def test_exported_layers_exist():
    """Verify all required GeoTIFF and PNG layers exist in outputs/ and data/sample/."""
    expected_layers = [
        "flood_hazard",
        "slope_instability",
        "dem_slope_deg",
        "multihazard_risk",
        "builtup_exposure",
    ]

    for name in expected_layers:
        for folder in ["outputs", "data/sample"]:
            tif = os.path.join(folder, f"{name}.tif")
            png = os.path.join(folder, f"{name}.png")
            assert os.path.exists(tif), f"Missing GeoTIFF: {tif}"
            assert os.path.exists(png), f"Missing PNG overlay: {png}"
            assert os.path.getsize(tif) > 0, f"Empty file: {tif}"
            assert os.path.getsize(png) > 0, f"Empty file: {png}"
