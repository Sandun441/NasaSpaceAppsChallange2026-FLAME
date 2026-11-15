import React, { useMemo, useState } from 'react';
import { flameApi } from '../../../services/flameApi';

const COLORS = [
  '#f97316', '#0284c7', '#059669',
  '#7c3aed', '#d97706', '#db2777'
];

const isObject = value =>
  value !== null && typeof value === 'object' && !Array.isArray(value);

const number = value => {
  if (value === null || value === undefined || value === '') return NaN;
  return Number(value);
};

function readable(value) {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (!value) return '';
  if (Array.isArray(value)) return value.map(readable).filter(Boolean).join(', ');
  if (isObject(value)) {
    const title = value.title || value.name || value.label || value.record_id || value.id;
    const reference = value.reference || value.source || value.url || value.path;
    if (title || reference) {
      return [title, reference].filter(Boolean).join(' — ');
    }
    return JSON.stringify(value);
  }
  return String(value);
}

function normalizeVisualization(spec) {
  const data = spec.series_data || spec.data || {};
  const curves = [];
  let categorical = null;
  let matrix = null;
  let scatter = null;
  let metadataOnly = false;

  const addCurve = (name, values) => {
    const clean = values
      .filter(p => Array.isArray(p) && p.length >= 2)
      .map(p => [number(p[0]), number(p[1])])
      .filter(p => p.every(Number.isFinite));

    if (clean.length > 1) {
      clean.sort((a, b) => a[0] - b[0]);
      curves.push({ name, values: clean });
    }
  };

  // Format 1: [{time: 0, channel: 20}, ...]
  const points = Array.isArray(data.points)
    ? data.points
    : Array.isArray(data.records)
      ? data.records
      : null;

  // Experiment-matrix scatter: two numeric axes and material categories.
  // Never connect discrete combustion tests as a time-series line.
  if (spec.chart_type === 'scatter' && points?.length) {
    const xKey = spec.x_variable;
    const yKey = spec.y_variable;
    if (xKey && yKey) {
      const valid = points.map((p, i) => ({
        x: number(p[xKey]),
        y: number(p[yKey]),
        group: readable(p.material_family || p.material || 'Unclassified'),
        id: readable(p.test_no || p.run_id || `Run ${i + 1}`),
        detail: readable(p.material || '')
      })).filter(p => Number.isFinite(p.x) && Number.isFinite(p.y));
      if (valid.length) scatter = valid;
    }
  }

  if (spec.chart_type !== 'scatter' && points?.length > 1 && isObject(points[0])) {
    const xKey = [
      spec.x_key, 'time', 'time_s', 'timestamp', 'elapsed_time', 'x'
    ].find(k => k && k in points[0]);

    if (xKey) {
      const channels = Array.isArray(spec.channel_ids) &&
        spec.channel_ids.length
        ? spec.channel_ids
        : Object.keys(points[0]).filter(k => k !== xKey);

      channels.forEach(channel => {
        addCurve(
          channel,
          points.map(p => [p[xKey], p[channel]])
        );
      });
    }
  }

  // Format 2: arrays such as exp1_time + exp1_radiometer_1,
  // exp2_time + exp2_radiometer_1, or time + temperature.
  if (isObject(data)) {
    const timeKeys = Object.keys(data).filter(k =>
      Array.isArray(data[k]) &&
      /(^time$|_time$|^time_|timestamp|time_s$)/i.test(k)
    );

    const used = new Set(curves.map(c => c.name));

    for (const key of Object.keys(data)) {
      const values = data[key];
      if (!Array.isArray(values) || values.length < 2) continue;
      if (timeKeys.includes(key) || key === 'points' || key === 'records') continue;
      if (used.has(key)) continue;
      if (!values.some(v => Number.isFinite(number(v)))) continue;

      let timeKey = null;

      // Pair exp1_... with exp1_time, exp2_... with exp2_time.
      const prefix = key.match(/^(exp\d+)_/i)?.[1];
      if (prefix && timeKeys.includes(`${prefix}_time`)) {
        timeKey = `${prefix}_time`;
      }

      // Support dataset_a_time and dataset_b_time.
      if (!timeKey) {
        timeKey = timeKeys.find(t => {
          const stem = t.replace(/_time$/, '');
          return stem && key.startsWith(stem + '_');
        });
      }

      if (!timeKey) timeKey = timeKeys.find(t => t === 'time');
      if (!timeKey && timeKeys.length === 1) timeKey = timeKeys[0];

      if (timeKey && data[timeKey].length === values.length) {
        addCurve(
          key,
          data[timeKey].map((x, i) => [x, values[i]])
        );
        used.add(key);
      }
    }

    // Format 3: series: [{name, data: [{x, y}, ...]}]
    const series = Array.isArray(data.series)
      ? data.series
      : Array.isArray(spec.series)
        ? spec.series
        : [];

    series.forEach((s, i) => {
      const values = s.data || s.points || s.values;
      if (!Array.isArray(values)) return;

      addCurve(
        s.name || s.label || `Series ${i + 1}`,
        values.map((p, j) => {
          if (Array.isArray(p)) return [p[0], p[1]];
          if (isObject(p)) {
            return [
              p.x ?? p.time ?? p.timestamp ?? j,
              p.y ?? p.value
            ];
          }
          return [j, p];
        })
      );
    });

    // Format 4: categorical data, including modeling feature-completeness
    // audits ({ features: [...], completeness_pct: [...] }).
    const isCompletenessAudit =
      Array.isArray(data.features) && Array.isArray(data.completeness_pct);
    const isCoverageAudit =
      Array.isArray(data.regimes) && Array.isArray(data.run_counts);

    const labels = isCompletenessAudit
      ? data.features
      : isCoverageAudit
        ? data.regimes
        : data.labels || data.categories || data.names;
    const rawValues = isCompletenessAudit
      ? data.completeness_pct
      : isCoverageAudit
        ? data.run_counts
        : data.values || data.counts || data.frequencies;

    if (Array.isArray(labels) && Array.isArray(rawValues)) {
      categorical = labels.map((label, i) => ({
        label: readable(label),
        value: number(rawValues[i])
      })).filter(row => Number.isFinite(row.value));
    }

    // Format 5: heatmap matrix supplied by the backend.
    const matrixData = data.matrix || data.grid;
    const rows = data.row_labels || data.rows;
    const columns = data.column_labels || data.columns;

    if (
      Array.isArray(matrixData) &&
      matrixData.length > 0 &&
      matrixData.every(Array.isArray)
    ) {
      matrix = {
        values: matrixData,
        rows: Array.isArray(rows) ? rows : [],
        columns: Array.isArray(columns) ? columns : []
      };
    }
  }

  // Format 6: direct array of categorical objects.
  if (!categorical) {
    const rows = Array.isArray(data)
      ? data
      : Array.isArray(data.items)
        ? data.items
        : null;

    if (rows?.length && rows.every(isObject)) {
      const normalized = rows.map(row => ({
        label: readable(
          row.label ?? row.category ?? row.name ?? row.regime
        ),
        value: number(
          row.value ?? row.count ?? row.frequency ?? row.total
        )
      })).filter(row => row.label && Number.isFinite(row.value));

      if (normalized.length) categorical = normalized;
    }
  }

  // Some equipment summaries provide only axis metadata and event markers,
  // not actual telemetry samples. Mark these honestly as unavailable.
  metadataOnly = spec.chart_type === 'multi_line' &&
    !curves.length && !categorical?.length && !matrix && !scatter;

  return { curves: curves.slice(0, 12), categorical, matrix, scatter, metadataOnly };
}

