import React from 'react';

export function InterpretationSection() {
  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-orange-50 text-orange-600 border border-orange-200 flex items-center justify-center text-xs font-mono font-bold">
            !
          </div>
          <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
            Research-Gap Interpretation & Epistemic Guidelines
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
          Scientific Rigor Standard
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs leading-relaxed">
        {/* Box 1: Space Exploration Criticality */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <div className="font-semibold text-sky-800 font-mono text-[11px] uppercase tracking-wider flex items-center gap-1.5">
            <span>●</span> Exploration Mission Criticality
          </div>
          <p className="text-slate-700">
            For long-duration lunar surface habitats (Artemis Base Camp) and crewed Mars transit vehicles, cabin fires present the single most hazardous rapid-consequence contingency. Current spacecraft flammability standards were developed primarily using normal 1g upward flame tests (NASA-STD-6001).
          </p>
          <p className="text-slate-500 text-[11px]">
            Without empirical partial-gravity burn physics, habitat engineers must rely on computational fluid dynamics (CFD) extrapolations that may underestimate flammability limits under low-velocity ventilation.
          </p>
        </div>

        {/* Box 2: Rigorous Epistemic Boundary */}
        <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 space-y-2">
          <div className="font-semibold text-amber-800 font-mono text-[11px] uppercase tracking-wider flex items-center gap-1.5">
            <span>⚠</span> Epistemic Boundary Notice
          </div>
          <p className="text-slate-700">
            <strong>Critical Boundary:</strong> A lack of direct partial-gravity flight records in NASA FLAME does <em>not</em> prove that no research on partial gravity exists anywhere in the scientific literature.
          </p>
          <p className="text-amber-900/80 text-[11px]">
            Valuable research exists in short drop-tower tests (2.2s &amp; 5.18s), parabolic aircraft flights (KC-135, Zero-G), and centrifuge rigs. In FLAME, we explicitly tag where indexed flight data ends and where ground-based models or hypotheses begin.
          </p>
        </div>

        {/* Box 3: Engineering Heuristics vs Physical Laws */}
        <div className="p-4 rounded-xl bg-purple-50/70 border border-purple-200 space-y-2">
          <div className="font-semibold text-purple-800 font-mono text-[11px] uppercase tracking-wider flex items-center gap-1.5">
            <span>★</span> Heuristic Scoring Transparency
          </div>
          <p className="text-slate-700">
            Priority scores (0.0 – 10.0) are calculated via a transparent 5-factor engineering heuristic: Coverage Deficiency (3.0), Mission Relevance (2.5), Resolvability (2.0), Metadata Completeness (1.5), and Baseline Readiness (1.0).
          </p>
          <p className="text-slate-500 text-[11px]">
            These scores serve as an engineering triage tool for future flight experiments and dataset ingestions; they are <strong>not</strong> physical combustion constants or validated NASA flight clearances.
          </p>
        </div>
      </div>
    </div>
  );
}
