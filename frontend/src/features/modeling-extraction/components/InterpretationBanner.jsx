import React from 'react';

export function InterpretationBanner({
  interpretation,
  onSelectAlternativeTarget,
  activeTargetId,
}) {
  if (!interpretation) return null;

  const target = interpretation.target || {};
  const targetStatus = target.status || 'NOT_SPECIFIED';
  const detectedFeatures = interpretation.detected_features || [];
  const materialFilter = interpretation.material_filter;
  const isUninstrumented = targetStatus === 'UNINSTRUMENTED_UNAVAILABLE';

  const statusBadges = {
    VERIFIED_MEASURED: {
      label: 'Verified Measured Target',
      bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
      dot: 'bg-emerald-500',
    },
    VALIDATED_DERIVED: {
      label: 'Validated Derived Target',
      bg: 'bg-sky-50 border-sky-200 text-sky-800',
      dot: 'bg-sky-500',
    },
    UNINSTRUMENTED_UNAVAILABLE: {
      label: 'Target Uninstrumented in Telemetry / Matrix',
      bg: 'bg-rose-50 border-rose-200 text-rose-800',
      dot: 'bg-rose-500',
    },
    EXPLORATORY_ONLY: {
      label: 'Exploratory Feature Extraction (No Supervised Target)',
      bg: 'bg-slate-100 border-slate-200 text-slate-700',
      dot: 'bg-slate-500',
    },
    NOT_SPECIFIED: {
      label: 'Unsupervised / Exploratory Mode',
      bg: 'bg-slate-100 border-slate-200 text-slate-700',
      dot: 'bg-slate-500',
    },
  };

  const currentBadge = statusBadges[targetStatus] || statusBadges.NOT_SPECIFIED;

  return (
    <div
      className={`rounded-2xl border p-4 sm:p-5 transition-all shadow-sm ${
        isUninstrumented
          ? 'bg-amber-50/70 border-amber-200'
          : 'bg-white border-slate-200'
      }`}
    >
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-3 mb-3">
        {/* Target Identity & Status Badge */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="text-xs font-semibold text-slate-900">Interpreted Target:</span>
          <span className="text-xs font-mono font-bold text-slate-900 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
            {target.label || 'None (Exploratory Features)'}
          </span>
          {target.unit && (
            <span className="text-[11px] font-mono text-slate-500">
              [{target.unit}]
            </span>
          )}
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${currentBadge.bg}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${currentBadge.dot}`} />
            {currentBadge.label}
          </span>
        </div>

        {/* Material Filter Pill if detected */}
        {materialFilter && (
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-500 text-[11px]">Material Filter:</span>
            <span className="font-mono text-orange-700 bg-orange-50 border border-orange-200 px-2 py-0.5 rounded text-[11px]">
              {materialFilter}
            </span>
          </div>
        )}
      </div>

      {/* Target Explanation / Scientific Feasibility Disclosure */}
      <div className="text-xs text-slate-700 space-y-2 leading-relaxed">
        <p className="bg-slate-50 p-3 rounded-xl border border-slate-200 font-sans">
          {target.explanation}
        </p>

        {/* If target is uninstrumented (like flame spread rate), offer verified alternatives */}
        {isUninstrumented && target.suggested_alternatives?.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-2">
            <div className="flex items-center gap-2 text-amber-900 font-semibold text-xs">
              <span>⚠️ Scientific Disclosure:</span>
              <span className="font-normal text-amber-900/90">
                To train supervised models, select a verified combustion metric recorded by onboard sensors:
              </span>
            </div>
            <div className="flex items-center gap-2 flex-wrap pt-1">
              {target.suggested_alternatives.map((altId) => {
                const altLabel =
                  altId === 'oxygen_consumption_delta_pct'
                    ? 'Oxygen Consumption Delta (ΔO₂)'
                    : altId === 'peak_plume_temperature_c'
                    ? 'Peak Plume Temperature (°C)'
                    : altId === 'final_co_ppm'
                    ? 'Final CO Emission (ppm)'
                    : altId;
                const isSelected = activeTargetId === altId;

                return (
                  <button
                    key={altId}
                    type="button"
                    onClick={() => onSelectAlternativeTarget(altId)}
                    className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-orange-500 text-white border-orange-600'
                        : 'bg-white hover:bg-orange-50 border-slate-200 text-slate-700 hover:text-orange-900'
                    }`}
                  >
                    <span>✦ Switch Target:</span>
                    <span className="font-mono font-semibold">{altLabel}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Detected Feature Chips */}
      {detectedFeatures.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-200 flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-mono text-slate-500">Detected Input Features:</span>
          {detectedFeatures.map((feat, idx) => (
            <span
              key={idx}
              className="text-[11px] px-2 py-0.5 rounded-md bg-slate-50 border border-slate-200 text-slate-700 font-mono"
            >
              ✓ {feat}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
