import React, { useState, useEffect, useCallback, useRef } from 'react';
import { flameApi } from '../../services/flameApi';
import { ResearchPromptBar } from '../../components/common/ResearchPromptBar';
import { PromptEquipmentResultsCard } from './components/PromptEquipmentResultsCard';
import { ObjectiveInputBar } from './components/ObjectiveInputBar';
import { CategorySelector } from './components/CategorySelector';
import { InvestigationsList } from './components/InvestigationsList';
import { VerifiedMeasurementsPanel } from './components/VerifiedMeasurementsPanel';
import { EngineeringInsights } from './components/EngineeringInsights';
import { ResearchGapsSection } from './components/ResearchGapsSection';
import { ActionLauncherBanner } from './components/ActionLauncherBanner';

export function EquipmentResearch({ onSelectTab, initialContext }) {
  // Query & Category State
  const [query, setQuery] = useState(() => initialContext?.objective || '');
  const [activeCategory, setActiveCategory] = useState(() => initialContext?.category || 'detection');

  // Backend Data State
  const [overview, setOverview] = useState(null);
  const [researchPackage, setResearchPackage] = useState(null);
  const [promptResult, setPromptResult] = useState(null);
  const [showManualSuite, setShowManualSuite] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Monotonic request counter to prevent stale async responses
  const reqSeqRef = useRef(0);

  // 1. Fetch Overview on Mount
  useEffect(() => {
    let isMounted = true;
    flameApi
      .getEquipmentOverview()
      .then((res) => {
        if (isMounted && res.overview) {
          setOverview(res.overview);
        }
      })
      .catch((err) => {
        console.error('Failed to load equipment research overview:', err);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Analyze Research Inquiry Handler
  const handleAnalyze = useCallback(
    async (queryToAnalyze, categoryOverride) => {
      const q = (queryToAnalyze ?? query).trim();
      if (!q) return;

      const currentSeq = ++reqSeqRef.current;
      setIsLoading(true);
      setError(null);

      const catFilter = categoryOverride && categoryOverride !== 'all' ? categoryOverride : null;

      try {
        const res = await flameApi.interpretEquipmentResearch(q, catFilter);
        if (currentSeq !== reqSeqRef.current) return;

        if (res.research_package) {
          setResearchPackage(res.research_package);
          if (res.research_package.category && (!categoryOverride || categoryOverride === 'all')) {
            setActiveCategory(res.research_package.category);
          }
        }
      } catch (err) {
        if (currentSeq !== reqSeqRef.current) return;
        console.error('Failed to interpret equipment research objective:', err);
        setError(err.message || 'Failed to interpret research inquiry.');
      } finally {
        if (currentSeq === reqSeqRef.current) {
          setIsLoading(false);
        }
      }
    },
    [query]
  );

  // 3. Prompt Response Handler from Shared ResearchPromptBar
  const handlePromptResult = useCallback((res) => {
    if (!res) return;
    reqSeqRef.current++;
    setPromptResult(res);
    if (res.specialist_data?.category) {
      setActiveCategory(res.specialist_data.category);
    }
    if (res.specialist_data?.equipment_package) {
      setResearchPackage(res.specialist_data.equipment_package);
    }
  }, []);

  // 4. Handle initialContext from AI Assistant or other tabs
  useEffect(() => {
    if (initialContext) {
      if (initialContext.handoff) {
        // Handled automatically by ResearchPromptBar to avoid duplicate calls
        return;
      }
      if (initialContext.objective || initialContext.query) {
        const q = initialContext.objective || initialContext.query;
        setQuery(q);
        handleAnalyze(q, initialContext.category);
      } else if (initialContext.category) {
        setActiveCategory(initialContext.category);
      }
    } else {
      // Default initial query on fresh load
      const defaultQ =
        'I want to design a more reliable spacecraft smoke detection system. Find relevant NASA experiments, available measurements, research limitations, and potential research directions.';
      setQuery(defaultQ);
      handleAnalyze(defaultQ, 'detection');
    }
  }, [initialContext, handleAnalyze]);

  // 5. Quick-start template selector
  const handleSelectTemplate = (tpl) => {
    setQuery(tpl.query);
    setActiveCategory(tpl.category);
    handleAnalyze(tpl.query, tpl.category);
  };

  // 6. Category switcher
  const handleSelectCategory = (catId) => {
    setActiveCategory(catId);
    if (query.trim()) {
      handleAnalyze(query.trim(), catId);
    }
  };

  // 7. Navigation router
  const handleNavigate = (tabId, params) => {
    if (typeof onSelectTab === 'function') {
      onSelectTab(tabId, params);
    } else {
      console.warn(`Navigation to tab "${tabId}" not available: onSelectTab prop missing.`);
    }
  };

  const categories = overview?.categories || [];
  const templates = overview?.quick_start_templates || [];

  const investigations = researchPackage?.matched_investigations || overview?.cataloged_investigations || [];
  const externalContext = researchPackage?.external_research_context || overview?.external_research_context || [];
  const insights = researchPackage?.scientific_insights;
  const gaps = researchPackage?.linked_research_gaps || [];
  const actions = researchPackage?.recommended_actions || [];
  const detectedParams = researchPackage?.detected_parameters || [];

  return (
    <div className="max-w-7xl w-full mx-auto space-y-7 py-4 sm:py-6 animate-in fade-in duration-300">
      {/* Top Title Banner */}
      <div className="space-y-3 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-xs font-mono text-orange-600 uppercase tracking-wider font-semibold">
            Module 02 • Spacecraft Fire-Safety Systems Research
          </span>
          <span className="text-[10px] font-mono text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded ml-auto">
            Scientific Decision Support • Not Certified Safety Approval
          </span>
        </div>

        <div className="space-y-1.5">
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-slate-900">
            Fire-Safety Equipment Research
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 max-w-4xl leading-relaxed">
            Investigate how NASA microgravity combustion findings (Saffire, BASS-II, Cygnus telemetry, SAME, FLEX) inform spacecraft fire detection, fire prevention, and fire suppression technologies. Ground your engineering decisions in traceable flight records with explicit epistemic boundaries.
          </p>
        </div>
      </div>

      {/* Shared ResearchPromptBar: Integrated Prompt Experience */}
      <ResearchPromptBar
        initialWorkspace="equipment"
        handoffContext={initialContext}
        renderInlineResults={false}
        onResult={handlePromptResult}
        onNavigate={handleNavigate}
      />

      {/* Structured Prompt Response Card (Visual-First F5 Layout) */}
      {promptResult && (
        <PromptEquipmentResultsCard
          result={promptResult}
          onReset={() => setPromptResult(null)}
          onNavigate={handleNavigate}
          onSelectCategory={handleSelectCategory}
        />
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 space-y-1">
          <strong>Research Discovery Error:</strong> {error}
        </div>
      )}

      {/* Collapsible Manual Analysis & Domain Suite */}
      <div className="space-y-5 pt-2">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
              Manual Category Explorer & Telemetry Inspection
            </h3>
            <span className="text-[10px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
              Active: {activeCategory.toUpperCase()}
            </span>
          </div>

          <button
            onClick={() => setShowManualSuite((prev) => !prev)}
            className="text-xs font-mono text-orange-600 hover:text-orange-700 flex items-center gap-1.5 cursor-pointer"
          >
            <span>{showManualSuite ? 'Hide Controls' : 'Show Controls'}</span>
            <span>{showManualSuite ? '▲' : '▼'}</span>
          </button>
        </div>

        {showManualSuite && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Component 1: Natural-Language Objective Input with Quick-Start Templates */}
            <ObjectiveInputBar
              query={query}
              onQueryChange={setQuery}
              onAnalyze={(q) => handleAnalyze(q, activeCategory)}
              isLoading={isLoading}
              templates={templates}
              onSelectTemplate={handleSelectTemplate}
            />

            {/* Component 2: Category Selector Tabs */}
            <CategorySelector
              categories={categories}
              activeCategory={activeCategory}
              onSelectCategory={handleSelectCategory}
            />

            {/* Component 3: Relevant NASA Evidence Cards */}
            <InvestigationsList
              investigations={investigations}
              externalContext={externalContext}
              activeCategory={activeCategory}
              onNavigate={handleNavigate}
            />

            {/* Component 4: Scientific Evidence Analysis (Verified Physical Channels) */}
            <VerifiedMeasurementsPanel
              parameters={detectedParams}
              investigations={investigations}
            />

            {/* Component 5: Equipment Research Insights (5-Tier Epistemic Synthesis) */}
            {insights && <EngineeringInsights insights={insights} />}

            {/* Component 6: Research Opportunities (Linked Research Gap Findings) */}
            {gaps.length > 0 && (
              <ResearchGapsSection gaps={gaps} onNavigate={handleNavigate} />
            )}

            {/* Component 7: Action Launcher (Cross-Dashboard Tool Navigation) */}
            {actions.length > 0 && (
              <ActionLauncherBanner actions={actions} onNavigate={handleNavigate} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
