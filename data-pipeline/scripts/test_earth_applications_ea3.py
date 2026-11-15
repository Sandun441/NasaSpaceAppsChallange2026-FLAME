"""
NASA FLAME — Automated Test Suite for Earth Applications Phase EA3
Tests:
1. Earth Application Inquiry Detection & Deterministic Resolution
2. 9-Section Grounded Scientific Synthesis in Fallback Mode (No Gemini API Key)
3. Specific Domain Inquiries: BASS-II, Saffire-III, SAME, Documented Adoption, Transfer Physics
4. Strict Adoption Accounting (0 documented, 10 supported, 1 exploratory)
5. Citation Whitelisting & Citation Card Structuring ([EA-EV-...])
6. Claim Validation & Anti-Hallucination Defenses (43s lead time, 15-20% efficiency, commercial deployment)
7. Dedicated Endpoint: GET /api/earth-applications/{id}/investigate
8. Full API integration via POST /api/rag/ask with evidence_id and earth_category
9. Non-regression of existing RAG and gap-investigation workflows
"""

import sys
from pathlib import Path
import os
import unittest

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from fastapi.testclient import TestClient
from api.main import app
from rag.earth_adapter import EarthApplicationsRAGAdapter
from rag.llm import GroundedAnswerSynthesizer
from earth_applications.catalog import INITIAL_EARTH_APPLICATION_CATALOG


