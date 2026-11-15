"""
NASA FLAME — Predictive-Modeling Data Extraction Test Suite
Comprehensive validation of all 12 core requirements:
1. Dataset discovery
2. Correct feature/target identification
3. Missing-target handling (uninstrumented flame spread rate)
4. Actual CSV export
5. Metadata and units preservation
6. Missing-data detection
7. Time-series and run-level extraction
8. Invalid dataset requests
9. Prevention of incompatible data merging
10. RAG-to-extraction navigation
11. Preview/export consistency
12. Non-regression of existing services
"""

import sys
import io
import csv
import json
from pathlib import Path
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.main import app
from modeling.registry import list_available_datasets, get_modeling_dataset_metadata, MODELING_DATASETS_REGISTRY
from modeling.analyzer import ResearchObjectiveAnalyzer
from modeling.extraction_service import PredictiveDataExtractionService
from rag.actions import ResearchToolRecommender

client = TestClient(app)
analyzer = ResearchObjectiveAnalyzer()
service = PredictiveDataExtractionService(base_dir=BASE_DIR)
recommender = ResearchToolRecommender()


def test_1_dataset_discovery():
    print("\n[Test 1/12] Dataset Discovery & Capabilities...")
    res = client.get("/api/modeling/datasets")
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["status"] == "success"
    assert payload["dataset_count"] >= 5

    ds_ids = [d["dataset_id"] for d in payload["datasets"]]
    assert "bass_ii_experiments" in ds_ids
    assert "saffire_iii_sample_1" in ds_ids
    assert "saffire_iii_sample_2" in ds_ids

    # Verify BASS-II capability
    bass = next(d for d in payload["datasets"] if d["dataset_id"] == "bass_ii_experiments")
    assert bass["paradigm"] == "tabular_run_level"
    assert bass["total_records"] == 129
    assert bass["feature_count"] >= 5
    assert bass["target_count"] >= 3

    # Verify Saffire-III capability
    saf1 = next(d for d in payload["datasets"] if d["dataset_id"] == "saffire_iii_sample_1")
    assert saf1["paradigm"] == "time_series_telemetry"
    assert saf1["total_records"] == 20909

    print("  ✓ PASSED: 5+ modeling datasets registered with verified run-level and time-series capabilities.")


def test_2_correct_feature_target_identification():
    print("\n[Test 2/12] Correct Feature & Target Identification...")
    q = "Predict oxygen consumption delta using airflow velocity and fuel material in microgravity."
    res = client.post("/api/modeling/interpret", json={"query": q})
    assert res.status_code == 200, res.text
    interp = res.json()["interpretation"]

    assert interp["target"]["id"] == "oxygen_consumption_delta_pct"
    assert interp["target"]["status"] == "VALIDATED_DERIVED"
    assert interp["target"]["unit"] == "% vol"
    assert "Airflow Velocity" in interp["detected_features"]
    assert "Fuel Material & Geometry" in interp["detected_features"]

    # Verify BASS-II evaluated as ELIGIBLE_SUPERVISED
    bass_eval = next(e for e in interp["dataset_evaluations"] if e["dataset_id"] == "bass_ii_experiments")
    assert bass_eval["suitability"] == "ELIGIBLE_SUPERVISED"
    print("  ✓ PASSED: Accurately identified target ΔO₂ and features with ELIGIBLE_SUPERVISED suitability.")


