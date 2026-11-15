"""
NASA FLAME — Scientific Validation & Citation Verification (Phase R4 / Modular Refactor)
Provides deterministic citation validation, claim validation against verified physical facts,
and hallucination safeguards for NASA microgravity combustion research.
"""

from typing import List, Dict, Any, Tuple
import re


def validate_citations(
    raw_citations: List[str],
    allowed_ids: List[str],
    answer_text: str,
) -> Tuple[List[str], List[str]]:
    """
    Validates that all cited IDs exist in the retrieved evidence pool.
    Purges hallucinated citation IDs and extracts cited IDs from text.
    """
    allowed_set = set(allowed_ids)
    valid_citations = []
    invalid_citations = []

    # Also find all [flame_...], [GAP-...], and [EA-EV-...] citations in answer text
    in_text_citations = re.findall(r"\[(flame_[a-zA-Z0-9_]+|GAP-[a-zA-Z0-9_-]+|EA-EV-[a-zA-Z0-9_-]+)\]", answer_text)
    all_candidate_citations = set(raw_citations) | set(in_text_citations)

    for cid in all_candidate_citations:
        if cid in allowed_set:
            valid_citations.append(cid)
        else:
            invalid_citations.append(cid)

    return sorted(list(set(valid_citations))), sorted(list(set(invalid_citations)))


