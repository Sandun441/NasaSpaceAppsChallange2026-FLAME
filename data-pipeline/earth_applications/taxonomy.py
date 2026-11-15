"""
NASA FLAME — Earth Applications Taxonomy & Classification Framework (Phase EA1)
Defines extensible categories, evidence classifications, and validation status rubrics
for connecting microgravity combustion research to terrestrial fire safety and science.
"""

from typing import List, Dict, Any

EARTH_APPLICATION_CATEGORIES = [
    {
        "id": "building_fire_safety",
        "title": "Building Fire Safety & Ventilation Ducts",
        "icon": "Building",
        "short_desc": "Conduit flame spread, HVAC duct fires, enclosed compartment dynamics, and structural fire safety.",
        "scientific_scope": (
            "Examines how forced convective flame spread, low-velocity boundary flows, and radiation-dominated "
            "combustion in microgravity inform flame propagation inside terrestrial building HVAC ducts, "
            "utility conduits, high-rise service shafts, and enclosed industrial spaces where buoyancy is restricted."
        ),
        "primary_investigations": ["saffire_iii", "bass_ii"],
        "transfer_considerations": (
            "In terrestrial buildings, buoyant thermal lift typically drives upward fire spread. However, inside horizontal "
            "mechanical air-handling ducts and ceiling plenums, forced fan velocity (0.1 to 2 m/s) dominates over buoyancy, "
            "making Saffire duct propagation models relevant for conduit fire propagation analysis."
        ),
    },
    {
        "id": "wildfire_combustion",
        "title": "Wildfire Combustion & Low-Wind Fuel Beds",
        "icon": "Trees",
        "short_desc": "Smoldering combustion, intra-bed oxidizer starvation, porous fuel arrays, and low-wind spread.",
        "scientific_scope": (
            "Investigates microscale flame spread through porous fuel matrices (cotton-fiberglass blends, thin fabrics) "
            "under low convective velocities (<10 cm/s), informing smolder-to-flame transition and intra-bed flame spread "
            "in packed forest duff, deep peat beds, and vegetative fuel arrays where macro-buoyancy is restricted."
        ),
        "primary_investigations": ["saffire_iii", "bass_ii"],
        "transfer_considerations": (
            "Open crown and surface wildfires are dominated by buoyant atmospheric updrafts and ambient wind coupling. "
            "Microgravity observations cannot model macro-scale wildfire behavior, but provide clean kinetic baseline data "
            "for intra-bed diffusion and oxygen-starved smoldering in tightly packed subterranean or forest duff layers."
        ),
    },
    {
        "id": "fire_detection_smoke_aerosol",
        "title": "Fire Detection & Smoke/Aerosol Dynamics",
        "icon": "Search",
        "short_desc": "Aerosol agglomeration, particle size shifts, optical scatterometry, and early multi-criteria detection.",
        "scientific_scope": (
            "Explores soot morphology, particle coagulation kinetics, and multi-sensor combustion signatures "
            "(radiant heat flux vs. plume temperature vs. optical scatter) to inform early warning systems in terrestrial "
            "cleanrooms, semiconductor fabrication plants, aircraft cargo bays, and subterranean mining shafts."
        ),
        "primary_investigations": ["cygnus_vehicle_telemetry", "saffire_iii", "same"],
        "transfer_considerations": (
            "Terrestrial smoke detectors are engineered for buoyant smoke plumes that rise quickly to ceilings. In non-buoyant "
            "or low-velocity environments (such as cleanrooms and ventilated transit tunnels), aerosol residence times are longer, "
            "resulting in larger soot agglomerates that alter the optimal optical scattering wavelength."
        ),
    },
    {
        "id": "material_flammability_fire_resistance",
        "title": "Material Flammability & Fire-Resistant Polymers",
        "icon": "Shield",
        "short_desc": "Solid fuel pyrolysis, limiting oxygen limits, low-flow stabilization, and flame-retardant polymers.",
        "scientific_scope": (
            "Evaluates solid polymer combustion (PMMA, Nomex, cotton blends) across oxygen concentrations and flow velocities "
            "without buoyant convection, providing pure chemical-kinetic and pyrolysis properties that benchmark "
            "terrestrial flammability models (e.g. cone calorimetry and Pyropolis CFD sub-models)."
        ),
        "primary_investigations": ["bass_ii", "saffire_iii", "sofie"],
        "transfer_considerations": (
            "Standard 1g material screening (e.g. UL 94, ASTM E84, NASA-STD-6001 Test 1) is heavily masked by buoyant draft velocity. "
            "Microgravity isolates pure convective feeding and flame anchoring, identifying flammability stabilization regimes "
            "that occur in low-speed forced ventilation but are extinguished by buoyant blowout in normal gravity."
        ),
    },
    {
        "id": "fire_suppression_research",
        "title": "Fire Suppression & Extinction Kinetics",
        "icon": "Flame",
        "short_desc": "Radiative extinction limits, convective blow-off corridors, oxygen starvation, and gaseous diluents.",
        "scientific_scope": (
            "Investigates fundamental flame extinction boundaries: quiescent starvation (<1.5 cm/s), convective blow-off "
            "(>28-38 cm/s), and inert gas dilution (CO₂, N₂), providing benchmark extinction thresholds for terrestrial "
            "total-flooding gaseous suppression systems and water mist design."
        ),
        "primary_investigations": ["bass_ii", "saffire_iii", "flex", "sofie"],
        "transfer_considerations": (
            "In 1g fires, suppressants must overcome buoyant momentum plumes to reach the flame zone. Microgravity data isolates "
            "the intrinsic chemical and radiative cooling thresholds required for extinction, establishing theoretical minimum "
            "inhibitor concentrations that terrestrial systems must achieve locally."
        ),
    },
    {
        "id": "combustion_efficiency_emissions",
        "title": "Combustion Efficiency, Soot & Emissions",
        "icon": "Cpu",
        "short_desc": "Symmetric diffusion flames, soot inception/growth, cool flame kinetics, and emission reduction.",
        "scientific_scope": (
            "Analyzes spherically symmetric and coflow laminar diffusion flames to measure soot formation pathways, "
            "radiative heat loss, and low-temperature 'cool flame' reaction kinetics, directly informing cleaner "
            "terrestrial gas turbines, industrial boilers, and low-emission internal combustion engines."
        ),
        "primary_investigations": ["acme", "flex"],
        "transfer_considerations": (
            "Terrestrial combustion chambers operate with high turbulence and Reynolds numbers. Microgravity provides "
            "unperturbed laminar diffusion flame structures that allow isolating chemical soot precursor kinetics from "
            "turbulent mixing, enabling validation of numerical combustion mechanism solvers."
        ),
    },
    {
        "id": "other_terrestrial_applications",
        "title": "Other Evidence-Supported Terrestrial Applications",
        "icon": "Layers",
        "short_desc": "Specialized industrial hazard analysis, high-consequence facility safety, and computational combustion.",
        "scientific_scope": (
            "Encompasses additional evidence-supported terrestrial applications such as semiconductor manufacturing exhaust safety, "
            "subterranean mining refuge bays, nuclear facility ventilation containment, and computational combustion code validation."
        ),
        "primary_investigations": ["saffire_iii", "bass_ii", "cygnus_vehicle_telemetry"],
        "transfer_considerations": (
            "Must be strictly evaluated on a case-by-case basis against specific experimental evidence and boundary conditions."
        ),
    },
]

