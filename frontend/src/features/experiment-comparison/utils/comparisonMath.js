/**
 * NASA FLAME — Scientific Comparison Mathematics & Metrics
 *
 * Implements descriptive statistics, physical dimension verification,
 * event-based time alignment (ignition t0 shift), and empirical difference calculations.
 *
 * CRITICAL SCIENTIFIC PRINCIPLES:
 * 1. Never assume the first data point represents ignition.
 * 2. Event-aligned timelines are ONLY applied when a verified ignition event timestamp exists.
 * 3. Never interpolate across missing measurements or null data gaps.
 * 4. Correlation does not imply causation; sensor differences alone do not equal a flammability safety rating.
 */

import { resolveChannelUnit, extractMeasurementChannels } from '../../dataset-explorer/utils/channelUnits.js';

/**
 * Detect documented ignition timestamp in records
 * Checks physical igniter telemetry (Igniter Current > 0.5A, Igniter Power Enable > 0, Igniter Voltage > 5V)
 *
 * @param {Array<Object>} records - Raw dataset records
 * @param {string} timeAxis - Name of time column (e.g. 'Elapsed Time (s)')
 * @returns {number|null} Exact ignition elapsed seconds, or null if no ignition event found
 */
export function detectIgnitionTimestamp(records = [], timeAxis = 'Elapsed Time (s)') {
  if (!Array.isArray(records) || records.length === 0 || !timeAxis) {
    return null;
  }

  for (let i = 0; i < records.length; i++) {
    const row = records[i];

    // Check Igniter Current (typical Saffire threshold > 0.5 A)
    const rawCurrent = row['Igniter Current'];
    if (rawCurrent !== undefined && rawCurrent !== null && rawCurrent !== '') {
      const current = parseFloat(rawCurrent);
      if (!Number.isNaN(current) && current > 0.5) {
        const rawTime = row[timeAxis];
        const t = parseFloat(rawTime);
        return !Number.isNaN(t) ? t : i;
      }
    }

    // Check Igniter Power Enable
    const rawEnable = row['Igniter Power Enable'];
    if (rawEnable !== undefined && rawEnable !== null && rawEnable !== '') {
      const enable = parseFloat(rawEnable);
      if (!Number.isNaN(enable) && enable >= 1) {
        const rawTime = row[timeAxis];
        const t = parseFloat(rawTime);
        return !Number.isNaN(t) ? t : i;
      }
    }

    // Check Igniter Voltage
    const rawVolt = row['Igniter Voltage'];
    if (rawVolt !== undefined && rawVolt !== null && rawVolt !== '') {
      const volt = parseFloat(rawVolt);
      if (!Number.isNaN(volt) && volt > 5.0) {
        const rawTime = row[timeAxis];
        const t = parseFloat(rawTime);
        return !Number.isNaN(t) ? t : i;
      }
    }
  }

  return null;
}

/**
 * Compute real descriptive measurements for a single dataset and channel
 */
