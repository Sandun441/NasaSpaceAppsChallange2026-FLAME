import React from 'react';
import { HeroSection } from './sections/HeroSection';
import { PillarsSection } from './sections/PillarsSection';
import { InteractiveFireSimulator } from '../simulator';

export function LandingPage({
  onSelectTab,
  onOpenKnowledgeModal,
  initialContext,
  messages,
  setMessages,
  inputQuery,
  setInputQuery,
  activeFinding,
  setActiveFinding,
  activeEarthEvidence,
  setActiveEarthEvidence,
}) {
  return (
    <main className="max-w-5xl w-full mx-auto flex-1 flex flex-col justify-between py-2 sm:py-6 space-y-6 sm:space-y-8">
      <HeroSection
        onSelectTab={onSelectTab}
        initialContext={initialContext}
        messages={messages}
        setMessages={setMessages}
        inputQuery={inputQuery}
        setInputQuery={setInputQuery}
        activeFinding={activeFinding}
        setActiveFinding={setActiveFinding}
        activeEarthEvidence={activeEarthEvidence}
        setActiveEarthEvidence={setActiveEarthEvidence}
      />

      {/* Main Dashboard Interactive Microgravity Fire Simulator (Priority P1) */}
      <section className="w-full pt-1">
        <InteractiveFireSimulator />
      </section>

      {/* Dynamic Knowledge Ingestion Banner (Priority P2) */}
      <section className="w-full bg-gradient-to-r from-orange-50 via-white to-sky-50 border border-slate-200 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs text-left">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Dynamic RAG Knowledge Ingestion
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-orange-100 text-orange-800 border border-orange-200 font-semibold">
              Live Indexing
            </span>
          </div>
          <p className="text-xs text-slate-600 max-w-2xl font-mono">
            Import new flight test telemetry (CSV/TSV/XLSX), publications (PDF), or experimental documentation directly into the live BM25 & dense vector RAG index.
          </p>
        </div>

        {onOpenKnowledgeModal && (
          <button
            type="button"
            onClick={onOpenKnowledgeModal}
            className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-mono font-bold transition-all cursor-pointer shadow-xs shrink-0 flex items-center gap-2"
          >
            <svg className="w-4 h-4 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Open Knowledge Manager →
          </button>
        )}
      </section>

      <PillarsSection onSelectTab={onSelectTab} />
    </main>
  );
}

export { HeroSection } from './sections/HeroSection';
export { PillarsSection } from './sections/PillarsSection';
export { FlameHeroEffect } from './components/FlameHeroEffect';
export { SearchBar } from './components/SearchBar';
export { PillarCard } from './components/PillarCard';
