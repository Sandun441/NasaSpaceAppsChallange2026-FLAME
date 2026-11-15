"""
NASA FLAME — Automated Test Suite for Phase RG4: Grounded RAG Integration & Scientific Validation

Verifies:
1. Deterministic finding retrieval via RG2 service (no hallucinated findings).
2. Finding-to-RAG context transfer: dimensions, denominator, and finding ID correctly assembled.
3. Grounded research explanation in retrieval-only mode delivers all 5 mandatory scientific categories.
4. Epistemic boundary notice: missing FLAME data is never claimed to prove global absence.
5. Priority score clearly labeled as engineering heuristic, not physical combustion parameter.
6. Context-aware dashboard action recommendations (Visualizer, Comparison, Gap Explorer).
7. FastAPI endpoint contracts: POST /api/rag/ask with finding_id and GET /api/research-gaps/findings/{id}/investigate.
8. Error handling and 404 fallback for non-existent findings.
9. Mocked LLM integration with citation validation.
10. Non-regression across existing RG1, RG2, and RAG R4 baselines.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock
import json

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from fastapi.testclient import TestClient
from api.main import app
from research_gaps.gap_detection_service import ResearchGapDetectionService
from rag.context import GroundedContextAssembler
from rag.actions import ResearchToolRecommender
from rag.llm import GroundedAnswerSynthesizer, GeminiProvider


def run_tests():
    print("=" * 76)
    print("NASA FLAME — Phase RG4: Grounded RAG Integration & Validation Test Suite")
    print("=" * 76)

    client = TestClient(app)
    gap_service = ResearchGapDetectionService()
    passed_tests = 0
    total_tests = 10

    # ----------------------------------------------------
    # Test 1: Deterministic Finding Retrieval via RG2 Service
    # ----------------------------------------------------
    print("\n[Test 1/10] Deterministic Finding Retrieval via RG2 Service...")
    sample_finding_id = "GAP-COV-GRAV-PARTIAL-LUNAR"
    finding = gap_service.get_finding_by_id(sample_finding_id)

    assert finding is not None, f"Expected finding {sample_finding_id} to exist"
    assert finding["finding_id"] == sample_finding_id
    assert "Lunar Gravity" in finding["title"]
    assert finding["gap_type"] == "coverage_gap"
    assert finding["observed_usable_run_count"] == 0
    print(f"    • Finding ID: {finding['finding_id']}")
    print(f"    • Finding Title: {finding['title']}")
    print(f"    • Gap Type: {finding['gap_type']} (0 of 133 runs)")
    print("  ✓ PASSED: Authoritative RG2 finding deterministically retrieved.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 2: Context Assembler Finding Block & Citation Whitelist
    # ----------------------------------------------------
    print("\n[Test 2/10] Context Assembler Finding Block & Allowed Citation Whitelist...")
    assembler = GroundedContextAssembler()
    mock_evidence = [
        {
            "record_id": "flame_saffire_001",
            "experiment_id": "saffire_iii_sample_1",
            "investigation_name": "Saffire-III",
            "usable": True,
            "fuel_material": "PMMA",
            "content": "Saffire-III Sample 1 burned PMMA in microgravity at 21% O2.",
            "data_quality_warnings": [],
            "source_provenance": "NASA Telemetry File",
        }
    ]

    context_result = assembler.assemble(
        retrieved_records=mock_evidence,
        research_question="What is the coverage status?",
        finding=finding,
    )

    context_str = context_result["assembled_text"]
    allowed_citations = context_result["allowed_citation_ids"]

    assert "DETERMINISTIC RESEARCH GAP FINDING FROM RG2 SERVICE" in context_str
    assert sample_finding_id in context_str
    assert "Lunar Gravity" in context_str
    assert sample_finding_id in allowed_citations
    assert "flame_saffire_001" in allowed_citations
    print(f"    • Injected finding block size: {len(context_str)} chars")
    print(f"    • Allowed citations: {allowed_citations}")
    print("  ✓ PASSED: Finding context correctly formatted with citation allowance.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 3: Grounded Synthesis with 5 Mandatory Scientific Sections
    # ----------------------------------------------------
    print("\n[Test 3/10] Retrieval-Only Grounded Synthesis 5 Mandatory Sections...")
    # Force provider without key to test retrieval-only deterministic synthesis
    synthesizer = GroundedAnswerSynthesizer(llm_provider=GeminiProvider(api_key=None))
    response = synthesizer.answer(
        question=f"Investigate coverage and scientific context for {sample_finding_id}",
        retrieved_candidates=mock_evidence,
        finding=finding,
    )

    answer_text = response["answer"]
    assert response["status"] in ("grounded_gap_synthesis", "retrieval_only_fallback")
    assert response.get("finding", {}).get("finding_id") == sample_finding_id

    # Verify all 5 mandatory scientific categories
    section_headers = [
        "Verified Experimental Observations in FLAME",
        "Deterministic Database Gap Analysis",
        "Scientific Interpretation & Exploration Mission Significance",
        "Actionable Next Steps & Proposed Future Research",
        "Epistemic Boundary Notice & Missing Information Disclosure",
    ]
    for sh in section_headers:
        assert sh in answer_text, f"Missing required scientific section: {sh}"
        print(f"    • Verified section header present: '{sh}'")

    print("  ✓ PASSED: All 5 mandatory scientific categories generated in retrieval-only mode.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 4: Epistemic Boundary Notice & Absence Disclaimers
    # ----------------------------------------------------
    print("\n[Test 4/10] Epistemic Boundary Notice & Global vs Local Absence Disclaimers...")
    assert "Missing data in FLAME does not prove NASA never conducted an experiment" in answer_text
    assert "0 of 133" in answer_text
    print("    • Epistemic boundary correctly states missing FLAME data != global scientific absence.")
    print("  ✓ PASSED: Epistemic boundary disclaimers strictly adhered to.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 5: Priority Score Transparent Engineering Heuristic Notice
    # ----------------------------------------------------
    print("\n[Test 5/10] Priority Score Heuristic Disclosure...")
    assert "engineering triage heuristics, not physical laws of combustion" in answer_text
    print("    • Transparent disclaimer verified: heuristic priority is not a physical measurement.")
    print("  ✓ PASSED: Engineering ranking heuristic clearly communicated.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 6: Context-Aware Navigation Recommendations
    # ----------------------------------------------------
    print("\n[Test 6/10] Context-Aware Tool Recommendations for Research Gaps...")
    recommender = ResearchToolRecommender()
    sparse_finding = gap_service.get_finding_by_id("GAP-SPARSE-OX-ELEVATED-SAFFIRE")
    assert sparse_finding is not None

    actions = recommender.recommend(
        question="Investigate elevated oxygen gap",
        retrieved_evidence=mock_evidence,
        finding=sparse_finding,
    )

    tool_names = [a["tool_name"] for a in actions]
    tab_ids = [a["tab_id"] for a in actions]
    print(f"    • Recommended tools: {tool_names}")
    print(f"    • Target tabs: {tab_ids}")

    assert "dataset-explorer" in tab_ids or "gap-detection" in tab_ids
    assert any(a["tool_name"] == "Scientific Telemetry Visualizer" or a["tool_name"] == "Research-Gap Detection" for a in actions)
    print("  ✓ PASSED: High-value dashboard action recommendations produced.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 7: FastAPI POST /api/rag/ask with finding_id
    # ----------------------------------------------------
    print("\n[Test 7/10] FastAPI POST /api/rag/ask Contract with finding_id...")
    req_body = {
        "question": f"What is the research gap in {sample_finding_id}?",
        "top_k": 5,
        "finding_id": sample_finding_id,
    }
    api_resp = client.post("/api/rag/ask", json=req_body)
    assert api_resp.status_code == 200, f"Expected 200, got {api_resp.status_code}: {api_resp.text}"

    data = api_resp.json()
    assert data["status"] in ("grounded_answer", "grounded_gap_synthesis", "retrieval_only_fallback")
    assert data["finding_id"] == sample_finding_id
    citation_ids = [c["record_id"] for c in data.get("evidence_citations", [])]
    assert sample_finding_id in citation_ids
    assert "Deterministic Database Gap Analysis" in data["answer"]
    print(f"    • HTTP 200 OK — Finding {data['finding_id']} grounded in response.")
    print("  ✓ PASSED: /api/rag/ask contract with finding_id verified.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 8: FastAPI GET /api/research-gaps/findings/{id}/investigate
    # ----------------------------------------------------
    print("\n[Test 8/10] FastAPI GET /api/research-gaps/findings/{id}/investigate...")
    inv_resp = client.get(f"/api/research-gaps/findings/{sample_finding_id}/investigate")
    assert inv_resp.status_code == 200, f"Expected 200, got {inv_resp.status_code}: {inv_resp.text}"

    inv_data = inv_resp.json()
    assert inv_data["status"] == "success"
    assert inv_data["finding_id"] == sample_finding_id
    assert "investigation" in inv_data
    assert "suggested_actions" in inv_data
    print(f"    • HTTP 200 OK — Investigate endpoint returned complete scientific package.")

    # Check 404 for non-existent finding
    bad_resp = client.get("/api/research-gaps/findings/GAP-NON-EXISTENT-999/investigate")
    assert bad_resp.status_code == 404, f"Expected 404 for bad finding, got {bad_resp.status_code}"
    print("    • HTTP 404 correctly returned for non-existent finding ID.")
    print("  ✓ PASSED: Dedicated investigate endpoint and error boundaries verified.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 9: Mocked Gemini LLM Integration with Grounding Validation
    # ----------------------------------------------------
    print("\n[Test 9/10] Mocked Gemini LLM Synthesis with Grounding Validation...")
    mock_provider = MagicMock(spec=GeminiProvider)
    mock_provider.is_configured.return_value = True
    mock_provider.model_name = "gemini-3.5-flash-lite"
    mock_provider.generate.return_value = {
        "success": True,
        "raw_text": json.dumps({
            "answer": (
                "### 1. Verified Experimental Observations in FLAME\n"
                "Testing showed PMMA combustion [flame_saffire_001].\n\n"
                "### 2. Deterministic Database Gap Analysis (Phase RG2 Engine)\n"
                "According to authoritative finding [GAP-COV-GRAV-PARTIAL-LUNAR], zero lunar atmosphere runs exist.\n\n"
                "### 3. Scientific Interpretation & Exploration Mission Significance\n"
                "Lunar gravity at 34% O2 represents a critical Artemis exploration gap.\n\n"
                "### 4. Actionable Next Steps & Proposed Future Research\n"
                "Ingest planned Artemis test flight records.\n\n"
                "### 5. Epistemic Boundary Notice & Missing Information Disclosure\n"
                "Unrepresented in FLAME database (0 of 133 runs)."
            ),
            "evidence_backed_claims": ["PMMA combustion demonstrated [flame_saffire_001]"],
            "citation_record_ids": ["flame_saffire_001", "GAP-COV-GRAV-PARTIAL-LUNAR"],
            "scientific_limitations": ["Limited to FLAME collection (0 of 133 runs)"],
            "relevant_experiment_ids": ["saffire_iii_sample_1"],
            "evidence_sufficiency": "sufficient",
        }),
        "status_code": 200,
        "model": "gemini-3.5-flash-lite",
        "retries_attempted": 0,
    }

    synth_with_mock = GroundedAnswerSynthesizer(llm_provider=mock_provider)
    mock_ans = synth_with_mock.answer(
        question="Analyze lunar atmospheric gap",
        retrieved_candidates=mock_evidence,
        finding=finding,
    )

    assert mock_ans["status"] in ("grounded_answer", "grounded_llm_answer")
    mock_citation_ids = [c["record_id"] for c in mock_ans.get("evidence_citations", [])]
    assert sample_finding_id in mock_citation_ids
    assert "flame_saffire_001" in mock_citation_ids
    print("    • Mocked Gemini successfully produced citation-verified grounded synthesis.")
    print("  ✓ PASSED: Mocked Gemini LLM synthesis and citation whitelist validated.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 10: Non-Regression across Baseline Suites
    # ----------------------------------------------------
    print("\n[Test 10/10] Non-Regression across RG1, RG2, and RAG Baselines...")
    # RG1 Coverage baseline
    cov_resp = client.get("/api/research-gaps/coverage/summary")
    assert cov_resp.status_code == 200
    cov_data = cov_resp.json()
    assert cov_data["summary"]["total_experiment_runs"] == 133
    assert cov_data["summary"]["unprocessed_raw_assets_count"] == 11

    # RG2 Finding baseline
    all_findings = gap_service.detect_all_gaps()
    assert len(all_findings) == 21, f"Expected 21 findings, got {len(all_findings)}"

    # RAG Search baseline
    rag_resp = client.post("/api/rag/search", json={"query": "PMMA flame spread", "top_k": 3})
    assert rag_resp.status_code == 200
    rag_data = rag_resp.json()
    assert len(rag_data["records"]) > 0

    print("    • RG1 Coverage: 133 usable runs, 11 raw assets verified.")
    print("    • RG2 Detection: Exactly 21 canonical findings preserved.")
    print("    • RAG Search: Hybrid retrieval operational.")
    print("  ✓ PASSED: Complete non-regression verified.")
    passed_tests += 1

    # ----------------------------------------------------
    # Summary
    # ----------------------------------------------------
    print("\n" + "=" * 76)
    print(f"ALL TESTS PASSED: {passed_tests} / {total_tests} (100% Success Rate)")
    print("NASA FLAME Phase RG4 Grounded RAG Integration is verified and scientifically sound.")
    print("=" * 76)
    return True


if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