def test_3_missing_target_handling():
    print("\n[Test 3/12] Missing & Uninstrumented Target Handling...")
    q = "I want to develop a model to predict flame spread rate using oxygen concentration, airflow velocity, and fuel material."
    res = client.post("/api/modeling/interpret", json={"query": q})
    assert res.status_code == 200, res.text
    interp = res.json()["interpretation"]

    target = interp["target"]
    assert target["id"] == "flame_spread_rate_cm_s"
    assert target["status"] == "UNINSTRUMENTED_UNAVAILABLE"
    assert "photogrammetry" in target["explanation"].lower() or "unrecorded" in target["explanation"].lower()
    assert len(target["suggested_alternatives"]) > 0

    # Ensure all telemetry and matrix datasets mark flame spread rate as TARGET_UNAVAILABLE
    for e in interp["dataset_evaluations"]:
        assert e["suitability"] == "TARGET_UNAVAILABLE", f"{e['dataset_id']} should be TARGET_UNAVAILABLE"
        assert "UNINSTRUMENTED" in e["target_availability"]

    # Also test attempting to force preview with uninstrumented target
    prev_res = client.post("/api/modeling/preview", json={
        "dataset_id": "bass_ii_experiments",
        "target_id": "flame_spread_rate_cm_s"
    })
    assert prev_res.status_code == 400
    assert "uninstrumented" in prev_res.json()["detail"].lower()
    print("  ✓ PASSED: Flame spread rate correctly marked UNINSTRUMENTED with explicit scientific disclosures.")


def test_4_actual_csv_export():
    print("\n[Test 4/12] Actual CSV Export Execution...")
    res = client.post("/api/modeling/export", json={
        "dataset_id": "bass_ii_experiments",
        "format": "csv",
        "selected_features": ["fuel_material", "initial_oxygen_pct", "airflow_velocity_proxy"],
        "target_id": "oxygen_consumption_delta_pct",
        "max_rows": 10
    })
    assert res.status_code == 200, res.text
    assert "text/csv" in res.headers["content-type"]
    assert "bass_ii_experiments_modeling_data.csv" in res.headers["content-disposition"]

    csv_reader = csv.reader(io.StringIO(res.text))
    header = next(csv_reader)
    assert header == ["run_id", "fuel_material", "initial_oxygen_pct", "airflow_velocity_proxy", "oxygen_consumption_delta_pct"]

    rows = list(csv_reader)
    assert len(rows) == 10
    # Verify row 1 has real data (B1, PMMA, 22.2)
    assert rows[0][0] == "B1"
    assert "pmma" in rows[0][1].lower()
    assert float(rows[0][2]) == 22.2
    print("  ✓ PASSED: Valid CSV exported containing exact requested columns and real experimental measurements.")


def test_5_metadata_and_units_preservation():
    print("\n[Test 5/12] Metadata and Units Preservation...")
    res = client.post("/api/modeling/export", json={
        "dataset_id": "bass_ii_experiments",
        "format": "json",
        "selected_features": ["fuel_material", "initial_oxygen_pct"],
        "target_id": "oxygen_consumption_delta_pct",
        "material_filter": "PMMA"
    })
    assert res.status_code == 200, res.text
    assert "application/json" in res.headers["content-type"]
    meta = res.json()

    assert meta["metadata_version"] == "1.0"
    assert meta["dataset_info"]["dataset_id"] == "bass_ii_experiments"
    assert meta["dataset_info"]["facility"] == "ISS Microgravity Science Glovebox (MSG)"
    assert meta["filters_applied"]["material_filter"] == "PMMA"
    assert meta["target_metadata"]["unit"] == "% vol"
    assert meta["target_metadata"]["role"] == "target"
    assert meta["target_metadata"]["category"] == "validated_derived"
    assert "SLPSRAD" in meta["scientific_citation"]
    print("  ✓ PASSED: JSON metadata preserves variable definitions, physical units (% vol), and flight provenance.")


def test_6_missing_data_detection():
    print("\n[Test 6/12] Missing-Data & Quality Detection...")
    res = client.post("/api/modeling/preview", json={
        "dataset_id": "bass_ii_experiments",
        "selected_features": ["fuel_material", "initial_oxygen_pct", "airflow_velocity_proxy", "fan_display"],
        "target_id": "oxygen_consumption_delta_pct",
        "preview_limit": 50
    })
    assert res.status_code == 200, res.text
    q_report = res.json()["preview"]["quality_report"]

    assert "data_completeness_pct" in q_report
    assert 80.0 <= q_report["data_completeness_pct"] <= 100.0
    assert "missing_counts" in q_report
    assert "initial_oxygen_pct" in q_report["missing_counts"]
    assert q_report["group_split_column"] == "run_id"
    print("  ✓ PASSED: Evaluated column completeness, missing counts, and group split column without silent imputation.")


