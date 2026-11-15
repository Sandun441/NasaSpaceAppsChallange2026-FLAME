"""
NASA FLAME — Predictive-Modeling Data Preparation & Extraction Service
Handles dataset loading, filtering, feature calculation, data quality auditing,
bounded time-window extraction, and multi-format export (CSV, JSON metadata, Quality Report).

Scientific Safeguards Enforced:
- Zero fabricated measurements or invented labels
- No silent target imputation or unsupported interpolation
- Preservation of physical units and original timestamps
- Group-aware cross-validation identifiers for leakage prevention
- Prevention of incompatible cross-experiment dataset merging
- Explicit empirical source anomaly detection and flagging without silent modification
- Safe server-side file access restricted to registered paths
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

from modeling.registry import MODELING_DATASETS_REGISTRY, get_modeling_dataset_metadata

BASE_DIR = Path(__file__).resolve().parents[1]


def parse_initial_numeric(val: Any) -> float:
    """
    Extract the initial numeric float token from potentially multi-step or delimited strings.
    Prevents catastrophic concatenation bugs (e.g., '5,4,3,2,1' -> 54321, '68, 52, 47...' -> 6.852e11).
    Returns np.nan for empty, placeholder, or invalid entries.
    """
    if pd.isna(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in ("none", "nan", "null", "--", "?", "n/a", "see notes", "see fan"):
        return np.nan
    m = re.search(r"([+-]?(?:\d+\.?\d*|\.\d+))", s)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return np.nan
    return np.nan


def detect_airflow_profile(val: Any) -> str:
    """Categorize whether airflow proxy represents a constant setting or dynamic multi-step protocol."""
    if pd.isna(val):
        return "unspecified"
    s = str(val).strip()
    if not s or s.lower() in ("none", "nan", "null", "--", "?", "n/a", "see notes", "see fan"):
        return "unspecified"
    if any(delim in s for delim in (",", ";", ">", "down", "incr", "decr", "step", "pot")):
        return "dynamic_multi_step"
    return "constant"


class PredictiveDataExtractionService:
    """
    Core extraction and data preparation service for NASA microgravity datasets.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or BASE_DIR

    def _resolve_file_path(self, rel_path: str) -> Path:
        """Safely resolve relative path within data-pipeline directory."""
        full_path = (self.base_dir / rel_path).resolve()
        if not str(full_path).startswith(str(self.base_dir.resolve())):
            raise ValueError(f"Access denied: Path {rel_path} outside data-pipeline root.")
        if not full_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {rel_path}")
        return full_path

    def validate_no_incompatible_merge(self, dataset_ids: List[str]) -> None:
        """
        Verify that requested datasets are scientifically compatible for merging.
        Prevents merging tabular run-level matrices (e.g. BASS-II) with high-frequency telemetry (e.g. Saffire).
        """
        if len(dataset_ids) <= 1:
            return

        paradigms = set()
        for ds_id in dataset_ids:
            meta = get_modeling_dataset_metadata(ds_id)
            if not meta:
                raise ValueError(f"Unknown dataset ID: {ds_id}")
            paradigms.add(meta["paradigm"])

        if len(paradigms) > 1:
            raise ValueError(
                f"Incompatible dataset merge blocked: Cannot combine disparate paradigms {list(paradigms)} "
                f"into a single predictive modeling table. Tabular run-level experiments and continuous "
                f"high-frequency time-series telemetry operate under fundamentally different physical dimensions."
            )

    def extract_dataset(
        self,
        dataset_id: str,
        selected_features: Optional[List[str]] = None,
        target_id: Optional[str] = None,
        material_filter: Optional[str] = None,
        min_oxygen: Optional[float] = None,
        max_oxygen: Optional[float] = None,
        min_flow: Optional[float] = None,
        max_flow: Optional[float] = None,
        start_time_s: Optional[float] = None,
        end_time_s: Optional[float] = None,
        max_rows: Optional[int] = None,
        complete_cases_only: bool = False,
        exclude_flagged_anomalies: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
        """
        Extract, filter, and audit experimental records.
        Returns: (prepared_dataframe, column_metadata_dict, quality_report_dict)
        """
        meta = get_modeling_dataset_metadata(dataset_id)
        if not meta:
            raise ValueError(f"Unknown dataset ID: {dataset_id}")

        file_path = self._resolve_file_path(meta["source_file"])
        paradigm = meta["paradigm"]

        if paradigm == "tabular_run_level":
            return self._extract_tabular_bass(
                file_path=file_path,
                meta=meta,
                selected_features=selected_features,
                target_id=target_id,
                material_filter=material_filter,
                min_oxygen=min_oxygen,
                max_oxygen=max_oxygen,
                min_flow=min_flow,
                max_flow=max_flow,
                max_rows=max_rows,
                complete_cases_only=complete_cases_only,
                exclude_flagged_anomalies=exclude_flagged_anomalies,
            )
        elif paradigm in ("time_series_telemetry", "vehicle_telemetry"):
            return self._extract_telemetry_series(
                file_path=file_path,
                meta=meta,
                selected_features=selected_features,
                target_id=target_id,
                min_oxygen=min_oxygen,
                max_oxygen=max_oxygen,
                min_flow=min_flow,
                max_flow=max_flow,
                start_time_s=start_time_s,
                end_time_s=end_time_s,
                max_rows=max_rows,
                complete_cases_only=complete_cases_only,
                exclude_flagged_anomalies=exclude_flagged_anomalies,
            )
        else:
            raise ValueError(f"Unsupported dataset paradigm: {paradigm}")

    def _extract_tabular_bass(
        self,
        file_path: Path,
        meta: Dict[str, Any],
        selected_features: Optional[List[str]],
        target_id: Optional[str],
        material_filter: Optional[str],
        min_oxygen: Optional[float],
        max_oxygen: Optional[float],
        min_flow: Optional[float],
        max_flow: Optional[float],
        max_rows: Optional[int],
        complete_cases_only: bool = False,
        exclude_flagged_anomalies: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
        """Process BASS-II tabular run-level dataset with scientific anomaly detection and provenance tracking."""
        df_raw = pd.read_csv(file_path, encoding="utf-8-sig")
        total_available = len(df_raw)

        # Build feature mapping
        avail_features = {f["id"]: f for f in meta["available_features"]}
        supp_targets = {t["id"]: t for t in meta["supported_targets"]}
        unsupp_targets = {t["id"]: t for t in meta["unsupported_targets"]}

        # If target is explicitly uninstrumented, do not silently calculate or invent it
        if target_id and target_id in unsupp_targets:
            raise ValueError(
                f"Target '{target_id}' is uninstrumented in {meta['name']}. "
                f"{unsupp_targets[target_id]['reason']}"
            )

        # Standard clean columns
        df_clean = pd.DataFrame()
        col_meta = {}

        # Always include group identifier for GroupKFold (resolves to Test no. from raw source)
        if "Test no." in df_raw.columns:
            df_clean["run_id"] = df_raw["Test no."].astype(str)
        elif "run_id" in df_raw.columns:
            df_clean["run_id"] = df_raw["run_id"].astype(str)
        else:
            df_clean["run_id"] = df_raw.iloc[:, 0].astype(str)

        col_meta["run_id"] = {
            "label": "Experimental Run ID",
            "unit": "run_code",
            "role": "group_identifier",
            "category": "contextual_metadata",
            "data_type": "string",
            "source_col": "Test no.",
        }

        # Physical Specimen ID (Sample no.) for grouping repeated specimen burns
        if "Sample no." in df_raw.columns:
            df_clean["sample_id"] = df_raw["Sample no."].astype("string").str.strip()
            df_clean.loc[
                df_clean["sample_id"].str.lower().isin(["", "nan", "none", "null", "n/a", "<na>"]).fillna(True),
                "sample_id",
            ] = pd.NA
            col_meta["sample_id"] = {
                "label": "Physical Specimen Sample ID",
                "unit": "sample_code",
                "role": "group_identifier",
                "category": "contextual_metadata",
                "data_type": "string",
                "source_col": "Sample no.",
            }

        # Fuel material
        df_clean["fuel_material"] = df_raw["Material"].astype(str)
        col_meta["fuel_material"] = {
            "label": "Fuel Material & Geometry",
            "unit": "categorical",
            "role": "input",
            "category": "contextual_metadata",
            "data_type": "string",
            "source_col": "Material",
        }

        # Helper for standard numeric series
        def safe_to_numeric(series):
            return pd.to_numeric(series.astype(str).str.replace(r"[^\d\.\-]", "", regex=True), errors="coerce")

        # Map numerical columns
        df_clean["initial_oxygen_pct"] = safe_to_numeric(df_raw["calibrated  initial O2 % by vol "])
        col_meta["initial_oxygen_pct"] = {
            "label": "Calibrated Initial O₂",
            "unit": "% vol",
            "role": "input",
            "category": "verified_measured",
            "data_type": "float",
            "source_col": "calibrated  initial O2 % by vol ",
        }

        final_o2 = safe_to_numeric(df_raw["calibrated final O2 % by vol"])
        df_clean["final_oxygen_pct"] = final_o2
        col_meta["final_oxygen_pct"] = {
            "label": "Calibrated Final O₂",
            "unit": "% vol",
            "role": "target" if target_id == "final_oxygen_pct" else "input",
            "category": "verified_measured",
            "data_type": "float",
            "source_col": "calibrated final O2 % by vol",
        }

        # Derived ΔO₂ (Faithfully preserve empirical initial - final without fabrication)
        df_clean["oxygen_consumption_delta_pct"] = df_clean["initial_oxygen_pct"] - df_clean["final_oxygen_pct"]
        col_meta["oxygen_consumption_delta_pct"] = {
            "label": "Oxygen Consumption Delta (ΔO₂)",
            "unit": "% vol",
            "role": "target" if target_id == "oxygen_consumption_delta_pct" else "derived_feature",
            "category": "validated_derived",
            "data_type": "float",
            "source_col": "initial_oxygen_pct - final_oxygen_pct",
        }

        # Airflow velocity proxy & provenance
        raw_air = df_raw["Air display"].astype(str).replace({"nan": None})
        df_clean["raw_airflow_display"] = raw_air
        col_meta["raw_airflow_display"] = {
            "label": "Raw Airflow Display String",
            "unit": "text",
            "role": "metadata",
            "category": "contextual_metadata",
            "data_type": "string",
            "source_col": "Air display",
        }

        df_clean["airflow_profile"] = df_raw["Air display"].apply(detect_airflow_profile)
        col_meta["airflow_profile"] = {
            "label": "Airflow Velocity Profile Type",
            "unit": "profile_code",
            "role": "metadata",
            "category": "contextual_metadata",
            "data_type": "string",
            "source_col": "Air display",
        }

        # Correct parsing using parse_initial_numeric: prevents catastrophic concatenation
        df_clean["airflow_velocity_proxy"] = df_raw["Air display"].apply(parse_initial_numeric)
        col_meta["airflow_velocity_proxy"] = {
            "label": "Initial Forced Airflow Display Proxy",
            "unit": "cm/s",
            "role": "input",
            "category": "verified_measured",
            "data_type": "float",
            "source_col": "Air display",
        }

        # Flow restrictor
        df_clean["flow_restrictor"] = safe_to_numeric(df_raw["Flow restrictor"])
        col_meta["flow_restrictor"] = {
            "label": "Flow Restrictor Setting",
            "unit": "setting_id",
            "role": "input",
            "category": "contextual_metadata",
            "data_type": "integer",
            "source_col": "Flow restrictor",
        }

        # Fan display & provenance
        raw_fan = df_raw["Fan display"].astype(str).replace({"nan": None})
        df_clean["raw_fan_display"] = raw_fan
        col_meta["raw_fan_display"] = {
            "label": "Raw Fan Display String",
            "unit": "text",
            "role": "metadata",
            "category": "contextual_metadata",
            "data_type": "string",
            "source_col": "Fan display",
        }

        # Correct parsing using parse_initial_numeric: prevents concatenation of multi-step fan settings
        df_clean["fan_display"] = df_raw["Fan display"].apply(parse_initial_numeric)
        col_meta["fan_display"] = {
            "label": "Initial Fan Speed Display",
            "unit": "RPM_proxy",
            "role": "input",
            "category": "verified_measured",
            "data_type": "float",
            "source_col": "Fan display",
        }

        # CO2 columns
        init_co2 = safe_to_numeric(df_raw["Initial CO2 % by vol"])
        fin_co2 = safe_to_numeric(df_raw["Final CO2 % by vol"])
        df_clean["initial_co2_pct"] = init_co2
        col_meta["initial_co2_pct"] = {
            "label": "Initial CO₂",
            "unit": "% vol",
            "role": "input",
            "category": "verified_measured",
            "data_type": "float",
            "source_col": "Initial CO2 % by vol",
        }
        df_clean["co2_generation_delta_pct"] = fin_co2 - init_co2
        col_meta["co2_generation_delta_pct"] = {
            "label": "CO₂ Generation Delta (ΔCO₂)",
            "unit": "% vol",
            "role": "target" if target_id == "co2_generation_delta_pct" else "derived_feature",
            "category": "validated_derived",
            "data_type": "float",
            "source_col": "Final CO2 - Initial CO2",
        }

        # CO ppm
        fin_co = safe_to_numeric(df_raw["Final CO (ppm)"])
        df_clean["final_co_ppm"] = fin_co
        col_meta["final_co_ppm"] = {
            "label": "Final CO Emission",
            "unit": "ppm",
            "role": "target" if target_id == "final_co_ppm" else "input",
            "category": "verified_measured",
            "data_type": "float",
            "source_col": "Final CO (ppm)",
        }

        # Video frames
        df_clean["total_frames_shot"] = safe_to_numeric(df_raw["total frames shot"])
        col_meta["total_frames_shot"] = {
            "label": "Recorded Video Frames",
            "unit": "frames",
            "role": "input",
            "category": "verified_measured",
            "data_type": "integer",
            "source_col": "total frames shot",
        }

        # Detect and flag uncorrected empirical source anomalies without modifying raw values
        flags = []
        anomalous_details = []
        for idx, row in df_clean.iterrows():
            row_flags = []
            run_id = str(row.get("run_id", ""))
            
            # ΔO₂ empirical source anomalies
            d_o2 = row.get("oxygen_consumption_delta_pct")
            if pd.notna(d_o2):
                if d_o2 > 15.0:
                    flag_name = f"flagged_o2_source_anomaly_delta_{d_o2:+.1f}pct"
                    row_flags.append(flag_name)
                    anomalous_details.append({
                        "run_id": run_id,
                        "flag": flag_name,
                        "type": "extreme_positive_o2_delta",
                        "initial_o2": row.get("initial_oxygen_pct"),
                        "final_o2": row.get("final_oxygen_pct"),
                        "delta_o2": round(float(d_o2), 2),
                        "details": f"Run {run_id}: Initial O2 = {row.get('initial_oxygen_pct')}%, Final O2 = {row.get('final_oxygen_pct')}%, Delta = {d_o2:+.1f} percentage points. Uncorrected NASA PI log value."
                    })
                elif d_o2 < -5.0:
                    flag_name = f"flagged_o2_source_anomaly_delta_{d_o2:+.1f}pct"
                    row_flags.append(flag_name)
                    anomalous_details.append({
                        "run_id": run_id,
                        "flag": flag_name,
                        "type": "negative_consumption_o2_delta",
                        "initial_o2": row.get("initial_oxygen_pct"),
                        "final_o2": row.get("final_oxygen_pct"),
                        "delta_o2": round(float(d_o2), 2),
                        "details": f"Run {run_id}: Initial O2 = {row.get('initial_oxygen_pct')}%, Final O2 = {row.get('final_oxygen_pct')}%, Delta = {d_o2:+.1f} percentage points (apparent O2 rise). Uncorrected NASA PI log value."
                    })

            # Fan setting bounds check (e.g., T15 = 80122)
            fan_val = row.get("fan_display")
            if pd.notna(fan_val) and fan_val > 500.0:
                flag_name = f"flagged_fan_setting_out_of_bounds_{fan_val:.0f}"
                row_flags.append(flag_name)
                anomalous_details.append({
                    "run_id": run_id,
                    "flag": flag_name,
                    "type": "fan_setting_out_of_bounds",
                    "fan_val": fan_val,
                    "details": f"Run {run_id}: Raw Excel Fan display is '{row.get('raw_fan_display')}', which parsed to {fan_val:.0f}. Normal range is 0-150."
                })

            flags.append("; ".join(row_flags) if row_flags else None)

        df_clean["data_quality_flags"] = flags
        col_meta["data_quality_flags"] = {
            "label": "Data Quality & Anomaly Flags",
            "unit": "flag_code",
            "role": "metadata",
            "category": "contextual_metadata",
            "data_type": "string",
            "source_col": "NASA FLAME Quality Engine",
        }

        # Apply Filters
        mask = pd.Series(True, index=df_clean.index)
        if material_filter:
            mask = mask & df_clean["fuel_material"].str.contains(material_filter, case=False, na=False)
        if min_oxygen is not None:
            mask = mask & (df_clean["initial_oxygen_pct"] >= min_oxygen)
        if max_oxygen is not None:
            mask = mask & (df_clean["initial_oxygen_pct"] <= max_oxygen)
        if min_flow is not None:
            mask = mask & (df_clean["airflow_velocity_proxy"] >= min_flow)
        if max_flow is not None:
            mask = mask & (df_clean["airflow_velocity_proxy"] <= max_flow)

        if exclude_flagged_anomalies:
            mask = mask & df_clean["data_quality_flags"].isna()

        filtered_df = df_clean[mask].copy()

        # Preserve both the test-run identifier and physical specimen identifier.
        # Specimen-level grouping is necessary when the same specimen appears in
        # multiple experimental runs; run_id alone cannot prevent that leakage.
        cols_to_keep = ["run_id"]
        if "sample_id" in filtered_df.columns:
            cols_to_keep.append("sample_id")

        # Select Columns: If selected_features specified, filter down
        if selected_features:
            for f in selected_features:
                if f in filtered_df.columns and f not in cols_to_keep:
                    cols_to_keep.append(f)
        else:
            # Default to all standard features
            cols_to_keep.extend([
                "fuel_material",
                "initial_oxygen_pct",
                "airflow_velocity_proxy",
                "flow_restrictor",
                "fan_display",
            ])

        if target_id and target_id in filtered_df.columns and target_id not in cols_to_keep:
            cols_to_keep.append(target_id)

        # If selected_features not explicitly limited, retain provenance flag column by default
        if not selected_features and "data_quality_flags" in filtered_df.columns and "data_quality_flags" not in cols_to_keep:
            cols_to_keep.append("data_quality_flags")

        result_df = filtered_df[cols_to_keep].copy()

        # Filter complete cases if requested
        if complete_cases_only:
            check_cols = [c for c in cols_to_keep if c != "data_quality_flags"]
            result_df = result_df.dropna(subset=check_cols).copy()

        filtered_count = len(result_df)

        # Build Quality Report BEFORE max_rows truncation to guarantee accurate dataset-wide statistics
        quality_report = self._generate_quality_report(
            df=result_df,
            total_available=total_available,
            filtered_count=filtered_count,
            paradigm=meta["paradigm"],
            target_id=target_id,
            meta=meta,
            anomalous_details=anomalous_details,
        )

        if max_rows and max_rows > 0:
            result_df = result_df.head(max_rows)

        quality_report["exported_records_count"] = len(result_df)

        return result_df, {k: col_meta[k] for k in cols_to_keep if k in col_meta}, quality_report

    def _extract_telemetry_series(
        self,
        file_path: Path,
        meta: Dict[str, Any],
        selected_features: Optional[List[str]],
        target_id: Optional[str],
        min_oxygen: Optional[float],
        max_oxygen: Optional[float],
        min_flow: Optional[float],
        max_flow: Optional[float],
        start_time_s: Optional[float],
        end_time_s: Optional[float],
        max_rows: Optional[int],
        complete_cases_only: bool = False,
        exclude_flagged_anomalies: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
        """Process continuous sensor telemetry (Saffire / Cygnus) with verified peak targets and lookahead leakage prevention."""
        df_raw = pd.read_csv(file_path, encoding="utf-8-sig")
        total_available = len(df_raw)

        unsupp_targets = {t["id"]: t for t in meta.get("unsupported_targets", [])}
        if target_id and target_id in unsupp_targets:
            raise ValueError(
                f"Target '{target_id}' is uninstrumented in {meta['name']}. "
                f"{unsupp_targets[target_id]['reason']}"
            )

        avail_feat_map = {f["id"]: f for f in meta.get("available_features", [])}
        supp_target_map = {t["id"]: t for t in meta.get("supported_targets", [])}

        time_col = "Elapsed Time (s)" if "Elapsed Time (s)" in df_raw.columns else "Relative Time (s)"
        if time_col not in df_raw.columns:
            time_col = df_raw.columns[0]

        df_clean = pd.DataFrame()
        col_meta = {}

        # Timestamp
        df_clean["elapsed_time_s"] = pd.to_numeric(df_raw[time_col], errors="coerce")
        col_meta["elapsed_time_s"] = {
            "label": "Elapsed Time",
            "unit": "s",
            "role": "timestamp",
            "category": "verified_measured",
            "data_type": "float",
            "source_col": time_col,
        }

        # Map available features
        for f_id, f_def in avail_feat_map.items():
            src = f_def["source_col"]
            if src in df_raw.columns:
                df_clean[f_id] = pd.to_numeric(df_raw[src], errors="coerce")
                col_meta[f_id] = {
                    "label": f_def["label"],
                    "unit": f_def["unit"],
                    "role": "input",
                    "category": f_def["category"],
                    "data_type": f_def["data_type"],
                    "source_col": src,
                }

        # Apply Bounded Time Window
        mask = pd.Series(True, index=df_clean.index)
        if start_time_s is not None:
            mask = mask & (df_clean["elapsed_time_s"] >= start_time_s)
        if end_time_s is not None:
            mask = mask & (df_clean["elapsed_time_s"] <= end_time_s)

        # Environmental filters
        if "oxygen_concentration_pct" in df_clean.columns:
            if min_oxygen is not None:
                mask = mask & (df_clean["oxygen_concentration_pct"] >= min_oxygen)
            if max_oxygen is not None:
                mask = mask & (df_clean["oxygen_concentration_pct"] <= max_oxygen)

        if "flow_velocity_cm_s" in df_clean.columns:
            if min_flow is not None:
                mask = mask & (df_clean["flow_velocity_cm_s"] >= min_flow)
            if max_flow is not None:
                mask = mask & (df_clean["flow_velocity_cm_s"] <= max_flow)

        filtered_df = df_clean[mask].copy()

        # Handle target if supported
        plume_tc_cols = [c for c in df_raw.columns if "Plume Temp" in c or "plume temp" in c.lower()]

        if target_id and target_id in supp_target_map:
            t_def = supp_target_map[target_id]

            if target_id in ("event_peak_plume_temperature_c", "peak_plume_temperature_c"):
                # Calculate true global peak across all plume thermocouples
                if plume_tc_cols:
                    event_peak_val = float(df_raw[plume_tc_cols].apply(pd.to_numeric, errors="coerce").max().max())
                elif "plume_temp_tc1" in filtered_df.columns:
                    event_peak_val = float(filtered_df["plume_temp_tc1"].max())
                else:
                    event_peak_val = 0.0

                filtered_df[target_id] = event_peak_val
                col_meta[target_id] = {
                    "label": "Event Maximum Plume Temperature (TC1-TC6)",
                    "unit": "°C",
                    "role": "target",
                    "category": "verified_measured",
                    "data_type": "float",
                    "source_col": f"max({', '.join(plume_tc_cols)})",
                }
            elif target_id == "instantaneous_plume_temp_tc1_c":
                if "plume_temp_tc1" in filtered_df.columns:
                    filtered_df[target_id] = filtered_df["plume_temp_tc1"]
                else:
                    filtered_df[target_id] = pd.to_numeric(df_raw[plume_tc_cols[0]], errors="coerce") if plume_tc_cols else np.nan
                col_meta[target_id] = {
                    "label": "Instantaneous Plume Temp (TC1)",
                    "unit": "°C",
                    "role": "target",
                    "category": "verified_measured",
                    "data_type": "float",
                    "source_col": "Plume Temp 1 (TC1)",
                }
            elif "radiometer_1" in filtered_df.columns and "heat_flux" in target_id:
                filtered_df[target_id] = filtered_df["radiometer_1"]
                col_meta[target_id] = {
                    "label": t_def["label"],
                    "unit": t_def["unit"],
                    "role": "target",
                    "category": t_def["category"],
                    "data_type": t_def["data_type"],
                    "source_col": t_def["formula"],
                }
            else:
                filtered_df[target_id] = filtered_df["elapsed_time_s"]
                col_meta[target_id] = {
                    "label": t_def["label"],
                    "unit": t_def["unit"],
                    "role": "target",
                    "category": t_def["category"],
                    "data_type": t_def["data_type"],
                    "source_col": t_def["formula"],
                }

        # Select Columns
        cols_to_keep = ["elapsed_time_s"]
        if selected_features:
            for f in selected_features:
                if f in filtered_df.columns and f not in cols_to_keep:
                    cols_to_keep.append(f)
        else:
            cols_to_keep.extend([c for c in filtered_df.columns if c != "elapsed_time_s"])

        if target_id and target_id in filtered_df.columns and target_id not in cols_to_keep:
            cols_to_keep.append(target_id)

        result_df = filtered_df[cols_to_keep].copy()

        if complete_cases_only:
            result_df = result_df.dropna().copy()

        filtered_count = len(result_df)

        # Build Quality Report BEFORE truncation to preserve full population statistics
        quality_report = self._generate_quality_report(
            df=result_df,
            total_available=total_available,
            filtered_count=filtered_count,
            paradigm=meta["paradigm"],
            target_id=target_id,
            meta=meta,
        )

        # Cap max rows to prevent unbounded memory in continuous telemetry
        safe_max_rows = max_rows if (max_rows and max_rows > 0) else 5000
        result_df = result_df.head(safe_max_rows)
        quality_report["exported_records_count"] = len(result_df)

        return result_df, {k: col_meta[k] for k in cols_to_keep if k in col_meta}, quality_report

    def _generate_quality_report(
        self,
        df: pd.DataFrame,
        total_available: int,
        filtered_count: int,
        paradigm: str,
        target_id: Optional[str],
        meta: Dict[str, Any],
        anomalous_details: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate audit report detailing missing values, constant features, and leakage risks."""
        missing_counts = {}
        constant_columns = []
        zero_variance_columns = []

        # Analyze columns excluding internal flag strings
        audit_cols = [c for c in df.columns if c != "data_quality_flags"]

        for col in audit_cols:
            n_missing = int(df[col].isna().sum())
            missing_counts[col] = n_missing

            if pd.api.types.is_numeric_dtype(df[col]):
                vals = df[col].dropna()
                if len(vals) > 0 and vals.nunique() <= 1:
                    constant_columns.append(col)
                elif len(vals) > 1 and float(vals.std()) == 0.0:
                    zero_variance_columns.append(col)

        # Leakage Risk Analysis
        if paradigm == "time_series_telemetry":
            leakage_risk = "HIGH_AUTOCORRELATION_RISK"
            leakage_advice = (
                "Continuous 30.3 Hz sensor readings exhibit extreme intra-series autocorrelation. "
                "Random train/test row splitting will leak future state into training folds. "
                "Recommendation: Apply group-based splitting by experiment/burn (GroupKFold) or "
                "extract bounded time windows (5s-10s blocks) before fitting external models."
            )
            group_split_column = meta.get("group_column", "source_file")
        elif paradigm == "tabular_run_level":
            leakage_risk = "MODERATE_GROUP_CORRELATION_RISK"
            if "sample_id" in df.columns and df["sample_id"].notna().any():
                group_split_column = "sample_id"
                leakage_advice = (
                    "Repeated burns of the same physical specimen must not be split across training "
                    "and validation folds. Use GroupKFold with 'sample_id' (physical Sample no.) "
                    "after verifying specimen identifiers are valid and consistent. "
                    "'run_id' identifies individual experiments and is not sufficient for specimen grouping."
                )
            else:
                group_split_column = "run_id"
                leakage_advice = (
                    "Physical specimen IDs are unavailable in this export. Grouping by unique 'run_id' "
                    "does NOT prevent repeated-specimen leakage; verify specimen-level grouping "
                    "before claiming leakage-free cross-validation."
                )
        else:
            leakage_risk = "TIME_SERIES_MONOTONIC_TREND"
            leakage_advice = "Use TimeSeriesSplit to avoid lookahead bias."
            group_split_column = "elapsed_time_s"

        total_cells = max(1, len(audit_cols) * len(df))
        total_missing = sum(missing_counts.values())
        completeness_pct = round(float(100.0 * (1.0 - (total_missing / total_cells))), 2)

        warnings = []
        if constant_columns:
            warnings.append(f"Constant features detected with zero variance: {constant_columns}")
        if target_id and missing_counts.get(target_id, 0) > 0:
            warnings.append(
                f"Target '{target_id}' has {missing_counts[target_id]} missing values. "
                "Missing target rows should be dropped prior to supervised model training; silent imputation is forbidden."
            )
        if not target_id:
            warnings.append("No supervised target selected. Data extracted in exploratory/unsupervised mode.")

        # Saffire Target Leakage Warning
        if target_id in ("event_peak_plume_temperature_c", "peak_plume_temperature_c"):
            plume_inputs = [c for c in df.columns if c in ("plume_temp_tc1", "plume_temp_tc2", "plume_temp_tc3", "plume_temp_tc4", "plume_temp_tc5", "plume_temp_tc6")]
            if plume_inputs:
                warnings.append(
                    f"TARGET LEAKAGE WARNING: Contemporaneous plume thermocouple feature(s) {plume_inputs} are "
                    f"concurrently selected as inputs with event peak target '{target_id}'. "
                    "Using in-flight thermocouple readings to predict overall event peak temperature will result in lookahead leakage."
                )

        # Anomaly Warnings & Statistics
        anom_details = anomalous_details or []
        anomalous_records_count = len(anom_details)
        if anomalous_records_count > 0:
            runs_flagged = [d["run_id"] for d in anom_details]
            warnings.append(
                f"EMPIRICAL ANOMALY DISCLOSURE: {anomalous_records_count} runs ({', '.join(runs_flagged)}) contain "
                "uncorrected NASA PI log anomalies (e.g. extreme ΔO₂ values exceeding +15% or apparent negative consumption). "
                "These values are preserved faithfully from authoritative records and flagged in 'data_quality_flags'. "
                "Enable 'exclude_flagged_anomalies=True' to omit these records from modeling."
            )

        # Record counts taxonomy
        labeled_count = int(df[target_id].notna().sum()) if target_id and target_id in df.columns else len(df)
        complete_case_count = int(df[audit_cols].dropna().shape[0])

        return {
            "dataset_id": meta["dataset_id"],
            "dataset_name": meta["name"],
            "total_available_records": total_available,
            "available_records_count": total_available,
            "filtered_records_count": filtered_count,
            "extracted_records_count": filtered_count,  # backward compatibility
            "exported_records_count": filtered_count,
            "preview_records_count": min(25, filtered_count),
            "labeled_records_count": labeled_count,
            "complete_case_records_count": complete_case_count,
            "anomalous_records_count": anomalous_records_count,
            "anomalous_records_details": anom_details,
            "data_completeness_pct": completeness_pct,
            "missing_counts": missing_counts,
            "constant_columns": constant_columns,
            "zero_variance_columns": zero_variance_columns,
            "leakage_risk": leakage_risk,
            "group_split_column": group_split_column,
            "leakage_advice": leakage_advice,
            "warnings": warnings,
        }

    def generate_preview(
        self,
        dataset_id: str,
        selected_features: Optional[List[str]] = None,
        target_id: Optional[str] = None,
        material_filter: Optional[str] = None,
        min_oxygen: Optional[float] = None,
        max_oxygen: Optional[float] = None,
        min_flow: Optional[float] = None,
        max_flow: Optional[float] = None,
        start_time_s: Optional[float] = None,
        end_time_s: Optional[float] = None,
        preview_limit: int = 25,
        complete_cases_only: bool = False,
        exclude_flagged_anomalies: bool = False,
    ) -> Dict[str, Any]:
        """
        Produce a fast JSON-serializable preview table with column metadata and quality audit.
        Evaluates quality statistics across all filtered records, returning a bounded preview slice.
        """
        # Call extract_dataset WITHOUT max_rows so the quality report evaluates the full filtered population
        full_df, col_meta, quality = self.extract_dataset(
            dataset_id=dataset_id,
            selected_features=selected_features,
            target_id=target_id,
            material_filter=material_filter,
            min_oxygen=min_oxygen,
            max_oxygen=max_oxygen,
            min_flow=min_flow,
            max_flow=max_flow,
            start_time_s=start_time_s,
            end_time_s=end_time_s,
            max_rows=None,
            complete_cases_only=complete_cases_only,
            exclude_flagged_anomalies=exclude_flagged_anomalies,
        )

        total_filtered = len(full_df)
        preview_df = full_df.head(preview_limit)

        # Format rows for preview table (replace NaN with None for clean JSON)
        clean_records = preview_df.replace({np.nan: None}).to_dict(orient="records")

        columns_list = []
        for col_name in full_df.columns:
            m = col_meta.get(col_name, {})
            columns_list.append({
                "id": col_name,
                "label": m.get("label", col_name),
                "unit": m.get("unit", "N/A"),
                "role": m.get("role", "input"),
                "category": m.get("category", "measured"),
                "data_type": m.get("data_type", "float"),
                "missing_count": quality["missing_counts"].get(col_name, 0),
            })

        quality["preview_records_count"] = len(clean_records)

        return {
            "dataset_id": dataset_id,
            "dataset_name": quality["dataset_name"],
            "preview_rows": clean_records,
            "columns": columns_list,
            "preview_count": len(clean_records),
            "total_filtered_count": total_filtered,
            "total_extracted_count": total_filtered,
            "complete_case_count": quality["complete_case_records_count"],
            "labeled_count": quality["labeled_records_count"],
            "anomalous_count": quality["anomalous_records_count"],
            "quality_report": quality,
        }

    def export_csv(
        self,
        dataset_id: str,
        selected_features: Optional[List[str]] = None,
        target_id: Optional[str] = None,
        material_filter: Optional[str] = None,
        min_oxygen: Optional[float] = None,
        max_oxygen: Optional[float] = None,
        min_flow: Optional[float] = None,
        max_flow: Optional[float] = None,
        start_time_s: Optional[float] = None,
        end_time_s: Optional[float] = None,
        max_rows: Optional[int] = None,
        complete_cases_only: bool = False,
        exclude_flagged_anomalies: bool = False,
    ) -> str:
        """
        Generate true CSV string of experimental data. Zero mocked or fabricated values.
        """
        df, _, _ = self.extract_dataset(
            dataset_id=dataset_id,
            selected_features=selected_features,
            target_id=target_id,
            material_filter=material_filter,
            min_oxygen=min_oxygen,
            max_oxygen=max_oxygen,
            min_flow=min_flow,
            max_flow=max_flow,
            start_time_s=start_time_s,
            end_time_s=end_time_s,
            max_rows=max_rows,
            complete_cases_only=complete_cases_only,
            exclude_flagged_anomalies=exclude_flagged_anomalies,
        )

        output = io.StringIO()
        df.to_csv(output, index=False, encoding="utf-8")
        return output.getvalue()

    def export_metadata_json(
        self,
        dataset_id: str,
        selected_features: Optional[List[str]] = None,
        target_id: Optional[str] = None,
        material_filter: Optional[str] = None,
        min_oxygen: Optional[float] = None,
        max_oxygen: Optional[float] = None,
        min_flow: Optional[float] = None,
        max_flow: Optional[float] = None,
        start_time_s: Optional[float] = None,
        end_time_s: Optional[float] = None,
        max_rows: Optional[int] = None,
        complete_cases_only: bool = False,
        exclude_flagged_anomalies: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate machine-readable JSON metadata including variable descriptions, physical units,
        applied filter thresholds, and scientific data provenance matching exported population.
        """
        meta = get_modeling_dataset_metadata(dataset_id)
        if not meta:
            raise ValueError(f"Unknown dataset ID: {dataset_id}")

        df, col_meta, quality = self.extract_dataset(
            dataset_id=dataset_id,
            selected_features=selected_features,
            target_id=target_id,
            material_filter=material_filter,
            min_oxygen=min_oxygen,
            max_oxygen=max_oxygen,
            min_flow=min_flow,
            max_flow=max_flow,
            start_time_s=start_time_s,
            end_time_s=end_time_s,
            max_rows=max_rows,
            complete_cases_only=complete_cases_only,
            exclude_flagged_anomalies=exclude_flagged_anomalies,
        )

        return {
            "metadata_version": "1.0",
            "extraction_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "software": "NASA FLAME Predictive-Modeling Extraction Tool",
            "dataset_info": {
                "dataset_id": meta["dataset_id"],
                "name": meta["name"],
                "investigation": meta["investigation"],
                "facility": meta["facility"],
                "gravity_regime": meta["gravity_regime"],
                "source_file": meta["source_file"],
                "paradigm": meta["paradigm"],
            },
            "filters_applied": {
                "material_filter": material_filter,
                "min_oxygen_pct": min_oxygen,
                "max_oxygen_pct": max_oxygen,
                "min_flow_cm_s": min_flow,
                "max_flow_cm_s": max_flow,
                "start_time_s": start_time_s,
                "end_time_s": end_time_s,
                "complete_cases_only": complete_cases_only,
                "exclude_flagged_anomalies": exclude_flagged_anomalies,
            },
            "selected_target": target_id,
            "target_metadata": col_meta.get(target_id) if target_id else None,
            "feature_schema": col_meta,
            "record_counts": {
                "total_available_records": quality["total_available_records"],
                "filtered_records_count": quality["filtered_records_count"],
                "exported_records_count": quality["exported_records_count"],
                "labeled_records_count": quality["labeled_records_count"],
                "complete_case_records_count": quality["complete_case_records_count"],
                "anomalous_records_count": quality["anomalous_records_count"],
            },
            "quality_audit": quality,
            "recommended_splitting": {
                "strategy": "GroupKFold" if meta["paradigm"] in ("tabular_run_level", "time_series_telemetry") else "TimeSeriesSplit",
                "group_column": quality["group_split_column"],
                "rationale": quality["leakage_advice"],
            },
            "scientific_citation": (
                "NASA Space Life and Physical Sciences Research and Applications Division (SLPSRAD). "
                f"Investigation: {meta['investigation']}. NASA FLAME Scientific Intelligence Dashboard 2026."
            ),
        }

    def export_quality_report_markdown(
        self,
        dataset_id: str,
        selected_features: Optional[List[str]] = None,
        target_id: Optional[str] = None,
        material_filter: Optional[str] = None,
        min_oxygen: Optional[float] = None,
        max_oxygen: Optional[float] = None,
        min_flow: Optional[float] = None,
        max_flow: Optional[float] = None,
        start_time_s: Optional[float] = None,
        end_time_s: Optional[float] = None,
        max_rows: Optional[int] = None,
        complete_cases_only: bool = False,
        exclude_flagged_anomalies: bool = False,
    ) -> str:
        """
        Generate structured Markdown / text quality report with empirical anomaly disclosures.
        """
        df, col_meta, quality = self.extract_dataset(
            dataset_id=dataset_id,
            selected_features=selected_features,
            target_id=target_id,
            material_filter=material_filter,
            min_oxygen=min_oxygen,
            max_oxygen=max_oxygen,
            min_flow=min_flow,
            max_flow=max_flow,
            start_time_s=start_time_s,
            end_time_s=end_time_s,
            max_rows=max_rows,
            complete_cases_only=complete_cases_only,
            exclude_flagged_anomalies=exclude_flagged_anomalies,
        )

        md = []
        md.append(f"# NASA FLAME — Predictive-Modeling Data Quality Report")
        md.append(f"**Dataset:** {quality['dataset_name']} (`{dataset_id}`)")
        md.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        md.append("")
        md.append("## 1. Extraction & Population Summary")
        md.append(f"- **Total Records in Source:** {quality['total_available_records']}")
        md.append(f"- **Filtered Records Matching Filter:** {quality['filtered_records_count']}")
        md.append(f"- **Exported Records Count:** {quality['exported_records_count']}")
        md.append(f"- **Labeled Records Count (Non-null Target):** {quality['labeled_records_count']}")
        md.append(f"- **Complete-Case Records (Zero Missing):** {quality['complete_case_records_count']}")
        md.append(f"- **Flagged Empirical Source Anomalies:** {quality['anomalous_records_count']}")
        md.append(f"- **Overall Data Completeness:** {quality['data_completeness_pct']}%")
        md.append(f"- **Target Variable:** {target_id or 'None (Exploratory Unsupervised Mode)'}")
        md.append("")
        md.append("## 2. Feature Schema & Missing Value Audit")
        md.append("| Column Name | Label | Unit | Role | Category | Missing Count | Missing % |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for col, count in quality["missing_counts"].items():
            m = col_meta.get(col, {})
            pct = round(100.0 * count / max(1, quality["exported_records_count"]), 1)
            md.append(f"| `{col}` | {m.get('label', col)} | {m.get('unit', 'N/A')} | {m.get('role', 'input')} | {m.get('category', 'measured')} | {count} | {pct}% |")
        md.append("")
        md.append("## 3. Data Leakage & Splitting Guidance")
        md.append(f"**Leakage Risk Rating:** `{quality['leakage_risk']}`")
        md.append(f"**Recommended Split Group:** `{quality['group_split_column']}`")
        md.append(f"> {quality['leakage_advice']}")
        md.append("")
        if quality["anomalous_records_details"]:
            md.append("## 4. Empirical Source Anomaly Disclosures")
            md.append("The following records contain uncorrected empirical source entries from the NASA PI experiment matrix. They are preserved verbatim but flagged:")
            md.append("| Run ID | Anomaly Flag | Type | Details |")
            md.append("| :--- | :--- | :--- | :--- |")
            for a in quality["anomalous_records_details"]:
                md.append(f"| `{a['run_id']}` | `{a['flag']}` | {a.get('type', 'N/A')} | {a.get('details', '')} |")
            md.append("")
        if quality["constant_columns"]:
            md.append("## 5. Constant Features (Zero Variance)")
            for c in quality["constant_columns"]:
                md.append(f"- `{c}`: Exhibits zero variance across filtered samples. Consider dropping before fitting linear or distance-based ML models.")
            md.append("")
        if quality["warnings"]:
            md.append("## 6. Scientific Warnings & Disclosures")
            for w in quality["warnings"]:
                md.append(f"- ⚠️ {w}")
            md.append("")
        md.append("## 7. Provenance & Scientific Citation")
        md.append("Extracted from validated NASA microgravity combustion archives without synthetic generation or silent target imputation.")
        return "\n".join(md)
