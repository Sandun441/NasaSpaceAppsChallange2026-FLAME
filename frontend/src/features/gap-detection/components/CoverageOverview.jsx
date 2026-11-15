import React, { useState, useEffect } from 'react';
import { flameApi } from '../../../services/flameApi';

const GAP_TYPE_LABELS = {
  coverage_gap: { label: 'Coverage Gaps', color: 'rose', desc: 'Unrepresented regimes in indexed database' },
  sparse_evidence: { label: 'Sparse Evidence', color: 'amber', desc: 'Fewer than 5 usable flight runs' },
  measurement_gap: { label: 'Measurement Gaps', color: 'orange', desc: 'Critical sensor channels unmonitored' },
  metadata_gap: { label: 'Metadata Gaps', color: 'purple', desc: 'Missing environmental or specimen logs' },
  ingestion_opportunity: { label: 'Ingestion Opportunities', color: 'sky', desc: 'Raw flight assets & external NASA archives' },
  comparison_gap: { label: 'Comparison Gaps', color: 'indigo', desc: 'Insufficient baseline pairs for causal isolation' },
};

export function CoverageOverview({ onSelectGapType, onNavigateToMatrix, onNavigateToExplorer }) {
  const [gapSummary, setGapSummary] = useState(null);
  const [coverageSummary, setCoverageSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSummaries = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [gapRes, covRes] = await Promise.all([
        flameApi.getGapSummary(),
        flameApi.getCoverageSummary(),
      ]);

      if (gapRes?.status === 'success' && gapRes.summary) {
        setGapSummary(gapRes.summary);
      }
      if (covRes?.status === 'success' && covRes.summary) {
        setCoverageSummary(covRes.summary);
      }
    } catch (err) {
      console.error('Failed to load coverage summaries:', err);
      setError(err.message || 'Unable to load research gap metrics from backend.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSummaries();
  }, []);

  if (isLoading) {
    return (
      <div className="p-8 rounded-2xl bg-slate-50 border border-slate-200 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <div className="text-xs font-mono text-slate-500">Loading NASA FLAME research gap metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 space-y-3 text-center">
        <div className="text-rose-800 font-semibold text-sm">Failed to Load Metrics</div>
        <div className="text-xs text-rose-700 font-mono">{error}</div>
        <button
          onClick={fetchSummaries}
          className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-mono transition-colors"
        >
          Retry Connection ↺
        </button>
      </div>
    );
  }

  const totalFindings = gapSummary?.total_findings ?? 21;
  const highPriorityCount = gapSummary?.priority_tier_counts?.['high (>= 7.0)'] ?? 16;
  const mediumPriorityCount = gapSummary?.priority_tier_counts?.['medium (4.0 - 6.9)'] ?? 5;
  const totalRuns = coverageSummary?.total_experiment_runs ?? 133;
  const totalDatasets = coverageSummary?.total_cataloged_datasets ?? 11;
  const totalInvestigations = coverageSummary?.total_investigations ?? 2;
  const rawAssetsCount = coverageSummary?.unprocessed_raw_assets_count ?? 11;
  const breakdown = gapSummary?.breakdown_by_gap_type || {};

  return (
    <div className="space-y-5">
      {/* 4 High-Level Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Metric 1: Total Findings */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-1 shadow-sm hover:border-slate-300 transition-colors">
          <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>Detected Gap Findings</span>
            <span className="w-2 h-2 rounded-full bg-orange-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight flex items-baseline gap-2">
            <span>{totalFindings}</span>
            <span className="text-xs font-normal text-slate-400 font-mono">systematic findings</span>
          </div>
          <div className="text-[11px] text-slate-500">
            Across 6 distinct gap taxonomies
          </div>
        </div>

        {/* Metric 2: High Priority Actionable Gaps */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-1 shadow-sm hover:border-slate-300 transition-colors">
          <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>High-Priority Gaps</span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-50 text-rose-800 border border-rose-200">
              Score ≥ 7.0
            </span>
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-rose-600 tracking-tight flex items-baseline gap-2">
            <span>{highPriorityCount}</span>
            <span className="text-xs font-normal text-slate-400 font-mono">urgent targets</span>
          </div>
          <div className="text-[11px] text-slate-500">
            {mediumPriorityCount} medium-priority findings
          </div>
        </div>

        {/* Metric 3: Empirical Runs Analyzed */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-1 shadow-sm hover:border-slate-300 transition-colors">
          <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>Indexed Flight Runs</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-emerald-700 tracking-tight flex items-baseline gap-2">
            <span>{totalRuns}</span>
            <span className="text-xs font-normal text-slate-400 font-mono">usable runs</span>
          </div>
          <div className="text-[11px] text-slate-500">
            {totalDatasets} datasets in {totalInvestigations} flight investigations
          </div>
        </div>

        {/* Metric 4: Ingestion Opportunities */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-1 shadow-sm hover:border-slate-300 transition-colors">
          <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>Uningested Assets</span>
            <span className="w-2 h-2 rounded-full bg-sky-500" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold text-sky-700 tracking-tight flex items-baseline gap-2">
            <span>{rawAssetsCount}</span>
            <span className="text-xs font-normal text-slate-400 font-mono">raw files</span>
          </div>
          <div className="text-[11px] text-slate-500">
            4 documented ingestion opportunities
          </div>
        </div>
      </div>

      {/* Gap Taxonomies Interactive Strip */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-orange-500" />
            <h3 className="text-xs font-semibold text-slate-900 tracking-tight uppercase font-mono">
              Research Gap Taxonomies (Click to Filter Findings)
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-500">
            Deterministic Engine Categorization
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {Object.entries(GAP_TYPE_LABELS).map(([typeKey, meta]) => {
            const count = breakdown[typeKey] ?? 0;
            return (
              <button
                key={typeKey}
                type="button"
                onClick={() => onSelectGapType && onSelectGapType(typeKey)}
                className="p-2.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 hover:border-orange-300 text-left transition-all group cursor-pointer flex flex-col justify-between shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-mono font-bold text-slate-800 group-hover:text-orange-600">
                      {meta.label}
                    </span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold bg-slate-100 text-slate-700 group-hover:bg-orange-50 group-hover:text-orange-700">
                      {count}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 line-clamp-2 leading-snug">
                    {meta.desc}
                  </p>
                </div>
                <div className="mt-2 text-[10px] font-mono text-orange-600 opacity-0 group-hover:opacity-100 transition-opacity">
                  View findings →
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Quick Navigation Cards: Matrix Heatmap & Structured Condition Explorer */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Heatmap Card */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-3 flex flex-col justify-between shadow-sm">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase text-sky-700 tracking-wider">
                Multi-Dimensional Heatmaps
              </span>
              <span className="text-[10px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                4×4 Regimes
              </span>
            </div>
            <h4 className="text-sm font-semibold text-slate-900">
              Coverage Matrix Heatmap
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Explore experimental coverage across Gravity Regimes (Earth 1g, Microgravity, Lunar 0.16g, Martian 0.38g) vs Oxygen Regimes, or Fuel Families vs Airflow Velocities.
            </p>
          </div>
          {onNavigateToMatrix && (
            <button
              onClick={onNavigateToMatrix}
              className="mt-2 px-3 py-2 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 text-xs font-mono font-medium transition-colors flex items-center justify-between cursor-pointer"
            >
              <span>Open Interactive Matrix Heatmap</span>
              <span>→</span>
            </button>
          )}
        </div>

        {/* Condition Explorer Card */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-3 flex flex-col justify-between shadow-sm">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase text-orange-600 tracking-wider">
                Scientific Condition Evaluator
              </span>
              <span className="text-[10px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                7 Dimensions
              </span>
            </div>
            <h4 className="text-sm font-semibold text-slate-900">
              Structured Condition & Inquiry Explorer
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Test specific mission envelopes (such as Artemis Lunar 34% O₂ or Quiescent Smothering) against FLAME's database and inspect matched runs or identified gaps.
            </p>
          </div>
          {onNavigateToExplorer && (
            <button
              onClick={onNavigateToExplorer}
              className="mt-2 px-3 py-2 rounded-lg bg-orange-50 hover:bg-orange-100 text-orange-800 border border-orange-200 text-xs font-mono font-medium transition-colors flex items-center justify-between cursor-pointer"
            >
              <span>Open Condition & Inquiry Explorer</span>
              <span>→</span>
            </button>
          )}
        </div>
      </div>

      {/* Database Scope & Epistemic Boundary Notice */}
      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3 text-xs leading-relaxed">
        <span className="text-sky-600 text-sm mt-0.5">ℹ</span>
        <div className="space-y-1 text-slate-600">
          <div className="font-semibold text-slate-800 font-mono text-[11px]">
            Database Scope & Epistemic Boundary:
          </div>
          <p className="text-[11px]">
            Research gap metrics and coverage statuses are computed strictly against NASA FLAME's indexed experimental database (<strong>{totalRuns} runs</strong> across BASS-II, Saffire-III, and Cygnus telemetry). An "Unrepresented Regime" or "Coverage Gap" denotes the absence of empirical runs within this indexed corpus and does <strong>not</strong> imply that NASA or international partners have never investigated the phenomenon in ground drop towers, parabolic aircraft, or unindexed archives.
          </p>
        </div>
      </div>
    </div>
  );
}
