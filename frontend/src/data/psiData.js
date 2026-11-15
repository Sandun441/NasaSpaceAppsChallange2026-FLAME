/**
 * NASA Physical Sciences Informatics (PSI) Combustion Science Metadata & Research Dimensions
 * 
 * Provides official PSI repository metadata and canonical research parameter dimensions
 * (gravity, oxygen, pressure, fuel, airflow) for prompt interpretation and UI filters.
 */

export const PSI_METADATA_PRIMER = {
  repositoryName: "NASA Physical Sciences Informatics (PSI) System",
  url: "https://psi.nasa.gov",
  combustionDiscipline: "Combustion Science & Spacecraft Fire Safety",
  flightFacilities: [
    "ISS Microgravity Science Glovebox (MSG)",
    "ISS Combustion Integrated Rack (CIR)",
    "Cygnus Saffire Flow Duct Facility"
  ],
  availableInRawRecords: [
    "Thermocouple temperature arrays",
    "Chamber pressure logs",
    "Radiometer radiant heat flux voltages",
    "Calibrated flame imaging sequences",
    "Duct flow anemometer readings"
  ],
  availableOnlyInSecondaryPublications: [
    "Derived chemical kinetic rate equations",
    "Soot volume fraction cross-sections",
    "Asymptotic flame extinction boundary curves"
  ],
  unavailableInPSIFlightRecords: [
    "Steady-state long-duration burning in continuous lunar (0.16g) or Martian (0.38g) gravity",
    "Commercial equipment certification ratings"
  ]
};

export const RESEARCH_DIMENSIONS = {
  gravity: [
    { id: 'all', label: 'All Gravity Regimes' },
    { id: 'normal', label: 'Normal Gravity (1g)' },
    { id: 'micro', label: 'Microgravity (0g / ~10⁻⁵g)' },
    { id: 'partial-lunar', label: 'Partial Gravity - Lunar (0.16g)' },
    { id: 'partial-mars', label: 'Partial Gravity - Mars (0.38g)' }
  ],
  oxygen: [
    { id: 'all', label: 'All O₂ Levels' },
    { id: 'low', label: 'Hypoxic / Low O₂ (<18%)' },
    { id: 'normal', label: 'Standard Air (21% O₂)' },
    { id: 'elevated', label: 'Intermediate Exploration (28–34% O₂)' },
    { id: 'high', label: 'Hyperoxic (>34% O₂)' }
  ],
  pressure: [
    { id: 'all', label: 'All Pressures' },
    { id: 'hypobaric', label: 'Hypobaric Cabin (56–70 kPa / 8.2–10.2 psi)' },
    { id: 'standard', label: 'Sea Level Standard (101.3 kPa / 14.7 psi)' },
    { id: 'hyperbaric', label: 'Elevated Pressure (>105 kPa)' }
  ],
  fuel: [
    { id: 'all', label: 'All Fuel Types' },
    { id: 'solid-flat', label: 'Solid Fabrics & Flat Sheets' },
    { id: 'solid-thick', label: 'Thick Solids' },
    { id: 'droplet', label: 'Liquid Droplets' },
    { id: 'gaseous', label: 'Gaseous Burner Fuels' }
  ],
  airflow: [
    { id: 'all', label: 'All Airflows' },
    { id: 'quiescent', label: 'Quiescent Flow (0 cm/s)' },
    { id: 'low-flow', label: 'Low Forced Convection (0.5 – 5 cm/s)' },
    { id: 'high-flow', label: 'High Forced Convection (>10 cm/s)' }
  ]
};

export const PSI_STATISTICS = {
  totalFlightDatasets: 11,
  indexedFlightRuns: 133,
  primaryInvestigations: 6,
  auditedEvidenceRecords: 11
};
