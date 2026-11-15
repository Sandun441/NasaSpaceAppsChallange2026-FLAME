import React from 'react';
import {
  CategoryIcon,
  DatabaseIcon,
  BookOpenIcon,
  CheckCircleIcon,
  LightbulbIcon,
  ArrowRightIcon,
  ExternalLinkIcon,
  SparklesIcon,
} from './EarthIcons';

export function EarthEvidenceCard({
  evidence,
  isSelected = false,
  onSelect,
  onOpenVisualizer,
  onOpenModelingExtraction,
  onOpenGapMatrix,
  onAskAssistant,
}) {
  const isLocal = evidence.validation_status === 'locally_verified';
  const isHypothesis = evidence.evidence_classification === 'exploratory_hypothesis';
  const isDocumented = evidence.evidence_classification === 'documented_application';

  const hasSaffireTelemetry =
    evidence.investigation_id === 'saffire_iii' ||
    (evidence.dataset_or_measurement_reference &&
      evidence.dataset_or_measurement_reference.includes('saffire_iii_sample_1.csv'));

  const hasBassData =
    evidence.investigation_id === 'bass_ii' ||
    (evidence.dataset_or_measurement_reference &&
      evidence.dataset_or_measurement_reference.includes('bass_ii_experiments.csv'));

  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-xl border transition-all duration-200 space-y-3 cursor-pointer flex flex-col justify-between ${
        isSelected
          ? 'bg-white border-orange-400 ring-1 ring-orange-300 shadow-md'
          : 'bg-white hover:bg-slate-50 border-slate-200 hover:border-slate-300 shadow-xs'
      }`}
    >
      <div className="space-y-2.5">
        {/* Top Badges Row */}
        <div className="flex flex-wrap items-center justify-between gap-1.5">
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* ID Badge */}
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
              {evidence.id}
            </span>

            {/* Category Badge */}
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-200 flex items-center gap-1">
              <CategoryIcon categoryId={evidence.category_id} className="w-3 h-3" />
              <span>{evidence.category_title}</span>
            </span>
          </div>

          {/* NASA Investigation Badge */}
          <div className="flex items-center gap-1">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 uppercase tracking-wider font-semibold">
              {evidence.investigation_id.replace('_', ' ')}
            </span>
            {evidence.related_investigation_ids && evidence.related_investigation_ids.length > 0 && (
              <span
                title={`Related co-investigation: ${evidence.related_investigation_ids.join(', ')}`}
                className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200"
              >
                +{evidence.related_investigation_ids.length}
              </span>
            )}
          </div>
        </div>

        {/* Title */}
        <h3 className="text-sm font-semibold text-slate-900 tracking-tight leading-snug group-hover:text-orange-600 transition-colors">
          {evidence.title}
        </h3>

        {/* Dual Dimension Badges: Dimension A (Flight Grounding) vs Dimension B (Terrestrial Validation) */}
        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
          {/* Dimension A: Flight Verification */}
          {isLocal ? (
            <span
              title="Verified against local telemetry and CSV datasets archived in NASA FLAME"
              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1"
            >
              <DatabaseIcon className="w-3 h-3 text-purple-600" />
              <span>Locally Verified Telemetry</span>
            </span>
          ) : (
            <span
              title="Verified against peer-reviewed literature or NASA Technical Memorandums"
              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1"
            >
              <BookOpenIcon className="w-3 h-3 text-blue-600" />
              <span>Literature Verified (TM / DOI)</span>
            </span>
          )}

          {/* Dimension B: Terrestrial Application Validation */}
          {isHypothesis ? (
            <span
              title="Exploratory research hypothesis; unvalidated for terrestrial engineering deployment"
              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1 font-semibold"
            >
              <LightbulbIcon className="w-3 h-3 text-amber-600" />
              <span>Exploratory Hypothesis</span>
            </span>
          ) : isDocumented ? (
            <span
              title="Documented terrestrial application with verified commercial adoption"
              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200 flex items-center gap-1 font-semibold"
            >
              <CheckCircleIcon className="w-3 h-3 text-sky-600" />
              <span>Documented Application</span>
            </span>
          ) : (
            <span
              title="Theoretical and peer-reviewed physical connection; requires terrestrial turbulent scaling"
              className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1 font-semibold"
            >
              <CheckCircleIcon className="w-3 h-3 text-emerald-600" />
              <span>Supported Implication</span>
            </span>
          )}
        </div>

        {/* Audited Scientific Finding */}
        <div className="space-y-1 pt-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold block">
            Verified Flight Observation:
          </span>
          <p className="text-xs text-slate-700 leading-relaxed line-clamp-3">
            {evidence.scientific_finding}
          </p>
        </div>

        {/* Proposed Terrestrial Relevance */}
        <div className="space-y-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-orange-600 font-semibold block">
            Terrestrial Research Relevance:
          </span>
          <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
            {evidence.proposed_terrestrial_relevance}
          </p>
        </div>
      </div>

      {/* Card Footer: Physical Boundaries & Cross-Module Action Buttons */}
      <div className="pt-3 border-t border-slate-100 space-y-2">
        <div className="text-[10px] font-mono text-amber-800 bg-amber-50 px-2 py-1 rounded border border-amber-200 line-clamp-1">
          <span className="font-semibold text-amber-700">1g Difference: </span>
          {evidence.gravity_buoyancy_ventilation_differences}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-1.5 pt-1">
          {/* Inspect Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect();
            }}
            className="text-xs font-mono font-medium text-orange-600 hover:text-orange-700 flex items-center gap-1 transition-colors cursor-pointer"
          >
            <span>Inspect Evidence</span>
            <ArrowRightIcon className="w-3 h-3" />
          </button>

          {/* Quick Cross-Module Launch Pills */}
          <div className="flex items-center gap-1">
            {hasSaffireTelemetry && onOpenVisualizer && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenVisualizer();
                }}
                title="Open Saffire Telemetry in Scientific Visualizer"
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 hover:text-sky-800 transition-colors cursor-pointer flex items-center gap-0.5"
              >
                <span>Visualizer</span>
                <ExternalLinkIcon className="w-2.5 h-2.5" />
              </button>
            )}

            {hasBassData && onOpenModelingExtraction && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenModelingExtraction();
                }}
                title="Extract BASS-II data in Predictive Modeling Extraction"
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 hover:text-purple-800 transition-colors cursor-pointer flex items-center gap-0.5"
              >
                <span>ML Extract</span>
                <ExternalLinkIcon className="w-2.5 h-2.5" />
              </button>
            )}

            {onOpenGapMatrix && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenGapMatrix();
                }}
                title="Inspect in Research Gap Heatmap Matrix"
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 hover:text-slate-900 transition-colors cursor-pointer"
              >
                <span>Gaps</span>
              </button>
            )}

            {onAskAssistant && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onAskAssistant();
                }}
                title="Investigate with Grounded Scientific AI Assistant"
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 hover:text-orange-800 transition-colors cursor-pointer flex items-center gap-0.5"
              >
                <span>Ask AI</span>
                <SparklesIcon className="w-2.5 h-2.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
