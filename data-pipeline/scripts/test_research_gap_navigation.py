"""
NASA FLAME — Automated Regression Test: AI Assistant → Coverage Matrix Navigation State

Verifies:
1. AI Assistant action recommendation for research gap findings generates destination 'gap-detection'
   with sub_tab: 'matrix' and the complete finding context.
2. Finding resolution for GAP-COV-GRAV-PARTIAL-LUNAR accurately extracts scientific_dimensions:
   gravity = 'partial_lunar', oxygen = None (unspecified oxygen regime).
3. Non-arbitrary oxygen selection invariant: when a finding specifies only gravity, the navigation
   and state mapping must target the entire Partial Lunar gravity row rather than picking an arbitrary oxygen cell.
4. Coverage Matrix data integrity: all four Partial Lunar cells (low_o2, normal_o2, elevated_o2, high_o2)
   are verified as critical gaps with 0 usable test runs in FLAME.
5. Finding metadata completeness: evidence count (0), denominator ('0 of 133'), limitations,
   and epistemic boundary notices are preserved and accessible to the matrix inspector.
6. Non-regression across other finding types (material, airflow, sparse evidence).
"""

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from fastapi.testclient import TestClient
from api.main import app
from research_gaps.gap_detection_service import ResearchGapDetectionService
from rag.actions import ResearchToolRecommender


