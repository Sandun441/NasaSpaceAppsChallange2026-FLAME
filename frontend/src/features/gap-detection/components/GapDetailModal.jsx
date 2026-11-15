import React, { useEffect, useState } from 'react';
import { flameApi } from '../../../services/flameApi';

const GAP_TYPE_BADGES = {
  coverage_gap: { bg: 'bg-rose-50 text-rose-800 border-rose-200', label: 'Coverage Gap' },
  sparse_evidence: { bg: 'bg-amber-50 text-amber-800 border-amber-200', label: 'Sparse Evidence' },
  measurement_gap: { bg: 'bg-orange-50 text-orange-800 border-orange-200', label: 'Measurement Gap' },
  metadata_gap: { bg: 'bg-purple-50 text-purple-800 border-purple-200', label: 'Metadata Gap' },
  ingestion_opportunity: { bg: 'bg-sky-50 text-sky-800 border-sky-200', label: 'Ingestion Opportunity' },
  comparison_gap: { bg: 'bg-indigo-50 text-indigo-800 border-indigo-200', label: 'Comparison Gap' },
};

export function GapDetailModal({ gap, onClose, onSelectTab, onAnalyzeInExplorer }) {
  const [detailedGap, setDetailedGap] = useState(gap);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  useEffect(() => {
    // If only an ID was passed, or if we want the freshest detail from API
    let isMounted = true;
    const fetchDetail = async () => {
      const findingId = typeof gap === 'string' ? gap : gap?.finding_id || gap?.id;
      if (!findingId) return;

      setIsLoadingDetail(true);
      try {
        const res = await flameApi.getGapFindingDetail(findingId);
        if (isMounted && res?.status === 'success' && res.finding) {
          setDetailedGap(res.finding);
        }
      } catch (err) {
        console.warn('Could not fetch fresh finding detail, using initial prop:', err);
      } finally {
        if (isMounted) setIsLoadingDetail(false);
      }
    };

    fetchDetail();
    return () => {
      isMounted = false;
    };
  }, [gap]);

  if (!gap && !detailedGap) return null;

  const current = detailedGap || gap;
  const findingId = current.finding_id || current.id || 'GAP-UNKNOWN';
  const typeMeta = GAP_TYPE_BADGES[current.gap_type] || {
    bg: 'bg-slate-800 text-slate-300 border-slate-700',
    label: current.gap_type || 'Research Gap',
  };

  const priority = current.priority_score ?? 0;
  const priorityColor =
    priority >= 7.0
      ? 'text-rose-800 bg-rose-50 border-rose-200'
      : priority >= 4.0
      ? 'text-amber-800 bg-amber-50 border-amber-200'
      : 'text-sky-800 bg-sky-50 border-sky-200';

  const factors = current.scoring_factors || {};
  const confidence = current.evidence_confidence || {
    level: 'HIGH',
    justification: 'Factual database determination.',
    scope: 'Identified strictly within FLAME repository scope.',
  };

  const dimensions = current.scientific_dimensions || {};
  const experimentIds = current.supporting_experiment_ids || [];
  const datasetIds = current.supporting_dataset_ids || [];
  const provenance = current.provenance_references || [];
  const limitations = current.limitations || [];

  const handleOpenDatasetExplorer = () => {
    if (onSelectTab) {
      onSelectTab('dataset-explorer');
      onClose();
    }
  };

  const handleLaunchExplorer = () => {
    if (onAnalyzeInExplorer) {
      onAnalyzeInExplorer(dimensions);
      onClose();
    }
  };

  const handleInvestigateWithAI = () => {
    if (onSelectTab) {
      onSelectTab('home', {
        initialFindingId: findingId,
        initialFindingTitle: current.title,
        initialFinding: current,
        initialQuery: `Investigate scientific evidence and coverage status for research gap ${findingId}: ${current.title}`,
      });
      if (onClose) onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog Card */}
      <div className="relative w-full max-w-4xl bg-white border border-slate-200 rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6 text-slate-800 z-10 max-h-[92vh] overflow-y-auto animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-200">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-bold">
                {findingId}
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${typeMeta.bg}`}>
                {typeMeta.label}
              </span>
              <span className={`text-[10px] font-mono px-2.5 py-0.5 rounded border font-bold ${priorityColor}`}>
                Heuristic Priority {priority.toFixed(1)} / 10
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                Confidence: {confidence.level}
              </span>
            </div>

            <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight leading-snug">
              {current.title}
            </h2>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onSelectTab && (
              <button
                type="button"
                onClick={handleInvestigateWithAI}
                className="px-3 py-1.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs font-mono transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
                title="Open Grounded Scientific AI Assistant to investigate this finding"
              >
                <span>Investigate with AI</span>
                <span>✨</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200 transition-colors cursor-pointer text-sm"
              aria-label="Close dialog"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Section 1: Scientific Explanation & Denominator */}
        <div className="space-y-3">
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
            {current.explanation}
          </p>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
            <span className="text-slate-500">
              Database Denominator & Scope:{' '}
              <strong className="text-slate-900 font-semibold">
                {current.denominator_and_scope || '0 of 133 indexed records in FLAME database'}
              </strong>
            </span>
            <span className="text-orange-700 text-[11px]">
              Observed Usable Runs: {current.observed_usable_run_count ?? 0}
            </span>
          </div>
        </div>

        {/* Section 2: Transparent 5-Factor Heuristic Priority Breakdown */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold font-mono uppercase text-orange-700 tracking-wider">
                Transparent Heuristic Priority Factor Breakdown
              </span>
            </div>
            <span className="text-[10.5px] font-mono text-slate-500">
              Total Score: <strong className="text-slate-900 font-bold">{priority.toFixed(1)} / 10</strong>
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 text-xs font-mono">
            {/* Factor 1: Coverage Deficiency */}
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-1">
              <div className="text-[10px] text-slate-500 uppercase">1. Deficiency</div>
              <div className="text-sm font-bold text-rose-600">
                {(factors.coverage_deficiency ?? 0).toFixed(1)} <span className="text-[10px] text-slate-400 font-normal">/ 3.0</span>
              </div>
              <div className="text-[9.5px] text-slate-500 leading-tight">Evidence deficit in FLAME</div>
            </div>

            {/* Factor 2: Mission Relevance */}
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-1">
              <div className="text-[10px] text-slate-500 uppercase">2. Mission Impact</div>
              <div className="text-sm font-bold text-amber-600">
                {(factors.mission_relevance ?? 0).toFixed(1)} <span className="text-[10px] text-slate-400 font-normal">/ 2.5</span>
              </div>
              <div className="text-[9.5px] text-slate-500 leading-tight">Artemis & Mars urgency</div>
            </div>

            {/* Factor 3: Resolvability */}
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-1">
              <div className="text-[10px] text-slate-500 uppercase">3. Resolvability</div>
              <div className="text-sm font-bold text-sky-600">
                {(factors.resolvability_feasibility ?? 0).toFixed(1)} <span className="text-[10px] text-slate-400 font-normal">/ 2.0</span>
              </div>
              <div className="text-[9.5px] text-slate-500 leading-tight">Feasibility to ingest / test</div>
            </div>

            {/* Factor 4: Metadata Quality */}
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-1">
              <div className="text-[10px] text-slate-500 uppercase">4. Metadata Completeness</div>
              <div className="text-sm font-bold text-purple-600">
                {(factors.metadata_quality ?? 0).toFixed(1)} <span className="text-[10px] text-slate-400 font-normal">/ 1.5</span>
              </div>
              <div className="text-[9.5px] text-slate-500 leading-tight">Logging & sensor completeness</div>
            </div>

            {/* Factor 5: Comparison Readiness */}
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-1 col-span-2 sm:col-span-1">
              <div className="text-[10px] text-slate-500 uppercase">5. Baseline Readiness</div>
              <div className="text-sm font-bold text-emerald-600">
                {(factors.comparison_readiness ?? 0).toFixed(1)} <span className="text-[10px] text-slate-400 font-normal">/ 1.0</span>
              </div>
              <div className="text-[9.5px] text-slate-500 leading-tight">Controlled comparison availability</div>
            </div>
          </div>

          <p className="text-[10.5px] text-slate-500 font-mono italic pt-1">
            * Epistemic Notice: Priority score is an engineering ranking heuristic reflecting safety criticality, mission impact, and ingestion feasibility. It is not an empirical measurement or physical combustion parameter.
          </p>
        </div>

        {/* Section 3: Evidence Confidence Card */}
        <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 font-mono uppercase">
            <span>●</span> Evidence Confidence Justification ({confidence.level})
          </div>
          <p className="text-xs text-slate-700 leading-relaxed">
            {confidence.justification}
          </p>
          <div className="text-[10.5px] font-mono text-slate-500 pt-1 border-t border-emerald-200/60">
            <strong>Database Scope Statement:</strong> {confidence.scope}
          </div>
        </div>

        {/* Section 4: Scientific Dimensions & Target Exploration Environment */}
        <div className="space-y-2">
          <span className="text-[11px] font-mono uppercase text-slate-500 tracking-wider block">
            Target Exploration Environment & Operating Conditions
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block">Gravity</span>
              <span className="text-slate-900 font-medium">{dimensions.gravity || 'N/A'}</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block">Oxygen (O₂)</span>
              <span className="text-slate-900 font-medium">{dimensions.oxygen || 'N/A'}</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block">Pressure</span>
              <span className="text-slate-900 font-medium">{dimensions.pressure || 'N/A'}</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 block">Fuel Family / Mat</span>
              <span className="text-slate-900 font-medium truncate block">
                {dimensions.fuel_family || dimensions.fuel_material || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Section 5: Supporting Experiment Runs & Provenance */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Supporting Experiments */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase text-slate-500 tracking-wider">
                Supporting Experiment Runs ({experimentIds.length})
              </span>
              {experimentIds.length > 0 && onSelectTab && (
                <button
                  type="button"
                  onClick={handleOpenDatasetExplorer}
                  className="text-[10px] font-mono text-orange-600 hover:text-orange-700 underline cursor-pointer"
                >
                  View in Dataset Explorer →
                </button>
              )}
            </div>
            {experimentIds.length > 0 ? (
              <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                {experimentIds.map((id) => (
                  <span
                    key={id}
                    className="px-2 py-0.5 rounded bg-white border border-slate-200 text-[10.5px] font-mono text-sky-800"
                  >
                    {id}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-slate-400 font-mono italic">
                No indexed experiment runs match this gap regime (unrepresented in FLAME database).
              </p>
            )}
          </div>

          {/* Provenance References */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-[11px] font-mono uppercase text-slate-500 tracking-wider block">
              Provenance & Scientific Archives
            </span>
            {provenance.length > 0 ? (
              <ul className="space-y-1 text-xs text-slate-700 font-mono">
                {provenance.map((ref, idx) => (
                  <li key={idx} className="flex items-center gap-1.5 text-sky-700 text-[11px]">
                    <span>▸</span> {ref}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[11px] text-slate-400 font-mono italic">
                NASA FLAME internal dataset catalog & Physical Sciences Informatics (PSI).
              </p>
            )}
          </div>
        </div>

        {/* Section 6: Actionable Next Steps & Limitations */}
        <div className="space-y-3 pt-2 border-t border-slate-200">
          <div className="p-3.5 rounded-xl bg-orange-50 border border-orange-200 space-y-1.5">
            <div className="text-[11px] font-mono uppercase font-bold text-orange-800">
              Recommended Next Step:
            </div>
            <p className="text-xs text-slate-800 leading-relaxed">
              {current.recommended_next_step || 'Consult NASA technical documentation for further testing requirements.'}
            </p>
          </div>

          {limitations.length > 0 && (
            <div className="space-y-1 text-xs text-slate-600">
              <span className="text-[10.5px] font-mono uppercase text-slate-500 block">
                Known Technical Limitations:
              </span>
              <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                {limitations.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Database Scope Disclaimer */}
          <div className="text-[10.5px] font-mono text-slate-500 border-t border-slate-200 pt-2">
            <strong>Database Scope Notice:</strong>{' '}
            {current.database_scope_disclaimer ||
              'Unrepresented in the indexed FLAME collection. Missing data in FLAME does not prove NASA never conducted an experiment.'}
          </div>
        </div>

        {/* Modal Actions Footer */}
        <div className="pt-4 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex flex-wrap items-center gap-2">
            {onSelectTab && (
              <button
                type="button"
                onClick={handleInvestigateWithAI}
                className="px-4 py-2 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs font-mono transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
              >
                <span>Investigate with Scientific AI</span>
                <span>↗</span>
              </button>
            )}
            <button
              type="button"
              onClick={handleLaunchExplorer}
              className="px-3.5 py-2 rounded-lg bg-orange-50 hover:bg-orange-100 text-orange-800 border border-orange-200 transition-colors cursor-pointer"
            >
              Analyze this Condition in Explorer →
            </button>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors cursor-pointer"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
