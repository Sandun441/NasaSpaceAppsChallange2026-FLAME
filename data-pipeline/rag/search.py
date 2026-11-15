"""
NASA FLAME — Scientific Knowledge Hybrid Search Engine (Phase R2)
Advanced multi-stage scientific retrieval engine:
1. BM25 Lexical Retrieval: Term-frequency and inverse document frequency scoring with title/keyword weighting.
2. Dense Vector Semantic Retrieval: 384-d sentence-transformer embeddings with NumPy cosine similarity.
3. Reciprocal Rank Fusion (RRF): Robust rank combination without ad-hoc score scaling.
4. Scientific Intent-Aware Re-ranking: Prevents generic investigation records from dominating specific experiment queries.
5. Exact Pre-Filtering: Investigation, dataset, record_type, and fuel material filters.
6. Structured Evidence & Provenance: Complete citation metadata for downstream LLMs and UI workspaces.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Literal, Tuple
import json
import re
import math
import logging

from rag.embeddings import LocalEmbeddingService
from rag.entity_resolution import DatasetEntityResolver
from rag.unicode_utils import clean_scientific_data, clean_scientific_unicode

logger = logging.getLogger("flame.rag.search")

RetrievalMode = Literal["lexical", "semantic", "hybrid"]


class ScientificKnowledgeStore:
    """In-memory hybrid searchable store of scientific knowledge records."""

    def __init__(self, records_path: Any):
        self.records_path = Path(records_path).resolve()
        self.base_dir = self.records_path.parents[2]  # data-pipeline directory
        self.records: List[Dict[str, Any]] = []
        self.lookup: Dict[str, Dict[str, Any]] = {}
        self.inverted_index: Dict[str, List[int]] = {}
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.is_loaded = False

        # Phase R2 Semantic Embedding Service
        self.embedding_service = LocalEmbeddingService(base_dir=self.base_dir)
        # Canonical Entity Resolver
        self.entity_resolver = DatasetEntityResolver(records_path=self.records_path)
        self.load()

    def load(self):
        """Load records from JSON file and construct inverted index."""
        if not self.records_path.exists():
            return

        with open(self.records_path, encoding="utf-8") as f:
            self.records = json.load(f)

        self.lookup = {r["record_id"]: r for r in self.records}
        self._build_index()
        self.is_loaded = True

        # Attempt to load semantic embeddings index
        if self.embedding_service.is_index_ready():
            self.embedding_service.load_index()

    def _tokenize(self, text: str) -> List[str]:
        """Normalize and tokenize text into index terms."""
        if not text:
            return []
        tokens = re.findall(r"\b[a-zA-Z0-9_°%/-]{2,}\b", text.lower())
        return tokens

    def _build_index(self):
        """Construct in-memory inverted index and document length stats."""
        self.inverted_index = {}
        self.doc_lengths = []
        total_len = 0

        for idx, rec in enumerate(self.records):
            text_corpus = (
                f"{rec.get('title', '')} "
                f"{rec.get('searchable_text', '')} "
                f"{' '.join(rec.get('keywords', []))} "
                f"{rec.get('materials_and_conditions', {}).get('fuel_material', '') or ''}"
            )
            tokens = self._tokenize(text_corpus)
            self.doc_lengths.append(len(tokens))
            total_len += len(tokens)

            unique_tokens = set(tokens)
            for token in unique_tokens:
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append(idx)

        self.avg_doc_length = (total_len / len(self.records)) if self.records else 0.0

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single scientific knowledge record by record_id."""
        return self.lookup.get(record_id)

    def add_records(self, new_records: List[Dict[str, Any]], persist: bool = True) -> int:
        """
        Dynamically append new scientific records to the in-memory knowledge store,
        rebuild the lexical/BM25 inverted index, update embedding index if available,
        and persist to disk so new knowledge survives server restarts.
        """
        if not new_records:
            return 0

        added_count = 0
        for rec in new_records:
            rid = rec.get("record_id")
            if not rid:
                continue

            if rid in self.lookup:
                # Update existing record in place
                for idx, existing in enumerate(self.records):
                    if existing.get("record_id") == rid:
                        self.records[idx] = rec
                        break
                self.lookup[rid] = rec
            else:
                self.records.append(rec)
                self.lookup[rid] = rec
                added_count += 1

        # Rebuild lexical BM25 index immediately
        self._build_index()

        # Update semantic dense embeddings if index is active
        if self.embedding_service.is_index_ready():
            try:
                self.embedding_service.build_index(self.records, force_rebuild=True)
            except Exception as e:
                logger.warning("Could not refresh dense embeddings after record addition: %s", e)

        # Persist to disk
        if persist:
            try:
                with open(self.records_path, "w", encoding="utf-8") as f:
                    json.dump(self.records, f, indent=2, ensure_ascii=False)

                jsonl_path = self.records_path.with_suffix(".jsonl")
                with open(jsonl_path, "w", encoding="utf-8") as f:
                    for r in self.records:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error("Failed to persist updated scientific knowledge records: %s", e)

        return added_count

    def remove_records(self, record_ids: set, persist: bool = True) -> int:
        """
        Remove records by ID, rebuild the lexical/BM25 index, and persist to disk.
        """
        initial_count = len(self.records)
        self.records = [r for r in self.records if r.get("record_id") not in record_ids]
        self.records_by_id = {r["record_id"]: r for r in self.records if "record_id" in r}
        self._build_index()

        if persist:
            try:
                with open(self.records_path, "w", encoding="utf-8") as f:
                    json.dump(self.records, f, indent=2, ensure_ascii=False)

                jsonl_path = self.records_path.with_suffix(".jsonl")
                with open(jsonl_path, "w", encoding="utf-8") as f:
                    for r in self.records:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error("Failed to persist updated scientific knowledge records: %s", e)

        return initial_count - len(self.records)

    def _apply_metadata_filters(
        self,
        record_type: Optional[str] = None,
        dataset_id: Optional[str] = None,
        investigation: Optional[str] = None,
        fuel_material: Optional[str] = None,
    ) -> List[int]:
        """Return indices of records matching all active metadata filters."""
        candidate_indices = set(range(len(self.records)))

        if record_type:
            candidate_indices = {
                i for i in candidate_indices if self.records[i].get("record_type") == record_type
            }

        if dataset_id:
            candidate_indices = {
                i for i in candidate_indices if self.records[i].get("dataset_id") == dataset_id
            }

        if investigation:
            inv_lower = investigation.lower()
            candidate_indices = {
                i for i in candidate_indices
                if inv_lower in self.records[i].get("investigation_name", "").lower()
            }

        if fuel_material:
            mat_lower = fuel_material.lower()
            candidate_indices = {
                i for i in candidate_indices
                if mat_lower in (self.records[i].get("materials_and_conditions", {}).get("fuel_material") or "").lower()
            }

        return sorted(list(candidate_indices))

    def _score_bm25(
        self,
        query: str,
        candidate_indices: List[int],
    ) -> List[Tuple[int, float]]:
        """Compute BM25 scores for candidate documents."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return [(idx, 0.0) for idx in candidate_indices]

        k1 = 1.5
        b = 0.75
        N = len(self.records)
        scored = []

        for idx in candidate_indices:
            rec = self.records[idx]
            doc_len = self.doc_lengths[idx]
            score = 0.0

            text_corpus = (
                f"{rec.get('title', '')} "
                f"{rec.get('searchable_text', '')} "
                f"{' '.join(rec.get('keywords', []))}"
            ).lower()

            title_lower = rec.get("title", "").lower()

            for q_term in query_tokens:
                postings = self.inverted_index.get(q_term, [])
                df = len(postings)
                if df == 0:
                    continue

                idf = math.log(1.0 + (N - df + 0.5) / (df + 0.5))
                tf = text_corpus.count(q_term)

                if tf > 0:
                    title_boost = 2.0 if q_term in title_lower else 1.0
                    numerator = tf * (k1 + 1.0)
                    denominator = tf + k1 * (1.0 - b + b * (doc_len / (self.avg_doc_length or 1.0)))
                    score += idf * (numerator / denominator) * title_boost

            if score > 0.0:
                scored.append((idx, score))

        # Sort descending by BM25 score, tie-break by record_id
        scored.sort(key=lambda x: (-x[1], self.records[x[0]]["record_id"]))
        return scored

    def _detect_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyze query for scientific intent:
        - experiment_level: user seeks specific tests, runs, materials, or parameter variations.
        - sensor_level: user asks about instruments, channels, thermocouples, telemetry.
        - overview_level: broad questions about mission or investigation goals.
        """
        q_lower = query.lower()

        is_experiment = bool(re.search(
            r"\b(experiment|experiments|test|tests|run|runs|sample|samples|pmma|cotton|nomex|sibal|burn|ignit|flame spread|extinction|quiescent|flow restrictor|pi|bhattacharjee|olson|ferkul|miller|tien|fernandez)\b",
            q_lower
        ))

        is_sensor = bool(re.search(
            r"\b(sensor|sensors|thermocouple|thermocouples|radiometer|radiometers|anemometer|smoke|pressure|pcm|flow|ventilation|channel|channels|telemetry|hz|measurement|measurements)\b",
            q_lower
        ))

        is_overview = bool(re.search(
            r"\b(investigation|overview|objective|mission|what is|summary|program|payload)\b",
            q_lower
        ))

        return {
            "is_experiment": is_experiment,
            "is_sensor": is_sensor,
            "is_overview": is_overview,
        }

    def _build_evidence_citation(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured evidence citation for a scientific knowledge record."""
        prov = rec.get("provenance", {})
        cond = rec.get("materials_and_conditions", {})
        stats = rec.get("measured_statistics")
        quality = rec.get("quality", {})

        channels = [
            {
                "channel_name": ch.get("channel_name"),
                "physical_quantity": ch.get("physical_quantity"),
                "unit": ch.get("unit"),
            }
            for ch in rec.get("channels_and_units", [])[:6]
        ]

        # Extract quality warnings
        quality_warnings = list(quality.get("quality_flags", []))
        if quality.get("known_issues"):
            quality_warnings.extend(quality.get("known_issues", []))

        return clean_scientific_data({
            "record_id": rec.get("record_id"),
            "investigation": rec.get("investigation_name"),
            "dataset_id": rec.get("dataset_id"),
            "record_type": rec.get("record_type"),
            "title": rec.get("title"),
            "source_file": prov.get("source_file"),
            "source_worksheet": prov.get("source_worksheet"),
            "source_excel_row": prov.get("source_excel_row"),
            "data_file": prov.get("data_file"),
            "fuel_material": cond.get("fuel_material"),
            "experimental_conditions": {
                k: v for k, v in cond.items() if v is not None
            },
            "measured_statistics": stats,
            "available_channels": channels,
            "quality_flags": quality.get("quality_flags", []),
            "quality_warnings": quality_warnings,
            "missing_fields": rec.get("missing_fields", []),
        })

    def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        mode: RetrievalMode = "hybrid",
        record_type: Optional[str] = None,
        dataset_id: Optional[str] = None,
        investigation: Optional[str] = None,
        fuel_material: Optional[str] = None,
        rrf_k: int = 60,
    ) -> Dict[str, Any]:
        """
        Execute Hybrid Scientific Retrieval (BM25 + Dense Semantic + RRF).
        Applies metadata pre-filtering, intent-aware rank calibration,
        and generates structured citations.
        """
        if not self.records:
            return {
                "query": query,
                "mode": mode,
                "total_candidates": 0,
                "returned": 0,
                "records": [],
                "evidence": [],
                "retrieval_status": {
                    "mode_used": mode,
                    "semantic_available": False,
                    "fallback_applied": False,
                }
            }

        # 1. Apply exact metadata filters
        candidate_indices = self._apply_metadata_filters(
            record_type=record_type,
            dataset_id=dataset_id,
            investigation=investigation,
            fuel_material=fuel_material,
        )

        total_candidates = len(candidate_indices)
        if total_candidates == 0:
            return {
                "query": query,
                "mode": mode,
                "total_candidates": 0,
                "returned": 0,
                "records": [],
                "evidence": [],
                "retrieval_status": {
                    "mode_used": mode,
                    "semantic_available": self.embedding_service.is_ready,
                    "fallback_applied": False,
                }
            }

        candidate_ids = [self.records[i]["record_id"] for i in candidate_indices]
        id_to_idx = {self.records[i]["record_id"]: i for i in candidate_indices}

        # Check semantic availability
        semantic_ready = self.embedding_service.is_ready
        if not semantic_ready and self.embedding_service.is_index_ready():
            semantic_ready = self.embedding_service.load_index()

        fallback_applied = False
        mode_used = mode

        if mode in ("semantic", "hybrid") and not semantic_ready:
            fallback_applied = True
            mode_used = "lexical"
            logger.warning("Semantic index not ready; falling back to lexical BM25.")

        # 2. Compute BM25 rankings if needed
        bm25_ranks: Dict[str, int] = {}
        bm25_scores: Dict[str, float] = {}

        if mode_used in ("lexical", "hybrid"):
            bm25_scored = self._score_bm25(query, candidate_indices)
            for rank_idx, (idx, score) in enumerate(bm25_scored, start=1):
                rid = self.records[idx]["record_id"]
                bm25_ranks[rid] = rank_idx
                bm25_scores[rid] = score

        # 3. Compute Semantic cosine rankings if needed
        semantic_ranks: Dict[str, int] = {}
        semantic_scores: Dict[str, float] = {}

        if mode_used in ("semantic", "hybrid") and semantic_ready:
            sem_scored = self.embedding_service.similarity_search(
                query=query,
                candidate_ids=candidate_ids,
                top_k=len(candidate_ids)
            )
            for rank_idx, (rid, score) in enumerate(sem_scored, start=1):
                semantic_ranks[rid] = rank_idx
                semantic_scores[rid] = score

        # 4. Rank candidates based on mode
        intent = self._detect_query_intent(query)
        entity_res = self.entity_resolver.resolve(query)
        req_records = set(entity_res.get("requested_record_ids", []))
        req_datasets = set(entity_res.get("requested_dataset_ids", []))

        final_scored: List[Dict[str, Any]] = []

        all_candidate_ids = set(bm25_ranks.keys()) | set(semantic_ranks.keys())
        # Ensure any explicitly requested records are included in candidate list
        for rid in req_records:
            if rid in self.lookup:
                all_candidate_ids.add(rid)

        if not all_candidate_ids:
            # If neither retriever scored (e.g. empty or out-of-vocab query), return candidates deterministically
            all_candidate_ids = set(candidate_ids)

        for rid in all_candidate_ids:
            rec = self.lookup[rid]
            rtype = rec.get("record_type")

            b_rank = bm25_ranks.get(rid)
            s_rank = semantic_ranks.get(rid)
            b_score = bm25_scores.get(rid, 0.0)
            s_score = semantic_scores.get(rid, 0.0)

            # Entity Priority Tier:
            # Explicitly requested experiment IDs must take priority over semantic retrieval ranking.
            priority_tier = 4
            if req_records and rid in req_records:
                priority_tier = 1
            elif req_datasets and rec.get("dataset_id") in req_datasets:
                if rtype == "experiment_run":
                    priority_tier = 2
                else:
                    priority_tier = 3
            elif not req_records and not req_datasets:
                priority_tier = 1  # Standard unconstrained search

            # Intent-aware granularity weighting:
            # Prevent generic macro investigation records from dominating specific experiment searches
            granularity_weight = 1.0
            if intent["is_experiment"] and not intent["is_overview"]:
                if rtype == "investigation":
                    granularity_weight = 0.65
                elif rtype == "experiment_run":
                    granularity_weight = 1.15
            elif intent["is_sensor"]:
                if rtype == "channel_group":
                    granularity_weight = 1.25
                elif rtype == "investigation":
                    granularity_weight = 0.70

            if mode_used == "hybrid":
                # Reciprocal Rank Fusion: 1 / (k + rank)
                rrf_bm25 = (1.0 / (rrf_k + b_rank)) if b_rank is not None else 0.0
                rrf_sem = (1.0 / (rrf_k + s_rank)) if s_rank is not None else 0.0
                rrf_score = (rrf_bm25 + rrf_sem) * granularity_weight
                primary_score = rrf_score
            elif mode_used == "semantic":
                primary_score = s_score * granularity_weight
            else:  # lexical
                primary_score = b_score * granularity_weight

            final_scored.append({
                "record": rec,
                "score": round(primary_score, 6),
                "priority_tier": priority_tier,
                "scores": {
                    "rrf": round(( (1.0/(rrf_k + b_rank) if b_rank else 0.0) +
                                   (1.0/(rrf_k + s_rank) if s_rank else 0.0) ) * granularity_weight, 6) if (b_rank or s_rank) else 0.0,
                    "semantic": round(s_score, 4),
                    "lexical": round(b_score, 4),
                },
                "ranks": {
                    "bm25_rank": b_rank,
                    "semantic_rank": s_rank,
                },
                "record_id": rid,
            })

        # Deterministic stable sorting:
        # 1. Priority tier ascending (1 is highest priority)
        # 2. Primary score descending
        # 3. Semantic score descending
        # 4. Lexical score descending
        # 5. record_id ascending string order
        final_scored.sort(key=lambda x: (
            x["priority_tier"],
            -x["score"],
            -x["scores"]["semantic"],
            -x["scores"]["lexical"],
            x["record_id"]
        ))

        # Top-K slice
        top_results = final_scored[:top_k]
        evidence_list = [self._build_evidence_citation(item["record"]) for item in top_results]

        return {
            "query": query,
            "mode": mode,
            "total_candidates": total_candidates,
            "returned": len(top_results),
            "records": top_results,
            "evidence": evidence_list,
            "retrieval_status": {
                "mode_requested": mode,
                "mode_used": mode_used,
                "semantic_available": semantic_ready,
                "fallback_applied": fallback_applied,
                "embedding_model": self.embedding_service.model_name if semantic_ready else None,
                "query_intent": intent,
                "entity_resolution": entity_res,
            }
        }

    def search(
        self,
        query: Optional[str] = None,
        record_type: Optional[str] = None,
        dataset_id: Optional[str] = None,
        investigation: Optional[str] = None,
        fuel_material: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Legacy/compatibility endpoint for GET /api/rag/records.
        Supports BM25 lexical ranking and exact physical metadata filters.
        """
        if not self.records:
            return {"total": 0, "returned": 0, "records": []}

        candidate_indices = self._apply_metadata_filters(
            record_type=record_type,
            dataset_id=dataset_id,
            investigation=investigation,
            fuel_material=fuel_material,
        )

        if not candidate_indices:
            return {"total": 0, "returned": 0, "offset": offset, "limit": limit, "records": []}

        if query:
            scored = self._score_bm25(query, candidate_indices)
            matched_records = [self.records[idx] for idx, _ in scored]
        else:
            matched_records = [self.records[i] for i in candidate_indices]

        total_matches = len(matched_records)
        paged_records = matched_records[offset: offset + limit]

        return {
            "total": total_matches,
            "offset": offset,
            "limit": limit,
            "returned": len(paged_records),
            "records": paged_records,
        }
