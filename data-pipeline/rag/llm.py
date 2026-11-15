"""
NASA FLAME — Scientific LLM Provider & Grounded Answer Synthesizer (Phase R4)
Provides server-side LLM inference via Google Gemini REST API with bounded exponential-backoff retries,
strict citation & claim validation, prompt-injection defense, and transparent retrieval-only fallback.
"""

from typing import List, Dict, Any, Optional, Tuple, Set, Union
import os
import json
import re
import logging
import urllib.request
import urllib.error
import time
import random

from rag.context import GroundedContextAssembler
from rag.actions import ResearchToolRecommender
from rag.entity_resolution import DatasetEntityResolver
from rag.unicode_utils import clean_scientific_unicode, clean_scientific_data
from rag.earth_adapter import EarthApplicationsRAGAdapter

logger = logging.getLogger("flame.rag.llm")

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_OUTPUT_TOKENS = 2048

from rag.gemini_provider import (
    GeminiProvider,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_MAX_OUTPUT_TOKENS,
)
from rag.scientific_validation import (
    validate_citations,
    validate_scientific_claims,
)
from rag.measurement_synthesis import (
    is_parameter_inquiry,
    format_stat_summary,
    calculate_sensor_channel_counts,
    get_experiment_telemetry_metrics,
    generate_measurement_audit_synthesis,
)
from rag.comparison_synthesis import (
    generate_comparison_synthesis,
)
from rag.gap_synthesis import (
    build_finding_citation_item,
    generate_gap_investigation_synthesis,
)
from rag.earth_synthesis import (
    generate_earth_application_synthesis,
)
from rag.fallback_synthesis import (
    generate_retrieval_only_synthesis,
)
from rag.conversation import (
    is_greeting_inquiry,
    is_out_of_domain_inquiry,
    is_educational_inquiry,
    is_nasa_scientific_query,
    generate_greeting_fallback,
    generate_educational_synthesis,
    parse_llm_json,
    generate_conversational_response,
)


__all__ = [
    "GeminiProvider",
    "GroundedAnswerSynthesizer",
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_MAX_OUTPUT_TOKENS",
]


