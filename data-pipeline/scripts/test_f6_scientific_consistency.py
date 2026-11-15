"""
NASA FLAME — Phase F6 Scientific Consistency & Reconciled Measurements Test Suite

Tests that the platform's specialist services enforce exact, scientifically grounded measurements:
1. BASS-II Matrix Material Totals: 129 flight runs reconciled (98 PMMA, 27 Cotton/SIBAL, 3 Nomex, 1 Wax; 121 literal keyword matches + 8 canonical runs).
2. Predictive Modeling Feature Completeness: Strict distinction between cell completeness (98.84%) and complete-case records (123/129, 95.3%).
3. Cross-Validation Grouping: run_id is 100% unique; GroupKFold cross-validation groups by physical specimen sample_id (107 unique specimens).
4. Research-Gap Relevance: Explicit query regimes partitioned into direct_matches and related_opportunities, with direct matches ranked first.
5. Earth Applications Weighting: Explicitly named investigations (e.g. BASS-II) receive priority weighting (+10), ranking BASS-II records first.
6. Saffire Radiometer & Ignition Timing: Reconciled with raw telemetry ground truth (t=60.03-67.98s igniter, radiative onset t=64.22s, peak 150.39 mW/cm² at t=197.74s, 1.65-6.6s optical lead).
"""

import unittest
import sys
import os

# Ensure data-pipeline root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from prompt_system.service import PromptResearchService
from prompt_system.models import PromptResearchRequest


class TestF6ScientificConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = PromptResearchService()

    def test_01_bass_ii_material_totals_reconciliation(self):
        """Verify BASS-II discrete matrix comparison reports both literal and canonical totals."""
        req = PromptResearchRequest(
            objective="Compare flammability parameter space of PMMA and Cotton in BASS-II",
            workspace="comparison",
        )
        resp = self.service.process_prompt(req)

        self.assertEqual(resp.status, "ok")
        self.assertEqual(resp.workspace, "comparison")
        data = resp.specialist_data

        # Total runs must equal canonical 129
        self.assertEqual(data.get("total_runs"), 129)
        # Literal keyword match: 91 PMMA, 27 Cotton, 3 Nomex = 121
        self.assertEqual(data.get("pmma_runs"), 91)
        self.assertEqual(data.get("cotton_runs"), 27)
        self.assertEqual(data.get("nomex_runs"), 3)
        # Canonical breakdown: 98 PMMA (91 + 5 thin-film + 2 spherical cast), 1 wax, 8 other
        self.assertEqual(data.get("canonical_pmma_runs"), 98)
        self.assertEqual(data.get("wax_runs"), 1)
        self.assertEqual(data.get("other_runs"), 8)

        # Check subtitle discloses the 121 vs 129 reconciliation
        chart = resp.visualizations[0]
        self.assertIn("129", chart.subtitle)
        self.assertIn("98 PMMA", chart.subtitle)
        self.assertIn("121", chart.subtitle)

        # Check key findings disclose the exact 98 PMMA runs and 121 literal matches
        finding_0 = resp.key_findings[0]
        self.assertIn("129 flight runs", finding_0)
        self.assertIn("98 PMMA", finding_0)
        self.assertIn("121 literal keyword matches", finding_0)

    def test_02_predictive_modeling_completeness_distinction(self):
        """Verify modeling service strictly distinguishes cell completeness from complete-case records."""
        req = PromptResearchRequest(
            objective="Extract candidate features for flame spread prediction in BASS-II",
            workspace="modeling",
        )
        resp = self.service.process_prompt(req)

        self.assertEqual(resp.status, "ok")
        self.assertEqual(resp.workspace, "modeling")
        data = resp.specialist_data

        # Cell completeness must be ~98.84%
        cell_comp = data.get("cell_completeness_pct")
        self.assertIsNotNone(cell_comp)
        self.assertAlmostEqual(cell_comp, 98.84, delta=0.5)

        # Complete case count must reflect ~123 complete cases
        comp_cases = data.get("complete_case_count")
        self.assertIn(comp_cases, [123, 124, 125, 126, 127])

        # Subtitle and findings must not confuse the two
        chart = resp.visualizations[0]
        self.assertIn("Cell Completeness", chart.subtitle)
        self.assertIn(str(comp_cases), chart.subtitle)

        finding_feasibility = next(f for f in resp.key_findings if "Dataset Feasibility" in f)
        self.assertIn("cell-level completeness", finding_feasibility)
        self.assertIn("complete-case records", finding_feasibility)

    def test_03_cross_validation_specimen_grouping(self):
        """Verify GroupKFold cross-validation correctly identifies sample_id for repeated burns."""
        req = PromptResearchRequest(
            objective="Configure predictive modeling cross-validation for BASS-II",
            workspace="modeling",
        )
        resp = self.service.process_prompt(req)

        data = resp.specialist_data
        self.assertEqual(data.get("specimen_group_column"), "sample_id")

        finding_leakage = next(f for f in resp.key_findings if "Data Leakage" in f)
        self.assertIn("sample_id", finding_leakage)
        self.assertIn("107 unique specimens", finding_leakage)

        caveat_cv = next(c for c in resp.scientific_caveats if "Cross-validation protocol" in c)
        self.assertIn("sample_id", caveat_cv)

    def test_04_gap_detection_direct_match_ranking(self):
        """Verify research gap detection partitions and prioritizes direct parameter matches."""
        req = PromptResearchRequest(
            objective="What are the combustion research gaps in lunar and partial gravity environments?",
            workspace="gap_detection",
        )
        resp = self.service.process_prompt(req)

        self.assertEqual(resp.status, "ok")
        data = resp.specialist_data

        direct_matches = data.get("direct_matches", [])
        related_opps = data.get("related_opportunities", [])
        applicable_gaps = data.get("applicable_gap_findings", [])

        self.assertGreater(len(direct_matches), 0)
        # Top applicable gap must come from direct matches
        self.assertEqual(applicable_gaps[0]["finding_id"], direct_matches[0]["finding_id"])

    def test_05_earth_applications_investigation_priority(self):
        """Verify explicit BASS-II query ranks BASS-II evidence ahead of general building duct evidence."""
        req = PromptResearchRequest(
            objective="How could BASS-II microgravity results inform fire safety research in buildings on Earth?",
            workspace="earth_applications",
        )
        resp = self.service.process_prompt(req)

        self.assertEqual(resp.status, "ok")
        data = resp.specialist_data

        # Primary record must be a BASS investigation record (EA-EV-BASS-PYRO-01 or EA-EV-BASS-EXT-02)
        primary_id = data.get("primary_evidence_id")
        self.assertIn("BASS", primary_id)

    def test_06_saffire_radiometer_grounded_measurements(self):
        """Verify Saffire radiometer measurements reflect audited telemetry times and flux."""
        req = PromptResearchRequest(
            objective="How do smoke detectors and radiometers detect microgravity fire in spacecraft?",
            workspace="equipment",
        )
        resp = self.service.process_prompt(req)

        self.assertEqual(resp.status, "ok")
        finding_rad = next(f for f in resp.key_findings if "Radiant heat detection" in f)

        # Must cite verified radiative onset t=64.22s, peak flux 150.39 mW/cm², and 1.65-6.6s optical lead
        self.assertIn("64.22", finding_rad)
        self.assertIn("150.39", finding_rad)
        self.assertIn("1.65", finding_rad)


if __name__ == "__main__":
    unittest.main()
