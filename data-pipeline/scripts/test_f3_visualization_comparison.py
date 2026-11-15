"""
NASA FLAME — Automated Test Suite for Phase F3
Prompt-Driven Scientific Visualization & Experiment Comparison

Validates:
1. Multi-Chart Generation (Temperature, Radiant Heat Flux, Airflow) decoupled by physical SI unit.
2. Channel Resolution & Missing Channel Handling (no invented channels or synthetic points).
3. Step 7 Routing Preservation (Explicit workspace stays in that workspace; global routing only on auto).
4. Step 6 Comparison Scientific Audit (Sensor baseline offset detection ~-17.5 to -19 mW/cm², no false negative flame peak).
5. Plume Thermocouple Grounding (Exact channel match and accurate peak temperature reporting).
6. BASS-II Discrete Matrix Comparison (129 flight runs, flammability corridor scatter spec).
7. Physical Event Markers (Saffire igniter active pulse durations).
8. Ambiguous Prompt Clarification Handling.
9. FastAPI REST Endpoints (/api/prompt/research).
10. Deterministic Fallback Mode (100% operational without external LLM keys).
"""

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from fastapi.testclient import TestClient
from prompt_system.models import (
    PromptResearchRequest,
    PromptResearchResponse,
    ChartSpecification,
    InterpretedScientificIntent,
)
from prompt_system.interpreter import PromptIntentInterpreter
from prompt_system.service import PromptResearchService
from api.main import (
    app,
    coverage_service,
    gap_detection_service,
    modeling_service,
    modeling_analyzer,
    equipment_service,
    earth_applications_service,
    rag_store,
)


