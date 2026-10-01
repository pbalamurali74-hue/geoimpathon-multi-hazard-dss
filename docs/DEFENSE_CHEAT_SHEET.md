# GEOIMPATHON 1.0 — Jury Defense Cheat-Sheet: Top 10 Hardest Questions & Winning Answers

This guide prepares the team to defend every technical, mathematical, and design decision before competition judges.

---

### Q1: "Your study area is in Chennai, which is largely flat. Why do you have a 'slope-instability' hazard layer at all? Isn't that misleading?"
**Winning Answer:**
> "That is an astute observation, and we address it plainly in our documentation: **we do not oversell slope instability.** 
> Because South Chennai is predominantly a low-relief coastal plain ($0\text{--}1.2^\circ$), FLOOD is the overwhelming primary hazard ($70\%$ weight). 
> However, the corridor contains active stone quarries, granitic inselbergs like the Vandalur and Trisulam hills, elevated railway and highway embankments, and major lake retention bunds (e.g. Chembarambakkam and Madambakkam). During extreme 500 mm cyclonic rain events, saturated soil and scouring cause embankment slumping, quarry rockfalls, and bund breaches that sever adjacent roads. 
> We label this layer accurately as *'slope-instability and erosion susceptibility'* and perform a geomorphic sanity check verifying physical slope scaling ($r_s = 0.860, p < 10^{-15}$). We explicitly tell judges this is a geomorphic sanity check, not an empirical landslide validation."

---

### Q2: "Did you use the Sentinel-1 Michaung event flood map to calibrate your hazard weights? Isn't there data leakage?"
**Winning Answer:**
> "Absolutely not. We strictly enforced the **No-Validation-Leakage Principle**.
> Our flood susceptibility model is built entirely on intrinsic, pre-disaster landscape attributes: Copernicus DEM elevation and HAND, Dynamic World pre-event land cover composites (2022–2023), pre-event Sentinel-2 NDVI, and historical 20-year CHIRPS climatology up to 2022.
> The Sentinel-1 SAR change detection of Cyclone Michaung (Dec 2023) was **strictly withheld from model construction and weights**. It serves purely as an independent, post-hoc out-of-sample ground truth test. Unit test `test_no_validation_leakage` programmatically enforces that the event flood raster never appears in hazard modeling code."

---

