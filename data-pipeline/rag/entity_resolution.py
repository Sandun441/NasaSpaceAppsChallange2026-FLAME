"""
NASA FLAME — Canonical Entity Resolution & Experiment Compatibility Engine
Provides deterministic experiment-entity recognition, catalog resolution,
unresolved entity detection, and scientific comparison compatibility validation.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import re
from pathlib import Path
import json


class DatasetEntityResolver:
    """
    Deterministically resolves natural-language references to canonical NASA datasets
    and experiment records. Guarantees that explicitly requested experiments take priority
    over semantic similarity, and prevents silent substitution when matches are unavailable.
    """

    def __init__(self, records_path: Optional[Path] = None, catalog_path: Optional[Path] = None):
        self.base_dir = Path(__file__).resolve().parents[1]
        self.records_path = records_path or (self.base_dir / "processed_data" / "rag" / "scientific_knowledge_records.json")
        self.catalog_path = catalog_path or (self.base_dir / "processed_data" / "catalog" / "dataset_catalog.json")

        self.datasets: Dict[str, Dict[str, Any]] = {}
        self.records_by_id: Dict[str, Dict[str, Any]] = {}
        self.runs_by_dataset: Dict[str, List[Dict[str, Any]]] = {}
        self._load_catalog_and_records()

    def _load_catalog_and_records(self):
        """Loads canonical catalog and RAG knowledge records for exact lookup."""
        if self.catalog_path.is_file():
            try:
                with open(self.catalog_path, encoding="utf-8") as f:
                    cat = json.load(f)
                    for ds in cat.get("datasets", []):
                        self.datasets[ds["dataset_id"]] = ds
            except Exception:
                pass

        if self.records_path.is_file():
            try:
                with open(self.records_path, encoding="utf-8") as f:
                    recs = json.load(f)
                    for r in recs:
                        rid = r["record_id"]
                        self.records_by_id[rid] = r
                        ds_id = r.get("dataset_id")
                        if ds_id:
                            if ds_id not in self.runs_by_dataset:
                                self.runs_by_dataset[ds_id] = []
                            self.runs_by_dataset[ds_id].append(r)
            except Exception:
                pass

    def resolve(self, query: str) -> Dict[str, Any]:
        """
        Analyzes research query for explicit experiment entities.
        Returns:
            - requested_dataset_ids: List of canonical dataset IDs mentioned
            - requested_record_ids: List of specific knowledge record IDs mentioned
            - is_comparison: Boolean indicating comparison inquiry
            - unresolved_requested_entities: Explicit experiments requested but not present in corpus
        """
        q_lower = query.lower()
        requested_datasets: List[str] = []
        requested_records: List[str] = []
        unresolved: List[str] = []

        # -------------------------------------------------------------
        # 1. Saffire Sample Recognition
        # -------------------------------------------------------------
        # Matches "Sample 1", "Sample 2", "Sample 5", "Sample 6", with optional Saffire prefix
        saffire_matches = list(re.finditer(
            r"\b(?:saffire(?:-?iii|-?ii|-?i|\s+3|\s+2|\s+1)?\s+)?sample[-_\s]?([0-9]+)\b",
            q_lower
        ))

        for m in saffire_matches:
            sample_num = m.group(1)
            raw_mention = m.group(0)
            if sample_num == "1":
                ds_id = "saffire_iii_sample_1"
                rec_id = "flame_run_saffire_iii_sample_1"
                if ds_id not in requested_datasets:
                    requested_datasets.append(ds_id)
                if rec_id not in requested_records:
                    requested_records.append(rec_id)
            elif sample_num == "2":
                ds_id = "saffire_iii_sample_2"
                rec_id = "flame_run_saffire_iii_sample_2"
                if ds_id not in requested_datasets:
                    requested_datasets.append(ds_id)
                if rec_id not in requested_records:
                    requested_records.append(rec_id)
            elif sample_num == "5":
                ds_id = "saffire_sample_5"
                rec_id = "flame_run_saffire_sample_5"
                if ds_id not in requested_datasets:
                    requested_datasets.append(ds_id)
                if rec_id not in requested_records:
                    requested_records.append(rec_id)
            elif sample_num == "6":
                ds_id = "saffire_sample_6"
                rec_id = "flame_run_saffire_sample_6"
                if ds_id not in requested_datasets:
                    requested_datasets.append(ds_id)
                if rec_id not in requested_records:
                    requested_records.append(rec_id)
            else:
                # User explicitly requested a sample not in indexed corpus (e.g. Sample 3, 4, 99)
                if raw_mention not in unresolved:
                    unresolved.append(raw_mention)

        # Fuel substrate synonyms for Saffire
        if "sibal" in q_lower and "saffire_iii_sample_1" not in requested_datasets:
            requested_datasets.append("saffire_iii_sample_1")
            requested_records.append("flame_run_saffire_iii_sample_1")
        if "nomex" in q_lower and "saffire_iii_sample_2" not in requested_datasets:
            requested_datasets.append("saffire_iii_sample_2")
            requested_records.append("flame_run_saffire_iii_sample_2")

        # -------------------------------------------------------------
        # 2. BASS-II Test Run Recognition
        # -------------------------------------------------------------
        # Matches tests like "B6", "Test B6", "Bhattacharjee B6", "O5B", "Olson O5B", etc.
        bass_patterns = [
            (r"\b(?:bhattacharjee|test\s+)?(b[0-9]+)\b", "flame_run_bass_ii_bhattacharjee_"),
            (r"\b(?:olson|test\s+)?(o[0-9]+[a-z]?)\b", "flame_run_bass_ii_olson_"),
            (r"\b(?:ferkul|test\s+)?(f[0-9]+)\b", "flame_run_bass_ii_ferkul_"),
            (r"\b(?:tien|t-ien|test\s+)?(t[0-9]+)\b", "flame_run_bass_ii_t_ien_"),
            (r"\b(?:miller|test\s+)?(m[0-9]+)\b", "flame_run_bass_ii_miller_"),
            (r"\b(?:fernandez-pello|fernandez|test\s+)?(fp[0-9]+)\b", "flame_run_bass_ii_fernandez_pello_"),
        ]

        found_bass_run = False
        for pattern, prefix in bass_patterns:
            for match in re.finditer(pattern, q_lower):
                test_suffix = match.group(1)
                candidate_rec_id = f"{prefix}{test_suffix}"
                if candidate_rec_id in self.records_by_id:
                    if candidate_rec_id not in requested_records:
                        requested_records.append(candidate_rec_id)
                    if "bass_ii_experiments" not in requested_datasets:
                        requested_datasets.append("bass_ii_experiments")
                    found_bass_run = True
                elif bool(re.search(r"\b(test|bass|run)\b", q_lower)):
                    # Explicit test code mentioned with test/run prefix that does not exist in store
                    unresolved.append(f"BASS-II Test {test_suffix.upper()}")

        if not found_bass_run and re.search(r"\b(bass-ii|bass 2|bass experiments|glovebox)\b", q_lower):
            if "bass_ii_experiments" not in requested_datasets:
                requested_datasets.append("bass_ii_experiments")

        # -------------------------------------------------------------
        # 3. Spacecraft Telemetry Recognition
        # -------------------------------------------------------------
        if re.search(r"\b(smoke detector|fiz2|obscuration)\b", q_lower):
            ds = "telemetry_cygnus_smoke_detector_data"
            if ds not in requested_datasets:
                requested_datasets.append(ds)
        if re.search(r"\b(pcm pressure|cabin pressure)\b", q_lower):
            ds = "telemetry_cygnus_pressure_data"
            if ds not in requested_datasets:
                requested_datasets.append(ds)
        if re.search(r"\b(avionics temp|cygnus temperature)\b", q_lower):
            ds = "telemetry_cygnus_temperature_data"
            if ds not in requested_datasets:
                requested_datasets.append(ds)

        # -------------------------------------------------------------
        # 4. Comparison Intent Detection
        # -------------------------------------------------------------
        is_comparison = bool(re.search(
            r"\b(compar|differ|versus|vs|against|contrast|relative to|similarity|similarities|sample 1.*sample 2|nomex.*sibal)\b",
            q_lower
        )) or len(requested_datasets) >= 2 or len(requested_records) >= 2

        return {
            "requested_dataset_ids": requested_datasets,
            "requested_record_ids": requested_records,
            "is_comparison": is_comparison,
            "unresolved_requested_entities": unresolved,
        }

    def validate_comparison_compatibility(
        self,
        dataset_a: str,
        dataset_b: str,
    ) -> Dict[str, Any]:
        """
        Validates whether two datasets can be scientifically compared in the comparison workspace.
        Returns compatibility status, supported alignment modes, and shared measurement channels.
        """
        if not dataset_a or not dataset_b:
            return {
                "is_compatible": False,
                "reason": "Both dataset A and dataset B must be specified for scientific comparison.",
                "supported_modes": [],
                "shared_channels": [],
            }

        saffire_continuous = {
            "saffire_iii_sample_1",
            "saffire_iii_sample_2",
            "saffire_sample_5",
            "saffire_sample_6",
        }

        # Case 1: Both are Saffire continuous sensor time-series
        if dataset_a in saffire_continuous and dataset_b in saffire_continuous:
            return {
                "is_compatible": True,
                "reason": "Compatible Saffire microgravity flight sensor runs with shared thermocouple and radiometer suites.",
                "supported_modes": ["side_by_side", "overlay_event_aligned", "overlay_recorded"],
                "default_mode": "overlay_event_aligned",
                "shared_channels": [
                    "Surface Thermocouples (TC7–TC12, °C)",
                    "Plume Thermocouples (TC1–TC6, °C)",
                    "Heat Flux Radiometers (Radiometers 1–4, mW/cm²)",
                    "Chamber Pressure (psia)",
                    "Ventilation Flow Velocity (cm/s)"
                ],
            }

        # Case 2: Both are BASS-II discrete matrix
        if dataset_a == "bass_ii_experiments" and dataset_b == "bass_ii_experiments":
            return {
                "is_compatible": True,
                "reason": "Compatible BASS-II discrete glovebox burn matrix with shared gas deltas and spread rates.",
                "supported_modes": ["bass_matrix_comparison"],
                "default_mode": "bass_matrix_comparison",
                "shared_channels": [
                    "Oxygen Depletion ΔO₂ (%)",
                    "Carbon Dioxide Generation ΔCO₂ (%)",
                    "Flame Spread Rate (cm/s)",
                    "Burn Duration (s)",
                ],
            }

        # Case 3: Spacecraft telemetry suites
        telemetry_suites = {
            "telemetry_cygnus_data",
            "telemetry_cygnus_pressure_data",
            "telemetry_cygnus_temperature_data",
            "telemetry_cygnus_smoke_detector_data",
            "telemetry_saffire_data",
        }
        if dataset_a in telemetry_suites and dataset_b in telemetry_suites:
            return {
                "is_compatible": True,
                "reason": "Compatible spacecraft vehicle telemetry time series with timestamp alignment.",
                "supported_modes": ["side_by_side", "overlay_recorded"],
                "default_mode": "side_by_side",
                "shared_channels": ["Timestamp / Flight Epoch (s)"],
            }

        # Case 4: Incompatible cross-category comparison
        return {
            "is_compatible": False,
            "reason": (
                f"Dataset '{dataset_a}' and dataset '{dataset_b}' have incompatible physical granularities "
                f"(continuous high-frequency sensor time-series vs discrete matrix/telemetry) and cannot be directly compared."
            ),
            "supported_modes": [],
            "shared_channels": [],
        }
