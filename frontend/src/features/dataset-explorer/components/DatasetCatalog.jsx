import React, { useState, useMemo } from 'react';
import { StatusBadge } from '../../../components/common/StatusBadge';

export function DatasetCatalog({
  datasets,
  selectedDatasetId,
  onSelectDataset,
  loading,
}) {
  const [searchFilter, setSearchFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all'); // 'all' | 'combustion' | 'spacecraft_telemetry'

  const filteredDatasets = useMemo(() => {
    return datasets.filter((d) => {
      // Category filter
      if (categoryFilter !== 'all' && d.category !== categoryFilter) {
        return false;
      }

      // Search filter
      if (searchFilter.trim()) {
        const query = searchFilter.toLowerCase();
        const matchesId = d.dataset_id?.toLowerCase().includes(query);
        const matchesSource = d.source_file?.toLowerCase().includes(query);
        const matchesNotes = d.notes?.some((n) => n.toLowerCase().includes(query));
        return matchesId || matchesSource || matchesNotes;
      }

      return true;
    });
  }, [datasets, categoryFilter, searchFilter]);

  const counts = useMemo(() => {
    const combustion = datasets.filter((d) => d.category === 'combustion').length;
    const telemetry = datasets.filter((d) => d.category === 'spacecraft_telemetry').length;
    return { all: datasets.length, combustion, telemetry };
  }, [datasets]);

  return (
    <div className="space-y-4">
      {/* Search and Category Filter Toolbar */}
      <div className="space-y-2.5">
        <div className="relative">
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Search datasets (e.g. 'bass', 'saffire', 'pressure')..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-slate-600 font-sans"
          />
          {searchFilter && (
            <button
              onClick={() => setSearchFilter('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white text-xs cursor-pointer"
            >
              ✕
            </button>
          )}
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 text-xs font-mono">
          <button
            onClick={() => setCategoryFilter('all')}
            className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
              categoryFilter === 'all'
                ? 'bg-slate-800 text-white font-medium border border-slate-700'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900/60 border border-slate-850'
            }`}
          >
            All ({counts.all})
          </button>
          <button
            onClick={() => setCategoryFilter('combustion')}
            className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
              categoryFilter === 'combustion'
                ? 'bg-orange-950/70 text-orange-300 font-medium border border-orange-800/60'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900/60 border border-slate-850'
            }`}
          >
            Combustion ({counts.combustion})
          </button>
          <button
            onClick={() => setCategoryFilter('spacecraft_telemetry')}
            className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
              categoryFilter === 'spacecraft_telemetry'
                ? 'bg-emerald-950/70 text-emerald-300 font-medium border border-emerald-800/60'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900/60 border border-slate-850'
            }`}
          >
            Telemetry ({counts.telemetry})
          </button>
        </div>
      </div>

      {/* Dataset List Items */}
      <div className="space-y-2 max-h-[620px] overflow-y-auto pr-1">
        {loading && (
          <div className="p-8 text-center text-xs font-mono text-slate-400 animate-pulse">
            Loading scientific catalog from FastAPI...
          </div>
        )}

        {!loading && filteredDatasets.length === 0 && (
          <div className="p-6 text-center text-xs font-mono text-slate-500 bg-slate-950/40 rounded-xl border border-slate-850">
            No datasets match the current filter.
          </div>
        )}

        {filteredDatasets.map((d) => {
          const isSelected = selectedDatasetId === d.dataset_id;

          return (
            <div
              key={d.dataset_id}
              onClick={() => onSelectDataset(d.dataset_id)}
              className={`p-3.5 rounded-xl border text-left transition-all duration-150 cursor-pointer flex flex-col justify-between space-y-2.5 group ${
                isSelected
                  ? 'bg-slate-850 border-orange-500 ring-1 ring-orange-500/40 shadow-lg'
                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-850/80'
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-1.5">
                  <span className="font-mono text-xs font-semibold text-white group-hover:text-orange-200 transition-colors truncate">
                    {d.dataset_id}
                  </span>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-orange-400 flex-shrink-0 animate-pulse" />
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-1.5">
                  <StatusBadge type="category" value={d.category} size="xs" />
                  <StatusBadge type="granularity" value={d.granularity} size="xs" />
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span className="text-slate-300 font-medium">
                  {d.record_count.toLocaleString()} records
                </span>
                <span className="text-[10px] text-amber-400/90 bg-amber-950/40 px-1.5 py-0.2 rounded border border-amber-900/30">
                  {d.scientific_validation || 'pending'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
