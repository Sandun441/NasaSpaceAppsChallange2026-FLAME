"""
NASA FLAME — Automated Test Suite for Phase F5
Prompt-Driven Fire-Safety Equipment and Earth Applications Research
Validates:
1. Equipment prompt interpretation
2. Equipment category and evidence state
3. Verified measurement rendering
4. Unsupported equipment claims
5. Earth Applications prompt interpretation
6. Correct evidence ID matching
7. Canonical classification integrity (10 supported, 1 exploratory, 0 documented)
8. Relevant subset retrieval versus full catalog
9. Research Connection Bridge 5-step navigation
10. Unknown or ambiguous objectives
11. Explicit workspace preservation
12. Gemini-unavailable deterministic fallback
13. Citation provenance
"""

import sys
import unittest
from pathlib import Path

# Add data-pipeline to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prompt_system.service import PromptResearchService
from prompt_system.models import PromptResearchRequest
from equipment.service import FireSafetyEquipmentService
from earth_applications.service import EarthApplicationsService


class TestPromptEquipmentEarthAppsF5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.equipment_service = FireSafetyEquipmentService()
        cls.earth_service = EarthApplicationsService()
        cls.service = PromptResearchService(
            equipment_service=cls.equipment_service,
            earth_applications_service=cls.earth_service,
        )

    # -------------------------------------------------------------------------
    # TEST 1: Equipment Prompt Interpretation
    # -------------------------------------------------------------------------
    def test_01_equipment_prompt_interpretation(self):
        req = PromptResearchRequest(
            objective="What NASA findings could help researchers improve spacecraft smoke detection?",
            workspace="equipment",
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        self.assertEqual(res.workspace, "equipment")
        self.assertEqual(res.specialist_data.get("category"), "detection")
        self.assertIn("category_metadata", res.specialist_data)
        self.assertGreaterEqual(len(res.specialist_data.get("matched_investigations", [])), 1)

        # Check that Cygnus vehicle telemetry is identified
        matched_inv_ids = [inv.get("id") for inv in res.specialist_data.get("matched_investigations", [])]
        self.assertIn("cygnus_vehicle_telemetry", matched_inv_ids)

    # -------------------------------------------------------------------------
    # TEST 2: Equipment Category and Evidence State (Prevention & Suppression)
    # -------------------------------------------------------------------------
    def test_02_equipment_category_and_evidence_state(self):
        # Prevention inquiry
        req_prev = PromptResearchRequest(
            objective="How does microgravity flammability testing inform spacecraft material selection standards?",
            workspace="equipment",
        )
        res_prev = self.service.process_prompt(req_prev)
        self.assertEqual(res_prev.status, "ok")
        self.assertEqual(res_prev.specialist_data.get("category"), "prevention")

        # Suppression inquiry
        req_supp = PromptResearchRequest(
            objective="What microgravity evidence informs fire extinction limits in low-flow vehicle ducts?",
            workspace="equipment",
        )
        res_supp = self.service.process_prompt(req_supp)
        self.assertEqual(res_supp.status, "ok")
        self.assertEqual(res_supp.specialist_data.get("category"), "suppression")

    # -------------------------------------------------------------------------
    # TEST 3: Verified Measurement Rendering
    # -------------------------------------------------------------------------
    def test_03_verified_measurement_rendering(self):
        req = PromptResearchRequest(
            objective="What NASA findings could help researchers improve spacecraft smoke detection?",
            workspace="equipment",
        )
        res = self.service.process_prompt(req)

        self.assertGreaterEqual(len(res.visualizations), 1)
        cygnus_spec = next((v for v in res.visualizations if "smoke_detector" in v.chart_id), None)
        self.assertIsNotNone(cygnus_spec, "Cygnus smoke detector chart specification missing")
        self.assertIn("Smoke_Detector_Scatterometer_FIZ2_V", cygnus_spec.channel_ids)
        self.assertIn("Smoke_Detector_Obscuration_FIZ2_V", cygnus_spec.channel_ids)
        self.assertEqual(cygnus_spec.y_units, "V")

        # Check Saffire radiometer chart
        saffire_spec = next((v for v in res.visualizations if "saffire_radiometer" in v.chart_id), None)
        self.assertIsNotNone(saffire_spec, "Saffire radiometer chart specification missing")
        self.assertIn("Radiometer 1", saffire_spec.channel_ids)
        self.assertIn("Plume Temp 3 (TC3)", saffire_spec.channel_ids)

    # -------------------------------------------------------------------------
    # TEST 4: Unsupported Equipment Claims Safeguards
    # -------------------------------------------------------------------------
    def test_04_unsupported_equipment_claims_safeguards(self):
        req = PromptResearchRequest(
            objective="What NASA findings could help researchers improve spacecraft smoke detection?",
            workspace="equipment",
        )
        res = self.service.process_prompt(req)

        # Check explicit decision support disclaimers
        has_std_caveat = any("NASA-STD-6001" in c or "SSP-30599" in c for c in res.scientific_caveats)
        self.assertTrue(has_std_caveat, "NASA-STD-6001 compliance boundary notice missing")

        has_zero_fab = any("Zero-fabrication" in c or "fabricated" in c.lower() for c in res.scientific_caveats)
        self.assertTrue(has_zero_fab, "Zero-fabrication disclosure missing")

        # Ensure no fabricated performance percentages in findings
        for f in res.key_findings:
            self.assertNotIn("99.", f)
            self.assertNotIn("100% effective", f)
            self.assertNotIn("certified response time of", f)

    # -------------------------------------------------------------------------
    # TEST 5: Earth Applications Prompt Interpretation
    # -------------------------------------------------------------------------
    def test_05_earth_applications_prompt_interpretation(self):
        req = PromptResearchRequest(
            objective="How could BASS-II microgravity results inform fire safety research in buildings on Earth?",
            workspace="earth_applications",
        )
        res = self.service.process_prompt(req)

        self.assertEqual(res.status, "ok")
        self.assertEqual(res.workspace, "earth_applications")
        self.assertGreaterEqual(res.specialist_data.get("evidence_count", 0), 1)

        # Check that key findings articulate buoyancy decoupling and CFD calibration
        self.assertTrue(any("buoyan" in f.lower() for f in res.key_findings))
        self.assertTrue(any("model" in f.lower() or "cfd" in f.lower() or "parameter" in f.lower() for f in res.key_findings))

    # -------------------------------------------------------------------------
    # TEST 6: Correct Evidence ID Matching
    # -------------------------------------------------------------------------
    def test_06_correct_evidence_id_matching(self):
        req = PromptResearchRequest(
            objective="How could BASS-II microgravity results inform fire safety research in buildings on Earth?",
            workspace="earth_applications",
        )
        res = self.service.process_prompt(req)

        matched_ids = [r.get("id") for r in res.specialist_data.get("matched_records", [])]
        # Should match building conduit flame spread and BASS-II solid polymer findings
        self.assertTrue(
            any(rec_id in matched_ids for rec_id in ["EA-EV-SAFFIRE-DUCT-01", "EA-EV-BASS-PYRO-01", "EA-EV-BASS-EXT-02"]),
            f"Expected BASS/Building evidence IDs in {matched_ids}",
        )

    # -------------------------------------------------------------------------
    # TEST 7: Canonical Classification Integrity
    # -------------------------------------------------------------------------
    def test_07_canonical_classification_integrity(self):
        req = PromptResearchRequest(
            objective="What Earth applications exist in the catalog?",
            workspace="earth_applications",
        )
        res = self.service.process_prompt(req)

        canon = res.specialist_data.get("canonical_counts", {})
        self.assertEqual(res.specialist_data.get("total_catalog_count"), 11)
        self.assertEqual(canon.get("supported_research_implication"), 10)
        self.assertEqual(canon.get("exploratory_hypothesis"), 1)
        self.assertEqual(canon.get("documented_application"), 0)

        # Verify EA-EV-SAFFIRE-WILD-03 is strictly exploratory_hypothesis
        all_records = self.earth_service.list_evidence(limit=50).get("evidence", [])
        wild_rec = next((r for r in all_records if r.get("id") == "EA-EV-SAFFIRE-WILD-03"), None)
        self.assertIsNotNone(wild_rec)
        self.assertEqual(wild_rec.get("evidence_classification"), "exploratory_hypothesis")

    # -------------------------------------------------------------------------
    # TEST 8: Relevant Subset Retrieval vs Full Catalog
    # -------------------------------------------------------------------------
    def test_08_relevant_subset_retrieval_vs_full_catalog(self):
        # 1. Targeted query should return a relevant subset (less than 11)
        req_targeted = PromptResearchRequest(
            objective="What microgravity findings provide insights into low-ventilation wildfire embers and spread?",
            workspace="earth_applications",
        )
        res_targeted = self.service.process_prompt(req_targeted)
        targeted_count = res_targeted.specialist_data.get("evidence_count", 0)
        self.assertGreaterEqual(targeted_count, 1)
        self.assertLess(targeted_count, 11, "Targeted query should not return the entire catalog")

        # 2. Broad overview query should return all 11 records
        req_broad = PromptResearchRequest(
            objective="Show all Earth applications across the entire catalog",
            workspace="earth_applications",
        )
        res_broad = self.service.process_prompt(req_broad)
        self.assertEqual(res_broad.specialist_data.get("evidence_count"), 11)

        # 3. Verify audit disclosure is present
        self.assertIn("unintended_retrieval_limit_audit", res_targeted.specialist_data)

    # -------------------------------------------------------------------------
    # TEST 9: Research Connection Bridge 5-Step Navigation
    # -------------------------------------------------------------------------
    def test_09_research_connection_bridge_navigation(self):
        req = PromptResearchRequest(
            objective="How could BASS-II microgravity results inform fire safety research in buildings on Earth?",
            workspace="earth_applications",
        )
        res = self.service.process_prompt(req)

        bridge = res.specialist_data.get("bridge_data")
        self.assertIsNotNone(bridge, "Bridge data missing in specialist_data")
        self.assertEqual(len(bridge.get("steps", [])), 5, "Connection Bridge must contain exactly 5 steps")

        # Verify step numbers
        step_nums = [s.get("number") for s in bridge.get("steps", [])]
        self.assertEqual(step_nums, [1, 2, 3, 4, 5])

        # Verify bridge action item
        bridge_action = next((a for a in res.suggested_actions if a.action == "navigate_earth_bridge"), None)
        self.assertIsNotNone(bridge_action, "Bridge navigation action missing")
        self.assertEqual(bridge_action.tab_id, "earth_applications")

    # -------------------------------------------------------------------------
    # TEST 10: Unknown or Ambiguous Objectives
    # -------------------------------------------------------------------------
    def test_10_unknown_or_ambiguous_objectives(self):
        req = PromptResearchRequest(
            objective="What is the meaning of life in zero g?",
            workspace="earth_applications",
        )
        res = self.service.process_prompt(req)
        # Should gracefully return baseline fallback without throwing exceptions
        self.assertEqual(res.status, "ok")
        self.assertGreaterEqual(res.specialist_data.get("evidence_count", 0), 1)

    # -------------------------------------------------------------------------
    # TEST 11: Explicit Workspace Preservation
    # -------------------------------------------------------------------------
    def test_11_explicit_workspace_preservation(self):
        # A prompt in equipment workspace must stay in equipment
        req_eq = PromptResearchRequest(
            objective="How do building wildfires spread on Earth?",
            workspace="equipment",
        )
        res_eq = self.service.process_prompt(req_eq)
        self.assertEqual(res_eq.workspace, "equipment")

        # A prompt in earth_applications workspace must stay in earth_applications
        req_ea = PromptResearchRequest(
            objective="What sensors detect smoke in spacecraft?",
            workspace="earth_applications",
        )
        res_ea = self.service.process_prompt(req_ea)
        self.assertEqual(res_ea.workspace, "earth_applications")

    # -------------------------------------------------------------------------
    # TEST 12: Gemini-Unavailable Deterministic Fallback
    # -------------------------------------------------------------------------
    def test_12_deterministic_fallback_execution(self):
        req = PromptResearchRequest(
            objective="What NASA findings could help researchers improve spacecraft smoke detection?",
            workspace="equipment",
        )
        res = self.service.process_prompt(req)
        self.assertEqual(res.execution_mode, "deterministic_fallback")

    # -------------------------------------------------------------------------
    # TEST 13: Citation Provenance
    # -------------------------------------------------------------------------
    def test_13_citation_provenance(self):
        # Equipment citations
        req_eq = PromptResearchRequest(
            objective="What NASA findings could help researchers improve spacecraft smoke detection?",
            workspace="equipment",
        )
        res_eq = self.service.process_prompt(req_eq)
        self.assertGreaterEqual(len(res_eq.provenance_citations), 1)
        for cit in res_eq.provenance_citations:
            self.assertTrue(bool(cit.id))
            self.assertTrue(bool(cit.title))
            self.assertTrue(bool(cit.reference))

        # Earth applications citations
        req_ea = PromptResearchRequest(
            objective="How could BASS-II microgravity results inform fire safety research in buildings on Earth?",
            workspace="earth_applications",
        )
        res_ea = self.service.process_prompt(req_ea)
        self.assertGreaterEqual(len(res_ea.provenance_citations), 1)
        for cit in res_ea.provenance_citations:
            self.assertTrue(cit.id.startswith("EA-EV-"))
            self.assertIn(cit.grounding_level, ["supported_research_implication", "exploratory_hypothesis"])


if __name__ == "__main__":
    unittest.main()
