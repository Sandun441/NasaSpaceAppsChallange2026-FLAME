import { useState, useEffect, useMemo, useCallback } from 'react';
import { flameApi } from '../../../services/flameApi';
import {
  detectTimeAxis,
  extractMeasurementChannels,
  evaluateAxisCompatibility,
} from '../utils/channelUnits';

/**
 * Dedicated hook for scientific visualization data loading, channel state,
 * axis compatibility management, and telemetry decimation.
 */
export function useVisualizationData(datasetId, datasetMetadata = null) {
  const [records, setRecords] = useState([]);
  const [columns, setColumns] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // View Mode: 'overview' (Full flight series with extrema-preserving decimation) vs 'window' (raw windowed buffer)
  const isExperimentGranularity = datasetMetadata?.granularity === 'experiment' || datasetId === 'bass_ii_experiments';
  const [viewMode, setViewMode] = useState(isExperimentGranularity ? 'window' : 'overview');

  // Windowing state for high-volume datasets
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(1000);

  // Decimation toggle (for client-side downsampling when in window mode)
  const [enableDownsampling, setEnableDownsampling] = useState(true);

  // Telemetry metadata
  const [dataQuality, setDataQuality] = useState(null);
  const [verifiedEvents, setVerifiedEvents] = useState([]);

  // User-configured channel selections per dataset
  const [userSelections, setUserSelections] = useState({});

  // Detect time/x-axis
  const timeAxis = useMemo(() => {
    return detectTimeAxis(columns);
  }, [columns]);

  // Extract all valid measurement channels
  const availableChannels = useMemo(() => {
    return extractMeasurementChannels(columns, datasetMetadata);
  }, [columns, datasetMetadata]);

  // Derive active selected channel IDs directly during render (prevents set-state-in-effect)
  const customIds = userSelections[datasetId] ?? null;

  const selectedChannelIds = useMemo(() => {
    if (customIds !== null) {
      return customIds;
    }
    if (availableChannels.length === 0) {
      return [];
    }

    // Heuristically pick 2-4 channels of the primary group (e.g. Plume thermocouples or pressure lines)
    const primaryCategory = availableChannels[0].category;
    const initialCandidates = availableChannels
      .filter((c) => c.category === primaryCategory)
      .slice(0, 4)
      .map((c) => c.id);

    return initialCandidates.length > 0 ? initialCandidates : [availableChannels[0].id];
  }, [customIds, availableChannels]);

  // Selected channel objects
  const selectedChannels = useMemo(() => {
    return availableChannels.filter((ch) => selectedChannelIds.includes(ch.id));
  }, [availableChannels, selectedChannelIds]);

  // Axis compatibility evaluation
  const axisCompatibility = useMemo(() => {
    return evaluateAxisCompatibility(selectedChannels);
  }, [selectedChannels]);

  // Master data fetching effect
  useEffect(() => {
    let ignore = false;
    if (!datasetId) return;

    setLoading(true);
    setError(null);

    const isExp = datasetMetadata?.granularity === 'experiment' || datasetId === 'bass_ii_experiments';

    if (isExp || viewMode === 'window') {
      // Windowed buffer mode (raw records)
      flameApi
        .fetchRecordRange(datasetId, { offset, count: limit })
        .then((result) => {
          if (!ignore) {
            setRecords(result.records || []);
            setColumns(result.columns || []);
            setTotalRecords(result.total_records || 0);
            setDataQuality(null);
            setLoading(false);
          }
        })
        .catch((err) => {
          if (!ignore) {
            setError(err.message || 'Failed to load records for visualization');
            setRecords([]);
            setLoading(false);
          }
        });
    } else {
      // Full Flight Overview mode: use high-performance telemetry endpoint
      flameApi
        .getTelemetry(datasetId, {
          channels: selectedChannelIds.length > 0 ? selectedChannelIds : undefined,
          downsamplePoints: 1000,
        })
        .then((res) => {
          if (!ignore) {
            const timeCol = res.time_channel || 'Elapsed Time (s)';
            const normalizedTelemetry = (res.telemetry || []).map((pt) => {
              const rawT = pt[timeCol] !== undefined ? pt[timeCol] : pt['time'];
              return {
                ...pt,
                time: rawT,
                [timeCol]: rawT,
              };
            });
            setRecords(normalizedTelemetry);
            setDataQuality(res.data_quality || null);
            setVerifiedEvents(res.verified_events || []);
            setTotalRecords(res.data_quality?.total_dataset_samples || 0);

            // Populate columns if not yet set
            setColumns((prevCols) => {
              if (prevCols.length > 0) return prevCols;
              const detected = [res.time_channel, ...(res.channels || [])];
              flameApi
                .getRecords(datasetId, { offset: 0, limit: 1 })
                .then((rec) => {
                  if (rec.columns) setColumns(rec.columns);
                })
                .catch(() => {});
              return detected;
            });
            setLoading(false);
          }
        })
        .catch(() => {
          // Fallback to fetchRecordRange if telemetry endpoint fails or is unsupported
          if (!ignore) {
            flameApi
              .fetchRecordRange(datasetId, { offset: 0, count: 1000 })
              .then((result) => {
                if (!ignore) {
                  setRecords(result.records || []);
                  setColumns(result.columns || []);
                  setTotalRecords(result.total_records || 0);
                  setLoading(false);
                }
              })
              .catch((err) => {
                if (!ignore) {
                  setError(err.message || 'Failed to load visualization data');
                  setLoading(false);
                }
              });
          }
        });
    }

    return () => {
      ignore = true;
    };
  }, [datasetId, viewMode, offset, limit, selectedChannelIds, datasetMetadata?.granularity]);

  // Channel toggling actions
  const toggleChannel = useCallback((channelId) => {
    setUserSelections((prev) => {
      const current = prev[datasetId] ?? selectedChannelIds;
      const next = current.includes(channelId)
        ? current.filter((id) => id !== channelId)
        : [...current, channelId];
      return { ...prev, [datasetId]: next };
    });
  }, [datasetId, selectedChannelIds]);

  const selectPreset = useCallback((channelIds) => {
    setUserSelections((prev) => ({ ...prev, [datasetId]: channelIds }));
  }, [datasetId]);

  const clearSelection = useCallback(() => {
    setUserSelections((prev) => ({ ...prev, [datasetId]: [] }));
  }, [datasetId]);

  const selectAllInCategory = useCallback((category) => {
    const categoryIds = availableChannels
      .filter((c) => c.category === category)
      .map((c) => c.id);
    setUserSelections((prev) => ({ ...prev, [datasetId]: categoryIds }));
  }, [datasetId, availableChannels]);

  // Window change helpers
  const changeOffset = useCallback((newOffset) => {
    setLoading(true);
    setOffset(Math.max(0, newOffset));
  }, []);

  const changeLimit = useCallback((newLimit) => {
    setLoading(true);
    setLimit(newLimit);
  }, []);

  return {
    records,
    columns,
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
    selectPreset,
    clearSelection,
    selectAllInCategory,
    changeOffset,
    changeLimit,
    refetch: () => {
      setLoading(true);
      // Trigger re-render
      setUserSelections((prev) => ({ ...prev }));
    },
  };
}
