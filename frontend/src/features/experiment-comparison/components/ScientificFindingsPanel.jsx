import React from 'react';

/**
 * ScientificFindingsPanel
 * Scientific analysis summary clearly dividing:
 * 1. Directly observed numerical differences
 * 2. Calculated descriptive statistics
 * 3. Possible scientific interpretations (combustion physics context)
 * 4. Data limitations & scientific validation safeguards
 */
export function ScientificFindingsPanel({
  datasetAId,
  datasetBId,
  datasetAInfo,
  datasetBInfo,
  activeChannelObj,
  statsA,
  statsB,
  comparisonMetrics,
  isEventAligned,
  ignitionTimeA,
  ignitionTimeB,
}) {
  if (!activeChannelObj || !statsA || !statsB || !comparisonMetrics) return null;

  const unit = activeChannelObj.unit || '';
  const channelLabel = activeChannelObj.label;

  // Peak analysis
  const peakDiff = comparisonMetrics.peakDiff;
  const higherDataset = peakDiff !== null ? (peakDiff > 0 ? datasetAId : datasetBId) : null;
  const absPeakDiff = comparisonMetrics.absPeakDiff;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-5">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-900 tracking-tight flex items-center gap-2">
            <span>🔬 Scientific Comparison Findings</span>
            <span className="text-[10px] font-mono text-orange-700 bg-orange-50 px-2 py-0.5 rounded border border-orange-200 font-semibold">
              {channelLabel}
            </span>
          </span>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500">
          <span>Sources: {datasetAInfo?.source_file || datasetAId} vs {datasetBInfo?.source_file || datasetBId}</span>
        </div>
      </div>

      {/* 4 Strict Scientific Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Section 1: Directly Observed Numerical Differences */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold text-orange-700">
            <span>1. Directly Observed Numerical Differences</span>
          </div>
          <ul className="text-xs font-mono text-slate-700 space-y-1.5 list-disc list-inside">
            <li>
              Peak recorded {channelLabel}: <strong className="text-slate-900">{statsA.max !== null ? statsA.max.toFixed(2) : '—'} {unit}</strong> (in {datasetAId}) vs <strong className="text-slate-900">{statsB.max !== null ? statsB.max.toFixed(2) : '—'} {unit}</strong> (in {datasetBId}).
            </li>
            {peakDiff !== null && (
              <li>
                Empirical peak delta: <strong className="text-orange-600">{higherDataset}</strong> recorded a maximum reading <strong className="text-slate-900">{absPeakDiff.toFixed(2)} {unit}</strong> higher than the comparison sample.
              </li>
            )}
            {isEventAligned && ignitionTimeA !== null && ignitionTimeB !== null && (
              <li>
                Ignition onset baseline: Igniter energization occurred at <strong className="text-slate-900">{ignitionTimeA.toFixed(2)}s</strong> in {datasetAId} and <strong className="text-slate-900">{ignitionTimeB.toFixed(2)}s</strong> in {datasetBId} (pre-ignition baseline difference: {Math.abs(ignitionTimeA - ignitionTimeB).toFixed(2)}s).
              </li>
            )}
            <li>
              Sensor availability: {datasetAId} has <strong className="text-slate-900">{statsA.missingCount}</strong> missing readings; {datasetBId} has <strong className="text-slate-900">{statsB.missingCount}</strong> missing readings in the current window.
            </li>
          </ul>
        </div>

        {/* Section 2: Calculated Descriptive Statistics */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold text-sky-700">
            <span>2. Calculated Descriptive Statistics</span>
          </div>
          <ul className="text-xs font-mono text-slate-700 space-y-1.5 list-disc list-inside">
            <li>
              Arithmetic mean across active window: <strong className="text-slate-900">{statsA.mean !== null ? statsA.mean.toFixed(2) : '—'} {unit}</strong> vs <strong className="text-slate-900">{statsB.mean !== null ? statsB.mean.toFixed(2) : '—'} {unit}</strong> (mean offset: {comparisonMetrics.meanDiff !== null ? `${comparisonMetrics.meanDiff.toFixed(2)} ${unit}` : '—'}).
            </li>
            <li>
              Recorded time of peak: <strong className="text-slate-900">{statsA.timeOfMax !== null ? `${statsA.timeOfMax.toFixed(2)}s` : '—'}</strong> in A vs <strong className="text-slate-900">{statsB.timeOfMax !== null ? `${statsB.timeOfMax.toFixed(2)}s` : '—'}</strong> in B (time-to-peak difference: {comparisonMetrics.timeOfPeakOffset !== null ? `${Math.abs(comparisonMetrics.timeOfPeakOffset).toFixed(2)}s` : '—'}).
            </li>
            <li>
              Net window evolution: ΔA = <strong className="text-slate-900">{statsA.startEndChange !== null ? `${statsA.startEndChange.toFixed(2)} ${unit}` : '—'}</strong>; ΔB = <strong className="text-slate-900">{statsB.startEndChange !== null ? `${statsB.startEndChange.toFixed(2)} ${unit}` : '—'}</strong>.
            </li>
            <li className="text-[11px] text-slate-500">
              Note: Descriptive calculations are computed over the loaded window buffer and are unaffected by visualization downsampling.
            </li>
          </ul>
        </div>

        {/* Section 3: Possible Scientific Interpretations */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold text-emerald-700">
            <span>3. Microgravity Combustion Interpretations</span>
          </div>
          <div className="text-xs text-slate-700 space-y-1.5 leading-relaxed font-sans">
            <p>
              In buoyant terrestrial environments, natural convection removes hot combustion products rapidly. In microgravity (Saffire flow duct), transport is governed strictly by forced ventilation and thermal radiation.
            </p>
            <p className="text-[11px] text-slate-500 font-mono">
              Observed temperature or heat flux differences between samples may reflect variations in:
            </p>
            <ul className="text-[11px] font-mono text-slate-600 space-y-1 list-disc list-inside">
              <li>Fuel substrate dimensions, surface area, and chemical composition.</li>
              <li>Forced airflow velocity across the sample surface (Anemometer 1 & 2).</li>
              <li>Radiative thermal feedback and flame stabilization distance.</li>
            </ul>
          </div>
        </div>

        {/* Section 4: Data Limitations & Validation Status */}
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-semibold text-rose-800">
            <span>4. Limitations & Scientific Safeguards</span>
          </div>
          <div className="text-xs text-rose-900 space-y-2 font-mono">
            <div className="bg-white border border-rose-200 p-2.5 rounded-lg space-y-1 text-[11px]">
              <strong>STRICT NASA FLAME SAFEGUARDS:</strong>
              <p>
                • <strong>Correlation is not causation:</strong> Divergent sensor traces reflect complex multi-physics coupling and must not be interpreted as a simple linear effect.
              </p>
              <p>
                • <strong>No automated safety conclusions:</strong> NASA FLAME does not declare a fuel material &quot;safer&quot; based solely on peak thermocouple temperatures.
              </p>
              <p>
                • <strong>Validation status:</strong> Both datasets carry scientific validation status <span className="underline">{datasetAInfo?.scientific_validation || 'pending'}</span> and <span className="underline">{datasetBInfo?.scientific_validation || 'pending'}</span>. Raw uncalibrated channels require manual investigator screening.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
