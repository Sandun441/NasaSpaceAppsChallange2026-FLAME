
from pathlib import Path
import json
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

DATA_DIR = (
    BASE / "processed_data"
    / "saffire" / "telemetry"
    / "analysis_ready"
)

DATASETS = [
    "raw_data",
    "cygnus_data",
    "cygnus_smoke_detector_data",
    "cygnus_pressure_data",
    "cygnus_temperature_data",
    "saffire_data"
]

# Columns representing time, row references,
# or processing metadata, not measurements.
def is_time_or_metadata(column):
    name = column.lower()

    if name in {
        "source_excel_row",
        "exclusion_reason"
    }:
        return True

    return any(term in name for term in [
        "timestamp",
        "relative time",
        "relativeseconds",
        "row to row delta",
        "cyg-saf ts",
        "rel-to-cygnus time"
    ])


def is_populated(series):
    return series.fillna("").astype(str).str.strip().ne("")


results = []

for dataset_id in DATASETS:

    source = DATA_DIR / f"{dataset_id}_excluded.csv"

    print(f"\nAuditing: {dataset_id}")

    if not source.exists():
        results.append({
            "dataset": dataset_id,
            "status": "missing_file"
        })
        continue

    df = pd.read_csv(
        source,
        dtype=str,
        keep_default_na=False,
        low_memory=False
    )

    measurement_columns = [
        col for col in df.columns
        if not is_time_or_metadata(col)
    ]

    column_counts = {}
    measurement_mask = pd.Series(
        False,
        index=df.index
    )

    for column in measurement_columns:
        populated = is_populated(df[column])

        column_counts[column] = int(populated.sum())
        measurement_mask |= populated

    rows_with_measurements = df.loc[measurement_mask]

    missing_timestamp_measurements = df.loc[
        measurement_mask
        & df["exclusion_reason"].eq(
            "missing_or_non_numeric_primary_timestamp"
        )
    ]

    examples = []

    for _, row in rows_with_measurements.head(10).iterrows():

        populated_values = {
            column: row[column]
            for column in measurement_columns
            if str(row[column]).strip()
        }

        examples.append({
            "source_excel_row": row["source_excel_row"],
            "exclusion_reason": row["exclusion_reason"],
            "measurement_preview": dict(
                list(populated_values.items())[:8]
            )
        })

    result = {
        "dataset": dataset_id,
        "status": "success",
        "excluded_rows": len(df),
        "rows_with_measurement_values": int(
            measurement_mask.sum()
        ),
        "rows_without_measurement_values": int(
            (~measurement_mask).sum()
        ),
        "missing_timestamp_rows_with_measurements": int(
            len(missing_timestamp_measurements)
        ),
        "populated_measurement_columns": {
            col: count
            for col, count in column_counts.items()
            if count > 0
        },
        "examples": examples,
        "review_status": "pending"
    }

    results.append(result)

    print(f"Excluded rows: {len(df)}")
    print(
        "Rows containing measurement values:",
        result["rows_with_measurement_values"]
    )

OUTPUT = DATA_DIR / "excluded_telemetry_audit.json"

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(
        results,
        f,
        indent=2,
        ensure_ascii=False
    )

print("\nEXCLUDED TELEMETRY AUDIT COMPLETED")
print(f"Saved to: {OUTPUT}")
print("No original data was modified.")
