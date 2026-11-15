"""
NASA FLAME — Scientific Intent Interpreter (Phase F2)
Extracts, validates, and resolves scientific entities, datasets, channels, time windows,
and target workspaces from natural-language researcher requests against verified NASA catalogs.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from prompt_system.models import InterpretedScientificIntent

# Canonical Dataset Mapping
DATASET_PATTERNS = [
    {
        "id": "saffire_iii_sample_1",
        "investigation_id": "saffire_iii",
        "keywords": [
            r"\bsaffire[- ]?(?:iii|3)?[- ]?sample[- ]?1\b",
            r"\bsaffire[- ]?1\b",
            r"\bsample[- ]?1\b",
            r"\bsaffire[- ]?(?:iii|3)\b",
        ],
        "default_channels": ["Radiometer 1", "Plume Temp 3 (TC3)"],
        "ignition_window": [50.0, 120.0],
        "full_window": [0.0, 689.96],
    },
    {
        "id": "saffire_iii_sample_2",
        "investigation_id": "saffire_iii",
        "keywords": [
            r"\bsaffire[- ]?(?:iii|3)?[- ]?sample[- ]?2\b",
            r"\bsaffire[- ]?2\b",
            r"\bsample[- ]?2\b",
        ],
        "default_channels": ["Radiometer 1", "Plume Temp 1 (TC1)"],
        "ignition_window": [15.0, 80.0],
        "full_window": [0.0, 159.95],
    },
    {
        "id": "saffire_sample_5",
        "investigation_id": "saffire_iii",
        "keywords": [r"\bsaffire[- ]?5\b", r"\bsample[- ]?5\b"],
        "default_channels": ["TC1", "TC2"],
        "ignition_window": [0.0, 100.0],
        "full_window": [0.0, 300.0],
    },
    {
        "id": "saffire_sample_6",
        "investigation_id": "saffire_iii",
        "keywords": [r"\bsaffire[- ]?6\b", r"\bsample[- ]?6\b"],
        "default_channels": ["TC1", "TC2"],
        "ignition_window": [0.0, 100.0],
        "full_window": [0.0, 300.0],
    },
    {
        "id": "bass_ii_experiments",
        "investigation_id": "bass_ii",
        "keywords": [
            r"\bbass[- ]?(?:ii|2)?\b",
            r"\bburning and suppression of solids\b",
            r"\bpmma\b",
            r"\bcotton\b",
            r"\bnomex\b",
            r"\bglovebox\b",
        ],
        "default_channels": ["Material", "Airflow_Display_Proxy", "Calibrated_Initial_O2_Pct"],
        "ignition_window": None,
        "full_window": None,
    },
    {
        "id": "telemetry_cygnus_smoke_detector_data",
        "investigation_id": "cygnus_vehicle_telemetry",
        "keywords": [
            r"\bcygnus smoke\b",
            r"\bvehicle smoke detector\b",
            r"\bfiz\b",
            r"\bobscuration\b",
        ],
        "default_channels": ["Smoke_Detector_Scatterometer_FIZ2_V", "Smoke_Detector_Obscuration_FIZ2_V"],
        "ignition_window": [0.0, 1000.0],
        "full_window": [0.0, 3600.0],
    },
    {
        "id": "telemetry_cygnus_pressure_data",
        "investigation_id": "cygnus_vehicle_telemetry",
        "keywords": [r"\bcygnus pressure\b", r"\bcabin pressure\b"],
        "default_channels": ["Cabin_Pressure_PSIA"],
        "ignition_window": [0.0, 1000.0],
        "full_window": [0.0, 3600.0],
    },
    {
        "id": "telemetry_cygnus_temperature_data",
        "investigation_id": "cygnus_vehicle_telemetry",
        "keywords": [r"\bcygnus temp\b", r"\bcabin temp\b"],
        "default_channels": ["PCM_Air_Temp_C"],
        "ignition_window": [0.0, 1000.0],
        "full_window": [0.0, 3600.0],
    },
]

# Channel Synonyms & Units
CHANNEL_DICTIONARY = {
    "radiometer_1": {
        "canonical": "Radiometer 1",
        "units": "mW/cm²",
        "label": "Radiometer 1 (Broadband Radiant Flux)",
        "patterns": [r"\bradiometer\s*1\b", r"\bradiometer\b", r"\bradiant\s*(?:heat\s*)?flux\b", r"\bradiant\s*emission\b"],
    },
    "radiometer_2": {
        "canonical": "Radiometer 2",
        "units": "mW/cm²",
        "label": "Radiometer 2 (Broadband Radiant Flux)",
        "patterns": [r"\bradiometer\s*2\b"],
    },
    "radiometer_3": {
        "canonical": "Radiometer 3",
        "units": "mW/cm²",
        "label": "Radiometer 3 (Broadband Radiant Flux)",
        "patterns": [r"\bradiometer\s*3\b"],
    },
    "radiometer_4": {
        "canonical": "Radiometer 4",
        "units": "mW/cm²",
        "label": "Radiometer 4 (Broadband Radiant Flux)",
        "patterns": [r"\bradiometer\s*4\b"],
    },
    "tc1": {
        "canonical": "Plume Temp 1 (TC1)",
        "units": "°C",
        "label": "Plume Thermocouple 1 (TC1)",
        "patterns": [r"\btc1\b", r"\btc\s*1\b", r"\bthermocouple\s*1\b", r"\bplume\s*temp\s*1\b"],
    },
    "tc2": {
        "canonical": "Plume Temp 2 (TC2)",
        "units": "°C",
        "label": "Plume Thermocouple 2 (TC2)",
        "patterns": [r"\btc2\b", r"\btc\s*2\b", r"\bthermocouple\s*2\b", r"\bplume\s*temp\s*2\b"],
    },
    "tc3": {
        "canonical": "Plume Temp 3 (TC3)",
        "units": "°C",
        "label": "Plume Thermocouple 3 (TC3 Downstream)",
        "patterns": [r"\btc3\b", r"\btc\s*3\b", r"\bthermocouple\s*3\b", r"\bplume\s*temp\s*3\b", r"\bdownstream\s*thermocouple\b"],
    },
    "tc4": {
        "canonical": "Plume Temp 4 (TC4)",
        "units": "°C",
        "label": "Plume Thermocouple 4 (TC4)",
        "patterns": [r"\btc4\b", r"\btc\s*4\b", r"\bthermocouple\s*4\b"],
    },
    "general_temperatures": {
        "canonical": "Plume Temp 3 (TC3)",
        "units": "°C",
        "label": "Plume Thermocouple Temperatures",
        "patterns": [r"\bthermocouple\s*temperatures?\b", r"\bthermocouples?\b", r"\btemperatures?\b", r"\bthermal\s*rise\b"],
    },
    "anemometer_1": {
        "canonical": "Anemometer 1",
        "units": "cm/s",
        "label": "Anemometer 1 (Duct Airflow Velocity)",
        "patterns": [
            r"\banemometer\s*1\b",
            r"\banemometer\b",
            r"\bairflow\s*velocity\b",
            r"\bairflow\b",
            r"\bflow\s*speed\b",
            r"\bflow\s*velocity\b",
            r"\bforced\s*flow\b",
            r"\bduct\s*flow\b",
        ],
    },
    "anemometer_2": {
        "canonical": "Anemometer 2",
        "units": "cm/s",
        "label": "Anemometer 2 (Duct Airflow Velocity)",
        "patterns": [r"\banemometer\s*2\b"],
    },
    "average_fan_speed": {
        "canonical": "Average Fan Speed",
        "units": "RPM",
        "label": "Average Duct Fan Speed",
        "patterns": [r"\bfan\s*speed\b", r"\bblower\s*speed\b", r"\btachometer\b"],
    },
    "inlet_temp": {
        "canonical": "Test Section Inlet Temp",
        "units": "°C",
        "label": "Test Section Inlet Air Temperature",
        "patterns": [r"\binlet\s*temp\w*\b", r"\bduct\s*inlet\s*temp\w*\b"],
    },
    "ambient_pressure": {
        "canonical": "Ambient Pressure",
        "units": "PSIA",
        "label": "Ambient Duct Pressure",
        "patterns": [r"\bambient\s*pressure\b", r"\bpressure\b", r"\bpsia\b"],
    },
    "o2": {
        "canonical": "O2",
        "units": "% vol",
        "label": "Oxygen Concentration (O₂)",
        "patterns": [r"\boxygen\b", r"\bo2\b", r"\boxygen\s*percentage\b"],
    },
    "co2": {
        "canonical": "CO2",
        "units": "% vol",
        "label": "Carbon Dioxide Concentration (CO₂)",
        "patterns": [r"\bco2\b", r"\bcarbon\s*dioxide\b"],
    },
}

# Workspace Intent Signatures
WORKSPACE_PATTERNS = [
    {
        "workspace": "comparison",
        "priority": 10,
        "keywords": [
            r"\bcompar\w*\b",
            r"\bdifference\s+between\b",
            r"\bversus\b",
            r"\bvs\.?\b",
            r"\bdelta\s+between\b",
            r"\bside[- ]by[- ]side\b",
            r"\boverlay\b",
        ],
    },
    {
        "workspace": "modeling",
        "priority": 9,
        "keywords": [
            r"\bpredict\w*\b",
            r"\bmodel(?:ing|s)?\b",
            r"\bmachine\s+learning\b",
            r"\bml\b",
            r"\bfeatures?\b",
            r"\btarget\b",
            r"\bexport\s+(?:\w+\s+)*(?:data|csv|for\s+ml)\b",
            r"\bprepare\s+(?:\w+\s+)*(?:data|dataset|features)\b",
            r"\bdata\s+extraction\b",
            r"\bleakage\b",
            r"\bsupervised\b",
            r"\bregression\b",
            r"\btrain(?:ing)?\b",
        ],
    },
    {
        "workspace": "visualization",
        "priority": 8,
        "keywords": [
            r"\bplot\w*\b",
            r"\bvisualiz\w*\b",
            r"\bgraph\w*\b",
            r"\bchart\w*\b",
            r"\bcurves?\b",
            r"\btime[- ]series\b",
            r"\btelemetry\b",
            r"\bdisplay\s+channel\b",
            r"\bsensor\s+data\b",
        ],
    },
    {
        "workspace": "gap_detection",
        "priority": 7,
        "keywords": [
            r"\bresearch\s+gap\w*\b",
            r"\bgap\w*\b",
            r"\bcoverage\b",
            r"\bunexplored\b",
            r"\bmissing\b",
            r"\bsparse\b",
            r"\bunrepresented\b",
            r"\bmissing\s+(?:\w+\s+)*(?:experiment|coverage|data|regime)\b",
            r"\bregimes?\b",
            r"\blunar\s+gravity\b",
            r"\bmars\s+gravity\b",
            r"\bpartial\s+gravity\b",
            r"\b0\.16g\b",
            r"\b0\.38g\b",
            r"\buntested\b",
        ],
    },
    {
        "workspace": "equipment",
        "priority": 6,
        "keywords": [
            r"\bsmoke\s+detect\w*\b",
            r"\bfire\s+detect\w*\b",
            r"\bextinguish\w*\b",
            r"\bsuppression\s+system\b",
            r"\bspacecraft\s+(?:smoke|hardware|equipment|detector|fire)\b",
            r"\bfire[- ]safety\s+equipment\b",
            r"\boptocoupler\b",
            r"\bscatterometer\b",
            r"\bobscuration\b",
            r"\balarm\b",
            r"\bfire\s+suppression\b",
            r"\bfire\s+prevention\b",
            r"\bdetector\s+placement\b",
            r"\bcabin\s+ventilation\b",
            r"\bflow\s+duct\b",
            r"\bradiometer\s+(?:detection|peak|flux)\b",
            r"\bflame\s+quenching\b",
            r"\bparticulate\s+agglomeration\b",
        ],
    },
    {
        "workspace": "earth_applications",
        "priority": 6,
        "keywords": [
            r"\bearth\b",
            r"\bterrestrial\b",
            r"\bwildfire\w*\b",
            r"\bbuilding\s+fire\w*\b",
            r"\bventilation\s+ducts?\b",
            r"\bindustrial\s+safety\b",
            r"\bterrestrial\s+transfer\b",
            r"\bmine\s+fire\w*\b",
            r"\bcleanroom\b",
            r"\bground[- ]based\b",
            r"\bbuoyancy[- ]free\b",
            r"\bconduit\s+flame\b",
            r"\bconnection\s+bridge\b",
            r"\bsoot\s+emissions?\b",
            r"\bcool[- ]flame\s+kinetics\b",
            r"\bpolymer\s+pyrolysis\b",
            r"\btransfer\s+limitations?\b",
        ],
    },
]


class PromptIntentInterpreter:
    """
    Interprets natural-language scientific requests against NASA FLAME datasets and services.
    """

    def interpret(
        self,
        objective: str,
        workspace_preference: str = "auto",
        context_filters: Optional[Dict[str, Any]] = None,
    ) -> InterpretedScientificIntent:
        """
        Parses an objective into an InterpretedScientificIntent.
        """
        q = (objective or "").strip()
        q_lower = q.lower()

        # Handle empty or trivial prompts
        if not q:
            return InterpretedScientificIntent(
                target_workspace=workspace_preference if workspace_preference != "auto" else "visualization",
                confidence=0.0,
                intent_summary="Empty research request received",
                needs_clarification=True,
                clarification_prompt="Please specify a research question, target measurement, or NASA experiment to analyze.",
                candidate_options=[
                    "Plot Saffire-III Sample 1 radiant heat flux and thermocouple temperatures during ignition.",
                    "Compare Saffire-III Sample 1 and Sample 2 temperature behavior.",
                    "Prepare BASS-II data for predicting flame behavior from oxygen and airflow.",
                    "Find missing experimental coverage for low oxygen and low airflow."
                ]
            )

        # Handle adversarial prompt injection attempt
        if re.search(r"\b(ignore\s+previous|system\s+prompt|dan\s+mode|jailbreak|pretend\s+to\s+be)\b", q_lower):
            return InterpretedScientificIntent(
                target_workspace=workspace_preference if workspace_preference != "auto" else "visualization",
                confidence=0.0,
                intent_summary="Non-scientific or adversarial prompt rejected",
                needs_clarification=True,
                clarification_prompt="FLAME only processes NASA microgravity combustion research and spacecraft fire-safety inquiries.",
                candidate_options=["Plot Saffire-III Sample 1 ignition telemetry", "Evaluate BASS-II low-flow flammability limits"]
            )

        # 1. Determine Target Workspace
        target_ws = self._resolve_workspace(q_lower, workspace_preference)

        # 2. Extract Datasets & Investigations
        primary_ds, secondary_ds, inv_id = self._extract_datasets(q_lower, context_filters)

        # 3. Extract Channels & Physical Units
        channels, units_map, variables = self._extract_channels(q_lower, primary_ds)

        # 4. Extract Time Window
        time_window = self._extract_time_window(q_lower, primary_ds)

        # 5. Extract Fuels & Environmental Conditions
        fuels, env_conditions = self._extract_environmental_conditions(q_lower)

        # 6. Assess Ambiguity & Clarification Needs
        needs_clarif = False
        clarif_msg = None
        candidate_options = None

        if target_ws in ("visualization", "comparison") and not primary_ds and not channels:
            # Overly vague request
            if len(q.split()) <= 4:
                needs_clarif = True
                clarif_msg = f"Inquiry '{q}' does not specify which NASA dataset or sensor channels to analyze."
                candidate_options = [
                    "Saffire-III Sample 1 (Radiometer & Thermocouples)",
                    "Saffire-III Sample 2 (In-duct flame spread)",
                    "BASS-II Glovebox Experiments (129 flight runs)"
                ]
        elif target_ws == "comparison" and primary_ds and not secondary_ds:
            # Comparison requested but only one dataset mentioned
            if "sample 1" in q_lower and "sample 2" not in q_lower:
                secondary_ds = "saffire_iii_sample_2"
            else:
                secondary_ds = "saffire_iii_sample_2" if primary_ds == "saffire_iii_sample_1" else "saffire_iii_sample_1"

        # Formulate human-readable intent summary
        summary_parts = []
        if inv_id:
            summary_parts.append(f"Investigation: {inv_id.upper()}")
        if primary_ds:
            summary_parts.append(f"Dataset: {primary_ds}")
        if secondary_ds:
            summary_parts.append(f"Compared with: {secondary_ds}")
        if channels:
            summary_parts.append(f"Channels: {', '.join(channels)}")
        if time_window:
            summary_parts.append(f"Time: {time_window[0]:.1f}s - {time_window[1]:.1f}s")
        if not summary_parts:
            summary_parts.append(f"Inquiry in {target_ws.replace('_', ' ').title()}")

        intent_summary = " | ".join(summary_parts)

        return InterpretedScientificIntent(
            target_workspace=target_ws,
            confidence=0.92 if (primary_ds and channels) else 0.75,
            intent_summary=intent_summary,
            investigation_id=inv_id,
            dataset_id=primary_ds,
            secondary_dataset_id=secondary_ds,
            target_variables=variables,
            channel_ids=channels,
            time_window=time_window,
            units_by_channel=units_map,
            fuel_materials=fuels,
            environmental_conditions=env_conditions,
            needs_clarification=needs_clarif,
            clarification_prompt=clarif_msg,
            candidate_options=candidate_options,
        )

    def _resolve_workspace(self, q_lower: str, preference: str) -> str:
        """
        Resolves the appropriate specialist workspace.
        Enforces Step 7 Routing Rule: A prompt entered in an explicit workspace
        (e.g. visualization or comparison) MUST remain in that workspace by default.
        Global routing only activates when preference == 'auto'.
        """
        if preference and preference != "auto":
            return preference

        # Automatic workspace routing when preference == 'auto'
        matched_scores = {}
        for w in WORKSPACE_PATTERNS:
            score = 0
            for kw in w["keywords"]:
                if re.search(kw, q_lower):
                    score += w["priority"]
            if score > 0:
                matched_scores[w["workspace"]] = score

        if matched_scores:
            best_ws = max(matched_scores.items(), key=lambda x: x[1])[0]
            return best_ws

        return "visualization"

    def detect_alternative_workspace(self, q_lower: str, active_ws: str) -> Optional[str]:
        """
        Detects if a user's prompt strongly indicates another workspace,
        allowing the system to suggest a navigation action without silently redirecting.
        """
        for w in WORKSPACE_PATTERNS:
            if w["workspace"] != active_ws and w["priority"] >= 8:
                for kw in w["keywords"]:
                    if re.search(kw, q_lower):
                        return w["workspace"]
        return None

    def _extract_datasets(
        self, q_lower: str, context_filters: Optional[Dict[str, Any]]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Resolves primary dataset, secondary dataset, and investigation.
        """
        primary = None
        secondary = None
        inv = None

        # Check for explicitly mentioned datasets
        found_datasets = []
        for d in DATASET_PATTERNS:
            for kw in d["keywords"]:
                if re.search(kw, q_lower):
                    if d["id"] not in found_datasets:
                        found_datasets.append(d["id"])
                    if not inv:
                        inv = d["investigation_id"]
                    break

        if len(found_datasets) >= 2:
            primary = found_datasets[0]
            secondary = found_datasets[1]
        elif len(found_datasets) == 1:
            primary = found_datasets[0]
        else:
            # Use context filter if available
            if context_filters and context_filters.get("dataset_id"):
                primary = context_filters.get("dataset_id")
            elif "saffire" in q_lower:
                primary = "saffire_iii_sample_1"
                inv = "saffire_iii"
            elif "bass" in q_lower or "pmma" in q_lower or "nomex" in q_lower:
                primary = "bass_ii_experiments"
                inv = "bass_ii"

        return primary, secondary, inv

    def _extract_channels(
        self, q_lower: str, dataset_id: Optional[str]
    ) -> Tuple[List[str], Dict[str, str], List[str]]:
        """
        Resolves physical sensor channels and variables.
        """
        channels = []
        units_map = {}
        variables = []

        # Check channel keywords
        for key, info in CHANNEL_DICTIONARY.items():
            matched = False
            for pat in info["patterns"]:
                if re.search(pat, q_lower):
                    matched = True
                    break

            if matched:
                canon = info["canonical"]
                if canon not in channels:
                    channels.append(canon)
                    units_map[canon] = info["units"]
                    variables.append(info["label"])

        # If user asked for Saffire Sample 1 with general terms like "radiant heat flux and thermocouple temperatures"
        if "radiant heat flux" in q_lower and "Radiometer 1" not in channels:
            channels.insert(0, "Radiometer 1")
            units_map["Radiometer 1"] = "mW/cm²"
            variables.append("Broadband Radiant Heat Flux")

        if ("thermocouple" in q_lower or "temperatures" in q_lower) and not any("TC" in c for c in channels):
            channels.append("Plume Temp 3 (TC3)")
            units_map["Plume Temp 3 (TC3)"] = "°C"
            variables.append("Downstream Exhaust Plume Temperature")

        # Fallback to dataset default channels if channels empty and dataset is known
        if not channels and dataset_id:
            for d in DATASET_PATTERNS:
                if d["id"] == dataset_id:
                    for c in d["default_channels"]:
                        channels.append(c)
                        # Infer units
                        if "Radiometer" in c:
                            units_map[c] = "mW/cm²"
                        elif "Temp" in c or "TC" in c:
                            units_map[c] = "°C"
                        elif "Pressure" in c:
                            units_map[c] = "PSIA"
                        elif "Anemometer" in c:
                            units_map[c] = "cm/s"
                        else:
                            units_map[c] = "raw"
                        variables.append(c)
                    break

        return channels, units_map, variables

    def _extract_time_window(self, q_lower: str, dataset_id: Optional[str]) -> Optional[List[float]]:
        """
        Extracts bounded time window [start, end].
        """
        # Explicit pattern: "from X to Y seconds", "between X and Y s", "X to Y s"
        explicit_m = re.search(r"\b(?:from|between)?\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?\s*(?:to|and|-)\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)\b", q_lower)
        if explicit_m:
            t0 = float(explicit_m.group(1))
            t1 = float(explicit_m.group(2))
            if t1 > t0:
                return [t0, t1]

        # Semantic keywords: "during ignition", "ignition phase", "ignition sequence"
        if re.search(r"\b(?:during\s+)?ignition(?:\s+(?:phase|sequence|pulse|event))?\b", q_lower):
            if dataset_id == "saffire_iii_sample_1":
                return [50.0, 120.0]
            elif dataset_id == "saffire_iii_sample_2":
                return [15.0, 80.0]
            return [50.0, 120.0]

        # "post ignition" or "steady flame spread"
        if re.search(r"\b(?:steady|flame\s+spread|propagation|post[- ]ignition)\b", q_lower):
            if dataset_id == "saffire_iii_sample_1":
                return [70.0, 250.0]

        return None

    def _extract_environmental_conditions(self, q_lower: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Extracts fuel materials and structured scientific environmental conditions.
        Supports canonical taxonomies for research-gap detection and modeling.
        """
        fuels = []
        for f in ["pmma", "cotton", "nomex", "sibal", "fiberglass"]:
            if re.search(rf"\b{f}\b", q_lower):
                fuels.append(f.upper() if f != "cotton" else "Cotton")

        env: Dict[str, Any] = {}

        # Gravity taxonomy check
        if any(k in q_lower for k in ["lunar", "0.16g", "moon"]):
            env["gravity"] = "partial_lunar"
        elif any(k in q_lower for k in ["martian", "mars", "0.38g"]):
            env["gravity"] = "partial_mars"
        elif any(k in q_lower for k in ["terrestrial", "1g", "normal gravity", "earth gravity"]):
            env["gravity"] = "normal"
        elif any(k in q_lower for k in ["microgravity", "0g", "zero-g", "spacecraft", "orbit", "iss", "msg", "saffire"]):
            env["gravity"] = "micro"

        # Oxygen taxonomy check
        o2_m = re.search(r"\b(\d{1,2}(?:\.\d+)?)\s*(?:%|pct)?\s*(?:vol)?\s*o2\b", q_lower)
        if o2_m:
            env["oxygen_pct"] = float(o2_m.group(1))
            val = float(o2_m.group(1))
            if val < 21.0:
                env["oxygen_regime"] = "low_o2"
            elif val > 30.0:
                env["oxygen_regime"] = "hyperoxic" if val > 34.0 else "elevated_o2"
            else:
                env["oxygen_regime"] = "normal_o2"
        elif any(k in q_lower for k in ["hyperoxic", ">34", "> 34"]):
            env["oxygen_regime"] = "hyperoxic"
        elif any(k in q_lower for k in ["elevated oxygen", "high oxygen", "elevated o2", "high o2"]):
            env["oxygen_regime"] = "elevated_o2"
        elif any(k in q_lower for k in ["low oxygen", "low o2", "hypoxic", "sub-atmospheric o"]):
            env["oxygen_regime"] = "low_o2"
        elif "21%" in q_lower:
            env["oxygen_regime"] = "normal_o2"

        # Airflow taxonomy check
        if any(k in q_lower for k in ["quiescent", "stagnant", "zero-velocity", "0 cm/s", "no flow"]):
            env["airflow_regime"] = "quiescent"
        elif any(k in q_lower for k in ["low airflow", "low-flow", "low flow", "slow flow"]):
            env["airflow_regime"] = "low-flow"
        elif any(k in q_lower for k in ["high airflow", "high-flow", "high flow", "blowoff"]):
            env["airflow_regime"] = "high-flow"

        # Fuel family & material check
        if any(k in q_lower for k in ["droplet", "alkane", "heptane"]):
            env["fuel_family"] = "droplet"
            if "heptane" in q_lower:
                env["fuel_material"] = "n-Heptane"
        elif any(k in q_lower for k in ["cotton", "sibal", "fabric", "nomex", "film"]):
            env["fuel_family"] = "solid-flat"
            if "nomex" in q_lower:
                env["fuel_material"] = "Nomex"
            elif "cotton" in q_lower:
                env["fuel_material"] = "Cotton"
        elif any(k in q_lower for k in ["rod", "cylinder", "thick", "slab"]):
            env["fuel_family"] = "solid-thick"
            if "pmma" in q_lower:
                env["fuel_material"] = "PMMA"

        # Pressure taxonomy check
        if any(k in q_lower for k in ["hypobaric", "low pressure", "8.2 psia", "0.56 atm"]):
            env["pressure_regime"] = "hypobaric"
        elif any(k in q_lower for k in ["hyperbaric", "high pressure"]):
            env["pressure_regime"] = "hyperbaric"

        # Parameter observation check
        if any(k in q_lower for k in ["carbon monoxide", " co ", "co emission"]):
            env["parameter"] = "carbon_monoxide_concentration"
        elif any(k in q_lower for k in ["radiometer", "radiant heat", "heat flux"]):
            env["parameter"] = "radiant_heat_flux"
        elif "temperature" in q_lower:
            env["parameter"] = "temperature"

        return fuels, env
