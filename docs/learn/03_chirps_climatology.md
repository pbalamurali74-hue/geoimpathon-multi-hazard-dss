# Learning Module 03: CHIRPS Rainfall Climatology

## 1. WHAT it does
The Climate Hazards Center InfraRed Precipitation with Station data (CHIRPS) provides a high-continuity, 20+ year daily precipitation record across our study domain. We extract the historical Mean Annual Maximum 3-Day Cumulative Rainfall (2000–2022) to represent extreme convective and cyclonic storm forcing. This establishes a baseline climate susceptibility indicator for regional flood and soil erosion risk.

## 2. WHY this method over alternatives
- **CHIRPS vs. ERA5-Land:** ERA5-Land provides reanalysis precipitation at ~9 km to 11 km grid resolution. CHIRPS has a finer native spatial resolution of 0.05° (~5.3 km) and blends satellite cold cloud duration (CCD) with local in-situ IMD (India Meteorological Department) rain gauge stations, yielding lower systematic bias over Peninsular India.
- **CHIRPS vs. GPM IMERG:** GPM IMERG provides high-cadence satellite microwave-infrared estimates (0.1°), but its consistent record starts only around 2014, whereas CHIRPS offers a 40+ year homogeneous baseline (1981–present) ideal for multi-decadal extreme return value estimation.
- **Mean Annual Maximum 3-Day Rainfall vs. Annual Mean Total:** Cyclone flood disasters in Tamil Nadu are triggered by concentrated 48-to-72-hour deluges (e.g., Cyclone Michaung delivered over $450 \text{ mm}$ in 48 hours). Annual totals dilute acute storm peaks, whereas the 3-day annual maximum directly models hydraulic ponding and embankment saturation capacity.

## 3. HOW it works (with worked numeric example)
For every year $y \in [2000, 2022]$:
1. Compute the rolling 3-day precipitation sum $P_{3\text{d}}(t) = \sum_{k=0}^{2} P(t - k)$ for each day $t$.
2. Extract the annual maximum 3-day value: $M_y = \max_{t \in \text{year } y} P_{3\text{d}}(t)$.
3. Compute the multi-year climatological mean:
   $$\bar{M}_{3\text{d}} = \frac{1}{N} \sum_{y=2000}^{2022} M_y$$

### Worked Example:
Across 3 sample years for a CHIRPS grid cell over Tambaram:
- Year 2020 Max 3-day (Cyclone Nivar): $310 \text{ mm}$
- Year 2021 Max 3-day (Nov deluge): $290 \text{ mm}$
- Year 2022 Max 3-day (Monsoon pulse): $195 \text{ mm}$
- Climatological indicator value:
  $$\bar{M}_{3\text{d}} = \frac{310 + 290 + 195}{3} = 265 \text{ mm}$$
- Min-Max normalized against regional baseline $[180 \text{ mm}, 320 \text{ mm}]$:
  $$I_{\text{rain}} = \frac{265 - 180}{320 - 180} = \frac{85}{140} = 0.607$$

## 4. Key Parameters and Sensitivity
- `chirps_start_year` (2000) and `chirps_end_year` (2022): Captures modern climate variability while preventing event leakage (ending before December 2023).
- Spatial Weight in AHP: CHIRPS is assigned a **low weight (0.05 to 0.08)** in the AHP matrix. Because the study corridor is 20 km x 20 km, a 5 km grid cell spans only 4x4 pixels across the entire bbox, resulting in minimal spatial variance across the area. Over-weighting it would add uniform artificial offsets rather than local discriminatory power.

## 5. Common Mistakes and Limitations
1. **Coarse Spatial Resolution (~5 km):** CHIRPS cannot capture localized convective cloudbursts that flood a single neighborhood while leaving an adjacent ward dry. It serves purely as a regional background forcing indicator.
2. **Data Leakage Trap:** Using rainfall from December 3–5, 2023 inside the hazard model would leak validation event data into a susceptibility index. The hazard index must model intrinsic spatial susceptibility, while the Michaung event tests its predictive validity.

## 6. Likely Judge Questions and Model Answers
- **Q1: Why did you include CHIRPS if it only has ~5 km resolution over a 20 km study area?**
  *Answer:* To maintain formal compliance with comprehensive multi-criteria flood hazard modeling frameworks while acknowledging its limitations honestly. We explicitly assign CHIRPS the lowest weight in our AHP hierarchy ($<8\%$) so local high-resolution 30 m topography (DEM, slope, HAND) and 10 m land cover govern spatial risk gradients.
- **Q2: Does your CHIRPS indicator use rainfall from Cyclone Michaung?**
  *Answer:* No. The climatology baseline ends in 2022. Including 2023 cyclone rainfall would violate our strict no-validation-leakage protocol.
- **Q3: Why 3-day rainfall rather than 1-day or 5-day?**
  *Answer:* Chennai's urban hydrology features extensive interconnected tank systems (eri cascades) and low-gradient drainage canals. One-day rain often fills retention basins, but intense 3-day cumulative rainfall overwhelms storage capacity and triggers basin-wide overtopping.
- **Q4: How did you resample CHIRPS to match the 30 m analysis grid?**
  *Answer:* Using bilinear interpolation. Bilinear interpolation smooths sharp rectangular 5 km pixel boundaries into a continuous climatic gradient without introducing non-physical ringing artifacts.
- **Q5: What alternative satellite precipitation products could improve resolution in future work?**
  *Answer:* IMD high-resolution gridded daily rainfall ($0.25^\circ$) or downscaled GPM IMERG half-hourly ($0.1^\circ$) merged with Doppler weather radar reflectivity from Chennai Port and Sriharikota radars.
