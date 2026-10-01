# Learning Module 06: Analytic Hierarchy Process (AHP) & Multi-Criteria Decision Analysis

## 1. WHAT it does
The Analytic Hierarchy Process (AHP) is a mathematical Multi-Criteria Decision Making (MCDM) framework developed by Thomas Saaty. It decomposes multi-hazard susceptibility into hierarchical criteria and derives objective relative weights through reciprocal pairwise comparison matrices. A formal Consistency Ratio ($\text{CR}$) is calculated to prove that expert comparisons are mathematically transitively consistent ($\text{CR} < 0.10$).

## 2. WHY this method over alternatives
- **AHP vs. Equal Weighting:** Equal weighting naively assumes that a 5 km rainfall grid cell contributes the exact same predictive influence to flooding as local 30 m topography (slope, HAND). In real terrain, slope and HAND dominate localized water accumulation. AHP weights reflect true physical hydrologic dominance.
- **AHP vs. Machine Learning (Random Forest / Logistic Regression):** Training a supervised machine learning classifier requires a comprehensive, unbiased inventory of historic hazard events. In coastal South Chennai, ground-truthed point inventories of past floods are sparse, biased toward complaints along major arterial roads, and unavailable for slope cuts. Moreover, training on Cyclone Michaung and evaluating on Cyclone Michaung causes severe circular data leakage. AHP provides an explainable, physics-grounded susceptibility baseline that can be independently validated.
- **AHP vs. Simple Ranking / Point Allocation:** Ranking methods (e.g., rank-sum) arbitrarily assign linear weights without checking logical consistency. AHP enforces reciprocal transitivity ($a_{ik} \approx a_{ij} \cdot a_{jk}$) and provides the mathematically rigorous Consistency Ratio.

---

## 3. AHP Matrices, Consistency Ratios, and Pairwise Justifications

### 3.1 Flood Susceptibility AHP Matrix ($7 \times 7$)
Criteria:
1. **HAND ($H$):** Height Above Nearest Drainage
2. **Slope ($S$):** Surface inclination
3. **Built-Up ($B$):** Impervious surface from Dynamic World
4. **Distance to Water ($D$):** Distance to JRC permanent waterbodies and drainage channels
5. **Elevation ($E$):** Absolute altitude from Copernicus DEM
6. **NDVI ($V$):** Pre-event vegetation density
7. **Rainfall ($R$):** CHIRPS mean annual max 3-day climatology

