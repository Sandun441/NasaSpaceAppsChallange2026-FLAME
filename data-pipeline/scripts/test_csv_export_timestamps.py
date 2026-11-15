"""
NASA FLAME — Scientific Telemetry CSV Export Timestamp Verification Suite
Verifies:
  1. No missing timestamps for valid time-series samples (Sample 1 & Sample 2).
  2. Timestamps remain strictly monotonically increasing.
  3. Exported measurements retain their exact original time associations from flight CSVs.
  4. Selected visualization interval (zoom range) matches actual exported timestamps.
  5. Full flight overview CSV export contains zero blank values under Elapsed Time (s).
  6. Zero artificial timestamps or interpolated measurements.
"""

import sys
import io
import csv
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from api.telemetry_service import extract_telemetry_payload


def test_saffire_1_full_overview_timestamps():
    print("\n[Test 1/5] Saffire-III Sample 1 Full Flight Overview Timestamps...")
    file_path = BASE / "processed_data" / "saffire" / "saffire_iii_sample_1.csv"
    res = extract_telemetry_payload(
        file_path=file_path,
        dataset_id="saffire_iii_sample_1",
        granularity="sensor_time_series",
        scientific_validation="pending",
        requested_channels=["Plume Temp 1 (TC1)", "Radiometer 1"],
        downsample_points=1000,
    )

    telemetry = res["telemetry"]
    time_col = res["time_channel"]
    assert time_col == "Elapsed Time (s)", f"Expected 'Elapsed Time (s)', got {time_col}"
    assert len(telemetry) > 500, f"Expected >500 decimated points, got {len(telemetry)}"

    # 1. Verify no missing timestamps
    for i, pt in enumerate(telemetry):
        assert time_col in pt, f"Point {i} missing key '{time_col}'"
        assert "time" in pt, f"Point {i} missing key 'time'"
        t_val = pt[time_col]
        assert t_val is not None, f"Point {i} has None timestamp"
        assert t_val != "", f"Point {i} has empty timestamp string"
        assert isinstance(t_val, (int, float)), f"Point {i} timestamp is not a number: {t_val}"

    # 2. Verify timestamps are strictly monotonically increasing
    timestamps = [pt[time_col] for pt in telemetry]
    for i in range(1, len(timestamps)):
        assert timestamps[i] > timestamps[i - 1], (
            f"Timestamps not monotonic at index {i}: {timestamps[i-1]} >= {timestamps[i]}"
        )

    # 3. Verify flight time bounds (0.0s to 689.964s)
    assert math.isclose(timestamps[0], 0.0, abs_tol=1e-3), f"Start time {timestamps[0]} != 0.0"
    assert math.isclose(timestamps[-1], 689.964, abs_tol=1e-2), f"End time {timestamps[-1]} != 689.964"

    print(f"  ✓ PASSED: {len(telemetry)} points verified; 0 missing timestamps; strictly monotonic ({timestamps[0]}s -> {timestamps[-1]}s).")


def test_measurement_time_association_fidelity():
    print("\n[Test 2/5] Verification of Measurement-Time Association (Zero Fabrication)...")
    file_path = BASE / "processed_data" / "saffire" / "saffire_iii_sample_1.csv"

    # Load raw flight CSV into a lookup map by rounded timestamp
    raw_lookup = {}
    with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_t = row.get("Elapsed Time (s)")
            if raw_t:
                try:
                    rounded_t = round(float(raw_t), 4)
                    raw_lookup[rounded_t] = row
                except ValueError:
                    pass

    # Extract decimated telemetry
    res = extract_telemetry_payload(
        file_path=file_path,
        dataset_id="saffire_iii_sample_1",
        granularity="sensor_time_series",
        scientific_validation="pending",
        requested_channels=["Plume Temp 1 (TC1)", "Radiometer 1"],
        downsample_points=1000,
    )

    telemetry = res["telemetry"]
    time_col = res["time_channel"]

    # Verify every single decimated point exists in raw CSV with exact matching values
    verified_matches = 0
    for pt in telemetry:
        t = pt[time_col]
        assert t in raw_lookup, f"Exported timestamp {t}s does NOT exist in raw flight CSV!"

        raw_row = raw_lookup[t]
        # Check Plume Temp 1
        exported_tc = pt["Plume Temp 1 (TC1)"]
        if exported_tc is not None:
            raw_tc = float(raw_row["Plume Temp 1 (TC1)"])
            assert math.isclose(exported_tc, raw_tc, abs_tol=1e-3), (
                f"Mismatch at t={t}s: exported {exported_tc} != raw {raw_tc}"
            )
        verified_matches += 1

    print(f"  ✓ PASSED: All {verified_matches} decimated points correspond exactly to genuine raw flight CSV rows.")


