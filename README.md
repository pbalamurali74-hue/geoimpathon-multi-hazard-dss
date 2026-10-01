# GEOIMPATHON 1.0 — Multi-Hazard Decision Support System & Least-Risk Emergency Routing

> **Problem Statement 1.1:** Multi-Hazard Decision-Support System + Least-Risk Emergency Routing  
> **Target Audience:** District Disaster Management Officers (DDMO), Emergency Operations Center (EOC) Incident Commanders, Municipal Rescue Dispatchers.  
> **Study Area:** South Chennai to Chengalpattu Corridor (`[80.03, 12.80, 80.22, 12.98]` [lon_min, lat_min, lon_max, lat_max], ~20 x 20 km: Tambaram, Pallikaranai, Velachery, Kattankulathur).  
> **Validation Event:** Cyclone Michaung Floods (December 2023).

---

## 1. Core Mission

> *"In a flood, the shortest route to a hospital can be the deadliest. Our system finds the least-risk route, names the roads whose loss isolates the most people, says where to pre-position relief, and measures how much hospital access collapses in a flood."*

---

## 2. Study Area & Topographic Reality

The South Chennai – Chengalpattu corridor is predominantly a **flat coastal and estuarine plain** flanked by the Bay of Bengal, the Pallikaranai marshland basin, and the Adyar river drainage network. 

- **Primary Hazard (Dominant): FLOOD.** Extreme precipitation, slow coastal drainage, low hydraulic gradients, and impervious urban expansion make flood inundation the overwhelming hazard during cyclonic storms like Cyclone Michaung.
- **Secondary Hazard: SLOPE-INSTABILITY & EROSION SUSCEPTIBILITY.** Because the terrain is predominantly flat, we plainly state: **we do not oversell this hazard**. Slope instability and erosion susceptibility are confined strictly to isolated granitic hills (e.g. Vandalur hills, St. Thomas Mount / Trisulam margins), active stone quarries, elevated railway/highway embankments, and lake retention bunds.

---

## 3. Strict Data & Scientific Integrity Protocol

### Allowed Data Only (Google Earth Engine + OpenStreetMap)
To maintain complete reproducibility, this system uses **zero external population datasets** (NO WorldPop, NO GHSL, NO LandScan, NO MERIT Hydro, NO commercial traffic APIs).
- **Copernicus GLO-30 DEM (30 m):** Elevation, slope (degrees), curvature, and Height Above Nearest Drainage (HAND) proxy.
- **Sentinel-1 SAR (IW VV):** Dual-date backscatter change detection ($\text{Post} - \text{Pre}$ in dB) with Refined Lee / focal speckle filtering and Otsu thresholding.
- **Sentinel-2 MSI (10 m):** Pre-disaster Red and NIR bands for Normalized Difference Vegetation Index (NDVI) and infiltration capacity.
- **CHIRPS Climatology (0.05° ~ 5 km):** 20+ year mean annual maximum 3-day rainfall to quantify extreme storm susceptibility.
- **JRC Global Surface Water (30 m):** 38-year permanent water occurrence mask ($>80\%$) to exclude existing waterbodies.
- **Dynamic World V1 (10 m):** Pre-event deep learning land use composite; built-up class serves as our **built-up exposure (population proxy)**.
- **OpenStreetMap (OSM):** Drive network topology, health facilities (hospitals, clinics), candidate shelters, and settlements.

### The "No-Validation-Leakage" Principle
The Sentinel-1 SAR flood inundation extent from Cyclone Michaung (Dec 2023) is **strictly withheld from all hazard layers, normalizations, and MCDM weights**. It is used purely as an **independent, post-hoc out-of-sample ground truth** layer.

---

## 4. End-to-End Pipeline Architecture