def test_7_timeseries_and_runlevel_extraction():
    print("\n[Test 7/12] Time-Series Bounded Window & Run-Level Extraction...")
    # Bounded Telemetry window (10s to 40s) on Saffire-III Sample 1
    res_saf = client.post("/api/modeling/preview", json={
        "dataset_id": "saffire_iii_sample_1",
        "selected_features": ["flow_velocity_cm_s", "ambient_pressure_psia", "plume_temp_tc1"],
        "target_id": "peak_plume_temperature_c",
        "start_time_s": 10.0,
        "end_time_s": 40.0,
        "preview_limit": 20
    })
    assert res_saf.status_code == 200, res_saf.text
    saf_preview = res_saf.json()["preview"]
    rows = saf_preview["preview_rows"]
    assert len(rows) > 0
    # Verify timestamps fall within [10.0, 40.0]
    for r in rows:
        t = r["elapsed_time_s"]
        assert 10.0 <= t <= 40.0, f"Timestamp {t} outside window [10.0, 40.0]"

    # Verify Leakage risk warning for telemetry
    assert "HIGH_AUTOCORRELATION_RISK" in saf_preview["quality_report"]["leakage_risk"]

    print("  ✓ PASSED: Bounded time-window telemetry correctly filtered with autocorrelation leakage protection.")


def test_8_invalid_dataset_requests():
    print("\n[Test 8/12] Invalid & Path-Traversal Dataset Requests...")
    # Unknown dataset
    res_404 = client.get("/api/modeling/datasets/non_existent_dataset_999")
    assert res_404.status_code == 404

    # Preview with invalid dataset
    res_prev = client.post("/api/modeling/preview", json={
        "dataset_id": "invalid_dataset_id"
    })
    assert res_prev.status_code == 400 or res_prev.status_code == 404

    # Export with invalid dataset
    res_exp = client.post("/api/modeling/export", json={
        "dataset_id": "hack_dataset_id",
        "format": "csv"
    })
    assert res_exp.status_code == 400 or res_exp.status_code == 404
    print("  ✓ PASSED: Securely rejected invalid and unindexed dataset requests without server exceptions.")


def test_9_prevention_of_incompatible_merging():
    print("\n[Test 9/12] Prevention of Incompatible Cross-Experiment Data Merging...")
    res = client.post("/api/modeling/validate-merge", json={
        "dataset_ids": ["bass_ii_experiments", "saffire_iii_sample_1"]
    })
    assert res.status_code == 400, "Should block merging tabular run-level with continuous telemetry"
    detail = res.json()["detail"]
    assert "incompatible dataset merge blocked" in detail.lower()
    assert "tabular_run_level" in detail and "time_series_telemetry" in detail
    print("  ✓ PASSED: Explicitly blocked merging tabular MSG glovebox matrix with 30.3 Hz Cygnus telemetry.")


def test_10_rag_to_extraction_navigation():
    print("\n[Test 10/12] RAG-to-Extraction Tool Recommendation & Routing...")
    q = "I want to develop a model to predict flame spread rate using oxygen concentration, airflow velocity, and fuel material."
    evidence = [{"dataset_id": "bass_ii_experiments", "record_type": "experiment"}]
    recs = recommender.recommend(q, evidence)

    assert len(recs) >= 1
    model_rec = next((r for r in recs if r["action_id"] == "open_modeling_extraction"), None)
    assert model_rec is not None, "Predictive modeling tool should be recommended"

    assert model_rec["tab_id"] == "modeling-extraction"
    assert model_rec["tool_name"] == "Predictive-Modeling Data Extraction"
    assert "Flame Spread Rate" in model_rec["label"]
    params = model_rec["params"]
    assert params["dataset_id"] == "bass_ii_experiments"
    assert params["target_id"] == "flame_spread_rate_cm_s"
    assert params["target_status"] == "UNINSTRUMENTED_UNAVAILABLE"
    assert "Oxygen Concentration" in params["detected_features"]
    print("  ✓ PASSED: RAG assistant recommends Predictive-Modeling Data Extraction with full context handover.")


