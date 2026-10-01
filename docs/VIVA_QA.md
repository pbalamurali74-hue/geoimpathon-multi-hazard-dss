# GEOIMPATHON 1.0 - Viva Defense & Jury Q&A Guide (30 Questions)

This document equips the student presentation team with rigorous, technically defended answers to the 30 most critical and challenging questions judges are likely to ask during the defense.

---

### Section 1: Problem Statement, Mission & Context

#### Q1: What is the core mission and narrative of your project?
**Answer:** "In a catastrophic flood, following the shortest route to a hospital can be the deadliest mistake an ambulance driver makes. Standard navigation models optimize purely for distance or speed, routinely funneling emergency vehicles into submerged underpasses and canal margins. Our system finds the least-risk route, names the vital road corridors whose severance isolates the most people, recommends optimal pre-positioning sites for rescue assets, and measures how much regional hospital access collapses under extreme cyclonic stress."

#### Q2: Why did you choose the South Chennai to Chengalpattu corridor as your study area?
**Answer:** This 20 km x 20 km corridor (Tambaram, Pallikaranai, Velachery, Kattankulathur) represents one of India's most vulnerable peri-urban growth axes. It features rapid concrete development, critical national transport arteries (GST Road, Chennai Bypass, OMR connector), and highly sensitive hydrological systems (Pallikaranai marshland and Adyar river headwaters) that suffered severe inundation during Cyclone Michaung in December 2023.

#### Q3: Why is the secondary hazard labeled "slope-instability and erosion susceptibility" rather than "landslide hazard"?
**Answer:** We prioritize scientific honesty. South Chennai is predominantly a low-relief coastal plain; calling the hazard a "mountainous landslide" would be inaccurate and easily discredited by geologists. However, the study area contains localized hillocks (St. Thomas Mount, Trisulam, Vandalur), deep granite quarry faces, highway flyover embankments, and major lake bunds (Chembarambakkam, Madambakkam) which suffer chronic slope failure, scouring, and bank erosion during extreme monsoonal downpours.

---

### Section 2: Satellite Data & Remote Sensing

#### Q4: Why Sentinel-1 SAR over optical Sentinel-2 imagery for flood mapping?
**Answer:** Tropical cyclones like Michaung bring 100% thick cloud cover and continuous rainfall. Optical sensors (Sentinel-2, Landsat) cannot penetrate cloud decks during the peak disaster event. Sentinel-1 operates at C-band microwave frequencies ($5.405 \text{ GHz}$, wavelength $\sim 5.6 \text{ cm}$), penetrating clouds, rain, and darkness to provide cloud-free surface backscatter measurements.

#### Q5: What is the physical principle behind radar flood detection?
**Answer:** Rough soil, vegetation, and urban surfaces produce diffuse scattering, reflecting microwave energy in all directions, including back to the sensor ($\sigma^0 \approx -11 \text{ dB}$). Smooth open standing water acts as a specular mirror, reflecting incoming radar pulses away from the satellite antenna. Consequently, floodwaters appear as stark, low-backscatter black surfaces ($\sigma^0 \le -16 \text{ dB}$).

#### Q6: Why did you use log-ratio change detection instead of single-image thresholding?
**Answer:** A single post-disaster image cannot distinguish between floodwater, permanent lakes, airport runways, or calm asphalt expressways, as all exhibit specular reflection. Log-ratio subtraction ($\Delta \sigma^0 = \sigma^0_{\text{post}} - \sigma^0_{\text{pre}}$) cancels out permanent flat features and isolates temporal decreases in backscatter caused by new inundation.

#### Q7: What are the primary physical limitations of SAR in urban flood detection?
**Answer:** Radar suffers from **double-bounce scattering** and **shadowing** in dense built-up environments. In narrow city streets with tall concrete buildings, radar pulses bounce from the road to the vertical building facade and back to the sensor (corner reflector), producing intense bright backscatter even if the street is flooded under 1 meter of water. SAR under-detects street-level flooding in narrow urban canyons.

#### Q8: Why did you choose Copernicus GLO-30 DEM over SRTM or NASADEM?
**Answer:** Copernicus DEM (derived from 2011–2015 TanDEM-X radar interferometry) has a documented vertical accuracy superior to legacy SRTM (acquired in 2000). In low-gradient coastal plains where 1 meter of vertical variation dictates flood inundation, SRTM exhibits significant vegetation canopy bias and elevation stripe errors that Copernicus GLO-30 eliminates.

#### Q9: What is HAND (Height Above Nearest Drainage) and why is it superior to raw elevation?
**Answer:** Absolute elevation is relative to mean sea level; it cannot differentiate an elevated coastal plateau from an inland river terrace. HAND models hydrologic flow paths across the DEM and computes the vertical elevation of each cell relative to its nearest downslope drainage stream. It isolates true gravitational flood accumulation potential from regional topographic trends.

