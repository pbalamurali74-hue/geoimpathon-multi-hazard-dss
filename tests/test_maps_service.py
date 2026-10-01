"""
Unit tests for Maps API and Multi-Provider Basemap Service.
"""

import pytest
import folium
from analysis.maps_service import (
    BASEMAP_REGISTRY,
    get_tile_config,
    create_interactive_map,
    get_maps_api_key,
    geocode_address_google,
)


def test_basemap_registry_completeness():
    """Verify that all core basemap styles are registered with URLs and attributions."""
    required_styles = [
        "CartoDB Positron (Clean Light)",
        "Google Maps Hybrid (Satellite)",
        "Google Maps Roadmap",
        "Google Maps Terrain",
        "OpenStreetMap Standard",
        "Esri World Imagery (Satellite)",
        "CartoDB Dark Matter",
    ]
    for style in required_styles:
        assert style in BASEMAP_REGISTRY
        entry = BASEMAP_REGISTRY[style]
        assert "url" in entry and entry["url"].startswith("http")
        assert "attr" in entry and len(entry["attr"]) > 0


def test_get_tile_config_with_and_without_key():
    """Test URL configuration and key parameter injection."""
    # Test default without key
    cfg = get_tile_config("Google Maps Hybrid (Satellite)", api_key="")
    assert "mt1.google.com" in cfg["url"]
    assert "key=" not in cfg["url"]

    # Test with key
    cfg_with_key = get_tile_config("Google Maps Hybrid (Satellite)", api_key="AIzaSyTest123")
    assert "key=AIzaSyTest123" in cfg_with_key["url"]

    # Test unknown style fallback
    cfg_fallback = get_tile_config("NonExistentStyle")
    assert cfg_fallback["url"] == BASEMAP_REGISTRY["CartoDB Positron (Clean Light)"]["url"]


def test_create_interactive_map():
    """Test Folium map generation with multiple base layers and layer controls."""
    center = (12.9249, 80.1158)
    m = create_interactive_map(
        location=center,
        zoom_start=12,
        active_basemap="Google Maps Hybrid (Satellite)",
        include_all_basemaps=True,
    )
    assert isinstance(m, folium.Map)
    assert m.location == list(center)
    assert m.options["zoom"] == 12

    # Verify tile layers added natively and cleanly
    tile_children = [
        child for child in m._children.values()
        if isinstance(child, folium.TileLayer)
    ]
    assert len(tile_children) >= 1


def test_geocode_google_no_key_returns_none():
    """Verify Google Maps geocoding gracefully returns None when key is absent."""
    result = geocode_address_google("Tambaram Railway Station", api_key="")
    assert result is None
