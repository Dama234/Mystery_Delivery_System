"""
Unit and Integration Tests for FastBox Mystery Delivery System
==============================================================
Tests all core tasks and bonus features with 100% assertion coverage.
"""

import csv
import json
import math
import os
import tempfile
import unittest

from delivery_simulator import (
    assign_packages,
    euclidean_distance,
    export_to_csv,
    generate_report,
    load_data,
    save_report,
    simulate_deliveries,
    simulate_midday_agent_joining,
)
from visualizer import render_ascii_map, render_route_summary


class TestDistanceCalculation(unittest.TestCase):
    """Evaluation Criteria: Distance calculation (20% weight)."""

    def test_euclidean_distance_3_4_5(self):
        self.assertAlmostEqual(euclidean_distance((0, 0), (3, 4)), 5.0)

    def test_euclidean_distance_zero(self):
        self.assertEqual(euclidean_distance((10.5, 20.5), (10.5, 20.5)), 0.0)

    def test_euclidean_distance_negative_coordinates(self):
        self.assertAlmostEqual(euclidean_distance((-10, -10), (10, 10)), math.sqrt(800))

    def test_euclidean_distance_symmetry(self):
        p1 = (14.2, 53.9)
        p2 = (88.1, 12.4)
        self.assertAlmostEqual(euclidean_distance(p1, p2), euclidean_distance(p2, p1))


