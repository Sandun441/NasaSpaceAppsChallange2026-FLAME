
from pathlib import Path
from openpyxl import load_workbook
import csv
import json
import hashlib
from datetime import datetime, date

# =========================================
# 1. Configuration
# =========================================

BASE = Path(__file__).resolve().parents[1]

SOURCE = (
    BASE / "raw_data" / "PSI-102"
    / "Saffire-III Telemetry Data.xlsx"
)

OUTPUT_DIR = (
    BASE / "processed_data" / "saffire"
    / "telemetry"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SHEETS = {
    "RawData": ("raw_data", 1),
    "CygnusData": ("cygnus_data", 1),
    "CygnusSmokeDetectorData": (
        "cygnus_smoke_detector_data", 2
    ),
    "CygnusPressureData": (
        "cygnus_pressure_data", 1
    ),
    "CygnusTemperatureData": (
        "cygnus_temperature_data", 1
    ),
    "SaffireData": ("saffire_data", 1)
}


# =========================================
# 2. Helper functions
# =========================================

def safe_value(value):
    if value is None:
        return ""

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


def create_headers(values):
    headers = []
    used = set()

    for i, value in enumerate(values):
        original = str(value).strip() if value is not None else ""
        name = original or f"unnamed_column_{i + 1}"

        if name in used:
            name = f"{name}_column_{i + 1}"

        used.add(name)
        headers.append(name)

    return headers


def calculate_hash(path):
    sha = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            sha.update(chunk)

    return sha.hexdigest()


# =========================================
# 3. Validate source
# =========================================

if not SOURCE.exists():
    raise FileNotFoundError(
        f"Telemetry workbook not found: {SOURCE}"
    )

print("Opening NASA Saffire telemetry workbook...")

workbook = load_workbook(
    SOURCE,
    read_only=True,
    data_only=True
)

summary = []

try:
    for sheet_name, (dataset_id, header_row) in SHEETS.items():

        print(f"\nProcessing: {sheet_name}")

        if sheet_name not in workbook.sheetnames:
            summary.append({
                "dataset": dataset_id,
                "status": "missing_worksheet"
            })
            continue

        try:
            sheet = workbook[sheet_name]

            # Read exact header row.
            header_values = next(
                sheet.iter_rows(
                    min_row=header_row,
                    max_row=header_row,
                    values_only=True
                )
            )

            headers = create_headers(header_values)

            csv_path = OUTPUT_DIR / f"{dataset_id}.csv"
            metadata_path = (
                OUTPUT_DIR / f"{dataset_id}_metadata.json"
            )

            count = 0
            blank_rows = 0

            with open(
                csv_path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "source_excel_row",
                    *headers
                ])

                for excel_row, values in enumerate(
                    sheet.iter_rows(
                        min_row=header_row + 1,
                        values_only=True
                    ),
                    start=header_row + 1
                ):

                    if all(
                        value is None for value in values
                    ):
                        blank_rows += 1
                        continue

                    writer.writerow([
                        excel_row,
                        *[safe_value(v) for v in values]
                    ])

                    count += 1

            metadata = {
                "dataset": dataset_id,
                "source_file": SOURCE.name,
                "source_worksheet": sheet_name,
                "source_header_row": header_row,
                "source_data_start_row": header_row + 1,
                "source_columns": len(headers),
                "extracted_records": count,
                "blank_rows_skipped": blank_rows,
                "original_headers": headers,
                "processing_status": "extracted_not_validated",
                "verified_investigation_id": None,
                "notes": [
                    "Original row order preserved.",
                    "No sensor values were normalized.",
                    "Blank cells remain blank.",
                    "Zero and negative values preserved.",
                    "Repeated timestamps retained.",
                    "Auxiliary columns retained.",
                    "Units not independently verified.",
                    "Spreadsheet formulas read as cached values."
                ]
            }

            with open(
                metadata_path,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(metadata, file, indent=2)

            summary.append({
                "dataset": dataset_id,
                "worksheet": sheet_name,
                "status": "success",
                "records": count,
                "columns": len(headers),
                "blank_rows_skipped": blank_rows
            })

            print(f"Extracted {count} rows")

        except Exception as error:
            print(f"ERROR: {error}")
            summary.append({
                "dataset": dataset_id,
                "status": "error",
                "message": str(error)
            })

finally:
    workbook.close()


# =========================================
# 4. Save batch summary
# =========================================

report = {
    "source_file": SOURCE.name,
    "source_sha256": calculate_hash(SOURCE),
    "datasets": summary,
    "scientific_validation_status": "pending"
}

summary_path = (
    OUTPUT_DIR / "telemetry_extraction_summary.json"
)

with open(
    summary_path,
    "w",
    encoding="utf-8"
) as file:
    json.dump(report, file, indent=2)

print("\n========================================")
print("SAFFIRE TELEMETRY EXTRACTION COMPLETED")
print("========================================")

for item in summary:
    print(
        f"{item['dataset']}: "
        f"{item['status']} "
        f"({item.get('records', 0)} rows)"
    )

print(f"\nSummary saved to: {summary_path}")
