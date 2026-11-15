import React, { useState } from 'react';
import { useVisualizationData } from '../../hooks/useVisualizationData';
import { ChannelSelector } from './ChannelSelector';
import { DataWindowControls } from './DataWindowControls';
import { TimeSeriesChart } from './TimeSeriesChart';
import { ExperimentMatrixChart } from './ExperimentMatrixChart';
import { LoadingSpinner } from '../../../../components/common/LoadingSpinner';
import { ResearchPromptBar } from '../../../../components/common/ResearchPromptBar';

/**
 * DataVisualizerWorkspace
 * Master container coordinating scientific visualization modes, channel selection,
 * server windowing, decimation, and verified experimental rendering.
 * Enhanced in Phase F3: Prompt-Driven Multi-Chart Presentation with Step 4 UX Layout Mandate.
 */
export function DataVisualizerWorkspace({ datasetId, datasetInfo, metadata, initialContext = null }) {
  const isExperimentMatrix = datasetInfo?.granularity === 'experiment';
  const [showLimitations, setShowLimitations] = useState(false);
  const [promptResponse, setPromptResponse] = useState(null);
  const [showPromptDetails, setShowPromptDetails] = useState(false);
  const [showManualExplorer, setShowManualExplorer] = useState(false);

  const {
    records,
    totalRecords,
    loading,
    error,
    offset,
    limit,
    timeAxis,
    viewMode,
    setViewMode,
    dataQuality,
    verifiedEvents,
    availableChannels,
    selectedChannels,
    selectedChannelIds,
    axisCompatibility,
    enableDownsampling,
    setEnableDownsampling,
    toggleChannel,
    clearSelection,
    selectAllInCategory,
    changeOffset,
    changeLimit,
    refetch,
  } = useVisualizationData(datasetId, metadata);

  const promptVisualizations = promptResponse?.visualizations || [];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* 1. Unified Research Prompt Bar (Phase F3 Multi-Channel Engine) */}
      <ResearchPromptBar
        initialWorkspace="visualization"
        renderInlineResults={false}
        handoffContext={initialContext}
        onResultReceived={(res) => {
          setPromptResponse(res);
          if (res) {
            setShowManualExplorer(false);
          }
        }}
        className="border-orange-200 shadow-sm"
      />

      {/* 2. Step 4 UX Layout: Main Scientific Graphs & Concise Observations */}
      {promptVisualizations.length > 0 && (
        <div className="space-y-5 p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          {/* 2.1 Compact Interpretation Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
            <div className="flex flex-wrap items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
              <h3 className="text-sm font-semibold text-slate-900 tracking-wide">
                Prompt Visualizations ({promptVisualizations.length} Units-Decoupled Charts)
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-50 border border-orange-200 text-orange-700 font-semibold">
                Units Separated
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700">
                Min-Max LTTB Decimated
              </span>
            </div>
            <div className="text-[11px] font-mono text-slate-500 flex items-center gap-2">
              <span>Objective:</span>
              <span className="text-orange-600 italic max-w-md truncate">
                "{promptResponse.objective}"
              </span>
            </div>
          </div>

          {/* 2.2 Main Scientific Graphs (Responsive Multi-Chart Grid) */}
          <div className={`grid gap-6 ${promptVisualizations.length > 1 ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1'}`}>
            {promptVisualizations.map((chart, idx) => {
              const chartPoints = chart.series_data?.points || [];
              const chartChannels = (chart.channel_ids || []).map((chId) => ({
                id: chId,
                label: chart.channel_labels?.[chId] || chId,
                units: chart.y_units || 'a.u.',
                color: idx === 0 ? '#38bdf8' : idx === 1 ? '#f97316' : '#a855f7',
              }));

              const chartEvents = (chart.event_markers || []).map((ev) => ({
                event_name: ev.event_name || ev.label || 'Event',
                timestamp_seconds: ev.time_start_s ?? ev.start_time ?? ev.timestamp_seconds ?? 0,
                time_start_s: ev.time_start_s ?? ev.start_time ?? 0,
                time_end_s: ev.time_end_s ?? ev.end_time ?? 0,
                color: ev.color || '#f59e0b',
                annotation: ev.annotation || '',
              }));

              return (
                <div
                  key={chart.chart_id || idx}
                  className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                          <span>{chart.title}</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white border border-slate-200 text-orange-600">
                            {chart.y_units}
                          </span>
                        </h4>
                        {chart.subtitle && (
                          <p className="text-[11px] font-mono text-slate-500 mt-0.5">
                            {chart.subtitle}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 font-mono text-[10px] text-slate-500">
                        <span className="bg-white px-2 py-0.5 rounded border border-slate-200">
                          {chart.data_resolution}
                        </span>
                        {chart.time_range && (
                          <span className="bg-white px-2 py-0.5 rounded border border-slate-200">
                            Range: {chart.time_range[0]?.toFixed(1)}s – {chart.time_range[1]?.toFixed(1)}s
                          </span>
                        )}
                      </div>
                    </div>

                    {/* TimeSeriesChart rendering */}
                    {chartPoints.length > 0 ? (
                      <TimeSeriesChart
                        records={chartPoints}
                        timeAxis="time"
                        selectedChannels={chartChannels}
                        axisCompatibility={{ isDualAxis: false, primaryUnits: chart.y_units }}
                        enableDownsampling={true}
                        verifiedEvents={chartEvents}
                        dataQuality={{
                          duration_seconds: chart.time_range ? chart.time_range[1] - chart.time_range[0] : 0,
                          time_start_seconds: chart.time_range?.[0] ?? 0,
                          time_end_seconds: chart.time_range?.[1] ?? 0,
                          sampling_rate_hz: 30.3,
                        }}
                        datasetId={chart.dataset_id}
                      />
                    ) : (
                      <div className="p-8 text-center text-xs font-mono text-slate-500 bg-white rounded-lg border border-slate-200">
                        No points returned for this telemetry channel window.
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-200 text-[10px] font-mono text-slate-500">
                    <span>Provenance: {chart.provenance}</span>
                    <span className="text-slate-600">{chartPoints.length} decimated samples</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 2.3 Concise Key Observations (Step 4 Mandate: 2-3 Bullet Points) */}
          {promptResponse.key_findings && promptResponse.key_findings.length > 0 && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-800 flex items-center gap-1.5 font-mono">
                  <span>✓</span> Verified Empirical Observations
                </span>
                <span className="text-[10px] font-mono text-slate-600">
                  {promptResponse.key_findings.length} evidence points
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

          {/* 2.4 Experiment Event Markers & Metadata */}
          {promptVisualizations.some((c) => c.event_markers?.length > 0) && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono">
              <div className="text-slate-600 mb-1.5 font-semibold text-[11px] flex items-center gap-1.5">
                <span className="text-amber-600">⚡</span>
                <span>Verified Experiment Event Markers</span>
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
                    <span className="text-amber-700 font-semibold block mb-1">⚠️ Scientific Limitations & Caveats:</span>
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

      {/* 3. Manual Telemetry Explorer Toggle Bar (Collapsible to prevent visual clutter) */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono">
        <span className="text-slate-800 font-semibold flex items-center gap-2">
          <span>🛠 Advanced Manual Controls & Telemetry Explorer</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-600">
            Manual Channel Selector, Windowing & Downsampling
          </span>
        </span>
        <button
          onClick={() => setShowManualExplorer(!showManualExplorer)}
          className="text-xs text-orange-600 hover:text-orange-700 cursor-pointer font-semibold"
        >
          {showManualExplorer ? 'Collapse Manual Controls ▲' : 'Expand Manual Controls ▼'}
        </button>
      </div>

      {/* 4. Existing Manual Controls and Visualization (Preserved Fully) */}
      {showManualExplorer && (
        <div className="space-y-5">
          {/* Scientific Dataset Header & Provenance Banner */}
          <div className="p-4 rounded-2xl bg-white border border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-orange-50 border border-orange-200 flex items-center justify-center text-orange-600 font-bold">
                📊
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900">
                    {datasetInfo?.dataset_id || datasetId}
                  </span>
                  <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                    {datasetInfo?.granularity || 'time_series'}
                  </span>
                  <span className="text-[10px] font-mono text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    Validation: {datasetInfo?.scientific_validation || 'pending review'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                  Source: {datasetInfo?.source_file || 'NASA Archive'} • {totalRecords.toLocaleString()} verified samples
                  {dataQuality?.duration_seconds && ` • Flight Duration: ${dataQuality.duration_seconds.toFixed(1)}s`}
                  {dataQuality?.sampling_rate_hz && ` • Sampling Rate: ~${dataQuality.sampling_rate_hz} Hz`}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
              {/* View Mode Switcher for Time-Series Datasets */}
              {!isExperimentMatrix && (
                <div className="flex items-center bg-slate-100 border border-slate-200 rounded-lg p-0.5">
                  <button
                    onClick={() => setViewMode('overview')}
                    className={`px-2.5 py-1 rounded text-[11px] transition cursor-pointer ${
                      viewMode === 'overview'
                        ? 'bg-white text-orange-600 font-semibold border border-orange-300 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                    title="View full flight experiment timeline with extrema-preserving decimation"
                  >
                    ⚡ Full Flight Overview
                  </button>
                  <button
                    onClick={() => setViewMode('window')}
                    className={`px-2.5 py-1 rounded text-[11px] transition cursor-pointer ${
                      viewMode === 'window'
                        ? 'bg-white text-orange-600 font-semibold border border-orange-300 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                    title="View raw full-resolution points with window navigation"
                  >
                    🔍 Windowed Buffer
                  </button>
                </div>
              )}

              <button
                onClick={() => setShowLimitations(!showLimitations)}
                className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition cursor-pointer"
                title="View verified scientific data disclosures and measurement boundaries"
              >
                {showLimitations ? 'Hide Limitations ▲' : 'Scientific Limitations ▼'}
              </button>

              <button
                onClick={refetch}
                disabled={loading}
                className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition cursor-pointer"
              >
                ↻ Reload
              </button>
            </div>
          </div>

          {/* Scientific Measurement Disclosures & Limitations Panel */}
          {showLimitations && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2 text-xs font-mono text-slate-700 animate-in fade-in duration-150">
              <div className="flex items-center gap-2 text-amber-800 font-semibold">
                <span>⚠️</span>
                <span>NASA Microgravity Flight Telemetry Grounding & Scientific Disclosures:</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-slate-600 pl-1">
                <li>
                  <strong className="text-slate-900">Flame Spread Rate:</strong> Uninstrumented in automated telemetry. Flame spread velocities require post-flight calibrated optical video tracking and flame edge digitization.
                </li>
                <li>
                  <strong className="text-slate-900">Extinction Boundary:</strong> No discrete scalar extinction column is recorded. Thermocouple decay slopes indicate cooling, but verified extinction identification requires validated analytical criteria and optical camera footage.
                </li>
                <li>
                  <strong className="text-slate-900">Discontinuity Preservation:</strong> SVG plots split trajectories across sensor dropouts or blank entries. Missing readings are never falsely connected with artificial straight lines.
                </li>
                <li>
                  <strong className="text-slate-900">Extrema Preservation:</strong> Min-Max decimation guarantees that temperature peaks, radiant heat flux spikes, and pressure drops are mathematically preserved in overview mode.
                </li>
              </ul>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs font-mono text-rose-800 flex items-center justify-between gap-3">
              <span>Failed to load data for visualization: {error}</span>
              <button
                onClick={refetch}
                className="px-3 py-1 rounded bg-rose-600 hover:bg-rose-700 text-white font-medium cursor-pointer"
              >
                Retry
              </button>
            </div>
          )}

          {/* Loading state indicator */}
          {loading && records.length === 0 && (
            <div className="p-16 rounded-2xl bg-slate-50 border border-slate-200 flex justify-center">
              <LoadingSpinner message="Retrieving real measurement channels from FastAPI backend..." />
            </div>
          )}

          {/* Visualization Canvas */}
          {records.length > 0 && (
            <>
              {isExperimentMatrix ? (
                /* Mode 1: Discrete ISS Microgravity Experiment Test Matrix (BASS-II) */
                <ExperimentMatrixChart records={records} />
              ) : (
                /* Mode 2: Multi-Channel Scientific Time Series (Saffire / Telemetry) */
                <div className="space-y-4">
                  {/* Channel Selector */}
                  <ChannelSelector
                    availableChannels={availableChannels}
                    selectedChannelIds={selectedChannelIds}
                    axisCompatibility={axisCompatibility}
                    onToggleChannel={toggleChannel}
                    onClearSelection={clearSelection}
                    onSelectAllInCategory={selectAllInCategory}
                  />

                  {/* Data Window Controls (Only when in windowed buffer mode) */}
                  {viewMode === 'window' && (
                    <DataWindowControls
                      offset={offset}
                      limit={limit}
                      totalRecords={totalRecords}
                      loadedCount={records.length}
                      loading={loading}
                      enableDownsampling={enableDownsampling}
                      onToggleDownsampling={() => setEnableDownsampling((prev) => !prev)}
                      onChangeOffset={changeOffset}
                      onChangeLimit={changeLimit}
                    />
                  )}

                  {/* Interactive Scientific Time Series SVG Plot */}
                  <TimeSeriesChart
                    records={records}
                    timeAxis={timeAxis}
                    selectedChannels={selectedChannels}
                    axisCompatibility={axisCompatibility}
                    enableDownsampling={enableDownsampling}
                    verifiedEvents={verifiedEvents}
                    dataQuality={dataQuality}
                    datasetId={datasetId}
                  />
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
