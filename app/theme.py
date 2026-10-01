"""Design system and theme constants for the GEOIMPATHON 1.0 DSS.

Every color, font, size, and styling rule is declared here to guarantee
visual consistency across Streamlit UI components, Matplotlib/Plotly figures,
and Folium map overlays. No hardcoded hex values should exist outside this file.
"""

from typing import Dict, Any

# Primary UI Palette
COLOR_WHITE: str = "#FFFFFF"
COLOR_PAPER: str = "#F4F7FA"
COLOR_BORDER_GREY: str = "#D5DEE8"
COLOR_INK: str = "#1B2733"
COLOR_MUTED_TEXT: str = "#5B6B7B"
COLOR_DEEP_BLUE: str = "#1F4E79"
COLOR_MID_BLUE: str = "#2E75B6"
COLOR_LIGHT_BLUE: str = "#DCE9F5"
COLOR_ORANGE: str = "#E8761A"
COLOR_DARK_ORANGE: str = "#B8470C"

# Sequential Multi-Hazard Risk Color Ramp (Colorblind-safe blue-to-orange)
RISK_RAMP: Dict[str, str] = {
    "Low": "#DCE9F5",
    "Moderate": "#8DB8E0",
    "High": "#F4A259",
    "Very High": "#C2410C",
}

# Hex list for continuous/binned colormaps
RISK_COLOR_LIST: list[str] = [
    "#DCE9F5",  # Low
    "#8DB8E0",  # Moderate
    "#F4A259",  # High
    "#C2410C",  # Very High
]

# Typography (Sentence case, clean technical system)
FONT_FAMILY: str = "'Source Sans 3', 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_SIZE_BODY: str = "14px"
FONT_SIZE_CAPTION: str = "12px"
FONT_SIZE_HEADING: str = "20px"
FONT_SIZE_TITLE: str = "24px"

# Map Geometry Styles
MAP_STYLES: Dict[str, Any] = {
    "safest_route": {
        "color": COLOR_DEEP_BLUE,
        "weight": 5,
        "opacity": 0.95,
        "dashArray": None,
    },
    "shortest_route": {
        "color": COLOR_ORANGE,
        "weight": 4,
        "opacity": 0.95,
        "dashArray": "6, 6",
    },
    "critical_road": {
        "color": COLOR_DARK_ORANGE,
        "weight": 5,
        "opacity": 0.9,
    },
    "hospital_safe": {
        "color": COLOR_MID_BLUE,
        "fill_color": COLOR_MID_BLUE,
        "radius": 7,
    },
    "hospital_unsafe": {
        "color": COLOR_DARK_ORANGE,
        "fill_color": COLOR_DARK_ORANGE,
        "radius": 7,
    },
    "shelter_safe": {
        "color": COLOR_MID_BLUE,
        "fill_color": COLOR_PAPER,
        "radius": 6,
    },
    "shelter_unsafe": {
        "color": COLOR_DARK_ORANGE,
        "fill_color": COLOR_PAPER,
        "radius": 6,
    },
    "settlement_normal": {
        "color": COLOR_MID_BLUE,
        "fill_color": COLOR_WHITE,
        "radius": 4,
        "weight": 2,
    },
    "settlement_isolated": {
        "color": COLOR_DARK_ORANGE,
        "fill_color": COLOR_WHITE,
        "radius": 6,
        "weight": 3,
    },
    "preposition_site": {
        "color": COLOR_DEEP_BLUE,
        "fill_color": COLOR_LIGHT_BLUE,
        "radius": 8,
        "weight": 2,
    },
}

# Custom Streamlit CSS injection string
CUSTOM_CSS: str = f"""
<style>
    /* Global Typography and Background */
    html, body, [class*="css"] {{
        font-family: {FONT_FAMILY};
        color: {COLOR_INK};
    }}
    .stApp {{
        background-color: {COLOR_WHITE};
    }}

    /* Top Navigation / Header Bar */
    .top-header-bar {{
        background-color: {COLOR_DEEP_BLUE};
        color: {COLOR_WHITE};
        padding: 12px 20px;
        border-radius: 4px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .top-header-bar h1 {{
        color: {COLOR_WHITE};
        font-size: 20px;
        font-weight: 600;
        margin: 0;
        padding: 0;
    }}
    .top-header-bar p {{
        color: {COLOR_LIGHT_BLUE};
        font-size: 13px;
        margin: 0;
        padding: 0;
    }}

    /* Sidebar Background & Spacing */
    section[data-testid="stSidebar"] {{
        background-color: {COLOR_PAPER};
        border-right: 1px solid {COLOR_BORDER_GREY};
        padding-top: 1rem;
    }}

    /* Flat Metric Card Containers */
    .metric-card {{
        background-color: {COLOR_WHITE};
        border: 1px solid {COLOR_BORDER_GREY};
        border-radius: 4px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }}
    .metric-label {{
        color: {COLOR_MUTED_TEXT};
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}
    .metric-value {{
        color: {COLOR_INK};
        font-size: 24px;
        font-weight: 700;
        line-height: 1.2;
    }}
    .metric-subtext {{
        color: {COLOR_MUTED_TEXT};
        font-size: 12px;
        margin-top: 4px;
    }}

    /* Side-by-side Emergency Route Card */
    .route-card-safest {{
        background-color: {COLOR_WHITE};
        border-left: 4px solid {COLOR_DEEP_BLUE};
        border-top: 1px solid {COLOR_BORDER_GREY};
        border-right: 1px solid {COLOR_BORDER_GREY};
        border-bottom: 1px solid {COLOR_BORDER_GREY};
        border-radius: 4px;
        padding: 14px;
    }}
    .route-card-fastest {{
        background-color: {COLOR_WHITE};
        border-left: 4px solid {COLOR_ORANGE};
        border-top: 1px solid {COLOR_BORDER_GREY};
        border-right: 1px solid {COLOR_BORDER_GREY};
        border-bottom: 1px solid {COLOR_BORDER_GREY};
        border-radius: 4px;
        padding: 14px;
    }}

    /* Callout & Warning Banners */
    .warning-banner {{
        background-color: {COLOR_PAPER};
        border-left: 4px solid {COLOR_ORANGE};
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 13px;
        color: {COLOR_INK};
        margin-bottom: 14px;
    }}

    /* Primary and Secondary Buttons */
    button[kind="primary"] {{
        background-color: {COLOR_ORANGE} !important;
        color: {COLOR_WHITE} !important;
        border-radius: 4px !important;
        border: none !important;
        font-weight: 600 !important;
    }}
    button[kind="secondary"] {{
        background-color: {COLOR_WHITE} !important;
        color: {COLOR_DEEP_BLUE} !important;
        border: 1px solid {COLOR_DEEP_BLUE} !important;
        border-radius: 4px !important;
    }}
</style>
"""
