# Learning Module 02: DEM Derivatives (Slope, Curvature, HAND Proxy)

## 1. WHAT it does
Digital Elevation Model (DEM) derivatives translate raw terrain elevation into localized hydraulic and geomorphic metrics: slope gradient (in degrees), surface profile curvature (convexity/concavity), and a Height Above Nearest Drainage (HAND) proxy. These layers quantify where gravity drives water accumulation, where runoff decelerates, and where terrain inclination creates slope instability risks.

## 2. WHY this method over alternatives
- **Copernicus GLO-30 vs. SRTM-30 / NASADEM:** SRTM (acquired in 2000) suffers from severe vertical bias in low-relief coastal floodplains (mean errors $>3 \text{ m}$) and contains canopy height artifacts over urban areas. Copernicus GLO-30 (derived from 2011–2015 TanDEM-X interferometry) provides superior relative vertical accuracy ($<2 \text{ m}$) and void-free surface modeling across coastal Tamil Nadu.
- **HAND Proxy vs. Absolute Elevation:** Absolute elevation is misleading across regional gradients. A point at $25 \text{ m}$ elevation adjacent to a local stream can flood completely, while a point at $15 \text{ m}$ perched on a coastal bluff never floods. HAND normalizes elevation relative to the hydrologic flow line, directly isolating inundation height above drainage.
- **Planform/Profile Curvature vs. Raw Elevation:** Raw elevation does not distinguish between ridge tops and valley bottoms of identical altitude. Curvature computes the second spatial derivative of elevation, identifying concave flow-convergence channels (hollows) where runoff concentrates.

## 3. HOW it works (with worked numeric example)
Given a $3 \times 3$ grid of elevation values centered at cell $e_5$ with spatial resolution $\Delta x = \Delta y = 30 \text{ m}$:
$$
\begin{bmatrix}
e_1 & e_2 & e_3 \\
e_4 & e_5 & e_6 \\
e_7 & e_8 & e_9
\end{bmatrix}
=
\begin{bmatrix}
14.2 & 14.0 & 13.8 \\
13.9 & 13.5 & 13.1 \\
13.6 & 13.0 & 12.4
\end{bmatrix} \text{ (meters)}
$$

### Step 1: Horn's Method for Slope Gradient
Calculate the rate of change in east-west ($p = \frac{\partial z}{\partial x}$) and north-south ($q = \frac{\partial z}{\partial y}$) directions:
$$p = \frac{(e_3 + 2e_6 + e_9) - (e_1 + 2e_4 + e_7)}{8 \Delta x} = \frac{(13.8 + 26.2 + 12.4) - (14.2 + 27.8 + 13.6)}{8 \times 30} = \frac{52.4 - 55.6}{240} = -0.0133$$
$$q = \frac{(e_7 + 2e_8 + e_9) - (e_1 + 2e_2 + e_3)}{8 \Delta y} = \frac{(13.6 + 26.0 + 12.4) - (14.2 + 28.0 + 13.8)}{240} = \frac{52.0 - 56.0}{240} = -0.0167$$

Slope in radians:
$$\theta = \arctan\left(\sqrt{p^2 + q^2}\right) = \arctan\left(\sqrt{(-0.0133)^2 + (-0.0167)^2}\right) = \arctan(0.0213) \approx 0.0213 \text{ rad}$$
Slope in degrees:
$$\text{Slope}^\circ = 0.0213 \times \frac{180}{\pi} \approx 1.22^\circ$$
*(Flatter than $2^\circ \implies$ extreme flood ponding potential; very low slope instability)*.

### Step 2: HAND Proxy Calculation
A local drainage line has water surface elevation $z_{\text{drain}} = 11.2 \text{ m}$.
For center cell $e_5 = 13.5 \text{ m}$:
$$\text{HAND} = z(e_5) - z_{\text{drain}} = 13.5 - 11.2 = 2.3 \text{ m}$$
A relative height of $2.3 \text{ m}$ indicates high vulnerability to seasonal storm surge and riverine overflow.

## 4. Key Parameters and Sensitivity
- `resolution_m` (Default: $30 \text{ m}$): Computing slope on $30 \text{ m}$ cells smooths micro-ditches and road embankments, avoiding micro-scale numerical noise while retaining regional topographic depressions.
- Direction of Normalization:
  - For Flood Hazard: Flat terrain is riskiest $\implies \text{Slope}$ is inverted ($1 - \text{norm}(\text{slope})$).
  - For Slope Instability: Steep terrain is riskiest $\implies \text{Slope}$ is direct ($\text{norm}(\text{slope})$).

## 5. Common Mistakes and Limitations
1. **Confusing DSM with DTM:** Spaceborne DEMs (like Copernicus GLO-30 and SRTM) are Digital Surface Models (DSMs) that measure the top of tree canopies and building roofs rather than bare ground. In dense urban Tambaram, building heights artificially elevate the DEM by $5\text{--}15 \text{ m}$. We use focal filtering and land-cover conditioning to mitigate canopy spikes.
2. **Geographic vs. Projected Coordinate Systems:** Calculating slope directly on unprojected lat/lon coordinates in degrees produces nonsensical slope angles because 1 degree of latitude $\approx 111 \text{ km}$ while 1 degree of elevation is in meters. Elevation derivatives must be calculated in metric coordinates (e.g. UTM Zone 44N, EPSG:32644) or using geodetic metric factor correction ($111,320 \cos(\text{lat})$).

## 6. Likely Judge Questions and Model Answers
- **Q1: Why is slope presented as its own standalone layer in the application?**
  *Answer:* Slope (in degrees) is an unambiguous physical baseline required by municipal engineers to plan emergency vehicle deployment. High-clearance rescue trucks cannot traverse steep embankments or bund cut-slopes, while shallow slopes identify zones prone to long-duration standing sheet flow.
- **Q2: How does HAND differ from simple elevation?**
  *Answer:* Simple elevation is absolute height above sea level. HAND is height above the nearest connected hydrological drainage stream along flow paths. It isolates hydraulic gravity potential from regional inland elevation gradients.
- **Q3: What causes slope instability in an otherwise flat Chennai study area?**
  *Answer:* Chennai is largely a low-lying coastal plain, but our study area encompasses the St. Thomas Mount hills, Trisulam granite quarries, Vandalur hillocks, highway flyover embankments, and lake bunds (e.g. Chembarambakkam and Madambakkam bunds), which undergo localized structural scouring and slope collapse during extreme rainfall.
- **Q4: How did you compute curvature?**
  *Answer:* We compute profile curvature by taking the second directional derivative along the maximum slope gradient vector. Negative values indicate concave flow-trapping hollows; positive values indicate convex shedding mounds.
- **Q5: Can you explain why SRTM was rejected?**
  *Answer:* SRTM was acquired via C-band radar in February 2000. It has known vertical offsets of 3-5 meters in South Indian coastal lowlands and contains substantial stripe noise and vegetation canopy bias compared to Copernicus 2015-era TanDEM-X radar interferometry.
