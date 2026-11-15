import React from 'react';
import { CategoryIcon } from './EarthIcons';

export function EarthCategoryExplorer({
  categories = [],
  activeCategory = 'all',
  onSelectCategory,
  totalRecords = 11,
}) {
  return (
    <div className="space-y-3">
      {/* Category Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-1">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Terrestrial Application Domains</span>
            <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
              7 Extensible Categories
            </span>
          </h2>
          <p className="text-xs text-slate-600">
            Select a domain to filter verified microgravity evidence and physical transfer mechanisms
          </p>
        </div>

        {/* All Categories Toggle Chip */}
        <button
          onClick={() => onSelectCategory('all')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer flex items-center gap-1.5 self-start sm:self-auto ${
            activeCategory === 'all'
              ? 'bg-orange-50 text-orange-700 border border-orange-200 font-semibold shadow-xs'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
          }`}
        >
          <span>All Application Domains</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-700 font-mono">
            {totalRecords}
          </span>
        </button>
      </div>

      {/* 7 Category Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5">
        {categories.map((cat) => {
          const isSelected = activeCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => onSelectCategory(isSelected ? 'all' : cat.id)}
              className={`p-3.5 rounded-xl border text-left transition-all duration-200 flex flex-col justify-between gap-2.5 cursor-pointer relative group ${
                isSelected
                  ? 'bg-orange-50 border-orange-400 shadow-sm ring-1 ring-orange-300'
                  : 'bg-white hover:bg-slate-50 border-slate-200 hover:border-slate-300 shadow-xs'
              }`}
            >
              {/* Top Row: Icon + Evidence Count Badge */}
              <div className="flex items-center justify-between w-full">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center transition-colors ${
                    isSelected
                      ? 'bg-orange-100 text-orange-700 border border-orange-300'
                      : 'bg-slate-100 text-slate-500 group-hover:text-orange-600 group-hover:bg-orange-50'
                  }`}
                >
                  <CategoryIcon categoryId={cat.id} className="w-4 h-4" />
                </div>

                <div className="flex items-center gap-1">
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                      isSelected
                        ? 'bg-orange-100 text-orange-800 border-orange-300 font-semibold'
                        : 'bg-slate-100 text-slate-600 border-slate-200'
                    }`}
                  >
                    {cat.evidence_count} {cat.evidence_count === 1 ? 'record' : 'records'}
                  </span>
                </div>
              </div>

              {/* Title & Short Description */}
              <div className="space-y-1">
                <h3
                  className={`text-xs font-semibold tracking-tight transition-colors ${
                    isSelected ? 'text-slate-900' : 'text-slate-800 group-hover:text-slate-900'
                  }`}
                >
                  {cat.title}
                </h3>
                <p className="text-[11px] text-slate-600 leading-snug line-clamp-2">
                  {cat.short_desc}
                </p>
              </div>

              {/* Primary Investigations Tags Footer */}
              {cat.primary_investigations && cat.primary_investigations.length > 0 && (
                <div className="pt-1.5 border-t border-slate-100 flex flex-wrap items-center gap-1">
                  {cat.primary_investigations.map((inv) => (
                    <span
                      key={inv}
                      className="text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200"
                    >
                      {inv.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              )}

              {/* Active Selection Indicator Pip */}
              {isSelected && (
                <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
