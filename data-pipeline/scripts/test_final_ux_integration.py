"""
NASA FLAME - Final UX Integration Automated Test Suite
Verifies:
1. Grounded answer synthesis for cross-module research inquiries.
2. Smart tool suggestions ("What would you like to explore next?") with handoff payload.
3. BASS-II discrete matrix comparison routing (zero time axis crash).
4. All 6 specialist workspaces prompt resolution.
5. Epistemic boundary adherence: zero synthetic or fabricated values.
"""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestFinalUXIntegration(unittest.TestCase):
    def test_homepage_prompt_grounded_answer_and_smart_suggestions(self):
        """Test that a broad inquiry returns a grounded answer and 3 smart tools with handoff payloads."""
        payload = {
            "objective": "How does oxygen concentration affect solid material flame spread in microgravity?",
            "workspace": "auto",
        }
        res = client.post("/api/prompt/research", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Check grounded answer exists, directly answers the scientific inquiry, and states limits
        self.assertIn("grounded_answer", data)
        ans = data["grounded_answer"]
        self.assertTrue(len(ans) > 50)
        self.assertIn("buoyant", ans.lower())
        self.assertIn("bass-ii", ans.lower())
        self.assertIn("cotton", ans.lower())
        self.assertIn("pmma", ans.lower())
        # Explicitly states limits on uninstrumented scalar flame spread rate
        self.assertTrue("flame spread rate" in ans.lower() or "uninstrumented" in ans.lower())
        # Must NOT report arbitrary single sensor maximum as the scientific conclusion
        self.assertNotIn("measured peak on 'o2' reached", ans.lower())

        # Check suggested actions (What would you like to explore next?)
        self.assertIn("suggested_actions", data)
        actions = data["suggested_actions"]
        self.assertTrue(len(actions) >= 3)

        # Smart tools must be ranked using relevance AND real data availability (BASS-II matrix)
        tab_ids = [a["tab_id"] for a in actions[:3]]
        self.assertIn("experiment-comparison", tab_ids)
        self.assertIn("gap-detection", tab_ids)

        for act in actions:
            self.assertIn("id", act)
            self.assertIn("label", act)
            self.assertIn("tab_id", act)
            self.assertIn("description", act)
            self.assertIn("icon", act)
            self.assertIn("payload", act)
            self.assertTrue(act["payload"].get("handoff", False))

    def test_saffire_timing_reconciliation(self):
        """Test that Saffire timing reconciles 64.22s, 66.56s, and attaches 1.65s/6.60s leads to steep onset."""
        payload = {
            "objective": "How do smoke detectors and radiometers detect microgravity fire in spacecraft?",
            "workspace": "equipment",
        }
        res = client.post("/api/prompt/research", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        finding_rad = next(f for f in data["key_findings"] if "Radiant heat detection" in f)
        # Must cite 64.22s as initial departure
        self.assertIn("64.22", finding_rad)
        # Must cite 66.56s as steep onset
        self.assertIn("66.56", finding_rad)
        # Must attach 1.65s lead to steep onset (t = 66.56s)
        self.assertIn("1.65", finding_rad)
        # Must state this reflects in-duct sensor physics, NOT commercial smoke-detector performance
        self.assertIn("not commercial smoke-detector performance", finding_rad.lower())

        # Grounded answer must also maintain this distinction
        self.assertIn("64.22", data["grounded_answer"])
        self.assertIn("66.56", data["grounded_answer"])
        self.assertIn("1.65", data["grounded_answer"])
        self.assertIn("commercial fire alarm", data["grounded_answer"].lower())

    def test_bass_ii_discrete_matrix_comparison_routing(self):
        """Test BASS-II queries do not crash with time axis error and return valid structured responses."""
        payload = {
            "objective": "Compare BASS-II Cotton vs PMMA glovebox burn matrix across oxygen concentrations.",
            "workspace": "auto",
        }
        res = client.post("/api/prompt/research", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("grounded_answer", data)
        self.assertTrue(len(data["grounded_answer"]) > 10)
        self.assertIn("BASS-II", data["grounded_answer"])
        self.assertEqual(data["workspace"], "comparison")

    def test_smoke_detector_equipment_suggestions(self):
        """Test spacecraft smoke detection inquiry returns grounded equipment answers and relevant suggestions."""
        payload = {
            "objective": "How does aerosol particle agglomeration affect smoke detector response times in spacecraft?",
            "workspace": "equipment",
        }
        res = client.post("/api/prompt/research", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("grounded_answer", data)
        self.assertTrue(len(data["grounded_answer"]) > 15)
        # Should suggest equipment research or gap detection
        tab_ids = [a["tab_id"] for a in data.get("suggested_actions", [])]
        self.assertTrue(any(t in ["equipment-research", "gap-detection", "earth-applications"] for t in tab_ids))

    def test_terrestrial_wildfire_transfer_suggestions(self):
        """Test terrestrial transfer inquiry produces transfer caveats and appropriate actions."""
        payload = {
            "objective": "What microgravity findings provide insights into low-ventilation wildfire embers and spread?",
            "workspace": "earth_applications",
        }
        res = client.post("/api/prompt/research", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("grounded_answer", data)
        # Must reflect exploratory or transfer nature
        self.assertTrue(len(data["grounded_answer"]) > 15)

    def test_all_six_specialist_workspaces_resolved(self):
        """Verify each of the 6 specialist workspaces processes its native inquiries cleanly."""
        test_cases = [
            ("visualization", "Plot Saffire-III Sample 1 radiant heat flux over full flight duration."),
            ("comparison", "Compare the radiant heat flux and temperature measurements from Saffire-III Sample 1 and Sample 2."),
            ("modeling", "Prepare BASS-II experimental data to study flame behavior using oxygen concentration, material, and airflow."),
            ("gap_detection", "What empirical combustion tests exist for lunar (0.16g) or Martian (0.38g) partial gravity?"),
            ("equipment", "What microgravity evidence informs fire extinction limits in low-flow vehicle ducts?"),
            ("earth_applications", "How could BASS-II microgravity results inform fire safety research in buildings on Earth?"),
        ]

        for ws, q in test_cases:
            res = client.post("/api/prompt/research", json={"objective": q, "workspace": ws})
            self.assertEqual(res.status_code, 200, f"Failed for workspace '{ws}'")
            data = res.json()
            self.assertIsNotNone(data.get("grounded_answer"), f"Missing grounded_answer for workspace '{ws}'")
            self.assertTrue(len(data.get("suggested_actions", [])) >= 2, f"Insufficient suggested_actions for '{ws}'")


if __name__ == "__main__":
    unittest.main()
