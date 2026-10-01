# GEOIMPATHON 1.0 — 3-Minute Live Jury Presentation Script

> **Goal:** Deliver a flawless, commanding, and punchy 3-minute pitch to the competition jury.  
> **Speaker Roles:** Can be presented by 1 speaker or split across 2 presenters (Presenter A: Context & Routing, Presenter B: Criticality & Science).  
> **Total Time:** 180 seconds (3:00).

---

### [0:00 – 0:30] The Hook & The Problem Statement
*(Screen showing Tab 1: Multi-Hazard Risk Map)*

> **Speaker:**  
> "Respected judges, during Cyclone Michaung in December 2023, an ambulance dispatched from Tambaram to reach a hospital took the shortest route suggested by standard GPS navigation. Within six minutes, that ambulance was submerged up to its hood in three feet of water along the Medavakkam marsh causeway.
>
> In an extreme flood, **the shortest route to a hospital can be the deadliest.**
>
> Standard navigation systems optimize for distance or historical traffic. They have zero awareness of hydrologic inundation, structural subway traps, or whether the destination hospital itself is currently flooded under water.
>
> We built the **Multi-Hazard Decision-Support System & Least-Risk Emergency Router**. Our system finds the least-risk route, names the specific roads whose loss isolates the most people, says where to pre-position relief boats and ambulances, and measures exactly how much hospital access collapses in a disaster."

---

### [0:30 – 1:00] The Multi-Hazard Baseline & The No-Leakage Principle
*(Presenter switches layers in Tab 1: Flood Hazard -> Slope Instability -> Multi-Hazard Risk)*

> **Speaker:**  
> "Our study area covers the 400 square kilometer South Chennai to Chengalpattu corridor—home to over a million residents across Tambaram, Pallikaranai, and Velachery.
>
> Because coastal Chennai is predominantly flat, flood is the dominant hazard. We model it using Copernicus GLO-30 DEM derivatives, Height Above Nearest Drainage (HAND), Dynamic World land cover, and pre-event NDVI. The second hazard is slope-instability and erosion susceptibility—confined strictly to quarries, lake bunds, and elevated railway cuts. We do not oversell it.
>
> Using mathematically consistent AHP with a Consistency Ratio of 0.02, verified against Shannon Information Entropy, we categorize the district into Low, Moderate, High, and Very High risk.
>
> And we strictly enforce the **No-Validation-Leakage Principle**: Sentinel-1 SAR imagery from the Michaung flood is withheld entirely from model construction. It is used exclusively as an independent, post-hoc ground truth."

---

### [1:00 – 1:45] Live Demo: Safest vs. Fastest Emergency Routing
*(Presenter switches to Tab 2: Emergency Route. Selects Origin: 'Madipakkam', toggles Safety Slider to α = 3.5)*

> **Speaker:**  
> "Now let us see what happens when a citizen in Madipakkam needs acute medical care.
>
> Notice the live comparison on screen:
> - The **Fastest Route** in dashed orange takes the shortest road. But look at the metric card: **68% of that route runs directly through High and Very High flood zones**, driving through a known underpass drowning trap.
> - Now look at our **Safest Route** in solid deep blue. By dynamically weighting road edges using our cost function $C = L \cdot (1 + \alpha R)$, the algorithm detours around the inundated wetland basin.
> - It adds just 4 minutes of travel time and 1.8 kilometers of distance, but it **reduces flood hazard exposure to 0%**.
> - Furthermore, look at the destination: our system automatically filtered out 142 flooded hospitals in High-risk zones, guiding the vehicle only to a verified, operational facility on dry ground."

---

### [1:45 – 2:20] Road Criticality & Relief Pre-positioning
*(Presenter switches to Tab 3: Critical roads & isolation)*

> **Speaker:**  
> "Disaster managers cannot fix every road simultaneously. Where should the District Disaster Management Officer stage barricades and relief assets?
>
> Instead of abstract topological betweenness, we developed a two-stage **Removal Impact Algorithm**. We simulated the physical severance of candidate roads across all 141 settlement routes.
>
> On the map, you see our **Top 10 Single Points of Failure** with numbered badges. Rank 1 is the Mount-Medavakkam arterial corridor. Severing this link forces acute detours for 17 residential wards and cuts access for over 135,000 exposure units.
>
> In the severed flood graph, our system identifies **24 completely isolated settlements** and **25 severely delayed communities**.
>
> Using a **Greedy Maximum-Coverage heuristic**, our system recommends these **5 strategic relief staging hubs** on verified safe ground outside High-risk zones. And we don't just give coordinates: Hub 1 at Pathala Vigneshvarar Temple is assigned 4 inflatable rescue boats and high-water tractors, while Hub 3 at Rama Anjaneya Koil is assigned 4x4 high-clearance ambulances and mobile generators."

---

### [2:20 – 2:45] Golden-Hour Access Collapse & Monte Carlo Robustness
*(Presenter switches to Tab 4: Dashboard, Access & Robustness)*

> **Speaker:**  
> "Finally, how resilient is the healthcare system, and how robust is our math?
>
> Look at our **Golden-Hour Access Collapse metric**: in normal conditions, 99.3% of built-up exposure can reach a hospital within 60 minutes. During Cyclone Michaung, that collapses to 76.7%—a **loss of 22.6% of hospital access**, leaving 132,000 exposure units cut off from definitive trauma care. For 30-minute acute emergencies, access collapses by **nearly 30%**.
>
> If a critic asks: *'Did your subjective AHP weights bias these routes?'*, we answer with 200 stochastic Monte Carlo runs. We perturbed all weights by $\pm 20\%$ multiplicative noise. Across all 200 trials, our primary emergency routes achieved **100% route stability**, and our critical road bottlenecks achieved **92.5% persistence**. Our decisions are governed by real physical geography, not weight nuances."

---

### [2:45 – 3:00] Winning Closing Statement
*(Presenter shows the What-and-Why Register in Tab 5 or the Executive Dashboard)*

> **Speaker:**  
> "Judges, every dataset in this tool is freely accessible via Google Earth Engine and OpenStreetMap. Every single parameter is logged in our What-and-Why register. The entire pipeline runs in under 10 minutes on an ordinary laptop, with all 23 automated tests passing in 2 seconds.
>
> This is not a theoretical GIS exercise. This is a battle-tested, command-center decision support system ready for District Disaster Management deployment.
>
> Thank you, and we welcome your questions!"
