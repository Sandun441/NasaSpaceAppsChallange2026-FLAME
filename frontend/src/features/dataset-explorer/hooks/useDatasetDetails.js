import { useState, useEffect, useCallback } from 'react';
import { flameApi } from '../../../services/flameApi';

/**
 * Hook to manage detailed metadata and server-side paginated records for a selected dataset
 */
export function useDatasetDetails(datasetId, initialLimit = 50) {
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [records, setRecords] = useState([]);
  const [columns, setColumns] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(initialLimit);
  const [hasMore, setHasMore] = useState(false);
  const [scientificValidation, setScientificValidation] = useState('pending');

  const [loadingMetadata, setLoadingMetadata] = useState(false);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [error, setError] = useState(null);

  // Fetch metadata when datasetId changes
  useEffect(() => {
    let ignore = false;

    if (datasetId) {
      flameApi.getMetadata(datasetId).then(
        (result) => {
          if (!ignore) {
            setDatasetInfo(result.dataset || null);
            setMetadata(result.metadata || null);
            if (result.dataset?.scientific_validation) {
              setScientificValidation(result.dataset.scientific_validation);
            }
            setLoadingMetadata(false);
          }
        },
        (err) => {
          if (!ignore) {
            setError(err.message || 'Failed to load dataset metadata');
            setLoadingMetadata(false);
          }
        }
      );
    }

    return () => {
      ignore = true;
    };
  }, [datasetId]);

  // Fetch paginated records when datasetId, offset, or limit change
  const fetchRecords = useCallback(async () => {
    if (!datasetId) return;

    setLoadingRecords(true);
    try {
      const result = await flameApi.getRecords(datasetId, { offset, limit });
      setRecords(result.records || []);
      setColumns(result.columns || []);
      setTotalRecords(result.total_records || 0);
      setHasMore(Boolean(result.has_more));
      if (result.scientific_validation) {
        setScientificValidation(result.scientific_validation);
      }
    } catch (err) {
      setError(err.message || 'Failed to load dataset records');
      setRecords([]);
    } finally {
      setLoadingRecords(false);
    }
  }, [datasetId, offset, limit]);

  useEffect(() => {
    let ignore = false;

    if (!datasetId) return;

    flameApi.getRecords(datasetId, { offset, limit }).then(
      (result) => {
        if (!ignore) {
          setRecords(result.records || []);
          setColumns(result.columns || []);
          setTotalRecords(result.total_records || 0);
          setHasMore(Boolean(result.has_more));
          if (result.scientific_validation) {
            setScientificValidation(result.scientific_validation);
          }
          setLoadingRecords(false);
        }
      },
      (err) => {
        if (!ignore) {
          setError(err.message || 'Failed to load dataset records');
          setRecords([]);
          setLoadingRecords(false);
        }
      }
    );

    return () => {
      ignore = true;
    };
  }, [datasetId, offset, limit]);

  // Pagination navigation helpers
  const goToPage = useCallback((page) => {
    const newOffset = Math.max(0, (page - 1) * limit);
    setOffset(newOffset);
  }, [limit]);

  const nextPage = useCallback(() => {
    if (offset + limit < totalRecords) {
      setOffset((prev) => prev + limit);
    }
  }, [offset, limit, totalRecords]);

  const prevPage = useCallback(() => {
    setOffset((prev) => Math.max(0, prev - limit));
  }, [limit]);

  const changeLimit = useCallback((newLimit) => {
    setLimit(newLimit);
    setOffset(0); // Reset to first page
  }, []);

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(totalRecords / limit));

  return {
    datasetInfo,
    metadata,
    records,
    columns,
    totalRecords,
    offset,
    limit,
    hasMore,
    scientificValidation,
    loadingMetadata,
    loadingRecords,
    isLoading: loadingMetadata || loadingRecords,
    error,
    currentPage,
    totalPages,
    goToPage,
    nextPage,
    prevPage,
    changeLimit,
    refetchRecords: fetchRecords,
  };
}