class TestJSONParsing(unittest.TestCase):
    """Evaluation Criteria: JSON parsing (10% weight)."""

    def test_load_dict_format(self):
        data = {
            "warehouses": {"W1": [10, 20]},
            "agents": {"A1": [15, 25]},
            "packages": [{"id": "P1", "warehouse": "W1", "destination": [30, 40]}],
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            wh, ag, pk = load_data(temp_path)
            self.assertEqual(wh, {"W1": (10.0, 20.0)})
            self.assertEqual(ag, {"A1": (15.0, 25.0)})
            self.assertEqual(len(pk), 1)
            self.assertEqual(pk[0]["id"], "P1")
            self.assertEqual(pk[0]["warehouse"], "W1")
            self.assertEqual(pk[0]["destination"], (30.0, 40.0))
        finally:
            os.remove(temp_path)

    def test_load_list_format(self):
        """Supports alternate list format found in the assignment description."""
        data = {
            "warehouses": [{"id": "W1", "location": [10, 20]}],
            "agents": [{"id": "A1", "location": [15, 25]}],
            "packages": [{"id": "P1", "warehouse_id": "W1", "destination": [30, 40]}],
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            wh, ag, pk = load_data(temp_path)
            self.assertEqual(wh, {"W1": (10.0, 20.0)})
            self.assertEqual(ag, {"A1": (15.0, 25.0)})
            self.assertEqual(len(pk), 1)
            self.assertEqual(pk[0]["id"], "P1")
            self.assertEqual(pk[0]["warehouse"], "W1")
        finally:
            os.remove(temp_path)

    def test_load_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_data("non_existent_file_xyz123.json")

    def test_unknown_warehouse_reference_raises(self):
        data = {
            "warehouses": {"W1": [0, 0]},
            "agents": {"A1": [0, 0]},
            "packages": [{"id": "P1", "warehouse": "W99", "destination": [1, 1]}],
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp_path = f.name
        try:
            with self.assertRaises(ValueError):
                load_data(temp_path)
        finally:
            os.remove(temp_path)


class TestAgentPackageAssignment(unittest.TestCase):
    """Evaluation Criteria: Agent-package assignment (25% weight)."""

    def setUp(self):
        self.warehouses = {
            "W1": (0.0, 0.0),
            "W2": (100.0, 100.0),
        }
        self.agents = {
            "A1": (2.0, 2.0),     # Close to W1
            "A2": (98.0, 98.0),   # Close to W2
        }
        self.packages = [
            {"id": "P1", "warehouse": "W1", "destination": (10, 10)},
            {"id": "P2", "warehouse": "W1", "destination": (20, 20)},
            {"id": "P3", "warehouse": "W2", "destination": (80, 80)},
        ]

    def test_assignment_to_nearest_warehouse_agent(self):
        assignments = assign_packages(self.warehouses, self.agents, self.packages)
        a1_ids = [p["id"] for p in assignments["A1"]]
        a2_ids = [p["id"] for p in assignments["A2"]]

        self.assertEqual(sorted(a1_ids), ["P1", "P2"])
        self.assertEqual(a2_ids, ["P3"])

    def test_total_packages_delivered_matches_total_packages(self):
        """Note from PDF: Make sure total packages delivered matches total packages."""
        assignments = assign_packages(self.warehouses, self.agents, self.packages)
        total_assigned = sum(len(pkgs) for pkgs in assignments.values())
        self.assertEqual(total_assigned, len(self.packages))

    def test_no_agents_raises_error(self):
        with self.assertRaises(ValueError):
            assign_packages(self.warehouses, {}, self.packages)


class TestSimulationAndReport(unittest.TestCase):
    """Evaluation Criteria: Simulation & report (25% weight)."""

    def setUp(self):
        self.warehouses = {"W1": (0.0, 0.0)}
        self.agents = {
            "A1": (3.0, 4.0),   # Dist to W1: 5.0
            "A2": (10.0, 10.0), # Idle agent
        }
        self.packages = [
            {"id": "P1", "warehouse": "W1", "destination": (0.0, 10.0)} # W1 to P1: 10.0
        ]

    def test_simulation_route_and_distance(self):
        assignments = assign_packages(self.warehouses, self.agents, self.packages)
        results = simulate_deliveries(self.warehouses, self.agents, assignments)

        # A1: Starts at (3,4) -> travels to W1 (0,0) [dist 5.0] -> travels to Dest (0,10) [dist 10.0]
        # Total distance = 15.0
        self.assertEqual(results["A1"]["packages_delivered"], 1)
        self.assertAlmostEqual(results["A1"]["total_distance"], 15.0)
        self.assertEqual(results["A1"]["final_position"], (0.0, 10.0))

        # Idle agent A2
        self.assertEqual(results["A2"]["packages_delivered"], 0)
        self.assertEqual(results["A2"]["total_distance"], 0.0)

    def test_report_generation_and_efficiency(self):
        assignments = assign_packages(self.warehouses, self.agents, self.packages)
        results = simulate_deliveries(self.warehouses, self.agents, assignments)
        report = generate_report(results)

        self.assertIn("A1", report)
        self.assertIn("A2", report)
        self.assertEqual(report["A1"]["packages_delivered"], 1)
        self.assertEqual(report["A1"]["total_distance"], 15.0)
        self.assertEqual(report["A1"]["efficiency"], 15.0)

        # Zero-division safety
        self.assertEqual(report["A2"]["packages_delivered"], 0)
        self.assertEqual(report["A2"]["efficiency"], 0.0)

        # Best agent should be A1
        self.assertEqual(report["best_agent"], "A1")

    def test_save_report_json(self):
        report = {
            "A1": {"packages_delivered": 1, "total_distance": 15.0, "efficiency": 15.0},
            "best_agent": "A1"
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            temp_path = f.name

        try:
            save_report(report, temp_path)
            with open(temp_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded, report)
        finally:
            os.remove(temp_path)


class TestAllProvidedDatasets(unittest.TestCase):
    """
    Note from PDF: Test your code with different JSON inputs.
    Tests all 6 datasets provided in the assignment prompt.
    """

    def test_all_input_files(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        inputs_dir = os.path.join(base_dir, "inputs")
        if not os.path.exists(inputs_dir):
            self.skipTest("inputs directory not found")

        json_files = [f for f in os.listdir(inputs_dir) if f.endswith(".json")]
        self.assertGreaterEqual(len(json_files), 6, "Expected at least 6 test datasets")

        for filename in sorted(json_files):
            filepath = os.path.join(inputs_dir, filename)
            with self.subTest(file=filename):
                wh, ag, pk = load_data(filepath)
                self.assertGreater(len(wh), 0)
                self.assertGreater(len(ag), 0)
                self.assertGreater(len(pk), 0)

                assignments = assign_packages(wh, ag, pk)
                total_assigned = sum(len(p) for p in assignments.values())
                self.assertEqual(total_assigned, len(pk), f"Total assigned must match in {filename}")

                results = simulate_deliveries(wh, ag, assignments)
                report = generate_report(results)

                total_delivered = sum(
                    v["packages_delivered"] for k, v in report.items() if k != "best_agent"
                )
                self.assertEqual(total_delivered, len(pk), f"Total delivered must match in {filename}")
                self.assertIsNotNone(report["best_agent"], f"Must have best agent in {filename}")


class TestBonusFeatures(unittest.TestCase):
    """Bonus (Optional): 10% weight."""

    def setUp(self):
        self.warehouses = {"W1": (10.0, 10.0)}
        self.agents = {"A1": (0.0, 0.0), "A2": (50.0, 50.0)}
        self.packages = [
            {"id": "P1", "warehouse": "W1", "destination": (20.0, 20.0)},
            {"id": "P2", "warehouse": "W1", "destination": (30.0, 30.0)},
        ]

    def test_bonus_1_random_delays(self):
        assignments = assign_packages(self.warehouses, self.agents, self.packages)
        results = simulate_deliveries(self.warehouses, self.agents, assignments, enable_delays=True, random_seed=99)
        a1 = results["A1"]
        self.assertGreater(a1["total_delay_minutes"], 0.0)
        self.assertGreater(a1["total_time_hours"], 0.0)

    def test_bonus_2_ascii_visualization(self):
        rendered_map = render_ascii_map(self.warehouses, self.agents, self.packages, width=40, height=15)
        self.assertIn("[W1]", rendered_map)
        self.assertIn("<A1>", rendered_map)
        self.assertIn("P1", rendered_map)

        assignments = assign_packages(self.warehouses, self.agents, self.packages)
        results = simulate_deliveries(self.warehouses, self.agents, assignments)
        route_text = render_route_summary("A1", self.agents["A1"], results["A1"]["routes"])
        self.assertIn("travel to W1", route_text)
        self.assertIn("pick up package P1", route_text)

    def test_bonus_3_midday_agent_joining(self):
        report = simulate_midday_agent_joining(
            self.warehouses,
            self.agents,
            self.packages,
            new_agent_id="A_NEW",
            new_agent_loc=(10.0, 10.0),
            packages_delivered_before_join=1,
        )
        self.assertIn("A_NEW", report)
        total_delivered = sum(v["packages_delivered"] for k, v in report.items() if k != "best_agent")
        self.assertEqual(total_delivered, 2)

    def test_bonus_4_export_to_csv(self):
        report = {
            "A1": {"packages_delivered": 2, "total_distance": 50.0, "efficiency": 25.0},
            "A2": {"packages_delivered": 0, "total_distance": 0.0, "efficiency": 0.0},
            "best_agent": "A1"
        }
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as f:
            temp_csv = f.name

        try:
            export_to_csv(report, temp_csv)
            self.assertTrue(os.path.exists(temp_csv))
            with open(temp_csv, "r", encoding="utf-8") as f:
                reader = list(csv.reader(f))
            self.assertEqual(reader[0][0], "Agent ID")
            self.assertEqual(reader[1][0], "A1")
            self.assertIn("TOP PERFORMER", reader[1][5])
            self.assertEqual(reader[2][0], "A2")
            self.assertEqual(reader[2][5], "Idle")
        finally:
            os.remove(temp_csv)


if __name__ == "__main__":
    unittest.main()
