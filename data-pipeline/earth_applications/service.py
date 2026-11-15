"""
NASA FLAME — Earth Applications Service (Phase EA1)
Core backend service for querying, filtering, and validating Earth Applications evidence.
Strictly evidence-grounded; enforces non-extrapolation and scientific safety guardrails.
"""

from typing import List, Dict, Any, Optional
from earth_applications.taxonomy import (
    EARTH_APPLICATION_CATEGORIES,
    EVIDENCE_CLASSIFICATION_RUBRIC,
    VALIDATION_STATUS_RUBRIC,
)
from earth_applications.models import (
    EarthApplicationEvidence,
    EarthApplicationCategoryModel,
)
from earth_applications.catalog import INITIAL_EARTH_APPLICATION_CATALOG


class EarthApplicationsService:
    """
    Coordinates Earth Applications evidence retrieval, filtering, and scientific safety verification.
    """

    def __init__(self, catalog: Optional[List[EarthApplicationEvidence]] = None):
        self._catalog = catalog if catalog is not None else INITIAL_EARTH_APPLICATION_CATALOG

    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Return the 7 extensible Earth Application categories with dynamic evidence counts.
        """
        counts = {}
        for ev in self._catalog:
            counts[ev.category_id] = counts.get(ev.category_id, 0) + 1

        result = []
        for cat in EARTH_APPLICATION_CATEGORIES:
            cat_copy = dict(cat)
            cat_copy["evidence_count"] = counts.get(cat["id"], 0)
            result.append(cat_copy)
        return result

    def list_evidence(
        self,
        category: Optional[str] = None,
        classification: Optional[str] = None,
        investigation_id: Optional[str] = None,
        provenance_status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Query and filter Earth Applications evidence records with pagination.
        """
        filtered = self._catalog

        if category:
            cat_lower = category.lower().strip()
            filtered = [e for e in filtered if e.category_id.lower() == cat_lower]

        if classification:
            cls_lower = classification.lower().strip()
            filtered = [e for e in filtered if e.evidence_classification.lower() == cls_lower]

        if investigation_id:
            inv_lower = investigation_id.lower().strip()
            filtered = [
                e for e in filtered
                if e.investigation_id.lower() == inv_lower
                or inv_lower in [r.lower() for r in e.related_investigation_ids]
            ]

        if provenance_status:
            prov_lower = provenance_status.lower().strip()
            filtered = [e for e in filtered if e.provenance_status.lower() == prov_lower]

        total_filtered = len(filtered)
        paged = filtered[offset : offset + limit]

        return {
            "status": "ok",
            "total_count": len(self._catalog),
            "filtered_count": total_filtered,
            "limit": limit,
            "offset": offset,
            "evidence": [e.dict() for e in paged],
        }

    def get_evidence_by_id(self, evidence_id: str) -> Optional[EarthApplicationEvidence]:
        """
        Retrieve a single evidence record by ID.
        """
        ev_id = evidence_id.strip()
        for ev in self._catalog:
            if ev.id.lower() == ev_id.lower():
                return ev
        return None

    def get_evidence_by_investigation(self, investigation_id: str) -> List[EarthApplicationEvidence]:
        """
        Retrieve all evidence records linked to a specific NASA investigation (as primary or related co-investigation).
        """
        inv_lower = investigation_id.lower().strip()
        return [
            e for e in self._catalog
            if e.investigation_id.lower() == inv_lower
            or inv_lower in [r.lower() for r in e.related_investigation_ids]
        ]

    def get_overview(self) -> Dict[str, Any]:
        """
        Return comprehensive overview of Earth Applications capabilities and scientific safeguards.
        Includes full reconciliation of canonical investigation counts (primary vs related co-investigations).
        """
        categories = self.get_categories()
        classification_counts = {}
        provenance_counts = {}

        primary_inv_counts = {}
        total_inv_involvements = {}
        all_unique_invs = set()
        multi_investigation_records = []

        for ev in self._catalog:
            cls = ev.evidence_classification
            classification_counts[cls] = classification_counts.get(cls, 0) + 1
            prov = ev.provenance_status
            provenance_counts[prov] = provenance_counts.get(prov, 0) + 1

            p_inv = ev.investigation_id
            primary_inv_counts[p_inv] = primary_inv_counts.get(p_inv, 0) + 1
            total_inv_involvements[p_inv] = total_inv_involvements.get(p_inv, 0) + 1
            all_unique_invs.add(p_inv)

            if ev.related_investigation_ids:
                multi_investigation_records.append({
                    "evidence_id": ev.id,
                    "title": ev.title,
                    "primary_investigation": ev.investigation_id,
                    "related_investigations": ev.related_investigation_ids,
                })
                for r_inv in ev.related_investigation_ids:
                    total_inv_involvements[r_inv] = total_inv_involvements.get(r_inv, 0) + 1
                    all_unique_invs.add(r_inv)

        return {
            "title": "NASA FLAME — Earth Applications Research Platform (Phase EA1.1 Audited)",
            "subtitle": "Connecting Microgravity Combustion Physics to Terrestrial Fire Safety & Engineering",
            "total_evidence_records": len(self._catalog),
            "categories": categories,
            "classification_breakdown": classification_counts,
            "provenance_breakdown": provenance_counts,
            "investigation_reconciliation": {
                "unique_primary_investigations_count": len(primary_inv_counts),
                "total_unique_investigations_count": len(all_unique_invs),
                "primary_investigation_counts": primary_inv_counts,
                "total_investigation_involvements": total_inv_involvements,
                "multi_investigation_records": multi_investigation_records,
                "canonical_investigations": sorted(list(all_unique_invs)),
            },
            "classification_rubric": EVIDENCE_CLASSIFICATION_RUBRIC,
            "validation_status_rubric": VALIDATION_STATUS_RUBRIC,
            "safeguards": {
                "transfer_disclaimer": (
                    "Microgravity combustion experiments isolate fundamental chemical kinetics and non-buoyant transport. "
                    "They do NOT directly predict macroscopic terrestrial fires where buoyant convective updrafts, ambient wind, "
                    "and large geometric scales dominate. All applications must be validated against terrestrial standards."
                ),
                "no_deployable_equipment_approval": (
                    "NASA FLAME provides scientific decision support and literature research bridges. It does not certify "
                    "or approve commercial fire-safety, wildfire, or suppression equipment for terrestrial deployment."
                ),
                "zero_fabricated_probabilities": (
                    "Evidence confidence is evaluated using qualitative, rubric-based validation standards (locally_verified, "
                    "external_literature_verified, pending_verification). No arbitrary or synthetic percentage probabilities are assigned."
                ),
            },
        }
