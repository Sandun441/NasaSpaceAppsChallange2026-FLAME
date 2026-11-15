import { useState, useEffect, useMemo, useCallback } from 'react';
import { flameApi } from '../../../services/flameApi';
import { detectTimeAxis } from '../../dataset-explorer/utils/channelUnits';
import {
  detectIgnitionTimestamp,
  computeDescriptiveStatistics,
  computeComparisonMetrics,
  matchChannels,
} from '../utils/comparisonMath';

/**
 * Hook for managing two-dataset scientific comparison state,
 * channel matching, bounded window fetching, and descriptive metrics.
 */
export function useExperimentComparison(initialDatasetA = 'saffire_iii_sample_1', initialDatasetB = 'saffire_iii_sample_2') {
  const [datasetAId, setDatasetAId] = useState(initialDatasetA);
  const [datasetBId, setDatasetBId] = useState(initialDatasetB);

  // Metadata states
  const [datasetAInfo, setDatasetAInfo] = useState(null);
  const [datasetBInfo, setDatasetBInfo] = useState(null);
  const [metadataA, setMetadataA] = useState(null);
  const [metadataB, setMetadataB] = useState(null);

  // Records states
  const [recordsA, setRecordsA] = useState([]);
  const [recordsB, setRecordsB] = useState([]);
  const [columnsA, setColumnsA] = useState([]);
  const [columnsB, setColumnsB] = useState([]);
  const [totalRecordsA, setTotalRecordsA] = useState(0);
  const [totalRecordsB, setTotalRecordsB] = useState(0);

  const [loadingA, setLoadingA] = useState(false);
  const [loadingB, setLoadingB] = useState(false);
  const [errorA, setErrorA] = useState(null);
  const [errorB, setErrorB] = useState(null);

  // Windowing state
  const [offsetA, setOffsetA] = useState(0);
  const [offsetB, setOffsetB] = useState(0);
  const [windowLimit, setWindowLimit] = useState(1000);

  // User-selected comparison channel
  const [selectedChannelId, setSelectedChannelId] = useState(null);

  // Alignment mode: 'side_by_side' | 'overlay_recorded' | 'overlay_event_aligned'
  const [alignmentMode, setAlignmentMode] = useState('side_by_side');

  // Downsampling toggle
  const [enableDownsampling, setEnableDownsampling] = useState(true);

  // Detect time axes
  const timeAxisA = useMemo(() => detectTimeAxis(columnsA), [columnsA]);
  const timeAxisB = useMemo(() => detectTimeAxis(columnsB), [columnsB]);

  // Load Metadata for A
  useEffect(() => {
    let ignore = false;
    if (!datasetAId) return;

    flameApi.getMetadata(datasetAId).then(
      (res) => {
        if (!ignore) {
          setDatasetAInfo(res.dataset || null);
          setMetadataA(res.metadata || null);
        }
      },
      (err) => {
        if (!ignore) setErrorA(err.message || 'Failed to load metadata for Dataset A');
      }
    );

    return () => {
      ignore = true;
    };
  }, [datasetAId]);

  // Load Metadata for B
  useEffect(() => {
    let ignore = false;
    if (!datasetBId) return;

    flameApi.getMetadata(datasetBId).then(
      (res) => {
        if (!ignore) {
          setDatasetBInfo(res.dataset || null);
          setMetadataB(res.metadata || null);
        }
      },
      (err) => {
        if (!ignore) setErrorB(err.message || 'Failed to load metadata for Dataset B');
      }
    );

    return () => {
      ignore = true;
    };
  }, [datasetBId]);

  // Fetch Records for A
  useEffect(() => {
    let ignore = false;
    if (!datasetAId) return;

    flameApi
      .fetchRecordRange(datasetAId, { offset: offsetA, count: windowLimit })
      .then((res) => {
        if (!ignore) {
          setRecordsA(res.records || []);
          setColumnsA(res.columns || []);
          setTotalRecordsA(res.total_records || 0);
          setLoadingA(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          setErrorA(err.message || 'Failed to load records for Dataset A');
          setRecordsA([]);
          setLoadingA(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [datasetAId, offsetA, windowLimit]);

  // Fetch Records for B
  useEffect(() => {
    let ignore = false;
    if (!datasetBId) return;

    flameApi
      .fetchRecordRange(datasetBId, { offset: offsetB, count: windowLimit })
      .then((res) => {
        if (!ignore) {
          setRecordsB(res.records || []);
          setColumnsB(res.columns || []);
          setTotalRecordsB(res.total_records || 0);
          setLoadingB(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          setErrorB(err.message || 'Failed to load records for Dataset B');
          setRecordsB([]);
          setLoadingB(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [datasetBId, offsetB, windowLimit]);

  // Match shared channels between A and B
  const channelMatching = useMemo(() => {
    return matchChannels(columnsA, columnsB, metadataA, metadataB);
  }, [columnsA, columnsB, metadataA, metadataB]);

  // Active Channel derivation
  const effectiveChannelId = useMemo(() => {
    if (selectedChannelId && channelMatching.sharedChannels.some((c) => c.id === selectedChannelId)) {
      return selectedChannelId;
    }
    // Default to first compatible thermocouple or shared channel
    if (channelMatching.sharedChannels.length > 0) {
      const tc = channelMatching.sharedChannels.find((c) => c.category === 'temperature');
      return tc ? tc.id : channelMatching.sharedChannels[0].id;
    }
    return null;
  }, [selectedChannelId, channelMatching]);

  const activeChannelObj = useMemo(() => {
    return channelMatching.sharedChannels.find((c) => c.id === effectiveChannelId) || null;
  }, [channelMatching, effectiveChannelId]);

  // Detect verified ignition event timestamps
  const ignitionTimeA = useMemo(() => {
    return detectIgnitionTimestamp(recordsA, timeAxisA);
  }, [recordsA, timeAxisA]);

  const ignitionTimeB = useMemo(() => {
    return detectIgnitionTimestamp(recordsB, timeAxisB);
  }, [recordsB, timeAxisB]);

  const canEventAlign = ignitionTimeA !== null && ignitionTimeB !== null;

  // Compute real descriptive measurements
  const statsA = useMemo(() => {
    return computeDescriptiveStatistics(recordsA, effectiveChannelId, timeAxisA);
  }, [recordsA, effectiveChannelId, timeAxisA]);

  const statsB = useMemo(() => {
    return computeDescriptiveStatistics(recordsB, effectiveChannelId, timeAxisB);
  }, [recordsB, effectiveChannelId, timeAxisB]);

  const comparisonMetrics = useMemo(() => {
    return computeComparisonMetrics(statsA, statsB);
  }, [statsA, statsB]);

  // Switch Dataset A
  const selectDatasetA = useCallback((id) => {
    setLoadingA(true);
    setDatasetAId(id);
    setOffsetA(0);
  }, []);

  // Switch Dataset B
  const selectDatasetB = useCallback((id) => {
    setLoadingB(true);
    setDatasetBId(id);
    setOffsetB(0);
  }, []);

  // Window Offset changes
  const changeOffsetA = useCallback((newOffset) => {
    setLoadingA(true);
    setOffsetA(Math.max(0, newOffset));
  }, []);

  const changeOffsetB = useCallback((newOffset) => {
    setLoadingB(true);
    setOffsetB(Math.max(0, newOffset));
  }, []);

  const changeWindowLimit = useCallback((newLimit) => {
    setLoadingA(true);
    setLoadingB(true);
    setWindowLimit(newLimit);
  }, []);

  const refetchAll = useCallback(() => {
    setLoadingA(true);
    setLoadingB(true);
    flameApi.fetchRecordRange(datasetAId, { offset: offsetA, count: windowLimit }).then((res) => {
      setRecordsA(res.records || []);
      setLoadingA(false);
    });
    flameApi.fetchRecordRange(datasetBId, { offset: offsetB, count: windowLimit }).then((res) => {
      setRecordsB(res.records || []);
      setLoadingB(false);
    });
  }, [datasetAId, datasetBId, offsetA, offsetB, windowLimit]);

  return {
    datasetAId,
    datasetBId,
    datasetAInfo,
    datasetBInfo,
    metadataA,
    metadataB,
    recordsA,
    recordsB,
    columnsA,
    columnsB,
    totalRecordsA,
    totalRecordsB,
    loadingA,
    loadingB,
    loading: loadingA || loadingB,
    errorA,
    errorB,
    error: errorA || errorB,
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
  };
}
