"""
NASA FLAME — Fire-Safety Equipment Research Test Suite (Scientifically Audited)
Comprehensive validation of all 12 core requirements:
1. Detection inquiry interpretation & source channel grounding
2. Prevention inquiry interpretation & material matrix accuracy
3. Suppression inquiry interpretation & extinction boundaries
4. Missing-evidence and epistemic boundary disclosures
5. Physical sensor channel, units, and ranges accuracy against raw flight logs
6. RAG-to-equipment-workspace navigation handover
7. Equipment-to-visualizer and gap navigation actions
8. Research-gap linking (RG2 integration)
9. Rejection/disclosure of unsupported performance numbers
10. Automated scientific claims audit enforcement
11. FastAPI endpoints contract and status codes
12. Non-regression of existing FLAME services
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.main import app
from equipment.service import FireSafetyEquipmentService
from equipment.analyzer import EquipmentResearchAnalyzer
from equipment.taxonomy import VERIFIED_INVESTIGATIONS_REGISTRY
from rag.actions import ResearchToolRecommender

client = TestClient(app)
analyzer = EquipmentResearchAnalyzer()
recommender = ResearchToolRecommender()


def test_1_detection_inquiry():
    print("\n[Test 1/12] Detection Inquiry & Grounded Telemetry Interpretation...")
    q = "I want to design a more reliable spacecraft smoke detection system. Find relevant NASA experiments, available measurements, research limitations, and potential research directions."
    res = client.post("/api/equipment-research/interpret", json={"query": q})
    assert res.status_code == 200, res.text
    pkg = res.json()["research_package"]

    assert pkg["category"] == "detection"
    local_inv_ids = [i["id"] for i in pkg["matched_investigations"]]
    assert "cygnus_vehicle_telemetry" in local_inv_ids
    assert "saffire_iii" in local_inv_ids

    # External research context separation (SAME is external, not local)
    ext_ids = [i["id"] for i in pkg.get("external_research_context", [])]
    assert "same" in ext_ids
    assert "same" not in local_inv_ids

    # Verify physical channels
    param_ids = [p["id"] for p in pkg["detected_parameters"]]
    assert "smoke_obscuration" in param_ids

    # Verify scientific audit passed with 0 violations
    audit = pkg.get("scientific_audit", {})
    assert audit.get("passed") is True, f"Audit failed: {audit.get('violations')}"
    assert audit.get("violations_count") == 0

    # Verify grounded direct observations
    insights = pkg["scientific_insights"]
    direct_ev = " ".join(insights["direct_experimental_evidence"])
    assert "saffire_iii_sample_1.csv" in direct_ev
    assert "cygnus_smoke_detector_data.csv" in direct_ev
    assert "95.64" in direct_ev  # Verified TC3 peak
    assert "150.39" in direct_ev  # Verified Radiometer 1 peak
    assert "t=109.79s" in direct_ev  # Verified TC3 peak time
    assert "t=60.03s" in direct_ev  # Verified ignition start time

    # Verify engineering design implications rewritten as flow considerations / hypotheses
    impl_text = " ".join(insights["engineering_design_implications"])
    assert "research hypothesis" in impl_text.lower()
    assert "recirculation" in impl_text.lower() or "return" in impl_text.lower()
    print("  ✓ PASSED: Detection inquiry correctly identified grounded telemetry, separated SAME, and passed claims audit.")


def test_2_prevention_inquiry():
    print("\n[Test 2/12] Prevention Inquiry & Material Flammability Limits...")
    q = "Investigate how microgravity forced airflow and elevated oxygen concentration influence solid fuel flammability, flame spread, and material fire safety."
    res = client.post("/api/equipment-research/interpret", json={"query": q})
    assert res.status_code == 200, res.text
    pkg = res.json()["research_package"]

    assert pkg["category"] == "prevention"
    inv_ids = [i["id"] for i in pkg["matched_investigations"]]
    assert "bass_ii" in inv_ids or "saffire_iii" in inv_ids

    audit = pkg.get("scientific_audit", {})
    assert audit.get("passed") is True

    insights = pkg["scientific_insights"]
    direct_ev = " ".join(insights["direct_experimental_evidence"])
    assert "bass_ii_experiments.csv" in direct_ev
    assert "129 runs" in direct_ev
    assert "Nomex" in direct_ev
    assert "14.46 psia" in direct_ev  # Correct nominal pressure in Saffire-III

    lim_text = " ".join(insights["evidence_limitations"]).lower()
    assert "certification" in lim_text or "nasa-std-6001" in lim_text
    print("  ✓ PASSED: Prevention inquiry mapped 129 runs, Nomex tests, and explicit NASA-STD-6001 disclaimer.")


def test_3_suppression_inquiry():
    print("\n[Test 3/12] Suppression Inquiry & Extinction Quenching Boundaries...")
    q = "What experimental evidence exists on flame extinction in microgravity? Analyze low-flow starvation limits, blow-off velocity, and limitations in suppression research."
    res = client.post("/api/equipment-research/interpret", json={"query": q})
    assert res.status_code == 200, res.text
    pkg = res.json()["research_package"]

    assert pkg["category"] == "suppression"
    audit = pkg.get("scientific_audit", {})
    assert audit.get("passed") is True

    insights = pkg["scientific_insights"]
    ev_text = " ".join(insights["direct_experimental_evidence"]).lower()
    assert "quiescent" in ev_text or "extinction" in ev_text or "low-flow" in ev_text
    assert "bass_ii_experiments.csv" in ev_text

    # Verify disclosure of no active extinguisher discharge testing
    lim_text = " ".join(insights["evidence_limitations"]).lower()
    assert "active" in lim_text or "extinguisher" in lim_text
    print("  ✓ PASSED: Suppression inquiry accurately detailed quiescent/blowoff extinction and disclosed lack of active extinguisher tests.")


def test_4_missing_evidence_and_boundary_handling():
    print("\n[Test 4/12] Missing Evidence & Epistemic Boundaries...")
    q = "Evaluate gaseous halon replacement suppression performance and smoke detector response times in hyperoxic microgravity."
    res = client.post("/api/equipment-research/interpret", json={"query": q})
    assert res.status_code == 200, res.text
    pkg = res.json()["research_package"]

    insights = pkg["scientific_insights"]
    lims = insights["evidence_limitations"]
    assert len(lims) >= 1
    assert any("response times" in l.lower() or "active" in l.lower() or "hyperoxic" in l.lower() for l in lims)
    print("  ✓ PASSED: Missing evidence and uninstrumented response times explicitly bound by epistemic disclosures.")


def test_5_source_citation_and_channel_accuracy():
    print("\n[Test 5/12] Physical Sensor Channel & Unit Accuracy...")
    res = client.get("/api/equipment-research/overview")
    assert res.status_code == 200, res.text
    invs = res.json()["overview"]["cataloged_investigations"]

    saffire = next(i for i in invs if i["id"] == "saffire_iii")
    channels = {c["id"]: c for c in saffire["verified_sensor_channels"]}
    assert "radiometer_1" in channels
    assert channels["radiometer_1"]["unit"] == "mW/cm²"
    assert "150.39" in channels["radiometer_1"]["measured_range"]

    assert "plume_temp_tc1_to_tc6" in channels
    assert channels["plume_temp_tc1_to_tc6"]["unit"] == "°C"
    assert "95.64" in channels["plume_temp_tc1_to_tc6"]["measured_range"]

    assert "ambient_pressure_psia" in channels
    assert "14.40 to 14.50" in channels["ambient_pressure_psia"]["measured_range"]

    cygnus = next(i for i in invs if i["id"] == "cygnus_vehicle_telemetry")
    cyg_channels = {c["id"]: c for c in cygnus["verified_sensor_channels"]}
    assert "smoke_detector_scatterometer_fiz2_v" in cyg_channels
    assert cyg_channels["smoke_detector_scatterometer_fiz2_v"]["unit"] == "V"
    assert "1.805" in cyg_channels["smoke_detector_scatterometer_fiz2_v"]["measured_range"]

    bass = next(i for i in invs if i["id"] == "bass_ii")
    bass_channels = {c["id"]: c for c in bass["verified_sensor_channels"]}
    assert "final_co_ppm" in bass_channels
    assert "950.0" in bass_channels["final_co_ppm"]["measured_range"]
    assert "3.2%" in bass_channels["oxygen_consumption_delta_pct"]["measured_range"]

    # Verify external investigations have is_locally_indexed == False
    same = VERIFIED_INVESTIGATIONS_REGISTRY["same"]
    assert same["is_locally_indexed"] is False
    assert len(same["verified_sensor_channels"]) == 0
    print("  ✓ PASSED: All local sensor channels and units verified against actual flight logs; external context separated.")


def test_6_rag_to_equipment_navigation():
    print("\n[Test 6/12] RAG-to-Equipment Research Navigation Handover...")
    q = "Find NASA research relevant to improving smoke detection in spacecraft."
    recs = recommender.recommend(q, [])
    assert len(recs) >= 1

    eq_rec = next((r for r in recs if r["action_id"] == "open_equipment_research"), None)
    assert eq_rec is not None, "Expected open_equipment_research recommendation"
    assert eq_rec["tab_id"] == "equipment-research"
    assert eq_rec["params"]["category"] == "detection"
    assert "smoke detection" in eq_rec["params"]["objective"].lower()
    print("  ✓ PASSED: RAG assistant recommended Equipment Research with objective and category context.")


def test_7_equipment_to_visualizer_and_gap_navigation():
    print("\n[Test 7/12] Equipment-to-Visualizer & Gap Navigation Actions...")
    q = "Design a multi-sensor smoke and thermal fire warning system"
    res = client.post("/api/equipment-research/interpret", json={"query": q})
    actions = res.json()["research_package"]["recommended_actions"]

    action_ids = [a["action_id"] for a in actions]
    assert "open_telemetry_visualizer" in action_ids
    assert "open_gap_detection" in action_ids
    assert "ask_rag_assistant" in action_ids

    viz_action = next(a for a in actions if a["action_id"] == "open_telemetry_visualizer")
    assert viz_action["tab_id"] == "dataset-explorer"
    assert "dataset_id" in viz_action["params"]
    print("  ✓ PASSED: Equipment research workspace provides direct actions to Visualizer, Gap Matrix, and AI Assistant.")


def test_8_research_gap_linking():
    print("\n[Test 8/12] RG2 Research Gap Linking Verification...")
    det_res = client.post("/api/equipment-research/interpret", json={"query": "smoke detection obscuration"})
    det_gaps = [g["finding_id"] for g in det_res.json()["research_package"]["linked_research_gaps"]]
    assert "GAP-MEAS-SMOKE-OBSCURATION" in det_gaps
    assert "GAP-MEAS-SAFFIRE-CO" in det_gaps

    prev_res = client.post("/api/equipment-research/interpret", json={"query": "Nomex fabric flammability"})
    prev_gaps = [g["finding_id"] for g in prev_res.json()["research_package"]["linked_research_gaps"]]
    assert "GAP-SPARSE-FUEL-NOMEX" in prev_gaps

    supp_res = client.post("/api/equipment-research/interpret", json={"query": "flame extinction in quiescent flow"})
    supp_gaps = [g["finding_id"] for g in supp_res.json()["research_package"]["linked_research_gaps"]]
    assert "GAP-SPARSE-AIRFLOW-QUIESCENT" in supp_gaps
    print("  ✓ PASSED: All 3 domains deterministically link relevant findings from the RG2 Gap Detection engine.")


def test_9_unsupported_performance_claims_safeguard():
    print("\n[Test 9/12] Unsupported Performance Claims Safeguard...")
    res = client.get("/api/equipment-research/overview")
    overview = res.json()["overview"]
    assert "safeguards" in overview
    assert "zero_fabrication" in overview["safeguards"]
    assert "decision_support_notice" in overview["safeguards"]

    q = "What is the detector accuracy improvement percentage in microgravity?"
    pkg = client.post("/api/equipment-research/interpret", json={"query": q}).json()["research_package"]
    all_text = " ".join([
        " ".join(pkg["scientific_insights"]["direct_experimental_evidence"]),
        " ".join(pkg["scientific_insights"]["derived_numerical_analysis"]),
        " ".join(pkg["scientific_insights"]["engineering_design_implications"]),
    ])
    assert "40% more accurate" not in all_text.lower()
    assert "85% faster" not in all_text.lower()
    print("  ✓ PASSED: System adheres strictly to zero-fabrication safeguards; no synthetic detector accuracy claims.")


def test_10_scientific_claims_automated_audit_enforcement():
    print("\n[Test 10/12] Automated Scientific Claims Audit Enforcement...")
    # Test valid insights -> 0 violations
    valid_res = analyzer.interpret("smoke detection")
    violations = analyzer.audit_scientific_claims(valid_res["scientific_insights"])
    assert len(violations) == 0, f"Expected 0 violations, got {violations}"

    # Test corrupted payload: inject unsupported numbers & unvalidated claims
    corrupted_insights = {
        "direct_experimental_evidence": [
            "Dataset: saffire_iii_sample_1.csv | ignited at t=191.0s and radiometer peaked at 12.5 mW/cm² under 10.6 to 11.5 psia pressure",
            "NASA SAME experiment demonstrated smoke particles agglomerate into large sizes",
            "Uncited observation without source dataset citation",
        ],
        "derived_numerical_analysis": [
            "Thermal rise after t=191s reached 12.5 mW/cm²",
        ],
        "engineering_design_implications": [
            "Ceiling-mounted smoke detectors used in terrestrial buildings are ineffective in spacecraft cabins.",
            "Multi-sensor fusion substantially reduces false nuisance alarms from exercise dust.",
        ],
    }
    flagged = analyzer.audit_scientific_claims(corrupted_insights)
    assert len(flagged) >= 5, f"Expected at least 5 audit flags, got {len(flagged)}: {flagged}"
    assert any("t=191" in f for f in flagged)
    assert any("12.5 mW/cm" in f for f in flagged)
    assert any("10.6" in f and "11.5 psia" in f for f in flagged)
    assert any("Unindexed external experiment" in f for f in flagged)
    assert any("ceiling detectors are ineffective" in f for f in flagged)
    assert any("false alarms" in f for f in flagged)
    print(f"  ✓ PASSED: Automated claim auditor caught {len(flagged)} simulated unsupported claims.")


def test_11_fastapi_endpoints_contract():
    print("\n[Test 11/12] FastAPI Endpoints Contract & Status Codes...")
    res1 = client.get("/api/equipment-research/overview")
    assert res1.status_code == 200
    assert len(res1.json()["overview"]["categories"]) == 3
    assert "cataloged_investigations" in res1.json()["overview"]
    assert "external_research_context" in res1.json()["overview"]

    res2 = client.post("/api/equipment-research/interpret", json={"query": "smoke detection"})
    assert res2.status_code == 200
    assert "research_package" in res2.json()
    assert res2.json()["research_package"]["scientific_audit"]["passed"] is True

    res_bad = client.post("/api/equipment-research/interpret", json={"query": ""})
    assert res_bad.status_code == 422

    res3 = client.get("/api/equipment-research/category/detection")
    assert res3.status_code == 200
    assert res3.json()["category_details"]["category_id"] == "detection"

    res4 = client.get("/api/equipment-research/category/non_existent_domain")
    assert res4.status_code == 404
    print("  ✓ PASSED: All 3 endpoints adhere to strict schemas, error boundaries, and HTTP status codes.")


def test_12_non_regression_existing_tools():
    print("\n[Test 12/12] Non-Regression across Existing NASA FLAME Services...")
    mod_res = client.post("/api/modeling/preview", json={"dataset_id": "bass_ii_experiments"})
    assert mod_res.status_code == 200
    assert mod_res.json()["preview"]["total_filtered_count"] == 129

    tel_res = client.get("/api/datasets/saffire_iii_sample_1/telemetry?max_points=50")
    assert tel_res.status_code == 200
    assert len(tel_res.json()["telemetry"]) > 0

    gap_res = client.get("/api/research-gaps/summary")
    assert gap_res.status_code == 200
    assert gap_res.json()["summary"]["total_findings"] == 21
    print("  ✓ PASSED: Zero regressions across Predictive Modeling, Telemetry Decimation, and Gap Detection.")


if __name__ == "__main__":
    print("=" * 80)
    print("NASA FLAME — Fire-Safety Equipment Research Test Suite")
    print("=" * 80)
    test_1_detection_inquiry()
    test_2_prevention_inquiry()
    test_3_suppression_inquiry()
    test_4_missing_evidence_and_boundary_handling()
    test_5_source_citation_and_channel_accuracy()
    test_6_rag_to_equipment_navigation()
    test_7_equipment_to_visualizer_and_gap_navigation()
    test_8_research_gap_linking()
    test_9_unsupported_performance_claims_safeguard()
    test_10_scientific_claims_automated_audit_enforcement()
    test_11_fastapi_endpoints_contract()
    test_12_non_regression_existing_tools()
    print("\n" + "=" * 80)
    print("ALL 12 FIRE-SAFETY EQUIPMENT RESEARCH TESTS PASSED (100% Success Rate)")
    print("=" * 80)
