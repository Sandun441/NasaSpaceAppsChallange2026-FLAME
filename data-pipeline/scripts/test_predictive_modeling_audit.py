"""
NASA FLAME — Predictive-Modeling Scientific Correctness Audit & Regression Suite
Verifies all 7 audit findings and fixes:
1. Export & audit population consistency across CSV, JSON metadata, Markdown report, and UI preview.
2. Airflow velocity proxy parsing eliminates 54,321 and 5.105e15, returning initial flow 5.0 for B10 and O5a.
3. Fan display parsing eliminates 6.852e11, returning initial fan 68.0 for M6.
4. Oxygen consumption anomalies (+20.6%, -19.7%) are preserved from raw NASA records, flagged, and audited.
5. Population taxonomy distinguishes available, filtered, labeled, complete-case, previewed, and exported counts.
6. Saffire peak plume temperature target is verified at 95.64 °C for Sample 1 (TC3) and 48.35 °C for Sample 2, with leakage warnings.
7. UI preview displays accurate total filtered records (129) alongside preview slice (25).
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
from modeling.registry import get_modeling_dataset_metadata
from modeling.extraction_service import PredictiveDataExtractionService, parse_initial_numeric, detect_airflow_profile

client = TestClient(app)
service = PredictiveDataExtractionService(base_dir=BASE_DIR)


def test_1_airflow_parsing_fixes():
    print("\n[Audit Test 1/7] Airflow Velocity Parsing Fixes (B10, O5a)...")
    # Raw values:
    # B10 cell in Excel: '5,4,3,2,1' -> must parse to 5.0, not 54321
    # O5a cell in Excel: '5,10,5, 2, 0 (49, 62, 49, 44, 42)' -> must parse to 5.0, not 5.105e15
    assert parse_initial_numeric("5,4,3,2,1") == 5.0
    assert parse_initial_numeric("5,10,5, 2, 0 (49, 62, 49, 44, 42)") == 5.0
    assert parse_initial_numeric("10, 5, 3, 0") == 10.0
    assert parse_initial_numeric("0") == 0.0

    # In extracted dataset
    df, meta, quality = service.extract_dataset(
        dataset_id="bass_ii_experiments",
        selected_features=["fuel_material", "initial_oxygen_pct", "airflow_velocity_proxy"],
        target_id="oxygen_consumption_delta_pct"
    )
    b10_row = df[df["run_id"] == "B10"].iloc[0]
    assert b10_row["airflow_velocity_proxy"] == 5.0, f"Expected 5.0 for B10, got {b10_row['airflow_velocity_proxy']}"

    o5a_row = df[df["run_id"] == "O5a"].iloc[0]
    assert o5a_row["airflow_velocity_proxy"] == 5.0, f"Expected 5.0 for O5a, got {o5a_row['airflow_velocity_proxy']}"

    # Verify airflow profile detection
    assert detect_airflow_profile("5,4,3,2,1") == "dynamic_multi_step"
    assert detect_airflow_profile("5") == "constant"
    print("  ✓ PASSED: B10 parsed to 5.0 cm/s and O5a parsed to 5.0 cm/s. Catastrophic concatenation eliminated.")


def test_2_fan_display_parsing_fixes():
    print("\n[Audit Test 2/7] Fan Speed Display Parsing Fixes (M6, B10)...")
    # Raw values:
    # M6 cell in Excel: '68, 52, 47, 43, 42, 41' -> must parse to 68.0, not 6.852e11
    # B10 cell in Excel: '1.7 (52), 1.25, 0.9, 0.6, 0.4, 0.35' -> must parse to 1.7
    assert parse_initial_numeric("68, 52, 47, 43, 42, 41") == 68.0
    assert parse_initial_numeric("1.7 (52), 1.25, 0.9, 0.6, 0.4, 0.35") == 1.7
    assert parse_initial_numeric("pot 1.1") == 1.1

    df, _, _ = service.extract_dataset(
        dataset_id="bass_ii_experiments",
        selected_features=["fan_display"],
        target_id="oxygen_consumption_delta_pct"
    )
    m6_row = df[df["run_id"] == "M6"].iloc[0]
    assert m6_row["fan_display"] == 68.0, f"Expected 68.0 for M6, got {m6_row['fan_display']}"
    print("  ✓ PASSED: M6 fan speed parsed to 68.0 RPM proxy. Catastrophic concatenation eliminated.")


def test_3_oxygen_consumption_anomalies_and_flags():
    print("\n[Audit Test 3/7] Oxygen Consumption Empirical Anomalies & Quality Flags...")
    df, _, quality = service.extract_dataset(
        dataset_id="bass_ii_experiments",
        target_id="oxygen_consumption_delta_pct"
    )

    # 1. Verify B2 (Initial 22.2, Final 1.6 -> Delta +20.6 percentage points)
    b2_row = df[df["run_id"] == "B2"].iloc[0]
    assert abs(b2_row["oxygen_consumption_delta_pct"] - 20.6) < 0.05
    assert "flagged_o2_source_anomaly_delta_+20.6pct" in b2_row["data_quality_flags"]

    # 2. Verify T28b (Initial 20.7, Final 40.4 -> Delta -19.7 percentage points)
    t28b_row = df[df["run_id"] == "T28b"].iloc[0]
    assert abs(t28b_row["oxygen_consumption_delta_pct"] - (-19.7)) < 0.05
    assert "flagged_o2_source_anomaly_delta_-19.7pct" in t28b_row["data_quality_flags"]

    # 3. Verify quality report counts and disclosures
    assert quality["anomalous_records_count"] >= 5
    anom_runs = [d["run_id"] for d in quality["anomalous_records_details"]]
    assert "B2" in anom_runs
    assert "P22a" in anom_runs
    assert "P22b" in anom_runs
    assert "T28a" in anom_runs
    assert "T28b" in anom_runs

    # 4. Verify exclude_flagged_anomalies toggle
    df_clean, _, quality_clean = service.extract_dataset(
        dataset_id="bass_ii_experiments",
        target_id="oxygen_consumption_delta_pct",
        exclude_flagged_anomalies=True
    )
    assert len(df_clean) == len(df) - quality["anomalous_records_count"]
    assert "B2" not in df_clean["run_id"].values
    assert "T28b" not in df_clean["run_id"].values
    print("  ✓ PASSED: Empirical source anomalies (+20.6%, -19.7%) faithfully preserved, flagged, and excludable.")


def test_4_population_taxonomy_and_consistency():
    print("\n[Audit Test 4/7] Population Accounting Consistency Across CSV, JSON, MD & Preview...")
    target = "oxygen_consumption_delta_pct"

    # Preview API
    prev_res = client.post("/api/modeling/preview", json={
        "dataset_id": "bass_ii_experiments",
        "target_id": target,
        "preview_limit": 25
    }).json()["preview"]

    # CSV Export API
    csv_res = client.post("/api/modeling/export", json={
        "dataset_id": "bass_ii_experiments",
        "format": "csv",
        "target_id": target
    })
    csv_rows = list(csv.DictReader(io.StringIO(csv_res.text)))

    # JSON Export API
    json_res = client.post("/api/modeling/export", json={
        "dataset_id": "bass_ii_experiments",
        "format": "json",
        "target_id": target
    }).json()

    # Markdown Export API
    md_res = client.post("/api/modeling/export", json={
        "dataset_id": "bass_ii_experiments",
        "format": "report",
        "target_id": target
    }).text

    # Assertions across representations
    assert prev_res["preview_count"] == 25
    assert prev_res["total_filtered_count"] == 129
    assert prev_res["total_extracted_count"] == 129

    assert len(csv_rows) == 129
    assert json_res["record_counts"]["total_available_records"] == 129
    assert json_res["record_counts"]["filtered_records_count"] == 129
    assert json_res["record_counts"]["exported_records_count"] == 129
    assert json_res["quality_audit"]["extracted_records_count"] == 129

    assert "- **Total Records in Source:** 129" in md_res
    assert "- **Filtered Records Matching Filter:** 129" in md_res
    assert "- **Exported Records Count:** 129" in md_res

    # Verify completeness matches
    json_comp = json_res["quality_audit"]["data_completeness_pct"]
    prev_comp = prev_res["quality_report"]["data_completeness_pct"]
    assert json_comp == prev_comp
    assert f"- **Overall Data Completeness:** {json_comp}%" in md_res

    print(f"  ✓ PASSED: 129 records and {json_comp}% completeness are 100% consistent across CSV, JSON, MD, and Preview.")


def test_5_complete_cases_and_missing_data_filtering():
    print("\n[Audit Test 5/7] Complete-Case vs Labeled vs Available Taxonomy...")
    # Baseline: 129 available, 127 labeled (2 runs lack final O2: B14, B21)
    df_base, _, q_base = service.extract_dataset(
        dataset_id="bass_ii_experiments",
        target_id="oxygen_consumption_delta_pct"
    )
    assert q_base["total_available_records"] == 129
    assert q_base["labeled_records_count"] == 127
    assert q_base["complete_case_records_count"] < 129

    # Filter with complete_cases_only=True
    df_complete, _, q_complete = service.extract_dataset(
        dataset_id="bass_ii_experiments",
        target_id="oxygen_consumption_delta_pct",
        complete_cases_only=True
    )
    assert len(df_complete) == q_base["complete_case_records_count"]
    # Verify zero missing values in complete cases
    cols_check = [c for c in df_complete.columns if c != "data_quality_flags"]
    assert df_complete[cols_check].isna().sum().sum() == 0
    print("  ✓ PASSED: Complete-case filtering drops incomplete runs; zero NaNs present when active.")


def test_6_saffire_peak_plume_temperature_and_leakage():
    print("\n[Audit Test 6/7] Saffire Peak Temperature & Target Leakage Prevention...")
    # Sample 1: True maximum across plume TC1-TC6 is 95.64 °C (on TC3)
    res_saf1 = client.post("/api/modeling/preview", json={
        "dataset_id": "saffire_iii_sample_1",
        "target_id": "peak_plume_temperature_c"
    }).json()["preview"]

    first_target_val = res_saf1["preview_rows"][0]["peak_plume_temperature_c"]
    assert abs(first_target_val - 95.644) < 0.01, f"Expected 95.64 °C, got {first_target_val}"

    # Sample 2: True maximum across plume TC1-TC6 is 48.35 °C (on TC3)
    res_saf2 = client.post("/api/modeling/preview", json={
        "dataset_id": "saffire_iii_sample_2",
        "target_id": "peak_plume_temperature_c"
    }).json()["preview"]

    first_target_val2 = res_saf2["preview_rows"][0]["peak_plume_temperature_c"]
    assert abs(first_target_val2 - 48.353) < 0.01, f"Expected 48.35 °C, got {first_target_val2}"

    # Leakage check: When plume_temp_tc1 is selected as input concurrently with event peak target
    res_saf_leak = client.post("/api/modeling/preview", json={
        "dataset_id": "saffire_iii_sample_1",
        "selected_features": ["flow_velocity_cm_s", "plume_temp_tc1"],
        "target_id": "peak_plume_temperature_c"
    }).json()["preview"]

    warnings_text = " ".join(res_saf_leak["quality_report"]["warnings"]).lower()
    assert "target leakage warning" in warnings_text
    assert "plume_temp_tc1" in warnings_text
    print("  ✓ PASSED: Saffire event peaks verified at 95.64 °C (Sample 1) and 48.35 °C (Sample 2) with leakage safeguard.")


def test_7_ui_preview_total_filtered_representation():
    print("\n[Audit Test 7/7] UI Preview Total Records Representation...")
    res = client.post("/api/modeling/preview", json={
        "dataset_id": "bass_ii_experiments",
        "preview_limit": 25
    }).json()["preview"]

    assert len(res["preview_rows"]) == 25
    assert res["total_filtered_count"] == 129
    assert res["total_extracted_count"] == 129
    assert res["complete_case_count"] > 0
    print("  ✓ PASSED: Preview response contains total_filtered_count=129 and preview_rows=25.")


if __name__ == "__main__":
    print("=" * 80)
    print("NASA FLAME — Predictive-Modeling Scientific Audit Test Suite")
    print("=" * 80)
    test_1_airflow_parsing_fixes()
    test_2_fan_display_parsing_fixes()
    test_3_oxygen_consumption_anomalies_and_flags()
    test_4_population_taxonomy_and_consistency()
    test_5_complete_cases_and_missing_data_filtering()
    test_6_saffire_peak_plume_temperature_and_leakage()
    test_7_ui_preview_total_filtered_representation()
    print("\n" + "=" * 80)
    print("ALL 7 SCIENTIFIC AUDIT TESTS PASSED (100% Success Rate)")
    print("=" * 80)
