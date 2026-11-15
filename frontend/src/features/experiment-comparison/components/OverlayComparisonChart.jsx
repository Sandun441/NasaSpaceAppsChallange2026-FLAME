import React, { useState, useMemo, useRef, useCallback } from 'react';
import { downsampleTimeSeries } from '../../dataset-explorer/utils/lttb';
import { flameApi } from '../../../services/flameApi';

/**
 * OverlayComparisonChart
 * Overlays compatible measurement curves from Dataset A and Dataset B onto a single time axis.
 * Supports absolute recorded time or event-aligned (t0 = ignition) timelines.
 */
export function OverlayComparisonChart({
  datasetAId,
  datasetBId,
  recordsA = [],
  recordsB = [],
  timeAxisA = 'Elapsed Time (s)',
  timeAxisB = 'Elapsed Time (s)',
  activeChannelObj,
  alignmentMode = 'overlay_recorded',
  ignitionTimeA = null,
  ignitionTimeB = null,
  enableDownsampling = true,
}) {
  const svgRef = useRef(null);

  // Zoom & brush state
  const [zoomRange, setZoomRange] = useState(null);
  const [brushStart, setBrushStart] = useState(null);
  const [brushCurrent, setBrushCurrent] = useState(null);
  const [isBrushing, setIsBrushing] = useState(false);

  // Hover state
  const [hoverPixelX, setHoverPixelX] = useState(null);

  // Hidden curve toggles
  const [hideA, setHideA] = useState(false);
  const [hideB, setHideB] = useState(false);

  const isEventAligned = alignmentMode === 'overlay_event_aligned' && ignitionTimeA !== null && ignitionTimeB !== null;
  const timeShiftA = isEventAligned ? ignitionTimeA : 0;
  const timeShiftB = isEventAligned ? ignitionTimeB : 0;

  // 1. Process Series A
  const seriesA = useMemo(() => {
    if (!recordsA.length || !activeChannelObj) return [];
    const pts = [];
    for (let i = 0; i < recordsA.length; i++) {
      const row = recordsA[i];
      const rawTime = row[timeAxisA];
      const rawVal = row[activeChannelObj.id];

      const t = rawTime !== undefined && rawTime !== null && rawTime !== '' ? parseFloat(rawTime) : i;
      const validT = Number.isNaN(t) ? i : t - timeShiftA;

      const isNull = rawVal === undefined || rawVal === null || rawVal === '' || rawVal === 'NaN';
      const num = isNull ? null : parseFloat(rawVal);
      const validVal = num !== null && !Number.isNaN(num) ? num : null;

      pts.push({ x: validT, y: validVal, rawIndex: i });
    }
    return pts;
  }, [recordsA, activeChannelObj, timeAxisA, timeShiftA]);

  // 2. Process Series B
  const seriesB = useMemo(() => {
    if (!recordsB.length || !activeChannelObj) return [];
    const pts = [];
    for (let i = 0; i < recordsB.length; i++) {
      const row = recordsB[i];
      const rawTime = row[timeAxisB];
      const rawVal = row[activeChannelObj.id];

      const t = rawTime !== undefined && rawTime !== null && rawTime !== '' ? parseFloat(rawTime) : i;
      const validT = Number.isNaN(t) ? i : t - timeShiftB;

      const isNull = rawVal === undefined || rawVal === null || rawVal === '' || rawVal === 'NaN';
      const num = isNull ? null : parseFloat(rawVal);
      const validVal = num !== null && !Number.isNaN(num) ? num : null;

      pts.push({ x: validT, y: validVal, rawIndex: i });
    }
    return pts;
  }, [recordsB, activeChannelObj, timeAxisB, timeShiftB]);

  // 3. Overall Time Bounds
  const { fullXMin, fullXMax } = useMemo(() => {
    let minT = Infinity;
    let maxT = -Infinity;

    seriesA.forEach((p) => {
      if (p.x < minT) minT = p.x;
      if (p.x > maxT) maxT = p.x;
    });
    seriesB.forEach((p) => {
      if (p.x < minT) minT = p.x;
      if (p.x > maxT) maxT = p.x;
    });

    if (!Number.isFinite(minT)) { minT = 0; maxT = 100; }
    return { fullXMin: minT, fullXMax: maxT };
  }, [seriesA, seriesB]);

  const activeXMin = zoomRange ? zoomRange[0] : fullXMin;
  const activeXMax = zoomRange ? zoomRange[1] : fullXMax;

  // Pan and Zoom Controls
  const handlePanLeft = useCallback(() => {
    if (!zoomRange) return;
    const span = zoomRange[1] - zoomRange[0];
    const shift = span * 0.25;
    const newMin = Math.max(fullXMin, zoomRange[0] - shift);
    const newMax = newMin + span;
    setZoomRange([newMin, Math.min(fullXMax, newMax)]);
  }, [zoomRange, fullXMin, fullXMax]);

  const handlePanRight = useCallback(() => {
    if (!zoomRange) return;
    const span = zoomRange[1] - zoomRange[0];
    const shift = span * 0.25;
    const newMax = Math.min(fullXMax, zoomRange[1] + shift);
    const newMin = Math.max(fullXMin, newMax - span);
    setZoomRange([newMin, newMax]);
  }, [zoomRange, fullXMin, fullXMax]);

  const handleZoomIn = useCallback(() => {
    const curMin = zoomRange ? zoomRange[0] : fullXMin;
    const curMax = zoomRange ? zoomRange[1] : fullXMax;
    const mid = (curMin + curMax) / 2;
    const halfSpan = (curMax - curMin) * 0.35;
    if (halfSpan < 0.05) return;
    setZoomRange([Math.max(fullXMin, mid - halfSpan), Math.min(fullXMax, mid + halfSpan)]);
  }, [zoomRange, fullXMin, fullXMax]);

  const handleZoomOut = useCallback(() => {
    if (!zoomRange) return;
    const curMin = zoomRange[0];
    const curMax = zoomRange[1];
    const mid = (curMin + curMax) / 2;
    const halfSpan = (curMax - curMin) * 0.75;
    const newMin = Math.max(fullXMin, mid - halfSpan);
    const newMax = Math.min(fullXMax, mid + halfSpan);
    if (newMin <= fullXMin && newMax >= fullXMax) {
      setZoomRange(null);
    } else {
      setZoomRange([newMin, newMax]);
    }
  }, [zoomRange, fullXMin, fullXMax]);

  const handleExportCsv = () => {
    if (!activeChannelObj) return;

    const winA = seriesA.filter((p) => p.x >= activeXMin && p.x <= activeXMax);
    const winB = seriesB.filter((p) => p.x >= activeXMin && p.x <= activeXMax);

    const timeMap = new Map();
    winA.forEach((p) => {
      const roundedT = Math.round(p.x * 1000) / 1000;
      timeMap.set(roundedT, { time: roundedT, [datasetAId]: p.y, [datasetBId]: null, delta_B_minus_A: null });
    });
    winB.forEach((p) => {
      const roundedT = Math.round(p.x * 1000) / 1000;
      if (!timeMap.has(roundedT)) {
        timeMap.set(roundedT, { time: roundedT, [datasetAId]: null, [datasetBId]: p.y, delta_B_minus_A: null });
      } else {
        const item = timeMap.get(roundedT);
        item[datasetBId] = p.y;
        if (item[datasetAId] !== null && p.y !== null) {
          item.delta_B_minus_A = Math.round((p.y - item[datasetAId]) * 1000) / 1000;
        }
      }
    });

    const rows = Array.from(timeMap.values()).sort((a, b) => a.time - b.time);
    const columns = ['time', datasetAId, datasetBId, 'delta_B_minus_A'];
    const comments = [
      'NASA FLAME Scientific Experiment Comparison Export',
      `Dataset A: ${datasetAId}`,
      `Dataset B: ${datasetBId}`,
      `Measurement Channel: ${activeChannelObj.label} [${activeChannelObj.unit}]`,
      `Alignment Mode: ${isEventAligned ? 'Event Aligned (t0 = Ignition)' : 'Absolute Recorded Time'}`,
      `Active Time Window: ${activeXMin.toFixed(3)}s to ${activeXMax.toFixed(3)}s`,
      `Total Paired Points: ${rows.length}`,
      `Discontinuities Preserved: Yes (Null values preserved across sensor gaps)`,
      `Scientific Safeguards: Sensor differences alone do not establish a flammability safety rating.`,
      `Export Timestamp: ${new Date().toISOString()}`,
    ];

    const filename = `comparison_${datasetAId}_vs_${datasetBId}_${activeChannelObj.id.replace(/[^a-zA-Z0-9]/g, '_')}.csv`;
    flameApi.exportCsv(filename, rows, columns, comments);
  };

  // 4. Filter to active zoom window and apply LTTB downsampling
  const downsampledA = useMemo(() => {
    const windowed = seriesA.filter((p) => p.x >= activeXMin && p.x <= activeXMax);
    return enableDownsampling && windowed.length > 800 ? downsampleTimeSeries(windowed, 800) : windowed;
  }, [seriesA, activeXMin, activeXMax, enableDownsampling]);

  const downsampledB = useMemo(() => {
    const windowed = seriesB.filter((p) => p.x >= activeXMin && p.x <= activeXMax);
    return enableDownsampling && windowed.length > 800 ? downsampleTimeSeries(windowed, 800) : windowed;
  }, [seriesB, activeXMin, activeXMax, enableDownsampling]);

  // 5. Y-Axis Scale Bounds across both series
  const { yMin, yMax } = useMemo(() => {
    let minY = Infinity;
    let maxY = -Infinity;

    if (!hideA) {
      downsampledA.forEach((p) => {
        if (p.y !== null && !Number.isNaN(p.y)) {
          if (p.y < minY) minY = p.y;
          if (p.y > maxY) maxY = p.y;
        }
      });
    }

    if (!hideB) {
      downsampledB.forEach((p) => {
        if (p.y !== null && !Number.isNaN(p.y)) {
          if (p.y < minY) minY = p.y;
          if (p.y > maxY) maxY = p.y;
        }
      });
    }

    if (!Number.isFinite(minY)) { minY = 0; maxY = 100; }
    const pad = (maxY - minY) * 0.08 || 1;
    return { yMin: minY - pad, yMax: maxY + pad };
  }, [downsampledA, downsampledB, hideA, hideB]);

  // 6. Geometry & Scalers
  const width = 940;
  const height = 440;
  const marginLeft = 65;
  const marginRight = 30;
  const marginTop = 30;
  const marginBottom = 50;

  const plotWidth = width - marginLeft - marginRight;
  const plotHeight = height - marginTop - marginBottom;

  const scaleX = useCallback(
    (x) => {
      const range = activeXMax - activeXMin || 1;
      return marginLeft + ((x - activeXMin) / range) * plotWidth;
    },
    [activeXMin, activeXMax, marginLeft, plotWidth]
  );

  const invertX = useCallback(
    (pixelX) => {
      const fraction = (pixelX - marginLeft) / plotWidth;
      return activeXMin + fraction * (activeXMax - activeXMin);
    },
    [activeXMin, activeXMax, marginLeft, plotWidth]
  );

  const scaleY = useCallback(
    (y) => {
      const range = yMax - yMin || 1;
      return marginTop + plotHeight - ((y - yMin) / range) * plotHeight;
    },
    [yMin, yMax, marginTop, plotHeight]
  );

  // 7. Generate Discontinuity-Preserving SVG Paths
  const pathA = useMemo(() => {
    if (hideA || !downsampledA.length) return '';
    let d = '';
    let inSub = false;
    for (let i = 0; i < downsampledA.length; i++) {
      const p = downsampledA[i];
      if (p.y === null || Number.isNaN(p.y)) {
        inSub = false;
      } else {
        const px = scaleX(p.x);
        const py = scaleY(p.y);
        d += inSub ? `L ${px.toFixed(2)} ${py.toFixed(2)} ` : `M ${px.toFixed(2)} ${py.toFixed(2)} `;
        inSub = true;
      }
    }
    return d;
  }, [downsampledA, hideA, scaleX, scaleY]);

  const pathB = useMemo(() => {
    if (hideB || !downsampledB.length) return '';
    let d = '';
    let inSub = false;
    for (let i = 0; i < downsampledB.length; i++) {
      const p = downsampledB[i];
      if (p.y === null || Number.isNaN(p.y)) {
        inSub = false;
      } else {
        const px = scaleX(p.x);
        const py = scaleY(p.y);
        d += inSub ? `L ${px.toFixed(2)} ${py.toFixed(2)} ` : `M ${px.toFixed(2)} ${py.toFixed(2)} `;
        inSub = true;
      }
    }
    return d;
  }, [downsampledB, hideB, scaleX, scaleY]);

  // 8. Axis Ticks
  const xTicks = useMemo(() => {
    const count = 7;
    const ticks = [];
    const step = (activeXMax - activeXMin) / (count - 1);
    for (let i = 0; i < count; i++) {
      const val = activeXMin + i * step;
      ticks.push({
        val,
        x: scaleX(val),
        label: Math.abs(val) >= 100 ? val.toFixed(0) : val.toFixed(1),
      });
    }
    return ticks;
  }, [activeXMin, activeXMax, scaleX]);

  const yTicks = useMemo(() => {
    const count = 6;
    const ticks = [];
    const step = (yMax - yMin) / (count - 1);
    for (let i = 0; i < count; i++) {
      const val = yMin + i * step;
      ticks.push({
        val,
        y: scaleY(val),
        label: Math.abs(val) >= 100 ? val.toFixed(0) : val.toFixed(1),
      });
    }
    return ticks;
  }, [yMin, yMax, scaleY]);

  // 9. Mouse Handlers
  const handleMouseDown = (e) => {
    if (e.button !== 0 || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const pixelX = ((e.clientX - rect.left) / rect.width) * width;
    if (pixelX >= marginLeft && pixelX <= width - marginRight) {
      setIsBrushing(true);
      setBrushStart(pixelX);
      setBrushCurrent(pixelX);
    }
  };

  const handleMouseMove = (e) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const pixelX = ((e.clientX - rect.left) / rect.width) * width;

    if (isBrushing) {
      const clampedX = Math.max(marginLeft, Math.min(width - marginRight, pixelX));
      setBrushCurrent(clampedX);
    }

    if (pixelX >= marginLeft && pixelX <= width - marginRight) {
      setHoverPixelX(pixelX);
    } else {
      setHoverPixelX(null);
    }
  };

  const handleMouseUp = () => {
    if (isBrushing && brushStart !== null && brushCurrent !== null) {
      const minPx = Math.min(brushStart, brushCurrent);
      const maxPx = Math.max(brushStart, brushCurrent);
      if (maxPx - minPx > 10) {
        const t1 = invertX(minPx);
        const t2 = invertX(maxPx);
        setZoomRange([Math.min(t1, t2), Math.max(t1, t2)]);
      }
    }
    setIsBrushing(false);
    setBrushStart(null);
    setBrushCurrent(null);
  };

  const handleMouseLeave = () => {
    setIsBrushing(false);
    setBrushStart(null);
    setBrushCurrent(null);
    setHoverPixelX(null);
  };

  // 10. Hover Tooltip Details
  const hoveredDetails = useMemo(() => {
    if (hoverPixelX === null) return null;
    const cursorTime = invertX(hoverPixelX);

    // Find nearest point in A
    let ptA = null;
    let minDiffA = Infinity;
    seriesA.forEach((p) => {
      const diff = Math.abs(p.x - cursorTime);
      if (diff < minDiffA) {
        minDiffA = diff;
        ptA = p;
      }
    });

    // Find nearest point in B
    let ptB = null;
    let minDiffB = Infinity;
    seriesB.forEach((p) => {
      const diff = Math.abs(p.x - cursorTime);
      if (diff < minDiffB) {
        minDiffB = diff;
        ptB = p;
      }
    });

    const valA = ptA && ptA.y !== null ? ptA.y : null;
    const valB = ptB && ptB.y !== null ? ptB.y : null;
    const diff = valA !== null && valB !== null ? valA - valB : null;

    return {
      time: cursorTime,
      px: hoverPixelX,
      valA,
      valB,
      pyA: valA !== null ? scaleY(valA) : null,
      pyB: valB !== null ? scaleY(valB) : null,
      diff,
    };
  }, [hoverPixelX, invertX, seriesA, seriesB, scaleY]);

  // Ignition Marker Line in Event-Aligned Mode
  const ignitionX = isEventAligned && 0 >= activeXMin && 0 <= activeXMax ? scaleX(0) : null;

  return (
    <div className="space-y-4">
      {/* Overlay Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-white border border-slate-200 px-4 py-2.5 rounded-xl font-mono shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-slate-500">Timeline Range:</span>
          <span className="text-slate-900 font-semibold">
            {activeXMin.toFixed(2)}s – {activeXMax.toFixed(2)}s
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            Δt = {(activeXMax - activeXMin).toFixed(2)}s
          </span>
          {isEventAligned && (
            <span className="text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-[10px] font-semibold">
              t′ = 0 corresponds to documented ignition
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Pan and Zoom Controls */}
          <div className="flex items-center rounded-lg bg-slate-100 border border-slate-200 overflow-hidden text-[11px] font-mono">
            <button
              onClick={handlePanLeft}
              disabled={!zoomRange}
              className="px-2.5 py-1 text-slate-700 hover:text-slate-900 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition cursor-pointer"
              title="Pan Left (Shift comparison window earlier in time)"
            >
              ◀ Pan Left
            </button>
            <div className="w-[1px] h-4 bg-slate-200" />
            <button
              onClick={handleZoomIn}
              className="px-2 py-1 text-slate-700 hover:text-slate-900 hover:bg-slate-200 transition cursor-pointer"
              title="Zoom In (Center and magnify)"
            >
              + Zoom In
            </button>
            <div className="w-[1px] h-4 bg-slate-200" />
            <button
              onClick={handleZoomOut}
              disabled={!zoomRange}
              className="px-2 py-1 text-slate-700 hover:text-slate-900 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition cursor-pointer"
              title="Zoom Out"
            >
              - Zoom Out
            </button>
            <div className="w-[1px] h-4 bg-slate-200" />
            <button
              onClick={handlePanRight}
              disabled={!zoomRange}
              className="px-2.5 py-1 text-slate-700 hover:text-slate-900 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition cursor-pointer"
              title="Pan Right (Shift comparison window later in time)"
            >
              Pan Right ▶
            </button>
          </div>

          {zoomRange && (
            <button
              onClick={() => setZoomRange(null)}
              className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-orange-600 text-[11px] border border-slate-200 transition cursor-pointer"
            >
              ↺ Reset Zoom
            </button>
          )}

          {/* Export Comparison CSV Button */}
          <button
            onClick={handleExportCsv}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-mono text-[11px] border border-emerald-600 font-semibold shadow-xs transition cursor-pointer"
            title="Download paired comparison data and deltas to CSV"
          >
            <span>📥</span>
            <span>Export Comparison CSV</span>
          </button>
        </div>
      </div>

      {/* Main SVG Canvas */}
      <div className="relative rounded-2xl bg-white border border-slate-200 shadow-sm p-2 select-none overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto cursor-crosshair"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
        >
          {/* Grid Lines */}
          <g className="stroke-slate-100">
            {xTicks.map((tick, i) => (
              <line
                key={`grid-x-${i}`}
                x1={tick.x}
                y1={marginTop}
                x2={tick.x}
                y2={marginTop + plotHeight}
                strokeDasharray="3 3"
              />
            ))}
            {yTicks.map((tick, i) => (
              <line
                key={`grid-y-${i}`}
                x1={marginLeft}
                y1={tick.y}
                x2={width - marginRight}
                y2={tick.y}
                strokeDasharray="3 3"
              />
            ))}
          </g>

          {/* Ignition Zero Marker (Event Aligned) */}
          {ignitionX !== null && (
            <g>
              <line
                x1={ignitionX}
                y1={marginTop}
                x2={ignitionX}
                y2={marginTop + plotHeight}
                stroke="#10b981"
                strokeWidth="1.5"
                strokeDasharray="4 2"
              />
              <text
                x={ignitionX + 5}
                y={marginTop + 15}
                className="text-[10px] fill-emerald-700 font-mono font-semibold"
              >
                Ignition (t′ = 0s)
              </text>
            </g>
          )}

          {/* Y-Axis */}
          <line
            x1={marginLeft}
            y1={marginTop}
            x2={marginLeft}
            y2={marginTop + plotHeight}
            stroke="#cbd5e1"
            strokeWidth="1.5"
          />
          {yTicks.map((tick, i) => (
            <g key={`tick-y-${i}`}>
              <line x1={marginLeft - 4} y1={tick.y} x2={marginLeft} y2={tick.y} stroke="#94a3b8" />
              <text
                x={marginLeft - 8}
                y={tick.y + 3}
                textAnchor="end"
                className="text-[10px] fill-slate-500 font-mono"
              >
                {tick.label}
              </text>
            </g>
          ))}
          {/* Y-Axis Label */}
          <text
            x={15}
            y={marginTop + plotHeight / 2}
            transform={`rotate(-90 15 ${marginTop + plotHeight / 2})`}
            textAnchor="middle"
            className="text-[11px] font-mono fill-orange-600 font-semibold"
          >
            {activeChannelObj ? `[${activeChannelObj.unit}]` : 'Measurement'}
          </text>

          {/* X-Axis */}
          <line
            x1={marginLeft}
            y1={marginTop + plotHeight}
            x2={width - marginRight}
            y2={marginTop + plotHeight}
            stroke="#cbd5e1"
            strokeWidth="1.5"
          />
          {xTicks.map((tick, i) => (
            <g key={`tick-x-${i}`}>
              <line
                x1={tick.x}
                y1={marginTop + plotHeight}
                x2={tick.x}
                y2={marginTop + plotHeight + 4}
                stroke="#94a3b8"
              />
              <text
                x={tick.x}
                y={marginTop + plotHeight + 16}
                textAnchor="middle"
                className="text-[10px] fill-slate-500 font-mono"
              >
                {tick.label}
              </text>
            </g>
          ))}
          {/* X-Axis Label */}
          <text
            x={marginLeft + plotWidth / 2}
            y={height - 12}
            textAnchor="middle"
            className="text-[11px] font-mono fill-slate-700 font-semibold"
          >
            {isEventAligned
              ? 'Time Relative to Ignition: t − t_ign (seconds)'
              : 'Recorded Experimental Time: Elapsed Time (seconds)'}
          </text>

          {/* Curve A (Amber) */}
          {!hideA && pathA && (
            <path
              d={pathA}
              fill="none"
              stroke="#f97316"
              strokeWidth="2"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}

          {/* Curve B (Cyan) */}
          {!hideB && pathB && (
            <path
              d={pathB}
              fill="none"
              stroke="#0284c7"
              strokeWidth="2"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          )}

          {/* Active Brush Box Selection */}
          {isBrushing && brushStart !== null && brushCurrent !== null && (
            <rect
              x={Math.min(brushStart, brushCurrent)}
              y={marginTop}
              width={Math.abs(brushCurrent - brushStart)}
              height={plotHeight}
              fill="#f59e0b"
              fillOpacity="0.15"
              stroke="#f59e0b"
              strokeWidth="1"
              strokeDasharray="4 2"
            />
          )}

          {/* Hover Crosshairs & Point Markers */}
          {hoveredDetails && (
            <g>
              <line
                x1={hoveredDetails.px}
                y1={marginTop}
                x2={hoveredDetails.px}
                y2={marginTop + plotHeight}
                stroke="#94a3b8"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
              {!hideA && hoveredDetails.pyA !== null && (
                <circle
                  cx={hoveredDetails.px}
                  cy={hoveredDetails.pyA}
                  r="4.5"
                  fill="#f97316"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              )}
              {!hideB && hoveredDetails.pyB !== null && (
                <circle
                  cx={hoveredDetails.px}
                  cy={hoveredDetails.pyB}
                  r="4.5"
                  fill="#0284c7"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              )}
            </g>
          )}
        </svg>

        {/* Hover Tooltip Box */}
        {hoveredDetails && (
          <div
            className="pointer-events-none absolute z-20 bg-white/95 border border-slate-200 rounded-xl p-3 shadow-xl backdrop-blur-md text-xs font-mono space-y-2 max-w-xs transition-all duration-75"
            style={{
              left: `${Math.min(
                width - 240,
                Math.max(20, (hoveredDetails.px / width) * 100)
              )}%`,
              top: '12px',
            }}
          >
            <div className="border-b border-slate-200 pb-1 text-slate-700 font-semibold flex items-center justify-between">
              <span>{isEventAligned ? 'Relative Time (t′):' : 'Recorded Time:'}</span>
              <span className="text-slate-900 font-bold">{hoveredDetails.time.toFixed(3)} s</span>
            </div>

            <div className="space-y-1 text-[11px]">
              <div className="flex items-center justify-between gap-3">
                <span className="text-orange-600 font-medium flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-orange-500" />
                  {datasetAId}:
                </span>
                <span className="text-slate-900 font-bold">
                  {hoveredDetails.valA !== null
                    ? `${hoveredDetails.valA.toFixed(2)} ${activeChannelObj?.unit}`
                    : 'No reading/Gap'}
                </span>
              </div>

              <div className="flex items-center justify-between gap-3">
                <span className="text-sky-600 font-medium flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-sky-500" />
                  {datasetBId}:
                </span>
                <span className="text-slate-900 font-bold">
                  {hoveredDetails.valB !== null
                    ? `${hoveredDetails.valB.toFixed(2)} ${activeChannelObj?.unit}`
                    : 'No reading/Gap'}
                </span>
              </div>

              {hoveredDetails.diff !== null && (
                <div className="border-t border-slate-200 pt-1 flex items-center justify-between gap-3">
                  <span className="text-slate-500">Delta (A − B):</span>
                  <span
                    className={`font-bold ${
                      hoveredDetails.diff > 0
                        ? 'text-orange-600'
                        : hoveredDetails.diff < 0
                        ? 'text-sky-600'
                        : 'text-slate-700'
                    }`}
                  >
                    {hoveredDetails.diff > 0 ? '+' : ''}
                    {hoveredDetails.diff.toFixed(2)} {activeChannelObj?.unit}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend & Visibility Toggles */}
      <div className="flex flex-wrap items-center gap-3 pt-1">
        <button
          onClick={() => setHideA(!hideA)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono border transition cursor-pointer ${
            hideA
              ? 'bg-slate-100 border-slate-200 text-slate-400 line-through'
              : 'bg-orange-50 border-orange-200 text-orange-900 font-medium shadow-xs'
          }`}
        >
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
          <span>Dataset A: {datasetAId}</span>
          <span className="text-[10px] text-orange-700">
            [{activeChannelObj?.unit}]
          </span>
        </button>

        <button
          onClick={() => setHideB(!hideB)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono border transition cursor-pointer ${
            hideB
              ? 'bg-slate-100 border-slate-200 text-slate-400 line-through'
              : 'bg-sky-50 border-sky-200 text-sky-900 font-medium shadow-xs'
          }`}
        >
          <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
          <span>Dataset B: {datasetBId}</span>
          <span className="text-[10px] text-sky-700">
            [{activeChannelObj?.unit}]
          </span>
        </button>
      </div>
    </div>
  );
}
