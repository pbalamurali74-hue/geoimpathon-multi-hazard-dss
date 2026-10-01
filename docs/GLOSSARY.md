# GEOIMPATHON 1.0 - Geospatial & Multi-Hazard Decision Support Glossary

This glossary provides exact, technical definitions for all geospatial, remote sensing, graph theory, and multi-criteria decision-making terms used throughout the project.

---

### A
- **AHP (Analytic Hierarchy Process):** A structured technique developed by Thomas Saaty for organizing and analyzing complex multi-criteria decisions. It decomposes decision problems into a hierarchy of sub-problems and utilizes pairwise comparison matrices to derive mathematically consistent ratio-scale priorities.
- **Alpha ($\alpha$) Parameter:** In our emergency routing model, $\alpha$ is the safety priority tuning parameter within the edge cost formulation $C = L \cdot (1 + \alpha \cdot R)$. When $\alpha = 0$, routing optimizes strictly for shortest physical distance / free-flow time; as $\alpha$ increases, paths systematically detour around flood-prone segments.
- **AUC (Area Under the Curve):** The definite integral of the Receiver Operating Characteristic (ROC) curve across all classification thresholds, ranging from $0.5$ (random chance) to $1.0$ (perfect discrimination). Represents the probability that a randomly chosen flooded pixel has a higher modeled susceptibility score than a randomly chosen dry pixel.

### B
- **Backscatter ($\sigma^0$ or Sigma Nought):** The fraction of transmitted radar signal reflected back to the synthetic aperture radar (SAR) antenna from a unit area of target surface, conventionally expressed in decibels (dB). Smooth open water causes specular reflection away from the sensor, leading to characteristically low backscatter ($\le -16 \text{ dB}$).
- **Betweenness Centrality:** A measure of node or edge centrality in a network graph based on the fraction of all shortest paths between all pairs of nodes that traverse that node or edge.
- **Block Threshold:** The hazard risk percentile cutoff (set at the 95th percentile / lower bound of the "Very High" risk band) above which road segments are deemed impassable and severed from the emergency response graph.

### C
- **Change Detection (SAR Log-Ratio):** Subtraction of calibrated backscatter images in decibel space ($\Delta \sigma^0_{\text{dB}} = \sigma^0_{\text{post}} - \sigma^0_{\text{pre}}$). A substantial decrease ($\le -3 \text{ dB}$) indicates a transition from rough dry ground to specular flood inundation.
- **CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data):** A quasi-global rainfall dataset (0.05° resolution) spanning 1981 to present, combining satellite thermal infrared cold-cloud-duration observations with in-situ rain gauge measurements.
- **Consistency Index (CI) & Consistency Ratio (CR):** Metrics within AHP measuring the internal transitivity of pairwise comparison matrices. $\text{CI} = (\lambda_{\max} - n)/(n - 1)$; $\text{CR} = \text{CI} / \text{RI}$, where $\text{RI}$ is the random index for matrix order $n$. A matrix is valid only if $\text{CR} < 0.10$.
- **Copernicus DEM (GLO-30):** A global 30-meter Digital Surface Model derived from the German radar satellite mission TanDEM-X, offering superior vertical accuracy in coastal plains compared to legacy SRTM.

### D
- **Dijkstra's Algorithm:** A classic graph search algorithm that solves the single-source shortest path problem for graphs with non-negative edge weights, utilized here with risk-augmented edge costs.
- **Dynamic World:** A near-real-time 10-meter resolution global land use and land cover (LULC) dataset produced via deep learning applied to Sentinel-2 L2A optical imagery by Google and the World Resources Institute.

### E
- **Entropy Weight Method:** An objective weighting method rooted in Shannon information theory. It calculates criterion weights based on the degree of dispersion in indicator values across geographic evaluation units. Higher variability yields lower entropy and higher weight.
- **Exposure (Built-Up Proxy):** In our system, exposure is strictly defined as the spatial extent and density of impervious/built-up land cover from Dynamic World, representing human settlement infrastructure without relying on unverified census disaggregations.

### F
- **Focal Median Filter:** A non-linear spatial image processing operator that computes the statistical median of pixel values within a moving kernel (e.g. $3 \times 3$ or $5 \times 5$), effective at filtering high-frequency granular SAR speckle without blurring sharp hydraulic boundaries.
- **Fuzzy Membership:** A normalization approach where crisp physical values are mapped to a continuous degree of membership in the set $[0, 1]$ using sigmoidal or linear transfer functions, capturing gradational transition zones in natural hazards.

### G
- **Golden-Hour Access Score:** The proportion of total regional built-up exposure that can reach an operational, safe hospital within 60 minutes of travel time under emergency scenario network conditions.

### H
- **HAND (Height Above Nearest Drainage):** A hydrologically conditioned terrain model normalized relative to the local drainage network along flow paths, isolating low-lying flood inundation potential from absolute regional elevation.

### J
- **JRC Global Surface Water (GSW):** The European Commission Joint Research Centre dataset derived from 38+ years of Landsat archives mapping global surface water presence, recurrence, and seasonality.

### M
- **MCDM / MCDA (Multi-Criteria Decision Making / Analysis):** An operational research sub-discipline concerned with evaluating multiple conflicting criteria in decision problems (e.g., AHP, weighted linear combination).
- **Monte Carlo Sensitivity Analysis:** Computational technique relying on repeated random sampling (200 stochastic trials) to propagate parameter uncertainty (AHP weights perturbed by $\pm 20\%$) through the spatial model.

### N
- **NDVI (Normalized Difference Vegetation Index):** Standard optical index computed as $(\text{NIR} - \text{Red}) / (\text{NIR} + \text{Red})$ indicating photosynthetic activity and surface biomass, used to assess infiltration capacity and soil stability.
- **No-Validation-Leakage Principle:** Strict methodological barrier ensuring that the Sentinel-1 SAR flood extent map of the Cyclone Michaung validation event is excluded entirely from the hazard susceptibility index generation, serving solely as post-hoc ground-truth.

### O
- **OSMnx:** A Python spatial network library that retrieves, models, analyzes, and visualizes complex street networks from OpenStreetMap as topologically clean NetworkX graphs.

### R
- **Removal Impact Criticality:** The systematic simulation of individual road link severance to quantify the resulting newly isolated built-up exposure and additional network-wide detour delay.
- **ROC (Receiver Operating Characteristic) Curve:** A graphical curve plotting True Positive Rate (Sensitivity) against False Positive Rate ($1 - \text{Specificity}$) across continuous decision thresholds.

### S
- **Sentinel-1 SAR:** The European Space Agency Copernicus constellation carrying C-band Synthetic Aperture Radar in Interferometric Wide (IW) swath mode with dual polarization (VV + VH).
- **Spatial Block Cross-Validation:** A model validation partitioning strategy where test and training subsets are spatially separated into contiguous geographic blocks to eliminate artificial performance inflation caused by spatial autocorrelation.
- **Specular Reflection:** The mirror-like reflection of electromagnetic waves from a smooth surface (such as floodwater) where angle of incidence equals angle of reflection, causing virtually zero backscatter to return to the active radar sensor.
