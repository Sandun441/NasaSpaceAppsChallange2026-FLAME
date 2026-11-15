
from pathlib import Path
import csv
import json
import re
import sys
from typing import Optional, Literal, List, Dict, Any
from api.ai_execution_router import create_ai_execution_router

from fastapi import FastAPI, HTTPException, Query, Response, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ==========================================
# 1. Configuration
# ==========================================

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from rag.search import ScientificKnowledgeStore
from rag.llm import GroundedAnswerSynthesizer
from rag.conversation import is_nasa_scientific_query
from rag.ingestion_manager import DynamicKnowledgeIngestionManager
from api.telemetry_service import extract_telemetry_payload
from research_gaps import DatasetCoverageService, ResearchGapDetectionService
from modeling.registry import list_available_datasets, get_modeling_dataset_metadata
from modeling.analyzer import ResearchObjectiveAnalyzer
from modeling.extraction_service import PredictiveDataExtractionService
from equipment import FireSafetyEquipmentService
from earth_applications import EarthApplicationsService
from rag.earth_adapter import EarthApplicationsRAGAdapter
from prompt_system.models import PromptResearchRequest, PromptResearchResponse
from prompt_system.service import PromptResearchService

CATALOG_PATH = (
    BASE / "processed_data"
    / "catalog"
    / "dataset_catalog.json"
)

RAG_RECORDS_PATH = (
    BASE / "processed_data"
    / "rag"
    / "scientific_knowledge_records.json"
)

RAG_MANIFEST_PATH = (
    BASE / "processed_data"
    / "rag"
    / "rag_manifest.json"
)

RAG_SCHEMA_PATH = (
    BASE / "processed_data"
    / "rag"
    / "rag_record_schema.json"
)

rag_store = ScientificKnowledgeStore(RAG_RECORDS_PATH)
coverage_service = DatasetCoverageService()
gap_detection_service = ResearchGapDetectionService(coverage_service=coverage_service)
modeling_service = PredictiveDataExtractionService(base_dir=BASE)
modeling_analyzer = ResearchObjectiveAnalyzer()
equipment_service = FireSafetyEquipmentService(
    rag_store=rag_store,
    gap_detection_service=gap_detection_service,
    base_dir=BASE,
)
earth_applications_service = EarthApplicationsService()
earth_adapter = EarthApplicationsRAGAdapter(service=earth_applications_service)
prompt_research_service = PromptResearchService(
    base_dir=BASE,
    coverage_service=coverage_service,
    gap_detection_service=gap_detection_service,
    modeling_service=modeling_service,
    modeling_analyzer=modeling_analyzer,
    equipment_service=equipment_service,
    earth_applications_service=earth_applications_service,
    rag_store=rag_store,
)
knowledge_ingestion_manager = DynamicKnowledgeIngestionManager(base_dir=BASE, rag_store=rag_store)


app = FastAPI(
    title="NASA FLAME Scientific API",
    description=(
        "Read-only access to NASA combustion "
        "experiment and telemetry datasets."
    ),
    version="0.1.0"
)

app.include_router(
    create_ai_execution_router(prompt_research_service)
)

# React development servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)


# ==========================================
# 2. Catalog helpers
# ==========================================

def load_catalog():
    if not CATALOG_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="Scientific dataset catalog unavailable"
        )

    try:
        with open(
            CATALOG_PATH,
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except (OSError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="Unable to read dataset catalog"
        )


def find_dataset(dataset_id):
    catalog = load_catalog()

    for dataset in catalog.get("datasets", []):
        if dataset["dataset_id"] == dataset_id:
            return dataset

    raise HTTPException(
        status_code=404,
        detail="Dataset not found"
    )


def safe_catalog_file(relative_path):
    if not relative_path:
        raise HTTPException(
            status_code=404,
            detail="File reference unavailable"
        )

    file_path = (BASE / relative_path).resolve()

    if not file_path.is_relative_to(BASE.resolve()):
        raise HTTPException(
            status_code=400,
            detail="Invalid dataset path"
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Dataset file unavailable"
        )

    return file_path


def load_metadata(dataset):
    relative_path = dataset.get("metadata_file")

    if not relative_path:
        return None

    path = safe_catalog_file(relative_path)

    try:
        with open(path, encoding="utf-8-sig") as file:
            return json.load(file)

    except (OSError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="Unable to read dataset metadata"
        )


# ==========================================
# 3. Health endpoint
# ==========================================

@app.get("/")
def root():
    return {
        "project": "NASA FLAME",
        "api_version": "0.1.0",
        "status": "running",
        "documentation": "/docs"
    }


@app.get("/api/health")
def health():
    catalog = load_catalog()

    return {
        "status": "ok",
        "dataset_count": len(
            catalog.get("datasets", [])
        ),
        "scientific_validation": "pending"
    }


# ==========================================
# 4. List available datasets
# ==========================================

@app.get("/api/datasets")
def list_datasets(
    category: str | None = None,
    granularity: str | None = None
):
    catalog = load_catalog()

    datasets = catalog.get("datasets", [])

    if category:
        datasets = [
            d for d in datasets
            if d["category"] == category
        ]

    if granularity:
        datasets = [
            d for d in datasets
            if d["granularity"] == granularity
        ]

    return {
        "count": len(datasets),
        "datasets": datasets
    }


# ==========================================
# 5. Individual dataset information
# ==========================================

@app.get("/api/datasets/{dataset_id}")
def get_dataset(dataset_id: str):
    return find_dataset(dataset_id)


# ==========================================
# 6. Scientific metadata
# ==========================================

@app.get("/api/datasets/{dataset_id}/metadata")
def get_dataset_metadata(dataset_id: str):
    dataset = find_dataset(dataset_id)

    return {
        "dataset_id": dataset_id,
        "dataset": dataset,
        "metadata": load_metadata(dataset)
    }


# ==========================================
# 7. Paginated scientific records
# ==========================================

@app.get("/api/datasets/{dataset_id}/records")
def get_dataset_records(
    dataset_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000)
):
    dataset = find_dataset(dataset_id)

    data_path = safe_catalog_file(
        dataset["data_file"]
    )

    if data_path.suffix.lower() != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Unsupported dataset format"
        )

    try:
        with open(
            data_path,
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            columns = reader.fieldnames or []

            records = []

            for index, row in enumerate(reader):

                if index < offset:
                    continue

                if len(records) >= limit:
                    break

                records.append(row)

    except (OSError, UnicodeError, csv.Error):
        raise HTTPException(
            status_code=503,
            detail="Unable to read dataset records"
        )

    total = dataset["record_count"]

    return {
        "dataset_id": dataset_id,
        "total_records": total,
        "offset": offset,
        "limit": limit,
        "returned": len(records),
        "has_more": offset + len(records) < total,
        "columns": columns,
        "records": records,
        "scientific_validation": dataset[
            "scientific_validation"
        ]
    }


# ==========================================
# 7b. Scientific Telemetry & Decimation (Phase V1)
# ==========================================

@app.get("/api/datasets/{dataset_id}/telemetry")
def get_dataset_telemetry(
    dataset_id: str,
    channels: Optional[str] = Query(default=None, description="Comma-separated list of measurement channel column names"),
    time_channel: Optional[str] = Query(default=None, description="Time axis column (defaults to verified time axis)"),
    start_time: Optional[float] = Query(default=None, description="Start time filter in seconds"),
    end_time: Optional[float] = Query(default=None, description="End time filter in seconds"),
    downsample_points: Optional[int] = Query(default=1000, ge=50, le=5000, description="Target downsampled points (null or 0 for raw records)")
):
    """
    Retrieve real, high-performance scientific telemetry for time-series combustion experiments.
    Provides extrema-preserving decimation (guaranteeing preservation of peak temperatures and spikes),
    sampling rate calculations (Hz), verified ignition event markers, and data quality indicators.
    """
    dataset = find_dataset(dataset_id)
    granularity = dataset.get("granularity", "")
    if granularity == "experiment":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dataset '{dataset_id}' has experiment-level granularity (discrete test runs) "
                f"without continuous time-series telemetry. Use /api/datasets/{dataset_id}/records instead."
            )
        )

    data_path = safe_catalog_file(dataset["data_file"])
    requested_channel_list = [c.strip() for c in channels.split(",") if c.strip()] if channels else None

    try:
        telemetry_payload = extract_telemetry_payload(
            file_path=data_path,
            dataset_id=dataset_id,
            granularity=granularity,
            scientific_validation=dataset.get("scientific_validation", "pending"),
            requested_channels=requested_channel_list,
            preferred_time_channel=time_channel,
            start_time=start_time,
            end_time=end_time,
            downsample_points=downsample_points,
        )
        return telemetry_payload
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process telemetry: {str(e)}")


