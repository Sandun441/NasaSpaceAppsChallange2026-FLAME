import React, { useState } from 'react';
import { AlertTriangleIcon } from './EarthIcons';

export function ResearchConnectionBridge({
  evidenceList = [],
  activeEvidenceId,
  onSelectEvidenceId,
}) {
  const [activeStep, setActiveStep] = useState(null); // null = all steps visible

  const currentEvidence =
    evidenceList.find((e) => e.id === activeEvidenceId) ||
    evidenceList[0] ||
    null;

  if (!currentEvidence) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-600 font-mono">
        Loading verified scientific evidence connection chains...
      </div>
    );
  }

  const isLocal = currentEvidence.validation_status === 'locally_verified';
  const isHypothesis = currentEvidence.evidence_classification === 'exploratory_hypothesis';
  const isDocumented = currentEvidence.evidence_classification === 'documented_application';

  // Physical mechanism extraction from verified data
  const deriveMechanismSummary = (ev) => {
    switch (ev.id) {
      case 'EA-EV-BASS-PYRO-01':
        return 'Decouples natural buoyant thermal updrafts from solid thermal degradation, isolating pure polymer pyrolysis kinetics and convective flame stabilization in low-speed forced flows.';
      case 'EA-EV-BASS-EXT-02':
        return 'Isolates radiative heat loss extinction at low convective velocities (<1.5 cm/s) and aerodynamic convective blowoff (>28-38 cm/s), identifying intrinsic physical flame quenching boundaries without buoyant air replenishment.';
      case 'EA-EV-SAFFIRE-DUCT-01':
        return 'Eliminates vertical buoyant plume lift, isolating forced convective flame propagation and radiation-dominated boundary layer transport in enclosed flow geometries analogous to horizontal ducts.';
      case 'EA-EV-SAFFIRE-DET-02':
        return 'Line-of-sight radiative emission is velocity-independent and travels at light speed, exhibiting steep ignition onset (t=66.56s) seconds before downstream convective gas transit reaches thermocouples (1.65s for TC3 to 6.60s for TC1 in the experimental flow duct).';
      case 'EA-EV-SAFFIRE-WILD-03':
        return 'Within dense porous fiber matrices, geometrical packing restricts buoyant air entrainment, causing flame spread to rely on microscale radiative preheating under low forced flow, resembling microgravity diffusion conditions.';
      case 'EA-EV-SAME-AERO-01':
        return 'Absence of buoyant convective venting prolongs soot residence time in high-temperature pyrolyzing zones, promoting Brownian agglomeration into larger particles (0.5 to 3.0+ µm) that alter optical scattering cross-sections.';
      case 'EA-EV-ACME-SOOT-01':
        return 'Spherically symmetric and coflow laminar flames eliminate buoyant flickering and turbulent fluctuations, enabling clean mathematical isolation of soot precursor inception and surface growth kinetics.';
      case 'EA-EV-SOFIE-FLAM-01':
        return 'Removes natural convective cooling and buoyant plume momentum, determining true intrinsic radiative and chemical flammability limits for thick polymer slabs and fabrics.';
      case 'EA-EV-FLEX-COOL-01':
        return 'Spherically symmetric alkane droplet combustion sustains steady low-temperature negative temperature coefficient (NTC) reaction zones, which are quenched by buoyant updrafts in normal gravity.';
      case 'EA-EV-FLEX-SUPP-02':
        return 'Spherical droplet geometry eliminates buoyant dilution mixing, establishing true minimum physical and radiative heat capacity quenching concentrations for inert gas diluents (CO₂, N₂, He).';
      case 'EA-EV-SAFFIRE-IND-04':
        return 'Direct measurement of forced flow ventilation differential pressure and convective flame deceleration during mechanical damper and blower shutdown in enclosed conduits.';
      default:
        return 'Isolates fundamental chemical kinetics and radiation transport from gravitational buoyant updrafts.';
    }
  };

  const mechanismText = deriveMechanismSummary(currentEvidence);

  const steps = [
    {
      number: 1,
      title: 'NASA Flight Investigation',
      badge: currentEvidence.investigation_id.toUpperCase(),
      subtitle: currentEvidence.investigation_name,
      content: (
        <div className="space-y-1 text-xs">
          <div className="text-slate-700">
            <span className="font-semibold text-slate-900">Source Archive:</span>{' '}
            <span className="font-mono text-[11px] text-orange-600">{currentEvidence.source_reference}</span>
          </div>
          {currentEvidence.dataset_or_measurement_reference && (
            <div className="text-slate-600 text-[11px] font-mono">
              <span className="text-purple-600 font-semibold">Sensor / File:</span>{' '}
              {currentEvidence.dataset_or_measurement_reference}
            </div>
          )}
        </div>
      ),
    },
    {
      number: 2,
      title: 'Verified Scientific Finding',
      badge: isLocal ? 'Locally Verified' : 'Literature Verified',
      subtitle: 'Audited Empirical Observation',
      content: (
        <p className="text-xs text-slate-800 leading-relaxed">
          {currentEvidence.scientific_finding}
        </p>
      ),
    },
    {
      number: 3,
      title: 'Physical Mechanism',
      badge: 'Decoupled Physics',
      subtitle: 'Buoyancy & Convection Isolation',
      content: (
        <p className="text-xs text-slate-800 leading-relaxed">
          {mechanismText}
        </p>
      ),
    },
    {
      number: 4,
      title: 'Potential Earth Relevance',
      badge: currentEvidence.category_title,
      subtitle: 'Terrestrial Fire Safety & Combustion',
      content: (
        <p className="text-xs text-slate-800 leading-relaxed">
          {currentEvidence.proposed_terrestrial_relevance}
        </p>
      ),
    },
    {
      number: 5,
      title: 'Evidence Class & Transfer Limitations',
      badge: isHypothesis ? 'Exploratory Hypothesis' : isDocumented ? 'Documented Application' : 'Supported Implication',
      subtitle: 'Scientific Epistemic Caveats',
      content: (
        <div className="space-y-1.5 text-xs text-slate-700">
          <p className="text-[11px] text-amber-800 leading-relaxed">
            <strong>1g Physical Difference:</strong> {currentEvidence.gravity_buoyancy_ventilation_differences}
          </p>
          <p className="text-[11px] text-slate-600 leading-relaxed">
            <strong>Transfer Bound:</strong> {currentEvidence.earth_transfer_limitations}
          </p>
        </div>
      ),
    },
  ];

  return (
    <div className="p-5 sm:p-6 rounded-2xl bg-white border border-slate-200 space-y-6 shadow-sm">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Microgravity to Earth Research Connection Bridge</span>
            <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
              5-Step Physical Translation Chain
            </span>
          </h2>
          <p className="text-xs text-slate-600">
            Traces verified microgravity measurements through decoupled physical mechanisms to terrestrial research relevance without overstating evidence.
          </p>
        </div>

        {/* Current Active Finding Badge */}
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-orange-50 text-orange-700 border border-orange-200 self-start sm:self-auto font-semibold">
          {currentEvidence.id}
        </span>
      </div>

      {/* Evidence Record Selector Pills */}
      <div className="space-y-1.5">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-600 block font-semibold">
          Select Scientific Evidence Chain ({evidenceList.length} available):
        </label>
        <div className="flex flex-wrap items-center gap-1.5">
          {evidenceList.map((ev) => {
            const isSel = ev.id === currentEvidence.id;
            return (
              <button
                key={ev.id}
                onClick={() => onSelectEvidenceId(ev.id)}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer flex items-center gap-1.5 ${
                  isSel
                    ? 'bg-orange-50 text-orange-700 border border-orange-200 font-semibold shadow-xs'
                    : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
                }`}
              >
                <span>{ev.id.replace('EA-EV-', '')}</span>
                <span className="text-[9px] uppercase px-1 rounded bg-slate-100 text-slate-600">
                  {ev.investigation_id.split('_')[0]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Evidence Title Card */}
      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="space-y-0.5">
          <span className="text-[10px] font-mono uppercase text-orange-600 font-semibold">
            Active Research Bridge:
          </span>
          <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
            {currentEvidence.title}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-orange-700 border border-slate-200">
            {currentEvidence.category_title}
          </span>
        </div>
      </div>

      {/* 5-Step Sequential Physical Chain */}
      <div className="space-y-3 relative">
        {steps.map((step, idx) => {
          const isHighlighted = activeStep === null || activeStep === step.number;
          return (
            <div
              key={step.number}
              onClick={() => setActiveStep(activeStep === step.number ? null : step.number)}
              className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer relative ${
                isHighlighted
                  ? 'bg-white border-orange-300 shadow-sm ring-1 ring-orange-200'
                  : 'bg-slate-50 border-slate-200 opacity-60'
              }`}
            >
              {/* Step Header */}
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-orange-50 text-orange-600 border border-orange-200 text-[11px] font-mono font-bold flex items-center justify-center">
                    {step.number}
                  </span>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-900 tracking-tight">
                      {step.title}
                    </h4>
                    <span className="text-[10px] font-mono text-slate-500">
                      {step.subtitle}
                    </span>
                  </div>
                </div>

                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                  {step.badge}
                </span>
              </div>

              {/* Step Content */}
              <div className="pt-2.5">
                {step.content}
              </div>

              {/* Connecting Down Arrow between steps */}
              {idx < steps.length - 1 && (
                <div className="absolute -bottom-3 left-6 z-10 w-4 h-4 rounded-full bg-white border border-slate-300 flex items-center justify-center text-[9px] text-slate-500 pointer-events-none">
                  ↓
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Epistemic Boundary Notice */}
      <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-[11px] text-amber-900 flex items-start gap-2.5">
        <AlertTriangleIcon className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <span className="font-semibold text-amber-900">Scientific Translation Integrity Standard:</span>
          <p className="text-amber-800 leading-relaxed">
            This translation bridge connects fundamental microgravity combustion physics to terrestrial fire research areas. It does <strong>not</strong> produce macroscopic fire behavior simulations or numerical predictions of terrestrial building fires.
          </p>
        </div>
      </div>
    </div>
  );
}
