import React, { useState } from 'react';
import { useApiStatus } from '../../hooks/useApiStatus';
import { useDatasetCatalog } from '../dataset-explorer/hooks/useDatasetCatalog';
import { useExperimentComparison } from './hooks/useExperimentComparison';
import { ComparisonDatasetSelector } from './components/ComparisonDatasetSelector';
import { ChannelMatcher } from './components/ChannelMatcher';
import { ComparisonToolbar } from './components/ComparisonToolbar';
import { SideBySideView } from './components/SideBySideView';
import { OverlayComparisonChart } from './components/OverlayComparisonChart';
import { ComparisonStatsTable } from './components/ComparisonStatsTable';
import { ScientificFindingsPanel } from './components/ScientificFindingsPanel';
import { BassComparisonView } from './components/BassComparisonView';
import { PromptComparisonChartCard } from './components/PromptComparisonChartCard';
import { ApiStatusBar } from '../../components/common/ApiStatusBar';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ResearchPromptBar } from '../../components/common/ResearchPromptBar';

/**
 * ExperimentComparison Workspace
 * Primary scientific comparison workspace for NASA FLAME.
 * Enables researchers to evaluate and compare compatible microgravity combustion datasets.
 * Enhanced in Phase F3: Prompt-Driven Multi-Chart Presentation with Step 4 UX Layout Mandate
 * and Step 6 Scientific Audit Grounding.
 */
