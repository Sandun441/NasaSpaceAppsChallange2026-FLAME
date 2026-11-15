import React from 'react';

export function Footer({ activeTab, onSelectTab }) {
  return (
    <footer className="max-w-6xl w-full mx-auto pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3 mt-12 pb-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-slate-700">FLAME</span>
        <span>•</span>
        <span>NASA Physical Science Informatics (PSI) Challenge</span>
        <span className="hidden sm:inline">•</span>
        <span className="text-[10px] font-mono text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
          NASA Open Science Platform
        </span>
      </div>

      <div className="flex items-center gap-3 text-[11px] font-mono text-slate-500">
        <button
          onClick={() => onSelectTab && onSelectTab('home')}
          className={`hover:text-slate-900 transition-colors cursor-pointer ${activeTab === 'home' ? 'text-orange-600 font-semibold' : ''}`}
        >
          Home
        </button>
        <span>•</span>
        <button
          onClick={() => onSelectTab && onSelectTab('dataset-explorer')}
          className={`hover:text-slate-900 transition-colors cursor-pointer ${activeTab === 'dataset-explorer' ? 'text-orange-600 font-semibold' : ''}`}
        >
          Dataset Explorer
        </button>
        <span>•</span>
        <button
          onClick={() => onSelectTab && onSelectTab('gap-detection')}
          className={`hover:text-slate-900 transition-colors cursor-pointer ${activeTab === 'gap-detection' ? 'text-orange-600 font-semibold' : ''}`}
        >
          Gap Detection
        </button>
        <span>•</span>
        <button
          onClick={() => onSelectTab && onSelectTab('equipment-research')}
          className={`hover:text-slate-900 transition-colors cursor-pointer ${activeTab === 'equipment-research' ? 'text-orange-600 font-semibold' : ''}`}
        >
          Equipment Research
        </button>
        <span>•</span>
        <button
          onClick={() => onSelectTab && onSelectTab('earth-applications')}
          className={`hover:text-slate-900 transition-colors cursor-pointer ${activeTab === 'earth-applications' ? 'text-orange-600 font-semibold' : ''}`}
        >
          Earth Applications
        </button>
      </div>
    </footer>
  );
}
