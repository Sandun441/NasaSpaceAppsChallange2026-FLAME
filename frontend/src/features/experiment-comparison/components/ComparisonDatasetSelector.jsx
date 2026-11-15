import React from 'react';

// Verified experimental provenance, fuel substrate materials, and sampling rates
const EXPERIMENT_SCIENTIFIC_PROVENANCE = {
  saffire_iii_sample_1: {
    material: 'SIBAL Cloth (75% Cotton / 25% Fiberglass)',
    flowCondition: 'Airflow ~0.4 m/s (concurrent flow)',
    atmosphere: 'Normal atmospheric O₂ (~21%), 1.0 atm',
    samplingRate: '~30.3 Hz',
  },
  saffire_iii_sample_2: {
    material: 'Nomex 7-oz Fabric (aromatic polyamide)',
    flowCondition: 'Airflow ~0.4 m/s (concurrent flow)',
    atmosphere: 'Normal atmospheric O₂ (~21%), 1.0 atm',
    samplingRate: '~30.3 Hz',
  },
  saffire_sample_5: {
    material: 'SIBAL Cloth (Cotton / Fiberglass blend)',
    flowCondition: 'Low airflow velocity (~0.2 m/s)',
    atmosphere: 'Oxygen-enriched microgravity test',
    samplingRate: '~30.3 Hz',
  },
  saffire_sample_6: {
    material: 'SIBAL Cloth (Cotton / Fiberglass blend)',
    flowCondition: 'High airflow velocity (~0.4 m/s)',
    atmosphere: 'Oxygen-enriched microgravity test',
    samplingRate: '~30.3 Hz',
  },
  telemetry_cygnus_data: {
    material: 'Cygnus PCM Vehicle Engineering Telemetry',
    flowCondition: 'Cabin ventilation loop',
    atmosphere: 'Pressurized Cargo Module interior',
    samplingRate: '~0.4 Hz',
  },
  telemetry_cygnus_smoke_detector_data: {
    material: 'FIZ 2 Optical Smoke Detection & Scatterometer',
    flowCondition: 'Cabin ventilation loop',
    atmosphere: 'Pressurized Cargo Module interior',
    samplingRate: '~0.4 Hz',
  },
  telemetry_cygnus_pressure_data: {
    material: 'PCM EPS Pressure Transducers',
    flowCondition: 'Hermetic cabin pressure monitoring',
    atmosphere: 'Pressurized Cargo Module interior',
    samplingRate: '~0.4 Hz',
  },
  telemetry_cygnus_temperature_data: {
    material: 'PCM Air Temperature RTD Suite',
    flowCondition: 'Cabin thermal management',
    atmosphere: 'Pressurized Cargo Module interior',
    samplingRate: '~0.4 Hz',
  },
  bass_ii_experiments: {
    material: '129 Discrete ISS Glovebox Burn Tests (PMMA, Cotton, Nomex)',
    flowCondition: 'Variable flow restrictors (Index 1, 2, 3)',
    atmosphere: 'ISS Glovebox chamber (16% to 23% O₂)',
    samplingRate: 'Discrete Matrix',
  },
};

/**
 * ComparisonDatasetSelector
 * Allows selecting Dataset A and Dataset B with scientific compatibility classification.
 */