def test_11_preview_export_consistency():
    print("\n[Test 11/12] Preview and Export Consistency...")
    # Fetch preview with limit 5
    res_prev = client.post("/api/modeling/preview", json={
        "dataset_id": "bass_ii_experiments",
        "selected_features": ["fuel_material", "initial_oxygen_pct"],
        "target_id": "oxygen_consumption_delta_pct",
        "preview_limit": 5
    })
    assert res_prev.status_code == 200
    prev_rows = res_prev.json()["preview"]["preview_rows"]

    # Fetch CSV export with max_rows 5
    res_csv = client.post("/api/modeling/export", json={
        "dataset_id": "bass_ii_experiments",
        "format": "csv",
        "selected_features": ["fuel_material", "initial_oxygen_pct"],
        "target_id": "oxygen_consumption_delta_pct",
        "max_rows": 5
    })
    assert res_csv.status_code == 200
    csv_rows = list(csv.reader(io.StringIO(res_csv.text)))
    headers = csv_rows[0]
    data_rows = csv_rows[1:]

    assert len(prev_rows) == len(data_rows) == 5

    # Check that each row value matches
    for i in range(5):
        p_row = prev_rows[i]
        c_row = data_rows[i]
        # run_id
        assert str(p_row["run_id"]) == str(c_row[headers.index("run_id")])
        # fuel_material
        assert str(p_row["fuel_material"]) == str(c_row[headers.index("fuel_material")])
        # initial_oxygen_pct
        assert float(p_row["initial_oxygen_pct"]) == float(c_row[headers.index("initial_oxygen_pct")])
        # oxygen_consumption_delta_pct
        assert round(float(p_row["oxygen_consumption_delta_pct"]), 3) == round(float(c_row[headers.index("oxygen_consumption_delta_pct")]), 3)

    print("  ✓ PASSED: 100% deterministic value-for-value match between UI preview and exported CSV.")


def test_12_non_regression_existing_services():
    print("\n[Test 12/12] Non-Regression of Existing Services...")
    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200

    # 2. Existing datasets list
    res_ds = client.get("/api/datasets")
    assert res_ds.status_code == 200
    assert len(res_ds.json()["datasets"]) >= 10

    # 3. Existing RAG summary
    res_rag = client.get("/api/rag/summary")
    assert res_rag.status_code == 200

    # 4. Research Gap findings
    res_gaps = client.get("/api/research-gaps/findings")
    assert res_gaps.status_code == 200
    assert res_gaps.json()["total_matched"] >= 20

    print("  ✓ PASSED: Catalog, telemetry, RAG, and research-gap APIs remain fully operational.")


if __name__ == "__main__":
    print("=" * 80)
    print("NASA FLAME — Predictive-Modeling Data Extraction Test Suite")
    print("=" * 80)

    test_1_dataset_discovery()
    test_2_correct_feature_target_identification()
    test_3_missing_target_handling()
    test_4_actual_csv_export()
    test_5_metadata_and_units_preservation()
    test_6_missing_data_detection()
    test_7_timeseries_and_runlevel_extraction()
    test_8_invalid_dataset_requests()
    test_9_prevention_of_incompatible_merging()
    test_10_rag_to_extraction_navigation()
    test_11_preview_export_consistency()
    test_12_non_regression_existing_services()

    print("\n" + "=" * 80)
    print("ALL 12 PREDICTIVE-MODELING TESTS PASSED (100% Success Rate)")
    print("=" * 80)
