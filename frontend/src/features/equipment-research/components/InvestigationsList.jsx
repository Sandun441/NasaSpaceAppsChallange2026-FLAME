import React from 'react';
import { Button } from '../../../components/common/Button';

export function InvestigationsList({
  investigations = [],
  externalContext = [],
  activeCategory,
  onNavigate,
}) {
  if (!investigations || investigations.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
        <p className="text-xs text-slate-700 font-medium">No Investigations Found</p>
        <p className="text-[11px] text-slate-500 font-mono">
          Try selecting another research domain or expanding your inquiry.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Locally Indexed Flight Investigations */}
      <div className="space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-slate-200">
          <div>
            <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <span>Locally Indexed NASA Flight Investigations</span>
              <span className="text-[10px] font-mono text-orange-700 bg-orange-50 border border-orange-200 px-2 py-0.5 rounded">
                {investigations.length} Verified Sources
              </span>
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Empirical flight experiment series with real sensor telemetry and records indexed in NASA FLAME
            </p>
          </div>
        </div>

        {/* Investigation Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {investigations.map((inv) => {
            const channels = inv.verified_sensor_channels || [];
            const relSummary =
              inv.relevance && activeCategory !== 'all'
                ? inv.relevance[activeCategory] || Object.values(inv.relevance)[0]
                : inv.relevance
                ? Object.values(inv.relevance)[0]
                : inv.relevance_summary;

            const primaryDataset = (inv.flight_datasets && inv.flight_datasets[0]) || inv.id;

            return (
              <div
                key={inv.id}
                className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-3.5 flex flex-col justify-between hover:border-slate-300 transition-all"
              >
                <div className="space-y-2.5">
                  {/* Title & Facility Badges */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-orange-600">
                        {inv.facility}
                      </span>
                      <h4 className="text-sm sm:text-base font-bold text-slate-900">
                        {inv.name}
                      </h4>
                    </div>
                    <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded shrink-0">
                      Indexed Telemetry
                    </span>
                  </div>

                  {/* Relevance Context */}
                  {relSummary && (
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-700 leading-relaxed">
                      <strong className="text-orange-700 block mb-0.5 font-mono text-[10px] uppercase">
                        Fire-Safety Research Relevance:
                      </strong>
                      {relSummary}
                    </div>
                  )}

                  {/* Verified Sensor Channels */}
                  {channels.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">
                        Verified Local Measurement Channels ({channels.length}):
                      </span>
                      <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
                        {channels.map((ch) => (
                          <div
                            key={ch.id}
                            className="bg-slate-50/70 border border-slate-200 rounded-lg p-2 text-xs flex flex-col gap-0.5"
                          >
                            <div className="flex items-center justify-between gap-1 flex-wrap">
                              <span className="font-semibold text-slate-800">{ch.label}</span>
                              <span className="text-[10px] font-mono text-orange-700 bg-orange-50 px-1.5 py-0.2 rounded border border-orange-200">
                                [{ch.unit}]
                              </span>
                            </div>
                            <span className="text-[10px] font-mono text-slate-500">
                              Range: {ch.measured_range}
                            </span>
                            {ch.source_dataset && (
                              <span className="text-[9px] font-mono text-slate-400">
                                Source: <code>{ch.source_dataset}</code>
                              </span>
                            )}
                            <p className="text-[11px] text-slate-600 font-sans leading-tight">
                              {ch.description}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="pt-2 border-t border-slate-200 flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-[10px] font-mono text-slate-500">
                    Dataset: <code className="text-slate-600">{primaryDataset}</code>
                  </span>

                  <div className="flex items-center gap-2">
                    {inv.id !== 'bass_ii' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          onNavigate('dataset-explorer', {
                            dataset_id: primaryDataset,
                            view_mode: 'visualization',
                          })
                        }
                        className="text-[11px] py-1 text-orange-700 border-orange-300 hover:bg-orange-50"
                      >
                        📈 View Telemetry
                      </Button>
                    )}
                    {inv.id === 'saffire_iii' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          onNavigate('experiment-comparison', {
                            exp1: 'saffire_iii_sample_1',
                            exp2: 'saffire_iii_sample_2',
                          })
                        }
                        className="text-[11px] py-1 text-slate-700 hover:text-slate-900 border-slate-200 hover:bg-slate-50"
                      >
                        ⚖️ Compare Runs
                      </Button>
                    )}
                    {inv.id === 'bass_ii' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          onNavigate('dataset-explorer', {
                            dataset_id: 'bass_ii_experiments',
                            view_mode: 'table',
                          })
                        }
                        className="text-[11px] py-1 text-slate-700 hover:text-slate-900 border-slate-200 hover:bg-slate-50"
                      >
                        📋 Inspect Matrix
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. External NASA Research Context (Unindexed Literature Reference) */}
      {externalContext && externalContext.length > 0 && (
        <div className="space-y-3 pt-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-slate-200">
            <div>
              <h3 className="text-xs font-semibold text-purple-900 uppercase tracking-wider flex items-center gap-2">
                <span>External NASA Research Context (Unindexed in FLAME)</span>
                <span className="text-[10px] font-mono text-purple-800 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded">
                  {externalContext.length} External Literature References
                </span>
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Published NASA flight investigations providing supplementary combustion physics context; no local telemetry indexed in FLAME
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {externalContext.map((ext) => (
              <div
                key={ext.id}
                className="bg-white border border-purple-200/80 rounded-xl p-3.5 space-y-2 flex flex-col justify-between shadow-xs"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="text-xs font-bold text-slate-900">
                      {ext.name}
                    </h4>
                    <span className="text-[9px] font-mono text-purple-800 bg-purple-50 border border-purple-200 px-1.5 py-0.5 rounded shrink-0">
                      Literature Only
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 block">
                    Facility: {ext.facility}
                  </span>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    {ext.description || (ext.relevance && Object.values(ext.relevance)[0])}
                  </p>
                  {ext.external_reference && (
                    <div className="text-[10px] font-mono text-purple-900 bg-purple-50 p-1.5 rounded border border-purple-200">
                      Reference: {ext.external_reference}
                    </div>
                  )}
                </div>
                <div className="text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-100">
                  Status: Unindexed in local FLAME telemetry
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
