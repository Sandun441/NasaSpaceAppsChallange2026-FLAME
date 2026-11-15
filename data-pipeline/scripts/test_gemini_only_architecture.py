#!/usr/bin/env python3
"""
NASA FLAME — Gemini-Only AI Assistant Architecture Verification Suite
Verifies:
1. 100% Gemini generation for all successful conversational and scientific assistant answers.
2. Zero fallback text, zero 9-section retrieval essays, zero canned greetings in user-facing assistant.
3. General conversation mode (greetings, general knowledge, physics definitions): no forced citations, direct answers.
4. NASA scientific research mode: hybrid retrieval, structured evidence grounding, citation validation.
5. Structured error contract (ai_unavailable) when Gemini is unconfigured or fails (honest provider reporting).
6. Specialist workspace deterministic synthesis methods remain preserved.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from api.main import app, rag_synthesizer
from rag.gemini_provider import GeminiProvider


class TestGeminiOnlyAssistantArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.orig_llm = rag_synthesizer.llm_provider

    @classmethod
    def tearDownClass(cls):
        rag_synthesizer.llm_provider = cls.orig_llm

    def setUp(self):
        # Reset provider before each test
        rag_synthesizer.llm_provider = self.orig_llm

    # =========================================================================
    # 1. UNCONFIGURED GEMINI ERROR BEHAVIOR
    # =========================================================================

    def test_unconfigured_gemini_general_query_returns_structured_error(self):
        """Unconfigured Gemini returns status='ai_unavailable', answer=None, no fallback essay."""
        mock_unconf = GeminiProvider(api_key=None)
        self.assertFalse(mock_unconf.is_configured)
        rag_synthesizer.llm_provider = mock_unconf

        res = self.client.post("/api/rag/ask", json={"question": "Hello there!"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "ai_unavailable")
        self.assertIsNone(data["answer"])
        self.assertEqual(data["error_code"], "GEMINI_UNAVAILABLE")
        self.assertFalse(data["retryable"])
        self.assertEqual(data["evidence_citations"], [])
        self.assertEqual(data["llm_provider_status"]["provider"], "google-gemini")
        self.assertEqual(data["llm_provider_status"]["status"], "error")
        self.assertFalse(data["llm_provider_status"]["is_configured"])

    def test_unconfigured_gemini_scientific_query_returns_structured_error(self):
        """Unconfigured Gemini returns status='ai_unavailable', answer=None without fallback 9-section essay."""
        mock_unconf = GeminiProvider(api_key=None)
        rag_synthesizer.llm_provider = mock_unconf

        res = self.client.post("/api/rag/ask", json={
            "question": "What oxygen concentration was tested in Saffire-III Sample 1?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "ai_unavailable")
        self.assertIsNone(data["answer"])
        self.assertEqual(data["error_code"], "GEMINI_UNAVAILABLE")
        self.assertFalse(data["retryable"])
        self.assertEqual(data["evidence_citations"], [])
        self.assertEqual(data["llm_provider_status"]["provider"], "google-gemini")
        self.assertEqual(data["llm_provider_status"]["status"], "error")
        self.assertFalse(data["llm_provider_status"]["is_configured"])

    # =========================================================================
    # 2. GEMINI API ERROR (503 / 429) BEHAVIOR
    # =========================================================================

    def test_gemini_api_error_returns_structured_retryable_error(self):
        """Gemini 503 error returns status='ai_unavailable', retryable=True, answer=None."""
        mock_llm = GeminiProvider(api_key="valid_mock_key")
        mock_llm.generate = MagicMock(return_value={
            "success": False,
            "error": "Gemini API HTTP 503: Service Unavailable",
            "status_code": 503,
            "model": "gemini-3.5-flash-lite",
            "retries_attempted": 3,
        })
        rag_synthesizer.llm_provider = mock_llm

        res = self.client.post("/api/rag/ask", json={
            "question": "How does forced flow affect flame spread in Saffire-III?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "ai_unavailable")
        self.assertIsNone(data["answer"])
        self.assertEqual(data["error_code"], "GEMINI_API_ERROR")
        self.assertTrue(data["retryable"])
        self.assertEqual(data["llm_provider_status"]["provider"], "google-gemini")
        self.assertEqual(data["llm_provider_status"]["status"], "error")
        self.assertEqual(data["llm_provider_status"]["status_code"], 503)

    # =========================================================================
    # 3. GENERAL CONVERSATION (GREETINGS, GENERAL KNOWLEDGE, DEFINITIONS)
    # =========================================================================

    def test_greeting_routes_to_gemini_conversation(self):
        """Greetings invoke Gemini directly with conversation instructions, returning natural response."""
        mock_llm = GeminiProvider(api_key="valid_mock_key")
        captured_calls = []

        def mock_generate(system_instruction, user_prompt):
            captured_calls.append({"system": system_instruction, "prompt": user_prompt})
            return {
                "success": True,
                "raw_text": json.dumps({
                    "answer": "Hello! I am NASA FLAME Research Intelligence. Welcome to microgravity combustion research."
                }),
                "status_code": 200,
                "model": "gemini-3.5-flash-lite",
                "retries_attempted": 0,
            }
        mock_llm.generate = MagicMock(side_effect=mock_generate)
        rag_synthesizer.llm_provider = mock_llm

        res = self.client.post("/api/rag/ask", json={"question": "Hi, who are you?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(len(captured_calls), 1)
        self.assertIn("NASA FLAME Research Intelligence", captured_calls[0]["system"])
        self.assertEqual(data["status"], "gemini_conversation")
        self.assertEqual(data["retrieval_mode"], "gemini_conversation")
        self.assertIn("Welcome to microgravity combustion research", data["answer"])
        self.assertEqual(data["evidence_citations"], [])
        self.assertEqual(data["llm_provider_status"]["provider"], "google-gemini")
        self.assertEqual(data["llm_provider_status"]["status"], "success")

    def test_general_knowledge_query_routes_directly_to_gemini(self):
        """General knowledge query ('What is the capital of France?') answered by Gemini without canned rejection."""
        mock_llm = GeminiProvider(api_key="valid_mock_key")
        captured_calls = []

        def mock_generate(system_instruction, user_prompt):
            captured_calls.append({"system": system_instruction, "prompt": user_prompt})
            return {
                "success": True,
                "raw_text": json.dumps({
                    "answer": "The capital of France is Paris. In NASA FLAME, I can also assist with microgravity combustion!"
                }),
                "status_code": 200,
                "model": "gemini-3.5-flash-lite",
                "retries_attempted": 0,
            }
        mock_llm.generate = MagicMock(side_effect=mock_generate)
        rag_synthesizer.llm_provider = mock_llm

        res = self.client.post("/api/rag/ask", json={"question": "What is the capital of France?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(len(captured_calls), 1)
        self.assertIn("mode", data["llm_provider_status"])
        self.assertEqual(data["llm_provider_status"]["mode"], "general")
        self.assertEqual(data["status"], "gemini_conversation")
        self.assertIn("Paris", data["answer"])
        self.assertNotIn("I cannot answer questions outside", data["answer"])
        self.assertEqual(data["llm_provider_status"]["provider"], "google-gemini")

    def test_educational_definition_routes_directly_to_gemini(self):
        """Physics concept definition ('What is microgravity?') answered by Gemini with clean educational directives."""
        mock_llm = GeminiProvider(api_key="valid_mock_key")
        captured_calls = []

        def mock_generate(system_instruction, user_prompt):
            captured_calls.append({"system": system_instruction, "prompt": user_prompt})
            return {
                "success": True,
                "raw_text": json.dumps({
                    "answer": "**Microgravity** is an environment of apparent weightlessness where gravitational acceleration is balanced by continuous freefall."
                }),
                "status_code": 200,
                "model": "gemini-3.5-flash-lite",
                "retries_attempted": 0,
            }
        mock_llm.generate = MagicMock(side_effect=mock_generate)
        rag_synthesizer.llm_provider = mock_llm

        res = self.client.post("/api/rag/ask", json={"question": "What is microgravity?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(len(captured_calls), 1)
        self.assertEqual(data["llm_provider_status"]["mode"], "educational")
        self.assertEqual(data["status"], "gemini_conversation")
        self.assertIn("apparent weightlessness", data["answer"])
        self.assertEqual(data["evidence_citations"], [])

    # =========================================================================
    # 4. NASA SCIENTIFIC RESEARCH INQUIRY
    # =========================================================================

    def test_scientific_query_routes_to_gemini_with_evidence_and_citations(self):
        """Scientific research query retrieves NASA candidates and validates citations."""
        mock_llm = GeminiProvider(api_key="valid_mock_key")
        captured_calls = []

        def mock_generate(system_instruction, user_prompt):
            captured_calls.append({"system": system_instruction, "prompt": user_prompt})
            return {
                "success": True,
                "raw_text": json.dumps({
                    "answer": "In Saffire-III Sample 1, NASA investigated PMMA flammability [flame_run_saffire_iii_sample_1].",
                    "citation_record_ids": ["flame_run_saffire_iii_sample_1"],
                    "evidence_backed_claims": ["PMMA investigated in Sample 1 [flame_run_saffire_iii_sample_1]"],
                    "scientific_limitations": []
                }),
                "status_code": 200,
                "model": "gemini-3.5-flash-lite",
                "retries_attempted": 0,
            }
        mock_llm.generate = MagicMock(side_effect=mock_generate)
        rag_synthesizer.llm_provider = mock_llm

        res = self.client.post("/api/rag/ask", json={
            "question": "What did NASA investigate in Saffire-III Sample 1?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(len(captured_calls), 1)
        # Verify scientific context was passed to Gemini
        self.assertIn("RESEARCH QUESTION:", captured_calls[0]["prompt"])
        self.assertIn("=== SCIENTIFIC RETRIEVAL EVIDENCE BEGIN ===", captured_calls[0]["prompt"])

        self.assertEqual(data["status"], "grounded_llm_answer")
        self.assertEqual(data["evidence_sufficiency"], "sufficient")
        self.assertGreaterEqual(len(data["evidence_citations"]), 1)
        self.assertEqual(data["evidence_citations"][0]["record_id"], "flame_run_saffire_iii_sample_1")
        self.assertGreaterEqual(len(data.get("suggested_actions", [])), 1)
        self.assertEqual(data["llm_provider_status"]["provider"], "google-gemini")
        self.assertEqual(data["llm_provider_status"]["status"], "success")

    # =========================================================================
    # 5. PRESERVATION OF SPECIALIST WORKSPACE DETERMINISTIC SYNTHESIS
    # =========================================================================

    def test_specialist_earth_investigate_preserves_deterministic_report_when_gemini_unconfigured(self):
        """Specialist Earth Applications investigation retains 9-section deterministic report when unconfigured."""
        mock_unconf = GeminiProvider(api_key=None)
        rag_synthesizer.llm_provider = mock_unconf

        res = self.client.get("/api/earth-applications/EA-EV-BASS-PYRO-01/investigate")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Workspace report contains 9 structured sections
        self.assertEqual(data["status"], "success")
        self.assertIn("### 1. Direct Scientific Answer", data["answer"])
        self.assertIn("### 9. Areas Requiring Additional Terrestrial Validation", data["answer"])
        self.assertEqual(data["investigation"]["status"], "earth_application_retrieval_fallback")
        self.assertEqual(data["investigation"]["evidence_sufficiency"], "sufficient")


if __name__ == "__main__":
    unittest.main()
