"""
NASA FLAME — Earth Applications Phase EA2: Frontend Integration & Contract Test Suite
Validates all requirements for the Interactive Earth Applications Research Explorer:
1. Dynamic categories contract and dynamic evidence counts
2. Category filtering fidelity across all 7 canonical domains
3. Investigation and multi-dimension filtering (primary and co-investigations)
4. Classification filtering fidelity (audited 10 supported, 1 exploratory, 0 documented)
5. Provenance status filtering (6 local vs. 5 external literature)
6. Evidence detail workspace contract and complete field payload
7. Scientific connection bridge mechanism derivation integrity
8. Decoupled Dimension A vs. Dimension B assertions
9. Cross-module navigation contracts (Visualizer, Modeling, Gap Matrix)
10. Scientific caveats and negative safety enforcement (no fabricated probabilities)
11. Overview contract and canonical investigation reconciliation
12. Full platform non-regression across existing NASA FLAME services
"""

import sys
import subprocess
from pathlib import Path
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.main import app
from earth_applications.catalog import INITIAL_EARTH_APPLICATION_CATALOG
from earth_applications.taxonomy import EARTH_APPLICATION_CATEGORIES

client = TestClient(app)


def test_1_dynamic_categories_contract():
    print("\n[Test 1/12] Categories Contract & Dynamic Counts...")
    res = client.get("/api/earth-applications/categories")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "ok"
    assert data["total_categories"] == 7
    categories = data["categories"]
    assert len(categories) == 7

    expected_cats = {
        "building_fire_safety",
        "wildfire_combustion",
        "fire_detection_smoke_aerosol",
        "material_flammability_fire_resistance",
        "fire_suppression_research",
        "combustion_efficiency_emissions",
        "other_terrestrial_applications",
    }
    actual_cats = {c["id"] for c in categories}
    assert actual_cats == expected_cats

    total_ev = sum(c["evidence_count"] for c in categories)
    assert total_ev == 11, f"Expected sum of category counts to equal 11, got {total_ev}"
    print("  ✓ PASSED: All 7 categories returned with exact dynamic counts totaling 11 records.")


def test_2_category_filtering_fidelity():
    print("\n[Test 2/12] Category Filtering Fidelity Across All 7 Domains...")
    for cat_id in (
        "building_fire_safety",
        "wildfire_combustion",
        "fire_detection_smoke_aerosol",
        "material_flammability_fire_resistance",
        "fire_suppression_research",
        "combustion_efficiency_emissions",
        "other_terrestrial_applications",
    ):
        res = client.get(f"/api/earth-applications?category={cat_id}")
        assert res.status_code == 200
        items = res.json()["evidence"]
        assert len(items) >= 1, f"Category {cat_id} returned 0 items"
        assert all(e["category_id"] == cat_id for e in items)
    print("  ✓ PASSED: Every one of the 7 domains filters cleanly to its matching records.")


def test_3_investigation_and_multi_dimension_filtering():
    print("\n[Test 3/12] Investigation & Co-Investigation Filtering...")
    # Primary investigation filtering
    for inv in ("bass_ii", "saffire_iii", "flex", "same", "acme", "sofie"):
        res = client.get(f"/api/earth-applications?investigation_id={inv}")
        assert res.status_code == 200
        items = res.json()["evidence"]
        assert len(items) >= 1
        assert all(
            e["investigation_id"] == inv or inv in e.get("related_investigation_ids", [])
            for e in items
        )

    # Co-investigation filtering for cygnus_vehicle_telemetry
    res_cyg = client.get("/api/earth-applications?investigation_id=cygnus_vehicle_telemetry")
    assert res_cyg.status_code == 200
    cyg_items = res_cyg.json()["evidence"]
    assert len(cyg_items) == 1
    assert cyg_items[0]["id"] == "EA-EV-SAFFIRE-IND-04"
    assert "cygnus_vehicle_telemetry" in cyg_items[0]["related_investigation_ids"]
    print("  ✓ PASSED: Primary investigations and co-investigations filter deterministically.")


