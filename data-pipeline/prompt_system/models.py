"""
NASA FLAME — Shared Prompt Interpretation & Structured Response Models
Phase F2: Unified Pydantic models for specialist research requests and typed responses.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class PromptResearchRequest(BaseModel):
    """
    Standard request payload submitted from any research workspace or global input.
    """
    objective: str = Field(
        ...,
        min_length=1,
        max_length=1500,
        description="Natural-language scientific research objective or query"
    )
    workspace: Literal[
        "auto",
        "visualization",
        "comparison",
        "modeling",
        "gap_detection",
        "equipment",
        "earth_applications"
    ] = Field(
        default="auto",
        description="Target specialist workspace, or 'auto' for intelligent routing"
    )
    context_filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional current workspace filter context (e.g. dataset_id, channels, active category)"
    )
    conversation_context: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional conversation history for multi-turn thread grounding"
    )


class InterpretedScientificIntent(BaseModel):
    """
    Structured extraction of scientific entities and parameters from natural language.
    All extracted entities are resolved against actual NASA dataset catalogs.
    """
    target_workspace: str = Field(..., description="Target specialist workspace")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of intent mapping")
    intent_summary: str = Field(..., description="Concise human-readable summary of interpreted intent")
    investigation_id: Optional[str] = Field(default=None, description="NASA Investigation ID (e.g. saffire_iii, bass_ii)")
    dataset_id: Optional[str] = Field(default=None, description="Primary resolved dataset ID")
    secondary_dataset_id: Optional[str] = Field(default=None, description="Secondary dataset ID for comparison")
    target_variables: List[str] = Field(default_factory=list, description="Resolved scientific variable names")
    channel_ids: List[str] = Field(default_factory=list, description="Resolved physical sensor channel column names")
    time_window: Optional[List[float]] = Field(default=None, description="Resolved time window in seconds [start, end]")
    units_by_channel: Dict[str, str] = Field(default_factory=dict, description="Physical measurement units for each channel")
    fuel_materials: List[str] = Field(default_factory=list, description="Identified fuel material types")
    environmental_conditions: Dict[str, Any] = Field(default_factory=dict, description="O2, pressure, or flow constraints")
    needs_clarification: bool = Field(default=False, description="True if inquiry is ambiguous or missing required parameters")
    clarification_prompt: Optional[str] = Field(default=None, description="Clarification message if ambiguous")
    candidate_options: Optional[List[str]] = Field(default=None, description="Safe candidate options for user selection")


class ChartSpecification(BaseModel):
    """
    Reusable scientific visualization specification referencing real empirical data.
    Never contains hallucinated or synthetic point arrays.
    """
    chart_id: str = Field(..., description="Unique chart identifier")
    chart_type: Literal["line", "scatter", "bar", "heatmap", "multi_line"] = Field(
        ..., description="Supported scientific chart rendering type"
    )
    title: str = Field(..., description="Chart title with physical parameter description")
    subtitle: Optional[str] = Field(default=None, description="Experimental conditions and flight context")
    dataset_id: str = Field(..., description="Source dataset ID in NASA FLAME repository")
    channel_ids: List[str] = Field(..., description="Sensor column names included in this chart")
    channel_labels: Dict[str, str] = Field(..., description="Human-readable channel labels")
    x_variable: str = Field(default="time", description="X-axis variable name")
    x_label: str = Field(default="Elapsed Time", description="X-axis display label")
    x_units: str = Field(default="s", description="X-axis physical units")
    y_variable: str = Field(..., description="Y-axis primary variable name")
    y_label: str = Field(..., description="Y-axis display label")
    y_units: str = Field(..., description="Y-axis physical units (e.g. mW/cm², °C, % vol, cm/s)")
    time_range: Optional[List[float]] = Field(default=None, description="Active time window in seconds [min, max]")
    series_data: Dict[str, List[Any]] = Field(
        default_factory=dict,
        description="Real time-series data points from verified decimation or dataset records"
    )
    event_markers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Physical event annotations (e.g. igniter active pulse, extinction boundary)"
    )
    data_resolution: str = Field(
        default="full_resolution",
        description="Resolution status (e.g. decimated_lttb_400_pts, raw_daq_30.3hz, experiment_matrix)"
    )
    missing_data_notices: List[str] = Field(
        default_factory=list,
        description="Notices regarding sensor dropouts, saturated ranges, or uninstrumented windows"
    )
    provenance: str = Field(..., description="Direct NASA flight experiment provenance reference")


class CitationItem(BaseModel):
    """
    Traceable scientific citation referencing local flight telemetry or external literature.
    """
    id: str = Field(..., description="Citation ID (e.g. flame_rec_..., EA-EV-..., PSI-25)")
    type: str = Field(..., description="Source type (flight_telemetry, experiment_matrix, external_report)")
    title: str = Field(..., description="Citation title")
    investigation: Optional[str] = Field(default=None, description="NASA investigation name")
    reference: Optional[str] = Field(default=None, description="Source archive or file reference")
    grounding_level: str = Field(
        default="locally_verified",
        description="Epistemic tier: locally_verified, external_literature_verified, exploratory"
    )


class SuggestedActionItem(BaseModel):
    """
    Contextual interactive navigation action linking specialist workspaces.
    """
    id: str = Field(..., description="Action ID")
    label: str = Field(..., description="Button label for UI")
    tab_id: str = Field(..., description="Target dashboard tab ID")
    action: str = Field(..., description="Action identifier")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Contextual payload for target workspace")
    description: Optional[str] = Field(default=None, description="Brief explanation of what the tool will explore")
    icon: Optional[str] = Field(default=None, description="Suggested UI icon name")


class PromptResearchResponse(BaseModel):
    """
    Unified, strongly typed research response returned across all workspaces.
    """
    status: Literal["ok", "ambiguous", "insufficient_evidence", "unsupported_objective", "error"] = Field(
        ..., description="Execution outcome status"
    )
    workspace: str = Field(..., description="Target workspace handling this response")
    objective: str = Field(..., description="Original user research objective")
    interpreted_intent: InterpretedScientificIntent = Field(
        ..., description="Structured interpretation of scientific entities and parameters"
    )
    grounded_answer: Optional[str] = Field(
        default=None,
        description="Concise 2-4 sentence scientific answer synthesized from verified experimental evidence"
    )
    specialist_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workspace-specific structured payload (modeling export, gap matrix, equipment insights, etc.)"
    )
    visualizations: List[ChartSpecification] = Field(
        default_factory=list,
        description="Verified chart specifications referencing real empirical measurements"
    )
    key_findings: List[str] = Field(
        default_factory=list,
        description="Key scientific takeaways grounded in verified experimental observations"
    )
    scientific_caveats: List[str] = Field(
        default_factory=list,
        description="Epistemic transfer caveats, 1g buoyancy decoupling notes, scale limits"
    )
    provenance_citations: List[CitationItem] = Field(
        default_factory=list,
        description="Traceable citations for datasets, telemetry channels, or publications"
    )
    suggested_actions: List[SuggestedActionItem] = Field(
        default_factory=list,
        description="Recommended contextual dashboard actions"
    )
    execution_mode: Literal["llm_assisted", "deterministic_fallback"] = Field(
        ..., description="Indicates whether intent was parsed via LLM or deterministic fallback"
    )
    evidence_sufficiency: Literal["sufficient", "partial", "insufficient"] = Field(
        default="sufficient",
        description="Sufficiency of verified empirical data in FLAME catalog to address the inquiry"
    )
