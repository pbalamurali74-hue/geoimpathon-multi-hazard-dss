"""Unit and integration tests for Step 4: Road Criticality, Isolation Analysis, and Relief Pre-positioning."""

import os
import pytest
import pandas as pd
import geopandas as gpd

from routing.criticality import compute_road_criticality
from routing.preposition import analyze_settlement_isolation, recommend_preposition_sites


@pytest.fixture(scope="module")
def criticality_data():
    """Load or run criticality analysis."""
    csv_p = "outputs/top_critical_roads.csv"
    if not os.path.exists(csv_p):
        return compute_road_criticality()
    df = pd.read_csv(csv_p)
    gdf = gpd.read_file("outputs/top_critical_roads.geojson")
    return {"df": df, "gdf": gdf}


@pytest.fixture(scope="module")
def isolation_data():
    """Load or run isolation analysis."""
    csv_p = "outputs/settlement_isolation.csv"
    if not os.path.exists(csv_p):
        return analyze_settlement_isolation()
    return gpd.read_file("outputs/settlement_isolation.geojson")


@pytest.fixture(scope="module")
def preposition_data(isolation_data):
    """Load or run preposition recommendation."""
    csv_p = "outputs/preposition_sites.csv"
    if not os.path.exists(csv_p):
        return recommend_preposition_sites(isolation_data)
    df = pd.read_csv(csv_p)
    gdf = gpd.read_file("outputs/preposition_sites.geojson")
    return {"df": df, "gdf": gdf}


def test_top_critical_roads_exist_and_ranked(criticality_data):
    """Verify that exactly 10 single points of failure are identified and ranked."""
    df = criticality_data["df"]
    gdf = criticality_data["gdf"]

    assert len(df) == 10, f"Expected 10 critical roads, got {len(df)}"
    assert len(gdf) == 10, f"Expected 10 critical road geometries, got {len(gdf)}"

    # Ranks must be 1 to 10
    assert list(df["rank"]) == list(range(1, 11)), "Ranks must be strictly 1 through 10"

    # Required operational fields
    for col in ["name", "highway", "risk", "flow_exposure", "composite_criticality", "explanation", "lat", "lon"]:
        assert col in df.columns, f"Missing required column: {col}"
        assert df[col].notna().all(), f"Column {col} contains NaN values"

    # Operational explanations must be descriptive
    for exp in df["explanation"]:
        assert len(exp) > 20, f"Explanation is too brief: {exp}"


def test_settlement_isolation_analysis(isolation_data):
    """Verify that all 141 settlements are evaluated for flood isolation and delay."""
    gdf = isolation_data

    assert len(gdf) == 141, f"Expected 141 settlements, got {len(gdf)}"

    # Status distribution
    status_counts = gdf["status"].value_counts()
    assert "Isolated (Hospital Cut Off)" in status_counts, "Must identify isolated settlements"
    assert "Severely Delayed (≥2x Normal Time)" in status_counts, "Must identify severely delayed settlements"
    assert "Connected (Passable Route)" in status_counts, "Must identify connected settlements"

    # Check delayed settlements satisfy condition
    delayed = gdf[gdf["status"] == "Severely Delayed (≥2x Normal Time)"]
    for _, row in delayed.iterrows():
        assert row["delay_ratio"] >= 2.0, f"Settlement {row['name']} delay ratio {row['delay_ratio']} < 2.0"


def test_preposition_sites_greedy_max_coverage(preposition_data):
    """Verify that exactly k=5 strategic relief staging sites are recommended."""
    df = preposition_data["df"]
    gdf = preposition_data["gdf"]

    assert len(df) == 5, f"Expected 5 pre-positioning sites, got {len(df)}"
    assert len(gdf) == 5, f"Expected 5 pre-positioning site geometries, got {len(gdf)}"

    # Verify asset staging attributes
    for col in ["name", "lat", "lon", "covered_exposure", "asset_package", "staged_assets", "operational_mandate"]:
        assert col in df.columns, f"Missing required column {col} in preposition sites"
        assert df[col].notna().all(), f"Column {col} has missing values"

    # Rank 1 must have highest covered exposure
    assert df.loc[0, "covered_exposure"] >= df.loc[1, "covered_exposure"], (
        "Greedy max-coverage should order sites by initial marginal coverage"
    )


def test_criticality_and_preposition_exports():
    """Verify that all required CSV and GeoJSON export files exist and are non-empty."""
    expected_files = [
        "outputs/top_critical_roads.csv",
        "outputs/top_critical_roads.geojson",
        "outputs/settlement_isolation.csv",
        "outputs/settlement_isolation.geojson",
        "outputs/preposition_sites.csv",
        "outputs/preposition_sites.geojson",
    ]
    for path in expected_files:
        assert os.path.exists(path), f"Missing expected export file: {path}"
        assert os.path.getsize(path) > 100, f"File {path} is unexpectedly small or empty"
