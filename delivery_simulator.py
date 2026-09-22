"""
FastBox Mystery Delivery System
================================
A logistics simulator for FastBox that reads operational data,
assigns packages to the nearest agent based on Euclidean distance
from agent to warehouse, simulates delivery routes, and produces
an efficiency report.

Author: Antigravity Agent
"""

import argparse
import csv
import json
import math
import os
import random
from typing import Any, Dict, List, Optional, Tuple

# Import visualizer for ASCII route mapping
try:
    from visualizer import render_ascii_map, render_route_summary
except ImportError:
    render_ascii_map = None
    render_route_summary = None


# =====================================================================
# Task 1: Read and Parse JSON Data Manually
# =====================================================================

def load_data(filepath: str) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, Tuple[float, float]], List[Dict[str, Any]]]:
    """
    Reads and parses the input JSON file.
    
    Robustly handles both formats:
      Format A (Dictionaries with coordinate arrays):
        "warehouses": {"W1": [0, 0], ...}
        "agents": {"A1": [5, 5], ...}
        "packages": [{"id": "P1", "warehouse": "W1", "destination": [30, 40]}, ...]
      Format B (Lists of objects with id and location):
        "warehouses": [{"id": "W1", "location": [0, 0]}, ...]
        "agents": [{"id": "A1", "location": [5, 5]}, ...]
        "packages": [{"id": "P1", "warehouse_id": "W1", "destination": [30, 40]}, ...]

    Returns:
      (warehouses_dict, agents_dict, packages_list)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 1. Parse warehouses
    warehouses: Dict[str, Tuple[float, float]] = {}
    raw_wh = raw.get("warehouses", {})
    if isinstance(raw_wh, dict):
        for wid, coords in raw_wh.items():
            warehouses[str(wid)] = (float(coords[0]), float(coords[1]))
    elif isinstance(raw_wh, list):
        for item in raw_wh:
            wid = str(item.get("id") or item.get("name"))
            coords = item.get("location") or item.get("coordinates")
            warehouses[wid] = (float(coords[0]), float(coords[1]))
    else:
        raise ValueError("Invalid format for 'warehouses' in JSON input.")

    # 2. Parse agents
    agents: Dict[str, Tuple[float, float]] = {}
    raw_ag = raw.get("agents", {})
    if isinstance(raw_ag, dict):
        for aid, coords in raw_ag.items():
            agents[str(aid)] = (float(coords[0]), float(coords[1]))
    elif isinstance(raw_ag, list):
        for item in raw_ag:
            aid = str(item.get("id") or item.get("name"))
            coords = item.get("location") or item.get("coordinates")
            agents[aid] = (float(coords[0]), float(coords[1]))
    else:
        raise ValueError("Invalid format for 'agents' in JSON input.")

    # 3. Parse packages
    packages: List[Dict[str, Any]] = []
    raw_pkgs = raw.get("packages", [])
    if not isinstance(raw_pkgs, list):
        raise ValueError("'packages' must be a list in JSON input.")

    for item in raw_pkgs:
        pid = str(item.get("id"))
        wh = str(item.get("warehouse") or item.get("warehouse_id"))
        dest = item.get("destination") or item.get("location")
        if dest is None or len(dest) < 2:
            raise ValueError(f"Package {pid} has invalid destination coordinates.")
        if wh not in warehouses:
            raise ValueError(f"Package {pid} references unknown warehouse '{wh}'.")

        packages.append({
            "id": pid,
            "warehouse": wh,
            "destination": (float(dest[0]), float(dest[1]))
        })

    return warehouses, agents, packages


# =====================================================================
# Task 2: Distance Calculation & Agent-Package Assignment
# =====================================================================

def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Computes standard 2D Euclidean distance: sqrt((x2 - x1)^2 + (y2 - y1)^2).
    """
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def assign_packages(
    warehouses: Dict[str, Tuple[float, float]],
    agents: Dict[str, Tuple[float, float]],
    packages: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Assigns each package to the nearest agent based on Euclidean distance
    from the agent to the package's pickup warehouse.

    Returns:
      Dict mapping agent_id -> list of assigned package dictionaries.
    """
    if not agents:
        raise ValueError("Cannot assign packages: No delivery agents available.")

    # Precompute nearest agent for each warehouse
    nearest_agent_per_wh: Dict[str, str] = {}
    for wid, w_loc in warehouses.items():
        best_agent = None
        min_dist = float("inf")
        # Deterministic sorting for tie-breaking
        for aid in sorted(agents.keys()):
            dist = euclidean_distance(agents[aid], w_loc)
            if dist < min_dist:
                min_dist = dist
                best_agent = aid
        nearest_agent_per_wh[wid] = best_agent

    # Assign packages
    assignments: Dict[str, List[Dict[str, Any]]] = {aid: [] for aid in agents.keys()}
    for pkg in packages:
        wid = pkg["warehouse"]
        agent_id = nearest_agent_per_wh[wid]
        assignments[agent_id].append(pkg)

    # Verification: total assigned packages matches total packages
    total_assigned = sum(len(pkgs) for pkgs in assignments.values())
    assert total_assigned == len(packages), f"Assignment mismatch: {total_assigned} != {len(packages)}"

    return assignments


# =====================================================================
# Task 3: Simulate Delivery Operations
# =====================================================================

def simulate_deliveries(
    warehouses: Dict[str, Tuple[float, float]],
    agents: Dict[str, Tuple[float, float]],
    assignments: Dict[str, List[Dict[str, Any]]],
    enable_delays: bool = False,
    speed_units_per_hour: float = 30.0,
    delay_range_mins: Tuple[float, float] = (3.0, 15.0),
    random_seed: Optional[int] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Simulates delivery for each agent.
    
    Each agent starts at their initial location.
    For each assigned package:
      1. Travel from current position to warehouse (pick up package).
      2. Travel from warehouse to package destination (deliver package).
      3. Update current position to package destination.
    
    Tracks total distance traveled and detailed route legs.
    Optionally computes random delays and total delivery duration.
    """
    if random_seed is not None:
        random.seed(random_seed)

    agent_results: Dict[str, Dict[str, Any]] = {}

    for aid in sorted(agents.keys()):
        current_pos = agents[aid]
        total_distance = 0.0
        total_time_hours = 0.0
        total_delay_minutes = 0.0
        routes: List[Dict[str, Any]] = []

        assigned_pkgs = assignments.get(aid, [])

        for pkg in assigned_pkgs:
            w_id = pkg["warehouse"]
            w_pos = warehouses[w_id]
            d_pos = pkg["destination"]

            # Leg 1: Current location -> Warehouse
            dist_to_wh = euclidean_distance(current_pos, w_pos)
            # Leg 2: Warehouse -> Destination
            dist_to_dest = euclidean_distance(w_pos, d_pos)

            leg_dist = dist_to_wh + dist_to_dest
            total_distance += leg_dist

            # Bonus: random delay calculation
            leg_delay_mins = 0.0
            if enable_delays:
                # Add random traffic/handling delay
                leg_delay_mins = random.uniform(*delay_range_mins)
                total_delay_minutes += leg_delay_mins

            # Leg travel time
            leg_travel_hours = leg_dist / speed_units_per_hour
            total_time_hours += leg_travel_hours + (leg_delay_mins / 60.0)

            routes.append({
                "package_id": pkg["id"],
                "warehouse_id": w_id,
                "warehouse_pos": w_pos,
                "destination_pos": d_pos,
                "dist_to_wh": dist_to_wh,
                "dist_to_dest": dist_to_dest,
                "leg_distance": leg_dist,
                "delay_minutes": leg_delay_mins,
            })

            # Update agent position
            current_pos = d_pos

        agent_results[aid] = {
            "packages_delivered": len(assigned_pkgs),
            "total_distance": total_distance,
            "total_time_hours": total_time_hours,
            "total_delay_minutes": total_delay_minutes,
            "routes": routes,
            "final_position": current_pos,
        }

    return agent_results


# =====================================================================
# Task 4 & 5: Generate Report and Save to report.json
# =====================================================================

def generate_report(agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates the final report matching the specification:
    {
      "A1": {"packages_delivered": 2, "total_distance": 85.32, "efficiency": 42.66},
      "A2": {"packages_delivered": 2, "total_distance": 120.12, "efficiency": 60.06},
      "A3": {"packages_delivered": 1, "total_distance": 50.00, "efficiency": 50.00},
      "best_agent": "A1"
    }

    Efficiency = total_distance / packages_delivered (lower distance per package is better).
    best_agent is the agent with minimum efficiency among those who delivered >= 1 package.
    """
    report: Dict[str, Any] = {}
    best_agent: Optional[str] = None
    best_efficiency: float = float("inf")

    for aid in sorted(agent_results.keys()):
        stats = agent_results[aid]
        delivered = stats["packages_delivered"]
        dist = stats["total_distance"]

        # Safe division handling
        efficiency = round(dist / delivered, 2) if delivered > 0 else 0.0

        report[aid] = {
            "packages_delivered": delivered,
            "total_distance": round(dist, 2),
            "efficiency": efficiency,
        }

        # Track best agent (lowest average distance per package delivered)
        if delivered > 0 and efficiency < best_efficiency:
            best_efficiency = efficiency
            best_agent = aid

    report["best_agent"] = best_agent
    return report


def save_report(report: Dict[str, Any], filepath: str = "report.json") -> None:
    """Saves report dictionary to formatted JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print(f"[OK] Report successfully saved to: {filepath}")


# =====================================================================
# Bonus Features
# =====================================================================

def export_to_csv(report: Dict[str, Any], filepath: str = "top_performer.csv") -> None:
    """
    Bonus: Exports performance summary and top performer to CSV.
    """
    best_agent = report.get("best_agent")
    fieldnames = ["Agent ID", "Packages Delivered", "Total Distance", "Efficiency (dist/pkg)", "Performance Rank", "Status"]

    # Rank agents that delivered packages
    ranked_agents = []
    for k, v in report.items():
        if k != "best_agent" and isinstance(v, dict):
            ranked_agents.append((k, v["packages_delivered"], v["total_distance"], v["efficiency"]))

    # Sort: delivered > 0 first, then by efficiency ascending
    ranked_agents.sort(key=lambda x: (x[1] == 0, x[3]))

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for rank, (aid, pkgs, dist, eff) in enumerate(ranked_agents, 1):
            status = "TOP PERFORMER *" if aid == best_agent else ("Active" if pkgs > 0 else "Idle")
            writer.writerow([aid, pkgs, f"{dist:.2f}", f"{eff:.2f}", rank if pkgs > 0 else "N/A", status])

    print(f"[OK] Top performer exported to CSV: {filepath}")


def simulate_midday_agent_joining(
    warehouses: Dict[str, Tuple[float, float]],
    agents: Dict[str, Tuple[float, float]],
    packages: List[Dict[str, Any]],
    new_agent_id: str = "A_NEW",
    new_agent_loc: Tuple[float, float] = (50.0, 50.0),
    packages_delivered_before_join: int = 3,
) -> Dict[str, Any]:
    """
    Bonus: Demonstrates dynamic handling when a new agent joins mid-day.
    
    1. First N packages are delivered by initial fleet.
    2. New agent joins at `new_agent_loc`.
    3. Remaining pending packages are re-evaluated and reassigned if new agent is closer.
    """
    print(f"\n--- Bonus Feature: Dynamic Mid-Day Agent Arrival ({new_agent_id}) ---")
    print(f"Trigger: After {packages_delivered_before_join} packages, {new_agent_id} joins at {new_agent_loc}")

    # Initial assignments
    initial_assignments = assign_packages(warehouses, agents, packages)
    print(f"Initial Fleet: {list(agents.keys())}")

    # Flatten package delivery order
    done_packages = packages[:packages_delivered_before_join]
    pending_packages = packages[packages_delivered_before_join:]

    # Updated fleet
    updated_agents = dict(agents)
    updated_agents[new_agent_id] = new_agent_loc

    # Reassign pending packages to updated fleet
    pending_assignments = assign_packages(warehouses, updated_agents, pending_packages)

    # Count packages reassigned to new agent
    reassigned_count = len(pending_assignments.get(new_agent_id, []))
    print(f"Pending packages reassigned to {new_agent_id}: {reassigned_count} package(s)")

    # Simulate combined operations
    final_assignments = {aid: [] for aid in updated_agents.keys()}
    # Initial packages delivered by original assignees
    for p in done_packages:
        for aid, pkgs in initial_assignments.items():
            if any(x["id"] == p["id"] for x in pkgs):
                final_assignments[aid].append(p)
                break
    # Add pending packages
    for aid, pkgs in pending_assignments.items():
        final_assignments[aid].extend(pkgs)

    results = simulate_deliveries(warehouses, updated_agents, final_assignments)
    midday_report = generate_report(results)
    return midday_report


# =====================================================================
# Main CLI Entry Point
# =====================================================================

def run_pipeline(
    input_file: str = "data.json",
    output_file: str = "report.json",
    csv_file: Optional[str] = "top_performer.csv",
    visualize: bool = False,
    enable_delays: bool = False,
    run_midday: bool = False,
) -> Dict[str, Any]:
    """
    Executes the entire end-to-end pipeline:
    Load -> Assign -> Simulate -> Report -> (Optional Bonus Extensions).
    """
    print("=" * 60)
    print("       FASTBOX LOGISTICS SIMULATION - STARTING RUN")
    print("=" * 60)
    print(f"Input Data File : {input_file}")
    print(f"Report Target   : {output_file}")

    # Task 1: Load Data
    warehouses, agents, packages = load_data(input_file)
    print(f"[OK] Data Loaded : {len(warehouses)} Warehouses, {len(agents)} Agents, {len(packages)} Packages")

    # Task 2: Assign Packages
    assignments = assign_packages(warehouses, agents, packages)
    print("[OK] Nearest-Agent Assignments:")
    for aid in sorted(assignments.keys()):
        p_ids = [p["id"] for p in assignments[aid]]
        print(f"    Agent {aid}: {len(p_ids)} packages -> {p_ids}")

    # Task 3: Simulate Deliveries
    results = simulate_deliveries(warehouses, agents, assignments, enable_delays=enable_delays, random_seed=42)
    print("[OK] Delivery Simulation Completed.")

    # Task 4 & 5: Generate and Save Report
    report = generate_report(results)
    save_report(report, output_file)

    # Print Report to Terminal
    print("\n" + "=" * 60)
    print("                 FINAL REPORT SUMMARY")
    print("=" * 60)
    print(json.dumps(report, indent=4))
    print(f"* Best Agent: {report['best_agent']} *")
    print("=" * 60)

    # Bonus 1: Delay details if enabled
    if enable_delays:
        print("\n[Bonus 1] Random Delivery Delays Summary:")
        for aid, data in results.items():
            print(f"  Agent {aid}: Total Delay = {data['total_delay_minutes']:.1f} mins | Total Time = {data['total_time_hours']:.2f} hrs")

    # Bonus 2: ASCII Visualization
    if visualize and render_ascii_map:
        print("\n[Bonus 2] ASCII Route Map Visualization:")
        print(render_ascii_map(warehouses, agents, packages))
        print("\nAgent Route Logs:")
        for aid in sorted(agents.keys()):
            print(render_route_summary(aid, agents[aid], results[aid]["routes"]))

    # Bonus 4: Export to CSV
    if csv_file:
        export_to_csv(report, csv_file)

    # Bonus 3: Dynamic mid-day agent arrival
    if run_midday:
        midday_report = simulate_midday_agent_joining(
            warehouses, agents, packages, new_agent_id="A_REINFORCE", new_agent_loc=(50, 50)
        )
        print("Mid-day Simulation Report:")
        print(json.dumps(midday_report, indent=4))

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastBox Mystery Delivery System Simulator")
    parser.add_argument("--data", default="data.json", help="Path to input JSON file")
    parser.add_argument("--report", default="report.json", help="Path to output report JSON file")
    parser.add_argument("--csv", default="top_performer.csv", help="Path to output CSV file")
    parser.add_argument("--visualize", action="store_true", help="Display ASCII map and route log")
    parser.add_argument("--delays", action="store_true", help="Simulate random traffic and delivery delays")
    parser.add_argument("--midday-agent", action="store_true", help="Demonstrate dynamic mid-day agent joining")
    parser.add_argument("--all-bonuses", action="store_true", help="Enable all bonus features")

    args = parser.parse_args()

    do_vis = args.visualize or args.all_bonuses
    do_delays = args.delays or args.all_bonuses
    do_midday = args.midday_agent or args.all_bonuses

    run_pipeline(
        input_file=args.data,
        output_file=args.report,
        csv_file=args.csv,
        visualize=do_vis,
        enable_delays=do_delays,
        run_midday=do_midday,
    )
