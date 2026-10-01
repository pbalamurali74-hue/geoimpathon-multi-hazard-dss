# Learning Module 01: Sentinel-1 SAR Flood Detection

## 1. WHAT it does
Sentinel-1 synthetic aperture radar (SAR) flood mapping uses active C-band microwave pulses to detect standing water on the Earth's surface regardless of cloud cover or darkness. By comparing radar backscatter ($\sigma^0$) before and during Cyclone Michaung (December 2023), the algorithm isolates newly inundated open land and waterlogged terrain. The resulting binary flood raster serves as the ground-truth validation layer for our multi-hazard decision-support system.

## 2. WHY this method over alternatives
- **Versus Sentinel-2 / Landsat Optical Imagery:** Optical sensors rely on visible and infrared sunlight. During tropical cyclones like Michaung, dense cloud cover and torrential monsoon rains render optical sensors blind for days during peak inundation. Sentinel-1's $5.405 \text{ GHz}$ microwaves penetrate clouds, rain, and atmospheric haze effortlessly.
- **Versus Single-Image SAR Thresholding:** A single post-flood SAR image cannot distinguish between permanent water bodies, airport runways, calm asphalt highways, and floodwaters, as all appear dark due to specular reflection. Log-ratio change detection ($\text{Post} - \text{Pre}$) cancels out permanent smooth targets and isolates true temporal flood events.
- **Versus Hydrodynamic Modeling (e.g., HEC-RAS, LISFLOOD):** Hydraulic numerical models require high-resolution bathymetry, culvert geometries, and calibrated roughness coefficients that are rarely available for vast, un-gauged urban corridors in real time. Satellite SAR change detection directly observes actual standing water on the ground.

## 3. HOW it works (with worked numeric example)
Rough soil and urban surfaces cause diffuse radar backscatter, returning significant microwave energy to the satellite antenna (e.g., $-11 \text{ dB}$). When water inundates the land, the smooth water surface acts like a mirror, reflecting incoming radar pulses away from the satellite antenna (specular reflection), causing backscatter to drop dramatically (e.g., to $-18 \text{ dB}$).

### Worked Example:
Suppose a pixel in Pallikaranai wetland margin has:
- Pre-event backscatter ($\sigma^0_{\text{pre}}$): $-11.5 \text{ dB}$
- Post-event backscatter ($\sigma^0_{\text{post}}$): $-17.8 \text{ dB}$
- Change detection difference:
  $$\Delta \sigma^0 = \sigma^0_{\text{post}} - \sigma^0_{\text{pre}} = -17.8 - (-11.5) = -6.3 \text{ dB}$$
- Empirical threshold check: $-6.3 \text{ dB} \le -3.0 \text{ dB} \implies \text{Candidate Flood = True}$.
- Low backscatter absolute check: $-17.8 \text{ dB} \le -15.0 \text{ dB} \implies \text{Confirmed Water Specular Reflection}$.
- Permanent water check: JRC Occurrence is $12\% \le 80\% \implies \text{Not Permanent Water}$.
- Slope mask check: Copernicus DEM slope is $1.2^\circ \le 5.0^\circ \implies \text{Passes Topographic Mask}$.
- Result: **Classified as Event Floodwater**.

## 4. Key Parameters and Sensitivity
- `difference_threshold_db` (Default: $-3.0 \text{ dB}$):
  - *If relaxed to $-1.5 \text{ dB}$*: Captures minor soil moisture changes and wet grass, introducing high false-alarm rates.
  - *If made conservative to $-5.0 \text{ dB}$*: Misses emergent vegetation and shallow flood fringes, under-estimating inundated area.
- `jrc_permanent_water_threshold` (Default: $80\%$): Pixels with historical water presence $>80\%$ are masked out to prevent lakes/rivers from contaminating event flood statistics.
- `max_slope_deg` (Default: $5.0^\circ$): Water collects in depressions and flat terrains; slopes $>5^\circ$ suffer from radar terrain layover/shadow artifacts that produce false specular signals.
- `min_patch_pixels` (Default: $8$ pixels / $\sim 7,200 \text{ m}^2$): Eliminates single isolated noisy pixels (speckle remnants) via connected-component labeling.

## 5. Common Mistakes and Limitations
1. **Urban Double-Bounce and Shadowing:** In dense concrete settlements (e.g., narrow streets in Velachery), radar signals bounce from streets to vertical walls and back to the antenna (corner reflection), producing bright backscatter even if the street is under $1 \text{ m}$ of water. SAR systematically under-detects street-level flooding in narrow urban canyons.
2. **Emergent Vegetation:** Tall reeds or flooded tree canopies reflect radar signals diffusely, masking underlying standing water.
3. **Orbit and Pass Direction Mismatch:** Comparing an ascending pass with a descending pass, or images from different relative orbits, introduces geometric look-angle distortions that produce massive false change artifacts. Always pair identical relative orbits.

## 6. Likely Judge Questions and Model Answers
- **Q1: Why did you use VV polarization instead of VH or dual-pol combinations?**
  *Answer:* VV (vertical transmit, vertical receive) polarization is more sensitive to vertical surface roughness and surface wave disturbances on water than cross-polarization (VH). For open water detection over lowlands, VV exhibits a wider dynamic backscatter separation between calm water and rough soil.
- **Q2: Does your Sentinel-1 flood map feed into the flood hazard index?**
  *Answer:* No. Doing so would cause circular reasoning and severe validation data leakage. The hazard layer is derived exclusively from static landscape susceptibility indicators (DEM, HAND, slope, land cover, rainfall climatology). The Sentinel-1 flood map is reserved strictly as independent ground truth for ROC/AUC validation.
- **Q3: How do you address radar speckle noise?**
  *Answer:* We apply a $3 \times 3$ focal median filter. Unlike linear mean smoothing which blurs sharp land-water boundaries, the median filter preserves sharp edge gradients while stripping impulsive speckle spikes.
- **Q4: Cyclone Michaung peaked on Dec 3-4, 2023. What if the Sentinel-1 overpass was several days later?**
  *Answer:* Sentinel-1 has a 12-day revisit over Chennai from a single orbit track. Floodwaters in the flat, low-lying coastal basins (Pallikaranai basin and Chembarambakkam outflow) persist for 5 to 10 days post-cyclone due to sluggish coastal drainage, allowing post-event acquisitions up to Dec 10-15 to capture residual flood extent accurately.
- **Q5: What are the spatial resolution limitations?**
  *Answer:* Sentinel-1 GRD pixels are resampled to $30 \text{ m}$ to match the Copernicus DEM and prevent over-sampling artifacts. Linear urban drainage ditches and small street channels narrower than $30 \text{ m}$ cannot be individually resolved.
