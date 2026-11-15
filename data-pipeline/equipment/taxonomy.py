"""
NASA FLAME — Spacecraft Fire-Safety Equipment Research Taxonomy & Knowledge Models
Strictly separates locally indexed NASA flight datasets from external NASA research context.

Locally Indexed NASA Flight Datasets in FLAME:
- Saffire-I, II, III flight telemetry (saffire_iii_sample_1, saffire_iii_sample_2, etc.)
- BASS-II glovebox solid combustion test matrix (bass_ii_experiments: 129 runs)
- Cygnus operational Pressurized Cargo Module (PCM) environmental telemetry (telemetry_cygnus_data, cygnus_smoke_detector_data)

External NASA Research Context (Unindexed in FLAME):
- SAME (Smoke Aerosol Measurement Experiment, ISS MSG) — aerosol agglomeration literature reference
- FLEX (Flame Extinguishment Experiment, ISS CIR) — droplet burning & inert gas dilution literature reference
"""

from typing import Dict, Any, List

FIRE_SAFETY_CATEGORIES = [
    {
        "id": "detection",
        "title": "Fire Detection & Early Warning",
        "icon": "Search",
        "short_desc": "Smoke obscuration, aerosol scattering, thermal plume sensing, and ventilation sensor placement.",
        "scientific_scope": (
            "Investigates microgravity smoke transport, absence of thermal buoyancy, aerosol optical scattering, "
            "radiometer heat-flux thresholds, and early multi-channel combustion signatures inside spacecraft ventilation."
        ),
        "primary_investigations": ["Cygnus Vehicle Telemetry", "Saffire-III"],
        "external_research_context": ["SAME (External NASA ISS Experiment, unindexed in FLAME)"],
        "key_parameters": [
            "smoke_obscuration",
            "scatterometer_voltage",
            "plume_temperature",
            "radiant_heat_flux",
            "duct_airflow_velocity",
            "cabin_pressure",
        ],
        "distinction_note": (
            "CRITICAL DISTINCTION: Telemetry logs record combustion environmental conditions and raw vehicle photodiode "
            "voltages during flight burns. They do not constitute standardized factory detector sensitivity calibration curves."
        ),
    },
    {
        "id": "prevention",
        "title": "Fire Prevention & Material Flammability",
        "icon": "Shield",
        "short_desc": "Combustible materials, limiting oxygen index, forced airflow velocity, and ignition thresholds.",
        "scientific_scope": (
            "Examines solid fuel combustion (PMMA, Cotton Sibal, Nomex) across atmospheric oxygen regimes (15% to 22.2% vol indexed) "
            "and ventilation speeds (0 to 49 cm/s). Identifies non-buoyant flammability boundaries and ignition limits."
        ),
        "primary_investigations": ["BASS-II", "Saffire-III"],
        "external_research_context": [],
        "key_parameters": [
            "fuel_material",
            "oxygen_concentration",
            "airflow_velocity_proxy",
            "flow_restrictor",
            "co2_concentration",
            "total_frames_shot",
        ],
        "distinction_note": (
            "SAFETY DISCLOSURE: Microgravity combustion test observations provide scientific behavioral data but do NOT "
            "constitute formal NASA-STD-6001 material safety certifications or flight qualification approvals."
        ),
    },
    {
        "id": "suppression",
        "title": "Fire Suppression & Extinction Dynamics",
        "icon": "Flame",
        "short_desc": "Flame extinction limits, low-flow quiescent quenching, blow-off limits, and gaseous suppression physics.",
        "scientific_scope": (
            "Analyzes empirical flame extinction events under low-flow starvation (<1-2 cm/s), high-flow blow-off (>28-38 cm/s), "
            "oxygen depletion, and vacuum depressurization. Identifies suppression research gaps in microgravity."
        ),
        "primary_investigations": ["BASS-II", "Saffire-III"],
        "external_research_context": ["FLEX (External NASA ISS CIR Experiment, unindexed in FLAME)"],
        "key_parameters": [
            "extinction_airflow_limit",
            "oxygen_consumption_delta",
            "quiescent_starvation",
            "blowoff_velocity",
        ],
        "distinction_note": (
            "RESEARCH DISCLOSURE: Saffire and BASS-II evaluated spontaneous or flow-induced flame extinction. "
            "Active extinguisher discharge agents (fine water mist, gaseous halon alternatives) were not tested in these flight runs."
        ),
    },
]

