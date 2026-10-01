# GEOIMPATHON 1.0 - UI/UX Design System Specification

## 1. Design Philosophy & Audience

### 1.1 Target User
The primary user is a **District Disaster Management Officer (DDMO)** in the South Chennai – Chengalpattu jurisdiction during extreme weather contingencies (e.g., Cyclone Michaung-level precipitation). The user operates on a standard laptop (1366x768 or 1080p), under high stress and time pressure, and requires actionable facts, transparent risk scores, and predictable route recommendations.

### 1.2 Core Principles
- **No Decorative Overhead:** No glassmorphism, heavy drop shadows, neon accents, gradient washes, dark mode toggles, or AI chat-bubble widgets.
- **Cognitive Clarity:** Information hierarchy is immediate. Safe operations are rendered in stable blue tones; urgent hazards, warnings, and compromises are rendered in distinct orange tones.
- **Colorblind-Safe & Multi-Channel Signaling:** Blue-orange contrasts provide high colorblind accessibility. Geometry (line dash arrays, marker icons, thickness) reinforces color differentiation so color is never the sole signal.
- **Strict Single-Source Theming:** Every visual element derives from `app/theme.py` and `.streamlit/config.toml`.

---

## 2. Color Palette & Tokens

| Token Name | Hex Code | Semantic Role |
| :--- | :--- | :--- |
| `COLOR_WHITE` | `#FFFFFF` | Page canvas, card backgrounds, white casing on route polylines |
| `COLOR_PAPER` | `#F4F7FA` | Sidebar surface, secondary panels, callout background |
| `COLOR_BORDER_GREY` | `#D5DEE8` | 1px card borders, structural dividers, subtle grid lines |
| `COLOR_INK` | `#1B2733` | High-contrast body text, table text, metric values (never `#000000`) |
| `COLOR_MUTED_TEXT` | `#5B6B7B` | Captions, axis labels, metadata subtitles, table headers |
| `COLOR_DEEP_BLUE` | `#1F4E79` | Header bar, primary headings, safest emergency route line, primary action |
| `COLOR_MID_BLUE` | `#2E75B6` | Interactive hyperlinks, selected states, safe hospital map markers |
| `COLOR_LIGHT_BLUE` | `#DCE9F5` | Hover fills, table row selection, Low risk band |
| `COLOR_ORANGE` | `#E8761A` | Shortest (unweighted) route line, warning badges, primary action triggers |
| `COLOR_DARK_ORANGE` | `#B8470C` | Very High risk band, critical single-point-of-failure roads, blocked road flags |

### 2.1 Sequential Multi-Hazard Risk Color Ramp
One unified sequential ramp is used across all raster overlays, legends, and summary charts:
- **Low Risk:** `#DCE9F5` (Percentile: 0th – 50th)
- **Moderate Risk:** `#8DB8E0` (Percentile: 50th – 80th)
- **High Risk:** `#F4A259` (Percentile: 80th – 95th)
- **Very High Risk:** `#C2410C` (Percentile: 95th – 100th)

---

## 3. Typography & Spatial Grid

- **Font Family:** `'Source Sans 3', 'IBM Plex Sans', -apple-system, sans-serif`
- **Scale:**
  - Page Title: 24px (Semi-Bold, 600)
  - Section Heading: 20px (Semi-Bold, 600)
  - Subheading / Card Title: 16px (Medium, 500)
  - Body Text: 14px (Regular, 400, line-height: 1.5)
  - Captions & Microcopy: 12px (Regular, 400)
  - Headline Metric Value: 24px (Bold, 700)
- **Corner Radius:** `4px` everywhere (sharp, professional, utilitarian).
- **Borders:** `1px solid #D5DEE8`.
- **Spacing Grid:** Multiples of `8px` (`8px`, `16px`, `24px`, `32px`).

---

## 4. UI Component Library

