
from pathlib import Path
import json
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "processed_data" / "saffire"

SOURCE = DATA_DIR / "saffire_iii_sample_1.csv"
META_SOURCE = DATA_DIR / "saffire_iii_sample_1_metadata.json"

REPORT = DATA_DIR / "saffire_iii_sample_1_validation.json"
CHANNEL_REPORT = DATA_DIR / "saffire_iii_sample_1_channels.csv"

# 1. Load data and metadata
df = pd.read_csv(SOURCE, low_memory=False)

with open(META_SOURCE, encoding="utf-8") as f:
    metadata = json.load(f)

sensor_columns = [
    item["column_name"]
    for item in metadata["columns"]
    if item["column_name"] not in {
        "Elapsed Time (s)",
        "Epoch Time",
        "Timestamp (ms)",
        "Index"
    }
]

# 2. Check time-series integrity
time = pd.to_numeric(
    df["Elapsed Time (s)"],
    errors="coerce"
)

time_diff = time.diff().dropna()

epoch = pd.to_numeric(
    df["Epoch Time"],
    errors="coerce"
)

index = pd.to_numeric(
    df["Index"],
    errors="coerce"
)

time_checks = {
    "missing_elapsed_time": int(time.isna().sum()),
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
    "first_elapsed_seconds": float(time.iloc[0]),
    "last_elapsed_seconds": float(time.iloc[-1]),
    "median_sampling_interval": float(
        time_diff.median()
    )
}

# 3. Inspect each measurement channel
channels = []

for name in sensor_columns:
    values = pd.to_numeric(
        df[name],
        errors="coerce"
    )

    valid = values.dropna()

    source_info = next(
        item for item in metadata["columns"]
        if item["column_name"] == name
    )

    channels.append({
        "sensor": name,
        "unit": source_info["original_unit"] or "",
        "count": int(len(values)),
        "missing_or_non_numeric": int(values.isna().sum()),
        "negative_count": int((values < 0).sum()),
        "zero_count": int((values == 0).sum()),
        "unique_values": int(values.nunique()),
        "minimum": float(valid.min()) if len(valid) else None,
        "maximum": float(valid.max()) if len(valid) else None,
        "mean": float(valid.mean()) if len(valid) else None,
        "constant_channel": bool(
            values.nunique(dropna=False) <= 1
        ),
        "review_status": "pending"
    })

channel_df = pd.DataFrame(channels)

# 4. Produce summary
report = {
    "dataset": metadata["dataset"],
    "records": int(len(df)),
    "original_sensor_columns": len(sensor_columns),
    "time_integrity": time_checks,
    "total_missing_or_non_numeric_sensor_values": int(
        channel_df["missing_or_non_numeric"].sum()
    ),
    "constant_channels": channel_df.loc[
        channel_df["constant_channel"], "sensor"
    ].tolist(),
    "channels_with_negative_values": channel_df.loc[
        channel_df["negative_count"] > 0, "sensor"
    ].tolist(),
    "scientific_validation_status": "pending",
    "notes": [
        "Negative readings are observations, not automatic errors.",
        "Constant channels may represent fixed instrument states.",
        "Sensor ranges require instrument-specific review.",
        "No measurements were changed or removed."
    ]
}

# 5. Save validation results
channel_df.to_csv(
    CHANNEL_REPORT,
    index=False,
    encoding="utf-8-sig"
)

with open(REPORT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

# 6. Display summary
print("\nSAFFIRE VALIDATION COMPLETED")
print("=" * 40)
print(f"Records: {len(df)}")
print(f"Sensor channels: {len(sensor_columns)}")

print("\nTime integrity:")
for key, value in time_checks.items():
    print(f"  {key}: {value}")

print(
    "\nConstant channels:",
    len(report["constant_channels"])
)

print(
    "Channels with negative readings:",
    len(report["channels_with_negative_values"])
)

print(f"\nSaved: {REPORT.name}")
print(f"Saved: {CHANNEL_REPORT.name}")
print("\nScientific review remains pending.")
