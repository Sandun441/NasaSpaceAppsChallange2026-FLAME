"""
NASA FLAME — Earth Applications Evidence Catalog (Phase EA1.1 Audited)
Scientifically audited catalog linking NASA microgravity combustion findings to terrestrial applications.
Strictly separates:
  Dimension A: Experimental evidence verification (flight dataset / literature provenance)
  Dimension B: Terrestrial application validation (documented use, supported implication, exploratory hypothesis)

Zero fabricated measurements, probabilities, regulatory approvals, or numerical transfer predictions.
"""

from typing import List
from earth_applications.models import EarthApplicationEvidence

INITIAL_EARTH_APPLICATION_CATALOG: List[EarthApplicationEvidence] = [
    # 1. BASS-II: Material Flammability & Pyrolysis Modeling
    EarthApplicationEvidence(
        id="EA-EV-BASS-PYRO-01",
        category_id="material_flammability_fire_resistance",
        category_title="Material Flammability & Fire-Resistant Polymers",
        title="Buoyancy-Free Solid Polymer Pyrolysis & Flammability Benchmarking",
        description=(
            "Microgravity solid combustion data isolates pure chemical-kinetic pyrolysis properties "
            "from buoyant convective flows, providing baseline validation data for terrestrial polymer fire models."
        ),
        investigation_id="bass_ii",
        investigation_name="Burning and Suppression of Solids - II (BASS-II)",
        related_investigation_ids=[],
        source_type="flight_experiment_dataset",
        source_reference="https://psi.nasa.gov/physci/repo/data/investigations/PSI-25",
        supporting_excerpt=(
            "BASS-II examined solid fuel combustion across 129 test runs in the ISS Microgravity Science Glovebox (MSG), "
            "evaluating cast/extruded PMMA, cotton blends, and Nomex in controlled flow environments (0 to 49 cm/s display proxy) "
            "and calibrated initial oxygen concentrations (15.8% to 22.2% vol) without buoyant plume upward acceleration."
        ),
        dataset_or_measurement_reference="bass_ii_experiments.csv (129 runs; columns: Material, Air display, calibrated initial O2 % by vol)",
        scientific_finding=(
            "Solid flat fuels exhibit a narrow convective survival corridor: flame stabilization requires a minimum forced "
            "airflow (~1.5 cm/s) to avoid oxygen starvation, while excessive velocity (>28-38 cm/s) induces convective blowoff. "
            "Within this corridor, steady flame spread occurs without buoyant upward acceleration."
        ),
        proposed_terrestrial_relevance=(
            "Provides clean, non-buoyant burning rate and solid pyrolysis parameters for terrestrial fire researchers "
            "to validate numerical pyrolysis sub-models in computational fluid dynamics (CFD) codes such as NIST Fire Dynamics "
            "Simulator (FDS) and Pyropolis, isolating solid thermal degradation kinetics from buoyant flow artifacts."
        ),
        evidence_classification="supported_research_implication",
        validation_status="locally_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Locally verified against 129 flight runs in bass_ii_experiments.csv and NASA PSI-25 archive. "
            "Dimension B (Terrestrial Validation): Supported research implication for numerical pyrolysis modeling; does not constitute a terrestrial material flammability certification."
        ),
        earth_transfer_limitations=(
            "In terrestrial 1g environments, natural buoyant convection induces draft velocities of 1 to 2+ m/s around burning solids, "
            "overwhelming the low-velocity (<10 cm/s) stabilization regime observed in microgravity. Terrestrial materials testing "
            "(e.g., ASTM E1354 cone calorimetry, UL 94) is dominated by buoyant convective flows."
        ),
        gravity_buoyancy_ventilation_differences=(
            "In 1g, buoyant updrafts pull fresh oxygen into the fire base and accelerate hot effluent vertically. "
            "In microgravity, flow is driven entirely by mechanical ventilation; without forced flow, flames self-extinguish radiatively."
        ),
        uncertainty_notes=(
            "BASS-II samples were small-scale specimens (1-2 cm wide, 10-20 cm long). Extrapolating small-scale glovebox results "
            "to large-scale terrestrial polymer geometries requires intermediate-scale validation."
        ),
        provenance_status="locally_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 2. BASS-II: Low-Flow Suppression & Quenching Boundaries
    EarthApplicationEvidence(
        id="EA-EV-BASS-EXT-02",
        category_id="fire_suppression_research",
        category_title="Fire Suppression & Extinction Kinetics",
        title="Convective Velocity Extinction Boundaries (<1.5 cm/s & >28-38 cm/s) for Flame Stabilization",
        description=(
            "Empirical extinction thresholds in BASS-II isolate radiative cooling and convective blow-off limits, "
            "informing the fundamental physical boundaries for flame quenching in low-ventilation environments."
        ),
        investigation_id="bass_ii",
        investigation_name="Burning and Suppression of Solids - II (BASS-II)",
        related_investigation_ids=[],
        source_type="flight_experiment_dataset",
        source_reference="https://psi.nasa.gov/physci/repo/data/investigations/PSI-25",
        supporting_excerpt=(
            "Flame extinction was systematically recorded in BASS-II across 14 low-flow tests (B9, B11, B14, B21, B22, O2, O4, P1, "
            "P4, P9, P10, P13a, P22a, P25) where astronaut-adjusted flow velocity was reduced below 1.0 to 2.0 cm/s, "
            "causing radiative extinction without buoyant air replenishment. Blow-off extinction occurred at velocities exceeding 28 to 38 cm/s."
        ),
        dataset_or_measurement_reference="bass_ii_experiments.csv (Tests B9, B11, B14, B21, B22, O2, O4, B18, B19, O7, O8b; Final CO ppm: 0.3 to 950 ppm)",
        scientific_finding=(
            "When forced airflow velocity is reduced below critical thresholds (<1.5 cm/s), solid diffusion flames build an insulating "
            "blanket of CO₂ and H₂O combustion products that inhibits oxygen transport, driving the flame to radiative collapse. "
            "Conversely, increasing airflow above 28-38 cm/s drives convective blow-off extinction."
        ),
        proposed_terrestrial_relevance=(
            "Informs theoretical flame extinction criteria in fire protection engineering by establishing the fundamental non-buoyant "
            "radiative cooling and flow starvation thresholds required to collapse diffusion flames in confined low-ventilation compartments."
        ),
        evidence_classification="supported_research_implication",
        validation_status="locally_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Locally verified against 14 documented low-flow and 6 blow-off extinction runs in bass_ii_experiments.csv. "
            "Dimension B (Terrestrial Validation): Supported research implication for quenching kinetics; BASS-II evaluated flow starvation, not active chemical suppressants."
        ),
        earth_transfer_limitations=(
            "Terrestrial 1g fires generate persistent natural buoyant draft, preventing the quiescent suffocating blanket from forming "
            "unless the compartment is completely sealed. Gaseous suppressants on Earth must overcome buoyant draft velocities."
        ),
        gravity_buoyancy_ventilation_differences=(
            "Buoyancy continuously clears combustion products away from 1g flames. In microgravity, stagnant combustion products remain "
            "adjacent to the flame surface, creating an intrinsic radiative extinction envelope."
        ),
        uncertainty_notes=(
            "BASS-II evaluated spontaneous flow starvation, not active chemical suppression agent injection. "
            "Translating starvation limits to active chemical agent requirements requires kinetic mechanism modeling."
        ),
        provenance_status="locally_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 3. Saffire-III: HVAC & Ventilation Duct Conduit Fires
    EarthApplicationEvidence(
        id="EA-EV-SAFFIRE-DUCT-01",
        category_id="building_fire_safety",
        category_title="Building Fire Safety & Ventilation Ducts",
        title="Large-Scale Conduit Flame Spread & Thermal Hazard Modeling in Forced Ducts",
        description=(
            "Continuous 30.3 Hz sensor telemetry from Saffire large-scale flow duct burns informs fire propagation "
            "and thermal loading models in terrestrial building HVAC conduits, utility tunnels, and mine ventilation shafts."
        ),
        investigation_id="saffire_iii",
        investigation_name="Spacecraft Fire Safety Demonstration III (Saffire-III)",
        related_investigation_ids=[],
        source_type="flight_telemetry_dataset",
        source_reference="Saffire-III Flight Experiment Archive (Orbital ATK OA-7 / Cygnus PCM)",
        supporting_excerpt=(
            "Saffire-III evaluated thick fabric combustion (0.4 m x 1.0 m Sibal: 75% cotton / 25% fiberglass) inside a 0.5 m x 0.9 m "
            "flow tunnel under 23.0 cm/s calibrated ventilation, logging broadband radiant flux up to 150.39 mW/cm² and downstream "
            "thermocouple plume temperatures peaking at 95.64°C on TC3."
        ),
        dataset_or_measurement_reference="saffire_iii_sample_1.csv (20,909 rows; channels: Radiometer 1, Plume Temp 1-6, Anemometer 1, Ambient Pressure)",
        scientific_finding=(
            "Sustained, steady flame propagation occurred over 689.96 s in a confined flow duct under low-speed forced ventilation (23.0 cm/s on Anemometer 1), "
            "producing substantial downstream thermal rise (mean convective gradient +0.841 °C/s on TC1, +1.547 °C/s on TC3) and high radiant emission (150.39 mW/cm²)."
        ),
        proposed_terrestrial_relevance=(
            "Informs flame propagation and convective thermal loading models inside terrestrial mechanical ventilation ducts, "
            "subway service conduits, and high-rise exhaust shafts where forced fan flow (0.2 to 2.0 m/s) dominates over vertical buoyancy, "
            "aiding validation of automatic fire damper closure criteria and conduit fire barrier calculations."
        ),
        evidence_classification="supported_research_implication",
        validation_status="locally_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Locally verified against 20,909 continuous telemetry rows in saffire_iii_sample_1.csv. "
            "Dimension B (Terrestrial Validation): Supported research implication for duct flame spread modeling; not a certified building safety code standard."
        ),
        earth_transfer_limitations=(
            "Scale and orientation differences: Saffire flow tunnel is 0.4 m x 0.9 m cross-section, while commercial building HVAC ducts "
            "can exceed 1 to 2 m in diameter. In terrestrial horizontal ducts, buoyant thermal stratification causes flames and hot gases "
            "to cling to the duct ceiling, whereas microgravity flames remain symmetrically centered."
        ),
        gravity_buoyancy_ventilation_differences=(
            "In 1g, horizontal duct flow exhibits vertical thermal stratification (ceiling jetting). In microgravity, absence of buoyancy "
            "preserves axisymmetric temperature and velocity profiles along the flow duct axis."
        ),
        uncertainty_notes=(
            "Saffire tested clean airflow with cotton-fiberglass fuel; commercial terrestrial ducts often contain accumulated dust, "
            "grease, or microbial residue that may accelerate flame spread."
        ),
        provenance_status="locally_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 4. Saffire-III: In-Duct Fast Radiative Early Detection
    EarthApplicationEvidence(
        id="EA-EV-SAFFIRE-DET-02",
        category_id="fire_detection_smoke_aerosol",
        category_title="Fire Detection & Smoke/Aerosol Dynamics",
        title="Radiative Heat-Flux Detection Threshold Lead Time in Forced Duct Flows",
        description=(
            "Temporal correlation of Saffire telemetry demonstrates that broadband radiant flux reaches detection thresholds "
            "prior to downstream convective thermal rise in low-velocity duct combustion."
        ),
        investigation_id="saffire_iii",
        investigation_name="Spacecraft Fire Safety Demonstration III (Saffire-III)",
        related_investigation_ids=[],
        source_type="flight_telemetry_dataset",
        source_reference="Saffire-III Flight Experiment Archive (Cygnus PCM)",
        supporting_excerpt=(
            "In saffire_iii_sample_1.csv, Radiometer 1 exhibited steep radiative ignition onset at t=66.56s (-1.35 mW/cm², "
            "representing ~9.6% of the 167.87 mW/cm² dynamic range above the -17.48 mW/cm² baseline, with raw zero-crossing at t=66.89s) "
            "during the active igniter current pulse (t=60.03s to 67.98s). Downstream plume thermocouple TC3 began rising at t=66.56s (28.77°C) "
            "and crossed 35.0°C (+6°C rise above 28.98°C baseline) at t=68.21s (1.65s after radiometer onset), while TC1 crossed 31.6°C "
            "(+8°C rise above 23.46°C baseline) at t=73.16s (6.60s after radiometer onset). Downstream peak temperature on TC3 reached 95.64°C at t=109.79s (43.23s after onset). "
            "This reflects in-duct sensor transit physics during ignition, not certified building fire-alarm detector response."
        ),
        dataset_or_measurement_reference="saffire_iii_sample_1.csv (Radiometer 1 at t=66.56s, Plume Temp 3 at t=68.21s, Plume Temp 1 at t=73.16s; Igniter Current at t=60.03s)",
        scientific_finding=(
            "Line-of-sight broadband radiant emission detected ignition kernel emergence at t=66.56s (steep radiative rise, ~9.6% net dynamic span), "
            "preceding convective thermal arrival on downstream thermocouple TC3 (35°C threshold) by 1.65 s, and preceding TC1 (31.6°C threshold) by 6.60 s "
            "along the experimental flow tunnel. Convective peak exhaust temperature occurred 43.23 s later at t=109.79s."
        ),
        proposed_terrestrial_relevance=(
            "Informs sensor placement strategies for terrestrial industrial ducts and air-handling conduits: line-of-sight optical/radiant flux "
            "sensors provide earlier fire detection than downstream thermal rakes that depend on physical convective transit of hot gases."
        ),
        evidence_classification="supported_research_implication",
        validation_status="locally_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Locally verified via baseline, dynamic range, and threshold timestamp extraction on saffire_iii_sample_1.csv. "
            "Dimension B (Terrestrial Validation): Supported research implication for duct sensor layout; experimental ignition response does not constitute certified commercial fire alarm detector performance (e.g. UL 268 / UL 217)."
        ),
        earth_transfer_limitations=(
            "In terrestrial open rooms, smoke detectors rely on upward buoyant plume rising. In forced-flow horizontal conduits, "
            "sensors must account for optical obscuration from airborne dust and process vapors that could foul optical windows. "
            "Additionally, laboratory radiometer response to an active igniter coil does not evaluate commercial fire alarm false-alarm immunity or smoke particulate sensitivity."
        ),
        gravity_buoyancy_ventilation_differences=(
            "Radiative emission physics is invariant with gravity; however, convective plume transit time in 1g is modified by buoyant acceleration "
            "if the duct has vertical risers."
        ),
        uncertainty_notes=(
            "Saffire radiometers were protected by purge flows and clean tunnel windows; industrial terrestrial ducts require self-cleaning or air-curtain optical protection."
        ),
        provenance_status="locally_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 5. Saffire & BASS: Wildfire Intra-Bed Combustion Modeling
    EarthApplicationEvidence(
        id="EA-EV-SAFFIRE-WILD-03",
        category_id="wildfire_combustion",
        category_title="Wildfire Combustion & Low-Wind Fuel Beds",
        title="Microscale Radiative Spread in Low-Ventilation Porous Fuel Beds (Research Hypothesis)",
        description=(
            "Flame spread observations over porous fabric fuel matrices under low forced airflow (<5 cm/s) provide "
            "a theoretical research hypothesis for modeling intra-bed smoldering and flame spread in packed wildland forest duff."
        ),
        investigation_id="saffire_iii",
        investigation_name="Spacecraft Fire Safety Demonstration (Saffire-III)",
        related_investigation_ids=["bass_ii"],
        source_type="flight_telemetry_dataset",
        source_reference="Saffire-III & BASS-II Multi-Investigation Archive",
        supporting_excerpt=(
            "BASS-II and Saffire evaluated flame spread along porous fabric blends (cotton-fiberglass Sibal) under concurrent and opposed "
            "velocities as low as 2 to 5 cm/s, observing slow, steady flame propagation where radiant heat exchange dominates over convective cooling."
        ),
        dataset_or_measurement_reference="saffire_iii_sample_1.csv & bass_ii_experiments.csv (Runs SIBAL 1cm and 2cm wide, display flows 0 to 5 cm/s)",
        scientific_finding=(
            "In low-velocity regimes without buoyant draft, porous fabric fuels sustain steady propagation at low oxygen consumption rates "
            "(ΔO₂ ≤ 0.1% vol in BASS-II), with radiative feedback from the flame zone preheating adjacent unburned fuel fibers."
        ),
        proposed_terrestrial_relevance=(
            "Serves as an exploratory research hypothesis for wildland fire scientists investigating microscale intra-bed smoldering "
            "in tightly packed forest duff, peat bogs, and needle litters where physical packing suppresses macroscale buoyant convection."
        ),
        evidence_classification="exploratory_hypothesis",
        validation_status="locally_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Locally verified combustion data in BASS-II and Saffire-III archives. "
            "Dimension B (Terrestrial Validation): Strictly an exploratory hypothesis; microgravity fabric data has not been experimentally validated against real forest duff."
        ),
        earth_transfer_limitations=(
            "Macroscale wildfires are driven by ambient wind, terrain slopes, fuel moisture gradients, and massive buoyant convection columns. "
            "Microgravity data cannot predict open forest fire fronts; relevance is strictly confined to microscale intra-bed smolder kinetics."
        ),
        gravity_buoyancy_ventilation_differences=(
            "Open wildland fires generate intense buoyant updrafts that pull air into the fire base and drive ember spotting. "
            "Within dense duff beds, geometric packing restricts buoyant flow, creating localized diffusion-controlled conditions resembling microgravity."
        ),
        uncertainty_notes=(
            "Cotton-fiberglass Sibal fabric is an idealized cellulose model; wildland duff contains lignin, moisture (10-30%), and inorganic ash that alter pyrolysis."
        ),
        provenance_status="locally_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 6. SAME: Aerosol Agglomeration in Low-Ventilation Enclosures
    EarthApplicationEvidence(
        id="EA-EV-SAME-AERO-01",
        category_id="fire_detection_smoke_aerosol",
        category_title="Fire Detection & Smoke/Aerosol Dynamics",
        title="Aerosol Particulate Agglomeration Kinetics in Low-Circulation Enclosures",
        description=(
            "NASA SAME findings demonstrate that absence of buoyant plume venting promotes soot particle agglomeration, "
            "altering optical scattering properties in low-ventilation terrestrial enclosures."
        ),
        investigation_id="same",
        investigation_name="Smoke Aerosol Measurement Experiment (SAME / SAME-R)",
        related_investigation_ids=[],
        source_type="technical_memorandum",
        source_reference="NASA/TM—2009-215801 (Urban et al., NASA Glenn Research Center)",
        supporting_excerpt=(
            "SAME on the ISS Microgravity Science Glovebox examined smoke particulates from overheated aerospace materials (PTFE Teflon, Kapton, silicone), "
            "demonstrating that in the absence of buoyant updrafts, particles experience prolonged residence in pyrolyzing zones, yielding mean aggregate "
            "diameters significantly larger (0.5 to 3.0+ µm) than in 1g smoke (0.1 to 0.3 µm)."
        ),
        dataset_or_measurement_reference="NASA/TM—2009-215801 & raw_data/PSI-102 candidate logs (GMT262 RUN 13 teflon.xlsx, GMT263 run 14 kapton avg.xlsx)",
        scientific_finding=(
            "In non-buoyant combustion environments, primary soot particles coagulate into larger agglomerates with altered optical scattering cross-sections, "
            "substantially reducing the ionization smoke detection signal while enhancing forward and backscatter optical photodiode signals."
        ),
        proposed_terrestrial_relevance=(
            "Informs smoke detection design and aerosol sensor calibration in specialized low-circulation terrestrial facilities: "
            "semiconductor cleanrooms, underground mine refuge stations, sealed telecommunication vaults, and submarine compartments."
        ),
        evidence_classification="supported_research_implication",
        validation_status="external_literature_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Verified against NASA Technical Memorandum TM-2009-215801 and PSI-102 raw experiment logs. "
            "Dimension B (Terrestrial Validation): Supported research implication for low-ventilation aerosol physics; not a commercial detector certification."
        ),
        earth_transfer_limitations=(
            "In standard terrestrial buildings, buoyant thermal plumes rapidly transport smoke away from the fire origin before extensive coagulation occurs. "
            "Terrestrial smoke detectors are engineered and certified (UL 268 / EN 54) for smaller 1g aerosol particle size distributions."
        ),
        gravity_buoyancy_ventilation_differences=(
            "Buoyancy shortens aerosol residence time in the high-temperature reaction zone. In microgravity, extended residence allows Brownian coagulation "
            "to produce large chain-like soot agglomerates."
        ),
        uncertainty_notes=(
            "Aerosol size distribution depends strongly on the specific polymer pyrolyzed and local temperature gradients; transfer requires aerosol sizing instrumentation."
        ),
        provenance_status="external_literature_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 7. ACME: Soot Inception Kinetics
    EarthApplicationEvidence(
        id="EA-EV-ACME-SOOT-01",
        category_id="combustion_efficiency_emissions",
        category_title="Combustion Efficiency, Soot & Emissions",
        title="Laminar Microgravity Diffusion Flame Soot Inception & Growth Kinetics",
        description=(
            "ACME coflow and spherical diffusion flame experiments isolated soot inception chemistry from buoyant flickering, "
            "providing chemical-kinetic mechanism benchmarks for combustion emission modeling."
        ),
        investigation_id="acme",
        investigation_name="Advanced Combustion via Microgravity Experiments (ACME)",
        related_investigation_ids=[],
        source_type="mission_investigation_overview",
        source_reference="https://science.nasa.gov/biological-physical/investigations/acme/",
        supporting_excerpt=(
            "ACME investigated laminar microgravity diffusion flames on the ISS CIR (experiments: CIR-SOOT, CFI, Flame Design), "
            "producing unperturbed, spherical and coflow flames to measure soot inception, growth, and oxidation kinetics under controlled fuel/inert dilution."
        ),
        dataset_or_measurement_reference="NASA CIR ACME Data Archive (https://science.nasa.gov/biological-physical/investigations/acme/)",
        scientific_finding=(
            "Removing gravity-induced buoyant acceleration produces steady, unperturbed laminar diffusion flame structures with extended reaction zones, "
            "enabling precise optical measurement of soot precursor formation (polycyclic aromatic hydrocarbons, PAH) and temperature-dependent soot oxidation."
        ),
        proposed_terrestrial_relevance=(
            "Provides fundamental chemical-kinetic benchmark mechanisms (e.g. PAH growth and soot oxidation rates) used by combustion researchers "
            "in numerical simulation codes (CHEMKIN, OpenFOAM) to model soot precursors and emission pathways in terrestrial gas flames."
        ),
        evidence_classification="supported_research_implication",
        validation_status="external_literature_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Verified against NASA Biological & Physical Sciences ACME mission overview and CIR archives. "
            "Dimension B (Terrestrial Validation): Supported research implication for chemical kinetic mechanism validation; not a demonstrated commercial turbine adoption."
        ),
        earth_transfer_limitations=(
            "Terrestrial industrial combustors operate at high Reynolds numbers with intense turbulent mixing and elevated pressures (10-30 bar). "
            "Microgravity laminar kinetic data must be coupled with turbulent combustion models (LES/RANS) for terrestrial engine design."
        ),
        gravity_buoyancy_ventilation_differences=(
            "In 1g, buoyant instabilities cause flame flickering at ~10-15 Hz, disrupting optical diagnostics and mixing soot with ambient air prematurely. "
            "Microgravity eliminates flickering, yielding steady laminar flames."
        ),
        uncertainty_notes=(
            "ACME tested gaseous hydrocarbon fuels (methane, ethylene, propane); heavy terrestrial liquid fuel blends introduce additional liquid droplet atomization physics."
        ),
        provenance_status="external_literature_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 8. SoFIE: Material Thermal Degradation & Cone Calorimetry Benchmarking
    EarthApplicationEvidence(
        id="EA-EV-SOFIE-FLAM-01",
        category_id="material_flammability_fire_resistance",
        category_title="Material Flammability & Fire-Resistant Polymers",
        title="Pure Radiative Thermal Degradation for Terrestrial Fire Safety Benchmarking",
        description=(
            "NASA SoFIE (Solid Fuel Ignition and Extinction) provides baseline data on solid material ignition delay "
            "and pyrolysis under controlled radiant fluxes, benchmarking terrestrial cone calorimeter numerical models."
        ),
        investigation_id="sofie",
        investigation_name="Solid Fuel Ignition and Extinction (SoFIE - MIST / GEL)",
        related_investigation_ids=[],
        source_type="mission_investigation_overview",
        source_reference="https://science.nasa.gov/biological-physical/investigations/sofie-mist-solid-fuel-ignition-and-extinction-material-ignition-and-suppression-test/",
        supporting_excerpt=(
            "SoFIE in the ISS Combustion Integrated Rack (CIR) studies ignition and flammability of solid spacecraft materials under controlled "
            "flow and radiant heating environments, measuring ignition limits, flame growth, and extinction without buoyant flow distortion."
        ),
        dataset_or_measurement_reference="NASA CIR SoFIE Mission Documentation (https://science.nasa.gov/biological-physical/investigations/sofie-mist-solid-fuel-ignition-and-extinction-material-ignition-and-suppression-test/)",
        scientific_finding=(
            "External radiant heat flux strongly couples with boundary airflow velocity to determine ignition delay and flame spread rate; "
            "in microgravity, thermal boundary layers are thicker and lack buoyant convective heat losses, altering the surface energy balance."
        ),
        proposed_terrestrial_relevance=(
            "Provides pure solid-phase thermal decomposition parameters (activation energies, heat of gasification) that benchmark "
            "terrestrial standard testing models (e.g. ASTM E1354 Cone Calorimeter and ISO 5660), improving numerical predictive capabilities for architectural building materials."
        ),
        evidence_classification="supported_research_implication",
        validation_status="external_literature_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Verified against NASA Biological & Physical Sciences SoFIE mission documentation. "
            "Dimension B (Terrestrial Validation): Supported research implication for pyrolysis model calibration; does not replace formal ASTM building code ratings."
        ),
        earth_transfer_limitations=(
            "Standard terrestrial building material flammability codes require full-scale 1g certification tests. Microgravity data "
            "informs numerical material modeling, but cannot replace formal building code qualification tests."
        ),
        gravity_buoyancy_ventilation_differences=(
            "In 1g, buoyant flow removes heat from the unburned surface via natural convection cooling. In microgravity, heat losses "
            "are dominated by radiative emission and slow forced flow."
        ),
        uncertainty_notes=(
            "SoFIE flight tests are ongoing on the ISS CIR; full multi-material datasets are actively being integrated into NASA Physical Sciences Informatics."
        ),
        provenance_status="external_literature_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 9. FLEX: Cool Flame Chemical Kinetics for Advanced Automotive Engines
    EarthApplicationEvidence(
        id="EA-EV-FLEX-COOL-01",
        category_id="combustion_efficiency_emissions",
        category_title="Combustion Efficiency, Soot & Emissions",
        title="Low-Temperature Cool-Flame Kinetics for Advanced Internal Combustion Engine Modeling",
        description=(
            "Discovery of quasi-steady spherical cool flames in FLEX liquid droplet burning informs low-temperature "
            "combustion reaction pathways in chemical kinetic models used in advanced engine research."
        ),
        investigation_id="flex",
        investigation_name="Flame Extinguishment Experiment (FLEX / FLEX-2)",
        related_investigation_ids=[],
        source_type="peer_reviewed_literature",
        source_reference="https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/",
        supporting_excerpt=(
            "FLEX droplet combustion tests in the ISS CIR discovered that after visible hot flames extinguished radiatively, "
            "droplets of n-heptane continued to vaporize and burn with an invisible, low-temperature (~600-800 K) cool flame "
            "sustained by low-temperature peroxy chemistry."
        ),
        dataset_or_measurement_reference="FLEX CIR Data Archive & published literature on microgravity cool flames (Williams et al.)",
        scientific_finding=(
            "Hydrocarbon droplets sustain a second stage of quasi-steady low-temperature combustion governed by negative temperature "
            "coefficient (NTC) chemical kinetics, which is impossible to observe steadily in 1g due to buoyant plume disturbances."
        ),
        proposed_terrestrial_relevance=(
            "Informs low-temperature chemical kinetic reaction mechanisms (e.g. Lawrence Livermore National Laboratory mechanisms) "
            "used by combustion researchers studying Homogeneous Charge Compression Ignition (HCCI) and Low-Temperature Combustion (LTC) regimes."
        ),
        evidence_classification="supported_research_implication",
        validation_status="external_literature_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Verified against peer-reviewed published CIR droplet combustion literature. "
            "Dimension B (Terrestrial Validation): Supported research implication for chemical kinetic modeling; not an adopted commercial engine hardware modification."
        ),
        earth_transfer_limitations=(
            "In 1g, droplets fall, collide, and experience buoyant convection, making isolated steady droplet cool flames unobservable on Earth. "
            "Terrestrial engines operate with high-pressure spray mists rather than isolated single droplets."
        ),
        gravity_buoyancy_ventilation_differences=(
            "Buoyancy in 1g accelerates hot gases away, cooling the droplet environment and extinguishing cool-flame reaction zones. "
            "Microgravity provides the spherically symmetric, diffusion-dominated conditions necessary for sustained low-temperature chemistry."
        ),
        uncertainty_notes=(
            "FLEX evaluated pure alkane droplets (n-heptane, n-octane); commercial terrestrial gasoline and diesel fuels contain hundreds of aromatic and branched hydrocarbon species."
        ),
        provenance_status="external_literature_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 10. FLEX: Inert Gas Extinction Limits
    EarthApplicationEvidence(
        id="EA-EV-FLEX-SUPP-02",
        category_id="fire_suppression_research",
        category_title="Fire Suppression & Extinction Kinetics",
        title="Inert Gas Dilution Extinction Limits (CO₂, N₂, He) for Spherical Diffusion Flames",
        description=(
            "Spherical droplet extinction limits under inert gas dilution in FLEX provide baseline minimum extinguishing concentrations "
            "uncontaminated by buoyant dilution mixing."
        ),
        investigation_id="flex",
        investigation_name="Flame Extinguishment Experiment (FLEX / FLEX-2)",
        related_investigation_ids=[],
        source_type="mission_investigation_overview",
        source_reference="https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/",
        supporting_excerpt=(
            "FLEX evaluated liquid fuel droplet extinction diameters under progressive dilution with nitrogen, carbon dioxide, and helium "
            "in the CIR chamber, mapping the radiative extinction boundary as a function of inert gas heat capacity."
        ),
        dataset_or_measurement_reference="FLEX Droplet Extinction Archive (ISS CIR)",
        scientific_finding=(
            "Quantified the exact mole fraction of inert diluent (CO₂, N₂, He) required to induce radiative extinction in spherical diffusion flames, "
            "demonstrating that CO₂ extinguishes flames at lower molar concentrations than N₂ due to its higher molar heat capacity."
        ),
        proposed_terrestrial_relevance=(
            "Provides baseline physical extinction data relevant to clean gaseous fire suppression research frameworks (such as ISO 14520, NFPA 2001 inert agents IG-55, IG-100), "
            "separating chemical/thermal heat capacity quenching mechanisms from fluid-dynamic turbulent entrainment."
        ),
        evidence_classification="supported_research_implication",
        validation_status="external_literature_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Verified against peer-reviewed published CIR droplet extinction archives. "
            "Dimension B (Terrestrial Validation): Supported research implication for total-flooding inert gas suppression theory; FLEX tested inert gases only (CO2, N2, He), not halocarbons."
        ),
        earth_transfer_limitations=(
            "In 1g terrestrial fires, suppression agent discharge must penetrate turbulent fire plumes; microgravity establishes "
            "the theoretical local minimum extinction limit, but terrestrial systems require safety design factors (typically +20% to +30%) "
            "to account for non-uniform distribution."
        ),
        gravity_buoyancy_ventilation_differences=(
            "In 1g, dense gaseous suppressants (such as CO₂) settle to the floor due to negative buoyancy, while hot fire gases rise. "
            "Microgravity eliminates gravitational settling, allowing pure dilution kinetics to be measured."
        ),
        uncertainty_notes=(
            "Liquid droplet spherical symmetry isolates pure 1-D radial diffusion; terrestrial fires involve complex 3-D pool or solid geometries."
        ),
        provenance_status="external_literature_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),

    # 11. Saffire-III & Cygnus: In-Duct Ventilation Fan & Damper Shutdown Dynamics
    EarthApplicationEvidence(
        id="EA-EV-SAFFIRE-IND-04",
        category_id="other_terrestrial_applications",
        category_title="Other Evidence-Supported Terrestrial Applications",
        title="Forced-Ventilation Conduit Flow Differential Pressure & Damper Shutdown Dynamics",
        description=(
            "In-duct fan differential pressure and thermal decay tracking from Cygnus and Saffire telemetry inform "
            "motorized fire damper closure criteria and ventilation shutdown protocols in industrial conduits."
        ),
        investigation_id="saffire_iii",
        investigation_name="Spacecraft Fire Safety Demonstration III (Saffire-III)",
        related_investigation_ids=["cygnus_vehicle_telemetry"],
        source_type="flight_telemetry_dataset",
        source_reference="Saffire-III Flight Telemetry Archive (Cygnus PCM)",
        supporting_excerpt=(
            "Cygnus vehicle and Saffire telemetry recorded fan differential pressures (FIZ 2 Cabin Fan Delta P from -126.38 to +106.30 Pa) "
            "and prolonged convective thermal decay (>300 s) following in-duct flame front burnout."
        ),
        dataset_or_measurement_reference="cygnus_data.csv (FIZ 2 Cabin Fan Delta P (Pa)) & saffire_iii_sample_1.csv (Plume Temp 1-6)",
        scientific_finding=(
            "In-duct flame propagation produces localized pressure differentials across ventilation fan stages and prolonged structural heat retention "
            "in surrounding conduit walls, demonstrating the physical necessity of rapid automated fan trip interlocks to prevent forced oxidizer feeding."
        ),
        proposed_terrestrial_relevance=(
            "Informs safety damper interlock design and automated fan shutdown timelines in terrestrial mechanical ventilation conduits "
            "and industrial air-handling tunnels, where active fan pressure drives smoke spread before damper isolation."
        ),
        evidence_classification="supported_research_implication",
        validation_status="locally_verified",
        confidence_rubric=(
            "Dimension A (Experimental Grounding): Locally verified against Cygnus operational telemetry and Saffire flow duct time-series. "
            "Dimension B (Terrestrial Validation): Supported research implication for ventilation shutdown engineering; not a proprietary commercial scrubber approval."
        ),
        earth_transfer_limitations=(
            "Industrial terrestrial ducts may carry hazardous chemical vapors or grease not present in spacecraft test ducts. "
            "Consensus standards such as NFPA 90A (Standard for the Installation of Air-Conditioning and Ventilating Systems) serve as relevant terrestrial evaluation frameworks that require separate 1g physical testing."
        ),
        gravity_buoyancy_ventilation_differences=(
            "Gravity differences are minor inside high-velocity horizontal ducts, but buoyant chimney effects become significant if exhaust stacks "
            "have vertical runs exceeding 10 to 30 meters."
        ),
        uncertainty_notes=(
            "Saffire tested ambient Cygnus module air; industrial ducts carrying flammable solvent vapors introduce chemical kinetics beyond solid fabric burns."
        ),
        provenance_status="locally_verified",
        last_verified_utc="2026-11-15T06:00:00Z",
    ),
]
