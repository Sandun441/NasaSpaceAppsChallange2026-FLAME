"""
Saffire Extractor for NASA FLAME RAG Pipeline.
Extracts flight sample experiment_run records and verified sensor channel_group profiles
for the high-frequency Saffire combustion sensor suites.
"""

from pathlib import Path
from typing import List, Dict, Any
import json
from ..schema import (
    ScientificKnowledgeRecord,
    DataProvenance,
    ExperimentalConditions,
    ChannelInfo,
    MeasuredStatistics,
    QualityAndValidation,
)
from .base import build_record_id, format_searchable_text, extract_keywords_from_text


SAFFIRE_SAMPLES = [
    {
        "id": "saffire_iii_sample_1",
        "name": "Saffire-III Sample 1 (Large-Scale SIBAL Fabric)",
        "material": "SIBAL fabric (75% Cotton / 25% Fiberglass blend)",
        "material_details": "0.4 m wide x 1.0 m long large-scale fabric sheet",
        "ignition_seconds": 66.0,
        "duration_seconds": 689.96,
        "sampling_hz": 30.3,
        "airflow": "Forced duct airflow ~20 cm/s (Fan Speed ~1800 RPM)",
        "objective": (
            "Investigate large-scale concurrent flame spread, pyrolysis front propagation, and radiative "
            "heat flux across practical spacecraft fabric in microgravity inside the uncrewed Cygnus resupply vehicle."
        ),
        "source_file": "Saffire III Sample 1 Sensors.xlsx",
        "meta_file": "processed_data/saffire/saffire_iii_sample_1_metadata.json",
        "quality_file": "processed_data/saffire/saffire_iii_sample_1_validation.json",
        "notes": "Large-scale flame growth observed across cotton-fiberglass blend; igniter current active for ~10 seconds.",
    },
    {
        "id": "saffire_iii_sample_2",
        "name": "Saffire-III Sample 2 (Nomex Aerospace Polymer)",
        "material": "Nomex flame-resistant meta-aramid fabric",
        "material_details": "Material test strip array (flame-resistant aerospace polymer)",
        "ignition_seconds": 60.03,
        "duration_seconds": 159.95,
        "sampling_hz": 30.3,
        "airflow": "Forced duct airflow ~20 cm/s (Fan Speed ~1800 RPM)",
        "objective": (
            "Evaluate flammability, char formation, and extinction of flame-resistant aerospace polymers (Nomex) "
            "under low-gravity forced airflow conditions."
        ),
        "source_file": "Saffire III Sample 2 Sensors.xlsx",
        "meta_file": "processed_data/saffire/saffire_iii_sample_2_metadata.json",
        "quality_file": "processed_data/saffire/saffire_iii_sample_2_validation.json",
        "notes": "Nomex sample exhibited localized smoldering and self-extinction under post-ignition airflow.",
    },
    {
        "id": "saffire_sample_5",
        "name": "Saffire Sensor Data Sample 5",
        "material": "Solid spacecraft fuel sample 5",
        "material_details": "Standard Saffire sensor test specimen",
        "ignition_seconds": 60.03,
        "duration_seconds": 375.0,
        "sampling_hz": 30.3,
        "airflow": "Forced duct airflow (calibrated anemometer series)",
        "objective": (
            "Record microgravity combustion dynamics and thermal plume signatures across independent sample burn."
        ),
        "source_file": "Saffire Sensor Data Sample 5.xlsx",
        "meta_file": "processed_data/saffire/saffire_sample_5_metadata.json",
        "quality_file": "processed_data/saffire/saffire_sample_5_validation.json",
        "notes": "Independent flight sample; negative and constant channels documented in validation summary.",
    },
    {
        "id": "saffire_sample_6",
        "name": "Saffire Sensor Data Sample 6",
        "material": "Solid spacecraft fuel sample 6",
        "material_details": "Standard Saffire sensor test specimen",
        "ignition_seconds": 59.99,
        "duration_seconds": 375.0,
        "sampling_hz": 30.3,
        "airflow": "Forced duct airflow (calibrated anemometer series)",
        "objective": (
            "Record microgravity combustion dynamics and thermal plume signatures across independent sample burn."
        ),
        "source_file": "Saffire Sensor Data Sample 6.xlsx",
        "meta_file": "processed_data/saffire/saffire_sample_6_metadata.json",
        "quality_file": "processed_data/saffire/saffire_sample_6_validation.json",
        "notes": "Independent flight sample; negative and constant channels documented in validation summary.",
    },
]


