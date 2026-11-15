import React, { useState } from 'react';

/**
 * PromptEarthResultsCard
 * Visual-first result layout for Prompt-Driven Earth Applications Research (Phase F5).
 * Follows F3/F4 architecture:
 * Prompt Interpretation -> Matched Evidence Cards -> 5-Step Connection Bridge Preview -> 2-3 Concise Findings -> Expandable Safeguards & Provenance.
 */
export function PromptEarthResultsCard({
  result,
  onReset,
  onNavigate,
  onSelectCategory,
  onSelectEvidence,
  onOpenBridge,
}) {
  const [isDisclosuresOpen, setIsDisclosuresOpen] = useState(false);

  if (!result) return null;

  const {
    objective,
    interpreted_intent,
    specialist_data = {},
    key_findings = [],
    scientific_caveats = [],
    provenance_citations = [],
    suggested_actions = [],
  } = result;

  const matchedRecords = specialist_data.matched_records || [];
  const totalCount = specialist_data.total_catalog_count || 11;
  const canonicalCounts = specialist_data.canonical_counts || {
    supported_research_implication: 10,
    exploratory_hypothesis: 1,
    documented_application: 0,
  };
  const primaryEvidenceId = specialist_data.primary_evidence_id;
  const primaryCategoryId = specialist_data.primary_category_id;
  const bridgeData = specialist_data.bridge_data;

  return (
    <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-6 transition-all animate-in fade-in duration-300">
      {/* 1. Header Strip: Interpretation & Canonical Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="space-y-1.5 max-w-3xl">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
              Earth Applications Research Interpretation
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-orange-50 text-orange-700 border border-orange-200 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
              {matchedRecords.length} OF {totalCount} AUDITED EVIDENCE RECORDS
            </span>

            {/* Dynamic Canonical Counts Badge */}
            <div className="flex items-center gap-1.5 text-[10px] font-mono bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full text-slate-700">
              <span className="text-emerald-700 font-bold">{canonicalCounts.supported_research_implication} Supported</span>
              <span className="text-slate-300">•</span>
              <span className="text-amber-700 font-bold">{canonicalCounts.exploratory_hypothesis} Exploratory</span>
              <span className="text-slate-300">•</span>
              <span className="text-slate-600">{canonicalCounts.documented_application} Documented</span>
            </div>
          </div>

          <p className="text-sm font-medium text-slate-900 italic leading-snug">
            &ldquo;{objective}&rdquo;
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {primaryCategoryId && onSelectCategory && (
            <button
              onClick={() => onSelectCategory(primaryCategoryId)}
              className="px-3 py-1.5 rounded-lg text-xs font-mono font-medium text-orange-700 bg-orange-50 hover:bg-orange-100 border border-orange-200 transition-colors cursor-pointer"
              title="Filter explorer to primary matched category"
            >
              Filter Explorer Domain
            </button>
          )}
          {onReset && (
            <button
              onClick={onReset}
              className="px-2.5 py-1.5 rounded-lg text-xs font-mono text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-colors cursor-pointer"
              title="Reset prompt result view"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* 2. Matched Evidence Cards */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
            Audited Terrestrial Evidence Records
          </h4>
          <span className="text-[11px] font-mono text-slate-500">
            Source Grounding: Locally Audited NASA Flight Archives
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {matchedRecords.slice(0, 3).map((ev) => {
            const isExploratory = ev.evidence_classification === 'exploratory_hypothesis';
            return (
              <div
                key={ev.id}
                className={`p-3.5 rounded-xl bg-slate-50 border transition-all flex flex-col justify-between space-y-3 ${
                  primaryEvidenceId === ev.id ? 'border-orange-400 shadow-sm' : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-1.5 flex-wrap">
                    <span className="font-mono text-[10px] text-orange-700 bg-orange-50 px-2 py-0.5 rounded border border-orange-200">
                      {ev.id}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                        isExploratory
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      }`}
                    >
                      {isExploratory ? 'Exploratory Hypothesis' : 'Supported Implication'}
                    </span>
                  </div>

                  <div>
                    <h5 className="text-xs font-bold text-slate-900 leading-snug line-clamp-1">{ev.title}</h5>
                    <p className="text-[10px] font-mono text-slate-500">
                      {ev.investigation_name || ev.investigation_id} • {ev.category_title || ev.category_id}
                    </p>
                  </div>

                  <p className="text-xs text-slate-700 leading-relaxed line-clamp-2">
                    {ev.scientific_finding}
                  </p>

                  {ev.proposed_terrestrial_relevance && (
                    <div className="p-2 rounded bg-white border border-slate-200 text-[11px] text-slate-700 leading-snug line-clamp-2">
                      <span className="font-semibold text-orange-600">Earth Relevance:</span>{' '}
                      {ev.proposed_terrestrial_relevance}
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-200 flex items-center justify-between gap-2">
                  <button
                    onClick={() => onSelectEvidence && onSelectEvidence(ev.id)}
                    className="text-[10px] font-mono text-orange-600 hover:text-orange-700 cursor-pointer"
                  >
                    Inspect Detail &rarr;
                  </button>
                  <button
                    onClick={() => onOpenBridge && onOpenBridge(ev.id)}
                    className="text-[10px] font-mono text-orange-600 hover:text-orange-700 cursor-pointer font-semibold"
                  >
                    Open Bridge &rarr;
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. 5-Step Research Connection Bridge Preview */}
      {bridgeData && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                Physical Research Connection Bridge (5-Step Chain)
              </h4>
              <p className="text-[11px] font-mono text-slate-500 truncate max-w-xl">
                Primary Grounded Finding: <span className="text-orange-700 font-semibold">[{bridgeData.evidence_id}] {bridgeData.title}</span>
              </p>
            </div>

            {onOpenBridge && (
              <button
                onClick={() => onOpenBridge(bridgeData.evidence_id)}
                className="px-3 py-1.5 rounded-lg text-xs font-mono font-medium text-orange-700 bg-orange-50 hover:bg-orange-100 border border-orange-200 transition-colors cursor-pointer shrink-0"
              >
                Open Full 5-Step Bridge Tab &rarr;
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 pt-1">
            {bridgeData.steps.map((step) => (
              <div
                key={step.number}
                className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-1.5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-orange-600">
                      Step {step.number}
                    </span>
                    <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-100 text-slate-600 truncate max-w-[80px]">
                      {step.badge}
                    </span>
                  </div>
                  <div className="text-[11px] font-semibold text-slate-900 leading-tight mt-1">
                    {step.title}
                  </div>
                </div>

                <div className="text-[10px] text-slate-600 line-clamp-3 leading-snug">
                  {step.scientific_finding ||
                    step.physical_mechanism ||
                    step.proposed_terrestrial_relevance ||
                    step.earth_transfer_limitations ||
                    step.source_reference}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Concise Scientific Findings */}
      {key_findings.length > 0 && (
        <div className="space-y-2.5">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
            Concise Scientific Research Takeaways
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {key_findings.map((finding, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed flex flex-col justify-between"
              >
                <div>
                  <span className="text-[10px] font-mono font-bold text-indigo-600 block mb-1">
                    Takeaway {idx + 1}
                  </span>
                  <p>{finding}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Expandable Scientific Safeguards & Provenance */}
      <div className="border-t border-slate-100 pt-3">
        <button
          onClick={() => setIsDisclosuresOpen((prev) => !prev)}
          className="text-xs font-mono text-slate-600 hover:text-slate-900 transition-colors flex items-center gap-2 cursor-pointer w-full text-left"
        >
          <span className="w-3.5 h-3.5 flex items-center justify-center font-bold text-slate-600 border border-slate-300 rounded text-[10px]">
            {isDisclosuresOpen ? '−' : '+'}
          </span>
          <span>
            {isDisclosuresOpen ? 'Hide' : 'Show'} Scientific Transfer Caveats, Local Adoption Audit & Citations ({provenance_citations.length})
          </span>
        </button>

        {isDisclosuresOpen && (
          <div className="mt-3.5 space-y-3.5 text-xs text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200 animate-in fade-in duration-200">
            {/* Caveats */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-bold uppercase text-amber-700 tracking-wider">
                Scientific Transfer Limitations & Epistemic Boundaries
              </span>
              <ul className="list-disc pl-4 space-y-1 text-slate-700 text-xs leading-relaxed">
                {scientific_caveats.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>

            {/* Retrieval Audit Notice */}
            {specialist_data.unintended_retrieval_limit_audit && (
              <div className="p-2.5 rounded bg-white border border-slate-200 text-[11px] font-mono space-y-1 text-slate-600">
                <span className="font-bold text-sky-700">Catalog Retrieval Audit Notice:</span>
                <p>{specialist_data.unintended_retrieval_limit_audit}</p>
              </div>
            )}

            {/* Citations */}
            {provenance_citations.length > 0 && (
              <div className="space-y-1.5 pt-2 border-t border-slate-200">
                <span className="text-[10px] font-mono font-bold uppercase text-orange-600 tracking-wider">
                  Traceable Source Citations & References
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {provenance_citations.map((cit) => (
                    <div
                      key={cit.id}
                      className="p-2 rounded bg-white border border-slate-200 text-[11px] font-mono space-y-0.5"
                    >
                      <div className="font-semibold text-slate-900 truncate">{cit.title}</div>
                      <div className="text-slate-500 text-[10px]">
                        Investigation: <span className="text-orange-600">{cit.investigation}</span> • Tier:{' '}
                        <span className="text-amber-700">{cit.grounding_level}</span>
                      </div>
                      <div className="text-slate-400 text-[10px] truncate">
                        Source: {cit.reference}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
