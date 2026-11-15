import React, { useState } from 'react';

export function EvidenceCard({ evidence, index, onNavigateTool }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const rid = evidence.record_id || 'unknown_record';
  const title = evidence.title || rid;
  const inv = evidence.investigation || 'NASA Combustion Investigation';
  const rtype = evidence.record_type || 'record';
  const provFile = evidence.source_file || 'NASA Workbook';
  const provSheet = evidence.source_worksheet;
  const provRow = evidence.source_excel_row;
  const cond = evidence.experimental_conditions || {};
  const stats = evidence.measured_statistics;
  const channels = evidence.available_channels || [];
  const warnings = evidence.quality_warnings || [];
  const missing = evidence.missing_fields || [];
  const isEarthEvidence = rtype === 'earth_application_evidence' || String(rid).startsWith('EA-EV-');

  return (
    <div className={`rounded-xl p-3.5 transition-all duration-150 text-xs shadow-xs border ${
      isEarthEvidence 
        ? 'bg-white border-emerald-200 hover:border-emerald-300' 
        : 'bg-white border-slate-200 hover:border-slate-300'
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded border ${
              isEarthEvidence 
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200' 
                : 'bg-orange-50 text-orange-700 border-orange-200'
            }`}>
              #{index} • {isEarthEvidence ? 'Earth Application Finding' : rtype}
            </span>
            <span className="font-mono text-[10px] text-slate-500">
              {rid}
            </span>
            {isEarthEvidence && evidence.category_title && (
              <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                {evidence.category_title}
              </span>
            )}
          </div>
          <h4 className="font-semibold text-slate-900 text-xs tracking-tight">
            {title}
          </h4>
          <p className="text-[11px] text-slate-500">
            {inv} {evidence.evidence_classification && `• [${evidence.evidence_classification.replace(/_/g, ' ')}]`}
          </p>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {isEarthEvidence && onNavigateTool && (
            <button
              onClick={() => onNavigateTool('earth-applications', { evidence_id: rid })}
              className="px-2 py-1 rounded bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 text-[10px] font-mono transition-colors cursor-pointer"
            >
              Inspect in Earth Apps →
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 text-[11px] font-mono transition-colors cursor-pointer"
          >
            {isExpanded ? 'Collapse ▲' : 'Details ▼'}
          </button>
        </div>
      </div>

      {/* Primary Empirical Summary */}
      {isEarthEvidence ? (
        <div className="mt-2.5 space-y-1.5 text-[11px] bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          {evidence.scientific_finding && (
            <div>
              <span className="text-emerald-700 font-mono text-[10px] uppercase font-semibold block">Flight Observation:</span>
              <p className="text-slate-700 leading-relaxed">{evidence.scientific_finding}</p>
            </div>
          )}
          {evidence.proposed_terrestrial_relevance && (
            <div>
              <span className="text-sky-700 font-mono text-[10px] uppercase font-semibold block">Terrestrial Relevance:</span>
              <p className="text-slate-700 leading-relaxed">{evidence.proposed_terrestrial_relevance}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <div>
            <span className="text-slate-500 font-mono">Fuel Substrate: </span>
            <span className="text-slate-800 font-medium">{cond.fuel_material || 'N/A'}</span>
            {cond.oxygen_concentration && (
              <span className="text-slate-500 font-mono ml-2">({cond.oxygen_concentration} O₂)</span>
            )}
          </div>
          <div>
            <span className="text-slate-500 font-mono">Flow / Chamber: </span>
            <span className="text-slate-800">{cond.flow_velocity || cond.gravity_regime || 'Microgravity'}</span>
          </div>
        </div>
      )}

      {/* Measured Stats */}
      {stats && (stats.delta_value !== undefined || stats.notes) && (
        <div className="mt-2 text-[11px] text-emerald-700 font-mono flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>{stats.notes || `Observed delta: ${stats.delta_value}`}</span>
        </div>
      )}

      {/* Expandable Section */}
      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-slate-200 space-y-2.5 text-[11px] animate-in fade-in duration-150">
          {isEarthEvidence ? (
            <div className="space-y-2">
              {evidence.source_reference && (
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <div className="text-[10px] font-mono uppercase text-slate-500 mb-0.5">Primary Literature Source</div>
                  <div className="text-slate-700 font-mono text-[10px] break-all">{evidence.source_reference}</div>
                </div>
              )}

              {evidence.dataset_or_measurement_reference && (
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <div className="text-[10px] font-mono uppercase text-slate-500 mb-0.5">NASA Telemetry / Dataset Provenance</div>
                  <div className="text-slate-700 font-mono text-[10px]">{evidence.dataset_or_measurement_reference}</div>
                </div>
              )}

              {evidence.gravity_buoyancy_ventilation_differences && (
                <div className="bg-amber-50 border border-amber-200 p-2 rounded text-amber-900 text-[10px]">
                  <span className="font-semibold text-amber-800 uppercase tracking-wider block mb-0.5">Physical Gravity & Buoyancy Differences:</span>
                  <p className="leading-relaxed">{evidence.gravity_buoyancy_ventilation_differences}</p>
                </div>
              )}

              {evidence.earth_transfer_limitations && (
                <div className="bg-amber-50 border border-amber-200 p-2 rounded text-amber-900 text-[10px]">
                  <span className="font-semibold text-amber-800 uppercase tracking-wider block mb-0.5">Terrestrial Scaling Limitations:</span>
                  <p className="leading-relaxed">{evidence.earth_transfer_limitations}</p>
                </div>
              )}

              {evidence.confidence_rubric && (
                <div className="bg-slate-50 p-2 rounded border border-slate-200 text-[10px] font-mono text-slate-600">
                  <span className="text-slate-800 font-semibold">Validation Rubric: </span>
                  <span>{evidence.confidence_rubric}</span>
                </div>
              )}
            </div>
          ) : (
            <>
              {/* Provenance */}
              <div className="bg-slate-50 p-2 rounded border border-slate-200">
                <div className="text-[10px] font-mono uppercase text-slate-500 mb-1">Source Provenance</div>
                <div className="text-slate-700 font-mono">
                  Workbook: <span className="text-slate-900 font-semibold">{provFile}</span>
                  {provSheet && <span> | Sheet: <span className="text-slate-900 font-semibold">{provSheet}</span></span>}
                  {provRow !== undefined && provRow !== null && <span> | Row: <span className="text-slate-900 font-semibold">{provRow}</span></span>}
                </div>
                {evidence.data_file && (
                  <div className="text-slate-500 font-mono text-[10px] mt-0.5">
                    Relative CSV: {evidence.data_file}
                  </div>
                )}
              </div>

              {/* Available Channels */}
              {channels.length > 0 && (
                <div>
                  <div className="text-[10px] font-mono uppercase text-slate-500 mb-1">Recorded Sensor Channels</div>
                  <div className="flex flex-wrap gap-1.5">
                    {channels.map((ch, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono border border-slate-200"
                      >
                        {ch.channel_name} {ch.unit ? `(${ch.unit})` : ''}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Quality Screening Warnings */}
              {warnings.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 p-2 rounded text-amber-900 text-[10px] font-mono">
                  <div className="font-semibold uppercase tracking-wider mb-0.5 text-amber-800">Quality Screening Warnings:</div>
                  <ul className="list-disc list-inside space-y-0.5">
                    {warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Missing Fields Transparency */}
              {missing.length > 0 && (
                <div className="bg-slate-100 p-2 rounded text-slate-600 text-[10px] font-mono border border-slate-200">
                  <span className="font-semibold text-slate-800">Explicitly Unrecorded Fields: </span>
                  <span>{missing.join(', ')}</span>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