```mermaid
flowchart LR
    subgraph S1["1. Satellite Data"]
        S1A["Sentinel-1 SAR"]
        S1B["Sentinel-2 MSI"]
        S1C["Copernicus DEM"]
        S1D["CHIRPS Rain"]
        S1E["JRC Water"]
        S1F["Dynamic World"]
        S1G["OpenStreetMap"]
    end

    subgraph S2["2. Processing"]
        S2A["Speckle Filter & dB"]
        S2B["Horn Slope & HAND"]
        S2C["NDVI Infiltration"]
        S2D["Permanent Water Mask"]
        S2E["Exposure Proxy"]
        S2F["Drive Graph Topology"]
    end

    subgraph S3["3. Geospatial Analysis"]
        S3A["Min-Max Norm [0, 1]"]
        S3B["Fuzzy HAND Comparison"]
        S3C["AHP Solver (CR < 0.10)"]
        S3D["Shannon Entropy Cross-Check"]
        S3E["Continuous Edge Sampling"]
        S3F["Structural Bumps"]
    end

    subgraph S4["4. Models"]
        S4A["Multi-Hazard Risk Map"]
        S4B["Dijkstra Routing (Cost = L*(1+a*R))"]
        S4C["Removal Impact (G \\ {e*})"]
        S4D["Greedy Max-Coverage"]
        S4E["Golden-Hour Access"]
        S4F["200 Monte Carlo Runs"]
    end

    subgraph S5["5. Dashboard"]
        S5A["Multi-Hazard Risk Map"]
        S5B["Safest vs Fastest Router"]
        S5C["Top 10 Critical Roads"]
        S5D["Pre-positioning Plan"]
        S5E["Access Collapse Stats"]
        S5F["Validation & ROC/AUC"]
    end

    subgraph S6["6. Decisions"]
        S6A["Prioritized Sandbagging"]
        S6B["Safe Evacuation Route"]
        S6C["Single Points of Failure"]
        S6D["Boat/Ambulance Staging"]
        S6E["Hospital Surge Alert"]
    end

    S1 --> S2 --> S3 --> S4 --> S5 --> S6
```

---

## 5. Key System Capabilities

### 1. Multi-Hazard Susceptibility & Risk Classification
- **Flood Susceptibility:** Weighted combination of HAND, elevation, slope, distance to water, impervious built-up, NDVI, and CHIRPS rainfall. Analytic Hierarchy Process ($\lambda_{\max} = 7.172, \text{CR} = 0.0217 \ll 0.10$).
- **Slope-Instability Susceptibility:** Geomorphically weighted combination of slope angle, curvature, local relief, road-cut distance, stream proximity, and rainfall ($\lambda_{\max} = 7.177, \text{CR} = 0.0224 \ll 0.10$).
- **Objective Cross-Check:** Shannon Entropy Weighting ($r_s = 0.751, p < 10^{-15}$).
- **Multi-Hazard Index:** $0.70 \times \text{Flood} + 0.30 \times \text{Slope}$.
- **Percentile Thresholds:** Low ($<50\text{th}$), Moderate ($50\text{--}80\text{th}$), High ($80\text{--}95\text{th}$), Very High ($\ge 95\text{th}$).

### 2. Least-Risk Emergency Routing Engine
- **Edge Cost Formulation:** $C_e = L_e \cdot (1 + \alpha \cdot R_e)$, with live interactive Safety Slider ($\alpha \in [0.0, 10.0]$).
- **Continuous Edge Sampling:** Risk sampled every 30 m along road geometry: $R_e = 0.5 \cdot \text{mean} + 0.5 \cdot \text{max}$.
- **Structural Trap Penalties:** $+0.15$ risk bump for underpasses/tunnels (`tunnel=*`, `layer < 0`) and $+0.08$ for low river bridges.
- **Inundated Edge Severance:** Edges with $R_e \ge 0.5983$ (95th percentile) are blocked in the flood scenario.
- **Facility Safety Filter:** Excludes inundated hospitals ($R \ge 80\text{th}$ percentile) to prevent routing casualties to flooded wards.
- **Safe Fallback:** If floodwaters sever all access to an isolated low-lying settlement, the system automatically falls back to the lowest-risk route and warns the operator.

