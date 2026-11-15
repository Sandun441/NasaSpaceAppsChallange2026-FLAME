import React, { useState } from 'react';

/**
 * PromptGapResultsCard
 * Visual presentation of research-gap detection results derived from natural-language inquiry.
 * Complies with Phase F4 Step 3 UX layout mandate:
 * 1. Compact interpretation summary
 * 2. Interactive parameter-space coverage chart
 * 3. Top 3–5 relevant research-gap cards with heuristic priority disclosures
 * 4. Concise evidence-backed observations
 * 5. Expandable methodology, scientific limitations & citations
 */
export function PromptGapResultsCard({ promptResponse, onSelectGap, onNavigateSubTab }) {
  const [showDisclosures, setShowDisclosures] = useState(false);

  if (!promptResponse) return null;

  const specData = promptResponse.specialist_data || {};
  const coverageStatus = specData.coverage_status || 'covered';
  const matchedRuns = specData.matched_usable_runs_count ?? 0;
  const applicableGaps = specData.applicable_gap_findings || [];
  const filters = specData.filters || {};

  // Status configuration
  const statusConfig = {
    covered: {
      label: 'Empirical Evidence Available',
      badgeClass: 'bg-emerald-50 border-emerald-200 text-emerald-800',
      dotClass: 'bg-emerald-500',
    },
    sparse: {
      label: 'Sparse Evidence (< 5 Runs)',
      badgeClass: 'bg-amber-50 border-amber-200 text-amber-800',
      dotClass: 'bg-amber-500',
    },
    coverage_gap: {
      label: 'Empirical Coverage Gap (0 Runs in FLAME)',
      badgeClass: 'bg-rose-50 border-rose-200 text-rose-800',
      dotClass: 'bg-rose-500 animate-pulse',
    },
    unsupported_query: {
      label: 'Free-Text Inquiry',
      badgeClass: 'bg-slate-100 border-slate-200 text-slate-700',
      dotClass: 'bg-slate-400',
    },
  }[coverageStatus] || {
    label: coverageStatus.replace('_', ' ').toUpperCase(),
    badgeClass: 'bg-slate-100 border-slate-200 text-slate-700',
    dotClass: 'bg-slate-400',
  };

  // Coverage distribution data for visual chart
  const regimes = [
    { label: 'Low O₂ (<21%)', runs: 33, status: 'covered', color: '#10b981' },
    { label: 'Normal O₂ (21%)', runs: 91, status: 'covered', color: '#06b6d4' },
    { label: 'Elevated O₂ (21-30%)', runs: 5, status: 'sparse', color: '#f59e0b' },
    { label: 'Hyperoxic (>34%)', runs: 0, status: 'gap', color: '#f43f5e' },
    { label: 'Partial Lunar (0.16g)', runs: 0, status: 'gap', color: '#f43f5e' },
    { label: 'Quiescent Flow (<1cm/s)', runs: 1, status: 'sparse', color: '#f59e0b' },
  ];

  return (
    <div className="space-y-5 p-5 rounded-2xl bg-white border border-slate-200 shadow-sm animate-in fade-in duration-200">
      {/* 1. Compact Interpretation Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div className="flex flex-wrap items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
          <h3 className="text-sm font-semibold text-slate-900 tracking-wide">
            Research-Gap Coverage Evaluation
          </h3>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border flex items-center gap-1.5 ${statusConfig.badgeClass}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${statusConfig.dotClass}`} />
            <span>{statusConfig.label}</span>
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600">
            {matchedRuns} Matched Usable Runs
          </span>
        </div>

        <div className="text-[11px] font-mono text-slate-500 flex items-center gap-2">
          <span>Inquiry:</span>
          <span className="text-orange-600 italic max-w-md truncate">
            "{promptResponse.objective}"
          </span>
        </div>
      </div>

      {/* Structured Filter Pills */}
      {Object.keys(filters).length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="text-slate-500 text-[11px]">Evaluated Conditions:</span>
          {filters.gravity && (
            <span className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-sky-800 text-[11px]">
              Gravity: {filters.gravity}
            </span>
          )}
          {filters.oxygen_regime && (
            <span className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-emerald-800 text-[11px]">
              Oxygen: {filters.oxygen_regime}
            </span>
          )}
          {filters.airflow_regime && (
            <span className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-amber-800 text-[11px]">
              Airflow: {filters.airflow_regime}
            </span>
          )}
          {filters.fuel_family && (
            <span className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-purple-800 text-[11px]">
              Fuel: {filters.fuel_family}
            </span>
          )}
          {filters.parameter && (
            <span className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-rose-800 text-[11px]">
              Channel: {filters.parameter}
            </span>
          )}
        </div>
      )}

      {/* 2. Interactive Parameter-Space Coverage Bar Chart */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h4 className="text-xs font-bold font-mono text-slate-900 flex items-center gap-2">
              <span>Microgravity Flammability Parameter Space Coverage</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                133 Indexed Flight Experiments
              </span>
            </h4>
            <p className="text-[11px] font-mono text-slate-500 mt-0.5">
              Empirical run distribution across combustion regimes. Zero-run bins highlight critical safety gaps.
            </p>
          </div>
          <div className="flex items-center gap-3 text-[10px] font-mono">
            <span className="flex items-center gap-1 text-emerald-700">
              <span className="w-2 h-2 rounded bg-emerald-500" /> Covered
            </span>
            <span className="flex items-center gap-1 text-amber-700">
              <span className="w-2 h-2 rounded bg-amber-500" /> Sparse (&lt;5)
            </span>
            <span className="flex items-center gap-1 text-rose-700">
              <span className="w-2 h-2 rounded bg-rose-500" /> Gap (0 runs)
            </span>
          </div>
        </div>

        {/* SVG Bar Chart */}
        <div className="pt-2">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {regimes.map((r, i) => {
              const maxRuns = 91;
              const barHeightPct = r.runs === 0 ? 4 : Math.max(10, Math.round((r.runs / maxRuns) * 100));
              const isZero = r.runs === 0;

              return (
                <div
                  key={i}
                  className={`p-3 rounded-xl border flex flex-col justify-between transition-all ${
                    isZero
                      ? 'bg-rose-50 border-rose-200 hover:border-rose-300'
                      : r.runs < 5
                      ? 'bg-amber-50 border-amber-200 hover:border-amber-300'
                      : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                  }`}
                >
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono font-semibold block text-slate-800 truncate" title={r.label}>
                      {r.label}
                    </span>
                    <span
                      className={`text-xs font-bold font-mono ${
                        isZero ? 'text-rose-700' : r.runs < 5 ? 'text-amber-700' : 'text-slate-800'
                      }`}
                    >
                      {isZero ? '0 Runs (GAP)' : `${r.runs} Runs`}
                    </span>
                  </div>

                  {/* Visual Bar Indicator */}
                  <div className="mt-3 w-full bg-slate-200/60 rounded-full h-2 overflow-hidden border border-slate-200">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isZero ? 'bg-rose-500/80 w-1' : r.runs < 5 ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${barHeightPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. Top 3–5 Relevant Research-Gap Cards */}
      {applicableGaps.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-orange-700 font-bold flex items-center gap-1.5">
              <span>🔍</span> Relevant Ranked Research-Gap Findings ({applicableGaps.length})
            </span>
            <span className="text-slate-500 text-[10px]">
              Classified under 6 Canonical Taxonomy Types • Disclosed Heuristic Priorities
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {applicableGaps.map((gap) => {
              const gapTypeLabel = (gap.gap_type || 'coverage_gap').replace('_', ' ');
              const priority = gap.priority_score ?? 'N/A';

              return (
                <div
                  key={gap.finding_id}
                  className="p-4 rounded-xl bg-white border border-slate-200 hover:border-orange-300 transition-all space-y-2.5 flex flex-col justify-between group shadow-xs"
                >
                  <div>
                    {/* Card Top Badges */}
                    <div className="flex flex-wrap items-center justify-between gap-1.5 mb-1.5">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-semibold">
                        {gap.finding_id}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-50 border border-orange-200 text-orange-800 uppercase">
                        {gapTypeLabel}
                      </span>
                      <span
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600"
                        title="Heuristic priority score calculated from risk, uncertainty, and mission impact weights. Not a certified risk metric."
                      >
                        Priority: {priority}/100 <span className="text-[9px] text-slate-400">(Heuristic)</span>
                      </span>
                    </div>

                    {/* Title */}
                    <h5 className="text-xs font-bold text-slate-900 group-hover:text-orange-600 transition-colors leading-snug">
                      {gap.title}
                    </h5>

                    {/* Scientific Significance / Explanation */}
                    <p className="text-[11px] text-slate-600 leading-relaxed mt-1.5">
                      {gap.description || gap.scientific_significance || 'Empirical combustion data gap identified in indexed NASA flight archives.'}
                    </p>
                  </div>

                  {/* Card Bottom Meta & Action */}
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span>
                      {gap.affected_datasets && gap.affected_datasets.length > 0
                        ? `Scope: ${gap.affected_datasets.slice(0, 2).join(', ')}`
                        : 'Scope: NASA FLAME Global Catalog'}
                    </span>
                    <button
                      onClick={() => onSelectGap && onSelectGap(gap)}
                      className="text-orange-600 hover:text-orange-700 font-semibold transition-colors cursor-pointer flex items-center gap-1"
                    >
                      <span>Inspect Details</span>
                      <span>→</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Concise Evidence-Backed Observations (Step 4 Mandate: 2–3 Bullets) */}
      {promptResponse.key_findings && promptResponse.key_findings.length > 0 && (
        <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-800 flex items-center gap-1.5 font-mono">
              <span>✓</span> Empirical Coverage Observations
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              {promptResponse.key_findings.length} findings
            </span>
          </div>
          <ul className="space-y-1.5 text-xs text-slate-800 font-sans">
            {promptResponse.key_findings.map((f, i) => (
              <li key={i} className="flex items-start gap-2 leading-relaxed">
                <span className="text-emerald-600 mt-0.5">•</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 5. Expandable Methodology, Scientific Limitations & Citations */}
      <div className="pt-2 border-t border-slate-200">
        <button
          onClick={() => setShowDisclosures(!showDisclosures)}
          className="text-xs text-orange-600 hover:text-orange-700 font-mono cursor-pointer flex items-center gap-1.5"
        >
          <span>{showDisclosures ? 'Hide Scientific Methodology & Safeguards ▲' : 'Show Scientific Methodology & Safeguards ▼'}</span>
        </button>

        {showDisclosures && (
          <div className="mt-3 p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs font-mono">
            {/* Epistemic Disclosures */}
            <div>
              <span className="text-amber-800 font-semibold block mb-1">⚠️ Epistemic Disclosures & Scientific Safeguards:</span>
              <ul className="list-disc list-inside space-y-1 text-slate-700 text-[11px]">
                {promptResponse.scientific_caveats?.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>

            {/* Citations */}
            {promptResponse.provenance_citations && promptResponse.provenance_citations.length > 0 && (
              <div>
                <span className="text-slate-600 font-semibold block mb-1">Authoritative NASA Provenance Sources:</span>
                <div className="flex flex-wrap gap-2">
                  {promptResponse.provenance_citations.map((cit) => (
                    <span
                      key={cit.id}
                      className="px-2.5 py-1 rounded bg-white border border-slate-200 text-slate-700 text-[11px]"
                    >
                      {cit.title} ({cit.reference}) • {cit.grounding_level}
                    </span>
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