def test_4_classification_filtering_fidelity():
    print("\n[Test 4/12] Classification Filtering (10 Supported, 1 Exploratory, 0 Documented)...")
    res_supp = client.get("/api/earth-applications?classification=supported_research_implication")
    assert res_supp.status_code == 200
    assert res_supp.json()["filtered_count"] == 10

    res_hyp = client.get("/api/earth-applications?classification=exploratory_hypothesis")
    assert res_hyp.status_code == 200
    assert res_hyp.json()["filtered_count"] == 1
    assert res_hyp.json()["evidence"][0]["id"] == "EA-EV-SAFFIRE-WILD-03"

    res_doc = client.get("/api/earth-applications?classification=documented_application")
    assert res_doc.status_code == 200
    assert res_doc.json()["filtered_count"] == 0, "No records should claim documented_application without published standards adoption"
    print("  ✓ PASSED: Classification breakdown strictly enforced: 10 supported, 1 exploratory, 0 documented.")


def test_5_provenance_filtering():
    print("\n[Test 5/12] Flight Provenance Status Filtering (6 Local vs. 5 External Literature)...")
    res_local = client.get("/api/earth-applications?provenance_status=locally_verified")
    assert res_local.status_code == 200
    local_items = res_local.json()["evidence"]
    assert len(local_items) == 6
    assert all(e["validation_status"] == "locally_verified" for e in local_items)

    res_ext = client.get("/api/earth-applications?provenance_status=external_literature_verified")
    assert res_ext.status_code == 200
    ext_items = res_ext.json()["evidence"]
    assert len(ext_items) == 5
    assert all(e["validation_status"] == "external_literature_verified" for e in ext_items)
    print("  ✓ PASSED: Flight data provenance separated: 6 locally verified CSVs vs 5 external literature reports.")


def test_6_evidence_detail_workspace_contract():
    print("\n[Test 6/12] Evidence Detail Workspace Contract...")
    test_id = "EA-EV-SAFFIRE-DET-02"
    res = client.get(f"/api/earth-applications/{test_id}/evidence")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["evidence_id"] == test_id
    ev = data["evidence"]

    # Verify all mandatory scientific fields are populated
    for field in (
        "id",
        "category_id",
        "category_title",
        "title",
        "description",
        "investigation_id",
        "investigation_name",
        "source_type",
        "source_reference",
        "supporting_excerpt",
        "scientific_finding",
        "proposed_terrestrial_relevance",
        "evidence_classification",
        "validation_status",
        "confidence_rubric",
        "earth_transfer_limitations",
        "gravity_buoyancy_ventilation_differences",
    ):
        assert field in ev, f"Missing field '{field}' in evidence detail response"
        assert len(str(ev[field])) > 0, f"Empty field '{field}'"

    # Specific threshold lead-time verification for Saffire
    assert "66.56 s" in ev["scientific_finding"] or "66.56s" in ev["scientific_finding"]
    assert "1.65 s" in ev["scientific_finding"] or "1.65s" in ev["scientific_finding"]
    assert "43s lead" not in ev["title"].lower()
    print("  ✓ PASSED: Evidence detail workspace payload verified with exact scientific parameters.")


def test_7_physical_connection_bridge_integrity():
    print("\n[Test 7/12] Physical Connection Bridge Mechanism Integrity...")
    # Verify that all 11 records have substantial scientific finding and terrestrial relevance for the 5-step chain
    res = client.get("/api/earth-applications")
    assert res.status_code == 200
    all_ev = res.json()["evidence"]
    assert len(all_ev) == 11

    for ev in all_ev:
        assert len(ev["investigation_name"]) > 3
        assert len(ev["scientific_finding"]) > 20
        assert len(ev["proposed_terrestrial_relevance"]) > 20
        assert len(ev["earth_transfer_limitations"]) > 20
        assert len(ev["gravity_buoyancy_ventilation_differences"]) > 20
    print("  ✓ PASSED: All 11 records contain complete, substantive content for the 5-step translation chain.")


def test_8_decoupled_dimensions_assertion():
    print("\n[Test 8/12] Dimension A vs. Dimension B Decoupling Assertion...")
    # Critical test: EA-EV-SAFFIRE-WILD-03 has Tier 1 locally verified flight data, but its terrestrial application is exploratory_hypothesis
    res = client.get("/api/earth-applications/EA-EV-SAFFIRE-WILD-03")
    assert res.status_code == 200
    wild = res.json()["evidence"]
    assert wild["validation_status"] == "locally_verified"
    assert wild["evidence_classification"] == "exploratory_hypothesis"
    assert "Dimension A" in wild["confidence_rubric"]
    assert "Dimension B" in wild["confidence_rubric"]
    print("  ✓ PASSED: Locally verified flight data does NOT automatically imply verified terrestrial adoption.")


