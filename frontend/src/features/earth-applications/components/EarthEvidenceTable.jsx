import React from 'react';
import {
  CategoryIcon,
  DatabaseIcon,
  BookOpenIcon,
  CheckCircleIcon,
  LightbulbIcon,
  ChevronRightIcon,
} from './EarthIcons';

export function EarthEvidenceTable({
  evidenceList = [],
  selectedEvidenceId,
  onSelectEvidence,
  onOpenVisualizer,
  onOpenModelingExtraction,
}) {
  if (evidenceList.length === 0) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-600 font-mono">
        No evidence records matched your active filter criteria.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-mono text-slate-600 uppercase tracking-wider">
          <tr>
            <th className="py-3 px-3">Evidence ID</th>
            <th className="py-3 px-3">Application Title & Category</th>
            <th className="py-3 px-3">NASA Investigation</th>
            <th className="py-3 px-3">Dimension A: Flight Data</th>
            <th className="py-3 px-3">Dimension B: Terrestrial Status</th>
            <th className="py-3 px-3">Verified Scientific Finding</th>
            <th className="py-3 px-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {evidenceList.map((ev) => {
            const isSelected = selectedEvidenceId === ev.id;
            const isLocal = ev.validation_status === 'locally_verified';
            const isHypothesis = ev.evidence_classification === 'exploratory_hypothesis';
            const isDocumented = ev.evidence_classification === 'documented_application';

            const hasSaffire =
              ev.investigation_id === 'saffire_iii' ||
              (ev.dataset_or_measurement_reference &&
                ev.dataset_or_measurement_reference.includes('saffire_iii_sample_1.csv'));

            const hasBass =
              ev.investigation_id === 'bass_ii' ||
              (ev.dataset_or_measurement_reference &&
                ev.dataset_or_measurement_reference.includes('bass_ii_experiments.csv'));

            return (
              <tr
                key={ev.id}
                onClick={() => onSelectEvidence(ev)}
                className={`transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-orange-50/80 text-slate-900'
                    : 'hover:bg-slate-50 text-slate-700'
                }`}
              >
                {/* ID */}
                <td className="py-3 px-3 whitespace-nowrap">
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                    {ev.id}
                  </span>
                </td>

                {/* Title & Category */}
                <td className="py-3 px-3 max-w-xs">
                  <div className="font-medium text-slate-900 tracking-tight leading-snug">
                    {ev.title}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1 mt-0.5">
                    <CategoryIcon categoryId={ev.category_id} className="w-3 h-3 text-orange-600" />
                    <span>{ev.category_title}</span>
                  </div>
                </td>

                {/* Investigation */}
                <td className="py-3 px-3 whitespace-nowrap">
                  <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 uppercase">
                    {ev.investigation_id.replace('_', ' ')}
                  </span>
                  {ev.related_investigation_ids && ev.related_investigation_ids.length > 0 && (
                    <div className="text-[9px] font-mono text-slate-400 mt-0.5">
                      +{ev.related_investigation_ids.join(', ')}
                    </div>
                  )}
                </td>

                {/* Dimension A */}
                <td className="py-3 px-3 whitespace-nowrap">
                  {isLocal ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                      <DatabaseIcon className="w-3 h-3 text-purple-600" />
                      <span>Local CSV</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                      <BookOpenIcon className="w-3 h-3 text-blue-600" />
                      <span>Literature TM</span>
                    </span>
                  )}
                </td>

                {/* Dimension B */}
                <td className="py-3 px-3 whitespace-nowrap">
                  {isHypothesis ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                      <LightbulbIcon className="w-3 h-3 text-amber-600" />
                      <span>Hypothesis</span>
                    </span>
                  ) : isDocumented ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
                      <CheckCircleIcon className="w-3 h-3 text-sky-600" />
                      <span>Documented</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <CheckCircleIcon className="w-3 h-3 text-emerald-600" />
                      <span>Supported Implication</span>
                    </span>
                  )}
                </td>

                {/* Finding */}
                <td className="py-3 px-3 max-w-sm">
                  <p className="text-[11px] text-slate-700 line-clamp-2 leading-relaxed">
                    {ev.scientific_finding}
                  </p>
                </td>

                {/* Actions */}
                <td className="py-3 px-3 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end gap-1.5">
                    {hasSaffire && onOpenVisualizer && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenVisualizer(ev);
                        }}
                        title="Open Saffire Telemetry in Visualizer"
                        className="text-[10px] font-mono px-2 py-1 rounded bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 transition-colors"
                      >
                        Visualizer
                      </button>
                    )}

                    {hasBass && onOpenModelingExtraction && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenModelingExtraction(ev);
                        }}
                        title="Extract in Predictive Modeling Extraction"
                        className="text-[10px] font-mono px-2 py-1 rounded bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition-colors"
                      >
                        ML Extract
                      </button>
                    )}

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectEvidence(ev);
                      }}
                      className="text-xs font-mono text-orange-600 hover:text-orange-700 p-1 rounded hover:bg-orange-50 transition-colors"
                    >
                      <ChevronRightIcon className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