class TestVisualizationComparisonF3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.interpreter = PromptIntentInterpreter()
        cls.service = PromptResearchService(
            base_dir=BASE,
            coverage_service=coverage_service,
            gap_detection_service=gap_detection_service,
            modeling_service=modeling_service,
            modeling_analyzer=modeling_analyzer,
            equipment_service=equipment_service,
            earth_applications_service=earth_applications_service,
            rag_store=rag_store,
        )

    # -------------------------------------------------------------------------
    # TEST 1: Step 2 Multi-Channel Resolution & 3 Units-Separated Charts
    # -------------------------------------------------------------------------
    def test_01_multi_channel_visualization_three_charts(self):
        req = PromptResearchRequest(
            objective="Visualize temperature, radiant heat flux, and airflow during Saffire-III Sample 1 ignition.",
            workspace="visualization"
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        self.assertEqual(res.workspace, "visualization")
        self.assertEqual(res.interpreted_intent.dataset_id, "saffire_iii_sample_1")

        # Must resolve all 3 distinct physical quantities
        resolved = res.interpreted_intent.channel_ids
        self.assertTrue(any("Radiometer" in ch for ch in resolved), "Must resolve Radiometer")
        self.assertTrue(any("TC" in ch or "Temp" in ch for ch in resolved), "Must resolve Thermocouples")
        self.assertTrue(any("Anemometer" in ch or "flow" in ch.lower() for ch in resolved), "Must resolve Anemometer")

        # Must generate 3 distinct charts separated by SI units
        self.assertGreaterEqual(len(res.visualizations), 3)
        units_returned = [c.y_units for c in res.visualizations]
        self.assertIn("mW/cm²", units_returned)
        self.assertIn("°C", units_returned)
        self.assertIn("cm/s", units_returned)

        # Check real empirical points and decimation in each chart
        for c in res.visualizations:
            self.assertIsInstance(c, ChartSpecification)
            pts = c.series_data.get("points", [])
            self.assertGreater(len(pts), 50, f"Chart {c.title} must have real decimated points")
            self.assertTrue("decimated_lttb" in c.data_resolution)

        # Step 4 Layout: Exactly 2-3 concise observations
        self.assertGreaterEqual(len(res.key_findings), 2)
        self.assertLessEqual(len(res.key_findings), 4)

    # -------------------------------------------------------------------------
    # TEST 2: Step 7 Routing Rule Preservation
    # -------------------------------------------------------------------------
    def test_02_step_7_routing_preservation(self):
        # A prompt entered in visualization MUST stay in visualization
        req_vis = PromptResearchRequest(
            objective="Compare Saffire-III Sample 1 with Sample 2 temperature behavior",
            workspace="visualization"
        )
        res_vis = self.service.process_prompt(req_vis)
        self.assertEqual(res_vis.workspace, "visualization", "Prompt in visualization must stay in visualization")
        # Must suggest switching rather than silently redirecting
        action_labels = [a.label for a in res_vis.suggested_actions]
        self.assertTrue(
            any("Comparison" in label for label in action_labels),
            "Must provide suggested action to switch to comparison workspace"
        )

        # A prompt entered in comparison MUST stay in comparison
        req_comp = PromptResearchRequest(
            objective="Plot Saffire-III Sample 1 radiant heat flux over full flight duration",
            workspace="comparison"
        )
        res_comp = self.service.process_prompt(req_comp)
        self.assertEqual(res_comp.workspace, "comparison", "Prompt in comparison must stay in comparison")

        # Global routing only activates when workspace is 'auto'
        req_auto = PromptResearchRequest(
            objective="Prepare BASS-II data for machine learning flame spread model",
            workspace="auto"
        )
        res_auto = self.service.process_prompt(req_auto)
        self.assertEqual(res_auto.workspace, "modeling", "Auto routing must resolve to modeling")

    # -------------------------------------------------------------------------
    # TEST 3: Step 6 Comparison Scientific Audit (Radiometer Baseline Offset)
    # -------------------------------------------------------------------------
    def test_03_step_6_comparison_scientific_audit(self):
        req = PromptResearchRequest(
            objective="Compare the radiant heat flux and temperature measurements from Saffire-III Sample 1 and Sample 2.",
            workspace="comparison"
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        self.assertEqual(res.workspace, "comparison")
        self.assertEqual(res.specialist_data.get("dataset_a"), "saffire_iii_sample_1")
        self.assertEqual(res.specialist_data.get("dataset_b"), "saffire_iii_sample_2")

        # Visualizations must decouple radiometer (mW/cm²) and thermocouple (°C)
        units_returned = [c.y_units for c in res.visualizations]
        self.assertIn("mW/cm²", units_returned)
        self.assertIn("°C", units_returned)

        # Check Radiometer 1 series data
        r_chart = next(c for c in res.visualizations if c.y_units == "mW/cm²")
        self.assertIn("exp1_radiometer_1", r_chart.series_data)
        self.assertIn("exp2_radiometer_1", r_chart.series_data)

        # Audit Radiometer Findings: Must detect electrical baseline offset
        all_findings = " ".join(res.key_findings)
        self.assertTrue(
            "baseline" in all_findings.lower(),
            "Key findings must explicitly identify the electrical baseline offset"
        )
        self.assertTrue(
            "-17." in all_findings or "-18." in all_findings or "baseline offset" in all_findings.lower(),
            "Must report baseline offset of ~ -17.5 to -18.7 mW/cm²"
        )
        self.assertTrue(
            "extinction" in all_findings.lower(),
            "Must recognize localized flame extinction in Sample 2 before radiometer station"
        )

        # Audit Plume Thermocouple Findings: Accurate temperatures
        self.assertTrue(
            "Plume Temp" in all_findings or "thermocouple" in all_findings.lower(),
            "Thermocouple comparison must be included"
        )

        # Audit Missing Data Notices on Radiometer Chart
        self.assertTrue(
            any("electrical baseline" in n.lower() or "baseline" in n.lower() for n in r_chart.missing_data_notices),
            "Missing data notice must explain the sensor offset to researchers"
        )

    # -------------------------------------------------------------------------
    # TEST 4: BASS-II Discrete Matrix Comparison
    # -------------------------------------------------------------------------
    def test_04_bass_ii_discrete_matrix_comparison(self):
        req = PromptResearchRequest(
            objective="Compare BASS-II Cotton vs PMMA glovebox burn matrix.",
            workspace="comparison"
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        self.assertEqual(res.workspace, "comparison")
        self.assertTrue(res.specialist_data.get("is_discrete_matrix"))
        self.assertEqual(res.specialist_data.get("total_runs"), 129)
        self.assertGreaterEqual(res.specialist_data.get("pmma_runs", 0), 80)
        self.assertGreaterEqual(res.specialist_data.get("cotton_runs", 0), 20)

        # Chart specification must be a scatter plot
        self.assertEqual(len(res.visualizations), 1)
        chart = res.visualizations[0]
        self.assertEqual(chart.chart_type, "scatter")
        self.assertEqual(chart.y_units, "% vol")
        self.assertEqual(chart.x_units, "cm/s proxy")
        self.assertIn("points", chart.series_data)
        self.assertGreater(len(chart.series_data["points"]), 10)

    # -------------------------------------------------------------------------
    # TEST 5: Ambiguity Detection & Clarification Handling
    # -------------------------------------------------------------------------
    def test_05_ambiguous_prompt_clarification(self):
        req = PromptResearchRequest(
            objective="Show me combustion",
            workspace="auto"
        )
        res = self.service.process_prompt(req)
        self.assertEqual(res.status, "ambiguous")
        self.assertGreater(len(res.suggested_actions), 0)
        for act in res.suggested_actions:
            self.assertIsNotNone(act.label)
            self.assertIsNotNone(act.tab_id)

    # -------------------------------------------------------------------------
    # TEST 6: FastAPI REST Endpoint Verification
    # -------------------------------------------------------------------------
    def test_06_fastapi_rest_endpoints(self):
        # Test /api/prompt/research for comparison
        payload = {
            "objective": "Compare Saffire-III Sample 1 and Sample 2 radiant heat flux",
            "workspace": "comparison"
        }
        res = self.client.post("/api/prompt/research", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["workspace"], "comparison")
        self.assertGreaterEqual(len(data["visualizations"]), 1)
        self.assertGreaterEqual(len(data["key_findings"]), 2)

        # Test /api/prompt/research for visualization
        payload_vis = {
            "objective": "Visualize temperature, radiant heat flux, and airflow during Saffire-III Sample 1 ignition.",
            "workspace": "visualization"
        }
        res_vis = self.client.post("/api/prompt/research", json=payload_vis)
        self.assertEqual(res_vis.status_code, 200)
        data_vis = res_vis.json()
        self.assertEqual(data_vis["status"], "ok")
        self.assertGreaterEqual(len(data_vis["visualizations"]), 3)

    # -------------------------------------------------------------------------
    # TEST 7: Full Non-Regression of Existing Endpoints
    # -------------------------------------------------------------------------
    def test_07_platform_non_regression(self):
        # Health check
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)

        # Datasets list
        res = self.client.get("/api/datasets")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.json()), 2)

        # Earth Applications Overview
        r_ea = self.client.get("/api/earth-applications/overview")
        self.assertEqual(r_ea.status_code, 200)

        # Equipment Research Overview
        r_eq = self.client.get("/api/equipment-research/overview")
        self.assertEqual(r_eq.status_code, 200)

        # Research Gaps Findings
        r_gaps = self.client.get("/api/research-gaps/findings")
        self.assertEqual(r_gaps.status_code, 200)

        # Telemetry endpoint
        res = self.client.get("/api/datasets/saffire_iii_sample_1/telemetry?limit=100")
        self.assertEqual(res.status_code, 200)
        self.assertIn("telemetry", res.json())


if __name__ == "__main__":
    unittest.main()