function LineChart({ curves, spec }) {
  const all = curves.flatMap(c => c.values);

  const xs = all.map(p => p[0]);
  const ys = all.map(p => p[1]);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const xScale = x =>
    60 + ((x - minX) / (maxX - minX || 1)) * 690;

  const yScale = y =>
    210 - ((y - minY) / (maxY - minY || 1)) * 170;

  const format = n => Number.isFinite(n)
    ? Number(n.toPrecision(5)).toString()
    : 'N/A';

  return (
    <div className="space-y-3">
      <svg
        viewBox="0 0 800 260"
        role="img"
        aria-label={spec.title || 'Scientific measurement chart'}
        className="w-full rounded-lg bg-white border border-slate-200"
      >
        {[0, 1, 2, 3, 4].map(i => {
          const y = 40 + i * 42.5;
          const value = maxY - (maxY - minY) * i / 4;

          return (
            <g key={i}>
              <line
                x1="60" x2="750" y1={y} y2={y}
                stroke="#e2e8f0" strokeDasharray="3 5"
              />
              <text
                x="54" y={y + 4} textAnchor="end"
                fill="#64748b" fontSize="11"
              >
                {format(value)}
              </text>
            </g>
          );
        })}

        <line x1="60" y1="210" x2="750" y2="210" stroke="#cbd5e1" />
        <line x1="60" y1="40" x2="60" y2="210" stroke="#cbd5e1" />

        {curves.map((curve, i) => (
          <polyline
            key={curve.name + i}
            fill="none"
            stroke={COLORS[i % COLORS.length]}
            strokeWidth="1.7"
            vectorEffect="non-scaling-stroke"
            strokeLinejoin="round"
            points={curve.values
              .map(([x, y]) => `${xScale(x)},${yScale(y)}`)
              .join(' ')}
          />
        ))}

        <text x="60" y="231" fill="#64748b" fontSize="11">
          {format(minX)}
        </text>
        <text
          x="750" y="231" textAnchor="end"
          fill="#64748b" fontSize="11"
        >
          {format(maxX)}
        </text>
        <text
          x="400" y="250" textAnchor="middle"
          fill="#475569" fontSize="11"
        >
          {spec.x_label || 'Time'} {spec.x_units ? `(${spec.x_units})` : ''}
        </text>
        <text x="62" y="24" fill="#475569" fontSize="11">
          {spec.y_label || 'Measurement'} {spec.y_units ? `(${spec.y_units})` : ''}
        </text>
      </svg>

      <div className="flex flex-wrap gap-3 text-[11px]">
        {curves.map((c, i) => (
          <span key={c.name + i} style={{ color: COLORS[i % COLORS.length] }}>
            ● {c.name}
          </span>
        ))}
      </div>
    </div>
  );
}

