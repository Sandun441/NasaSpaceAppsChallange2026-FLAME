/**
 * Scientific Measurement Channel Classification & Unit Resolver
 *
 * NASA microgravity combustion datasets record varied physical phenomena.
 * This module inspects column names, verified metadata units, and physical dimensions
 * to prevent scientifically invalid cross-axis comparisons (e.g. combining °C and RPM on one scale).
 */

// Columns that are structural, identifiers, or time axes (never measurement channels)
const NON_MEASUREMENT_REGEX = /^(source_|CygnusTimestamp|SaffireTimestamp|Epoch Time|Timestamp \(ms\)|Index|Elapsed Time \(s\)|Relative Time|unnamed_|Actual Date|GMT 2014|Test no|Sample no|Material|Flow restrictor|Notes)/i;

// Time axis candidates in order of preference
const TIME_AXIS_CANDIDATES = [
  'Elapsed Time (s)',
  'Relative Time (s)',
  'Relative Time (ms)',
  'Timestamp (ms)',
  'Epoch Time',
  'Index',
  'source_excel_row',
];

// Physical unit classifications
export const PHYSICAL_CATEGORIES = {
  TEMPERATURE: {
    id: 'temperature',
    label: 'Temperature',
    defaultUnit: '°C',
    aliases: ['Degrees C', 'degC', '°C', 'celsius', 'C'],
    colorPalette: ['#f97316', '#ef4444', '#fb923c', '#f87171', '#fdba74', '#ea580c', '#c2410c'],
  },
  HEAT_FLUX: {
    id: 'heat_flux',
    label: 'Radiant Heat Flux',
    defaultUnit: 'mw/cm²',
    aliases: ['mw/cm^2', 'mw/cm2', 'w/m2', 'mw/cm²'],
    colorPalette: ['#a855f7', '#c084fc', '#9333ea', '#e879f9', '#d8b4fe'],
  },
  PRESSURE: {
    id: 'pressure',
    label: 'Chamber Pressure',
    defaultUnit: 'PSIA',
    aliases: ['PSIA', 'psi', 'kpa', 'bar'],
    colorPalette: ['#3b82f6', '#60a5fa', '#2563eb', '#93c5fd', '#1d4ed8'],
  },
  GAS_CONCENTRATION: {
    id: 'gas_concentration',
    label: 'Gas Concentration',
    defaultUnit: '%',
    aliases: ['%', '% by vol', 'ppm'],
    colorPalette: ['#10b981', '#34d399', '#059669', '#6ee7b7', '#047857'],
  },
  FLOW_VELOCITY: {
    id: 'flow_velocity',
    label: 'Flow Velocity',
    defaultUnit: 'cm/sec',
    aliases: ['cm/sec', 'cm/s', 'm/s'],
    colorPalette: ['#06b6d4', '#22d3ee', '#0891b2', '#67e8f9'],
  },
  FAN_SPEED: {
    id: 'fan_speed',
    label: 'Fan Speed',
    defaultUnit: 'RPM',
    aliases: ['RPM', 'rpm'],
    colorPalette: ['#14b8a6', '#2dd4bf', '#0d9488'],
  },
  ELECTRICAL_OPTICAL: {
    id: 'electrical_optical',
    label: 'Optical / Voltage',
    defaultUnit: 'V',
    aliases: ['V', 'mV', 'A', 'mA'],
    colorPalette: ['#eab308', '#facc15', '#ca8a04', '#84cc16'],
  },
  OTHER: {
    id: 'other',
    label: 'Instrument Signal',
    defaultUnit: '',
    aliases: [],
    colorPalette: ['#94a3b8', '#cbd5e1', '#64748b'],
  },
};

/**
 * Determine the best X-axis column for a dataset
 */
export function detectTimeAxis(columns = []) {
  for (const candidate of TIME_AXIS_CANDIDATES) {
    if (columns.includes(candidate)) {
      return candidate;
    }
  }
  // Check case-insensitive match
  for (const candidate of TIME_AXIS_CANDIDATES) {
    const found = columns.find(
      (c) => c.toLowerCase() === candidate.toLowerCase()
    );
    if (found) return found;
  }
  return columns.length > 0 ? columns[0] : null;
}

/**
 * Cleanly resolve the physical unit and category for a given column name
 */
export function resolveChannelUnit(columnName, metadata = null) {
  // 1. Check metadata measurement_units map if provided
  if (metadata?.measurement_units && metadata.measurement_units[columnName]) {
    const unit = metadata.measurement_units[columnName];
    return categorizeUnit(unit, columnName);
  }

  // 2. Check metadata columns array
  if (Array.isArray(metadata?.columns)) {
    const metaCol = metadata.columns.find((c) => c.column_name === columnName);
    if (metaCol?.original_unit) {
      return categorizeUnit(metaCol.original_unit, columnName);
    }
  }

  // 3. Infer unit from column name e.g. "PCM EPS 1 Press (psi)" -> "psi"
  const parenthetical = columnName.match(/\(([^)]+)\)$/);
  if (parenthetical) {
    const candidate = parenthetical[1].trim();
    // Exclude sensor labels like (TC1), (TC7)
    if (!/^TC\d+$/i.test(candidate)) {
      return categorizeUnit(candidate, columnName);
    }
  }

  // 4. Infer by keywords in column name
  return inferUnitByName(columnName);
}

