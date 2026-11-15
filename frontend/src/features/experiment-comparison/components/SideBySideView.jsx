import React from 'react';
import { TimeSeriesChart } from '../../dataset-explorer/components/visualization/TimeSeriesChart';

/**
 * SideBySideView
 * Renders independent interactive charts for Dataset A and Dataset B side-by-side.
 */
export function SideBySideView({
  datasetAId,
  datasetBId,
  recordsA = [],
  recordsB = [],
  timeAxisA = 'Elapsed Time (s)',
  timeAxisB = 'Elapsed Time (s)',
  activeChannelObj,
  enableDownsampling = true,
  offsetA = 0,
  offsetB = 0,
  totalRecordsA = 0,
  totalRecordsB = 0,
  windowLimit = 1000,
  onChangeOffsetA,
  onChangeOffsetB,
}) {
  if (!activeChannelObj) {
    return (
      <div className="p-8 text-center text-xs font-mono text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
        Select a shared measurement channel above to view side-by-side comparisons.
      </div>
    );
  }

  // Create isolated single-channel objects for A and B with distinct colors
  const channelA = {
    ...activeChannelObj,
    color: '#f97316', // Orange for A
  };

  const channelB = {
    ...activeChannelObj,
    color: '#0284c7', // Sky for B
  };

  const axisCompatA = { mode: 'single', leftUnit: activeChannelObj.unit };
  const axisCompatB = { mode: 'single', leftUnit: activeChannelObj.unit };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {/* Dataset A Chart */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 space-y-3 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
            <span className="text-xs font-mono font-semibold text-slate-900">
              Dataset A: {datasetAId}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            Window: {(offsetA + 1).toLocaleString()}–{Math.min(totalRecordsA, offsetA + recordsA.length).toLocaleString()} of {totalRecordsA.toLocaleString()}
          </span>
        </div>

        <TimeSeriesChart
          records={recordsA}
          timeAxis={timeAxisA}
          selectedChannels={[channelA]}
          axisCompatibility={axisCompatA}
          enableDownsampling={enableDownsampling}
        />

        {/* Dataset A Window Navigation */}
        <div className="flex items-center justify-between text-xs font-mono pt-1">
          <button
            onClick={() => onChangeOffsetA(Math.max(0, offsetA - windowLimit))}
            disabled={offsetA <= 0}
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 disabled:opacity-30 border border-slate-200 transition cursor-pointer text-[11px]"
          >
            ← Prev A Window
          </button>
          <span className="text-[10px] text-slate-500">
            {recordsA.length} samples loaded
          </span>
          <button
            onClick={() => onChangeOffsetA(offsetA + windowLimit)}
            disabled={offsetA + windowLimit >= totalRecordsA}
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 disabled:opacity-30 border border-slate-200 transition cursor-pointer text-[11px]"
          >
            Next A Window →
          </button>
        </div>
      </div>

      {/* Dataset B Chart */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 space-y-3 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
            <span className="text-xs font-mono font-semibold text-slate-900">
              Dataset B: {datasetBId}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            Window: {(offsetB + 1).toLocaleString()}–{Math.min(totalRecordsB, offsetB + recordsB.length).toLocaleString()} of {totalRecordsB.toLocaleString()}
          </span>
        </div>

        <TimeSeriesChart
          records={recordsB}
          timeAxis={timeAxisB}
          selectedChannels={[channelB]}
          axisCompatibility={axisCompatB}
          enableDownsampling={enableDownsampling}
        />

        {/* Dataset B Window Navigation */}
        <div className="flex items-center justify-between text-xs font-mono pt-1">
          <button
            onClick={() => onChangeOffsetB(Math.max(0, offsetB - windowLimit))}
            disabled={offsetB <= 0}
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 disabled:opacity-30 border border-slate-200 transition cursor-pointer text-[11px]"
          >
            ← Prev B Window
          </button>
          <span className="text-[10px] text-slate-500">
            {recordsB.length} samples loaded
          </span>
          <button
            onClick={() => onChangeOffsetB(offsetB + windowLimit)}
            disabled={offsetB + windowLimit >= totalRecordsB}
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 disabled:opacity-30 border border-slate-200 transition cursor-pointer text-[11px]"
          >
            Next B Window →
          </button>
        </div>
      </div>
    </div>
  );
}
