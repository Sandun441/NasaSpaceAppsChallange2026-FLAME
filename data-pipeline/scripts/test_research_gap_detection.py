"""
NASA FLAME — Automated Test Suite for Phase RG2: Scientific Research Gap Detection Engine

Verifies:
1. All 6 detection types: coverage_gap, sparse_evidence, measurement_gap, metadata_gap, ingestion_opportunity, comparison_gap.
2. Correct run counts and denominator integrity (133 flight experiment runs).
3. Duplicate prevention: 100% unique, stable finding IDs.
4. Deterministic heuristic ranking and priority score sorting.
5. Unknown and not-applicable parameter handling.
6. Scientific source traceability and evidence confidence justifications.
7. Query filtering and analyze endpoint contracts (structured filters vs free-text limitation).
8. FastAPI HTTP status codes, schema validation, and 404 error handling.
9. Non-regression across existing RG1 coverage, RAG search, and telemetry endpoints.
"""

import sys
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from fastapi.testclient import TestClient
from api.main import app
from research_gaps.gap_detection_service import (
    ResearchGapDetectionService,
    GAP_TYPE_COVERAGE,
    GAP_TYPE_SPARSE,
    GAP_TYPE_MEASUREMENT,
    GAP_TYPE_METADATA,
    GAP_TYPE_INGESTION,
    GAP_TYPE_COMPARISON,
    VALID_GAP_TYPES,
)


