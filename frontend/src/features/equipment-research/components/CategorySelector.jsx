import React from 'react';

export function CategorySelector({
  categories = [],
  activeCategory,
  onSelectCategory,
}) {
  const allTabs = [
    {
      id: 'all',
      title: 'All Research Domains',
      short_desc: 'Comprehensive multi-disciplinary view across detection, prevention, and suppression.',
      icon: '🌐',
    },
    ...categories,
  ];

  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-slate-200">
        <h2 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-2">
          <span>Fire-Safety Research Domains</span>
          <span className="text-[10px] font-mono text-orange-700 bg-orange-50 border border-orange-200 px-2 py-0.5 rounded">
            Interactive Filter
          </span>
        </h2>
        <span className="text-xs text-slate-500">
          Filter investigations, verified measurements, and engineering insights by domain
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {allTabs.map((cat) => {
          const isActive = activeCategory === cat.id;

          return (
            <button
              key={cat.id}
              onClick={() => onSelectCategory(cat.id)}
              className={`p-3.5 rounded-xl border text-left transition-all duration-150 flex flex-col justify-between cursor-pointer group shadow-xs ${
                isActive
                  ? 'bg-orange-50/50 border-orange-500 ring-1 ring-orange-500/50 shadow-sm'
                  : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-900 group-hover:text-orange-600 transition-colors flex items-center gap-1.5">
                    <span>{cat.icon || '🔥'}</span>
                    <span>{cat.title}</span>
                  </span>
                  {isActive && (
                    <span className="text-[9px] font-mono uppercase bg-orange-100 text-orange-800 border border-orange-300 px-1.5 py-0.5 rounded font-bold">
                      Active
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed font-sans line-clamp-2">
                  {cat.short_desc}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
