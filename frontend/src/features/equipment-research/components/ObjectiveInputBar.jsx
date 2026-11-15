import React from 'react';
import { Button } from '../../../components/common/Button';

export function ObjectiveInputBar({
  query,
  onQueryChange,
  onAnalyze,
  isLoading,
  templates = [],
  onSelectTemplate,
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query && query.trim() && !isLoading) {
      onAnalyze(query.trim());
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
      {/* Header & Explanation */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-orange-600">
            Natural-Language Research Objective
          </span>
          <h2 className="text-sm sm:text-base font-semibold text-slate-900">
            Spacecraft Fire-Safety Decision Support & Systems Exploration
          </h2>
        </div>
        <span className="text-[10px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
          Retrieval-Only & API Ready
        </span>
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="e.g. I want to design a more reliable spacecraft smoke detection system. Find relevant NASA experiments, available measurements, research limitations, and potential research directions."
            className="w-full bg-slate-50 border border-slate-200 focus:border-orange-500 rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 font-sans transition-all"
          />
          <div className="absolute right-2 top-2">
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={isLoading || !query.trim()}
              className="bg-orange-500 hover:bg-orange-600 text-white font-semibold px-4 text-xs shadow-sm"
            >
              {isLoading ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Analyzing...</span>
                </span>
              ) : (
                '🔍 Discover Evidence'
              )}
            </Button>
          </div>
        </div>

        {/* Quick-Start Research Templates */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">
            Quick-Start Research Inquiries:
          </span>
          <div className="flex flex-wrap gap-2">
            {templates.map((tpl) => (
              <button
                key={tpl.id}
                type="button"
                onClick={() => onSelectTemplate(tpl)}
                disabled={isLoading}
                className="text-left text-xs bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-orange-300 rounded-lg px-2.5 py-1.5 transition-all text-slate-700 hover:text-slate-900 flex items-center gap-2 group cursor-pointer shadow-xs"
              >
                <span className={`text-[9px] font-mono uppercase px-1.5 py-0.2 rounded border font-semibold ${
                  tpl.category === 'detection'
                    ? 'bg-sky-50 text-sky-800 border-sky-200'
                    : tpl.category === 'prevention'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border-rose-200'
                }`}>
                  {tpl.badge}
                </span>
                <span className="text-[11px] group-hover:text-orange-700 transition-colors">
                  {tpl.label}
                </span>
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
}
