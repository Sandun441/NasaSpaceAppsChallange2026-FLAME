"""
NASA FLAME — Earth Applications Evidence Models (Phase EA1)
Pydantic data models enforcing strict schema, provenance, and classification rules.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


EvidenceClassificationType = Literal[
    "documented_application",
    "supported_research_implication",
    "exploratory_hypothesis",
]

ValidationStatusType = Literal[
    "locally_verified",
    "external_literature_verified",
    "pending_verification",
    "unverified_hypothesis",
]


class EarthApplicationEvidence(BaseModel):
    """
    Structured model for evidence linking NASA microgravity combustion research to terrestrial applications.
    Strictly separates verified source observations from generated research interpretations.
    """
    id: str = Field(..., description="Unique immutable evidence identifier (e.g., EA-EV-BASS-MAT-01)")
    category_id: str = Field(..., description="Application category identifier from the taxonomy")
    category_title: str = Field(..., description="Human-readable application category title")
    title: str = Field(..., description="Specific terrestrial application or scientific research title")
    description: str = Field(..., description="Concise summary of the proposed terrestrial connection")
    investigation_id: str = Field(..., description="NASA combustion investigation identifier (e.g., bass_ii, saffire_iii, acme)")
    investigation_name: str = Field(..., description="Human-readable NASA flight investigation name")
    related_investigation_ids: List[str] = Field(
        default_factory=list,
        description="Secondary or related NASA flight investigation identifiers (e.g., co-investigations or cross-referenced missions)",
    )
    
    # Source provenance & verification
    source_type: str = Field(
        ...,
        description="Type of source: flight_telemetry_dataset, peer_reviewed_literature, technical_memorandum, mission_archive",
    )
    source_reference: str = Field(..., description="Verifiable URL, DOI, or internal document identifier")
    supporting_excerpt: str = Field(..., description="Verifiable excerpt or explicit pointer from the source documentation")
    dataset_or_measurement_reference: Optional[str] = Field(
        None,
        description="Specific local dataset filename, sensor channel, or run identifier when locally indexed in FLAME",
    )
    
    # Scientific synthesis & transfer logic
    scientific_finding: str = Field(..., description="Verified empirical or published microgravity combustion finding")
    proposed_terrestrial_relevance: str = Field(..., description="How this finding informs terrestrial fire safety or combustion science")
    
    # Classification & Validation Rubrics (No fabricated probabilities!)
    evidence_classification: EvidenceClassificationType = Field(
        ...,
        description="Classification: documented_application | supported_research_implication | exploratory_hypothesis",
    )
    validation_status: ValidationStatusType = Field(
        ...,
        description="Validation status: locally_verified | external_literature_verified | pending_verification | unverified_hypothesis",
    )
    confidence_rubric: str = Field(
        ...,
        description="Explicit rubric explaining the validation criteria applied; no fabricated percentage probabilities",
    )
    
    # Epistemic boundaries & physical transfer constraints
    earth_transfer_limitations: str = Field(
        ...,
        description="Critical limitations in applying microgravity observations directly to terrestrial Earth conditions",
    )
    gravity_buoyancy_ventilation_differences: str = Field(
        ...,
        description="Detailed physics differences: 1g buoyant upward convection vs. microgravity diffusion/forced ventilation",
    )
    uncertainty_notes: str = Field(..., description="Specific scientific uncertainties or unmeasured parameters")
    provenance_status: str = Field(
        ...,
        description="Detailed data provenance origin: locally_verified (FLAME CSVs) or external_literature_verified",
    )
    last_verified_utc: Optional[str] = Field(
        None,
        description="ISO 8601 UTC timestamp of last verification against source records",
    )


class EarthApplicationCategoryModel(BaseModel):
    """Schema for category overview."""
    id: str
    title: str
    icon: str
    short_desc: str
    scientific_scope: str
    primary_investigations: List[str]
    transfer_considerations: str
    evidence_count: int = 0


class EarthApplicationListResponse(BaseModel):
    """Response envelope for catalog list query."""
    status: str = "ok"
    total_count: int
    filtered_count: int
    limit: int
    offset: int
    evidence: List[EarthApplicationEvidence]


class EarthApplicationDetailResponse(BaseModel):
    """Response envelope for single evidence record."""
    status: str = "ok"
    evidence: EarthApplicationEvidence