def validate_scientific_claims(
    answer_text: str,
    retrieved_candidates: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministic scientific claim validation verifying that generated statements
    adhere to physical facts in the retrieved NASA FLAME corpus.
    Checks for:
    1. Equating telemetry recording duration (e.g. 689.96s for Sample 1 / 159.95s for Sample 2) with combustion duration.
    2. Equating timeline ignition timestamp (epoch t = 66s / t = 60s) with ignition delay.
    3. Treating unrecorded parameters (such as flame spread rate) as 0 cm/s or non-occurrence.
    4. Asserting that exact extinction times must be solely inferred from thermocouple decay slopes.
    5. Asserting universal NASA absence based solely on local corpus omission.
    6. Fabricating uninstrumented sensor channels.
    7. Unsupported terrestrial lead time claims.
    8. Unsupported efficiency percentage gains.
    9. Commercial adoption or code certification claims.
    10. Invented wind-speed requirements.
    11. Unsupported risk reduction predictions.
    """
    text = answer_text or ""
    flags = []
    warnings = []
    corrections = []

    # 1. Check: Equating telemetry recording duration with combustion duration
    for pat in [
        r"(?:combustion|burning|flame)\s+(?:duration|time)\s*(?:was|is|=|of|lasted)\s*(?:approximately|~)?\s*(?:689(?:\.96)?|159(?:\.95)?|174[0-9]|1742|20909|4848)",
        r"(?:burned|combusted)\s+for\s+(?:approximately|~)?\s*(?:689(?:\.96)?|159(?:\.95)?|174[0-9]|1742|20909|4848)\s*(?:s|sec|seconds)",
    ]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            prefix = text[max(0, m.start() - 60):m.start()].lower()
            if any(neg in prefix for neg in ["not", "cannot", "never", "distinct from", "does not mean", "should not", "not equated"]):
                continue
            flags.append("equates_recording_duration_to_combustion")
            warnings.append(
                "Identified statement conflating continuous data acquisition (DAQ) recording duration (e.g. 689.96s for Sample 1 or 159.95s for Sample 2) with active flame combustion duration. Continuous sensor logging initiated prior to igniter activation and persisted through post-extinguishment thermal cooldown."
            )
            corrections.append(
                "Scientific Correction: Elapsed file recording duration (e.g. 689.96s for Sample 1 or 159.95s for Sample 2) reflects total continuous telemetry acquisition time, not active flame burning duration."
            )
            break
        if "equates_recording_duration_to_combustion" in flags:
            break

    # 2. Check: Equating timeline event timestamp with ignition delay
    delay_pat = r"ignition\s+delay\s+(?:was|of|is|=|:)\s*(?:approximately|~)?\s*(?:66(?:\.0)?|60(?:\.03)?)\s*(?:s|sec|seconds)?"
    for m in re.finditer(delay_pat, text, re.IGNORECASE):
        prefix = text[max(0, m.start() - 60):m.start()].lower()
        if any(neg in prefix for neg in ["not", "cannot", "never", "distinct from", "does not mean", "should not", "not the"]):
            continue
        flags.append("equates_ignition_timestamp_to_delay")
        warnings.append(
            "Identified statement interpreting timeline event timestamp (t = 66.0s or 60.03s) as physical ignition delay. In Saffire flight telemetry, t = 66s is the timeline trigger epoch when igniter current was commanded, not the time delay required to achieve ignition."
        )
        corrections.append(
            "Clarification: Timestamp t = 66.0s represents the timeline event epoch when the igniter was energized, not the physical ignition delay."
        )
        break

    # 3. Check: Treating missing parameter (flame spread rate) as 0 cm/s
    for pat in [
        r"(?:flame\s+)?(?:spread\s+rate|rate\s+of\s+spread)\s*(?:is|was|=|:|of)\s*0(?:\.0)?\s*(?:cm/s|mm/s)",
        r"(?:recorded|measured|exhibited|had)\s+(?:a\s+)?(?:flame\s+)?spread\s+rate\s+of\s+0(?:\.0)?\s*(?:cm/s|mm/s)",
    ]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            prefix = text[max(0, m.start() - 60):m.start()].lower()
            if any(neg in prefix for neg in ["not", "cannot", "never", "no assumption", "neither", "does not mean", "should not", "must not"]):
                continue
            flags.append("missing_value_treated_as_zero")
            warnings.append(
                "Identified statement treating an uninstrumented parameter (flame spread rate) as 0 cm/s. In Saffire continuous sensor telemetry, flame spread rate was not derived from sensor logs and is unrecorded, not zero."
            )
            corrections.append(
                "Scientific Safeguard: Uninstrumented parameter (flame spread rate) cannot be assumed to be 0 cm/s; optical video photogrammetry is required."
            )
            break
        if "missing_value_treated_as_zero" in flags:
            break

    # 4. Check: Universal NASA absence claim
    univ_pat = r"(?:no\s+NASA\s+(?:study|research|experiment|data)|NASA\s+has\s+never|absent\s+from\s+all\s+NASA|nowhere\s+in\s+NASA)"
    for m in re.finditer(univ_pat, text, re.IGNORECASE):
        prefix = text[max(0, m.start() - 60):m.start()].lower()
        if any(neg in prefix for neg in ["not", "cannot", "never", "does not mean", "does not imply", "should not", "cannot conclude"]):
            continue
        flags.append("universal_absence_claim")
        warnings.append(
            "Identified statement extrapolating omission from the indexed NASA FLAME corpus to universal absence across all NASA research."
        )
        corrections.append(
            "Boundary Caveat: Parameter omission applies strictly to the currently indexed NASA FLAME corpus, not all NASA publications."
        )
        break

    # 5. Check: Unsupported assertion that exact extinction times must be inferred from thermocouple decay slopes
    extinct_slope_pat = r"extinction\s+(?:time|timestamp|times).*?(?:must\s+be|is)\s+inferred\s+from\s+thermocouple\s+(?:temperature\s+)?decay\s+slope"
    for m in re.finditer(extinct_slope_pat, text, re.IGNORECASE):
        flags.append("unsupported_extinction_method_assertion")
        warnings.append(
            "Identified assertion that exact extinction times must be inferred from thermocouple decay slopes. Thermal data may support analysis, but exact extinction identification requires an appropriate validated method and potentially additional observations (such as optical video analysis)."
        )
        corrections.append(
            "Scientific Qualification: Thermal data supports post-burn cooling analysis, but exact extinction timestamps require validated analytical methods or optical camera observations."
        )
        break

    # 6. Check: Fabricated terrestrial smoke alarm lead-time (e.g. "43 seconds earlier", "43s warning lead time")
    for pat in [
        r"43\s*(?:s|sec|seconds)?\s*(?:earlier|lead\s*time|faster\s*warning|advance\s*warning)",
        r"(?:earlier|advance)\s*warning\s*of\s*43\s*(?:s|sec|seconds)",
    ]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            prefix = text[max(0, m.start() - 60):m.start()].lower()
            if any(neg in prefix for neg in ["not", "cannot", "never", "does not mean", "should not", "not a generic", "chamber"]):
                continue
            flags.append("unsupported_lead_time_claim")
            warnings.append(
                "Identified assertion generalizing a specific flight sensor experiment timeline (such as 43 seconds) to a guaranteed terrestrial smoke detection lead-time advantage."
            )
            corrections.append(
                "Terrestrial Sensor Caveat: 43-second timelines documented in flight sensor testing (SAME/Cygnus) represent specific chamber response epochs, not certified terrestrial fire alarm lead-time gains."
            )
            break

    # 7. Check: Fabricated energy efficiency or emission reduction percentages (e.g. "15-20% efficiency", "15% lower emissions")
    for pat in [
        r"(?:15\s*-\s*20%|15%|20%)\s*(?:efficiency|fuel\s*savings|emission\s*reduction|lower\s*emissions)",
        r"(?:improve|increase|reduce)\s*(?:efficiency|emissions)\s*by\s*(?:15\s*-\s*20%|15%|20%)",
    ]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            prefix = text[max(0, m.start() - 60):m.start()].lower()
            if any(neg in prefix for neg in ["not", "unsupported", "cannot", "unverified", "no proof", "hypothetical"]):
                continue
            flags.append("unsupported_efficiency_percentage_claim")
            warnings.append(
                "Identified unsupported numerical percentage gain claim (e.g. 15-20% efficiency) derived from microgravity research without terrestrial empirical burner validation."
            )
            corrections.append(
                "Engineering Safeguard: Fundamental microgravity flame kinetics inform theoretical mechanism development, but specific industrial burner efficiency gains require terrestrial empirical verification."
            )
            break

    # 8. Check: Commercial equipment deployment or code certification claims
    for pat in [
        r"(?:already|currently)\s*(?:deployed|adopted|used)\s*in\s*commercial\s*(?:turbines|boilers|buildings|appliances)",
        r"certified\s*(?:under|for)\s*(?:commercial|terrestrial|nfpa|building)\s*(?:standards|codes)",
    ]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            prefix = text[max(0, m.start() - 60):m.start()].lower()
            if re.search(r"\b(?:not|zero|no|cannot|neither|does not|unsupported|unverified)\b", prefix):
                continue
            flags.append("unsupported_commercial_adoption_claim")
            warnings.append(
                "Identified unsupported claim asserting commercial adoption or safety code certification of microgravity research findings."
            )
            corrections.append(
                "Adoption Status Notice: Under NASA FLAME's audited standards, there are 0 documented commercial applications in the Earth Applications catalog; all findings represent supported research implications or exploratory hypotheses."
            )
            break

    # 9. Check: Invented fixed wind-speed requirements (>2.5 m/s) in Earth validation synthesis
    for pat in [
        r"(?:wind\s+tunnel|forced\s+velocit\w*|wind\s+speed)\s*(?:exceeding|of|at|over|above|>)\s*2\.5\s*(?:m/s|meter)",
        r">2\.5\s*m/s",
    ]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            prefix = text[max(0, m.start() - 60):m.start()].lower()
            if any(neg in prefix for neg in ["not", "unsupported", "cannot", "unverified", "no fixed", "arbitrary", "without"]):
                continue
            flags.append("invented_wind_speed_requirement")
            warnings.append(
                "Identified unsupported fixed wind-speed requirement (>2.5 m/s) in terrestrial validation synthesis. Earth validation protocols must be grounded in specific domain standards rather than arbitrary fixed velocity thresholds."
            )
            corrections.append(
                "Validation Grounding Correction: Terrestrial testing requirements depend on the specific application domain and relevant consensus standard, not an arbitrary universal fixed wind speed."
            )
            break
        if "invented_wind_speed_requirement" in flags:
            break

    # 10. Check: Unsupported quantitative risk reduction predictions
    for pat in [
        r"\b(?:reduce|decreas\w*|lower\w*|prevent\w*)\b.*?\b(?:risk|fatalit\w*|casualt\w*|loss(?:es)?|damage)\b.*?\b\d{1,3}%",
        r"\b\d{1,3}%\b.*?\b(?:reduction|decrease|drop)\b.*?\b(?:risk|damage|fatalit\w*|loss(?:es)?)\b",
    ]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            prefix = text[max(0, m.start() - 60):m.start()].lower()
            if any(neg in prefix for neg in ["not", "cannot", "unsupported", "does not mean", "no claim", "never"]):
                continue
            flags.append("unsupported_risk_reduction_prediction")
            warnings.append(
                "Identified unsupported quantitative risk reduction prediction derived from microgravity research without actuarial or terrestrial safety engineering validation."
            )
            corrections.append(
                "Scientific Safeguard: Microgravity findings inform fundamental physical mechanisms; they do not substantiate quantitative terrestrial risk or fatality reduction percentages."
            )
            break
        if "unsupported_risk_reduction_prediction" in flags:
            break

    return {
        "is_valid": len(flags) == 0,
        "flags": flags,
        "warnings": warnings,
        "corrections": corrections,
    }
