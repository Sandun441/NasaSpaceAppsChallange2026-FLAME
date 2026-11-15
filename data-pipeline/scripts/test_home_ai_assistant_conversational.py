"""
NASA FLAME — Scientific AI Assistant Conversational Routing & Grounding Unit Tests (Gemini-Only Architecture)
Verifies all sequences required by Task 8 & Final Gemini-Only Policy:
A. Hi -> How are you? -> Can you help me study microgravity? (conversational flow via Gemini)
B. What is microgravity? -> Explain it simply. (educational definition & simplification via Gemini)
C. What did NASA find in Saffire-III? -> Show me relevant visualizations. (empirical research & viz actions)
D. Compare Saffire-III Sample 1 and Sample 2. (structured comparative analysis via Gemini)
E. Gemini unavailable -> honest ai_unavailable status, null answer, and zero fallback essays.
F. Scientific records missing oxygen/flow/pressure -> missing values displayed, zero invented defaults.
"""

import unittest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from unittest.mock import MagicMock
import json
import re

# Add data-pipeline root to path
base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir))

from api.main import app, rag_synthesizer
from rag.llm import GroundedAnswerSynthesizer, GeminiProvider, DEFAULT_GEMINI_MODEL


class TestHomeAiAssistantConversational(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.orig_llm = rag_synthesizer.llm_provider

        mock_llm = GeminiProvider(api_key="mock_key")
        def mock_generate(system_instruction, user_prompt):
            p_lower = user_prompt.lower()
            q_line = p_lower
            for line in user_prompt.split("\n"):
                if "RESEARCH QUESTION:" in line or "USER INQUIRY:" in line:
                    q_line = line.lower()
                    break

            if "explain it simply" in q_line:
                return {
                    "success": True,
                    "raw_text": json.dumps({"answer": "Without gravity, hot air doesn't rise, so flames become spherical."}),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0
                }
            if "what is microgravity" in q_line:
                return {
                    "success": True,
                    "raw_text": json.dumps({"answer": "**Microgravity** is an environment of apparent weightlessness where gravitational acceleration is balanced by continuous freefall ($u_b \\approx 0$)."}),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0
                }
            if re.search(r"\b(hi|hello|how are you|help me study)\b", q_line):
                return {
                    "success": True,
                    "raw_text": json.dumps({"answer": "Hello! I am NASA FLAME Research Intelligence, ready to assist."}),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0
                }
            if "compare" in q_line or ("sample 1" in q_line and "sample 2" in q_line):
                return {
                    "success": True,
                    "raw_text": json.dumps({
                        "answer": "Comparing Saffire-III Sample 1 (SIBAL fabric) [flame_run_saffire_iii_sample_1] and Sample 2 (Nomex) [flame_run_saffire_iii_sample_2].",
                        "citation_record_ids": ["flame_run_saffire_iii_sample_1", "flame_run_saffire_iii_sample_2"],
                        "evidence_backed_claims": ["Sample 1 tested SIBAL [flame_run_saffire_iii_sample_1]"],
                        "scientific_limitations": []
                    }),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0
                }
            if "saffire" in q_line:
                return {
                    "success": True,
                    "raw_text": json.dumps({
                        "answer": "In Saffire-III, NASA evaluated large-scale vehicle flame spread [flame_inv_saffire_iii].",
                        "citation_record_ids": ["flame_inv_saffire_iii"],
                        "evidence_backed_claims": ["Saffire-III evaluated flame spread [flame_inv_saffire_iii]"],
                        "scientific_limitations": []
                    }),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0
                }
            return {
                "success": True,
                "raw_text": json.dumps({"answer": "Gemini response."}),
                "status_code": 200,
                "model": DEFAULT_GEMINI_MODEL,
                "retries_attempted": 0
            }

        mock_llm.generate = MagicMock(side_effect=mock_generate)
        rag_synthesizer.llm_provider = mock_llm

    @classmethod
    def tearDownClass(cls):
        rag_synthesizer.llm_provider = cls.orig_llm

    def test_sequence_a_conversational_chain(self):
        """Sequence A: Hi -> How are you? -> Can you help me study microgravity?"""
        # 1. Greeting
        r1 = self.client.post("/api/rag/ask", json={"question": "Hi"})
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()
        self.assertIsNotNone(d1["answer"])
        self.assertNotIn("Insufficient Evidence", d1["answer"])
        self.assertEqual(len(d1.get("evidence_citations", [])), 0)
        self.assertEqual(len(d1.get("suggested_actions", [])), 0)
        self.assertEqual(d1.get("llm_provider_status", {}).get("provider"), "google-gemini")
        self.assertEqual(d1.get("status"), "gemini_conversation")

        # 2. Follow-up pleasantry
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": d1["answer"]}
        ]
        r2 = self.client.post("/api/rag/ask", json={"question": "How are you?", "conversation_history": history})
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        self.assertIsNotNone(d2["answer"])
        self.assertEqual(len(d2.get("evidence_citations", [])), 0)
        self.assertEqual(len(d2.get("suggested_actions", [])), 0)
        self.assertEqual(d2.get("status"), "gemini_conversation")

        # 3. Conversational capability inquiry
        history.extend([
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": d2["answer"]}
        ])
        r3 = self.client.post("/api/rag/ask", json={"question": "Can you help me study microgravity?", "conversation_history": history})
        self.assertEqual(r3.status_code, 200)
        d3 = r3.json()
        self.assertIsNotNone(d3["answer"])
        self.assertEqual(len(d3.get("evidence_citations", [])), 0)
        self.assertEqual(len(d3.get("suggested_actions", [])), 0)
        self.assertEqual(d3.get("status"), "gemini_conversation")

    def test_sequence_b_educational_and_simplification(self):
        """Sequence B: What is microgravity? -> Explain it simply."""
        # 1. Educational concept
        r1 = self.client.post("/api/rag/ask", json={"question": "What is microgravity?"})
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()
        ans1 = d1["answer"].lower()
        self.assertTrue("microgravity" in ans1 or "weightless" in ans1 or "freefall" in ans1)
        self.assertEqual(len(d1.get("evidence_citations", [])), 0)
        self.assertEqual(len(d1.get("suggested_actions", [])), 0)
        self.assertEqual(d1.get("status"), "gemini_conversation")

        # 2. Conversational simplification
        history = [
            {"role": "user", "content": "What is microgravity?"},
            {"role": "assistant", "content": d1["answer"]}
        ]
        r2 = self.client.post("/api/rag/ask", json={"question": "Explain it simply.", "conversation_history": history})
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        self.assertIsNotNone(d2["answer"])
        self.assertEqual(len(d2.get("evidence_citations", [])), 0)
        self.assertEqual(len(d2.get("suggested_actions", [])), 0)
        self.assertEqual(d2.get("status"), "gemini_conversation")

    def test_sequence_c_scientific_and_visualizations(self):
        """Sequence C: What did NASA find in Saffire-III? -> Show me relevant visualizations."""
        # 1. Empirical research query
        r1 = self.client.post("/api/rag/ask", json={"question": "What did NASA find in Saffire-III?"})
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()
        self.assertEqual(d1.get("status"), "grounded_llm_answer")
        self.assertTrue(len(d1.get("evidence_citations", [])) > 0)
        actions = d1.get("suggested_actions", [])
        self.assertTrue(len(actions) > 0 and len(actions) <= 3)

        # 2. Request for visualizations
        history = [
            {"role": "user", "content": "What did NASA find in Saffire-III?"},
            {"role": "assistant", "content": d1["answer"][:1000]}
        ]
        r2 = self.client.post("/api/rag/ask", json={"question": "Show me relevant visualizations.", "conversation_history": history})
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        actions2 = d2.get("suggested_actions", [])
        tool_tabs = [a.get("tab_id") for a in actions2]
        self.assertIn("dataset-explorer", tool_tabs)

    def test_sequence_d_experiment_comparison(self):
        """Sequence D: Compare Saffire-III Sample 1 and Sample 2."""
        r = self.client.post("/api/rag/ask", json={"question": "Compare Saffire-III Sample 1 and Sample 2."})
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d.get("status"), "grounded_llm_answer")
        ans = d["answer"]
        self.assertTrue("Sample 1" in ans and "Sample 2" in ans)
        actions = d.get("suggested_actions", [])
        tool_tabs = [a.get("tab_id") for a in actions]
        self.assertIn("experiment-comparison", tool_tabs)

    def test_sequence_e_gemini_unavailable_honest_provider_status(self):
        """Sequence E: Gemini unavailable -> honest ai_unavailable status and null answer."""
        unconfigured_provider = GeminiProvider(api_key="")
        synth = GroundedAnswerSynthesizer(llm_provider=unconfigured_provider)

        # 1. Greeting unconfigured -> ai_unavailable
        res_hi = synth.answer("Hi", [])
        self.assertEqual(res_hi["status"], "ai_unavailable")
        self.assertIsNone(res_hi["answer"])
        self.assertEqual(res_hi["error_code"], "GEMINI_UNAVAILABLE")
        self.assertEqual(res_hi["retryable"], False)
        self.assertEqual(res_hi["llm_provider_status"]["is_configured"], False)
        self.assertEqual(res_hi["llm_provider_status"]["provider"], "google-gemini")
        self.assertEqual(res_hi["llm_provider_status"]["status"], "error")
        self.assertEqual(len(res_hi["evidence_citations"]), 0)

        # 2. Educational unconfigured -> ai_unavailable
        res_edu = synth.answer("What is microgravity?", [])
        self.assertEqual(res_edu["status"], "ai_unavailable")
        self.assertIsNone(res_edu["answer"])
        self.assertEqual(res_edu["error_code"], "GEMINI_UNAVAILABLE")

        # 3. Scientific unconfigured -> ai_unavailable
        res_sci = synth.answer("How does oxygen concentration affect flame spread in microgravity?", [])
        self.assertEqual(res_sci["status"], "ai_unavailable")
        self.assertIsNone(res_sci["answer"])
        self.assertEqual(res_sci["error_code"], "GEMINI_UNAVAILABLE")

    def test_sequence_f_missing_scientific_parameter_integrity(self):
        """Sequence F: Missing conditions in records display 'Not recorded' and never invented defaults."""
        synth = GroundedAnswerSynthesizer()
        rec_a = {
            "record_id": "test_exp_a",
            "title": "Test Run A",
            "investigation": "Microgravity Test",
            "experimental_conditions": {
                "fuel_material": "PMMA",
                # missing: oxygen, flow, pressure
            },
            "missing_fields": ["optical_sync"]
        }
        rec_b = {
            "record_id": "test_exp_b",
            "title": "Test Run B",
            "investigation": "Microgravity Test",
            "experimental_conditions": {
                "fuel_material": "Nomex",
                # missing: oxygen, flow, pressure
            },
            "missing_fields": []
        }
        res = synth._generate_comparison_synthesis(
            question="Compare Run A and Run B",
            evidence_items=[rec_a, rec_b],
            entities={"requested_record_ids": ["test_exp_a", "test_exp_b"]},
            reason="test"
        )
        ans = res["answer"]
        # Ensure no invented default values were substituted
        self.assertNotIn("21.0%", ans)
        self.assertNotIn("20.0 cm/s", ans)
        self.assertNotIn("14.7 psia", ans)
        self.assertNotIn("Environmental Equivalence", ans)
        self.assertIn("Not recorded", ans)


if __name__ == "__main__":
    unittest.main()
