"""
NASA FLAME — Scientific Knowledge Record Schema
Formal data contract for Phase R1 RAG ingestion.
Standardizes heterogeneous microgravity combustion experiments, continuous sensor series,
and vehicle telemetry into normalized, traceable, and search-optimized records.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


RecordType = Literal["investigation", "dataset", "experiment_run", "channel_group", "document_section", "custom_dataset"]


class DataProvenance(BaseModel):
    """Traceable physical and digital origin of scientific data."""
    source_file: str = Field(description="Name of the source Excel workbook or document")
    source_worksheet: Optional[str] = Field(default=None, description="Source worksheet or table name")
    source_excel_row: Optional[int] = Field(default=None, description="Row index in original workbook where applicable")
    source_sha256: Optional[str] = Field(default=None, description="SHA256 hash of original file if verified")
    data_file: Optional[str] = Field(default=None, description="Relative path to processed CSV dataset file")


class ExperimentalConditions(BaseModel):
    """Documented physical parameters and fuel characteristics under test."""
    fuel_material: Optional[str] = Field(default=None, description="Fuel material substrate (e.g. Cotton, PMMA, Nomex, SIBAL)")
    material_details: Optional[str] = Field(default=None, description="Specific fuel thickness, dimensions, or weave")
    gravity_regime: str = Field(default="microgravity", description="Gravity level: microgravity_iss_msg, microgravity_cygnus, or normal_gravity")
    oxygen_concentration: Optional[str] = Field(default=None, description="Ambient or initial oxygen percentage (O2 % vol)")
    flow_velocity: Optional[str] = Field(default=None, description="Forced convection or ventilation rate (cm/s or RPM)")
    pressure: Optional[str] = Field(default=None, description="Ambient chamber or vehicle pressure")
    flow_restrictor: Optional[str] = Field(default=None, description="Flow restrictor orifice index if applicable")


class ChannelInfo(BaseModel):
    """Measurement channel specification."""
    channel_name: str = Field(description="Column or sensor name as recorded in source")
    physical_quantity: str = Field(description="Classified physical phenomenon (e.g. temperature, heat_flux, pressure)")
    unit: Optional[str] = Field(default=None, description="Verified scientific physical unit")
    sampling_rate_hz: Optional[float] = Field(default=None, description="Nominal sampling frequency in Hertz")


class MeasuredStatistics(BaseModel):
    """Real descriptive statistics computed from actual measurements (never fabricated)."""
    min_value: Optional[float] = Field(default=None, description="Minimum recorded value")
    max_value: Optional[float] = Field(default=None, description="Maximum recorded value")
    mean_value: Optional[float] = Field(default=None, description="Arithmetic mean of valid readings")
    time_of_max_seconds: Optional[float] = Field(default=None, description="Elapsed seconds when maximum occurred")
    valid_sample_count: Optional[int] = Field(default=None, description="Count of valid numeric values")
    missing_sample_count: Optional[int] = Field(default=None, description="Count of null, blank, or NaN data gaps")
    delta_value: Optional[float] = Field(default=None, description="Net observed delta (e.g. Initial O2 - Final O2)")
    notes: Optional[str] = Field(default=None, description="Descriptive notes on the computation scope")


class QualityAndValidation(BaseModel):
    """Validation report references, screening notes, and flagged readings."""
    validation_status: str = Field(default="pending", description="Validation status: pending, extracted_not_validated, verified")
    quality_report_file: Optional[str] = Field(default=None, description="Relative path to quality or validation report")
    quality_flags: List[str] = Field(default_factory=list, description="Specific data issues flagged for investigator review")
    known_issues: List[str] = Field(default_factory=list, description="Known experimental or telemetry caveats")


class ScientificKnowledgeRecord(BaseModel):
    """
    Standardized Scientific Knowledge Record for NASA FLAME RAG Architecture.
    Serves as the fundamental unit of retrieval and grounding.
    """
    record_id: str = Field(description="Unique deterministic primary key (e.g. flame_run_bass_ii_b2)")
    record_type: RecordType = Field(description="Granularity of the record")
    experiment_id: Optional[str] = Field(default=None, description="Identifies specific experiment, test, or sample")
    dataset_id: Optional[str] = Field(default=None, description="Parent dataset identifier in dataset_catalog.json")
    investigation_name: str = Field(description="Formal NASA investigation name (e.g. BASS-II, Saffire-III, Cygnus Telemetry)")
    title: str = Field(description="Human-readable title describing this scientific record")
    scientific_objective: str = Field(description="Scientific goals and combustion research objectives")
    description: str = Field(description="Detailed narrative explaining experimental scope, setup, and results")
    materials_and_conditions: ExperimentalConditions = Field(default_factory=ExperimentalConditions)
    channels_and_units: List[ChannelInfo] = Field(default_factory=list)
    measured_statistics: Optional[MeasuredStatistics] = Field(default=None)
    provenance: DataProvenance
    quality: QualityAndValidation = Field(default_factory=QualityAndValidation)
    missing_fields: List[str] = Field(default_factory=list, description="Explicitly documented missing or unrecorded metadata attributes")
    searchable_text: str = Field(description="Pre-compiled, dense scientific text optimized for BM25 and vector embedding")
    keywords: List[str] = Field(default_factory=list, description="Searchable domain keywords and physical parameters")
    created_at_utc: str = Field(description="ISO 8601 generation timestamp")
