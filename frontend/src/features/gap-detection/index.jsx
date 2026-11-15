import React, { useState, useEffect } from 'react';
import { CoverageOverview } from './components/CoverageOverview';
import { CoverageMatrix } from './components/CoverageMatrix';
import { IdentifiedGaps } from './components/IdentifiedGaps';
import { GapDetailModal } from './components/GapDetailModal';
import { TopicSearch } from './components/TopicSearch';
import { InterpretationSection } from './components/InterpretationSection';
import { PromptGapResultsCard } from './components/PromptGapResultsCard';
import { ResearchPromptBar } from '../../components/common/ResearchPromptBar';

const SUB_TABS = [
  { id: 'overview', label: 'Executive Overview', icon: '📊' },
  { id: 'matrix', label: 'Coverage Heatmap Matrix', icon: '▦' },
  { id: 'findings', label: 'Identified Gap Findings (21)', icon: '🔍' },
  { id: 'explorer', label: 'Condition & Inquiry Explorer', icon: '⚙' },
];

export function ResearchGapDetection({ onSelectTab, initialContext }) {
  const [activeSubTab, setActiveSubTab] = useState(() => {
    if (initialContext?.sub_tab || initialContext?.subTab) {
      return initialContext.sub_tab || initialContext.subTab;
    }
    if (initialContext?.finding_id || initialContext?.initialFindingId) {
      return 'matrix';
    }
    return 'overview';
  });

  const [selectedGap, setSelectedGap] = useState(null);
  const [gapTypeFilter, setGapTypeFilter] = useState('all');
  const [prefilledExplorerFilters, setPrefilledExplorerFilters] = useState(null);

  // Phase F4 Prompt Response & UX Layout State
  const [promptResponse, setPromptResponse] = useState(null);
  const [showManualSuite, setShowManualSuite] = useState(true);

  // Synchronize active sub-tab when incoming navigation state arrives (e.g. from AI Assistant)
  useEffect(() => {
    if (initialContext) {
      if (initialContext.sub_tab || initialContext.subTab) {
        setActiveSubTab(initialContext.sub_tab || initialContext.subTab);
      } else if (initialContext.finding_id || initialContext.initialFindingId) {
        setActiveSubTab('matrix');
      }
    }
  }, [initialContext]);

  // Transition from Overview taxonomy chip to Findings tab
  const handleSelectGapTypeFromOverview = (typeKey) => {
    setGapTypeFilter(typeKey);
    setActiveSubTab('findings');
  };

  // Transition from Matrix cell inspector to Condition Explorer
  const handleAnalyzeRegimeFromMatrix = (regimeFilters) => {
    setPrefilledExplorerFilters({
      gravity: regimeFilters.gravity || 'all',
      oxygen: regimeFilters.oxygen_regime || 'all',
      fuel_family: regimeFilters.fuel_family || 'all',
      airflow: regimeFilters.airflow_regime || 'all',
    });
    setActiveSubTab('explorer');
  };

  // Transition from Modal to Condition Explorer
  const handleAnalyzeFromModal = (dimensions) => {
    setPrefilledExplorerFilters({
      gravity: dimensions.gravity || 'all',
      oxygen: dimensions.oxygen || 'all',
      pressure: dimensions.pressure || 'all',
      fuel_family: dimensions.fuel_family || 'all',
      fuel_material: dimensions.fuel_material || '',
      airflow: dimensions.airflow || 'all',
      parameter: dimensions.parameter || 'all',
    });
    setActiveSubTab('explorer');
  };

  // Cell inspector open modal
  const handleOpenCellGapModal = (gapIdOrFinding) => {
    if (typeof gapIdOrFinding === 'string') {
      setSelectedGap({ finding_id: gapIdOrFinding });
    } else {
      setSelectedGap(gapIdOrFinding);
    }
  };

  // Step 6 State Connection: Synchronize prompt results to gap filters and findings
  const handlePromptResult = (res) => {
    setPromptResponse(res);
    if (res) {
      setShowManualSuite(false);
      const filters = res.specialist_data?.filters || {};
      if (Object.keys(filters).length > 0) {
        setPrefilledExplorerFilters({
          gravity: filters.gravity || 'all',
          oxygen: filters.oxygen_regime || 'all',
          pressure: filters.pressure_regime || 'all',
          fuel_family: filters.fuel_family || 'all',
          fuel_material: filters.fuel_material || '',
          airflow: filters.airflow_regime || 'all',
          parameter: filters.parameter || 'all',
        });
      }
    }
  };

  const handleActionTriggered = (act) => {
    if (act.action === 'navigate_matrix') {
      setActiveSubTab('matrix');
      setShowManualSuite(true);
    } else if (act.action === 'navigate_findings') {
      setActiveSubTab('findings');
      setShowManualSuite(true);
    } else if (act.tab_id && onSelectTab) {
      onSelectTab(act.tab_id);
    }
  };

  return (
    <div className="max-w-6xl w-full mx-auto space-y-6 py-4 sm:py-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="space-y-3 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-xs font-mono text-orange-600 uppercase tracking-wider font-semibold">
            Module 04 • NASA FLAME Analytical Suite
          </span>
          <span className="text-[10px] font-mono text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded ml-auto">
            133 Runs • 21 Findings
          </span>
        </div>

        <div className="space-y-1.5">
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-slate-900">
            Research Gap Detection
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 max-w-3xl leading-relaxed">
            Deterministic coverage analysis and systematic gap detection across NASA microgravity combustion archives (BASS-II, Saffire-III, Cygnus). Identify unrepresented conditions, sparse evidence regimes, missing sensor channels, and immediate ingestion opportunities for Artemis and Mars fire safety.
          </p>
        </div>
      </div>

      {/* 1. Unified Research Prompt Bar (Phase F4 Gap Detection Engine) */}
      <ResearchPromptBar
        initialWorkspace="gap_detection"
        handoffContext={initialContext}
        renderInlineResults={false}
        onResultReceived={handlePromptResult}
        onActionTriggered={handleActionTriggered}
        className="border-slate-200 shadow-sm"
      />

      {/* 2. Step 3 UX Layout: Prompt-Derived Coverage Evaluation & Gap Cards */}
      {promptResponse && (
        <PromptGapResultsCard
          promptResponse={promptResponse}
          onSelectGap={(gap) => setSelectedGap(gap)}
          onNavigateSubTab={(tabId) => {
            setActiveSubTab(tabId);
            setShowManualSuite(true);
          }}
        />
      )}

      {/* 3. Manual Gap Detection Suite Toggle Bar (Collapsible to prevent visual clutter) */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono">
        <span className="text-slate-800 font-semibold flex items-center gap-2">
          <span>🛠 Advanced Research Gap Suite</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-500">
            Overview, Heatmap Matrix, 21 Findings, Condition Explorer
          </span>
        </span>
        <button
          onClick={() => setShowManualSuite(!showManualSuite)}
          className="text-xs text-orange-600 hover:text-orange-700 cursor-pointer font-semibold"
        >
          {showManualSuite ? 'Collapse Manual Suite ▲' : 'Expand Manual Suite ▼'}
        </button>
      </div>

      {/* 4. Existing Manual Suite Components (Preserved Completely) */}
      {showManualSuite && (
        <div className="space-y-5 animate-in fade-in duration-150">
          {/* Sub-Navigation Navigation Bar */}
          <div className="flex flex-wrap items-center gap-2 pt-1 pb-2">
            {SUB_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveSubTab(tab.id)}
                className={`px-3.5 py-2 rounded-xl text-xs font-mono transition-all flex items-center gap-2 cursor-pointer ${
                  activeSubTab === tab.id
                    ? 'bg-orange-50 text-orange-700 border border-orange-300 shadow-xs font-semibold'
                    : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200 hover:border-slate-300'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* View 1: Executive Overview */}
          {activeSubTab === 'overview' && (
            <CoverageOverview
              onSelectGapType={handleSelectGapTypeFromOverview}
              onNavigateToMatrix={() => setActiveSubTab('matrix')}
              onNavigateToExplorer={() => setActiveSubTab('explorer')}
            />
          )}

          {/* View 2: Coverage Heatmap Matrix */}
          {activeSubTab === 'matrix' && (
            <CoverageMatrix
              onSelectCellGap={handleOpenCellGapModal}
              onAnalyzeRegime={handleAnalyzeRegimeFromMatrix}
              activeFindingId={initialContext?.finding_id || initialContext?.initialFindingId}
              initialFinding={initialContext?.finding}
              onOpenFindingModal={(finding) => setSelectedGap(finding)}
            />
          )}

          {/* View 3: Identified Gap Findings */}
          {activeSubTab === 'findings' && (
            <IdentifiedGaps
              onOpenGapDetail={(finding) => setSelectedGap(finding)}
              activeGapId={selectedGap?.finding_id}
              selectedGapTypeFilter={gapTypeFilter}
              onSelectGapTypeFilter={setGapTypeFilter}
              onSelectTab={onSelectTab}
            />
          )}

          {/* View 4: Condition & Inquiry Explorer */}
          {activeSubTab === 'explorer' && (
            <TopicSearch
              onSelectTab={onSelectTab}
              prefilledFilters={prefilledExplorerFilters}
              onSelectGap={(finding) => setSelectedGap(finding)}
            />
          )}

          {/* Epistemic Guidelines & Interpretation Section */}
          <InterpretationSection />
        </div>
      )}

      {/* Modal Inspector */}
      {selectedGap && (
        <GapDetailModal
          gap={selectedGap}
          onClose={() => setSelectedGap(null)}
          onSelectTab={onSelectTab}
          onAnalyzeInExplorer={handleAnalyzeFromModal}
        />
      )}
    </div>
  );
}

export default ResearchGapDetection;
