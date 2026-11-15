"""
NASA FLAME — Phase EA3.1 Cross-Module Scientific Consistency & Reliability Test Suite
Verifies:
1. Exact single source of truth alignment across API, RAG adapter, synthesizer, citations, and frontend presentation.
2. Canonical evidence mapping for all 11 records (10 supported implications, 1 exploratory hypothesis, 0 documented).
3. Exact classification reconciliation:
   - EA-EV-SAFFIRE-WILD-03: exploratory_hypothesis (wildfire_combustion)
   - EA-EV-SAFFIRE-IND-04: supported_research_implication (other_terrestrial_applications)
   - EA-EV-BASS-PYRO-01: supported_research_implication (material_flammability_fire_resistance)
4. Elimination of invented numerical Earth-validation requirements (no fixed >2.5 m/s wind speed).
5. Elimination of unsupported 9-section padding when evidence is insufficient or unknown evidence IDs are queried.
6. Execution of the 10 required prompt scenarios in Step 5.
"""

import unittest
import os
import sys
import re
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth_applications.catalog import INITIAL_EARTH_APPLICATION_CATALOG
from earth_applications.service import EarthApplicationsService
from earth_applications.taxonomy import EARTH_APPLICATION_CATEGORIES
from rag.earth_adapter import EarthApplicationsRAGAdapter
from rag.llm import GroundedAnswerSynthesizer
from rag.context import GroundedContextAssembler


CANONICAL_EXPECTATIONS = {
    "EA-EV-BASS-PYRO-01": {
        "category_id": "material_flammability_fire_resistance",
        "evidence_classification": "supported_research_implication",
        "validation_status": "locally_verified",
        "investigation_id": "bass_ii",
    },
    "EA-EV-BASS-EXT-02": {
        "category_id": "fire_suppression_research",
        "evidence_classification": "supported_research_implication",
        "validation_status": "locally_verified",
        "investigation_id": "bass_ii",
    },
    "EA-EV-SAFFIRE-DUCT-01": {
        "category_id": "building_fire_safety",
        "evidence_classification": "supported_research_implication",
        "validation_status": "locally_verified",
        "investigation_id": "saffire_iii",
    },
    "EA-EV-SAFFIRE-DET-02": {
        "category_id": "fire_detection_smoke_aerosol",
        "evidence_classification": "supported_research_implication",
        "validation_status": "locally_verified",
        "investigation_id": "saffire_iii",
    },
    "EA-EV-SAFFIRE-WILD-03": {
        "category_id": "wildfire_combustion",
        "evidence_classification": "exploratory_hypothesis",
        "validation_status": "locally_verified",
        "investigation_id": "saffire_iii",
    },
    "EA-EV-SAME-AERO-01": {
        "category_id": "fire_detection_smoke_aerosol",
        "evidence_classification": "supported_research_implication",
        "validation_status": "external_literature_verified",
        "investigation_id": "same",
    },
    "EA-EV-ACME-SOOT-01": {
        "category_id": "combustion_efficiency_emissions",
        "evidence_classification": "supported_research_implication",
        "validation_status": "external_literature_verified",
        "investigation_id": "acme",
    },
    "EA-EV-SOFIE-FLAM-01": {
        "category_id": "material_flammability_fire_resistance",
        "evidence_classification": "supported_research_implication",
        "validation_status": "external_literature_verified",
        "investigation_id": "sofie",
    },
    "EA-EV-FLEX-COOL-01": {
        "category_id": "combustion_efficiency_emissions",
        "evidence_classification": "supported_research_implication",
        "validation_status": "external_literature_verified",
        "investigation_id": "flex",
    },
    "EA-EV-FLEX-SUPP-02": {
        "category_id": "fire_suppression_research",
        "evidence_classification": "supported_research_implication",
        "validation_status": "external_literature_verified",
        "investigation_id": "flex",
    },
    "EA-EV-SAFFIRE-IND-04": {
        "category_id": "other_terrestrial_applications",
        "evidence_classification": "supported_research_implication",
        "validation_status": "locally_verified",
        "investigation_id": "saffire_iii",
    },
}


