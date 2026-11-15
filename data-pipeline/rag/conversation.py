"""
NASA FLAME — Conversational Intelligence & Routing (Phase R4 / Modular Refactor)
Handles greetings, pleasantries, out-of-domain inquiries, educational definitions,
and robust JSON parsing for conversational LLM interactions.
"""

from typing import List, Dict, Any, Optional
import json
import re
import logging

from rag.unicode_utils import clean_scientific_unicode

logger = logging.getLogger("flame.rag.conversation")


def is_greeting_inquiry(q_lower: str) -> bool:
    """
    Identifies conversational greetings, pleasantries, identity inquiries, and general capability requests.
    Excludes queries with explicit empirical scientific keywords.
    """
    clean = q_lower.strip()
    # Direct short greetings
    if re.match(r"^(hi|hello|hey|greetings|howdy|good\s+(morning|afternoon|evening|day))(\s*[!?.])*$", clean):
        return True

    # Conversational questions: "how are you", "how are you doing", "who are you", "what can you do", "can you help me..."
    conv_patterns = [
        r"^\s*(hi|hello|hey|greetings|howdy)\b",
        r"^\s*good\s+(morning|afternoon|evening)\b",
        r"\bhow\s+are\s+you\b",
        r"\bhow\s+(are\s+)?you\s+doing\b",
        r"\bhow('s|s)\s+it\s+going\b",
        r"\bwho\s+are\s+you\b",
        r"\bwhat\s+(is\s+your\s+name|are\s+you)\b",
        r"\bwhat\s+can\s+you\s+do\b",
        r"\b(can|could|will)\s+you\s+help\s+me(\s+study(\s+microgravity)?)?\b",
        r"^\s*(thanks|thank\s+you|bye|goodbye)\b",
    ]
    if not any(re.search(p, clean) for p in conv_patterns):
        return False

    # Exclude empirical research inquiries that mention specific tests, datasets, or measurements
    empirical_keywords = [
        "saffire", "bass", "cygnus", "sample 1", "sample 2", "sample 5", "sample 6",
        "thermocouple", "radiometer", "ignition delay", "flame spread rate", "extinction",
        "burn duration", "sensor", "telemetry", "pressure psia", "flow_velocity", "pmma", "nomex"
    ]
    return not any(k in clean for k in empirical_keywords)


def is_out_of_domain_inquiry(q_lower: str) -> bool:
    """Identifies queries outside combustion, aerospace, and physical science."""
    out_of_domain_topics = [
        "capital of", "president of", "population of", "weather in", "movie", "song",
        "recipe for", "football", "soccer", "basketball", "olympics", "who won the",
        "stock price", "crypto", "bitcoin", "write a poem about", "tell me a joke"
    ]
    is_out = any(t in q_lower for t in out_of_domain_topics)
    is_scientific = any(
        k in q_lower for k in ["saffire", "bass", "flame", "burn", "spread", "oxygen", "temperature", "ignit", "smoke", "gap", "earth", "gravity"]
    )
    return is_out and not is_scientific