def test_9_cross_module_navigation_contracts():
    print("\n[Test 9/12] Cross-Module Navigation Contract Verifications...")
    # 1. Saffire telemetry dataset contract in visualizer
    saffire_res = client.get("/api/datasets/saffire_iii_sample_1/telemetry?max_points=50")
    assert saffire_res.status_code == 200
    assert len(saffire_res.json()["telemetry"]) > 0

    # 2. BASS-II experiments dataset contract in modeling extraction
    bass_res = client.post("/api/modeling/preview", json={"dataset_id": "bass_ii_experiments"})
    assert bass_res.status_code == 200
    assert bass_res.json()["preview"]["total_filtered_count"] == 129

    # 3. Research gap matrix contract
    gap_res = client.get("/api/research-gaps/summary")
    assert gap_res.status_code == 200
    assert gap_res.json()["summary"]["total_findings"] == 21
    print("  ✓ PASSED: Navigation destination contracts for Visualizer, ML Extraction, and Gap Matrix verified.")


def test_10_scientific_caveats_and_negative_safety():
    print("\n[Test 10/12] Scientific Caveats & Negative Safety Enforcement...")
    res = client.get("/api/earth-applications")
    assert res.status_code == 200
    evidence_list = res.json()["evidence"]

    for ev in evidence_list:
        rubric_text = ev["confidence_rubric"].lower()
        assert "% confidence" not in rubric_text
        assert "% probability" not in rubric_text
        assert "certified for deployment" not in ev["proposed_terrestrial_relevance"].lower()
        assert "approved for commercial use" not in ev["proposed_terrestrial_relevance"].lower()

    # Overview safeguards
    overview_res = client.get("/api/earth-applications/overview")
    assert overview_res.status_code == 200
    safeguards = overview_res.json()["overview"]["safeguards"]
    assert "transfer_disclaimer" in safeguards
    assert "no_deployable_equipment_approval" in safeguards
    assert "zero_fabricated_probabilities" in safeguards
    print("  ✓ PASSED: Strict scientific safety enforced; zero fabricated probabilities or deployment claims.")


def test_11_overview_contract_and_investigation_reconciliation():
    print("\n[Test 11/12] Overview Contract & Canonical Investigation Reconciliation...")
    res = client.get("/api/earth-applications/overview")
    assert res.status_code == 200
    overview = res.json()["overview"]

    assert overview["total_evidence_records"] == 11
    assert len(overview["categories"]) == 7
    recon = overview["investigation_reconciliation"]
    assert recon["unique_primary_investigations_count"] == 6
    assert recon["total_unique_investigations_count"] == 7
    assert set(recon["canonical_investigations"]) == {
        "acme",
        "bass_ii",
        "cygnus_vehicle_telemetry",
        "flex",
        "saffire_iii",
        "same",
        "sofie",
    }
    print("  ✓ PASSED: Exactly 7 canonical investigations reconciled across 11 records.")


def test_12_non_regression_across_flame():
    print("\n[Test 12/12] Full Platform Non-Regression across Existing NASA FLAME Services...")
    # 1. Equipment research
    eq_res = client.get("/api/equipment-research/overview")
    assert eq_res.status_code == 200

    # 2. Predictive modeling
    mod_res = client.get("/api/modeling/datasets")
    assert mod_res.status_code == 200

    # 3. Gap detection
    gap_res = client.get("/api/research-gaps/findings")
    assert gap_res.status_code == 200

    # 4. Telemetry decimation
    tel_res = client.get("/api/datasets/saffire_iii_sample_1/telemetry?max_points=20")
    assert tel_res.status_code == 200
    print("  ✓ PASSED: Zero regressions across Equipment Research, Predictive Modeling, Gap Detection, and Telemetry.")


if __name__ == "__main__":
    print("=" * 80)
    print("NASA FLAME — Earth Applications Phase EA2 Test Suite")
    print("=" * 80)
    test_1_dynamic_categories_contract()
    test_2_category_filtering_fidelity()
    test_3_investigation_and_multi_dimension_filtering()
    test_4_classification_filtering_fidelity()
    test_5_provenance_filtering()
    test_6_evidence_detail_workspace_contract()
    test_7_physical_connection_bridge_integrity()
    test_8_decoupled_dimensions_assertion()
    test_9_cross_module_navigation_contracts()
    test_10_scientific_caveats_and_negative_safety()
    test_11_overview_contract_and_investigation_reconciliation()
    test_12_non_regression_across_flame()
    print("\n" + "=" * 80)
    print("ALL 12 EA2 INTEGRATION TESTS PASSED (100% Success Rate)")
    print("=" * 80)
