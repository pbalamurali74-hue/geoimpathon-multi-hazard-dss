# Learning Module 10: Dijkstra Least-Risk Routing & Edge-Cost Design

## 1. WHAT it does
Standard navigation systems (Google Maps, Waze) route vehicles along the shortest distance or fastest free-flow path. In a catastrophic cyclone, following the shortest path through low-lying underpasses or canal margins is lethal: vehicles stall in rising floodwaters, trapping patients and emergency responders. Our routing engine models the OpenStreetMap drive network as a risk-weighted directed graph and applies Dijkstra's algorithm with an edge-cost penalty that balances detour distance against flood hazards.

## 2. WHY this method over alternatives
- **Risk-Weighted Dijkstra vs. Standard Shortest Path (Dijkstra $\alpha = 0$):** Standard shortest path ignores water depth entirely, routinely routing ambulances through lethal drowning zones. Our risk-weighted cost formulation forces paths to divert to higher, safer ground.
- **Continuous Cost Scaling vs. Strict Binary Road Deletion:** Deleting every road with water removes entire suburban networks, leaving 80% of settlements with "No route found." Continuous scaling allows vehicles to traverse minor, shallow water ($<80\text{th}$ percentile) with a proportional delay penalty, while strictly blocking lethal zones ($>95\text{th}$ percentile).
- **Sampling Along Edges (30 m intervals) vs. Centroid Sampling:** Long road links (e.g. a 3 km stretch of the Chennai Bypass) often span dry elevated flyovers and low-lying submerged wetlands. Centroid sampling evaluates only the midpoint, missing deep localized dips. Sampling points every 30 m ensures localized hazards are captured.

---

## 3. HOW it works (with worked numeric example)

### Edge Risk Formulation:
For each road edge $e$ with length $L_e$:
1. Sample points every $30 \text{ m}$ along the line geometry.
2. Intersect points with the continuous Multi-Hazard Risk raster $R(x, y) \in [0, 1]$.
3. Compute the mean risk ($\bar{R}_e$) and peak localized risk ($R_{\max, e}$).
4. Combine into base edge risk:
   $$R_{\text{edge}} = 0.5 \bar{R}_e + 0.5 R_{\max, e}$$
   *(Using both mean and max prevents a road with a single deeply submerged underpass from appearing safe due to low average water depth)*.
5. **Structural Risk Bumps:**
   - If OSM tag indicates a tunnel or depressed grade (`tunnel=*` or `layer < 0`): $R_{\text{edge}} \leftarrow \min(1.0, R_{\text{edge}} + 0.15)$ (extreme drowning trap).
   - If OSM tag indicates a low bridge over water (`bridge=yes` crossing a stream): $R_{\text{edge}} \leftarrow \min(1.0, R_{\text{edge}} + 0.08)$ (overtopping and scour risk).

### Edge Cost Function:
$$C_e = L_e \cdot (1 + \alpha \cdot R_{\text{edge}})$$
Where $\alpha \in [0, 10]$ is the interactive UI safety priority slider (default $\alpha = 3.0$).

### Worked Numeric Example:
An ambulance must choose between Route A (Shortest through lowland) and Route B (Detour on ridge):

- **Route A (Shortest):**
  - Length: $L_A = 5.0 \text{ km}$
  - Mean risk: $0.65$, Max risk: $0.90 \implies R_{\text{edge}} = 0.5(0.65) + 0.5(0.90) = 0.775$ (High Risk)
  - Cost at $\alpha = 0$ (Fastest): $C_A = 5.0 \cdot (1 + 0) = \mathbf{5.0}$
  - Cost at $\alpha = 3$ (Safest): $C_A = 5.0 \cdot (1 + 3 \times 0.775) = 5.0 \times (1 + 2.325) = 5.0 \times 3.325 = \mathbf{16.625}$

