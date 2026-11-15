
import json
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

INPUT = BASE / "extracted_data" / "inspection_report.json"
OUTPUT = BASE / "processed_data" / "dataset_manifest.csv"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open(INPUT, "r", encoding="utf-8") as f:
    reports = json.load(f)


def classify(filename, sheet):
    name = (filename + " " + sheet).lower()

    if "saffire" in name or "cygnus" in name:
        return "Saffire"

    if "bass" in name or sheet.lower() in [
        "bhattacharjee", "ferkul", "miller",
        "olson", "fernandez-pello", "t'ien"
    ]:
        return "BASS"

    if "gmt" in name or "kapton" in name:
        return "SAME_candidate"

    return "Needs_review"


rows = []

for report in reports:
    filename = report["file"]

    for sheet in report.get("worksheets", []):
        rows.append({
            "source_file": filename,
            "worksheet": sheet["name"],
            "rows": sheet.get("rows", 0),
            "columns": sheet.get("columns", 0),
            "category_candidate": classify(
                filename, sheet["name"]
            ),
            "verified_investigation_id": "",
            "review_status": "pending"
        })

with open(
    OUTPUT, "w", newline="", encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Created manifest with {len(rows)} worksheets")
print(f"Saved to: {OUTPUT}")