export function ComparisonDatasetSelector({
  datasets = [],
  datasetAId,
  datasetBId,
  datasetAInfo,
  datasetBInfo,
  onSelectDatasetA,
  onSelectDatasetB,
}) {
  const provA = EXPERIMENT_SCIENTIFIC_PROVENANCE[datasetAId] || null;
  const provB = EXPERIMENT_SCIENTIFIC_PROVENANCE[datasetBId] || null;
  // Categorize datasets for clear grouping
  const saffireGroup = datasets.filter((d) => d.dataset_id.startsWith('saffire_'));
  const telemetryGroup = datasets.filter((d) => d.dataset_id.startsWith('telemetry_'));
  const bassGroup = datasets.filter((d) => d.dataset_id === 'bass_ii_experiments');

  // Evaluate cross-dataset compatibility
  const isSaffirePair = datasetAId.startsWith('saffire_') && datasetBId.startsWith('saffire_');
  const isTelemetryPair = datasetAId.startsWith('telemetry_') && datasetBId.startsWith('telemetry_');
  const isBassPair = datasetAId === 'bass_ii_experiments' && datasetBId === 'bass_ii_experiments';
  const isMismatch = (datasetAInfo?.granularity && datasetBInfo?.granularity && datasetAInfo.granularity !== datasetBInfo.granularity);

  const handleSwap = () => {
    onSelectDatasetA(datasetBId);
    onSelectDatasetB(datasetAId);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
            Experiment Comparison Pair
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            Dual-Dataset Scientific Analysis
          </span>
        </div>

        <button
          onClick={handleSwap}
          className="text-[11px] font-mono text-orange-600 hover:text-orange-700 transition flex items-center gap-1 cursor-pointer bg-slate-50 px-2 py-1 rounded border border-slate-200"
          title="Swap Dataset A and B"
        >
          <span>⇄ Swap (A ↔ B)</span>
        </button>
      </div>

      {/* Selectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
        {/* Dataset A */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold text-orange-600 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
              Dataset A (Primary)
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              {datasetAInfo?.granularity || 'loading...'}
            </span>
          </div>

          <select
            value={datasetAId}
            onChange={(e) => onSelectDatasetA(e.target.value)}
            className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-3 py-2 text-xs font-mono outline-none focus:border-orange-500 cursor-pointer"
          >
            <optgroup label="Saffire Combustion Sensor Series">
              {saffireGroup.map((d) => (
                <option key={`a-${d.dataset_id}`} value={d.dataset_id}>
                  {d.dataset_id} ({d.record_count.toLocaleString()} rows)
                </option>
              ))}
            </optgroup>
            <optgroup label="Cygnus Spacecraft Telemetry">
              {telemetryGroup.map((d) => (
                <option key={`a-${d.dataset_id}`} value={d.dataset_id}>
                  {d.dataset_id} ({d.record_count.toLocaleString()} rows)
                </option>
              ))}
            </optgroup>
            <optgroup label="BASS-II Glovebox Experiments">
              {bassGroup.map((d) => (
                <option key={`a-${d.dataset_id}`} value={d.dataset_id}>
                  {d.dataset_id} ({d.record_count} tests)
                </option>
              ))}
            </optgroup>
          </select>

          <div className="space-y-1 pt-1 border-t border-slate-200 text-[10px] font-mono">
            {provA && (
              <div className="flex flex-wrap gap-1.5 items-center">
                <span className="bg-orange-50 text-orange-700 px-1.5 py-0.5 rounded border border-orange-200 font-semibold">
                  Fuel: {provA.material}
                </span>
                <span className="bg-white text-slate-700 px-1.5 py-0.5 rounded border border-slate-200">
                  Rate: {provA.samplingRate}
                </span>
                <span className="bg-white text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
                  {provA.flowCondition}
                </span>
              </div>
            )}
            <p className="text-[11px] text-slate-500 truncate">
              Source: {datasetAInfo?.source_file || 'NASA Archive'}
            </p>
          </div>
        </div>

        {/* Dataset B */}
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold text-sky-600 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
              Dataset B (Comparison)
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              {datasetBInfo?.granularity || 'loading...'}
            </span>
          </div>

          <select
            value={datasetBId}
            onChange={(e) => onSelectDatasetB(e.target.value)}
            className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-3 py-2 text-xs font-mono outline-none focus:border-sky-500 cursor-pointer"
          >
            <optgroup label="Saffire Combustion Sensor Series">
              {saffireGroup.map((d) => (
                <option key={`b-${d.dataset_id}`} value={d.dataset_id}>
                  {d.dataset_id} ({d.record_count.toLocaleString()} rows)
                </option>
              ))}
            </optgroup>
            <optgroup label="Cygnus Spacecraft Telemetry">
              {telemetryGroup.map((d) => (
                <option key={`b-${d.dataset_id}`} value={d.dataset_id}>
                  {d.dataset_id} ({d.record_count.toLocaleString()} rows)
                </option>
              ))}
            </optgroup>
            <optgroup label="BASS-II Glovebox Experiments">
              {bassGroup.map((d) => (
                <option key={`b-${d.dataset_id}`} value={d.dataset_id}>
                  {d.dataset_id} ({d.record_count} tests)
                </option>
              ))}
            </optgroup>
          </select>

          <div className="space-y-1 pt-1 border-t border-slate-200 text-[10px] font-mono">
            {provB && (
              <div className="flex flex-wrap gap-1.5 items-center">
                <span className="bg-sky-50 text-sky-700 px-1.5 py-0.5 rounded border border-sky-200 font-semibold">
                  Fuel: {provB.material}
                </span>
                <span className="bg-white text-slate-700 px-1.5 py-0.5 rounded border border-slate-200">
                  Rate: {provB.samplingRate}
                </span>
                <span className="bg-white text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
                  {provB.flowCondition}
                </span>
              </div>
            )}
            <p className="text-[11px] text-slate-500 truncate">
              Source: {datasetBInfo?.source_file || 'NASA Archive'}
            </p>
          </div>
        </div>
      </div>

      {/* Scientific Compatibility Status Alert */}
      <div>
        {isSaffirePair && (
          <div className="flex items-center gap-2 text-xs font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-2 rounded-xl font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>
              High Compatibility: Saffire sensor pairs share identical sensor locations, physical units (°C, mw/cm², cm/sec, PSIA), and 30Hz sampling rates.
            </span>
          </div>
        )}

        {isTelemetryPair && (
          <div className="flex items-center gap-2 text-xs font-mono text-indigo-800 bg-indigo-50 border border-indigo-200 px-3 py-2 rounded-xl font-semibold">
            <span className="w-2 h-2 rounded-full bg-indigo-500" />
            <span>
              Telemetry Suite Compatibility: Cygnus vehicle telemetry records share the common Relative Time (s) axis.
            </span>
          </div>
        )}

        {isBassPair && (
          <div className="flex items-center gap-2 text-xs font-mono text-amber-800 bg-amber-50 border border-amber-200 px-3 py-2 rounded-xl font-semibold">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span>
              Discrete Experiment Matrix Mode: Comparing 129 discrete ISS microgravity burn runs across material fuels and oxygen levels.
            </span>
          </div>
        )}

        {isMismatch && (
          <div className="flex items-start gap-2 text-xs font-mono text-rose-800 bg-rose-50 border border-rose-200 p-3 rounded-xl font-semibold">
            <span className="text-base">⚠️</span>
            <div className="space-y-0.5">
              <span className="font-semibold">Scientific Safeguard: Investigation Granularity Mismatch</span>
              <p className="text-[11px] text-rose-700 leading-relaxed font-normal">
                Dataset A ({datasetAInfo?.granularity}) and Dataset B ({datasetBInfo?.granularity}) have incompatible data structures. A continuous sensor time-series cannot be mathematically compared directly against an experiment test matrix. Please select datasets from the same category.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
