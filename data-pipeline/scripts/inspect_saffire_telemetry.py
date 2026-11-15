
from pathlib import Path
from datetime import date, datetime
import json
from openpyxl import load_workbook

# ==========================================
# 1. Configuration
# ==========================================

BASE = Path(__file__).resolve().parents[1]

SOURCE = (
    BASE / "raw_data" / "PSI-102"
    / "Saffire-III Telemetry Data.xlsx"
)

OUTPUT = (
    BASE / "extracted_data"
    / "saffire_telemetry_inspection.json"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

PREVIEW_ROWS = 6
MAX_PREVIEW_COLUMNS = 100


# ==========================================
# 2. Serialize Excel values
# ==========================================

def safe_value(value):
    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


# ==========================================
# 3. Inspect workbook
# ==========================================

if not SOURCE.exists():
    raise FileNotFoundError(
        f"Telemetry workbook not found: {SOURCE}"
    )

print("Opening Saffire telemetry workbook...")

# Read-only mode avoids loading the entire
# large workbook into memory.
workbook = load_workbook(
    SOURCE,
    read_only=True,
    data_only=True
)

report = {
    "source_file": SOURCE.name,
    "worksheets": []
}

try:
    for sheet in workbook.worksheets:
        print(f"\nInspecting worksheet: {sheet.title}")

        preview = []

        for row in sheet.iter_rows(
            min_row=1,
            max_row=min(PREVIEW_ROWS, sheet.max_row),
            max_col=min(
                MAX_PREVIEW_COLUMNS,
                sheet.max_column
            ),
            values_only=True
        ):
            preview.append([
                safe_value(value) for value in row
            ])

        entry = {
            "worksheet": sheet.title,
            "reported_rows": sheet.max_row,
            "reported_columns": sheet.max_column,
            "preview": preview
        }

        report["worksheets"].append(entry)

        print(f"Rows: {sheet.max_row}")
        print(f"Columns: {sheet.max_column}")

        print("First row preview:")
        if preview:
            for index, value in enumerate(preview[0]):
                if value is not None:
                    print(f"  Column {index + 1}: {value}")

finally:
    workbook.close()


# ==========================================
# 4. Save inspection report
# ==========================================

with open(OUTPUT, "w", encoding="utf-8") as file:
    json.dump(
        report,
        file,
        indent=2,
        ensure_ascii=False
    )

print("\n====================================")
print("TELEMETRY INSPECTION COMPLETED")
print("====================================")

print(f"Worksheets: {len(report['worksheets'])}")
print(f"Report saved to: {OUTPUT}")
