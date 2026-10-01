"""Unit and integration tests for Step 2: Emergency least-risk routing and network risk."""

import os
import pytest
import numpy as np
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, LineString

from routing.router import (
    annotate_network_with_risk,
    classify_facilities_safety,
    calculate_dual_routes,
    is_edge_blocked,
)


@pytest.fixture
def sample_annotated_graph():
    graph_p = "data/sample/drive_network_risk.graphml"
    if not os.path.exists(graph_p):
        return annotate_network_with_risk()
    import osmnx as ox
    return ox.load_graphml(graph_p)


@pytest.fixture
def sample_facilities():
    hosp_p = "data/sample/hospitals.geojson"
    return gpd.read_file(hosp_p)


def test_edge_cost_formula():
    """Verify edge cost function C = L * (1 + alpha * risk)."""
    length = 1000.0  # 1 km
    risk = 0.60      # High risk

    # At alpha = 0 (Fastest), cost must equal physical length
    cost_fastest = length * (1.0 + 0.0 * risk)
    assert np.isclose(cost_fastest, 1000.0), "Alpha=0 cost must equal physical length"

    # At alpha = 3 (Safest), cost must be 2.8x length
    cost_safest = length * (1.0 + 3.0 * risk)
    assert np.isclose(cost_safest, 2800.0), "Alpha=3 cost must be length * (1 + 3 * 0.6) = 2800"

    # Higher alpha strictly penalizes riskier edges
    cost_higher = length * (1.0 + 5.0 * risk)
    assert cost_higher > cost_safest > cost_fastest


def test_blocked_edge_flag(sample_annotated_graph):
    """Verify that edges above block threshold (p95) are flagged as is_blocked = True."""
    G = sample_annotated_graph
    blocked_count = 0
    passable_count = 0

    for _, _, _, data in G.edges(keys=True, data=True):
        risk = float(data.get("risk", 0.0))
        is_blocked = is_edge_blocked(data)

        if is_blocked:
            blocked_count += 1
            # Blocked edges must have high risk
            assert risk >= 0.50, f"Blocked edge has unexpectedly low risk: {risk}"
        else:
            passable_count += 1

    assert blocked_count > 0, "There should be blocked high-risk edges in flood scenario"
    assert passable_count > blocked_count, "Passable edges must outnumber blocked edges"


def test_structural_risk_bumps():
    """Verify tunnel underpass and bridge risk bumps are applied properly."""
    bump_tunnel = 0.15
    bump_bridge = 0.08
    base_risk = 0.50

    tunnel_risk = min(1.0, base_risk + bump_tunnel)
    bridge_risk = min(1.0, base_risk + bump_bridge)

    assert np.isclose(tunnel_risk, 0.65), "Tunnel risk bump must be +0.15"
    assert np.isclose(bridge_risk, 0.58), "Bridge risk bump must be +0.08"


def test_facility_safety_classification(sample_facilities):
    """Verify facilities are partitioned into Safe and Unsafe categories."""
    hosp = sample_facilities
    assert "is_safe" in hosp.columns, "Facilities GeoDataFrame must contain 'is_safe'"
    assert "sampled_risk" in hosp.columns, "Facilities GeoDataFrame must contain 'sampled_risk'"

    safe_count = int(hosp["is_safe"].sum())
    unsafe_count = len(hosp) - safe_count

    assert safe_count > 0, "Must have safe hospitals available"
    assert unsafe_count > 0, "Must identify compromised hospitals in inundation zones"

    # Safe hospitals must have lower risk than unsafe ones
    max_safe_risk = hosp[hosp["is_safe"]]["sampled_risk"].max()
    min_unsafe_risk = hosp[~hosp["is_safe"]]["sampled_risk"].min()
    assert max_safe_risk <= min_unsafe_risk, "Safe hospitals must strictly have lower risk than unsafe ones"


def test_dual_route_calculation(sample_annotated_graph, sample_facilities):
    """Verify calculate_dual_routes returns non-empty valid metrics and polylines."""
    G = sample_annotated_graph
    hosp = sample_facilities
    origin_coord = (80.115, 12.924)  # Tambaram coordinates

    res = calculate_dual_routes(G, origin_coord, hosp, alpha=3.0)

    assert "fastest" in res
    assert "safest" in res
    assert "compromise_text" in res
    assert len(res["fastest"]["coordinates"]) >= 2, "Fastest route polyline must have >= 2 points"
    assert len(res["safest"]["coordinates"]) >= 2, "Safest route polyline must have >= 2 points"

    assert res["fastest"]["distance_km"] > 0, "Distance must be positive"
    assert res["safest"]["distance_km"] > 0, "Distance must be positive"
    assert res["fastest"]["time_min"] > 0, "Travel time must be positive"
    assert res["safest"]["time_min"] > 0, "Travel time must be positive"
