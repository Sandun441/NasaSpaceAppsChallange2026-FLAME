
from pathlib import Path
import json
import pandas as pd

# ==========================================
# 1. Configuration
# ==========================================

BASE = Path(__file__).resolve().parents[1]

SOURCE_DIR = (
    BASE / "processed_data" / "saffire" / "telemetry"
)

OUTPUT_DIR = SOURCE_DIR / "analysis_ready"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "raw_data": "CygnusTimestamp",
    "cygnus_data": "CygnusTimestamp",
    "cygnus_smoke_detector_data": "CygnusTimestamp",
    "cygnus_pressure_data": "CygnusTimestamp",
    "cygnus_temperature_data": "CygnusTimestamp",
    "saffire_data": "SaffireTimestamp"
}

# Timestamp screening range (Unix milliseconds)
MIN_TIMESTAMP = 946684800000
MAX_TIMESTAMP = 4102444800000

summary = []

# ==========================================
# 2. Process each dataset independently
# ==========================================

for dataset_id, timestamp_column in DATASETS.items():

    print(f"\nProcessing: {dataset_id}")

    source = SOURCE_DIR / f"{dataset_id}.csv"

    if not source.exists():
        summary.append({
            "dataset": dataset_id,
            "status": "missing_file"
        })
        continue

    try:
        df = pd.read_csv(
            source,
            low_memory=False
        )

        if timestamp_column not in df.columns:
            raise ValueError(
                f"Missing column: {timestamp_column}"
            )

        # Preserve all source columns and row references.
        timestamps = pd.to_numeric(
            df[timestamp_column],
            errors="coerce"
        )

        valid = timestamps.between(
            MIN_TIMESTAMP,
            MAX_TIMESTAMP
        )

        missing = timestamps.isna()
        out_of_range = timestamps.notna() & ~valid

        # ==================================
        # 3. Separate analysis and review rows
        # ==================================

        analysis = df.loc[valid].copy()
        excluded = df.loc[~valid].copy()

        excluded["exclusion_reason"] = [
            "missing_or_non_numeric_primary_timestamp"
            if missing.loc[i]
            else "out_of_range_primary_timestamp"
            for i in excluded.index
        ]

        # Save each dataset independently.
        analysis_path = (
            OUTPUT_DIR / f"{dataset_id}_analysis.csv"
        )

        excluded_path = (
            OUTPUT_DIR / f"{dataset_id}_excluded.csv"
        )

        analysis.to_csv(
            analysis_path,
            index=False,
            encoding="utf-8-sig"
        )

        excluded.to_csv(
            excluded_path,
            index=False,
            encoding="utf-8-sig"
        )

        # ==================================
        # 4. Check retained time integrity
        # ==================================

        retained_time = timestamps.loc[valid]
        differences = retained_time.diff().dropna()

        result = {
            "dataset": dataset_id,
            "status": "success",
            "source_rows": int(len(df)),
            "analysis_rows": int(len(analysis)),
            "excluded_rows": int(len(excluded)),
            "missing_timestamp_rows": int(
                missing.sum()
            ),
            "out_of_range_timestamp_rows": int(
                out_of_range.sum()
            ),
            "duplicate_retained_timestamps": int(
                retained_time.duplicated().sum()
            ),
            "backward_retained_time_transitions": int(
                (differences < 0).sum()
            ),
            "processing_status": "timestamp_screened",
            "scientific_validation_status": "pending"
        }

        summary.append(result)

        print(f"Source rows: {len(df)}")
        print(f"Retained rows: {len(analysis)}")
        print(f"Excluded rows: {len(excluded)}")

    except Exception as error:
        print(f"ERROR: {error}")

        summary.append({
            "dataset": dataset_id,
            "status": "error",
            "message": str(error)
        })

# ==========================================
# 5. Save processing summary
# ==========================================

summary_path = (
    OUTPUT_DIR / "telemetry_preparation_summary.json"
)

with open(
    summary_path,
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        summary,
        file,
        indent=2,
        ensure_ascii=False
    )

# ==========================================
# 6. Print summary
# ==========================================

print("\n====================================")
print("TELEMETRY PREPARATION COMPLETED")
print("====================================")

for result in summary:
    print(
        f"{result['dataset']}: "
        f"{result['status']} "
        f"({result.get('analysis_rows', 0)} retained)"
    )

print(f"\nSummary: {summary_path}")

print("\nOriginal datasets were not modified.")
print("Excluded rows were preserved separately.")
print("Scientific validation remains pending.")
