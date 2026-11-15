import React, { useState, useEffect } from 'react';
import { flameApi } from '../../../services/flameApi';

const GRAVITY_ROWS = [
  { id: 'normal', label: 'Normal Earth', code: '1.0g' },
  { id: 'micro', label: 'Microgravity', code: '0g (μg)' },
  { id: 'partial_lunar', label: 'Partial Lunar', code: '0.16g' },
  { id: 'partial_mars', label: 'Partial Martian', code: '0.38g' },
];

const OXYGEN_COLS = [
  { id: 'low_o2', label: 'Hypoxic', sub: '< 18.0% O₂' },
  { id: 'normal_o2', label: 'Normal', sub: '18.0 – 22.0% O₂' },
  { id: 'elevated_o2', label: 'Elevated', sub: '22.0 – 34.0% O₂' },
  { id: 'high_o2', label: 'High', sub: '> 34.0% O₂' },
];

const MATERIAL_ROWS = [
  { id: 'solid-flat', label: 'Solid-Flat Fuels', code: 'PMMA, Cotton, SIBAL' },
  { id: 'solid-thick', label: 'Solid-Thick Fuels', code: 'Thick Cast Polymers' },
  { id: 'droplet', label: 'Liquid Droplets', code: 'Heptane, Alkanes (FLEX)' },
  { id: 'gaseous', label: 'Gaseous Fuels', code: 'Methane, Ethylene' },
];

const AIRFLOW_COLS = [
  { id: 'quiescent', label: 'Quiescent', sub: '0 cm/s' },
  { id: 'low-flow', label: 'Low-Flow', sub: '< 10 cm/s' },
  { id: 'high-flow', label: 'High-Flow', sub: '> 10 cm/s' },
];