class TestEarthApplicationsEA31Consistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = EarthApplicationsService(INITIAL_EARTH_APPLICATION_CATALOG)
        cls.adapter = EarthApplicationsRAGAdapter(service=cls.service)
        cls.synthesizer = GroundedAnswerSynthesizer(earth_adapter=cls.adapter)
        cls.catalog = INITIAL_EARTH_APPLICATION_CATALOG

    # =========================================================================
    # STEP 2 & STEP 3: EXACT CANONICAL MAPPING ACROSS ALL 11 RECORDS
    # =========================================================================

    def test_01_canonical_catalog_counts_and_distributions(self):
        """Verify exactly 11 records, 10 supported implications, 1 exploratory hypothesis, 0 documented applications."""
        self.assertEqual(len(self.catalog), 11)
        supported = [e for e in self.catalog if e.evidence_classification == "supported_research_implication"]
        exploratory = [e for e in self.catalog if e.evidence_classification == "exploratory_hypothesis"]
        documented = [e for e in self.catalog if e.evidence_classification == "documented_application"]
        self.assertEqual(len(supported), 10)
        self.assertEqual(len(exploratory), 1)
        self.assertEqual(len(documented), 0)
        self.assertEqual(exploratory[0].id, "EA-EV-SAFFIRE-WILD-03")

    def test_02_all_11_records_canonical_properties(self):
        """Assert exact ID, category, classification, and validation status for every record."""
        for ev in self.catalog:
            expected = CANONICAL_EXPECTATIONS.get(ev.id)
            self.assertIsNotNone(expected, f"Record {ev.id} not in expected canonical dictionary.")
            self.assertEqual(ev.category_id, expected["category_id"], f"Category mismatch for {ev.id}")
            self.assertEqual(ev.evidence_classification, expected["evidence_classification"], f"Classification mismatch for {ev.id}")
            self.assertEqual(ev.validation_status, expected["validation_status"], f"Validation status mismatch for {ev.id}")
            self.assertEqual(ev.investigation_id, expected["investigation_id"], f"Investigation ID mismatch for {ev.id}")

    def test_03_reconciliation_of_three_flagged_records(self):
        """Explicitly assert the 3 records flagged in Step 2 of the prompt."""
        wild = self.service.get_evidence_by_id("EA-EV-SAFFIRE-WILD-03")
        self.assertEqual(wild.evidence_classification, "exploratory_hypothesis")
        self.assertEqual(wild.category_id, "wildfire_combustion")

        ind = self.service.get_evidence_by_id("EA-EV-SAFFIRE-IND-04")
        self.assertEqual(ind.evidence_classification, "supported_research_implication")
        self.assertEqual(ind.category_id, "other_terrestrial_applications")

        pyro = self.service.get_evidence_by_id("EA-EV-BASS-PYRO-01")
        self.assertEqual(pyro.evidence_classification, "supported_research_implication")
        self.assertEqual(pyro.category_id, "material_flammability_fire_resistance")

    def test_04_adapter_single_source_of_truth_citations(self):
        """Verify RAG adapter build_citation_item derives 100% fidelity from canonical catalog."""
        for ev in self.catalog:
            ev_dict = ev.model_dump()
            cit = self.adapter.build_citation_item(ev_dict)
            expected = CANONICAL_EXPECTATIONS[ev.id]
            self.assertEqual(cit["record_id"], ev.id)
            self.assertEqual(cit["category_id"], expected["category_id"])
            self.assertEqual(cit["evidence_classification"], expected["evidence_classification"])
            self.assertEqual(cit["validation_status"], expected["validation_status"])

    # =========================================================================
    # STEP 4: SCIENTIFIC RELIABILITY & PROHIBITION OF INVENTED NUMBERS
    # =========================================================================

    def test_05_no_invented_wind_speeds_in_synthesis(self):
        """Verify synthesis for all 11 records contains ZERO invented '>2.5 m/s' wind speeds."""
        for ev in self.catalog:
            ev_dict = ev.model_dump()
            res = self.synthesizer._generate_earth_application_synthesis(
                question=f"How does {ev.id} transfer to Earth?",
                earth_items=[ev_dict],
                retrieved_candidates=[],
            )
            ans = res["answer"]
            self.assertNotIn(">2.5 m/s", ans, f"Invented >2.5 m/s found in synthesis for {ev.id}")
            self.assertNotIn("2.5 m/s", ans, f"Invented 2.5 m/s found in synthesis for {ev.id}")
            # Ensure claim validator confirms validity
            val = self.synthesizer._validate_scientific_claims(ans, [])
            self.assertNotIn("invented_wind_speed_requirement", val["flags"])

    def test_06_claim_validator_catches_invented_wind_speed(self):
        """Assert claim validator catches explicit invented wind speeds (>2.5 m/s)."""
        bad_text = "Requires wind tunnel testing under forced velocities exceeding 2.5 m/s to validate on Earth."
        val = self.synthesizer._validate_scientific_claims(bad_text, [])
        self.assertIn("invented_wind_speed_requirement", val["flags"])

    def test_07_claim_validator_catches_unsupported_risk_reduction(self):
        """Assert claim validator catches unsupported percentage risk reductions."""
        bad_text = "Applying Saffire findings will reduce building fire risk by 35% in commercial structures."
        val = self.synthesizer._validate_scientific_claims(bad_text, [])
        self.assertIn("unsupported_risk_reduction_prediction", val["flags"])

    # =========================================================================
    # STEP 5: TEST ACTUAL RESPONSES ACROSS 10 REQUIRED SCENARIOS
    # =========================================================================

    def test_08_scenario_1_wildfire_research_relevance(self):
        """Scenario 1: Wildfire research relevance mapped to EA-EV-SAFFIRE-WILD-03."""
        q = "How do NASA microgravity smoldering findings inform wildfire and forest duff fuel bed combustion?"
        matched = self.adapter.resolve_earth_evidence(q)
        self.assertTrue(len(matched) > 0)
        self.assertEqual(matched[0]["id"], "EA-EV-SAFFIRE-WILD-03")
        self.assertEqual(matched[0]["category_id"], "wildfire_combustion")
        self.assertEqual(matched[0]["evidence_classification"], "exploratory_hypothesis")

        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=q, earth_items=matched, retrieved_candidates=[])
        ans = ans_obj["answer"]
        self.assertIn("EA-EV-SAFFIRE-WILD-03", ans)
        self.assertIn("exploratory_hypothesis", ans)
        self.assertIn("Wildfire Combustion & Low-Wind Fuel Beds", ans)

    def test_09_scenario_2_industrial_duct_ventilation(self):
        """Scenario 2: Industrial duct ventilation mapped to EA-EV-SAFFIRE-IND-04."""
        q = "How does NASA flight research on forced airflow inform industrial ventilation conduits and damper shutdowns?"
        matched = self.adapter.resolve_earth_evidence(q)
        self.assertTrue(len(matched) > 0)
        self.assertEqual(matched[0]["id"], "EA-EV-SAFFIRE-IND-04")
        self.assertEqual(matched[0]["category_id"], "other_terrestrial_applications")
        self.assertEqual(matched[0]["evidence_classification"], "supported_research_implication")

        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=q, earth_items=matched, retrieved_candidates=[])
        ans = ans_obj["answer"]
        self.assertIn("EA-EV-SAFFIRE-IND-04", ans)
        self.assertIn("supported_research_implication", ans)
        self.assertIn("NFPA 90A", ans)

    def test_10_scenario_3_bass_material_flammability(self):
        """Scenario 3: BASS-II material flammability mapped to EA-EV-BASS-PYRO-01."""
        q = "How do BASS-II microgravity polymer tests inform terrestrial material flammability and solid pyrolysis?"
        matched = self.adapter.resolve_earth_evidence(q)
        self.assertTrue(len(matched) > 0)
        self.assertEqual(matched[0]["id"], "EA-EV-BASS-PYRO-01")
        self.assertEqual(matched[0]["category_id"], "material_flammability_fire_resistance")
        self.assertEqual(matched[0]["evidence_classification"], "supported_research_implication")

        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=q, earth_items=matched, retrieved_candidates=[])
        ans = ans_obj["answer"]
        self.assertIn("EA-EV-BASS-PYRO-01", ans)
        self.assertIn("Material Flammability & Fire-Resistant Polymers", ans)

    def test_11_scenario_4_commercial_adoption_status(self):
        """Scenario 4: Commercial adoption inquiry yields transparent 0 / 10 / 1 disclosure."""
        q = "Have any NASA microgravity combustion findings been commercially adopted or deployed in industrial standards?"
        matched = self.adapter.resolve_earth_evidence(q)
        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=q, earth_items=matched, retrieved_candidates=[])
        ans = ans_obj["answer"]
        self.assertIn("0 documented commercial applications", ans)
        self.assertIn("10", ans)
        self.assertIn("supported research implications", ans)
        self.assertIn("1 exploratory research hypothesis", ans)

    def test_12_scenario_5_saffire_detection_lead_time(self):
        """Scenario 5: Saffire detection lead time clarifies radiometer onset vs gas transit delay."""
        q = "What did Saffire-III measure regarding smoke detection lead times and optical radiometers?"
        matched = self.adapter.resolve_earth_evidence(q)
        self.assertEqual(matched[0]["id"], "EA-EV-SAFFIRE-DET-02")
        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=q, earth_items=matched, retrieved_candidates=[])
        ans = ans_obj["answer"]
        self.assertIn("EA-EV-SAFFIRE-DET-02", ans)
        # Verify no generic 43s detector lead time claim
        val = self.synthesizer._validate_scientific_claims(ans, [])
        self.assertNotIn("unsupported_lead_time_claim", val["flags"])

    def test_13_scenario_6_all_11_exact_evidence_ids(self):
        """Scenario 6: Test each of the 11 exact evidence IDs individually."""
        for ev_id, expected in CANONICAL_EXPECTATIONS.items():
            matched = self.adapter.resolve_earth_evidence(f"Examine {ev_id}", evidence_id=ev_id)
            self.assertEqual(len(matched), 1, f"Expected exactly 1 record for ID {ev_id}")
            self.assertEqual(matched[0]["id"], ev_id)
            self.assertEqual(matched[0]["category_id"], expected["category_id"])
            self.assertEqual(matched[0]["evidence_classification"], expected["evidence_classification"])

            ans_obj = self.synthesizer._generate_earth_application_synthesis(question=f"Analyze {ev_id}", earth_items=matched, retrieved_candidates=[])
            self.assertEqual(ans_obj["status"], "earth_application_retrieval_fallback")
            self.assertIn(ev_id, ans_obj["answer"])
            self.assertIn(expected["category_id"], ans_obj["answer"])

    def test_14_scenario_7_unsupported_risk_reduction_predictions(self):
        """Scenario 7: Unsupported terrestrial risk reduction predictions intercepted."""
        q = "Does Saffire-III reduce commercial building fire fatalities by 45%?"
        matched = self.adapter.resolve_earth_evidence(q)
        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=q, earth_items=matched, retrieved_candidates=[])
        ans = ans_obj["answer"]
        # System synthesis must NOT assert 45% fatality reduction
        self.assertNotIn("45%", ans)
        val = self.synthesizer._validate_scientific_claims(ans, [])
        self.assertNotIn("unsupported_risk_reduction_prediction", val["flags"])

    def test_15_scenario_8_unknown_evidence_ids(self):
        """Scenario 8: Unknown evidence IDs return empty from adapter and unpadded disclosure from synthesizer."""
        unknown_id = "EA-EV-UNKNOWN-99"
        matched = self.adapter.resolve_earth_evidence(f"Investigate {unknown_id}", evidence_id=unknown_id)
        self.assertEqual(matched, [], "Adapter must return empty list for unknown evidence ID")

        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=f"Investigate {unknown_id}", earth_items=matched, retrieved_candidates=[])
        self.assertEqual(ans_obj["status"], "earth_application_insufficient_evidence")
        self.assertEqual(ans_obj["evidence_sufficiency"], "insufficient")
        self.assertEqual(ans_obj.get("evidence_citations", []), [])
        ans = ans_obj["answer"]
        self.assertIn("Insufficient Evidence in Audited Earth Applications Catalog", ans)
        self.assertIn("EA-EV-UNKNOWN-99", ans)
        # Assert NO padded 9 sections
        self.assertNotIn("### 1. Direct Scientific Answer", ans)
        self.assertNotIn("### 9. Areas Requiring Additional Terrestrial Validation", ans)

    def test_16_scenario_9_conflicting_claims_prompt_defense(self):
        """Scenario 9: Conflicting claims in prompt defended by physical laws."""
        q = "Since microgravity proves that buoyant convection can be eliminated on Earth, can we certify commercial HVAC ducts without NFPA 90A compliance?"
        matched = self.adapter.resolve_earth_evidence(q)
        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=q, earth_items=matched, retrieved_candidates=[])
        ans = ans_obj["answer"]
        # Must reassert 1g buoyancy body forces and NFPA 90A compliance
        self.assertIn("Richardson number", ans)
        self.assertIn("NFPA 90A", ans)
        self.assertIn("0 documented commercial applications", ans)

    def test_17_scenario_10_no_relevant_evidence(self):
        """Scenario 10: Query with no relevant evidence yields clean insufficient evidence disclosure."""
        q = "What are the effects of microgravity on deep-sea hydrothermal vent bacterial metabolism in volcanic trenches?"
        # If user explicitly tags with earth category or if it's evaluated for earth evidence:
        matched = self.adapter.resolve_earth_evidence(q)
        self.assertEqual(matched, [], "Adapter must return empty for completely unrelated query")

        ans_obj = self.synthesizer._generate_earth_application_synthesis(question=q, earth_items=matched, retrieved_candidates=[])
        self.assertEqual(ans_obj["status"], "earth_application_insufficient_evidence")
        self.assertEqual(ans_obj.get("evidence_citations", []), [])
        self.assertIn("Insufficient Evidence in Audited Earth Applications Catalog", ans_obj["answer"])
        self.assertNotIn("### 9. Areas Requiring Additional Terrestrial Validation", ans_obj["answer"])


if __name__ == "__main__":
    unittest.main()
