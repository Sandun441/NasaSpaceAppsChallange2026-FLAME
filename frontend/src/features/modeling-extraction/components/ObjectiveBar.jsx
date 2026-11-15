import React from 'react';
import { Button } from '../../../components/common/Button';

const PROMPT_TEMPLATES = [
  {
    label: 'BASS-II: Predict ΔO₂ from Flow & Fuel',
    query: 'Predict oxygen consumption delta using airflow velocity and fuel material in microgravity.',
  },
  {
    label: 'Saffire-III: Peak Flame Temp',
    query: 'Extract Saffire peak plume temperature from duct flow velocity and pressure.',
  },
  {
    label: 'Feasibility Check: Flame Spread Rate',
    query: 'I want to develop a model to predict flame spread rate using oxygen concentration, airflow velocity, and fuel material.',
  },
  {
    label: 'BASS-II: CO Emission from O₂ & Fan',
    query: 'Predict final CO emission from initial oxygen concentration and fan display.',
  },
  {
    label: 'Cygnus: Smoke Detector Obscuration',
    query: 'Extract smoke detector obscuration signals and cabin pressure from Cygnus telemetry.',
  },
];

export function ObjectiveBar({
  query,
  onQueryChange,
  onSubmit,
  isLoading,
  onSelectTemplate,
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (query.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm relative">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
            Natural-Language Research Objective
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Describe your machine learning goal. The engine verifies feature availability, assesses target measurability, and audits leakage risks.
          </p>
        </div>
        <span className="text-[11px] font-mono text-orange-700 bg-orange-50 px-2 py-0.5 rounded border border-orange-200 font-semibold">
          Deterministic ML Engine
        </span>
      </div>

      {/* Main Prompt Bar */}
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. I want to develop a model to predict flame spread rate using oxygen concentration, airflow velocity, and fuel material."
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition-all font-sans"
          />
          {query && (
            <button
              type="button"
              onClick={() => onQueryChange('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 text-xs px-1 py-0.5"
            >
              ✕
            </button>
          )}
        </div>

        <Button
          onClick={onSubmit}
          disabled={!query.trim() || isLoading}
          variant="accent"
          size="md"
          className="whitespace-nowrap bg-orange-500 hover:bg-orange-600 text-white font-medium"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              Analyzing Objective...
            </span>
          ) : (
            'Interpret & Match Data'
          )}
        </Button>
      </div>

      {/* Quick Prompt Chips */}
      <div className="mt-3.5 pt-3 border-t border-slate-200 flex items-center gap-1.5 flex-wrap">
        <span className="text-[11px] font-mono text-slate-500 mr-1">Quick Objectives:</span>
        {PROMPT_TEMPLATES.map((tmpl, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectTemplate(tmpl.query)}
            className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-slate-300 text-slate-700 hover:text-orange-600 transition-colors font-sans cursor-pointer text-left"
          >
            {tmpl.label}
          </button>
        ))}
      </div>
    </div>
  );
}