### 3. Road Criticality & Removal Impact Vulnerability
- **Stage 1 (Path Flow Accumulation):** Computes safest paths from all 141 settlements to nearest safe hospital; screens top 40 bottleneck corridors carrying high built-up exposure.
- **Stage 2 (Removal Impact Verification):** Simulates exact link failure ($G \setminus \{e^*\}$); identifies the **Top 10 Single Points of Failure** based on newly isolated exposure and detour minutes.
- **Actionable Callouts:** Each critical road receives a one-line operational summary (e.g. Mount–Medavakkam Road severance forces detours for 17 communities).

### 4. Settlement Isolation & Greedy Pre-positioning
- **Settlement Isolation:** Analyzes reachability in $G_{\text{flood}}$:
  - **24 Isolated Settlements** ($136,867\text{ exposure units}$) completely cut off from safe hospitals.
  - **25 Severely Delayed Settlements** ($157,452\text{ exposure units}$) experiencing $\ge 2.0\times$ normal travel time.
  - **92 Connected Settlements** remain accessible.
- **Greedy Maximum-Coverage Pre-positioning:** Recommends $k = 5$ staging hubs on verified safe ground outside High-risk zones, covering $>200,000$ vulnerable exposure units with specialized asset mixes:
  - Hub #1: Hydro-Rescue Unit (4 Inflatable Rescue Boats, 2 High-Water Tractors) at Pathala Vigneshvarar Temple.
  - Hub #2: Urban Inundation Unit (3 Inflatable Boats, 2 4x4 Ambulances) at Sri Lakshmi Kuberar Temple.
  - Hub #3: Highway Transit Choke Hub (3 High-Clearance Ambulances, Generators) at Rama Anjaneya Koil.
  - Hub #4: Bund Shoring & Rapid Rescue (2 Boats, 1,000 Sandbags) at Ganesh Temple.
  - Hub #5: Southern Emergency Medical Outpost (2 Ambulances, Field Clinic) at Designated Public Shelter.

### 5. Golden-Hour Access Collapse & Monte Carlo Robustness
- **Golden-Hour (60 min) Access Collapse:** Drops from **$99.3\%$** normal baseline to **$76.7\%$** in flood $\implies \mathbf{-22.6\% \ \text{Access Collapse}}$ ($132,506$ exposure units lose timely care).
- **Acute Emergency (30 min) Access Collapse:** Drops from **$99.3\%$** to **$69.7\%$** $\implies \mathbf{-29.6\% \ \text{Collapse}}$ ($173,601$ exposure units).
- **200-Run Monte Carlo Robustness:**
  - Multi-parameter perturbation ($\pm 20\%$ multiplicative noise on AHP weights, $0.60\text{--}0.80$ multi-hazard split).
  - **Route Confidence:** $\mathbf{100.0\%}$ stability across primary benchmark corridors.
  - **Critical Road Persistence:** $\mathbf{92.5\%}$ average retention of top-10 single points of failure across all trials.