### Q3: "Your flood validation ROC AUC is 0.707. Why isn't it 0.95 like some machine learning papers claim?"
**Winning Answer:**
> "There are three crucial scientific reasons why our 0.707 AUC is honest and realistic, whereas 0.95 scores in disaster literature are almost always artifacts of methodological errors:
> 1. **Zero Data Leakage:** High AUC papers frequently train machine learning models on the event flood itself or use post-flood optical indices, creating circular data leakage.
> 2. **Masking Permanent Water:** Many papers include permanent lakes, rivers, and the ocean in their test samples, generating millions of trivial True Positives. We masked out all water bodies with $>80\%$ 38-year JRC occurrence. Our model is tested exclusively on dry terrestrial floodplains that newly inundated.
> 3. **Spatial Autocorrelation (Tobler's First Law):** Random pixel splitting allows neighboring pixels into train and test sets, inflating AUC by 0.10. When evaluated with our Spatial Block Cross-Validation across 16 geographic blocks, our model maintains a consistent $0.686 \pm 0.037$ AUC, proving genuine spatial generalizability."

---

### Q4: "Why did you use AHP instead of training a Random Forest or XGBoost model?"
**Winning Answer:**
> "In disaster risk management, machine learning models face a fatal flaw: **absence of complete negative ground truth**. An area that did not flood in December 2023 might flood in a 100-year storm with a different storm track. Training a supervised classifier on a single event overfits to that storm's specific rainfall epicenter.
> Multi-Criteria Decision Analysis (MCDM/AHP) models the physical physics of runoff (drainage height, slope, infiltration, imperviousness) independently of storm idiosyncrasies. Furthermore, AHP is 100% transparent and explainable to municipal engineers, whereas black-box neural networks cannot be audited during emergency operations. Finally, we cross-checked AHP against objective Shannon Information Entropy, achieving a strong $0.751$ correlation."

---

### Q5: "Why did you use Dynamic World built-up probability as a population proxy instead of WorldPop or GHSL?"
**Winning Answer:**
> "Per the competition rules, **only Google Earth Engine and OpenStreetMap data are permitted**; external population downloads like WorldPop, LandScan, or GHSL are prohibited.
> Furthermore, WorldPop models rely heavily on census disaggregation that is outdated (India's last census was 2011). In contrast, Sentinel-2 Dynamic World provides 10-meter near-real-time deep learning classification of physical built-up structures updated continuously. Physical building footprint is the most accurate spatial proxy for where human beings live, work, and require emergency rescue. We call it plainly: *'built-up exposure (population proxy)'*, never claiming it is an exact census headcount."

---

### Q6: "Why does your routing model not use live traffic APIs (Google Maps, TomTom)?"
**Winning Answer:**
> "During a catastrophic cyclone, commercial traffic APIs fail catastrophically for three reasons:
> 1. **Cell Tower Blackouts:** Cyclone Michaung knocked out cellular towers across South Chennai, leaving ambulances without mobile internet connectivity. Our routing engine runs 100% offline from cached OpenStreetMap NetworkX graphs.
> 2. **Missing Inundation Data:** Google Maps detects vehicle slowdowns from cell phone probe speeds. If a road is completely submerged and empty of cars, Google Maps reports it as 'green / free-flowing' because there are no delayed phones—leading ambulances directly into lethal drowning traps.
> 3. **Closed Graph API Restrictions:** Commercial APIs do not allow disaster managers to dynamically sever road edges, simulate bridge washouts, or apply non-Euclidean safety penalties $C = L(1 + \alpha R)$."

---

### Q7: "Why didn't you just use standard Betweenness Centrality to find critical roads?"
**Winning Answer:**
> "Betweenness centrality is purely topological: it assumes every intersection in the city generates equal traffic demand and every node is an equally important destination.
> In disaster triage, demand originates specifically from inhabited settlements and flows exclusively toward operational, non-inundated hospitals. A back alley that connects two loops receives a high betweenness score despite serving zero residents.
> Our two-stage **Removal Impact Algorithm** screens candidate edges by actual traversing settlement exposure, then physically severs the edge in $G \setminus \{e^*\}$ to measure the true consequence: how many human beings are newly isolated, and how many extra minutes of medical delay are added."

---

### Q8: "How did you define an 'isolated settlement', and what if a settlement is surrounded by water?"
**Winning Answer:**
> "A settlement is strictly classified as **Isolated** if, in the flood-scenario graph $G_{\text{flood}}$ (where roads with risk $\ge 0.5983$ [95th percentile] are severed), there is no passable path to ANY safe, operational hospital.
> In our study area, 24 settlements (including Madipakkam and Puzhuthivakkam in the Pallikaranai marsh basin) become completely isolated. 
> In individual trip routing, if an origin settlement is severed in $G_{\text{flood}}$, our router executes an **automatic safe fallback**: it finds the lowest-risk route on the full network and displays an explicit operational warning: *'No completely safe route found. Showing the lowest-risk option instead.'*"

---

### Q9: "How do you know your 0.70 Flood / 0.30 Slope split didn't arbitrarily skew the results?"
**Winning Answer:**
> "We addressed this through our **200-run Monte Carlo Robustness Engine**. 
> We simultaneously perturbed all indicator AHP weights by $\pm 20\%$ multiplicative noise and varied the multi-hazard split across the range $[0.60, 0.80]$.
> Across all 200 stochastic trials:
> - Primary emergency hospital routes achieved **100.0% stability** ($\text{Jaccard} = 1.000$).
> - The Top-10 Single Points of Failure achieved an average **92.5% persistence**.
> This proves that our emergency routes and bottleneck discoveries are governed by the physical topography of Chennai and the street network layout, rather than subjective weight nuances."

---

### Q10: "If the District Collector asks: 'What three concrete actions should we take tomorrow morning based on your system?', what do you tell them?"
**Winning Answer:**
> "We hand the Collector three immediate, actionable deliverables exported directly from our system:
> 1. **Immediate Barricading & Culvert Reinforcement:** Pre-deploy police teams and sandbags to our **Top 10 Single Points of Failure**—specifically the Mount-Medavakkam Road causeway and Ponniamman Koil Street—before cyclonic rains peak.
> 2. **Pre-Position Relief Assets at our 5 Recommended Hubs:** Stage 4 Inflatable Rescue Boats and high-water tractors at Pathala Vigneshvarar Temple to cover the 24 marsh communities, and stage high-clearance 4x4 ambulances at Rama Anjaneya Koil to secure the GST Road corridor.
> 3. **Hospital Surge & Diversion Protocol:** Divert emergency patient intake away from the 142 healthcare facilities in High-risk flood zones and alert secondary hospitals in Tambaram and Chromepet that they will face a **22.6% Golden-Hour access surge** from neighboring isolated wards."