VERIFIED_INVESTIGATIONS_REGISTRY = {
    "saffire_iii": {
        "id": "saffire_iii",
        "name": "Spacecraft Fire Safety Experiment III (Saffire-III)",
        "facility": "Cygnus Unmanned Cargo Vehicle (OA-5/OA-7)",
        "gravity_regime": "Microgravity (10⁻⁴ to 10⁻⁵ g)",
        "primary_focus": "Large-scale fabric and solid combustion in controlled flow duct",
        "is_locally_indexed": True,
        "flight_datasets": ["saffire_iii_sample_1", "saffire_iii_sample_2"],
        "relevance": {
            "detection": "Continuous 30.3 Hz telemetry for broadband radiant heat flux and 6-thermocouple plume exhaust array.",
            "prevention": "Thick Sibal fabric burns under controlled 23 cm/s ventilation, 14.46 psia pressure, and nominal O₂.",
            "suppression": "Flame propagation under forced air; post-burn thermal decay tracking without active suppressants.",
        },
        "verified_sensor_channels": [
            {
                "id": "radiometer_1",
                "label": "Broadband Radiant Heat Flux (Radiometer 1)",
                "unit": "mW/cm²",
                "role": "detection",
                "source_dataset": "saffire_iii_sample_1.csv",
                "measured_range": "-19.33 to 150.39 mW/cm² (Sample 1 peak 150.39 mW/cm² at t=197.7s)",
                "description": "Measures total radiant thermal emission from flame zone to flow tunnel wall.",
            },
            {
                "id": "plume_temp_tc1_to_tc6",
                "label": "Exhaust Thermocouple Plume Array (TC1-TC6)",
                "unit": "°C",
                "role": "detection",
                "source_dataset": "saffire_iii_sample_1.csv",
                "measured_range": "Ambient ~22°C to 95.64°C (Sample 1 peak on TC3 at t=109.8s; TC1 peak 63.31°C)",
                "description": "Six-channel thermocouple rake monitoring downstream convective exhaust thermal plume.",
            },
            {
                "id": "flow_velocity_cm_s",
                "label": "Tunnel Ventilation Airflow Velocity (Anemometer 1)",
                "unit": "cm/s",
                "role": "prevention_suppression",
                "source_dataset": "saffire_iii_sample_1.csv",
                "measured_range": "0.14 to 24.95 cm/s (mean 23.00 cm/s on Anemometer 1)",
                "description": "Calibrated duct airflow velocity driving forced convective microgravity combustion.",
            },
            {
                "id": "ambient_pressure_psia",
                "label": "Duct Ambient Pressure",
                "unit": "psia",
                "role": "prevention",
                "source_dataset": "saffire_iii_sample_1.csv",
                "measured_range": "14.40 to 14.50 psia (~99.7 kPa nominal atmospheric pressure)",
                "description": "Operating chamber pressure inside Cygnus pressurized cargo module during test.",
            },
            {
                "id": "sample_temp_tc7_to_tc12",
                "label": "Sample Surface Thermocouples (TC7-TC12)",
                "unit": "°C",
                "role": "prevention",
                "source_dataset": "saffire_iii_sample_1.csv",
                "measured_range": "Ambient ~7°C up to 1088.21°C (Sample 1 peak on TC11 at t=307.2s; TC9 peak 1059.96°C)",
                "description": "Direct contact thermocouples recording fuel surface pyrolysis and flame temperatures.",
            },
        ],
    },
    "bass_ii": {
        "id": "bass_ii",
        "name": "Burning and Suppression of Solids - II (BASS-II)",
        "facility": "ISS Microgravity Science Glovebox (MSG)",
        "gravity_regime": "Microgravity (10⁻⁴ to 10⁻⁵ g)",
        "primary_focus": "Solid fuel flammability, ignition thresholds, and low-flow extinction limits",
        "is_locally_indexed": True,
        "flight_datasets": ["bass_ii_experiments"],
        "relevance": {
            "detection": "Toxic gas post-burn emissions: Carbon Monoxide (CO ppm) from 0.3 to 950.0 ppm across 129 runs.",
            "prevention": "129 runs across PMMA, Cotton Sibal, and Nomex across 15.8% to 22.2% initial calibrated O₂.",
            "suppression": "Extinction boundary cataloging: quiescent flame extinction (<1-2 cm/s) and blow-off extinction (>28-38 cm/s).",
        },
        "verified_sensor_channels": [
            {
                "id": "airflow_velocity_proxy",
                "label": "Initial Forced Airflow Display Proxy",
                "unit": "cm/s",
                "role": "prevention_suppression",
                "source_dataset": "bass_ii_experiments.csv",
                "measured_range": "0.0 to 49.0 cm/s display proxy",
                "description": "Astronaut-controlled flow velocity inside MSG flow duct to evaluate flame stabilization and blowoff.",
            },
            {
                "id": "initial_oxygen_pct",
                "label": "Calibrated Initial Oxygen Concentration",
                "unit": "% vol",
                "role": "prevention",
                "source_dataset": "bass_ii_experiments.csv",
                "measured_range": "15.8% to 22.2% vol",
                "description": "Glovebox chamber oxygen concentration prior to ignition spark.",
            },
            {
                "id": "final_co_ppm",
                "label": "Final Carbon Monoxide Post-Burn Emission",
                "unit": "ppm",
                "role": "detection",
                "source_dataset": "bass_ii_experiments.csv",
                "measured_range": "0.3 to 950.0 ppm (Sibal fabric: 2-190 ppm; thick PMMA: up to 950 ppm)",
                "description": "Electrochemical sensor reading of toxic CO combustion products inside glovebox volume.",
            },
            {
                "id": "oxygen_consumption_delta_pct",
                "label": "Oxygen Depletion (ΔO₂)",
                "unit": "% vol",
                "role": "suppression",
                "source_dataset": "bass_ii_experiments.csv",
                "measured_range": "0.0% to 3.2% vol (valid runs; 5 instrument-reset outliers in raw logs excluded)",
                "description": "Calculated oxygen consumption reflecting fuel mass consumed before flame extinction.",
            },
        ],
    },
    "cygnus_vehicle_telemetry": {
        "id": "cygnus_vehicle_telemetry",
        "name": "Cygnus Spacecraft Environmental & Smoke Detector Telemetry",
        "facility": "Orbital ATK / Northrop Grumman Cygnus Pressurized Cargo Module",
        "gravity_regime": "Microgravity (10⁻⁴ to 10⁻⁵ g)",
        "primary_focus": "Operational vehicle smoke detector scatterometer response and cabin ventilation",
        "is_locally_indexed": True,
        "flight_datasets": ["telemetry_cygnus_data", "cygnus_smoke_detector_data"],
        "relevance": {
            "detection": "Direct scatterometer voltage from flight smoke detector FIZ 2 (0.000 to 1.805 V) and photodiode obscuration channel.",
            "prevention": "Cabin pressure monitoring (PCM Press 1-3) and thermal atmospheric stability.",
            "suppression": "Cabin fan differential pressure monitoring (FIZ 1 & 2 Cabin Fan ΔP).",
        },
        "verified_sensor_channels": [
            {
                "id": "smoke_detector_scatterometer_fiz2_v",
                "label": "FIZ 2 Smoke Detector Scatterometer Voltage",
                "unit": "V",
                "role": "detection",
                "source_dataset": "cygnus_smoke_detector_data.csv",
                "measured_range": "0.000 to 1.805 V (3,845 records, 130 elevated scatter > 0.05 V)",
                "description": "Optical light-scattering detector measuring aerosol particulate backscatter in Cygnus module.",
            },
            {
                "id": "smoke_detector_obscuration_fiz2_v",
                "label": "FIZ 2 Smoke Detector Obscuration Voltage",
                "unit": "V",
                "role": "detection",
                "source_dataset": "cygnus_smoke_detector_data.csv",
                "measured_range": "-4.235 to 3.835 V (raw photodiode voltage, baseline 0.000 V)",
                "description": "Photodiode obscuration channel monitoring smoke particulate attenuation in vehicle cargo bay.",
            },
            {
                "id": "smoke_detector_obscuration_fiz1_v",
                "label": "FIZ 1 Smoke Detector Obscuration Voltage",
                "unit": "V",
                "role": "detection",
                "source_dataset": "cygnus_data.csv",
                "measured_range": "0.000 V (inactive/uncalibrated in flight telemetry archive)",
                "description": "Redundant vehicle photodiode channel recorded as inactive zero baseline.",
            },
            {
                "id": "pcm_air_temp_c",
                "label": "Pressurized Cargo Module (PCM) Bulk Air Temp",
                "unit": "°C",
                "role": "detection",
                "source_dataset": "cygnus_data.csv",
                "measured_range": "0.00 to 20.70 °C",
                "description": "Operational ambient vehicle atmosphere temperature monitoring.",
            },
            {
                "id": "cabin_fan_delta_p_pa",
                "label": "Cabin Ventilation Fan Differential Pressure",
                "unit": "Pa",
                "role": "detection_ventilation",
                "source_dataset": "cygnus_data.csv",
                "measured_range": "-126.38 to +106.30 Pa on FIZ 2 Cabin Fan ΔP",
                "description": "Monitors forced ventilation circulation maintaining air movement through smoke sensor heads.",
            },
        ],
    },
    "same": {
        "id": "same",
        "name": "Smoke Aerosol Measurement Experiment (SAME / SAME-R)",
        "facility": "ISS Microgravity Science Glovebox (MSG)",
        "gravity_regime": "Microgravity (10⁻⁴ to 10⁻⁵ g)",
        "primary_focus": "Particulate size distribution and agglomeration physics of microgravity smoke",
        "is_locally_indexed": False,
        "flight_datasets": [],
        "external_reference": "NASA TM-2009-215801 (Smoke Aerosol Measurement Experiment, ISS MSG)",
        "description": "External NASA ISS research providing aerosol particle size and morphology context; not indexed as local telemetry in FLAME.",
        "relevance": {
            "detection": "External literature reports that microgravity smoke particulates experience prolonged reaction zone residence, producing larger mean agglomerate diameters than 1g smoke.",
        },
        "verified_sensor_channels": [],
    },
    "flex": {
        "id": "flex",
        "name": "Flame Extinguishment Experiment (FLEX / FLEX-2)",
        "facility": "ISS Combustion Integrated Rack (CIR)",
        "gravity_regime": "Microgravity (10⁻⁴ to 10⁻⁵ g)",
        "primary_focus": "Isolated liquid droplet burning and suppressant gas dilution limits",
        "is_locally_indexed": False,
        "flight_datasets": [],
        "external_reference": "NASA / JAXA Combustion Integrated Rack records (Flame Extinguishment Experiment, ISS CIR)",
        "description": "External NASA ISS research on isolated droplet burning and inert gas dilution; not indexed as local telemetry in FLAME.",
        "relevance": {
            "suppression": "External literature reports radiative extinction and cool-flame persistence under N₂ and CO₂ inert gas dilution in spherical droplet flames.",
        },
        "verified_sensor_channels": [],
    },
}

