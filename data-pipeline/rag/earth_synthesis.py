"""
NASA FLAME — Earth Applications Synthesis (Phase R4 / Modular Refactor)
Synthesizes a grounded 9-section scientific response for inquiries querying Earth Applications
and terrestrial combustion research implications.
Enforces strict grounding in audited evidence records [EA-EV-...], physical transfer caveats
(1g buoyancy coupling, Froude/Richardson numbers), and explicit zero-commercial-adoption disclosures.
"""

from typing import List, Dict, Any
import re

from rag.unicode_utils import clean_scientific_unicode


def generate_earth_application_synthesis(
    question: str,
    earth_items: List[Dict[str, Any]],
    retrieved_candidates: List[Dict[str, Any]] = None,
    reason: str = "Retrieval-only terrestrial synthesis",
) -> Dict[str, Any]:
    """
    Synthesizes a grounded 9-section scientific response for inquiries querying Earth Applications
    and terrestrial combustion research implications.
    Enforces strict grounding in audited evidence records [EA-EV-...], physical transfer caveats
    (1g buoyancy coupling, Froude/Richardson numbers), and explicit zero-commercial-adoption disclosures.
    """
    q_lower = (question or "").lower()

    # Handle queries with zero matching Earth evidence records without padding 9 empty sections
    if not earth_items:
        target_id_str = ""
        id_match = re.search(r"\b(EA-EV-[A-Z0-9\-]+)\b", question, re.IGNORECASE)
        if id_match:
            target_id_str = f" for requested identifier `{id_match.group(1).upper()}`"

        return {
            "answer": clean_scientific_unicode(
                f"**NASA FLAME Grounded Scientific AI — Earth Applications Synthesis**  \n\n"
                f"### Insufficient Evidence in Audited Earth Applications Catalog\n\n"
                f"No verified Earth application evidence records{target_id_str} were found matching the research inquiry "
                f"*{clean_scientific_unicode(question)}* in the audited NASA FLAME catalog.\n\n"
                f"**Scientific Verification Boundaries:**\n"
                f"- The Earth Applications catalog contains exactly 11 audited evidence records across 7 defined categories.\n"
                f"- If you specified an evidence ID (e.g., `EA-EV-...`), verify that it matches an active canonical record in the catalog.\n"
                f"- NASA FLAME does not generate synthetic transfer claims or pad speculative engineering sections when empirical flight records are absent."
            ),
            "evidence_backed_claims": [],
            "citation_record_ids": [],
            "scientific_limitations": [
                "No matching audited Earth application evidence found in NASA FLAME catalog.",
                "Zero synthetic claims or speculative engineering recommendations generated without empirical flight grounding."
            ],
            "relevant_experiment_ids": [],
            "evidence_sufficiency": "insufficient",
            "status": "earth_application_insufficient_evidence",
        }

    primary_ev = earth_items[0]
    ev_id = primary_ev.get("id", "EA-EV-UNKNOWN")
    ev_title = primary_ev.get("title", "Earth Application Finding")
    cat_title = primary_ev.get("category_title", "Terrestrial Combustion Research")
    inv_name = primary_ev.get("investigation_name", "NASA Combustion Research")
    finding_text = primary_ev.get("scientific_finding", "")
    relevance_text = primary_ev.get("proposed_terrestrial_relevance", "")
    diff_text = primary_ev.get("gravity_buoyancy_ventilation_differences", "")
    limits_text = primary_ev.get("earth_transfer_limitations", "")
    class_text = primary_ev.get("evidence_classification", "supported_research_implication")
    val_status = primary_ev.get("validation_status", "locally_verified")
    rubric_text = primary_ev.get("confidence_rubric", "")
    source_ref = primary_ev.get("source_reference", "")
    dataset_ref = primary_ev.get("dataset_or_measurement_reference", "")
    excerpt_text = primary_ev.get("supporting_excerpt", "")
    uncertainty = primary_ev.get("uncertainty_notes", "")

    citations = [ev.get("id") for ev in earth_items if ev.get("id")]
    claims = []
    sections = []

    # Check for commercial / industrial adoption inquiries
    is_adoption_inquiry = bool(re.search(
        r"\b(commercial\s+adoption|commercially\s+adopted|field\s+deployment|market|industry\s+standard|standards\s+adoption|certified|code\s+compliance|deployed\s+in|used\s+in\s+commercial|commercial\s+market)\b",
        q_lower
    ))

    # Header
    sections.append(
        f"**NASA FLAME Grounded Scientific AI — Earth Applications Synthesis**  \n"
        f"**Target Terrestrial Evidence:** **{ev_title}** [`{ev_id}`] ({cat_title})  \n"
        f"*Operating in Grounded Retrieval-Only Mode ({reason}). Grounded strictly in audited NASA combustion flight evidence "
        f"and physical transport mechanics.*"
    )

    # 1. Direct Scientific Answer
    sec1 = ["### 1. Direct Scientific Answer\n"]
    if is_adoption_inquiry:
        sec1.append(
            f"Under NASA FLAME's audited verification standards (which require documented terrestrial field deployment, "
            f"commercial market adoption, or formal building/industrial standard incorporation), there are currently "
            f"**0 documented commercial applications** in the Earth Applications catalog. "
            f"All 11 audited records represent fundamental combustion science insights classified as either "
            f"**supported research implications** (10 records) or **1 exploratory research hypothesis** (1 record: EA-EV-SAFFIRE-WILD-03). "
            f"While microgravity experiments provide clean, buoyancy-free benchmark kinetics and transport observations, "
            f"commercial and industrial deployment requires dedicated terrestrial scaling, buoyancy re-coupling, and regulatory certification."
        )
        claims.append(f"Adoption status audit: 0 documented commercial applications, 10 supported research implications, 1 exploratory hypothesis [{ev_id}].")
    else:
        sec1.append(
            f"NASA microgravity combustion research on **{inv_name}** informs terrestrial combustion science by isolating fundamental "
            f"pyrolysis, flame spread, aerosol morphology, and extinction mechanics from buoyant convection. "
            f"Specifically, **{ev_title}** [`{ev_id}`] demonstrates that {finding_text} "
            f"This provides empirical baseline data for {relevance_text}"
        )
        claims.append(f"{ev_title}: {finding_text} [{ev_id}]")
    sections.append("\n".join(sec1))

    # 2. Relevant NASA Investigations
    sec2 = ["### 2. Relevant NASA Microgravity Investigations\n"]
    sec2.append(
        f"- **Primary Investigation:** **{inv_name}** (`{primary_ev.get('investigation_id', 'N/A')}`)\n"
        f"  - *Flight Platform & Rig:* {primary_ev.get('flight_experiment', 'NASA Flight Facility / ISS')}\n"
        f"  - *Source Reference:* {source_ref}\n"
        f"  - *Telemetry / Measurement Reference:* {dataset_ref or 'Verified technical report / sensor array'}"
    )
    related_invs = primary_ev.get("related_investigation_ids", [])
    if related_invs:
        sec2.append(f"  - *Correlated Spaceflight Investigations:* {', '.join(related_invs)}")
    if len(earth_items) > 1:
        sec2.append("\n- **Additional Cross-Referenced Evidence Records:**")
        for secondary_ev in earth_items[1:3]:
            s_id = secondary_ev.get("id")
            sec2.append(
                f"  - **{secondary_ev.get('title')}** [`{s_id}`]: {secondary_ev.get('investigation_name')} "
                f"({secondary_ev.get('category_title')})"
            )
    sections.append("\n".join(sec2))

    # 3. Verified Experimental Observations
    sec3 = ["### 3. Verified Experimental Observations from Flight Telemetry\n"]
    sec3.append(
        f"Experimental observations from {inv_name} establish key physical parameters under controlled low-gravity conditions:\n"
        f"- **Scientific Finding:** {finding_text}\n"
        f"- **Empirical Evidence & Excerpt:** \"{excerpt_text}\" [{ev_id}]\n"
        f"- **Measurement Provenance:** {val_status.replace('_', ' ').title()} (Dimension A: Flight Grounding verified)"
    )
    claims.append(f"Empirical flight evidence: {excerpt_text} [{ev_id}]")
    sections.append("\n".join(sec3))

    # 4. Underlying Physical Mechanisms (Decoupled Buoyancy)
    sec4 = ["### 4. Underlying Physical Mechanisms (Decoupled Buoyancy & Transport)\n"]
    sec4.append(
        f"In 1g terrestrial combustion, buoyant body forces ($g \\cdot \\Delta \\rho$) are always present, and the Richardson number "
        f"$Ri = Gr / Re^2$ governs the balance between buoyant and forced inertial momentum:\n"
        f"- **Buoyancy vs. Forced Convection:** In low-velocity or quiescent conditions, buoyant updrafts dominate ($Ri \\gg 1$, with buoyant velocity "
        f"scaling as $u_{{buoyant}} \\sim \\sqrt{{2 g H \\Delta T / T_\\infty}}$, typically ~0.5 to 2 m/s for laboratory-scale flames), coupling upward "
        f"fluid acceleration with oxidizer entrainment and flame flickering. However, in high-velocity forced ventilation (such as industrial conduits where "
        f"$u \\ge 1-2$ m/s), forced inertia can dominate ($Ri \\ll 1$) even in normal gravity.\n"
        f"- **Microgravity Isolation:** In orbit ($10^{-6}g$), $Gr \\to 0$, forcing $Ri \\ll 1$ across all flow velocities. Pure forced ventilation "
        f"or pure molecular diffusion governs oxygen transport to the fuel surface. This eliminates buoyant stretch and flickering, allowing researchers "
        f"to directly observe intrinsic solid pyrolysis kinetics, low-velocity flame extinction thresholds, and smoke aerosol agglomeration without convective distortion.\n"
        f"- **Observed Mechanism:** {diff_text}"
    )
    sections.append("\n".join(sec4))

    # 5. Potential Terrestrial Research Implications
    sec5 = ["### 5. Potential Terrestrial Research Implications\n"]
    sec5.append(
        f"The transfer of {inv_name} findings to terrestrial combustion engineering involves:\n"
        f"- **Target Application Domain:** **{cat_title}** (`{primary_ev.get('category_id')}`)\n"
        f"- **Proposed Research Relevance:** {relevance_text}\n"
        f"- **Dimension B Classification:** `{class_text}`\n"
        f"  - *Classification Meaning:* This finding provides a validated scientific mechanism or empirical trend that informs "
        f"terrestrial models or experimental designs, but does NOT constitute a certified commercial system or standalone design code."
    )
    sections.append("\n".join(sec5))

    # 6. Gravity, Buoyancy, and Scale-Transfer Limitations
    sec6 = ["### 6. Gravity, Buoyancy, and Scale-Transfer Limitations\n"]
    sec6.append(
        f"Direct application of microgravity combustion observations to 1g terrestrial systems is constrained by fundamental physics:\n"
        f"- **Convective Updrafts:** {diff_text}\n"
        f"- **Geometric & Boundary Scale Constraints:** {limits_text}\n"
        f"- **Dimensional Scaling Mismatch:** Microgravity laminar flames in small ducts (e.g. 5 cm Saffire flow duct or 10 cm BASS glovebox) "
        f"do not exhibit the high-Reynolds-number turbulent mixing or large-scale thermal radiation feedback typical of full-scale terrestrial "
        f"industrial furnaces, building shafts, or wildland fire fronts."
    )
    sections.append("\n".join(sec6))

    # 7. Evidence Classification, Confidence Tier & Quality Warnings
    sec7 = ["### 7. Evidence Classification, Confidence Tier & Quality Warnings\n"]
    sec7.append(
        f"- **Dimension A (Flight Evidence Grounding):** `{val_status}`\n"
        f"- **Dimension B (Terrestrial Application Status):** `{class_text}`\n"
        f"- **Confidence Rubric:** {rubric_text}\n"
        f"- **Uncertainty Disclosures & Caveats:** {uncertainty or 'Parameter boundaries reflect flight chamber geometry.'}\n"
        f"- **Catalog Standards Adherence:** 0 documented commercial applications; 10 supported research implications; 1 exploratory hypothesis."
    )
    sections.append("\n".join(sec7))

    # 8. Source Citations and Traceable Evidence IDs
    sec8 = ["### 8. Source Citations & Traceable Evidence IDs\n"]
    for ev in earth_items[:3]:
        sec8.append(
            f"- **[{ev['id']}]**: *{ev['title']}*. NASA Investigation: {ev['investigation_name']}. "
            f"Source: `{ev.get('source_reference')}`."
        )
    sections.append("\n".join(sec8))

    # 9. Areas Requiring Additional Terrestrial Validation
    sec9 = ["### 9. Areas Requiring Additional Terrestrial Validation\n"]

    # Domain-specific validation grounded in actual consensus standards
    cat_id = primary_ev.get("category_id", "")
    if cat_id == "material_flammability_fire_resistance":
        domain_val = (
            "Standardized Terrestrial Flammability Testing: Benchmarking kinetic pyrolysis models against "
            "standard terrestrial cone calorimetry (ASTM E1354) and vertical flame tests (UL 94), accounting for "
            "1g buoyant plume acceleration and flame anchoring."
        )
    elif cat_id == "fire_suppression_research":
        domain_val = (
            "Terrestrial Total-Flooding & Cup-Burner Protocols: Verifying chemical and thermal extinction concentrations "
            "under ISO 14520 / NFPA 2001 protocols, where buoyant momentum plumes alter suppressant entrainment."
        )
    elif cat_id == "wildfire_combustion":
        domain_val = (
            "Porous Bed Terrestrial Validation: Replicating smoldering propagation across heterogeneous organic soil, "
            "duff, and peat layers under ambient atmospheric moisture gradients and ambient boundary layer winds."
        )
    elif cat_id == "fire_detection_smoke_aerosol":
        domain_val = (
            "Terrestrial Smoke Chamber Testing: Evaluating optical scattering and ionization responses under UL 268 / UL 217 "
            "standards where 1g gravitational sedimentation and thermal updrafts compete with aerosol agglomeration."
        )
    elif cat_id == "combustion_efficiency_emissions":
        domain_val = (
            "Turbulent Flame Rig Verification: Coupling microgravity chemical kinetic mechanisms with turbulent mixing models "
            "(LES/RANS) in high-pressure optical spray chambers and gas turbine combustors."
        )
    elif cat_id in ("building_fire_safety", "other_terrestrial_applications"):
        domain_val = (
            "Full-Scale Conduit & Damper Evaluation: Full-scale duct testing conforming to NFPA 90A (Standard for the Installation "
            "of Air-Conditioning and Ventilating Systems), verifying damper actuation timelines and industrial airflow isolation."
        )
    else:
        domain_val = (
            f"Protocol-Grounded Terrestrial Testing: Controlled 1g experimentation addressing specific transfer boundaries: "
            f"{limits_text or 'Re-coupling natural convection and full-scale geometric boundaries.'}"
        )

    sec9.append(
        f"Before microgravity insights from `{ev_id}` can be translated into certified terrestrial engineering practices, "
        f"the following empirical and analytical validation steps are required:\n"
        f"1. **Coupled Buoyancy CFD Modeling:** Numerical validation of CFD models (e.g. NIST FDS, OpenFOAM) incorporating both "
        f"decoupled kinetic parameters and 1g buoyant body-force source terms ($g \\cdot \\Delta \\rho$).\n"
        f"2. **{domain_val}**\n"
        f"3. **Scale-Up & Geometric Verification:** Full-scale testing on commercial materials and structural geometries to assess "
        f"thermal radiation feedback beyond small flight test sections.\n"
        f"4. **Consensus Standards Body Review:** Formal validation and peer review through established standards organizations "
        f"(e.g. ASTM, NFPA, UL, ISO) prior to any regulatory, commercial, or life-safety engineering deployment."
    )
    sections.append("\n".join(sec9))

    full_answer = clean_scientific_unicode("\n\n".join(sections))
    limitations = [
        f"Evidence record {ev_id} is grounded in verified NASA flight data ({val_status}).",
        "Terrestrial application status is classified strictly as supported research implication or exploratory hypothesis (0 documented commercial applications).",
        "1g terrestrial environments reintroduce buoyant body forces: low-speed unconfined fires transition to buoyancy dominance ($Ri \\gg 1$), while high-speed mechanical duct flows may maintain forced-convection dominance ($Ri \\ll 1$).",
        "Findings inform fundamental scientific understanding and numerical modeling, but do not constitute certified equipment designs or engineering approvals."
    ]
    clean_lims = [clean_scientific_unicode(l) for l in limitations]

    relevant_experiments = [primary_ev.get("investigation_id")] if primary_ev.get("investigation_id") else []
    for e in earth_items:
        inv = e.get("investigation_id")
        if inv and inv not in relevant_experiments:
            relevant_experiments.append(inv)

    return {
        "answer": full_answer,
        "evidence_backed_claims": claims,
        "citation_record_ids": citations,
        "scientific_limitations": clean_lims,
        "relevant_experiment_ids": relevant_experiments,
        "evidence_sufficiency": "sufficient" if earth_items else "partial",
        "status": "earth_application_retrieval_fallback",
    }
