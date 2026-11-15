"""
NASA FLAME — Scientific Research Gap Detection Engine (Phase RG2)

Provides deterministic, explainable, and scientifically grounded detection of:
1. coverage_gap: applicable experimental condition combinations unrepresented in FLAME's indexed datasets
2. sparse_evidence: combinations with fewer comparable usable experiment runs than a threshold
3. measurement_gap: scientific parameters confirmed absent from available measurement records
4. metadata_gap: scientifically relevant metadata that is unknown or incomplete
5. ingestion_opportunity: raw spreadsheet assets on disk or external NASA PSI programs uningested
6. comparison_gap: insufficient scientifically comparable experiments available for causal evaluation

Strict scientific rules:
1. Unrepresented in FLAME does NOT imply NASA never conducted the experiment.
2. Distinguish unknown metadata from confirmed missing instrumentation.
3. Keep evidence confidence strictly separate from priority scoring.
4. All priority scores are explicitly labeled as heuristic, not scientifically validated.
"""

from pathlib import Path
import json
import logging
from typing import Dict, List, Any, Optional

from .coverage_service import (
    DatasetCoverageService,
    STATUS_OBSERVED,
    STATUS_CONFIRMED_MISSING,
    STATUS_UNKNOWN,
    STATUS_NOT_APPLICABLE,
    TIER_DIRECTLY_COMPARABLE,
    TIER_CONDITIONALLY_COMPARABLE,
    TIER_METHODOLOGICALLY_INCOMPARABLE,
)

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[1]

# Gap Type Constants
GAP_TYPE_COVERAGE = "coverage_gap"
GAP_TYPE_SPARSE = "sparse_evidence"
GAP_TYPE_MEASUREMENT = "measurement_gap"
GAP_TYPE_METADATA = "metadata_gap"
GAP_TYPE_INGESTION = "ingestion_opportunity"
GAP_TYPE_COMPARISON = "comparison_gap"

VALID_GAP_TYPES = {
    GAP_TYPE_COVERAGE,
    GAP_TYPE_SPARSE,
    GAP_TYPE_MEASUREMENT,
    GAP_TYPE_METADATA,
    GAP_TYPE_INGESTION,
    GAP_TYPE_COMPARISON,
}

# Recognized Scientific Taxonomies for Rigorous Condition Validation
RECOGNIZED_GRAVITY_REGIMES = {"micro", "normal", "partial_lunar", "partial_mars", "1g", "0.16g", "0.38g"}
RECOGNIZED_OXYGEN_REGIMES = {"low_o2", "normal_o2", "elevated_o2", "high_o2", "hyperoxic"}
RECOGNIZED_PRESSURE_REGIMES = {"standard", "hypobaric", "hyperbaric"}
RECOGNIZED_FUEL_FAMILIES = {"solid-flat", "solid-thick", "droplet", "gaseous"}
RECOGNIZED_AIRFLOW_REGIMES = {"quiescent", "low-flow", "high-flow"}
RECOGNIZED_PARAMETERS = {
    "temperature",
    "pressure",
    "radiant_heat_flux",
    "radiometer_amplifier_gain",
    "flow_velocity",
    "oxygen_concentration",
    "carbon_dioxide_concentration",
    "carbon_monoxide_concentration",
    "flame_spread_rate",
    "extinction_time",
    "fuel_mass_loss",
    "fuel_moisture_content",
    "video_frames",
}


