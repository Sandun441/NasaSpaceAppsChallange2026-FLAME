"""
Telemetry Extractor for NASA FLAME RAG Pipeline.
Extracts channel_group records for vehicle-level Cygnus engineering telemetry,
fire detection instrumentation, and cabin pressure dynamics.
"""

from pathlib import Path
from typing import List, Dict, Any
from ..schema import (
    ScientificKnowledgeRecord,
    DataProvenance,
    ExperimentalConditions,
    ChannelInfo,
    QualityAndValidation,
)
from .base import build_record_id, format_searchable_text, extract_keywords_from_text


CYGNUS_TELEMETRY_GROUPS = [
    {
        "id": "cygnus_smoke_detector_fiz2",
        "name": "Cygnus FIZ 2 Smoke Detector Suite",
        "dataset_id": "telemetry_cygnus_smoke_detector_data",
        "quantity": "smoke_obscuration_and_scattering",
        "unit": "V (Volts)",
        "channels": [
            "FIZ 2 Smoke Detector Obscuration (V)",
            "FIZ 2 Smoke Detector Scatterometer (V)"
        ],
        "objective": (
            "Monitor early smoke aerosol agglomeration, optical obscuration, and light scattering "
            "during microgravity combustion tests aboard the Cygnus Pressurized Cargo Module."
        ),
        "description": (
            "The Fire Interface Zone (FIZ) 2 smoke detector measures both beam extinction (obscuration voltage) "
            "and optical forward-angle scattering (scatterometer voltage). In microgravity, the absence of buoyant "
            "rising plumes leads to larger aerosol particulate agglomerates, altering detector response dynamics compared to Earth."
        ),
        "source_file": "Saffire-III Telemetry Data.xlsx",
        "worksheet": "CygnusSmokeDetectorData",
        "data_file": "processed_data/saffire/telemetry/analysis_ready/cygnus_smoke_detector_data_analysis.csv",
        "quality_file": "processed_data/saffire/telemetry/telemetry_validation_summary.json",
        "notes": "Timestamp screening applied to filter duplicates; negative and zero values preserved in original extraction.",
    },
    {
        "id": "cygnus_pcm_pressure_suite",
        "name": "Cygnus Pressurized Cargo Module (PCM) Pressure Sensors",
        "dataset_id": "telemetry_cygnus_pressure_data",
        "quantity": "chamber_pressure",
        "unit": "psi",
        "channels": [
            "PCM EPS 1 Press (psi)",
            "PCM EPS 2 Press (psi)",
            "PCM EPS 3 Press (psi)"
        ],
        "objective": (
            "Quantify spacecraft cabin pressure fluctuations and verify structural containment integrity "
            "during microgravity solid combustion burns."
        ),
        "description": (
            "Triple-redundant pressure transducers monitoring the uncrewed Cygnus Pressurized Cargo Module (PCM). "
            "Tracks atmospheric pressure response to heat addition, thermal expansion, and post-burn cooling."
        ),
        "source_file": "Saffire-III Telemetry Data.xlsx",
        "worksheet": "CygnusPressureData",
        "data_file": "processed_data/saffire/telemetry/analysis_ready/cygnus_pressure_data_analysis.csv",
        "quality_file": "processed_data/saffire/telemetry/telemetry_validation_summary.json",
        "notes": "Nominal cabin pressure maintained near standard vehicle operating limits (~14.7 - 15.2 psi).",
    },
    {
        "id": "cygnus_pcm_air_temperature",
        "name": "Cygnus Bulk Cabin Air Temperature",
        "dataset_id": "telemetry_cygnus_temperature_data",
        "quantity": "air_temperature",
        "unit": "degC",
        "channels": ["PCM Air Temp (degC)"],
        "objective": (
            "Measure bulk cabin ambient temperature rise resulting from convective effluent mixing "
            "outside the Saffire flow duct."
        ),
        "description": (
            "Bulk environmental air temperature recorded inside the Cygnus vehicle. Demonstrates the effectiveness "
            "of the Saffire duct exhaust filtration and cooling in isolating the wider spacecraft from combustion heat."
        ),
        "source_file": "Saffire-III Telemetry Data.xlsx",
        "worksheet": "CygnusTemperatureData",
        "data_file": "processed_data/saffire/telemetry/analysis_ready/cygnus_temperature_data_analysis.csv",
        "quality_file": "processed_data/saffire/telemetry/telemetry_validation_summary.json",
        "notes": "Vehicle air temperature exhibits gradual thermal rise with low-frequency telemetry sampling.",
    },
]


def extract_telemetry_records(base_dir: Path, now_iso: str) -> List[ScientificKnowledgeRecord]:
    """Generate channel_group records for vehicle-level Cygnus telemetry suites."""
    records = []

    for tg in CYGNUS_TELEMETRY_GROUPS:
        rec_id = build_record_id("cg", tg["id"])
        title = f"Vehicle Telemetry Instrumentation: {tg['name']}"

        searchable = format_searchable_text(
            title=title,
            investigation="Cygnus Spacecraft Engineering Telemetry",
            record_type="channel_group",
            objective=tg["objective"],
            description=tg["description"],
            conditions=f"Vehicle: Cygnus Pressurized Cargo Module (PCM) | Quantity: {tg['quantity']} | Unit: {tg['unit']}",
            measurements=f"Telemetry channels: {', '.join(tg['channels'])}",
            provenance=f"Source: {tg['source_file']} | Worksheet: {tg['worksheet']} | Data: {tg['data_file']}",
            validation_flags=tg["notes"],
            limitations="Spacecraft housekeeping telemetry has lower sampling rates than internal experiment sensors. Do not merge timestamps directly with Saffire sensors.",
        )

        keywords = extract_keywords_from_text(
            "Cygnus", tg["name"], tg["quantity"], tg["unit"], *tg["channels"]
        )

        channel_objs = [
            ChannelInfo(channel_name=ch, physical_quantity=tg["quantity"], unit=tg["unit"])
            for ch in tg["channels"]
        ]

        record = ScientificKnowledgeRecord(
            record_id=rec_id,
            record_type="channel_group",
            experiment_id=None,
            dataset_id=tg["dataset_id"],
            investigation_name="Cygnus Spacecraft Engineering Telemetry",
            title=title,
            scientific_objective=tg["objective"],
            description=tg["description"],
            materials_and_conditions=ExperimentalConditions(gravity_regime="microgravity_cygnus"),
            channels_and_units=channel_objs,
            measured_statistics=None,
            provenance=DataProvenance(
                source_file=tg["source_file"],
                source_worksheet=tg["worksheet"],
                data_file=tg["data_file"],
            ),
            quality=QualityAndValidation(
                validation_status="pending",
                quality_report_file=tg["quality_file"],
                quality_flags=[tg["notes"]],
                known_issues=["Engineering telemetry recorded independently from high-rate science instrumentation."],
            ),
            missing_fields=["sub_second_synchronization_manifest"],
            searchable_text=searchable,
            keywords=keywords,
            created_at_utc=now_iso,
        )
        records.append(record)

    return records
