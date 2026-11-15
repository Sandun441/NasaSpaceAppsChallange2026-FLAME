import { useState, useEffect, useCallback } from 'react';
import { flameApi } from '../services/flameApi';

/**
 * useApiStatus hook
 * Manages live connection health, dataset counts, and validation status from FastAPI.
 */
export function useApiStatus(autoCheck = true) {
  const [status, setStatus] = useState('connecting'); // 'connecting' | 'connected' | 'disconnected'
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);

  const checkConnection = useCallback(async (isManualRetry = false) => {
    if (isManualRetry) {
      setIsRetrying(true);
      setStatus('connecting');
      setError(null);
    }

    try {
      const data = await flameApi.getHealth(5000);
      setHealth(data);
      setStatus('connected');
      setError(null);
      setLastChecked(new Date());
    } catch (err) {
      setStatus('disconnected');
      setHealth(null);
      setError(err.message || 'Unable to connect to NASA FLAME API');
      setLastChecked(new Date());
    } finally {
      if (isManualRetry) {
        setIsRetrying(false);
      }
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    if (autoCheck) {
      flameApi.getHealth(5000).then(
        (data) => {
          if (!ignore) {
            setHealth(data);
            setStatus('connected');
            setError(null);
            setLastChecked(new Date());
          }
        },
        (err) => {
          if (!ignore) {
            setStatus('disconnected');
            setHealth(null);
            setError(err.message || 'Unable to connect to NASA FLAME API');
            setLastChecked(new Date());
          }
        }
      );
    }

    return () => {
      ignore = true;
    };
  }, [autoCheck]);

  return {
    status,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    isDisconnected: status === 'disconnected',
    health,
    datasetCount: health?.dataset_count ?? null,
    validationStatus: health?.scientific_validation ?? null,
    error,
    lastChecked,
    isRetrying,
    checkConnection,
  };
}
