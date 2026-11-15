"""
NASA FLAME — Earth Applications RAG Adapter (Phase EA3)
Connects the Grounded Scientific RAG Assistant to the audited Earth Applications evidence catalog.
Enforces:
1. Deterministic evidence ID matching and category/investigation resolution.
2. Separation of raw flight telemetry provenance from terrestrial application validation.
3. Whitelisted citation IDs ([EA-EV-...]) for hallucination detection.
4. Epistemic boundaries prohibiting unsupported commercial adoption claims.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional

from earth_applications.service import EarthApplicationsService
from earth_applications.catalog import INITIAL_EARTH_APPLICATION_CATALOG
from earth_applications.taxonomy import EARTH_APPLICATION_CATEGORIES
from rag.unicode_utils import clean_scientific_unicode, clean_scientific_data

logger = logging.getLogger(__name__)


class EarthApplicationsRAGAdapter:
    """
    Retrieval and grounding adapter for Earth Applications.
    Maps natural-language terrestrial combustion inquiries to audited evidence records.
    """

    def __init__(self, service: Optional[EarthApplicationsService] = None):
        self.service = service or EarthApplicationsService(INITIAL_EARTH_APPLICATION_CATALOG)
        self.catalog = INITIAL_EARTH_APPLICATION_CATALOG

    def is_earth_application_inquiry(
        self,
        question: str,
        evidence_id: Optional[str] = None,
        earth_category: Optional[str] = None,
        investigation_id: Optional[str] = None,
    ) -> bool:
        """
        Determine if the inquiry relates to Earth applications or terrestrial combustion research.
        """
        if evidence_id or earth_category:
            return True

        q_lower = (question or "").lower()

        # Direct ID or finding reference
        if "ea-ev-" in q_lower:
            return True

        # Explicit terrestrial transfer terms
        earth_patterns = [
            r"\b(earth|terrestrial|ground[- ]based)\b",
            r"\b(building|hvac|duct|conduit|shaft|riser)\b",
            r"\b(wildfire|forest|duff|peat|smolder(?:ing)?)\b",
            r"\b(smoke detector|smoke detection|aerosol|agglomerat\w*|photodiode|cleanroom)\b",
            r"\b(flammability|polymer|pyrolysis|pmma|nomex|cotton|sibal)\b",
            r"\b(fire suppression|suppression|extinction|quench\w*|blow-?off|inert gas|ig-55)\b",
            r"\b(emission|soot|gas turbine|cool flame|ntc|hcci|internal combustion)\b",
            r"\b(mine|refuge|industrial hazard|damper|ventilation shutdown)\b",
            r"\b(commercial(?:ly)? adopt\w*|documented adopt\w*|standards? adopt\w*|astm|nfpa|iso 14520)\b",
            r"\b(buoyancy transfer|gravity difference|scale limit|scaling|transfer limit\w*|transfer caveat\w*|transfer physics|buoyancy|1g|normal gravity)\b",
        ]
        return any(re.search(pat, q_lower) for pat in earth_patterns)

    def resolve_earth_evidence(
        self,
        question: str,
        evidence_id: Optional[str] = None,
        earth_category: Optional[str] = None,
        investigation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Deterministically resolve matching Earth Applications evidence records from the audited catalog.
        """
        q_lower = (question or "").lower().strip()
        matched_records = []
        seen_ids = set()

        # 1. Exact Evidence ID Resolution
        target_id = evidence_id
        if not target_id:
            id_match = re.search(r"\b(EA-EV-[A-Z0-9\-]+)\b", question, re.IGNORECASE)
            if id_match:
                target_id = id_match.group(1).upper()

        if target_id:
            ev = self.service.get_evidence_by_id(target_id)
            if ev:
                # Deterministic single-record return for explicit ID inquiry
                return [ev.model_dump() if hasattr(ev, "model_dump") else ev.dict()]
            else:
                # Requested ID does not exist in audited catalog: do NOT fall back to unrelated records
                return []

        # 2. Category Domain Resolution
        target_cat = earth_category
        if not target_cat:
            if re.search(r"\b(building|hvac|duct|conduit)\b", q_lower):
                target_cat = "building_fire_safety"
            elif re.search(r"\b(wildfire|forest|duff|peat)\b", q_lower):
                target_cat = "wildfire_combustion"
            elif re.search(r"\b(detector|detection|smoke|aerosol|agglomerat\w*)\b", q_lower):
                target_cat = "fire_detection_smoke_aerosol"
            elif re.search(r"\b(flammability|polymer|pyrolysis|pmma)\b", q_lower):
                target_cat = "material_flammability_fire_resistance"
            elif re.search(r"\b(suppression|extinction|quench|inert)\b", q_lower):
                target_cat = "fire_suppression_research"
            elif re.search(r"\b(emission|soot|turbine|cool flame|hcci)\b", q_lower):
                target_cat = "combustion_efficiency_emissions"
            elif re.search(r"\b(mine|industrial|damper|containment)\b", q_lower):
                target_cat = "other_terrestrial_applications"

        # 3. Specific Investigation Resolution
        target_inv = investigation_id
        if not target_inv:
            for inv_candidate in ("bass_ii", "saffire_iii", "flex", "same", "acme", "sofie", "cygnus_vehicle_telemetry"):
                if inv_candidate.replace("_", "") in q_lower.replace(" ", "").replace("-", ""):
                    target_inv = inv_candidate
                    break

        # If BOTH category and investigation are resolved, prioritize records matching the intersection!
        if target_cat and target_inv:
            for ev in self.catalog:
                matches_inv = ev.investigation_id == target_inv or target_inv in (ev.related_investigation_ids or [])
                if ev.category_id == target_cat and matches_inv:
                    if ev.id not in seen_ids:
                        matched_records.append(ev.model_dump() if hasattr(ev, "model_dump") else ev.dict())
                        seen_ids.add(ev.id)

        # Then add remaining records for the specific category
        if target_cat:
            cat_res = self.service.list_evidence(category=target_cat)
            for ev_dict in cat_res.get("evidence", []):
                if ev_dict["id"] not in seen_ids:
                    matched_records.append(ev_dict)
                    seen_ids.add(ev_dict["id"])

        # Then add remaining records for the specific investigation
        if target_inv:
            inv_records = self.service.get_evidence_by_investigation(target_inv)
            for ev in inv_records:
                if ev.id not in seen_ids:
                    matched_records.append(ev.model_dump() if hasattr(ev, "model_dump") else ev.dict())
                    seen_ids.add(ev.id)

        # 4. Keyword Scoring Fallback across All 11 Audited Records
        if len(matched_records) < 3:
            scores = []
            tokens = set(re.findall(r"[a-z0-9]+", q_lower))
            # Remove stop words and generic tokens
            tokens.difference_update({
                "what", "which", "how", "does", "can", "is", "are", "the", "and", "or",
                "to", "in", "of", "for", "with", "nasa", "research", "combustion", "flame",
                "experiment", "experiments", "study", "studies", "data", "effects", "effect",
                "microgravity", "gravity", "flight", "space", "iss", "orbit", "orbital",
                "on", "at", "by", "from", "into", "about", "between", "through", "over", "under"
            })

            for ev in self.catalog:
                if ev.id in seen_ids:
                    continue
                score = 0
                searchable = (
                    f"{ev.title} {ev.description} {ev.scientific_finding} "
                    f"{ev.proposed_terrestrial_relevance} {ev.category_title} {ev.investigation_name} "
                    f"{ev.earth_transfer_limitations}"
                ).lower()
                searchable_tokens = set(re.findall(r"[a-z0-9]+", searchable))

                for tok in tokens:
                    if len(tok) >= 3 and tok in searchable_tokens:
                        score += 1
                        if tok in ev.title.lower():
                            score += 2
                        if tok in ev.category_id:
                            score += 2
                        if tok in ev.investigation_id:
                            score += 2

                if score >= 3:
                    scores.append((score, ev.model_dump() if hasattr(ev, "model_dump") else ev.dict()))

            scores.sort(key=lambda x: x[0], reverse=True)
            for _, ev_dict in scores:
                if len(matched_records) >= 3:
                    break
                matched_records.append(ev_dict)
                seen_ids.add(ev_dict["id"])

        # Fallback only for general catalog overview inquiries (e.g. "What terrestrial applications exist?")
        is_overview_inquiry = bool(re.search(
            r"\b(overview|list|all|what (?:terrestrial|earth) applications|catalog|summary|categories)\b",
            q_lower
        ))
        if not matched_records and is_overview_inquiry:
            matched_records = [ev.model_dump() if hasattr(ev, "model_dump") else ev.dict() for ev in self.catalog[:4]]

        return matched_records

    def build_citation_item(self, evidence_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an Earth Application evidence record for inclusion in RAG evidence_citations.
        """
        return {
            "record_id": evidence_dict["id"],
            "record_type": "earth_application_evidence",
            "title": evidence_dict["title"],
            "investigation": evidence_dict["investigation_name"],
            "investigation_id": evidence_dict["investigation_id"],
            "related_investigation_ids": evidence_dict.get("related_investigation_ids", []),
            "category_id": evidence_dict["category_id"],
            "category_title": evidence_dict["category_title"],
            "scientific_finding": evidence_dict["scientific_finding"],
            "proposed_terrestrial_relevance": evidence_dict["proposed_terrestrial_relevance"],
            "source_type": evidence_dict.get("source_type", "flight_experiment_dataset"),
            "source_reference": evidence_dict.get("source_reference", ""),
            "dataset_or_measurement_reference": evidence_dict.get("dataset_or_measurement_reference"),
            "provenance_status": evidence_dict.get("provenance_status", "locally_verified"),
            "evidence_classification": evidence_dict.get("evidence_classification", "supported_research_implication"),
            "validation_status": evidence_dict.get("validation_status", "locally_verified"),
            "confidence_rubric": evidence_dict.get("confidence_rubric", ""),
            "earth_transfer_limitations": evidence_dict.get("earth_transfer_limitations", ""),
            "gravity_buoyancy_ventilation_differences": evidence_dict.get("gravity_buoyancy_ventilation_differences", ""),
        }

    def format_evidence_for_context(self, evidence_items: List[Dict[str, Any]]) -> str:
        """
        Format audited Earth Applications evidence into a structured, anti-injection-safe context block.
        """
        if not evidence_items:
            return ""

        blocks = [
            "=== AUDITED EARTH APPLICATIONS EVIDENCE BEGIN ===\n"
            "INSTRUCTIONS FOR TERRESTRIAL APPLICATION REASONING:\n"
            "1. Ground all terrestrial answers strictly in the audited evidence records below.\n"
            "2. Cite every factual assertion using its exact evidence ID [EA-EV-...].\n"
            "3. Strictly distinguish Dimension A (Flight Grounding) from Dimension B (Terrestrial Validation).\n"
            "4. Adhere to audited classifications: 10 supported implications, 1 exploratory hypothesis, 0 documented applications.\n"
            "5. Never claim commercial gas turbines or automotive engines have adopted ACME or FLEX without published proof.\n"
            "6. Preserve 1g buoyancy updraft caveats (1-2+ m/s) and geometric scale limits (glovebox vs. full scale).\n"
            "7. Saffire detector threshold timing reflects experimental threshold lead (1.65s to 6.60s), not general detector lead.\n"
            "8. Never fabricate percentage probabilities or equipment certification claims.\n"
            "===================================================\n"
        ]

        for ev in evidence_items:
            blocks.append(
                f"[EARTH APPLICATION EVIDENCE: {ev['id']}]\n"
                f"Title: {ev['title']}\n"
                f"Category: {ev['category_title']} ({ev['category_id']})\n"
                f"NASA Investigation: {ev['investigation_name']} ({ev['investigation_id']})\n"
                f"Related Investigations: {', '.join(ev.get('related_investigation_ids', [])) or 'None'}\n"
                f"Dimension A (Flight Grounding): {ev.get('validation_status')} (Provenance: {ev.get('provenance_status')})\n"
                f"Dimension B (Terrestrial Validation): {ev.get('evidence_classification')}\n"
                f"Source Reference: {ev.get('source_reference')}\n"
                f"Dataset/Sensor Reference: {ev.get('dataset_or_measurement_reference') or 'Literature Technical Report'}\n"
                f"Supporting Excerpt: {ev.get('supporting_excerpt')}\n"
                f"Audited Scientific Finding: {ev.get('scientific_finding')}\n"
                f"Proposed Terrestrial Relevance: {ev.get('proposed_terrestrial_relevance')}\n"
                f"Physical Gravity & Buoyancy Differences: {ev.get('gravity_buoyancy_ventilation_differences')}\n"
                f"Earth Transfer Limitations: {ev.get('earth_transfer_limitations')}\n"
                f"Uncertainty Notes: {ev.get('uncertainty_notes') or 'Nominal parameter boundaries'}\n"
                f"Confidence Rubric: {ev.get('confidence_rubric')}\n"
                f"--- END EVIDENCE {ev['id']} ---\n\n"
            )

        blocks.append("=== AUDITED EARTH APPLICATIONS EVIDENCE END ===\n\n")
        return clean_scientific_unicode("".join(blocks))

