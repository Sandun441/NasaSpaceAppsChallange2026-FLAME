"""
NASA FLAME — Baseline Verification Suite for rag/llm.py (Gemini-Only Architecture)
Captures behaviors across representative scenarios:
- Gemini generates 100% of successful conversational and scientific answers.
- General conversation (greetings, pleasantries, educational concepts, general knowledge) routes through Gemini directly.
- Scientific questions assemble grounded context and validate citations.
- Unconfigured Gemini or API errors return honest ai_unavailable status (no synthetic fallback essays).
- Deterministic analysis modules remain 100% intact for specialist workspaces.
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock
import json

# Add data-pipeline root
base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir))

from rag.llm import GroundedAnswerSynthesizer, GeminiProvider, DEFAULT_GEMINI_MODEL
from rag.search import ScientificKnowledgeStore


class TestLlmRefactorBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records_path = base_dir / "processed_data" / "rag" / "scientific_knowledge_records.json"
        cls.store = ScientificKnowledgeStore(records_path)
        cls.store.load()
        cls.synth_unconfigured = GroundedAnswerSynthesizer(llm_provider=GeminiProvider(api_key=""))

        # Configured Gemini mock provider
        cls.mock_llm = GeminiProvider(api_key="mock_valid_key")
        def mock_generate(system_instruction, user_prompt):
            import re
            p_lower = user_prompt.lower()
            if "capital of france" in p_lower:
                return {
                    "success": True,
                    "raw_text": json.dumps({"answer": "The capital of France is Paris."}),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0,
                }
            elif "explain it simply" in p_lower:
                return {
                    "success": True,
                    "raw_text": json.dumps({"answer": "Without gravity, hot air doesn't rise, so flames become spherical balls shaped by diffusion."}),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0,
                }
            elif "what is microgravity" in p_lower or "concept of microgravity" in p_lower:
                return {
                    "success": True,
                    "raw_text": json.dumps({"answer": "**Microgravity** is an environment of apparent weightlessness where gravitational acceleration is balanced by continuous freefall ($u_b \\approx 0$)."}),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0,
                }
            elif re.search(r"\b(hi|hello|how are you)\b", p_lower) and "research question:" not in p_lower:
                return {
                    "success": True,
                    "raw_text": json.dumps({"answer": "Hello! I am NASA FLAME Research Intelligence, ready to assist with microgravity combustion research."}),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0,
                }
            elif "oxygen" in p_lower:
                return {
                    "success": True,
                    "raw_text": json.dumps({
                        "answer": "In microgravity, oxygen concentration directly influences the flame spread rate [flame_run_saffire_iii_sample_1].",
                        "evidence_backed_claims": ["Oxygen governs flame spread [flame_run_saffire_iii_sample_1]"],
                        "citation_record_ids": ["flame_run_saffire_iii_sample_1"],
                        "scientific_limitations": ["Continuous DAQ duration differs from flame duration."]
                    }),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0,
                }
            elif "compare" in p_lower:
                return {
                    "success": True,
                    "raw_text": json.dumps({
                        "answer": "Comparing Saffire-III Sample 1 (SIBAL fabric) [flame_run_saffire_iii_sample_1] and Sample 2 (Nomex) [flame_run_saffire_iii_sample_2].",
                        "evidence_backed_claims": [
                            "Sample 1 tested SIBAL [flame_run_saffire_iii_sample_1]",
                            "Sample 2 tested Nomex [flame_run_saffire_iii_sample_2]"
                        ],
                        "citation_record_ids": ["flame_run_saffire_iii_sample_1", "flame_run_saffire_iii_sample_2"],
                        "scientific_limitations": []
                    }),
                    "status_code": 200,
                    "model": DEFAULT_GEMINI_MODEL,
                    "retries_attempted": 0,
                }
            return {
                "success": True,
                "raw_text": json.dumps({"answer": "General response generated by Gemini."}),
                "status_code": 200,
                "model": DEFAULT_GEMINI_MODEL,
                "retries_attempted": 0,
            }
        cls.mock_llm.generate = MagicMock(side_effect=mock_generate)
        cls.synth_configured = GroundedAnswerSynthesizer(llm_provider=cls.mock_llm)

    def _retrieve(self, q: str, top_k: int = 8):
        return self.store.search_hybrid(query=q, top_k=top_k, mode="hybrid").get("records", [])

    # 1. "Hi" -> Gemini Conversational Answer
    def test_01_greeting_hi(self):
        res = self.synth_configured.answer("Hi", [])
        self.assertEqual(res["status"], "gemini_conversation")
        self.assertEqual(res["llm_provider_status"]["provider"], "google-gemini")
        self.assertEqual(res["llm_provider_status"]["status"], "success")
        self.assertIn("NASA FLAME", res["answer"])
        self.assertEqual(len(res["evidence_citations"]), 0)

    # 2. "How are you?" -> Gemini Pleasantry
    def test_02_pleasantry_how_are_you(self):
        res = self.synth_configured.answer("How are you?", [])
        self.assertEqual(res["status"], "gemini_conversation")
        self.assertEqual(res["llm_provider_status"]["provider"], "google-gemini")
        self.assertIn("NASA FLAME", res["answer"])

    # 3. "What is microgravity?" -> Gemini Educational Definition
    def test_03_educational_definition(self):
        res = self.synth_configured.answer("What is microgravity?", [])
        self.assertEqual(res["status"], "gemini_conversation")
        self.assertEqual(res["llm_provider_status"]["provider"], "google-gemini")
        self.assertIn("Microgravity", res["answer"])

    # 4. "Explain it simply." -> Gemini Simplification Followup
    def test_04_simplification_followup(self):
        hist = [{"role": "user", "content": "What is microgravity?"}, {"role": "assistant", "content": "Microgravity definition"}]
        res = self.synth_configured.answer("Explain it simply.", [], conversation_history=hist)
        self.assertEqual(res["status"], "gemini_conversation")
        self.assertEqual(res["llm_provider_status"]["provider"], "google-gemini")
        self.assertIn("flames", res["answer"].lower())

    # 5. "What is the capital of France?" -> Gemini General Knowledge (No domain restriction template)
    def test_05_general_knowledge_query(self):
        res = self.synth_configured.answer("What is the capital of France?", [])
        self.assertEqual(res["status"], "gemini_conversation")
        self.assertEqual(res["llm_provider_status"]["provider"], "google-gemini")
        self.assertIn("Paris", res["answer"])

    # 6. "How does oxygen affect flame spread in microgravity?" -> Grounded NASA Research
    def test_06_scientific_oxygen_flame_spread(self):
        cands = self._retrieve("How does oxygen affect flame spread in microgravity?")
        res = self.synth_configured.answer("How does oxygen affect flame spread in microgravity?", cands)
        self.assertEqual(res["status"], "grounded_llm_answer")
        self.assertEqual(res["llm_provider_status"]["provider"], "google-gemini")
        self.assertTrue(len(res["evidence_citations"]) > 0)
        self.assertTrue(len(res["suggested_actions"]) > 0)

    # 7. "Compare Saffire-III Sample 1 and Sample 2." -> Grounded Comparison
    def test_07_compare_saffire_samples(self):
        cands = self._retrieve("Compare Saffire-III Sample 1 and Sample 2.")
        res = self.synth_configured.answer("Compare Saffire-III Sample 1 and Sample 2.", cands)
        self.assertEqual(res["status"], "grounded_llm_answer")
        self.assertTrue(len(res["evidence_citations"]) >= 2)
        tool_tabs = [a.get("tab_id") for a in res["suggested_actions"]]
        self.assertIn("experiment-comparison", tool_tabs)

    # 8. Deterministic Measurement Audit Synthesis Functionality (Specialist Workspaces)
    def test_08_deterministic_measurement_audit(self):
        cands = self._retrieve("What are the extinction times in Saffire-III?")
        res = self.synth_unconfigured._generate_measurement_audit_synthesis(
            question="What are the extinction times in Saffire-III?",
            evidence_items=cands,
            entities={"requested_record_ids": ["flame_run_saffire_iii_sample_1"]},
        )
        self.assertIn("Extinction Time Status", res["answer"])
        self.assertIn("Scientific Reliability", res["answer"])

    # 9. Deterministic Research Gap Synthesis Functionality (Specialist Workspaces)
    def test_09_deterministic_gap_investigation(self):
        finding = {
            "finding_id": "GAP-ENV-001",
            "title": "Partial Gravity Combustion Gap",
            "priority_score": 9.2,
            "evidence_confidence": {"level": "HIGH", "justification": "Verified across flight database"},
            "denominator": "BASS-II / Saffire flight database",
            "explanation": "Limited empirical data in 0.16g and 0.38g regimes.",
            "scientific_dimensions": {"fuel_material": "PMMA"}
        }
        cands = self._retrieve("What research gaps exist under lunar gravity?")
        res = self.synth_unconfigured._generate_gap_investigation_synthesis(
            finding=finding,
            question="What research gaps exist under lunar gravity?",
            evidence_items=cands,
        )
        self.assertIn("GAP-ENV-001", res["answer"])
        self.assertIn("Deterministic Database Gap Analysis", res["answer"])

    # 10. Deterministic Earth Application Synthesis Functionality (Specialist Workspaces)
    def test_10_deterministic_earth_application_transfer(self):
        ev = self.synth_unconfigured.earth_adapter.service.get_evidence_by_id("EA-EV-BASS-PYRO-01")
        earth_ev = [ev.model_dump() if hasattr(ev, "model_dump") else ev.dict()]
        cands = self._retrieve("How could NASA fire research inform building safety?")
        res = self.synth_unconfigured._generate_earth_application_synthesis(
            question="How could NASA fire research inform building safety?",
            earth_items=earth_ev,
            retrieved_candidates=cands,
        )
        self.assertIn("EA-EV-BASS-PYRO-01", res["answer"])
        self.assertIn("Terrestrial", res["answer"])

    # 11. Gemini Unavailable -> Honest ai_unavailable status and null answer
    def test_11_gemini_unavailable_honest_status(self):
        res = self.synth_unconfigured.answer("Hi", [])
        self.assertEqual(res["status"], "ai_unavailable")
        self.assertIsNone(res["answer"])
        self.assertEqual(res["error_code"], "GEMINI_UNAVAILABLE")
        self.assertEqual(res["retryable"], False)
        self.assertEqual(res["llm_provider_status"]["is_configured"], False)
        self.assertEqual(res["llm_provider_status"]["provider"], "google-gemini")
        self.assertEqual(res["llm_provider_status"]["status"], "error")

    # 12. Gemini HTTP Failure -> Honest ai_unavailable status with retryable flag
    def test_12_gemini_http_failure_handling(self):
        mock_provider = GeminiProvider(api_key="mock_key")
        mock_provider.generate = MagicMock(return_value={
            "success": False,
            "error": "Gemini API HTTP 503: Service Unavailable",
            "status_code": 503,
            "retries_attempted": 3,
            "raw_text": None,
        })
        synth = GroundedAnswerSynthesizer(llm_provider=mock_provider)
        cands = self._retrieve("How does oxygen affect flame spread in microgravity?")
        res = synth.answer("How does oxygen affect flame spread in microgravity?", cands)
        self.assertEqual(res["status"], "ai_unavailable")
        self.assertIsNone(res["answer"])
        self.assertEqual(res["error_code"], "GEMINI_API_ERROR")
        self.assertEqual(res["retryable"], True)
        self.assertEqual(res["llm_provider_status"]["status"], "error")
        self.assertEqual(res["llm_provider_status"]["status_code"], 503)
        self.assertEqual(res["llm_provider_status"]["provider"], "google-gemini")

    # 13. Missing experimental metadata in comparison synthesis
    def test_13_missing_experimental_metadata_handling(self):
        rec_a = {
            "record_id": "test_rec_a",
            "title": "Test Run A",
            "investigation": "Microgravity Test",
            "experimental_conditions": {"fuel_material": "PMMA"},
            "missing_fields": []
        }
        rec_b = {
            "record_id": "test_rec_b",
            "title": "Test Run B",
            "investigation": "Microgravity Test",
            "experimental_conditions": {"fuel_material": "Nomex"},
            "missing_fields": []
        }
        res = self.synth_unconfigured._generate_comparison_synthesis(
            question="Compare A and B",
            evidence_items=[rec_a, rec_b],
            entities={"requested_record_ids": ["test_rec_a", "test_rec_b"]},
            reason="test"
        )
        self.assertIn("Not recorded", res["answer"])
        self.assertNotIn("21.0%", res["answer"])
        self.assertNotIn("20.0 cm/s", res["answer"])
        self.assertNotIn("14.7 psia", res["answer"])

    # 14. Invalid citation IDs purged
    def test_14_invalid_citation_purged(self):
        allowed_ids = ["flame_rec_01", "flame_rec_02"]
        raw_citations = ["flame_rec_01", "hallucinated_record_999"]
        valid, invalid = self.synth_unconfigured._validate_citations(
            raw_citations=raw_citations,
            allowed_ids=allowed_ids,
            answer_text="Claim citing [flame_rec_01] and [hallucinated_record_999]."
        )
        self.assertIn("flame_rec_01", valid)
        self.assertIn("hallucinated_record_999", invalid)


if __name__ == "__main__":
    unittest.main()
