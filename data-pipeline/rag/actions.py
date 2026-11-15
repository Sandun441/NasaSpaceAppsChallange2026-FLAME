"""
NASA FLAME — Deterministic Research Tool Recommendation Engine (Phase R3)
Maps researcher questions and retrieved scientific evidence to actionable dashboard tools:
1. Scientific Data Visualization (Dataset Explorer)
2. Experiment Comparison Workspace
3. Research-Gap Detection
4. Fire Safety Equipment Research
5. Earth Applications
"""

from typing import List, Dict, Any, Optional, Union
import re
from rag.entity_resolution import DatasetEntityResolver
from modeling.analyzer import ResearchObjectiveAnalyzer


class ResearchToolRecommender:
    """
    Analyzes researcher intent and retrieved records to recommend relevant
    interactive tools within the NASA FLAME application.
    Uses real dataset IDs and verified frontend routing targets.
    """

    def __init__(self, entity_resolver: Optional[DatasetEntityResolver] = None):
        self.entity_resolver = entity_resolver or DatasetEntityResolver()
        self.modeling_analyzer = ResearchObjectiveAnalyzer()

    def recommend(
        self,
        question: str,
        retrieved_evidence: List[Dict[str, Any]],
        finding: Optional[Dict[str, Any]] = None,
        earth_evidence: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Produce 1 to 3 deterministic recommendations tailored to the researcher's query,
        active research gap finding, or Earth Applications inquiry.
        """
        q_lower = question.lower()

        # Check if greeting, casual conversational pleasantry, basic physical definition, or out-of-domain
        is_greeting = bool(re.search(
            r"\b(hi|hello|hey|greetings|howdy|good\s+(morning|afternoon|evening)|how\s+are\s+you|how\s+(are\s+)?you\s+doing|how('s|s)\s+it\s+going|thanks|thank\s+you|bye|goodbye)\b",
            q_lower
        ))
        is_casual = bool(re.search(
            r"\b(who\s+are\s+you|what\s+can\s+you\s+do|what\s+is\s+this|(can|could|will)\s+you\s+help\s+me(\s+study(\s+microgravity)?)?)\b",
            q_lower
        ))
        is_educational = bool(re.search(
            r"^\s*(what\s+is|what\s+are|define|explain|meaning\s+of)\s+(microgravity|buoyancy|buoyant\s+convection|buoyancy\s+decoupling|froude\s+number|richardson\s+number)\b|\b(explain\s+(it\s+)?(more\s+)?simply|make\s+it\s+simpler|simplify(\s+that)?|in\s+simpler\s+terms|eli5|explain\s+like\s+i('m|\s+am)\s+5|break\s+that\s+down)\b",
            q_lower
        ))
        out_of_domain = any(t in q_lower for t in [
            "capital of", "president of", "weather in", "recipe for", "football", "soccer", "stock price", "crypto", "joke"
        ])

        # Do not suggest research tools for greetings, casual greetings, or out-of-domain questions
        if (is_greeting or is_casual or is_educational or out_of_domain) and not any(
            k in q_lower for k in ["saffire", "bass", "flame", "burn", "spread", "oxygen", "temperature", "ignit", "smoke", "gap", "earth", "pmma", "cotton", "nomex"]
        ):
            return []

        recommendations = []
        rec_keys = set()

        # Check for follow-up comparison intent using conversation history
        is_followup_compare = bool(re.search(
            r"\b(compare\s+(those|them|these)|those\s+experiments|how\s+do\s+they\s+compare)\b",
            q_lower
        ))
        if is_followup_compare:
            hist_text = ""
            if conversation_history:
                hist_text = " ".join([m.get("content", "") for m in conversation_history if isinstance(m, dict)]).lower()
            if "saffire" in hist_text or not hist_text:
                rec_keys.add("comparison")
                recommendations.append({
                    "action_id": "open_experiment_comparison",
                    "tool_name": "Experiment Comparison",
                    "tab_id": "experiment-comparison",
                    "category": "Comparative Experiment Analysis",
                    "label": "Compare Saffire-III Sample 1 vs Sample 2",
                    "description": "Perform side-by-side parametric comparison of materials, flow, and sensor channels.",
                    "params": {
                        "exp1": "saffire_iii_sample_1",
                        "exp2": "saffire_iii_sample_2",
                    },
                    "icon": "GitCompare",
                })

        # If Earth Applications evidence is active/relevant, prioritize Earth Applications recommendations
        if earth_evidence:
            ev_list = [earth_evidence] if isinstance(earth_evidence, dict) else (earth_evidence or [])
            if ev_list:
                primary_ev = ev_list[0]
                ev_id = primary_ev.get("id", "")
                cat_id = primary_ev.get("category_id", "")
                title = primary_ev.get("title", "Earth Application Finding")
                inv_id = str(primary_ev.get("investigation_id", "")).lower()

                if "earth_apps" not in rec_keys:
                    rec_keys.add("earth_apps")
                    recommendations.append({
                        "action_id": "open_earth_applications",
                        "tool_name": "Earth Applications Research Explorer",
                        "tab_id": "earth-applications",
                        "category": "Terrestrial Research Transfer",
                        "label": f"Inspect Terrestrial Evidence: {ev_id}",
                        "description": f"Trace verified experimental observations and transfer caveats for {title}.",
                        "params": {
                            "evidence_id": ev_id,
                            "category_id": cat_id,
                            "evidence": primary_ev,
                        },
                        "icon": "Globe",
                    })

                if "saffire" in inv_id and "visualizer" not in rec_keys:
                    rec_keys.add("visualizer")
                    recommendations.append({
                        "action_id": "open_telemetry_visualizer",
                        "tool_name": "Scientific Telemetry Visualizer",
                        "tab_id": "dataset-explorer",
                        "category": "Sensor Telemetry Visualization",
                        "label": "Inspect Saffire Sensor Telemetry Arrays",
                        "description": "Examine radiant flux, thermocouple arrays, and duct airflow sensor traces supporting this research.",
                        "params": {
                            "dataset_id": "saffire_iii_sample_1",
                            "view": "visualize",
                        },
                        "icon": "LineChart",
                    })
                elif "bass" in inv_id and "modeling" not in rec_keys:
                    rec_keys.add("modeling")
                    recommendations.append({
                        "action_id": "open_modeling_extraction",
                        "tool_name": "Predictive-Modeling Data Extraction",
                        "tab_id": "modeling-extraction",
                        "category": "Machine Learning Data Preparation",
                        "label": "Audit BASS-II Modeling Records",
                        "description": "Inspect 129 discrete glovebox combustion records, stoichiometric parameters, and flame spread features.",
                        "params": {
                            "dataset_id": "bass_ii_experiments",
                        },
                        "icon": "Database",
                    })

        # If a deterministic research gap finding is active, prioritize gap and supporting experiment actions
        if finding:
            fid = finding.get("finding_id", "GAP-UNKNOWN")
            supp_exps = finding.get("supporting_experiment_ids", [])
            saffire_runs = [e for e in supp_exps if "saffire" in e]

            if saffire_runs and "visualizer" not in rec_keys:
                target_exp = saffire_runs[0]
                rec_keys.add("visualizer")
                recommendations.append({
                    "action_id": "open_telemetry_visualizer",
                    "tool_name": "Scientific Telemetry Visualizer",
                    "tab_id": "dataset-explorer",
                    "category": "Sensor Telemetry Visualization",
                    "label": f"Visualize Supporting Run: {target_exp}",
                    "description": "Inspect 30.3 Hz thermocouple arrays, radiant heat flux, and duct airflow telemetry.",
                    "params": {
                        "dataset_id": target_exp,
                        "view": "visualize",
                    },
                    "icon": "LineChart",
                })

            if len(supp_exps) >= 2 and "comparison" not in rec_keys:
                rec_keys.add("comparison")
                recommendations.append({
                    "action_id": "open_experiment_comparison",
                    "tool_name": "Experiment Comparison",
                    "tab_id": "experiment-comparison",
                    "category": "Comparative Experiment Analysis",
                    "label": f"Compare Supporting Runs: {supp_exps[0]} vs {supp_exps[1]}",
                    "description": "Perform side-by-side parametric comparison of materials, flow, and sensor channels.",
                    "params": {
                        "exp1": supp_exps[0],
                        "exp2": supp_exps[1],
                    },
                    "icon": "GitCompare",
                })

            if "gap_detection" not in rec_keys:
                rec_keys.add("gap_detection")
                recommendations.append({
                    "action_id": "open_gap_detection",
                    "tool_name": "Research-Gap Detection",
                    "tab_id": "gap-detection",
                    "category": "Coverage Heatmap",
                    "label": f"Inspect Gap Finding in Matrix: {fid}",
                    "description": "Analyze environmental coverage heatmaps, 5-factor heuristic breakdown, and database scope.",
                    "params": {
                        "finding_id": fid,
                        "gap_type": finding.get("gap_type"),
                        "sub_tab": "matrix",
                        "finding": finding,
                    },
                    "icon": "Layers",
                })

        # Deterministic entity resolution
        entities = self.entity_resolver.resolve(question)
        req_datasets = entities.get("requested_dataset_ids", [])
        unresolved = entities.get("unresolved_requested_entities", [])

        # Extract distinct available datasets from evidence
        unique_datasets = []
        for e in retrieved_evidence:
            ds = e.get("dataset_id")
            if ds and ds != "N/A" and ds not in unique_datasets:
                unique_datasets.append(ds)

        # Priority 1: explicitly requested datasets
        if len(req_datasets) >= 2:
            primary_ds = req_datasets[0]
            secondary_ds = req_datasets[1]
        elif len(req_datasets) == 1:
            primary_ds = req_datasets[0]
            # Choose compatible secondary dataset from evidence if available
            secondary_ds = next((d for d in unique_datasets if d != primary_ds), None)
            if not secondary_ds:
                secondary_ds = primary_ds
        elif unique_datasets:
            primary_ds = unique_datasets[0]
            secondary_ds = unique_datasets[1] if len(unique_datasets) > 1 else primary_ds
        else:
            primary_ds = "saffire_iii_sample_1"
            secondary_ds = "saffire_iii_sample_2"

        # Check for predictive modeling / ML feature extraction intent
        is_modeling = bool(re.search(
            r"\b(predict|predictive|model|modeling|train|supervised|machine learning|ml dataset|feature extraction|extract data|extract features|target variable|regression|classification|flame spread rate|spread rate prediction)\b",
            q_lower
        ))

        if is_modeling and "modeling" not in rec_keys:
            rec_keys.add("modeling")
            modeling_res = self.modeling_analyzer.interpret(question)
            target = modeling_res.get("target", {})
            evals = modeling_res.get("dataset_evaluations", [])
            top_eval = evals[0] if evals else None
            rec_ds = top_eval["dataset_id"] if top_eval else modeling_res.get("recommended_dataset_id", "bass_ii_experiments")

            if target.get("id"):
                label_text = f"Extract Modeling Data: {target['label']}"
                desc_text = f"Status: {target.get('status', 'MEASURED')}. Audit features, check leakage risks, and export records for {rec_ds}."
            else:
                label_text = f"Prepare Modeling Dataset: {rec_ds}"
                desc_text = "Audit available features, select variables, and export exploratory training records."

            recommendations.append({
                "action_id": "open_modeling_extraction",
                "tool_name": "Predictive-Modeling Data Extraction",
                "tab_id": "modeling-extraction",
                "category": "Machine Learning Data Preparation",
                "label": label_text,
                "description": desc_text,
                "params": {
                    "objective": question,
                    "dataset_id": rec_ds,
                    "target_id": target.get("id"),
                    "target_status": target.get("status"),
                    "target_label": target.get("label"),
                    "detected_features": modeling_res.get("detected_features", []),
                    "suitability": top_eval["suitability"] if top_eval else "EXPLORATORY_ONLY",
                    "scientific_explanation": top_eval["scientific_explanation"] if top_eval else "",
                },
                "icon": "Database",
            })

        # Check for continuous sensor or visualization intent
        is_viz = bool(re.search(
            r"\b(plot|chart|graph|visualiz|time series|sensor|thermocouple|radiometer|trace|signal|reading|channel|temperature|pressure|heat flux|current)\b",
            q_lower
        )) or any(e.get("record_type") in ("channel_group", "dataset") for e in retrieved_evidence[:3])

        if is_viz and "visualization" not in rec_keys and primary_ds:
            rec_keys.add("visualization")
            label_text = f"Inspect {primary_ds} in Live Data Viewer" if primary_ds != "bass_ii_experiments" else "Inspect BASS-II Matrix in Dataset Explorer"
            recommendations.append({
                "action_id": "open_visualization",
                "tool_name": "Scientific Data Visualization",
                "tab_id": "dataset-explorer",
                "category": "Visualization & Waveforms",
                "label": label_text,
                "description": f"Plot calibrated measurements and multi-channel waveforms for {primary_ds}.",
                "params": {
                    "dataset_id": primary_ds,
                    "view_mode": "visualization" if primary_ds != "bass_ii_experiments" else "table",
                },
                "icon": "LineChart",
            })

        # Check for comparison intent
        is_compare = entities.get("is_comparison", False) or bool(re.search(
            r"\b(compar|differ|versus|vs|against|contrast|pmma.*cotton|sibal.*nomex|flow restrictor|sample 1.*sample 2)\b",
            q_lower
        )) or len(req_datasets) >= 2 or (not unresolved and len(unique_datasets) >= 2)

        # Do not recommend comparison of arbitrary datasets if the user requested an unindexed sample
        if is_compare and not unresolved and "comparison" not in rec_keys:
            compat = self.entity_resolver.validate_comparison_compatibility(primary_ds, secondary_ds)
            if compat.get("is_compatible", False):
                rec_keys.add("comparison")
                if primary_ds == "bass_ii_experiments" and secondary_ds == "bass_ii_experiments":
                    comp_label = "Compare Solid Fuel Tests in BASS-II Matrix"
                    comp_desc = "Contrast gas deltas (ΔO₂, ΔCO₂), flow restrictors, and fuel materials across discrete ISS Glovebox runs."
                    alignment_mode = "bass_matrix_comparison"
                else:
                    comp_label = f"Compare {primary_ds} vs {secondary_ds}"
                    comp_desc = f"Perform side-by-side or event-aligned overlay comparison using shared physical sensor channels."
                    alignment_mode = compat.get("default_mode", "overlay_event_aligned")

                recommendations.append({
                    "action_id": "open_comparison",
                    "tool_name": "Experiment Comparison Workspace",
                    "tab_id": "experiment-comparison",
                    "category": "Cross-Experiment Analysis",
                    "label": comp_label,
                    "description": comp_desc,
                    "params": {
                        "dataset_a": primary_ds,
                        "dataset_b": secondary_ds,
                        "alignment": alignment_mode,
                        "supported_modes": compat.get("supported_modes", []),
                        "shared_channels": compat.get("shared_channels", []),
                    },
                    "icon": "GitCompare",
                })

        # Check for equipment / fire safety engineering intent
        is_equipment = bool(re.search(
            r"\b(equipment|smoke\w*|detect\w*|fiz\w*|extinguish\w*|suppress\w*|alarm\w*|ventilat\w*|sensor response|fire prevention|flammab\w*|fire safety\w*)\b",
            q_lower
        )) or any("smoke" in str(e).lower() for e in retrieved_evidence[:3])

        if is_equipment and "equipment" not in rec_keys:
            rec_keys.add("equipment")
            # Determine category focus
            if any(k in q_lower for k in ("extinguish", "suppress", "quench", "starvation", "blowoff")):
                eq_cat = "suppression"
                eq_label = "Investigate Spacecraft Fire Suppression & Extinction Limits"
                eq_desc = "Analyze low-flow flame starvation, blow-off velocity limits, and gaseous diluent suppression in microgravity."
            elif any(k in q_lower for k in ("prevent", "material", "flammab", "loi", "nomex", "pmma", "fuel")):
                eq_cat = "prevention"
                eq_label = "Evaluate Material Flammability & Fire Prevention Limits"
                eq_desc = "Inspect microgravity ignition thresholds, oxygen concentration limits, and solid fuel combustion behavior."
            else:
                eq_cat = "detection"
                eq_label = "Investigate Spacecraft Fire Detection & Sensor Response"
                eq_desc = "Examine Cygnus smoke detector scatterometer signals, Saffire radiometers, and particulate transport in return ducts."

            recommendations.append({
                "action_id": "open_equipment_research",
                "tool_name": "Fire-Safety Equipment Research",
                "tab_id": "equipment-research",
                "category": "Hardware & Life Support",
                "label": eq_label,
                "description": eq_desc,
                "params": {
                    "objective": question,
                    "category": eq_cat,
                    "focus": eq_cat,
                    "evidence_ids": [e.get("record_id") for e in retrieved_evidence[:3] if e.get("record_id")],
                },
                "icon": "ShieldAlert",
            })

        # Check for gap detection / lunar / partial gravity / unexplored regime intent
        is_gap = bool(re.search(
            r"\b(gap|gaps|unexplored|partial gravity|lunar|mars|0.16g|0.38g|regime|coverage|boundary|limit|threshold|quiescent)\b",
            q_lower
        ))

        if is_gap and "gap_detection" not in rec_keys:
            rec_keys.add("gap_detection")
            recommendations.append({
                "action_id": "open_gap_detection",
                "tool_name": "Research-Gap Detection",
                "tab_id": "gap-detection",
                "category": "Exploration Roadmap",
                "label": "Analyze Combustion Environmental Coverage Heatmap",
                "description": "Map investigated microgravity data against unexplored lunar (0.16g) and Martian (0.38g) partial gravity conditions.",
                "params": {
                    "focus": "partial_gravity",
                },
                "icon": "Layers",
            })

        # Check for Earth applications / terrestrial transfer intent
        is_earth = bool(re.search(
            r"\b(earth|terrestrial|mine|wildfire|industrial|hazard|transfer|halon|water mist|ground)\b",
            q_lower
        ))

        if is_earth and "earth_apps" not in rec_keys:
            rec_keys.add("earth_apps")
            recommendations.append({
                "action_id": "open_earth_applications",
                "tool_name": "Earth Applications",
                "tab_id": "earth-applications",
                "category": "Terrestrial Hazard Transfer",
                "label": "Explore Earth Hazard & Suppression Applications",
                "description": "Translate microgravity soot and buoyancy-free flame insights to terrestrial mine safety and clean suppression.",
                "params": {},
                "icon": "Globe",
            })

        # Default fallback recommendation if none triggered
        if not recommendations:
            recommendations.append({
                "action_id": "open_dataset_explorer",
                "tool_name": "Live Dataset Explorer",
                "tab_id": "dataset-explorer",
                "category": "Catalog Browsing",
                "label": f"Explore Dataset: {primary_ds}",
                "description": "Browse verified measurement records, channel schema, and provenance metadata.",
                "params": {
                    "dataset_id": primary_ds,
                },
                "icon": "Database",
            })

        return recommendations[:3]
