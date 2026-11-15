import React, { useState, useMemo, useRef, useCallback } from 'react';
import { downsampleTimeSeries } from '../../utils/lttb';
import { flameApi } from '../../../../services/flameApi';

/**
 * NASA FLAME Scientific Time-Series Chart
 *
 * High-performance, pure React + SVG scientific visualization engine.
 * Features:
 * - Single or Dual Y-axes (prevents false cross-unit scale distortions)
 * - Strict discontinuity preservation (breaks SVG lines across missing/null values)
 * - Click-and-drag brush box zoom on time axis + pan controls & reset
 * - Interactive crosshair cursor with real recorded values and verified physical units
 * - Physically verified experimental event markers (e.g. ignition onset)
 * - Clearly defined analysis intervals with interval-scoped descriptive statistics
 * - Built-in CSV export with scientific metadata headers
 */
export function TimeSeriesChart({
  records = [],
  timeAxis = 'Elapsed Time (s)',
  selectedChannels = [],
  axisCompatibility,
  enableDownsampling = true,
  verifiedEvents = [],
  dataQuality = null,
  datasetId = '',
  onExportCsv = null,
}) {
  const svgRef = useRef(null);

  // Zoom state: [minTime, maxTime] or null (full range)
  const [zoomRange, setZoomRange] = useState(null);
  const [brushStart, setBrushStart] = useState(null);
  const [brushCurrent, setBrushCurrent] = useState(null);
  const [isBrushing, setIsBrushing] = useState(false);

  // Statistics Scope: 'interval' (active zoom window) or 'all' (full loaded buffer)
  const [statsScope, setStatsScope] = useState('interval');

  // Hover crosshair state: clientX relative to plot
  const [hoverIndex, setHoverIndex] = useState(null);

  // Hidden channels state (for legend toggle)
  const [hiddenChannelIds, setHiddenChannelIds] = useState([]);

  const toggleChannelVisibility = (chId) => {
    setHiddenChannelIds((prev) =>
      prev.includes(chId) ? prev.filter((id) => id !== chId) : [...prev, chId]
    );
  };

  // 1. Parse and extract time values and channel points
  const parsedData = useMemo(() => {
    if (!records.length || !timeAxis) {
      return { timeValues: [], channelSeries: {}, fullXMin: 0, fullXMax: 1 };
    }

    const timeValues = [];
    const channelSeries = {};

    selectedChannels.forEach((ch) => {
      channelSeries[ch.id] = [];
    });

    for (let i = 0; i < records.length; i++) {
      const row = records[i];
      const rawTime = row[timeAxis] !== undefined ? row[timeAxis] : row['time'];
      const t = rawTime !== undefined && rawTime !== null && rawTime !== '' ? parseFloat(rawTime) : i;
      const validT = Number.isNaN(t) ? i : t;

      timeValues.push(validT);

      selectedChannels.forEach((ch) => {
        const rawVal = row[ch.id];
        const isNullOrEmpty = rawVal === undefined || rawVal === null || rawVal === '' || rawVal === 'NaN';
        const numVal = isNullOrEmpty ? null : parseFloat(rawVal);
        const validVal = numVal !== null && !Number.isNaN(numVal) ? numVal : null;

        channelSeries[ch.id].push({
          x: validT,
          y: validVal,
          rawIndex: i,
        });
      });
    }

    const fullXMin = timeValues.length > 0 ? timeValues[0] : 0;
    const fullXMax = timeValues.length > 0 ? timeValues[timeValues.length - 1] : 1;

    return { timeValues, channelSeries, fullXMin, fullXMax };
  }, [records, timeAxis, selectedChannels]);

  // 2. Active time bounds (zoomed or full)
  const activeXMin = zoomRange ? zoomRange[0] : parsedData.fullXMin;
  const activeXMax = zoomRange ? zoomRange[1] : parsedData.fullXMax;

  // Pan and Zoom Controls
  const handlePanLeft = useCallback(() => {
    if (!zoomRange) return;
    const span = zoomRange[1] - zoomRange[0];
    const shift = span * 0.25;
    const newMin = Math.max(parsedData.fullXMin, zoomRange[0] - shift);
    const newMax = newMin + span;
    setZoomRange([newMin, Math.min(parsedData.fullXMax, newMax)]);
  }, [zoomRange, parsedData.fullXMin, parsedData.fullXMax]);

  const handlePanRight = useCallback(() => {
    if (!zoomRange) return;
    const span = zoomRange[1] - zoomRange[0];
    const shift = span * 0.25;
    const newMax = Math.min(parsedData.fullXMax, zoomRange[1] + shift);
    const newMin = Math.max(parsedData.fullXMin, newMax - span);
    setZoomRange([newMin, newMax]);
  }, [zoomRange, parsedData.fullXMin, parsedData.fullXMax]);

  const handleZoomIn = useCallback(() => {
    const curMin = zoomRange ? zoomRange[0] : parsedData.fullXMin;
    const curMax = zoomRange ? zoomRange[1] : parsedData.fullXMax;
    const mid = (curMin + curMax) / 2;
    const halfSpan = (curMax - curMin) * 0.35;
    if (halfSpan < 0.05) return;
    setZoomRange([Math.max(parsedData.fullXMin, mid - halfSpan), Math.min(parsedData.fullXMax, mid + halfSpan)]);
  }, [zoomRange, parsedData.fullXMin, parsedData.fullXMax]);

  const handleZoomOut = useCallback(() => {
    if (!zoomRange) return;
    const curMin = zoomRange[0];
    const curMax = zoomRange[1];
    const mid = (curMin + curMax) / 2;
    const halfSpan = (curMax - curMin) * 0.75;
    const newMin = Math.max(parsedData.fullXMin, mid - halfSpan);
    const newMax = Math.min(parsedData.fullXMax, mid + halfSpan);
    if (newMin <= parsedData.fullXMin && newMax >= parsedData.fullXMax) {
      setZoomRange(null);
    } else {
      setZoomRange([newMin, newMax]);
    }
  }, [zoomRange, parsedData.fullXMin, parsedData.fullXMax]);

  const resetZoom = () => {
    setZoomRange(null);
  };

  // 3. Filter points within active X window and apply LTTB downsampling if enabled
  const processedSeries = useMemo(() => {
    const result = {};

    selectedChannels.forEach((ch) => {
      const allPoints = parsedData.channelSeries[ch.id] || [];

      // Window filtering
      const windowed = allPoints.filter(
        (pt) => pt.x >= activeXMin && pt.x <= activeXMax
      );

      // Downsampling: If enabled and points > 800, decimate with gap preservation
      if (enableDownsampling && windowed.length > 800) {
        result[ch.id] = downsampleTimeSeries(windowed, 800);
      } else {
        result[ch.id] = windowed;
      }
    });

    return result;
  }, [selectedChannels, parsedData, activeXMin, activeXMax, enableDownsampling]);

  // 4. Determine Y-axis scales (Left and Right)
  const isDualAxis = axisCompatibility?.mode === 'dual';
  const rightChannelIds = (axisCompatibility?.rightChannels || []).map((c) => c.id);

  const { yMinLeft, yMaxLeft, yMinRight, yMaxRight } = useMemo(() => {
    let minL = Infinity;
    let maxL = -Infinity;
    let minR = Infinity;
    let maxR = -Infinity;

    selectedChannels.forEach((ch) => {
      if (hiddenChannelIds.includes(ch.id)) return;
      const pts = processedSeries[ch.id] || [];
      const isRight = isDualAxis && rightChannelIds.includes(ch.id);

      pts.forEach((pt) => {
        if (pt.y !== null && !Number.isNaN(pt.y)) {
          if (isRight) {
            if (pt.y < minR) minR = pt.y;
            if (pt.y > maxR) maxR = pt.y;
          } else {
            if (pt.y < minL) minL = pt.y;
            if (pt.y > maxL) maxL = pt.y;
          }
        }
      });
    });

    // Fallbacks if no data
    if (!Number.isFinite(minL)) { minL = 0; maxL = 100; }
    if (!Number.isFinite(minR)) { minR = 0; maxR = 100; }

    // Add 6% headroom padding
    const padL = (maxL - minL) * 0.06 || 1;
    const padR = (maxR - minR) * 0.06 || 1;

    return {
      yMinLeft: minL - padL,
      yMaxLeft: maxL + padL,
      yMinRight: minR - padR,
      yMaxRight: maxR + padR,
    };
  }, [selectedChannels, hiddenChannelIds, processedSeries, isDualAxis, rightChannelIds]);

  // 5. Chart Layout Geometry
  const width = 940;
  const height = 440;
  const marginLeft = 65;
  const marginRight = isDualAxis ? 65 : 25;
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
    (y, isRight = false) => {
      const yMin = isRight ? yMinRight : yMinLeft;
      const yMax = isRight ? yMaxRight : yMaxLeft;
      const range = yMax - yMin || 1;
      return marginTop + plotHeight - ((y - yMin) / range) * plotHeight;
    },
    [yMinLeft, yMaxLeft, yMinRight, yMaxRight, marginTop, plotHeight]
  );

  // 6. Generate SVG Path Strings with DISCONTINUITY PRESERVATION
  const paths = useMemo(() => {
    const lines = {};

    selectedChannels.forEach((ch) => {
      if (hiddenChannelIds.includes(ch.id)) return;
      const pts = processedSeries[ch.id] || [];
      const isRight = isDualAxis && rightChannelIds.includes(ch.id);

      let d = '';
      let inSubpath = false;

      for (let i = 0; i < pts.length; i++) {
        const pt = pts[i];
        if (pt.y === null || Number.isNaN(pt.y)) {
          inSubpath = false;
        } else {
          const px = scaleX(pt.x);
          const py = scaleY(pt.y, isRight);

          if (!inSubpath) {
            d += `M ${px.toFixed(2)} ${py.toFixed(2)} `;
            inSubpath = true;
          } else {
            d += `L ${px.toFixed(2)} ${py.toFixed(2)} `;
          }
        }
      }

      lines[ch.id] = d;
    });

    return lines;
  }, [selectedChannels, hiddenChannelIds, processedSeries, isDualAxis, rightChannelIds, scaleX, scaleY]);

  // 7. Grid Lines & Ticks
  const xTicks = useMemo(() => {
    const count = 7;
    const ticks = [];
    const step = (activeXMax - activeXMin) / (count - 1);
    for (let i = 0; i < count; i++) {
      const val = activeXMin + i * step;
      ticks.push({
        val,
        x: scaleX(val),
        label: val >= 1000 ? val.toFixed(0) : val.toFixed(1),
      });
    }
    return ticks;
  }, [activeXMin, activeXMax, scaleX]);

  const yTicksLeft = useMemo(() => {
    const count = 6;
    const ticks = [];
    const step = (yMaxLeft - yMinLeft) / (count - 1);
    for (let i = 0; i < count; i++) {
      const val = yMinLeft + i * step;
      ticks.push({
        val,
        y: scaleY(val, false),
        label: Math.abs(val) >= 100 ? val.toFixed(0) : val.toFixed(1),
      });
    }
    return ticks;
  }, [yMinLeft, yMaxLeft, scaleY]);

  const yTicksRight = useMemo(() => {
    if (!isDualAxis) return [];
    const count = 6;
    const ticks = [];
    const step = (yMaxRight - yMinRight) / (count - 1);
    for (let i = 0; i < count; i++) {
      const val = yMinRight + i * step;
      ticks.push({
        val,
        y: scaleY(val, true),
        label: Math.abs(val) >= 100 ? val.toFixed(0) : val.toFixed(1),
      });
    }
    return ticks;
  }, [isDualAxis, yMinRight, yMaxRight, scaleY]);

  // 8. Mouse brush & hover handlers
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
      // Find closest time point
      const timeAtCursor = invertX(pixelX);
      const timeArr = parsedData.timeValues;
      if (timeArr.length > 0) {
        let closestIdx = 0;
        let minDiff = Infinity;
        for (let i = 0; i < timeArr.length; i++) {
          const diff = Math.abs(timeArr[i] - timeAtCursor);
          if (diff < minDiff) {
            minDiff = diff;
            closestIdx = i;
          }
        }
        setHoverIndex(closestIdx);
      }
    } else {
      setHoverIndex(null);
    }
  };

  const handleMouseUp = () => {
    if (isBrushing && brushStart !== null && brushCurrent !== null) {
      const minPx = Math.min(brushStart, brushCurrent);
      const maxPx = Math.max(brushStart, brushCurrent);

      // Only zoom if dragged at least 10px
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
    setHoverIndex(null);
  };

  // 9. Hover Tooltip Details
  const hoveredPointInfo = useMemo(() => {
    if (hoverIndex === null || !records[hoverIndex]) return null;

    const row = records[hoverIndex];
    const timeVal = parsedData.timeValues[hoverIndex];

    const channelValues = selectedChannels.map((ch) => {
      const rawVal = row[ch.id];
      const isNull = rawVal === undefined || rawVal === null || rawVal === '' || rawVal === 'NaN';
      const numVal = isNull ? null : parseFloat(rawVal);
      const isRight = isDualAxis && rightChannelIds.includes(ch.id);

      return {
        ...ch,
        val: isNull || Number.isNaN(numVal) ? 'No reading' : numVal,
        numericVal: isNull || Number.isNaN(numVal) ? null : numVal,
        isNull,
        py: isNull || Number.isNaN(numVal) ? null : scaleY(numVal, isRight),
      };
    });

    return {
      time: timeVal,
      px: scaleX(timeVal),
      channelValues,
    };
  }, [hoverIndex, records, parsedData, selectedChannels, isDualAxis, rightChannelIds, scaleX, scaleY]);

  // 10. Summary Statistics (Interval-Scoped or Full Loaded Window)
  const channelStats = useMemo(() => {
    return selectedChannels.map((ch) => {
      const allPts = parsedData.channelSeries[ch.id] || [];
      const ptsToAnalyze = statsScope === 'interval'
        ? allPts.filter((pt) => pt.x >= activeXMin && pt.x <= activeXMax)
        : allPts;

      let min = Infinity;
      let max = -Infinity;
      let sum = 0;
      let validCount = 0;
      let missingCount = 0;

      ptsToAnalyze.forEach((pt) => {
        if (pt.y !== null && !Number.isNaN(pt.y)) {
          if (pt.y < min) min = pt.y;
          if (pt.y > max) max = pt.y;
          sum += pt.y;
          validCount++;
        } else {
          missingCount++;
        }
      });

      const mean = validCount > 0 ? sum / validCount : null;

      return {
        id: ch.id,
        label: ch.label,
        unit: ch.unit,
        color: ch.color,
        min: Number.isFinite(min) ? min : null,
        max: Number.isFinite(max) ? max : null,
        mean,
        validCount,
        missingCount,
      };
    });
  }, [selectedChannels, parsedData, statsScope, activeXMin, activeXMax]);

  // 11. CSV Export Handler
  const handleExportCsv = () => {
    if (onExportCsv) {
      onExportCsv({ activeXMin, activeXMax, selectedChannels });
      return;
    }

    const rowsToExport = records
      .filter((r) => {
        const rawT = r[timeAxis] !== undefined ? r[timeAxis] : r['time'];
        const t = parseFloat(rawT);
        if (Number.isNaN(t)) return true;
        return t >= activeXMin && t <= activeXMax;
      })
      .map((r) => {
        const rawT = r[timeAxis] !== undefined ? r[timeAxis] : r['time'];
        const numericT = rawT !== undefined && rawT !== null && rawT !== '' ? parseFloat(rawT) : null;
        return {
          ...r,
          [timeAxis]: numericT !== null && !Number.isNaN(numericT) ? numericT : rawT,
        };
      });

    const exportCols = [timeAxis, ...selectedChannels.map((c) => c.id)];
    const comments = [
      'NASA FLAME Scientific Data Export',
      `Dataset ID: ${datasetId || 'NASA_Microgravity_Combustion_Telemetry'}`,
      `Time Axis Column: ${timeAxis}`,
      `Time Window: ${activeXMin.toFixed(3)}s to ${activeXMax.toFixed(3)}s (Span: ${(activeXMax - activeXMin).toFixed(3)}s)`,
      `Total Exported Points: ${rowsToExport.length}`,
      `Sampling Rate: ~${dataQuality?.sampling_rate_hz || 30.3} Hz`,
      `Selected Channels: ${selectedChannels.map((c) => `${c.label} [${c.unit}]`).join(', ')}`,
      `Discontinuities Preserved: Yes (Null/missing sensor readings left blank)`,
      `Scientific Limitations: Flame spread rate and exact extinction times require post-flight optical analysis.`,
      `Export Timestamp: ${new Date().toISOString()}`,
    ];

    const filename = `${datasetId || 'nasa_flame'}_${activeXMin.toFixed(0)}s_${activeXMax.toFixed(0)}s.csv`;
    flameApi.exportCsv(filename, rowsToExport, exportCols, comments, timeAxis);
  };

  if (selectedChannels.length === 0) {
    return (
      <div className="p-12 rounded-2xl bg-white border border-slate-200 text-center space-y-3 shadow-sm">
        <div className="w-10 h-10 mx-auto rounded-full bg-orange-50 border border-orange-200 flex items-center justify-center text-orange-600">
          📈
        </div>
        <p className="text-sm font-medium text-slate-900">No Measurement Channels Selected</p>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          Select one or more verified sensor channels from the channel selector above to render real telemetry measurements.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Chart Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-white border border-slate-200 px-4 py-2.5 rounded-xl shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-slate-500">Time Window:</span>
          <span className="font-mono text-slate-900 font-semibold">
            {activeXMin.toFixed(2)}s – {activeXMax.toFixed(2)}s
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            Δt = {(activeXMax - activeXMin).toFixed(2)}s
          </span>
          {zoomRange && (
            <span className="bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded text-[11px] font-mono font-medium">
              Zoom Active
            </span>
          )}
          {dataQuality?.sampling_rate_hz > 0 && (
            <span className="text-[10px] font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
              Rate: ~{dataQuality.sampling_rate_hz} Hz
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Pan & Zoom Controls */}
          <div className="flex items-center rounded-lg bg-slate-100 border border-slate-200 overflow-hidden text-[11px] font-mono">
            <button
              onClick={handlePanLeft}
              disabled={!zoomRange}
              className="px-2.5 py-1 text-slate-700 hover:text-slate-900 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition cursor-pointer"
              title="Pan Left (Shift window earlier in time)"
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
              title="Pan Right (Shift window later in time)"
            >
              Pan Right ▶
            </button>
          </div>

          {zoomRange && (
            <button
              onClick={resetZoom}
              className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-orange-600 font-mono text-[11px] border border-slate-200 transition cursor-pointer"
            >
              ↺ Reset Zoom
            </button>
          )}

          {/* Export CSV Button */}
          <button
            onClick={handleExportCsv}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-mono text-[11px] border border-emerald-600 font-semibold shadow-xs transition cursor-pointer"
            title="Download active time-series data to CSV"
          >
            <span>📥</span>
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Main SVG Chart Canvas */}
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
          {/* Background Grid Lines */}
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
            {yTicksLeft.map((tick, i) => (
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

          {/* Left Y-Axis */}
          <line
            x1={marginLeft}
            y1={marginTop}
            x2={marginLeft}
            y2={marginTop + plotHeight}
            stroke="#cbd5e1"
            strokeWidth="1.5"
          />
          {yTicksLeft.map((tick, i) => (
            <g key={`tick-l-${i}`}>
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
          {/* Left Y-Axis Unit Label */}
          <text
            x={15}
            y={marginTop + plotHeight / 2}
            transform={`rotate(-90 15 ${marginTop + plotHeight / 2})`}
            textAnchor="middle"
            className="text-[11px] font-mono fill-orange-600 font-semibold"
          >
            {axisCompatibility?.leftUnit ? `[${axisCompatibility.leftUnit}]` : 'Value'}
          </text>

          {/* Right Y-Axis (If Dual Axis) */}
          {isDualAxis && (
            <>
              <line
                x1={width - marginRight}
                y1={marginTop}
                x2={width - marginRight}
                y2={marginTop + plotHeight}
                stroke="#818cf8"
                strokeWidth="1.5"
              />
              {yTicksRight.map((tick, i) => (
                <g key={`tick-r-${i}`}>
                  <line
                    x1={width - marginRight}
                    y1={tick.y}
                    x2={width - marginRight + 4}
                    y2={tick.y}
                    stroke="#a5b4fc"
                  />
                  <text
                    x={width - marginRight + 8}
                    y={tick.y + 3}
                    textAnchor="start"
                    className="text-[10px] fill-indigo-600 font-mono"
                  >
                    {tick.label}
                  </text>
                </g>
              ))}
              <text
                x={width - 15}
                y={marginTop + plotHeight / 2}
                transform={`rotate(90 ${width - 15} ${marginTop + plotHeight / 2})`}
                textAnchor="middle"
                className="text-[11px] font-mono fill-indigo-600 font-semibold"
              >
                {`[${axisCompatibility?.rightUnit}]`}
              </text>
            </>
          )}

          {/* Bottom X-Axis */}
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
          {/* Bottom X-Axis Label */}
          <text
            x={marginLeft + plotWidth / 2}
            y={height - 12}
            textAnchor="middle"
            className="text-[11px] font-mono fill-slate-700 font-semibold"
          >
            {timeAxis}
          </text>

          {/* Render Verified Experimental Event Markers */}
          {verifiedEvents && verifiedEvents.map((evt, idx) => {
            const rawTime = evt.timestamp_seconds ?? evt.time_seconds ?? evt.time_start_s ?? evt.time ?? evt.start_time;
            const evtTime = typeof rawTime === 'number' && !Number.isNaN(rawTime) ? rawTime : null;
            if (evtTime === null || evtTime < activeXMin || evtTime > activeXMax) return null;
            const px = scaleX(evtTime);
            const labelText = evt.event_name || evt.label || 'Event';
            const color = evt.color || '#10b981';
            return (
              <g key={`verified-event-${idx}`} className="group cursor-help">
                <line
                  x1={px}
                  y1={marginTop}
                  x2={px}
                  y2={marginTop + plotHeight}
                  stroke={color}
                  strokeWidth="1.8"
                  strokeDasharray="4 3"
                />
                <rect
                  x={px - 56}
                  y={marginTop + 6}
                  width={112}
                  height={20}
                  rx={4}
                  fill="#ecfdf5"
                  fillOpacity="0.95"
                  stroke={color}
                  strokeWidth="1"
                />
                <text
                  x={px}
                  y={marginTop + 19}
                  textAnchor="middle"
                  className="text-[10px] font-mono font-bold fill-emerald-800"
                >
                  ⚡ {labelText} ({evtTime.toFixed(1)}s)
                </text>
              </g>
            );
          })}

          {/* Render Sensor Channel Paths */}
          {selectedChannels.map((ch) => {
            if (hiddenChannelIds.includes(ch.id)) return null;
            const d = paths[ch.id];
            if (!d) return null;

            return (
              <path
                key={ch.id}
                d={d}
                fill="none"
                stroke={ch.color}
                strokeWidth="1.8"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            );
          })}

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

          {/* Hover Crosshair Line & Point Markers */}
          {hoveredPointInfo && hoveredPointInfo.px >= marginLeft && hoveredPointInfo.px <= width - marginRight && (
            <g>
              <line
                x1={hoveredPointInfo.px}
                y1={marginTop}
                x2={hoveredPointInfo.px}
                y2={marginTop + plotHeight}
                stroke="#94a3b8"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
              {hoveredPointInfo.channelValues.map((ch) => {
                if (hiddenChannelIds.includes(ch.id) || ch.py === null) return null;
                return (
                  <circle
                    key={`dot-${ch.id}`}
                    cx={hoveredPointInfo.px}
                    cy={ch.py}
                    r="4"
                    fill={ch.color}
                    stroke="#ffffff"
                    strokeWidth="1.5"
                  />
                );
              })}
            </g>
          )}
        </svg>

        {/* Floating Tooltip Box */}
        {hoveredPointInfo && (
          <div
            className="pointer-events-none absolute z-20 bg-white/95 border border-slate-200 rounded-xl p-3 shadow-xl backdrop-blur-md text-xs space-y-1.5 font-mono max-w-xs transition-all duration-75"
            style={{
              left: `${Math.min(
                width - 240,
                Math.max(20, (hoveredPointInfo.px / width) * 100)
              )}%`,
              top: '12px',
            }}
          >
            <div className="border-b border-slate-200 pb-1 text-slate-700 font-semibold flex items-center justify-between">
              <span>Time:</span>
              <span className="text-orange-600">{typeof hoveredPointInfo.time === 'number' ? hoveredPointInfo.time.toFixed(3) : '—'} s</span>
            </div>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {hoveredPointInfo.channelValues.map((ch) => {
                if (hiddenChannelIds.includes(ch.id)) return null;
                return (
                  <div key={`tip-${ch.id}`} className="flex items-center justify-between gap-3 text-[11px]">
                    <div className="flex items-center gap-1.5 truncate">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: ch.color }} />
                      <span className="text-slate-700 truncate" title={ch.label}>
                        {ch.label}
                      </span>
                    </div>
                    <span className="font-semibold text-slate-900 shrink-0">
                      {typeof ch.numericVal === 'number' && !Number.isNaN(ch.numericVal) ? `${ch.numericVal.toFixed(3)} ${ch.unit || ''}` : 'Missing/Gap'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Channel Legend & Visibility Toggles */}
      <div className="flex flex-wrap gap-2 pt-1">
        {selectedChannels.map((ch) => {
          const isHidden = hiddenChannelIds.includes(ch.id);
          const isRight = isDualAxis && rightChannelIds.includes(ch.id);

          return (
            <button
              key={`legend-${ch.id}`}
              onClick={() => toggleChannelVisibility(ch.id)}
              className={`flex items-center gap-2 px-2.5 py-1 rounded-lg text-xs font-mono border transition cursor-pointer ${
                isHidden
                  ? 'bg-slate-100 border-slate-200 text-slate-400 line-through opacity-60'
                  : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 shadow-xs'
              }`}
            >
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: isHidden ? '#cbd5e1' : ch.color }}
              />
              <span className="truncate max-w-[200px]" title={ch.label}>
                {ch.label}
              </span>
              <span className="text-[10px] text-slate-500 bg-slate-50 px-1.5 py-0.2 rounded border border-slate-200">
                {ch.unit} {isRight ? '(Right Axis)' : '(Left Axis)'}
              </span>
            </button>
          );
        })}
      </div>

      {/* Summary Statistics Table with Clearly Defined Analysis Interval */}
      <div className="bg-white border border-slate-200 rounded-xl p-3.5 space-y-3 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-b border-slate-200 pb-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-slate-900">Active Analysis Interval:</span>
            <span className="font-mono bg-slate-50 px-2 py-0.5 rounded text-orange-700 border border-slate-200 font-semibold">
              [{activeXMin.toFixed(2)}s – {activeXMax.toFixed(2)}s] (Δt = {(activeXMax - activeXMin).toFixed(2)}s)
            </span>
            {zoomRange && (
              <span className="text-[11px] font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
                Zoomed Analysis Interval
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setStatsScope(statsScope === 'interval' ? 'all' : 'interval')}
              className="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 cursor-pointer transition"
              title="Toggle statistics calculation scope between the active zoomed interval and the full loaded dataset"
            >
              Scope: {statsScope === 'interval' ? 'Active Interval Only' : 'Full Loaded Buffer'}
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono text-slate-700">
            <thead>
              <tr className="border-b border-slate-200 text-[10px] text-slate-500 uppercase tracking-wider">
                <th className="pb-1.5 pr-4">Channel</th>
                <th className="pb-1.5 px-3">Unit</th>
                <th className="pb-1.5 px-3">Min</th>
                <th className="pb-1.5 px-3">Max</th>
                <th className="pb-1.5 px-3">Mean</th>
                <th className="pb-1.5 px-3">Valid Readings</th>
                <th className="pb-1.5 pl-3 text-right">Data Gaps</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-[11px]">
              {channelStats.map((st) => (
                <tr key={`stat-${st.id}`} className="hover:bg-slate-50">
                  <td className="py-1.5 pr-4 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: st.color }} />
                    <span className="truncate max-w-[220px]" title={st.label}>
                      {st.label}
                    </span>
                  </td>
                  <td className="py-1.5 px-3 text-slate-500">{st.unit || '—'}</td>
                  <td className="py-1.5 px-3 text-amber-700 font-medium">
                    {typeof st.min === 'number' && !Number.isNaN(st.min) ? st.min.toFixed(2) : '—'}
                  </td>
                  <td className="py-1.5 px-3 text-rose-700 font-medium">
                    {typeof st.max === 'number' && !Number.isNaN(st.max) ? st.max.toFixed(2) : '—'}
                  </td>
                  <td className="py-1.5 px-3 text-emerald-700 font-medium">
                    {typeof st.mean === 'number' && !Number.isNaN(st.mean) ? st.mean.toFixed(2) : '—'}
                  </td>
                  <td className="py-1.5 px-3 text-slate-700">{st.validCount.toLocaleString()}</td>
                  <td className="py-1.5 pl-3 text-right">
                    {st.missingCount > 0 ? (
                      <span className="text-amber-700 font-semibold">{st.missingCount} gaps</span>
                    ) : (
                      <span className="text-slate-400">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
