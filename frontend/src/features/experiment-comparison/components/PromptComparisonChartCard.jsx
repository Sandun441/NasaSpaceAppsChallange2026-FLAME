import React, { useState, useMemo } from 'react';
import { OverlayComparisonChart } from './OverlayComparisonChart';
import { flameApi } from '../../../services/flameApi';

/**
 * PromptComparisonChartCard
 * Renders units-decoupled comparative scientific charts derived from natural-language prompts.
 * Supports dual-dataset continuous time series (Saffire-III) and discrete experiment matrices (BASS-II).
 * Complies with Phase F3 Step 4 UX layout and Step 6 scientific audit requirements.
 */
export function PromptComparisonChartCard({ chart, datasetAId, datasetBId, idx = 0 }) {
  const isScatter = chart.chart_type === 'scatter';
  const [alignmentMode, setAlignmentMode] = useState('overlay_recorded');

  const recordsA = chart.series_data?.sample1_points || chart.series_data?.points || [];
  const recordsB = chart.series_data?.sample2_points || [];

  const channelId = chart.channel_ids?.[0] || 'Radiometer 1';
  const activeChannelObj = useMemo(
    () => ({
      id: channelId,
      label: chart.title || channelId,
      unit: chart.y_units || 'a.u.',
    }),
    [channelId, chart.title, chart.y_units]
  );

  // Extract ignition times from event markers if available
  const ignitionA = useMemo(() => {
    const ev = (chart.event_markers || []).find(
      (m) => m.event_name && (m.event_name.includes('Sample 1') || m.event_name.includes(datasetAId))
    );
    return ev ? ev.time_start_s : 60.03;
  }, [chart.event_markers, datasetAId]);

  const ignitionB = useMemo(() => {
    const ev = (chart.event_markers || []).find(
      (m) => m.event_name && (m.event_name.includes('Sample 2') || m.event_name.includes(datasetBId))
    );
    return ev ? ev.time_start_s : 22.0;
  }, [chart.event_markers, datasetBId]);

  // Scatter plot points for discrete matrix comparison (BASS-II)
  const scatterPoints = chart.series_data?.points || [];

  return (
    <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-3 flex flex-col justify-between shadow-sm">
      {/* Chart Header */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2 pb-2 border-b border-slate-200">
          <div>
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span>{chart.title}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-orange-600">
                {chart.y_units}
              </span>
            </h4>
            {chart.subtitle && (
              <p className="text-[11px] font-mono text-slate-500 mt-0.5">{chart.subtitle}</p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2 font-mono text-[10px]">
            {!isScatter && (
              <div className="flex items-center bg-slate-100 border border-slate-200 rounded-lg p-0.5">
                <button
                  onClick={() => setAlignmentMode('overlay_recorded')}
                  className={`px-2 py-0.5 rounded transition cursor-pointer ${
                    alignmentMode === 'overlay_recorded'
                      ? 'bg-white text-orange-600 font-semibold border border-orange-300 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Absolute Time
                </button>
                <button
                  onClick={() => setAlignmentMode('overlay_event_aligned')}
                  className={`px-2 py-0.5 rounded transition cursor-pointer ${
                    alignmentMode === 'overlay_event_aligned'
                      ? 'bg-white text-orange-600 font-semibold border border-orange-300 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                  title="Align time axis to t0 = ignition start"
                >
                  Ignition-Aligned (t₀=0s)
                </button>
              </div>
            )}
            <span className="bg-slate-50 px-2 py-0.5 rounded border border-slate-200 text-slate-600">
              {chart.data_resolution}
            </span>
          </div>
        </div>

        {/* Step 6 Baseline Offset Scientific Disclosure Alert */}
        {chart.missing_data_notices && chart.missing_data_notices.length > 0 && (
          <div className="mb-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-[11px] font-mono text-amber-900 flex items-start gap-2">
            <span className="text-amber-800 font-bold">ℹ Sensor Calibration Note:</span>
            <div className="space-y-0.5">
              {chart.missing_data_notices.map((n, i) => (
                <p key={i}>{n}</p>
              ))}
            </div>
          </div>
        )}

        {/* Mode 1: Continuous Time-Series Dual Comparison (OverlayComparisonChart) */}
        {!isScatter && (
          <div className="relative">
            {recordsA.length > 0 && recordsB.length > 0 ? (
              <OverlayComparisonChart
                datasetAId={datasetAId || chart.dataset_id}
                datasetBId={datasetBId || 'saffire_iii_sample_2'}
                recordsA={recordsA}
                recordsB={recordsB}
                timeAxisA="time"
                timeAxisB="time"
                activeChannelObj={activeChannelObj}
                alignmentMode={alignmentMode}
                ignitionTimeA={ignitionA}
                ignitionTimeB={ignitionB}
                enableDownsampling={true}
              />
            ) : (
              <div className="p-8 text-center text-xs font-mono text-slate-500 bg-slate-50 border border-slate-200 rounded-lg">
                No comparative records available for this channel.
              </div>
            )}
          </div>
        )}

        {/* Mode 2: Discrete Experiment Matrix Scatter Plot (BASS-II Parameter Space) */}
        {isScatter && (
          <div className="space-y-3">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between mb-3 text-xs font-mono">
                <span className="text-slate-800 font-semibold">
                  Flammability Corridor: Initial O₂ vs Airflow Velocity Display Proxy
                </span>
                <span className="text-slate-500">
                  {scatterPoints.length} Validated Flight Points
                </span>
              </div>

              {/* Responsive SVG Scatter Plot */}
              <div className="relative overflow-x-auto">
                <svg
                  viewBox="0 0 760 340"
                  className="w-full h-auto max-h-[340px] select-none font-mono text-[10px]"
                >
                  {/* Grid Lines */}
                  {[0, 5, 10, 15, 20, 25, 30].map((flow, i) => {
                    const x = 50 + (flow / 30) * 660;
                    return (
                      <g key={i}>
                        <line x1={x} y1={20} x2={x} y2={280} stroke="#e2e8f0" strokeDasharray="3 3" />
                        <text x={x} y={300} textAnchor="middle" fill="#94a3b8">{flow}</text>
                      </g>
                    );
                  })}
                  {[15, 18, 20, 22, 25].map((o2, i) => {
                    const y = 280 - ((o2 - 15) / 10) * 260;
                    return (
                      <g key={i}>
                        <line x1={50} y1={y} x2={710} y2={y} stroke="#e2e8f0" strokeDasharray="3 3" />
                        <text x={42} y={y + 3} textAnchor="end" fill="#94a3b8">{o2}%</text>
                      </g>
                    );
                  })}

                  {/* Axes */}
                  <line x1={50} y1={280} x2={710} y2={280} stroke="#cbd5e1" strokeWidth="1.5" />
                  <line x1={50} y1={20} x2={50} y2={280} stroke="#cbd5e1" strokeWidth="1.5" />

                  {/* Axis Labels */}
                  <text x={380} y={325} textAnchor="middle" fill="#64748b" className="font-semibold text-xs">
                    Airflow Velocity Display Proxy (cm/s)
                  </text>
                  <text
                    x={-150}
                    y={16}
                    textAnchor="middle"
                    fill="#64748b"
                    transform="rotate(-90)"
                    className="font-semibold text-xs"
                  >
                    Initial Oxygen Concentration (% vol)
                  </text>

                  {/* Scatter Data Points */}
                  {scatterPoints.map((pt, i) => {
                    const flow = Math.min(30, Math.max(0, pt.air_display_proxy || 0));
                    const o2 = Math.min(25, Math.max(15, pt.initial_o2_pct || 15));
                    const cx = 50 + (flow / 30) * 660;
                    const cy = 280 - ((o2 - 15) / 10) * 260;
                    const isCotton = pt.material_family === 'Cotton/SIBAL';
                    const isPmma = pt.material_family === 'PMMA';
                    const fill = isCotton ? '#f59e0b' : isPmma ? '#0284c7' : '#a855f7';

                    return (
                      <g key={i} className="hover:opacity-100 transition-opacity">
                        <circle
                          cx={cx}
                          cy={cy}
                          r={6}
                          fill={fill}
                          fillOpacity="0.8"
                          stroke="#ffffff"
                          strokeWidth="1.5"
                          className="cursor-pointer"
                        >
                          <title>
                            {`Test #${pt.test_no}: ${pt.material}\nInitial O₂: ${pt.initial_o2_pct}%\nAirflow Proxy: ${pt.air_display_proxy} cm/s`}
                          </title>
                        </circle>
                      </g>
                    );
                  })}
                </svg>
              </div>

              {/* Scatter Legend */}
              <div className="flex flex-wrap items-center justify-center gap-6 mt-3 pt-3 border-t border-slate-200 text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-sky-500" />
                  <span className="text-slate-700">PMMA Cylinders / Rods</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-orange-500" />
                  <span className="text-slate-700">Cotton / SIBAL Fabric</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-purple-500" />
                  <span className="text-slate-700">Nomex Polymer</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chart Footer with Provenance */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-200 text-[10px] font-mono text-slate-500">
        <span>Provenance: {chart.provenance}</span>
        <span className="text-slate-600">
          {isScatter
            ? `${scatterPoints.length} Matrix Runs`
            : `${recordsA.length} vs ${recordsB.length} Telemetry Points`}
        </span>
      </div>
    </div>
  );
}