# ==========================================
# 8. Scientific RAG Knowledge Base (Phase R1)
# ==========================================

@app.get("/api/rag/summary")
def get_rag_summary():
    """Retrieve RAG knowledge base manifest, counts by type/investigation, and metadata audit."""
    if not RAG_MANIFEST_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="Scientific RAG knowledge base manifest unavailable"
        )
    try:
        with open(RAG_MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="Unable to read RAG manifest"
        )


@app.get("/api/rag/schema")
def get_rag_schema():
    """Retrieve formal JSON schema for ScientificKnowledgeRecord."""
    if not RAG_SCHEMA_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="RAG record schema definition unavailable"
        )
    try:
        with open(RAG_SCHEMA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        raise HTTPException(
            status_code=503,
            detail="Unable to read RAG schema"
        )


@app.get("/api/rag/records")
def search_rag_records(
    q: str | None = None,
    record_type: str | None = None,
    dataset_id: str | None = None,
    investigation: str | None = None,
    material: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
):
    """
    Search and retrieve normalized scientific knowledge records.
    Supports BM25 lexical ranking and exact physical metadata filters.
    """
    if not rag_store.is_loaded:
        rag_store.load()

    return rag_store.search(
        query=q,
        record_type=record_type,
        dataset_id=dataset_id,
        investigation=investigation,
        fuel_material=material,
        offset=offset,
        limit=limit,
    )


@app.get("/api/rag/records/{record_id}")
def get_rag_record(record_id: str):
    """Retrieve a single verified scientific knowledge record by unique record_id."""
    if not rag_store.is_loaded:
        rag_store.load()

    record = rag_store.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Scientific knowledge record '{record_id}' not found"
        )
    return record


# ==========================================
# 9. Hybrid Scientific Retrieval (Phase R2)
# ==========================================

class RagSearchFilters(BaseModel):
    investigation: Optional[str] = Field(default=None, description="Filter by NASA investigation (e.g. BASS-II, Saffire-III)")
    dataset_id: Optional[str] = Field(default=None, description="Filter by catalog dataset ID")
    record_type: Optional[str] = Field(default=None, description="Filter by granularity: investigation, dataset, experiment_run, channel_group")
    fuel_material: Optional[str] = Field(default=None, description="Filter by fuel material substrate (e.g. PMMA, Cotton, Nomex)")


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500, description="Natural-language scientific research query")
    top_k: int = Field(default=10, ge=1, le=100, description="Maximum number of ranked records to return")
    mode: Literal["lexical", "semantic", "hybrid"] = Field(default="hybrid", description="Retrieval mode: lexical (BM25), semantic (dense vector), or hybrid (RRF)")
    filters: Optional[RagSearchFilters] = Field(default=None, description="Exact physical and provenance metadata filters")


@app.post("/api/rag/search")
def search_scientific_knowledge(req: RagSearchRequest):
    """
    Execute multi-mode scientific information retrieval across NASA microgravity experiments.
    Modes:
      - 'lexical': BM25 term-frequency and inverse document frequency scoring.
      - 'semantic': Dense vector cosine similarity via 384-d sentence-transformers.
      - 'hybrid': Reciprocal Rank Fusion (RRF) combining lexical and semantic ranking.
    Includes exact metadata pre-filtering, intent-aware calibration, and structured evidence citations.
    """
    if not rag_store.is_loaded:
        rag_store.load()

    filters_dict = req.filters.model_dump() if req.filters else {}

    results = rag_store.search_hybrid(
        query=req.query,
        top_k=req.top_k,
        mode=req.mode,
        record_type=filters_dict.get("record_type"),
        dataset_id=filters_dict.get("dataset_id"),
        investigation=filters_dict.get("investigation"),
        fuel_material=filters_dict.get("fuel_material"),
    )

    return results


# ==========================================
# 10. Grounded Scientific AI Assistant (Phase R3)
# ==========================================

