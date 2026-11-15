"""
NASA FLAME — Earth Applications Test Suite (Phase EA1.1 Audited)
Comprehensive validation of all 20 core and audit requirements:
1. Catalog loading and Pydantic schema validation
2. Categories endpoint contract and dynamic counts
3. List endpoint contract, query filters, and pagination
4. Category filtering fidelity
5. Classification filtering fidelity (audited: documented=0, supported=10, exploratory=1)
6. Investigation filtering fidelity (primary and co-investigations)
7. Investigation endpoint and missing evidence handling (404)
8. Single evidence detail endpoints and 404 error boundaries
9. Negative safety tests preventing unsupported claims & fabricated probabilities
10. Citation provenance and local vs. external separation
11. Overview endpoint contract and safeguards
12. Full non-regression across all existing NASA FLAME services
13. Dimension A vs. Dimension B separation (flight data vs. terrestrial validation)
14. Documented application adoption evidence (ACME & FLEX downgrade verification)
15. Saffire radiative detection lead time accuracy (threshold lead vs. peak delay)
16. BASS-II convective velocity extinction boundaries accuracy (no unmeasured Damköhler limits)
17. FLEX unsupported claims removal (no 15-20% efficiency, no halon replacement)
18. Saffire industrial ventilation safety refocus (no speculative silane scrubber claims)
19. SAME aerosol agglomeration citation verification (NASA/TM-2009-215801)
20. Canonical investigation counts and multi-investigation reconciliation
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.main import app
from earth_applications.service import EarthApplicationsService
from earth_applications.models import EarthApplicationEvidence
from earth_applications.taxonomy import EARTH_APPLICATION_CATEGORIES
from earth_applications.catalog import INITIAL_EARTH_APPLICATION_CATALOG

client = TestClient(app)
service = EarthApplicationsService()


def test_1_catalog_loading_and_schema():
    print("\n[Test 1/20] Catalog Loading & Schema Integrity...")
    assert len(INITIAL_EARTH_APPLICATION_CATALOG) == 11, f"Expected 11 records, got {len(INITIAL_EARTH_APPLICATION_CATALOG)}"

    # Validate each record adheres to the EarthApplicationEvidence schema
    cat_ids = set()
    inv_ids = set()
    for ev in INITIAL_EARTH_APPLICATION_CATALOG:
        assert isinstance(ev, EarthApplicationEvidence)
        assert ev.id.startswith("EA-EV-")
        assert len(ev.title) > 5
        assert len(ev.description) > 10
        assert len(ev.scientific_finding) > 10
        assert len(ev.proposed_terrestrial_relevance) > 10
        assert len(ev.earth_transfer_limitations) > 10
        assert len(ev.gravity_buoyancy_ventilation_differences) > 10
        assert isinstance(ev.related_investigation_ids, list)
        cat_ids.add(ev.category_id)
        inv_ids.add(ev.investigation_id)

    # Verify all 7 categories are represented
    taxonomy_ids = {c["id"] for c in EARTH_APPLICATION_CATEGORIES}
    assert cat_ids == taxonomy_ids, f"Mismatch in category representation: {taxonomy_ids - cat_ids}"

    # Verify priority primary investigations are present
    priority_invs = {"bass_ii", "saffire_iii", "same", "acme", "sofie", "flex"}
    assert priority_invs == inv_ids, f"Mismatch in primary investigations: {inv_ids}"
    print(f"  ✓ PASSED: All 11 evidence records loaded covering all 7 categories and 6 primary investigations.")


def test_2_categories_endpoint_contract():
    print("\n[Test 2/20] Categories Endpoint Contract & Dynamic Evidence Counts...")
    res = client.get("/api/earth-applications/categories")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "ok"
    assert data["total_categories"] == 7
    categories = data["categories"]
    assert len(categories) == 7

    for cat in categories:
        assert "id" in cat
        assert "title" in cat
        assert "scientific_scope" in cat
        assert "transfer_considerations" in cat
        assert "evidence_count" in cat
        assert cat["evidence_count"] > 0, f"Category {cat['id']} has 0 evidence records"
    print("  ✓ PASSED: All 7 categories returned with non-zero dynamic evidence counts.")


def test_3_list_endpoint_and_pagination():
    print("\n[Test 3/20] List Endpoint & Pagination...")
    res_full = client.get("/api/earth-applications")
    assert res_full.status_code == 200, res_full.text
    data_full = res_full.json()
    total = data_full["total_count"]
    assert total == 11

    # Test limit and offset pagination
    res_page1 = client.get("/api/earth-applications?limit=3&offset=0")
    assert res_page1.status_code == 200
    d1 = res_page1.json()
    assert len(d1["evidence"]) == 3
    assert d1["limit"] == 3
    assert d1["offset"] == 0

    res_page2 = client.get("/api/earth-applications?limit=3&offset=3")
    assert res_page2.status_code == 200
    d2 = res_page2.json()
    assert len(d2["evidence"]) == 3
    assert d2["offset"] == 3

    # Ensure pages are distinct
    ids_p1 = {e["id"] for e in d1["evidence"]}
    ids_p2 = {e["id"] for e in d2["evidence"]}
    assert len(ids_p1.intersection(ids_p2)) == 0, "Pages should not overlap"
    print("  ✓ PASSED: List endpoint pagination behaves deterministically.")


def test_4_category_filtering():
    print("\n[Test 4/20] Category Filtering Fidelity...")
    # Test building fire safety
    res_bldg = client.get("/api/earth-applications?category=building_fire_safety")
    assert res_bldg.status_code == 200
    items = res_bldg.json()["evidence"]
    assert len(items) >= 1
    assert all(e["category_id"] == "building_fire_safety" for e in items)

    # Test wildfire
    res_wild = client.get("/api/earth-applications?category=wildfire_combustion")
    assert res_wild.status_code == 200
    wild_items = res_wild.json()["evidence"]
    assert len(wild_items) >= 1
    assert all(e["category_id"] == "wildfire_combustion" for e in wild_items)

    # Test combustion emissions
    res_emiss = client.get("/api/earth-applications?category=combustion_efficiency_emissions")
    assert res_emiss.status_code == 200
    emiss_items = res_emiss.json()["evidence"]
    assert len(emiss_items) == 2
    assert all(e["category_id"] == "combustion_efficiency_emissions" for e in emiss_items)
    print("  ✓ PASSED: Category filtering accurately isolates corresponding records.")


def test_5_classification_filtering():
    print("\n[Test 5/20] Evidence Classification Filtering Fidelity (Audited)...")
    # supported_research_implication: 10 records
    res_supp = client.get("/api/earth-applications?classification=supported_research_implication")
    assert res_supp.status_code == 200, res_supp.text
    d_supp = res_supp.json()
    assert d_supp["filtered_count"] == 10
    assert all(e["evidence_classification"] == "supported_research_implication" for e in d_supp["evidence"])

    # exploratory_hypothesis: 1 record (EA-EV-SAFFIRE-WILD-03)
    res_hyp = client.get("/api/earth-applications?classification=exploratory_hypothesis")
    assert res_hyp.status_code == 200, res_hyp.text
    d_hyp = res_hyp.json()
    assert d_hyp["filtered_count"] == 1
    assert d_hyp["evidence"][0]["id"] == "EA-EV-SAFFIRE-WILD-03"

    # documented_application: currently 0 records because no flight investigation has verified adoption in commercial production standards
    res_doc = client.get("/api/earth-applications?classification=documented_application")
    assert res_doc.status_code == 200, res_doc.text
    d_doc = res_doc.json()
    assert d_doc["filtered_count"] == 0, "No records should claim documented_application without published proof of terrestrial adoption"
    print("  ✓ PASSED: Classification filtering validates supported (10), exploratory (1), and empty documented tier (0).")


def test_6_investigation_filtering():
    print("\n[Test 6/20] Investigation Filtering Fidelity (Primary & Co-Investigations)...")
    for inv in ("bass_ii", "saffire_iii", "acme", "same", "flex", "sofie"):
        res = client.get(f"/api/earth-applications?investigation_id={inv}")
        assert res.status_code == 200, res.text
        items = res.json()["evidence"]
        assert len(items) >= 1, f"Expected items for investigation {inv}"
        assert all(
            e["investigation_id"] == inv or inv in e.get("related_investigation_ids", [])
            for e in items
        )

    # Test co-investigation retrieval for cygnus_vehicle_telemetry
    res_cyg = client.get("/api/earth-applications?investigation_id=cygnus_vehicle_telemetry")
    assert res_cyg.status_code == 200
    cyg_items = res_cyg.json()["evidence"]
    assert len(cyg_items) == 1
    assert cyg_items[0]["id"] == "EA-EV-SAFFIRE-IND-04"
    assert "cygnus_vehicle_telemetry" in cyg_items[0]["related_investigation_ids"]
    print("  ✓ PASSED: Investigation filtering isolates records across all priority investigations and co-investigations.")


def test_7_investigation_endpoint_and_missing_evidence():
    print("\n[Test 7/20] Investigation Endpoint & Missing Evidence Handling...")
    # Known investigation with evidence
    res_saffire = client.get("/api/earth-applications/investigations/saffire_iii")
    assert res_saffire.status_code == 200, res_saffire.text
    assert res_saffire.json()["investigation_id"] == "saffire_iii"
    assert res_saffire.json()["evidence_count"] == 4

    # Co-investigation lookup via endpoint
    res_cyg = client.get("/api/earth-applications/investigations/cygnus_vehicle_telemetry")
    assert res_cyg.status_code == 200
    assert res_cyg.json()["evidence_count"] == 1

    # Unknown investigation -> 404 with meaningful error
    res_unknown = client.get("/api/earth-applications/investigations/non_existent_mission_xyz")
    assert res_unknown.status_code == 404
    assert "No verified Earth application evidence found" in res_unknown.json()["detail"]
    print("  ✓ PASSED: Investigation endpoint returns evidence or structured 404 for missing evidence.")


def test_8_single_evidence_detail_endpoints():
    print("\n[Test 8/20] Single Evidence Detail Endpoints & Error Boundaries...")
    target_id = "EA-EV-BASS-PYRO-01"

    # GET /api/earth-applications/{id}
    res1 = client.get(f"/api/earth-applications/{target_id}")
    assert res1.status_code == 200, res1.text
    ev = res1.json()["evidence"]
    assert ev["id"] == target_id
    assert ev["investigation_id"] == "bass_ii"

    # GET /api/earth-applications/{id}/evidence
    res2 = client.get(f"/api/earth-applications/{target_id}/evidence")
    assert res2.status_code == 200, res2.text
    assert res2.json()["evidence_id"] == target_id
    assert res2.json()["evidence"]["category_id"] == "material_flammability_fire_resistance"

    # 404 for non-existent evidence ID
    res_404 = client.get("/api/earth-applications/EA-EV-NON-EXISTENT-99")
    assert res_404.status_code == 404
    assert "not found" in res_404.json()["detail"].lower()
    print("  ✓ PASSED: Single evidence and detail endpoints contract and error boundaries verified.")


def test_9_negative_safety_tests():
    print("\n[Test 9/20] Negative Safety Tests (No Fabricated Probabilities, Transfer Disclaimers)...")
    res = client.get("/api/earth-applications")
    assert res.status_code == 200
    all_evidence = res.json()["evidence"]

    for ev in all_evidence:
        # Check that no probability percentages are presented as confidence
        rubric_text = ev["confidence_rubric"].lower()
        assert "% confidence" not in rubric_text
        assert "% probability" not in rubric_text

        # Every record MUST contain explicit Earth transfer limitations
        assert len(ev["earth_transfer_limitations"]) >= 25, f"Record {ev['id']} lacks substantive transfer limitations"

        # Every record MUST contain gravity/buoyancy differences
        assert len(ev["gravity_buoyancy_ventilation_differences"]) >= 25, f"Record {ev['id']} lacks buoyancy physics differences"

        # Check that no deployable equipment approval is claimed
        full_text = f"{ev['title']} {ev['description']} {ev['proposed_terrestrial_relevance']}".lower()
        assert "certified for deployment" not in full_text
        assert "approved for commercial use" not in full_text

    print("  ✓ PASSED: Strict scientific safety enforced; zero fabricated probabilities or deployment claims.")


def test_10_citation_provenance_and_local_vs_external():
    print("\n[Test 10/20] Citation Provenance & Local vs. External Separation...")
    # Locally verified records must cite local dataset files
    res_local = client.get("/api/earth-applications?provenance_status=locally_verified")
    assert res_local.status_code == 200
    local_items = res_local.json()["evidence"]
    assert len(local_items) == 6

    for item in local_items:
        assert item["dataset_or_measurement_reference"] is not None
        ref = item["dataset_or_measurement_reference"].lower()
        assert any(ds in ref for ds in ("saffire_iii_sample_1.csv", "bass_ii_experiments.csv", "cygnus_data.csv"))

    # External literature records must cite verifiable external URLs/reports
    res_ext = client.get("/api/earth-applications?provenance_status=external_literature_verified")
    assert res_ext.status_code == 200
    ext_items = res_ext.json()["evidence"]
    assert len(ext_items) == 5

    for item in ext_items:
        src = item["source_reference"]
        assert src.startswith("http") or src.startswith("NASA/TM") or src.startswith("NASA TM")
    print("  ✓ PASSED: Local telemetry citations strictly decoupled from external literature citations.")


def test_11_overview_endpoint_contract():
    print("\n[Test 11/20] Overview Endpoint Contract & Safeguards...")
    res = client.get("/api/earth-applications/overview")
    assert res.status_code == 200, res.text
    overview = res.json()["overview"]

    assert overview["total_evidence_records"] == 11
    assert len(overview["categories"]) == 7
    assert "classification_breakdown" in overview
    assert "provenance_breakdown" in overview
    assert "investigation_reconciliation" in overview
    assert "safeguards" in overview
    assert "transfer_disclaimer" in overview["safeguards"]
    assert "no_deployable_equipment_approval" in overview["safeguards"]
    assert "zero_fabricated_probabilities" in overview["safeguards"]
    print("  ✓ PASSED: Overview endpoint presents complete breakdown and required scientific safeguards.")


def test_12_non_regression_existing_tools():
    print("\n[Test 12/20] Non-Regression across Existing NASA FLAME Services...")
    # 1. Equipment research overview
    eq_res = client.get("/api/equipment-research/overview")
    assert eq_res.status_code == 200
    assert len(eq_res.json()["overview"]["categories"]) == 3

    # 2. Predictive modeling preview
    mod_res = client.post("/api/modeling/preview", json={"dataset_id": "bass_ii_experiments"})
    assert mod_res.status_code == 200
    assert mod_res.json()["preview"]["total_filtered_count"] == 129

    # 3. Gap detection summary
    gap_res = client.get("/api/research-gaps/summary")
    assert gap_res.status_code == 200
    assert gap_res.json()["summary"]["total_findings"] == 21

    # 4. Telemetry decimation
    tel_res = client.get("/api/datasets/saffire_iii_sample_1/telemetry?max_points=50")
    assert tel_res.status_code == 200
    assert len(tel_res.json()["telemetry"]) > 0
    print("  ✓ PASSED: Zero regressions across Equipment Research, Predictive Modeling, Gap Detection, and Telemetry.")


def test_13_dimension_a_vs_dimension_b_separation():
    print("\n[Test 13/20] EA1.1 Audit: Dimension A vs. Dimension B Separation...")
    # Dimension A: Experimental measurement verification (flight data or external literature)
    # Dimension B: Terrestrial application validation (documented use, supported implication, exploratory hypothesis)
    # Critical rule: Locally verified flight data must NEVER automatically imply a verified terrestrial use!
    res = client.get("/api/earth-applications/EA-EV-SAFFIRE-WILD-03")
    assert res.status_code == 200
    wild = res.json()["evidence"]
    assert wild["validation_status"] == "locally_verified"
    assert wild["evidence_classification"] == "exploratory_hypothesis"
    assert "Dimension A (Experimental Grounding): Locally verified" in wild["confidence_rubric"]
    assert "Dimension B (Terrestrial Validation): Strictly an exploratory hypothesis" in wild["confidence_rubric"]
    print("  ✓ PASSED: Dimension A and Dimension B are strictly separated (locally verified flight data does not imply verified terrestrial use).")


def test_14_documented_application_adoption_evidence():
    print("\n[Test 14/20] EA1.1 Audit: Documented Application Adoption Standards (ACME & FLEX Downgrades)...")
    # ACME soot reduction must NOT be documented_application (downgraded to supported_research_implication)
    res_acme = client.get("/api/earth-applications/EA-EV-ACME-SOOT-01")
    assert res_acme.status_code == 200
    acme = res_acme.json()["evidence"]
    assert acme["evidence_classification"] == "supported_research_implication"
    assert "commercial turbine adoption" not in acme["proposed_terrestrial_relevance"].lower()

    # FLEX cool flame must NOT be documented_application (downgraded to supported_research_implication)
    res_flex = client.get("/api/earth-applications/EA-EV-FLEX-COOL-01")
    assert res_flex.status_code == 200
    flex = res_flex.json()["evidence"]
    assert flex["evidence_classification"] == "supported_research_implication"

    # Global check: no record claims documented_application without published adoption proof
    res_all = client.get("/api/earth-applications")
    doc_apps = [e for e in res_all.json()["evidence"] if e["evidence_classification"] == "documented_application"]
    assert len(doc_apps) == 0, f"Expected 0 documented_application records pending explicit commercial adoption evidence, found {len(doc_apps)}"
    print("  ✓ PASSED: Documented application tier strictly guarded; ACME and FLEX appropriately downgraded to supported implications.")


def test_15_saffire_detection_lead_time_accuracy():
    print("\n[Test 15/20] EA1.1 Audit: Saffire Radiative Detection Lead Time Correction...")
    res = client.get("/api/earth-applications/EA-EV-SAFFIRE-DET-02")
    assert res.status_code == 200
    det = res.json()["evidence"]

    # Must NOT claim misleading 43s lead time
    assert "43s lead" not in det["title"].lower()
    assert "43 seconds earlier" not in det["scientific_finding"].lower()
    assert "43s lead time" not in det["proposed_terrestrial_relevance"].lower()

    # Must accurately state onset threshold lead (1.65s to 6.60s) and downstream peak delay (t=109.79s)
    finding = det["scientific_finding"]
    assert "66.56 s" in finding or "66.56s" in finding
    assert "1.65 s" in finding or "1.65s" in finding
    assert "6.60 s" in finding or "6.60s" in finding
    assert "109.79 s" in finding or "109.79s" in finding
    print("  ✓ PASSED: Saffire detection lead time accurately distinguishes genuine onset lead (1.65s - 6.60s) from downstream peak delay (109.79s).")


def test_16_bass_extinction_boundaries_accuracy():
    print("\n[Test 16/20] EA1.1 Audit: BASS-II Convective Extinction Boundaries Accuracy...")
    res = client.get("/api/earth-applications/EA-EV-BASS-EXT-02")
    assert res.status_code == 200
    ext = res.json()["evidence"]

    # Title must not use unmeasured theoretical construct "Damköhler limits"
    assert "Damköhler limits" not in ext["title"]
    assert "Convective Velocity Extinction Boundaries" in ext["title"]

    # Finding must describe the empirical velocity bounds (<1.5 cm/s and >28-38 cm/s)
    finding = ext["scientific_finding"]
    assert "1.5 cm/s" in finding
    assert "28-38 cm/s" in finding
    assert "oxygen transport" in finding.lower() or "starvation" in ext["proposed_terrestrial_relevance"].lower()
    assert "blow-off" in finding.lower() or "blowoff" in finding.lower()
    print("  ✓ PASSED: BASS-II extinction boundaries accurately framed as empirical convective boundaries (<1.5 cm/s & >28-38 cm/s).")


def test_17_flex_unsupported_claims_removal():
    print("\n[Test 17/20] EA1.1 Audit: FLEX Unsupported Claims Removal (Efficiency & Halon)...")
    # 1. FLEX cool flame: fabricated "15-20% fuel efficiency" must be completely removed
    res_cool = client.get("/api/earth-applications/EA-EV-FLEX-COOL-01")
    assert res_cool.status_code == 200
    cool = res_cool.json()["evidence"]
    cool_text = f"{cool['title']} {cool['description']} {cool['scientific_finding']} {cool['proposed_terrestrial_relevance']}"
    assert "15-20%" not in cool_text
    assert "15 to 20%" not in cool_text
    assert "15–20%" not in cool_text

    # 2. FLEX suppression: unsupported "halon replacement" must be completely removed
    res_supp = client.get("/api/earth-applications/EA-EV-FLEX-SUPP-02")
    assert res_supp.status_code == 200
    supp = res_supp.json()["evidence"]
    supp_text = f"{supp['title']} {supp['description']} {supp['scientific_finding']} {supp['proposed_terrestrial_relevance']}"
    assert "halon" not in supp_text.lower()
    # Must explicitly state inert diluents (nitrogen, carbon dioxide, helium) tested
    assert "carbon dioxide" in supp["supporting_excerpt"].lower() or "co₂" in supp["scientific_finding"]
    print("  ✓ PASSED: Fabricated 15-20% efficiency and unsupported halon replacement claims removed from FLEX records.")


def test_18_saffire_industrial_scrubber_removal():
    print("\n[Test 18/20] EA1.1 Audit: Saffire Industrial Ventilation Refocus...")
    res = client.get("/api/earth-applications/EA-EV-SAFFIRE-IND-04")
    assert res.status_code == 200
    ind = res.json()["evidence"]
    ind_text = f"{ind['title']} {ind['description']} {ind['scientific_finding']} {ind['proposed_terrestrial_relevance']}".lower()

    # Speculative semiconductor silane scrubbers removed
    assert "silane" not in ind_text
    assert "semiconductor exhaust scrubber" not in ind_text

    # Refocused on forced conduit ventilation fan differential pressure and damper shutdown dynamics
    assert "ventilation" in ind_text
    assert "damper" in ind_text
    assert "differential pressure" in ind_text
    print("  ✓ PASSED: Saffire industrial record refocused on forced conduit ventilation fan/damper shutdown dynamics.")


def test_19_same_citation_verification():
    print("\n[Test 19/20] EA1.1 Audit: SAME Citation Verification (NASA/TM-2009-215801)...")
    res = client.get("/api/earth-applications/EA-EV-SAME-AERO-01")
    assert res.status_code == 200
    same = res.json()["evidence"]

    # Formal report title and number verified
    assert "NASA/TM—2009-215801" in same["source_reference"] or "NASA/TM-2009-215801" in same["source_reference"]
    assert "Urban" in same["source_reference"]

    # Buoyancy differences explicitly qualified
    assert "1g" in same["earth_transfer_limitations"] or "1g" in same["supporting_excerpt"]
    assert "buoyancy" in same["gravity_buoyancy_ventilation_differences"].lower()
    print("  ✓ PASSED: SAME aerosol record verifies NASA/TM-2009-215801 citation and qualifies 1g plume differences.")


def test_20_investigation_reconciliation_details():
    print("\n[Test 20/20] EA1.1 Audit: Canonical Investigation Reconciliation...")
    res = client.get("/api/earth-applications/overview")
    assert res.status_code == 200
    overview = res.json()["overview"]
    recon = overview["investigation_reconciliation"]

    # 6 primary investigations: bass_ii, saffire_iii, same, acme, sofie, flex
    assert recon["unique_primary_investigations_count"] == 6

    # 7 total unique canonical investigations including co-investigation cygnus_vehicle_telemetry
    assert recon["total_unique_investigations_count"] == 7
    expected_canonical = {"acme", "bass_ii", "cygnus_vehicle_telemetry", "flex", "saffire_iii", "same", "sofie"}
    assert set(recon["canonical_investigations"]) == expected_canonical

    # Multi-investigation records correctly documented
    multi_records = recon["multi_investigation_records"]
    assert len(multi_records) == 2
    multi_ids = {m["evidence_id"] for m in multi_records}
    assert multi_ids == {"EA-EV-SAFFIRE-WILD-03", "EA-EV-SAFFIRE-IND-04"}

    # Total involvements: bass_ii=3 (2 primary + 1 related), saffire_iii=4, cygnus_vehicle_telemetry=1
    involvements = recon["total_investigation_involvements"]
    assert involvements["bass_ii"] == 3
    assert involvements["saffire_iii"] == 4
    assert involvements["cygnus_vehicle_telemetry"] == 1
    assert involvements["same"] == 1
    assert involvements["acme"] == 1
    assert involvements["sofie"] == 1
    assert involvements["flex"] == 2
    print("  ✓ PASSED: Exactly 7 canonical investigations reconciled across 11 records with co-investigation traceability.")


if __name__ == "__main__":
    print("=" * 80)
    print("NASA FLAME — Earth Applications Test Suite (Phase EA1.1 Audited)")
    print("=" * 80)
    test_1_catalog_loading_and_schema()
    test_2_categories_endpoint_contract()
    test_3_list_endpoint_and_pagination()
    test_4_category_filtering()
    test_5_classification_filtering()
    test_6_investigation_filtering()
    test_7_investigation_endpoint_and_missing_evidence()
    test_8_single_evidence_detail_endpoints()
    test_9_negative_safety_tests()
    test_10_citation_provenance_and_local_vs_external()
    test_11_overview_endpoint_contract()
    test_12_non_regression_existing_tools()
    test_13_dimension_a_vs_dimension_b_separation()
    test_14_documented_application_adoption_evidence()
    test_15_saffire_detection_lead_time_accuracy()
    test_16_bass_extinction_boundaries_accuracy()
    test_17_flex_unsupported_claims_removal()
    test_18_saffire_industrial_scrubber_removal()
    test_19_same_citation_verification()
    test_20_investigation_reconciliation_details()
    print("\n" + "=" * 80)
    print("ALL 20 EARTH APPLICATIONS AUDIT TESTS PASSED (100% Success Rate)")
    print("=" * 80)
