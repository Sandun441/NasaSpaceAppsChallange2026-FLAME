import React, { useState, useEffect } from 'react';
import { flameApi } from '../../../services/flameApi';

const PRESETS = [
  {
    label: 'Artemis Lunar Habitat',
    desc: '0.16g, 34% O₂, 8.2 psia (0.56 atm)',
    filters: {
      gravity: 'partial_lunar',
      oxygen: 'elevated_o2',
      pressure: 'hypobaric',
      fuel_family: 'all',
      fuel_material: '',
      airflow: 'all',
      parameter: 'all',
    },
    query: 'What is the flammability limit under lunar partial gravity in elevated oxygen exploration atmospheres?',
  },
  {
    label: 'Quiescent Smothering Limit',
    desc: '0g, 0 cm/s quiescent ventilation',
    filters: {
      gravity: 'micro',
      oxygen: 'all',
      pressure: 'all',
      fuel_family: 'all',
      fuel_material: '',
      airflow: 'quiescent',
      parameter: 'all',
    },
    query: 'Can a solid fuel flame sustain in microgravity under complete zero-velocity quiescent airflow?',
  },
  {
    label: 'Nomex Fire-Resistant Performance',
    desc: '0g, Nomex vs cotton comparison',
    filters: {
      gravity: 'micro',
      oxygen: 'all',
      pressure: 'all',
      fuel_family: 'solid-flat',
      fuel_material: 'Nomex',
      airflow: 'all',
      parameter: 'all',
    },
    query: 'How many microgravity flame spread runs in FLAME tested Nomex fire-resistant fabric?',
  },
  {
    label: 'Saffire CO Combustion Emissions',
    desc: '0g, elevated O₂, carbon monoxide sensor',
    filters: {
      gravity: 'micro',
      oxygen: 'elevated_o2',
      pressure: 'all',
      fuel_family: 'all',
      fuel_material: '',
      airflow: 'all',
      parameter: 'carbon_monoxide_concentration',
    },
    query: 'Are direct carbon monoxide gas emissions recorded during Saffire-III flight burns?',
  },
  {
    label: 'FLEX Droplet Extinction',
    desc: '0g, liquid alkane droplet fuel',
    filters: {
      gravity: 'micro',
      oxygen: 'all',
      pressure: 'all',
      fuel_family: 'droplet',
      fuel_material: 'n-Heptane',
      airflow: 'all',
      parameter: 'all',
    },
    query: 'Does the FLAME indexed database include liquid droplet combustion extinction limits?',
  },
];

const STATUS_CONFIGS = {
  covered: {
    label: 'Empirical Evidence Available',
    bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    dot: 'bg-emerald-500',
  },
  sparse: {
    label: 'Sparse Evidence (< 5 Runs)',
    bg: 'bg-amber-50 border-amber-200 text-amber-800',
    dot: 'bg-amber-500',
  },
  coverage_gap: {
    label: 'Empirical Coverage Gap',
    bg: 'bg-rose-50 border-rose-200 text-rose-800',
    dot: 'bg-rose-500 animate-pulse',
  },
  unknown_or_inapplicable: {
    label: 'Regime Outside Taxonomy',
    bg: 'bg-purple-50 border-purple-200 text-purple-800',
    dot: 'bg-purple-500',
  },
  unsupported_query: {
    label: 'Free-Text Inquiry (RAG Assistant Recommended)',
    bg: 'bg-sky-50 border-sky-200 text-sky-800',
    dot: 'bg-sky-500',
  },
  not_evaluated: {
    label: 'No Parameters Submitted',
    bg: 'bg-slate-100 border-slate-200 text-slate-500',
    dot: 'bg-slate-400',
  },
};