rag_synthesizer = GroundedAnswerSynthesizer()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class RagAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000, description="Natural-language scientific research inquiry")
    top_k: int = Field(default=8, ge=1, le=50, description="Number of evidence records to retrieve for reasoning")
    filters: Optional[RagSearchFilters] = Field(default=None, description="Optional metadata pre-filters")
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Recent conversation turns (max 10)")
    finding_id: Optional[str] = Field(default=None, description="Optional research gap finding ID to ground inquiry in deterministic gap analysis")
    evidence_id: Optional[str] = Field(default=None, description="Optional Earth Application evidence ID (e.g. EA-EV-BASS-PYRO-01)")
    earth_category: Optional[str] = Field(default=None, description="Optional Earth Application category filter")
    investigation_id: Optional[str] = Field(default=None, description="Optional NASA investigation filter")


@app.post("/api/rag/ask")
def ask_scientific_assistant(req: RagAskRequest):
    """
    Submit a research question to the NASA FLAME Grounded Scientific AI Assistant.
    Retrieves evidence via hybrid RRF search, validates citations, enforces prompt-injection boundaries,
    and returns evidence-backed findings alongside suggested interactive dashboard actions.
    If finding_id is supplied, grounds the explanation in the deterministic Phase RG2 gap finding.
    If evidence_id or earth_category is supplied (or detected in question), grounds the explanation in audited Earth Applications.
    If no GEMINI_API_KEY is configured, gracefully operates in a transparent retrieval-only synthesis mode.
    """
    if not rag_store.is_loaded:
        rag_store.load()

    history_dicts = [m.model_dump() for m in (req.conversation_history or [])[-10:]]

    # Determine whether inquiry is a NASA scientific query or general conversation
    is_scientific = is_nasa_scientific_query(
        question=req.question,
        finding_id=req.finding_id,
        evidence_id=req.evidence_id,
        earth_category=req.earth_category,
        investigation_id=req.investigation_id,
        conversation_history=history_dicts,
    )

    if not is_scientific:
        # General conversation mode (greetings, pleasantries, educational concepts, general knowledge)
        # Skip NASA flight record hybrid retrieval; call Gemini directly
        return rag_synthesizer.answer(
            question=req.question,
            retrieved_candidates=[],
            conversation_history=history_dicts,
            finding=None,
            earth_evidence=None,
        )

    filters_dict = req.filters.model_dump() if req.filters else {}
    finding = None
    earth_evidence = None
    retrieval_query = req.question
    retrieval_fuel = filters_dict.get("fuel_material")

    if req.finding_id:
        finding = gap_detection_service.get_finding_by_id(req.finding_id)
        if finding:
            dims = finding.get("scientific_dimensions", {})
            if not retrieval_fuel and dims.get("fuel_material"):
                retrieval_fuel = dims.get("fuel_material")
            retrieval_query = f"{req.question} {finding.get('title', '')} {finding.get('explanation', '')}"

    # Check for Earth Applications inquiry
    if earth_adapter.is_earth_application_inquiry(
        question=req.question,
        evidence_id=req.evidence_id,
        earth_category=req.earth_category,
        investigation_id=req.investigation_id,
    ):
        earth_evidence = earth_adapter.resolve_earth_evidence(
            question=req.question,
            evidence_id=req.evidence_id,
            earth_category=req.earth_category,
            investigation_id=req.investigation_id,
        )
        if earth_evidence and not req.finding_id:
            top_ev = earth_evidence[0]
            retrieval_query = f"{req.question} {top_ev.get('title', '')} {top_ev.get('scientific_finding', '')[:200]}"

    # Check for follow-up conversational inquiry referencing previous experiments
    if req.conversation_history and re.search(r"\b(compare\s+(those|them|these)|those\s+experiments|how\s+do\s+they\s+compare|what\s+about\s+(them|those)|(show\s+me\s+)?(relevant\s+)?visualiz(ation|ations)?|plot\s+(them|those|that))\b", req.question, re.IGNORECASE):
        history_text = " ".join([m.content for m in req.conversation_history if isinstance(m.content, str)]).lower()
        if "saffire" in history_text or "sample" in history_text:
            retrieval_query = f"{req.question} Saffire-III Sample 1 Sample 2 flame spread comparison telemetry"
        elif "bass" in history_text:
            retrieval_query = f"{req.question} BASS-II solid fuel flammability comparison"

    # Step 1: Hybrid retrieval
    retrieval_res = rag_store.search_hybrid(
        query=retrieval_query,
        top_k=req.top_k,
        mode="hybrid",
        record_type=filters_dict.get("record_type"),
        dataset_id=filters_dict.get("dataset_id"),
        investigation=filters_dict.get("investigation") or (req.investigation_id if req.investigation_id in ("bass_ii", "saffire_iii") else None),
        fuel_material=retrieval_fuel,
    )

    # Step 2: Grounded answer synthesis
    history_dicts = [m.model_dump() for m in (req.conversation_history or [])[-10:]]
    answer_res = rag_synthesizer.answer(
        question=req.question,
        retrieved_candidates=retrieval_res.get("records", []),
        conversation_history=history_dicts,
        finding=finding,
        earth_evidence=earth_evidence,
    )
    if finding:
        answer_res["finding"] = finding
        answer_res["finding_id"] = finding.get("finding_id")
    if earth_evidence is not None:
        answer_res["earth_evidence"] = earth_evidence
        answer_res["earth_evidence_id"] = req.evidence_id or (earth_evidence[0].get("id") if earth_evidence else None)

    return answer_res


# ==========================================
# Dynamic RAG Knowledge Upload & Ingestion (Phase P2)
# ==========================================

class TestSearchRequest(BaseModel):
    query: str = Field(..., description="Query to test against RAG store")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    mode: str = Field(default="hybrid", description="Search mode: hybrid, bm25, or dense")


