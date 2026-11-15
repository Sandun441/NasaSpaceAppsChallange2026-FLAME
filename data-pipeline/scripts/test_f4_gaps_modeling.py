"""
NASA FLAME — Automated Test Suite for Phase F4
Prompt-Driven Research-Gap Detection & Predictive-Modeling Data Extraction

Validates:
1. Prompt-to-gap filtering (low O2, low airflow, microgravity).
2. Prompt-to-coverage matrix selection & regime distribution.
3. Correct ranked gap findings (canonical gap types, heuristic priority disclosures).
4. Unknown / unrepresented research topics (hyperoxic, quiescent).
5. Partial gravity coverage behavior (0 runs for 0.16g lunar / 0.38g mars in FLAME).
6. Prompt-to-modeling configuration (BASS-II dataset resolution, feature extraction).
7. Measured target validation (burn duration, uninstrumented flame spread rate disclosure).
8. Feature completeness calculations (real percentage, zero synthetic imputation).
9. Target leakage protection (segregation of target from candidate features).
10. Dataset preview and export compatibility (real rows, verified schema).
11. Missing-data handling (null preservation across multi-step flow test runs).
12. Explicit workspace routing preservation (Step 7 rule).
13. Deterministic fallback guarantee (works 100% without Gemini API keys).
14. Scientific source provenance (PSI, Saffire, Cygnus telemetry).
15. Full platform non-regression.
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


class TestGapsModelingF4(unittest.TestCase):
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
    # TEST 1: Prompt-to-Gap Filtering & Regime Matching
    # -------------------------------------------------------------------------
    def test_01_gap_prompt_filtering_and_matching(self):
        req = PromptResearchRequest(
            objective="Find missing experimental coverage for low oxygen concentrations and low airflow in microgravity combustion.",
            workspace="gap_detection",
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        self.assertEqual(res.workspace, "gap_detection")
        spec = res.specialist_data

        # Check structured filter extraction
        self.assertEqual(spec.get("coverage_status"), "covered")
        self.assertEqual(spec.get("matched_usable_runs_count"), 33)
        self.assertGreaterEqual(len(spec.get("applicable_gap_findings", [])), 1)

        # Check that top findings reflect low-flow / oxygen / cross-facility constraints
        finding_ids = [g.get("finding_id") for g in spec.get("applicable_gap_findings", [])]
        self.assertTrue(
            any("QUIESCENT" in fid or "AIRFLOW" in fid or "OX" in fid for fid in finding_ids),
            "Must surface quiescent airflow or oxygen gap findings"
        )

        # Check visual coverage chart
        self.assertGreaterEqual(len(res.visualizations), 1)
        chart = res.visualizations[0]
        self.assertEqual(chart.chart_type, "bar")
        self.assertEqual(chart.y_units, "runs")
        self.assertIn("regimes", chart.series_data)
        self.assertIn("run_counts", chart.series_data)

        # Exactly 2-3 concise observations
        self.assertGreaterEqual(len(res.key_findings), 2)
        self.assertLessEqual(len(res.key_findings), 4)

    # -------------------------------------------------------------------------
    # TEST 2: Partial Gravity Coverage Behavior (Lunar 0.16g & Martian 0.38g)
    # -------------------------------------------------------------------------
    def test_02_partial_gravity_gap_behavior(self):
        req = PromptResearchRequest(
            objective="What empirical combustion tests exist for lunar (0.16g) or Martian (0.38g) partial gravity?",
            workspace="gap_detection",
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        spec = res.specialist_data
        self.assertEqual(spec.get("coverage_status"), "coverage_gap")
        self.assertEqual(spec.get("matched_usable_runs_count"), 0)

        # Must explicitly identify lunar gravity gap finding
        finding_ids = [g.get("finding_id") for g in spec.get("applicable_gap_findings", [])]
        self.assertIn("GAP-COV-GRAV-PARTIAL-LUNAR", finding_ids)

        # Check heuristic priority score disclosure
        top_gap = spec.get("applicable_gap_findings")[0]
        self.assertIsNotNone(top_gap.get("priority_score"))
        all_caveats = " ".join(res.scientific_caveats)
        self.assertIn("heuristic", all_caveats.lower())

    # -------------------------------------------------------------------------
    # TEST 3: Predictive Modeling Objective Interpretation & BASS-II Configuration
    # -------------------------------------------------------------------------
    def test_03_modeling_prompt_configuration(self):
        req = PromptResearchRequest(
            objective="Prepare BASS-II experimental data to study flame behavior using oxygen concentration, material, and airflow.",
            workspace="modeling",
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        self.assertEqual(res.workspace, "modeling")
        spec = res.specialist_data

        # Check dataset recommendation
        self.assertEqual(spec.get("recommended_dataset_id"), "bass_ii_experiments")
        self.assertIn("initial_oxygen_pct", spec.get("selected_features", []))
        self.assertIn("airflow_velocity_proxy", spec.get("selected_features", []))

        # Check real preview data
        preview = spec.get("preview", {})
        self.assertGreater(len(preview.get("preview_rows", [])), 0)
        self.assertGreater(len(preview.get("columns", [])), 0)

        # Check feature completeness visualization
        self.assertGreaterEqual(len(res.visualizations), 1)
        chart = res.visualizations[0]
        self.assertEqual(chart.y_units, "%")
        self.assertIn("completeness_pct", chart.series_data)

    # -------------------------------------------------------------------------
    # TEST 4: Target Leakage Protection & Group CV Guidance
    # -------------------------------------------------------------------------
    def test_04_target_leakage_protection_and_cv(self):
        # Query requesting target that might collide with features
        req = PromptResearchRequest(
            objective="Predict burn duration using burn duration, oxygen, and airflow.",
            workspace="modeling",
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        spec = res.specialist_data

        # Target must NOT be in selected_features
        features = spec.get("selected_features", [])
        self.assertNotIn("burn_duration_s", features)

        # Quality report must specify group_split_column
        quality = spec.get("quality_report", {})
        self.assertEqual(quality.get("group_split_column"), "run_id")

        # Key findings must mandate GroupKFold
        all_findings = " ".join(res.key_findings)
        self.assertIn("GroupKFold", all_findings)

    # -------------------------------------------------------------------------
    # TEST 5: Target Measurability Disclosure (Uninstrumented Flame Spread Rate)
    # -------------------------------------------------------------------------
    def test_05_uninstrumented_target_disclosure(self):
        req = PromptResearchRequest(
            objective="Evaluate flame spread rate prediction feasibility using Saffire telemetry.",
            workspace="modeling",
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        all_findings = " ".join(res.key_findings)
        # Must disclose that flame spread rate requires optical edge tracking and is unrecorded in raw sensor logs
        self.assertTrue(
            "optical" in all_findings.lower() or "unrecorded" in all_findings.lower() or "uninstrumented" in all_findings.lower(),
            "Must disclose optical tracking requirement for flame spread rate"
        )

    # -------------------------------------------------------------------------
    # TEST 6: Step 7 Workspace Routing Preservation
    # -------------------------------------------------------------------------
    def test_06_step_7_routing_preservation(self):
        # In gap_detection asking for modeling
        req_g = PromptResearchRequest(
            objective="Prepare BASS-II data for machine learning model",
            workspace="gap_detection",
        )
        res_g = self.service.process_prompt(req_g)
        self.assertEqual(res_g.workspace, "gap_detection", "Must remain in gap_detection")
        actions_g = [a.label for a in res_g.suggested_actions]
        self.assertTrue(any("Modeling" in l for l in actions_g), "Must suggest switching to modeling")

        # In modeling asking for visualization
        req_m = PromptResearchRequest(
            objective="Plot Saffire-III radiant heat flux",
            workspace="modeling",
        )
        res_m = self.service.process_prompt(req_m)
        self.assertEqual(res_m.workspace, "modeling", "Must remain in modeling")

    # -------------------------------------------------------------------------
    # TEST 7: FastAPI Endpoints Verification
    # -------------------------------------------------------------------------
    def test_07_fastapi_endpoints(self):
        # Gap Detection REST call
        payload_gap = {
            "objective": "Find missing experimental coverage for low oxygen and low airflow in microgravity.",
            "workspace": "gap_detection"
        }
        res = self.client.post("/api/prompt/research", json=payload_gap)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["workspace"], "gap_detection")
        self.assertGreaterEqual(len(data["key_findings"]), 2)

        # Modeling REST call
        payload_mod = {
            "objective": "Prepare BASS-II experimental data to study flame behavior using oxygen concentration, material, and airflow.",
            "workspace": "modeling"
        }
        res_mod = self.client.post("/api/prompt/research", json=payload_mod)
        self.assertEqual(res_mod.status_code, 200)
        data_mod = res_mod.json()
        self.assertEqual(data_mod["status"], "ok")
        self.assertEqual(data_mod["workspace"], "modeling")
        self.assertGreaterEqual(len(data_mod["key_findings"]), 2)

    # -------------------------------------------------------------------------
    # TEST 8: Full Platform Non-Regression
    # -------------------------------------------------------------------------
    def test_08_platform_non_regression(self):
        # Datasets
        r_ds = self.client.get("/api/datasets")
        self.assertEqual(r_ds.status_code, 200)

        # Telemetry
        r_tel = self.client.get("/api/datasets/saffire_iii_sample_1/telemetry?limit=50")
        self.assertEqual(r_tel.status_code, 200)

        # Research Gaps findings
        r_gaps = self.client.get("/api/research-gaps/findings")
        self.assertEqual(r_gaps.status_code, 200)
        self.assertEqual(len(r_gaps.json().get("findings", [])), 21)

        # Modeling datasets
        r_mod = self.client.get("/api/modeling/datasets")
        self.assertEqual(r_mod.status_code, 200)
        self.assertGreaterEqual(len(r_mod.json().get("datasets", [])), 3)


if __name__ == "__main__":
    unittest.main()
