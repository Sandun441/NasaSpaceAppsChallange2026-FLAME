import React from 'react';

export function DatasetSelectorCards({
  datasets,
  evaluations = [],
  activeDatasetId,
  onSelectDataset,
}) {
  if (!datasets || datasets.length === 0) return null;

  // Build evaluation lookup
  const evalMap = {};
  evaluations.forEach((e) => {
    evalMap[e.dataset_id] = e;
  });

  const suitabilityBadges = {
    ELIGIBLE_SUPERVISED: {
      label: 'Eligible for Supervised ML',
      cls: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      dot: 'bg-emerald-500',
    },
    EXPLORATORY_ONLY: {
      label: 'Exploratory Features Only',
      cls: 'bg-sky-50 text-sky-800 border-sky-200',
      dot: 'bg-sky-500',
    },
    TARGET_UNAVAILABLE: {
      label: 'Target Uninstrumented',
      cls: 'bg-rose-50 text-rose-800 border-rose-200',
      dot: 'bg-rose-500',
    },
    INCOMPATIBLE_OBJECTIVE: {
      label: 'Incompatible Objective',
      cls: 'bg-slate-100 text-slate-600 border-slate-200',
      dot: 'bg-slate-400',
    },
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-2">
          <span>NASA Experimental Datasets</span>
          <span className="text-slate-500 font-normal">({datasets.length} evaluated)</span>
        </h3>
        <span className="text-[11px] text-slate-500">
          Select dataset to configure features, filters, and export
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {datasets.map((ds) => {
          const isSelected = activeDatasetId === ds.dataset_id;
          const evaluation = evalMap[ds.dataset_id];
          const suitability = evaluation?.suitability || 'EXPLORATORY_ONLY';
          const badge = suitabilityBadges[suitability] || suitabilityBadges.EXPLORATORY_ONLY;

          return (
            <div
              key={ds.dataset_id}
              onClick={() => onSelectDataset(ds.dataset_id)}
              className={`p-4 rounded-xl border text-left transition-all cursor-pointer relative flex flex-col justify-between ${
                isSelected
                  ? 'bg-orange-50/40 border-orange-400 ring-1 ring-orange-400/40 shadow-sm'
                  : 'bg-white hover:bg-slate-50 border-slate-200 hover:border-slate-300 shadow-xs'
              }`}
            >
              <div>
                {/* Header: Paradigm & Suitability */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700">
                    {ds.paradigm === 'tabular_run_level'
                      ? 'Tabular Runs'
                      : ds.paradigm === 'time_series_telemetry'
                      ? '30.3 Hz Telemetry'
                      : 'Spacecraft Telemetry'}
                  </span>

                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${badge.cls}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                    {badge.label}
                  </span>
                </div>

                {/* Name & Investigation */}
                <h4 className="text-sm font-semibold text-slate-900 group-hover:text-orange-600 line-clamp-1 mb-1">
                  {ds.name}
                </h4>
                <p className="text-xs text-slate-500 font-mono mb-2">
                  {ds.investigation} • {ds.facility || ds.vehicle || 'Microgravity'}
                </p>

                {/* Records & Features Count */}
                <div className="flex items-center gap-3 text-xs text-slate-700 font-mono py-1.5 px-2 rounded-lg bg-slate-50 border border-slate-200 mb-2">
                  <span>
                    <strong className="text-orange-600">{ds.total_records?.toLocaleString()}</strong> records
                  </span>
                  <span>•</span>
                  <span>
                    <strong className="text-slate-800">{ds.feature_count}</strong> features
                  </span>
                  <span>•</span>
                  <span>
                    <strong className="text-emerald-700">{ds.target_count}</strong> targets
                  </span>
                </div>

                {/* Suitability explanation or target status */}
                {evaluation?.scientific_explanation && (
                  <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                    {evaluation.scientific_explanation}
                  </p>
                )}
              </div>

              {/* Group Splitting ID */}
              <div className="mt-3 pt-2.5 border-t border-slate-200 flex items-center justify-between text-[11px] font-mono text-slate-600">
                <span className="text-slate-500">Group Split:</span>
                <span className="text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 text-[10px]">
                  {ds.group_column || 'source_file'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
