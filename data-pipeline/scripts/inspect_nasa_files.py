
from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "raw_data"
OUTPUT_DIR = BASE_DIR / "extracted_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED = {".xls", ".xlsx"}
PREVIEW_ROWS = 8


def safe_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def inspect_file(path):
    result = {
        "file": str(path.relative_to(RAW_DIR)),
        "size_bytes": path.stat().st_size,
        "status": "success",
        "worksheets": []
    }

    try:
        with pd.ExcelFile(path) as excel:
            for sheet_name in excel.sheet_names:
                try:
                    # Preserve worksheet rows without assuming
                    # the first row contains column headings.
                    df = pd.read_excel(
                        excel,
                        sheet_name=sheet_name,
                        header=None
                    )

                    preview = [
                        [safe_value(value) for value in row]
                        for row in df.head(PREVIEW_ROWS).itertuples(
                            index=False, name=None
                        )
                    ]

                    result["worksheets"].append({
                        "name": sheet_name,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "non_empty_cells": int(
                            df.notna().sum().sum()
                        ),
                        "preview": preview,
                        "status": "success"
                    })
                except Exception as error:
                    result["worksheets"].append({
                        "name": sheet_name,
                        "status": "error",
                        "message": str(error)
                    })

    except Exception as error:
        result["status"] = "error"
        result["message"] = str(error)

    return result


def main():
    files = sorted(
        p for p in RAW_DIR.rglob("*")
        if p.is_file()
        and p.suffix.lower() in SUPPORTED
        and not p.name.startswith("~$")
    )

    print(f"Found {len(files)} Excel files.")

    results = []

    for path in files:
        print(f"Inspecting: {path.name}")
        results.append(inspect_file(path))

    output = OUTPUT_DIR / "inspection_report.json"

    with open(output, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nInspection complete: {output}")


if __name__ == "__main__":
    main()