class TestEarthApplicationsEA3(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.adapter = EarthApplicationsRAGAdapter()
        cls.synthesizer = GroundedAnswerSynthesizer()

    def test_01_inquiry_detection_positive(self):
        """Verifies natural-language terrestrial inquiry detection."""
        test_queries = [
            "How does BASS-II research inform terrestrial industrial furnace efficiency?",
            "What wildfire smoldering insights can be drawn from Saffire experiments?",
            "Are there Earth building fire safety applications from Cygnus smoke detection?",
            "Can microgravity soot research improve terrestrial mine ventilation safety?",
            "What are the physical transfer limitations between microgravity and 1g buoyancy?",
            "Has any NASA combustion finding been commercially adopted in industry?",
            "Investigate EA-EV-BASS-PYRO-01",
        ]
        for q in test_queries:
            self.assertTrue(
                self.adapter.is_earth_application_inquiry(q),
                f"Query should be recognized as Earth application inquiry: '{q}'"
            )

    def test_02_inquiry_detection_with_explicit_params(self):
        """Verifies inquiry detection when explicit evidence_id or earth_category is supplied."""
        self.assertTrue(self.adapter.is_earth_application_inquiry("General inquiry", evidence_id="EA-EV-BASS-PYRO-01"))
        self.assertTrue(self.adapter.is_earth_application_inquiry("General inquiry", earth_category="wildfire_combustion"))

    def test_03_inquiry_detection_negative(self):
        """Verifies pure spaceflight queries without terrestrial keywords are not misidentified."""
        pure_space_queries = [
            "What was the igniter voltage for Saffire-III Sample 1?",
            "List thermocouple readings during Cygnus reentry",
        ]
        for q in pure_space_queries:
            self.assertFalse(
                self.adapter.is_earth_application_inquiry(q),
                f"Pure space inquiry should not be identified as Earth application: '{q}'"
            )

    def test_04_evidence_resolution_by_id(self):
        """Verifies deterministic evidence resolution by exact ID."""
        records = self.adapter.resolve_earth_evidence("Inquiry", evidence_id="EA-EV-BASS-PYRO-01")
        self.assertGreaterEqual(len(records), 1)
        self.assertEqual(records[0]["id"], "EA-EV-BASS-PYRO-01")
        self.assertEqual(records[0]["investigation_id"], "bass_ii")

    def test_05_evidence_resolution_by_investigation(self):
        """Verifies deterministic evidence resolution by NASA investigation identifier."""
        saffire_records = self.adapter.resolve_earth_evidence("Saffire large scale burn", investigation_id="saffire_iii")
        self.assertGreaterEqual(len(saffire_records), 1)
        for r in saffire_records:
            self.assertEqual(r["investigation_id"], "saffire_iii")

    def test_06_evidence_resolution_by_category(self):
        """Verifies deterministic evidence resolution by category ID."""
        wildfire_records = self.adapter.resolve_earth_evidence("wildfire peat duff", earth_category="wildfire_combustion")
        self.assertGreaterEqual(len(wildfire_records), 1)
        for r in wildfire_records:
            self.assertEqual(r["category_id"], "wildfire_combustion")

    def test_07_nine_section_synthesis_structure(self):
        """Verifies that fallback synthesis produces all 9 required structured sections."""
        ev = self.adapter.service.get_evidence_by_id("EA-EV-BASS-PYRO-01").dict()
        q = "How do BASS-II solid pyrolysis kinetics inform terrestrial clean combustion?"
        res = self.synthesizer._generate_earth_application_synthesis(
            question=q,
            earth_items=[ev],
        )

        self.assertEqual(res["status"], "earth_application_retrieval_fallback")
        ans = res["answer"]

        # Check for all 9 required sections
        self.assertIn("### 1. Direct Scientific Answer", ans)
        self.assertIn("### 2. Relevant NASA Microgravity Investigations", ans)
        self.assertIn("### 3. Verified Experimental Observations", ans)
        self.assertIn("### 4. Underlying Physical Mechanisms", ans)
        self.assertIn("### 5. Potential Terrestrial Research Implications", ans)
        self.assertIn("### 6. Gravity, Buoyancy, and Scale-Transfer Limitations", ans)
        self.assertIn("### 7. Evidence Classification, Confidence Tier & Quality Warnings", ans)
        self.assertIn("### 8. Source Citations & Traceable Evidence IDs", ans)
        self.assertIn("### 9. Areas Requiring Additional Terrestrial Validation", ans)

        # Physical mechanisms check
        self.assertIn("Gr / Re^2", ans)

        # Check citation in answer
        self.assertIn("[EA-EV-BASS-PYRO-01]", ans)

        # Verify citation_record_ids contains the traceable ID
        self.assertIn("EA-EV-BASS-PYRO-01", res.get("citation_record_ids", []))

    def test_08_documented_adoption_inquiry_truthfulness(self):
        """Verifies that queries about commercial adoption explicitly state zero documented commercial adoptions."""
        q = "Has any NASA microgravity combustion research been commercially adopted or deployed in industry?"
        res = self.synthesizer._generate_earth_application_synthesis(
            question=q,
            earth_items=[self.adapter.service.get_evidence_by_id("EA-EV-BASS-PYRO-01").dict()],
        )

        ans = res["answer"]
        # Must clearly state 0 documented applications and 10 supported / 1 exploratory
        self.assertIn("0 documented commercial applications", ans)
        self.assertIn("10 supported research implications", ans)
        self.assertIn("1 exploratory", ans)

    def test_09_claim_validation_lead_time_defense(self):
        """Verifies that generalizing 43s flight sensor response to a generic terrestrial smoke alarm lead time is flagged."""
        hallucinated_text = (
            "NASA testing demonstrated a 43 seconds earlier warning lead time for all commercial terrestrial smoke alarms."
        )
        val = self.synthesizer._validate_scientific_claims(
            answer_text=hallucinated_text,
            retrieved_candidates=[],
        )
        self.assertFalse(val["is_valid"])
        self.assertIn("unsupported_lead_time_claim", val["flags"])

    def test_10_claim_validation_efficiency_percentage_defense(self):
        """Verifies that fabricating 15-20% efficiency gains without terrestrial testing is flagged."""
        hallucinated_text = (
            "Microgravity droplet research proved a 15-20% efficiency increase for commercial gas turbines."
        )
        val = self.synthesizer._validate_scientific_claims(
            answer_text=hallucinated_text,
            retrieved_candidates=[],
        )
        self.assertFalse(val["is_valid"])
        self.assertIn("unsupported_efficiency_percentage_claim", val["flags"])

    def test_11_claim_validation_commercial_adoption_defense(self):
        """Verifies that claiming current commercial deployment or building code certification is flagged."""
        hallucinated_text = (
            "This microgravity fire suppression technology is already deployed in commercial turbines and certified under NFPA standards."
        )
        val = self.synthesizer._validate_scientific_claims(
            answer_text=hallucinated_text,
            retrieved_candidates=[],
        )
        self.assertFalse(val["is_valid"])
        self.assertIn("unsupported_commercial_adoption_claim", val["flags"])

    def test_12_tool_recommendations_for_earth_evidence(self):
        """Verifies that tool recommendations prioritize Earth Applications and supporting tools."""
        ev = self.adapter.service.get_evidence_by_id("EA-EV-SAFFIRE-DET-02").dict()
        recs = self.synthesizer.tool_recommender.recommend(
            question="How does Saffire smoke detection inform building duct fire safety?",
            retrieved_evidence=[],
            earth_evidence=[ev],
        )

        action_ids = [r["action_id"] for r in recs]
        self.assertIn("open_earth_applications", action_ids)
        self.assertIn("open_telemetry_visualizer", action_ids)

    def test_13_api_post_rag_ask_earth_application(self):
        """Verifies POST /api/rag/ask endpoint handles earth applications inquiry under Gemini-Only policy."""
        payload = {
            "question": "How do BASS-II experiments inform terrestrial industrial furnace design?",
            "evidence_id": "EA-EV-BASS-PYRO-01",
        }
        resp = self.client.post("/api/rag/ask", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Under Gemini-only policy without API key, returns ai_unavailable with honest status
        self.assertEqual(data["status"], "ai_unavailable")
        self.assertIsNone(data["answer"])
        self.assertEqual(data["error_code"], "GEMINI_UNAVAILABLE")
        self.assertEqual(data["earth_evidence_id"], "EA-EV-BASS-PYRO-01")

        # Verify suggested actions include Earth Applications
        actions = data.get("suggested_actions", [])
        self.assertTrue(any(a["tab_id"] == "earth-applications" for a in actions))

    def test_14_api_get_investigate_earth_application(self):
        """Verifies GET /api/earth-applications/{id}/investigate endpoint."""
        resp = self.client.get("/api/earth-applications/EA-EV-BASS-PYRO-01/investigate")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["evidence_id"], "EA-EV-BASS-PYRO-01")
        self.assertIn("investigation", data)
        self.assertIn("answer", data)
        self.assertIn("### 1. Direct Scientific Answer", data["answer"])
        self.assertIn("### 4. Underlying Physical Mechanisms", data["answer"])
        self.assertIn("### 6. Gravity, Buoyancy, and Scale-Transfer Limitations", data["answer"])
        self.assertGreaterEqual(len(data["evidence_citations"]), 1)

    def test_15_api_get_investigate_not_found(self):
        """Verifies GET /api/earth-applications/{id}/investigate returns 404 for nonexistent ID."""
        resp = self.client.get("/api/earth-applications/EA-EV-NONEXISTENT/investigate")
        self.assertEqual(resp.status_code, 404)

    def test_16_regression_research_gap_investigation(self):
        """Verifies that research gap investigation endpoint still operates correctly."""
        resp = self.client.get("/api/research-gaps/findings/GAP-COV-GRAV-PARTIAL-LUNAR/investigate")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["finding_id"], "GAP-COV-GRAV-PARTIAL-LUNAR")
        self.assertIn("investigation", data)
        self.assertIn("answer", data)


if __name__ == "__main__":
    unittest.main()