QUICK_START_RESEARCH_TEMPLATES = [
    {
        "id": "tpl_smoke_detection",
        "category": "detection",
        "label": "Spacecraft Smoke Detection & Aerosol Transport",
        "query": "I want to design a more reliable spacecraft smoke detection system. Find relevant NASA experiments, available measurements, research limitations, and potential research directions.",
        "icon": "Search",
        "badge": "Detection",
    },
    {
        "id": "tpl_material_flammability",
        "category": "prevention",
        "label": "Material Flammability & Oxygen Limits",
        "query": "Investigate how microgravity forced airflow and elevated oxygen concentration influence solid fuel flammability, flame spread, and material fire safety.",
        "icon": "Shield",
        "badge": "Prevention",
    },
    {
        "id": "tpl_extinction_suppression",
        "category": "suppression",
        "label": "Flame Extinction & Quenching Dynamics",
        "query": "What experimental evidence exists on flame extinction in microgravity? Analyze low-flow starvation limits, blow-off velocity, and limitations in suppression research.",
        "icon": "Flame",
        "badge": "Suppression",
    },
    {
        "id": "tpl_multisensor_detection",
        "category": "detection",
        "label": "Multi-Sensor Fire Warning (Optical + Thermal + CO)",
        "query": "How can multi-sensor approaches combining optical obscuration, radiometer heat flux, and carbon monoxide sensing improve spacecraft fire alarm reliability?",
        "icon": "Layers",
        "badge": "Multi-Sensor",
    },
]
