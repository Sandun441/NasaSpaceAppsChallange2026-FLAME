import React from 'react';
import { PSI_METADATA_PRIMER } from '../../data/psiData';

export function MenuDrawer({ isOpen, onClose, onSelectTab, onOpenKnowledgeModal }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-md bg-white border-l border-slate-200 p-6 shadow-2xl flex flex-col justify-between overflow-y-auto text-slate-700 z-10 animate-in slide-in-from-right duration-200">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-200">
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded bg-orange-50 border border-orange-200 text-orange-600 flex items-center justify-center font-bold text-xs">
                Δ
              </div>
              <div>
                <h2 className="text-sm font-semibold text-slate-900 tracking-tight">FLAME System Menu</h2>
                <p className="text-[11px] text-slate-500 font-mono">NASA Open Science Explorer</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-800 transition-colors text-sm cursor-pointer"
              aria-label="Close menu"
            >
              ✕
            </button>
          </div>

          {/* Quick Navigation Section */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-500">Main Platform Views</h3>
            <div className="grid grid-cols-1 gap-1.5">
              <button
                onClick={() => { onSelectTab('home'); onClose(); }}
                className="w-full text-left px-3 py-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-between group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-medium text-slate-900 group-hover:text-orange-600 flex items-center gap-1.5">
                    <span>Home</span>
                    <span className="text-[9px] px-1 rounded bg-orange-50 text-orange-700 border border-orange-200 font-mono">AI Assistant</span>
                  </div>
                  <div className="text-[11px] text-slate-500">Scientific AI Assistant, fire simulator & flight intelligence</div>
                </div>
                <span className="text-xs text-slate-400 group-hover:text-slate-700">→</span>
              </button>

              {onOpenKnowledgeModal && (
                <button
                  onClick={() => { onOpenKnowledgeModal(); onClose(); }}
                  className="w-full text-left px-3 py-2.5 rounded-lg bg-orange-50/50 hover:bg-orange-50 border border-orange-200 transition-colors flex items-center justify-between group cursor-pointer"
                >
                  <div>
                    <div className="text-xs font-medium text-slate-900 group-hover:text-orange-600 flex items-center gap-1.5">
                      <span>Dynamic Knowledge Ingestion</span>
                      <span className="text-[9px] px-1 rounded bg-orange-100 text-orange-800 border border-orange-200 font-mono">Upload RAG</span>
                    </div>
                    <div className="text-[11px] text-slate-500">Upload CSV/PDF/text datasets into live knowledge base</div>
                  </div>
                  <span className="text-xs text-orange-500 group-hover:text-orange-700">→</span>
                </button>
              )}

              <button
                onClick={() => { onSelectTab('dataset-explorer'); onClose(); }}
                className="w-full text-left px-3 py-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-between group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-medium text-slate-900 group-hover:text-orange-600 flex items-center gap-1.5">
                    <span>NASA Dataset Explorer</span>
                    <span className="text-[9px] px-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">Live API</span>
                  </div>
                  <div className="text-[11px] text-slate-500">11 flight datasets, metadata inspection & live telemetry tables</div>
                </div>
                <span className="text-xs text-slate-400 group-hover:text-slate-700">→</span>
              </button>

              <button
                onClick={() => { onSelectTab('experiment-comparison'); onClose(); }}
                className="w-full text-left px-3 py-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-between group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-medium text-slate-900 group-hover:text-orange-600 flex items-center gap-1.5">
                    <span>Experiment Comparison</span>
                    <span className="text-[9px] px-1 rounded bg-sky-50 text-sky-700 border border-sky-200 font-mono">Dual-Engine</span>
                  </div>
                  <div className="text-[11px] text-slate-500">Cross-experiment analytics, event alignment & empirical deltas</div>
                </div>
                <span className="text-xs text-slate-400 group-hover:text-slate-700">→</span>
              </button>

              <button
                onClick={() => { onSelectTab('modeling-extraction'); onClose(); }}
                className="w-full text-left px-3 py-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-between group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-medium text-slate-900 group-hover:text-orange-600 flex items-center gap-1.5">
                    <span>Predictive-Modeling Data Extraction</span>
                    <span className="text-[9px] px-1 rounded bg-sky-50 text-sky-700 border border-sky-200 font-mono">ML Ready</span>
                  </div>
                  <div className="text-[11px] text-slate-500">Discover, audit leakage risks & export NASA combustion records for ML</div>
                </div>
                <span className="text-xs text-slate-400 group-hover:text-slate-700">→</span>
              </button>

              <button
                onClick={() => { onSelectTab('gap-detection'); onClose(); }}
                className="w-full text-left px-3 py-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-between group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-medium text-slate-900 group-hover:text-orange-600">Research Gap Detection</div>
                  <div className="text-[11px] text-slate-500">Coverage heatmap & partial-gravity unexplored frontiers</div>
                </div>
                <span className="text-xs text-slate-400 group-hover:text-slate-700">→</span>
              </button>

              <button
                onClick={() => { onSelectTab('equipment-research'); onClose(); }}
                className="w-full text-left px-3 py-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-between group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-medium text-slate-900 group-hover:text-orange-600">Fire-Safety Equipment Research</div>
                  <div className="text-[11px] text-slate-500">Connecting flight science to sensors & extinguishers</div>
                </div>
                <span className="text-xs text-slate-400 group-hover:text-slate-700">→</span>
              </button>

              <button
                onClick={() => { onSelectTab('earth-applications'); onClose(); }}
                className="w-full text-left px-3 py-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-between group cursor-pointer"
              >
                <div>
                  <div className="text-xs font-medium text-slate-900 group-hover:text-orange-600">Earth Applications</div>
                  <div className="text-[11px] text-slate-500">Industrial safety, wildfire modeling & clean suppression</div>
                </div>
                <span className="text-xs text-slate-400 group-hover:text-slate-700">→</span>
              </button>
            </div>
          </div>

          {/* NASA PSI Data Architecture Guide */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-sky-700 font-semibold">
                NASA PSI Data Structure
              </span>
              <a 
                href={PSI_METADATA_PRIMER.url} 
                target="_blank" 
                rel="noreferrer" 
                className="text-[10px] text-slate-500 hover:text-slate-900 underline font-mono"
              >
                psi.nasa.gov ↗
              </a>
            </div>

            <div className="space-y-2 text-[11px] text-slate-700 leading-relaxed">
              <div className="space-y-1">
                <span className="text-emerald-700 font-medium block">✓ In Raw Flight Records:</span>
                <p className="text-slate-500 text-[10.5px]">
                  Thermocouple temperature arrays, chamber pressure logs, radiometer voltages, calibrated video sequences, and duct flow anemometer readings.
                </p>
              </div>

              <div className="space-y-1 pt-1 border-t border-slate-200">
                <span className="text-amber-700 font-medium block">⚠ In Secondary Publications:</span>
                <p className="text-slate-500 text-[10.5px]">
                  Derived chemical kinetic rate equations, soot volume fraction maps, and asymptotic extinction curves.
                </p>
              </div>

              <div className="space-y-1 pt-1 border-t border-slate-200">
                <span className="text-rose-700 font-medium block">✕ Unavailable in PSI:</span>
                <p className="text-slate-500 text-[10.5px]">
                  Steady-state long-duration burning in continuous lunar (0.16g) or Martian (0.38g) gravity. Flight data is microgravity (~0g) or 1g ground control.
                </p>
              </div>
            </div>
          </div>

          {/* Scientific Disclaimer Card */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600 space-y-1.5">
            <div className="font-semibold text-slate-900 flex items-center gap-1.5">
              <span className="text-amber-600">ℹ</span> Rigorous Scientific Separation
            </div>
            <p className="leading-relaxed">
              FLAME enforces strict separation between raw empirical NASA flight records and secondary engineering interpretations. A lack of direct flight data in PSI does not imply an absence of international ground or parabolic research.
            </p>
          </div>
        </div>

        {/* Footer info */}
        <div className="pt-6 border-t border-slate-200 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
            <span className="font-semibold text-slate-800">FLAME v1.0</span>
            <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
              NASA PSI Platform
            </span>
          </div>
          <p className="text-[10px] text-slate-500">
            NASA Space Apps Challenge 2026 • Biological & Physical Sciences Open Science Repository
          </p>
        </div>
      </div>
    </div>
  );
}
