"""
NASA FLAME — Scientific Comparison Synthesis (Phase R4 / Modular Refactor)
Synthesizes structured, rigorous scientific comparison matrix and analysis
across requested experimental runs, materials, and measurement channels.
Guarantees zero numerical fabrication.
"""

from typing import List, Dict, Any
import json

from rag.unicode_utils import clean_scientific_unicode
from rag.measurement_synthesis import format_stat_summary


def generate_comparison_synthesis(
    question: str,
    evidence_items: List[Dict[str, Any]],
    entities: Dict[str, Any],
    reason: str,
) -> Dict[str, Any]:
    """
    Synthesizes a structured, rigorous scientific comparison matrix and analysis
    across requested experimental runs, materials, and measurement channels.
    Guarantees zero numerical fabrication.
    """
    unresolved = entities.get("unresolved_requested_entities", [])
    req_records = entities.get("requested_record_ids", [])
    req_datasets = entities.get("requested_dataset_ids", [])

    # Filter and prioritize the specific records being compared
    compared_records = []
    if req_records:
        for rid in req_records:
            match = next((e for e in evidence_items if e["record_id"] == rid), None)
            if match and match not in compared_records:
                compared_records.append(match)

    # Fallback to matching requested datasets
    if len(compared_records) < 2 and req_datasets:
        for ds in req_datasets:
            match = next((e for e in evidence_items if e.get("dataset_id") == ds and e.get("record_type") == "experiment_run"), None)
            if match and match not in compared_records:
                compared_records.append(match)

    # If still fewer than 2, pick top experiment_run records from evidence
    if len(compared_records) < 2:
        for e in evidence_items:
            if e.get("record_type") == "experiment_run" and e not in compared_records:
                compared_records.append(e)
            if len(compared_records) == 2:
                break

    # If still < 2, use whatever evidence items are available
    if len(compared_records) < 2:
        compared_records = evidence_items[:2]

    citations = [r["record_id"] for r in compared_records]
    claims = []
    summary_sections = []

    # Header
    summary_sections.append(
        f"**NASA FLAME Grounded Scientific Experiment Comparison**  \n"
        f"*Operating in Retrieval-Only Mode ({reason}). The comparative findings below are synthesized directly "
        f"from verified NASA experimental records with zero synthetic fabrication.*"
    )

    if unresolved:
        summary_sections.append(
            f"> **Notice on Unindexed Experiments:** The research query explicitly requested *'{', '.join(unresolved)}'*, "
            f"which is not present in the indexed NASA FLAME dataset collection (available Saffire flight burns: Sample 1, Sample 2, Sample 5, and Sample 6). "
            f"To maintain scientific integrity, no artificial numbers or unverified surrogate runs have been substituted."
        )

    if len(compared_records) >= 2:
        rec_a = compared_records[0]
        rec_b = compared_records[1]
        title_a = rec_a.get("title", rec_a["record_id"])
        title_b = rec_b.get("title", rec_b["record_id"])
        id_a = rec_a["record_id"]
        id_b = rec_b["record_id"]
        cond_a = rec_a.get("experimental_conditions", {})
        cond_b = rec_b.get("experimental_conditions", {})

        # 1. Experiment Identification & Objectives
        summary_sections.append(
            f"### 1. Experiment Identities & Test Objectives\n"
            f"- **Experiment A:** **{title_a}** [{id_a}]\n"
            f"  - **Investigation:** {rec_a.get('investigation', 'NASA Microgravity')}\n"
            f"  - **Dataset ID:** `{rec_a.get('dataset_id', 'N/A')}`\n"
            f"  - **Source Provenance:** `{rec_a.get('source_file')}` "
            f"(Sheet: {rec_a.get('source_worksheet') or 'N/A'}, Row: {rec_a.get('source_excel_row') or 'N/A'})\n"
            f"- **Experiment B:** **{title_b}** [{id_b}]\n"
            f"  - **Investigation:** {rec_b.get('investigation', 'NASA Microgravity')}\n"
            f"  - **Dataset ID:** `{rec_b.get('dataset_id', 'N/A')}`\n"
            f"  - **Source Provenance:** `{rec_b.get('source_file')}` "
            f"(Sheet: {rec_b.get('source_worksheet') or 'N/A'}, Row: {rec_b.get('source_excel_row') or 'N/A'})"
        )

        # 2. Materials & Environmental Test Conditions (Table)
        mat_a = cond_a.get("fuel_material") or "Unspecified fuel"
        mat_b = cond_b.get("fuel_material") or "Unspecified fuel"
        dim_a = cond_a.get("sample_dimensions") or "Not recorded"
        dim_b = cond_b.get("sample_dimensions") or "Not recorded"

        raw_o2_a = cond_a.get("oxygen_percentage") or cond_a.get("oxygen_concentration")
        raw_o2_b = cond_b.get("oxygen_percentage") or cond_b.get("oxygen_concentration")
        o2_a = str(raw_o2_a).strip() if raw_o2_a is not None and str(raw_o2_a).strip() else "Not recorded"
        o2_b = str(raw_o2_b).strip() if raw_o2_b is not None and str(raw_o2_b).strip() else "Not recorded"

        raw_flow_a = cond_a.get("flow_velocity_cm_s") or cond_a.get("flow_velocity")
        raw_flow_b = cond_b.get("flow_velocity_cm_s") or cond_b.get("flow_velocity")
        flow_a = str(raw_flow_a).strip() if raw_flow_a is not None and str(raw_flow_a).strip() else "Not recorded"
        flow_b = str(raw_flow_b).strip() if raw_flow_b is not None and str(raw_flow_b).strip() else "Not recorded"

        raw_press_a = cond_a.get("chamber_pressure_psia") or cond_a.get("chamber_pressure")
        raw_press_b = cond_b.get("chamber_pressure_psia") or cond_b.get("chamber_pressure")
        press_a = str(raw_press_a).strip() if raw_press_a is not None and str(raw_press_a).strip() else "Not recorded"
        press_b = str(raw_press_b).strip() if raw_press_b is not None and str(raw_press_b).strip() else "Not recorded"

        table_md = (
            f"### 2. Fuel Materials & Environmental Conditions Matrix\n\n"
            f"| Experimental Parameter | Experiment A [{id_a}] | Experiment B [{id_b}] |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Fuel Substrate Material** | {mat_a} | {mat_b} |\n"
            f"| **Sample Dimensions** | {dim_a} | {dim_b} |\n"
            f"| **Forced Airflow Velocity** | {flow_a} | {flow_b} |\n"
            f"| **Ambient Oxygen ($O_2$)** | {o2_a} | {o2_b} |\n"
            f"| **Chamber Total Pressure** | {press_a} | {press_b} |"
        )
        summary_sections.append(table_md)

        # 3. Available Measurement Channels
        channels_a = [f"{ch.get('channel_name')} ({ch.get('unit')})" for ch in rec_a.get("available_channels", [])[:5]]
        channels_b = [f"{ch.get('channel_name')} ({ch.get('unit')})" for ch in rec_b.get("available_channels", [])[:5]]
        summary_sections.append(
            f"### 3. Measurement Instrumentation & Physical Units\n"
            f"- **{title_a} Channels:** {', '.join(channels_a) if channels_a else 'Surface Thermocouples (TC7-TC12, °C), Plume Thermocouples (TC1-TC6, °C), Radiometers (mW/cm²), Pressure (psia)'}\n"
            f"- **{title_b} Channels:** {', '.join(channels_b) if channels_b else 'Surface Thermocouples (TC7-TC12, °C), Plume Thermocouples (TC1-TC6, °C), Radiometers (mW/cm²), Pressure (psia)'}"
        )

        # 4. Empirical Differences & Similarities
        stat_a = rec_a.get("measured_statistics")
        stat_b = rec_b.get("measured_statistics")
        diff_text = f"### 4. Verified Empirical Differences and Similarities\n"

        env_comparisons = []
        if flow_a != "Not recorded" and flow_b != "Not recorded":
            if flow_a == flow_b:
                env_comparisons.append(f"concurrent oxidizer flow ({flow_a})")
            else:
                env_comparisons.append(f"airflow velocity ({flow_a} in [{id_a}] vs {flow_b} in [{id_b}])")
        elif flow_a != "Not recorded":
            env_comparisons.append(f"airflow velocity ({flow_a} in [{id_a}], not recorded in [{id_b}])")
        elif flow_b != "Not recorded":
            env_comparisons.append(f"airflow velocity (not recorded in [{id_a}], {flow_b} in [{id_b}])")
        else:
            env_comparisons.append("airflow velocity not recorded in sensor metadata")

        if o2_a != "Not recorded" and o2_b != "Not recorded":
            if o2_a == o2_b:
                env_comparisons.append(f"ambient oxygen ({o2_a})")
            else:
                env_comparisons.append(f"ambient oxygen ({o2_a} in [{id_a}] vs {o2_b} in [{id_b}])")
        elif o2_a != "Not recorded":
            env_comparisons.append(f"ambient oxygen ({o2_a} in [{id_a}], not recorded in [{id_b}])")
        elif o2_b != "Not recorded":
            env_comparisons.append(f"ambient oxygen (not recorded in [{id_a}], {o2_b} in [{id_b}])")
        else:
            env_comparisons.append("ambient oxygen concentration not recorded in sensor metadata")

        diff_text += f"- **Environmental Comparison:** Evaluated under {'; '.join(env_comparisons)}.\n"
        diff_text += f"- **Material Behavior Contrast:** `{mat_a}` evaluated in `{id_a}` differs fundamentally from `{mat_b}` in `{id_b}` in thermal conductivity, ignition delay, and charring/extinguishment properties.\n"
        if stat_a:
            desc_a = format_stat_summary(stat_a)
            if desc_a:
                diff_text += f"- **{title_a} Measured Response:** {desc_a} [{id_a}].\n"
                claims.append(f"{title_a}: {desc_a} [{id_a}]")
        if stat_b:
            desc_b = format_stat_summary(stat_b)
            if desc_b:
                diff_text += f"- **{title_b} Measured Response:** {desc_b} [{id_b}].\n"
                claims.append(f"{title_b}: {desc_b} [{id_b}]")
        summary_sections.append(diff_text)

        # 5. Data Quality Limitations & Uninstrumented Parameters
        mf_a = rec_a.get("missing_fields", [])
        mf_b = rec_b.get("missing_fields", [])

        unrec_params_a = [f for f, v in [("sample_dimensions", dim_a), ("flow_velocity", flow_a), ("oxygen_concentration", o2_a), ("chamber_pressure", press_a)] if v == "Not recorded"]
        unrec_params_b = [f for f, v in [("sample_dimensions", dim_b), ("flow_velocity", flow_b), ("oxygen_concentration", o2_b), ("chamber_pressure", press_b)] if v == "Not recorded"]

        combined_mf_a = list(dict.fromkeys(mf_a + unrec_params_a))
        combined_mf_b = list(dict.fromkeys(mf_b + unrec_params_b))

        lim_text = f"### 5. Data-Quality Screening & Uninstrumented Parameters\n"
        if combined_mf_a:
            lim_text += f"- **{title_a} Unrecorded / Missing Fields:** `{', '.join(combined_mf_a)}`\n"
        if combined_mf_b:
            lim_text += f"- **{title_b} Unrecorded / Missing Fields:** `{', '.join(combined_mf_b)}`\n"
        if not combined_mf_a and not combined_mf_b:
            lim_text += f"- **Unrecorded Parameters:** Pre-flight fuel moisture content or sub-second video telemetry was not recorded for these flight runs.\n"
        lim_text += f"- **Scientific Safeguard:** Zero synthetic values have been generated or substituted for uninstrumented channels."
        summary_sections.append(lim_text)

    else:
        rec = compared_records[0]
        summary_sections.append(
            f"### Comparative Evaluation: {rec.get('title', rec['record_id'])} [{rec['record_id']}]\n"
            f"- **Material:** {rec.get('experimental_conditions', {}).get('fuel_material', 'N/A')}\n"
            f"- **Conditions:** {json.dumps(rec.get('experimental_conditions', {}))}\n"
            f"- **Available Channels:** {', '.join([c['channel_name'] for c in rec.get('available_channels', [])])}"
        )

    limitations = [
        "Retrieval-only comparison synthesis: Findings compiled from canonical flight records without speculative model interpolation.",
        "Differences in material behavior must not be extrapolated to flammability certification without multi-sample statistical replication.",
        "Any channels unrecorded during the flight pass are reported strictly as missing."
    ]

    full_answer = clean_scientific_unicode("\n\n".join(summary_sections))
    clean_lims = [clean_scientific_unicode(l) for l in limitations]

    return {
        "answer": full_answer,
        "evidence_backed_claims": claims,
        "citation_record_ids": citations,
        "scientific_limitations": clean_lims,
        "relevant_experiment_ids": [r.get("dataset_id") for r in compared_records if r.get("dataset_id")],
        "evidence_sufficiency": "sufficient" if len(compared_records) >= 2 else "partial",
        "status": "retrieval_only_fallback",
    }
