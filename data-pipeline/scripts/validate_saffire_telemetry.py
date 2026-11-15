
from pathlib import Path
import json
import pandas as pd

# ==========================================
# 1. Configuration
# ==========================================

BASE = Path(__file__).resolve().parents[1]

DATA_DIR = (
    BASE / "processed_data"
    / "saffire" / "telemetry"
)

DATASETS = {
    "raw_data": "CygnusTimestamp",
    "cygnus_data": "CygnusTimestamp",
    "cygnus_smoke_detector_data": "CygnusTimestamp",
    "cygnus_pressure_data": "CygnusTimestamp",
    "cygnus_temperature_data": "CygnusTimestamp",
    "saffire_data": "SaffireTimestamp"
}

OUTPUT = DATA_DIR / "telemetry_validation_summary.json"
CHANNEL_OUTPUT = DATA_DIR / "telemetry_channel_statistics.csv"

results = []
channel_statistics = []

# ==========================================
# 2. Inspect each dataset
# ==========================================

for dataset_id, timestamp_column in DATASETS.items():

    print(f"\nValidating: {dataset_id}")

    source = DATA_DIR / f"{dataset_id}.csv"

    if not source.exists():
        results.append({
            "dataset": dataset_id,
            "status": "error",
            "message": "CSV file not found"
        })
        continue

    try:
        df = pd.read_csv(
            source,
            low_memory=False
        )

        if timestamp_column not in df.columns:
            raise ValueError(
                f"Missing timestamp column: {timestamp_column}"
            )

        # ----------------------------------
        # 3. Check timestamps
        # ----------------------------------

        timestamps = pd.to_numeric(
            df[timestamp_column],
            errors="coerce"
        )

        valid_time = timestamps.dropna()
        time_differences = timestamps.diff()

        timestamp_checks = {
            "missing_or_non_numeric": int(
                timestamps.isna().sum()
            ),
            "duplicate_timestamps": int(
                valid_time.duplicated().sum()
            ),
            "non_increasing_in_row_order": int(
                (time_differences <= 0).sum()
            ),
            "negative_time_differences": int(
                (time_differences < 0).sum()
            ),
            "minimum_timestamp": (
                float(valid_time.min())
                if not valid_time.empty else None
            ),
            "maximum_timestamp": (
                float(valid_time.max())
                if not valid_time.empty else None
            )
        }

        # ----------------------------------
        # 4. Check original Excel rows
        # ----------------------------------

        row_numbers = pd.to_numeric(
            df["source_excel_row"],
            errors="coerce"
        )

        row_gaps = int(
            (row_numbers.diff().dropna() > 1).sum()
        )

        # ----------------------------------
        # 5. Inspect measurement columns
        # ----------------------------------

        non_measurement_columns = {
            "source_excel_row",
            "RelativeSeconds",
            "Relative Time (ms)",
            "Relative Time (s)",
            "CygnusTimestamp",
            "SaffireTimestamp",
            "Cyg-Saf TS (ms)",
            "Row to Row Delta T (ms)"
        }

        constant_channels = []
        negative_channels = []
        total_missing = 0

        for column in df.columns:

            if column in non_measurement_columns:
                continue

            raw = df[column]

            numeric = pd.to_numeric(
                raw,
                errors="coerce"
            )

            missing = int(raw.isna().sum())
            numeric_count = int(numeric.notna().sum())
            negative_count = int((numeric < 0).sum())

            unique_values = int(
                raw.nunique(dropna=False)
            )

            total_missing += missing

            if unique_values <= 1:
                constant_channels.append(column)

            if negative_count > 0:
                negative_channels.append(column)

            channel_statistics.append({
                "dataset": dataset_id,
                "column": column,
                "total_rows": len(df),
                "numeric_values": numeric_count,
                "missing_values": missing,
                "non_numeric_values": int(
                    raw.notna().sum() - numeric_count
                ),
                "negative_values": negative_count,
                "unique_values": unique_values,
                "minimum": (
                    float(numeric.min())
                    if numeric_count else None
                ),
                "maximum": (
                    float(numeric.max())
                    if numeric_count else None
                ),
                "constant_channel": unique_values <= 1
            })

        # ----------------------------------
        # 6. Create dataset summary
        # ----------------------------------

        result = {
            "dataset": dataset_id,
            "status": "success",
            "records": int(len(df)),
            "columns": int(len(df.columns)),
            "timestamp_checks": timestamp_checks,
            "source_row_gaps": row_gaps,
            "missing_measurement_cells": total_missing,
            "constant_channels": constant_channels,
            "channels_with_negative_values": negative_channels,
            "scientific_validation_status": "pending"
        }

        results.append(result)

        print(f"Records: {len(df)}")
        print(
            "Duplicate timestamps:",
            timestamp_checks["duplicate_timestamps"]
        )
        print(
            "Negative time differences:",
            timestamp_checks["negative_time_differences"]
        )
        print("Excel row gaps:", row_gaps)
        print("Missing cells:", total_missing)

    except Exception as error:
        print(f"ERROR: {error}")

        results.append({
            "dataset": dataset_id,
            "status": "error",
            "message": str(error)
        })

# ==========================================
# 7. Save validation reports
# ==========================================

with open(OUTPUT, "w", encoding="utf-8") as file:
    json.dump(
        results,
        file,
        indent=2,
        ensure_ascii=False
    )

pd.DataFrame(channel_statistics).to_csv(
    CHANNEL_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("\n====================================")
print("TELEMETRY VALIDATION COMPLETED")
print("====================================")

print(f"Datasets checked: {len(results)}")
print(f"Saved: {OUTPUT.name}")
print(f"Saved: {CHANNEL_OUTPUT.name}")

print("\nNo original measurements were modified.")
print("Scientific validation remains pending.")
