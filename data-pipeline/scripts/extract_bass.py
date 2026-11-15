
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

SOURCE = (
    BASE / "raw_data" / "PSI-102"
    / "BASS-II Test Matrix by PI Final.xlsx"
)

OUTPUT = (
    BASE / "processed_data"
    / "bass_ii_experiments.csv"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# All six worksheets have the same column structure.
with pd.ExcelFile(SOURCE) as workbook:
    sheets = workbook.sheet_names
    records = []

    for sheet in sheets:
        df = pd.read_excel(
            workbook,
            sheet_name=sheet,
            header=0,
            dtype=object
        )

        # Remove completely blank rows only.
        df = df.dropna(how="all").copy()

        # Preserve source information.
        df.insert(0, "source_file", SOURCE.name)
        df.insert(1, "source_worksheet", sheet)
        df.insert(
            2,
            "source_excel_row",
            df.index + 2
        )

        records.append(df)

    combined = pd.concat(
        records,
        ignore_index=True
    )

combined.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("BASS-II extraction completed!")
print(f"Source worksheets: {len(sheets)}")
print(f"Extracted records: {len(combined)}")
print(f"Columns: {len(combined.columns)}")
print(f"Saved to: {OUTPUT}")

print("\nSample records:")
print(combined.head(3).to_string(index=False))
