import React from 'react';

export function VerifiedMeasurementsPanel({ parameters = [], investigations = [] }) {
  // Aggregate verified sensor channels ONLY from locally indexed investigations
  const allChannels = [];
  const seenIds = new Set();

  for (const inv of investigations) {
    if (inv.is_locally_indexed === false) continue;
    for (const ch of inv.verified_sensor_channels || []) {
      if (!seenIds.has(ch.id)) {
        seenIds.add(ch.id);
        allChannels.push({
          ...ch,
          investigation_name: inv.name,
          facility: inv.facility,
        });
      }
    }
  }

  if (allChannels.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-3 border-b border-slate-100">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-orange-600">
            Physical Sensor Channels & Calibrated Telemetry
          </span>
          <h3 className="text-sm sm:text-base font-semibold text-slate-900">
            Available NASA Flight Measurements ({allChannels.length} Verified Channels)
          </h3>
        </div>
        <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
          100% Locally Indexed Data
        </span>
      </div>

      {/* Critical Scientific Distinction Alert */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs space-y-1">
        <span className="font-semibold text-amber-800 font-mono text-[11px] uppercase flex items-center gap-1.5">
          <span>⚠️ Critical Scientific Distinction:</span>
        </span>
        <p className="text-[11px] text-amber-900 leading-relaxed font-sans">
          Measurements recorded in Saffire, BASS-II, and Cygnus represent <strong>combustion environmental conditions</strong> (e.g. radiant heat flux, exhaust gas temperatures, bulk cabin flow velocity, toxic gas ppm, raw photodiode voltages). They do NOT represent standardized factory detector sensitivity calibration curves.
        </p>
      </div>

      {/* Channels Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {allChannels.map((ch) => (
          <div
            key={ch.id}
            className="bg-slate-50 border border-slate-200 rounded-xl p-3 space-y-2 flex flex-col justify-between hover:border-orange-300 transition-all"
          >
            <div className="space-y-1">
              <div className="flex items-center justify-between gap-1">
                <span className="font-mono text-[9px] text-slate-500 uppercase truncate">
                  {ch.facility}
                </span>
                <span className="font-mono text-[10px] text-orange-700 bg-orange-50 px-1.5 py-0.2 rounded border border-orange-200 font-bold shrink-0">
                  {ch.unit}
                </span>
              </div>

              <h4 className="text-xs font-semibold text-slate-900 leading-tight">
                {ch.label}
              </h4>

              <div className="text-[10px] font-mono text-slate-500 bg-white p-1.5 rounded border border-slate-200">
                Range: <strong className="text-slate-800">{ch.measured_range}</strong>
              </div>

              {ch.source_dataset && (
                <div className="text-[9px] font-mono text-slate-500">
                  Dataset: <code className="text-orange-600">{ch.source_dataset}</code>
                </div>
              )}

              <p className="text-[11px] text-slate-600 font-sans leading-tight pt-1">
                {ch.description}
              </p>
            </div>

            <div className="text-[9px] font-mono text-slate-400 pt-1 border-t border-slate-200">
              Source: {ch.investigation_name}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