### 6. Independent Satellite Validation
- **Balanced Ground Truth Sample:** $N = 5,000$ flooded and $N = 5,000$ dry pixels from Sentinel-1 SAR change detection (Cyclone Michaung, Dec 2023), permanent water excluded.
- **ROC AUC:** $\mathbf{0.707}$.
- **Operational Performance ($\tau = 0.511$):** Accuracy $65.2\%$, Precision $63.9\%$, Recall (Sensitivity) $69.8\%$, F1-Score $0.667$.
- **Spatial Block Cross-Validation ($4 \times 4$ Grid):** Mean Block $\text{AUC} = \mathbf{0.686 \pm 0.037}$, demonstrating genuine spatial generalizability free of spatial autocorrelation inflation (Tobler's First Law).
- **Slope Sanity Check:** Confirms monotonic scaling of hazard with slope ($r_s = 0.860, p < 10^{-15}$). Plainly stated as a geomorphic sanity check, not a validation.

---

## 6. Project Directory Layout

```
├── README.md                      # Complete system documentation & defense guide
├── config.yaml                    # Single source of truth (bbox, weights, thresholds)
├── requirements.txt               # Pinned Python package dependencies
├── app/
│   ├── app.py                     # 5-tab Streamlit Command-Center Dashboard
│   └── theme.py                   # Strict design tokens (WCAG AA palette, typography)
├── analysis/
│   ├── mcdm.py                    # AHP eigenvector solver, min-max, Shannon entropy
│   ├── hazard.py                  # Multi-hazard overlay, percentile classification
│   ├── raster_ops.py              # GeoTIFF I/O, RGBA palette rendering, 500m grid
│   ├── validation.py              # ROC/AUC, confusion matrix, spatial block CV
│   ├── access.py                  # Golden-Hour (30m/60m) access collapse engine
│   └── monte_carlo.py             # 200 stochastic runs, route confidence, persistence
├── routing/
│   ├── network.py                 # OSMnx 2.x drive network extraction & pruning
│   ├── router.py                  # Least-risk Dijkstra, edge risk attribution, dual routes
│   ├── criticality.py             # Path flow accumulation & G \ {e*} removal impact
│   └── preposition.py             # Settlement isolation & greedy max-coverage heuristic
├── data/
│   └── sample/                    # Cached rasters, graphs, and action lists (< 35 MB)
├── outputs/                       # Publication PNGs, action CSVs, GeoJSONs, metrics JSON
├── docs/
│   ├── design.md                  # Comprehensive architectural blueprint
│   ├── WHAT_AND_WHY.md            # What-and-Why Register for every dataset & tool
│   ├── GLOSSARY.md                # 20 key geospatial & disaster terms
│   ├── VIVA_QA.md                 # 30 Q&A guide for competition jury defense
│   ├── DEMO_SCRIPT.md             # 3-minute timed live pitch walkthrough
│   ├── SLIDE_DECK.md              # 10-slide presentation deck outline
│   ├── DEFENSE_CHEAT_SHEET.md     # Top-10 hardest judge questions & winning answers
│   └── learn/                     # 12 pedagogical modules (01 to 12)
└── tests/
    ├── test_step1.py              # Tests for AHP, normalization, layers
    ├── test_step2.py              # Tests for edge cost, blocked edges, dual routes
    ├── test_step3.py              # Tests for S1 validation, spatial block CV, no leakage
    ├── test_step4.py              # Tests for criticality removal impact, pre-positioning
    └── test_step5.py              # Tests for Golden-Hour access, Monte Carlo robustness
```

---

## 7. How to Install and Run

### 1. Environment Setup
```bash
# Clone the repository and navigate into the workspace
git clone <repository_url>
cd "Kackathon day 2"

# Ensure Python 3.10+ is available
python3 --version

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Automated Verification Tests
```bash
# Execute all 23 unit and integration tests
python3 -m pytest -v
```
*(All 23 tests should pass in under 2 seconds).*

### 3. Launch the Command-Center Web Application
```bash
# Start the Streamlit GIS Dashboard
streamlit run app/app.py
```
Open your browser at `http://localhost:8501`.

---

## 8. Honest Scientific Limitations

1. **Synthetic Aperture Radar Urban Under-Detection:** C-band Sentinel-1 SAR experiences double-bounce reflections and radar shadow in dense multistory urban corridors, causing under-detection of shallow street flooding. In open areas, marshes, and agricultural fields, specular reflection detection is near-perfect.
2. **Coarse Precipitation Climatology:** CHIRPS resolution is $\sim 5\text{ km}$ ($0.05^\circ$). Across our $20 \times 20\text{ km}$ study area, extreme 3-day rainfall varies by only $\sim 20\text{ mm}$. We deliberately assign CHIRPS a low AHP weight ($2.6\%$), validated by Shannon Entropy ($<3\%$).
3. **No Live Traffic:** The routing model uses OpenStreetMap speed classifications with flood slowdowns ($5\text{ km/h}$) and structural blockage. It reflects physical road passability, not real-time vehicular congestion.
4. **Proxy Exposure:** Human exposure is derived from Sentinel-2 Dynamic World built-up footprint probability. It represents physical structural exposure, not real-time mobile population census.
5. **No Landslide Inventory:** South Chennai lacks a documented historical landslide inventory from the Geological Survey of India. Our slope-instability layer is transparently evaluated as a **geomorphic sanity check** confirming physical slope-dependency, NOT an empirical validation.
