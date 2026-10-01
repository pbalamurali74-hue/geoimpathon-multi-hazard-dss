# Learning Module 05: Indicator Normalization (Min-Max & Fuzzy Membership)

## 1. WHAT it does
Normalization standardizes diverse physical indicators (measured in meters, degrees, millimeters, or reflectance ratios) onto a dimensionless $[0, 1]$ interval. Each indicator is assigned a functional direction (cost or benefit) depending on whether higher values increase or decrease hazard susceptibility. We utilize linear Min-Max normalization as our primary engine and benchmark it against non-linear Fuzzy Sigmoidal Membership for elevation/HAND.

## 2. WHY this method over alternatives
- **Min-Max Normalization vs. Z-Score Standardization:** Z-score produces values centered around zero with unbounded positive and negative ranges (e.g., $[-3.2, +4.1]$). Negative values violate the fundamental axioms of Multi-Criteria Weighted Linear Combination ($\sum w_i x_i$), where weights and scores must remain non-negative. Min-Max strictly bounds attributes to $[0, 1]$.
- **Min-Max with Outlier Clipping vs. Raw Min-Max:** Raw min-max is susceptible to extreme single-pixel outliers (e.g., a transmission tower elevating max DEM to $150 \text{ m}$ in a $20 \text{ m}$ plain), which compresses $99\%$ of the landscape into a narrow $0.0\text{--}0.2$ range. We clip values at the 1st and 99th percentiles before min-max scaling to preserve dynamic contrast.
- **Fuzzy Membership vs. Hard Boolean Slicing:** Binary thresholds classify a road at $1.99 \text{ m}$ elevation as "flooded (1)" and at $2.01 \text{ m}$ as "safe (0)". Fuzzy membership models the continuous transition zone of hydrological uncertainty.

## 3. HOW it works (with worked numeric example)

### Direction Rules:
- **Cost Direction (Direct Risk):** Higher physical value $\implies$ Higher risk $\implies$ Direct scaling:
  $$x_{\text{norm}} = \frac{x - x_{\min}}{x_{\max} - x_{\min}}$$
- **Benefit Direction (Inverse Risk):** Higher physical value $\implies$ Lower risk (e.g., elevation, slope in flood model, vegetation cover) $\implies$ Inverted scaling:
  $$x_{\text{norm}} = \frac{x_{\max} - x}{x_{\max} - x_{\min}} = 1 - \frac{x - x_{\min}}{x_{\max} - x_{\min}}$$

### Indicator Direction Matrix:
| Indicator | Model | Direction | Physical Justification |
| :--- | :--- | :--- | :--- |
| **Elevation** | Flood | Inverse (Benefit) | Water flows downhill under gravity; lower elevations collect water. |
| **Slope** | Flood | Inverse (Benefit) | Flatter slopes have low hydraulic gradient, causing ponding and slow drainage. |
| **HAND** | Flood | Inverse (Benefit) | Lower height above nearest drainage indicates direct riverine overflow vulnerability. |
| **Dist to Water** | Flood | Inverse (Benefit) | Proximity to waterbodies and lakes means shorter flow distance to inundation. |
| **NDVI** | Flood | Inverse (Benefit) | Dense vegetation enhances soil infiltration and surface roughness, delaying runoff. |
| **Impervious / Built** | Flood | Direct (Cost) | Concrete surfaces prevent infiltration, producing high storm runoff coefficients. |
| **CHIRPS Rain** | Flood | Direct (Cost) | Greater extreme precipitation delivers higher hydraulic volume to catchments. |
| **Slope** | Slope-Inst. | Direct (Cost) | Steeper terrain increases gravitational shear stress on soil and embankments. |
| **Curvature** | Slope-Inst. | Direct (Cost) | Concave hollows concentrate subsurface pore water pressure, triggering slides. |
| **Dist to Cut Slopes** | Slope-Inst. | Inverse (Benefit) | Roads cut into hills destabilize the toe of the slope; proximity increases hazard. |

### Fuzzy Sigmoidal Membership Example:
For HAND ($h$ in meters), risk follows a decreasing S-curve (sigmoidal membership):
$$\mu(h) = \frac{1}{1 + e^{\beta (h - h_0)}}$$
Where $h_0 = 3.0 \text{ m}$ (inflection midpoint) and $\beta = 1.2$ (steepness):
- At $h = 1.0 \text{ m}$ (low depression): $\mu(1) = \frac{1}{1 + e^{1.2(1 - 3)}} = \frac{1}{1 + e^{-2.4}} = \frac{1}{1 + 0.0907} \approx 0.917$ (Extreme Risk).
- At $h = 3.0 \text{ m}$ (transition): $\mu(3) = \frac{1}{1 + e^0} = 0.500$ (Moderate Risk).
- At $h = 6.0 \text{ m}$ (high ground): $\mu(6) = \frac{1}{1 + e^{1.2(3)}} = \frac{1}{1 + 36.6} \approx 0.026$ (Negligible Risk).

## 4. Key Parameters and Sensitivity
- Percentile Clamping: Clipping at $[P_1, P_{99}]$ prevents anomalous sensor noise from skewing the denominator $(x_{\max} - x_{\min})$.
- Inversion Check: A single inverted indicator accidentally normalized directly (e.g., treating high elevation as high flood risk) corrupts the entire composite index. Every indicator is unit-tested with assertion checks for proper directionality.

## 5. Common Mistakes and Limitations
1. **Normalizing After Averaging:** You must normalize each raw layer *before* computing weighted linear overlays; otherwise, indicators with larger physical numerical ranges (e.g. rainfall in hundreds of mm vs. slope in single-digit degrees) completely dominate the sum regardless of assigned AHP weights.
2. **Ignoring Study-Area Relativity:** Min-max bounds are relative to the bounding box. A normalized elevation score of $0.8$ means the top 20th percentile in South Chennai (e.g., $35 \text{ m}$ altitude), not $0.8$ relative to the Himalayas. This relativity is clearly communicated to users on the dashboard.

## 6. Likely Judge Questions and Model Answers
- **Q1: Why did you clip at the 1st and 99th percentiles before Min-Max normalization?**
  *Answer:* Satellite rasters frequently contain isolated corrupted pixels, communication dropouts, or artificial terrain spikes (e.g., high-voltage pylons). Clamping to $[P_1, P_{99}]$ establishes robust bounds that prevent a single anomalous outlier from compressing the dynamic variance of the entire landscape.
- **Q2: Why use linear min-max if natural hazard processes are often non-linear?**
  *Answer:* Linear min-max provides complete mathematical transparency and auditability for district disaster managers. However, to evaluate non-linearity, we implemented and benchmarked a sigmoidal fuzzy membership function for HAND, demonstrating high rank concordance ($r_s > 0.93$) while keeping the primary framework straightforward to defend.
- **Q3: What happens if an indicator has zero variance across the study area?**
  *Answer:* If $x_{\max} = x_{\min}$, division by zero occurs. Our normalization function checks for $\Delta x < 10^{-6}$ and returns a uniform zero array with a logged warning.
- **Q4: How do you verify that your normalization directions are correct?**
  *Answer:* We enforce automated unit tests in `tests/test_mcdm.py` that check synthetic test arrays with known physical orientations (e.g., asserting that elevation $= 0 \text{ m}$ receives risk $= 1.0$ and elevation $= 50 \text{ m}$ receives risk $= 0.0$).
- **Q5: Can you mix benefit and cost indicators in the same AHP matrix?**
  *Answer:* Yes, provided all indicators are properly pre-standardized such that a value of $1.0$ consistently denotes maximum hazard susceptibility across all layers before entering the weighted linear combination.
