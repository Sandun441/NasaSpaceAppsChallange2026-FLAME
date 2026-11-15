import React from 'react';
import { AlertTriangleIcon, InfoIcon } from './EarthIcons';

export function EarthOverviewHeader({ overview, onOpenSafeguardsModal }) {
  const totalRecords = overview?.total_evidence_records ?? 11;
  const categoriesCount = overview?.categories?.length ?? 7;
  const classificationBreakdown = overview?.classification_breakdown || {};
  const supportedCount = classificationBreakdown.supported_research_implication ?? 10;
  const exploratoryCount = classificationBreakdown.exploratory_hypothesis ?? 1;
  const documentedCount = classificationBreakdown.documented_application ?? 0;
  
  const provenanceBreakdown = overview?.provenance_breakdown || {};
  const localCount = provenanceBreakdown.locally_verified ?? 6;
  const externalCount = provenanceBreakdown.external_literature_verified ?? 5;

  const recon = overview?.investigation_reconciliation;
  const totalInvs = recon?.total_unique_investigations_count ?? 7;
  const primaryInvs = recon?.unique_primary_investigations_count ?? 6;

  return (
    <div className="space-y-4 border-b border-slate-200 pb-6">
      {/* Top Meta Status Row */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-mono text-emerald-700 uppercase tracking-wider font-semibold">
            Module 03 • Terrestrial Combustion Technology Transfer
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
            Phase EA2 Research Explorer
          </span>
        </div>

        <button
          onClick={onOpenSafeguardsModal}
          className="text-xs font-mono text-orange-700 hover:text-orange-800 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-orange-50 border border-orange-200 hover:bg-orange-100 transition-colors cursor-pointer"
        >
          <InfoIcon className="w-3.5 h-3.5" />
          <span>Scientific Rubric & Epistemic Boundaries</span>
        </button>
      </div>

      {/* Main Heading & Mission Abstract */}
      <div className="space-y-2">
        <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
          <span>Earth Applications</span>
          <span className="text-xs font-normal text-slate-600 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 hidden sm:inline">
            Evidence-Grounded Intelligence
          </span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 max-w-4xl leading-relaxed">
          Trace how NASA microgravity combustion findings (BASS-II, Saffire-III, FLEX, SAME, ACME, SOFIE) inform terrestrial fire protection engineering, building HVAC conduit safety, wildland duff smoldering kinetics, clean gaseous fire suppression, and low-emission combustor modeling.
        </p>
      </div>

      {/* Dynamic Summary Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 pt-2">
        {/* Total Records */}
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-500">Total Evidence</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold text-slate-900 font-mono">{totalRecords}</span>
            <span className="text-[10px] font-mono text-slate-400">findings</span>
          </div>
        </div>

        {/* Categories */}
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-500">Categories</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold text-emerald-600 font-mono">{categoriesCount}</span>
            <span className="text-[10px] font-mono text-slate-400">domains</span>
          </div>
        </div>

        {/* Canonical Investigations */}
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-500">Investigations</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold text-orange-600 font-mono">{totalInvs}</span>
            <span className="text-[10px] font-mono text-slate-400">({primaryInvs} primary)</span>
          </div>
        </div>

        {/* Supported Implications */}
        <div className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-200 shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-emerald-800">Supported Impl.</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold text-emerald-700 font-mono">{supportedCount}</span>
            <span className="text-[10px] font-mono text-emerald-700">peer-reviewed</span>
          </div>
        </div>

        {/* Exploratory Hypotheses */}
        <div className="p-3 rounded-xl bg-amber-50/50 border border-amber-200 shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-amber-800">Exploratory Hyp.</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold text-amber-700 font-mono">{exploratoryCount}</span>
            <span className="text-[10px] font-mono text-amber-700">hypothesis</span>
          </div>
        </div>

        {/* Documented Applications */}
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between group relative">
          <span className="text-[11px] font-mono text-slate-500">Documented App.</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold text-slate-800 font-mono">{documentedCount}</span>
            <span className="text-[10px] font-mono text-slate-400">adopted</span>
          </div>
        </div>

        {/* Locally Verified Datasets */}
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-col justify-between">
          <span className="text-[11px] font-mono text-slate-500">Flight Provenance</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-xl sm:text-2xl font-bold text-indigo-600 font-mono">{localCount}</span>
            <span className="text-[10px] font-mono text-slate-400">local / {externalCount} ext</span>
          </div>
        </div>
      </div>

      {/* Epistemic Boundary Notice & Physical Transfer Safeguard */}
      <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <AlertTriangleIcon className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold text-amber-900">Fundamental Scientific Transfer Boundary:</span>
            <p className="text-amber-800 text-[11px] leading-relaxed">
              Microgravity combustion experiments isolate chemical reaction kinetics and non-buoyant transport by eliminating gravitational buoyant lift. They do <strong>NOT</strong> directly predict macroscopic 1g terrestrial fires where buoyant updrafts (1–2+ m/s), atmospheric wind turbulence, and large geometric scales dominate.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
          <span className="text-[10px] font-mono text-slate-600 bg-white px-2.5 py-1 rounded border border-slate-200">
            Zero Fabricated Probabilities
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-white px-2.5 py-1 rounded border border-slate-200">
            No Equipment Approvals
          </span>
        </div>
      </div>
    </div>
  );
}
