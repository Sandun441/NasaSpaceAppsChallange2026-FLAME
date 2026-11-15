import React, { useState, useEffect, useMemo } from 'react';
import { flameApi } from '../../../services/flameApi';

const GAP_TYPE_OPTIONS = [
  { id: 'all', label: 'All Types' },
  { id: 'coverage_gap', label: 'Coverage Gaps' },
  { id: 'sparse_evidence', label: 'Sparse Evidence' },
  { id: 'measurement_gap', label: 'Measurement Gaps' },
  { id: 'metadata_gap', label: 'Metadata Gaps' },
  { id: 'ingestion_opportunity', label: 'Ingestion Opps' },
  { id: 'comparison_gap', label: 'Comparison Gaps' },
];

const CONFIDENCE_LEVEL_COLORS = {
  HIGH: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  MEDIUM: 'bg-amber-50 text-amber-800 border-amber-200',
  LOW: 'bg-slate-100 text-slate-700 border-slate-200',
};

const GAP_TYPE_BADGES = {
  coverage_gap: { bg: 'bg-rose-50 text-rose-800 border-rose-200', label: 'Coverage Gap' },
  sparse_evidence: { bg: 'bg-amber-50 text-amber-800 border-amber-200', label: 'Sparse Evidence' },
  measurement_gap: { bg: 'bg-orange-50 text-orange-800 border-orange-200', label: 'Measurement Gap' },
  metadata_gap: { bg: 'bg-purple-50 text-purple-800 border-purple-200', label: 'Metadata Gap' },
  ingestion_opportunity: { bg: 'bg-sky-50 text-sky-800 border-sky-200', label: 'Ingestion Opp' },
  comparison_gap: { bg: 'bg-indigo-50 text-indigo-800 border-indigo-200', label: 'Comparison Gap' },
};

