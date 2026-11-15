import React from 'react';

/**
 * ComparisonStatsTable
 * Side-by-side descriptive statistics and empirical delta table.
 * Explicitly distinguishes calculations over the selected data window vs full dataset.
 */
export function ComparisonStatsTable({
  datasetAId,
  datasetBId,
  activeChannelObj,
  statsA,
  statsB,
  comparisonMetrics,
  recordsCountA,
  recordsCountB,
}) {
  if (!statsA || !statsB || !activeChannelObj) return null;

  const unit = activeChannelObj.unit || '';

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-3 font-mono text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
            Descriptive Measurement Statistics: {activeChannelObj.label}
          </span>
          <span className="text-[10px] text-orange-700 bg-orange-50 px-2 py-0.5 rounded border border-orange-200 font-semibold">
            [{unit}]
          </span>
        </div>

        <span className="text-[10px] text-slate-600 bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200">
          Scope: Active Window (A: {recordsCountA.toLocaleString()} pts, B: {recordsCountB.toLocaleString()} pts)
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-slate-700">
          <thead>
            <tr className="border-b border-slate-200 text-[10px] text-slate-500 uppercase tracking-wider">
              <th className="py-2 pr-4">Statistical Metric</th>
              <th className="py-2 px-3 text-orange-600">Dataset A ({datasetAId})</th>
              <th className="py-2 px-3 text-sky-600">Dataset B ({datasetBId})</th>
              <th className="py-2 pl-3 text-right">Delta (A − B)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-[11px]">
            {/* Peak Max Value */}
            <tr className="hover:bg-slate-50">
              <td className="py-2 pr-4 text-slate-800 font-medium">Maximum Recorded Peak</td>
              <td className="py-2 px-3 font-semibold text-slate-900">
                {statsA.max !== null ? `${statsA.max.toFixed(2)} ${unit}` : '—'}
              </td>
              <td className="py-2 px-3 font-semibold text-slate-900">
                {statsB.max !== null ? `${statsB.max.toFixed(2)} ${unit}` : '—'}
              </td>
              <td className="py-2 pl-3 text-right font-bold text-orange-600">
                {comparisonMetrics?.peakDiff !== null
                  ? `${comparisonMetrics.peakDiff > 0 ? '+' : ''}${comparisonMetrics.peakDiff.toFixed(2)} ${unit}`
                  : '—'}
              </td>
            </tr>

            {/* Time of Peak */}
            <tr className="hover:bg-slate-50">
              <td className="py-2 pr-4 text-slate-500">Time of Peak (t_max)</td>
              <td className="py-2 px-3 text-slate-700">
                {statsA.timeOfMax !== null ? `${statsA.timeOfMax.toFixed(2)} s` : '—'}
              </td>
              <td className="py-2 px-3 text-slate-700">
                {statsB.timeOfMax !== null ? `${statsB.timeOfMax.toFixed(2)} s` : '—'}
              </td>
              <td className="py-2 pl-3 text-right text-slate-500">
                {comparisonMetrics?.timeOfPeakOffset !== null
                  ? `${comparisonMetrics.timeOfPeakOffset > 0 ? '+' : ''}${comparisonMetrics.timeOfPeakOffset.toFixed(2)} s offset`
                  : '—'}
              </td>
            </tr>

            {/* Minimum Value */}
            <tr className="hover:bg-slate-50">
              <td className="py-2 pr-4 text-slate-800 font-medium">Minimum Recorded Value</td>
              <td className="py-2 px-3 text-slate-700">
                {statsA.min !== null ? `${statsA.min.toFixed(2)} ${unit}` : '—'}
              </td>
              <td className="py-2 px-3 text-slate-700">
                {statsB.min !== null ? `${statsB.min.toFixed(2)} ${unit}` : '—'}
              </td>
              <td className="py-2 pl-3 text-right text-slate-500">
                {statsA.min !== null && statsB.min !== null
                  ? `${(statsA.min - statsB.min > 0 ? '+' : '')}${(statsA.min - statsB.min).toFixed(2)} ${unit}`
                  : '—'}
              </td>
            </tr>

            {/* Arithmetic Mean */}
            <tr className="hover:bg-slate-50">
              <td className="py-2 pr-4 text-slate-800 font-medium">Arithmetic Mean Value</td>
              <td className="py-2 px-3 text-slate-700">
                {statsA.mean !== null ? `${statsA.mean.toFixed(2)} ${unit}` : '—'}
              </td>
              <td className="py-2 px-3 text-slate-700">
                {statsB.mean !== null ? `${statsB.mean.toFixed(2)} ${unit}` : '—'}
              </td>
              <td className="py-2 pl-3 text-right font-medium text-slate-800">
                {comparisonMetrics?.meanDiff !== null
                  ? `${comparisonMetrics.meanDiff > 0 ? '+' : ''}${comparisonMetrics.meanDiff.toFixed(2)} ${unit}`
                  : '—'}
              </td>
            </tr>

            {/* Net Start-to-End Change */}
            <tr className="hover:bg-slate-50">
              <td className="py-2 pr-4 text-slate-500">Net Window Change (End − Start)</td>
              <td className="py-2 px-3 text-slate-700">
                {statsA.startEndChange !== null
                  ? `${statsA.startEndChange > 0 ? '+' : ''}${statsA.startEndChange.toFixed(2)} ${unit}`
                  : '—'}
              </td>
              <td className="py-2 px-3 text-slate-700">
                {statsB.startEndChange !== null
                  ? `${statsB.startEndChange > 0 ? '+' : ''}${statsB.startEndChange.toFixed(2)} ${unit}`
                  : '—'}
              </td>
              <td className="py-2 pl-3 text-right text-slate-500">
                {comparisonMetrics?.deltaOfChange !== null
                  ? `${comparisonMetrics.deltaOfChange > 0 ? '+' : ''}${comparisonMetrics.deltaOfChange.toFixed(2)} ${unit}`
                  : '—'}
              </td>
            </tr>

            {/* Valid Data Points */}
            <tr className="hover:bg-slate-50">
              <td className="py-2 pr-4 text-slate-500">Valid Numeric Readings</td>
              <td className="py-2 px-3 text-emerald-700 font-semibold">
                {statsA.validCount.toLocaleString()} pts ({statsA.completenessPercent.toFixed(1)}%)
              </td>
              <td className="py-2 px-3 text-emerald-700 font-semibold">
                {statsB.validCount.toLocaleString()} pts ({statsB.completenessPercent.toFixed(1)}%)
              </td>
              <td className="py-2 pl-3 text-right text-slate-500">
                {(statsA.validCount - statsB.validCount).toLocaleString()} pts
              </td>
            </tr>

            {/* Missing Data Gaps */}
            <tr className="hover:bg-slate-50">
              <td className="py-2 pr-4 text-slate-500">Missing Measurements (Null/Gaps)</td>
              <td className="py-2 px-3">
                {statsA.missingCount > 0 ? (
                  <span className="text-amber-700 font-semibold">{statsA.missingCount} gaps</span>
                ) : (
                  <span className="text-slate-400">0</span>
                )}
              </td>
              <td className="py-2 px-3">
                {statsB.missingCount > 0 ? (
                  <span className="text-amber-700 font-semibold">{statsB.missingCount} gaps</span>
                ) : (
                  <span className="text-slate-400">0</span>
                )}
              </td>
              <td className="py-2 pl-3 text-right text-slate-500">
                {Math.abs(statsA.missingCount - statsB.missingCount)} difference
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
