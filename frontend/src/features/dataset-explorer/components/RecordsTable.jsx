import React, { useState, useMemo } from 'react';

/**
 * Safe cell value formatter for NASA scientific measurements
 */
function FormatCell({ value }) {
  if (value === null || value === undefined || value === '') {
    return <span className="text-slate-400 font-mono select-none">—</span>;
  }

  const str = String(value);

  // Check if value is numeric
  const num = Number(str);
  if (!isNaN(num) && str.trim() !== '') {
    // If it's a decimal with > 4 decimal places, show a clean formatted number and raw in title
    const hasLongDecimals = str.includes('.') && str.split('.')[1].length > 4;
    return (
      <span
        className="font-mono text-slate-800 select-all"
        title={hasLongDecimals ? `Raw value: ${str}` : undefined}
      >
        {hasLongDecimals ? num.toFixed(4) : str}
      </span>
    );
  }

  // Normal text
  return <span className="text-slate-700 truncate max-w-[240px] inline-block">{str}</span>;
}

export function RecordsTable({
  datasetId,
  records = [],
  columns = [],
  metadataColumns = [],
  totalRecords = 0,
  offset = 0,
  limit = 50,
  hasMore = false,
  loading = false,
  currentPage = 1,
  totalPages = 1,
  onNextPage,
  onPrevPage,
  onChangeLimit,
}) {
  const [columnFilter, setColumnFilter] = useState('');
  const [copiedNotification, setCopiedNotification] = useState(false);

  // Map metadata columns for units
  const metaMap = useMemo(() => {
    const map = new Map();
    metadataColumns.forEach((c) => {
      map.set(c.column_name, c);
    });
    return map;
  }, [metadataColumns]);

  // Filter columns to display if user wants to focus on specific channels
  const activeColumns = useMemo(() => {
    if (!columnFilter.trim()) return columns;
    const q = columnFilter.toLowerCase();
    return columns.filter((col) => col.toLowerCase().includes(q));
  }, [columns, columnFilter]);

  const copyPageJson = () => {
    try {
      navigator.clipboard.writeText(JSON.stringify(records, null, 2));
      setCopiedNotification(true);
      setTimeout(() => setCopiedNotification(false), 2400);
    } catch {
      // Ignore clipboard write failure
    }
  };

  const startRecord = totalRecords > 0 ? offset + 1 : 0;
  const endRecord = Math.min(offset + limit, totalRecords);

  return (
    <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-4 shadow-sm">
      {/* Table Toolbar & Pagination Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Scientific Records Data Table</span>
              <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded font-semibold">
                Live Flight Telemetry
              </span>
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 font-mono">
            Showing records {startRecord.toLocaleString()}–{endRecord.toLocaleString()} of {totalRecords.toLocaleString()} • Server-side paginated
          </p>
        </div>

        {/* Action Controls & Pagination */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs font-mono">
          {/* Quick Column Filter */}
          <div className="relative">
            <input
              type="text"
              value={columnFilter}
              onChange={(e) => setColumnFilter(e.target.value)}
              placeholder="Filter columns..."
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-orange-500 w-36"
            />
            {columnFilter && (
              <button
                onClick={() => setColumnFilter('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
              >
                ✕
              </button>
            )}
          </div>

          {/* Page Size Selector */}
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 text-[11px]">Rows:</span>
            <select
              value={limit}
              onChange={(e) => onChangeLimit(Number(e.target.value))}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs text-slate-900 focus:outline-none cursor-pointer"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          {/* Copy Page JSON CTA */}
          <button
            onClick={copyPageJson}
            className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 transition-colors cursor-pointer border border-slate-200"
            title="Copy current page records as JSON"
          >
            {copiedNotification ? '✓ Copied Page' : 'Copy Page JSON'}
          </button>

          {/* Prev / Next Pagination */}
          <div className="flex items-center gap-1">
            <button
              onClick={onPrevPage}
              disabled={offset === 0 || loading}
              className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 border border-slate-200 cursor-pointer"
            >
              ◀ Prev
            </button>
            <span className="px-2 py-1 text-slate-500 font-mono text-[11px]">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={onNextPage}
              disabled={!hasMore && endRecord >= totalRecords || loading}
              className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 border border-slate-200 cursor-pointer"
            >
              Next ▶
            </button>
          </div>
        </div>
      </div>

      {/* Responsive Horizontal Scroll Table Container */}
      <div className="relative rounded-xl border border-slate-200 bg-white overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-white/70 backdrop-blur-[2px] z-20 flex items-center justify-center">
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-200 text-xs font-mono text-orange-600 shadow-lg">
              <span className="w-2 h-2 rounded-full bg-orange-500 animate-ping" />
              <span>Fetching server-side records from FastAPI...</span>
            </div>
          </div>
        )}

        <div className="overflow-x-auto max-h-[520px] overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 sticky top-0 z-10 border-b border-slate-200 backdrop-blur-sm">
              <tr>
                <th className="py-2.5 px-3 text-slate-500 font-mono text-[10px] uppercase tracking-wider sticky left-0 bg-slate-50 z-20 border-r border-slate-200 w-12 text-center">
                  #
                </th>
                {activeColumns.map((colName) => {
                  const unit = metaMap.get(colName)?.original_unit;
                  return (
                    <th
                      key={colName}
                      className="py-2.5 px-3 font-mono text-[11px] font-semibold text-slate-700 whitespace-nowrap border-r border-slate-200 last:border-r-0"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>{colName}</span>
                        {unit && (
                          <span className="text-[9px] font-mono px-1 rounded bg-sky-50 text-sky-700 border border-sky-200">
                            {unit}
                          </span>
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 font-mono text-xs">
              {records.length === 0 && !loading && (
                <tr>
                  <td
                    colSpan={activeColumns.length + 1}
                    className="p-8 text-center text-slate-500 font-mono"
                  >
                    No records found in this dataset page.
                  </td>
                </tr>
              )}

              {records.map((row, rowIdx) => {
                const globalIndex = offset + rowIdx + 1;

                return (
                  <tr
                    key={rowIdx}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="py-2 px-3 text-slate-500 font-mono text-[10px] text-center sticky left-0 bg-white border-r border-slate-200 z-10">
                      {globalIndex}
                    </td>
                    {activeColumns.map((colName) => (
                      <td
                        key={colName}
                        className="py-2 px-3 whitespace-nowrap border-r border-slate-200 last:border-r-0"
                      >
                        <FormatCell value={row[colName]} />
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Table Footer Navigation Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono text-slate-500 pt-1">
        <div>
          Showing {activeColumns.length} of {columns.length} columns • Dataset: <span className="text-slate-800">{datasetId}</span>
        </div>
        <div className="flex items-center gap-2">
          <span>Page {currentPage} of {totalPages}</span>
          <button
            onClick={onPrevPage}
            disabled={offset === 0 || loading}
            className="hover:text-slate-900 disabled:opacity-30 cursor-pointer"
          >
            Previous
          </button>
          <span>•</span>
          <button
            onClick={onNextPage}
            disabled={!hasMore && endRecord >= totalRecords || loading}
            className="hover:text-slate-900 disabled:opacity-30 cursor-pointer"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