function categorizeUnit(unitString, columnName = '') {
  const clean = (unitString || '').trim();
  const lower = clean.toLowerCase();

  for (const cat of Object.values(PHYSICAL_CATEGORIES)) {
    if (cat.aliases.some((a) => a.toLowerCase() === lower)) {
      return {
        unit: clean === 'Degrees C' ? '°C' : clean,
        category: cat.id,
        categoryLabel: cat.label,
      };
    }
  }

  return inferUnitByName(columnName, clean);
}

function inferUnitByName(columnName, fallbackUnit = '') {
  const lower = columnName.toLowerCase();

  if (lower.includes('temp') || lower.includes('tc')) {
    return { unit: '°C', category: PHYSICAL_CATEGORIES.TEMPERATURE.id, categoryLabel: PHYSICAL_CATEGORIES.TEMPERATURE.label };
  }
  if (lower.includes('radiometer') || lower.includes('flux')) {
    return { unit: 'mw/cm²', category: PHYSICAL_CATEGORIES.HEAT_FLUX.id, categoryLabel: PHYSICAL_CATEGORIES.HEAT_FLUX.label };
  }
  if (lower.includes('press')) {
    return { unit: 'PSIA', category: PHYSICAL_CATEGORIES.PRESSURE.id, categoryLabel: PHYSICAL_CATEGORIES.PRESSURE.label };
  }
  if (lower.includes('anemometer') || lower.includes('velocity')) {
    return { unit: 'cm/sec', category: PHYSICAL_CATEGORIES.FLOW_VELOCITY.id, categoryLabel: PHYSICAL_CATEGORIES.FLOW_VELOCITY.label };
  }
  if (lower.includes('fan') || lower.includes('tach')) {
    return { unit: 'RPM', category: PHYSICAL_CATEGORIES.FAN_SPEED.id, categoryLabel: PHYSICAL_CATEGORIES.FAN_SPEED.label };
  }
  if (lower.includes('o2') || lower.includes('co2') || lower.includes('ppm') || lower.includes('%')) {
    const isPpm = lower.includes('ppm');
    return {
      unit: isPpm ? 'ppm' : '%',
      category: PHYSICAL_CATEGORIES.GAS_CONCENTRATION.id,
      categoryLabel: PHYSICAL_CATEGORIES.GAS_CONCENTRATION.label,
    };
  }
  if (lower.includes('voltage') || lower.includes('current') || lower.includes('obscuration') || lower.includes('scatterometer') || lower.includes('(v)')) {
    return { unit: 'V', category: PHYSICAL_CATEGORIES.ELECTRICAL_OPTICAL.id, categoryLabel: PHYSICAL_CATEGORIES.ELECTRICAL_OPTICAL.label };
  }

  return {
    unit: fallbackUnit,
    category: PHYSICAL_CATEGORIES.OTHER.id,
    categoryLabel: PHYSICAL_CATEGORIES.OTHER.label,
  };
}

/**
 * Filter columns down to selectable measurement channels
 */
export function extractMeasurementChannels(columns = [], metadata = null) {
  const measurementCols = columns.filter((col) => !NON_MEASUREMENT_REGEX.test(col));

  return measurementCols.map((col, idx) => {
    const resolved = resolveChannelUnit(col, metadata);
    const cat = Object.values(PHYSICAL_CATEGORIES).find((c) => c.id === resolved.category) || PHYSICAL_CATEGORIES.OTHER;
    const color = cat.colorPalette[idx % cat.colorPalette.length];

    return {
      id: col,
      label: col,
      unit: resolved.unit,
      category: resolved.category,
      categoryLabel: resolved.categoryLabel,
      color,
    };
  });
}

/**
 * Check whether a set of channels is compatible on a single or dual axis chart
 * Enforces NASA FLAME scientific accuracy rule:
 * Unrelated sensor channels cannot be crammed onto a misleading single scale.
 * Up to 2 compatible unit groups are supported via Left and Right Y-axes.
 */
export function evaluateAxisCompatibility(selectedChannels = []) {
  if (selectedChannels.length === 0) {
    return {
      isValid: true,
      mode: 'empty',
      leftUnit: null,
      rightUnit: null,
      leftChannels: [],
      rightChannels: [],
      message: null,
    };
  }

  // Group channels by unit
  const unitMap = new Map();
  selectedChannels.forEach((channel) => {
    const key = channel.unit || channel.category;
    if (!unitMap.has(key)) {
      unitMap.set(key, []);
    }
    unitMap.get(key).push(channel);
  });

  const distinctUnits = Array.from(unitMap.keys());

  if (distinctUnits.length === 1) {
    return {
      isValid: true,
      mode: 'single',
      leftUnit: distinctUnits[0],
      rightUnit: null,
      leftChannels: unitMap.get(distinctUnits[0]),
      rightChannels: [],
      message: null,
    };
  }

  if (distinctUnits.length === 2) {
    return {
      isValid: true,
      mode: 'dual',
      leftUnit: distinctUnits[0],
      rightUnit: distinctUnits[1],
      leftChannels: unitMap.get(distinctUnits[0]),
      rightChannels: unitMap.get(distinctUnits[1]),
      message: `Dual-Axis Plot: Left Axis = [${distinctUnits[0]}], Right Axis = [${distinctUnits[1]}]`,
    };
  }

  // > 2 distinct units selected
  return {
    isValid: false,
    mode: 'incompatible',
    distinctUnits,
    message: `Physical Unit Conflict: Selected channels span ${distinctUnits.length} incompatible units (${distinctUnits.map((u) => `[${u}]`).join(', ')}). A 2D scientific chart supports at most 2 distinct physical units via dual axes. Please deselect incompatible channels to maintain scientific rigor.`,
  };
}