SAFFIRE_CHANNEL_GROUPS = [
    {
        "id": "saffire_plume_thermocouples",
        "name": "Saffire Plume Thermocouples (TC1–TC6)",
        "quantity": "temperature",
        "unit": "°C",
        "channels": [
            "Plume Temp 1 (TC1)", "Plume Temp 2 (TC2)", "Plume Temp 3 (TC3)",
            "Plume Temp 4 (TC4)", "Plume Temp 5 (TC5)", "Plume Temp 6 (TC6)"
        ],
        "description": (
            "Type-K thermocouples positioned in the combustion exhaust plume downstream of the sample. "
            "Measures gas plume temperature rise, convective heat transfer, and flame extinction dynamics."
        ),
        "sampling_hz": 30.3,
    },
    {
        "id": "saffire_sample_thermocouples",
        "name": "Saffire Sample Surface Thermocouples (TC7–TC12)",
        "quantity": "temperature",
        "unit": "°C",
        "channels": [
            "Sample Temp 1 (TC7)", "Sample Temp 2 (TC8)", "Sample Temp 3 (TC9)",
            "Sample Temp 4 (TC10)", "Sample Temp 5 (TC11)", "Sample Temp 6 (TC12)"
        ],
        "description": (
            "Thermocouples attached along the length of the solid fuel substrate. "
            "Measures solid phase preheating, pyrolysis temperature, and the propagation velocity of the flame front."
        ),
        "sampling_hz": 30.3,
    },
    {
        "id": "saffire_radiometers",
        "name": "Saffire Heat Flux Radiometers (Radiometer 1–4)",
        "quantity": "radiant_heat_flux",
        "unit": "mw/cm²",
        "channels": ["Radiometer 1", "Radiometer 2", "Radiometer 3", "Radiometer 4"],
        "description": (
            "Narrow and wide-angle thermopile radiometers positioned along the flow duct. "
            "Measures total radiative heat feedback from the microgravity flame to the surroundings and fuel surface."
        ),
        "sampling_hz": 30.3,
    },
    {
        "id": "saffire_flow_ventilation",
        "name": "Saffire Flow and Ventilation Instrumentation",
        "quantity": "flow_velocity",
        "unit": "cm/sec & RPM",
        "channels": ["Anemometer 1", "Anemometer 2", "Average Fan Speed"],
        "description": (
            "Hot-film anemometers measuring local forced air velocity across the fuel surface (cm/sec) "
            "and optical fan tachometer measuring duct ventilation impeller rotation (RPM)."
        ),
        "sampling_hz": 30.3,
    },
    {
        "id": "saffire_chamber_pressure_gas",
        "name": "Saffire Chamber Pressure and Atmospheric Sensors",
        "quantity": "pressure_and_concentration",
        "unit": "PSIA & %",
        "channels": ["Ambient Pressure", "O2", "CO2", "Humidity"],
        "description": (
            "Pressure transducers measuring Cygnus cabin pressure (PSIA) and electrochemical gas analyzers "
            "measuring oxygen depletion and carbon dioxide generation during the combustion process."
        ),
        "sampling_hz": 30.3,
    },
]


