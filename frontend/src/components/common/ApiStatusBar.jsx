import React from 'react';

/**
 * Visual indicator of live FastAPI backend connectivity
 */
export function ApiStatusBar({
  status,
  datasetCount,
  validationStatus,
  error,
  isRetrying,
  onRetry,
  compact = false,
  className = '',
}) {
  const isConnected = status === 'connected';
  const isConnecting = status === 'connecting';
  const isDisconnected = status === 'disconnected';

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-lg border text-xs font-mono ${
        isConnected
          ? 'bg-slate-50 border-slate-200 text-slate-700'
          : isConnecting
          ? 'bg-amber-50 border-amber-200 text-amber-800'
          : 'bg-rose-50 border-rose-200 text-rose-800'
      } ${className}`}>
        <span
          className={`w-2 h-2 rounded-full ${
            isConnected
              ? 'bg-emerald-500 animate-pulse'
              : isConnecting
              ? 'bg-amber-500 animate-ping'
              : 'bg-rose-500'
          }`}
        />
        <span>
          {isConnected && `API Live • ${datasetCount ?? 0} Datasets`}
          {isConnecting && 'Connecting to API...'}
          {isDisconnected && 'API Offline'}
        </span>

        {isDisconnected && onRetry && (
          <button
            onClick={onRetry}
            disabled={isRetrying}
            className="text-[10px] text-orange-600 hover:text-orange-700 underline font-mono cursor-pointer ml-1"
            title="Retry connecting to FastAPI"
          >
            {isRetrying ? 'Retrying...' : 'Retry'}
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono transition-all duration-200 ${
        isConnected
          ? 'bg-slate-50 border-slate-200 text-slate-700'
          : isConnecting
          ? 'bg-amber-50 border-amber-200 text-amber-800'
          : 'bg-rose-50 border-rose-200 text-rose-800'
      } ${className}`}
    >
      <div className="flex items-center gap-2.5">
        <span
          className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
            isConnected
              ? 'bg-emerald-500 shadow-xs'
              : isConnecting
              ? 'bg-amber-500 animate-ping'
              : 'bg-rose-500 shadow-xs'
          }`}
        />
        <div className="space-y-0.5">
          <div className="flex items-center gap-2 font-semibold text-slate-900">
            <span>
              {isConnected && 'FastAPI Backend Connected'}
              {isConnecting && 'Connecting to NASA FLAME API...'}
              {isDisconnected && 'Backend Disconnected (Offline)'}
            </span>
            {isConnected && validationStatus && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-50 text-amber-800 border border-amber-200">
                Validation: {validationStatus}
              </span>
            )}
          </div>
          <div className="text-[11px] text-slate-500">
            {isConnected && (
              <span>Target: http://127.0.0.1:8000 • Serving {datasetCount ?? 0} registered scientific flight datasets</span>
            )}
            {isConnecting && <span>Querying health status at http://127.0.0.1:8000/api/health...</span>}
            {isDisconnected && (
              <span className="text-rose-700">
                {error || 'Cannot reach FastAPI at http://127.0.0.1:8000. Run "python -m uvicorn api.main:app --port 8000" in data-pipeline/'}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 self-start sm:self-auto">
        {onRetry && (
          <button
            onClick={onRetry}
            disabled={isRetrying}
            className="px-3 py-1 rounded-lg bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <span>{isRetrying ? 'Checking...' : 'Refresh Status'}</span>
            <span className="text-[10px]">↺</span>
          </button>
        )}
      </div>
    </div>
  );
}
