# Learning Module 08: Multi-Hazard Weighted Overlay & Risk Categorization

## 1. WHAT it does
Multi-Hazard Weighted Linear Combination (WLC) computes the composite risk index by calculating the cell-by-cell weighted sum of normalized indicator layers. It first derives separate, physically grounded Flood Susceptibility ($H_{\text{flood}}$) and Slope-Instability Susceptibility ($H_{\text{slope}}$) rasters using their respective AHP weights. It then synthesizes them into an overall Multi-Hazard Risk Index ($R_{\text{multi}} = 0.70 H_{\text{flood}} + 0.30 H_{\text{slope}}$) and classifies the landscape into four operational tiers (Low, Moderate, High, Very High) using study-area percentile breaks.

## 2. WHY this method over alternatives
- **WLC vs. Boolean Overlay (AND/OR Logic):** Boolean overlay produces sharp binary masks (either high-risk or low-risk). It creates artificial cliff-edges where a single pixel falling $1 \text{ mm}$ below an arbitrary threshold is flagged as completely safe. WLC produces a continuous, gradational spectrum of risk that reflects real-world environmental vulnerability.
- **WLC vs. Black-Box Machine Learning Ensembles:** Deep neural networks or gradient-boosted trees require vast historical training datasets that do not exist for multi-hazard slope-flood combinations in Chennai. Furthermore, emergency decision-makers cannot interrogate *why* a particular road was classified as high-risk by a 50-layer neural network. WLC is 100% transparent, auditable, and easily explained to municipal leadership.
- **Percentile Breaks vs. Equal Interval / Natural Breaks (Jenks):**
  - *Equal Interval ($0\text{--}0.25, 0.25\text{--}0.50, \dots$)* fails when normalized scores cluster in specific ranges (e.g. low-gradient floodplains where scores cluster between $0.4\text{--}0.8$), leaving some classes empty.
  - *Natural Breaks (Jenks)* is computationally expensive on millions of pixels and creates arbitrary break values that shift whenever a boundary changes.
  - *Percentile Breaks (<50th, 50-80th, 80-95th, >95th)* guarantee consistent operational resource allocation: exactly the top 5% most vulnerable land is designated "Very High", prioritizing emergency action where intervention is most critical.

---

## 3. HOW it works (with worked numeric example)

### Mathematical Formulation:
1. **Component Hazards:**
   $$H_{\text{flood}}(x, y) = \sum_{i=1}^{7} w_{\text{flood}, i} \cdot I_{\text{norm}, i}(x, y)$$
   $$H_{\text{slope}}(x, y) = \sum_{j=1}^{7} w_{\text{slope}, j} \cdot J_{\text{norm}, j}(x, y)$$
   *(Where $\sum w_{\text{flood}, i} = 1.0$ and $\sum w_{\text{slope}, j} = 1.0$)*.
2. **Multi-Hazard Composite Index:**
   $$R_{\text{multi}}(x, y) = W_{\text{flood}} \cdot H_{\text{flood}}(x, y) + W_{\text{slope}} \cdot H_{\text{slope}}(x, y)$$
   *(Default weights: $W_{\text{flood}} = 0.70$, $W_{\text{slope}} = 0.30$; $\sum W = 1.0$)*.

### Worked Numeric Example:
Consider a cell along the Medavakkam marsh embankment:
- Normalized Flood Indicators:
  - $\text{HAND} = 0.85$, $\text{Slope} = 0.90$, $\text{Built} = 0.75$, $\text{DistWater} = 0.95$, $\text{Elev} = 0.80$, $\text{NDVI} = 0.60$, $\text{Rain} = 0.50$.
  $$H_{\text{flood}} = (0.3459 \times 0.85) + (0.2306 \times 0.90) + (0.1474 \times 0.75) + (0.0967 \times 0.95) + (0.0893 \times 0.80) + (0.0530 \times 0.60) + (0.0371 \times 0.50)$$
  $$H_{\text{flood}} = 0.2940 + 0.2075 + 0.1106 + 0.0919 + 0.0714 + 0.0318 + 0.0186 = \mathbf{0.8258}$$

