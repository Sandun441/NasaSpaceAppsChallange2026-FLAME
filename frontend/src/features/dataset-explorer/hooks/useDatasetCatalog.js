import { useState, useEffect, useCallback } from 'react';
import { flameApi } from '../../../services/flameApi';

/**
 * Hook to retrieve and filter the active scientific dataset catalog from FastAPI
 */
export function useDatasetCatalog(filters = {}) {
  const [datasets, setDatasets] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const category = filters.category;
  const granularity = filters.granularity;

  const fetchCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await flameApi.getDatasets({ category, granularity });
      setDatasets(result.datasets || []);
      setTotalCount(result.count || (result.datasets ? result.datasets.length : 0));
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch dataset catalog');
      setDatasets([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [category, granularity]);

  useEffect(() => {
    let ignore = false;

    flameApi.getDatasets({ category, granularity }).then(
      (result) => {
        if (!ignore) {
          setDatasets(result.datasets || []);
          setTotalCount(result.count || (result.datasets ? result.datasets.length : 0));
          setError(null);
          setLoading(false);
        }
      },
      (err) => {
        if (!ignore) {
          setError(err.message || 'Failed to fetch dataset catalog');
          setDatasets([]);
          setTotalCount(0);
          setLoading(false);
        }
      }
    );

    return () => {
      ignore = true;
    };
  }, [category, granularity]);

  return {
    datasets,
    totalCount,
    loading,
    error,
    refetch: fetchCatalog,
  };
}
