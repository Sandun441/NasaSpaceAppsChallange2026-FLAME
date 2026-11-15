#!/usr/bin/env python3
"""
NASA FLAME — Earth Applications Phase EA4 End-to-End Test Suite
Tests all 10 Researcher Journeys (A through J), critical physics (Richardson number),
Saffire threshold validation, standards qualification, and RAG fallback reliability.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import json

from api.main import app, rag_synthesizer
from earth_applications.service import EarthApplicationsService
from rag.earth_adapter import EarthApplicationsRAGAdapter
from rag.llm import GroundedAnswerSynthesizer, GeminiProvider


class TestEarthApplicationsEA4EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.service = EarthApplicationsService()
        cls.adapter = EarthApplicationsRAGAdapter()
        cls.llm = GroundedAnswerSynthesizer()

        cls.orig_llm = rag_synthesizer.llm_provider
        mock_llm = GeminiProvider(api_key="mock_key")
        def mock_generate(system_instruction, user_prompt):
            q_line = ""
            for line in user_prompt.splitlines():
                if any(line.startswith(prefix) for prefix in ("RESEARCH QUESTION:", "USER INQUIRY:", "Researcher:", "QUESTION:")):
                    q_line += " " + line
            target_text = (q_line if q_line.strip() else user_prompt).lower()

            if "unknown" in target_text:
                return {
                    "success": True,
                    "raw_text": json.dumps({
                        "answer": "Insufficient Evidence in Audited Earth Applications Catalog. The requested evidence ID is not present.",
                        "citation_record_ids": [],
                        "evidence_backed_claims": [],
                        "scientific_limitations": ["Unknown evidence ID"]
                    }),
                    "status_code": 200,
                    "model": "gemini-3.5-flash-lite",
                    "retries_attempted": 0,
                }
            if "commercial" in target_text:
                return {
                    "success": True,
                    "raw_text": json.dumps({
                        "answer": "There are 0 documented commercial applications in the catalog.",
                        "citation_record_ids": [],
                        "evidence_backed_claims": [],
                        "scientific_limitations": []
                    }),
                    "status_code": 200,
                    "model": "gemini-3.5-flash-lite",
                    "retries_attempted": 0,
                }
            return {
                "success": True,
                "raw_text": json.dumps({
                    "answer": "Observations in EA-EV-BASS-PYRO-01 from 129 flight burns support polymer pyrolysis modeling [EA-EV-BASS-PYRO-01].",
                    "citation_record_ids": ["EA-EV-BASS-PYRO-01"],
                    "evidence_backed_claims": ["BASS-II tested 129 burns [EA-EV-BASS-PYRO-01]"],
                    "scientific_limitations": []
                }),
                "status_code": 200,
                "model": "gemini-3.5-flash-lite",
                "retries_attempted": 0,
            }
        mock_llm.generate = MagicMock(side_effect=mock_generate)
        rag_synthesizer.llm_provider = mock_llm

    @classmethod
    def tearDownClass(cls):
        rag_synthesizer.llm_provider = cls.orig_llm

    # =========================================================================
    # RESEARCHER JOURNEYS (A through J)
    # =========================================================================

    def test_journey_a_category_selection_and_evidence_inspection(self):
        """Journey A: Open Earth Applications -> select a category -> inspect evidence."""
        # 1. Fetch categories
        res_cat = self.client.get("/api/earth-applications/categories")
        self.assertEqual(res_cat.status_code, 200)
        categories = res_cat.json().get("categories", [])
        self.assertEqual(len(categories), 7)

        # 2. Select category 'building_fire_safety'
        cat_id = "building_fire_safety"
        res_filtered = self.client.get(f"/api/earth-applications?category={cat_id}")
        self.assertEqual(res_filtered.status_code, 200)
        evidence_list = res_filtered.json().get("evidence", [])
        self.assertGreaterEqual(len(evidence_list), 1)
        for ev in evidence_list:
            self.assertEqual(ev["category_id"], cat_id)

        # 3. Inspect single evidence
        ev_id = evidence_list[0]["id"]
        res_single = self.client.get(f"/api/earth-applications/{ev_id}")
        self.assertEqual(res_single.status_code, 200)
        ev_data = res_single.json().get("evidence", {})
        self.assertEqual(ev_data["id"], ev_id)
        self.assertIn("scientific_finding", ev_data)
        self.assertIn("proposed_terrestrial_relevance", ev_data)
        self.assertIn("confidence_rubric", ev_data)

    def test_journey_b_saffire_iii_filter_and_visualizer_navigation(self):
        """Journey B: Filter by Saffire-III -> inspect an evidence record -> open Scientific Visualization."""
        res = self.client.get("/api/earth-applications?investigation_id=saffire_iii")
        self.assertEqual(res.status_code, 200)
        records = res.json().get("evidence", [])
        self.assertGreaterEqual(len(records), 1)

        # Pick EA-EV-SAFFIRE-DET-02
        target = next((r for r in records if r["id"] == "EA-EV-SAFFIRE-DET-02"), records[0])
        self.assertEqual(target["investigation_id"], "saffire_iii")

        # Verify cross-module destination payload for scientific visualization
        self.assertEqual(target["investigation_id"], "saffire_iii")
        self.assertIn("saffire_iii_sample_1.csv", target["dataset_or_measurement_reference"])

        # Check telemetry file exists locally
        telemetry_path = PROJECT_ROOT / "processed_data" / "saffire" / "saffire_iii_sample_1.csv"
        self.assertTrue(telemetry_path.exists(), "Telemetry file saffire_iii_sample_1.csv must exist locally")

    def test_journey_c_bass_ii_filter_and_predictive_modeling_navigation(self):
        """Journey C: Filter BASS-II -> inspect research -> open Predictive Modeling."""
        res = self.client.get("/api/earth-applications?investigation_id=bass_ii")
        self.assertEqual(res.status_code, 200)
        records = res.json().get("evidence", [])
        self.assertGreaterEqual(len(records), 2)

        pyro_record = next(r for r in records if r["id"] == "EA-EV-BASS-PYRO-01")
        self.assertEqual(pyro_record["investigation_id"], "bass_ii")
        self.assertIn("bass_ii_experiments.csv", pyro_record["dataset_or_measurement_reference"])

        # Check BASS-II data file exists locally
        bass_path = PROJECT_ROOT / "processed_data" / "bass_ii_experiments.csv"
        self.assertTrue(bass_path.exists(), "BASS-II data file must exist locally")

    def test_journey_d_wildfire_exploratory_hypothesis_and_limitations(self):
        """Journey D: Open wildfire research -> verify exploratory hypothesis classification and limitations."""
        res = self.client.get("/api/earth-applications/EA-EV-SAFFIRE-WILD-03")
        self.assertEqual(res.status_code, 200)
        ev = res.json().get("evidence", {})

        # Strict classification check
        self.assertEqual(ev["evidence_classification"], "exploratory_hypothesis")
        self.assertNotEqual(ev["evidence_classification"], "supported_research_implication")
        self.assertNotEqual(ev["evidence_classification"], "documented_application")

        # Check that transfer limitations explicitly note porous duff vs open crown difference
        self.assertIn("forest duff", ev["proposed_terrestrial_relevance"].lower())
        self.assertIn("buoyant", ev["earth_transfer_limitations"].lower())

    def test_journey_e_evidence_detail_ask_ai_and_return_navigation(self):
        """Journey E: Open an evidence detail -> Ask AI -> receive grounded answer -> return to original evidence."""
        # 1. Ask RAG about EA-EV-BASS-PYRO-01
        rag_res = self.client.post("/api/rag/ask", json={
            "question": "What empirical observations in EA-EV-BASS-PYRO-01 support polymer pyrolysis modeling?",
            "evidence_id": "EA-EV-BASS-PYRO-01",
        })
        self.assertEqual(rag_res.status_code, 200)
        data = rag_res.json()

        citation_ids = [c["record_id"] for c in data.get("evidence_citations", [])]
        self.assertIn("EA-EV-BASS-PYRO-01", citation_ids)
        self.assertIn("EA-EV-BASS-PYRO-01", data["answer"])
        self.assertIn("129", data["answer"])
        self.assertEqual(data.get("evidence_sufficiency"), "sufficient")

        # 2. Verify navigation action contract: frontend can navigate back via suggested_actions
        actions = data.get("suggested_actions", [])
        earth_actions = [a for a in actions if a.get("tab_id") == "earth-applications"]
        self.assertGreaterEqual(len(earth_actions), 1)

    def test_journey_f_commercial_adoption_query_catalog_transparency(self):
        """Journey F: Ask about commercial adoption -> receive 0 documented applications IN CURRENT CATALOG."""
        rag_res = self.client.post("/api/rag/ask", json={
            "question": "Has any NASA microgravity combustion finding been commercially adopted in building systems?",
        })
        self.assertEqual(rag_res.status_code, 200)
        data = rag_res.json()
        ans = data["answer"]

        # Assert explicit disclosure of zero documented commercial adoptions in catalog
        self.assertIn("0 documented", ans)
        self.assertIn("catalog", ans.lower())
        # Assert no claim of worldwide negative
        self.assertNotIn("no technology exists in the universe", ans.lower())

    def test_journey_g_unknown_evidence_id_insufficient_evidence(self):
        """Journey G: Ask about unknown evidence ID -> receive insufficient evidence without unrelated fallback."""
        # 1. Direct GET returns 404
        res_404 = self.client.get("/api/earth-applications/EA-EV-UNKNOWN-99")
        self.assertEqual(res_404.status_code, 404)

        # 2. RAG query returns clean insufficient evidence
        rag_res = self.client.post("/api/rag/ask", json={
            "question": "What are the terrestrial findings for EA-EV-UNKNOWN-99?",
        })
        self.assertEqual(rag_res.status_code, 200)
        data = rag_res.json()

        self.assertEqual(data.get("evidence_sufficiency"), "insufficient")
        self.assertIn(data.get("status"), ("insufficient_evidence", "earth_application_insufficient_evidence"))
        self.assertEqual(data.get("evidence_citations", []), [])
        self.assertIn("Insufficient Evidence", data["answer"])
        self.assertNotIn("### 1. Direct Scientific Answer", data["answer"])

    def test_journey_h_search_reset_and_pagination(self):
        """Journey H: Search, reset filters, and pagination."""
        # Pagination test (limit=2)
        res_paged = self.client.get("/api/earth-applications?limit=2&offset=0")
        self.assertEqual(res_paged.status_code, 200)
        paged_data = res_paged.json()
        self.assertEqual(len(paged_data["evidence"]), 2)
        self.assertEqual(paged_data["total_count"], 11)

        # Reset/all
        res_all = self.client.get("/api/earth-applications")
        self.assertEqual(res_all.status_code, 200)
        self.assertEqual(res_all.json()["total_count"], 11)

    def test_journey_i_backend_error_boundaries(self):
        """Journey I: Backend error boundaries (invalid category or investigation returns structured 404 or empty)."""
        # Non-existent category returns empty list (clean filter)
        res_bad_cat = self.client.get("/api/earth-applications?category=non_existent_category_xyz")
        self.assertEqual(res_bad_cat.status_code, 200)
        self.assertEqual(len(res_bad_cat.json()["evidence"]), 0)

        # Non-existent investigation detail endpoint returns 404
        res_bad_inv = self.client.get("/api/earth-applications/investigations/unknown_mission_xyz")
        self.assertEqual(res_bad_inv.status_code, 404)

    def test_journey_j_retrieval_only_offline_mode(self):
        """Journey J: Verify operation when Gemini is unavailable (retrieval-only fallback mode with full provenance)."""
        # Force offline/retrieval-only via synthesizer
        evidence = [self.adapter.service.get_evidence_by_id("EA-EV-SAFFIRE-DUCT-01").model_dump()]
        response = self.llm._generate_earth_application_synthesis(
            question="Explain the duct fire spread mechanism and transfer caveats.",
            earth_items=evidence,
            retrieved_candidates=[],
            reason="Simulated Gemini offline fallback test"
        )
        self.assertIn("answer", response)
        self.assertIn("### 1. Direct Scientific Answer", response["answer"])
        self.assertIn("### 4. Underlying Physical Mechanisms (Decoupled Buoyancy & Transport)", response["answer"])
        self.assertIn("### 6. Gravity, Buoyancy, and Scale-Transfer Limitations", response["answer"])
        self.assertIn("EA-EV-SAFFIRE-DUCT-01", response["citation_record_ids"])

    # =========================================================================
    # CRITICAL PHYSICS & RICHARDSON NUMBER VERIFICATION
    # =========================================================================

    def test_critical_physics_richardson_number_not_unconditionally_large(self):
        """Verify that 1g is not claimed to always imply Ri >> 1, correctly distinguishing forced vs buoyant flow."""
        evidence = [self.adapter.service.get_evidence_by_id("EA-EV-SAFFIRE-DUCT-01").model_dump()]
        resp = self.llm._generate_earth_application_synthesis(
            question="What is the Richardson number regime in normal gravity vs microgravity?",
            earth_items=evidence,
            retrieved_candidates=[],
            reason="Physics check test"
        )
        ans = resp["answer"]

        # Must mention Richardson number and ratio
        self.assertIn("Richardson number", ans)
        self.assertIn("Ri = Gr / Re^2", ans)

        # Must NOT claim 'In normal gravity (1g), Ri >> 1' unconditionally
        self.assertNotIn("In normal gravity (1g), Ri >> 1", ans)
        self.assertNotIn("In normal gravity ($1g$), $Ri \\gg 1$, and buoyant velocity", ans)

        # Must explicitly acknowledge that forced inertia can dominate (Ri << 1) even in normal gravity
        self.assertIn("Ri \\ll 1", ans)
        self.assertIn("forced", ans.lower())

    # =========================================================================
    # CRITICAL SAFFIRE THRESHOLD VERIFICATION
    # =========================================================================

    def test_critical_saffire_threshold_reproducibility(self):
        """Verify exact Saffire threshold calculation and experimental ignition context."""
        ev = self.service.get_evidence_by_id("EA-EV-SAFFIRE-DET-02")
        excerpt = ev.supporting_excerpt

        # Check explicit threshold numbers
        self.assertIn("66.56s", excerpt)
        self.assertIn("167.87 mW/cm²", excerpt)
        self.assertIn("-17.48 mW/cm² baseline", excerpt)
        self.assertIn("zero-crossing at t=66.89s", excerpt)
        self.assertIn("1.65s", excerpt)
        self.assertIn("6.60s", excerpt)
        self.assertIn("43.23s", excerpt)

        # Check explicit experimental ignition qualification vs building fire alarm
        self.assertIn("active igniter current pulse", excerpt)
        self.assertIn("not certified building fire-alarm detector response", excerpt)

        # Check rubric qualification
        self.assertIn("UL 268 / UL 217", ev.confidence_rubric)

    # =========================================================================
    # SCIENTIFIC STANDARDS QUALIFICATION CHECK
    # =========================================================================

    def test_scientific_standards_presented_as_validation_frameworks(self):
        """Verify standards (ASTM, UL, NFPA, ISO) are presented as validation frameworks, not automatic approvals."""
        all_records = self.service._catalog
        for ev in all_records:
            # Check NFPA 90A is not claimed as already satisfied
            if "NFPA 90A" in ev.earth_transfer_limitations:
                self.assertIn("frameworks", ev.earth_transfer_limitations)

            # Check UL 94 / ASTM are not claimed as granted
            if "UL 94" in ev.earth_transfer_limitations:
                self.assertNotIn("certified to UL 94", ev.earth_transfer_limitations)


if __name__ == "__main__":
    unittest.main()