@app.post("/api/rag/upload")
async def upload_knowledge_document(
    file: UploadFile = File(..., description="Document or dataset file (.csv, .xlsx, .pdf, .txt, .md, .json)"),
    title: Optional[str] = Form(None, description="Optional custom document title"),
    investigation: Optional[str] = Form(None, description="Optional associated flight investigation"),
    source_attribution: Optional[str] = Form(None, description="Optional author or institution citation"),
    notes: Optional[str] = Form(None, description="Optional scientific notes or experiment tags"),
):
    """
    Ingest a scientific research document or dataset into the NASA FLAME active RAG knowledge base.
    Validates file formats, parses content, computes numerical distributions, generates
    grounded knowledge chunks, and rebuilds the BM25/vector retrieval index in real time.
    """
    if not rag_store.is_loaded:
        rag_store.load()

    try:
        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        result = knowledge_ingestion_manager.ingest_file(
            filename=file.filename or "uploaded_document",
            file_bytes=content_bytes,
            title=title,
            investigation=investigation,
            source_attribution=source_attribution,
            notes=notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")


@app.get("/api/rag/knowledge-base")
def get_knowledge_base_status():
    """
    Get real-time operational status and statistics of the RAG knowledge store,
    including canonical NASA flight dataset counts, uploaded research documents, and supported types.
    """
    if not rag_store.is_loaded:
        rag_store.load()

    manifest = knowledge_ingestion_manager.get_manifest()
    total_records = len(rag_store.records)
    uploaded_records = manifest.get("total_uploaded_records", 0)
    canonical_records = max(0, total_records - uploaded_records)

    return {
        "status": "operational",
        "total_records": total_records,
        "canonical_records": canonical_records,
        "uploaded_records": uploaded_records,
        "uploaded_documents_count": manifest.get("total_uploaded_documents", 0),
        "documents": manifest.get("documents", []),
        "supported_extensions": [".csv", ".tsv", ".xlsx", ".xls", ".pdf", ".txt", ".md", ".json"],
        "retrieval_mode": "hybrid_rrf",
        "vector_embeddings_ready": getattr(rag_store.embedding_service, "is_ready", False) or rag_store.embedding_service.is_index_ready(),
    }


@app.post("/api/rag/test-search")
def test_knowledge_search(req: TestSearchRequest):
    """
    Execute immediate test retrieval against the active RAG store.
    Enables users and judges to verify that uploaded documents and canonical NASA datasets
    are immediately retrievable with grounded citations and source metadata.
    """
    if not rag_store.is_loaded:
        rag_store.load()

    results = rag_store.search_hybrid(
        query=req.query,
        top_k=req.top_k,
        mode=req.mode if req.mode in ("hybrid", "bm25", "dense") else "hybrid",
    )

    return {
        "status": "success",
        "query": req.query,
        "total_found": results.get("returned", 0),
        "citations": results.get("evidence", []),
        "records": results.get("records", []),
        "retrieval_status": results.get("retrieval_status", {}),
    }


@app.delete("/api/rag/documents/{document_id}")
def delete_knowledge_document(document_id: str):
    """
    Remove an uploaded research document and its generated records from the RAG store.
    Rebuilds lexical/vector indices and updates the upload manifest.
    """
    if not rag_store.is_loaded:
        rag_store.load()

    try:
        return knowledge_ingestion_manager.delete_document(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get("/api/research-gaps/findings/{finding_id}/investigate")
def investigate_research_gap_finding(finding_id: str):
    """
    Investigate a detected research gap finding using the Grounded Scientific RAG Assistant.
    Combines the deterministic finding from Phase RG2 with hybrid experimental retrieval
    to synthesize an evidence-grounded explanation distinguishing verified observations,
    database gap analysis, scientific interpretation, future testing directions, and missing data.
    """
    finding = gap_detection_service.get_finding_by_id(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail=f"Research gap finding '{finding_id}' not found")

    if not rag_store.is_loaded:
        rag_store.load()

    question = f"Investigate scientific evidence, supporting flight experiments, and coverage status for research gap {finding_id}: {finding.get('title')}"
    
    retrieval_res = rag_store.search_hybrid(
        query=f"{finding.get('title')} {finding.get('explanation')}",
        top_k=8,
        mode="hybrid",
        fuel_material=finding.get("scientific_dimensions", {}).get("fuel_material"),
    )

    answer_res = rag_synthesizer.answer(
        question=question,
        retrieved_candidates=retrieval_res.get("records", []),
        conversation_history=[],
        finding=finding,
    )
    answer_res["finding"] = finding
    answer_res["finding_id"] = finding_id

    return {
        "status": "success",
        "finding_id": finding_id,
        "finding": finding,
        "investigation": answer_res,
        "answer": answer_res.get("answer"),
        "evidence_citations": answer_res.get("evidence_citations", []),
        "suggested_actions": answer_res.get("suggested_actions", []),
    }


# ==========================================
# 11. Research Gap Coverage Analysis (Phase RG1)
# ==========================================

coverage_service = DatasetCoverageService()


@app.get("/api/research-gaps/coverage/summary")
def get_research_gap_coverage_summary():
    """
    Get high-level dataset coverage summary metrics for NASA FLAME.
    Provides total investigations, discrete experiments, time-series sensor runs,
    breakdowns by environmental regimes (gravity, oxygen, airflow), parameter distributions,
    and repository asset audit (processed vs unprocessed raw files vs unrepresented investigations).
    """
    inventory = coverage_service.load()
    return {
        "status": "success",
        "metadata": inventory.get("metadata", {}),
        "summary": inventory.get("summary", {}),
        "repository_audit": inventory.get("repository_audit", {})
    }


@app.get("/api/research-gaps/coverage/experiments")
def get_research_gap_experiments(
    investigation: Optional[str] = Query(None, description="Filter by investigation name substring"),
    fuel_family: Optional[str] = Query(None, description="Filter by fuel family (e.g. solid-flat, solid-thick)"),
    gravity_regime: Optional[str] = Query(None, description="Filter by gravity regime (e.g. micro, normal, partial_lunar)"),
    oxygen_regime: Optional[str] = Query(None, description="Filter by oxygen regime (e.g. low_o2, normal_o2, elevated_o2)"),
    airflow_regime: Optional[str] = Query(None, description="Filter by airflow regime (e.g. quiescent, low-flow, high-flow)"),
    limit: int = Query(default=50, ge=1, le=200, description="Page size limit"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination")
):
    """
    Query experiment-level coverage records across all 133 microgravity combustion runs.
    Returns granular environmental regimes, parameter observation statuses,
    metadata completeness scores, and scientific source provenance.
    """
    inventory = coverage_service.load()
    experiments = inventory.get("experiments", [])

    # Apply filters
    filtered = experiments
    if investigation:
        inv_lower = investigation.lower()
        filtered = [e for e in filtered if inv_lower in e.get("investigation_name", "").lower()]

    if fuel_family:
        ff_lower = fuel_family.lower()
        filtered = [e for e in filtered if e.get("fuel_family", "").lower() == ff_lower]

    if gravity_regime:
        gr_lower = gravity_regime.lower()
        filtered = [e for e in filtered if e.get("environmental_conditions", {}).get("gravity", {}).get("regime", "").lower() == gr_lower]

    if oxygen_regime:
        ox_lower = oxygen_regime.lower()
        filtered = [e for e in filtered if e.get("environmental_conditions", {}).get("oxygen", {}).get("regime", "").lower() == ox_lower]

    if airflow_regime:
        af_lower = airflow_regime.lower()
        filtered = [e for e in filtered if e.get("environmental_conditions", {}).get("airflow", {}).get("regime", "").lower() == af_lower]

    total_matched = len(filtered)
    paged = filtered[offset : offset + limit]

    return {
        "status": "success",
        "total_matched": total_matched,
        "limit": limit,
        "offset": offset,
        "experiments": paged
    }


@app.get("/api/research-gaps/coverage/experiments/{experiment_id}")
def get_research_gap_experiment_detail(experiment_id: str):
    """
    Retrieve full coverage profile for a specific experiment run by ID.
    Includes comprehensive parameter classification (observed, confirmed_missing, unknown, not_applicable),
    sensor channels, and source provenance.
    """
    inventory = coverage_service.load()
    experiments = inventory.get("experiments", [])

    exp = next((e for e in experiments if e.get("experiment_id") == experiment_id), None)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found in coverage inventory")

    return {
        "status": "success",
        "experiment": exp
    }


@app.get("/api/research-gaps/coverage/parameters")
def get_research_gap_parameters_catalog():
    """
    Get the canonical catalog of all monitored scientific parameters.
    Returns physical quantities, standard measurement units, sensor technologies,
    and dataset availability distributions.
    """
    inventory = coverage_service.load()
    return {
        "status": "success",
        "parameters": inventory.get("parameters_catalog", {})
    }


@app.get("/api/research-gaps/coverage/matrix")
def get_research_gap_coverage_matrix(
    matrix_type: Literal["gravity_vs_oxygen", "material_vs_airflow", "all"] = Query(
        default="gravity_vs_oxygen",
        description="Matrix heatmap dimension selection"
    )
):
    """
    Retrieve multi-dimensional dataset coverage heatmaps.
    Maps evidence density (robust, moderate, limited, critical gap) across
    gravity regimes, oxygen regimes, material families, and airflow velocities.
    Includes scientific disclaimers separating local database boundaries from NASA literature.
    """
    inventory = coverage_service.load()
    all_matrices = inventory.get("coverage_matrix", {})

    if matrix_type == "all":
        matrix_data = all_matrices
    elif matrix_type == "material_vs_airflow":
        matrix_data = {"material_vs_airflow": all_matrices.get("material_vs_airflow", {})}
    else:
        matrix_data = {"gravity_vs_oxygen": all_matrices.get("gravity_vs_oxygen", {})}

    return {
        "status": "success",
        "matrix_type": matrix_type,
        "matrix": matrix_data
    }


@app.get("/api/research-gaps/coverage/comparability")
def get_research_gap_comparability(
    exp1: Optional[str] = Query(None, description="First experiment ID for pairwise comparison (e.g. saffire_iii_sample_1)"),
    exp2: Optional[str] = Query(None, description="Second experiment ID for pairwise comparison (e.g. saffire_iii_sample_2)")
):
    """
    Evaluate scientific comparability between experiment runs or review benchmark comparisons.
    Enforces rigorous comparability checks:
      - Facility & instrumentation suite compatibility.
      - Material and environmental condition alignment.
      - Shared physical parameters & unit conversions.
      - Assignment to DIRECTLY_COMPARABLE, CONDITIONALLY_COMPARABLE, or METHODOLOGICALLY_INCOMPARABLE.
    """
    if exp1 and exp2:
        comparison_res = coverage_service.compare_experiments(exp1, exp2)
        if "error" in comparison_res:
            raise HTTPException(status_code=404, detail=comparison_res["error"])
        return {
            "status": "success",
            "comparison": comparison_res
        }

    inventory = coverage_service.load()
    return {
        "status": "success",
        "comparability_overview": inventory.get("comparability", {})
    }


# ==========================================
# 12. Scientific Research Gap Detection Engine (Phase RG2)
# ==========================================

# (gap_detection_service initialized globally above)


class ResearchGapAnalyzeRequest(BaseModel):
    gravity: Optional[str] = Field(default=None, description="Gravity regime (e.g. micro, normal, partial_lunar, partial_mars)")
    oxygen_regime: Optional[str] = Field(default=None, description="Oxygen regime (e.g. low_o2, normal_o2, elevated_o2, high_o2)")
    pressure_regime: Optional[str] = Field(default=None, description="Pressure regime (e.g. standard, hypobaric, hyperbaric)")
    fuel_family: Optional[str] = Field(default=None, description="Fuel family (e.g. solid-flat, solid-thick, droplet, gaseous)")
    fuel_material: Optional[str] = Field(default=None, description="Specific fuel material name or substring")
    airflow_regime: Optional[str] = Field(default=None, description="Airflow regime (e.g. quiescent, low-flow, high-flow)")
    parameter: Optional[str] = Field(default=None, description="Specific scientific parameter ID to verify")
    question: Optional[str] = Field(default=None, max_length=500, description="Optional natural language question for context (free-text interpretation is reserved for RAG)")


@app.get("/api/research-gaps/findings")
def get_research_gap_findings(
    gap_type: Optional[str] = Query(None, description="Filter by gap type: coverage_gap, sparse_evidence, measurement_gap, metadata_gap, ingestion_opportunity, comparison_gap"),
    dimension: Optional[str] = Query(None, description="Filter by scientific dimension: gravity, oxygen, pressure, fuel_family, fuel_material, airflow, parameter"),
    min_priority: float = Query(default=0.0, ge=0.0, le=10.0, description="Minimum heuristic priority score threshold (0.0 - 10.0)"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of findings to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset")
):
    """
    Retrieve deterministic scientific research gap findings across all 6 verified categories:
      - coverage_gap: applicable experimental conditions unrepresented in indexed collection
      - sparse_evidence: conditions with fewer than 5 usable experiment runs
      - measurement_gap: scientific parameters confirmed absent from sensor records
      - metadata_gap: scientifically relevant metadata unlogged or unknown
      - ingestion_opportunity: raw files on disk or external NASA PSI programs uningested
      - comparison_gap: insufficient comparable experiment pairs for causal isolation
    """
    findings = gap_detection_service.detect_all_gaps(
        gap_type=gap_type,
        dimension=dimension,
        min_priority=min_priority
    )

    total_matched = len(findings)
    paged = findings[offset : offset + limit]

    return {
        "status": "success",
        "total_matched": total_matched,
        "limit": limit,
        "offset": offset,
        "findings": paged
    }


@app.get("/api/research-gaps/findings/{finding_id}")
def get_research_gap_finding_detail(finding_id: str):
    """
    Retrieve full profile and transparent heuristic scoring breakdown for a specific research gap finding.
    Exposes stable ID, gap type, scientific dimensions, denominator, supporting experiment IDs,
    evidence confidence justification, priority score factors, limitations, and actionable next steps.
    """
    finding = gap_detection_service.get_finding_by_id(finding_id)
    if not finding:
        raise HTTPException(
            status_code=404,
            detail=f"Research gap finding '{finding_id}' not found"
        )

    return {
        "status": "success",
        "finding": finding
    }


@app.get("/api/research-gaps/summary")
def get_research_gaps_summary():
    """
    Get aggregate summary metrics across all detected scientific research gaps.
    Returns total findings count, breakdown by gap type, priority tier distributions,
    top 5 prioritized findings, and explicit database scope disclaimer.
    """
    summary = gap_detection_service.get_gap_summary()
    return {
        "status": "success",
        "summary": summary
    }


@app.post("/api/research-gaps/analyze")
def analyze_research_inquiry(req: ResearchGapAnalyzeRequest):
    """
    Evaluate empirical dataset coverage for a research question or parameter combination.
    Deterministically matches requested experimental conditions against FLAME's indexed records,
    reports matching usable runs, and attaches all applicable gap findings.
    If a free-text question without structured parameters is passed, reports that limitation explicitly.
    """
    filters_dict = {
        "gravity": req.gravity,
        "oxygen_regime": req.oxygen_regime,
        "pressure_regime": req.pressure_regime,
        "fuel_family": req.fuel_family,
        "fuel_material": req.fuel_material,
        "airflow_regime": req.airflow_regime,
        "parameter": req.parameter
    }

    analysis_res = gap_detection_service.analyze_inquiry(
        filters=filters_dict,
        question=req.question
    )

    return {
        "status": "success",
        "analysis": analysis_res
    }


# ==========================================
# 7. Predictive-Modeling Data Extraction API
# ==========================================

class ModelingInterpretRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000, description="Natural-language modeling research objective")


class ModelingPreviewRequest(BaseModel):
    dataset_id: str = Field(description="Target dataset identifier")
    selected_features: Optional[List[str]] = Field(default=None, description="List of feature IDs to select")
    target_id: Optional[str] = Field(default=None, description="Target variable ID")
    material_filter: Optional[str] = Field(default=None, description="Fuel material filter substring")
    min_oxygen: Optional[float] = Field(default=None, description="Minimum initial oxygen concentration (% vol)")
    max_oxygen: Optional[float] = Field(default=None, description="Maximum initial oxygen concentration (% vol)")
    min_flow: Optional[float] = Field(default=None, description="Minimum airflow velocity (cm/s)")
    max_flow: Optional[float] = Field(default=None, description="Maximum airflow velocity (cm/s)")
    start_time_s: Optional[float] = Field(default=None, description="Start of time window in seconds (telemetry)")
    end_time_s: Optional[float] = Field(default=None, description="End of time window in seconds (telemetry)")
    preview_limit: int = Field(default=25, ge=1, le=100, description="Max rows to return for preview table")
    complete_cases_only: bool = Field(default=False, description="Filter to only complete cases (drop rows with missing values)")
    exclude_flagged_anomalies: bool = Field(default=False, description="Exclude records flagged with empirical source anomalies")


class ModelingExportRequest(BaseModel):
    dataset_id: str = Field(description="Target dataset identifier")
    format: Literal["csv", "json", "report"] = Field(default="csv", description="Export format: csv, json, or report")
    selected_features: Optional[List[str]] = Field(default=None, description="List of feature IDs to export")
    target_id: Optional[str] = Field(default=None, description="Target variable ID")
    material_filter: Optional[str] = Field(default=None, description="Fuel material filter substring")
    min_oxygen: Optional[float] = Field(default=None, description="Minimum initial oxygen concentration (% vol)")
    max_oxygen: Optional[float] = Field(default=None, description="Maximum initial oxygen concentration (% vol)")
    min_flow: Optional[float] = Field(default=None, description="Minimum airflow velocity (cm/s)")
    max_flow: Optional[float] = Field(default=None, description="Maximum airflow velocity (cm/s)")
    start_time_s: Optional[float] = Field(default=None, description="Start of time window in seconds (telemetry)")
    end_time_s: Optional[float] = Field(default=None, description="End of time window in seconds (telemetry)")
    max_rows: Optional[int] = Field(default=None, ge=1, le=50000, description="Max records to export (capped for safety)")
    complete_cases_only: bool = Field(default=False, description="Filter to only complete cases (drop rows with missing values)")
    exclude_flagged_anomalies: bool = Field(default=False, description="Exclude records flagged with empirical source anomalies")


class ModelingValidateMergeRequest(BaseModel):
    dataset_ids: List[str] = Field(min_length=1, description="List of dataset IDs to validate for cross-experiment merging")


@app.get("/api/modeling/datasets")
def list_modeling_datasets_endpoint():
    """
    List all NASA combustion datasets registered and evaluated for predictive machine learning extraction.
    Returns dataset identities, paradigms (tabular vs telemetry), total records, and capabilities.
    """
    datasets = list_available_datasets()
    return {
        "status": "success",
        "dataset_count": len(datasets),
        "datasets": datasets
    }


@app.get("/api/modeling/datasets/{dataset_id}")
def get_modeling_dataset_schema_endpoint(dataset_id: str):
    """
    Retrieve full schema, measured/derived feature registry, supported targets, and unsupported targets for a dataset.
    """
    meta = get_modeling_dataset_metadata(dataset_id)
    if not meta:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found in predictive modeling registry."
        )
    return {
        "status": "success",
        "dataset": meta
    }


@app.post("/api/modeling/interpret")
def interpret_modeling_objective_endpoint(req: ModelingInterpretRequest):
    """
    Interpret researcher's natural-language objective into structured modeling targets, candidate features,
    and dataset suitability assessments. Identifies uninstrumented targets and provides alternative suggestions.
    """
    interpretation = modeling_analyzer.interpret(req.query)
    return {
        "status": "success",
        "interpretation": interpretation
    }


@app.post("/api/modeling/preview")
def preview_modeling_data_endpoint(req: ModelingPreviewRequest):
    """
    Generate bounded data preview table and data quality audit report (missing counts, constant columns, leakage risks).
    Guarantees preview rows match actual underlying data records.
    """
    try:
        preview_res = modeling_service.generate_preview(
            dataset_id=req.dataset_id,
            selected_features=req.selected_features,
            target_id=req.target_id,
            material_filter=req.material_filter,
            min_oxygen=req.min_oxygen,
            max_oxygen=req.max_oxygen,
            min_flow=req.min_flow,
            max_flow=req.max_flow,
            start_time_s=req.start_time_s,
            end_time_s=req.end_time_s,
            preview_limit=req.preview_limit,
            complete_cases_only=req.complete_cases_only,
            exclude_flagged_anomalies=req.exclude_flagged_anomalies,
        )
        return {
            "status": "success",
            "preview": preview_res
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/modeling/export")
def export_modeling_data_endpoint(req: ModelingExportRequest):
    """
    Export actual experimental records as CSV, metadata JSON, or Markdown quality audit report.
    Never fabricates values, never silently imputes missing targets, and preserves original measurement units.
    """
    try:
        if req.format == "csv":
            csv_content = modeling_service.export_csv(
                dataset_id=req.dataset_id,
                selected_features=req.selected_features,
                target_id=req.target_id,
                material_filter=req.material_filter,
                min_oxygen=req.min_oxygen,
                max_oxygen=req.max_oxygen,
                min_flow=req.min_flow,
                max_flow=req.max_flow,
                start_time_s=req.start_time_s,
                end_time_s=req.end_time_s,
                max_rows=req.max_rows,
                complete_cases_only=req.complete_cases_only,
                exclude_flagged_anomalies=req.exclude_flagged_anomalies,
            )
            filename = f"{req.dataset_id}_modeling_data.csv"
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )

        elif req.format == "json":
            meta_json = modeling_service.export_metadata_json(
                dataset_id=req.dataset_id,
                selected_features=req.selected_features,
                target_id=req.target_id,
                material_filter=req.material_filter,
                min_oxygen=req.min_oxygen,
                max_oxygen=req.max_oxygen,
                min_flow=req.min_flow,
                max_flow=req.max_flow,
                start_time_s=req.start_time_s,
                end_time_s=req.end_time_s,
                max_rows=req.max_rows,
                complete_cases_only=req.complete_cases_only,
                exclude_flagged_anomalies=req.exclude_flagged_anomalies,
            )
            filename = f"{req.dataset_id}_metadata.json"
            return Response(
                content=json.dumps(meta_json, indent=2),
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )

        elif req.format == "report":
            report_md = modeling_service.export_quality_report_markdown(
                dataset_id=req.dataset_id,
                selected_features=req.selected_features,
                target_id=req.target_id,
                material_filter=req.material_filter,
                min_oxygen=req.min_oxygen,
                max_oxygen=req.max_oxygen,
                min_flow=req.min_flow,
                max_flow=req.max_flow,
                start_time_s=req.start_time_s,
                end_time_s=req.end_time_s,
                max_rows=req.max_rows,
                complete_cases_only=req.complete_cases_only,
                exclude_flagged_anomalies=req.exclude_flagged_anomalies,
            )
            filename = f"{req.dataset_id}_quality_report.md"
            return Response(
                content=report_md,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format '{req.format}'. Use 'csv', 'json', or 'report'.")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/modeling/validate-merge")
def validate_merge_endpoint(req: ModelingValidateMergeRequest):
    """
    Validate whether multiple datasets can be scientifically merged into a single training table.
    Blocks invalid cross-paradigm merges (e.g. tabular discrete runs vs continuous sensor telemetry).
    """
    try:
        modeling_service.validate_no_incompatible_merge(req.dataset_ids)
        return {
            "status": "success",
            "compatible": True,
            "message": "Datasets share compatible experimental paradigms."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 8. Fire-Safety Equipment Research API
# ==========================================

class EquipmentInterpretRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000, description="Natural-language fire-safety equipment research inquiry")
    category_filter: Optional[Literal["detection", "prevention", "suppression", "multi_area"]] = Field(
        default=None, description="Optional category filter override"
    )


@app.get("/api/equipment-research/overview")
def get_equipment_research_overview_endpoint():
    """
    Retrieve comprehensive overview of Fire-Safety Equipment Research module,
    including the 3 research categories, quick-start templates, and verified investigations.
    """
    return {
        "status": "success",
        "overview": equipment_service.get_overview()
    }


@app.post("/api/equipment-research/interpret")
def interpret_equipment_research_endpoint(req: EquipmentInterpretRequest):
    """
    Interpret researcher's natural-language inquiry into a structured spacecraft fire-safety
    research workspace (parameters, relevant NASA investigations, verified measurements,
    scientific interpretation, engineering implications, research gaps, and recommended actions).
    """
    try:
        res = equipment_service.interpret_objective(
            query=req.query,
            category_override=req.category_filter
        )
        return {
            "status": "success",
            "research_package": res
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/equipment-research/category/{category_id}")
def get_equipment_category_endpoint(category_id: str):
    """
    Retrieve curated deep-dive information for a specific research category (detection, prevention, suppression).
    """
    try:
        details = equipment_service.get_category_details(category_id)
        return {
            "status": "success",
            "category_details": details
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# 10. Earth Applications (Phase EA1) Endpoints
# ==========================================

@app.get("/api/earth-applications/categories")
def get_earth_application_categories_endpoint():
    """
    Retrieve all 7 extensible Earth Application categories with dynamic evidence counts.
    """
    categories = earth_applications_service.get_categories()
    return {
        "status": "ok",
        "total_categories": len(categories),
        "categories": categories,
    }


@app.get("/api/earth-applications/overview")
def get_earth_applications_overview_endpoint():
    """
    Retrieve comprehensive overview of Earth Applications research bridges and scientific safeguards.
    """
    return {
        "status": "ok",
        "overview": earth_applications_service.get_overview(),
    }


@app.get("/api/earth-applications")
def list_earth_applications_endpoint(
    category: Optional[str] = Query(None, description="Category identifier filter"),
    classification: Optional[str] = Query(None, description="Evidence classification filter"),
    investigation_id: Optional[str] = Query(None, description="Investigation identifier filter"),
    provenance_status: Optional[str] = Query(None, description="Provenance status filter"),
    limit: int = Query(50, ge=1, le=100, description="Pagination record limit"),
    offset: int = Query(0, ge=0, description="Pagination record offset"),
):
    """
    Retrieve filtered and paginated list of Earth Applications evidence records.
    """
    res = earth_applications_service.list_evidence(
        category=category,
        classification=classification,
        investigation_id=investigation_id,
        provenance_status=provenance_status,
        limit=limit,
        offset=offset,
    )
    return res


@app.get("/api/earth-applications/investigations/{investigation_id}")
def get_earth_applications_by_investigation_endpoint(investigation_id: str):
    """
    Retrieve all verified Earth Application evidence records associated with a specific NASA investigation.
    """
    records = earth_applications_service.get_evidence_by_investigation(investigation_id)
    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"No verified Earth application evidence found for investigation '{investigation_id}'.",
        )
    return {
        "status": "ok",
        "investigation_id": investigation_id,
        "evidence_count": len(records),
        "evidence": [r.dict() for r in records],
    }


@app.get("/api/earth-applications/{id}")
def get_earth_application_by_id_endpoint(id: str):
    """
    Retrieve a single Earth Application evidence record by its unique ID.
    """
    record = earth_applications_service.get_evidence_by_id(id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Earth application evidence record '{id}' not found.",
        )
    return {
        "status": "ok",
        "evidence": record.dict(),
    }


@app.get("/api/earth-applications/{id}/evidence")
def get_earth_application_evidence_detail_endpoint(id: str):
    """
    Retrieve full evidence details, transfer limitations, and source provenance for an Earth Application finding.
    """
    record = earth_applications_service.get_evidence_by_id(id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Earth application evidence record '{id}' not found.",
        )
    return {
        "status": "ok",
        "evidence_id": record.id,
        "evidence": record.dict(),
    }


@app.get("/api/earth-applications/{id}/investigate")
def investigate_earth_application_endpoint(id: str, question: Optional[str] = Query(None)):
    """
    Investigate an Earth Application finding using the Grounded Scientific RAG Assistant.
    Synthesizes an evidence-grounded terrestrial transfer explanation distinguishing
    verified flight observations, physical mechanisms, transfer limitations, and validation requirements.
    """
    record = earth_applications_service.get_evidence_by_id(id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Earth application evidence record '{id}' not found.",
        )

    if not rag_store.is_loaded:
        rag_store.load()

    default_q = f"Investigate terrestrial combustion application and physical transfer limits for {id}: {record.title}"
    active_q = question or default_q

    # Hybrid retrieval of supporting NASA records
    retrieval_res = rag_store.search_hybrid(
        query=f"{record.title} {record.scientific_finding}",
        top_k=8,
        mode="hybrid",
        investigation=record.investigation_id if record.investigation_id in ("bass_ii", "saffire_iii") else None,
    )

    earth_evidence = [record.model_dump() if hasattr(record, "model_dump") else record.dict()]

    if rag_synthesizer.llm_provider.is_configured:
        answer_res = rag_synthesizer.answer(
            question=active_q,
            retrieved_candidates=retrieval_res.get("records", []),
            conversation_history=[],
            earth_evidence=earth_evidence,
        )
    else:
        answer_res = rag_synthesizer._generate_earth_application_synthesis(
            question=active_q,
            earth_items=earth_evidence,
            retrieved_candidates=retrieval_res.get("records", []),
            reason="Deterministic specialist Earth Applications workspace synthesis",
        )
        if not answer_res.get("evidence_citations"):
            answer_res["evidence_citations"] = [rag_synthesizer.earth_adapter.build_citation_item(earth_evidence[0])]

    answer_res["evidence_id"] = id
    answer_res["earth_evidence"] = earth_evidence

    return {
        "status": "success",
        "evidence_id": id,
        "evidence": record.model_dump() if hasattr(record, "model_dump") else record.dict(),
        "investigation": answer_res,
        "answer": answer_res.get("answer"),
        "evidence_citations": answer_res.get("evidence_citations", []),
        "suggested_actions": answer_res.get("suggested_actions", []),
    }


# ==========================================
# 16. Shared Prompt Research System (Phase F2)
# ==========================================

@app.post("/api/prompt/research", response_model=PromptResearchResponse)
def submit_prompt_research(req: PromptResearchRequest):
    """
    Unified entry point for natural-language scientific research inquiries.
    Intelligently resolves intent, checks evidence sufficiency, dispatches
    to specialist adapters, and produces typed structured responses.
    """
    return prompt_research_service.process_prompt(req)


@app.get("/api/prompt/capabilities")
def get_prompt_capabilities():
    """
    Returns supported workspace adapters, capability summaries, and representative scientific inquiries.
    """
    return {
        "status": "ok",
        "supported_workspaces": [
            {
                "id": "visualization",
                "label": "Scientific Visualization",
                "description": "Real empirical telemetry extraction, decimation, and units-segregated multi-channel charting.",
                "example_queries": [
                    "Plot Saffire-III Sample 1 radiant heat flux and thermocouple temperatures during ignition.",
                    "Show Cygnus cabin pressure and temperature during vehicle re-entry.",
                ],
            },
            {
                "id": "comparison",
                "label": "Experiment Comparison",
                "description": "Pairwise scientific comparability checking and quantitative telemetry parameter alignment.",
                "example_queries": [
                    "Compare Saffire-III Sample 1 and Sample 2 temperature behavior.",
                    "Compare radiometer heat flux peaks across Saffire flight burns.",
                ],
            },
            {
                "id": "modeling",
                "label": "Predictive-Modeling Data Extraction",
                "description": "Discovery of empirical labels, feature suitability analysis, and data leakage audit.",
                "example_queries": [
                    "Prepare BASS-II data for predicting flame spread rate from oxygen and airflow.",
                    "Extract PMMA flammability features for supervised machine learning.",
                ],
            },
            {
                "id": "gap_detection",
                "label": "Research-Gap Detection",
                "description": "Multi-dimensional experimental coverage evaluation and unexplored regime discovery.",
                "example_queries": [
                    "Find missing experimental coverage for low oxygen and low airflow in microgravity.",
                    "Identify uncharacterized partial-gravity combustion conditions.",
                ],
            },
            {
                "id": "equipment",
                "label": "Fire-Safety Equipment Research",
                "description": "Spacecraft fire detection and suppression investigation informed by microgravity physics.",
                "example_queries": [
                    "What NASA evidence is relevant to spacecraft smoke detection?",
                    "Evaluate sensor response times for early fire detection in microgravity ducts.",
                ],
            },
            {
                "id": "earth_applications",
                "label": "Earth Applications Research",
                "description": "Rigorous cross-domain translation of buoyancy-free combustion findings to terrestrial fire safety.",
                "example_queries": [
                    "How could BASS-II results inform fire safety on Earth?",
                    "Find microgravity evidence relevant to wildfire behavior and ventilation duct fires.",
                ],
            },
        ],
        "execution_modes": ["deterministic_fallback", "llm_assisted"],
        "units_separation_enforced": True,
        "synthetic_data_generation": False,
    }









