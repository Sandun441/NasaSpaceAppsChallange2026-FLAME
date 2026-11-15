
from pathlib import Path
import pandas as pd

# ==========================================
# 1. File paths
# ==========================================

BASE = Path(__file__).resolve().parents[1]

SOURCE = BASE / "processed_data" / "bass_ii_experiments.csv"
OUTPUT = BASE / "processed_data" / "bass_ii_validation.csv"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. Load extracted experiment data
# ==========================================

if not SOURCE.exists():
    raise FileNotFoundError(
        f"Source file not found: {SOURCE}"
    )

df = pd.read_csv(
    SOURCE,
    dtype=str,
    keep_default_na=False
)

print("Starting BASS-II scientific data validation...")
print(f"Total records loaded: {len(df)}")


# ==========================================
# 3. Define scientific measurement columns
# ==========================================

measurements = [
    "calibrated  initial O2 % by vol ",
    "calibrated final O2 % by vol",
    "Initial CO2 % by vol",
    "Final CO2 % by vol",
    "Initial CO (ppm)",
    "Final CO (ppm)"
]

oxygen_columns = {
    "calibrated  initial O2 % by vol ",
    "calibrated final O2 % by vol"
}

co2_columns = {
    "Initial CO2 % by vol",
    "Final CO2 % by vol"
}

co_columns = {
    "Initial CO (ppm)",
    "Final CO (ppm)"
}

# Ensure all required columns exist
required_columns = measurements + [
    "source_worksheet",
    "source_excel_row",
    "Test no."
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ==========================================
# 4. Validate measurements
# ==========================================

issues = []

missing_values = {"", "none", "nan", "n/a", "na", "null"}

for _, row in df.iterrows():

    for column in measurements:

        raw = str(row[column]).strip()
        issue = None

        # Check for missing measurements
        if raw.lower() in missing_values:
            issue = "missing_measurement"

        # Check for qualified measurements
        elif (
            raw.lower() in {"or", "over"}
            or raw.startswith((">", "<", "~", "≈"))
        ):
            issue = "qualified_or_non_numeric_value"

        else:
            number = pd.to_numeric(
                raw,
                errors="coerce"
            )

            # Check non-numeric values
            if pd.isna(number):
                issue = "non_numeric_value"

            # Validate oxygen measurements ONLY
            elif column in oxygen_columns:
                if number < 5 or number > 100:
                    issue = "oxygen_value_requires_review"

            # Validate CO2 independently
            elif column in co2_columns:
                if number < 0 or number > 100:
                    issue = "co2_value_outside_percent_range"

            # Validate CO independently
            elif column in co_columns:
                if number < 0:
                    issue = "negative_co_requires_review"

        # Save flagged issue
        if issue is not None:
            issues.append({
                "source_worksheet": row["source_worksheet"],
                "source_excel_row": row["source_excel_row"],
                "test_number": row["Test no."],
                "measurement": column,
                "original_value": raw,
                "issue_type": issue,
                "review_status": "pending"
            })


# ==========================================
# 5. Generate validation report
# ==========================================

columns = [
    "source_worksheet",
    "source_excel_row",
    "test_number",
    "measurement",
    "original_value",
    "issue_type",
    "review_status"
]

result = pd.DataFrame(
    issues,
    columns=columns
)

result.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================
# 6. Print validation summary
# ==========================================

print("\n======================================")
print("BASS-II VALIDATION COMPLETED")
print("======================================")

print(f"Records checked: {len(df)}")
print(f"Measurement fields checked: {len(measurements)}")
print(f"Total measurement issues flagged: {len(result)}")

if not result.empty:

    print("\nIssue summary:")
    print(result["issue_type"].value_counts().to_string())

    print("\nFlagged test records:")
    print(
        result[
            ["test_number", "measurement",
             "original_value", "issue_type"]
        ].to_string(index=False)
    )

else:
    print("\nNo validation issues found.")

print(f"\nValidation report saved to:\n{OUTPUT}")
