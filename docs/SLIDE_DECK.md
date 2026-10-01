# GEOIMPATHON 1.0 — 10-Slide Competition Pitch Deck

> **Project Title:** Multi-Hazard Decision Support System & Least-Risk Emergency Routing  
> **Team Domain:** Problem Statement 1.1 (Disaster Management, Geospatial AI, Emergency Operations)  
> **Event:** GEOIMPATHON 1.0 — South Chennai to Chengalpattu Corridor

---

### Slide 1: Title & The Mission
- **Slide Title:** In a Flood, the Shortest Route Can Be the Deadliest
- **Subtitle:** Operational Decision-Support System for Multi-Hazard Risk & Least-Risk Emergency Routing
- **Key Visual:** Split image: An ambulance stranded in high floodwater vs. our UI showing the deep-blue safest detour route.
- **Talking Points:**
  - Standard GPS navigation optimizes for Euclidean distance or traffic delays, directing emergency vehicles into lethal drowning traps.
  - Our system dynamically balances physical travel distance against continuous flood and erosion hazards.
- **Key Metric:** Study Area: $400\text{ km}^2$ (South Chennai – Chengalpattu) | Validation Event: Cyclone Michaung (Dec 2023).

---

### Slide 2: The Study Area & The Topographic Reality
- **Slide Title:** Terrain Dictates Hazard: Lowlands, Marshes & Quarry Bunds
- **Subtitle:** Flat Coastal Corridor Vulnerabilities
- **Key Visual:** 3D elevation drape (Copernicus DEM) highlighting the Pallikaranai wetland depression flanked by Vandalur hills.
- **Talking Points:**
  - Terrain is mostly flat coastal plain ($0\text{--}1.2^\circ$), making FLOOD the overwhelming primary hazard.
  - Secondary hazard: Slope-instability and erosion susceptibility on granitic hills, lake bunds, and quarry faces.
  - We state this plainly and honestly without overselling.
- **Key Metric:** Elevation: $1.2\text{ m} \to 72\text{ m}$ | Dominant Hazard: $70\%$ Flood / $30\%$ Slope Instability.

---

### Slide 3: Data Architecture & The No-Leakage Protocol
- **Slide Title:** 100% Open Data & Scientific Integrity
- **Subtitle:** Google Earth Engine + OpenStreetMap Only
- **Key Visual:** Architecture flowchart showing data ingest (Sentinel-1, Sentinel-2, Copernicus DEM, CHIRPS, JRC GSW, Dynamic World, OSM).
- **Talking Points:**
  - Zero external commercial or population downloads (Dynamic World built-up area used as population proxy).
  - **No-Validation-Leakage Protocol:** Sentinel-1 SAR flood imagery from Cyclone Michaung is strictly withheld from model construction; it is used purely as post-hoc ground truth.
- **Key Metric:** Native resolution: $10\text{ m} \to 30\text{ m}$ | Storage budget: $<35\text{ MB}$ local cache.

---

### Slide 4: Multi-Criteria Susceptibility Modeling
- **Slide Title:** Transparent Multi-Criteria Evaluation: AHP & Shannon Entropy
- **Subtitle:** Mathematically Consistent Criterion Weighting
- **Key Visual:** Comparison matrix table and multi-hazard risk map with 4 percentile tiers (Low, Mod, High, Very High).
- **Talking Points:**
  - Flood AHP Consistency Ratio $\text{CR} = 0.0217 \ll 0.10$ (HAND $34.6\%$, Elevation $23.1\%$, Slope $15.4\%$).
  - Objective verification using Shannon Information Entropy ($r_s = 0.751, p < 10^{-15}$).
  - Percentile classification preserves local vulnerability distribution without arbitrary external thresholds.
- **Key Metric:** Area Distribution: $50\%$ Low, $30\%$ Moderate, $15\%$ High, $5\%$ Very High.

---

### Slide 5: Least-Risk Emergency Routing
- **Slide Title:** Dynamic Safety Multiplier ($\alpha$): Balancing Detours vs. Danger
- **Subtitle:** Cost Function: $C_e = L_e \cdot (1 + \alpha \cdot R_e)$
- **Key Visual:** Interactive dual-route map (Orange dashed fastest vs. Deep blue solid safest) with side-by-side metric cards.
- **Talking Points:**
  - Continuous risk sampled every 30 m along road geometry ($0.5\cdot\text{mean} + 0.5\cdot\text{max}$).
  - Structural risk penalties for underpasses ($+0.15$) and low bridges over water ($+0.08$).
  - Automatic filtering of inundated hospitals ($R \ge 80\text{th percentile}$) to prevent casualty delivery to flooded facilities.
- **Key Metric:** Flood Zone Exposure: Fastest Route $68\% \to$ Safest Route $0\%$ ($+4\text{ min}, +1.8\text{ km}$ trade-off).