| Criterion | HAND ($H$) | Slope ($S$) | Built-Up ($B$) | Dist Water ($D$) | Elevation ($E$) | NDVI ($V$) | Rainfall ($R$) | Priority Weight ($w_i$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **HAND ($H$)** | 1 | 2 | 3 | 4 | 4 | 5 | 6 | **0.3459** (34.6%) |
| **Slope ($S$)** | 1/2 | 1 | 2 | 3 | 3 | 4 | 5 | **0.2306** (23.1%) |
| **Built-Up ($B$)** | 1/3 | 1/2 | 1 | 2 | 2 | 3 | 4 | **0.1474** (14.7%) |
| **Dist Water ($D$)**| 1/4 | 1/3 | 1/2 | 1 | 1 | 3 | 3 | **0.0967** (9.7%) |
| **Elevation ($E$)** | 1/4 | 1/3 | 1/2 | 1 | 1 | 2 | 3 | **0.0893** (8.9%) |
| **NDVI ($V$)** | 1/5 | 1/4 | 1/3 | 1/3 | 1/2 | 1 | 2 | **0.0530** (5.3%) |
| **Rainfall ($R$)** | 1/6 | 1/5 | 1/4 | 1/3 | 1/3 | 1/2 | 1 | **0.0371** (3.7%) |

$$\lambda_{\max} = 7.1722, \quad \text{CI} = \frac{7.1722 - 7}{6} = 0.0287, \quad \text{RI}_7 = 1.32, \quad \mathbf{\text{CR} = \frac{0.0287}{1.32} = 0.0217 < 0.10 \quad \text{(PASSED)}}$$

#### One-Sentence Justifications for Every Pairwise Comparison (Flood):
1. **HAND vs. Slope (2):** HAND directly captures relative hydraulic gravity head to the nearest stream channel, making it slightly more decisive than local surface slope.
2. **HAND vs. Built-Up (3):** Even an impervious surface will not flood if situated on a well-drained ridge high above drainage lines.
3. **HAND vs. Dist Water (4):** Vertical clearance above water levels governs overtopping far more reliably than horizontal proximity.
4. **HAND vs. Elevation (4):** In a flat coastal plain, height relative to local channels isolates depressions much better than absolute altitude above sea level.
5. **HAND vs. NDVI (5):** Vegetation delays surface runoff infiltration but cannot prevent inundation in low-lying hydrologic sinks.
6. **HAND vs. Rainfall (6):** CHIRPS precipitation has near-zero spatial variation across a 20 km bbox, whereas HAND varies at 30 m resolution across drainage micro-basins.
7. **Slope vs. Built-Up (2):** Flat terrain ($<1^\circ$) causes chronic water ponding regardless of surface paving, moderately outweighing land cover.
8. **Slope vs. Dist Water (3):** Slope determines whether standing water can drain away, making it more critical than mere distance to channels.
9. **Slope vs. Elevation (3):** Slope drives local hydraulic gradient, whereas absolute elevation cannot distinguish between flat upland plateaus and flat lowland sinks.
10. **Slope vs. NDVI (4):** Infiltration capacity from vegetation cannot compensate for lack of gravitational drainage on flat slopes.
11. **Slope vs. Rainfall (5):** Micro-topographic slope creates sharp localized risk boundaries, whereas rainfall is spatially uniform across the corridor.
12. **Built-Up vs. Dist Water (2):** High imperviousness in urban wards generates immediate flash runoff that overwhelms street drainage before reaching major waterbodies.
13. **Built-Up vs. Elevation (2):** Urban concrete sprawl drastically elevates peak discharge compared to regional natural elevation gradients.
14. **Built-Up vs. NDVI (3):** Impervious concrete surfaces replace natural vegetated soil, directly governing storm runoff volume.
15. **Built-Up vs. Rainfall (4):** Urban land use drives catastrophic localized inundation under storm conditions far more than regional rainfall differences.
16. **Dist Water vs. Elevation (1):** Proximity to waterbodies and absolute elevation have equal moderate importance in predicting backwater flooding.
17. **Dist Water vs. NDVI (3):** Proximity to major retention basins like Pallikaranai is far more critical than local lawn or scrub density.
18. **Dist Water vs. Rainfall (3):** Overflow from overflowing tanks and lakes creates acute hazard zones independent of regional rainfall totals.
19. **Elevation vs. NDVI (2):** Regional gravity drainage potential moderately outweighs local surface vegetation roughness.
20. **Elevation vs. Rainfall (3):** Elevation differentiates coastal floodplains from inland highlands, providing more spatial discrimination than uniform rainfall.
21. **NDVI vs. Rainfall (2):** Pre-event vegetation roughness and root absorption capacity provide localized variation that uniform rainfall grids cannot.

---

### 3.2 Slope-Instability & Erosion AHP Matrix ($7 \times 7$)
Criteria:
1. **Slope ($S$):** Terrain gradient (degrees)
2. **Curvature ($C$):** Profile curvature (flow convergence)
3. **Distance to Cut Slopes ($D_r$):** Distance to engineered road cuts and quarries
4. **Local Relief ($R_l$):** Difference between max and min elevation in moving window
5. **Distance to Streams ($D_s$):** Distance to erosive drainage channels
6. **Land Cover / Bare Soil ($L_b$):** Bare and disturbed ground vs. stabilized cover
7. **Rainfall ($R$):** Extreme 3-day precipitation climatology

| Criterion | Slope ($S$) | Curvature ($C$) | Cut Slopes ($D_r$) | Relief ($R_l$) | Dist Streams ($D_s$) | Land Cover ($L_b$) | Rainfall ($R$) | Priority Weight ($w_i$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Slope ($S$)** | 1 | 3 | 3 | 4 | 5 | 6 | 7 | **0.3841** (38.4%) |
| **Curvature ($C$)** | 1/3 | 1 | 1 | 2 | 3 | 4 | 5 | **0.1768** (17.7%) |
| **Cut Slopes ($D_r$)**| 1/3 | 1 | 1 | 2 | 3 | 4 | 5 | **0.1768** (17.7%) |
| **Relief ($R_l$)** | 1/4 | 1/2 | 1/2 | 1 | 2 | 3 | 4 | **0.1112** (11.1%) |
| **Dist Streams ($D_s$)**| 1/5 | 1/3 | 1/3 | 1/2 | 1 | 2 | 3 | **0.0715** (7.2%) |
| **Land Cover ($L_b$)**| 1/6 | 1/4 | 1/4 | 1/3 | 1/2 | 1 | 2 | **0.0470** (4.7%) |
| **Rainfall ($R$)** | 1/7 | 1/5 | 1/5 | 1/4 | 1/3 | 1/2 | 1 | **0.0325** (3.3%) |

$$\lambda_{\max} = 7.1770, \quad \text{CI} = \frac{7.1770 - 7}{6} = 0.0295, \quad \text{RI}_7 = 1.32, \quad \mathbf{\text{CR} = \frac{0.0295}{1.32} = 0.0224 < 0.10 \quad \text{(PASSED)}}$$

#### One-Sentence Justifications for Every Pairwise Comparison (Slope-Instability):
1. **Slope vs. Curvature (3):** Slope angle is the fundamental physical driver of gravitational shear stress, strongly dominating plan curvature.
2. **Slope vs. Cut Slopes (3):** Unstable slope inclinations cause failures even without anthropogenic cuts, moderately dominating road cut proximity.
3. **Slope vs. Relief (4):** A steep face induces shear failure regardless of whether the surrounding total hill height is high or modest.
4. **Slope vs. Dist Streams (5):** Toe erosion by water can only trigger slides where slopes are sufficiently steep to fail.
5. **Slope vs. Land Cover (6):** Bare soil on flat ground does not slide; slope gradient is an absolute prerequisite for mass wasting.
6. **Slope vs. Rainfall (7):** Extreme rain triggers slides only where topography is predisposed by steep slope angles.
7. **Curvature vs. Cut Slopes (1):** Concave moisture-accumulating hollows and destabilized engineered road cuts have equal moderate importance.
8. **Curvature vs. Relief (2):** Flow-focusing hollows elevate pore water pressure more effectively than broad regional elevation differences.
9. **Curvature vs. Dist Streams (3):** Subsurface water convergence in slope hollows triggers internal shear collapse before channel toe scour occurs.
10. **Curvature vs. Land Cover (4):** Geomorphic curvature directs subsurface flow regardless of shallow surface vegetative cover.
11. **Curvature vs. Rainfall (5):** Micro-topographic convergence focuses groundwater pore pressure under any given rain event.
12. **Cut Slopes vs. Relief (2):** Over-steepened artificial cuts at quarry faces and highway embankments trigger failures faster than natural macro-relief.
13. **Cut Slopes vs. Dist Streams (3):** Mechanically fractured quarry walls and road excavations represent more active unstable failure planes than distant natural stream banks.
14. **Cut Slopes vs. Land Cover (4):** Excavation and blasting remove mechanical toe support, posing higher risk than bare undisturbed soil.
15. **Cut Slopes vs. Rainfall (5):** Road cuts exhibit high acute structural instability during any monsoon downpour.
16. **Relief vs. Dist Streams (2):** High topographic potential energy accelerates debris travel distance more than stream bank proximity.
17. **Relief vs. Land Cover (3):** Elevated gravitational potential energy on steep hillocks outweighs superficial land cover variations.
18. **Relief vs. Rainfall (4):** Local elevation changes provide spatial variation that uniform rainfall climatology cannot.
19. **Dist Streams vs. Land Cover (2):** Hydraulic undercutting at the base of slopes is more destabilizing than surface vegetation health.
20. **Dist Streams vs. Rainfall (3):** Channel scouring acts locally at 30 m resolution, whereas rainfall is uniform at 5 km.
21. **Land Cover vs. Rainfall (2):** Bare soil versus rooted forest cover differentiates erosion susceptibility better than uniform regional rainfall.

---

## 4. Key Parameters and Sensitivity
- Eigenvector Solver: Weights are calculated via the exact principal eigenvector of the comparison matrix, normalized such that $\sum w_i = 1.0$.
- Consistency Threshold ($\text{CR} < 0.10$): If $\text{CR} \ge 0.10$, judgment inconsistencies exist (e.g. $A > B$, $B > C$, but $C > A$). Our codebase incorporates runtime assertions `assert cr < 0.10` to guarantee mathematical integrity.

## 5. Common Mistakes and Limitations
1. **Subjective Bias in Pairwise Ranks:** AHP relies on expert elicitation. To prevent arbitrary bias, our pairwise values are anchored in documented physical equations (Manning's equation for runoff, infinite slope stability safety factor equations) and cross-checked against objective Shannon Entropy weights.
2. **Matrix Reciprocal Violation:** Forgetting that $a_{ji} = 1 / a_{ij}$ breaks the mathematical formulation. We enforce automated reciprocity in `analysis/mcdm.py`.

## 6. Likely Judge Questions and Model Answers
- **Q1: What is the exact mathematical definition of the Consistency Ratio (CR)?**
  *Answer:* $\text{CR} = \text{CI} / \text{RI}_n$, where $\text{CI} = (\lambda_{\max} - n) / (n - 1)$, $\lambda_{\max}$ is the principal eigenvalue of the pairwise comparison matrix, $n$ is matrix dimension ($7$), and $\text{RI}_7 = 1.32$ is Saaty's empirical Random Index for a $7 \times 7$ reciprocal matrix. A value below $0.10$ proves consistency.
- **Q2: Why did you give CHIRPS rainfall such a small weight (3.7% in flood, 3.3% in slope)?**
  *Answer:* Because the study corridor is 20 km x 20 km. At 0.05° (~5 km) resolution, CHIRPS has almost zero spatial variance across the scene. Over-weighting it would add an artificial constant offset rather than discriminating between low-lying wards and safe uplands.
- **Q3: How do you defend the pairwise comparison between HAND and Slope?**
  *Answer:* In low-gradient coastal terrain, slope measures local steepness, but HAND measures height above the hydrologic drainage base level. A flat surface perched 25 m above the river will never flood, whereas a flat surface 0.5 m above the river will submerge instantly. Therefore, HAND is assigned higher relative importance ($a_{12} = 2$).
- **Q4: Why did you assert CR < 0.10 in code?**
  *Answer:* In automated DSS pipelines, configurable parameters can be modified by operators. Asserting $\text{CR} < 0.10$ ensures that any operator re-weighting maintains rigorous transitivity before generating operational risk maps.
- **Q5: How does AHP handle correlated indicators (e.g. Elevation and HAND)?**
  *Answer:* While AHP assumes criteria independence, mild physical correlation is handled by cross-checking against objective Shannon Entropy weights and evaluating model sensitivity via 200 Monte Carlo perturbations.
