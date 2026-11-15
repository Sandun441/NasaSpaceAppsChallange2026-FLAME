import React from 'react';
import { SUGGESTED_QUERIES } from '../../../lib/constants';

export function SuggestedQueries({ onSelectQuery }) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500 pt-1">
      <span className="text-[11px] font-mono text-slate-500">Popular queries:</span>
      {SUGGESTED_QUERIES.map((item) => (
        <button
          key={item.label}
          type="button"
          onClick={() => onSelectQuery(item.query)}
          className="px-2.5 py-1 rounded-md bg-white border border-slate-200 text-slate-700 hover:text-slate-900 hover:border-slate-300 hover:bg-slate-50 transition-all duration-150 text-[11px] cursor-pointer shadow-xs"
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