1. **Top Header Bar:** Solid `#1F4E79` horizontal bar containing the title `"GEOIMPATHON 1.0 | Multi-Hazard Decision-Support System"` and study area subtitle `"South Chennai – Chengalpattu Corridor (Cyclone Michaung Validation)"`.
2. **Left Sidebar Panel:** Fixed control station styled with `#F4F7FA` surface:
   - Study Area Badge & Geographic Extent.
   - Scenario Selector: `[ Normal Scenario | Flood Scenario (Michaung) ]`.
   - Route Origin Dropdown (All identified settlements).
   - Destination Selector (`Nearest Safe Hospital` vs `Nearest Safe Shelter`).
   - Safety Priority Slider: `Fastest <----------> Safest` ($\alpha = 0.0$ to $10.0$, default $3.0$).
   - Layer Control Groups: Hazard Rasters, Infrastructure Network, Settlements & Facilities, Analytical Overlays.
3. **Flat Metric Card:** Clean rectangular card with 1px border, uppercase 12px muted label, 24px ink value, and 12px status microcopy.
4. **Emergency Route Comparison Panel:** Side-by-side cards comparing:
   - **Fastest Route (Orange):** Total travel time, total distance, length inside High/Very High risk.
   - **Safest Route (Deep Blue):** Total travel time, total distance, length inside High/Very High risk.
   - **Compromise Statement:** Direct plain-text summary (e.g., *"The safest route adds 7 min and avoids 3.8 km of high-risk road."*).
5. **Action List Export Button:** Prominent orange button to download official CSV and GeoJSON operational lists.

---

## 5. Screen Wireframes (All 5 Tabs)

### Tab 1: Risk Map
```
+--------------------------------------------------------------------------------------------------+
| [Header Bar: GEOIMPATHON 1.0 | South Chennai - Chengalpattu Multi-Hazard DSS]                     |
+--------------------------------------------------------------------------------------------------+
| SIDEBAR                 | TAB 1: RISK MAP                                                        |
|                         | One-line summary: Interactive multi-hazard susceptibility and risk map.|
| Study Area:             |                                                                        |
| South Chennai           | +-----------------------------------------------+ +------------------+ |
| [80.03, 12.80,          | |                                               | | Layer Summary  | |
|  80.22, 12.98]          | |                                               | | Multi-Hazard   | |
|                         | |                                               | | Flood (70%)    | |
| Scenario:               | |             Interactive Folium Map            | | Slope-Inst(30%)| |
| ( ) Normal              | |            (CartoDB Positron Base)            | | DEM Slope (deg)| |
| (*) Flood (Michaung)    | |                                               | +------------------+ |
|                         | |  - Rasters: Flood / Slope-Inst / Composite    | | Area by Risk   | |
| Layers:                 | |  - Facilities: Hospitals (Squares)            | | [VH]  5.2%     | |
| [x] Multi-Hazard Risk   | |                Shelters (Houses)              | | [H]  14.8%     | |
| [ ] Flood Susceptibility| |  - Settlements: White dots                    | | [M]  30.0%     | |
| [ ] Slope Instability   | |                                               | | [L]  50.0%     | |
| [ ] DEM Slope (deg)     | |  [Legend: Low, Mod, High, Very High]          | +------------------+ |
| [x] Safe Hospitals      | |  [Scale Bar] [North Arrow] [Source Footer]    | | Export Layers  | |
| [x] Safe Shelters       | +-----------------------------------------------+ | [Download GeoTIFF| |
| [x] Settlements         |                                                   +------------------+ |
+--------------------------------------------------------------------------------------------------+
```

### Tab 2: Emergency Route
```
+--------------------------------------------------------------------------------------------------+
| SIDEBAR                 | TAB 2: EMERGENCY ROUTE                                                 |
|                         | One-line summary: Least-risk emergency routing with live safety slider.|
| Origin:                 |                                                                        |
| [ Tambaram West     v ] | +------------------------------------+ +-------------------------------+ |
|                         | |                                    | | ROUTE COMPARISON             | |
| Destination:            | |       Interactive Route Map        | |                              | |
| (*) Nearest Safe Hosp   | |                                    | | [ FASTEST ]     [ SAFEST ]   | |
| ( ) Nearest Safe Shelt  | | - Orange dashed: Fastest route     | | 18 min          24 min       | |
|                         | | - Deep blue solid: Safest route    | | 11.2 km         13.8 km      | |
| Safety Slider (alpha):  | | - Crossed markers: Blocked roads   | | 4.2 km in High  0.0 km in High| |
| Fastest <-> Safest      | |                                    | +-------------------------------+ |
| [=====|========] 3.0    | |                                    | Compromise Assessment:           | |
|                         | |                                    | "The safest route adds 6 min   | |
| [ Calculate Route ]     | |                                    |  and avoids 4.2 km of high-risk| |
|                         | |                                    |  road segments."               | |
+--------------------------------------------------------------------------------------------------+
```

