"""
BASS-II Extractor for NASA FLAME RAG Pipeline.
Transforms all 129 discrete ISS Glovebox test matrix runs into normalized
experiment_run scientific knowledge records with real parameter deltas and quality flags.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import csv
from ..schema import (
    ScientificKnowledgeRecord,
    DataProvenance,
    ExperimentalConditions,
    ChannelInfo,
    MeasuredStatistics,
    QualityAndValidation,
)
from .base import build_record_id, format_searchable_text, extract_keywords_from_text, sanitize_str


def parse_float(val: Any) -> Optional[float]:
    """Safely parse float value; return None if non-numeric or missing."""
    if val is None:
        return None
    try:
        f = float(str(val).strip())
        return f if not (f != f) else None  # NaN check
    except (ValueError, TypeError):
        return None


def extract_bass_records(base_dir: Path, now_iso: str) -> List[ScientificKnowledgeRecord]:
    """Extract individual experiment_run records for each of the 129 BASS-II test runs."""
    csv_path = base_dir / "processed_data" / "bass_ii_experiments.csv"
    val_path = base_dir / "processed_data" / "bass_ii_validation.csv"

    if not csv_path.exists():
        return []

    # 1. Load validation issues map
    validation_map = {}
    if val_path.exists():
        with open(val_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                sheet = r.get("source_worksheet", "")
                test_no = r.get("test_number", "")
                row_idx = r.get("source_excel_row", "")
                key = f"{sheet}_{test_no}_{row_idx}"
                if key not in validation_map:
                    validation_map[key] = []
                validation_map[key].append(
                    f"{r.get('measurement', 'measurement')}: {r.get('original_value', '')} ({r.get('issue_type', 'flagged')})"
                )

    records = []

    # 2. Ingest 129 test runs
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            test_no = sanitize_str(row.get("Test no.")) or f"Test_{idx + 1}"
            worksheet = sanitize_str(row.get("source_worksheet")) or "Unknown"
            excel_row = row.get("source_excel_row")
            excel_row_int = int(excel_row) if excel_row and str(excel_row).isdigit() else idx + 2
            material = sanitize_str(row.get("Material")) or "Unspecified Material"
            sample_no = sanitize_str(row.get("Sample no."))
            flow_restrictor = sanitize_str(row.get("Flow restrictor"))
            fan_display = sanitize_str(row.get("Fan display"))
            air_display = sanitize_str(row.get("Air display"))
            radiometer_gain = sanitize_str(row.get("Radiometer gain   (1000, 250, 50, 10)"))

            raw_init_o2 = row.get("calibrated  initial O2 % by vol ")
            raw_final_o2 = row.get("calibrated final O2 % by vol")
            raw_init_co2 = row.get("Initial CO2 % by vol")
            raw_final_co2 = row.get("Final CO2 % by vol")
            raw_init_co = row.get("Initial CO (ppm)")
            raw_final_co = row.get("Final CO (ppm)")
            raw_frames = row.get("total frames shot")

            init_o2 = parse_float(raw_init_o2)
            final_o2 = parse_float(raw_final_o2)
            init_co2 = parse_float(raw_init_co2)
            final_co2 = parse_float(raw_final_co2)
            init_co = parse_float(raw_init_co)
            final_co = parse_float(raw_final_co)
            frames = parse_float(raw_frames)

            # Compute real empirical deltas
            delta_o2 = (init_o2 - final_o2) if (init_o2 is not None and final_o2 is not None) else None
            delta_co2 = (final_co2 - init_co2) if (init_co2 is not None and final_co2 is not None) else None
            delta_co = (final_co - init_co) if (init_co is not None and final_co is not None) else None

            # Look up validation issues
            val_key = f"{worksheet}_{test_no}_{excel_row}"
            quality_flags = validation_map.get(val_key, [])

            # Document missing fields
            missing_fields = []
            if init_o2 is None: missing_fields.append("initial_o2_missing_or_non_numeric")
            if final_o2 is None: missing_fields.append("final_o2_missing_or_non_numeric")
            if init_co2 is None: missing_fields.append("initial_co2_missing_or_non_numeric")
            if final_co2 is None: missing_fields.append("final_co2_missing_or_non_numeric")
            if init_co is None: missing_fields.append("initial_co_missing_or_non_numeric")
            if final_co is None: missing_fields.append("final_co_missing_or_non_numeric")

            rec_id = build_record_id("run", f"bass_ii_{worksheet}_{test_no}")
            title = f"BASS-II Test Run {test_no} ({material}) • PI: {worksheet}"
            obj = (
                f"Evaluate solid fuel flammability, extinction threshold, and gas consumption in microgravity "
                f"under flow restrictor {flow_restrictor or 'N/A'} aboard the ISS Microgravity Science Glovebox."
            )

            desc = (
                f"Discrete microgravity combustion test {test_no} conducted under Principal Investigator {worksheet}. "
                f"Fuel: {material} (sample #{sample_no or 'N/A'}). "
                f"Initial O2 was {init_o2 if init_o2 is not None else 'unrecorded'}% by vol; "
                f"final O2 was {final_o2 if final_o2 is not None else 'unrecorded'}% by vol "
                f"(net O2 consumption: {f'{delta_o2:.2f}%' if delta_o2 is not None else 'indeterminate'}). "
                f"Total high-speed video frames acquired: {int(frames) if frames is not None else 'N/A'}."
            )

            conditions_str = (
                f"Material: {material} | Sample No: {sample_no or 'N/A'} | Flow Restrictor: {flow_restrictor or 'N/A'} | "
                f"Fan Setting: {fan_display or 'N/A'} | Air Display: {air_display or 'N/A'} | Facility: ISS MSG Glovebox"
            )

            measurements_str = (
                f"Initial O2: {init_o2}% | Final O2: {final_o2}% | Delta O2: {f'{delta_o2:.2f}%' if delta_o2 is not None else 'N/A'} | "
                f"Initial CO2: {init_co2}% | Final CO2: {final_co2}% | "
                f"Initial CO: {init_co} ppm | Final CO: {final_co} ppm | Frames: {frames}"
            )

            searchable = format_searchable_text(
                title=title,
                investigation="BASS-II (Burning and Suppression of Solids - II)",
                record_type="experiment_run",
                objective=obj,
                description=desc,
                conditions=conditions_str,
                measurements=measurements_str,
                provenance=f"Workbook: BASS-II Test Matrix by PI Final.xlsx | Sheet: {worksheet} | Row: {excel_row_int}",
                validation_flags="; ".join(quality_flags) if quality_flags else None,
                limitations="Discrete test matrix record. Values represent integral pre- and post-test glovebox gas concentrations.",
            )

            keywords = extract_keywords_from_text(
                "BASS-II", test_no, worksheet, material, f"flow restrictor {flow_restrictor}",
                "oxygen consumption", "glovebox", "microgravity"
            )

            measured_stats = MeasuredStatistics(
                min_value=final_o2,
                max_value=init_o2,
                mean_value=((init_o2 + final_o2) / 2.0) if (init_o2 is not None and final_o2 is not None) else None,
                delta_value=delta_o2,
                notes=f"Net O2 consumed: {delta_o2:.2f}%" if delta_o2 is not None else "Oxygen delta uncalculated",
            )

            record = ScientificKnowledgeRecord(
                record_id=rec_id,
                record_type="experiment_run",
                experiment_id=f"bass_ii_{test_no.lower()}",
                dataset_id="bass_ii_experiments",
                investigation_name="BASS-II (Burning and Suppression of Solids - II)",
                title=title,
                scientific_objective=obj,
                description=desc,
                materials_and_conditions=ExperimentalConditions(
                    fuel_material=material,
                    material_details=f"Sample #{sample_no}" if sample_no else None,
                    gravity_regime="microgravity_iss_msg",
                    oxygen_concentration=f"{init_o2}%" if init_o2 is not None else None,
                    flow_restrictor=flow_restrictor,
                    flow_velocity=f"Fan display {fan_display}" if fan_display else None,
                ),
                channels_and_units=[
                    ChannelInfo(channel_name="calibrated initial O2 % by vol ", physical_quantity="gas_concentration", unit="% vol"),
                    ChannelInfo(channel_name="calibrated final O2 % by vol", physical_quantity="gas_concentration", unit="% vol"),
                    ChannelInfo(channel_name="Initial CO2 % by vol", physical_quantity="gas_concentration", unit="% vol"),
                    ChannelInfo(channel_name="Final CO2 % by vol", physical_quantity="gas_concentration", unit="% vol"),
                    ChannelInfo(channel_name="Initial CO (ppm)", physical_quantity="gas_concentration", unit="ppm"),
                    ChannelInfo(channel_name="Final CO (ppm)", physical_quantity="gas_concentration", unit="ppm"),
                    ChannelInfo(channel_name="total frames shot", physical_quantity="video_frames", unit="frames"),
                ],
                measured_statistics=measured_stats,
                provenance=DataProvenance(
                    source_file="BASS-II Test Matrix by PI Final.xlsx",
                    source_worksheet=worksheet,
                    source_excel_row=excel_row_int,
                    data_file="processed_data/bass_ii_experiments.csv",
                ),
                quality=QualityAndValidation(
                    validation_status="pending",
                    quality_report_file="processed_data/bass_ii_validation.csv",
                    quality_flags=quality_flags,
                    known_issues=["Residual atmosphere between successive burns in Glovebox."],
                ),
                missing_fields=missing_fields,
                searchable_text=searchable,
                keywords=keywords,
                created_at_utc=now_iso,
            )
            records.append(record)

    return records
