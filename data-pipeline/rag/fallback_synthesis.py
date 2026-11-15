"""
NASA FLAME — Grounded Retrieval-Only Fallback Synthesis (Phase R4 / Modular Refactor)
Constructs a factual, transparent grounded synthesis directly from retrieved records
when generative LLM inference is disabled, unreachable, or falls back.
Directly answers parameter inquiries and guarantees zero synthetic fabrication.
"""

from typing import List, Dict, Any, Optional

from rag.unicode_utils import clean_scientific_unicode
from rag.entity_resolution import DatasetEntityResolver
from rag.measurement_synthesis import (
    is_parameter_inquiry,
    format_stat_summary,
    generate_measurement_audit_synthesis,
)
from rag.comparison_synthesis import generate_comparison_synthesis


def generate_retrieval_only_synthesis(
    question: str,
    evidence_items: List[Dict[str, Any]],
    reason: str = "Gemini API key not configured",
    entity_resolver: Optional[DatasetEntityResolver] = None,
) -> Dict[str, Any]:
    """
    Constructs a factual, transparent grounded synthesis directly from retrieved records
    when generative LLM inference is disabled or unreachable.
    Directly answers parameter inquiries and guarantees zero synthetic fabrication.
    """
    if not evidence_items:
        return {
            "answer": (
                f"**Insufficient Evidence in NASA FLAME Corpus**\n\n"
                f"No experimental records matching the research inquiry *'{question}'* were retrieved from "
                f"the indexed NASA combustion dataset collection (BASS-II, Saffire-III, and Cygnus telemetry).\n\n"
                f"**Scientific Guidance:** Check search terminology, adjust physical property filters, or explore the "
                f"Research-Gap Detection tool to evaluate whether this represents an unexplored partial-gravity regime."
            ),
            "evidence_backed_claims": [],
            "citation_record_ids": [],
            "scientific_limitations": [
                "Query yielded zero candidate records meeting relevance thresholds.",
                "The NASA FLAME corpus currently encompasses BASS-II solid fuels, Saffire-III large-scale flight burns, and Cygnus vehicle telemetry."
            ],
            "relevant_experiment_ids": [],
            "evidence_sufficiency": "insufficient",
            "status": "insufficient_evidence",
        }

    resolver = entity_resolver or DatasetEntityResolver()
    entities = resolver.resolve(question)

    # Intercept parameter inquiries (flame spread rates, extinction times, etc.)
    is_explicit_comparison = any(term in question.lower() for term in ["compare", "comparison", "contrast", "differ", "differences between", "versus", " vs ", " vs."])
    param_inquiry_flag, params = is_parameter_inquiry(question)

    if param_inquiry_flag and not is_explicit_comparison:
        return generate_measurement_audit_synthesis(
            question=question,
            evidence_items=evidence_items,
            entities=entities,
            reason=reason,
        )

    if entities.get("is_comparison", False) or is_explicit_comparison:
        return generate_comparison_synthesis(
            question=question,
            evidence_items=evidence_items,
            entities=entities,
            reason=reason,
        )

    top_recs = evidence_items[:4]
    citations = [r["record_id"] for r in top_recs]
    claims = []
    summary_paragraphs = []

    summary_paragraphs.append(
        f"**NASA FLAME Grounded Scientific Evidence Summary**  \n"
        f"*Operating in Retrieval-Only Mode ({reason}). The empirical findings below are synthesized directly "
        f"from verified NASA experimental records without generative model inference.*"
    )

    unresolved = entities.get("unresolved_requested_entities", [])
    if unresolved:
        summary_paragraphs.append(
            f"> **Notice on Unindexed Experiments:** The research inquiry explicitly requested *'{', '.join(unresolved)}'*, "
            f"which is not present in the indexed NASA FLAME dataset collection (available Saffire flight burns: Sample 1, Sample 2, Sample 5, and Sample 6). "
            f"To maintain scientific integrity, no artificial numbers or unverified surrogate runs have been substituted."
        )

    for idx, item in enumerate(top_recs, start=1):
        rid = item["record_id"]
        title = item.get("title", rid)
        inv = item.get("investigation", "NASA Investigation")
        cond = item.get("experimental_conditions", {})
        stats = item.get("measured_statistics")
        prov = f"{item.get('source_file')}"
        if item.get("source_worksheet"):
            prov += f" (Sheet: {item.get('source_worksheet')}, Row: {item.get('source_excel_row')})"

        fuel = cond.get("fuel_material", "Unspecified fuel substrate")
        o2 = cond.get("oxygen_concentration")
        flow = cond.get("flow_velocity")

        item_text = f"**{idx}. {title}** [{rid}]\n"
        item_text += f"- **Investigation & Provenance:** {inv} • `{prov}`\n"
        item_text += f"- **Fuel & Environment:** {fuel}"
        if o2:
            item_text += f" | Initial O₂: {o2}"
        if flow:
            item_text += f" | Forced Flow: {flow}"
        item_text += "\n"

        if stats:
            stat_desc = format_stat_summary(stats)
            if stat_desc:
                item_text += f"- **Empirical Measurements:** {stat_desc}\n"
                claims.append(f"{title}: {stat_desc} [{rid}]")

        if item.get("quality_warnings"):
            item_text += f"- **Quality Screening Note:** Flagged issue: {'; '.join(item['quality_warnings'])}\n"

        if item.get("missing_fields"):
            item_text += f"- **Missing Metadata:** Explicitly unrecorded: {', '.join(item['missing_fields'])}\n"

        summary_paragraphs.append(item_text)

    limitations = [
        "Retrieval-only mode active: Findings represent direct index extractions without synthetic LLM reasoning.",
        "Empirical observations from individual experiment runs reflect specific microgravity chamber conditions and must not be generalized as flammability certifications.",
        "Flagged readings and glovebox atmospheric residual conditions documented in NASA validation reports must be taken into account."
    ]

    full_answer = clean_scientific_unicode("\n\n".join(summary_paragraphs))
    clean_lims = [clean_scientific_unicode(l) for l in limitations]

    return {
        "answer": full_answer,
        "evidence_backed_claims": claims,
        "citation_record_ids": citations,
        "scientific_limitations": clean_lims,
        "relevant_experiment_ids": [r.get("dataset_id") for r in top_recs if r.get("dataset_id")],
        "evidence_sufficiency": "sufficient" if len(evidence_items) >= 2 else "partial",
        "status": "retrieval_only_fallback",
    }
