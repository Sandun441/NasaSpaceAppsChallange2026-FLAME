import React, { useState, useEffect, useCallback } from 'react';
import { flameApi } from '../../services/flameApi';
import { ResearchPromptBar } from '../../components/common/ResearchPromptBar';
import { PromptModelingResultsCard } from './components/PromptModelingResultsCard';
import { InterpretationBanner } from './components/InterpretationBanner';
import { DatasetSelectorCards } from './components/DatasetSelectorCards';
import { VariableSelectionPanel } from './components/VariableSelectionPanel';
import { DataPreviewTable } from './components/DataPreviewTable';
import { DataQualityAuditCard } from './components/DataQualityAuditCard';
import { ExportControls } from './components/ExportControls';

/**
 * PredictiveModelingExtraction Workspace
 * Machine learning data discovery, leakage safeguarding, preview, and extraction.
 * Enhanced in Phase F4: Prompt-Driven Data Discovery with Step 5 Data-Science Workspace Layout.
 */
export function PredictiveModelingExtraction({ initialContext, onSelectTab }) {
  // Query & Prompt State
  const [promptResponse, setPromptResponse] = useState(null);
  const [showManualConfig, setShowManualConfig] = useState(false);
  const [interpretation, setInterpretation] = useState(null);

  // Datasets & Active Selection State
  const [datasets, setDatasets] = useState([]);
  const [activeDatasetId, setActiveDatasetId] = useState(() => initialContext?.dataset_id || 'bass_ii_experiments');
  const [activeSchema, setActiveSchema] = useState(null);

  // Variable & Filter State
  const [selectedFeatures, setSelectedFeatures] = useState([]);
  const [selectedTargetId, setSelectedTargetId] = useState(() => initialContext?.target_id || null);
  const [filters, setFilters] = useState({
    materialFilter: '',
    minOxygen: null,
    maxOxygen: null,
    minFlow: null,
    maxFlow: null,
    startTime: null,
    endTime: null,
    completeCasesOnly: false,
    excludeFlaggedAnomalies: false,
  });

  // Preview & Export State
  const [previewData, setPreviewData] = useState(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [notification, setNotification] = useState(null);
  const [error, setError] = useState(null);

  const showNotification = (msg) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3500);
  };

  // 1. Initial Load: Fetch registered datasets catalog
  useEffect(() => {
    let isMounted = true;
    flameApi
      .getModelingDatasets()
      .then((res) => {
        if (isMounted && res.datasets) {
          setDatasets(res.datasets);
        }
      })
      .catch((err) => {
        console.error('Failed to load modeling datasets:', err);
        setError('Failed to connect to dataset registry. Please ensure backend is running.');
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Fetch schema whenever activeDatasetId changes
  useEffect(() => {
    let isMounted = true;
    if (!activeDatasetId) return;

    flameApi
      .getModelingDatasetSchema(activeDatasetId)
      .then((res) => {
        if (isMounted && res.dataset) {
          const schema = res.dataset;
          setActiveSchema(schema);

          // If no features selected yet, default select all available
          if (selectedFeatures.length === 0) {
            const featIds = (schema.available_features || []).map((f) => f.id);
            setSelectedFeatures(featIds);
          }

          // If current target is not supported in this dataset, reset to first supported or null
          const suppTargetIds = (schema.supported_targets || []).map((t) => t.id);
          if (selectedTargetId && !suppTargetIds.includes(selectedTargetId)) {
            setSelectedTargetId(suppTargetIds[0] || null);
          } else if (!selectedTargetId && suppTargetIds.length > 0) {
            setSelectedTargetId(suppTargetIds[0]);
          }
        }
      })
      .catch((err) => {
        console.error(`Failed to load schema for ${activeDatasetId}:`, err);
      });

    return () => {
      isMounted = false;
    };
  }, [activeDatasetId]);

  // 3. Step 6 State Connection: Handle incoming prompt research results
  const handlePromptResult = useCallback((res) => {
    setPromptResponse(res);
    if (res && res.specialist_data) {
      setShowManualConfig(false);
      const spec = res.specialist_data;

      // Update dataset selection
      if (spec.recommended_dataset_id) {
        setActiveDatasetId(spec.recommended_dataset_id);
      }

      // Update target selection
      if (spec.target_variable?.id) {
        setSelectedTargetId(spec.target_variable.id);
      } else if (spec.target_variable?.status === 'UNINSTRUMENTED_UNAVAILABLE') {
        setSelectedTargetId(null);
      }

      // Update candidate features
      if (spec.selected_features && spec.selected_features.length > 0) {
        setSelectedFeatures(spec.selected_features);
      }

      // Update interpretation object
      if (spec.interpretation) {
        setInterpretation(spec.interpretation);
      }

      // Update preview data if returned directly
      if (spec.preview && spec.preview.preview_rows) {
        setPreviewData(spec.preview);
      }
    }
  }, []);

  // 4. Data Preview Generator (Runs on filter/variable adjustment)
  const fetchPreview = useCallback(async () => {
    if (!activeDatasetId) return;

    setIsLoadingPreview(true);
    setError(null);

    const payload = {
      dataset_id: activeDatasetId,
      selected_features: selectedFeatures.length > 0 ? selectedFeatures : null,
      target_id: selectedTargetId || null,
      material_filter: filters.materialFilter || null,
      min_oxygen: filters.minOxygen ?? null,
      max_oxygen: filters.maxOxygen ?? null,
      min_flow: filters.minFlow ?? null,
      max_flow: filters.maxFlow ?? null,
      start_time_s: filters.startTime ?? null,
      end_time_s: filters.endTime ?? null,
      complete_cases_only: Boolean(filters.completeCasesOnly),
      exclude_flagged_anomalies: Boolean(filters.excludeFlaggedAnomalies),
      preview_limit: 25,
    };

    try {
      const res = await flameApi.previewModelingData(payload);
      if (res.preview) {
        setPreviewData(res.preview);
      }
    } catch (err) {
      console.error('Preview generation failed:', err);
      setError('Data preview failed: ' + (err.message || 'Unknown error'));
    } finally {
      setIsLoadingPreview(false);
    }
  }, [activeDatasetId, selectedFeatures, selectedTargetId, filters]);

  // Re-fetch preview when variables change if prompt did not supply one
  useEffect(() => {
    if (!promptResponse) {
      fetchPreview();
    }
  }, [activeDatasetId, selectedFeatures, selectedTargetId, filters, fetchPreview]);

  // Feature selection handlers
  const handleToggleFeature = (featId) => {
    setSelectedFeatures((prev) =>
      prev.includes(featId) ? prev.filter((id) => id !== featId) : [...prev, featId]
    );
  };

  const handleSelectAllFeatures = () => {
    if (activeSchema?.available_features) {
      setSelectedFeatures(activeSchema.available_features.map((f) => f.id));
    }
  };

  const handleClearFeatures = () => {
    setSelectedFeatures([]);
  };

  const handleFilterChange = (field, val) => {
    setFilters((prev) => ({ ...prev, [field]: val }));
  };

  // Alternative target switch
  const handleSelectAlternativeTarget = (altId) => {
    setSelectedTargetId(altId);
    showNotification(`Switched target to verified metric: ${altId}`);
  };

  // 5. Real Backend Export Handler
  const handleExport = async (format) => {
    const dsId = activeDatasetId || promptResponse?.specialist_data?.recommended_dataset_id || 'bass_ii_experiments';
    if (!dsId) return;

    setIsExporting(true);
    setError(null);

    const payload = {
      dataset_id: dsId,
      format,
      selected_features: selectedFeatures.length > 0 ? selectedFeatures : null,
      target_id: selectedTargetId || null,
      material_filter: filters.materialFilter || null,
      min_oxygen: filters.minOxygen ?? null,
      max_oxygen: filters.maxOxygen ?? null,
      min_flow: filters.minFlow ?? null,
      max_flow: filters.maxFlow ?? null,
      start_time_s: filters.startTime ?? null,
      end_time_s: filters.endTime ?? null,
      complete_cases_only: Boolean(filters.completeCasesOnly),
      exclude_flagged_anomalies: Boolean(filters.excludeFlaggedAnomalies),
      max_rows: format === 'csv' ? 50000 : null,
    };

    try {
      const blob = await flameApi.exportModelingDataBlob(payload);
      const ext = format === 'csv' ? 'csv' : format === 'json' ? 'json' : 'md';
      const filename = `${dsId}_${selectedTargetId || 'features'}.${ext}`;

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      showNotification(`Successfully downloaded ${filename}`);
    } catch (err) {
      console.error(`Export failed for format ${format}:`, err);
      setError(`Export failed: ${err.message || 'Server error'}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleActionTriggered = (act) => {
    if (act.action === 'export_csv') {
      handleExport('csv');
    } else if (act.tab_id && onSelectTab) {
      onSelectTab(act.tab_id);
    }
  };

  return (
    <div className="max-w-6xl w-full mx-auto space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed top-24 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 shadow-lg flex items-center gap-2 animate-in fade-in duration-200">
          <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
          <span>{notification}</span>
        </div>
      )}

      {/* Page Title & Vision Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono uppercase tracking-wider bg-orange-50 text-orange-700 border border-orange-200 font-semibold">
                Phase F4 Analytical Engine
              </span>
              <span className="text-xs text-slate-500 font-mono">
                Predictive-Modeling Data Extraction
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
              Machine Learning Data Discovery & Preparation
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-3xl leading-relaxed">
              Extract traceable NASA microgravity combustion datasets for external predictive modeling.
              Evaluate target measurability, eliminate data leakage through group-aware splitting, and export clean experimental tables.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {onSelectTab && (
              <button
                type="button"
                onClick={() => onSelectTab('home')}
                className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 hover:text-slate-900 text-xs font-mono transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <span>💬 Ask AI Assistant</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button
            onClick={() => setError(null)}
            className="text-slate-500 hover:text-slate-800 text-xs px-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* 1. Unified Research Prompt Bar (Phase F4 Engine) */}
      <ResearchPromptBar
        initialWorkspace="modeling"
        handoffContext={initialContext}
        renderInlineResults={false}
        onResultReceived={handlePromptResult}
        onActionTriggered={handleActionTriggered}
        className="border-orange-200 shadow-sm"
      />

      {/* 2. Step 5 Data-Science Workspace Layout: Prompt Results Card */}
      {promptResponse && (
        <PromptModelingResultsCard
          promptResponse={promptResponse}
          onExport={handleExport}
          isExporting={isExporting}
        />
      )}

      {/* 3. Real Data Preview Table */}
      <DataPreviewTable
        previewData={previewData}
        isLoading={isLoadingPreview}
        selectedTargetId={selectedTargetId}
      />

      {/* 4. Data Quality & Leakage Audit Card */}
      <DataQualityAuditCard
        qualityReport={previewData?.quality_report}
      />

      {/* 5. Manual Configuration Toggle Bar (Collapsible for Clean Workflow) */}
      <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono">
        <span className="text-slate-800 font-semibold flex items-center gap-2">
          <span>🛠 Advanced Manual Configuration & Variable Selection</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-600">
            Dataset Selector, Feature Checkboxes, Target Switcher & Bounds
          </span>
        </span>
        <button
          onClick={() => setShowManualConfig(!showManualConfig)}
          className="text-xs text-orange-600 hover:text-orange-700 cursor-pointer font-semibold"
        >
          {showManualConfig ? 'Collapse Manual Controls ▲' : 'Expand Manual Controls ▼'}
        </button>
      </div>

      {/* 6. Existing Manual Controls & Export Controls (Preserved Completely) */}
      {showManualConfig && (
        <div className="space-y-6 animate-in fade-in duration-150">
          {/* Target Interpretation Banner */}
          <InterpretationBanner
            interpretation={interpretation}
            onSelectAlternativeTarget={handleSelectAlternativeTarget}
            activeTargetId={selectedTargetId}
          />

          {/* Dataset Discovery Cards */}
          <DatasetSelectorCards
            datasets={datasets}
            evaluations={interpretation?.dataset_evaluations || []}
            activeDatasetId={activeDatasetId}
            onSelectDataset={setActiveDatasetId}
          />

          {/* Feature, Target, and Condition Configuration */}
          <VariableSelectionPanel
            schema={activeSchema}
            selectedFeatures={selectedFeatures}
            onToggleFeature={handleToggleFeature}
            onSelectAllFeatures={handleSelectAllFeatures}
            onClearFeatures={handleClearFeatures}
            selectedTargetId={selectedTargetId}
            onSelectTarget={setSelectedTargetId}
            filters={filters}
            onFilterChange={handleFilterChange}
            onApplyFilters={fetchPreview}
            isLoading={isLoadingPreview}
          />

          {/* Standalone Export Center */}
          <ExportControls
            onExport={handleExport}
            isExporting={isExporting}
            datasetId={activeDatasetId}
            targetId={selectedTargetId}
            selectedFeatures={selectedFeatures}
            groupSplitCol={previewData?.quality_report?.group_split_column || 'run_id'}
          />
        </div>
      )}

      {/* Scientific Disclosures & Limitations Footer */}
      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 font-mono space-y-1">
        <p>
          <strong className="text-slate-800">NASA FLAME Scientific Grounding Disclosure:</strong> All exported records originate from verified NASA experimental archives (BASS-II MSG glovebox matrices and Saffire Cygnus telemetry). No synthetic data generation or silent imputation is performed.
        </p>
        <p>
          Sensor logs record thermal, gas, and radiometer readings. External video photogrammetry is required for flame front edge tracking. Do not infer flame spread rates without optical validation.
        </p>
      </div>
    </div>
  );
}

export default PredictiveModelingExtraction;