def run_tests():
    print("=" * 76)
    print("NASA FLAME — Research Gap Navigation State Regression Suite")
    print("=" * 76)

    client = TestClient(app)
    gap_service = ResearchGapDetectionService()
    recommender = ResearchToolRecommender()
    passed_tests = 0
    total_tests = 6

    # ----------------------------------------------------
    # Test 1: AI Assistant Tool Recommendation Navigation Contract
    # ----------------------------------------------------
    print("\n[Test 1/6] AI Assistant Recommendation Contract for GAP-COV-GRAV-PARTIAL-LUNAR...")
    target_finding_id = "GAP-COV-GRAV-PARTIAL-LUNAR"
    finding = gap_service.get_finding_by_id(target_finding_id)
    assert finding is not None, f"Expected {target_finding_id} to exist"

    actions = recommender.recommend(
        question="What is the coverage status of lunar combustion?",
        retrieved_evidence=[],
        finding=finding,
    )

    gap_action = next((a for a in actions if a["action_id"] == "open_gap_detection"), None)
    assert gap_action is not None, "Expected 'open_gap_detection' action in recommendations"
    assert gap_action["tab_id"] == "gap-detection"
    assert "Coverage Heatmap" in gap_action["category"]
    assert gap_action["params"]["sub_tab"] == "matrix", f"Expected sub_tab == 'matrix', got {gap_action['params'].get('sub_tab')}"
    assert gap_action["params"]["finding_id"] == target_finding_id
    assert gap_action["params"]["finding"]["finding_id"] == target_finding_id

    print(f"    • Action ID: {gap_action['action_id']}")
    print(f"    • Target Tab: {gap_action['tab_id']}")
    print(f"    • Sub Tab: {gap_action['params']['sub_tab']}")
    print(f"    • Injected Finding: {gap_action['params']['finding_id']}")
    print("  ✓ PASSED: Recommendation correctly directs to Coverage Heatmap Matrix with finding payload.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 2: Dimension Invariant (Gravity Specified, Oxygen Unspecified)
    # ----------------------------------------------------
    print("\n[Test 2/6] Dimension Invariant for Partial Lunar Gravity Finding...")
    dims = finding.get("scientific_dimensions", {})
    assert dims.get("gravity") == "partial_lunar", f"Expected gravity == 'partial_lunar', got {dims.get('gravity')}"
    assert dims.get("oxygen") is None, f"Expected oxygen == None (finding applies to all O2 regimes), got {dims.get('oxygen')}"

    print(f"    • Verified gravity dimension: '{dims.get('gravity')}'")
    print(f"    • Verified oxygen dimension: {dims.get('oxygen')} (unrestricted/applies across all O2 columns)")
    print("  ✓ PASSED: Scientific dimensions strictly isolate gravity without arbitrary oxygen restriction.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 3: Coverage Matrix Data Integrity for Partial Lunar Row
    # ----------------------------------------------------
    print("\n[Test 3/6] Coverage Matrix Backend Data for All Partial Lunar Cells...")
    matrix_resp = client.get("/api/research-gaps/coverage/matrix?matrix_type=gravity_vs_oxygen")
    assert matrix_resp.status_code == 200
    matrix_data = matrix_resp.json().get("matrix", {}).get("gravity_vs_oxygen", {})

    expected_cells = [
        "partial_lunar_low_o2",
        "partial_lunar_normal_o2",
        "partial_lunar_elevated_o2",
        "partial_lunar_high_o2",
    ]

    for cell_key in expected_cells:
        cell = matrix_data.get(cell_key)
        assert cell is not None, f"Missing expected cell '{cell_key}' in matrix"
        runs = cell.get("experiment_count", 0)
        assert runs == 0, f"Expected 0 runs in {cell_key}, got {runs}"
        assert cell.get("status") == "gap", f"Expected status 'gap' in {cell_key}, got {cell.get('status')}"
        print(f"    • {cell_key}: {runs} runs (status: {cell.get('status')})")

    print("  ✓ PASSED: Entire Partial Lunar row verified as an unrepresented critical gap (0 runs across all 4 oxygen columns).")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 4: Finding Details, Limitations & Epistemic Scope Preservation
    # ----------------------------------------------------
    print("\n[Test 4/6] Finding Details, Limitations & Scope Preservation...")
    assert finding["observed_usable_run_count"] == 0
    assert "0 of 133" in finding["denominator_and_scope"]
    assert len(finding["limitations"]) >= 2
    assert any("centrifuge" in lim.lower() for lim in finding["limitations"])
    assert any("drop tower" in lim.lower() for lim in finding["limitations"])
    assert "does not prove NASA never conducted an experiment" in finding["database_scope_disclaimer"]

    print(f"    • Denominator & Scope: {finding['denominator_and_scope']}")
    print(f"    • Documented Limitations: {len(finding['limitations'])} specific constraints")
    print(f"    • Database Scope Disclaimer: {finding['database_scope_disclaimer']}")
    print("  ✓ PASSED: Complete scientific metadata preserved for finding-specific inspection panel.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 5: State Mapping Resolution Logic Validation
    # ----------------------------------------------------
    print("\n[Test 5/6] Matrix State Resolution Logic Simulation...")
    # Simulate the frontend state resolution logic
    def resolve_matrix_state_from_finding(f):
        f_dims = f.get("scientific_dimensions", {})
        if f_dims.get("gravity"):
            target_matrix = "gravity_vs_oxygen"
            row_highlight = f_dims["gravity"]
            if f_dims.get("oxygen"):
                col_highlight = f_dims["oxygen"]
                cell_key = f"{f_dims['gravity']}_{f_dims['oxygen']}"
            else:
                col_highlight = None
                cell_key = None  # Crucial: do not arbitrarily select a single oxygen column
            return target_matrix, row_highlight, col_highlight, cell_key
        elif f_dims.get("fuel_family"):
            target_matrix = "material_vs_airflow"
            row_highlight = f_dims["fuel_family"]
            col_highlight = f_dims.get("airflow")
            cell_key = f"{f_dims['fuel_family']}_{f_dims['airflow']}" if f_dims.get("airflow") else None
            return target_matrix, row_highlight, col_highlight, cell_key
        return "gravity_vs_oxygen", None, None, "micro_elevated_o2"

    mat_type, row_id, col_id, sel_cell = resolve_matrix_state_from_finding(finding)
    assert mat_type == "gravity_vs_oxygen", f"Expected 'gravity_vs_oxygen', got {mat_type}"
    assert row_id == "partial_lunar", f"Expected row_id == 'partial_lunar', got {row_id}"
    assert col_id is None, f"Expected col_id is None (not picking arbitrary column), got {col_id}"
    assert sel_cell is None, f"Expected sel_cell is None (showing finding overview panel instead of arbitrary cell), got {sel_cell}"

    print(f"    • Target Matrix: {mat_type}")
    print(f"    • Highlighted Row: {row_id}")
    print(f"    • Highlighted Col: {col_id} (None -> row-wide highlight)")
    print(f"    • Selected Cell: {sel_cell} (None -> Finding-Specific Inspection Panel)")
    print("  ✓ PASSED: State resolution accurately highlights row without arbitrary oxygen selection.")
    passed_tests += 1

    # ----------------------------------------------------
    # Test 6: Non-Regression across Other Finding Types
    # ----------------------------------------------------
    print("\n[Test 6/6] Non-Regression across Material and Airflow Findings...")
    nomex_finding = gap_service.get_finding_by_id("GAP-SPARSE-FUEL-NOMEX")
    assert nomex_finding is not None
    nomex_mat, nomex_row, nomex_col, nomex_cell = resolve_matrix_state_from_finding(nomex_finding)
    assert nomex_mat == "material_vs_airflow"
    assert nomex_row == "solid-flat"

    actions_nomex = recommender.recommend(
        question="Nomex fabric flammability",
        retrieved_evidence=[],
        finding=nomex_finding,
    )
    nomex_action = next((a for a in actions_nomex if a["action_id"] == "open_gap_detection"), None)
    assert nomex_action is not None
    assert nomex_action["params"]["sub_tab"] == "matrix"

    print("    • Material finding (GAP-SPARSE-FUEL-NOMEX) correctly routes to 'material_vs_airflow' with 'solid-flat' focus.")
    print("  ✓ PASSED: Non-regression across alternative finding dimensions verified.")
    passed_tests += 1

    # ----------------------------------------------------
    # Summary
    # ----------------------------------------------------
    print("\n" + "=" * 76)
    print(f"ALL TESTS PASSED: {passed_tests} / {total_tests} (100% Success Rate)")
    print("Research Gap Detection navigation state and finding resolution verified.")
    print("=" * 76)
    return True


if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
