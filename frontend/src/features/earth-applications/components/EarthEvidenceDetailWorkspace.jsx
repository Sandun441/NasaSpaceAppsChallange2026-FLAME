import React from 'react';
import {
  CategoryIcon,
  DatabaseIcon,
  CheckCircleIcon,
  AlertTriangleIcon,
  ExternalLinkIcon,
  ArrowRightIcon,
  InfoIcon,
  SparklesIcon,
} from './EarthIcons';

export function EarthEvidenceDetailWorkspace({
  evidence,
  onClose,
  onOpenVisualizer,
  onOpenModelingExtraction,
  onOpenGapMatrix,
  onAskAssistant,
}) {
  if (!evidence) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-600 font-mono">
        Select an evidence record to inspect detailed physical observations and terrestrial transfer mechanisms.
      </div>
    );
  }

  const isLocal = evidence.validation_status === 'locally_verified';
  const isHypothesis = evidence.evidence_classification === 'exploratory_hypothesis';
  const isDocumented = evidence.evidence_classification === 'documented_application';

  const hasSaffire =
    evidence.investigation_id === 'saffire_iii' ||
    (evidence.dataset_or_measurement_reference &&
      evidence.dataset_or_measurement_reference.includes('saffire_iii_sample_1.csv'));

  const hasBass =
    evidence.investigation_id === 'bass_ii' ||
    (evidence.dataset_or_measurement_reference &&
      evidence.dataset_or_measurement_reference.includes('bass_ii_experiments.csv'));

  const isSourceUrl =
    evidence.source_reference &&
    (evidence.source_reference.startsWith('http://') ||
      evidence.source_reference.startsWith('https://'));

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-white border border-slate-200 space-y-6 shadow-sm relative animate-in fade-in duration-200">
      {/* Workspace Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
              {evidence.id}
            </span>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-orange-50 text-orange-700 border border-orange-200 flex items-center gap-1">
              <CategoryIcon categoryId={evidence.category_id} className="w-3.5 h-3.5" />
              <span>{evidence.category_title}</span>
            </span>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-sky-50 text-sky-700 border border-sky-200 uppercase font-semibold">
              {evidence.investigation_name || evidence.investigation_id}
            </span>
          </div>

          <h2 className="text-base sm:text-xl font-bold text-slate-900 tracking-tight pt-1">
            {evidence.title}
          </h2>
          <p className="text-xs text-slate-600">
            {evidence.description}
          </p>
        </div>

        {/* Close or Back Button */}
        {onClose && (
          <button
            onClick={onClose}
            className="self-start md:self-center px-3 py-1.5 rounded-lg text-xs font-mono text-slate-600 hover:text-slate-900 bg-slate-100 border border-slate-200 hover:border-slate-300 transition-colors cursor-pointer"
          >
            ✕ Close Inspector
          </button>
        )}
      </div>

      {/* Main 2-Column Scientific Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Observed Flight Findings & Epistemology */}
        <div className="space-y-5">
          {/* Section A: Experiment Information & Provenance */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="text-xs font-semibold text-slate-900 tracking-tight flex items-center gap-1.5">
                <DatabaseIcon className="w-4 h-4 text-purple-600" />
                <span>Flight Experiment Provenance (Dimension A)</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                {isLocal ? 'Tier 1: Locally Verified' : 'Tier 2: External Literature'}
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div>
                <span className="text-[10px] font-mono uppercase text-slate-500 block">
                  Archive Source Reference:
                </span>
                {isSourceUrl ? (
                  <a
                    href={evidence.source_reference}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sky-600 hover:text-sky-700 underline font-mono inline-flex items-center gap-1 break-all mt-0.5"
                  >
                    <span>{evidence.source_reference}</span>
                    <ExternalLinkIcon className="w-3 h-3 shrink-0" />
                  </a>
                ) : (
                  <span className="text-slate-800 font-mono block mt-0.5">
                    {evidence.source_reference}
                  </span>
                )}
              </div>

              {evidence.dataset_or_measurement_reference && (
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">
                    Local Sensor / Dataset Pointer:
                  </span>
                  <div className="flex items-center justify-between gap-2 mt-0.5 p-2 rounded bg-white border border-slate-200">
                    <span className="text-slate-800 font-mono text-[11px] break-all">
                      {evidence.dataset_or_measurement_reference}
                    </span>
                    {isLocal && (
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 shrink-0">
                        FLAME CSV Indexed
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div>
                <span className="text-[10px] font-mono uppercase text-slate-500 block">
                  Supporting Archive Excerpt:
                </span>
                <p className="text-slate-700 italic text-[11px] leading-relaxed bg-white p-2.5 rounded border border-slate-200 mt-1">
                  &quot;{evidence.supporting_excerpt}&quot;
                </p>
              </div>
            </div>
          </div>

          {/* Section B: Verified Empirical Microgravity Finding */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="text-xs font-semibold text-slate-900 tracking-tight flex items-center gap-1.5">
                <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                <span>Verified Microgravity Scientific Finding</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                Audited Empirical Truth
              </span>
            </div>
            <p className="text-xs text-slate-800 leading-relaxed">
              {evidence.scientific_finding}
            </p>
          </div>

          {/* Section C: Dimension A vs Dimension B Confidence Rubric */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="text-xs font-semibold text-slate-900 tracking-tight flex items-center gap-1.5">
                <InfoIcon className="w-4 h-4 text-sky-600" />
                <span>Validation Rubric & Epistemic Decoupling</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                Non-Extrapolation Standard
              </span>
            </div>
            <div className="text-xs text-slate-700 space-y-1.5 leading-relaxed">
              <p className="bg-white p-2.5 rounded border border-slate-200 font-mono text-[11px]">
                {evidence.confidence_rubric}
              </p>
              <div className="text-[11px] text-slate-600 flex items-start gap-1 pt-1">
                <span className="text-emerald-600 font-bold">•</span>
                <span>
                  <strong>Dimension A:</strong> Measurement validity in NASA flight archives.
                </span>
              </div>
              <div className="text-[11px] text-slate-600 flex items-start gap-1">
                <span className="text-sky-600 font-bold">•</span>
                <span>
                  <strong>Dimension B:</strong> Documented use, supported implication, or exploratory hypothesis.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Terrestrial Relevance, Physical Transfer & Cross-Module */}
        <div className="space-y-5">
          {/* Section D: Proposed Terrestrial Relevance */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="text-xs font-semibold text-slate-900 tracking-tight flex items-center gap-1.5">
                <ArrowRightIcon className="w-4 h-4 text-orange-600" />
                <span>Proposed Terrestrial Research Relevance</span>
              </span>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                  isHypothesis
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : isDocumented
                    ? 'bg-sky-50 text-sky-700 border-sky-200'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                }`}
              >
                {isHypothesis
                  ? 'Exploratory Hypothesis'
                  : isDocumented
                  ? 'Documented Application'
                  : 'Supported Implication'}
              </span>
            </div>
            <p className="text-xs text-slate-800 leading-relaxed">
              {evidence.proposed_terrestrial_relevance}
            </p>
          </div>

          {/* Section E: Physical Gravity, Buoyancy & Scale Differences */}
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-amber-200">
              <span className="text-xs font-semibold text-amber-900 tracking-tight flex items-center gap-1.5">
                <AlertTriangleIcon className="w-4 h-4 text-amber-600" />
                <span>Physical Gravity, Buoyancy & Scale Differences</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-amber-800 border border-amber-200">
                1g vs Microgravity
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div>
                <span className="text-[10px] font-mono uppercase text-amber-800 block">
                  Buoyant Draft vs Forced Mechanical Flow:
                </span>
                <p className="text-slate-800 text-[11px] leading-relaxed mt-0.5">
                  {evidence.gravity_buoyancy_ventilation_differences}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-amber-800 block">
                  Terrestrial Scaling & Geometry Limitations:
                </span>
                <p className="text-slate-800 text-[11px] leading-relaxed mt-0.5">
                  {evidence.earth_transfer_limitations}
                </p>
              </div>
            </div>
          </div>

          {/* Section F: Uncertainties and Evidence Gaps */}
          {evidence.uncertainty_notes && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <span className="text-xs font-semibold text-slate-900 tracking-tight block">
                Scientific Uncertainties & Unmeasured Parameters
              </span>
              <p className="text-xs text-slate-600 leading-relaxed">
                {evidence.uncertainty_notes}
              </p>
            </div>
          )}

          {/* Section G: Cross-Module Launch Actions */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <span className="text-xs font-semibold text-slate-900 tracking-tight block">
              Cross-Module Scientific Intelligence Actions
            </span>

            <div className="flex flex-wrap items-center gap-2">
              {onAskAssistant && (
                <button
                  onClick={() => onAskAssistant(evidence)}
                  className="px-3 py-2 rounded-xl text-xs font-mono bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 transition-colors cursor-pointer flex items-center gap-1.5"
                >
                  <SparklesIcon className="w-3.5 h-3.5 text-orange-600" />
                  <span>Ask AI Assistant About This Research</span>
                </button>
              )}

              {hasSaffire && onOpenVisualizer && (
                <button
                  onClick={() => onOpenVisualizer(evidence)}
                  className="px-3 py-2 rounded-xl text-xs font-mono bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 transition-colors cursor-pointer flex items-center gap-1.5"
                >
                  <DatabaseIcon className="w-3.5 h-3.5 text-sky-600" />
                  <span>Open Saffire Telemetry in Visualizer</span>
                </button>
              )}

              {hasBass && onOpenModelingExtraction && (
                <button
                  onClick={() => onOpenModelingExtraction(evidence)}
                  className="px-3 py-2 rounded-xl text-xs font-mono bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition-colors cursor-pointer flex items-center gap-1.5"
                >
                  <DatabaseIcon className="w-3.5 h-3.5 text-purple-600" />
                  <span>Export Runs in Predictive Modeling</span>
                </button>
              )}

              {onOpenGapMatrix && (
                <button
                  onClick={() => onOpenGapMatrix(evidence)}
                  className="px-3 py-2 rounded-xl text-xs font-mono bg-white text-slate-700 border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer flex items-center gap-1.5"
                >
                  <span>Examine Finding in Research Gap Matrix</span>
                  <ArrowRightIcon className="w-3.5 h-3.5 text-slate-500" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