export function computeDescriptiveStatistics(records = [], channelId = '', timeAxis = 'Elapsed Time (s)') {
  if (!records.length || !channelId) {
    return {
      min: null,
      max: null,
      mean: null,
      timeOfMax: null,
      timeOfMin: null,
      startVal: null,
      endVal: null,
      startEndChange: null,
      validCount: 0,
      missingCount: 0,
      completenessPercent: 0,
    };
  }

  let min = Infinity;
  let max = -Infinity;
  let sum = 0;
  let timeOfMax = null;
  let timeOfMin = null;
  let validCount = 0;
  let missingCount = 0;
  let firstValid = null;
  let lastValid = null;

  for (let i = 0; i < records.length; i++) {
    const row = records[i];
    const rawVal = row[channelId];
    const isNullOrEmpty = rawVal === undefined || rawVal === null || rawVal === '' || rawVal === 'NaN';

    if (isNullOrEmpty) {
      missingCount++;
    } else {
      const num = parseFloat(rawVal);
      if (Number.isNaN(num)) {
        missingCount++;
      } else {
        validCount++;
        sum += num;

        if (firstValid === null) {
          firstValid = num;
        }
        lastValid = num;

        const rawTime = timeAxis ? row[timeAxis] : null;
        const t = rawTime !== null && rawTime !== undefined && rawTime !== '' ? parseFloat(rawTime) : i;

        if (num > max) {
          max = num;
          timeOfMax = Number.isNaN(t) ? i : t;
        }
        if (num < min) {
          min = num;
          timeOfMin = Number.isNaN(t) ? i : t;
        }
      }
    }
  }

  const mean = validCount > 0 ? sum / validCount : null;
  const startEndChange = firstValid !== null && lastValid !== null ? lastValid - firstValid : null;
  const total = validCount + missingCount;
  const completenessPercent = total > 0 ? (validCount / total) * 100 : 0;

  return {
    min: Number.isFinite(min) ? min : null,
    max: Number.isFinite(max) ? max : null,
    mean,
    timeOfMax,
    timeOfMin,
    startVal: firstValid,
    endVal: lastValid,
    startEndChange,
    validCount,
    missingCount,
    completenessPercent,
  };
}

/**
 * Compare descriptive statistics between Dataset A and Dataset B
 */
export function computeComparisonMetrics(statsA, statsB) {
  if (!statsA || !statsB) return null;

  const peakDiff = statsA.max !== null && statsB.max !== null ? statsA.max - statsB.max : null;
  const meanDiff = statsA.mean !== null && statsB.mean !== null ? statsA.mean - statsB.mean : null;
  const timeOfPeakOffset =
    statsA.timeOfMax !== null && statsB.timeOfMax !== null
      ? statsA.timeOfMax - statsB.timeOfMax
      : null;
  const deltaOfChange =
    statsA.startEndChange !== null && statsB.startEndChange !== null
      ? statsA.startEndChange - statsB.startEndChange
      : null;

  return {
    peakDiff,
    absPeakDiff: peakDiff !== null ? Math.abs(peakDiff) : null,
    meanDiff,
    absMeanDiff: meanDiff !== null ? Math.abs(meanDiff) : null,
    timeOfPeakOffset,
    deltaOfChange,
    aCompleteness: statsA.completenessPercent,
    bCompleteness: statsB.completenessPercent,
  };
}

/**
 * Match shared measurement channels between two datasets and classify compatibility
 */
export function matchChannels(columnsA = [], columnsB = [], metadataA = null, metadataB = null) {
  const channelsA = extractMeasurementChannels(columnsA, metadataA);
  const channelsB = extractMeasurementChannels(columnsB, metadataB);

  const mapB = new Map(channelsB.map((c) => [c.id, c]));

  const sharedChannels = [];
  const aOnlyChannels = [];
  const bOnlyChannels = [];

  channelsA.forEach((chA) => {
    if (mapB.has(chA.id)) {
      const chB = mapB.get(chA.id);
      // Check unit compatibility
      const unitA = chA.unit || resolveChannelUnit(chA.id, metadataA).unit;
      const unitB = chB.unit || resolveChannelUnit(chB.id, metadataB).unit;

      const isCompatible = !unitA || !unitB || unitA.toLowerCase() === unitB.toLowerCase();

      sharedChannels.push({
        id: chA.id,
        label: chA.label,
        unit: chA.unit || chB.unit,
        category: chA.category,
        categoryLabel: chA.categoryLabel,
        colorA: '#f59e0b', // Amber for Dataset A
        colorB: '#06b6d4', // Cyan for Dataset B
        isCompatible,
        unitA,
        unitB,
      });
      mapB.delete(chA.id);
    } else {
      aOnlyChannels.push(chA);
    }
  });

  mapB.forEach((chB) => {
    bOnlyChannels.push(chB);
  });

  return {
    sharedChannels,
    aOnlyChannels,
    bOnlyChannels,
    totalShared: sharedChannels.length,
    compatibleCount: sharedChannels.filter((c) => c.isCompatible).length,
  };
}