export function TopicSearch({
  onSelectTab,
  prefilledFilters = null,
  onSelectGap,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    gravity: 'all',
    oxygen: 'all',
    pressure: 'all',
    fuel_family: 'all',
    fuel_material: '',
    airflow: 'all',
    parameter: 'all',
  });

  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);

  // Apply prefilled filters when passed from matrix or modal
  useEffect(() => {
    if (prefilledFilters) {
      setFilters((prev) => ({
        ...prev,
        ...prefilledFilters,
      }));
      // Trigger analysis immediately with prefilled values
      handleExecuteAnalysis(prefilledFilters, searchQuery);
    }
  }, [prefilledFilters]);

  const handleFilterChange = (dim, val) => {
    setFilters((prev) => ({ ...prev, [dim]: val }));
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setFilters({
      gravity: 'all',
      oxygen: 'all',
      pressure: 'all',
      fuel_family: 'all',
      fuel_material: '',
      airflow: 'all',
      parameter: 'all',
    });
    setAnalysisResult(null);
    setAnalysisError(null);
  };

  const handleSelectPreset = (preset) => {
    setSearchQuery(preset.query);
    setFilters(preset.filters);
    handleExecuteAnalysis(preset.filters, preset.query);
  };

  const handleExecuteAnalysis = async (filterState = filters, queryText = searchQuery) => {
    setIsAnalyzing(true);
    setAnalysisError(null);

    const payload = {
      gravity: filterState.gravity !== 'all' ? filterState.gravity : null,
      oxygen_regime: filterState.oxygen !== 'all' ? filterState.oxygen : null,
      pressure_regime: filterState.pressure !== 'all' ? filterState.pressure : null,
      fuel_family: filterState.fuel_family !== 'all' ? filterState.fuel_family : null,
      fuel_material: filterState.fuel_material?.trim() || null,
      airflow_regime: filterState.airflow !== 'all' ? filterState.airflow : null,
      parameter: filterState.parameter !== 'all' ? filterState.parameter : null,
      question: queryText.trim() || null,
    };

    try {
      const res = await flameApi.analyzeResearchGap(payload);
      if (res?.status === 'success' && res.analysis) {
        setAnalysisResult(res.analysis);
      } else {
        setAnalysisResult(res?.analysis || null);
      }
    } catch (err) {
      console.error('Failed to analyze research gap inquiry:', err);
      setAnalysisError(err.message || 'Error communicating with research gap analysis engine.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleExecuteAnalysis();
  };

  const statusMeta =
    STATUS_CONFIGS[analysisResult?.coverage_status] || STATUS_CONFIGS.not_evaluated;

  return (
    <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-5 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Structured Condition & Inquiry Explorer</span>
            <span className="text-[10px] font-mono text-sky-800 bg-sky-50 border border-sky-200 px-2 py-0.5 rounded">
              Deterministic Coverage Evaluator
            </span>
          </h2>
          <p className="text-xs text-slate-500">
            Evaluate exact experimental conditions against FLAME's indexed records, identify matching runs, and detect empirical gaps.
          </p>
        </div>

        <button
          onClick={handleResetFilters}
          className="text-[11px] font-mono text-slate-500 hover:text-slate-900 transition-colors self-start sm:self-auto cursor-pointer"
        >
          Reset All Dimensions ↺
        </button>
      </div>

      {/* Preset Buttons */}
      <div className="space-y-1.5">
        <div className="text-[10.5px] font-mono text-slate-500 uppercase tracking-wider">
          Rapid Exploration Presets (Artemis & PSI Envelopes):
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => handleSelectPreset(preset)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-[11px] font-mono text-slate-700 hover:text-slate-900 border border-slate-200 transition-colors cursor-pointer text-left"
              title={preset.desc}
            >
              <div className="font-semibold text-slate-900">{preset.label}</div>
              <div className="text-[9.5px] text-slate-500">{preset.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Form: Free Text Inquiry + 7 Dimension Filters */}
      <form onSubmit={handleSubmit} className="space-y-4 pt-2 border-t border-slate-200">
        {/* Free Text Input */}
        <div className="space-y-1">
          <label className="text-[10.5px] font-mono uppercase text-slate-500 block">
            Scientific Question or Research Context (Optional Free Text):
          </label>
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. 'How does partial gravity affect flame spread in 34% oxygen?'..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 pr-10"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 text-xs cursor-pointer"
              >
                ✕
              </button>
            )}
          </div>
          <div className="text-[10px] text-slate-500 font-mono">
            * Note: Free-text natural language questions are synthesized by the Grounded RAG Assistant. To evaluate empirical coverage, set structured parameters below.
          </div>
        </div>

        {/* 7 Dimensions Dropdown Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 text-xs font-mono pt-1">
          {/* 1. Gravity */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">1. Gravity</label>
            <select
              value={filters.gravity}
              onChange={(e) => handleFilterChange('gravity', e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-slate-800 focus:outline-none cursor-pointer text-[11px]"
            >
              <option value="all">All Gravity</option>
              <option value="micro">Microgravity (0g)</option>
              <option value="normal">Normal Earth (1g)</option>
              <option value="partial_lunar">Lunar (0.16g)</option>
              <option value="partial_mars">Martian (0.38g)</option>
            </select>
          </div>

          {/* 2. Oxygen Regime */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">2. Oxygen</label>
            <select
              value={filters.oxygen}
              onChange={(e) => handleFilterChange('oxygen', e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-slate-800 focus:outline-none cursor-pointer text-[11px]"
            >
              <option value="all">All O₂</option>
              <option value="low_o2">Hypoxic (&lt; 18.0% O₂)</option>
              <option value="normal_o2">Normal (18.0 – 22.0% O₂)</option>
              <option value="elevated_o2">Elevated (22.0 – 34.0% O₂)</option>
              <option value="high_o2">High (&gt; 34.0% O₂)</option>
            </select>
          </div>

          {/* 3. Pressure */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">3. Pressure</label>
            <select
              value={filters.pressure}
              onChange={(e) => handleFilterChange('pressure', e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-slate-800 focus:outline-none cursor-pointer text-[11px]"
            >
              <option value="all">All Pressures</option>
              <option value="standard">Standard (1.0 atm)</option>
              <option value="hypobaric">Hypobaric (&lt;0.7 atm)</option>
              <option value="hyperbaric">Hyperbaric (&gt;1.0 atm)</option>
            </select>
          </div>

          {/* 4. Fuel Family */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">4. Fuel Family</label>
            <select
              value={filters.fuel_family}
              onChange={(e) => handleFilterChange('fuel_family', e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-slate-800 focus:outline-none cursor-pointer text-[11px]"
            >
              <option value="all">All Families</option>
              <option value="solid-flat">Solid-Flat</option>
              <option value="solid-thick">Solid-Thick</option>
              <option value="droplet">Droplet (Liquid)</option>
              <option value="gaseous">Gaseous</option>
            </select>
          </div>

          {/* 5. Fuel Material */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">5. Fuel Material</label>
            <input
              type="text"
              value={filters.fuel_material}
              onChange={(e) => handleFilterChange('fuel_material', e.target.value)}
              placeholder="e.g. PMMA, Nomex"
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-slate-800 focus:outline-none text-[11px] placeholder:text-slate-400"
            />
          </div>

          {/* 6. Airflow */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">6. Airflow</label>
            <select
              value={filters.airflow}
              onChange={(e) => handleFilterChange('airflow', e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-slate-800 focus:outline-none cursor-pointer text-[11px]"
            >
              <option value="all">All Flow</option>
              <option value="quiescent">Quiescent (0 cm/s)</option>
              <option value="low-flow">Low (&lt;10 cm/s)</option>
              <option value="high-flow">High (&gt;10 cm/s)</option>
            </select>
          </div>

          {/* 7. Parameter */}
          <div className="space-y-1 col-span-2 sm:col-span-1">
            <label className="text-[10px] text-slate-500 uppercase block">7. Parameter (13)</label>
            <select
              value={filters.parameter}
              onChange={(e) => handleFilterChange('parameter', e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-2 py-1.5 text-slate-800 focus:outline-none cursor-pointer text-[11px]"
            >
              <option value="all">All Parameters</option>
              <option value="temperature">Temperature (°C)</option>
              <option value="pressure">Chamber Pressure (kPa)</option>
              <option value="radiant_heat_flux">Radiant Heat Flux (kW/m²)</option>
              <option value="radiometer_amplifier_gain">Radiometer Gain Setting</option>
              <option value="flow_velocity">Flow Velocity (m/s)</option>
              <option value="oxygen_concentration">O₂ Concentration (% vol)</option>
              <option value="carbon_dioxide_concentration">CO₂ Evolution (% vol)</option>
              <option value="carbon_monoxide_concentration">CO Toxic Gas (ppm)</option>
              <option value="smoke_obscuration">Smoke Obscuration (V)</option>
              <option value="flame_spread_rate">Flame Spread Rate (mm/s)</option>
              <option value="extinction_time">Extinction Time (s)</option>
              <option value="fuel_moisture_content">Pre-flight Moisture (% mass)</option>
              <option value="video_frames">Video Acquisition (frames)</option>
            </select>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end pt-2">
          <button
            type="submit"
            disabled={isAnalyzing}
            className="px-5 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-medium text-xs font-mono transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2 cursor-pointer"
          >
            {isAnalyzing ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Evaluating Empirical Coverage...</span>
              </>
            ) : (
              <>
                <span>Evaluate Research Condition</span>
                <span>→</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Analysis Error Message */}
      {analysisError && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs font-mono text-rose-800">
          Analysis Error: {analysisError}
        </div>
      )}

      {/* Analysis Results Display Panel */}
      {analysisResult && (
        <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-4 animate-in fade-in duration-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${statusMeta.dot}`} />
              <span className={`text-xs font-mono px-2.5 py-0.5 rounded border font-semibold ${statusMeta.bg}`}>
                {statusMeta.label}
              </span>
            </div>

            <div className="text-xs font-mono text-slate-500">
              Matched Usable Runs:{' '}
              <strong className="text-slate-900 font-bold">
                {analysisResult.matched_usable_runs_count ?? 0}
              </strong>{' '}
              runs
            </div>
          </div>

          {/* Explanation */}
          <div className="space-y-1.5">
            <div className="text-[10.5px] font-mono uppercase text-slate-500">Scientific Evaluation:</div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {analysisResult.explanation}
            </p>
          </div>

          {/* Special Case: Unsupported Free-Text Query with RAG Assistant Referral */}
          {analysisResult.coverage_status === 'unsupported_query' && (
            <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold text-sky-800 font-mono uppercase">
                <span>ℹ</span> Grounded RAG Assistant Available
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                You submitted a natural-language question without structured parameter filters. For natural-language synthesis, evidence retrieval, and flight record comparisons, please consult the Grounded RAG Assistant.
              </p>
              {onSelectTab && (
                <button
                  type="button"
                  onClick={() => onSelectTab('home')}
                  className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs font-mono transition-colors shadow-sm flex items-center gap-2 cursor-pointer"
                >
                  <span>Ask NASA FLAME Scientific AI Assistant</span>
                  <span>↗</span>
                </button>
              )}
            </div>
          )}

          {/* Matched Experiment Runs List */}
          {analysisResult.matched_experiment_ids && analysisResult.matched_experiment_ids.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-200">
              <div className="text-[10.5px] font-mono uppercase text-slate-500">
                Matched FLAME Experiment Runs ({analysisResult.matched_experiment_ids.length}):
              </div>
              <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto">
                {analysisResult.matched_experiment_ids.map((id) => (
                  <span
                    key={id}
                    className="px-2 py-0.5 rounded bg-white border border-slate-200 text-[10.5px] font-mono text-emerald-800"
                  >
                    {id}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Applicable Gap Findings */}
          {analysisResult.applicable_gap_findings && analysisResult.applicable_gap_findings.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-200">
              <div className="text-[10.5px] font-mono uppercase text-rose-700 font-semibold">
                Applicable Research Gap Findings ({analysisResult.applicable_gap_findings.length}):
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {analysisResult.applicable_gap_findings.map((gapItem) => (
                  <div
                    key={gapItem.finding_id}
                    className="p-3 rounded-lg bg-white border border-slate-200 flex items-center justify-between gap-2 shadow-xs"
                  >
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-mono text-slate-500 block font-semibold">
                        {gapItem.finding_id}
                      </span>
                      <span className="text-xs text-slate-900 font-medium line-clamp-1">
                        {gapItem.title}
                      </span>
                    </div>
                    {onSelectGap && (
                      <button
                        type="button"
                        onClick={() => onSelectGap(gapItem)}
                        className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-[10.5px] font-mono text-orange-700 transition-colors cursor-pointer whitespace-nowrap"
                      >
                        Inspect →
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Scientific Disclaimer */}
          <div className="text-[10.5px] font-mono text-slate-500 pt-2 border-t border-slate-200">
            <strong>Scope Notice:</strong>{' '}
            {analysisResult.scientific_disclaimer ||
              'Coverage is evaluated strictly against FLAME indexed records (133 runs). Unrepresented in FLAME does not mean NASA never conducted the experiment.'}
          </div>
        </div>
      )}
    </div>
  );
}