def is_nasa_scientific_query(
    question: str,
    finding_id: Optional[str] = None,
    evidence_id: Optional[str] = None,
    earth_category: Optional[str] = None,
    investigation_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """
    Determines whether an inquiry requires NASA scientific retrieval
    (mentioning NASA missions, experiments, telemetry, parameters, research gaps, or Earth applications)
    or is general conversation (greetings, pleasantries, general knowledge, conceptual physics definitions).
    """
    if finding_id or evidence_id or earth_category or (investigation_id and investigation_id in ("bass_ii", "saffire_iii")):
        return True

    q_lower = (question or "").lower().strip()
    if not q_lower:
        return False

    if is_greeting_inquiry(q_lower):
        return False

    if is_educational_inquiry(q_lower, conversation_history):
        return False

    if is_out_of_domain_inquiry(q_lower):
        return False

    # Check for explicit scientific record / evidence / gap identifiers
    if re.search(r"\b(ea-ev|gap-|flame_)[a-z0-9_-]*\b", q_lower):
        return True

    # Check for empirical NASA keywords
    empirical_keywords = [
        "saffire", "bass", "cygnus", "sample 1", "sample 2", "sample 3", "sample 4", "sample 5", "sample 6",
        "b6", "narrow channel", "glovebox", "pmma", "nomex", "cotton", "fiberglass",
        "thermocouple", "radiometer", "ignition delay", "flame spread", "extinction",
        "quench", "burn duration", "sensor", "telemetry", "pressure psia", "flow_velocity",
        "oxygen concentration", "o2", "soot", "heat flux", "radiation",
        "research gap", "lunar gravity", "martian gravity", "partial gravity",
        "terrestrial transfer", "terrestrial", "building safety", "smoke detector", "smoke detection", "obscuration",
        "flammability envelope", "froude", "richardson", "buoyancy decoupling",
        "wildfire", "pyrolysis", "commercial adoption", "earth application"
    ]
    if any(k in q_lower for k in empirical_keywords):
        return True

    # Check conversation history for empirical context if this is a follow-up
    if conversation_history and re.search(r"\b(compare|contrast|those|them|these|sample|telemetry|sensor|chart|plot|visualiz\w*)\b", q_lower):
        history_text = " ".join([m.get("content", "") for m in conversation_history if isinstance(m.get("content"), str)]).lower()
        if any(k in history_text for k in ["saffire", "bass", "sample 1", "sample 2", "cygnus", "pmma", "nomex"]):
            return True

    # General combustion/fire/space physics keywords
    science_keywords = [
        "microgravity", "combustion", "flame", "fire", "burn", "oxidizer", "ignition", "spacecraft",
        "iss", "zero gravity", "low gravity"
    ]
    if any(k in q_lower for k in science_keywords):
        return True

    return False


def is_educational_inquiry(
    q_lower: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> bool:
    """
    Identifies general educational/concept definitions and conversational simplification requests.
    Excludes empirical inquiries demanding specific flight dataset measurements.
    """
    clean = q_lower.strip()

    # Concept definitions
    concept_patterns = [
        r"^\s*(what\s+is|what\s+are|define|meaning\s+of|explain\s+the\s+concept\s+of)\s+(microgravity|buoyancy|buoyant\s+convection|buoyancy\s+decoupling|diffusion|diffusion\s+flame|froude\s+number|richardson\s+number|flammability)\b",
        r"^\s*why\s+(do|are)\s+flames\s+(spherical|round)\s+in\s+space\b",
        r"^\s*explain\s+(microgravity|buoyancy|buoyant\s+convection|buoyancy\s+decoupling)\b",
    ]
    if any(re.search(p, clean) for p in concept_patterns):
        empirical_keywords = [
            "saffire", "bass", "cygnus", "sample 1", "sample 2", "sample 5", "sample 6",
            "thermocouple", "radiometer", "ignition delay", "flame spread rate", "extinction",
            "telemetry", "dataset"
        ]
        return not any(k in clean for k in empirical_keywords)

    # Conversational simplification follow-ups
    simplification_patterns = [
        r"\b(explain\s+(it\s+)?(more\s+)?simply|make\s+it\s+simpler|simplify(\s+that)?|in\s+simpler\s+terms|eli5|explain\s+like\s+i('m|\s+am)\s+5|break\s+that\s+down)\b"
    ]
    if any(re.search(p, clean) for p in simplification_patterns):
        return True

    return False


def generate_greeting_fallback(
    question: str,
    llm_provider: Any = None,
    reason: str = "Deterministic greeting fallback",
    status_code: Optional[int] = None,
    retries: int = 0,
) -> Dict[str, Any]:
    """Delivers deterministic greeting fallback with honest provider reporting."""
    is_conf = getattr(llm_provider, "is_configured", False) if llm_provider else False
    model = getattr(llm_provider, "model_name", "gemini-3.5-flash-lite") if llm_provider else "gemini-3.5-flash-lite"
    return {
        "question": question,
        "answer": (
            "Hello! I am NASA FLAME Research Intelligence, an AI research assistant specializing in NASA microgravity "
            "combustion experiments (including BASS-II narrow channel tests, Saffire-III large-scale flight burns, and Cygnus telemetry).\n\n"
            "I can help you explore flame spread dynamics, fuel flammability envelopes across BASS-II and Saffire-III, "
            "ignition telemetry, spacecraft smoke detection, research gaps in partial gravity, and terrestrial fire safety transfer.\n\n"
            "What research question or experiment would you like to investigate?"
        ),
        "evidence_citations": [],
        "relevant_records": [],
        "quality_warnings": [],
        "scientific_limitations": [],
        "suggested_actions": [],
        "retrieval_mode": "conversational_fallback",
        "status": "success",
        "evidence_sufficiency": "sufficient",
        "claim_validation": {"validated": True, "discrepancies": []},
        "llm_provider_status": {
            "is_configured": is_conf,
            "provider": "deterministic-conversational-fallback",
            "model": model,
            "status": "fallback",
            "reason": reason,
            "status_code": status_code,
            "retries_attempted": retries,
        }
    }


def generate_educational_synthesis(
    question: str,
    llm_provider: Any = None,
    reason: str = "Deterministic educational fallback",
    status_code: Optional[int] = None,
    retries: int = 0,
) -> Dict[str, Any]:
    """Delivers deterministic educational fallback with honest provider reporting."""
    is_conf = getattr(llm_provider, "is_configured", False) if llm_provider else False
    model = getattr(llm_provider, "model_name", "gemini-3.5-flash-lite") if llm_provider else "gemini-3.5-flash-lite"
    q_lower = question.lower()
    if "microgravity" in q_lower:
        ans = (
            "**Microgravity and Its Effect on Combustion**\n\n"
            "**Microgravity** (often denoted as $\\mu g$ or $\\sim 10^{-6} g$) is an environment of apparent weightlessness "
            "where gravitational acceleration is balanced by continuous freefall, such as in low Earth orbit aboard the International Space Station (ISS).\n\n"
            "**Key Physical Effects on Fire Behavior:**\n"
            "- **Buoyancy Decoupling:** In normal Earth gravity ($1g$), density differences caused by heat generate buoyant updrafts (hot gases rise, drawing fresh oxidizer into the flame base). In microgravity, natural buoyant convective flows are effectively eliminated ($u_b \\approx 0$).\n"
            "- **Diffusion Domination:** Quiescent flames in microgravity become rounded, spherical, and symmetric, governed primarily by molecular diffusion rather than turbulent buoyant plumes.\n"
            "- **Forced Flow Sensitivity:** Because natural drafts vanish, forced air flows (even subtle ventilation velocities of 0.5–20 cm/s, as investigated in BASS-II and Saffire) dictate oxidizer transport, soot accumulation, and flame propagation rates.\n\n"
            "*In the NASA FLAME platform, you can investigate quantitative flight telemetry from 129 BASS-II glovebox runs and large-scale Saffire burns examining these principles.*"
        )
    else:
        ans = (
            f"**Physical Principle Explanation: {question}**\n\n"
            "In microgravity combustion research, physical processes such as buoyancy-driven convection, oxidizer diffusion, "
            "and soot radiation behave fundamentally differently than in 1g terrestrial environments. Without buoyant updrafts, "
            "combustion is governed by forced low-speed airflow and molecular transport.\n\n"
            "To examine specific experimental measurements, ask about NASA flight datasets such as BASS-II (narrow channel PMMA/cotton) "
            "or Saffire-III (large-scale vehicle burns)."
        )
    return {
        "question": question,
        "answer": ans,
        "evidence_citations": [],
        "relevant_records": [],
        "quality_warnings": [],
        "scientific_limitations": [
            "General scientific definition explaining physical principles; consult indexed flight telemetry for empirical measurements."
        ],
        "suggested_actions": [],
        "retrieval_mode": "educational_fallback",
        "status": "success",
        "evidence_sufficiency": "sufficient",
        "claim_validation": {"validated": True, "discrepancies": []},
        "llm_provider_status": {
            "is_configured": is_conf,
            "provider": "deterministic-educational-fallback",
            "model": model,
            "status": "fallback",
            "reason": reason,
            "status_code": status_code,
            "retries_attempted": retries,
        }
    }


def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Robust parser for LLM JSON output with markdown stripping, LaTeX escape recovery, and field fallback."""
    if not raw_text or not raw_text.strip():
        return {}
    clean = raw_text.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    clean = clean.strip()

    # 1. Direct parse
    try:
        return json.loads(clean, strict=False)
    except Exception:
        pass

    # 2. Fix unescaped LaTeX backslashes (e.g. \mu, \approx, \text, \sim, \times)
    fixed = re.sub(r'\\(?![/"\\bfnrtu])', r'\\\\', clean)
    try:
        return json.loads(fixed, strict=False)
    except Exception:
        pass

    # 3. Regex JSON block extraction
    try:
        match = re.search(r"(\{.*\})", fixed, re.DOTALL)
        if match:
            return json.loads(match.group(1), strict=False)
    except Exception:
        pass

    # 4. Fallback regex extraction for answer and citations
    res = {}
    ans_m = re.search(r'"answer"\s*:\s*"(.*?)(?:"\s*,\s*"[a-zA-Z_]+"|\s*"\s*\})', clean, re.DOTALL)
    if ans_m:
        res["answer"] = ans_m.group(1).replace(r'\"', '"').replace(r'\n', '\n')
    cits_m = re.search(r'"citation_record_ids"\s*:\s*\[(.*?)\]', clean, re.DOTALL)
    if cits_m:
        res["citation_record_ids"] = [c.strip().strip('"\'') for c in cits_m.group(1).split(",") if c.strip()]
    return res


def generate_conversational_response(
    question: str,
    llm_provider: Any,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    mode: str = "greeting",
) -> Dict[str, Any]:
    """
    Routes conversational inquiries (greetings, educational definitions, general knowledge)
    strictly through Gemini. Zero fallback texts and zero ungrounded tool clutter.
    If Gemini is unconfigured or fails, returns structured ai_unavailable status.
    """
    clean_q = question.strip()

    # 1. Honest check if Gemini is configured
    if not getattr(llm_provider, "is_configured", False):
        return {
            "question": clean_q,
            "answer": None,
            "evidence_citations": [],
            "relevant_records": [],
            "quality_warnings": [],
            "scientific_limitations": ["Gemini AI model is not configured."],
            "suggested_actions": [],
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
                "model": getattr(llm_provider, "model_name", "gemini-3.5-flash-lite") if llm_provider else "gemini-3.5-flash-lite",
                "status": "error",
                "reason": "GEMINI_API_KEY environment variable not configured",
                "status_code": 401,
                "retries_attempted": 0,
            }
        }

    # 2. Prepare conversational prompts for Gemini
    if mode == "educational":
        system_instruction = (
            "You are NASA FLAME Research Intelligence, an expert scientific educator specializing in combustion physics "
            "and NASA microgravity research.\n\n"
            "INSTRUCTIONS:\n"
            "- Provide a clear, natural, and scientifically accurate educational explanation of the requested concept.\n"
            "- If the user asks to explain it simply or simplify a previous answer, use intuitive analogies and clear language "
            "(explaining why buoyant convection disappears without gravity, why flames become spherical, and why diffusion or forced flow dominates).\n"
            "- Format using clean GitHub markdown with inline LaTeX math where appropriate (e.g. $u_b \\approx 0$, $1g$, $\\mu g$).\n"
            "- Do NOT invent flight experiments, do NOT fabricate telemetry, and do NOT force artificial citation brackets [flame_...].\n"
            "- Output MUST be a valid JSON object matching: {\"answer\": \"<your explanation in markdown>\"}"
        )
    elif mode == "greeting":
        system_instruction = (
            "You are NASA FLAME Research Intelligence, a friendly, professional AI research assistant for the NASA Space Apps Challenge 2026. "
            "You specialize in NASA microgravity combustion experiments (BASS-II narrow channel tests, Saffire-III vehicle burns, Cygnus telemetry) "
            "and terrestrial fire safety applications.\n\n"
            "INSTRUCTIONS:\n"
            "- Respond warmly, naturally, and concisely (1-2 short paragraphs).\n"
            "- Address the researcher's greeting or check-in directly.\n"
            "- Briefly highlight what you can help investigate (flame spread dynamics, solid fuel flammability, ignition telemetry, "
            "spacecraft smoke detection, research gaps in partial gravity, and terrestrial fire safety).\n"
            "- Invite the researcher to propose a research question, material, or experiment.\n"
            "- Do NOT cite fake papers or force citation brackets [flame_...].\n"
            "- Do NOT report 'insufficient evidence' for greetings.\n"
            "- Output MUST be a valid JSON object matching: {\"answer\": \"<your response in markdown>\"}"
        )
    else:  # mode == "general" (general knowledge, pleasantries, questions outside microgravity)
        system_instruction = (
            "You are NASA FLAME Research Intelligence, a knowledgeable and conversational AI assistant for NASA research.\n\n"
            "INSTRUCTIONS:\n"
            "- Answer the user's question accurately, politely, and concisely.\n"
            "- For general knowledge questions (geography, history, general science, math, etc.), provide a direct and helpful answer.\n"
            "- You may warmly mention that you specialize in NASA microgravity combustion research (BASS-II, Saffire-III, Cygnus telemetry) if the user seeks fire science insights, but never refuse to answer or output generic canned rejection templates.\n"
            "- Do NOT cite fake papers or force citation brackets [flame_...].\n"
            "- Format using clean GitHub markdown.\n"
            "- Output MUST be a valid JSON object matching: {\"answer\": \"<your response in markdown>\"}"
        )

    conv_context = ""
    if conversation_history:
        recent_turns = conversation_history[-6:]
        turn_lines = []
        for t in recent_turns:
            r = "Researcher" if t.get("role") == "user" else "Assistant"
            turn_lines.append(f"{r}: {t.get('content', '')[:400]}")
        if turn_lines:
            conv_context = "CONVERSATION HISTORY:\n" + "\n".join(turn_lines) + "\n\n"

    user_prompt = f"{conv_context}USER INQUIRY: {clean_q}\n\nProvide your response in JSON: {{\"answer\": \"...\"}}"

    llm_response = llm_provider.generate(
        system_instruction=system_instruction,
        user_prompt=user_prompt,
    )

    # 3. Handle Gemini API failure
    if not llm_response.get("success"):
        logger.warning("Conversational Gemini generation failed: %s; returning ai_unavailable status", llm_response.get("error"))
        status_code = llm_response.get("status_code", 0)
        retryable = status_code in (429, 500, 502, 503, 504)
        return {
            "question": clean_q,
            "answer": None,
            "evidence_citations": [],
            "relevant_records": [],
            "quality_warnings": [],
            "scientific_limitations": [f"Gemini API error: {llm_response.get('error', 'Service unavailable')}"],
            "suggested_actions": [],
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
                "model": llm_provider.model_name,
                "status": "error",
                "reason": llm_response.get("error"),
                "status_code": status_code,
                "retries_attempted": llm_response.get("retries_attempted", 0),
            }
        }

    # 4. Parse JSON answer
    raw_text = llm_response.get("raw_text", "")
    parsed_json = parse_llm_json(raw_text)
    answer_text = parsed_json.get("answer") or raw_text
    clean_ans = clean_scientific_unicode(answer_text)

    return {
        "question": clean_q,
        "answer": clean_ans,
        "evidence_citations": [],
        "relevant_records": [],
        "quality_warnings": [],
        "scientific_limitations": [] if mode in ("greeting", "general") else [
            "Educational concept explanation; empirical flight data is available across indexed NASA datasets."
        ],
        "suggested_actions": [],
        "retrieval_mode": "gemini_conversation",
        "status": "gemini_conversation",
        "evidence_sufficiency": "sufficient",
        "claim_validation": {"validated": True, "discrepancies": []},
        "llm_provider_status": {
            "is_configured": True,
            "provider": "google-gemini",
            "model": llm_provider.model_name,
            "status": "success",
            "mode": mode,
            "retries_attempted": llm_response.get("retries_attempted", 0),
        }
    }
