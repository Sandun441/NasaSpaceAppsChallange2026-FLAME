"""
Catalog Extractor for NASA FLAME RAG Pipeline.
Ingests dataset_catalog.json to generate macro-investigation records
and catalog-level dataset profiles.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from ..schema import (
    ScientificKnowledgeRecord,
    DataProvenance,
    ExperimentalConditions,
    ChannelInfo,
    QualityAndValidation,
)
from .base import build_record_id, format_searchable_text, extract_keywords_from_text


INVESTIGATION_DEFINITIONS = [
    {
        "id": "bass_ii",
        "name": "BASS-II (Burning and Suppression of Solids - II)",
        "objective": (
            "Determine the extinction limits, burning rates, and narrow-channel flammability of solid "
            "materials in microgravity under low-speed forced airflow inside the ISS Microgravity Science Glovebox."
        ),
        "description": (
            "BASS-II investigated combustion over solid fuel geometries (flat sheets, cylinders, and films) "
            "aboard the International Space Station. Experiments evaluated fuel thickness, forced airflow, and "
            "extinction boundaries across diverse Principal Investigator sub-projects (Bhattacharjee, Ferkul, "
            "Miller, Olson, Fernandez-Pello, and T'ien)."
        ),
        "gravity": "microgravity_iss_msg",
        "materials": "PMMA films and spheres, Cotton fabric, Nomex flame-resistant polymer, Cast PMMA",
        "conditions": "ISS Microgravity Science Glovebox (MSG), forced flow restrictors (1, 2, 3), variable O2 concentration (17%–30%)",
        "channels": "calibrated initial/final O2 % by vol, Initial/Final CO2 % by vol, Initial/Final CO (ppm), Radiometer gain, frames shot",
        "source": "BASS-II Test Matrix by PI Final.xlsx",
        "validation_report": "processed_data/bass_ii_validation.csv",
    },
    {
        "id": "saffire_iii",
        "name": "Saffire-III (Spacecraft Fire Safety Demonstration III)",
        "objective": (
            "Evaluate large-scale upward and concurrent flame propagation, pyrolysis, and smoke evolution "
            "over realistic spacecraft materials in low-gravity aboard an uncrewed Cygnus resupply vehicle."
        ),
        "description": (
            "Saffire-III executed microgravity burn experiments inside a flow duct on an Orbital ATK Cygnus "
            "spacecraft after undocking from the ISS. Flown samples included large-scale fabrics (0.4m x 1.0m) "
            "and material strips instrumented with 12 thermocouples, 4 radiometers, anemometers, and optical diagnostic sensors."
        ),
        "gravity": "microgravity_cygnus",
        "materials": "SIBAL fabric (Cotton/fiberglass blend), Nomex flame-resistant polymer sheets",
        "conditions": "Cygnus flow duct, forced ventilation (~0.2 m/s / 20 cm/s), ambient vehicle cabin pressure, 30 Hz sampling rate",
        "channels": "Plume Temp 1-6 (°C), Sample Temp 1-6 (°C), Radiometer 1-4 (mw/cm²), Anemometers (cm/s), Fan Speed (RPM), Pressure (PSIA), O2/CO2 (%)",
        "source": "Saffire III Sample 1 & 2 Sensors.xlsx",
        "validation_report": "processed_data/saffire/saffire_iii_sample_1_validation.json",
    },
    {
        "id": "cygnus_telemetry",
        "name": "Cygnus Spacecraft Engineering Telemetry",
        "objective": (
            "Monitor vehicle-level environmental response, cabin depressurization dynamics, and smoke detector "
            "optical obscuration during microgravity combustion test operations."
        ),
        "description": (
            "Spacecraft engineering telemetry recorded by the Cygnus vehicle systems during Saffire experiments. "
            "Captures optical obscuration and scattering signals from the FIZ 2 smoke detector, pressurized cargo module (PCM) "
            "pressures, and vehicle air temperatures."
        ),
        "gravity": "microgravity_cygnus",
        "materials": "Vehicle cabin atmosphere, combustion aerosol effluents",
        "conditions": "Uncrewed Cygnus Pressurized Cargo Module (PCM), post-departure flight phase",
        "channels": "FIZ 2 Smoke Detector Obscuration (V), Scatterometer (V), PCM EPS Pressures 1-3 (psi), PCM Air Temp (degC)",
        "source": "Saffire-III Telemetry Data.xlsx",
        "validation_report": "processed_data/saffire/telemetry/telemetry_validation_summary.json",
    },
]


def extract_investigation_records(now_iso: str) -> List[ScientificKnowledgeRecord]:
    """Generate macro-level investigation records."""
    records = []
    for inv in INVESTIGATION_DEFINITIONS:
        rec_id = build_record_id("inv", inv["id"])

        searchable = format_searchable_text(
            title=f"NASA Investigation: {inv['name']}",
            investigation=inv["name"],
            record_type="investigation",
            objective=inv["objective"],
            description=inv["description"],
            conditions=f"{inv['conditions']} | Gravity: {inv['gravity']} | Materials: {inv['materials']}",
            measurements=inv["channels"],
            provenance=f"NASA PSI combustion archive | Primary source: {inv['source']}",
            limitations="Flight investigation data requires consideration of facility-specific flow geometries and sensor boundaries.",
        )

        keywords = extract_keywords_from_text(
            inv["name"], inv["objective"], inv["materials"], inv["channels"], inv["gravity"]
        )

        record = ScientificKnowledgeRecord(
            record_id=rec_id,
            record_type="investigation",
            experiment_id=inv["id"],
            dataset_id=None,
            investigation_name=inv["name"],
            title=f"NASA Investigation Profile: {inv['name']}",
            scientific_objective=inv["objective"],
            description=inv["description"],
            materials_and_conditions=ExperimentalConditions(
                fuel_material=inv["materials"],
                gravity_regime=inv["gravity"],
            ),
            channels_and_units=[],
            measured_statistics=None,
            provenance=DataProvenance(
                source_file=inv["source"],
                source_worksheet=None,
            ),
            quality=QualityAndValidation(
                validation_status="pending",
                quality_report_file=inv["validation_report"],
                quality_flags=[],
                known_issues=["Facility-specific boundary effects apply."],
            ),
            missing_fields=["detailed_flight_timeline_manifest"],
            searchable_text=searchable,
            keywords=keywords,
            created_at_utc=now_iso,
        )
        records.append(record)

    return records


def extract_dataset_records(catalog_data: Dict[str, Any], now_iso: str) -> List[ScientificKnowledgeRecord]:
    """Generate catalog-level dataset records from dataset_catalog.json."""
    records = []
    datasets = catalog_data.get("datasets", [])

    for ds in datasets:
        ds_id = ds["dataset_id"]
        category = ds.get("category", "combustion")
        granularity = ds.get("granularity", "sensor_time_series")
        record_count = ds.get("record_count", 0)
        source_file = ds.get("source_file", "NASA Archive")
        worksheet = ds.get("source_worksheet")
        data_file = ds.get("data_file")
        quality_report = ds.get("quality_report")
        notes = ds.get("notes", [])

        # Map to parent investigation
        if ds_id.startswith("bass"):
            inv_name = "BASS-II (Burning and Suppression of Solids - II)"
            obj = "Experiment-level test matrix measuring extinction limits, gas concentrations, and flammability parameters."
        elif ds_id.startswith("saffire"):
            inv_name = "Saffire-III (Spacecraft Fire Safety Demonstration III)"
            obj = f"High-frequency (30Hz) calibrated sensor time series capturing combustion flame spread for {ds_id}."
        else:
            inv_name = "Cygnus Spacecraft Engineering Telemetry"
            obj = f"Spacecraft environmental and fire detection telemetry recording {ds_id}."

        rec_id = build_record_id("ds", ds_id)
        title = f"NASA Flight Dataset: {ds_id} ({granularity})"
        desc = (
            f"Cataloged NASA scientific dataset containing {record_count:,} recorded rows. "
            f"Extracted from {source_file} (sheet: '{worksheet}'). "
            f"Maintains original sensor columns, physical units, and un-interpolated data gaps."
        )

        searchable = format_searchable_text(
            title=title,
            investigation=inv_name,
            record_type="dataset",
            objective=obj,
            description=desc,
            conditions=f"Category: {category} | Granularity: {granularity} | Row Count: {record_count:,}",
            measurements=f"Refer to dataset column manifest. {record_count:,} sequential readings recorded.",
            provenance=f"Source file: {source_file} | Worksheet: {worksheet} | Processed: {data_file}",
            validation_flags="; ".join(notes) if notes else "Pending validation screening",
            limitations="Dataset preserved in original extraction form without artificial normalization or interpolation.",
        )

        keywords = extract_keywords_from_text(
            ds_id, inv_name, category, granularity, source_file, *notes
        )

        missing_fields = []
        if ds.get("metadata_file") is None:
            missing_fields.append("metadata_file_unassigned")
        if ds.get("investigation_id") is None:
            missing_fields.append("investigation_id_unassigned")

        record = ScientificKnowledgeRecord(
            record_id=rec_id,
            record_type="dataset",
            experiment_id=ds_id,
            dataset_id=ds_id,
            investigation_name=inv_name,
            title=title,
            scientific_objective=obj,
            description=desc,
            materials_and_conditions=ExperimentalConditions(
                gravity_regime="microgravity_cygnus" if "cygnus" in ds_id or "saffire" in ds_id else "microgravity_iss_msg"
            ),
            channels_and_units=[],
            measured_statistics=None,
            provenance=DataProvenance(
                source_file=source_file,
                source_worksheet=worksheet,
                data_file=data_file,
            ),
            quality=QualityAndValidation(
                validation_status=ds.get("scientific_validation", "pending"),
                quality_report_file=quality_report,
                quality_flags=notes,
                known_issues=notes,
            ),
            missing_fields=missing_fields,
            searchable_text=searchable,
            keywords=keywords,
            created_at_utc=now_iso,
        )
        records.append(record)

    return records
