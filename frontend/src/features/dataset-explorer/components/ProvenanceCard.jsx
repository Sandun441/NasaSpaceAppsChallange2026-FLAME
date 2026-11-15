import React from 'react';
import { StatusBadge } from '../../../components/common/StatusBadge';

export function ProvenanceCard({ datasetInfo, metadata }) {
  if (!datasetInfo) return null;

  return (
    <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-4 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-orange-500" />
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight font-mono">
              {datasetInfo.dataset_id}
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            NASA Flight Combustion Experiment & Telemetry Provenance
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge type="category" value={datasetInfo.category} size="sm" />
          <StatusBadge type="granularity" value={datasetInfo.granularity} size="sm" />
          <StatusBadge type="validation" value={datasetInfo.scientific_validation || 'pending'} size="sm" />
        </div>
      </div>

      {/* Provenance Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Source Flight File</span>
          <div className="font-mono text-slate-700 text-[11px] truncate" title={datasetInfo.source_file}>
            {datasetInfo.source_file || '—'}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Source Worksheet</span>
          <div className="font-mono text-slate-700 text-[11px] truncate" title={datasetInfo.source_worksheet}>
            {datasetInfo.source_worksheet || '—'}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Total Archived Records</span>
          <div className="font-mono text-emerald-600 font-bold text-sm">
            {datasetInfo.record_count?.toLocaleString()}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 block">Quality Report Reference</span>
          <div className="font-mono text-sky-600 text-[11px] truncate" title={datasetInfo.quality_report}>
            {datasetInfo.quality_report || '—'}
          </div>
        </div>
      </div>

      {/* SHA-256 and Extraction Specs (if available in metadata) */}
      {metadata?.source_sha256 && (
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate-500 truncate">
            <span className="text-slate-500 uppercase text-[10px]">Source SHA-256:</span>
            <span className="text-slate-700 text-[10.5px] truncate font-mono select-all">
              {metadata.source_sha256}
            </span>
          </div>
          <div className="text-[10px] text-slate-500 whitespace-nowrap">
            Header Row: {metadata.source_header_row} • Data Start Row: {metadata.source_data_start_row}
          </div>
        </div>
      )}

      {/* Scientific Notes & Warnings from Catalog */}
      {datasetInfo.notes && datasetInfo.notes.length > 0 && (
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
          <span className="text-[10px] font-mono uppercase text-amber-700 font-semibold block tracking-wider">
            NASA Flight Extraction & Data Notes
          </span>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-slate-700 text-[11.5px]">
            {datasetInfo.notes.map((note, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-600 font-mono">▸</span>
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Scientific Validation Integrity Banner */}
      <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-mono text-[10.5px] uppercase font-semibold text-amber-800">
          <span>⚠</span> Scientific Epistemic Guardrail — Provisional Flight Measurements
        </div>
        <p className="text-[11px] leading-relaxed text-slate-700">
          Measurements presented in this explorer reflect original sensor calibrations extracted from NASA flight archives. While structural and timestamp screenings were performed, scientific validation status is designated as <strong>pending</strong> until formal peer review and principal investigator certification are completed.
        </p>
      </div>
    </div>
  );
}
