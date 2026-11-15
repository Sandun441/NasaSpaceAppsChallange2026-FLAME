import React, { useState, useMemo } from 'react';

export function ColumnsViewer({ columns = [], metadataColumns = [] }) {
  const [columnSearch, setColumnSearch] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  // Map metadata columns by column_name for quick unit lookups
  const metaMap = useMemo(() => {
    const map = new Map();
    metadataColumns.forEach((c) => {
      map.set(c.column_name, c);
    });
    return map;
  }, [metadataColumns]);

  const filteredColumns = useMemo(() => {
    if (!columnSearch.trim()) return columns;
    const q = columnSearch.toLowerCase();
    return columns.filter((col) => {
      const meta = metaMap.get(col);
      return (
        col.toLowerCase().includes(q) ||
        (meta?.original_unit && meta.original_unit.toLowerCase().includes(q))
      );
    });
  }, [columns, columnSearch, metaMap]);

  if (columns.length === 0) return null;

  const displayLimit = isExpanded ? filteredColumns.length : 14;
  const visibleColumns = filteredColumns.slice(0, displayLimit);
  const remainingCount = filteredColumns.length - displayLimit;

  return (
    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono uppercase text-sky-400 font-semibold tracking-wider">
            Available Measurement Channels
          </span>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
            {columns.length} columns
          </span>
        </div>

        {/* Filter input */}
        <div className="relative max-w-xs w-full">
          <input
            type="text"
            value={columnSearch}
            onChange={(e) => setColumnSearch(e.target.value)}
            placeholder="Filter channels (e.g. 'TC', 'Pressure', 'O2')..."
            className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-[11px] text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-slate-600"
          />
          {columnSearch && (
            <button
              onClick={() => setColumnSearch('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white text-xs"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Column Chips List */}
      <div className="flex flex-wrap gap-1.5">
        {visibleColumns.map((colName) => {
          const meta = metaMap.get(colName);
          const unit = meta?.original_unit;

          return (
            <span
              key={colName}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300"
              title={unit ? `${colName} (Unit: ${unit})` : colName}
            >
              <span className="truncate max-w-[200px]">{colName}</span>
              {unit && (
                <span className="text-[9px] px-1 py-0.2 rounded bg-sky-950 text-sky-300 border border-sky-800/50 font-bold">
                  {unit}
                </span>
              )}
            </span>
          );
        })}
      </div>

      {filteredColumns.length > 14 && (
        <div className="pt-1 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span>
            Showing {visibleColumns.length} of {filteredColumns.length} channels
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-orange-400 hover:text-orange-300 underline cursor-pointer"
          >
            {isExpanded ? 'Show Fewer Columns [-]' : `Show All +${remainingCount} Columns [+]`}
          </button>
        </div>
      )}
    </div>
  );
}
