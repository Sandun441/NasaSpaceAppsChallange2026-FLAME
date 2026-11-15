import React, { useState, useMemo } from 'react';

/**
 * NASA BASS-II Discrete Experiment Matrix Visualizer
 *
 * Dedicated visualization for discrete ISS microgravity combustion test runs.
 * DOES NOT force discrete test matrices into a continuous time-series.
 * Provides multi-variable parameter comparison, gas consumption metrics, and material correlation.
 */
export function ExperimentMatrixChart({ records = [] }) {
  const [metricKey, setMetricKey] = useState('oxygen');
  const [selectedMaterial, setSelectedMaterial] = useState('ALL');
  const [hoveredTest, setHoveredTest] = useState(null);
  const [viewMode, setViewMode] = useState('delta'); // 'delta' or 'comparison'

  // Metric configurations
  const METRIC_CONFIGS = {
    oxygen: {
      label: 'Oxygen Consumption (O₂ % by vol)',
      initialCol: 'calibrated  initial O2 % by vol ',
      finalCol: 'calibrated final O2 % by vol',
      unit: '% vol',
      colorInit: '#38bdf8',
      colorFinal: '#f97316',
      deltaLabel: 'Net O₂ Consumed (Initial - Final)',
      deltaColor: '#ef4444',
      isDecrease: true,
    },
    co2: {
      label: 'Carbon Dioxide Evolution (CO₂ % by vol)',
      initialCol: 'Initial CO2 % by vol',
      finalCol: 'Final CO2 % by vol',
      unit: '% vol',
      colorInit: '#94a3b8',
      colorFinal: '#10b981',
      deltaLabel: 'Net CO₂ Produced (Final - Initial)',
      deltaColor: '#10b981',
      isDecrease: false,
    },
    co: {
      label: 'Carbon Monoxide Generation (CO ppm)',
      initialCol: 'Initial CO (ppm)',
      finalCol: 'Final CO (ppm)',
      unit: 'ppm',
      colorInit: '#fbbf24',
      colorFinal: '#f59e0b',
      deltaLabel: 'Net CO Produced (Final - Initial)',
      deltaColor: '#f59e0b',
      isDecrease: false,
    },
    frames: {
      label: 'High-Speed Video Frames Shot',
      initialCol: null,
      finalCol: 'total frames shot',
      unit: 'frames',
      colorInit: null,
      colorFinal: '#8b5cf6',
      deltaLabel: 'Total Video Frames',
      deltaColor: '#8b5cf6',
      isDecrease: false,
    },
  };

  const activeMetric = METRIC_CONFIGS[metricKey];

  // Distinct Materials list for filter
  const materialsList = useMemo(() => {
    const set = new Set();
    records.forEach((r) => {
      if (r.Material && r.Material.trim()) {
        set.add(r.Material.trim());
      }
    });
    return Array.from(set).sort();
  }, [records]);

  // Filtered & Parsed Test Data
  const parsedTests = useMemo(() => {
    return records
      .filter((r) => {
        if (selectedMaterial === 'ALL') return true;
        return (r.Material || '').trim() === selectedMaterial;
      })
      .map((r, idx) => {
        const testNo = r['Test no.'] || `Test-${idx + 1}`;
        const material = r.Material || 'Unspecified Material';
        const flowRestrictor = r['Flow restrictor'] || 'N/A';

        const rawInit = activeMetric.initialCol ? r[activeMetric.initialCol] : null;
        const rawFinal = r[activeMetric.finalCol];

        const initVal = rawInit !== null && rawInit !== '' && rawInit !== undefined ? parseFloat(rawInit) : null;
        const finalVal = rawFinal !== null && rawFinal !== '' && rawFinal !== undefined ? parseFloat(rawFinal) : null;

        let delta = null;
        if (initVal !== null && finalVal !== null && !Number.isNaN(initVal) && !Number.isNaN(finalVal)) {
          delta = activeMetric.isDecrease ? initVal - finalVal : finalVal - initVal;
        } else if (metricKey === 'frames' && finalVal !== null && !Number.isNaN(finalVal)) {
          delta = finalVal;
        }

        return {
          testNo,
          material,
          flowRestrictor,
          initVal: initVal !== null && !Number.isNaN(initVal) ? initVal : null,
          finalVal: finalVal !== null && !Number.isNaN(finalVal) ? finalVal : null,
          delta,
        };
      });
  }, [records, selectedMaterial, activeMetric, metricKey]);

  // Min / Max for Bar Scaling
  const { maxDelta, maxVal } = useMemo(() => {
    let mDelta = 0;
    let mVal = 0;

    parsedTests.forEach((t) => {
      if (t.delta !== null && t.delta > mDelta) mDelta = t.delta;
      if (t.initVal !== null && t.initVal > mVal) mVal = t.initVal;
      if (t.finalVal !== null && t.finalVal > mVal) mVal = t.finalVal;
    });

    return {
      maxDelta: mDelta > 0 ? mDelta : 1,
      maxVal: mVal > 0 ? mVal : 1,
    };
  }, [parsedTests]);

  return (
    <div className="space-y-5">
      {/* Scientific Distinction Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs font-mono text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-semibold text-amber-800">
          <span>🔬</span>
          <span>BASS-II Discrete Microgravity Test Matrix</span>
        </div>
        <p className="text-[11px] text-slate-700 leading-relaxed">
          This dataset contains 129 discrete microgravity combustion tests conducted inside the Microgravity Science Glovebox (MSG) on the ISS. Each record represents an independent burn test across diverse solid fuel samples and air flows.
        </p>
      </div>

      {/* Control Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white border border-slate-200 p-3.5 rounded-xl text-xs shadow-sm">
        {/* Metric Selector */}
        <div className="flex items-center gap-2">
          <span className="text-slate-500 font-mono">Parameter:</span>
          <select
            value={metricKey}
            onChange={(e) => setMetricKey(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-slate-800 rounded-lg px-2.5 py-1 text-xs font-mono focus:border-orange-500 outline-none cursor-pointer"
          >
            <option value="oxygen">O₂ Consumption (Initial vs Final %)</option>
            <option value="co2">CO₂ Evolution (% by vol)</option>
            <option value="co">CO Generation (ppm)</option>
            <option value="frames">High-Speed Video Frames</option>
          </select>
        </div>

        {/* Material Filter */}
        <div className="flex items-center gap-2">
          <span className="text-slate-500 font-mono">Fuel Material:</span>
          <select
            value={selectedMaterial}
            onChange={(e) => setSelectedMaterial(e.target.value)}
            className="bg-slate-50 border border-slate-200 text-slate-800 rounded-lg px-2.5 py-1 text-xs font-mono focus:border-orange-500 outline-none max-w-xs cursor-pointer truncate"
          >
            <option value="ALL">All Materials ({records.length} Tests)</option>
            {materialsList.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        {/* View Mode Toggle */}
        {activeMetric.initialCol && (
          <div className="flex items-center rounded-lg bg-slate-100 border border-slate-200 p-0.5">
            <button
              onClick={() => setViewMode('delta')}
              className={`px-2.5 py-1 text-[11px] font-mono rounded cursor-pointer transition ${
                viewMode === 'delta'
                  ? 'bg-white text-orange-600 font-semibold border border-orange-300 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Net Delta Bar
            </button>
            <button
              onClick={() => setViewMode('comparison')}
              className={`px-2.5 py-1 text-[11px] font-mono rounded cursor-pointer transition ${
                viewMode === 'comparison'
                  ? 'bg-white text-orange-600 font-semibold border border-orange-300 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Initial vs Final
            </button>
          </div>
        )}
      </div>

      {/* Bar Chart Visualization */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-3">
        <div className="flex items-center justify-between text-xs font-mono text-slate-600 border-b border-slate-200 pb-2">
          <span>{activeMetric.label}</span>
          <span>Showing {parsedTests.length} tests</span>
        </div>

        {/* Scrollable Bar Canvas */}
        <div className="overflow-x-auto pb-2">
          <div
            className="flex items-end gap-1.5 h-64 pt-6 px-2 min-w-full"
            style={{ width: `${Math.max(800, parsedTests.length * 28)}px` }}
          >
            {parsedTests.map((t, idx) => {
              const heightPercent =
                viewMode === 'delta'
                  ? t.delta !== null
                    ? Math.max(3, (t.delta / maxDelta) * 100)
                    : 0
                  : t.finalVal !== null
                  ? Math.max(3, (t.finalVal / maxVal) * 100)
                  : 0;

              const initHeightPercent =
                viewMode === 'comparison' && t.initVal !== null
                  ? Math.max(3, (t.initVal / maxVal) * 100)
                  : 0;

              return (
                <div
                  key={`bar-${t.testNo}-${idx}`}
                  className="flex flex-col items-center flex-1 h-full justify-end group relative cursor-pointer"
                  onMouseEnter={() => setHoveredTest(t)}
                  onMouseLeave={() => setHoveredTest(null)}
                >
                  {/* Bars container */}
                  <div className="w-full flex items-end justify-center gap-0.5 h-full">
                    {viewMode === 'comparison' && activeMetric.initialCol && (
                      <div
                        className="w-1/2 rounded-t transition-all group-hover:brightness-110"
                        style={{
                          height: `${initHeightPercent}%`,
                          backgroundColor: activeMetric.colorInit,
                        }}
                      />
                    )}
                    <div
                      className={`${viewMode === 'comparison' && activeMetric.initialCol ? 'w-1/2' : 'w-full'} rounded-t transition-all group-hover:brightness-110`}
                      style={{
                        height: `${heightPercent}%`,
                        backgroundColor:
                          viewMode === 'delta' ? activeMetric.deltaColor : activeMetric.colorFinal,
                      }}
                    />
                  </div>

                  {/* Test label below bar */}
                  <span className="text-[9px] font-mono text-slate-400 group-hover:text-orange-600 mt-1 truncate max-w-full">
                    {t.testNo.replace(/^B/, '')}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Hovered Test Details Panel */}
        {hoveredTest && (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs font-mono text-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-sm animate-in fade-in duration-100">
            <div>
              <span className="text-orange-600 font-semibold text-sm">
                Test {hoveredTest.testNo}
              </span>
              <span className="text-slate-500 ml-2">Material: {hoveredTest.material}</span>
              <span className="text-slate-500 ml-2">(Flow Restrictor: {hoveredTest.flowRestrictor})</span>
            </div>

            <div className="flex items-center gap-4 text-[11px]">
              {hoveredTest.initVal !== null && (
                <div>
                  <span className="text-slate-500">Initial:</span>{' '}
                  <span className="text-sky-600 font-medium">
                    {hoveredTest.initVal} {activeMetric.unit}
                  </span>
                </div>
              )}
              {hoveredTest.finalVal !== null && (
                <div>
                  <span className="text-slate-500">Final:</span>{' '}
                  <span className="text-orange-600 font-medium">
                    {hoveredTest.finalVal} {activeMetric.unit}
                  </span>
                </div>
              )}
              {hoveredTest.delta !== null && (
                <div className="bg-white px-2 py-0.5 rounded border border-slate-200">
                  <span className="text-slate-500">Net Delta:</span>{' '}
                  <span className="text-rose-600 font-bold">
                    {hoveredTest.delta.toFixed(2)} {activeMetric.unit}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