---

### Section 3: Exposure, Land Cover & Ethics

#### Q10: Why do you term your exposure layer "built-up exposure (population proxy)" rather than "population"?
**Answer:** To maintain ethical and methodological rigor. Problem rules prohibit unverified external census disaggregations. Dynamic World provides 10-meter per-pixel probabilities of physical built structures from Sentinel-2. A commercial warehouse has high built-up density but zero nighttime population, while a residential apartment has high human density. Clarifying that it is a physical built-up infrastructure proxy avoids false claims of demographic certainty.

#### Q11: Why did you construct a 22-month pre-event composite for Dynamic World?
**Answer:** Single optical acquisitions are subject to seasonal sun glint, agricultural crop harvesting, and cloud shadows. Taking the pixel-wise median across 22 months of Sentinel-2 overpasses (January 2022 to October 2023) filters out seasonal transient noise and provides a clean, pre-disaster baseline of impervious urban footprint.

---

### Section 4: Multi-Criteria Decision Making (MCDM) & AHP

#### Q12: How did you compute weights for your flood susceptibility indicators?
**Answer:** Using Saaty's Analytic Hierarchy Process (AHP). We constructed a reciprocal $7 \times 7$ pairwise comparison matrix based on peer-reviewed hydrological literature, computed the principal eigenvector, and normalized it to derive criterion weights: HAND (34.6%), Slope (23.1%), Built-Up (14.7%), Distance to Water (9.7%), Elevation (8.9%), NDVI (5.3%), and Rainfall (3.7%).

#### Q13: What is the Consistency Ratio (CR) and what value did your matrices achieve?
**Answer:** The Consistency Ratio measures transitivity in pairwise judgments: $\text{CR} = \text{CI} / \text{RI}_n$. A matrix is scientifically acceptable only if $\text{CR} < 0.10$. Our Flood AHP matrix achieved $\text{CR} = 0.0217$, and our Slope-Instability matrix achieved $\text{CR} = 0.0224$. Both easily pass the threshold.

#### Q14: Why is CHIRPS rainfall given the lowest weight in both AHP matrices?
**Answer:** Because our study area is 20 km x 20 km, while CHIRPS has a spatial resolution of 0.05° (~5 km). Across the entire bounding box, CHIRPS contains only about 16 pixels, exhibiting virtually no spatial variance. Over-weighting it would add an artificial constant numerical bias across the area rather than discriminating between low-lying flood-prone wards and elevated safe zones.

#### Q15: How does your system combine Flood and Slope-Instability into Multi-Hazard Risk?
**Answer:** Via a weighted linear combination: $R_{\text{multi}} = 0.70 H_{\text{flood}} + 0.30 H_{\text{slope}}$. The 70/30 split reflects the geographic reality of coastal South Chennai, where tropical storm floods represent the vast majority of historical disaster damage, while preserving slope failure sensitivity around quarries, flyovers, and lake bunds.

#### Q16: Why did you use percentile breaks for risk classification instead of equal intervals?
**Answer:** Equal intervals ($0\text{--}0.25, 0.25\text{--}0.50, \dots$) fail when environmental data clusters in a specific range, leaving categories empty. Percentile breaks (<50th, 50-80th, 80-95th, >95th) guarantee operational utility: the top 5% highest-risk terrain is consistently designated "Very High", providing emergency managers with a clear, actionable prioritization tier.

---

### Section 5: Normalization & Objective Cross-Checks

#### Q17: Why did you clip rasters at the 1st and 99th percentiles before Min-Max normalization?
**Answer:** Satellite sensors occasionally produce single-pixel anomalies (e.g. cloud shadows, sensor dropouts, transmission towers). Normalizing against absolute minimum and maximum values would allow a single rogue pixel to compress 99% of the real landscape into a tiny, un-differentiated numerical band. Clamping to $[P_1, P_{99}]$ preserves dynamic contrast.

#### Q18: What is the Entropy Weight Method (EWM) and why did you use it?
**Answer:** EWM is an objective weighting method based on Shannon Information Entropy. It calculates criterion weights strictly from empirical data dispersion. We use it as an independent mathematical cross-check against our subjective AHP weights to prove that our chosen weights do not distort data distributions.

#### Q19: What was the Spearman correlation between your AHP and Entropy risk maps?
**Answer:** The Spearman rank correlation coefficient between the AHP-weighted risk raster and the Entropy-weighted risk raster is $r_s \approx 0.84$ ($p < 0.001$). This strong positive correlation demonstrates high ordinal consistency between expert hydrologic knowledge and empirical data variance.

---

### Section 6: Validation & The No-Leakage Rule

#### Q20: What is the 'No-Validation-Leakage' principle and how did you enforce it?
**Answer:** The Sentinel-1 SAR flood extent map of Cyclone Michaung is strictly excluded from all hazard layers, normalization steps, and AHP weight formulations. It is used exclusively as an independent, out-of-sample ground truth layer for post-hoc ROC/AUC validation. Feeding validation event observations into the susceptibility model would constitute circular reasoning and fraudulent validation.

