import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { flameApi } from '../../services/flameApi';
import { ResearchPromptBar } from '../../components/common/ResearchPromptBar';
import { PromptEarthResultsCard } from './components/PromptEarthResultsCard';
import { EarthOverviewHeader } from './components/EarthOverviewHeader';
import { EarthCategoryExplorer } from './components/EarthCategoryExplorer';
import { EarthFilterBar } from './components/EarthFilterBar';
import { EarthEvidenceCard } from './components/EarthEvidenceCard';
import { EarthEvidenceTable } from './components/EarthEvidenceTable';
import { EarthEvidenceDetailWorkspace } from './components/EarthEvidenceDetailWorkspace';
import { ResearchConnectionBridge } from './components/ResearchConnectionBridge';
import { EarthSafeguardsRubricModal } from './components/EarthSafeguardsRubricModal';
import { SparklesIcon } from './components/EarthIcons';

export function EarthApplications({ onSelectTab, initialContext }) {
  // Navigation Section Sub-Tab
  const [activeSection, setActiveSection] = useState('explorer'); // 'explorer' | 'bridge'

  // Backend Data State
  const [overview, setOverview] = useState(null);
  const [categories, setCategories] = useState([]);
  const [evidenceList, setEvidenceList] = useState([]);
  const [totalCount, setTotalCount] = useState(11);
  const [promptResult, setPromptResult] = useState(null);
  const [showManualExplorer, setShowManualExplorer] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filter & Search State
  const [selectedCategory, setSelectedCategory] = useState(
    () => initialContext?.category_id || initialContext?.category || 'all'
  );
  const [selectedInvestigation, setSelectedInvestigation] = useState(
    () => initialContext?.investigation_id || initialContext?.investigation || 'all'
  );
  const [selectedClassification, setSelectedClassification] = useState(
    () => initialContext?.classification || 'all'
  );
  const [selectedProvenance, setSelectedProvenance] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // View Mode & Pagination
  const [viewMode, setViewMode] = useState('cards'); // 'cards' | 'table'
  const [selectedEvidenceId, setSelectedEvidenceId] = useState(
    () => initialContext?.evidence_id || initialContext?.finding_id || null
  );

  // Safeguards Modal
  const [isSafeguardsModalOpen, setIsSafeguardsModalOpen] = useState(false);

  // Monotonic request counter to prevent stale async responses
  const reqSeqRef = useRef(0);

  // 1. Fetch Overview & Categories on Mount
  useEffect(() => {
    let isMounted = true;

    Promise.all([
      flameApi.getEarthApplicationsOverview().catch((err) => {
        console.error('Failed to load overview:', err);
        return null;
      }),
      flameApi.getEarthApplicationCategories().catch((err) => {
        console.error('Failed to load categories:', err);
        return null;
      }),
    ]).then(([overviewRes, categoriesRes]) => {
      if (!isMounted) return;
      if (overviewRes?.overview) {
        setOverview(overviewRes.overview);
      }
      if (categoriesRes?.categories) {
        setCategories(categoriesRes.categories);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Fetch Evidence Records on Filter Change
  const fetchEvidence = useCallback(async () => {
    const currentSeq = ++reqSeqRef.current;
    setIsLoading(true);
    setError(null);

    const params = {
      limit: 50,
      offset: 0,
    };

    if (selectedCategory !== 'all') {
      params.category = selectedCategory;
    }
    if (selectedInvestigation !== 'all') {
      params.investigation_id = selectedInvestigation;
    }
    if (selectedClassification !== 'all') {
      params.classification = selectedClassification;
    }
    if (selectedProvenance !== 'all') {
      params.provenance_status = selectedProvenance;
    }

    try {
      const res = await flameApi.getEarthApplications(params);
      if (currentSeq !== reqSeqRef.current) return;

      if (res && res.evidence) {
        setEvidenceList(res.evidence);
        setTotalCount(res.total_count ?? 11);

        // Auto-select first item if no item selected or previous item not in filtered results
        if (res.evidence.length > 0) {
          setSelectedEvidenceId((prev) => {
            const exists = res.evidence.some((e) => e.id === prev);
            return exists ? prev : res.evidence[0].id;
          });
        } else {
          setSelectedEvidenceId(null);
        }
      }
    } catch (err) {
      if (currentSeq !== reqSeqRef.current) return;
      console.error('Failed to query Earth Applications evidence:', err);
      setError(err.message || 'Failed to load verified Earth application evidence.');
    } finally {
      if (currentSeq === reqSeqRef.current) {
        setIsLoading(false);
      }
    }
  }, [selectedCategory, selectedInvestigation, selectedClassification, selectedProvenance]);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence]);

  // 3. Prompt Response Handler from Shared ResearchPromptBar
  const handlePromptResult = useCallback((res) => {
    if (!res) return;
    reqSeqRef.current++;
    setPromptResult(res);

    if (res.specialist_data?.primary_category_id) {
      setSelectedCategory(res.specialist_data.primary_category_id);
    }
    if (res.specialist_data?.primary_evidence_id) {
      setSelectedEvidenceId(res.specialist_data.primary_evidence_id);
    }
  }, []);

  // 4. Client-side search filtering across title, finding, and relevance
  const displayedEvidence = useMemo(() => {
    if (!searchQuery.trim()) return evidenceList;
    const q = searchQuery.toLowerCase().trim();
    return evidenceList.filter((e) => {
      const titleMatch = e.title && e.title.toLowerCase().includes(q);
      const findingMatch = e.scientific_finding && e.scientific_finding.toLowerCase().includes(q);
      const relMatch = e.proposed_terrestrial_relevance && e.proposed_terrestrial_relevance.toLowerCase().includes(q);
      const idMatch = e.id && e.id.toLowerCase().includes(q);
      const invMatch = e.investigation_id && e.investigation_id.toLowerCase().includes(q);
      return titleMatch || findingMatch || relMatch || idMatch || invMatch;
    });
  }, [evidenceList, searchQuery]);

  // Active selected evidence object
  const activeEvidence = useMemo(() => {
    return displayedEvidence.find((e) => e.id === selectedEvidenceId) || displayedEvidence[0] || null;
  }, [displayedEvidence, selectedEvidenceId]);

  // Filter Reset Handler
  const handleResetFilters = () => {
    setSelectedCategory('all');
    setSelectedInvestigation('all');
    setSelectedClassification('all');
    setSelectedProvenance('all');
    setSearchQuery('');
  };

  // Switch to Connection Bridge for a specific evidence record
  const handleOpenBridge = (evidenceId) => {
    if (evidenceId) {
      setSelectedEvidenceId(evidenceId);
    }
    setActiveSection('bridge');
  };

  // Cross-Module Deep-Linking Handlers
  const handleOpenVisualizer = (ev) => {
    if (!onSelectTab) return;
    const target = ev || activeEvidence;
    const datasetId =
      target?.investigation_id === 'saffire_iii' ? 'saffire_iii_sample_1' : 'saffire_iii_sample_1';
    onSelectTab('dataset-explorer', {
      dataset_id: datasetId,
      view: 'visualize',
      source: 'earth-applications',
      evidence_id: target?.id,
    });
  };

  const handleOpenModelingExtraction = (ev) => {
    if (!onSelectTab) return;
    const target = ev || activeEvidence;
    onSelectTab('modeling-extraction', {
      dataset_id: 'bass_ii_experiments',
      objective: `Explore BASS-II data connected to Earth Applications finding ${target?.id || ''}: ${target?.title || ''}`,
      source: 'earth-applications',
      evidence_id: target?.id,
    });
  };

  const handleOpenGapMatrix = (ev) => {
    if (!onSelectTab) return;
    onSelectTab('gap-detection', {
      target_sub_tab: 'matrix',
      source: 'earth-applications',
      evidence_id: (ev || activeEvidence)?.id,
    });
  };

  const handleAskAssistant = (ev) => {
    if (!onSelectTab) return;
    const target = ev || activeEvidence;
    onSelectTab('home', {
      source: 'earth-applications',
      evidence_id: target?.id,
      category_id: target?.category_id,
      investigation_id: target?.investigation_id,
      title: target?.title,
      question: `How does NASA ${target?.investigation_name || target?.investigation_id} evidence [${target?.id}] inform terrestrial combustion research, and what are the physical gravity transfer limitations?`,
    });
  };

  return (
    <div className="max-w-6xl w-full mx-auto space-y-6 py-4 sm:py-6 animate-in fade-in duration-300">
      {/* 1. Overview Header */}
      <EarthOverviewHeader
        overview={overview}
        onOpenSafeguardsModal={() => setIsSafeguardsModalOpen(true)}
      />

      {/* Shared ResearchPromptBar: Integrated Prompt Experience */}
      <ResearchPromptBar
        initialWorkspace="earth_applications"
        handoffContext={initialContext}
        renderInlineResults={false}
        onResult={handlePromptResult}
        onNavigate={(tabId, payload) => {
          if (tabId === 'earth_applications') {
            if (payload?.evidence_id) {
              handleOpenBridge(payload.evidence_id);
            } else if (payload?.category_id) {
              setSelectedCategory(payload.category_id);
              setActiveSection('explorer');
            }
          } else if (onSelectTab) {
            onSelectTab(tabId, payload);
          }
        }}
      />

      {/* Structured Prompt Response Card (Visual-First F5 Layout) */}
      {promptResult && (
        <PromptEarthResultsCard
          result={promptResult}
          onReset={() => setPromptResult(null)}
          onNavigate={onSelectTab}
          onSelectCategory={(catId) => {
            setSelectedCategory(catId);
            setActiveSection('explorer');
          }}
          onSelectEvidence={(evId) => {
            setSelectedEvidenceId(evId);
            setActiveSection('explorer');
          }}
          onOpenBridge={handleOpenBridge}
        />
      )}

      {/* 2. Top View Switcher (Evidence Explorer vs Connection Bridge) */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveSection('explorer')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeSection === 'explorer'
                ? 'bg-orange-50 text-orange-700 border border-orange-200 shadow-xs'
                : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
            }`}
          >
            <span>Verified Evidence Explorer</span>
            <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-700">
              {displayedEvidence.length}
            </span>
          </button>

          <button
            onClick={() => setActiveSection('bridge')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              activeSection === 'bridge'
                ? 'bg-orange-50 text-orange-700 border border-orange-200 shadow-xs'
                : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200'
            }`}
          >
            <SparklesIcon className="w-3.5 h-3.5 text-orange-600" />
            <span>Physical Connection Bridge</span>
            <span className="text-[10px] font-mono px-1.5 rounded bg-orange-50 text-orange-700 border border-orange-200">
              5-Step Chain
            </span>
          </button>
        </div>

        {/* Dynamic Epistemic Badges */}
        <div className="hidden sm:flex items-center gap-2 text-[10px] font-mono text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            10 Supported
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            1 Exploratory
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            0 Documented
          </span>
        </div>
      </div>

      {/* 3. Section A: Evidence Explorer View */}
      {activeSection === 'explorer' && (
        <div className="space-y-6">
          {/* Collapsible Manual Filters Header */}
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900">
              Manual Category Explorer & Filter Suite
            </h3>
            <button
              onClick={() => setShowManualExplorer((prev) => !prev)}
              className="text-xs font-mono text-orange-600 hover:text-orange-700 flex items-center gap-1 cursor-pointer"
            >
              <span>{showManualExplorer ? 'Hide Explorer' : 'Show Explorer'}</span>
              <span>{showManualExplorer ? '▲' : '▼'}</span>
            </button>
          </div>

          {showManualExplorer && (
            <div className="space-y-6 animate-in fade-in duration-200">
              {/* Interactive 7 Category Explorer */}
              <EarthCategoryExplorer
                categories={categories}
                activeCategory={selectedCategory}
                onSelectCategory={setSelectedCategory}
                totalRecords={totalCount}
              />

              {/* Filter & Search Bar */}
              <EarthFilterBar
                categories={categories}
                selectedCategory={selectedCategory}
                onSelectCategory={setSelectedCategory}
                selectedInvestigation={selectedInvestigation}
                onSelectInvestigation={setSelectedInvestigation}
                selectedClassification={selectedClassification}
                onSelectClassification={setSelectedClassification}
                selectedProvenance={selectedProvenance}
                onSelectProvenance={setSelectedProvenance}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                viewMode={viewMode}
                onToggleViewMode={setViewMode}
                filteredCount={displayedEvidence.length}
                totalCount={totalCount}
                onResetFilters={handleResetFilters}
              />
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={fetchEvidence}
                className="px-2.5 py-1 rounded bg-rose-600 hover:bg-rose-700 text-white font-mono text-[10px]"
              >
                Retry
              </button>
            </div>
          )}

          {/* Loading Skeleton */}
          {isLoading && (
            <div className="p-12 text-center text-xs font-mono text-slate-500 space-y-2">
              <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p>Querying verified Earth application findings from NASA FLAME backend...</p>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && displayedEvidence.length === 0 && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm space-y-3">
              <p className="text-sm font-semibold text-slate-900">No evidence records matched your active filters</p>
              <p className="text-xs text-slate-600 font-mono">
                Try selecting a different domain or reset filters to view all 11 verified findings.
              </p>
              <button
                onClick={handleResetFilters}
                className="px-4 py-2 rounded-xl bg-slate-100 text-slate-800 text-xs font-mono font-medium hover:bg-slate-200 border border-slate-200 transition-colors cursor-pointer"
              >
                Reset All Filters
              </button>
            </div>
          )}

          {/* Evidence Grid / Table View */}
          {!isLoading && displayedEvidence.length > 0 && (
            <>
              {viewMode === 'cards' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                  {displayedEvidence.map((ev) => (
                    <EarthEvidenceCard
                      key={ev.id}
                      evidence={ev}
                      isSelected={selectedEvidenceId === ev.id}
                      onSelect={() => setSelectedEvidenceId(ev.id)}
                      onOpenVisualizer={() => handleOpenVisualizer(ev)}
                      onOpenModelingExtraction={() => handleOpenModelingExtraction(ev)}
                      onOpenGapMatrix={() => handleOpenGapMatrix(ev)}
                      onAskAssistant={() => handleAskAssistant(ev)}
                    />
                  ))}
                </div>
              ) : (
                <EarthEvidenceTable
                  evidenceList={displayedEvidence}
                  selectedEvidenceId={selectedEvidenceId}
                  onSelectEvidence={(ev) => setSelectedEvidenceId(ev.id)}
                  onOpenVisualizer={handleOpenVisualizer}
                  onOpenModelingExtraction={handleOpenModelingExtraction}
                />
              )}

              {/* Scientific Detail Workspace */}
              {activeEvidence && (
                <div className="pt-4">
                  <div className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-orange-500" />
                    <span>Scientific Detail Inspection Workspace</span>
                  </div>
                  <EarthEvidenceDetailWorkspace
                    evidence={activeEvidence}
                    onOpenVisualizer={() => handleOpenVisualizer(activeEvidence)}
                    onOpenModelingExtraction={() => handleOpenModelingExtraction(activeEvidence)}
                    onOpenGapMatrix={() => handleOpenGapMatrix(activeEvidence)}
                    onAskAssistant={() => handleAskAssistant(activeEvidence)}
                  />
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* 4. Section B: Microgravity to Earth Physical Connection Bridge */}
      {activeSection === 'bridge' && (
        <ResearchConnectionBridge
          evidenceList={evidenceList.length > 0 ? evidenceList : displayedEvidence}
          activeEvidenceId={selectedEvidenceId}
          onSelectEvidenceId={setSelectedEvidenceId}
        />
      )}

      {/* 5. Safeguards & Epistemic Rubrics Modal */}
      <EarthSafeguardsRubricModal
        isOpen={isSafeguardsModalOpen}
        onClose={() => setIsSafeguardsModalOpen(false)}
      />
    </div>
  );
}