- Normalized Slope-Instability Indicators:
  - $\text{Slope} = 0.25$, $\text{Curvature} = 0.40$, $\text{CutSlopes} = 0.60$, $\text{Relief} = 0.30$, $\text{DistStreams} = 0.50$, $\text{LandCover} = 0.40$, $\text{Rain} = 0.50$.
  $$H_{\text{slope}} = (0.3841 \times 0.25) + (0.1768 \times 0.40) + (0.1768 \times 0.60) + (0.1112 \times 0.30) + (0.0715 \times 0.50) + (0.0470 \times 0.40) + (0.0325 \times 0.50)$$
  $$H_{\text{slope}} = 0.0960 + 0.0707 + 0.1061 + 0.0334 + 0.0358 + 0.0188 + 0.0163 = \mathbf{0.3771}$$

- Multi-Hazard Combination:
  $$R_{\text{multi}} = (0.70 \times 0.8258) + (0.30 \times 0.3771) = 0.5781 + 0.1131 = \mathbf{0.6912}$$

- Percentile Classification (against study corridor distribution):
  - 50th percentile ($P_{50}$) = $0.380$
  - 80th percentile ($P_{80}$) = $0.590$
  - 95th percentile ($P_{95}$) = $0.720$
  - Since $0.590 \le 0.6912 < 0.720 \implies \mathbf{High \ Risk \ Zone}$.

---

## 4. Key Parameters and Sensitivity
- Multi-Hazard Split ($0.70 / 0.30$): Reflects the geomorphic dominance of coastal lowlands where storm flooding is the existential catastrophic hazard. The $0.30$ slope weight ensures localized hillocks, quarries, and highway cut slopes are not ignored.
- Percentile Thresholds:
  - `< 50th percentile`: **Low Risk** (Safe operational zones, shelter staging areas).
  - `50th – 80th percentile`: **Moderate Risk** (Passable with caution, monitor drainage).
  - `80th – 95th percentile`: **High Risk** (Flooded roads slowed to $5 \text{ km/h}$, rescue assets required).
  - `> 95th percentile`: **Very High Risk** (Impassable; roads severed from emergency routing).

## 5. Common Mistakes and Limitations
1. **Failing to Verify Weights Sum to 1.0:** In custom or user-adjusted overlays, un-normalized weights arbitrarily scale the output range, invalidating downstream percentile comparisons. We enforce `assert np.isclose(sum(weights), 1.0)`.
2. **Assuming Percentiles are Universal:** Percentile breaks are relative to South Chennai. The 95th percentile in Chennai corresponds to an absolute risk score calibrated to this coastal plain, not a mountainous terrain.

## 6. Likely Judge Questions and Model Answers
- **Q1: Why did you choose a 70/30 split between flood and slope instability?**
  *Answer:* Geomorphically, the Tambaram-Pallikaranai corridor is a low-relief coastal delta where tropical cyclone storm surges and riverine overtopping represent >85% of historical disaster losses. Slope instability is confined to localized quarry faces, rail/highway embankments, and lake bunds. A 70/30 split prevents slope hazards from being ignored while properly reflecting flood dominance.
- **Q2: Why use percentile breaks instead of absolute thresholds like 0.25, 0.50, 0.75?**
  *Answer:* Multi-criteria index distributions rarely span a perfect uniform distribution from 0.0 to 1.0. Absolute thresholds often lead to empty categories or lump 80% of the area into one class. Percentile breaks guarantee operational discrimination: emergency managers know that "Very High" represents exactly the top 5% most critical terrain.
- **Q3: What happens to a road whose multi-hazard risk is in the Very High band?**
  *Answer:* In our emergency routing model, roads in the Very High band ($\ge 95\text{th percentile}$) are treated as impassable and severed from the graph to prevent emergency vehicles from entering deadly drowning traps.
- **Q4: Are the Flood and Slope layers exported separately?**
  *Answer:* Yes. The pipeline exports individual GeoTIFF and PNG layers for Flood Hazard, Slope Instability Hazard, DEM Slope (degrees), and Combined Multi-Hazard Risk, each with dedicated layer toggles in the Streamlit application.
- **Q5: Can an emergency officer adjust the 70/30 hazard weights in real time?**
  *Answer:* Yes, the configuration and user interface support live adjustments to hazard weights with automatic re-normalization ensuring they always sum to 1.0.
