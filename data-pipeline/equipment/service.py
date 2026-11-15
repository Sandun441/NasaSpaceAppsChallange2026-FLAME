"""
NASA FLAME — Fire-Safety Equipment Research Service
Coordinates research objective interpretation, RAG knowledge retrieval,
telemetry channel extraction, and research-gap linking.
Strictly separates locally indexed NASA flight datasets from external literature context.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from equipment.taxonomy import (
    FIRE_SAFETY_CATEGORIES,
    VERIFIED_INVESTIGATIONS_REGISTRY,
    QUICK_START_RESEARCH_TEMPLATES,
)
from equipment.analyzer import EquipmentResearchAnalyzer

BASE_DIR = Path(__file__).resolve().parents[1]


class FireSafetyEquipmentService:
    """
    Core backend service for Spacecraft Fire-Safety Equipment Research.
    """

    def __init__(
        self,
        rag_store: Optional[Any] = None,
        gap_detection_service: Optional[Any] = None,
        base_dir: Optional[Path] = None,
    ):
        self.base_dir = base_dir or BASE_DIR
        self.analyzer = EquipmentResearchAnalyzer()
        self.rag_store = rag_store
        self.gap_detection_service = gap_detection_service

    def get_overview(self) -> Dict[str, Any]:
        """
        Return comprehensive overview of Fire-Safety Equipment Research capabilities,
        distinguishing locally indexed flight datasets from external NASA research context.
        """
        local_invs = [inv for inv in VERIFIED_INVESTIGATIONS_REGISTRY.values() if inv.get("is_locally_indexed", True)]
        external_context = [inv for inv in VERIFIED_INVESTIGATIONS_REGISTRY.values() if not inv.get("is_locally_indexed", True)]

        return {
            "title": "NASA FLAME — Fire-Safety Equipment Research Platform",
            "subtitle": "Microgravity Combustion Evidence for Spacecraft Fire Detection, Prevention & Suppression",
            "categories": FIRE_SAFETY_CATEGORIES,
            "quick_start_templates": QUICK_START_RESEARCH_TEMPLATES,
            "cataloged_investigations": local_invs,
            "external_research_context": external_context,
            "total_local_investigations_count": len(local_invs),
            "total_investigations_count": len(local_invs),
            "safeguards": {
                "decision_support_notice": (
                    "NASA FLAME Equipment Research is an evidence-grounded scientific exploration workspace. "
                    "It is designed to inform academic and engineering research, not to replace certified "
                    "spacecraft life-support engineering approvals or NASA-STD-6001 material certifications."
                ),
                "zero_fabrication": (
                    "All sensor channels, physical units, and measurement ranges reflect verified NASA flight "
                    "telemetry records from Saffire, BASS-II, and Cygnus. External literature context (SAME, FLEX) "
                    "is strictly separated from local telemetry."
                ),
            },
        }

    def get_category_details(self, category_id: str) -> Dict[str, Any]:
        """
        Return curated deep-dive information for a specific research category (detection, prevention, suppression).
        """
        cat_meta = next((c for c in FIRE_SAFETY_CATEGORIES if c["id"] == category_id), None)
        if not cat_meta:
            raise ValueError(f"Unknown equipment research category '{category_id}'. Valid: detection, prevention, suppression.")

        # Filter investigations relevant to this category
        relevant_invs = []
        for inv_id, inv in VERIFIED_INVESTIGATIONS_REGISTRY.items():
            if category_id in inv.get("relevance", {}):
                relevant_invs.append({
                    "id": inv["id"],
                    "name": inv["name"],
                    "facility": inv["facility"],
                    "gravity_regime": inv["gravity_regime"],
                    "is_locally_indexed": inv.get("is_locally_indexed", True),
                    "relevance_summary": inv["relevance"][category_id],
                    "verified_channels": [
                        ch for ch in inv.get("verified_sensor_channels", [])
                        if category_id in ch.get("role", "")
                    ],
                })

        # Synthesize baseline insights for this category
        baseline_insights = self.analyzer.interpret(
            query=f"Overview of spacecraft fire {category_id} research in microgravity",
            category_override=category_id,
        )

        return {
            "category_id": category_id,
            "category": cat_meta,
            "relevant_investigations": relevant_invs,
            "scientific_insights": baseline_insights["scientific_insights"],
            "scientific_audit": baseline_insights.get("scientific_audit", {}),
            "linked_research_gaps": baseline_insights["linked_research_gaps"],
            "recommended_actions": baseline_insights["recommended_actions"],
        }

    def interpret_objective(self, query: str, category_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute full natural-language research objective analysis, integrating:
        1. Deterministic category & parameter interpretation
        2. Supporting scientific evidence retrieved from RAG knowledge store
        3. 5-Tier scientific insights & epistemic boundaries
        4. Automated scientific claims audit
        5. Linked findings from Research Gap Detection engine
        6. Actionable dashboard navigation links
        """
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty.")

        # 1. Analyze query
        interpretation = self.analyzer.interpret(query=query.strip(), category_override=category_override)

        # 2. Retrieve supporting evidence from RAG store if available
        retrieved_evidence = []
        if self.rag_store and hasattr(self.rag_store, "search"):
            try:
                results = self.rag_store.search(query.strip(), top_k=5, mode="hybrid")
                for r in results:
                    rec = r.get("record", {})
                    retrieved_evidence.append({
                        "record_id": rec.get("record_id"),
                        "title": rec.get("title"),
                        "record_type": rec.get("record_type"),
                        "dataset_id": rec.get("dataset_id"),
                        "investigation": rec.get("investigation"),
                        "summary": rec.get("summary") or rec.get("abstract", "")[:250],
                        "score": round(float(r.get("score", 0.0)), 3),
                        "citations": rec.get("citations", []),
                    })
            except Exception:
                pass

        interpretation["retrieved_evidence"] = retrieved_evidence

        # 3. Enhance linked research gaps with live gap engine if available
        if self.gap_detection_service and hasattr(self.gap_detection_service, "get_finding_by_id"):
            enhanced_gaps = []
            for g in interpretation["linked_research_gaps"]:
                fid = g["finding_id"]
                live_finding = self.gap_detection_service.get_finding_by_id(fid)
                if live_finding:
                    enhanced_gaps.append({
                        "finding_id": fid,
                        "gap_type": live_finding.get("gap_type"),
                        "title": live_finding.get("title"),
                        "summary": live_finding.get("finding_statement") or g["summary"],
                        "research_priority": live_finding.get("priority_score", g["research_priority"]),
                        "supporting_experiment_ids": live_finding.get("supporting_experiment_ids", []),
                        "action": "open_gap_detection",
                    })
                else:
                    enhanced_gaps.append(g)
            interpretation["linked_research_gaps"] = enhanced_gaps

        return interpretation
