
from pathlib import Path
import json
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "processed_data" / "saffire" / "telemetry"

OUTPUT = DATA_DIR / "telemetry_layout_audit.json"

DATASETS = {
    "raw_data": "CygnusTimestamp",
    "cygnus_data": "CygnusTimestamp",
    "cygnus_smoke_detector_data": "CygnusTimestamp",
    "cygnus_pressure_data": "CygnusTimestamp",
    "cygnus_temperature_data": "CygnusTimestamp",
    "saffire_data": "SaffireTimestamp"
}

# Plausible Unix timestamps in milliseconds.
# Screening range only, not scientific verification.
MIN_TIMESTAMP = 946684800000   # 2000-01-01 UTC
MAX_TIMESTAMP = 4102444800000  # 2100-01-01 UTC

results = []

for dataset_id, time_column in DATASETS.items():

    print(f"\nAuditing: {dataset_id}")

    source = DATA_DIR / f"{dataset_id}.csv"

    if not source.exists():
        results.append({
            "dataset": dataset_id,
            "status": "missing_file"
        })
        continue

    df = pd.read_csv(
        source,
        low_memory=False
    )

    if time_column not in df.columns:
        results.append({
            "dataset": dataset_id,
            "status": "missing_timestamp_column"
        })
        continue

    timestamps = pd.to_numeric(
        df[time_column],
        errors="coerce"
    )

    valid_mask = timestamps.between(
        MIN_TIMESTAMP,
        MAX_TIMESTAMP
    )

    invalid_mask = (
        timestamps.notna() & ~valid_mask
    )

    missing_mask = timestamps.isna()

    valid_rows = df.loc[valid_mask]

    def row_range(frame):
        if frame.empty:
            return None

        return {
            "first": int(
                frame["source_excel_row"].min()
            ),
            "last": int(
                frame["source_excel_row"].max()
            )
        }

    # Inspect all columns individually.
    column_profiles = []

    for col in df.columns:
        if col == "source_excel_row":
            continue

        series = df[col]

        nonempty = series.notna()

        column_profiles.append({
            "column": col,
            "non_empty_rows": int(nonempty.sum()),
            "empty_rows": int((~nonempty).sum()),
            "first_non_empty_excel_row": (
                int(df.loc[
                    nonempty, "source_excel_row"
                ].iloc[0])
                if nonempty.any() else None
            ),
            "last_non_empty_excel_row": (
                int(df.loc[
                    nonempty, "source_excel_row"
                ].iloc[-1])
                if nonempty.any() else None
            )
        })

    # Time checks on valid timestamps.
    valid_times = timestamps[valid_mask]
    valid_diffs = valid_times.diff().dropna()

    result = {
        "dataset": dataset_id,
        "status": "audited",
        "total_rows": int(len(df)),
        "timestamp_column": time_column,
        "valid_timestamp_rows": int(valid_mask.sum()),
        "missing_timestamp_rows": int(missing_mask.sum()),
        "out_of_range_timestamp_rows": int(
            invalid_mask.sum()
        ),
        "valid_timestamp_excel_row_range": row_range(
            valid_rows
        ),
        "duplicate_valid_timestamps": int(
            valid_times.duplicated().sum()
        ),
        "negative_valid_time_differences": int(
            (valid_diffs < 0).sum()
        ),
        "out_of_range_examples": df.loc[
            invalid_mask,
            ["source_excel_row", time_column]
        ].head(10).to_dict(orient="records"),
        "columns": column_profiles,
        "scientific_review_status": "pending"
    }

    results.append(result)

    print(f"Total rows: {len(df)}")
    print(f"Valid timestamp rows: {valid_mask.sum()}")
    print(f"Missing timestamps: {missing_mask.sum()}")
    print(
        "Out-of-range timestamps:",
        invalid_mask.sum()
    )

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(
        results,
        f,
        indent=2,
        ensure_ascii=False
    )

print("\n====================================")
print("TELEMETRY LAYOUT AUDIT COMPLETE")
print("====================================")
print(f"Report saved to:\n{OUTPUT}")
print("Original data remains unchanged.")