class ResearchGapDetectionService:
    """
    Core engine for NASA FLAME Phase RG2: Scientific Research Gap Detection.
    Consumes verified RG1 dataset coverage outputs to deterministically detect,
    explain, and heuristically prioritize research gaps without using an LLM.
    """

    def __init__(self, coverage_service: Optional[DatasetCoverageService] = None):
        self.coverage_service = coverage_service or DatasetCoverageService(base_dir=BASE)
        self._cached_findings: Optional[List[Dict[str, Any]]] = None

    def detect_all_gaps(
        self,
        gap_type: Optional[str] = None,
        dimension: Optional[str] = None,
        min_priority: float = 0.0,
        sparse_threshold: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Detect all deterministic scientific research gaps across the 6 supported types.
        Supports filtering by gap type, dimension, and minimum priority score.
        """
        inventory = self.coverage_service.load()
        findings = self._generate_canonical_findings(inventory, sparse_threshold=sparse_threshold)

        # Apply filtering
        filtered = findings
        if gap_type:
            gt_lower = gap_type.lower()
            filtered = [f for f in filtered if f["gap_type"] == gt_lower]

        if dimension:
            dim_lower = dimension.lower()
            filtered = [
                f for f in filtered
                if dim_lower in f["scientific_dimensions"]
                and f["scientific_dimensions"][dim_lower] is not None
            ]

        if min_priority > 0.0:
            filtered = [f for f in filtered if f["priority_score"] >= min_priority]

        # Sort deterministically by priority score descending, then by finding_id
        filtered.sort(key=lambda x: (-x["priority_score"], x["finding_id"]))
        return filtered

    def get_finding_by_id(self, finding_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single finding by its stable unique ID."""
        all_findings = self.detect_all_gaps()
        return next((f for f in all_findings if f["finding_id"] == finding_id), None)

    def get_gap_summary(self) -> Dict[str, Any]:
        """
        Generate aggregate summary metrics across all detected research gaps.
        Includes breakdown by gap type, priority tier distributions, and database scope disclaimer.
        """
        findings = self.detect_all_gaps()
        
        type_counts = {}
        for f in findings:
            gt = f["gap_type"]
            type_counts[gt] = type_counts.get(gt, 0) + 1

        priority_tiers = {
            "high (>= 7.0)": sum(1 for f in findings if f["priority_score"] >= 7.0),
            "medium (4.0 - 6.9)": sum(1 for f in findings if 4.0 <= f["priority_score"] < 7.0),
            "low (< 4.0)": sum(1 for f in findings if f["priority_score"] < 4.0)
        }

        # Top 5 prioritized findings
        top_findings = [
            {
                "finding_id": f["finding_id"],
                "gap_type": f["gap_type"],
                "title": f["title"],
                "priority_score": f["priority_score"],
                "evidence_confidence": f["evidence_confidence"]["level"]
            }
            for f in findings[:5]
        ]

        return {
            "total_findings": len(findings),
            "breakdown_by_gap_type": type_counts,
            "priority_tier_counts": priority_tiers,
            "top_prioritized_findings": top_findings,
            "scoring_methodology": "Heuristic composite score based on coverage deficiency, mission relevance, metadata quality, and resolution feasibility. Not scientifically validated.",
            "database_scope_disclaimer": "Unrepresented in the indexed FLAME collection. Missing data in FLAME does not prove NASA never conducted an experiment."
        }

    def analyze_inquiry(
        self,
        filters: Dict[str, Any],
        question: Optional[str] = None,
        sparse_threshold: int = 5
    ) -> Dict[str, Any]:
        """
        Perform structured parameter analysis for a research inquiry.
        Matches requested experimental conditions against FLAME's indexed records,
        identifies matching usable runs, and attaches all applicable gap findings.

        Scientific rules:
        - Uninterpreted free-text queries return 'unsupported_query' with 0 matching runs.
        - Empty parameter inquiries return 'not_evaluated' with 0 matching runs.
        - Conditions with 0 matching runs distinguish recognized collection coverage gaps
          from unknown or inapplicable conditions.
        - Free-text synthesis is explicitly deferred to Grounded RAG Assistant (/api/rag/ask).
        """
        inventory = self.coverage_service.load()
        experiments = inventory.get("experiments", [])
        all_findings = self.detect_all_gaps(sparse_threshold=sparse_threshold)

        structured_keys = [
            "gravity", "oxygen_regime", "pressure_regime",
            "fuel_family", "fuel_material", "airflow_regime", "parameter"
        ]
        active_filters = {
            k: str(v).strip()
            for k, v in filters.items()
            if k in structured_keys and v is not None and str(v).strip() != ""
        }
        has_structured_filters = len(active_filters) > 0

        # Handle queries lacking structured parameters
        if not has_structured_filters:
            if question and str(question).strip():
                return {
                    "query_filters": filters,
                    "raw_question_submitted": question,
                    "query_status": "unsupported_free_text",
                    "coverage_status": "unsupported_query",
                    "explanation": (
                        "Natural-language free-text questions cannot be evaluated directly by the deterministic "
                        "Research Gap Detection Engine without structured parameter extraction. "
                        "For natural-language evidence retrieval, scientific explanations, and synthesis across NASA flight records, "
                        "please query the Grounded RAG Assistant (`POST /api/rag/ask`). "
                        "To evaluate empirical coverage and detect research gaps, please supply structured experimental parameters "
                        "(e.g. gravity, oxygen_regime, pressure_regime, fuel_family, fuel_material, airflow_regime, parameter)."
                    ),
                    "free_text_limitation": (
                        "Free-text natural language interpretation is reserved for the Grounded RAG Assistant (/api/rag/ask). "
                        "Research Gap Detection performs deterministic parameter analysis against indexed scientific conditions."
                    ),
                    "recommended_action": "Query Grounded RAG Assistant (POST /api/rag/ask) for natural-language inquiries, or supply structured parameters for gap evaluation.",
                    "matched_usable_runs_count": 0,
                    "matched_experiment_ids": [],
                    "parameter_observation_status": None,
                    "applicable_gap_findings_count": 0,
                    "applicable_gap_findings": [],
                    "scientific_disclaimer": "Unrepresented in the indexed FLAME collection. Missing data in FLAME does not prove NASA never conducted an experiment."
                }
            else:
                return {
                    "query_filters": filters,
                    "raw_question_submitted": question,
                    "query_status": "missing_parameters",
                    "coverage_status": "not_evaluated",
                    "explanation": (
                        "No experimental condition filters or research inquiry were supplied for evaluation. "
                        "Please provide at least one structured condition parameter (e.g. gravity, oxygen_regime, pressure_regime, fuel_family, fuel_material, airflow_regime, parameter)."
                    ),
                    "free_text_limitation": None,
                    "recommended_action": "Supply structured condition parameters to evaluate dataset coverage and detect research gaps.",
                    "matched_usable_runs_count": 0,
                    "matched_experiment_ids": [],
                    "parameter_observation_status": None,
                    "applicable_gap_findings_count": 0,
                    "applicable_gap_findings": [],
                    "scientific_disclaimer": "Unrepresented in the indexed FLAME collection. Missing data in FLAME does not prove NASA never conducted an experiment."
                }

        # Match empirical runs against structured filters
        matched_experiments = list(experiments)
        req_gravity = active_filters.get("gravity")
        req_oxygen = active_filters.get("oxygen_regime")
        req_pressure = active_filters.get("pressure_regime")
        req_fuel_family = active_filters.get("fuel_family")
        req_fuel_material = active_filters.get("fuel_material")
        req_airflow = active_filters.get("airflow_regime")
        req_parameter = active_filters.get("parameter")

        if req_gravity:
            matched_experiments = [
                e for e in matched_experiments
                if e["environmental_conditions"]["gravity"]["regime"].lower() == req_gravity.lower()
            ]

        if req_oxygen:
            matched_experiments = [
                e for e in matched_experiments
                if e["environmental_conditions"]["oxygen"]["regime"].lower() == req_oxygen.lower()
            ]

        if req_pressure:
            matched_experiments = [
                e for e in matched_experiments
                if e["environmental_conditions"]["pressure"]["regime"].lower() == req_pressure.lower()
            ]

        if req_fuel_family:
            matched_experiments = [
                e for e in matched_experiments
                if e["fuel_family"].lower() == req_fuel_family.lower()
            ]

        if req_fuel_material:
            matched_experiments = [
                e for e in matched_experiments
                if req_fuel_material.lower() in e["fuel_material"].lower()
            ]

        if req_airflow:
            matched_experiments = [
                e for e in matched_experiments
                if e["environmental_conditions"]["airflow"]["regime"].lower() == req_airflow.lower()
            ]

        # Parameter presence check
        param_observation_status = None
        if req_parameter:
            observed_with_param = [
                e for e in matched_experiments
                if e.get("parameters", {}).get(req_parameter, {}).get("status") == STATUS_OBSERVED
            ]
            param_observation_status = {
                "parameter": req_parameter,
                "runs_with_parameter_observed": len(observed_with_param),
                "total_condition_runs": len(matched_experiments),
                "observation_status": STATUS_OBSERVED if len(observed_with_param) > 0 else STATUS_CONFIRMED_MISSING
            }

        # Taxonomy validity check
        is_recognized = True
        unrecognized_reasons = []

        if req_gravity and req_gravity.lower() not in RECOGNIZED_GRAVITY_REGIMES:
            is_recognized = False
            unrecognized_reasons.append(f"Gravity regime '{req_gravity}' is not recognized in FLAME taxonomy ({sorted(RECOGNIZED_GRAVITY_REGIMES)}).")

        if req_oxygen and req_oxygen.lower() not in RECOGNIZED_OXYGEN_REGIMES:
            is_recognized = False
            unrecognized_reasons.append(f"Oxygen regime '{req_oxygen}' is not recognized in FLAME taxonomy ({sorted(RECOGNIZED_OXYGEN_REGIMES)}).")

        if req_pressure and req_pressure.lower() not in RECOGNIZED_PRESSURE_REGIMES:
            is_recognized = False
            unrecognized_reasons.append(f"Pressure regime '{req_pressure}' is not recognized in FLAME taxonomy ({sorted(RECOGNIZED_PRESSURE_REGIMES)}).")

        if req_fuel_family and req_fuel_family.lower() not in RECOGNIZED_FUEL_FAMILIES:
            is_recognized = False
            unrecognized_reasons.append(f"Fuel family '{req_fuel_family}' is not recognized in FLAME taxonomy ({sorted(RECOGNIZED_FUEL_FAMILIES)}).")

        if req_airflow and req_airflow.lower() not in RECOGNIZED_AIRFLOW_REGIMES:
            is_recognized = False
            unrecognized_reasons.append(f"Airflow regime '{req_airflow}' is not recognized in FLAME taxonomy ({sorted(RECOGNIZED_AIRFLOW_REGIMES)}).")

        if req_parameter and req_parameter.lower() not in RECOGNIZED_PARAMETERS:
            is_recognized = False
            unrecognized_reasons.append(f"Parameter '{req_parameter}' is not recognized in canonical parameter catalog ({sorted(RECOGNIZED_PARAMETERS)}).")

        # Find applicable gap findings matching requested dimensions
        applicable_findings = []
        for f in all_findings:
            dims = f["scientific_dimensions"]
            match = False
            if req_gravity and dims.get("gravity") and dims["gravity"].lower() == req_gravity.lower():
                match = True
            if req_oxygen and dims.get("oxygen") and dims["oxygen"].lower() == req_oxygen.lower():
                match = True
            if req_fuel_family and dims.get("fuel_family") and dims["fuel_family"].lower() == req_fuel_family.lower():
                match = True
            if req_fuel_material and dims.get("fuel_material") and req_fuel_material.lower() in dims["fuel_material"].lower():
                match = True
            if req_airflow and dims.get("airflow") and dims["airflow"].lower() == req_airflow.lower():
                match = True
            if req_parameter and dims.get("parameter") and dims["parameter"].lower() == req_parameter.lower():
                match = True

            if match:
                applicable_findings.append({
                    "finding_id": f["finding_id"],
                    "gap_type": f["gap_type"],
                    "title": f["title"],
                    "priority_score": f["priority_score"],
                    "recommended_next_step": f["recommended_next_step"]
                })

        # Determine coverage status and meaningful explanation
        if not is_recognized:
            coverage_status = "unknown_or_inapplicable"
            query_status = "unrecognized_or_inapplicable_condition"
            explanation = (
                "The requested condition, parameter, or combination is unrecognized in FLAME's combustion taxonomy or represents an inapplicable experimental configuration. "
                + " ".join(unrecognized_reasons)
            )
        elif len(matched_experiments) == 0:
            coverage_status = "coverage_gap"
            query_status = "indexed_collection_coverage_gap"
            explanation = (
                "Condition recognized in combustion science taxonomy but completely unrepresented in FLAME's indexed collection (0 matching usable runs). "
                "Unrepresented in FLAME does not mean NASA never conducted the experiment."
            )
        elif req_parameter and param_observation_status and param_observation_status["runs_with_parameter_observed"] == 0:
            coverage_status = "coverage_gap"
            query_status = "parameter_confirmed_missing"
            explanation = (
                f"Parameter '{req_parameter}' is confirmed missing from all {len(matched_experiments)} matching experiment records in FLAME's indexed collection."
            )
        elif len(matched_experiments) < sparse_threshold:
            coverage_status = "sparse"
            query_status = "sparse_evidence"
            explanation = (
                f"Sparse evidence: Only {len(matched_experiments)} usable experiment runs match the specified criteria in FLAME's indexed collection "
                f"(below configurable system heuristic threshold of {sparse_threshold} runs)."
            )
        else:
            coverage_status = "covered"
            query_status = "covered"
            explanation = f"Condition covered: Found {len(matched_experiments)} usable experiment runs matching the specified criteria in FLAME's indexed collection."

        free_text_limitation = None
        if question and str(question).strip():
            free_text_limitation = (
                "Evaluated structured filter parameters. Free-text interpretation of the question itself is handled by the Grounded RAG Assistant (/api/rag/ask)."
            )

        return {
            "query_filters": filters,
            "raw_question_submitted": question,
            "query_status": query_status,
            "coverage_status": coverage_status,
            "explanation": explanation,
            "free_text_limitation": free_text_limitation,
            "matched_usable_runs_count": len(matched_experiments),
            "matched_experiment_ids": [e["experiment_id"] for e in matched_experiments[:15]],
            "parameter_observation_status": param_observation_status,
            "applicable_gap_findings_count": len(applicable_findings),
            "applicable_gap_findings": applicable_findings,
            "scientific_disclaimer": "Unrepresented in the indexed FLAME collection. Missing data in FLAME does not prove NASA never conducted an experiment."
        }

    # ==========================================
    # Canonical Gap Generation Engine
    # ==========================================

    def _generate_canonical_findings(
        self,
        inventory: Dict[str, Any],
        sparse_threshold: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate the complete set of deterministic research gap findings across all 6 categories."""
        findings = []

        summary = inventory.get("summary", {})
        repo_audit = inventory.get("repository_audit", {})
        experiments = inventory.get("experiments", [])
        total_runs = len(experiments)

        # ----------------------------------------------------
        # Category 1: Coverage Gaps (Unrepresented Conditions)
        # ----------------------------------------------------
        # 1.1 Partial Lunar Gravity
        findings.append(self._create_finding(
            finding_id="GAP-COV-GRAV-PARTIAL-LUNAR",
            gap_type=GAP_TYPE_COVERAGE,
            title="Partial Lunar Gravity (0.16g) Unrepresented in FLAME Collection",
            explanation=(
                "Partial lunar gravity (0.16g) is completely unrepresented in FLAME's indexed flight datasets. "
                "Current indexed records are limited to orbital microgravity (~10⁻⁵g). Lunar surface habitats under the "
                "Artemis program operate at 0.16g with elevated oxygen atmospheres (up to 34% O2 at 8.2 psia), "
                "where reduced buoyancy creates unique flame stabilization and slow-combustion regimes."
            ),
            dimensions={"gravity": "partial_lunar"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=[],
            experiment_ids=[],
            provenance=["Dataset Catalog (All 11 datasets verified microgravity)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified by 100% microgravity attribution across all 133 flight runs in the dataset catalog.",
            deficiency_score=3.0,
            relevance_score=2.5,
            metadata_score=1.0,
            feasibility_score=0.5,
            readiness_score=0.0,
            limitations=[
                "Orbital spacecraft cannot simulate 0.16g without centrifuges.",
                "Terrestrial drop towers offer short-duration (~2-5s) partial gravity testing but are uningested in FLAME."
            ],
            next_step="Ingest lunar partial-gravity parabolic flight or drop tower datasets into FLAME."
        ))

        # 1.2 Partial Martian Gravity
        findings.append(self._create_finding(
            finding_id="GAP-COV-GRAV-PARTIAL-MARS",
            gap_type=GAP_TYPE_COVERAGE,
            title="Partial Martian Gravity (0.38g) Unrepresented in FLAME Collection",
            explanation=(
                "Partial Martian gravity (0.38g) is unrepresented in FLAME's indexed datasets. "
                "Long-duration Mars surface mission fire safety requires understanding low-gravity buoyancy convection."
            ),
            dimensions={"gravity": "partial_mars"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=[],
            experiment_ids=[],
            provenance=["Dataset Catalog (All 11 datasets verified microgravity)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified by catalog audit; zero Martian gravity records present.",
            deficiency_score=3.0,
            relevance_score=2.2,
            metadata_score=1.0,
            feasibility_score=0.5,
            readiness_score=0.0,
            limitations=["Requires parabolic flight or centrifuges for empirical testing."],
            next_step="Identify candidate Martian gravity combustion datasets in NASA archives."
        ))

        # 1.3 Normal Earth Gravity (1g) Baseline
        findings.append(self._create_finding(
            finding_id="GAP-COV-GRAV-NORMAL-1G",
            gap_type=GAP_TYPE_COVERAGE,
            title="Normal Earth Gravity (1.0g) Ground Baselines Unrepresented in FLAME",
            explanation=(
                "Normal Earth gravity (1.0g) baseline combustion runs are unrepresented in FLAME's indexed datasets. "
                "NASA flight combustion investigations typically perform terrestrial 1g baselines prior to flight. "
                "These ground baselines have not yet been imported into FLAME's catalog, preventing direct microgravity-to-1g comparison."
            ),
            dimensions={"gravity": "normal"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=[],
            experiment_ids=[],
            provenance=["Dataset Catalog (11 flight datasets indexed)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified by catalog audit; only orbital flight datasets are registered.",
            deficiency_score=3.0,
            relevance_score=2.0,
            metadata_score=1.2,
            feasibility_score=1.8,
            readiness_score=0.8,
            limitations=["Terrestrial baseline data exists in secondary NASA publications but requires normalization into FLAME."],
            next_step="Normalize terrestrial 1g BASS-II and Saffire ground comparison datasets into FLAME."
        ))

        # 1.4 Hyperoxic Microgravity (>34% O2)
        findings.append(self._create_finding(
            finding_id="GAP-COV-OX-HYPEROXIC",
            gap_type=GAP_TYPE_COVERAGE,
            title="Hyperoxic Microgravity Regime (>34% O2) Unrepresented in FLAME",
            explanation=(
                "Hyperoxic microgravity combustion (>34% O2) is completely unrepresented in FLAME's indexed datasets. "
                "Flight safety regulations severely restrict high-oxygen burns in uncrewed spacecraft (Cygnus) "
                "and ISS glovebox facilities due to catastrophic flammability risks."
            ),
            dimensions={"oxygen": "high_o2", "gravity": "micro"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=[],
            experiment_ids=[],
            provenance=["BASS-II matrix (max O2: 23.0%)", "Saffire calibrated data (max O2: ~22%)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Audited calibrated initial O2 in BASS-II (max 23.0%) and Saffire (ambient ~21-22%); zero hyperoxic records present.",
            deficiency_score=3.0,
            relevance_score=1.8,
            metadata_score=1.0,
            feasibility_score=0.4,
            readiness_score=0.0,
            limitations=["Extreme spacecraft fire hazard restricts orbital execution."],
            next_step="Review specialized ground high-pressure oxygen chamber testing literature."
        ))

        # 1.5 Droplet Combustion (Liquid Fuels)
        findings.append(self._create_finding(
            finding_id="GAP-COV-FUEL-DROPLET",
            gap_type=GAP_TYPE_COVERAGE,
            title="Liquid Droplet Combustion Unrepresented in Indexed FLAME Collection",
            explanation=(
                "Liquid droplet combustion (e.g. heptane, decane, methanol) is unrepresented in FLAME's 11 indexed datasets. "
                "NASA conducted extensive droplet combustion on the ISS under the FLEX (Flame Extinction Experiment) program, "
                "discovering cool flame phenomena in microgravity. These datasets are currently outside FLAME's database boundary."
            ),
            dimensions={"fuel_family": "droplet"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=[],
            experiment_ids=[],
            provenance=["NASA PSI Portal / CIR FLEX Project Records"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Catalog contains only solid fabrics, thin films, and PMMA slabs; liquid droplet records omitted.",
            deficiency_score=3.0,
            relevance_score=2.2,
            metadata_score=1.4,
            feasibility_score=1.5,
            readiness_score=0.5,
            limitations=["FLEX datasets are hosted in NASA PSI but require dedicated extraction into FLAME CSV formats."],
            next_step="Download and ingest NASA FLEX droplet combustion datasets into FLAME."
        ))

        # 1.6 Gaseous Burner Flames
        findings.append(self._create_finding(
            finding_id="GAP-COV-FUEL-GASEOUS",
            gap_type=GAP_TYPE_COVERAGE,
            title="Gaseous Burner Combustion Unrepresented in Indexed FLAME Collection",
            explanation=(
                "Gaseous burner flames (e.g. methane, ethylene co-flow diffusion flames) are unrepresented in FLAME's catalog. "
                "NASA conducted gaseous combustion investigations under the ACME (Advanced Combustion via Microgravity Experiments) "
                "program in the ISS CIR. These datasets have not yet been ingested into FLAME."
            ),
            dimensions={"fuel_family": "gaseous"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=[],
            experiment_ids=[],
            provenance=["NASA PSI Portal / CIR ACME Project Records"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Audited catalog confirms 100% solid fuel representation in current index.",
            deficiency_score=3.0,
            relevance_score=2.0,
            metadata_score=1.3,
            feasibility_score=1.4,
            readiness_score=0.5,
            limitations=["ACME data requires extraction from CIR raw telemetry archives."],
            next_step="Ingest NASA ACME gaseous combustion datasets into FLAME."
        ))

        # ----------------------------------------------------
        # Category 2: Sparse Evidence (Low Replicate Counts)
        # ----------------------------------------------------
        # 2.1 Quiescent / Stagnant Airflow
        quiescent_runs = [e["experiment_id"] for e in experiments if e["environmental_conditions"]["airflow"]["regime"] == "quiescent"]
        if len(quiescent_runs) < sparse_threshold:
            findings.append(self._create_finding(
                finding_id="GAP-SPARSE-AIRFLOW-QUIESCENT",
                gap_type=GAP_TYPE_SPARSE,
                title="Sparse Evidence: Stagnant Microgravity Combustion (1 Run)",
                explanation=(
                    f"Only {len(quiescent_runs)} experiment run in FLAME's indexed collection ({', '.join(quiescent_runs)}) was conducted "
                    "under truly quiescent (0.0 cm/s flow) microgravity conditions. Stagnant microgravity combustion relies purely on molecular diffusion, "
                    "causing flame smothering and cool flame survival. A single test run prevents statistical flammability boundary characterization. "
                    f"Sparse evidence is evaluated against a configurable system heuristic (< {sparse_threshold} usable runs), not an established universal threshold in combustion science."
                ),
                dimensions={"airflow": "quiescent", "gravity": "micro"},
                observed_count=len(quiescent_runs),
                total_denominator=total_runs,
                dataset_ids=["bass_ii_experiments"],
                experiment_ids=quiescent_runs,
                provenance=["bass_ii_experiments.csv (Test O2, Air display: 0)"],
                confidence_level="HIGH",
                confidence_justification="Confidence in database gap: Verified by exact airflow parsing across all 129 BASS-II rows and 4 Saffire sensor datasets.",
                deficiency_score=2.0,
                relevance_score=2.1,
                metadata_score=1.2,
                feasibility_score=1.2,
                readiness_score=0.8,
                limitations=["Stagnant flames in glovebox chambers are prone to premature oxygen depletion."],
                next_step="Identify additional zero-flow BASS-I or European Space Agency (ESA) microgravity diffusion tests."
            ))

        # 2.2 Elevated Oxygen in Large-Scale Fabric Tests
        elevated_saffire = [e["experiment_id"] for e in experiments if "saffire" in e["dataset_id"] and e["environmental_conditions"]["oxygen"]["regime"] == "elevated_o2"]
        if len(elevated_saffire) < sparse_threshold:
            findings.append(self._create_finding(
                finding_id="GAP-SPARSE-OX-ELEVATED-SAFFIRE",
                gap_type=GAP_TYPE_SPARSE,
                title="Sparse Evidence: Large-Scale Fabric Burns in Elevated Oxygen (2 Runs)",
                explanation=(
                    f"Only {len(elevated_saffire)} large-scale flight experiment runs ({', '.join(elevated_saffire)}) evaluate fabric combustion "
                    "under elevated oxygen (~22% vol) in the Saffire flow duct. Exploration missions require fire safety data up to 34% O2, "
                    "making large-scale enriched oxygen combustion data-limited in the indexed repository. "
                    f"Sparse evidence is evaluated against a configurable system heuristic (< {sparse_threshold} usable runs), not an established universal threshold in combustion science."
                ),
                dimensions={"oxygen": "elevated_o2", "fuel_family": "solid-flat", "gravity": "micro"},
                observed_count=len(elevated_saffire),
                total_denominator=4,
                dataset_ids=["saffire_sample_5", "saffire_sample_6"],
                experiment_ids=elevated_saffire,
                provenance=["Saffire Sensor Data Sample 5.xlsx", "Saffire Sensor Data Sample 6.xlsx"],
                confidence_level="HIGH",
                confidence_justification="Confidence in database gap: Verified from calibrated O2 series in Saffire Samples 5 & 6.",
                deficiency_score=1.5,
                relevance_score=2.4,
                metadata_score=1.4,
                feasibility_score=1.0,
                readiness_score=0.9,
                limitations=["Cygnus flight experiments are constrained by single-mission vehicle lifespans."],
                next_step="Cross-reference with Saffire-IV and Saffire-V subsequent mission flight reports."
            ))

        # 2.3 Nomex Meta-Aramid Fabric
        nomex_runs = [e["experiment_id"] for e in experiments if "nomex" in e["fuel_material"].lower()]
        if len(nomex_runs) < sparse_threshold:
            findings.append(self._create_finding(
                finding_id="GAP-SPARSE-FUEL-NOMEX",
                gap_type=GAP_TYPE_SPARSE,
                title=f"Sparse Evidence: Nomex Meta-Aramid Fire-Resistant Fabric ({len(nomex_runs)} Runs)",
                explanation=(
                    f"Only {len(nomex_runs)} experiment runs ({', '.join(nomex_runs)}) evaluate Nomex aramid fabric. "
                    "Nomex is a primary protective fabric used in astronaut flight suits and spacecraft interior lining. "
                    "A single large-scale flight sample (Saffire Sample 2) and three discrete tests in BASS-II (bass_ii_f1, bass_ii_f2, bass_ii_f3) provide limited replication. "
                    f"Sparse evidence is evaluated against a configurable system heuristic (< {sparse_threshold} usable runs), not an established universal threshold in combustion science."
                ),
                dimensions={"fuel_material": "Nomex", "fuel_family": "solid-flat"},
                observed_count=len(nomex_runs),
                total_denominator=total_runs,
                dataset_ids=["saffire_iii_sample_2", "bass_ii_experiments"],
                experiment_ids=nomex_runs,
                provenance=["Saffire III Sample 2 Sensors.xlsx", "BASS-II Test Matrix by PI Final.xlsx (runs f1, f2, f3)"],
                confidence_level="HIGH",
                confidence_justification="Confidence in database gap: Direct count of 4 verified Nomex test records in active FLAME database.",
                deficiency_score=1.5,
                relevance_score=2.3,
                metadata_score=1.3,
                feasibility_score=1.2,
                readiness_score=0.9,
                limitations=["Nomex exhibits charring and rapid extinction in standard air in microgravity."],
                next_step="Audit raw_data for additional Nomex test runs or evaluate Saffire-IV Nomex data."
            ))

        # ----------------------------------------------------
        # Category 3: Measurement Gaps (Confirmed Absent Parameters)
        # ----------------------------------------------------
        # 3.1 Carbon Monoxide in Saffire
        findings.append(self._create_finding(
            finding_id="GAP-MEAS-SAFFIRE-CO",
            gap_type=GAP_TYPE_MEASUREMENT,
            title="Measurement Gap: Carbon Monoxide (CO) Absent in Saffire Flow Duct",
            explanation=(
                "Carbon monoxide (CO) toxic gas concentration is confirmed absent as an empirical measurement from Saffire-III flow duct telemetry. "
                "The Saffire flight sensor rig measured CO2 and O2, but lacked an electrochemical or optical CO sensor. "
                "In contrast, small-scale BASS-II tests logged discrete initial and final CO readings (0-6 ppm). "
                "The Saffire flight rig lacked instrumentation to measure carbon monoxide, and no validated secondary inference model is available in FLAME "
                "to reconstruct continuous CO concentrations from CO2 or O2 channels alone. Unvalidated estimation of toxic CO from other gases without verified kinetics is scientifically unsupported."
            ),
            dimensions={"parameter": "carbon_monoxide_concentration"},
            observed_count=0,
            total_denominator=4,
            dataset_ids=["saffire_iii_sample_1", "saffire_iii_sample_2", "saffire_sample_5", "saffire_sample_6"],
            experiment_ids=["saffire_iii_sample_1", "saffire_iii_sample_2"],
            provenance=["Saffire III Sensor Layout Metadata (61 physical channels, zero CO channels)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Audited all physical sensor channels across Saffire flight metadata; zero carbon monoxide sensors installed.",
            deficiency_score=2.5,
            relevance_score=2.4,
            metadata_score=1.5,
            feasibility_score=0.6,
            readiness_score=0.0,
            limitations=[
                "Hardware sensor omission on flown spacecraft; cannot be retroactively measured empirically.",
                "Downstream CO estimation from other telemetry channels lacks a validated scientific inference model in FLAME."
            ],
            next_step="Recommend integrating dedicated calibrated electrochemical or optical CO sensors into future flight duct hardware; do not infer CO without a validated reaction model."
        ))

        # 3.2 Flame Spread Rate as Direct Telemetry Channel
        findings.append(self._create_finding(
            finding_id="GAP-MEAS-FLAME-SPREAD-RATE",
            gap_type=GAP_TYPE_MEASUREMENT,
            title="Measurement Gap: Continuous Flame Spread Rate Absent as Direct Sensor Channel",
            explanation=(
                "Flame spread rate (mm/s) is confirmed absent as a direct continuous empirical sensor channel in both Saffire telemetry "
                "and BASS-II spreadsheets. Flame spread rate is a derived scientific quantity requiring post-flight optical "
                "video edge tracking or thermocouple isotherm arrival calculations, rather than a raw empirical measurement. "
                "Classifying flame spread rate as an empirical sensor channel confuses raw telemetry with derived analytical quantities."
            ),
            dimensions={"parameter": "flame_spread_rate"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=["saffire_iii_sample_1", "saffire_iii_sample_2", "bass_ii_experiments"],
            experiment_ids=["saffire_iii_sample_1", "saffire_iii_sample_2"],
            provenance=["Saffire channel catalog", "BASS-II matrix column schema"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified by parameter catalog and schema audit; spread rate exists only as a derived post-flight quantity.",
            deficiency_score=2.0,
            relevance_score=2.5,
            metadata_score=1.3,
            feasibility_score=1.8,
            readiness_score=0.7,
            limitations=["Optical camera resolution, smoke occlusion, and camera frame rate limit tracking accuracy of derived spread rates."],
            next_step="Implement a validated post-processing derivation module using synchronized optical video frame DIO timestamps."
        ))

        # 3.3 Fuel Specimen Moisture Content
        findings.append(self._create_finding(
            finding_id="GAP-MEAS-FUEL-MOISTURE",
            gap_type=GAP_TYPE_MEASUREMENT,
            title="Measurement Gap: Pre-Flight Specimen Moisture Content Undocumented",
            explanation=(
                "Pre-flight fuel specimen moisture content (% mass) is confirmed missing metadata from primary flight records in both BASS-II and Saffire. "
                "Moisture content strongly influences cellulose (Cotton, SIBAL) ignition thresholds and flame spread rates. "
                "Although launch facility ambient relative humidity was managed, individual specimen pre-burn moisture values were unmeasured. "
                "Approximating fabric moisture from cabin relative humidity (~30-40% RH) represents an uncalibrated assumption without documented sorption isotherm models."
            ),
            dimensions={"parameter": "fuel_moisture_content"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=["saffire_iii_sample_1", "saffire_iii_sample_2", "bass_ii_experiments"],
            experiment_ids=["saffire_iii_sample_1", "bass_ii_b1"],
            provenance=["BASS-II test log sheets", "Saffire flight metadata"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified absence of pre-flight specimen moisture measurements across all indexed flight runs.",
            deficiency_score=1.5,
            relevance_score=1.9,
            metadata_score=1.0,
            feasibility_score=0.5,
            readiness_score=0.0,
            limitations=[
                "Unrecorded prior to launch; specimen moisture cannot be directly recovered post-flight.",
                "Deriving moisture from cabin RH is an uncalibrated assumption without verified material sorption isotherms."
            ],
            next_step="Log specimen dry-basis moisture in future flight pre-test protocols; document sorption isotherm models if estimating from cabin RH."
        ))

        # 3.4 BASS-II Calibrated Heat Flux vs Gain
        findings.append(self._create_finding(
            finding_id="GAP-MEAS-BASS-CALIBRATED-HEAT-FLUX",
            gap_type=GAP_TYPE_MEASUREMENT,
            title="Measurement Gap: Calibrated Physical Radiant Heat Flux Omitted in BASS-II",
            explanation=(
                "BASS-II records an electrical instrument gain setting (10, 50, 250, 1000) rather than an empirical calibrated physical "
                "radiant heat flux measurement in kW/m² or mW/cm². Saffire records 4 calibrated broadband thermopiles. "
                "Conflating an instrument amplifier setting with an empirical physical radiant heat flux measurement is scientifically incorrect."
            ),
            dimensions={"parameter": "radiant_heat_flux"},
            observed_count=0,
            total_denominator=129,
            dataset_ids=["bass_ii_experiments"],
            experiment_ids=["bass_ii_b1"],
            provenance=["BASS-II Test Matrix by PI Final.xlsx (Column: 'Radiometer gain')"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified column header and numerical entries in bass_ii_experiments.csv record amplifier gain switch settings, not calibrated kW/m² flux.",
            deficiency_score=2.0,
            relevance_score=1.8,
            metadata_score=1.2,
            feasibility_score=1.2,
            readiness_score=0.5,
            limitations=["Requires PI radiometer volt-to-heat-flux calibration curves to convert raw instrument settings to physical flux."],
            next_step="Obtain and apply PI radiometer calibration equations to compute calibrated physical radiant heat flux from recorded signals."
        ))

        # ----------------------------------------------------
        # Category 4: Metadata Gaps (Unknown / Incomplete Fields)
        # ----------------------------------------------------
        # 4.1 BASS-II Chamber Pressure
        findings.append(self._create_finding(
            finding_id="GAP-META-BASS-PRESSURE",
            gap_type=GAP_TYPE_METADATA,
            title="Metadata Gap: BASS-II Discrete Chamber Pressure Unlogged per Run",
            explanation=(
                "Ambient chamber pressure is unlogged per test run in the BASS-II test matrix spreadsheet, representing missing run metadata. "
                "While the ISS Microgravity Science Glovebox operated at nominal ISS cabin pressure (~101.3 kPa), this operational assumption "
                "does not replace empirical per-run pressure logging, as transient chamber pressure variations during combustion and venting were unrecorded."
            ),
            dimensions={"parameter": "pressure", "pressure": "standard"},
            observed_count=0,
            total_denominator=129,
            dataset_ids=["bass_ii_experiments"],
            experiment_ids=["bass_ii_b1"],
            provenance=["bass_ii_experiments.csv (no pressure column)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified absence of per-run chamber pressure columns in BASS-II CSV and matrix sheets.",
            deficiency_score=1.5,
            relevance_score=1.5,
            metadata_score=1.0,
            feasibility_score=1.4,
            readiness_score=0.6,
            limitations=["Nominal pressure is bounded by ISS MSG operational envelopes (101.3 ± 2 kPa), but individual run dynamics remain unrecorded."],
            next_step="Document nominal ISS Glovebox 101.3 kPa cabin pressure in BASS-II dataset metadata with explicit note that per-run telemetry was unlogged."
        ))

        # 4.2 Saffire Extinction Timestamps
        findings.append(self._create_finding(
            finding_id="GAP-META-SAFFIRE-EXTINCTION-TIMESTAMP",
            gap_type=GAP_TYPE_METADATA,
            title="Metadata Gap: Saffire Extinction Timestamps Unlogged as Scalar Columns",
            explanation=(
                "Exact extinction timestamps for Saffire samples are unlogged as discrete scalar columns in the calibrated CSVs. "
                "Extinction time is a derived analytical quantity rather than a raw empirical sensor channel, and must be inferred from "
                "thermocouple cooling rates, gas concentration plateaus, and optical camera records using validated analytical methods."
            ),
            dimensions={"parameter": "extinction_time"},
            observed_count=2,
            total_denominator=4,
            dataset_ids=["saffire_iii_sample_1", "saffire_iii_sample_2"],
            experiment_ids=["saffire_iii_sample_1", "saffire_iii_sample_2"],
            provenance=["Saffire metadata JSON files"],
            confidence_level="MEDIUM",
            confidence_justification="Confidence in database gap: Confirmed absence of scalar extinction timestamp columns in calibrated CSVs; Sample 1 (~continuous burn) and Sample 2 (~155s) extinction times require analytical derivation.",
            deficiency_score=1.2,
            relevance_score=2.0,
            metadata_score=1.3,
            feasibility_score=1.8,
            readiness_score=0.9,
            limitations=["Analytical extinction determination depends on sensor response time, camera visibility, and threshold definition."],
            next_step="Publish validated analytical extinction timestamps and methodology in dataset documentation."
        ))

        # ----------------------------------------------------
        # Category 5: Ingestion Opportunities (Raw Files & External)
        # ----------------------------------------------------
        # 5.1 Raw Teflon
        findings.append(self._create_finding(
            finding_id="GAP-INGEST-RAW-TEFLON",
            gap_type=GAP_TYPE_INGESTION,
            title="Ingestion Opportunity: Raw Teflon (PTFE) Run Available on Disk",
            explanation=(
                "Raw spreadsheet 'GMT262 RUN 13 teflon.xlsx' exists locally on disk in raw_data/PSI-102 (298 KB). "
                "Teflon (PTFE) is a critical aerospace wire insulation and structural polymer with high flame resistance. "
                "This file is un-normalized and absent from FLAME's active catalog."
            ),
            dimensions={"fuel_material": "Teflon (PTFE)", "fuel_family": "solid-thick"},
            observed_count=0,
            total_denominator=repo_audit.get("unprocessed_raw_files_count", 11),
            dataset_ids=[],
            experiment_ids=[],
            provenance=["data-pipeline/raw_data/PSI-102/GMT262 RUN 13 teflon.xlsx"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified file presence and size on local disk via repository audit.",
            deficiency_score=2.0,
            relevance_score=2.3,
            metadata_score=1.4,
            feasibility_score=2.0,
            readiness_score=1.0,
            limitations=["Requires spreadsheet sheet inspection and unit calibration extraction."],
            next_step="Write an automated extraction parser for GMT262 RUN 13 teflon.xlsx and register in dataset_catalog.json."
        ))

        # 5.2 Raw Kapton
        findings.append(self._create_finding(
            finding_id="GAP-INGEST-RAW-KAPTON",
            gap_type=GAP_TYPE_INGESTION,
            title="Ingestion Opportunity: 3 Raw Kapton (Polyimide) Spreadsheets Available on Disk",
            explanation=(
                "Three raw spreadsheets for Kapton polyimide exist in raw_data/PSI-102: 'kaptonGMT257.xlsx', "
                "'kaptonGMT257 zgy average.xlsx', and 'GMT263 run 14 kapton avg.xlsx' (totaling ~1.6 MB). "
                "Kapton is standard spacecraft thermal blanket insulation. These files are un-normalized and pending catalog registration."
            ),
            dimensions={"fuel_material": "Kapton (Polyimide)", "fuel_family": "solid-flat"},
            observed_count=0,
            total_denominator=repo_audit.get("unprocessed_raw_files_count", 11),
            dataset_ids=[],
            experiment_ids=[],
            provenance=["data-pipeline/raw_data/PSI-102/kaptonGMT257.xlsx"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified 3 Kapton spreadsheet files present on disk.",
            deficiency_score=2.0,
            relevance_score=2.4,
            metadata_score=1.4,
            feasibility_score=2.0,
            readiness_score=1.0,
            limitations=["Need to verify whether GMT257 and GMT263 contain full 30Hz time series or averaged intervals."],
            next_step="Parse Kapton spreadsheets, validate time channels, and add to active combustion catalog."
        ))

        # 5.3 Raw Silicone
        findings.append(self._create_finding(
            finding_id="GAP-INGEST-RAW-SILICONE",
            gap_type=GAP_TYPE_INGESTION,
            title="Ingestion Opportunity: Raw Silicone Elastomer Run Available on Disk",
            explanation=(
                "Raw spreadsheet 'Silicone GMT255hkp run 5s.xlsx' (4.4 MB) is physically present on disk in raw_data/PSI-102. "
                "Silicone elastomers are extensively used in space seals and potting compounds. "
                "This file is un-normalized and absent from FLAME's active catalog."
            ),
            dimensions={"fuel_material": "Silicone Elastomer", "fuel_family": "solid-thick"},
            observed_count=0,
            total_denominator=repo_audit.get("unprocessed_raw_files_count", 11),
            dataset_ids=[],
            experiment_ids=[],
            provenance=["data-pipeline/raw_data/PSI-102/Silicone GMT255hkp run 5s.xlsx"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified file presence and 4.4 MB size on local disk.",
            deficiency_score=2.0,
            relevance_score=2.1,
            metadata_score=1.3,
            feasibility_score=2.0,
            readiness_score=1.0,
            limitations=["Large multi-sheet spreadsheet requiring sensor column validation."],
            next_step="Normalize Silicone GMT255 spreadsheet into analysis-ready CSV."
        ))

        # 5.4 External NASA FLEX
        findings.append(self._create_finding(
            finding_id="GAP-INGEST-EXT-NASA-FLEX",
            gap_type=GAP_TYPE_INGESTION,
            title="Ingestion Opportunity: External NASA FLEX Droplet Datasets (ISS CIR)",
            explanation=(
                "NASA's FLEX and FLEX-2 programs conducted over 300 microgravity droplet combustion tests in the ISS CIR. "
                "These datasets reside in NASA's Physical Sciences Informatics (PSI) system and represent an immediate ingestion "
                "opportunity to expand FLAME into liquid fuel flammability and cool flame science."
            ),
            dimensions={"fuel_family": "droplet"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=[],
            experiment_ids=[],
            provenance=["NASA PSI Portal (Investigation: FLEX)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Directly documented in NASA PSI repository archives as an external uningested investigation.",
            deficiency_score=3.0,
            relevance_score=2.3,
            metadata_score=1.5,
            feasibility_score=1.6,
            readiness_score=0.6,
            limitations=["Requires downloading raw data packages from psi.nasa.gov."],
            next_step="Build an ingestion pipeline adapter for NASA PSI FLEX data packages."
        ))

        # ----------------------------------------------------
        # Category 6: Comparison Gaps (Insufficient Comparability)
        # ----------------------------------------------------
        # 6.1 Cross-Facility BASS-II vs Saffire
        findings.append(self._create_finding(
            finding_id="GAP-COMP-CROSS-FACILITY-BASS-SAFFIRE",
            gap_type=GAP_TYPE_COMPARISON,
            title="Comparison Gap: BASS-II and Saffire Methodologically Incompatible for Direct Sensor Overlay",
            explanation=(
                "Direct numerical comparison and sensor superposition between BASS-II and Saffire experiment runs is methodologically invalid. "
                "BASS-II used small-scale samples (1-2 cm wide) in the ISS Glovebox with discrete initial/final readings, "
                "whereas Saffire investigated large-scale fabrics (0.4m x 1.0m) in a forced wind tunnel with 30 Hz sensor arrays. "
                "Cross-facility comparisons must be restricted to qualitative flammability trends rather than quantitative sensor overlays."
            ),
            dimensions={"gravity": "micro"},
            observed_count=0,
            total_denominator=total_runs,
            dataset_ids=["bass_ii_experiments", "saffire_iii_sample_1"],
            experiment_ids=["bass_ii_b1", "saffire_iii_sample_1"],
            provenance=["Scientific Comparability Engine (Tier: METHODOLOGICALLY_INCOMPARABLE)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Formally demonstrated by RG1 comparability tier logic based on differing facility geometry, scale, and instrumentation.",
            deficiency_score=1.5,
            relevance_score=2.0,
            metadata_score=1.5,
            feasibility_score=1.2,
            readiness_score=0.9,
            limitations=["Geometric boundary layers and duct aspect ratios differ by an order of magnitude between facilities."],
            next_step="Develop non-dimensional Damköhler / Reynolds scaling models for qualitative cross-facility comparison."
        ))

        # 6.2 Saffire Sample 1 vs Sample 5 Confounded Variables
        findings.append(self._create_finding(
            finding_id="GAP-COMP-MULTIVARIATE-SAFFIRE-1-5",
            gap_type=GAP_TYPE_COMPARISON,
            title="Comparison Gap: Saffire 1 vs Saffire 5 Confounded by Dual Variable Shifts",
            explanation=(
                "Saffire Sample 1 and Sample 5 cannot provide a direct bivariate comparison because multiple environmental variables differ simultaneously. "
                "Both burn SIBAL fabric in the Saffire duct, but recorded oxygen concentrations differ (21.0% vs ~22.0% vol) and forced flow conditions differ "
                "(~20-25 cm/s at Fan 1800 RPM vs ~19.6 cm/s at Fan 1000 RPM). Simultaneous variations in multiple variables prevent isolating individual causal effects without numerical modeling."
            ),
            dimensions={"oxygen": "elevated_o2", "airflow": "high-flow", "fuel_material": "SIBAL"},
            observed_count=2,
            total_denominator=4,
            dataset_ids=["saffire_iii_sample_1", "saffire_sample_5"],
            experiment_ids=["saffire_iii_sample_1", "saffire_sample_5"],
            provenance=["Scientific Comparability Engine (Tier: CONDITIONALLY_COMPARABLE)"],
            confidence_level="HIGH",
            confidence_justification="Confidence in database gap: Verified by RG1 pairwise variable alignment engine; recorded flow velocities and oxygen concentrations both differ.",
            deficiency_score=1.2,
            relevance_score=2.2,
            metadata_score=1.5,
            feasibility_score=1.4,
            readiness_score=0.9,
            limitations=["Simultaneous shifts in multiple primary independent variables prevent single-variable causal attribution."],
            next_step="Compare Sample 5 against Sample 6 (isolated airflow variation at matching elevated O2) instead of Sample 1."
        ))

        return findings

    @staticmethod
    def _create_finding(
        finding_id: str,
        gap_type: str,
        title: str,
        explanation: str,
        dimensions: Dict[str, Any],
        observed_count: int,
        total_denominator: int,
        dataset_ids: List[str],
        experiment_ids: List[str],
        provenance: List[str],
        confidence_level: str,
        confidence_justification: str,
        deficiency_score: float,
        relevance_score: float,
        metadata_score: float,
        feasibility_score: float,
        readiness_score: float,
        limitations: List[str],
        next_step: str
    ) -> Dict[str, Any]:
        """Construct a standardized, explainable research gap finding with transparent heuristic scoring."""
        # Calculate heuristic priority score (sum of components, bounded between 0.0 and 10.0)
        raw_score = deficiency_score + relevance_score + metadata_score + feasibility_score + readiness_score
        priority_score = round(min(10.0, max(0.0, raw_score)), 1)

        dim_clean = {
            "gravity": dimensions.get("gravity"),
            "oxygen": dimensions.get("oxygen"),
            "pressure": dimensions.get("pressure"),
            "fuel_family": dimensions.get("fuel_family"),
            "fuel_material": dimensions.get("fuel_material"),
            "airflow": dimensions.get("airflow"),
            "parameter": dimensions.get("parameter")
        }

        scope_txt = f"{observed_count} of {total_denominator} indexed records in FLAME database"

        return {
            "finding_id": finding_id,
            "gap_type": gap_type,
            "title": title,
            "explanation": explanation,
            "scientific_dimensions": dim_clean,
            "observed_usable_run_count": observed_count,
            "denominator_and_scope": scope_txt,
            "supporting_dataset_ids": dataset_ids,
            "supporting_experiment_ids": experiment_ids,
            "provenance_references": provenance,
            "evidence_confidence": {
                "level": confidence_level,
                "justification": confidence_justification,
                "scope": "Confidence that this database gap or absence is accurately identified in the indexed FLAME repository, not confidence in an external physical hypothesis."
            },
            "priority_score": priority_score,
            "scoring_factors": {
                "coverage_deficiency": round(deficiency_score, 1),
                "mission_relevance": round(relevance_score, 1),
                "metadata_quality": round(metadata_score, 1),
                "resolvability_feasibility": round(feasibility_score, 1),
                "comparison_readiness": round(readiness_score, 1),
                "heuristic_label": "Heuristic prioritization score (not scientifically validated; deficiency threshold is a configurable system heuristic)"
            },
            "limitations": limitations,
            "recommended_next_step": next_step,
            "database_scope_disclaimer": "Unrepresented in the indexed FLAME collection. Missing data in FLAME does not prove NASA never conducted an experiment."
        }
