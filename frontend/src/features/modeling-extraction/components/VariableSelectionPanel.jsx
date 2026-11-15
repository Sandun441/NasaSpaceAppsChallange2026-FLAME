import React, { useState } from 'react';
import { Button } from '../../../components/common/Button';

export function VariableSelectionPanel({
  schema,
  selectedFeatures = [],
  onToggleFeature,
  onSelectAllFeatures,
  onClearFeatures,
  selectedTargetId,
  onSelectTarget,
  filters,
  onFilterChange,
  onApplyFilters,
  isLoading,
}) {
  const [showUnsupported, setShowUnsupported] = useState(false);

  if (!schema) return null;

  const supportedTargets = schema.supported_targets || [];
  const unsupportedTargets = schema.unsupported_targets || [];
  const availableFeatures = schema.available_features || [];
  const isTelemetry = schema.paradigm === 'time_series_telemetry' || schema.paradigm === 'vehicle_telemetry';

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-6">
      {/* Top Banner / Dataset Overview */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pb-4 border-b border-slate-200">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-orange-600 font-semibold">
            Feature & Target Configuration
          </span>
          <h3 className="text-sm sm:text-base font-semibold text-slate-900">
            {schema.name}
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={onSelectAllFeatures}
            className="text-[11px] py-1 text-slate-700 hover:text-slate-900 bg-white border-slate-200"
          >
            Select All Features
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={onClearFeatures}
            className="text-[11px] py-1 text-slate-600 hover:text-slate-800 bg-white border-slate-200"
          >
            Clear Features
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Column 1: Target Variable Selection (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <span>Target Variable (Y)</span>
              <span className="text-slate-500 font-normal">({supportedTargets.length} verified)</span>
            </h4>
            <span className="text-[10px] text-orange-600 font-mono font-semibold">
              {selectedTargetId ? 'Supervised Mode' : 'Exploratory Mode'}
            </span>
          </div>

          <div className="space-y-2">
            {/* Option: None / Exploratory */}
            <label
              className={`p-3 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${
                !selectedTargetId
                  ? 'bg-orange-50 border-orange-400 ring-1 ring-orange-400/40 text-slate-900'
                  : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-600'
              }`}
            >
              <input
                type="radio"
                name="target_selection"
                checked={!selectedTargetId}
                onChange={() => onSelectTarget(null)}
                className="mt-0.5 text-orange-500 focus:ring-orange-500"
              />
              <div className="text-xs">
                <span className="font-semibold text-slate-900">No Target (Exploratory / Unsupervised Mode)</span>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Export verified input features without assigning a supervised target column.
                </p>
              </div>
            </label>

            {/* Supported Targets */}
            {supportedTargets.map((target) => {
              const isSelected = selectedTargetId === target.id;
              const isMeasured = target.category === 'verified_measured';

              return (
                <label
                  key={target.id}
                  className={`p-3 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-orange-50 border-orange-400 ring-1 ring-orange-400/40 shadow-xs'
                      : 'bg-slate-50 hover:bg-slate-100 border-slate-200'
                  }`}
                >
                  <input
                    type="radio"
                    name="target_selection"
                    checked={isSelected}
                    onChange={() => onSelectTarget(target.id)}
                    className="mt-0.5 text-orange-500 focus:ring-orange-500"
                  />
                  <div className="text-xs space-y-1 flex-1">
                    <div className="flex items-center justify-between gap-1 flex-wrap">
                      <span className="font-semibold text-slate-900">{target.label}</span>
                      <span className="text-[10px] font-mono text-orange-700 bg-orange-50 px-1.5 py-0.5 rounded border border-orange-200 font-semibold">
                        {target.unit}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded-full border font-medium ${
                          isMeasured
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : 'bg-sky-50 text-sky-800 border-sky-200'
                        }`}
                      >
                        {isMeasured ? 'Direct Measured' : 'Validated Derived'}
                      </span>
                      {target.formula && (
                        <span className="text-[10px] font-mono text-slate-500">
                          Formula: {target.formula}
                        </span>
                      )}
                    </div>

                    <p className="text-[11px] text-slate-600 leading-tight">
                      {target.description}
                    </p>
                  </div>
                </label>
              );
            })}
          </div>

          {/* Unsupported Targets Collapsible Warning */}
          {unsupportedTargets.length > 0 && (
            <div className="pt-2">
              <button
                type="button"
                onClick={() => setShowUnsupported(!showUnsupported)}
                className="text-[11px] font-mono text-amber-700 hover:text-amber-800 font-semibold flex items-center gap-1.5 cursor-pointer"
              >
                <span>{showUnsupported ? '▼' : '►'}</span>
                <span>Uninstrumented Targets in this Dataset ({unsupportedTargets.length})</span>
              </button>

              {showUnsupported && (
                <div className="mt-2 space-y-2 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
                  {unsupportedTargets.map((ut) => (
                    <div key={ut.id} className="space-y-0.5">
                      <span className="font-semibold text-amber-800">
                        ✕ {ut.label} [{ut.unit}]
                      </span>
                      <p className="text-[11px] text-slate-700 leading-relaxed font-sans">
                        {ut.reason}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Column 2: Input Features Selection (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <span>Candidate Input Features (X)</span>
              <span className="text-slate-500 font-normal">
                ({selectedFeatures.length} of {availableFeatures.length} selected)
              </span>
            </h4>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[320px] overflow-y-auto pr-1">
            {availableFeatures.map((feat) => {
              const isChecked = selectedFeatures.includes(feat.id);

              return (
                <label
                  key={feat.id}
                  className={`p-2.5 rounded-xl border flex items-start gap-2.5 cursor-pointer transition-all ${
                    isChecked
                      ? 'bg-orange-50 border-orange-300 text-slate-900'
                      : 'bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-600'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => onToggleFeature(feat.id)}
                    className="mt-0.5 rounded border-slate-300 text-orange-500 focus:ring-orange-500"
                  />
                  <div className="text-xs flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="font-medium truncate text-slate-900">{feat.label}</span>
                      <span className="text-[10px] font-mono text-slate-500 shrink-0">
                        [{feat.unit}]
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-[10px] font-mono text-slate-500 truncate">
                        Col: {feat.source_col}
                      </span>
                      <span className="text-[9px] px-1 py-0.2 rounded bg-white border border-slate-200 text-slate-600">
                        {feat.category === 'verified_measured' ? 'measured' : 'metadata'}
                      </span>
                    </div>
                  </div>
                </label>
              );
            })}
          </div>

          {/* Environmental Condition Filters */}
          <div className="pt-3 border-t border-slate-200 space-y-3">
            <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
              Experimental Condition Filters
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Material Filter */}
              <div>
                <label className="text-[11px] font-mono text-slate-600 block mb-1">
                  Fuel Material Filter:
                </label>
                <input
                  type="text"
                  value={filters.materialFilter || ''}
                  onChange={(e) => onFilterChange('materialFilter', e.target.value)}
                  placeholder="e.g. PMMA, cotton..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500"
                />
              </div>

              {/* Min Initial Oxygen */}
              <div>
                <label className="text-[11px] font-mono text-slate-600 block mb-1">
                  Min O₂ (% vol):
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={filters.minOxygen ?? ''}
                  onChange={(e) => onFilterChange('minOxygen', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="e.g. 15.0"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 font-mono"
                />
              </div>

              {/* Min Flow Velocity */}
              <div>
                <label className="text-[11px] font-mono text-slate-600 block mb-1">
                  Min Flow (cm/s):
                </label>
                <input
                  type="number"
                  step="1.0"
                  value={filters.minFlow ?? ''}
                  onChange={(e) => onFilterChange('minFlow', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="e.g. 2.0"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 font-mono"
                />
              </div>
            </div>

            {/* Time Window (if telemetry) */}
            {isTelemetry && (
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-[11px] font-mono text-orange-600 block mb-1">
                    Telemetry Window Start (s):
                  </label>
                  <input
                    type="number"
                    step="5.0"
                    value={filters.startTime ?? ''}
                    onChange={(e) => onFilterChange('startTime', e.target.value ? parseFloat(e.target.value) : null)}
                    placeholder="0.0"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-orange-600 block mb-1">
                    Telemetry Window End (s):
                  </label>
                  <input
                    type="number"
                    step="5.0"
                    value={filters.endTime ?? ''}
                    onChange={(e) => onFilterChange('endTime', e.target.value ? parseFloat(e.target.value) : null)}
                    placeholder="e.g. 120.0"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-orange-500 font-mono"
                  />
                </div>
              </div>
            )}

            {/* Quality and Anomaly Safeguard Toggles */}
            <div className="pt-2 border-t border-slate-200 flex flex-wrap gap-4 text-xs">
              <label className="flex items-center gap-2 cursor-pointer text-slate-700 hover:text-slate-900">
                <input
                  type="checkbox"
                  checked={Boolean(filters.excludeFlaggedAnomalies)}
                  onChange={(e) => onFilterChange('excludeFlaggedAnomalies', e.target.checked)}
                  className="rounded border-slate-300 text-orange-500 focus:ring-orange-500"
                />
                <span className="flex items-center gap-1.5">
                  <span>Exclude Flagged Empirical Anomalies</span>
                  <span className="text-[10px] text-amber-700 font-mono">(drops uncorrected source logs)</span>
                </span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-slate-700 hover:text-slate-900">
                <input
                  type="checkbox"
                  checked={Boolean(filters.completeCasesOnly)}
                  onChange={(e) => onFilterChange('completeCasesOnly', e.target.checked)}
                  className="rounded border-slate-300 text-orange-500 focus:ring-orange-500"
                />
                <span className="flex items-center gap-1.5">
                  <span>Complete Cases Only</span>
                  <span className="text-[10px] text-emerald-700 font-mono">(drop records with any NaN)</span>
                </span>
              </label>
            </div>

            {/* Apply Button */}
            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                size="sm"
                onClick={onApplyFilters}
                disabled={isLoading}
                className="bg-orange-500 hover:bg-orange-600 text-white font-medium"
              >
                {isLoading ? 'Updating Preview...' : '↻ Apply Filters & Update Preview'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
