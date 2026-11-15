/**
 * Largest-Triangle-Three-Buckets (LTTB) Downsampling Algorithm
 *
 * Mathematically downsamples high-frequency scientific time-series data while
 * preserving visual peaks, troughs, transient flame ignition spikes, and overall waveform dynamics.
 *
 * CRITICAL SCIENTIFIC REQUIREMENT:
 * Preserves missing measurement gaps (null/NaN). Never interpolates across missing intervals.
 * Segment boundaries and discontinuities are strictly retained.
 */

/**
 * Standard LTTB for a continuous run of valid [x, y] numeric points.
 * @param {Array<{x: number, y: number, rawIndex?: number}>} data - Valid numeric points
 * @param {number} threshold - Desired number of points in output
 * @returns {Array<{x: number, y: number, rawIndex?: number}>}
 */
export function lttbDownsampleRun(data, threshold) {
  const dataLen = data.length;
  if (threshold >= dataLen || threshold === 0) {
    return data;
  }

  const sampled = [];
  let sampledIndex = 0;

  // Bucket size. Leave room for start and end data points
  const every = (dataLen - 2) / (threshold - 2);

  let a = 0; // Initially point a is the first point
  sampled[sampledIndex++] = data[a];

  for (let i = 0; i < threshold - 2; i++) {
    // Calculate point average for next bucket (containing c)
    let avgX = 0;
    let avgY = 0;
    let avgRangeStart = Math.floor((i + 1) * every) + 1;
    let avgRangeEnd = Math.floor((i + 2) * every) + 1;
    avgRangeEnd = avgRangeEnd < dataLen ? avgRangeEnd : dataLen;

    const avgRangeLength = avgRangeEnd - avgRangeStart;

    for (let j = avgRangeStart; j < avgRangeEnd; j++) {
      avgX += data[j].x;
      avgY += data[j].y;
    }
    avgX /= (avgRangeLength || 1);
    avgY /= (avgRangeLength || 1);

    // Get the range for this bucket
    let rangeOffs = Math.floor((i + 0) * every) + 1;
    let rangeTo = Math.floor((i + 1) * every) + 1;

    // Point a
    const pointAx = data[a].x;
    const pointAy = data[a].y;

    let maxArea = -1;
    let nextA = rangeOffs;

    for (let j = rangeOffs; j < rangeTo; j++) {
      // Calculate triangle area over points a, this point, and the average point of next bucket
      const area = Math.abs(
        (pointAx - avgX) * (data[j].y - pointAy) -
        (pointAx - data[j].x) * (avgY - pointAy)
      ) * 0.5;

      if (area > maxArea) {
        maxArea = area;
        nextA = j;
      }
    }

    sampled[sampledIndex++] = data[nextA]; // Pick point with max area
    a = nextA; // This becomes next a
  }

  // Always include the last point
  sampled[sampledIndex++] = data[dataLen - 1];

  return sampled;
}

/**
 * Discontinuity-Aware Downsampler
 * Segments raw data into continuous segments separated by null/NaN values.
 * Downsamples each continuous segment proportionally, then rejoins them with null gap markers.
 *
 * @param {Array<{x: number, y: number|null, rawIndex?: number}>} data - Time series points
 * @param {number} maxPoints - Maximum target point count
 * @returns {Array<{x: number, y: number|null, rawIndex?: number}>}
 */
export function downsampleTimeSeries(data, maxPoints = 800) {
  if (!Array.isArray(data) || data.length <= maxPoints) {
    return data;
  }

  // 1. Group points into continuous valid runs and null gaps
  const segments = [];
  let currentRun = [];

  for (let i = 0; i < data.length; i++) {
    const pt = data[i];
    const isValNull = pt.y === null || pt.y === undefined || Number.isNaN(pt.y);

    if (isValNull) {
      if (currentRun.length > 0) {
        segments.push({ type: 'valid', points: currentRun });
        currentRun = [];
      }
      segments.push({ type: 'gap', point: pt });
    } else {
      currentRun.push(pt);
    }
  }

  if (currentRun.length > 0) {
    segments.push({ type: 'valid', points: currentRun });
  }

  // Count total valid points across all runs
  const totalValidPoints = segments.reduce((sum, seg) => {
    return seg.type === 'valid' ? sum + seg.points.length : sum;
  }, 0);

  if (totalValidPoints <= maxPoints) {
    return data;
  }

  // 2. Downsample each valid segment proportionally
  const downsampled = [];
  for (const seg of segments) {
    if (seg.type === 'gap') {
      downsampled.push(seg.point);
    } else {
      // Proportion of maxPoints allocated to this segment (minimum 2 points if length >= 2)
      const segRatio = seg.points.length / totalValidPoints;
      const targetForSeg = Math.max(2, Math.round(maxPoints * segRatio));

      if (seg.points.length <= targetForSeg) {
        downsampled.push(...seg.points);
      } else {
        const decimated = lttbDownsampleRun(seg.points, targetForSeg);
        downsampled.push(...decimated);
      }
    }
  }

  return downsampled;
}
