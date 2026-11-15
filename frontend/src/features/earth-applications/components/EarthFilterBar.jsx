import React from 'react';
import { FilterIcon, RotateCcwIcon, GridIcon, TableIcon } from './EarthIcons';

export function EarthFilterBar({
  categories = [],
  selectedCategory = 'all',
  onSelectCategory,
  selectedInvestigation = 'all',
  onSelectInvestigation,
  selectedClassification = 'all',
  onSelectClassification,
  selectedProvenance = 'all',
  onSelectProvenance,
  searchQuery = '',
  onSearchChange,
  viewMode = 'cards',
  onToggleViewMode,
  filteredCount = 0,
  totalCount = 11,
  onResetFilters,
}) {
  const hasActiveFilters =
    selectedCategory !== 'all' ||
    selectedInvestigation !== 'all' ||
    selectedClassification !== 'all' ||
    selectedProvenance !== 'all' ||
    Boolean(searchQuery.trim());

  const investigationsList = [
    { id: 'all', label: 'All Investigations (7)' },
    { id: 'saffire_iii', label: 'Saffire-III (4)' },
    { id: 'bass_ii', label: 'BASS-II (3)' },
    { id: 'flex', label: 'FLEX / FLEX-2 (2)' },
    { id: 'same', label: 'SAME (1)' },
    { id: 'acme', label: 'ACME (1)' },
    { id: 'sofie', label: 'SOFIE (1)' },
    { id: 'cygnus_vehicle_telemetry', label: 'Cygnus Telemetry (1)' },
  ];

  const classificationsList = [
    { id: 'all', label: 'All Classes' },
    { id: 'supported_research_implication', label: 'Supported Implication (10)' },
    { id: 'exploratory_hypothesis', label: 'Exploratory Hypothesis (1)' },
    { id: 'documented_application', label: 'Documented Application (0)' },
  ];

  return (
    <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
      {/* Top Filter Controls Row */}
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex items-center gap-2">
          <FilterIcon className="w-4 h-4 text-orange-600" />
          <span className="text-xs font-semibold text-slate-900 tracking-tight">
            Evidence Filters
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
            {filteredCount} of {totalCount} records
          </span>
        </div>

        {/* View Mode & Reset Controls */}
        <div className="flex items-center gap-2">
          {/* Card / Table Toggle */}
          <div className="flex items-center p-0.5 rounded-lg bg-slate-100 border border-slate-200">
            <button
              onClick={() => onToggleViewMode('cards')}
              title="Cards View"
              className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                viewMode === 'cards'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <GridIcon className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onToggleViewMode('table')}
              title="Scientific Table View"
              className={`p-1.5 rounded-md transition-colors cursor-pointer ${
                viewMode === 'table'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Reset Filters */}
          {hasActiveFilters && (
            <button
              onClick={onResetFilters}
              className="text-xs font-mono text-amber-700 hover:text-amber-800 flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-amber-50 border border-amber-200 hover:bg-amber-100 transition-colors cursor-pointer"
            >
              <RotateCcwIcon className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Selectors Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
        {/* Category Select */}
        <div>
          <label className="block text-[10px] font-mono text-slate-600 mb-1">
            Category Domain
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => onSelectCategory(e.target.value)}
            className="w-full text-xs font-mono bg-slate-50 text-slate-900 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-orange-500 cursor-pointer"
          >
            <option value="all">All Domains (7 categories)</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title} ({c.evidence_count})
              </option>
            ))}
          </select>
        </div>

        {/* Investigation Select */}
        <div>
          <label className="block text-[10px] font-mono text-slate-600 mb-1">
            NASA Investigation
          </label>
          <select
            value={selectedInvestigation}
            onChange={(e) => onSelectInvestigation(e.target.value)}
            className="w-full text-xs font-mono bg-slate-50 text-slate-900 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-orange-500 cursor-pointer"
          >
            {investigationsList.map((inv) => (
              <option key={inv.id} value={inv.id}>
                {inv.label}
              </option>
            ))}
          </select>
        </div>

        {/* Classification Select */}
        <div>
          <label className="block text-[10px] font-mono text-slate-600 mb-1">
            Evidence Classification
          </label>
          <select
            value={selectedClassification}
            onChange={(e) => onSelectClassification(e.target.value)}
            className="w-full text-xs font-mono bg-slate-50 text-slate-900 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-orange-500 cursor-pointer"
          >
            {classificationsList.map((cls) => (
              <option key={cls.id} value={cls.id}>
                {cls.label}
              </option>
            ))}
          </select>
        </div>

        {/* Flight Provenance Select */}
        <div>
          <label className="block text-[10px] font-mono text-slate-600 mb-1">
            Flight Provenance (Dim. A)
          </label>
          <select
            value={selectedProvenance}
            onChange={(e) => onSelectProvenance(e.target.value)}
            className="w-full text-xs font-mono bg-slate-50 text-slate-900 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-orange-500 cursor-pointer"
          >
            <option value="all">All Provenance</option>
            <option value="locally_verified">Locally Verified (6)</option>
            <option value="external_literature_verified">External Literature (5)</option>
          </select>
        </div>

        {/* Search Input */}
        <div>
          <label className="block text-[10px] font-mono text-slate-600 mb-1">
            Search Findings & Relevance
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="e.g. soot, PMMA, duct, cool flame..."
            className="w-full text-xs font-mono bg-slate-50 text-slate-900 border border-slate-200 rounded-lg px-2.5 py-1.5 placeholder:text-slate-400 focus:outline-none focus:border-orange-500"
          />
        </div>
      </div>
    </div>
  );
}