def extract_saffire_records(base_dir: Path, now_iso: str) -> List[ScientificKnowledgeRecord]:
    """Generate experiment_run and channel_group knowledge records for Saffire."""
    records = []

    # 1. Generate experiment_run records for each sample burn
    for s in SAFFIRE_SAMPLES:
        rec_id = build_record_id("run", s["id"])
        title = f"Flight Experiment Run: {s['name']}"
        desc = (
            f"Saffire microgravity flight combustion experiment burning {s['material']}. "
            f"Experimental duration: {s['duration_seconds']}s recorded at ~{s['sampling_hz']} Hz. "
            f"Ignition verified by physical telemetry at t = {s['ignition_seconds']}s. "
            f"Airflow condition: {s['airflow']}."
        )

        conditions_str = (
            f"Material: {s['material']} ({s['material_details']}) | Airflow: {s['airflow']} | "
            f"Ignition Time: {s['ignition_seconds']}s | Sampling: ~{s['sampling_hz']} Hz | Facility: Cygnus Flow Duct"
        )

        channels_str = (
            "61 calibrated sensors: 12 Thermocouples (Plume & Sample °C), 4 Radiometers (mw/cm²), "
            "2 Anemometers (cm/s), Fan Speed (RPM), Pressure (PSIA), O2 & CO2 (%), Igniter Telemetry (A, V)"
        )

        searchable = format_searchable_text(
            title=title,
            investigation="Saffire-III (Spacecraft Fire Safety Demonstration III)",
            record_type="experiment_run",
            objective=s["objective"],
            description=desc,
            conditions=conditions_str,
            measurements=channels_str,
            provenance=f"Source Excel: {s['source_file']} (Calibrated Data) | Processed: processed_data/saffire/{s['id']}.csv",
            validation_flags=s["notes"],
            limitations="Continuous 30Hz flight telemetry. Pre-ignition baselines ran for ~60-66s prior to igniter energization.",
        )

        keywords = extract_keywords_from_text(
            "Saffire", s["id"], s["material"], s["airflow"], "igniter", "radiometer", "thermocouple", "microgravity"
        )

        record = ScientificKnowledgeRecord(
            record_id=rec_id,
            record_type="experiment_run",
            experiment_id=s["id"],
            dataset_id=s["id"],
            investigation_name="Saffire-III (Spacecraft Fire Safety Demonstration III)",
            title=title,
            scientific_objective=s["objective"],
            description=desc,
            materials_and_conditions=ExperimentalConditions(
                fuel_material=s["material"],
                material_details=s["material_details"],
                gravity_regime="microgravity_cygnus",
                flow_velocity=s["airflow"],
            ),
            channels_and_units=[
                ChannelInfo(channel_name="Plume Temp 1-6", physical_quantity="temperature", unit="°C", sampling_rate_hz=s["sampling_hz"]),
                ChannelInfo(channel_name="Sample Temp 1-6", physical_quantity="temperature", unit="°C", sampling_rate_hz=s["sampling_hz"]),
                ChannelInfo(channel_name="Radiometer 1-4", physical_quantity="radiant_heat_flux", unit="mw/cm²", sampling_rate_hz=s["sampling_hz"]),
                ChannelInfo(channel_name="Anemometer 1-2", physical_quantity="flow_velocity", unit="cm/sec", sampling_rate_hz=s["sampling_hz"]),
                ChannelInfo(channel_name="Ambient Pressure", physical_quantity="pressure", unit="PSIA", sampling_rate_hz=s["sampling_hz"]),
            ],
            measured_statistics=MeasuredStatistics(
                time_of_max_seconds=s["ignition_seconds"],
                notes=f"Documented ignition at t = {s['ignition_seconds']}s",
            ),
            provenance=DataProvenance(
                source_file=s["source_file"],
                source_worksheet="Calibrated Data",
                data_file=f"processed_data/saffire/{s['id']}.csv",
            ),
            quality=QualityAndValidation(
                validation_status="pending",
                quality_report_file=s["quality_file"],
                quality_flags=[s["notes"]],
                known_issues=["Negative radiometer offsets and constant DIO channels documented in validation summary."],
            ),
            missing_fields=["pre_flight_fuel_moisture_content"],
            searchable_text=searchable,
            keywords=keywords,
            created_at_utc=now_iso,
        )
        records.append(record)

    # 2. Generate channel_group records for Saffire sensor suites
    for cg in SAFFIRE_CHANNEL_GROUPS:
        rec_id = build_record_id("cg", cg["id"])
        title = f"Measurement Channel Group: {cg['name']}"
        obj = f"Measure {cg['quantity']} to quantify microgravity combustion dynamics."
        desc = f"{cg['description']} Channels included: {', '.join(cg['channels'])}."

        searchable = format_searchable_text(
            title=title,
            investigation="Saffire-III (Spacecraft Fire Safety Demonstration III)",
            record_type="channel_group",
            objective=obj,
            description=desc,
            conditions=f"Quantity: {cg['quantity']} | Unit: {cg['unit']} | Nominal Rate: ~{cg['sampling_hz']} Hz",
            measurements=f"Active channels: {', '.join(cg['channels'])}",
            provenance="Saffire Flight Sensor Suite | Flown on Cygnus Resupply Spacecraft",
            limitations="Sensors are subject to thermal lag, radiation losses, and potential sooting during rich combustion phases.",
        )

        keywords = extract_keywords_from_text(cg["name"], cg["quantity"], cg["unit"], *cg["channels"])

        channel_objs = [
            ChannelInfo(channel_name=ch, physical_quantity=cg["quantity"], unit=cg["unit"], sampling_rate_hz=cg["sampling_hz"])
            for ch in cg["channels"]
        ]

        record = ScientificKnowledgeRecord(
            record_id=rec_id,
            record_type="channel_group",
            experiment_id=None,
            dataset_id="saffire_iii_sample_1",
            investigation_name="Saffire-III (Spacecraft Fire Safety Demonstration III)",
            title=title,
            scientific_objective=obj,
            description=desc,
            materials_and_conditions=ExperimentalConditions(gravity_regime="microgravity_cygnus"),
            channels_and_units=channel_objs,
            measured_statistics=None,
            provenance=DataProvenance(
                source_file="Saffire III Sample 1 & 2 Sensors.xlsx",
                source_worksheet="Calibrated Data",
            ),
            quality=QualityAndValidation(
                validation_status="pending",
                quality_flags=["Calibrated sensor suite with zero artificial interpolation applied."],
            ),
            missing_fields=["in_situ_calibration_drift_manifest"],
            searchable_text=searchable,
            keywords=keywords,
            created_at_utc=now_iso,
        )
        records.append(record)

    return records