export function IdentifiedGaps({
  onOpenGapDetail,
  activeGapId,
  selectedGapTypeFilter = 'all',
  onSelectGapTypeFilter,
  onSelectTab,
}) {
  const [findings, setFindings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [minPriority, setMinPriority] = useState(0.0);
  const [confidenceFilter, setConfidenceFilter] = useState('all');
  const [sortBy, setSortBy] = useState('priority_desc');

  useEffect(() => {
    let isMounted = true;
    const fetchFindings = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await flameApi.getGapFindings({ limit: 100 });
        if (isMounted) {
          if (res?.status === 'success' && Array.isArray(res.findings)) {
            setFindings(res.findings);
          } else {
            setFindings([]);
          }
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to fetch research gap findings:', err);
          setError(err.message || 'Failed to load research gap findings from backend.');
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchFindings();
    return () => {
      isMounted = false;
    };
  }, []);

  // Filtered and sorted findings list
  const filteredFindings = useMemo(() => {
    return findings
      .filter((f) => {
        // Gap Type
        if (selectedGapTypeFilter && selectedGapTypeFilter !== 'all') {
          if (f.gap_type !== selectedGapTypeFilter) return false;
        }

        // Min Priority
        if (minPriority > 0.0) {
          if ((f.priority_score ?? 0) < minPriority) return false;
        }

        // Evidence Confidence
        if (confidenceFilter !== 'all') {
          const conf = f.evidence_confidence?.level || 'LOW';
          if (conf !== confidenceFilter) return false;
        }

        // Free Text Search
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchTitle = (f.title || '').toLowerCase().includes(q);
          const matchId = (f.finding_id || '').toLowerCase().includes(q);
          const matchExpl = (f.explanation || '').toLowerCase().includes(q);
          const matchType = (f.gap_type || '').toLowerCase().includes(q);
          const dims = Object.values(f.scientific_dimensions || {}).filter(Boolean).join(' ').toLowerCase();
          const matchDims = dims.includes(q);

          if (!matchTitle && !matchId && !matchExpl && !matchType && !matchDims) {
            return false;
          }
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'priority_desc') {
          return (b.priority_score ?? 0) - (a.priority_score ?? 0);
        }
        if (sortBy === 'priority_asc') {
          return (a.priority_score ?? 0) - (b.priority_score ?? 0);
        }
        if (sortBy === 'confidence_desc') {
          const order = { HIGH: 3, MEDIUM: 2, LOW: 1 };
          const cA = order[a.evidence_confidence?.level] || 0;
          const cB = order[b.evidence_confidence?.level] || 0;
          return cB - cA;
        }
        if (sortBy === 'title_asc') {
          return (a.title || '').localeCompare(b.title || '');
        }
        return 0;
      });
  }, [findings, selectedGapTypeFilter, minPriority, confidenceFilter, searchQuery, sortBy]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setMinPriority(0.0);
    setConfidenceFilter('all');
    setSortBy('priority_desc');
    if (onSelectGapTypeFilter) onSelectGapTypeFilter('all');
  };

  return (
    <div className="space-y-5">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Identified Research Gap Findings</span>
            <span className="text-[10px] font-mono text-rose-800 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded">
              21 Systematic Findings
            </span>
          </h2>
          <p className="text-xs text-slate-500">
            Scientifically grounded gaps, sparse evidence areas, unmonitored parameters, and immediate ingestion opportunities.
          </p>
        </div>

        <button
          onClick={handleResetFilters}
          className="text-[11px] font-mono text-slate-500 hover:text-slate-900 transition-colors self-start sm:self-auto cursor-pointer"
        >
          Reset Filters ↺
        </button>
      </div>

      {/* Filter and Search Bar Controls */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search gap findings by ID, title, keyword (e.g. 'lunar', 'droplet', 'carbon monoxide')..."
            className="w-full bg-white border border-slate-200 rounded-lg px-3.5 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 text-xs cursor-pointer"
            >
              ✕
            </button>
          )}
        </div>

        {/* Gap Type Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-200">
          <span className="text-[10.5px] font-mono text-slate-500 mr-1 uppercase">Gap Type:</span>
          {GAP_TYPE_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onSelectGapTypeFilter && onSelectGapTypeFilter(opt.id)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-mono transition-colors cursor-pointer ${
                selectedGapTypeFilter === opt.id
                  ? 'bg-orange-50 text-orange-700 border border-orange-300 font-semibold'
                  : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Secondary Filter Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-200 text-xs font-mono">
          {/* Priority Threshold */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">Min Heuristic Priority:</label>
            <select
              value={minPriority}
              onChange={(e) => setMinPriority(parseFloat(e.target.value))}
              className="w-full bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-800 focus:outline-none cursor-pointer"
            >
              <option value="0.0">All Priority Tiers (≥ 0.0)</option>
              <option value="4.0">Medium & High (≥ 4.0)</option>
              <option value="7.0">High Priority Only (≥ 7.0)</option>
            </select>
          </div>

          {/* Evidence Confidence Filter */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">Evidence Confidence:</label>
            <select
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-800 focus:outline-none cursor-pointer"
            >
              <option value="all">All Confidence Levels</option>
              <option value="HIGH">HIGH Confidence (Database Certainty)</option>
              <option value="MEDIUM">MEDIUM Confidence</option>
              <option value="LOW">LOW Confidence</option>
            </select>
          </div>

          {/* Sort By */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-500 uppercase block">Sort Order:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-800 focus:outline-none cursor-pointer"
            >
              <option value="priority_desc">Priority: High to Low</option>
              <option value="priority_asc">Priority: Low to High</option>
              <option value="confidence_desc">Evidence Confidence: High to Low</option>
              <option value="title_asc">Title: A to Z</option>
            </select>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 px-1">
        <span>
          Showing <strong className="text-slate-900 font-bold">{filteredFindings.length}</strong> of{' '}
          {findings.length} findings
        </span>
        <span className="text-slate-400 text-[10px]">
          * Priority scores are transparent engineering heuristics, not physical laws
        </span>
      </div>

      {/* Findings Cards List */}
      {isLoading ? (
        <div className="p-12 text-center space-y-3 bg-slate-50 rounded-xl border border-slate-200">
          <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <div className="text-xs font-mono text-slate-500">Loading research gap findings...</div>
        </div>
      ) : error ? (
        <div className="p-8 text-center text-xs text-rose-600 font-mono bg-rose-50 rounded-xl border border-rose-200">
          Error: {error}
        </div>
      ) : filteredFindings.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredFindings.map((finding) => {
            const isSelected = activeGapId === finding.finding_id;
            const typeMeta = GAP_TYPE_BADGES[finding.gap_type] || {
              bg: 'bg-slate-100 text-slate-700 border-slate-200',
              label: finding.gap_type,
            };
            const priority = finding.priority_score ?? 0;
            const priorityBadgeColor =
              priority >= 7.0
                ? 'bg-rose-50 text-rose-800 border-rose-200'
                : priority >= 4.0
                ? 'bg-amber-50 text-amber-800 border-amber-200'
                : 'bg-sky-50 text-sky-800 border-sky-200';

            const confLevel = finding.evidence_confidence?.level || 'HIGH';
            const confColor = CONFIDENCE_LEVEL_COLORS[confLevel] || CONFIDENCE_LEVEL_COLORS.LOW;

            const dimensions = Object.entries(finding.scientific_dimensions || {})
              .filter(([_, v]) => Boolean(v))
              .map(([k, v]) => `${k}: ${v}`);

            return (
              <div
                key={finding.finding_id}
                onClick={() => onOpenGapDetail && onOpenGapDetail(finding)}
                className={`p-5 rounded-xl border bg-white hover:bg-slate-50/80 transition-all duration-200 space-y-3.5 flex flex-col justify-between cursor-pointer group shadow-xs ${
                  isSelected
                    ? 'border-orange-500 ring-1 ring-orange-500 shadow-md'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="space-y-2.5">
                  {/* Card Header Pills */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
                        {finding.finding_id}
                      </span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${typeMeta.bg}`}>
                        {typeMeta.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${priorityBadgeColor}`}
                        title="Heuristic Priority Score (0-10 scale)"
                      >
                        Priority {priority.toFixed(1)}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${confColor}`}
                        title="Evidence Confidence: factual certainty in database absence or records"
                      >
                        {confLevel}
                      </span>
                    </div>
                  </div>

                  {/* Title */}
                  <h3 className="text-sm font-semibold text-slate-900 group-hover:text-orange-600 transition-colors leading-snug">
                    {finding.title}
                  </h3>

                  {/* Explanation */}
                  <p className="text-xs text-slate-600 leading-relaxed line-clamp-3">
                    {finding.explanation}
                  </p>

                  {/* Dimension Pills */}
                  {dimensions.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 text-[10px] font-mono pt-1">
                      {dimensions.map((dim, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200"
                        >
                          {dim}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Footer Denominator and Action */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-400 text-[10px] truncate max-w-[170px]" title={finding.denominator_and_scope}>
                    {finding.denominator_and_scope || 'FLAME indexed repository'}
                  </span>
                  <div className="flex items-center gap-2">
                    {onSelectTab && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectTab('home', {
                            initialFindingId: finding.finding_id,
                            initialFindingTitle: finding.title,
                            initialFinding: finding,
                            initialQuery: `Investigate scientific evidence and coverage status for research gap ${finding.finding_id}: ${finding.title}`,
                          });
                        }}
                        className="px-2 py-0.5 rounded bg-orange-50 hover:bg-orange-100 text-orange-800 border border-orange-200 text-[10.5px] transition-colors cursor-pointer flex items-center gap-1"
                        title="Directly investigate this research gap with Grounded Scientific AI"
                      >
                        <span>AI Investigate</span>
                        <span>✨</span>
                      </button>
                    )}
                    <span className="text-orange-600 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                      <span>Details</span>
                      <span>→</span>
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-8 rounded-xl border border-dashed border-slate-200 bg-slate-50 text-center space-y-2">
          <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400 text-sm">
            ∅
          </div>
          <div className="text-sm font-medium text-slate-800">No Matching Findings</div>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            No research gap findings match your current filter and search criteria. Try resetting filters.
          </p>
          <button
            onClick={handleResetFilters}
            className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-mono transition-colors cursor-pointer mt-2"
          >
            Reset Filters ↺
          </button>
        </div>
      )}
    </div>
  );
}
