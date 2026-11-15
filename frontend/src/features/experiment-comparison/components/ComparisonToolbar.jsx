import React from 'react';

/**
 * ComparisonToolbar
 * Controls alignment mode, window limits, offset navigation, and downsampling.
 */
export function ComparisonToolbar({
  alignmentMode,
  canEventAlign,
  ignitionTimeA,
  ignitionTimeB,
  datasetAId,
  datasetBId,
  windowLimit,
  enableDownsampling,
  loading,
  onSelectAlignmentMode,
  onChangeWindowLimit,
  onToggleDownsampling,
}) {
  return (
    <div className="bg-white border border-slate-200 p-3.5 rounded-2xl flex flex-wrap items-center justify-between gap-4 text-xs font-mono shadow-sm">
      {/* Alignment Mode Tabs */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-slate-500 mr-1 text-[11px]">Time Alignment:</span>

        <button
          onClick={() => onSelectAlignmentMode('side_by_side')}
          className={`px-3 py-1.5 rounded-lg border text-[11px] transition cursor-pointer ${
            alignmentMode === 'side_by_side'
              ? 'bg-white border-orange-300 text-orange-600 font-semibold shadow-sm'
              : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900'
          }`}
        >
          Side-by-Side
        </button>

        <button
          onClick={() => onSelectAlignmentMode('overlay_recorded')}
          className={`px-3 py-1.5 rounded-lg border text-[11px] transition cursor-pointer ${
            alignmentMode === 'overlay_recorded'
              ? 'bg-white border-orange-300 text-orange-600 font-semibold shadow-sm'
              : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900'
          }`}
        >
          Recorded Time Overlay (t=0s)
        </button>

        <div className="relative group">
          <button
            onClick={() => canEventAlign && onSelectAlignmentMode('overlay_event_aligned')}
            disabled={!canEventAlign}
            className={`px-3 py-1.5 rounded-lg border text-[11px] transition flex items-center gap-1.5 ${
              !canEventAlign
                ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
                : alignmentMode === 'overlay_event_aligned'
                ? 'bg-white border-orange-300 text-orange-600 font-semibold shadow-sm cursor-pointer'
                : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900 cursor-pointer'
            }`}
          >
            <span>⚡ Event-Aligned (t₀ = Ignition)</span>
            {canEventAlign && (
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            )}
          </button>

          {!canEventAlign && (
            <div className="absolute left-0 bottom-full mb-1 hidden group-hover:block z-30 bg-white border border-slate-200 rounded p-2 text-[10px] text-slate-600 w-64 shadow-lg">
              Event alignment is disabled because verified ignition telemetry is not documented in both selected datasets. NASA FLAME never assumes or fabricates an ignition timestamp.
            </div>
          )}
        </div>
      </div>

      {/* Downsampling & Windowing Controls */}
      <div className="flex flex-wrap items-center gap-2.5">
        <button
          onClick={onToggleDownsampling}
          className={`px-2.5 py-1 rounded text-[11px] border transition cursor-pointer ${
            enableDownsampling
              ? 'bg-emerald-50 border-emerald-300 text-emerald-800 font-semibold'
              : 'bg-slate-100 border-slate-200 text-slate-700'
          }`}
          title="Toggle Largest-Triangle-Three-Buckets decimation algorithm"
        >
          {enableDownsampling ? '✓ LTTB 800pts' : 'Full Raw Points'}
        </button>

        <select
          value={windowLimit}
          onChange={(e) => onChangeWindowLimit(Number(e.target.value))}
          disabled={loading}
          className="bg-slate-50 border border-slate-200 text-slate-800 rounded px-2 py-1 text-[11px] outline-none cursor-pointer"
        >
          <option value={500}>500 pts window</option>
          <option value={1000}>1,000 pts window</option>
          <option value={2000}>2,000 pts window</option>
          <option value={3000}>3,000 pts window</option>
        </select>
      </div>

      {/* Event Details Ribbon if Event-Aligned */}
      {alignmentMode === 'overlay_event_aligned' && canEventAlign && (
        <div className="w-full bg-amber-50 border border-amber-200 rounded-xl p-2.5 flex flex-wrap items-center justify-between text-[11px] text-amber-900 font-medium">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-amber-800">Documented Ignition Timestamps:</span>
            <span>
              {datasetAId}: <strong className="text-slate-900">{ignitionTimeA?.toFixed(2)}s</strong>
            </span>
            <span>•</span>
            <span>
              {datasetBId}: <strong className="text-slate-900">{ignitionTimeB?.toFixed(2)}s</strong>
            </span>
          </div>
          <span className="text-[10px] text-amber-700">
            Time axis shifted so t′ = 0 corresponds to verified igniter energization
          </span>
        </div>
      )}
    </div>
  );
}
