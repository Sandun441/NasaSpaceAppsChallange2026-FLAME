import React from 'react';

export function EngineeringInsights({ insights }) {
  if (!insights) return null;

  const directEvidence = insights.direct_experimental_evidence || [];
  const derivedAnalysis = insights.derived_numerical_analysis || [];
  const scientificInterpretation = insights.scientific_interpretation || [];
  const designImplications = insights.engineering_design_implications || [];
  const limitations = insights.evidence_limitations || [];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-3 border-b border-slate-100">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-orange-600">
            Epistemic Synthesis & Flight Translation
          </span>
          <h3 className="text-sm sm:text-base font-semibold text-slate-900">
            5-Tier Scientific Evidence & Engineering Insights
          </h3>
        </div>
        <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
          Scientifically Audited
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Tier 1: Direct Experimental Evidence */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-emerald-700 font-mono">
              Tier 1 • Direct Experimental Observations
            </h4>
          </div>
          <p className="text-[11px] text-slate-500 font-sans">
            Empirical observations directly measured in verified microgravity burns:
          </p>
          <ul className="space-y-1.5 pt-1">
            {directEvidence.map((item, idx) => (
              <li key={idx} className="text-xs text-slate-800 flex items-start gap-2 leading-relaxed">
                <span className="text-emerald-600 font-mono text-[11px] shrink-0">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Tier 2: Derived Numerical Analysis */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-orange-500" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-orange-700 font-mono">
              Tier 2 • Derived Numerical Analysis
            </h4>
          </div>
          <p className="text-[11px] text-slate-500 font-sans">
            Metrics calculated mathematically from calibrated flight channels without imputation:
          </p>
          <ul className="space-y-1.5 pt-1">
            {derivedAnalysis.map((item, idx) => (
              <li key={idx} className="text-xs text-slate-800 flex items-start gap-2 leading-relaxed">
                <span className="text-orange-600 font-mono text-[11px] shrink-0">📐</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Tier 3: Scientific Interpretation */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-500" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-700 font-mono">
              Tier 3 • Scientific Combustion Interpretation
            </h4>
          </div>
          <p className="text-[11px] text-slate-500 font-sans">
            Fundamental microgravity physics driving observable fire behaviors:
          </p>
          <ul className="space-y-1.5 pt-1">
            {scientificInterpretation.map((item, idx) => (
              <li key={idx} className="text-xs text-slate-800 flex items-start gap-2 leading-relaxed">
                <span className="text-indigo-600 font-mono text-[11px] shrink-0">🔬</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Tier 4: Engineering Design Implications */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-700 font-mono">
              Tier 4 • Spacecraft Equipment Design Implications
            </h4>
          </div>
          <p className="text-[11px] text-slate-500 font-sans">
            Actionable architecture considerations for spacecraft life-support engineers:
          </p>
          <ul className="space-y-1.5 pt-1">
            {designImplications.map((item, idx) => (
              <li key={idx} className="text-xs text-slate-800 flex items-start gap-2 leading-relaxed">
                <span className="text-amber-600 font-mono text-[11px] shrink-0">🛠️</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Tier 5: Epistemic Boundaries & Scientific Limitations */}
      {limitations.length > 0 && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-rose-700 font-mono">
              Tier 5 • Epistemic Boundaries & Missing Evidence Disclosures
            </h4>
          </div>
          <p className="text-[11px] text-rose-700 font-sans">
            Explicit disclosures of experimental constraints and unindexed regimes:
          </p>
          <ul className="space-y-1 pt-1">
            {limitations.map((item, idx) => (
              <li key={idx} className="text-xs text-rose-900 flex items-start gap-2 leading-relaxed">
                <span className="text-rose-600 font-mono text-[11px] shrink-0">⚠️</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