def run_tests():
    print("=" * 76)
    print("NASA FLAME — Research Gap Phase RG2: Gap Detection Engine Test Suite")
    print("=" * 76)

    service = ResearchGapDetectionService()
    client = TestClient(app)
    passed_tests = 0
    total_tests = 9

    # ----------------------------------------------------
    # Test 1: All 6 Gap Types Detected
    # ----------------------------------------------------
    print("\n[Test 1/9] Verification of All 6 Canonical Gap Types...")
    findings = service.detect_all_gaps(sparse_threshold=5)
    types_found = set(f["gap_type"] for f in findings)

    assert types_found == VALID_GAP_TYPES, f"Expected {VALID_GAP_TYPES}, got {types_found}"
    for gt in VALID_GAP_TYPES:
        count = sum(1 for f in findings if f["gap_type"] == gt)
        assert count > 0, f"Expected findings for {gt}, got 0"
        print(f"    • {gt}: {count} findings")

    print(f"  ✓ PASSED: All 6 canonical gap types successfully detected ({len(findings)} total findings).")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 2: Duplicate Prevention & ID Stability
    # ----------------------------------------------------
    print("\n[Test 2/9] Duplicate Prevention & Finding ID Stability...")
    finding_ids = [f["finding_id"] for f in findings]
    assert len(finding_ids) == len(set(finding_ids)), f"Duplicate finding IDs detected: {len(finding_ids)} vs {len(set(finding_ids))}"

    for f_id in finding_ids:
        assert f_id.startswith("GAP-"), f"Invalid ID format: {f_id}"

    # Verify repeatable generation across consecutive runs
    findings_run_2 = service.detect_all_gaps(sparse_threshold=5)
    assert [f["finding_id"] for f in findings_run_2] == finding_ids

    print("  ✓ PASSED: 100% of finding IDs are unique, validly formatted, and stable across runs.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 3: Run Counts & Denominator Integrity
    # ----------------------------------------------------
    print("\n[Test 3/9] Denominator Integrity & Exact Experiment Run Accounting...")
    summary = service.coverage_service.load().get("summary", {})
    assert summary.get("total_experiment_runs") == 133, f"Expected 133 runs, got {summary.get('total_experiment_runs')}"

    # Quiescent airflow finding must report exactly 1 observed run
    gap_quiescent = service.get_finding_by_id("GAP-SPARSE-AIRFLOW-QUIESCENT")
    assert gap_quiescent is not None
    assert gap_quiescent["observed_usable_run_count"] == 1
    assert "1 of 133" in gap_quiescent["denominator_and_scope"]

    # Partial lunar gravity must report exactly 0 observed runs
    gap_lunar = service.get_finding_by_id("GAP-COV-GRAV-PARTIAL-LUNAR")
    assert gap_lunar is not None
    assert gap_lunar["observed_usable_run_count"] == 0

    print("  ✓ PASSED: All findings enforce exact numerical denominators against 133 indexed runs.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 4: Deterministic Ranking & Transparent Scoring
    # ----------------------------------------------------
    print("\n[Test 4/9] Deterministic Heuristic Ranking & Transparent Scoring...")
    scores = [f["priority_score"] for f in findings]
    # Verify descending sort order
    assert scores == sorted(scores, reverse=True), "Findings are not sorted by priority score descending"

    for f in findings:
        score = f["priority_score"]
        assert 0.0 <= score <= 10.0, f"Score out of bounds: {score}"
        factors = f["scoring_factors"]
        assert "coverage_deficiency" in factors
        assert "mission_relevance" in factors
        assert "metadata_quality" in factors
        assert "resolvability_feasibility" in factors
        assert "heuristic_label" in factors
        assert "Heuristic" in factors["heuristic_label"]

    print("  ✓ PASSED: Priority scores strictly sorted descending with transparent heuristic factor breakdowns.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 5: Evidence Confidence vs Priority Separation
    # ----------------------------------------------------
    print("\n[Test 5/9] Evidence Confidence vs Priority Separation & Database Scope...")
    for f in findings:
        conf = f["evidence_confidence"]
        assert conf["level"] in ["HIGH", "MEDIUM", "LOW"], f"Invalid confidence level: {conf['level']}"
        assert len(conf["justification"]) > 10, "Confidence justification missing or too short"
        assert "scope" in conf, f"Missing confidence scope in {f['finding_id']}"
        assert "database gap" in conf["scope"].lower() or "flame repository" in conf["scope"].lower()
        # Confidence is an independent dictionary, not a component of priority score

    # Verify CO recommendation safety (Task 3)
    gap_co = service.get_finding_by_id("GAP-MEAS-SAFFIRE-CO")
    assert gap_co is not None
    assert "do not infer co without a validated reaction model" in gap_co["recommended_next_step"].lower()

    # Verify Nomex run count accuracy (Task 2 & 3)
    gap_nomex = service.get_finding_by_id("GAP-SPARSE-FUEL-NOMEX")
    assert gap_nomex is not None
    assert gap_nomex["observed_usable_run_count"] == 4
    assert "(4 Runs)" in gap_nomex["title"]
    assert "4 of 133" in gap_nomex["denominator_and_scope"]

    print("  ✓ PASSED: Evidence confidence strictly decoupled from heuristic priority score and scoped to database gap.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 6: Scientific Traceability & Scope Disclaimers
    # ----------------------------------------------------
    print("\n[Test 6/9] Scientific Traceability & Database Scope Disclaimers...")
    for f in findings:
        assert len(f["provenance_references"]) > 0, f"Missing provenance for {f['finding_id']}"
        assert len(f["limitations"]) > 0, f"Missing scientific limitations for {f['finding_id']}"
        assert len(f["recommended_next_step"]) > 10, f"Missing next step for {f['finding_id']}"
        assert "Unrepresented in the indexed FLAME collection" in f["database_scope_disclaimer"]

    print("  ✓ PASSED: 100% of findings include traceable provenance, limitations, next steps, and disclaimers.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 7: Inquiry Analysis Contract & Free-Text Guard
    # ----------------------------------------------------
    print("\n[Test 7/9] Structured Inquiry Analysis & Free-Text Guardrails...")
    # 1. Condition with zero records (lunar partial gravity)
    res_lunar = service.analyze_inquiry({"gravity": "partial_lunar"})
    assert res_lunar["coverage_status"] == "coverage_gap"
    assert res_lunar["matched_usable_runs_count"] == 0
    assert any(g["finding_id"] == "GAP-COV-GRAV-PARTIAL-LUNAR" for g in res_lunar["applicable_gap_findings"])

    # 2. Condition with robust records (low O2 hypoxic)
    res_low_o2 = service.analyze_inquiry({"oxygen_regime": "low_o2"})
    assert res_low_o2["coverage_status"] == "covered"
    assert res_low_o2["matched_usable_runs_count"] == 59

    # 3. Parameter check
    res_co = service.analyze_inquiry({"parameter": "carbon_monoxide_concentration"})
    assert any(g["finding_id"] == "GAP-MEAS-SAFFIRE-CO" for g in res_co["applicable_gap_findings"])

    # 4. Free-text question without structured parameters (Task 1 fix)
    res_freetext = service.analyze_inquiry({}, question="Can we predict flame spread on lunar soil?")
    assert res_freetext["coverage_status"] == "unsupported_query"
    assert res_freetext["matched_usable_runs_count"] == 0
    assert res_freetext["matched_experiment_ids"] == []
    assert res_freetext["free_text_limitation"] is not None
    assert "RAG Assistant" in res_freetext["free_text_limitation"]
    assert "POST /api/rag/ask" in res_freetext["explanation"]
    assert res_freetext["recommended_action"] is not None

    # 5. Empty inquiry without question or filters
    res_empty = service.analyze_inquiry({})
    assert res_empty["coverage_status"] == "not_evaluated"
    assert res_empty["matched_usable_runs_count"] == 0
    assert res_empty["matched_experiment_ids"] == []

    # 6. Unrecognized condition
    res_unrec = service.analyze_inquiry({"gravity": "jupiter_gravity"})
    assert res_unrec["coverage_status"] == "unknown_or_inapplicable"
    assert res_unrec["matched_usable_runs_count"] == 0
    assert "not recognized" in res_unrec["explanation"]

    # 7. Fuel material search
    res_nomex = service.analyze_inquiry({"fuel_material": "nomex"})
    assert res_nomex["coverage_status"] == "sparse"
    assert res_nomex["matched_usable_runs_count"] == 4
    assert set(res_nomex["matched_experiment_ids"]) == {"bass_ii_f1", "bass_ii_f2", "bass_ii_f3", "saffire_iii_sample_2"}

    print("  ✓ PASSED: Condition matching, parameter checks, free-text RAG limitation, and unknown condition guards validated.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 8: FastAPI RG2 Endpoints Contract
    # ----------------------------------------------------
    print("\n[Test 8/9] FastAPI RG2 Endpoints Contract & Status Codes...")
    # 1. GET /api/research-gaps/findings
    r_findings = client.get("/api/research-gaps/findings?gap_type=coverage_gap&min_priority=7.0")
    assert r_findings.status_code == 200
    data_findings = r_findings.json()
    assert data_findings["status"] == "success"
    assert all(f["gap_type"] == "coverage_gap" for f in data_findings["findings"])
    assert all(f["priority_score"] >= 7.0 for f in data_findings["findings"])

    # 2. GET /api/research-gaps/findings/{finding_id}
    r_detail = client.get("/api/research-gaps/findings/GAP-COV-GRAV-PARTIAL-LUNAR")
    assert r_detail.status_code == 200
    assert r_detail.json()["finding"]["finding_id"] == "GAP-COV-GRAV-PARTIAL-LUNAR"

    # Detail 404 check
    r_404 = client.get("/api/research-gaps/findings/NON_EXISTENT_GAP_ID")
    assert r_404.status_code == 404

    # 3. GET /api/research-gaps/summary (Task 2 audit check)
    r_summary = client.get("/api/research-gaps/summary")
    assert r_summary.status_code == 200
    sum_data = r_summary.json()["summary"]
    assert sum_data["total_findings"] == 21
    assert sum_data["breakdown_by_gap_type"] == {
        "coverage_gap": 6,
        "ingestion_opportunity": 4,
        "measurement_gap": 4,
        "sparse_evidence": 3,
        "comparison_gap": 2,
        "metadata_gap": 2
    }
    assert sum_data["priority_tier_counts"] == {
        "high (>= 7.0)": 16,
        "medium (4.0 - 6.9)": 5,
        "low (< 4.0)": 0
    }
    assert len(sum_data["top_prioritized_findings"]) == 5

    # 4. POST /api/research-gaps/analyze
    r_analyze = client.post("/api/research-gaps/analyze", json={"gravity": "partial_mars", "oxygen_regime": "elevated_o2"})
    assert r_analyze.status_code == 200
    assert r_analyze.json()["analysis"]["coverage_status"] == "coverage_gap"
    assert r_analyze.json()["analysis"]["matched_usable_runs_count"] == 0

    # 5. POST /api/research-gaps/analyze with uninterpreted free-text question
    r_analyze_freetext = client.post("/api/research-gaps/analyze", json={"question": "What is the fire hazard of Nomex in partial gravity?"})
    assert r_analyze_freetext.status_code == 200
    assert r_analyze_freetext.json()["analysis"]["coverage_status"] == "unsupported_query"
    assert r_analyze_freetext.json()["analysis"]["matched_usable_runs_count"] == 0

    print("  ✓ PASSED: All 4 new RG2 FastAPI endpoints returned HTTP 200 with strictly validated schemas and audited totals.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 9: Non-Regression on RG1, Visualization & RAG
    # ----------------------------------------------------
    print("\n[Test 9/9] Non-Regression across RG1 Coverage, Telemetry & RAG...")
    # RG1 Coverage summary
    r_cov_summary = client.get("/api/research-gaps/coverage/summary")
    assert r_cov_summary.status_code == 200
    assert r_cov_summary.json()["summary"]["total_cataloged_datasets"] == 11

    # Telemetry decimation endpoint
    r_telem = client.get("/api/datasets/saffire_iii_sample_1/telemetry?downsample=50")
    assert r_telem.status_code == 200
    assert len(r_telem.json()["telemetry"]) > 0

    # RAG search endpoint
    r_rag = client.post("/api/rag/search", json={"query": "PMMA extinction threshold", "top_k": 3, "mode": "lexical"})
    assert r_rag.status_code == 200
    assert len(r_rag.json()["records"]) > 0

    print("  ✓ PASSED: Zero regressions across existing RG1 coverage, visualization, and RAG services.")
    passed_tests += 1

    print("\n" + "=" * 76)
    print(f"REGRESSION TEST RESULTS: {passed_tests}/{total_tests} Test Suites Passed Successfully (100% Green)")
    print("=" * 76)


if __name__ == "__main__":
    run_tests()
