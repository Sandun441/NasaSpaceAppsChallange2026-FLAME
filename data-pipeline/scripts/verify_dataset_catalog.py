
from pathlib import Path
import csv
import json

BASE = Path(__file__).resolve().parents[1]

CATALOG_PATH = (
    BASE / "processed_data"
    / "catalog" / "dataset_catalog.json"
)

OUTPUT_PATH = (
    BASE / "processed_data"
    / "catalog" / "catalog_verification.json"
)


def count_csv_records(path):
    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        reader = csv.reader(file)

        header = next(reader, None)

        if not header:
            raise ValueError("Missing CSV header")

        if len(header) != len(set(header)):
            raise ValueError("Duplicate CSV column names")

        count = 0
        invalid_width_rows = 0

        for row in reader:
            count += 1

            if len(row) != len(header):
                invalid_width_rows += 1

        return count, len(header), invalid_width_rows


with open(CATALOG_PATH, encoding="utf-8") as file:
    catalog = json.load(file)

results = []

seen_ids = set()

for dataset in catalog["datasets"]:

    dataset_id = dataset["dataset_id"]
    relative_path = dataset["data_file"]

    # Prevent catalog paths from escaping
    # the local data-pipeline directory.
    data_path = (BASE / relative_path).resolve()

    result = {
        "dataset_id": dataset_id,
        "expected_records": dataset["record_count"],
        "actual_records": None,
        "columns": None,
        "invalid_width_rows": None,
        "status": "pending"
    }

    try:
        if dataset_id in seen_ids:
            raise ValueError("Duplicate dataset ID")

        seen_ids.add(dataset_id)

        if not data_path.is_relative_to(BASE.resolve()):
            raise ValueError("Unsafe dataset path")

        if data_path.suffix.lower() != ".csv":
            raise ValueError("Expected a CSV file")

        if not data_path.is_file():
            raise FileNotFoundError(data_path)

        actual, columns, invalid = count_csv_records(
            data_path
        )

        result["actual_records"] = actual
        result["columns"] = columns
        result["invalid_width_rows"] = invalid

        if actual != dataset["record_count"]:
            result["status"] = "record_count_mismatch"

        elif invalid > 0:
            result["status"] = "invalid_csv_structure"

        else:
            result["status"] = "passed"

    except Exception as error:
        result["status"] = "failed"
        result["error"] = str(error)

    results.append(result)

all_passed = (
    len(results) == catalog["dataset_count"]
    and len(seen_ids) == len(results)
    and all(
        item["status"] == "passed"
        for item in results
    )
)

report = {
    "project": "NASA FLAME",
    "catalog_dataset_count": catalog["dataset_count"],
    "verified_dataset_count": len(results),
    "passed": sum(
        item["status"] == "passed"
        for item in results
    ),
    "all_passed": all_passed,
    "results": results
}

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as file:
    json.dump(report, file, indent=2)

print("\nNASA FLAME — CATALOG VERIFICATION")
print("=" * 45)

for result in results:
    print(
        f"{result['dataset_id']}: "
        f"{result['status']}"
    )

print("\nOverall result:",
      "PASSED" if all_passed else "REVIEW REQUIRED")

print(f"Report saved: {OUTPUT_PATH}")
