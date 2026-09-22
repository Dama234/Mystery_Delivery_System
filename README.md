# FastBox Mystery Delivery System 🚚📦

A comprehensive logistics simulation engine built for **FastBox**, simulating a day of parcel pickup and delivery operations across multiple warehouses, delivery agents, and customer destinations.

---

## 🎯 Overview of Implemented Tasks

| Task | Description | Evaluation Weight | Implementation Status |
| :--- | :--- | :--- | :--- |
| **Task 1** | **JSON Parsing** | 10% | ✅ Implemented in `load_data()` with support for both dictionary and list formats |
| **Task 2** | **Euclidean Distance & Assignment** | 20% + 25% | ✅ Precise `euclidean_distance()` and nearest-agent mapping via `assign_packages()` |
| **Task 3** | **Route Simulation & Distance Tracking** | 25% | ✅ Sequential agent route simulation tracking total distance in `simulate_deliveries()` |
| **Task 4 & 5** | **Report Generation & JSON Export** | 25% | ✅ Efficiency metric computation, best agent identification, saved to `report.json` |
| **Bonus 1** | **Random Delivery Delays** | 10% | ✅ Realistic transit delays and time tracking per agent leg |
| **Bonus 2** | **ASCII Route Map Visualization** | 10% | ✅ 2D spatial grid & step-by-step route breakdown in `visualizer.py` |
| **Bonus 3** | **Mid-Day Agent Joining** | 10% | ✅ Dynamic re-dispatch of pending packages when a new agent comes online |
| **Bonus 4** | **Export Top Performer to CSV** | 10% | ✅ Performance ranking and top performer marked in `top_performer.csv` |

---

## 📁 Repository Structure

```
├── delivery_simulator.py      # Core simulation engine and CLI entry point
├── visualizer.py              # 2D ASCII spatial territory and route visualizer
├── test_delivery_simulator.py # Comprehensive unit test suite (19 test cases)
├── data.json                  # Default active input dataset (12 pkgs, 5 WH, 5 agents)
├── report.json                # Generated simulation report
├── top_performer.csv          # Exported CSV of top performer & metrics
├── README.md                  # Detailed project documentation
└── inputs/                    # 9 diverse test datasets provided in assignment
    ├── dataset_1_pdf.json     # 3 warehouses, 3 agents, 5 packages (Assignment PDF)
    ├── dataset_2_10pkgs.json  # 3 warehouses, 3 agents, 10 packages
    ├── dataset_3_12pkgs.json  # 5 warehouses, 5 agents, 12 packages
    ├── dataset_4_10pkgs.json  # 5 warehouses, 5 agents, 10 packages
    ├── dataset_5_9pkgs.json   # 4 warehouses, 4 agents, 9 packages
    ├── dataset_6_10pkgs.json  # 4 warehouses, 4 agents, 10 packages
    ├── dataset_7_11pkgs.json  # 5 warehouses, 4 agents, 11 packages
    ├── dataset_8_11pkgs.json  # 5 warehouses, 4 agents, 11 packages
    └── dataset_9_8pkgs.json   # 3 warehouses, 4 agents, 8 packages
```

---

## 🧠 Approach & Architecture

The simulator models parcel logistics operations through five decoupled, modular components:

1. **Robust Data Ingestion (`load_data`)**:
   - Parses JSON data cleanly without heavy external framework dependencies.
   - Automatically normalizes both dictionary-based inputs (`"warehouses": {"W1": [x, y]}`) and list-of-objects schemas (`[{"id": "W1", "location": [x, y]}]`), as well as key aliases (`warehouse` vs `warehouse_id`, `destination` vs `location`).
2. **Nearest-Neighbor Spatial Mapping (`assign_packages`)**:
   - Computes Euclidean distance from each agent's starting position to every warehouse.
   - Maps each package to the nearest agent responsible for that package's warehouse.
   - Uses deterministic lexicographical sorting for tie-breaking.
3. **Continuous Route Simulation (`simulate_deliveries`)**:
   - Simulates physical vehicle movements: an agent begins at their assigned starting coordinates, drives to the package's warehouse to pick it up, then drives to the destination to complete drop-off.
   - For subsequent packages, the agent's current location seamlessly carries forward from their previous drop-off destination directly to the next warehouse, avoiding artificial resets.
4. **Metric Evaluation & Report Generation (`generate_report`, `save_report`)**:
   - Evaluates `packages_delivered`, `total_distance`, and `efficiency` ($\frac{\text{total\_distance}}{\text{packages\_delivered}}$).
   - Identifies `best_agent` as the agent with the lowest average distance per package delivered (minimum non-zero efficiency).
   - Handles idle agent edge cases (0 packages delivered) with safe zero-division guarding (`efficiency = 0.0`).
5. **Operational Extensions (All 4 Bonuses)**:
   - **Delays**: Stochastic delay modeling (3–15 mins/leg) tracking total transit hours.
   - **ASCII Visualizer**: 2D coordinate grid projection and step-by-step route flow logs.
   - **Dynamic Mid-Day Agent Arrival**: Rebalances unpicked parcels when new capacity enters the fleet.
   - **CSV Reporting**: Tabular export ranking fleet performance.

---

## 🔍 Specific Logic Assumptions & Interpretations