function CategoryChart({ rows, spec }) {
  if (!rows.length) return null;

  const max = Math.max(0, ...rows.map(r => r.value));
  const visible = rows.slice(0, 30);

  return (
    <div className="space-y-2">
      {visible.map((row, i) => (
        <div key={i} className="grid grid-cols-[minmax(0,1fr)_2fr_auto] items-center gap-3 text-xs">
          <span className="text-slate-700 break-words">{row.label}</span>
          <div className="h-4 bg-slate-100 rounded overflow-hidden">
            <div
              className="h-full bg-orange-500"
              style={{
                width: `${max > 0 ? Math.max(0, row.value / max) * 100 : 0}%`
              }}
            />
          </div>
          <span className="font-mono text-slate-800">
            {row.value.toLocaleString()}
          </span>
        </div>
      ))}
      {rows.length > visible.length && (
        <p className="text-xs text-slate-500">
          Showing {visible.length} of {rows.length} categories.
          Export JSON to inspect all values.
        </p>
      )}
      {spec.y_units && (
        <p className="text-xs text-slate-500">Units: {spec.y_units}</p>
      )}
    </div>
  );
}

function MatrixChart({ matrix }) {
  const finite = matrix.values.flat()
    .map(number)
    .filter(Number.isFinite);

  if (!finite.length) return null;

  const max = Math.max(...finite);
  const min = Math.min(...finite);

  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-collapse min-w-full">
        <thead>
          <tr>
            <th className="p-2 text-slate-500 text-left">Parameter</th>
            {matrix.values[0].map((_, j) => (
              <th key={j} className="p-2 text-slate-700">
                {readable(matrix.columns[j]) || `Column ${j + 1}`}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.values.map((row, i) => (
            <tr key={i}>
              <th className="p-2 text-left text-slate-700">
                {readable(matrix.rows[i]) || `Row ${i + 1}`}
              </th>
              {row.map((raw, j) => {
                const value = number(raw);
                const ratio = Number.isFinite(value)
                  ? (value - min) / (max - min || 1)
                  : 0;

                return (
                  <td
                    key={j}
                    className="p-2 text-center border border-slate-200 text-slate-800"
                    style={{
                      backgroundColor: Number.isFinite(value)
                        ? `rgba(249, 115, 22, ${0.08 + ratio * 0.45})`
                        : 'transparent'
                    }}
                  >
                    {Number.isFinite(value) ? value : 'N/A'}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScatterChart({ points, spec }) {
  const xs = points.map(p => p.x);
  const ys = points.map(p => p.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const xScale = x => 70 + (x - minX) / (maxX - minX || 1) * 670;
  const yScale = y => 226 - (y - minY) / (maxY - minY || 1) * 174;
  const groups = [...new Set(points.map(p => p.group))];
  const groupColor = g => COLORS[groups.indexOf(g) % COLORS.length];
  const format = n => Number(n.toPrecision(5)).toString();

  return (
    <div className="space-y-3">
      <svg viewBox="0 0 800 292" role="img"
        aria-label={spec.title || 'Experiment scatter chart'}
        className="w-full rounded-lg bg-white border border-slate-200">
        {[0, 1, 2, 3, 4].map(i => {
          const value = minY + (maxY - minY) * i / 4;
          const y = yScale(value);
          return <g key={i}>
            <line x1="70" x2="740" y1={y} y2={y} stroke="#e2e8f0" strokeDasharray="3 5" />
            <text x="60" y={y + 4} textAnchor="end" fill="#64748b" fontSize="11">{format(value)}</text>
          </g>;
        })}
        {[0, 1, 2, 3, 4].map(i => {
          const value = minX + (maxX - minX) * i / 4;
          const x = xScale(value);
          return <text key={i} x={x} y="244" textAnchor="middle" fill="#64748b" fontSize="11">{format(value)}</text>;
        })}
        <line x1="70" x2="740" y1="226" y2="226" stroke="#cbd5e1" />
        <line x1="70" x2="70" y1="52" y2="226" stroke="#cbd5e1" />
        {points.map((p, i) => <circle
          key={`${p.id}-${i}`} cx={xScale(p.x)} cy={yScale(p.y)} r="5"
          fill={groupColor(p.group)} fillOpacity="0.85" stroke="#ffffff" strokeWidth="1">
          <title>{`${p.id} — ${p.group}\n${p.detail}\n${spec.x_label || 'X'}: ${p.x}\n${spec.y_label || 'Y'}: ${p.y}`}</title>
        </circle>)}
        <text x="400" y="280" textAnchor="middle" fill="#475569" fontSize="11">
          {spec.x_label || spec.x_variable}{spec.x_units ? ` (${spec.x_units})` : ''}
        </text>
        <text x="72" y="27" fill="#475569" fontSize="11">
          {spec.y_label || spec.y_variable}{spec.y_units ? ` (${spec.y_units})` : ''}
        </text>
      </svg>
      <div className="flex flex-wrap gap-3 text-xs">
        {groups.map(g => <span key={g} style={{ color: groupColor(g) }}>● {g}</span>)}
      </div>
      <p className="text-xs text-slate-500">
        {points.length} plotted records from the backend chart sample. Hover over points for test IDs.
        These are discrete experimental runs, not continuous telemetry.
      </p>
    </div>
  );
}

function MissingTelemetryNotice({ spec }) {
  const events = Array.isArray(spec.event_markers) ? spec.event_markers : [];
  const notices = Array.isArray(spec.missing_data_notices) ? spec.missing_data_notices : [];
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3">
      <p className="text-xs text-amber-800">
        This tool returned chart metadata but no measurement samples (series_data is empty).
        A waveform cannot be plotted from this response without retrieving telemetry.
      </p>
      {events.length > 0 && <div className="space-y-2">
        <p className="text-xs font-semibold text-slate-800">Recorded event annotations (not a waveform)</p>
        {events.map((event, i) => (
          <div key={i} className="text-xs text-slate-700">
            <span className="font-mono text-sky-700">{event.time}s</span>{' — '}
            <strong>{event.label}</strong>
            {event.description && <p className="text-slate-500 mt-1">{event.description}</p>}
          </div>
        ))}
      </div>}
      {notices.map((note, i) => <p key={i} className="text-xs text-slate-500">{readable(note)}</p>)}
    </div>
  );
}

function ScientificChart({ spec }) {
  const { curves, categorical, matrix, scatter, metadataOnly } = useMemo(
    () => normalizeVisualization(spec),
    [spec]
  );

  if (scatter?.length) return <ScatterChart points={scatter} spec={spec} />;
  if (curves.length) return <LineChart curves={curves} spec={spec} />;
  if (categorical?.length) return <CategoryChart rows={categorical} spec={spec} />;
  if (matrix) return <MatrixChart matrix={matrix} />;
  if (metadataOnly) return <MissingTelemetryNotice spec={spec} />;

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2">
      <p className="text-xs text-amber-800">
        This visualization uses a specialist data format that cannot yet
        be displayed safely in the AI Assistant.
      </p>
      <p className="text-xs text-slate-500">
        The verified chart specification is preserved in the JSON export.
        No values have been estimated or invented for display.
      </p>
    </div>
  );
}

function ModelingDownloads({ result }) {
  const [activeExport, setActiveExport] = useState(null);
  const [exportError, setExportError] = useState('');

  const details = result.specialist_data || {};
  const preview = details.preview || {};
  const datasetId = details.recommended_dataset_id || preview.dataset_id;
  const schemaColumns = Array.isArray(preview.columns) ? preview.columns : [];
  const allowedIds = new Set(schemaColumns.map(column => column.id));
  const requestedFeatures = Array.isArray(details.selected_features)
    ? details.selected_features
    : [];
  // Use the exact selected features confirmed in the backend preview. If no
  // reliable selection is available, let the backend choose its documented defaults.
  const selectedFeatures = requestedFeatures.length && allowedIds.size
    ? requestedFeatures.filter(id => allowedIds.has(id))
    : requestedFeatures;
  const target = details.target_object || {};
  const targetId = target.status !== 'UNINSTRUMENTED_UNAVAILABLE' &&
    target.status !== 'NOT_SPECIFIED' && target.id && allowedIds.has(target.id)
    ? target.id : null;
  const unavailableTarget = target.status === 'UNINSTRUMENTED_UNAVAILABLE';

  const downloadExport = async (format) => {
    if (!datasetId || activeExport) return;
    setExportError('');
    setActiveExport(format);
    try {
      const payload = {
        dataset_id: datasetId,
        format,
        selected_features: selectedFeatures.length ? selectedFeatures : null,
        target_id: targetId,
        complete_cases_only: false,
        exclude_flagged_anomalies: false,
      };
      const blob = await flameApi.exportModelingDataBlob(payload);
      if (!blob.size) throw new Error('The backend returned an empty export.');
      const extension = format === 'report' ? 'md' : format;
      const suffix = format === 'csv' ? 'modeling_data' : format === 'json' ? 'metadata' : 'quality_report';
      const safeName = String(datasetId).replace(/[^a-z0-9_-]/gi, '_');
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${safeName}_${suffix}.${extension}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      setExportError(error?.message || 'Could not export modeling data.');
    } finally {
      setActiveExport(null);
    }
  };

  if (!datasetId) return (
    <p className="text-xs text-amber-800">A modeling dataset was not identified; export is unavailable for this response.</p>
  );

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 space-y-3">
      <h4 className="text-sm font-semibold text-slate-900">Download verified modeling data</h4>
      <p className="text-xs text-slate-600">
        Source: {datasetId}. Downloads use the backend extraction service, not the chart preview.
        Original missing readings and anomaly flags are retained where available.
      </p>
      {unavailableTarget && (
        <p className="text-xs text-amber-800">
          The requested prediction target is not measured in this dataset. Exports contain available inputs only; no target labels are invented.
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        {[
          ['csv', 'Download CSV dataset'],
          ['json', 'Download metadata JSON'],
          ['report', 'Download quality report'],
        ].map(([format, label]) => (
          <button
            key={format}
            type="button"
            disabled={activeExport !== null}
            onClick={() => downloadExport(format)}
            className="rounded-lg border border-sky-300 bg-white px-3 py-2 text-xs font-medium text-sky-800 hover:bg-sky-50 shadow-xs disabled:opacity-50 cursor-pointer"
          >
            {activeExport === format ? 'Preparing download…' : label}
          </button>
        ))}
      </div>
      {exportError && <p role="alert" className="text-xs text-rose-700">{exportError}</p>}
    </div>
  );
}

export function ExecutedToolResult({ result }) {
  if (!result) return null;

  const charts = Array.isArray(result.visualizations)
    ? result.visualizations
    : [];

  const findings = Array.isArray(result.key_findings)
    ? result.key_findings.map(readable).filter(Boolean)
    : [];

  const citations = Array.isArray(result.provenance_citations)
    ? result.provenance_citations.map(readable).filter(Boolean)
    : [];

  const caveats = Array.isArray(result.scientific_caveats)
    ? result.scientific_caveats.map(readable).filter(Boolean)
    : [];

  const download = () => {
    const blob = new Blob(
      [JSON.stringify(result, null, 2)],
      { type: 'application/json' }
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `flame-${result.workspace || 'research'}-result.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <section className="space-y-4 border-t border-slate-200 pt-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-orange-600 text-sm">
          Executed: {(result.workspace || 'research').replaceAll('_', ' ')}
        </h3>
        <button
          type="button"
          onClick={download}
          className="text-xs text-sky-700 hover:text-sky-800 underline cursor-pointer"
        >
          Export result JSON
        </button>
      </div>

      {result.workspace === 'modeling' && <ModelingDownloads result={result} />}

      {!!findings.length && (
        <details className="text-xs text-slate-700">
          <summary className="cursor-pointer font-medium">
            Verified research findings ({findings.length})
          </summary>
          <ul className="list-disc pl-5 space-y-2 mt-3">
            {findings.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        </details>
      )}

      {charts.map((chart, i) => (
        <div
          key={chart.chart_id || i}
          className="bg-white border border-slate-200 p-3 rounded-xl space-y-3 shadow-xs"
        >
          <h4 className="text-sm font-medium text-slate-900">
            {chart.title || `Scientific Chart ${i + 1}`}
          </h4>
          {chart.subtitle && (
            <p className="text-xs text-slate-500">{chart.subtitle}</p>
          )}
          <ScientificChart spec={chart} />
          {chart.provenance && (
            <p className="text-[10px] text-slate-500">
              Source: {readable(chart.provenance)}
            </p>
          )}
        </div>
      ))}

      {!!citations.length && (
        <details className="text-xs text-slate-700">
          <summary className="cursor-pointer">
            Scientific provenance ({citations.length})
          </summary>
          <ul className="mt-2 list-disc pl-5 space-y-1">
            {citations.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </details>
      )}

      {!!caveats.length && (
        <details className="text-xs text-amber-800">
          <summary className="cursor-pointer">
            Scientific limitations ({caveats.length})
          </summary>
          <ul className="mt-2 list-disc pl-5 space-y-1">
            {caveats.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </details>
      )}
    </section>
  );
}