- **Route B (Detour via higher ground):**
  - Length: $L_B = 7.5 \text{ km}$ ($50\%$ longer physical distance)
  - Mean risk: $0.15$, Max risk: $0.25 \implies R_{\text{edge}} = 0.5(0.15) + 0.5(0.25) = 0.200$ (Low Risk)
  - Cost at $\alpha = 0$ (Fastest): $C_B = 7.5 \cdot (1 + 0) = \mathbf{7.5}$
  - Cost at $\alpha = 3$ (Safest): $C_B = 7.5 \cdot (1 + 3 \times 0.200) = 7.5 \times (1 + 0.600) = 7.5 \times 1.600 = \mathbf{12.000}$

- **Decision Outcome:**
  - When $\alpha = 0$ (Fastest): Model picks **Route A** ($C_A = 5.0 < C_B = 7.5$), driving into hazardous floodwaters.
  - When $\alpha = 3$ (Safest): Model picks **Route B** ($C_B = 12.0 < C_A = 16.625$), safely detouring around the flooded corridor with an acceptable 2.5 km added distance.

---

## 4. Key Parameters and Sensitivity
- Safety Slider $\alpha$ (Default: $3.0$, Range: $0.0\text{--}10.0$):
  - $\alpha = 0$: Reverts to standard shortest Euclidean/free-flow path.
  - $\alpha = 3$: Penalizes high-risk roads significantly while avoiding extreme multi-hour detours.
  - $\alpha = 10$: Forces extreme conservative routing, strictly avoiding any puddle even if it requires a 30 km detour.
- Block Threshold (95th percentile): Roads with $R_{\text{edge}} \ge 0.72$ (top 5% risk) are completely severed.
- Fallback Mechanism: If severance disconnects a remote neighborhood, the algorithm displays a clear visual warning: *"No completely safe route found. Showing the lowest-risk alternative instead."* and routes via minimal accumulated risk.

## 5. Common Mistakes and Limitations
1. **No Live Traffic:** OSMnx models physical road hierarchy speeds, not live congestion. In the README and UI, we state plainly that travel times assume free-flow speeds on dry roads and $5 \text{ km/h}$ crawling speed in High-risk flood zones.
2. **Ignoring One-Way Streets:** Drive networks must be modeled as directed graphs (`DiGraph`) to respect one-way medians, divided expressways, and turning restrictions.

## 6. Likely Judge Questions and Model Answers
- **Q1: Why did you combine mean risk and max risk as 0.5*mean + 0.5*max?**
  *Answer:* Mean risk captures the overall wetness along the entire road link, but flood drownings are caused by single localized deep spots. If a 2 km road is completely dry except for a 50-meter dip in an underpass where water is 2 meters deep, the mean risk is misleadingly low (~0.10). Adding 50% max risk ensures the deep underpass flags the entire edge as hazardous.
- **Q2: Why give extra risk bumps to tunnels and low bridges?**
  *Answer:* Tunnels and subways (OSM `tunnel=*` or `layer < 0`) are notorious urban death traps during cyclones (e.g., Chennai subway drownings during Michaung). Water concentrates rapidly in depressed underpasses. Bridges over swollen canals suffer from structural hydraulic scouring and overtopping. Adding explicit risk bumps (+0.15 for tunnels, +0.08 for bridges) accounts for these physical infrastructure failure modes.
- **Q3: What happens when alpha = 0?**
  *Answer:* The edge cost simplifies to physical distance ($C_e = L_e$), yielding the conventional shortest path regardless of flood risk. This allows the side-by-side comparison panel to directly contrast fastest vs. safest routes.
- **Q4: How do you handle emergency destinations?**
  *Answer:* Hospitals and shelters located within High or Very High risk zones are flagged as "Unsafe" and systematically excluded from destination queries. The router directs patients only to facilities on dry, operational high ground.
- **Q5: What travel speed is assumed in flooded areas?**
  *Answer:* In normal dry zones, vehicles travel at class-specific free-flow speeds (motorway: 80 km/h, secondary: 40 km/h, residential: 20 km/h). In High-risk flood zones, passable roads are throttled to a cautious 5 km/h crawling speed.
