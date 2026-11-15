import React from 'react';

/**
 * Reusable scientific status pill for validation, categories, and granularities
 */
export function StatusBadge({ type, value, size = 'sm' }) {
  if (!value) return null;

  const sizeClasses = {
    xs: 'text-[9px] px-1.5 py-0.5',
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
  };

  const currentSize = sizeClasses[size] || sizeClasses.sm;

  if (type === 'validation') {
    const isPending = String(value).toLowerCase() === 'pending';
    return (
      <span
        className={`inline-flex items-center gap-1 font-mono font-medium rounded border ${currentSize} ${
          isPending
            ? 'bg-amber-50 text-amber-800 border-amber-200'
            : 'bg-emerald-50 text-emerald-800 border-emerald-200'
        }`}
        title={
          isPending
            ? 'Scientific Validation: Pending Review (Extracted source data preserved without manual certification)'
            : 'Scientific Validation: Verified'
        }
      >
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            isPending ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'
          }`}
        />
        <span>Validation: {value}</span>
      </span>
    );
  }

  if (type === 'granularity') {
    const styles = {
      experiment: 'bg-purple-50 text-purple-800 border-purple-200',
      sensor_time_series: 'bg-cyan-50 text-cyan-800 border-cyan-200',
      telemetry_time_series: 'bg-sky-50 text-sky-800 border-sky-200',
    };

    const style = styles[value] || 'bg-slate-100 text-slate-700 border-slate-200';

    const labels = {
      experiment: 'Experiment Matrix',
      sensor_time_series: 'Sensor Time-Series',
      telemetry_time_series: 'Spacecraft Telemetry',
    };

    return (
      <span className={`inline-flex items-center font-mono rounded border ${currentSize} ${style}`}>
        {labels[value] || value}
      </span>
    );
  }

  if (type === 'category') {
    const isCombustion = value === 'combustion';
    return (
      <span
        className={`inline-flex items-center font-mono uppercase tracking-wider rounded border ${currentSize} ${
          isCombustion
            ? 'bg-orange-50 text-orange-800 border-orange-200'
            : 'bg-emerald-50 text-emerald-800 border-emerald-200'
        }`}
      >
        {isCombustion ? 'Combustion' : 'Telemetry'}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center font-mono rounded bg-slate-100 text-slate-700 border border-slate-200 ${currentSize}`}>
      {value}
    </span>
  );
}