---

### Slide 6: Road Criticality & Removal Impact
- **Slide Title:** Single Points of Failure: Beyond Betweenness Centrality
- **Subtitle:** Two-Stage Simulated Removal Impact ($G \setminus \{e^*\}$)
- **Key Visual:** Folium map displaying the Top 10 Critical Road corridors with numbered badges ($1\text{--}10$).
- **Talking Points:**
  - Betweenness centrality treats an empty alleyway identically to a major hospital causeway.
  - Stage 1 screens candidate links by traversing built-up exposure; Stage 2 simulates physical link loss ($G \setminus \{e^*\}$).
  - Ranks roads by exact newly isolated exposure and acute transit delays.
- **Key Metric:** Rank 1 (Mount–Medavakkam Road): Cuts access for 17 residential wards and $135,000$ exposure units.

---

### Slide 7: Settlement Isolation & Relief Pre-positioning
- **Slide Title:** Proactive Relief: Staging Boats & Ambulances Before the Storm
- **Subtitle:** Greedy Maximum-Coverage Staging Heuristic ($k = 5$)
- **Key Visual:** Map of 24 isolated settlements (orange circles) and 5 safe pre-positioning hubs (blue badges).
- **Talking Points:**
  - In the flood scenario, $24$ settlements are completely isolated from safe hospitals, and $25$ suffer $\ge 2\times$ delays.
  - Greedy heuristic places $5$ relief hubs on verified safe ground outside High-risk zones ($<80\text{th percentile}$).
  - Tailored operational equipment packages (rescue boats in marsh basins; 4x4 ambulances on highway cuts).
- **Key Metric:** Coverage: $>200,000$ vulnerable exposure units sheltered or covered within a $3.5\text{ km}$ radius.

---

### Slide 8: Golden-Hour Healthcare Access Collapse
- **Slide Title:** Measuring Systemic Failure: How Hospital Access Collapses
- **Subtitle:** 60-Minute Trauma & 30-Minute Acute Access Deprivation
- **Key Visual:** Grouped bar chart comparing normal vs. flood access percentages with downward collapse callout badges.
- **Talking Points:**
  - $\text{Access}_T$: Proportion of built-up exposure reaching an operational hospital within $T$ minutes.
  - Severe flood conditions trigger systemic access collapse across South Chennai.
- **Key Metric:** 
  - Golden-Hour (60 min) Access: $99.3\% \to 76.7\%$ ($\mathbf{-22.6\% \ \text{Collapse}}$, $132,506$ exposure units cut off).
  - Acute Emergency (30 min) Access: $99.3\% \to 69.7\%$ ($\mathbf{-29.6\% \ \text{Collapse}}$, $173,601$ exposure units).

---

### Slide 9: Independent Validation & The Spatial Autocorrelation Defense
- **Slide Title:** Independent Ground Truth Validation vs. Cyclone Michaung
- **Subtitle:** ROC Curve, Spatial Block CV, and Why AUC Alone Misleads
- **Key Visual:** Two-panel figure: ROC Curve ($\text{AUC} = 0.707$) and 16-Block Spatial Cross-Validation Grid.
- **Talking Points:**
  - Balanced 1:1 test sample ($5,000$ flooded, $5,000$ dry pixels), permanent water masked ($>80\%$).
  - Accuracy $65.2\%$, Precision $63.9\%$, Recall $69.8\%$, F1 $0.667$.
  - Spatial Block Cross-Validation controls for Tobler's First Law (Mean Block $\text{AUC} = 0.686 \pm 0.037$).
  - Explains why AUC alone can mislead: error cost asymmetry and spatial autocorrelation inflation.
- **Key Metric:** Balanced $\text{AUC} = 0.707$ | Spatial Block $\text{AUC} = 0.686 \pm 0.037$ across 16 zones.

---

### Slide 10: Monte Carlo Robustness & Command-Center Ready
- **Slide Title:** Decision Confidence: 200 Monte Carlo Perturbations
- **Subtitle:** Production-Grade, Tested, and Deployed
- **Key Visual:** Two-panel Monte Carlo figure showing $100\%$ route stability across benchmark origins.
- **Talking Points:**
  - 200 stochastic trials perturbing AHP weights by $\pm 20\%$ multiplicative noise and hazard split ($0.60\text{--}0.80$).
  - Emergency routes remain $100\%$ stable; critical road bottlenecks maintain $92.5\%$ persistence.
  - Complete, lightweight codebase: 23 unit tests pass in 2 seconds; runs entirely offline or online.
- **Key Metric:** Route Confidence: $\mathbf{100.0\%}$ | Critical Road Persistence: $\mathbf{92.5\%}$ | Total Unit Tests: **23/23 Passing**.
