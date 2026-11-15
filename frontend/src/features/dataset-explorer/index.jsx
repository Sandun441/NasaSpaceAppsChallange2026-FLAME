import React, { useState, useEffect } from 'react';
import { useDatasetCatalog } from './hooks/useDatasetCatalog';
import { useDatasetDetails } from './hooks/useDatasetDetails';
import { useApiStatus } from '../../hooks/useApiStatus';
import { DatasetCatalog } from './components/DatasetCatalog';
import { ProvenanceCard } from './components/ProvenanceCard';
import { ColumnsViewer } from './components/ColumnsViewer';
import { RecordsTable } from './components/RecordsTable';
import { DataVisualizerWorkspace } from './components/visualization/DataVisualizerWorkspace';
import { ApiStatusBar } from '../../components/common/ApiStatusBar';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export function DatasetExplorer({ initialContext = null }) {
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
    loading: loadingCatalog,
    error: catalogError,
    refetch: refetchCatalog,
  } = useDatasetCatalog();

  const incomingDs = initialContext?.dataset_id || initialContext?.datasetId || initialContext?.initialDatasetId;
  const incomingView = initialContext?.view || initialContext?.activeView;

  const [selectedDatasetId, setSelectedDatasetId] = useState(incomingDs || 'saffire_iii_sample_1');
  const [activeView, setActiveView] = useState(incomingView || 'visualize'); // 'visualize' | 'table'

  useEffect(() => {
    if (incomingDs) {
      setSelectedDatasetId(incomingDs);
    }
    if (incomingView) {
      setActiveView(incomingView);
    }
  }, [incomingDs, incomingView]);

  // Derive active dataset ID safely
  const effectiveDatasetId = selectedDatasetId || (datasets.length > 0 ? datasets[0].dataset_id : 'saffire_iii_sample_1');

  const {
    datasetInfo,
    metadata,
    records,
    columns,
    totalRecords,
    offset,
    limit,
    hasMore,
    loadingRecords,
    error: recordsError,
    currentPage,
    totalPages,
    nextPage,
    prevPage,
    changeLimit,
    refetchRecords,
  } = useDatasetDetails(effectiveDatasetId, 50);

  const handleRetryAll = () => {
    checkConnection(true);
    refetchCatalog();
    if (effectiveDatasetId) {
      refetchRecords();
    }
  };

  return (
    <div className="max-w-7xl w-full mx-auto space-y-6 py-4 sm:py-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="space-y-3 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-mono text-emerald-700 uppercase tracking-wider font-semibold">
            Module 00 • NASA Live Flight Datasets
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded ml-auto">
            FastAPI Live Telemetry
          </span>
        </div>

        <div className="space-y-1.5">
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-slate-900">
            NASA Flight Dataset Explorer
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 max-w-4xl leading-relaxed">
            Direct read-only scientific interface to the 11 registered NASA microgravity combustion and spacecraft telemetry datasets from BASS-II, Saffire-III, and Cygnus missions.
          </p>
        </div>

        {/* Live Backend Connection Status Banner */}
        <ApiStatusBar
          status={apiStatus}
          datasetCount={datasetCount || datasets.length}
          validationStatus={validationStatus}
          error={apiError || catalogError}
          isRetrying={isRetrying}
          onRetry={handleRetryAll}
        />
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Dataset Catalog Navigation (4 cols) */}
        <div className="lg:col-span-4 p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Scientific Datasets</span>
              <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                {datasets.length} available
              </span>
            </h2>
            <button
              onClick={refetchCatalog}
              disabled={loadingCatalog}
              className="text-[11px] font-mono text-slate-500 hover:text-slate-900 transition-colors cursor-pointer"
              title="Refresh catalog list"
            >
              ↻ Refresh
            </button>
          </div>

          <DatasetCatalog
            datasets={datasets}
            selectedDatasetId={effectiveDatasetId}
            onSelectDataset={setSelectedDatasetId}
            loading={loadingCatalog}
          />
        </div>

        {/* Right Column: Detailed Dataset Inspection & Interactive Visualizer (8 cols) */}
        <div className="lg:col-span-8 space-y-5">
          {/* Provenance Card */}
          {datasetInfo ? (
            <ProvenanceCard datasetInfo={datasetInfo} metadata={metadata} />
          ) : (
            <div className="p-8 rounded-2xl bg-slate-50 border border-slate-200 text-center text-xs font-mono text-slate-600">
              {loadingCatalog ? (
                <LoadingSpinner message="Retrieving dataset catalog..." />
              ) : (
                'Select a scientific dataset from the catalog to inspect metadata and measurements.'
              )}
            </div>
          )}

          {/* Measurement Channels and Units Viewer */}
          {columns.length > 0 && (
            <ColumnsViewer
              columns={columns}
              metadataColumns={metadata?.columns || []}
            />
          )}

          {/* View Mode Switcher: [Visualize Data] vs [Records Table] */}
          {datasetInfo && (
            <div className="flex items-center justify-between border-b border-slate-200 pb-3 pt-1">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveView('visualize')}
                  className={`px-4 py-2 rounded-xl text-xs font-mono font-medium flex items-center gap-2 transition cursor-pointer shadow-xs ${
                    activeView === 'visualize'
                      ? 'bg-orange-50 text-orange-700 border border-orange-200 shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <span>📈</span>
                  <span>Visualize Data</span>
                  <span className="text-[10px] bg-orange-100 text-orange-800 px-1.5 py-0.2 rounded font-semibold">
                    Interactive Workspace
                  </span>
                </button>
                <button
                  onClick={() => setActiveView('table')}
                  className={`px-4 py-2 rounded-xl text-xs font-mono font-medium flex items-center gap-2 transition cursor-pointer shadow-xs ${
                    activeView === 'table'
                      ? 'bg-orange-50 text-orange-700 border border-orange-200 shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <span>📋</span>
                  <span>Records Table</span>
                  <span className="text-[10px] text-slate-600 bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200">
                    {totalRecords.toLocaleString()} rows
                  </span>
                </button>
              </div>
            </div>
          )}

          {/* Active View: Visualization or Records Table */}
          {datasetInfo && activeView === 'visualize' && (
            <DataVisualizerWorkspace
              datasetId={effectiveDatasetId}
              datasetInfo={datasetInfo}
              metadata={metadata}
              initialContext={initialContext}
            />
          )}

          {datasetInfo && activeView === 'table' && (
            <>
              {recordsError && (
                <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs font-mono text-rose-800 flex items-center justify-between gap-3">
                  <span>{recordsError}</span>
                  <button
                    onClick={refetchRecords}
                    className="px-3 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-medium text-xs cursor-pointer"
                  >
                    Retry Records
                  </button>
                </div>
              )}

              <RecordsTable
                datasetId={effectiveDatasetId}
                records={records}
                columns={columns}
                metadataColumns={metadata?.columns || []}
                totalRecords={totalRecords}
                offset={offset}
                limit={limit}
                hasMore={hasMore}
                loading={loadingRecords}
                currentPage={currentPage}
                totalPages={totalPages}
                onNextPage={nextPage}
                onPrevPage={prevPage}
                onChangeLimit={changeLimit}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
