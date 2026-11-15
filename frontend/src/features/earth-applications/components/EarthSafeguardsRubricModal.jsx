import React from 'react';
import {
  ShieldIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  DatabaseIcon,
  InfoIcon,
} from './EarthIcons';

export function EarthSafeguardsRubricModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="max-w-2xl w-full max-h-[85vh] overflow-y-auto rounded-2xl bg-white border border-slate-200 shadow-2xl p-6 space-y-6 text-xs text-slate-700">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-orange-50 text-orange-600 border border-orange-200 flex items-center justify-center">
              <ShieldIcon className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Scientific Rubrics & Epistemic Boundaries
              </h2>
              <p className="text-[11px] text-slate-500 font-mono">
                Phase EA2 Epistemological Grounding Standard
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg bg-slate-100 border border-slate-200 text-slate-500 hover:text-slate-800 flex items-center justify-center text-sm cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* 1. Dimension A: Flight Data Grounding */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <DatabaseIcon className="w-3.5 h-3.5 text-purple-600" />
            <span>Dimension A — Experimental Grounding Levels</span>
          </h3>
          <div className="space-y-1.5 font-mono text-[11px]">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-purple-700 font-bold">locally_verified (Tier 1):</span> Evidence is directly traceable to raw or processed flight telemetry files indexed in NASA FLAME (e.g. Saffire-III, BASS-II, Cygnus).
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-blue-700 font-bold">external_literature_verified (Tier 2):</span> Evidence is verified against published peer-reviewed NASA publications or Technical Memorandums (e.g., NASA/TM—2009-215801 for SAME).
            </div>
          </div>
        </div>

        {/* 2. Dimension B: Terrestrial Validation Status */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircleIcon className="w-3.5 h-3.5 text-emerald-600" />
            <span>Dimension B — Terrestrial Application Validation</span>
          </h3>
          <div className="space-y-1.5 text-[11px]">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-emerald-700 font-bold font-mono">supported_research_implication:</span> Grounded theoretical or physical mechanism connecting microgravity physics to terrestrial fire science. Requires numerical modeling or scaling validation.
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-amber-700 font-bold font-mono">exploratory_hypothesis:</span> Scientifically plausible research hypothesis without dedicated terrestrial experimental validation (e.g., wildland intra-bed smoldering).
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-sky-700 font-bold font-mono">documented_application (Current Count = 0):</span> Requires verified published evidence of actual terrestrial adoption into commercial standards or deployed industrial hardware.
            </div>
          </div>
        </div>

        {/* 3. Why Documented Applications are Currently Zero */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
          <div className="flex items-center gap-2 text-slate-900 font-semibold text-xs">
            <InfoIcon className="w-4 h-4 text-sky-600" />
            <span>Why are Documented Terrestrial Applications currently 0?</span>
          </div>
          <p className="text-[11px] text-slate-600 leading-relaxed">
            NASA microgravity combustion experiments provide foundational chemical and fluid kinetic insights. However, claiming that commercial gas turbine manufacturers or automobile engines have directly integrated microgravity findings into production hardware without verifiable published adoption records represents unsupported marketing hyperbole. FLAME enforces strict scientific honesty: fundamental research implications are categorized as <strong>supported implications</strong>, reserving <strong>documented application</strong> strictly for verified industrial adoption.
          </p>
        </div>

        {/* 4. Physical Transfer Boundaries */}
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
          <div className="flex items-center gap-2 text-amber-900 font-semibold text-xs">
            <AlertTriangleIcon className="w-4 h-4 text-amber-600" />
            <span>Physical Gravity & Scaling Disclaimers</span>
          </div>
          <ul className="text-[11px] text-amber-800 space-y-1 list-disc list-inside leading-relaxed">
            <li><strong>Buoyant Lift Invariance:</strong> Normal 1g fires generate natural buoyant updrafts of 1–2+ m/s that mask the low-speed (&lt;10 cm/s) phenomena isolated in space.</li>
            <li><strong>Scale Extrapolation:</strong> Glovebox experiments (1–2 cm samples) do not directly predict full-scale building structural collapse or macroscale wildfire behavior.</li>
            <li><strong>No Equipment Approval:</strong> NASA FLAME provides decision support and scientific literature bridges; it does NOT certify or approve fire safety equipment for commercial deployment.</li>
          </ul>
        </div>

        {/* Modal Footer */}
        <div className="flex justify-end pt-2 border-t border-slate-100">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-mono font-medium bg-slate-900 text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
}
