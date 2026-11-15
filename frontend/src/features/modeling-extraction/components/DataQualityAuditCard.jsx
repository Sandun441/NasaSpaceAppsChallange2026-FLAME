import React, { useState } from 'react';

export function DataQualityAuditCard({ qualityReport }) {
  const [showAnomalyDetails, setShowAnomalyDetails] = useState(false);

  if (!qualityReport) return null;

  const completeness = qualityReport.data_completeness_pct ?? 100.0;
  const missingCounts = qualityReport.missing_counts || {};
  const constantCols = qualityReport.constant_columns || [];
  const leakageRisk = qualityReport.leakage_risk || 'UNKNOWN';
  const groupCol = qualityReport.group_split_column || 'run_id';
  const advice = qualityReport.leakage_advice || '';
  const warnings = qualityReport.warnings || [];
  const anomDetails = qualityReport.anomalous_records_details || [];
  const anomCount = qualityReport.anomalous_records_count || anomDetails.length;

  const totalAvailable = qualityReport.total_available_records ?? qualityReport.available_records_count;
  const filteredCount = qualityReport.filtered_records_count ?? qualityReport.extracted_records_count;
  const exportedCount = qualityReport.exported_records_count ?? filteredCount;
  const labeledCount = qualityReport.labeled_records_count;
  const completeCases = qualityReport.complete_case_records_count;

  const isHighRisk = leakageRisk.includes('HIGH');

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-orange-600">
            Scientific Data Quality & Leakage Audit
          </span>
          <h3 className="text-sm font-semibold text-slate-900">
            Population Accounting, Missing Values & Cross-Validation Safeguards
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-500">Completeness:</span>
          <span
            className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
              completeness >= 95
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : completeness >= 80
                ? 'bg-amber-50 text-amber-800 border-amber-200'
                : 'bg-rose-50 text-rose-800 border-rose-200'
            }`}
          >
            {completeness}%
          </span>
        </div>
      </div>

      {/* Population Taxonomy Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-center">
          <div className="text-[10px] font-mono text-slate-500 uppercase">Available</div>
          <div className="text-base font-bold font-mono text-slate-900 mt-0.5">{totalAvailable ?? '—'}</div>
          <div className="text-[9px] text-slate-500">raw source</div>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-center">
          <div className="text-[10px] font-mono text-slate-500 uppercase">Filtered</div>
          <div className="text-base font-bold font-mono text-orange-600 mt-0.5">{filteredCount ?? '—'}</div>
          <div className="text-[9px] text-slate-500">matching filters</div>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-center">
          <div className="text-[10px] font-mono text-slate-500 uppercase">Labeled</div>
          <div className="text-base font-bold font-mono text-orange-600 mt-0.5">{labeledCount ?? '—'}</div>
          <div className="text-[9px] text-slate-500">valid target</div>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-center">
          <div className="text-[10px] font-mono text-slate-500 uppercase">Complete Cases</div>
          <div className="text-base font-bold font-mono text-emerald-700 mt-0.5">{completeCases ?? '—'}</div>
          <div className="text-[9px] text-slate-500">zero missing</div>
        </div>
        <div className={`rounded-xl p-2.5 text-center border ${
          anomCount > 0 ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'
        }`}>
          <div className="text-[10px] font-mono text-amber-800 uppercase">Flagged Anomalies</div>
          <div className="text-base font-bold font-mono text-amber-700 mt-0.5">{anomCount}</div>
          <div className="text-[9px] text-slate-500">{anomCount > 0 ? 'source uncorrected' : 'none detected'}</div>
        </div>
      </div>

      {/* Anomaly Details Drawer / Table */}
      {anomCount > 0 && (
        <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-900 flex items-center gap-1.5">
              <span>⚠️ NASA PI Log Empirical Anomalies Disclosed ({anomCount} runs)</span>
            </span>
            <button
              type="button"
              onClick={() => setShowAnomalyDetails(!showAnomalyDetails)}
              className="text-[11px] font-mono text-amber-700 hover:text-amber-900 underline cursor-pointer"
            >
              {showAnomalyDetails ? 'Hide details' : 'Inspect flagged records'}
            </button>
          </div>
          <p className="text-[11px] text-amber-900/90 leading-relaxed font-sans">
            These values originate directly from the authoritative NASA PI flight logs (e.g., extreme ΔO₂ differences of +20.6% and -19.7 percentage points, or out-of-bounds fan potentiometer readings). They are preserved verbatim to maintain flight provenance, but flagged so researchers can exclude them using the filter toggle.
          </p>

          {showAnomalyDetails && (
            <div className="overflow-x-auto max-h-[180px] overflow-y-auto mt-2 border border-amber-200 rounded-lg">
              <table className="w-full text-left text-[11px] font-mono">
                <thead className="bg-amber-100 text-amber-900 sticky top-0">
                  <tr>
                    <th className="px-2.5 py-1.5">Run</th>
                    <th className="px-2.5 py-1.5">Anomaly Type</th>
                    <th className="px-2.5 py-1.5">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-amber-200 text-slate-800 bg-white">
                  {anomDetails.map((a, i) => (
                    <tr key={i} className="hover:bg-amber-50">
                      <td className="px-2.5 py-1.5 font-bold text-orange-600">{a.run_id}</td>
                      <td className="px-2.5 py-1.5 text-amber-800">{a.type}</td>
                      <td className="px-2.5 py-1.5 text-slate-600 font-sans text-[11px]">{a.details}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left: Leakage Risk & Group-aware Split Guidance */}
        <div
          className={`p-3.5 rounded-xl border space-y-2 ${
            isHighRisk
              ? 'bg-rose-50 border-rose-200'
              : 'bg-slate-50 border-slate-200'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
              <span>🛡️ Leakage Risk:</span>
              <span
                className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded ${
                  isHighRisk
                    ? 'bg-rose-100 text-rose-800 border border-rose-300'
                    : 'bg-amber-100 text-amber-800 border border-amber-300'
                }`}
              >
                {leakageRisk}
              </span>
            </span>

            <span className="text-[11px] font-mono text-slate-500">
              Split on: <strong className="text-orange-600">{groupCol}</strong>
            </span>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed font-sans">
            {advice}
          </p>

          <div className="text-[11px] font-mono text-slate-600 bg-white p-2 rounded-lg border border-slate-200">
            <strong>Mandatory Protocol:</strong> Use <code>GroupKFold(groups=df['{groupCol}'])</code>. Never perform uniform random train/test splits on correlated microgravity runs.
          </div>
        </div>

        {/* Right: Missing Values & Constant Columns */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
          <span className="text-xs font-semibold text-slate-900 block">
            Column Completeness & Variance
          </span>

          {/* Missing Counts Summary */}
          <div className="space-y-1 max-h-[100px] overflow-y-auto pr-1 text-xs font-mono">
            {Object.entries(missingCounts).map(([col, cnt]) => {
              const hasMissing = cnt > 0;
              return (
                <div
                  key={col}
                  className="flex items-center justify-between text-[11px] py-0.5 border-b border-slate-200"
                >
                  <span className={hasMissing ? 'text-amber-800 font-medium' : 'text-slate-600'}>
                    {col}
                  </span>
                  <span className={hasMissing ? 'text-amber-700 font-bold' : 'text-slate-400'}>
                    {cnt} missing
                  </span>
                </div>
              );
            })}
          </div>

          {/* Constant Columns Warning */}
          {constantCols.length > 0 && (
            <div className="text-[11px] text-amber-900 bg-amber-50 p-2 rounded border border-amber-200">
              ⚠️ Zero-variance columns detected: <strong>{constantCols.join(', ')}</strong>. Drop before linear regression or PCA.
            </div>
          )}

          {/* Other Warnings */}
          {warnings.length > 0 && (
            <div className="space-y-1">
              {warnings.map((w, idx) => (
                <p key={idx} className="text-[11px] text-slate-600 leading-tight">
                  • {w}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