### Tab 3: Critical Roads & Isolation
```
+--------------------------------------------------------------------------------------------------+
| SIDEBAR                 | TAB 3: CRITICAL ROADS AND ISOLATION                                    |
|                         | One-line summary: Single points of failure and isolated communities.   |
| Top Critical Roads:     |                                                                        |
| [ 10                 v ]| +------------------------------------+ +-------------------------------+ |
|                         | |                                    | | TOP 10 CRITICAL ROAD CORRIDORS| |
| Pre-position Sites:     | |  Map:                              | | 1. GST Road / Tambaram Flyover| |
| [ 5                  v ]| |  - Dark orange lines: Top 10       | |    Iso Pop: 42,000 | +18 min  | |
|                         | |    critical road segments (1-10)   | | 2. Medavakkam Main Road       | |
| [x] Show Pre-position   | |  - Orange rings: Isolated /        | |    Iso Pop: 28,500 | +22 min  | |
|     Sites               | |    severely delayed settlements    | +-------------------------------+ |
|                         | |  - Blue stars: Pre-position sites  | | PRE-POSITIONING PLAN          | |
|                         | |                                    | | Site 1: Chromepet Sub-depot  | |
|                         | |                                    | | Site 2: Vandalur Junction    | |
+--------------------------------------------------------------------------------------------------+
```

### Tab 4: Dashboard
```
+--------------------------------------------------------------------------------------------------+
| TAB 4: OPERATIONAL DASHBOARD                                                                     |
| One-line summary: Real-time mission metrics, access collapse, and model verification.            |
|                                                                                                  |
| +--------------------+ +--------------------+ +--------------------+ +--------------------+     |
| | GOLDEN-HOUR ACCESS | | ISOLATED / DELAYED | | MODEL ROC AUC      | | ROUTE CONFIDENCE   |     |
| | 94.2% -> 58.1%     | | 7 Settlements      | | 0.884              | | 91.5% Stability    |     |
| | (-36.1% collapse)  | | 64,200 Exposure    | | Balanced test set  | | 200 Monte Carlo    |     |
| +--------------------+ +--------------------+ +--------------------+ +--------------------+     |
|                                                                                                  |
| +-----------------------------------------+ +--------------------------------------------------+ |
| | Area Distribution by Risk Class (Bar)   | | Top 10 Settlements at Risk (Horizontal Bar)      | |
| | [Low: 50% | Mod: 30% | High: 15% | VH] | | [Tambaram, Pallikaranai, Velachery, ...]         | |
| +-----------------------------------------+ +--------------------------------------------------+ |
| | Flood Validation ROC Curve              | | Monte Carlo AHP Sensitivity Distribution         | |
| | (Michaung S1 Truth vs Susceptibility)   | | (Weight perturbation +/-20%)                     | |
+--------------------------------------------------------------------------------------------------+
```

### Tab 5: Methods & Data
```
+--------------------------------------------------------------------------------------------------+
| TAB 5: METHODS AND DATA REGISTER                                                                 |
| One-line summary: Complete scientific traceability, parameter justification, and limitations.   |
|                                                                                                  |
| Full interactive table showing:                                                                  |
| Item | What it is | Why we use it | Alternative rejected & why | Code location | Stage           |
|                                                                                                  |
| Scientific Notes:                                                                                |
| - AHP Pairwise Matrices & Consistency Ratio Proof (CR < 0.10)                                    |
| - Entropy-weight cross-check & Spearman correlation                                              |
| - No-Validation-Leakage principle strictly enforced                                              |
| - Known limitations: 30m resolution, SAR urban shadow, static network speeds                      |
+--------------------------------------------------------------------------------------------------+
```