#### Q21: What ROC AUC score did your flood model achieve, and how was it tested?
**Answer:** Our flood susceptibility model achieved an ROC AUC of $0.884$. It was evaluated using balanced 1:1 random sampling (5,000 flooded and 5,000 dry pixels), with permanent waterbodies (JRC Occurrence $>80\%$) strictly excluded. At the High-Risk threshold, the model achieved a Precision of $83.2\%$, Recall of $84.0\%$, and an F1-score of $0.836$.

#### Q22: Why did you perform spatial block cross-validation?
**Answer:** Standard random pixel sampling ignores spatial autocorrelation (Tobler's First Law): neighboring pixels share identical environmental conditions, leading to artificially inflated accuracy scores. By partitioning the study area into contiguous spatial blocks and testing on held-out blocks, we prove genuine spatial generalizability.

---

### Section 7: Emergency Routing & Network Graph

#### Q23: How do you sample continuous raster risk onto discrete road network edges?
**Answer:** We sample points every 30 meters along each road polyline from OpenStreetMap. For each edge, we calculate the mean risk ($\bar{R}_e$) and peak risk ($R_{\max, e}$), combining them as $R_{\text{edge}} = 0.5 \bar{R}_e + 0.5 R_{\max, e}$. This ensures that even if a 2 km road is mostly dry, a single localized deep depression in an underpass will properly elevate the entire link's risk.

#### Q24: What is the mathematical formulation of your edge-cost function?
**Answer:** $C_e = L_e \cdot (1 + \alpha \cdot R_{\text{edge}})$, where $L_e$ is physical edge length, $R_{\text{edge}} \in [0, 1]$ is multi-hazard risk, and $\alpha \ge 0$ is the interactive safety slider. When $\alpha = 0$, cost equals length (fastest route); as $\alpha$ increases, paths systematically detour around flood-prone segments.

#### Q25: Why do you add specific risk bumps to tunnels and low bridges?
**Answer:** Road tunnels and depressed underpasses (OSM `tunnel=*`, `layer < 0`) are notorious urban drowning traps during monsoons where floodwaters accumulate rapidly (+0.15 risk bump). Low bridges over natural drainage channels suffer from hydrodynamic overtopping and pier scouring (+0.08 risk bump).

---

### Section 8: Road Criticality & Isolation Analysis

#### Q26: How does your Road Criticality Index identify single points of failure?
**Answer:** First, we route every settlement to its nearest safe hospital, accumulating traversing built-up exposure on each edge and weighting by edge risk to screen the top 30 candidates. Then, we simulate physical edge deletion (Removal Impact) for each candidate. An edge's criticality is defined by the exact built-up exposure that becomes isolated from all safe hospitals and the total added detour delay if that link is severed.

#### Q27: How does your system define and handle "Safe" vs. "Unsafe" hospitals?
**Answer:** Any hospital or shelter located within a High or Very High multi-hazard risk zone ($\ge 80\text{th percentile}$) is flagged as "Unsafe" (compromised access, submerged ground floors, power failure risk) and excluded from emergency destination routing. The system directs patients only to facilities on dry, operational ground.

---

### Section 9: Pre-positioning & Golden-Hour Access

#### Q28: How does the greedy maximum-coverage pre-positioning algorithm work?
**Answer:** It selects $K = 5$ strategic staging sites for rescue boats, high-clearance ambulances, and relief supplies. Candidate locations are constrained to be outside High-risk zones and situated on accessible roads. The greedy algorithm iteratively picks sites that maximize coverage of isolated and severely delayed settlements, ranked by affected built-up exposure.

#### Q29: What is the Golden-Hour Access Score and what did your analysis reveal?
**Answer:** The Golden-Hour Access Score measures the percentage of regional built-up exposure that can reach an operational safe hospital within 60 minutes. Under normal conditions, coverage is $94.2\%$. Under the Cyclone Michaung flood scenario (blocked high-risk roads severed, flooded roads slowed to $5 \text{ km/h}$), access collapses to $58.1\%$, representing a catastrophic $36.1\%$ collapse in emergency medical reachability.

---

### Section 10: Robustness & Practical Utility

#### Q30: How did you prove the mathematical stability of your system using Monte Carlo simulation?
**Answer:** We executed 200 stochastic Monte Carlo trials, perturbing AHP weights and the hazard split by $\pm 20\%$ multiplicative noise and re-checking consistency. Across 200 trials, the safest evacuation route remained 100% identical in over $91\%$ of runs, and the Top-10 critical roads showed an average Jaccard overlap of $88.4\%$. This proves to disaster management officials that our recommendations are structurally sound and not artifacts of subjective tuning.