class GroundedAnswerSynthesizer:
    """
    Orchestrates grounded scientific answer generation, strict citation validation,
    prompt-injection protection, and deterministic retrieval-only fallback.
    """

    def __init__(
        self,
        context_assembler: Optional[GroundedContextAssembler] = None,
        tool_recommender: Optional[ResearchToolRecommender] = None,
        llm_provider: Optional[GeminiProvider] = None,
        entity_resolver: Optional[DatasetEntityResolver] = None,
        earth_adapter: Optional[EarthApplicationsRAGAdapter] = None,
    ):
        self.context_assembler = context_assembler or GroundedContextAssembler()
        self.tool_recommender = tool_recommender or ResearchToolRecommender()
        self.llm_provider = llm_provider or GeminiProvider()
        self.entity_resolver = entity_resolver or DatasetEntityResolver()
        self.earth_adapter = earth_adapter or EarthApplicationsRAGAdapter()

    def _build_system_instruction(
        self,
        finding: Optional[Dict[str, Any]] = None,
        earth_evidence: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    ) -> str:
        """Constructs strict scientific reasoning system prompt with Phase R4 hardening, optional RG4 gap directives, and EA3 terrestrial transfer directives."""
        base_instruction = (
            "You are NASA FLAME Research Intelligence, a specialized scientific AI assistant for NASA microgravity "
            "combustion experiments (BASS-II, Saffire-III, Cygnus telemetry).\n\n"
            "STRICT SCIENTIFIC GROUNDING DIRECTIVES (PHASE R4 HARDENED):\n"
            "1. NEVER equate total file recording duration with flame-burning duration. "
            "In Saffire-III Sample 1, the total 30.3Hz recording duration was 689.96s (20,909 rows), and in Sample 2 it was 159.95s (4,848 rows). "
            "Continuous sensor logging begins prior to igniter activation and persists during post-extinguishment thermal cooldown.\n"
            "2. Distinguish clearly between:\n"
            "   (A) Directly measured observations (e.g. 'Test B6 recorded initial O2 of 21.0% and final O2 of 20.9%')\n"
            "   (B) Experiment metadata (e.g. ignition timeline epoch t = 66.0s, which is an event timestamp, NOT ignition delay)\n"
            "   (C) Qualitative observations and descriptions\n"
            "   (D) Scientific interpretations supported by empirical data\n"
            "   (E) Documented data gaps or uninstrumented variables\n"
            "3. DO NOT imply causal relationships without rigorous supporting measurement evidence.\n"
            "4. NEVER invent or extrapolate numeric values, flame spread rates, extinction times, temperatures, "
            "oxygen concentrations, pressure values, or sensor channels. Thermal data may support post-burn analysis, but exact extinction "
            "identification requires an appropriate validated method and potentially additional observations (e.g. optical video analysis).\n"
            "5. Preserve exact scientific values, decimal precision, and physical units (e.g. °C, mW/cm², psia, cm/s).\n"
            "6. Distinguish nominally similar experimental conditions from proven identical conditions.\n"
            "7. Clearly disclose missing values, quality warnings (e.g. negative/constant channels), and instrument limitations.\n"
            "8. Avoid extrapolating experimental microgravity findings to unrelated conditions or terrestrial flammability standards.\n"
            "9. Cite the specific retrieved records supporting substantive scientific claims in brackets [flame_...] or [EA-EV-...].\n"
            "10. When evidence is insufficient, explicitly state that the available NASA FLAME records cannot establish the answer.\n"
            "11. Do NOT claim that a measurement is absent from all NASA research merely because it is absent from the retrieved evidence.\n"
            "12. NEVER interpret missing metadata or unrecorded channels as proof that a physical event (such as spread or extinction) did not occur.\n\n"
            "CONVERSATIONAL INTELLIGENCE DIRECTIVES:\n"
            "- Greetings: If the researcher sends a greeting (e.g. 'Hi', 'Hello', 'Hey'), respond warmly and professionally as NASA FLAME Research Intelligence, introducing NASA microgravity combustion research and inviting inquiries (BASS-II, Saffire-III, Cygnus telemetry, flame spread, ignition, suppression, research gaps, Earth transfer). Citation list should be empty []. Do NOT report insufficient evidence for pleasantries.\n"
            "- Educational Inquiries: If the researcher asks a fundamental physical definition (e.g. 'What is microgravity?', 'What is buoyancy decoupling?'), explain the governing physics (buoyancy decoupling, spherical flame geometry, diffusion vs forced flow) clearly and concisely. Do NOT invent flight experiments or force citations into basic definitions.\n"
            "- Out-of-Domain: If the query is unrelated to spaceflight combustion, fire safety, or physics, politely and transparently acknowledge domain boundaries and redirect to microgravity combustion science.\n"
            "- Follow-up Inquiries: If the query is a follow-up referring to previous turns (e.g. 'Can you compare those experiments?'), use the provided conversation history to resolve pronouns and answer coherently in context.\n\n"
            "STRUCTURED COMPARISON REQUIREMENTS:\n"
            "If the query asks to compare, contrast, or evaluate differences between experiments, samples, or materials (e.g. Saffire Sample 1 vs Sample 2), "
            "you MUST structure your answer into clear scientific sections:\n"
            "- Section 1: Experiment Identities & Test Objectives\n"
            "- Section 2: Fuel Materials & Environmental Conditions (Markdown matrix table)\n"
            "- Section 3: Available Measurement Channels & Physical Units\n"
            "- Section 4: Verified Differences and Similarities\n"
            "- Section 5: Data-Quality Screening & Uninstrumented Parameters\n"
            "- Section 6: Provenance & Citations [flame_...]\n"
            "NEVER fabricate missing values or extrapolate unmeasured channels."
        )

        if finding:
            fid = finding.get("finding_id", "GAP-UNKNOWN")
            base_instruction += (
                f"\n\nSPECIAL DIRECTIVE FOR RESEARCH GAP FINDING [{fid}]:\n"
                f"You are investigating an authoritative, deterministic research gap finding from the Phase RG2 engine.\n"
                f"1. The deterministic finding from Phase RG2 is immutable ground truth. You must never contradict, alter, or fabricate finding metrics (priority score, evidence confidence, or denominator).\n"
                f"2. You MUST structure your answer into five distinct scientific sections:\n"
                f"   - Section 1: Verified Experimental Observations in FLAME\n"
                f"   - Section 2: Deterministic Database Gap Analysis (Phase RG2 Engine)\n"
                f"   - Section 3: Scientific Interpretation & Exploration Mission Significance\n"
                f"   - Section 4: Actionable Next Steps & Proposed Future Research\n"
                f"   - Section 5: Epistemic Boundary Notice & Missing Information Disclosure\n"
                f"3. Cite the finding [{fid}] and any retrieved records [flame_...] in brackets.\n"
                f"4. Never claim that missing coverage in FLAME proves a global scientific research gap or that NASA never conducted research elsewhere."
            )

        if earth_evidence:
            ev_list = [earth_evidence] if isinstance(earth_evidence, dict) else (earth_evidence or [])
            ev_ids = [e.get("id", "") for e in ev_list if e.get("id")]
            ids_str = ", ".join(f"[{i}]" for i in ev_ids)
            base_instruction += (
                f"\n\nSPECIAL DIRECTIVE FOR EARTH APPLICATIONS & TERRESTRIAL TRANSFER {ids_str}:\n"
                f"You are synthesizing terrestrial combustion research implications from NASA microgravity flight evidence.\n"
                f"1. Strictly adhere to verified experimental observations in cited records {ids_str}. Do not fabricate measurements, materials, or testing conditions.\n"
                f"2. Maintain strict distinction between Dimension A (Flight Grounding) and Dimension B (Terrestrial Validation). As audited, the catalog contains 10 supported research implications, 1 exploratory hypothesis, and ZERO documented commercial applications. If asked about commercial adoption, explicitly state there are zero verified commercial adoptions in the catalog.\n"
                f"3. Never claim certified safety code compliance, equipment deployment approvals, or fabricated performance gains (e.g., 15-20% efficiency, 43s lead time).\n"
                f"4. Clearly articulate physical transfer barriers: buoyant body force re-coupling in 1g governed by Richardson number (Ri = Gr/Re²: Ri >> 1 in low-speed/buoyant plumes vs. Ri << 1 in high-speed forced flows), Froude disparities, turbulent plume formation, and scale differences.\n"
                f"5. Cite the evidence records in brackets, e.g. [EA-EV-BASS-PYRO-01]."
            )

        example_cits = '["flame_..."'
        if finding:
            example_cits += f', "{finding.get("finding_id", "")}"'
        if earth_evidence:
            ev_list = [earth_evidence] if isinstance(earth_evidence, dict) else (earth_evidence or [])
            if ev_list:
                example_cits += f', "{ev_list[0].get("id", "")}"'
        example_cits += ']'

        base_instruction += (
            "\n\nOUTPUT FORMAT: You must reply with a valid JSON object matching this schema:\n"
            "{\n"
            '  "answer": "Detailed, rigorous scientific response with bracketed citations [flame_...] and/or [EA-EV-...].",\n'
            '  "evidence_backed_claims": ["Specific empirical assertion 1 [flame_...]", "Assertion 2 [EA-EV-...]"],\n'
            f'  "citation_record_ids": {example_cits},\n'
            '  "scientific_limitations": ["Limitation or scope caveat 1", "Caveat 2"],\n'
            '  "relevant_experiment_ids": ["bass_ii_b6", "saffire_iii_sample_1"],\n'
            '  "evidence_sufficiency": "sufficient | partial | insufficient"\n'
            "}"
        )
        return base_instruction

    def _validate_citations(
        self,
        raw_citations: List[str],
        allowed_ids: List[str],
        answer_text: str,
    ) -> Tuple[List[str], List[str]]:
        """
        Validates that all cited IDs exist in the retrieved evidence pool.
        Purges hallucinated citation IDs and extracts cited IDs from text.
        """
        return validate_citations(raw_citations, allowed_ids, answer_text)

    def _validate_scientific_claims(
        self,
        answer_text: str,
        retrieved_candidates: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic scientific claim validation verifying that generated statements
        adhere to physical facts in the retrieved NASA FLAME corpus.
        """
        return validate_scientific_claims(answer_text, retrieved_candidates)

    def _is_parameter_inquiry(self, question: str) -> Tuple[bool, List[str]]:
        return is_parameter_inquiry(question)

    def _format_stat_summary(self, stat: Optional[Dict[str, Any]]) -> Optional[str]:
        return format_stat_summary(stat)

    def _calculate_sensor_channel_counts(self, channels_and_units: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
        return calculate_sensor_channel_counts(channels_and_units)

    def _get_experiment_telemetry_metrics(self, rec: Dict[str, Any], evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        return get_experiment_telemetry_metrics(rec, evidence_items)

    def _generate_measurement_audit_synthesis(
        self,
        question: str,
        evidence_items: List[Dict[str, Any]],
        entities: Dict[str, Any],
        reason: str = "Retrieval-only parameter inquiry audit",
    ) -> Dict[str, Any]:
        return generate_measurement_audit_synthesis(
            question=question,
            evidence_items=evidence_items,
            entities=entities,
            reason=reason,
        )

    def _generate_comparison_synthesis(
        self,
        question: str,
        evidence_items: List[Dict[str, Any]],
        entities: Dict[str, Any],
        reason: str,
    ) -> Dict[str, Any]:
        return generate_comparison_synthesis(
            question=question,
            evidence_items=evidence_items,
            entities=entities,
            reason=reason,
        )

    def _generate_gap_investigation_synthesis(
        self,
        finding: Dict[str, Any],
        question: str,
        evidence_items: List[Dict[str, Any]],
        reason: str = "Retrieval-only scientific gap investigation",
    ) -> Dict[str, Any]:
        return generate_gap_investigation_synthesis(
            finding=finding,
            question=question,
            evidence_items=evidence_items,
            reason=reason,
        )

    def _generate_earth_application_synthesis(
        self,
        question: str,
        earth_items: List[Dict[str, Any]],
        retrieved_candidates: List[Dict[str, Any]] = None,
        reason: str = "Retrieval-only terrestrial synthesis",
    ) -> Dict[str, Any]:
        return generate_earth_application_synthesis(
            question=question,
            earth_items=earth_items,
            retrieved_candidates=retrieved_candidates,
            reason=reason,
        )

    def _generate_retrieval_only_synthesis(
        self,
        question: str,
        evidence_items: List[Dict[str, Any]],
        reason: str = "Gemini API key not configured",
    ) -> Dict[str, Any]:
        return generate_retrieval_only_synthesis(
            question=question,
            evidence_items=evidence_items,
            reason=reason,
            entity_resolver=self.entity_resolver,
        )

    def _build_finding_citation_item(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        return build_finding_citation_item(finding)

    def _is_greeting_inquiry(self, q_lower: str) -> bool:
        return is_greeting_inquiry(q_lower)

    def _is_out_of_domain_inquiry(self, q_lower: str) -> bool:
        return is_out_of_domain_inquiry(q_lower)

    def _is_educational_inquiry(
        self,
        q_lower: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> bool:
        return is_educational_inquiry(q_lower, conversation_history)

    def _is_nasa_scientific_query(
        self,
        question: str,
        finding_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        earth_category: Optional[str] = None,
        investigation_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        return is_nasa_scientific_query(
            question=question,
            finding_id=finding_id,
            evidence_id=evidence_id,
            earth_category=earth_category,
            investigation_id=investigation_id,
            conversation_history=conversation_history,
        )

    def _generate_greeting_fallback(
        self,
        question: str,
        reason: str = "Deterministic greeting fallback",
        status_code: Optional[int] = None,
        retries: int = 0,
    ) -> Dict[str, Any]:
        return generate_greeting_fallback(
            question=question,
            llm_provider=self.llm_provider,
            reason=reason,
            status_code=status_code,
            retries=retries,
        )

    def _generate_educational_synthesis(
        self,
        question: str,
        reason: str = "Deterministic educational fallback",
        status_code: Optional[int] = None,
        retries: int = 0,
    ) -> Dict[str, Any]:
        return generate_educational_synthesis(
            question=question,
            llm_provider=self.llm_provider,
            reason=reason,
            status_code=status_code,
            retries=retries,
        )

    @staticmethod
    def _parse_llm_json(raw_text: str) -> Dict[str, Any]:
        return parse_llm_json(raw_text)

    def _generate_conversational_response(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        mode: str = "greeting",
    ) -> Dict[str, Any]:
        return generate_conversational_response(
            question=question,
            llm_provider=self.llm_provider,
            conversation_history=conversation_history,
            mode=mode,
        )

    def answer(
        self,
        question: str,
        retrieved_candidates: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        finding: Optional[Dict[str, Any]] = None,
        earth_evidence: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    ) -> Dict[str, Any]:
        """
        Master answer synthesis pipeline:
        1. Context assembly & token budgeting (including deterministic gap findings and earth applications if present).
        2. Tool recommendations based on research intent, active finding, or terrestrial evidence.
        3. Generative inference via Gemini with bounded backoff retries.
        4. Citation verification against candidate pool.
        5. Deterministic scientific claim validation (combustion vs logging duration, timestamps vs delays, etc.).
        6. Transparent retrieval-only fallback if unconfigured or failed.
        """
        clean_q = question.strip()
        q_lower = clean_q.lower()

        # Step 0A: Check for greeting / conversational check-in
        if self._is_greeting_inquiry(q_lower):
            return self._generate_conversational_response(
                question=clean_q,
                conversation_history=conversation_history,
                mode="greeting"
            )

        # Step 0B: Check for educational concept inquiry
        if self._is_educational_inquiry(q_lower, conversation_history):
            return self._generate_conversational_response(
                question=clean_q,
                conversation_history=conversation_history,
                mode="educational"
            )

        # Step 0C: Check for general conversation or out-of-domain inquiry
        if self._is_out_of_domain_inquiry(q_lower) or not self._is_nasa_scientific_query(
            question=clean_q,
            finding_id=finding.get("finding_id") if finding else None,
            evidence_id=(earth_evidence[0].get("id") if isinstance(earth_evidence, list) and earth_evidence else (earth_evidence.get("id") if isinstance(earth_evidence, dict) else None)),
            conversation_history=conversation_history,
        ):
            return self._generate_conversational_response(
                question=clean_q,
                conversation_history=conversation_history,
                mode="general"
            )

        # Step 1: Assemble grounded context
        context_data = self.context_assembler.assemble(
            retrieved_records=retrieved_candidates,
            research_question=clean_q,
            finding=finding,
            earth_evidence=earth_evidence,
        )

        structured_evidence = context_data["structured_evidence"]
        allowed_ids = context_data["allowed_citation_ids"]

        # Step 2: Recommend research tools
        suggested_actions = self.tool_recommender.recommend(
            question=clean_q,
            retrieved_evidence=structured_evidence,
            finding=finding,
            earth_evidence=earth_evidence,
            conversation_history=conversation_history,
        )

        # Collect quality warnings across all retrieved evidence
        all_quality_warnings = []
        for e in structured_evidence:
            for w in e.get("quality_warnings", []):
                if w not in all_quality_warnings:
                    all_quality_warnings.append(w)

        # Step 3: Check if LLM inference is available
        if not self.llm_provider.is_configured:
            res_obj = {
                "question": clean_q,
                "answer": None,
                "evidence_citations": [],
                "relevant_records": structured_evidence,
                "quality_warnings": all_quality_warnings,
                "scientific_limitations": ["Gemini AI model is not configured."],
                "suggested_actions": suggested_actions,
                "retrieval_mode": "ai_unavailable",
                "status": "ai_unavailable",
                "error_code": "GEMINI_UNAVAILABLE",
                "error_message": "FLAME AI is temporarily unavailable. Please configure GEMINI_API_KEY.",
                "retryable": False,
                "evidence_sufficiency": "insufficient",
                "claim_validation": {"validated": False, "discrepancies": []},
                "llm_provider_status": {
                    "is_configured": False,
                    "provider": "google-gemini",
                    "model": self.llm_provider.model_name,
                    "status": "error",
                    "reason": "GEMINI_API_KEY environment variable not configured",
                    "status_code": 401,
                    "retries_attempted": 0,
                }
            }
            if finding:
                res_obj["finding"] = finding
                res_obj["finding_id"] = finding.get("finding_id")
            if earth_evidence is not None:
                res_obj["earth_evidence"] = earth_evidence
                ev_list = [earth_evidence] if isinstance(earth_evidence, dict) else (earth_evidence or [])
                if ev_list:
                    res_obj["earth_evidence_id"] = ev_list[0].get("id")
            return res_obj

        # Step 4: Execute LLM generation
        system_prompt = self._build_system_instruction(finding=finding, earth_evidence=earth_evidence)
        conv_context = ""
        if conversation_history:
            recent_turns = conversation_history[-4:]
            turn_lines = []
            for t in recent_turns:
                r = "Researcher" if t.get("role") == "user" else "Assistant"
                turn_lines.append(f"{r}: {t.get('content', '')[:300]}")
            if turn_lines:
                conv_context = "CONVERSATION HISTORY:\n" + "\n".join(turn_lines) + "\n\n"

        user_prompt = f"{conv_context}RESEARCH QUESTION: {clean_q}\n\n{context_data['assembled_text']}"

        llm_response = self.llm_provider.generate(
            system_instruction=system_prompt,
            user_prompt=user_prompt,
        )

        if not llm_response["success"]:
            logger.warning("LLM generation failed: %s; returning ai_unavailable status", llm_response.get("error"))
            status_code = llm_response.get("status_code", 0)
            retryable = status_code in (429, 500, 502, 503, 504)
            res_obj = {
                "question": clean_q,
                "answer": None,
                "evidence_citations": [],
                "relevant_records": structured_evidence,
                "quality_warnings": all_quality_warnings,
                "scientific_limitations": [f"Gemini API error: {llm_response.get('error', 'Service unavailable')}"],
                "suggested_actions": suggested_actions,
                "retrieval_mode": "ai_unavailable",
                "status": "ai_unavailable",
                "error_code": "GEMINI_API_ERROR",
                "error_message": f"FLAME AI is temporarily unavailable: {llm_response.get('error', 'API error')}",
                "retryable": retryable,
                "evidence_sufficiency": "insufficient",
                "claim_validation": {"validated": False, "discrepancies": []},
                "llm_provider_status": {
                    "is_configured": True,
                    "provider": "google-gemini",
                    "model": self.llm_provider.model_name,
                    "status": "error",
                    "reason": llm_response.get("error"),
                    "status_code": status_code,
                    "retries_attempted": llm_response.get("retries_attempted", 0),
                }
            }
            if finding:
                res_obj["finding"] = finding
                res_obj["finding_id"] = finding.get("finding_id")
            if earth_evidence is not None:
                res_obj["earth_evidence"] = earth_evidence
                ev_list = [earth_evidence] if isinstance(earth_evidence, dict) else (earth_evidence or [])
                if ev_list:
                    res_obj["earth_evidence_id"] = ev_list[0].get("id")
            return res_obj

        # Step 5: Parse and validate structured output
        raw_text = llm_response.get("raw_text", "")
        parsed_json = self._parse_llm_json(raw_text)
        answer_text = parsed_json.get("answer", raw_text)
        claims = parsed_json.get("evidence_backed_claims", [])
        raw_citations = parsed_json.get("citation_record_ids", [])
        limitations = parsed_json.get("scientific_limitations", [])

        if not parsed_json:
            logger.warning("Failed to parse JSON response from LLM. Using raw text fallback.")
            limitations.append("Generated answer could not be verified against structured schema.")

        # Step 6: Validate citations against candidate pool
        valid_citations, invalid_citations = self._validate_citations(
            raw_citations=raw_citations,
            allowed_ids=allowed_ids,
            answer_text=answer_text,
        )

        if invalid_citations:
            logger.warning("Purged %d hallucinated citations: %s", len(invalid_citations), invalid_citations)
            limitations.append(f"Purged {len(invalid_citations)} unverified citation references.")

        evidence_sufficiency = "sufficient"
        status_val = "grounded_llm_answer"
        if not valid_citations:
            logger.warning("LLM provided no verifiable citations; retaining Gemini answer with epistemic caveat")
            limitations.append("Generated citations could not be verified against retrieved NASA flight records.")
            evidence_sufficiency = "insufficient"
            status_val = "insufficient_evidence"
        elif invalid_citations:
            evidence_sufficiency = "partial"

        # Step 7: Deterministic scientific claim validation
        claim_validation = self._validate_scientific_claims(
            answer_text=answer_text,
            retrieved_candidates=structured_evidence,
        )

        if not claim_validation["is_valid"]:
            for warn in claim_validation["warnings"]:
                if warn not in limitations:
                    limitations.append(warn)
            if claim_validation["corrections"]:
                corr_block = "\n\n> **Scientific Quality Notice:** " + " ".join(claim_validation["corrections"])
                answer_text += corr_block

        clean_ans = clean_scientific_unicode(answer_text)
        clean_lims = [clean_scientific_unicode(l) for l in limitations]
        citation_evidence = clean_scientific_data([e for e in structured_evidence if e["record_id"] in valid_citations])
        if finding and finding.get("finding_id") in valid_citations:
            citation_evidence.insert(0, self._build_finding_citation_item(finding))
        if earth_evidence:
            ev_list = [earth_evidence] if isinstance(earth_evidence, dict) else (earth_evidence or [])
            for ev in reversed(ev_list):
                if ev.get("id") in valid_citations:
                    citation_evidence.insert(0, self.earth_adapter.build_citation_item(ev))

        res_obj = {
            "question": clean_q,
            "answer": clean_ans,
            "evidence_citations": citation_evidence,
            "relevant_records": structured_evidence,
            "quality_warnings": all_quality_warnings,
            "scientific_limitations": clean_lims,
            "suggested_actions": suggested_actions,
            "retrieval_mode": "grounded_llm_answer",
            "status": status_val,
            "evidence_sufficiency": evidence_sufficiency,
            "claim_validation": claim_validation,
            "llm_provider_status": {
                "is_configured": True,
                "provider": "google-gemini",
                "model": self.llm_provider.model_name,
                "status": "success",
                "citations_validated": len(valid_citations),
                "citations_purged": len(invalid_citations),
                "retries_attempted": llm_response.get("retries_attempted", 0),
            }
        }
        if finding:
            res_obj["finding"] = finding
        if earth_evidence:
            res_obj["earth_evidence"] = earth_evidence
            ev_list = [earth_evidence] if isinstance(earth_evidence, dict) else (earth_evidence or [])
            if ev_list:
                res_obj["earth_evidence_id"] = ev_list[0].get("id")
        return res_obj