1. **Routing Path & Agent Continuity**:
   - Deliveries for an agent are fulfilled sequentially in order.
   - An agent starts at their initial position `agent_location`. For package 1, the agent travels to the warehouse, picks up the package, and delivers to destination 1. For package 2, the agent departs from destination 1 directly to the next warehouse.
2. **Tie-Breaking Rule**:
   - If two agents are equidistant to a warehouse, deterministic tie-breaking by agent ID sorting (e.g., `A1` before `A2`) is enforced to guarantee 100% reproducible results.
3. **Efficiency Metric Definition**:
   - Efficiency is defined as $\frac{\text{total\_distance}}{\text{packages\_delivered}}$ (average distance per delivery).
   - A **lower** score represents higher delivery efficiency (less travel required per package delivered).
   - Only active agents (`packages_delivered > 0`) are eligible for `best_agent`.
4. **Idle Agent Handling**:
   - If an agent is assigned 0 packages, their metrics are recorded as `packages_delivered: 0`, `total_distance: 0.0`, `efficiency: 0.0`.

---

## 🛠️ Technical Challenges & Resolutions

### 1. Reconciling Varying JSON Schemas
* **Challenge**: The assignment specifications presented different JSON structures—a dictionary format mapping IDs to coordinates vs. a list format with nested objects (`warehouse_id`, `location`).
* **Resolution**: Built a polymorphic parser in `load_data()` that automatically detects schemas, validates coordinate dimensionality, and normalizes them into strongly typed tuples `(float, float)`.

### 2. Multi-Trip Routing Ambiguity vs. Assignment Figures
* **Challenge**: Understanding whether agents reset to home base between deliveries or operate in continuous routes.
* **Resolution**: Implemented continuous route simulation where agents move from customer destination directly to the next warehouse pickup, which accurately reflects real-world courier fleet logistics.

### 3. Idle Agents & Division-by-Zero Protection
* **Challenge**: In scenarios where certain warehouses/agents dominate geography (e.g. `dataset_2_10pkgs.json` where A1 is closest to all warehouses), other agents remain idle. Calculating `total_distance / packages_delivered` would raise `ZeroDivisionError`.
* **Resolution**: Implemented safe conditional efficiency evaluation (`dist / delivered if delivered > 0 else 0.0`) and ensured `best_agent` selection excludes non-participating agents.

---

## 🚀 How to Run the Simulator

### 1. Basic Run (Default `data.json`)
Runs the standard simulation on `data.json` and outputs `report.json`:
```bash
python delivery_simulator.py
```

### 2. Run with Any Specific Dataset
```bash
python delivery_simulator.py --data inputs/dataset_1_pdf.json
```

### 3. Run with All Bonus Features Enabled
Enables random delivery delays, ASCII map visualization, mid-day agent arrival, and CSV export:
```bash
python delivery_simulator.py --all-bonuses
```

### 4. Run Specific Bonus Features Individually
* **ASCII Route Map & Leg-by-leg Visualizer**:
  ```bash
  python delivery_simulator.py --visualize
  ```
* **Simulate Random Traffic / Transit Delays**:
  ```bash
  python delivery_simulator.py --delays
  ```
* **Dynamic Mid-Day Agent Joining Demonstration**:
  ```bash
  python delivery_simulator.py --midday-agent
  ```
* **Custom Output Paths**:
  ```bash
  python delivery_simulator.py --data inputs/dataset_4_10pkgs.json --report my_report.json --csv my_top_performer.csv
  ```

---

## 🧪 Automated Testing

A full automated test suite is provided using Python's standard `unittest` library:
```bash
python -m unittest test_delivery_simulator.py -v
```

All 19 test cases verify:
- Euclidean distance calculation with known geometric triangles and edge cases.
- Robust JSON parsing across both dictionary and list formats.
- Error handling for invalid input files and nonexistent warehouse references.
- Nearest-agent assignment logic ensuring **total delivered packages == total input packages**.
- Route distance calculation and zero-division protection for idle agents.
- All 9 datasets in `inputs/` pass cleanly.
- All 4 bonus features function as expected.

---

## 📊 Sample Output Report (`report.json`)

```json
{
    "A1": {
        "packages_delivered": 3,
        "total_distance": 69.96,
        "efficiency": 23.32
    },
    "A2": {
        "packages_delivered": 4,
        "total_distance": 133.29,
        "efficiency": 33.32
    },
    "A3": {
        "packages_delivered": 5,
        "total_distance": 103.75,
        "efficiency": 20.75
    },
    "A4": {
        "packages_delivered": 0,
        "total_distance": 0.0,
        "efficiency": 0.0
    },
    "A5": {
        "packages_delivered": 0,
        "total_distance": 0.0,
        "efficiency": 0.0
    },
    "best_agent": "A3"
}
```

### Top Performer Export (`top_performer.csv`)
```csv
Agent ID,Packages Delivered,Total Distance,Efficiency (dist/pkg),Performance Rank,Status
A3,5,103.75,20.75,1,TOP PERFORMER *
A1,3,69.96,23.32,2,Active
A2,4,133.29,33.32,3,Active
A4,0,0.00,0.00,N/A,Idle
A5,0,0.00,0.00,N/A,Idle
```