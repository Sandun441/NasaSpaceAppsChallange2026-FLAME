
from pathlib import Path
import pandas as pd
import json
import hashlib
import re

# ==========================================
# 1. Configuration
# ==========================================

BASE = Path(__file__).resolve().parents[1]

SOURCE = (
    BASE / "raw_data" / "PSI-102"
    / "Saffire III Sample 1 Sensors.xlsx"
)

OUTPUT_DIR = BASE / "processed_data" / "saffire"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_OUTPUT = OUTPUT_DIR / "saffire_iii_sample_1.csv"
METADATA_OUTPUT = OUTPUT_DIR / "saffire_iii_sample_1_metadata.json"

SHEET_NAME = "Calibrated Data"

# ==========================================
# 2. Read source workbook
# ==========================================

if not SOURCE.exists():
    raise FileNotFoundError(f"Missing file: {SOURCE}")

print("Reading Saffire III Sample 1...")

# Preserve original text values, including timestamps.
df = pd.read_excel(
    SOURCE,
    sheet_name=SHEET_NAME,
    header=None,
    dtype=object
)

# First row contains measurement names.
# Second row contains units.
headers = df.iloc[0].tolist()
units = df.iloc[1].tolist()

# Actual measurements begin on Excel row 3.
data = df.iloc[2:].copy()

# ==========================================
# 3. Preserve column names and units
# ==========================================

column_names = []
column_metadata = []
used_names = set()

for index, (header, unit) in enumerate(zip(headers, units)):

    original_name = (
        str(header).strip()
        if pd.notna(header) else ""
    )

    original_unit = (
        str(unit).strip()
        if pd.notna(unit) else ""
    )

    name = original_name or f"unnamed_column_{index + 1}"

    # Make sure column names are unique.
    if name in used_names:
        name = f"{name}_column_{index + 1}"

    used_names.add(name)
    column_names.append(name)

    column_metadata.append({
        "source_column": index + 1,
        "column_name": name,
        "original_header": original_name,
        "original_unit": original_unit or None
    })

data.columns = column_names

# Remove completely empty measurement rows.
data = data.dropna(how="all").copy()

# ==========================================
# 4. Add provenance information
# ==========================================

data.insert(0, "source_file", SOURCE.name)
data.insert(1, "source_worksheet", SHEET_NAME)

# Pandas index is zero-based. Original data
# starts at Excel row 3.
data.insert(2, "source_excel_row", data.index + 1)

# ==========================================
# 5. Basic quality inspection
# ==========================================

measurement_columns = [
    col for col in column_names
    if col not in {
        "Elapsed Time (s)",
        "Epoch Time",
        "Timestamp (ms)",
        "Index"
    }
]

missing_counts = {
    col: int(data[col].isna().sum())
    for col in column_names
}

# Record possible numeric-conversion issues
# without changing the original measurements.
numeric_issues = {}

for col in measurement_columns:
    values = data[col].dropna()

    if values.empty:
        continue

    parsed = pd.to_numeric(values, errors="coerce")

    failures = int(parsed.isna().sum())

    if failures:
        numeric_issues[col] = failures

# ==========================================
# 6. Save structured measurements
# ==========================================

data.to_csv(
    DATA_OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 7. Save metadata and source information
# ==========================================

sha256 = hashlib.sha256()

with open(SOURCE, "rb") as file:
    for chunk in iter(lambda: file.read(1024 * 1024), b""):
        sha256.update(chunk)

metadata = {
    "dataset": "Saffire III Sample 1",
    "source_file": SOURCE.name,
    "source_worksheet": SHEET_NAME,
    "source_sha256": sha256.hexdigest(),
    "source_header_row": 1,
    "source_units_row": 2,
    "source_data_start_row": 3,
    "extracted_records": len(data),
    "total_columns": len(column_names),
    "columns": column_metadata,
    "missing_values_per_column": missing_counts,
    "non_numeric_values_per_measurement": numeric_issues,
    "processing_status": "extracted_not_validated",
    "verified_investigation_id": None
}

with open(
    METADATA_OUTPUT,
    "w",
    encoding="utf-8"
) as file:
    json.dump(metadata, file, indent=2)

# ==========================================
# 8. Display extraction summary
# ==========================================

print("\n====================================")
print("SAFFIRE EXTRACTION COMPLETED")
print("====================================")

print(f"Records extracted: {len(data)}")
print(f"Measurement columns: {len(column_names)}")

print(f"\nData saved to:\n{DATA_OUTPUT}")
print(f"\nMetadata saved to:\n{METADATA_OUTPUT}")

print("\nFirst 10 columns:")

for item in column_metadata[:10]:
    print(
        f"- {item['column_name']} "
        f"({item['original_unit'] or 'unit not specified'})"
    )

print("\nExtraction completed successfully!")