export function ExperimentComparison({ initialContext }) {
  const {
    status: apiStatus,
    datasetCount,
    validationStatus,
    error: apiError,
    isRetrying,
    checkConnection,
  } = useApiStatus();

  const {
    datasets,
    error: catalogError,
    refetch: refetchCatalog,
  } = useDatasetCatalog();

  const initialA = initialContext?.dataset_a_id || initialContext?.datasetA || 'saffire_iii_sample_1';
  const initialB = initialContext?.dataset_b_id || initialContext?.datasetB || 'saffire_iii_sample_2';

  const {
    datasetAId,
    datasetBId,
    datasetAInfo,
    datasetBInfo,
    recordsA,
    recordsB,
    totalRecordsA,
    totalRecordsB,
    loading,
    error,
    timeAxisA,
    timeAxisB,
    offsetA,
    offsetB,
    windowLimit,
    channelMatching,
    effectiveChannelId,
    activeChannelObj,
    ignitionTimeA,
    ignitionTimeB,
    canEventAlign,
    alignmentMode,
    enableDownsampling,
    statsA,
    statsB,
    comparisonMetrics,
    selectDatasetA,
    selectDatasetB,
    setSelectedChannelId,
    setAlignmentMode,
    setEnableDownsampling,
    changeOffsetA,
    changeOffsetB,
    changeWindowLimit,
    refetchAll,
  } = useExperimentComparison(initialA, initialB);

  // Phase F3 Prompt Response & UX Layout State
  const [promptResponse, setPromptResponse] = useState(null);
  const [showPromptDetails, setShowPromptDetails] = useState(false);
  const [showManualComparison, setShowManualComparison] = useState(false);

  React.useEffect(() => {
    if (initialContext?.dataset_a_id && selectDatasetA) {
      selectDatasetA(initialContext.dataset_a_id);
    }
    if (initialContext?.dataset_b_id && selectDatasetB) {
      selectDatasetB(initialContext.dataset_b_id);
    }
  }, [initialContext]);

  const isBothBass = datasetAId === 'bass_ii_experiments' && datasetBId === 'bass_ii_experiments';

  const handleRetry = () => {
    checkConnection(true);
    refetchCatalog();
    refetchAll();
  };

  const handlePromptResult = (res) => {
    setPromptResponse(res);
    if (res) {
      setShowManualComparison(false);
      // Synchronize manual selector state if prompt resolved datasets
      if (res.specialist_data?.is_discrete_matrix) {
        if (datasetAId !== 'bass_ii_experiments') selectDatasetA('bass_ii_experiments');
        if (datasetBId !== 'bass_ii_experiments') selectDatasetB('bass_ii_experiments');
      } else if (res.specialist_data?.dataset_a && res.specialist_data?.dataset_b) {
        if (datasetAId !== res.specialist_data.dataset_a) selectDatasetA(res.specialist_data.dataset_a);
        if (datasetBId !== res.specialist_data.dataset_b) selectDatasetB(res.specialist_data.dataset_b);
      }
    }
  };

  const promptVisualizations = promptResponse?.visualizations || [];

  return (
    <div className="max-w-7xl w-full mx-auto space-y-6 py-4 sm:py-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="space-y-3 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-xs font-mono text-orange-600 uppercase tracking-wider font-semibold">
            Module 01 • NASA Scientific Experiment Comparison Workspace
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded ml-auto">
            Dual-Dataset Engine
          </span>
        </div>

        <div className="space-y-1.5">
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-slate-900">
            Scientific Experiment Comparison
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 max-w-4xl leading-relaxed">
            Multi-experiment comparative analytics for NASA microgravity combustion research. Compare compatible continuous Saffire sensor suites across samples, or evaluate discrete BASS-II glovebox burn test matrices using verified physical dimensions and documented event timelines.
          </p>
        </div>

        {/* Live Backend Connection Status Banner */}
        <ApiStatusBar
          status={apiStatus}
          datasetCount={datasetCount || datasets.length}
          validationStatus={validationStatus}
          error={apiError || catalogError}
          isRetrying={isRetrying}
          onRetry={handleRetry}
        />
      </div>

      {/* 1. Unified Research Prompt Bar (Phase F3 Engine) */}
      <ResearchPromptBar
        initialWorkspace="comparison"
        renderInlineResults={false}
        handoffContext={initialContext}
        onResultReceived={handlePromptResult}
        className="border-orange-200 shadow-sm"
      />

      {/* 2. Step 4 UX Layout: Prompt-Driven Comparative Charts & Concise Observations */}
      {promptVisualizations.length > 0 && (
        <div className="space-y-5 p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          {/* 2.1 Compact Interpretation Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
            <div className="flex flex-wrap items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
              <h3 className="text-sm font-semibold text-slate-900 tracking-wide">
                Comparative Charts ({promptVisualizations.length} Units-Decoupled Series)
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-50 border border-orange-200 text-orange-700 font-semibold">
                Units Separated
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700">
                Min-Max LTTB Dual Series
              </span>
            </div>
            <div className="text-[11px] font-mono text-slate-500 flex items-center gap-2">
              <span>Comparing:</span>
              <span className="text-orange-600 font-semibold">
                {promptResponse.specialist_data?.dataset_a || datasetAId} vs{' '}
                {promptResponse.specialist_data?.dataset_b || datasetBId}
              </span>
            </div>
          </div>

          {/* 2.2 Main Comparative Scientific Graphs (Responsive Grid) */}
          <div className={`grid gap-6 ${promptVisualizations.length > 1 ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1'}`}>
            {promptVisualizations.map((chart, idx) => (
              <PromptComparisonChartCard
                key={chart.chart_id || idx}
                chart={chart}
                datasetAId={promptResponse.specialist_data?.dataset_a || datasetAId}
                datasetBId={promptResponse.specialist_data?.dataset_b || datasetBId}
                idx={idx}
              />
            ))}
          </div>

          {/* 2.3 Concise Key Observations (Step 4 Mandate + Step 6 Audit Grounding) */}
          {promptResponse.key_findings && promptResponse.key_findings.length > 0 && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-800 flex items-center gap-1.5 font-mono">
                  <span>✓</span> Grounded Comparative Observations
                </span>
                <span className="text-[10px] font-mono text-slate-600">
                  {promptResponse.key_findings.length} verified metrics
                </span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-800">
                {promptResponse.key_findings.map((finding, idx) => (
                  <li key={idx} className="flex items-start gap-2 leading-relaxed">
                    <span className="text-emerald-600 mt-0.5">•</span>
                    <span>{finding}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 2.4 Event Markers & Comparability Verdict */}
          {promptVisualizations.some((c) => c.event_markers?.length > 0) && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono">
              <div className="text-slate-600 mb-1.5 font-semibold text-[11px] flex items-center gap-1.5">
                <span className="text-amber-600">⚡</span>
                <span>Documented Experiment Event Markers & Comparability</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {promptVisualizations
                  .flatMap((c) => c.event_markers || [])
                  .map((ev, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded bg-white border border-slate-200 text-amber-800 text-[11px] flex items-center gap-1.5"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                      <span>{ev.event_name}</span>
                      {ev.annotation && <span className="text-slate-500 text-[10px]">({ev.annotation})</span>}
                    </span>
                  ))}
              </div>
            </div>
          )}

          {/* 2.5 Expandable Scientific Limitations & Citations */}
          <div className="pt-2 border-t border-slate-200">
            <button
              onClick={() => setShowPromptDetails(!showPromptDetails)}
              className="text-xs text-orange-600 hover:text-orange-700 font-mono cursor-pointer flex items-center gap-1.5"
            >
              <span>{showPromptDetails ? 'Hide Scientific Disclosures & Provenance ▲' : 'Show Scientific Disclosures & Provenance ▼'}</span>
            </button>

            {showPromptDetails && (
              <div className="mt-3 p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs font-mono">
                {/* Caveats */}
                {promptResponse.scientific_caveats && promptResponse.scientific_caveats.length > 0 && (
                  <div>
                    <span className="text-amber-700 font-semibold block mb-1">⚠️ Scientific Transfer & Sensor Limitations:</span>
                    <ul className="list-disc list-inside space-y-1 text-slate-700 text-[11px]">
                      {promptResponse.scientific_caveats.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Citations */}
                {promptResponse.provenance_citations && promptResponse.provenance_citations.length > 0 && (
                  <div>
                    <span className="text-slate-600 font-semibold block mb-1">Source Provenance Citations:</span>
                    <div className="flex flex-wrap gap-2">
                      {promptResponse.provenance_citations.map((cit) => (
                        <span
                          key={cit.id}
                          className="px-2.5 py-1 rounded bg-white border border-slate-200 text-slate-700 text-[11px]"
                        >
                          {cit.title} ({cit.reference}) • {cit.grounding_level}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 3. Manual Comparison Suite Toggle Bar (Collapsible for Clean Prompt Experience) */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono">
        <span className="text-slate-800 font-semibold flex items-center gap-2">
          <span>🛠 Advanced Manual Comparison Suite</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-600">
            Dataset Selector, Channel Matcher, Alignment & Statistics
          </span>
        </span>
        <button
          onClick={() => setShowManualComparison(!showManualComparison)}
          className="text-xs text-orange-600 hover:text-orange-700 cursor-pointer font-semibold"
        >
          {showManualComparison ? 'Collapse Manual Controls ▲' : 'Expand Manual Controls ▼'}
        </button>
      </div>

      {/* 4. Existing Manual Comparison Tools (Preserved Completely) */}
      {showManualComparison && (
        <div className="space-y-5 animate-in fade-in duration-150">
          {/* Dataset Selection Bar */}
          <ComparisonDatasetSelector
            datasets={datasets}
            datasetAId={datasetAId}
            datasetBId={datasetBId}
            datasetAInfo={datasetAInfo}
            datasetBInfo={datasetBInfo}
            onSelectDatasetA={selectDatasetA}
            onSelectDatasetB={selectDatasetB}
          />

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs font-mono text-rose-800 flex items-center justify-between gap-3">
              <span>Failed to load comparison data: {error}</span>
              <button
                onClick={refetchAll}
                className="px-3 py-1 rounded bg-rose-600 hover:bg-rose-700 text-white font-medium cursor-pointer"
              >
                Retry Loading
              </button>
            </div>
          )}

          {/* Loading Spinner */}
          {loading && recordsA.length === 0 && recordsB.length === 0 && (
            <div className="p-16 rounded-2xl bg-slate-50 border border-slate-200 flex justify-center">
              <LoadingSpinner message="Retrieving experimental measurements from FastAPI backend..." />
            </div>
          )}

          {/* Comparison Body */}
          {isBothBass ? (
            /* Mode 1: Discrete BASS-II Matrix Comparison */
            <BassComparisonView records={recordsA} />
          ) : (
            /* Mode 2: Continuous Sensor Time-Series Comparison */
            <div className="space-y-5">
              {/* Shared Channel Selector */}
              <ChannelMatcher
                sharedChannels={channelMatching.sharedChannels}
                aOnlyChannels={channelMatching.aOnlyChannels}
                bOnlyChannels={channelMatching.bOnlyChannels}
                activeChannelId={effectiveChannelId}
                onSelectChannel={setSelectedChannelId}
              />

              {/* Comparison Controls Toolbar */}
              <ComparisonToolbar
                alignmentMode={alignmentMode}
                canEventAlign={canEventAlign}
                ignitionTimeA={ignitionTimeA}
                ignitionTimeB={ignitionTimeB}
                datasetAId={datasetAId}
                datasetBId={datasetBId}
                windowLimit={windowLimit}
                enableDownsampling={enableDownsampling}
                loading={loading}
                onSelectAlignmentMode={setAlignmentMode}
                onChangeWindowLimit={changeWindowLimit}
                onToggleDownsampling={() => setEnableDownsampling(!enableDownsampling)}
              />

              {/* Chart Display Area */}
              {alignmentMode === 'side_by_side' ? (
                <SideBySideView
                  datasetAId={datasetAId}
                  datasetBId={datasetBId}
                  recordsA={recordsA}
                  recordsB={recordsB}
                  timeAxisA={timeAxisA}
                  timeAxisB={timeAxisB}
                  activeChannelObj={activeChannelObj}
                  enableDownsampling={enableDownsampling}
                  offsetA={offsetA}
                  offsetB={offsetB}
                  totalRecordsA={totalRecordsA}
                  totalRecordsB={totalRecordsB}
                  windowLimit={windowLimit}
                  onChangeOffsetA={changeOffsetA}
                  onChangeOffsetB={changeOffsetB}
                />
              ) : (
                <OverlayComparisonChart
                  datasetAId={datasetAId}
                  datasetBId={datasetBId}
                  recordsA={recordsA}
                  recordsB={recordsB}
                  timeAxisA={timeAxisA}
                  timeAxisB={timeAxisB}
                  activeChannelObj={activeChannelObj}
                  alignmentMode={alignmentMode}
                  ignitionTimeA={ignitionTimeA}
                  ignitionTimeB={ignitionTimeB}
                  enableDownsampling={enableDownsampling}
                />
              )}

              {/* Descriptive Statistics Table */}
              <ComparisonStatsTable
                datasetAId={datasetAId}
                datasetBId={datasetBId}
                activeChannelObj={activeChannelObj}
                statsA={statsA}
                statsB={statsB}
                comparisonMetrics={comparisonMetrics}
                recordsCountA={recordsA.length}
                recordsCountB={recordsB.length}
              />

              {/* Scientific Findings & Safeguards Panel */}
              <ScientificFindingsPanel
                datasetAId={datasetAId}
                datasetBId={datasetBId}
                datasetAInfo={datasetAInfo}
                datasetBInfo={datasetBInfo}
                activeChannelObj={activeChannelObj}
                statsA={statsA}
                statsB={statsB}
                comparisonMetrics={comparisonMetrics}
                isEventAligned={alignmentMode === 'overlay_event_aligned'}
                ignitionTimeA={ignitionTimeA}
                ignitionTimeB={ignitionTimeB}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
