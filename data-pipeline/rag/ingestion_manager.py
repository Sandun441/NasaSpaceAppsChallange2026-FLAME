"""
NASA FLAME — Dynamic RAG Knowledge Upload & Ingestion Engine (Phase P2)
Enables authorized scientific researchers to import and index new experimental datasets,
flight publications, telemetry CSVs, and technical documents into the active RAG store.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
import io

from .schema import (
    ScientificKnowledgeRecord,
    DataProvenance,
    ExperimentalConditions,
    ChannelInfo,
    MeasuredStatistics,
    QualityAndValidation,
)
from .search import ScientificKnowledgeStore

logger = logging.getLogger("flame.rag.ingestion")

SUPPORTED_EXTENSIONS = {
    ".csv", ".tsv", ".xlsx", ".xls", ".pdf", ".txt", ".md", ".json"
}

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class DynamicKnowledgeIngestionManager:
    """Manages parsing, normalization, indexing, and persistence of uploaded knowledge."""

    def __init__(self, base_dir: Path, rag_store: ScientificKnowledgeStore):
        self.base_dir = Path(base_dir).resolve()
        self.rag_store = rag_store
        self.rag_dir = self.base_dir / "processed_data" / "rag"
        self.rag_dir.mkdir(parents=True, exist_ok=True)
        self.upload_manifest_path = self.rag_dir / "uploaded_documents_manifest.json"
        self._ensure_manifest()

    def _ensure_manifest(self):
        """Ensure uploaded documents tracking manifest exists."""
        if not self.upload_manifest_path.exists():
            initial_manifest = {
                "total_uploaded_documents": 0,
                "total_uploaded_records": 0,
                "documents": [],
                "last_updated_utc": datetime.now(timezone.utc).isoformat(),
            }
            with open(self.upload_manifest_path, "w", encoding="utf-8") as f:
                json.dump(initial_manifest, f, indent=2)

    def get_manifest(self) -> Dict[str, Any]:
        """Read and return upload manifest."""
        self._ensure_manifest()
        try:
            with open(self.upload_manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load upload manifest: %s", e)
            return {
                "total_uploaded_documents": 0,
                "total_uploaded_records": 0,
                "documents": [],
                "last_updated_utc": datetime.now(timezone.utc).isoformat(),
            }

    def _save_manifest(self, manifest: Dict[str, Any]):
        """Persist updated manifest to disk."""
        manifest["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
        with open(self.upload_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def ingest_file(
        self,
        filename: str,
        file_bytes: bytes,
        title: Optional[str] = None,
        investigation: Optional[str] = None,
        source_attribution: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate, parse, normalize, and index an uploaded document or dataset.
        Returns detailed ingestion results including indexed record count and IDs.
        """
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum limit of 25 MB ({len(file_bytes)} bytes)")

        safe_filename = Path(filename).name.strip()
        if not safe_filename:
            raise ValueError("Invalid or empty filename")

        ext = Path(safe_filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        file_sha256 = hashlib.sha256(file_bytes).hexdigest()
        manifest = self.get_manifest()

        # Check for duplicate upload
        for doc in manifest.get("documents", []):
            if doc.get("sha256") == file_sha256:
                return {
                    "status": "already_indexed",
                    "message": f"Document '{safe_filename}' has already been indexed ({doc.get('record_count', 0)} records).",
                    "document_id": doc.get("document_id"),
                    "record_count": doc.get("record_count", 0),
                    "indexed_records": doc.get("record_ids", []),
                }

        doc_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", Path(safe_filename).stem.lower())[:32]
        doc_id = f"doc_{int(datetime.now(timezone.utc).timestamp())}_{doc_slug}"
        doc_title = title.strip() if title and title.strip() else Path(safe_filename).stem.replace("_", " ").title()
        inv_name = investigation.strip() if investigation and investigation.strip() else "User Uploaded Research"

        now_iso = datetime.now(timezone.utc).isoformat()

        # Parse file based on extension
        records: List[ScientificKnowledgeRecord] = []

        if ext in {".csv", ".tsv"}:
            records = self._parse_csv(
                file_bytes=file_bytes,
                filename=safe_filename,
                doc_id=doc_id,
                doc_title=doc_title,
                inv_name=inv_name,
                source_sha256=file_sha256,
                source_attribution=source_attribution,
                notes=notes,
                now_iso=now_iso,
                delimiter="," if ext == ".csv" else "\t",
            )
        elif ext in {".xlsx", ".xls"}:
            records = self._parse_excel(
                file_bytes=file_bytes,
                filename=safe_filename,
                doc_id=doc_id,
                doc_title=doc_title,
                inv_name=inv_name,
                source_sha256=file_sha256,
                source_attribution=source_attribution,
                notes=notes,
                now_iso=now_iso,
            )
        elif ext == ".pdf":
            records = self._parse_pdf(
                file_bytes=file_bytes,
                filename=safe_filename,
                doc_id=doc_id,
                doc_title=doc_title,
                inv_name=inv_name,
                source_sha256=file_sha256,
                source_attribution=source_attribution,
                notes=notes,
                now_iso=now_iso,
            )
        elif ext in {".txt", ".md"}:
            records = self._parse_text(
                file_bytes=file_bytes,
                filename=safe_filename,
                doc_id=doc_id,
                doc_title=doc_title,
                inv_name=inv_name,
                source_sha256=file_sha256,
                source_attribution=source_attribution,
                notes=notes,
                now_iso=now_iso,
            )
        elif ext == ".json":
            records = self._parse_json(
                file_bytes=file_bytes,
                filename=safe_filename,
                doc_id=doc_id,
                doc_title=doc_title,
                inv_name=inv_name,
                source_sha256=file_sha256,
                source_attribution=source_attribution,
                notes=notes,
                now_iso=now_iso,
            )

        if not records:
            raise ValueError(f"No extractable scientific content or valid records found in {safe_filename}.")

        # Convert to dicts and index into RAG store
        record_dicts = [r.model_dump() for r in records]
        added_count = self.rag_store.add_records(record_dicts, persist=True)

        # Update upload tracking manifest
        record_ids = [r.record_id for r in records]
        doc_entry = {
            "document_id": doc_id,
            "filename": safe_filename,
            "title": doc_title,
            "investigation_name": inv_name,
            "source_attribution": source_attribution or "Researcher Data Upload",
            "sha256": file_sha256,
            "file_size_bytes": len(file_bytes),
            "record_count": len(records),
            "record_ids": record_ids,
            "uploaded_at_utc": now_iso,
            "notes": notes or "",
        }

        manifest["documents"].append(doc_entry)
        manifest["total_uploaded_documents"] = len(manifest["documents"])
        manifest["total_uploaded_records"] = sum(d.get("record_count", 0) for d in manifest["documents"])
        self._save_manifest(manifest)

        return {
            "status": "success",
            "message": f"Successfully ingested and indexed {len(records)} records from '{safe_filename}'.",
            "document_id": doc_id,
            "title": doc_title,
            "record_count": len(records),
            "records_indexed": record_ids,
            "total_knowledge_store_records": len(self.rag_store.records),
        }

    # -------------------------------------------------------------
    # Format Parsers
    # -------------------------------------------------------------

    def _parse_csv(
        self,
        file_bytes: bytes,
        filename: str,
        doc_id: str,
        doc_title: str,
        inv_name: str,
        source_sha256: str,
        source_attribution: Optional[str],
        notes: Optional[str],
        now_iso: str,
        delimiter: str = ",",
    ) -> List[ScientificKnowledgeRecord]:
        """Extract structured dataset summary and experiment run records from tabular data."""
        import pandas as pd

        try:
            df = pd.read_csv(io.BytesIO(file_bytes), sep=delimiter, low_memory=False)
        except Exception as e:
            # Fallback encoding try
            df = pd.read_csv(io.BytesIO(file_bytes), sep=delimiter, encoding="latin1", low_memory=False)

        if df.empty:
            raise ValueError(f"CSV file '{filename}' contains no data rows.")

        records: List[ScientificKnowledgeRecord] = []
        num_rows, num_cols = df.shape
        col_names = [str(c).strip() for c in df.columns]

        # Identify physical channels and statistics
        channels: List[ChannelInfo] = []
        stats_notes = []

        for col in col_names:
            series = df[col]
            lower_col = col.lower()
            phys_q = "measurement"
            unit = None

            # Detect physical quantity
            if any(k in lower_col for k in ["temp", "tc", "thermo", "t_"]):
                phys_q = "temperature"
                unit = "°C" if "c" in lower_col else "K"
            elif any(k in lower_col for k in ["o2", "oxygen", "ox_"]):
                phys_q = "oxygen_concentration"
                unit = "%"
            elif any(k in lower_col for k in ["press", "p_", "kpa", "atm"]):
                phys_q = "pressure"
                unit = "kPa"
            elif any(k in lower_col for k in ["flow", "vel", "speed", "cm/s", "m/s"]):
                phys_q = "flow_velocity"
                unit = "m/s" if "m/s" in lower_col else "cm/s"
            elif any(k in lower_col for k in ["heat", "flux", "rad"]):
                phys_q = "heat_flux"
                unit = "kW/m²"
            elif any(k in lower_col for k in ["smoke", "obscur", "photodiode", "volt"]):
                phys_q = "optical_obscuration"
                unit = "V"

            channels.append(ChannelInfo(channel_name=col, physical_quantity=phys_q, unit=unit))

            if pd.api.types.is_numeric_dtype(series):
                valid_vals = series.dropna()
                if not valid_vals.empty:
                    stats_notes.append(
                        f"{col}: min={float(valid_vals.min()):.3f}, mean={float(valid_vals.mean()):.3f}, max={float(valid_vals.max()):.3f}"
                    )

        # 1. Master Dataset Record
        dataset_searchable = (
            f"Dataset: {doc_title}. Investigation: {inv_name}. File: {filename}. "
            f"Dimensions: {num_rows} rows by {num_cols} measurement columns. "
            f"Columns: {', '.join(col_names[:25])}. "
            f"Key Column Statistics: {'; '.join(stats_notes[:10])}. "
            f"Source: {source_attribution or filename}. Notes: {notes or 'User uploaded scientific dataset'}."
        )

        master_rec = ScientificKnowledgeRecord(
            record_id=f"{doc_id}_dataset",
            record_type="dataset",
            dataset_id=doc_id,
            investigation_name=inv_name,
            title=f"{doc_title} (Dataset Overview)",
            scientific_objective=f"Structured tabular combustion data imported from {filename}.",
            description=(
                f"Tabular combustion telemetry/dataset containing {num_rows} rows and {num_cols} columns. "
                f"Measured parameters include: {', '.join(col_names[:15])}."
            ),
            materials_and_conditions=ExperimentalConditions(
                gravity_regime="microgravity" if "micro" in filename.lower() else "normal_gravity",
            ),
            channels_and_units=channels[:20],
            measured_statistics=MeasuredStatistics(
                valid_sample_count=num_rows,
                notes=f"Total dataset records: {num_rows}. Channels: {num_cols}.",
            ),
            provenance=DataProvenance(
                source_file=filename,
                source_sha256=source_sha256,
                data_file=f"user_uploads/{filename}",
            ),
            quality=QualityAndValidation(
                validation_status="user_uploaded",
                quality_flags=["user_imported_data"],
            ),
            searchable_text=dataset_searchable,
            keywords=["dataset", "tabular_telemetry", inv_name.lower(), doc_slug] + [c.lower() for c in col_names[:10]],
            created_at_utc=now_iso,
        )
        records.append(master_rec)

        # 2. Segment into Representative Experiment Runs if applicable or row blocks
        # If dataset has distinct experiment IDs or conditions
        id_cols = [c for c in col_names if any(k in c.lower() for k in ["test", "run", "sample", "exp", "condition", "material"])]
        if id_cols:
            grouped = df.groupby(id_cols[0])
            for group_val, grp in list(grouped)[:40]:  # Cap at 40 runs per file
                run_rows = len(grp)
                sub_stats = []
                for ch in channels:
                    if ch.channel_name in grp.columns and pd.api.types.is_numeric_dtype(grp[ch.channel_name]):
                        v = grp[ch.channel_name].dropna()
                        if not v.empty:
                            sub_stats.append(f"{ch.channel_name}: min={float(v.min()):.2f}, mean={float(v.mean()):.2f}, max={float(v.max()):.2f}")

                run_text = (
                    f"Experiment Run {group_val} from dataset {doc_title}. Investigation: {inv_name}. "
                    f"Sample count: {run_rows} readings. "
                    f"Measured metrics: {'; '.join(sub_stats[:8])}. "
                    f"Source: {filename}."
                )

                run_rec = ScientificKnowledgeRecord(
                    record_id=f"{doc_id}_run_{re.sub(r'[^a-zA-Z0-9_-]', '_', str(group_val).lower())[:24]}",
                    record_type="experiment_run",
                    experiment_id=str(group_val),
                    dataset_id=doc_id,
                    investigation_name=inv_name,
                    title=f"{doc_title} — Test Run {group_val}",
                    scientific_objective=f"Individual experiment run {group_val} from {filename}.",
                    description=f"Recorded data segment containing {run_rows} time-series readings for condition {group_val}.",
                    materials_and_conditions=ExperimentalConditions(
                        fuel_material=str(group_val) if "material" in id_cols[0].lower() else None,
                        gravity_regime="microgravity" if "micro" in filename.lower() else "normal_gravity",
                    ),
                    channels_and_units=channels[:15],
                    measured_statistics=MeasuredStatistics(
                        valid_sample_count=run_rows,
                        notes=f"Sub-series for {group_val}.",
                    ),
                    provenance=DataProvenance(
                        source_file=filename,
                        source_worksheet=str(group_val),
                        source_sha256=source_sha256,
                    ),
                    quality=QualityAndValidation(
                        validation_status="user_uploaded",
                    ),
                    searchable_text=run_text,
                    keywords=["experiment_run", str(group_val).lower(), inv_name.lower(), "telemetry"],
                    created_at_utc=now_iso,
                )
                records.append(run_rec)

        return records

    def _parse_excel(
        self,
        file_bytes: bytes,
        filename: str,
        doc_id: str,
        doc_title: str,
        inv_name: str,
        source_sha256: str,
        source_attribution: Optional[str],
        notes: Optional[str],
        now_iso: str,
    ) -> List[ScientificKnowledgeRecord]:
        """Parse Excel workbook across sheets."""
        import pandas as pd

        excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        sheet_names = excel_file.sheet_names
        records: List[ScientificKnowledgeRecord] = []

        for sheet in sheet_names[:10]:  # up to 10 sheets
            df = excel_file.parse(sheet)
            if df.empty:
                continue

            num_rows, num_cols = df.shape
            col_names = [str(c).strip() for c in df.columns]

            sheet_text = (
                f"Worksheet: {sheet} in Excel workbook {doc_title}. Investigation: {inv_name}. File: {filename}. "
                f"Rows: {num_rows}, Columns: {num_cols}. "
                f"Headers: {', '.join(col_names[:20])}. "
                f"Attribution: {source_attribution or filename}."
            )

            rec = ScientificKnowledgeRecord(
                record_id=f"{doc_id}_{re.sub(r'[^a-zA-Z0-9_-]', '_', sheet.lower())[:20]}",
                record_type="dataset",
                dataset_id=doc_id,
                investigation_name=inv_name,
                title=f"{doc_title} — Sheet: {sheet}",
                scientific_objective=f"Excel worksheet '{sheet}' data from {filename}.",
                description=f"Spreadsheet data containing {num_rows} rows and {num_cols} columns from sheet '{sheet}'.",
                provenance=DataProvenance(
                    source_file=filename,
                    source_worksheet=sheet,
                    source_sha256=source_sha256,
                ),
                quality=QualityAndValidation(validation_status="user_uploaded"),
                searchable_text=sheet_text,
                keywords=["excel_worksheet", sheet.lower(), inv_name.lower()],
                created_at_utc=now_iso,
            )
            records.append(rec)

        return records

    def _parse_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        doc_id: str,
        doc_title: str,
        inv_name: str,
        source_sha256: str,
        source_attribution: Optional[str],
        notes: Optional[str],
        now_iso: str,
    ) -> List[ScientificKnowledgeRecord]:
        """Extract multi-page text and chunk into document sections using pymupdf."""
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        if page_count == 0:
            raise ValueError(f"PDF '{filename}' contains 0 pages.")

        records: List[ScientificKnowledgeRecord] = []

        # Extract text per page
        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text").strip()
            if not page_text or len(page_text) < 40:
                continue

            # Split into chunks of ~800 characters if page is large
            chunks = self._chunk_text(page_text, max_chars=900, overlap=100)
            for c_idx, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_p{page_idx + 1}_c{c_idx + 1}"
                searchable = (
                    f"Publication / Document: {doc_title} (Page {page_idx + 1}). "
                    f"Investigation: {inv_name}. File: {filename}. "
                    f"Content: {chunk} "
                    f"Attribution: {source_attribution or filename}."
                )

                rec = ScientificKnowledgeRecord(
                    record_id=chunk_id,
                    record_type="document_section",
                    dataset_id=doc_id,
                    investigation_name=inv_name,
                    title=f"{doc_title} — Page {page_idx + 1} (Section {c_idx + 1})",
                    scientific_objective=f"Extracted scientific literature passage from {filename} page {page_idx + 1}.",
                    description=chunk,
                    provenance=DataProvenance(
                        source_file=filename,
                        source_worksheet=f"Page {page_idx + 1}",
                        source_sha256=source_sha256,
                    ),
                    quality=QualityAndValidation(validation_status="user_uploaded"),
                    searchable_text=searchable,
                    keywords=["publication", "scientific_document", f"page_{page_idx + 1}", inv_name.lower()],
                    created_at_utc=now_iso,
                )
                records.append(rec)

        doc.close()
        return records

    def _parse_text(
        self,
        file_bytes: bytes,
        filename: str,
        doc_id: str,
        doc_title: str,
        inv_name: str,
        source_sha256: str,
        source_attribution: Optional[str],
        notes: Optional[str],
        now_iso: str,
    ) -> List[ScientificKnowledgeRecord]:
        """Parse raw plain text or Markdown files into section records."""
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1")

        content = content.strip()
        if not content:
            raise ValueError(f"Text file '{filename}' is empty.")

        chunks = self._chunk_text(content, max_chars=1000, overlap=150)
        records: List[ScientificKnowledgeRecord] = []

        for c_idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_sec_{c_idx + 1}"
            searchable = (
                f"Document: {doc_title}. Investigation: {inv_name}. Section {c_idx + 1}. "
                f"Source File: {filename}. "
                f"Text: {chunk} "
                f"Attribution: {source_attribution or filename}."
            )

            rec = ScientificKnowledgeRecord(
                record_id=chunk_id,
                record_type="document_section",
                dataset_id=doc_id,
                investigation_name=inv_name,
                title=f"{doc_title} (Section {c_idx + 1})",
                scientific_objective=f"Imported research documentation section from {filename}.",
                description=chunk,
                provenance=DataProvenance(
                    source_file=filename,
                    source_worksheet=f"Section {c_idx + 1}",
                    source_sha256=source_sha256,
                ),
                quality=QualityAndValidation(validation_status="user_uploaded"),
                searchable_text=searchable,
                keywords=["text_document", inv_name.lower(), f"section_{c_idx + 1}"],
                created_at_utc=now_iso,
            )
            records.append(rec)

        return records

    def _parse_json(
        self,
        file_bytes: bytes,
        filename: str,
        doc_id: str,
        doc_title: str,
        inv_name: str,
        source_sha256: str,
        source_attribution: Optional[str],
        notes: Optional[str],
        now_iso: str,
    ) -> List[ScientificKnowledgeRecord]:
        """Parse JSON objects or arrays into scientific records."""
        data = json.loads(file_bytes.decode("utf-8"))
        records: List[ScientificKnowledgeRecord] = []

        if isinstance(data, list):
            items = data[:60]
            for idx, item in enumerate(items):
                item_title = item.get("title") or item.get("name") or f"Item {idx + 1}"
                item_desc = item.get("description") or item.get("text") or json.dumps(item)[:500]

                searchable = (
                    f"JSON Record: {item_title}. Dataset: {doc_title}. Investigation: {inv_name}. "
                    f"Data: {json.dumps(item, ensure_ascii=False)}."
                )

                rec = ScientificKnowledgeRecord(
                    record_id=f"{doc_id}_item_{idx + 1}",
                    record_type="dataset",
                    dataset_id=doc_id,
                    investigation_name=inv_name,
                    title=f"{doc_title} — {item_title}",
                    scientific_objective=f"Structured JSON record from {filename}.",
                    description=item_desc,
                    provenance=DataProvenance(
                        source_file=filename,
                        source_worksheet=f"Item {idx + 1}",
                        source_sha256=source_sha256,
                    ),
                    quality=QualityAndValidation(validation_status="user_uploaded"),
                    searchable_text=searchable,
                    keywords=["json_record", inv_name.lower()],
                    created_at_utc=now_iso,
                )
                records.append(rec)
        elif isinstance(data, dict):
            searchable = f"JSON Document: {doc_title}. Investigation: {inv_name}. Content: {json.dumps(data)[:1500]}."
            rec = ScientificKnowledgeRecord(
                record_id=f"{doc_id}_main",
                record_type="dataset",
                dataset_id=doc_id,
                investigation_name=inv_name,
                title=doc_title,
                scientific_objective=f"JSON document imported from {filename}.",
                description=json.dumps(data, indent=2)[:800],
                provenance=DataProvenance(
                    source_file=filename,
                    source_sha256=source_sha256,
                ),
                quality=QualityAndValidation(validation_status="user_uploaded"),
                searchable_text=searchable,
                keywords=["json_data", inv_name.lower()],
                created_at_utc=now_iso,
            )
            records.append(rec)

        return records

    def _chunk_text(self, text: str, max_chars: int = 800, overlap: int = 100) -> List[str]:
        """Split text into overlapping character windows on sentence/paragraph boundaries."""
        clean = re.sub(r"\s+", " ", text).strip()
        if len(clean) <= max_chars:
            return [clean]

        chunks = []
        start = 0
        while start < len(clean):
            end = min(start + max_chars, len(clean))
            # Try to snap end to period or space
            if end < len(clean):
                boundary = clean.rfind(". ", start, end)
                if boundary > start + (max_chars // 2):
                    end = boundary + 1
                else:
                    space_boundary = clean.rfind(" ", start, end)
                    if space_boundary > start + (max_chars // 2):
                        end = space_boundary

            segment = clean[start:end].strip()
            if segment:
                chunks.append(segment)

            if end >= len(clean):
                break
            start = max(start + 1, end - overlap)

        return chunks

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Remove an uploaded document and its records from the RAG store and manifest."""
        manifest = self.get_manifest()
        docs = manifest.get("documents", [])
        target_doc = None
        for d in docs:
            if d.get("document_id") == document_id:
                target_doc = d
                break
        if not target_doc:
            raise ValueError(f"Document with ID '{document_id}' not found.")

        record_ids_to_remove = set(target_doc.get("record_ids", []))

        # Remove from manifest
        manifest["documents"] = [d for d in docs if d.get("document_id") != document_id]
        manifest["total_uploaded_documents"] = len(manifest["documents"])
        manifest["total_uploaded_records"] = sum(d.get("record_count", 0) for d in manifest["documents"])
        self._save_manifest(manifest)

        # Remove from RAG store
        removed_count = self.rag_store.remove_records(record_ids_to_remove, persist=True)

        return {
            "status": "success",
            "message": f"Successfully removed document '{target_doc.get('filename')}' ({removed_count} records).",
            "document_id": document_id,
            "total_knowledge_store_records": len(self.rag_store.records),
        }