export function CoverageMatrix({
  onSelectCellGap,
  onAnalyzeRegime,
  activeFindingId,
  initialFinding,
  onOpenFindingModal,
}) {
  const [activeMatrixType, setActiveMatrixType] = useState('gravity_vs_oxygen');
  const [matrixData, setMatrixData] = useState(null);
  const [selectedCellKey, setSelectedCellKey] = useState(activeFindingId ? null : 'micro_elevated_o2');
  const [activeFinding, setActiveFinding] = useState(initialFinding || null);
  const [highlightedRowId, setHighlightedRowId] = useState(null);
  const [highlightedColId, setHighlightedColId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchMatrix = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await flameApi.getCoverageMatrix('all');
        if (isMounted) {
          if (res?.status === 'success' && res.matrix) {
            setMatrixData(res.matrix);
          } else {
            setMatrixData(res || {});
          }
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load coverage matrix:', err);
          setError(err.message || 'Failed to load coverage matrix from backend.');
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchMatrix();
    return () => {
      isMounted = false;
    };
  }, []);

  // Synchronize and resolve active finding for matrix highlighting
  useEffect(() => {
    let isMounted = true;
    if (!activeFindingId) {
      return;
    }

    const applyFinding = (finding) => {
      setActiveFinding(finding);
      const dims = finding.scientific_dimensions || {};

      if (dims.gravity) {
        setActiveMatrixType('gravity_vs_oxygen');
        setHighlightedRowId(dims.gravity);
        if (dims.oxygen) {
          setHighlightedColId(dims.oxygen);
          setSelectedCellKey(`${dims.gravity}_${dims.oxygen}`);
        } else {
          // Do not arbitrarily select an oxygen category when the finding only specifies gravity!
          setHighlightedColId(null);
          setSelectedCellKey(null);
        }
      } else if (dims.fuel_family) {
        setActiveMatrixType('material_vs_airflow');
        setHighlightedRowId(dims.fuel_family);
        if (dims.airflow) {
          setHighlightedColId(dims.airflow);
          setSelectedCellKey(`${dims.fuel_family}_${dims.airflow}`);
        } else {
          setHighlightedColId(null);
          setSelectedCellKey(null);
        }
      } else if (dims.airflow) {
        setActiveMatrixType('material_vs_airflow');
        setHighlightedRowId(null);
        setHighlightedColId(dims.airflow);
        setSelectedCellKey(null);
      } else if (dims.oxygen) {
        setActiveMatrixType('gravity_vs_oxygen');
        setHighlightedRowId(null);
        setHighlightedColId(dims.oxygen);
        setSelectedCellKey(null);
      } else {
        setSelectedCellKey(null);
      }
    };

    if (
      initialFinding &&
      (initialFinding.finding_id === activeFindingId || initialFinding.id === activeFindingId)
    ) {
      applyFinding(initialFinding);
    } else {
      const fetchFinding = async () => {
        try {
          const res = await flameApi.getGapFindingDetail(activeFindingId);
          if (isMounted && res?.status === 'success' && res.finding) {
            applyFinding(res.finding);
          }
        } catch (err) {
          console.warn('Could not resolve research gap finding for matrix:', err);
        }
      };
      fetchFinding();
    }

    return () => {
      isMounted = false;
    };
  }, [activeFindingId, initialFinding]);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'heavy':
        return {
          bg: 'bg-emerald-50 hover:bg-emerald-100/70 border-emerald-200 text-emerald-900',
          dot: 'bg-emerald-500',
          label: 'Robust Evidence',
          intensity: 'Heavy (≥10)',
        };
      case 'moderate':
        return {
          bg: 'bg-sky-50 hover:bg-sky-100/70 border-sky-200 text-sky-900',
          dot: 'bg-sky-500',
          label: 'Moderate Evidence',
          intensity: 'Moderate (3-9)',
        };
      case 'limited':
        return {
          bg: 'bg-amber-50 hover:bg-amber-100/70 border-amber-200 text-amber-900',
          dot: 'bg-amber-500',
          label: 'Limited Evidence',
          intensity: 'Limited (1-2)',
        };
      case 'gap':
      default:
        return {
          bg: 'bg-rose-50/60 hover:bg-rose-100/70 border-rose-200 text-rose-900 border-dashed',
          dot: 'bg-rose-500 animate-pulse',
          label: 'Critical Gap',
          intensity: 'Unrepresented',
        };
    }
  };

  const currentMatrix = matrixData?.[activeMatrixType] || {};
  const selectedCellData = currentMatrix[selectedCellKey] || null;

  // Determine row and column objects based on matrix type
  let selectedRowLabel = '';
  let selectedColLabel = '';
  if (selectedCellKey) {
    if (activeMatrixType === 'gravity_vs_oxygen') {
      const [grav, oxy] = selectedCellKey.split(/_(low_o2|normal_o2|elevated_o2|high_o2)/).filter(Boolean);
      const rowObj = GRAVITY_ROWS.find((r) => r.id === grav);
      const colObj = OXYGEN_COLS.find((c) => c.id === oxy);
      selectedRowLabel = rowObj ? `${rowObj.label} (${rowObj.code})` : grav;
      selectedColLabel = colObj ? `${colObj.label} (${colObj.sub})` : oxy;
    } else {
      const parts = selectedCellKey.split('_');
      const matId = parts[0];
      const airId = parts.slice(1).join('_');
      const rowObj = MATERIAL_ROWS.find((r) => r.id === matId);
      const colObj = AIRFLOW_COLS.find((c) => c.id === airId);
      selectedRowLabel = rowObj ? `${rowObj.label}` : matId;
      selectedColLabel = colObj ? `${colObj.label} (${colObj.sub})` : airId;
    }
  }

  const handleSwitchMatrix = (type) => {
    setActiveMatrixType(type);
    if (type === 'gravity_vs_oxygen') {
      setSelectedCellKey(highlightedRowId && highlightedRowId.startsWith('partial') ? null : 'micro_elevated_o2');
    } else {
      setSelectedCellKey('solid-flat_low-flow');
    }
  };

  const handleAnalyzeInExplorer = () => {
    if (!onAnalyzeRegime) return;
    if (selectedCellKey) {
      if (activeMatrixType === 'gravity_vs_oxygen') {
        const [grav, oxy] = selectedCellKey.split(/_(low_o2|normal_o2|elevated_o2|high_o2)/).filter(Boolean);
        onAnalyzeRegime({
          gravity: grav,
          oxygen_regime: oxy,
        });
      } else {
        const parts = selectedCellKey.split('_');
        const matId = parts[0];
        const airId = parts.slice(1).join('_');
        onAnalyzeRegime({
          fuel_family: matId,
          airflow_regime: airId,
        });
      }
    } else if (activeFinding) {
      onAnalyzeRegime({
        gravity: activeFinding.scientific_dimensions?.gravity || 'all',
        oxygen_regime: activeFinding.scientific_dimensions?.oxygen || 'all',
        fuel_family: activeFinding.scientific_dimensions?.fuel_family || 'all',
        airflow_regime: activeFinding.scientific_dimensions?.airflow || 'all',
      });
    }
  };

  return (
    <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-5 shadow-sm">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Research Coverage Heatmap Matrix</span>
            <span className="text-[10px] font-mono text-orange-700 bg-orange-50 border border-orange-200 px-2 py-0.5 rounded">
              Interactive Regime Inspector
            </span>
          </h2>
          <p className="text-xs text-slate-500">
            Compare empirical runs and coverage densities across mission-critical environmental and material regimes.
          </p>
        </div>

        {/* Matrix Switcher Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-100 border border-slate-200 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => handleSwitchMatrix('gravity_vs_oxygen')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors cursor-pointer ${
              activeMatrixType === 'gravity_vs_oxygen'
                ? 'bg-white text-orange-700 border border-orange-300 font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Gravity × Oxygen
          </button>
          <button
            type="button"
            onClick={() => handleSwitchMatrix('material_vs_airflow')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors cursor-pointer ${
              activeMatrixType === 'material_vs_airflow'
                ? 'bg-white text-orange-700 border border-orange-300 font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Fuel Material × Airflow
          </button>
        </div>
      </div>

      {/* Legend Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-500 px-3 py-2 rounded-lg bg-slate-50 border border-slate-200">
        <span className="text-slate-700 font-medium">Empirical Density Standard:</span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" /> Robust (≥10 runs)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-sky-500" /> Moderate (3–9 runs)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-500" /> Limited (1–2 runs)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500" /> Gap (0 runs)
          </span>
        </div>
      </div>

      {isLoading ? (
        <div className="py-12 text-center space-y-2">
          <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <div className="text-xs font-mono text-slate-500">Loading coverage heatmap matrix...</div>
        </div>
      ) : error ? (
        <div className="py-8 text-center text-xs text-rose-600 font-mono">
          Error loading matrix: {error}
        </div>
      ) : (
        /* Matrix Heatmap Grid */
        <div className="overflow-x-auto pb-2">
          {activeMatrixType === 'gravity_vs_oxygen' ? (
            /* Gravity vs Oxygen 4x4 Grid */
            <div className="min-w-[660px]">
              {/* Column Headers */}
              <div className="grid grid-cols-5 gap-2 text-center text-xs font-mono pb-2">
                <div className="text-left text-slate-500 uppercase text-[10px] tracking-wider self-end pb-1 pl-2">
                  Gravity Regime ↓ / O₂ Regime →
                </div>
                {OXYGEN_COLS.map((col) => (
                  <div key={col.id} className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="font-semibold text-slate-800">{col.label}</div>
                    <div className="text-[10px] text-slate-500">{col.sub}</div>
                  </div>
                ))}
              </div>

              {/* Rows */}
              <div className="space-y-2">
                {GRAVITY_ROWS.map((row) => {
                  const isRowHighlighted = highlightedRowId === row.id;

                  return (
                    <div key={row.id} className="grid grid-cols-5 gap-2 items-stretch">
                      {/* Row Header */}
                      <div
                        className={`p-2.5 rounded-lg border flex flex-col justify-center transition-all ${
                          isRowHighlighted
                            ? 'bg-orange-50 border-orange-400 shadow-sm ring-1 ring-orange-400/60'
                            : 'bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-1">
                          <div
                            className={`text-xs font-semibold ${
                              isRowHighlighted ? 'text-orange-950 font-bold' : 'text-slate-800'
                            }`}
                          >
                            {row.label}
                          </div>
                          {isRowHighlighted && (
                            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-orange-500 text-white font-bold uppercase tracking-wider animate-pulse">
                              Target
                            </span>
                          )}
                        </div>
                        <div
                          className={`text-[10px] font-mono ${
                            isRowHighlighted ? 'text-orange-800 font-medium' : 'text-orange-600'
                          }`}
                        >
                          {row.code}
                        </div>
                        {isRowHighlighted && (
                          <div className="text-[8.5px] font-mono text-orange-700 mt-0.5 leading-tight">
                            Finding Focus Regime
                          </div>
                        )}
                      </div>

                      {/* Cells */}
                      {OXYGEN_COLS.map((col) => {
                        const cellKey = `${row.id}_${col.id}`;
                        const cell = currentMatrix[cellKey] || { status: 'gap', experiment_count: 0, usable_records: 0 };
                        const badge = getStatusBadge(cell.status);
                        const isSelected = selectedCellKey === cellKey;
                        const isCellInHighlightedRow = isRowHighlighted;
                        const isCellInHighlightedCol = highlightedColId === col.id;
                        const isHighlighted = isCellInHighlightedRow || isCellInHighlightedCol;
                        const runCount = cell.experiment_count ?? cell.usable_records ?? 0;

                        return (
                          <button
                            key={cellKey}
                            type="button"
                            onClick={() => setSelectedCellKey(cellKey)}
                            className={`p-3 rounded-xl border text-left transition-all duration-150 flex flex-col justify-between cursor-pointer ${
                              badge.bg
                            } ${
                              isSelected
                                ? 'ring-2 ring-orange-500 ring-offset-2 ring-offset-white border-orange-500 shadow-sm scale-[1.02]'
                                : isHighlighted
                                ? 'border-orange-400 bg-orange-50/70 hover:border-orange-500'
                                : ''
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1.5 text-[11px] font-mono">
                                <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
                                <span className="font-medium">{badge.intensity}</span>
                              </span>
                              <span className="text-[10px] font-mono opacity-90 font-bold">
                                {runCount} runs
                              </span>
                            </div>

                            <div className="mt-3 pt-1 border-t border-slate-200/80 flex items-center justify-between text-[10px] font-mono">
                              <span className="opacity-80 text-[9px] truncate">
                                {cell.gap_status ? cell.gap_status.split(':')[0] : badge.label}
                              </span>
                              <span className="text-xs">
                                {isSelected ? '◉' : isHighlighted ? '◈' : '○'}
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Material vs Airflow Grid */
            <div className="min-w-[620px]">
              {/* Column Headers */}
              <div className="grid grid-cols-4 gap-2 text-center text-xs font-mono pb-2">
                <div className="text-left text-slate-500 uppercase text-[10px] tracking-wider self-end pb-1 pl-2">
                  Fuel Material ↓ / Airflow Velocity →
                </div>
                {AIRFLOW_COLS.map((col) => (
                  <div key={col.id} className="p-2 rounded-lg bg-slate-50 border border-slate-200">
                    <div className="font-semibold text-slate-800">{col.label}</div>
                    <div className="text-[10px] text-slate-500">{col.sub}</div>
                  </div>
                ))}
              </div>

              {/* Rows */}
              <div className="space-y-2">
                {MATERIAL_ROWS.map((row) => {
                  const isRowHighlighted = highlightedRowId === row.id;

                  return (
                    <div key={row.id} className="grid grid-cols-4 gap-2 items-stretch">
                      {/* Row Header */}
                      <div
                        className={`p-2.5 rounded-lg border flex flex-col justify-center transition-all ${
                          isRowHighlighted
                            ? 'bg-orange-50 border-orange-400 shadow-sm ring-1 ring-orange-400/60'
                            : 'bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-1">
                          <div
                            className={`text-xs font-semibold ${
                              isRowHighlighted ? 'text-orange-950 font-bold' : 'text-slate-800'
                            }`}
                          >
                            {row.label}
                          </div>
                          {isRowHighlighted && (
                            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-orange-500 text-white font-bold uppercase tracking-wider animate-pulse">
                              Target
                            </span>
                          )}
                        </div>
                        <div
                          className={`text-[10px] font-mono ${
                            isRowHighlighted ? 'text-orange-800 font-medium' : 'text-orange-600'
                          }`}
                        >
                          {row.code}
                        </div>
                        {isRowHighlighted && (
                          <div className="text-[8.5px] font-mono text-orange-700 mt-0.5 leading-tight">
                            Finding Focus Material
                          </div>
                        )}
                      </div>

                      {/* Cells */}
                      {AIRFLOW_COLS.map((col) => {
                        const cellKey = `${row.id}_${col.id}`;
                        const cell = currentMatrix[cellKey] || { status: 'gap', experiment_count: 0 };
                        const badge = getStatusBadge(cell.status);
                        const isSelected = selectedCellKey === cellKey;
                        const isCellInHighlightedRow = isRowHighlighted;
                        const isCellInHighlightedCol = highlightedColId === col.id;
                        const isHighlighted = isCellInHighlightedRow || isCellInHighlightedCol;
                        const runCount = cell.experiment_count ?? 0;

                        return (
                          <button
                            key={cellKey}
                            type="button"
                            onClick={() => setSelectedCellKey(cellKey)}
                            className={`p-3 rounded-xl border text-left transition-all duration-150 flex flex-col justify-between cursor-pointer ${
                              badge.bg
                            } ${
                              isSelected
                                ? 'ring-2 ring-orange-500 ring-offset-2 ring-offset-white border-orange-500 shadow-sm scale-[1.02]'
                                : isHighlighted
                                ? 'border-orange-400 bg-orange-50/70 hover:border-orange-500'
                                : ''
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1.5 text-[11px] font-mono">
                                <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
                                <span className="font-medium">{badge.intensity}</span>
                              </span>
                              <span className="text-[10px] font-mono opacity-90 font-bold">
                                {runCount} runs
                              </span>
                            </div>

                            <div className="mt-3 pt-1 border-t border-slate-200/80 flex items-center justify-between text-[10px] font-mono">
                              <span className="opacity-80 text-[9px]">{badge.label}</span>
                              <span className="text-xs">
                                {isSelected ? '◉' : isHighlighted ? '◈' : '○'}
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Case 1: Finding-Specific Inspection Panel (when active finding has no single cell key) */}
      {activeFinding && !selectedCellKey && (
        <div className="p-4 sm:p-6 rounded-2xl bg-orange-50/40 border border-orange-300 space-y-4 animate-in fade-in duration-200 shadow-sm">
          {/* Panel Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-orange-200">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
                <span className="text-[10.5px] font-mono font-bold px-2 py-0.5 rounded bg-white text-orange-700 border border-orange-300">
                  {activeFinding.finding_id}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 uppercase">
                  {activeFinding.gap_type || 'coverage_gap'}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                  Heuristic Priority: {(activeFinding.priority_score ?? 0).toFixed(1)} / 10
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                  Confidence: {activeFinding.evidence_confidence?.level || 'HIGH'}
                </span>
              </div>

              <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight leading-snug">
                {activeFinding.title}
              </h3>

              <div className="text-xs font-mono text-orange-700 flex flex-wrap items-center gap-1.5 pt-0.5">
                <span>Target Regime:</span>
                <strong className="text-slate-900 font-semibold">
                  {highlightedRowId === 'partial_lunar'
                    ? 'Partial Lunar Gravity (0.16g) • Applicable across all Oxygen levels (< 18.0% to > 34.0% O₂)'
                    : activeFinding.title}
                </strong>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
              <button
                type="button"
                onClick={() => {
                  if (onOpenFindingModal) {
                    onOpenFindingModal(activeFinding);
                  } else if (onSelectCellGap) {
                    onSelectCellGap(activeFinding);
                  }
                }}
                className="px-3 py-1.5 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs font-mono transition-colors shadow-sm cursor-pointer flex items-center gap-1"
              >
                <span>Inspect Full Finding</span>
                <span>↗</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setActiveFinding(null);
                  setHighlightedRowId(null);
                  setHighlightedColId(null);
                  setSelectedCellKey('micro_elevated_o2');
                }}
                className="px-2.5 py-1.5 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 hover:text-slate-900 text-xs font-mono transition-colors cursor-pointer"
                title="Exit finding view and return to standard cell inspector"
              >
                Clear Highlight ✕
              </button>
            </div>
          </div>

          {/* Metric / Denominator Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase block">Observed Runs</span>
              <span className="text-sm font-bold text-rose-600">
                {activeFinding.observed_usable_run_count ?? 0} Usable Runs
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase block">Database Scope</span>
              <span
                className="text-[11px] font-semibold text-slate-800 truncate block"
                title={activeFinding.denominator_and_scope}
              >
                {activeFinding.denominator_and_scope || '0 of 133 runs in FLAME'}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase block">Gravity Condition</span>
              <span className="text-[11px] font-semibold text-orange-700">
                {activeFinding.scientific_dimensions?.gravity || 'Partial Lunar (0.16g)'}
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase block">Oxygen Scope</span>
              <span className="text-[11px] font-semibold text-sky-700">
                {activeFinding.scientific_dimensions?.oxygen || 'All Regimes (<18% to >34%)'}
              </span>
            </div>
          </div>

          {/* Scientific Explanation & Physical Context */}
          <div className="space-y-2">
            <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block">
              Scientific Context & Physical Combustion Significance
            </span>
            <p className="text-xs text-slate-700 leading-relaxed bg-white p-3 rounded-xl border border-slate-200">
              {activeFinding.explanation}
            </p>
          </div>

          {/* Limitations & Next Step */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {/* Limitations */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 space-y-1.5">
              <span className="text-[10.5px] font-mono text-slate-700 uppercase tracking-wider block font-semibold">
                Scientific & Experimental Limitations:
              </span>
              {activeFinding.limitations && activeFinding.limitations.length > 0 ? (
                <ul className="list-disc list-inside space-y-1 text-[11px] text-slate-600">
                  {activeFinding.limitations.map((lim, idx) => (
                    <li key={idx}>{lim}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-[11px] text-slate-400 italic">No specific limitations documented.</p>
              )}
            </div>

            {/* Recommended Next Step & Scope Notice */}
            <div className="p-3.5 rounded-xl bg-white border border-slate-200 space-y-2">
              <div className="space-y-1">
                <span className="text-[10.5px] font-mono text-orange-700 uppercase tracking-wider block font-semibold">
                  Actionable Next Step:
                </span>
                <p className="text-[11px] text-slate-700">
                  {activeFinding.recommended_next_step || 'Consult NASA PSI archives for candidate partial-gravity datasets.'}
                </p>
              </div>

              <div className="text-[10px] font-mono text-slate-500 border-t border-slate-200 pt-1.5">
                <strong>Database Notice:</strong>{' '}
                {activeFinding.database_scope_disclaimer ||
                  'Unrepresented in FLAME database. Missing data in FLAME does not prove NASA never conducted an experiment.'}
              </div>
            </div>
          </div>

          {/* Footer Navigation Action */}
          <div className="pt-2 border-t border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
            <span className="text-slate-500 text-[10.5px]">
              Click any individual cell in the matrix above to inspect specific oxygen column values.
            </span>
            <button
              type="button"
              onClick={handleAnalyzeInExplorer}
              className="px-3.5 py-1.5 rounded-lg bg-orange-50 hover:bg-orange-100 text-orange-800 border border-orange-200 text-[11px] font-mono transition-colors cursor-pointer"
            >
              Analyze Lunar Regime in Condition Explorer →
            </button>
          </div>
        </div>
      )}

      {/* Case 2: Interactive Cell Inspector Panel */}
      {selectedCellData && (
        <div className="p-4 sm:p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4 animate-in fade-in duration-200">
          {/* Active finding context banner if finding is present */}
          {activeFinding && (
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-orange-50 border border-orange-200 text-xs font-mono">
              <div className="flex items-center gap-2 truncate">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 shrink-0" />
                <span className="text-orange-700 font-semibold shrink-0">{activeFinding.finding_id}:</span>
                <span className="text-slate-800 truncate">{activeFinding.title}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-2">
                <button
                  type="button"
                  onClick={() => setSelectedCellKey(null)}
                  className="text-[10.5px] font-mono text-orange-600 hover:text-orange-700 underline cursor-pointer"
                >
                  ← View Finding Summary Panel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setActiveFinding(null);
                    setHighlightedRowId(null);
                    setHighlightedColId(null);
                  }}
                  className="text-[10.5px] font-mono text-slate-400 hover:text-slate-600 px-1"
                  title="Dismiss finding context"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
            <div>
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${getStatusBadge(selectedCellData.status).dot}`} />
                <h3 className="text-sm font-semibold text-slate-900 tracking-tight">
                  Regime Inspection: {selectedRowLabel} × {selectedColLabel}
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Status:{' '}
                <span className="font-medium text-slate-800">
                  {selectedCellData.gap_status || getStatusBadge(selectedCellData.status).label}
                </span>
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-md bg-white border border-slate-200 text-[11px] font-mono text-slate-700">
                {selectedCellData.experiment_count ?? selectedCellData.usable_records ?? 0} Usable Runs
              </span>
              <button
                type="button"
                onClick={handleAnalyzeInExplorer}
                className="px-3 py-1 rounded-md bg-orange-50 hover:bg-orange-100 text-orange-800 border border-orange-200 text-[11px] font-mono transition-colors cursor-pointer"
              >
                Analyze in Explorer →
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="md:col-span-2 space-y-2">
              <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block">
                Scientific Overview & Physical Context
              </span>
              <p className="text-slate-700 leading-relaxed">
                {selectedCellData.description ||
                  (selectedCellData.status === 'gap'
                    ? 'No empirical combustion records exist in FLAME for this regime. Unrepresented in FLAME does not mean NASA never conducted an experiment.'
                    : `Empirically verified in FLAME with ${selectedCellData.experiment_count || 0} usable microgravity test runs.`)}
              </p>

              {selectedCellData.scientific_disclaimer && (
                <p className="text-[11px] text-slate-500 font-mono italic">
                  Note: {selectedCellData.scientific_disclaimer}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block">
                Supporting Experiment IDs
              </span>
              {selectedCellData.experiment_ids && selectedCellData.experiment_ids.length > 0 ? (
                <div className="max-h-28 overflow-y-auto pr-1 space-y-1">
                  {selectedCellData.experiment_ids.map((id) => (
                    <div
                      key={id}
                      className="px-2 py-0.5 rounded bg-white border border-slate-200 text-[10.5px] font-mono text-sky-800"
                    >
                      {id}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-[11px] font-mono text-slate-400 italic">
                  No indexed experiment runs for this regime.
                </div>
              )}
            </div>
          </div>

          {selectedCellData.status === 'gap' && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="space-y-0.5">
                <span className="font-semibold block text-rose-900">
                  Empirical Research Gap
                </span>
                <span className="text-slate-600 text-[11px]">
                  FLAME's indexed collection contains 0 steady-state combustion runs for this parameter cell.
                </span>
              </div>
              {onSelectCellGap && (
                <button
                  type="button"
                  onClick={() =>
                    onSelectCellGap(
                      activeFinding?.finding_id || selectedCellData.related_finding_id || 'GAP-COV-GRAV-PARTIAL-LUNAR'
                    )
                  }
                  className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-medium text-xs whitespace-nowrap transition-colors cursor-pointer border border-rose-600 shadow-xs"
                >
                  View Related Gap Finding →
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
