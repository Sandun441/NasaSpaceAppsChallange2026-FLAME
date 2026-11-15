
from pathlib import Path
import csv
import json

BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "processed_data"
SAFFIRE = PROCESSED / "saffire"
TELEMETRY = SAFFIRE / "telemetry"

OUTPUT_DIR = PROCESSED / "catalog"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

datasets = []
warnings = []


def load_json(path):
    if not path.exists():
        warnings.append(f"Missing metadata: {path.name}")
        return None

    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def relative_path(path):
    return str(path.relative_to(BASE)).replace("\\", "/")


def count_csv_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return max(0, sum(1 for _ in csv.reader(f)) - 1)


def add_dataset(
    dataset_id,
    category,
    granularity,
    path,
    records,
    source_file,
    worksheet,
    metadata_path=None,
    quality_path=None,
    notes=None
):
    if not path.exists():
        warnings.append(f"Missing dataset: {path.name}")
        return

    datasets.append({
        "dataset_id": dataset_id,
        "category": category,
        "granularity": granularity,
        "data_file": relative_path(path),
        "record_count": int(records),
        "source_file": source_file,
        "source_worksheet": worksheet,
        "metadata_file": (
            relative_path(metadata_path)
            if metadata_path and metadata_path.exists()
            else None
        ),
        "quality_report": (
            relative_path(quality_path)
            if quality_path and quality_path.exists()
            else None
        ),
        "scientific_validation": "pending",
        "investigation_id": None,
        "notes": notes or []
    })


# ==========================================
# 1. Register BASS-II
# ==========================================

bass_path = PROCESSED / "bass_ii_experiments.csv"
bass_quality = PROCESSED / "bass_ii_validation.csv"

if bass_path.exists():
    add_dataset(
        dataset_id="bass_ii_experiments",
        category="combustion",
        granularity="experiment",
        path=bass_path,
        records=count_csv_rows(bass_path),
        source_file="BASS-II Test Matrix by PI Final.xlsx",
        worksheet="Multiple worksheets",
        quality_path=bass_quality,
        notes=[
            "Experiment-level test matrix",
            "Original measurement values preserved",
            "Flagged readings require scientific review"
        ]
    )
else:
    warnings.append("BASS-II extraction not found")


# ==========================================
# 2. Register four Saffire datasets
# ==========================================

sensor_ids = [
    "saffire_iii_sample_1",
    "saffire_iii_sample_2",
    "saffire_sample_5",
    "saffire_sample_6"
]

for dataset_id in sensor_ids:
    data_path = SAFFIRE / f"{dataset_id}.csv"
    meta_path = SAFFIRE / f"{dataset_id}_metadata.json"
    quality_path = SAFFIRE / f"{dataset_id}_validation.json"

    metadata = load_json(meta_path)

    if metadata is None:
        continue

    add_dataset(
        dataset_id=dataset_id,
        category="combustion",
        granularity="sensor_time_series",
        path=data_path,
        records=metadata["extracted_records"],
        source_file=metadata["source_file"],
        worksheet=metadata["source_worksheet"],
        metadata_path=meta_path,
        quality_path=quality_path,
        notes=[
            "Original sensor columns and units preserved",
            "Sample is independently identified",
            "Negative and constant channels require review"
        ]
    )


# ==========================================
# 3. Register six telemetry datasets
# ==========================================

telemetry_summary = load_json(
    TELEMETRY / "telemetry_extraction_summary.json"
)

preparation = load_json(
    TELEMETRY / "analysis_ready"
    / "telemetry_preparation_summary.json"
)

prepared_lookup = {}

if isinstance(preparation, list):
    prepared_lookup = {
        item["dataset"]: item
        for item in preparation
        if item.get("status") == "success"
    }

if telemetry_summary:
    for item in telemetry_summary["datasets"]:

        if item.get("status") != "success":
            continue

        dataset_id = item["dataset"]

        analysis_path = (
            TELEMETRY / "analysis_ready"
            / f"{dataset_id}_analysis.csv"
        )

        source_path = TELEMETRY / f"{dataset_id}.csv"

        # Prefer timestamp-screened version, while
        # retaining original extraction separately.
        use_prepared = (
            analysis_path.exists()
            and dataset_id in prepared_lookup
        )

        selected_path = (
            analysis_path if use_prepared else source_path
        )

        records = (
            prepared_lookup[dataset_id]["analysis_rows"]
            if use_prepared else item["records"]
        )

        add_dataset(
            dataset_id=f"telemetry_{dataset_id}",
            category="spacecraft_telemetry",
            granularity="telemetry_time_series",
            path=selected_path,
            records=records,
            source_file=telemetry_summary["source_file"],
            worksheet=item["worksheet"],
            metadata_path=(
                TELEMETRY / f"{dataset_id}_metadata.json"
            ),
            quality_path=(
                TELEMETRY / "telemetry_validation_summary.json"
            ),
            notes=[
                "Original extraction preserved separately",
                "Timestamp screening is not scientific validation",
                "Some telemetry worksheets overlap",
                "Duplicate and backward timestamps may remain",
                "Do not automatically merge with sensor datasets"
            ]
        )


# ==========================================
# 4. Save the catalog
# ==========================================

catalog = {
    "project": "NASA FLAME",
    "schema_version": "1.0",
    "dataset_count": len(datasets),
    "datasets": datasets,
    "warnings": warnings,
    "scientific_validation_status": "pending"
}

json_path = OUTPUT_DIR / "dataset_catalog.json"
csv_path = OUTPUT_DIR / "dataset_catalog.csv"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(catalog, f, indent=2, ensure_ascii=False)

fieldnames = [
    "dataset_id",
    "category",
    "granularity",
    "record_count",
    "data_file",
    "source_file",
    "source_worksheet",
    "scientific_validation"
]

with open(
    csv_path, "w", newline="", encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for item in datasets:
        writer.writerow({
            name: item.get(name)
            for name in fieldnames
        })

print("\nDATASET CATALOG CREATED")
print("=" * 40)

print(f"Registered datasets: {len(datasets)}")

for item in datasets:
    print(
        f"{item['dataset_id']}: "
        f"{item['record_count']} records"
    )

print(f"\nWarnings: {len(warnings)}")

for warning in warnings:
    print(f"WARNING: {warning}")

print(f"\nSaved: {json_path}")
print(f"Saved: {csv_path}")
