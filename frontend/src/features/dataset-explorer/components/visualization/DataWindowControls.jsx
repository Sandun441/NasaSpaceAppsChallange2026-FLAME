import React from 'react';

/**
 * DataWindowControls
 * Server-side range windowing controls for large datasets (e.g., Saffire III with 20k+ records).
 */
export function DataWindowControls({
  offset = 0,
  limit = 1000,
  totalRecords = 0,
  loadedCount = 0,
  loading = false,
  enableDownsampling = true,
  onToggleDownsampling,
  onChangeOffset,
  onChangeLimit,
}) {
  const currentEnd = Math.min(totalRecords, offset + loadedCount);
  const hasPrev = offset > 0;
  const hasNext = offset + limit < totalRecords;

  const handleNextWindow = () => {
    if (hasNext) {
      onChangeOffset(offset + limit);
    }
  };

  const handlePrevWindow = () => {
    if (hasPrev) {
      onChangeOffset(Math.max(0, offset - limit));
    }
  };

  const handleJumpToStart = () => {
    onChangeOffset(0);
  };

  const handleJumpToEnd = () => {
    const endOffset = Math.max(0, totalRecords - limit);
    onChangeOffset(endOffset);
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 bg-white border border-slate-200 p-3 rounded-xl text-xs font-mono shadow-sm">
      {/* Window Range Info */}
      <div className="flex items-center gap-2">
        <span className="text-slate-500">Records Window:</span>
        <span className="text-slate-900 font-semibold">
          {totalRecords > 0 ? `${(offset + 1).toLocaleString()} – ${currentEnd.toLocaleString()}` : '0'}
        </span>
        <span className="text-slate-500">
          of {totalRecords.toLocaleString()} records
        </span>
        {loading && (
          <span className="text-orange-600 flex items-center gap-1 text-[11px] animate-pulse">
            <span>⟳</span> Fetching server records...
          </span>
        )}
      </div>

      {/* Navigation and Downsampling */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Downsampling Toggle */}
        <button
          onClick={onToggleDownsampling}
          className={`px-2.5 py-1 rounded text-[11px] border transition cursor-pointer ${
            enableDownsampling
              ? 'bg-emerald-50 border-emerald-300 text-emerald-800 font-semibold'
              : 'bg-slate-100 border-slate-200 text-slate-700'
          }`}
          title="Toggle Largest-Triangle-Three-Buckets decimation algorithm"
        >
          {enableDownsampling ? '✓ LTTB Decimated (Optimal 60fps)' : 'Full Raw Points'}
        </button>

        {/* Window Size Select */}
        <select
          value={limit}
          onChange={(e) => onChangeLimit(Number(e.target.value))}
          disabled={loading}
          className="bg-slate-50 border border-slate-200 text-slate-800 rounded px-2 py-1 text-[11px] outline-none cursor-pointer"
        >
          <option value={500}>500 pts window</option>
          <option value={1000}>1,000 pts window</option>
          <option value={2000}>2,000 pts window</option>
          <option value={3000}>3,000 pts window</option>
        </select>

        {/* Pagination Buttons */}
        <div className="flex items-center gap-1">
          <button
            onClick={handleJumpToStart}
            disabled={!hasPrev || loading}
            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 disabled:opacity-30 transition cursor-pointer text-[11px]"
            title="Jump to Start of Test"
          >
            ⇤ Start
          </button>
          <button
            onClick={handlePrevWindow}
            disabled={!hasPrev || loading}
            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 disabled:opacity-30 transition cursor-pointer text-[11px]"
          >
            ← Prev
          </button>
          <button
            onClick={handleNextWindow}
            disabled={!hasNext || loading}
            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 disabled:opacity-30 transition cursor-pointer text-[11px]"
          >
            Next →
          </button>
          <button
            onClick={handleJumpToEnd}
            disabled={!hasNext || loading}
            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 disabled:opacity-30 transition cursor-pointer text-[11px]"
            title="Jump to End of Test"
          >
            End ⇥
          </button>
        </div>
      </div>
    </div>
  );
}
