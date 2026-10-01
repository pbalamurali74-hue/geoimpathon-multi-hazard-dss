"""Unit and integration tests for Step 5: Golden-Hour Access Collapse and Monte Carlo Robustness."""

import json
import os
import pytest

from analysis.access import compute_golden_hour_access
from analysis.monte_carlo import run_monte_carlo_robustness


@pytest.fixture(scope="module")
def access_data():
    """Load or run Golden-Hour access calculation."""
    json_p = "outputs/access_metrics.json"
    if not os.path.exists(json_p):
        return compute_golden_hour_access()
    with open(json_p, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def monte_carlo_data():
    """Load or run Monte Carlo robustness analysis."""
    json_p = "outputs/monte_carlo_metrics.json"
    if not os.path.exists(json_p):
        return run_monte_carlo_robustness(n_runs=20)
    with open(json_p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_golden_hour_access_calculation(access_data):
    """Verify that Golden-Hour (60m) and Acute (30m) access collapse metrics are correctly computed."""
    d = access_data

    # Required fields
    assert "golden_hour_60min" in d
    assert "acute_emergency_30min" in d
    assert "total_exposure_units" in d

    gh = d["golden_hour_60min"]
    ac = d["acute_emergency_30min"]

    # Pre-disaster access must be high
    assert gh["normal_access_pct"] >= 90.0, "Normal 60-min access should be >= 90%"
    assert ac["normal_access_pct"] >= 90.0, "Normal 30-min access should be >= 90%"

    # Flood access must be lower (proving disaster access collapse)
    assert gh["flood_access_pct"] < gh["normal_access_pct"], "Flood access must decline"
    assert ac["flood_access_pct"] < ac["normal_access_pct"], "Flood access must decline"

    # Collapse must be significant
    assert gh["access_collapse_pct"] >= 15.0, "Golden-Hour collapse should reflect severe flood impacts"
    assert ac["access_collapse_pct"] >= 20.0, "Acute 30-min collapse should be even more severe"

    # Plot must exist
    assert os.path.exists("outputs/golden_hour_access.png")
    assert os.path.getsize("outputs/golden_hour_access.png") > 10000


def test_monte_carlo_robustness_execution(monte_carlo_data):
    """Verify that 200 Monte Carlo runs confirm route stability and critical corridor persistence."""
    mc = monte_carlo_data

    assert mc["n_runs"] >= 20, "Should have executed at least 20 runs"
    assert mc["noise_level_pct"] == 20, "Noise level must be +/- 20%"

    # Route confidence must be high
    assert mc["overall_route_confidence_pct"] >= 85.0, (
        f"Route confidence ({mc['overall_route_confidence_pct']}%) should demonstrate decision stability"
    )

    # Critical road persistence must be between 70% and 100%
    pers = mc["mean_critical_road_persistence_pct"]
    assert 70.0 <= pers <= 100.0, f"Critical road persistence ({pers}%) must be realistic"

    # Route stability by origin must be populated
    for origin, stats in mc["route_stability_by_origin"].items():
        assert 0.0 <= stats["mean_jaccard"] <= 1.0
        assert stats["identical_pct"] >= 70.0

    # Plot must exist
    assert os.path.exists("outputs/monte_carlo_robustness.png")
    assert os.path.getsize("outputs/monte_carlo_robustness.png") > 10000