EVIDENCE_CLASSIFICATION_RUBRIC = {
    "documented_application": {
        "label": "Documented Terrestrial Application",
        "description": (
            "The microgravity experimental finding has been directly utilized, benchmarked, or cited in published "
            "terrestrial engineering standards, combustion models, or industrial technology developments."
        ),
        "transferability_standard": "Demonstrated citation or direct incorporation into terrestrial combustion/fire tools.",
    },
    "supported_research_implication": {
        "label": "Supported Research Implication",
        "description": (
            "The microgravity physical mechanism (e.g. low-flow flame anchoring, soot agglomeration, radiative extinction) "
            "has a rigorous, peer-reviewed theoretical connection to terrestrial fire science, but requires scaling, "
            "numerical modeling, or terrestrial validation before direct engineering application."
        ),
        "transferability_standard": "Theoretically and physically grounded in verified data; requires terrestrial scaling.",
    },
    "exploratory_hypothesis": {
        "label": "Exploratory Research Hypothesis",
        "description": (
            "A scientifically plausible research hypothesis proposing how microgravity combustion insights might inform "
            "a terrestrial challenge, but currently lacking dedicated terrestrial experimental validation or transfer qualification."
        ),
        "transferability_standard": "Hypothesis only; unvalidated for terrestrial engineering deployment.",
    },
}

VALIDATION_STATUS_RUBRIC = {
    "locally_verified": {
        "label": "Locally Verified in NASA FLAME",
        "description": "Evidence is directly traceable to raw or processed flight datasets and time-series archived within NASA FLAME.",
        "grounding_level": "Tier 1: Full local data provenance and channel verification.",
    },
    "external_literature_verified": {
        "label": "External Literature Verified",
        "description": (
            "Evidence is verified against peer-reviewed NASA publications, technical reports (TM/CR), or NASA Physical "
            "Sciences Informatics (PSI) repository records with verifiable URLs or DOIs, but raw telemetry is unindexed in FLAME."
        ),
        "grounding_level": "Tier 2: External peer-reviewed provenance.",
    },
    "pending_verification": {
        "label": "Pending Verification",
        "description": "Candidate finding or investigation noted in mission overviews, but primary supporting documents are pending full access or verification.",
        "grounding_level": "Tier 3: Unconfirmed candidate; not established evidence.",
    },
    "unverified_hypothesis": {
        "label": "Unverified Hypothesis",
        "description": "Exploratory research hypothesis that has not been confirmed through experimental flight records or literature.",
        "grounding_level": "Tier 4: Speculative; not verified.",
    },
}