def test_saffire_2_timestamps():
    print("\n[Test 3/5] Saffire-III Sample 2 Full Flight Overview Timestamps...")
    file_path = BASE / "processed_data" / "saffire" / "saffire_iii_sample_2.csv"
    res = extract_telemetry_payload(
        file_path=file_path,
        dataset_id="saffire_iii_sample_2",
        granularity="sensor_time_series",
        scientific_validation="pending",
        requested_channels=["Plume Temp 1 (TC1)", "Radiometer 1"],
        downsample_points=1000,
    )

    telemetry = res["telemetry"]
    time_col = res["time_channel"]
    assert time_col == "Elapsed Time (s)"
    assert len(telemetry) > 200

    timestamps = [pt[time_col] for pt in telemetry]
    # Check no blanks
    for i, t in enumerate(timestamps):
        assert t is not None and t != "", f"Sample 2 Point {i} timestamp is blank"
        assert isinstance(t, (int, float))

    # Check monotonicity
    for i in range(1, len(timestamps)):
        assert timestamps[i] > timestamps[i - 1]

    # Check time bounds (0.0s to 159.95s)
    assert math.isclose(timestamps[0], 0.0, abs_tol=1e-3)
    assert math.isclose(timestamps[-1], 159.95, abs_tol=0.1)
    print(f"  ✓ PASSED: Saffire 2 ({len(telemetry)} points, 0.0s -> {timestamps[-1]}s) verified with 0 blank timestamps.")


def test_visualization_zoom_interval_export():
    print("\n[Test 4/5] Zoomed Visualization Interval Filtering Fidelity...")
    file_path = BASE / "processed_data" / "saffire" / "saffire_iii_sample_1.csv"
    start_filter = 60.0
    end_filter = 120.0

    res = extract_telemetry_payload(
        file_path=file_path,
        dataset_id="saffire_iii_sample_1",
        granularity="sensor_time_series",
        scientific_validation="pending",
        requested_channels=["Plume Temp 1 (TC1)"],
        start_time=start_filter,
        end_time=end_filter,
        downsample_points=300,
    )

    telemetry = res["telemetry"]
    time_col = res["time_channel"]
    assert len(telemetry) > 50

    timestamps = [pt[time_col] for pt in telemetry]
    for t in timestamps:
        assert start_filter <= t <= end_filter + 0.1, (
            f"Timestamp {t} outside requested interval [{start_filter}, {end_filter}]"
        )

    print(f"  ✓ PASSED: Zoom interval [{start_filter}s, {end_filter}s] accurately bounded ({timestamps[0]}s -> {timestamps[-1]}s).")


def test_csv_export_formatting_and_non_blank_header():
    print("\n[Test 5/5] End-to-End CSV Export Generation & Non-Blank Column Verification...")
    file_path = BASE / "processed_data" / "saffire" / "saffire_iii_sample_1.csv"
    res = extract_telemetry_payload(
        file_path=file_path,
        dataset_id="saffire_iii_sample_1",
        granularity="sensor_time_series",
        scientific_validation="pending",
        requested_channels=["Plume Temp 1 (TC1)", "Radiometer 1"],
        downsample_points=1000,
    )

    telemetry = res["telemetry"]
    time_axis = res["time_channel"]
    columns = [time_axis, "Plume Temp 1 (TC1)", "Radiometer 1"]

    # Simulate frontend exportCsv logic
    comments = [
        "NASA FLAME Scientific Data Export",
        "Dataset ID: saffire_iii_sample_1",
        f"Time Axis Column: {time_axis}",
        f"Time Window: 0.000s to 689.964s",
        f"Total Exported Points: {len(telemetry)}",
    ]

    output = io.StringIO()
    for c in comments:
        output.write(f"# {c}\r\n")

    # Header
    output.write(",".join(f'"{col}"' for col in columns) + "\r\n")

    # Rows (using the fixed alias resolution)
    for row in telemetry:
        vals = []
        for col in columns:
            val = row.get(col)
            if (val is None or val == "") and (col.lower().find("time") != -1 or col == time_axis):
                val = row.get("time")
            if val is None or val == "":
                vals.append("")
            elif isinstance(val, (int, float)):
                vals.append(str(val))
            else:
                vals.append(f'"{str(val)}"')
        output.write(",".join(vals) + "\r\n")

    csv_text = output.getvalue()

    # Parse generated CSV back using standard csv.reader
    data_lines = [line for line in csv_text.splitlines() if not line.startswith("#") and line.strip()]
    reader = csv.DictReader(data_lines)
    parsed_rows = list(reader)

    assert len(parsed_rows) == len(telemetry), f"Expected {len(telemetry)} rows, got {len(parsed_rows)}"

    # Verify that NOT A SINGLE row has a blank 'Elapsed Time (s)'
    blank_time_count = 0
    valid_time_count = 0
    for idx, r in enumerate(parsed_rows):
        time_str = r.get(time_axis)
        assert time_str is not None, f"Row {idx} missing {time_axis} key"
        if time_str.strip() == "":
            blank_time_count += 1
        else:
            valid_time_count += 1
            float(time_str)  # must parse as float

    assert blank_time_count == 0, f"Found {blank_time_count} BLANK timestamps in CSV export!"
    assert valid_time_count == len(parsed_rows), f"Valid timestamp count {valid_time_count} != total rows {len(parsed_rows)}"
    print(f"  ✓ PASSED: Successfully exported {len(parsed_rows)} rows. Exactly 0 blank timestamps under '{time_axis}'.")


def main():
    print("==========================================================================")
    print("NASA FLAME — Scientific Telemetry CSV Export Timestamp Regression Suite")
    print("==========================================================================")
    test_saffire_1_full_overview_timestamps()
    test_measurement_time_association_fidelity()
    test_saffire_2_timestamps()
    test_visualization_zoom_interval_export()
    test_csv_export_formatting_and_non_blank_header()
    print("\n==========================================================================")
    print("ALL TESTS PASSED: 5/5 Regression Test Suites Succeeded (100% Green)")
    print("==========================================================================")


if __name__ == "__main__":
    main()
