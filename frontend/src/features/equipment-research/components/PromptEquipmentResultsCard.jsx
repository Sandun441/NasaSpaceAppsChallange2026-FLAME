import React, { useState } from 'react';

/**
 * PromptEquipmentResultsCard
 * Visual-first result layout for Prompt-Driven Fire-Safety Equipment Research (Phase F5).
 * Follows F3/F4 architecture:
 * Prompt Interpretation -> Verified Evidence Cards -> Measurement Actions/Charts -> 2-3 Concise Findings -> Expandable Safeguards & Provenance.
 */
export function PromptEquipmentResultsCard({ result, onReset, onNavigate, onSelectCategory }) {
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
    visualizations = [],
  } = result;

  const category = specialist_data.category || interpreted_intent?.target_workspace || 'detection';
  const categoryMeta = specialist_data.category_metadata || {};
  const matchedInvs = specialist_data.matched_investigations || [];
  const detectedParams = specialist_data.detected_parameters || [];
  const linkedGaps = specialist_data.linked_research_gaps || [];

  const categoryColorMap = {
    detection: {
      badge: 'bg-orange-50 text-orange-700 border-orange-200',
      pill: 'bg-orange-50 text-orange-700 border-orange-200',
      accent: 'border-slate-200',
      dot: 'bg-orange-500',
    },
    prevention: {
      badge: 'bg-amber-50 text-amber-700 border-amber-200',
      pill: 'bg-amber-50 text-amber-700 border-amber-200',
      accent: 'border-slate-200',
      dot: 'bg-amber-500',
    },
    suppression: {
      badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      pill: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      accent: 'border-slate-200',
      dot: 'bg-emerald-500',
    },
  };

  const style = categoryColorMap[category] || categoryColorMap.detection;

  return (
    <div className={`p-5 rounded-2xl bg-white border ${style.accent} shadow-sm space-y-6 transition-all animate-in fade-in duration-300`}>
      {/* 1. Header Strip: Interpretation Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="space-y-1.5 max-w-3xl">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
              Equipment Research Interpretation
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${style.pill} flex items-center gap-1.5`}>
              <span className={`w-1.5 h-1.5 rounded-full ${style.dot} animate-pulse`} />
              {category.toUpperCase()} DOMAIN
            </span>
            {matchedInvs.length > 0 && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono text-slate-700 bg-slate-100 border border-slate-200">
                {matchedInvs.length} Verified Flight Investigation{matchedInvs.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <p className="text-sm font-medium text-slate-900 italic leading-snug">
            &ldquo;{objective}&rdquo;
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {categoryMeta.id && onSelectCategory && (
            <button
              onClick={() => onSelectCategory(category)}
              className="px-3 py-1.5 rounded-lg text-xs font-mono font-medium text-orange-700 bg-orange-50 hover:bg-orange-100 border border-orange-200 transition-colors cursor-pointer"
              title={`Switch active workspace category to ${category}`}
            >
              Set Active Domain
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

      {/* 2. Verified NASA Flight Evidence Cards */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
            Verified NASA Investigations & Sensor Telemetry
          </h4>
          <span className="text-[11px] font-mono text-slate-500">
            Grounding: Locally Verified Flight Archives
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {matchedInvs.slice(0, 4).map((inv) => (
            <div
              key={inv.id}
              className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 hover:border-orange-300 transition-colors space-y-2.5"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h5 className="text-xs font-bold text-slate-900 leading-snug">{inv.name}</h5>
                  <p className="text-[11px] font-mono text-slate-500">{inv.facility}</p>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-sky-50 text-sky-700 border border-sky-200 shrink-0">
                  {inv.is_locally_indexed ? 'Local Telemetry' : 'External Literature'}
                </span>
              </div>

              {inv.relevance?.[category] && (
                <p className="text-xs text-slate-700 leading-relaxed line-clamp-2">
                  {inv.relevance[category]}
                </p>
              )}

              {/* Verified Physical Sensor Channels */}
              {inv.verified_sensor_channels && inv.verified_sensor_channels.length > 0 && (
                <div className="pt-2 border-t border-slate-200 space-y-1">
                  <div className="text-[10px] font-mono uppercase text-slate-500">
                    Verified Physical Channels:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {inv.verified_sensor_channels.slice(0, 3).map((ch) => (
                      <span
                        key={ch.id}
                        className="px-2 py-0.5 rounded bg-white border border-slate-200 text-[10px] font-mono text-orange-700"
                        title={ch.description}
                      >
                        {ch.label} [{ch.unit}]
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 3. Measurement Telemetry Actions & Visualizations */}
      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Verified Telemetry Navigation & Gap Links
          </h4>
          <span className="text-[10px] font-mono text-slate-500">1-Click Launchers</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {suggested_actions.slice(0, 3).map((act) => (
            <button
              key={act.id}
              onClick={() => onNavigate && onNavigate(act.tab_id, act.payload)}
              className="p-2.5 rounded-lg bg-white hover:bg-orange-50/50 border border-slate-200 hover:border-orange-300 text-left transition-all group cursor-pointer flex flex-col justify-between"
            >
              <div className="space-y-1">
                <div className="text-xs font-semibold text-slate-900 group-hover:text-orange-600 transition-colors">
                  {act.label}
                </div>
                <div className="text-[10px] font-mono text-slate-500 line-clamp-1">
                  Target Tab: {act.tab_id}
                </div>
              </div>
              <div className="pt-2 text-[10px] font-mono text-orange-600 flex items-center gap-1">
                <span>Launch Tool</span>
                <span className="group-hover:translate-x-0.5 transition-transform">&rarr;</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 4. Concise Scientific Research Insights */}
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
                    Finding {idx + 1}
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
            {isDisclosuresOpen ? 'Hide' : 'Show'} Scientific Epistemic Safeguards & Traceable Citations ({provenance_citations.length})
          </span>
        </button>

        {isDisclosuresOpen && (
          <div className="mt-3.5 space-y-3.5 text-xs text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200 animate-in fade-in duration-200">
            {/* Caveats */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-bold uppercase text-amber-700 tracking-wider">
                Epistemic Caveats & Safeguards
              </span>
              <ul className="list-disc pl-4 space-y-1 text-slate-700 text-xs leading-relaxed">
                {scientific_caveats.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>

            {/* Citations */}
            {provenance_citations.length > 0 && (
              <div className="space-y-1.5 pt-2 border-t border-slate-200">
                <span className="text-[10px] font-mono font-bold uppercase text-orange-600 tracking-wider">
                  Traceable Source Provenance
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {provenance_citations.map((cit) => (
                    <div
                      key={cit.id}
                      className="p-2 rounded bg-white border border-slate-200 text-[11px] font-mono space-y-0.5"
                    >
                      <div className="font-semibold text-slate-900 truncate">{cit.title}</div>
                      <div className="text-slate-500 text-[10px]">
                        Investigation: <span className="text-orange-600">{cit.investigation}</span>
                      </div>
                      <div className="text-slate-400 text-[10px] truncate">
                        Ref: {cit.reference}
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
