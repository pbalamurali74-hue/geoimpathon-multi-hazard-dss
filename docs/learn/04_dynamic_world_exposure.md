# Learning Module 04: Dynamic World Land Cover & Built-Up Exposure

## 1. WHAT it does
Dynamic World is a 10-meter near-real-time global land use and land cover (LULC) product derived from deep learning on Sentinel-2 optical imagery. We construct a multi-temporal pre-event composite (January 2022 to October 2023) to compute the per-pixel probability of built-up/impervious surfaces, water, and bare ground. The built-up probability serves dual roles: as an impervious surface indicator that amplifies flood runoff, and as the official "built-up exposure (population proxy)" metric to quantify human risk and road criticality.

## 2. WHY this method over alternatives
- **Dynamic World vs. WorldPop / GHSL:** Hackathon problem rules strictly restrict data to Earth Engine and OpenStreetMap, prohibiting external population grids. WorldPop disaggregates decennial census data using statistical models that often suffer from spatial allocation errors in rapidly growing peri-urban corridors like Tambaram-Kattankulathur. Dynamic World directly reflects verified 10 m physical structures and impervious surfaces visible from Sentinel-2.
- **Dynamic World vs. ESA WorldCover (Static 2020/2021):** ESA WorldCover produces a single categorical classification from 2020 or 2021. South Chennai underwent rapid urbanization between 2020 and 2023. Dynamic World captures new developments up to October 2023 and provides continuous per-pixel class probabilities rather than coarse hard-boundary labels.
- **Multi-Temporal Composite vs. Single-Date Optical Image:** Single-date cloud-free optical scenes are subject to seasonal crop cycles, sun-glint, and ephemeral cloud shadows. Taking the median probability across a 22-month pre-event window (Jan 2022 – Oct 2023) eliminates transient cloud artifacts and produces a stable representation of the urban footprint.

## 3. HOW it works (with worked numeric example)
Dynamic World neural networks output 9 softmax probabilities per pixel: `water`, `trees`, `grass`, `flooded_vegetation`, `crops`, `shrub_and_scrub`, `built`, `bare`, and `snow_and_ice`.

### Worked Example: Runoff & Exposure Quantification
For a pixel on the Tambaram-Velachery corridor:
- Softmax probability for `built`: $P(\text{built}) = 0.82$
- Softmax probability for `bare`: $P(\text{bare}) = 0.12$
- Softmax probability for `trees`: $P(\text{trees}) = 0.04$
- Softmax probability for `water`: $P(\text{water}) = 0.02$

1. **Hydraulic Runoff Factor ($I_{\text{impervious}}$):**
   Impervious concrete surfaces prevent infiltration, channeling $80\text{--}95\%$ of rainfall into surface runoff:
   $$I_{\text{impervious}} = P(\text{built}) + 0.5 \cdot P(\text{bare}) = 0.82 + 0.5(0.12) = 0.88$$
2. **Built-Up Exposure Proxy ($E$):**
   Exposure is directly proportional to built surface area. For a $30 \text{ m} \times 30 \text{ m}$ analysis cell ($900 \text{ m}^2$):
   $$E_{\text{cell}} = P(\text{built}) \times 900 \text{ m}^2 = 0.82 \times 900 = 738 \text{ m}^2 \text{ built footprint}$$
3. **Settlement Exposure ($E_{\text{settlement}}$):**
   Aggregating all cells within a settlement's Voronoi polygon or service radius gives its total built footprint, used directly to weight critical road disruption impact.

## 4. Key Parameters and Sensitivity
- `dw_composite_start` (2022-01-01) and `dw_composite_end` (2023-10-31): Closes prior to the December 2023 flood event to guarantee no post-disaster standing water or cloud cover biases the baseline exposure map.
- Normalization Direction:
  - In Flood Hazard: Built-up surface increases runoff coefficient $\implies$ Cost direction (higher $P(\text{built}) \implies$ higher flood susceptibility).
  - In Slope Instability: Built-up/paved areas often stabilize surface soil vs. steep barren cuts $\implies$ Distinct evaluation in slope model.

## 5. Common Mistakes and Limitations
1. **Never Call It "Population":** Always label the metric **"built-up exposure (population proxy)"**. A warehouse or shopping complex has high built-up probability but may house few residents at night, whereas high-density residential wards have massive occupant density. Clarifying this terminology demonstrates professional rigor to judges.
2. **Resampling Artifacts:** Dynamic World is native 10 m, while Copernicus DEM is 30 m. We resample Dynamic World to 30 m using area-weighted pixel averaging, preserving the true percentage of impervious cover within each 30 m hydraulic cell.

## 6. Likely Judge Questions and Model Answers
- **Q1: Why did you not use WorldPop or LandScan to count real people?**
  *Answer:* Problem Statement rules strictly prohibit external downloads and unverified third-party population rasters, permitting only Earth Engine and OpenStreetMap sources. Furthermore, WorldPop models rely on out-of-date 2011 Indian Census projections. Dynamic World 10 m built-up probability provides an objective, freshly observed proxy of physical human settlement footprint.
- **Q2: How does built-up land cover influence flood susceptibility in your model?**
  *Answer:* Built-up concrete and asphalt surfaces are near-impermeable, exhibiting runoff coefficients exceeding 0.85 compared to 0.15 for vegetated soil. In flat urban catchments like Velachery, high impervious cover prevents infiltration, concentrating storm runoff into streets.
- **Q3: What if cloud cover contaminated the Dynamic World composite?**
  *Answer:* We filter out all scenes with cloud probability $>20\%$ and compute the multi-temporal temporal median across 22 months of Sentinel-2 acquisitions (over 100 overpasses). Cloud shadows and transient clouds are statistically filtered out by median reduction.
- **Q4: How did you define the exposure of an OSM settlement point?**
  *Answer:* We sum the built-up exposure raster within a localized catchment around the settlement centroid, capturing the surrounding built infrastructure footprint.
- **Q5: Can bare soil be mistaken for built-up land?**
  *Answer:* Dynamic World's deep neural network is trained on millions of global multispectral tiles, separating bare agricultural fallow from built asphalt/concrete using short-wave infrared (SWIR) spectral absorption characteristics.
