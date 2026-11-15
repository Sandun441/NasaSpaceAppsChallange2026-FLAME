
from pathlib import Path
import pandas as pd
import json
import hashlib

BASE = Path(__file__).resolve().parents[1]

RAW_DIR = BASE / "raw_data" / "PSI-102"
OUTPUT_DIR = BASE / "processed_data" / "saffire"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "saffire_iii_sample_2": "Saffire III Sample 2 Sensors.xlsx",
    "saffire_sample_5": "Saffire Sensor Data Sample 5.xlsx",
    "saffire_sample_6": "Saffire Sensor Data Sample 6.xlsx",
}

EXPECTED_HEADERS = [
    "Elapsed Time (s)",
    "Epoch Time",
    "Timestamp (ms)",
    "Index"
]

results = []

for dataset_id, filename in FILES.items():
    source = RAW_DIR / filename

    print(f"\nProcessing: {filename}")

    if not source.exists():
        print("ERROR: File not found")
        results.append({
            "dataset": dataset_id,
            "status": "file_not_found"
        })
        continue

    try:
        df = pd.read_excel(
            source,
            sheet_name="Calibrated Data",
            header=None,
            dtype=object
        )

        # Check the worksheet format first.
        headers = [
            str(value).strip() if pd.notna(value) else ""
            for value in df.iloc[0]
        ]

        if headers[:4] != EXPECTED_HEADERS:
            raise ValueError(
                "Unexpected worksheet headers. "
                "Manual review required."
            )

        units = [
            str(value).strip() if pd.notna(value) else ""
            for value in df.iloc[1]
        ]

        data = df.iloc[2:].copy()
        data = data.dropna(how="all")

        column_names = []
        columns_metadata = []
        used = set()

        for i, (name, unit) in enumerate(
            zip(headers, units)
        ):
            column = name or f"unnamed_column_{i+1}"

            if column in used:
                column = f"{column}_column_{i+1}"

            used.add(column)
            column_names.append(column)

            columns_metadata.append({
                "source_column": i + 1,
                "column_name": column,
                "original_header": name,
                "original_unit": unit or None
            })

        data.columns = column_names

        # Preserve original source row references.
        data.insert(0, "source_file", filename)
        data.insert(1, "source_worksheet", "Calibrated Data")
        data.insert(2, "source_excel_row", data.index + 1)

        csv_path = OUTPUT_DIR / f"{dataset_id}.csv"
        json_path = OUTPUT_DIR / f"{dataset_id}_metadata.json"

        data.to_csv(
            csv_path,
            index=False,
            encoding="utf-8-sig"
        )

        # Source file integrity checksum.
        sha256 = hashlib.sha256()

        with open(source, "rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b""
            ):
                sha256.update(chunk)

        metadata = {
            "dataset": dataset_id,
            "source_file": filename,
            "source_worksheet": "Calibrated Data",
            "source_sha256": sha256.hexdigest(),
            "source_header_row": 1,
            "source_units_row": 2,
            "source_data_start_row": 3,
            "extracted_records": len(data),
            "total_columns": len(column_names),
            "columns": columns_metadata,
            "missing_values_per_column": {
                col: int(data[col].isna().sum())
                for col in column_names
            },
            "processing_status": "extracted_not_validated",
            "verified_investigation_id": None
        }

        with open(
            json_path, "w", encoding="utf-8"
        ) as file:
            json.dump(metadata, file, indent=2)

        print(f"SUCCESS: {len(data)} records extracted")

        results.append({
            "dataset": dataset_id,
            "status": "success",
            "records": len(data),
            "columns": len(column_names)
        })

    except Exception as error:
        print(f"ERROR: {error}")

        results.append({
            "dataset": dataset_id,
            "status": "error",
            "message": str(error)
        })

summary_path = OUTPUT_DIR / "batch_extraction_summary.json"

with open(summary_path, "w", encoding="utf-8") as file:
    json.dump(results, file, indent=2)

print("\nBATCH EXTRACTION COMPLETED")

for result in results:
    print(result)

print(f"\nSummary saved to: {summary_path}")
