"""
NASA FLAME — Predictive-Modeling Dataset Capability & Schema Registry
Provides standardized schemas for NASA microgravity combustion datasets:
- Distinguishes measured labels, derived features, contextual metadata, and uninstrumented parameters
- Encodes physical units, data types, and group-aware cross-validation identifiers
- Explicitly documents uninstrumented targets (e.g. flame spread rate in sensor logs)
- Provides documented source anomaly disclosures and target leakage safeguards
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# Registered datasets suitable for predictive modeling data extraction
MODELING_DATASETS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "bass_ii_experiments": {
        "dataset_id": "bass_ii_experiments",
        "name": "BASS-II Solid Fuel Microgravity Combustion Matrix",
        "investigation": "BASS-II",
        "facility": "ISS Microgravity Science Glovebox (MSG)",
        "paradigm": "tabular_run_level",
        "gravity_regime": "Microgravity (10⁻⁴ to 10⁻⁵ g)",
        "source_file": "processed_data/bass_ii_experiments.csv",
        "total_records": 129,
        "group_column": "run_id",
        "alternative_group_column": "Sample no.",
        "description": "Run-level experimental test matrix of 129 solid fuel burns conducted in the ISS Microgravity Science Glovebox. Records initial airflow velocity proxy, gas concentrations, fuel geometry, and frame counts.",
        "leakage_guidance": "For cross-validation, group samples by 'run_id' (Test no.) or 'Sample no.' using GroupKFold. Repeated burns on the same sample or fuel geometry must never be split randomly across training and validation folds.",
        "available_features": [
            {
                "id": "fuel_material",
                "label": "Fuel Material & Geometry",
                "source_col": "Material",
                "unit": "categorical",
                "data_type": "string",
                "role": "input",
                "category": "contextual_metadata",
                "description": "Fuel material composition and sample dimensions (e.g., 100 µm PMMA film, 200 µm PMMA film, cotton blend, Sibal cloth)."
            },
            {
                "id": "airflow_velocity_proxy",
                "label": "Initial Forced Airflow Proxy",
                "source_col": "Air display",
                "unit": "cm/s",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Initial forced airflow velocity proxy (cm/s) parsed from primary protocol setting (MSG duct flow: 0-50 cm/s). Dynamic multi-step flow protocols are preserved in raw_airflow_display."
            },
            {
                "id": "raw_airflow_display",
                "label": "Raw Airflow Display String",
                "source_col": "Air display",
                "unit": "protocol_text",
                "data_type": "string",
                "role": "metadata",
                "category": "contextual_metadata",
                "description": "Raw unparsed text string from NASA PI Excel matrix capturing complete multi-step airflow protocol (e.g. '5,4,3,2,1')."
            },
            {
                "id": "airflow_profile",
                "label": "Airflow Protocol Profile",
                "source_col": "derived",
                "unit": "category",
                "data_type": "string",
                "role": "metadata",
                "category": "contextual_metadata",
                "description": "Airflow protocol type: 'constant' for single-velocity runs or 'dynamic_multi_step' for astronaut stepped flow adjustments."
            },
            {
                "id": "flow_restrictor",
                "label": "Flow Restrictor Setting",
                "source_col": "Flow restrictor",
                "unit": "setting_id",
                "data_type": "integer",
                "role": "input",
                "category": "contextual_metadata",
                "description": "Orifice flow restrictor position (0, 1, or 2) governing duct velocity profile."
            },
            {
                "id": "fan_display",
                "label": "Initial Fan Speed Display",
                "source_col": "Fan display",
                "unit": "RPM_proxy",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Initial fan tachometer speed display or potentiometer setting governing ventilation."
            },
            {
                "id": "raw_fan_display",
                "label": "Raw Fan Display String",
                "source_col": "Fan display",
                "unit": "protocol_text",
                "data_type": "string",
                "role": "metadata",
                "category": "contextual_metadata",
                "description": "Raw unparsed fan display string from NASA Excel matrix (e.g. '68, 52, 47, 43, 42, 41')."
            },
            {
                "id": "radiometer_gain",
                "label": "Radiometer Electronic Gain",
                "source_col": "Radiometer gain   (1000, 250, 50, 10)",
                "unit": "gain_factor",
                "data_type": "float",
                "role": "input",
                "category": "contextual_metadata",
                "description": "Electronic amplifier gain setting (1000, 250, 50, 10) for radiometer sensor instrumentation."
            },
            {
                "id": "initial_oxygen_pct",
                "label": "Calibrated Initial O₂ Concentration",
                "source_col": "calibrated  initial O2 % by vol ",
                "unit": "% vol",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Calibrated initial oxygen volumetric concentration inside the MSG chamber prior to ignition."
            },
            {
                "id": "initial_co2_pct",
                "label": "Initial CO₂ Concentration",
                "source_col": "Initial CO2 % by vol",
                "unit": "% vol",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Initial ambient carbon dioxide volumetric concentration prior to sample ignition."
            },
            {
                "id": "initial_co_ppm",
                "label": "Initial CO Concentration",
                "source_col": "Initial CO (ppm)",
                "unit": "ppm",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Background carbon monoxide concentration in parts per million before burn initiation."
            },
            {
                "id": "total_frames_shot",
                "label": "Recorded Video Frames",
                "source_col": "total frames shot",
                "unit": "frames",
                "data_type": "integer",
                "role": "input",
                "category": "verified_measured",
                "description": "Total optical video camera frames captured during the burn duration."
            },
            {
                "id": "data_quality_flags",
                "label": "Data Quality & Anomaly Flags",
                "source_col": "derived",
                "unit": "flag_codes",
                "data_type": "string",
                "role": "metadata",
                "category": "contextual_metadata",
                "description": "Scientific anomaly flags (e.g. source O2 delta anomaly, dynamic multi-step airflow protocol, qualified reading)."
            }
        ],
        "supported_targets": [
            {
                "id": "oxygen_consumption_delta_pct",
                "label": "Oxygen Consumption Delta (ΔO₂)",
                "unit": "% vol",
                "data_type": "float",
                "target_type": "regression",
                "category": "validated_derived",
                "formula": "calibrated_initial_O2 - calibrated_final_O2",
                "description": "Net volumetric oxygen depletion resulting from solid fuel combustion inside the sealed glovebox. NOTE: 5 raw experimental runs (B2, P22a, P22b, T28a, T28b) contain verified source Excel anomalies producing extreme deltas (+20.6%, +20.2%, -19.1%, +19.8%, -19.7%); these are flagged in data_quality_flags.",
                "source_cols": ["calibrated  initial O2 % by vol ", "calibrated final O2 % by vol"]
            },
            {
                "id": "co2_generation_delta_pct",
                "label": "Carbon Dioxide Generation Delta (ΔCO₂)",
                "unit": "% vol",
                "data_type": "float",
                "target_type": "regression",
                "category": "validated_derived",
                "formula": "Final_CO2 - Initial_CO2",
                "description": "Net volumetric carbon dioxide generated by the combustion process.",
                "source_cols": ["Initial CO2 % by vol", "Final CO2 % by vol"]
            },
            {
                "id": "final_co_ppm",
                "label": "Measured Final CO Emission",
                "unit": "ppm",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "Final CO (ppm)",
                "description": "Measured carbon monoxide concentration in parts per million post-combustion.",
                "source_cols": ["Final CO (ppm)"]
            },
            {
                "id": "final_oxygen_pct",
                "label": "Measured Final O₂ Concentration",
                "unit": "% vol",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "calibrated final O2 % by vol",
                "description": "Calibrated oxygen concentration remaining in the chamber at extinction.",
                "source_cols": ["calibrated final O2 % by vol"]
            }
        ],
        "unsupported_targets": [
            {
                "id": "flame_spread_rate_cm_s",
                "label": "Flame Spread Rate",
                "unit": "cm/s",
                "reason": "Flame spread rates were calculated by external photogrammetry from video frames and are unrecorded in this instrumented test matrix table. Estimating spread rate from gas delta without optical tracking is scientifically unsupported. Use Oxygen Consumption Delta (ΔO₂) as an intensity proxy, or export the matrix for exploratory analysis."
            },
            {
                "id": "exact_extinction_time_s",
                "label": "Exact Extinction Time",
                "unit": "s",
                "reason": "Exact extinction time is not recorded as a distinct timestamp channel in this matrix; only total frames shot is recorded. Extinction identification requires validated optical frame analysis."
            }
        ]
    },
    "saffire_iii_sample_1": {
        "dataset_id": "saffire_iii_sample_1",
        "name": "Saffire-III Sample 1 (Sibal Cotton-Fiberglass Blend Telemetry)",
        "investigation": "Saffire-III",
        "facility": "Cygnus OA-7 Flow Duct (Microgravity)",
        "paradigm": "time_series_telemetry",
        "gravity_regime": "Microgravity (< 10⁻⁴ g)",
        "source_file": "processed_data/saffire/saffire_iii_sample_1.csv",
        "total_records": 20909,
        "sampling_rate_hz": 30.3,
        "duration_s": 690.0,
        "fuel_material": "Cotton-Fiberglass blend (Sibal cloth, 0.4 m × 1.0 m)",
        "group_column": "source_file",
        "description": "Continuous 30.3 Hz sensor telemetry (20,909 records, 690 s) of a large-scale upward microgravity flame spread over cotton-fiberglass fabric inside the pressurized Cygnus cargo vehicle.",
        "leakage_guidance": "High autocorrelation risk! Do NOT split contiguous telemetry records randomly into train and test folds. Feature extraction must operate across bounded time windows (e.g. 5-second or 10-second blocks). When cross-validating, group by experimental burn run (e.g. Sample 1 vs Sample 2) rather than intra-run random sampling.",
        "available_features": [
            {
                "id": "elapsed_time_s",
                "label": "Elapsed Time",
                "source_col": "Elapsed Time (s)",
                "unit": "s",
                "data_type": "float",
                "role": "timestamp",
                "category": "verified_measured",
                "description": "Calibrated elapsed time since telemetry recording initiation at 30.3 Hz."
            },
            {
                "id": "flow_velocity_cm_s",
                "label": "Duct Flow Velocity (Anemometer 1)",
                "source_col": "Anemometer 1",
                "unit": "cm/s",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Calibrated forced airflow velocity inside the combustion flow tunnel."
            },
            {
                "id": "ambient_pressure_psia",
                "label": "Tunnel Ambient Pressure",
                "source_col": "Ambient Pressure",
                "unit": "psia",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Static chamber pressure measured inside the flow duct."
            },
            {
                "id": "oxygen_concentration_pct",
                "label": "Oxygen Concentration (O₂)",
                "source_col": "O2",
                "unit": "% vol",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Oxygen volumetric concentration measured by optical sensor in the flow channel."
            },
            {
                "id": "co2_concentration_pct",
                "label": "Carbon Dioxide (CO₂)",
                "source_col": "CO2",
                "unit": "% vol",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Carbon dioxide volumetric concentration measured in the flow channel."
            },
            {
                "id": "plume_temp_tc1",
                "label": "Plume Temperature TC1",
                "source_col": "Plume Temp 1 (TC1)",
                "unit": "°C",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Type K thermocouple reading in downstream exhaust plume (TC1)."
            },
            {
                "id": "plume_temp_tc2",
                "label": "Plume Temperature TC2",
                "source_col": "Plume Temp 2 (TC2)",
                "unit": "°C",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Type K thermocouple reading in downstream plume (TC2)."
            },
            {
                "id": "sample_temp_tc7",
                "label": "Sample Surface Temp TC7",
                "source_col": "Sample Temp 1 (TC7)",
                "unit": "°C",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Thermocouple placed directly on the fuel sample surface (TC7)."
            },
            {
                "id": "sample_temp_tc8",
                "label": "Sample Surface Temp TC8",
                "source_col": "Sample Temp 2 (TC8)",
                "unit": "°C",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Thermocouple placed on fuel sample surface downstream (TC8)."
            },
            {
                "id": "radiometer_1",
                "label": "Radiometer 1 Radiant Heat Flux",
                "source_col": "Radiometer 1",
                "unit": "mW/cm²",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Calibrated broadband radiant heat flux from the flame to the tunnel wall."
            },
            {
                "id": "fan_speed_rpm",
                "label": "Average Fan Speed",
                "source_col": "Average Fan Speed",
                "unit": "RPM",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Average rotational speed of the ducted fan creating forced convective flow."
            }
        ],
        "supported_targets": [
            {
                "id": "event_peak_plume_temperature_c",
                "label": "Event Peak Plume Temperature (Max TC1-TC6)",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "validated_derived",
                "formula": "max(Plume Temp 1..6 over burn)",
                "description": "True maximum gas temperature reached in the combustion plume across the full burn event. Verified at 95.64 °C (recorded by TC3 at t=109.8s). To prevent target leakage, features must be restricted to pre-ignition or early-burn observations.",
                "source_cols": ["Plume Temp 1 (TC1)", "Plume Temp 2 (TC2)", "Plume Temp 3 (TC3)", "Plume Temp 4 (TC4)", "Plume Temp 5 (TC5)", "Plume Temp 6 (TC6)"]
            },
            {
                "id": "instantaneous_plume_temp_tc1_c",
                "label": "Instantaneous Plume Temperature TC1",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "Plume Temp 1 (TC1) at time t",
                "description": "Instantaneous exhaust gas temperature measured by thermocouple TC1 at elapsed time step t. Used for dynamic state modeling from concurrent flow and pressure.",
                "source_cols": ["Plume Temp 1 (TC1)"]
            },
            {
                "id": "peak_plume_temperature_c",
                "label": "Peak Plume Temperature (Alias to Event Peak)",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "validated_derived",
                "formula": "max(Plume Temp 1..6 over burn)",
                "description": "Backward-compatible alias mapping to event_peak_plume_temperature_c (95.64 °C for Sample 1).",
                "source_cols": ["Plume Temp 1 (TC1)", "Plume Temp 2 (TC2)", "Plume Temp 3 (TC3)"]
            },
            {
                "id": "peak_radiant_heat_flux_mw_cm2",
                "label": "Event Peak Radiant Heat Flux",
                "unit": "mW/cm²",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "max(Radiometer 1..4)",
                "description": "Maximum radiant thermal emission detected by wall-mounted radiometers during combustion.",
                "source_cols": ["Radiometer 1", "Radiometer 2"]
            }
        ],
        "unsupported_targets": [
            {
                "id": "flame_spread_rate_cm_s",
                "label": "Flame Spread Rate",
                "unit": "cm/s",
                "reason": "Flame spread rate is uninstrumented in continuous sensor telemetry. Saffire sensor logs capture thermal and heat flux time-series at discrete points. Determining flame spread rate requires video optical pyrometry and flame-front edge tracking. Do not infer spread rate from thermocouple slopes without optical validation."
            },
            {
                "id": "exact_extinction_time_s",
                "label": "Exact Extinction Time",
                "unit": "s",
                "reason": "Thermocouple decay slopes indicate thermal cooling, but exact flame extinction requires optical verification of luminous flame absence. Telemetry alone is insufficient for definitive extinction labeling."
            }
        ]
    },
    "saffire_iii_sample_2": {
        "dataset_id": "saffire_iii_sample_2",
        "name": "Saffire-III Sample 2 (PMMA / Nomex Blend Telemetry)",
        "investigation": "Saffire-III",
        "facility": "Cygnus OA-7 Flow Duct (Microgravity)",
        "paradigm": "time_series_telemetry",
        "gravity_regime": "Microgravity (< 10⁻⁴ g)",
        "source_file": "processed_data/saffire/saffire_iii_sample_2.csv",
        "total_records": 4848,
        "sampling_rate_hz": 30.3,
        "duration_s": 160.0,
        "fuel_material": "PMMA / Nomex fabric blend",
        "group_column": "source_file",
        "description": "Continuous 30.3 Hz sensor telemetry (4,848 records, 160 s) from Saffire-III Sample 2 investigating thick PMMA / Nomex combustion dynamics under microgravity forced airflow.",
        "leakage_guidance": "High autocorrelation risk! Use bounded time windows. For multi-experiment modeling, group cross-validation by sample burn (Sample 1 vs Sample 2) to test generalization across distinct fuel materials.",
        "available_features": [
            {
                "id": "elapsed_time_s",
                "label": "Elapsed Time",
                "source_col": "Elapsed Time (s)",
                "unit": "s",
                "data_type": "float",
                "role": "timestamp",
                "category": "verified_measured",
                "description": "Calibrated elapsed time at 30.3 Hz."
            },
            {
                "id": "flow_velocity_cm_s",
                "label": "Duct Flow Velocity (Anemometer 1)",
                "source_col": "Anemometer 1",
                "unit": "cm/s",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Calibrated airflow velocity in flow duct."
            },
            {
                "id": "ambient_pressure_psia",
                "label": "Tunnel Ambient Pressure",
                "source_col": "Ambient Pressure",
                "unit": "psia",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Static chamber pressure."
            },
            {
                "id": "oxygen_concentration_pct",
                "label": "Oxygen Concentration (O₂)",
                "source_col": "O2",
                "unit": "% vol",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Volumetric oxygen concentration."
            },
            {
                "id": "plume_temp_tc1",
                "label": "Plume Temperature TC1",
                "source_col": "Plume Temp 1 (TC1)",
                "unit": "°C",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Exhaust plume thermocouple 1."
            },
            {
                "id": "radiometer_1",
                "label": "Radiometer 1 Radiant Heat Flux",
                "source_col": "Radiometer 1",
                "unit": "mW/cm²",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Broadband radiant heat flux."
            }
        ],
        "supported_targets": [
            {
                "id": "event_peak_plume_temperature_c",
                "label": "Event Peak Plume Temperature (Max TC1-TC6)",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "validated_derived",
                "formula": "max(Plume Temp 1..6 over burn)",
                "description": "Maximum exhaust gas temperature measured during the 160 s burn (verified at 48.35 °C on TC3 at t=159.9s).",
                "source_cols": ["Plume Temp 1 (TC1)", "Plume Temp 2 (TC2)", "Plume Temp 3 (TC3)"]
            },
            {
                "id": "instantaneous_plume_temp_tc1_c",
                "label": "Instantaneous Plume Temperature TC1",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "Plume Temp 1 (TC1) at time t",
                "description": "Instantaneous TC1 thermocouple reading at time t.",
                "source_cols": ["Plume Temp 1 (TC1)"]
            },
            {
                "id": "peak_plume_temperature_c",
                "label": "Peak Plume Temperature (Alias to Event Peak)",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "validated_derived",
                "formula": "max(Plume Temp 1..6 over burn)",
                "description": "Alias mapping to event_peak_plume_temperature_c (48.35 °C for Sample 2).",
                "source_cols": ["Plume Temp 1 (TC1)"]
            },
            {
                "id": "peak_radiant_heat_flux_mw_cm2",
                "label": "Event Peak Radiant Heat Flux",
                "unit": "mW/cm²",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "max(Radiometer 1..4)",
                "description": "Maximum radiant flux measured during Sample 2 combustion.",
                "source_cols": ["Radiometer 1"]
            }
        ],
        "unsupported_targets": [
            {
                "id": "flame_spread_rate_cm_s",
                "label": "Flame Spread Rate",
                "unit": "cm/s",
                "reason": "Flame spread rate is uninstrumented in sensor telemetry. External camera photogrammetry is required."
            }
        ]
    },
    "saffire_sample_5": {
        "dataset_id": "saffire_sample_5",
        "name": "Saffire-I Sample 5 Telemetry",
        "investigation": "Saffire-I",
        "facility": "Cygnus OA-6 Flow Duct",
        "paradigm": "time_series_telemetry",
        "gravity_regime": "Microgravity (< 10⁻⁴ g)",
        "source_file": "processed_data/saffire/saffire_sample_5.csv",
        "total_records": 11363,
        "sampling_rate_hz": 30.3,
        "duration_s": 375.0,
        "group_column": "source_file",
        "description": "30.3 Hz continuous telemetry record (11,363 records) for Saffire-I Sample 5 combustion experiment.",
        "leakage_guidance": "High autocorrelation risk! Group cross-validation by sample burn.",
        "available_features": [
            {
                "id": "elapsed_time_s",
                "label": "Elapsed Time",
                "source_col": "Elapsed Time (s)",
                "unit": "s",
                "data_type": "float",
                "role": "timestamp",
                "category": "verified_measured",
                "description": "Elapsed time at 30.3 Hz."
            },
            {
                "id": "plume_temp_tc1",
                "label": "Plume Temp TC1",
                "source_col": "Plume Temp 1 (TC1)",
                "unit": "°C",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Plume thermocouple reading."
            },
            {
                "id": "radiometer_1",
                "label": "Radiometer 1 Heat Flux",
                "source_col": "Radiometer 1",
                "unit": "mW/cm²",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Radiometer heat flux reading."
            }
        ],
        "supported_targets": [
            {
                "id": "event_peak_plume_temperature_c",
                "label": "Event Peak Plume Temperature",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "validated_derived",
                "formula": "max(Plume Temp 1..6 over burn)",
                "description": "Peak plume temperature reached during burn.",
                "source_cols": ["Plume Temp 1 (TC1)"]
            },
            {
                "id": "instantaneous_plume_temp_tc1_c",
                "label": "Instantaneous Plume Temperature TC1",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "Plume Temp 1 (TC1) at time t",
                "description": "Instantaneous TC1 reading at time t.",
                "source_cols": ["Plume Temp 1 (TC1)"]
            },
            {
                "id": "peak_plume_temperature_c",
                "label": "Peak Plume Temperature (Alias)",
                "unit": "°C",
                "data_type": "float",
                "target_type": "regression",
                "category": "validated_derived",
                "formula": "max(Plume Temp 1..6 over burn)",
                "description": "Alias mapping to event_peak_plume_temperature_c.",
                "source_cols": ["Plume Temp 1 (TC1)"]
            }
        ],
        "unsupported_targets": [
            {
                "id": "flame_spread_rate_cm_s",
                "label": "Flame Spread Rate",
                "unit": "cm/s",
                "reason": "Uninstrumented in sensor telemetry."
            }
        ]
    },
    "telemetry_cygnus_data": {
        "dataset_id": "telemetry_cygnus_data",
        "name": "Cygnus Spacecraft Environment Telemetry",
        "investigation": "Saffire Ground & Flight Telemetry",
        "facility": "Cygnus Pressurized Cargo Module (PCM)",
        "paradigm": "vehicle_telemetry",
        "gravity_regime": "Microgravity (< 10⁻⁴ g)",
        "source_file": "processed_data/saffire/telemetry/analysis_ready/cygnus_data_analysis.csv",
        "total_records": 3844,
        "sampling_rate_hz": 0.4,
        "group_column": "source_file",
        "description": "0.4 Hz environmental telemetry of the Cygnus spacecraft cabin: cabin pressure, cabin air temperature, and smoke detector obscuration / scatterometer readings (FIZ 1 / FIZ 2).",
        "leakage_guidance": "Time-ordered cross-validation (TimeSeriesSplit) recommended due to monotonic vehicle pressure trends.",
        "available_features": [
            {
                "id": "relative_time_s",
                "label": "Relative Time",
                "source_col": "Relative Time (s)",
                "unit": "s",
                "data_type": "float",
                "role": "timestamp",
                "category": "verified_measured",
                "description": "Relative elapsed mission time in seconds."
            },
            {
                "id": "cabin_air_temp_c",
                "label": "PCM Cabin Air Temperature",
                "source_col": "PCM Air Temp (degC)",
                "unit": "°C",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Internal air temperature of the Cygnus Pressurized Cargo Module."
            },
            {
                "id": "cabin_pressure_psi",
                "label": "PCM Cabin Pressure",
                "source_col": "PCM Press EPS 1 (psi)",
                "unit": "psi",
                "data_type": "float",
                "role": "input",
                "category": "verified_measured",
                "description": "Internal static atmospheric pressure of the spacecraft cabin."
            }
        ],
        "supported_targets": [
            {
                "id": "smoke_detector_obscuration_fiz1_v",
                "label": "FIZ 1 Smoke Detector Obscuration Voltage",
                "unit": "V",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "FIZ1 Smoke Detector Obscuration  (V)",
                "description": "Photodiode obscuration voltage signal from FIZ 1 smoke detector.",
                "source_cols": ["FIZ1 Smoke Detector Obscuration  (V)"]
            },
            {
                "id": "smoke_detector_scatterometer_fiz1_v",
                "label": "FIZ 1 Scatterometer Signal",
                "unit": "V",
                "data_type": "float",
                "target_type": "regression",
                "category": "verified_measured",
                "formula": "FIZ 1 Smoke Detector Scatterometer (V)",
                "description": "Forward optical scattering sensor response in FIZ 1 detector.",
                "source_cols": ["FIZ 1 Smoke Detector Scatterometer (V)"]
            }
        ],
        "unsupported_targets": [
            {
                "id": "flame_spread_rate_cm_s",
                "label": "Flame Spread Rate",
                "unit": "cm/s",
                "reason": "Cygnus telemetry records vehicle cabin life support and detector signals, not combustion flame-front propagation."
            }
        ]
    }
}


def get_modeling_dataset_metadata(dataset_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full capability registry entry for a dataset ID."""
    return MODELING_DATASETS_REGISTRY.get(dataset_id)


def list_available_datasets() -> List[Dict[str, Any]]:
    """List summary cards of all registered modeling datasets."""
    summaries = []
    for ds_id, ds in MODELING_DATASETS_REGISTRY.items():
        summaries.append({
            "dataset_id": ds["dataset_id"],
            "name": ds["name"],
            "investigation": ds["investigation"],
            "facility": ds.get("facility") or ds.get("vehicle"),
            "paradigm": ds["paradigm"],
            "gravity_regime": ds["gravity_regime"],
            "total_records": ds["total_records"],
            "feature_count": len(ds["available_features"]),
            "target_count": len(ds["supported_targets"]),
            "unsupported_target_count": len(ds["unsupported_targets"]),
            "description": ds["description"],
            "group_column": ds["group_column"],
        })
    return summaries
