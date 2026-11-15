export const RESEARCH_TOOLS = [
  {
    id: 'dataset-explorer',
    title: 'Scientific Visualization',
    description: 'Plot high-frequency flight sensor telemetry from Saffire-III, Cygnus, and ACME with extrema-preserving decimation.',
    actionText: 'Open Visualizer →',
    icon: 'Chart',
    tag: '30.3 Hz Flight Telemetry',
  },
  {
    id: 'experiment-comparison',
    title: 'Experiment Comparison',
    description: 'Compare multi-run burning behaviors across materials, oxygen levels, and forced flow in BASS-II and Saffire.',
    actionText: 'Compare Experiments →',
    icon: 'Scale',
    tag: '129 ISS Flight Runs',
  },
  {
    id: 'modeling-extraction',
    title: 'Predictive Modeling',
    description: 'Extract audited feature matrices with GroupKFold specimen grouping to eliminate repeated-burn data leakage.',
    actionText: 'Extract Features →',
    icon: 'Matrix',
    tag: 'Zero-Leakage GroupKFold',
  },
  {
    id: 'gap-detection',
    title: 'Research Gap Detection',
    description: 'Map explored flight regimes against unexplored partial gravity (0.16g Moon, 0.38g Mars) combustion environments.',
    actionText: 'Explore Gaps →',
    icon: 'Target',
    tag: 'Lunar 0.16g • 21 Findings',
  },
  {
    id: 'equipment-research',
    title: 'Fire-Safety Research',
    description: 'Connect microgravity aerosol agglomeration and extinction dynamics to spacecraft smoke detectors and suppression systems.',
    actionText: 'Inspect Equipment →',
    icon: 'Shield',
    tag: 'Cygnus Telemetry • Sensors',
  },
  {
    id: 'earth-applications',
    title: 'Earth Applications',
    description: 'Translate buoyancy-decoupled combustion science into industrial safety, building conduits, and wildfire ember modeling.',
    actionText: 'Discover Applications →',
    icon: 'Globe',
    tag: '11 Audited Evidence Records',
  },
];

export const NAV_LINKS = [
  { id: 'home', label: 'Home' },
  { id: 'dataset-explorer', label: 'Dataset Explorer' },
  { id: 'experiment-comparison', label: 'Experiment Comparison' },
  { id: 'modeling-extraction', label: 'ML Extraction' },
  { id: 'gap-detection', label: 'Research Gap Detection' },
  { id: 'equipment-research', label: 'Fire-Safety Equipment' },
  { id: 'earth-applications', label: 'Earth Applications' },
  { id: 'menu', label: 'Menu', isMenu: true },
];

export const SUGGESTED_QUERIES = [
  { label: 'BASS Material Limits', query: 'What are the flammability limits of solid materials in BASS-II under low airflow?' },
  { label: 'Lunar 34% O₂ Hazard', query: 'How does 34% oxygen at 10.2 psi in lunar gravity affect fabric ignition thresholds?' },
  { label: 'FLEX Extinction', query: 'Compare droplet extinction limits between CO2 and Helium dilution in FLEX experiments.' },
  { label: 'SAME Smoke Dynamics', query: 'How does microgravity aerosol agglomeration affect early smoke detector response times?' },
];

export const PILLARS_DATA = [
  {
    id: 'visualization',
    index: '01',
    category: 'Scientific Telemetry',
    title: 'Scientific Visualization',
    description: 'Explore verified high-frequency flight sensor data from Saffire-III, Cygnus, and ACME with extrema-preserving decimation.',
    details: 'Visualizes broadband radiometers, plume exhaust thermocouples, and duct flow anemometers. Mathematical LTTB downsampling preserves microsecond ignition spikes.',
    tag: 'Saffire • Cygnus • 30.3 Hz',
    targetTab: 'dataset-explorer',
    actionText: 'Explore Telemetry →'
  },
  {
    id: 'comparison',
    index: '02',
    category: 'Empirical Matrices',
    title: 'Experiment Comparison',
    description: 'Compare multi-run burning behaviors across solid materials (PMMA, Cotton/SIBAL, Nomex) in BASS-II and Saffire.',
    details: 'Side-by-side multi-line telemetry and 129-run flammability corridor scatter charts isolating chemical composition, oxygen concentration, and forced flow.',
    tag: 'BASS-II • 129 Runs • Saffire',
    targetTab: 'experiment-comparison',
    actionText: 'Compare Experiments →'
  },
  {
    id: 'modeling',
    index: '03',
    category: 'Machine Learning',
    title: 'Predictive Modeling Data',
    description: 'Extract audited feature matrices with strict cross-validation grouping by physical specimen (sample_id) to eliminate leakage.',
    details: 'Evaluates feature completeness, inspects uninstrumented targets (flame front tracking), and exports structured CSVs for predictive machine learning.',
    tag: 'GroupKFold • Zero Leakage • PSI',
    targetTab: 'modeling-extraction',
    actionText: 'Extract Features →'
  },
  {
    id: 'prevention',
    index: '04',
    category: 'Coverage & Gaps',
    title: 'Research Gap Detection',
    description: 'Map investigated microgravity combustion regimes against unexplored partial gravity (0.16g Moon, 0.38g Mars) environments.',
    details: 'Visualizes coverage heatmaps across gravity, oxygen concentration, and pressure. Deterministically ranks direct parameter matches for exploration habitats.',
    tag: 'Lunar 0.16g • 21 Findings • Gaps',
    targetTab: 'gap-detection',
    actionText: 'Explore Research Gaps →'
  },
  {
    id: 'equipment',
    index: '05',
    category: 'Engineering & Detection',
    title: 'Fire-Safety Equipment',
    description: 'Connect microgravity aerosol agglomeration and extinction findings to smoke sensors, radiometers, and suppression systems.',
    details: 'Translates flight telemetry from Cygnus obscuration/scatterometers and Saffire radiometer onset into design criteria for spacecraft safety systems.',
    tag: 'Cygnus • Saffire Radiometer • Smoke',
    targetTab: 'equipment-research',
    actionText: 'Inspect Equipment Insights →'
  },
  {
    id: 'earth_apps',
    index: '06',
    category: 'Terrestrial Transfer',
    title: 'Earth Applications',
    description: 'Translate buoyancy-decoupled combustion science into industrial hazard mitigation, building conduits, and wildfire ember modeling.',
    details: 'Traces 11 audited evidence records across 7 terrestrial domains via a 5-step connection bridge adhering strictly to conservative adoption classifications.',
    tag: '11 Records • 7 Domains • 5-Step Bridge',
    targetTab: 'earth-applications',
    actionText: 'Discover Earth Applications →'
  },
];


