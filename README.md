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
C:\Users\bchai\OneDrive\Desktop\pythonpro\
├── delivery_simulator.py      # Core simulation engine and CLI entry point
├── visualizer.py              # 2D ASCII spatial territory and route visualizer
├── test_delivery_simulator.py # Comprehensive unit test suite (19 test cases)
├── data.json                  # Default active input dataset
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

## 🚀 How to Run the Simulator

### 1. Basic Run (Default `data.json`)
Runs the standard simulation on `data.json` and outputs `report.json`:
```bash
python delivery_simulator.py
```

### 2. Run with Custom Dataset
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