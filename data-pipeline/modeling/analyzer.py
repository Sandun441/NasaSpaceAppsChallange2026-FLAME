"""
NASA FLAME — Predictive-Modeling Research Objective Analyzer
Interprets natural-language researcher requests into structured predictive modeling specifications:
- Identifies intended prediction target, candidate input features, and experiment conditions
- Distinguishes verified measured labels, validated derived features, metadata, and uninstrumented parameters
- Evaluates dataset suitability: ELIGIBLE_SUPERVISED, EXPLORATORY_ONLY, TARGET_UNAVAILABLE, INCOMPATIBLE_OBJECTIVE
- Operates deterministically with or without Gemini API key
- Explicitly flags uninstrumented targets (e.g. flame spread rate in sensor logs) with scientifically grounded explanations
"""

from typing import Dict, Any, List, Optional
import re
from modeling.registry import MODELING_DATASETS_REGISTRY


class ResearchObjectiveAnalyzer:
    """
    Analyzes natural-language modeling requests against real NASA experimental schemas.
    """

    TARGET_TAXONOMY = [
        {
            "id": "flame_spread_rate_cm_s",
            "keywords": [
                r"\bflame spread rate\b",
                r"\bflame spread\b",
                r"\bspread rate\b",
                r"\bflame speed\b",
                r"\bflame velocity\b",
                r"\bpropagation rate\b",
                r"\bpropagation speed\b",
            ],
            "label": "Flame Spread Rate",
            "unit": "cm/s",
            "status": "UNINSTRUMENTED_UNAVAILABLE",
            "explanation": "Flame spread rate is unrecorded in continuous sensor logs and the BASS-II matrix. Tracking flame front velocity requires optical video photogrammetry.",
            "alternatives": ["oxygen_consumption_delta_pct", "peak_plume_temperature_c"],
        },
        {
            "id": "exact_extinction_time_s",
            "keywords": [
                r"\bextinction time\b",
                r"\btime to extinguish\b",
                r"\btime of extinction\b",
                r"\bquench time\b",
            ],
            "label": "Exact Extinction Time",
            "unit": "s",
            "status": "UNINSTRUMENTED_UNAVAILABLE",
            "explanation": "Exact extinction time is not recorded as a sensor channel. In BASS-II, only total frames shot is recorded. In Saffire, thermocouple decay indicates cooling, but exact flame extinction requires optical verification.",
            "alternatives": ["final_oxygen_pct", "oxygen_consumption_delta_pct"],
        },
        {
            "id": "oxygen_consumption_delta_pct",
            "keywords": [
                r"\boxygen consumption\b",
                r"\bdelta o2\b",
                r"\bo2 delta\b",
                r"\boxygen delta\b",
                r"\bo2 depletion\b",
                r"\boxygen depletion\b",
            ],
            "label": "Oxygen Consumption Delta (ΔO₂)",
            "unit": "% vol",
            "status": "VALIDATED_DERIVED",
            "explanation": "Verified combustion consumption metric calculated as calibrated initial O₂ minus final O₂.",
            "alternatives": [],
        },
        {
            "id": "co2_generation_delta_pct",
            "keywords": [
                r"\bco2 generation\b",
                r"\bco2 production\b",
                r"\bdelta co2\b",
                r"\bco2 delta\b",
                r"\bcarbon dioxide generation\b",
            ],
            "label": "CO₂ Generation Delta (ΔCO₂)",
            "unit": "% vol",
            "status": "VALIDATED_DERIVED",
            "explanation": "Verified combustion product metric calculated as final CO₂ minus initial CO₂.",
            "alternatives": [],
        },
        {
            "id": "final_co_ppm",
            "keywords": [
                r"\bco emission\b",
                r"\bcarbon monoxide emission\b",
                r"\bfinal co\b",
                r"\bco ppm\b",
                r"\bcarbon monoxide level\b",
            ],
            "label": "Final CO Emission",
            "unit": "ppm",
            "status": "VERIFIED_MEASURED",
            "explanation": "Directly measured post-combustion toxic gas emission level.",
            "alternatives": [],
        },
        {
            "id": "peak_plume_temperature_c",
            "keywords": [
                r"\bpeak temperature\b",
                r"\bmax temperature\b",
                r"\bmaximum temperature\b",
                r"\bflame temperature\b",
                r"\bplume temperature\b",
                r"\bthermal peak\b",
            ],
            "label": "Peak Plume Temperature",
            "unit": "°C",
            "status": "VERIFIED_MEASURED",
            "explanation": "Directly measured maximum exhaust thermocouple temperature reached during burn.",
            "alternatives": [],
        },
        {
            "id": "peak_radiant_heat_flux_mw_cm2",
            "keywords": [
                r"\bradiant heat flux\b",
                r"\bheat flux\b",
                r"\bradiometer peak\b",
                r"\bthermal radiation\b",
                r"\bflux peak\b",
            ],
            "label": "Peak Radiant Heat Flux",
            "unit": "mW/cm²",
            "status": "VERIFIED_MEASURED",
            "explanation": "Directly measured maximum broadband radiant thermal emission to tunnel wall.",
            "alternatives": [],
        },
        {
            "id": "smoke_detector_obscuration_fiz1_v",
            "keywords": [
                r"\bsmoke detector\b",
                r"\bobscuration\b",
                r"\bfiz\b",
                r"\bscatterometer\b",
                r"\bsmoke obscuration\b",
            ],
            "label": "Smoke Detector Obscuration Voltage",
            "unit": "V",
            "status": "VERIFIED_MEASURED",
            "explanation": "Directly measured photodiode obscuration voltage response in Cygnus smoke detector.",
            "alternatives": [],
        },
    ]

    FEATURE_TAXONOMY = [
        {
            "id": "oxygen_concentration",
            "keywords": [r"\boxygen\b", r"\bo2\b", r"\box\b", r"\boxygen concentration\b"],
            "label": "Oxygen Concentration",
            "mappings": {
                "bass_ii_experiments": "initial_oxygen_pct",
                "saffire_iii_sample_1": "oxygen_concentration_pct",
                "saffire_iii_sample_2": "oxygen_concentration_pct",
            }
        },
        {
            "id": "airflow_velocity",
            "keywords": [r"\bairflow\b", r"\bair flow\b", r"\bvelocity\b", r"\bflow speed\b", r"\bventilation\b", r"\bconvection\b"],
            "label": "Airflow Velocity",
            "mappings": {
                "bass_ii_experiments": "airflow_velocity_proxy",
                "saffire_iii_sample_1": "flow_velocity_cm_s",
                "saffire_iii_sample_2": "flow_velocity_cm_s",
            }
        },
        {
            "id": "fuel_material",
            "keywords": [r"\bfuel\b", r"\bmaterial\b", r"\bpmma\b", r"\bcotton\b", r"\bsibal\b", r"\bnomex\b", r"\bthickness\b", r"\bsample\b"],
            "label": "Fuel Material & Geometry",
            "mappings": {
                "bass_ii_experiments": "fuel_material",
                "saffire_iii_sample_1": None,  # Fixed material (Sibal)
                "saffire_iii_sample_2": None,  # Fixed material (PMMA/Nomex)
            }
        },
        {
            "id": "ambient_pressure",
            "keywords": [r"\bpressure\b", r"\bpsia\b", r"\bpsi\b", r"\bchamber pressure\b"],
            "label": "Ambient Pressure",
            "mappings": {
                "bass_ii_experiments": None,  # Constant ~1 atm in MSG
                "saffire_iii_sample_1": "ambient_pressure_psia",
                "saffire_iii_sample_2": "ambient_pressure_psia",
                "telemetry_cygnus_data": "cabin_pressure_psi",
            }
        },
        {
            "id": "co2_concentration",
            "keywords": [r"\bco2\b", r"\bcarbon dioxide\b"],
            "label": "CO₂ Concentration",
            "mappings": {
                "bass_ii_experiments": "initial_co2_pct",
                "saffire_iii_sample_1": "co2_concentration_pct",
            }
        },
        {
            "id": "temperatures",
            "keywords": [r"\btemperature\b", r"\bthermocouple\b", r"\bthermal\b", r"\bplume temp\b"],
            "label": "Plume / Surface Temperature",
            "mappings": {
                "saffire_iii_sample_1": "plume_temp_tc1",
                "saffire_iii_sample_2": "plume_temp_tc1",
                "telemetry_cygnus_data": "cabin_air_temp_c",
            }
        },
        {
            "id": "heat_flux",
            "keywords": [r"\bradiometer\b", r"\bheat flux\b", r"\bradiation\b"],
            "label": "Radiant Heat Flux",
            "mappings": {
                "bass_ii_experiments": "radiometer_gain",
                "saffire_iii_sample_1": "radiometer_1",
                "saffire_iii_sample_2": "radiometer_1",
            }
        },
    ]

    def interpret(self, query: str) -> Dict[str, Any]:
        """
        Parse natural-language query and return structured prediction specification and dataset evaluations.
        """
        q = (query or "").strip().lower()

        # 1. Identify Target
        detected_target = None
        for t_spec in self.TARGET_TAXONOMY:
            for pat in t_spec["keywords"]:
                if re.search(pat, q):
                    detected_target = t_spec
                    break
            if detected_target:
                break

        # 2. Identify Requested Features
        detected_features = []
        for f_spec in self.FEATURE_TAXONOMY:
            for pat in f_spec["keywords"]:
                if re.search(pat, q):
                    detected_features.append(f_spec)
                    break

        # 3. Detect Material / Environment Filters
        material_filter = None
        if "pmma" in q:
            material_filter = "PMMA"
        elif "cotton" in q:
            material_filter = "Cotton"
        elif "sibal" in q:
            material_filter = "Sibal cloth"
        elif "nomex" in q:
            material_filter = "Nomex"

        # 4. Evaluate each dataset
        evaluations = []
        for ds_id, ds in MODELING_DATASETS_REGISTRY.items():
            eval_res = self._evaluate_dataset(ds, detected_target, detected_features, q)
            evaluations.append(eval_res)

        # Sort evaluations: ELIGIBLE_SUPERVISED first, then EXPLORATORY_ONLY, then TARGET_UNAVAILABLE
        rank_order = {
            "ELIGIBLE_SUPERVISED": 0,
            "EXPLORATORY_ONLY": 1,
            "TARGET_UNAVAILABLE": 2,
            "INCOMPATIBLE_OBJECTIVE": 3,
        }
        evaluations.sort(key=lambda x: rank_order.get(x["suitability"], 99))

        # Overall synthesis
        if detected_target:
            target_status = detected_target["status"]
            target_label = detected_target["label"]
            target_id = detected_target["id"]
            target_explanation = detected_target["explanation"]
            suggested_alternatives = detected_target["alternatives"]
        else:
            target_status = "NOT_SPECIFIED"
            target_label = "Unsupervised / Exploratory Feature Extraction"
            target_id = None
            target_explanation = "No specific prediction target identified in query. Data extraction will proceed in exploratory/feature-extraction mode."
            suggested_alternatives = ["oxygen_consumption_delta_pct", "peak_plume_temperature_c"]

        return {
            "query": query,
            "target": {
                "id": target_id,
                "label": target_label,
                "status": target_status,
                "unit": detected_target["unit"] if detected_target else None,
                "explanation": target_explanation,
                "suggested_alternatives": suggested_alternatives,
            },
            "detected_features": [f["label"] for f in detected_features],
            "material_filter": material_filter,
            "dataset_evaluations": evaluations,
            "recommended_dataset_id": evaluations[0]["dataset_id"] if evaluations else "bass_ii_experiments",
        }

    def _evaluate_dataset(
        self,
        ds: Dict[str, Any],
        detected_target: Optional[Dict[str, Any]],
        detected_features: List[Dict[str, Any]],
        raw_query: str,
    ) -> Dict[str, Any]:
        """
        Determine dataset suitability for the identified objective.
        """
        ds_id = ds["dataset_id"]
        supported_targets = {t["id"]: t for t in ds.get("supported_targets", [])}
        unsupported_targets = {t["id"]: t for t in ds.get("unsupported_targets", [])}
        available_features = {f["id"]: f for f in ds.get("available_features", [])}

        matching_features = []
        for feat in detected_features:
            col_id = feat["mappings"].get(ds_id)
            if col_id and col_id in available_features:
                matching_features.append(available_features[col_id])

        # If no target specified, exploratory only
        if not detected_target or not detected_target["id"]:
            suitability = "EXPLORATORY_ONLY"
            scientific_explanation = (
                f"{ds['name']} contains {len(matching_features)} matching physical variables "
                f"across {ds['total_records']} experimental records suitable for unsupervised or exploratory modeling."
            )
            target_availability = "No target requested. Exploratory mode available."
            return {
                "dataset_id": ds_id,
                "name": ds["name"],
                "investigation": ds["investigation"],
                "paradigm": ds["paradigm"],
                "total_records": ds["total_records"],
                "suitability": suitability,
                "target_availability": target_availability,
                "matching_features": matching_features,
                "scientific_explanation": scientific_explanation,
                "leakage_guidance": ds.get("leakage_guidance", ""),
            }

        target_id = detected_target["id"]

        # Check if target is explicitly unsupported in this dataset
        if target_id in unsupported_targets:
            unsupported_info = unsupported_targets[target_id]
            suitability = "TARGET_UNAVAILABLE"
            scientific_explanation = (
                f"Target '{detected_target['label']}' is unrecorded in {ds['name']}. "
                f"{unsupported_info['reason']} "
                f"You can export this dataset for exploratory analysis without supervised target labels."
            )
            target_availability = f"UNINSTRUMENTED: {unsupported_info['reason']}"
        elif target_id in supported_targets:
            target_info = supported_targets[target_id]
            suitability = "ELIGIBLE_SUPERVISED"
            scientific_explanation = (
                f"Target '{target_info['label']}' is {target_info['category'].replace('_', ' ')} "
                f"in {ds['name']} ({ds['total_records']} records). "
                f"{len(matching_features)} requested input features are directly available."
            )
            target_availability = f"AVAILABLE: {target_info['label']} ({target_info['unit']})"
        else:
            # Target is not relevant to this dataset
            suitability = "INCOMPATIBLE_OBJECTIVE"
            scientific_explanation = (
                f"{ds['name']} does not measure or derive target '{detected_target['label']}'. "
                f"This dataset is intended for {ds['paradigm'].replace('_', ' ')}."
            )
            target_availability = "NOT_APPLICABLE"

        return {
            "dataset_id": ds_id,
            "name": ds["name"],
            "investigation": ds["investigation"],
            "paradigm": ds["paradigm"],
            "total_records": ds["total_records"],
            "suitability": suitability,
            "target_availability": target_availability,
            "matching_features": matching_features,
            "scientific_explanation": scientific_explanation,
            "leakage_guidance": ds.get("leakage_guidance", ""),
        }
