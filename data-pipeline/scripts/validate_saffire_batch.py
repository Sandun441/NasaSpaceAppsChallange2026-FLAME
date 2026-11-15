
from pathlib import Path
import json
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "processed_data" / "saffire"

DATASETS = [
    "saffire_iii_sample_2",
    "saffire_sample_5",
    "saffire_sample_6"
]

TIME_COLUMNS = {
    "Elapsed Time (s)",
    "Epoch Time",
    "Timestamp (ms)",
    "Index"
}

summary = []

for dataset_id in DATASETS:
    print(f"\nValidating: {dataset_id}")

    csv_path = DATA_DIR / f"{dataset_id}.csv"
    meta_path = DATA_DIR / f"{dataset_id}_metadata.json"

    try:
        df = pd.read_csv(csv_path, low_memory=False)

        with open(meta_path, encoding="utf-8") as f:
            metadata = json.load(f)

        sensors = [
            col["column_name"]
            for col in metadata["columns"]
            if col["column_name"] not in TIME_COLUMNS
        ]

        expected_columns = [
            col["column_name"]
            for col in metadata["columns"]
        ]

        missing_columns = [
            name for name in expected_columns
            if name not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing columns: {missing_columns}"
            )

        elapsed = pd.to_numeric(
            df["Elapsed Time (s)"],
            errors="coerce"
        )
        epoch = pd.to_numeric(
            df["Epoch Time"],
            errors="coerce"
        )
        index = pd.to_numeric(
            df["Index"],
            errors="coerce"
        )

        time_diff = elapsed.diff().dropna()

        time_checks = {
            "missing_elapsed_time": int(
                elapsed.isna().sum()
            ),
            "non_increasing_elapsed_time": int(
                (time_diff <= 0).sum()
            ),
            "large_time_gaps_over_0_1s": int(
                (time_diff > 0.1).sum()
            ),
            "non_increasing_epoch": int(
                (epoch.diff().dropna() <= 0).sum()
            ),
            "index_sequence_breaks": int(
                (index.diff().dropna() != 1).sum()
            ),
            "median_sampling_interval": (
                float(time_diff.median())
                if not time_diff.empty else None
            )
        }

        channels = []

        for name in sensors:
            values = pd.to_numeric(
                df[name],
                errors="coerce"
            )

            valid = values.dropna()

            channels.append({
                "sensor": name,
                "count": len(values),
                "missing_or_non_numeric": int(
                    values.isna().sum()
                ),
                "negative_count": int(
                    (values < 0).sum()
                ),
                "zero_count": int(
                    (values == 0).sum()
                ),
                "unique_values": int(
                    values.nunique()
                ),
                "minimum": (
                    float(valid.min())
                    if not valid.empty else None
                ),
                "maximum": (
                    float(valid.max())
                    if not valid.empty else None
                ),
                "constant_channel": bool(
                    values.nunique(dropna=False) <= 1
                )
            })

        channel_df = pd.DataFrame(channels)

        report = {
            "dataset": dataset_id,
            "records": int(len(df)),
            "sensor_channels": len(sensors),
            "time_integrity": time_checks,
            "missing_or_non_numeric_sensor_values": int(
                channel_df["missing_or_non_numeric"].sum()
            ),
            "constant_channels": channel_df.loc[
                channel_df["constant_channel"],
                "sensor"
            ].tolist(),
            "channels_with_negative_values": channel_df.loc[
                channel_df["negative_count"] > 0,
                "sensor"
            ].tolist(),
            "scientific_validation_status": "pending"
        }

        with open(
            DATA_DIR / f"{dataset_id}_validation.json",
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(report, f, indent=2)

        channel_df.to_csv(
            DATA_DIR / f"{dataset_id}_channels.csv",
            index=False,
            encoding="utf-8-sig"
        )

        summary.append({
            "dataset": dataset_id,
            "status": "success",
            "records": len(df),
            "time_checks": time_checks,
            "missing_values": report[
                "missing_or_non_numeric_sensor_values"
            ],
            "constant_channels": len(
                report["constant_channels"]
            ),
            "negative_channels": len(
                report["channels_with_negative_values"]
            )
        })

        print("Validation report created successfully.")

    except Exception as error:
        print(f"ERROR: {error}")
        summary.append({
            "dataset": dataset_id,
            "status": "error",
            "message": str(error)
        })

summary_path = DATA_DIR / "batch_validation_summary.json"

with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("\nBATCH VALIDATION COMPLETED")
print(f"Summary saved: {summary_path}")
