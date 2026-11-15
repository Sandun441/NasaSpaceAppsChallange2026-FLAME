import React, { useState, useMemo } from 'react';

/**
 * BassComparisonView
 * Dedicated scientific comparison workspace for discrete BASS-II microgravity burn runs.
 * Compares two distinct ISS MSG glovebox tests across fuel materials, flow restrictors, and gas metrics.
 */
export function BassComparisonView({ records = [] }) {
  const [testAIndex, setTestAIndex] = useState(0); // Test B1
  const [testBIndex, setTestBIndex] = useState(1); // Test B2

  const testA = records[testAIndex] || null;
  const testB = records[testBIndex] || null;

  // Extract numerical parameters for Test A
  const paramsA = useMemo(() => {
    if (!testA) return null;
    const initO2 = parseFloat(testA['calibrated  initial O2 % by vol ']) || 0;
    const finalO2 = parseFloat(testA['calibrated final O2 % by vol']) || 0;
    const initCO2 = parseFloat(testA['Initial CO2 % by vol']) || 0;
    const finalCO2 = parseFloat(testA['Final CO2 % by vol']) || 0;
    const initCO = parseFloat(testA['Initial CO (ppm)']) || 0;
    const finalCO = parseFloat(testA['Final CO (ppm)']) || 0;
    const frames = parseFloat(testA['total frames shot']) || 0;

    return {
      testNo: testA['Test no.'] || 'Test A',
      material: testA.Material || 'Unspecified',
      flowRestrictor: testA['Flow restrictor'] || 'N/A',
      initO2,
      finalO2,
      deltaO2: initO2 - finalO2,
      initCO2,
      finalCO2,
      deltaCO2: finalCO2 - initCO2,
      initCO,
      finalCO,
      deltaCO: finalCO - initCO,
      frames,
    };
  }, [testA]);

  // Extract numerical parameters for Test B
  const paramsB = useMemo(() => {
    if (!testB) return null;
    const initO2 = parseFloat(testB['calibrated  initial O2 % by vol ']) || 0;
    const finalO2 = parseFloat(testB['calibrated final O2 % by vol']) || 0;
    const initCO2 = parseFloat(testB['Initial CO2 % by vol']) || 0;
    const finalCO2 = parseFloat(testB['Final CO2 % by vol']) || 0;
    const initCO = parseFloat(testB['Initial CO (ppm)']) || 0;
    const finalCO = parseFloat(testB['Final CO (ppm)']) || 0;
    const frames = parseFloat(testB['total frames shot']) || 0;

    return {
      testNo: testB['Test no.'] || 'Test B',
      material: testB.Material || 'Unspecified',
      flowRestrictor: testB['Flow restrictor'] || 'N/A',
      initO2,
      finalO2,
      deltaO2: initO2 - finalO2,
      initCO2,
      finalCO2,
      deltaCO2: finalCO2 - initCO2,
      initCO,
      finalCO,
      deltaCO: finalCO - initCO,
      frames,
    };
  }, [testB]);

  if (!paramsA || !paramsB) {
    return (
      <div className="p-8 text-center text-xs font-mono text-slate-500 bg-white rounded-2xl border border-slate-200 shadow-sm">
        Loading BASS-II experiment records...
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      {/* Investigation Notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs font-mono text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-semibold text-amber-800">
          <span>🔬</span>
          <span>BASS-II Discrete Experiment Comparison Matrix</span>
        </div>
        <p className="text-[11px] text-slate-700 leading-relaxed">
          Comparing discrete microgravity solid fuel burn tests conducted inside the Microgravity Science Glovebox (MSG) on the International Space Station.
        </p>
      </div>

      {/* Test Run Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Test Run A */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono font-semibold text-orange-600">
            <span>Test Run A</span>
            <span className="text-[10px] text-slate-500 font-normal">
              Row {(testAIndex + 1)} of {records.length}
            </span>
          </div>

          <select
            value={testAIndex}
            onChange={(e) => setTestAIndex(Number(e.target.value))}
            className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-3 py-2 text-xs font-mono outline-none focus:border-orange-500 cursor-pointer"
          >
            {records.map((r, idx) => (
              <option key={`opt-a-${idx}`} value={idx}>
                {r['Test no.']} — {r.Material ? r.Material.slice(0, 38) : 'Unknown'}
              </option>
            ))}
          </select>

          <div className="text-[11px] font-mono text-slate-700 space-y-0.5 pt-1">
            <p><strong>Material:</strong> {paramsA.material}</p>
            <p><strong>Flow Restrictor:</strong> {paramsA.flowRestrictor}</p>
          </div>
        </div>

        {/* Test Run B */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono font-semibold text-sky-600">
            <span>Test Run B</span>
            <span className="text-[10px] text-slate-500 font-normal">
              Row {(testBIndex + 1)} of {records.length}
            </span>
          </div>

          <select
            value={testBIndex}
            onChange={(e) => setTestBIndex(Number(e.target.value))}
            className="w-full bg-white border border-slate-200 text-slate-800 rounded-lg px-3 py-2 text-xs font-mono outline-none focus:border-sky-500 cursor-pointer"
          >
            {records.map((r, idx) => (
              <option key={`opt-b-${idx}`} value={idx}>
                {r['Test no.']} — {r.Material ? r.Material.slice(0, 38) : 'Unknown'}
              </option>
            ))}
          </select>

          <div className="text-[11px] font-mono text-slate-700 space-y-0.5 pt-1">
            <p><strong>Material:</strong> {paramsB.material}</p>
            <p><strong>Flow Restrictor:</strong> {paramsB.flowRestrictor}</p>
          </div>
        </div>
      </div>

      {/* Numerical Parameter Comparison Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
        {/* Metric 1: Net Oxygen Consumed */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-sm">
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">
            Net O₂ Consumed (Initial − Final)
          </span>
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-bold text-orange-600">{paramsA.deltaO2.toFixed(2)} %</span>
            <span className="text-slate-400">vs</span>
            <span className="text-sm font-bold text-sky-600">{paramsB.deltaO2.toFixed(2)} %</span>
          </div>
          <div className="text-[10px] text-slate-500 border-t border-slate-200 pt-1 flex justify-between">
            <span>Delta (A − B):</span>
            <span className="text-slate-900 font-bold">
              {(paramsA.deltaO2 - paramsB.deltaO2 > 0 ? '+' : '')}
              {(paramsA.deltaO2 - paramsB.deltaO2).toFixed(2)} %
            </span>
          </div>
        </div>

        {/* Metric 2: Net CO2 Produced */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-sm">
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">
            Net CO₂ Evolved (Final − Initial)
          </span>
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-bold text-orange-600">{paramsA.deltaCO2.toFixed(2)} %</span>
            <span className="text-slate-400">vs</span>
            <span className="text-sm font-bold text-sky-600">{paramsB.deltaCO2.toFixed(2)} %</span>
          </div>
          <div className="text-[10px] text-slate-500 border-t border-slate-200 pt-1 flex justify-between">
            <span>Delta (A − B):</span>
            <span className="text-slate-900 font-bold">
              {(paramsA.deltaCO2 - paramsB.deltaCO2 > 0 ? '+' : '')}
              {(paramsA.deltaCO2 - paramsB.deltaCO2).toFixed(2)} %
            </span>
          </div>
        </div>

        {/* Metric 3: Net Carbon Monoxide Generated */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-sm">
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">
            Net CO Generated (ppm)
          </span>
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-bold text-orange-600">{paramsA.deltaCO.toFixed(0)} ppm</span>
            <span className="text-slate-400">vs</span>
            <span className="text-sm font-bold text-sky-600">{paramsB.deltaCO.toFixed(0)} ppm</span>
          </div>
          <div className="text-[10px] text-slate-500 border-t border-slate-200 pt-1 flex justify-between">
            <span>Delta (A − B):</span>
            <span className="text-slate-900 font-bold">
              {(paramsA.deltaCO - paramsB.deltaCO > 0 ? '+' : '')}
              {(paramsA.deltaCO - paramsB.deltaCO).toFixed(0)} ppm
            </span>
          </div>
        </div>

        {/* Metric 4: Video Frames Acquired */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-2 shadow-sm">
          <span className="text-[11px] text-slate-500 uppercase tracking-wider">
            High-Speed Video Frames
          </span>
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-bold text-orange-600">{paramsA.frames.toLocaleString()}</span>
            <span className="text-slate-400">vs</span>
            <span className="text-sm font-bold text-sky-600">{paramsB.frames.toLocaleString()}</span>
          </div>
          <div className="text-[10px] text-slate-500 border-t border-slate-200 pt-1 flex justify-between">
            <span>Difference:</span>
            <span className="text-slate-900 font-bold">
              {(paramsA.frames - paramsB.frames).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Detailed Parameter Comparison Table */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm font-mono text-xs space-y-3">
        <div className="border-b border-slate-200 pb-2 flex justify-between items-center">
          <span className="font-semibold text-slate-900">Full Parameter Comparison Matrix</span>
          <span className="text-[10px] text-slate-500">BASS-II Glovebox Experiments</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-slate-700">
            <thead>
              <tr className="border-b border-slate-200 text-[10px] text-slate-500 uppercase tracking-wider">
                <th className="py-2 pr-4">Parameter</th>
                <th className="py-2 px-3 text-orange-600">Test {paramsA.testNo}</th>
                <th className="py-2 px-3 text-sky-600">Test {paramsB.testNo}</th>
                <th className="py-2 pl-3 text-right">Comparison Difference</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-[11px]">
              <tr className="hover:bg-slate-50">
                <td className="py-2 pr-4 text-slate-500">Fuel Material Substrate</td>
                <td className="py-2 px-3 text-slate-900 font-medium">{paramsA.material}</td>
                <td className="py-2 px-3 text-slate-900 font-medium">{paramsB.material}</td>
                <td className="py-2 pl-3 text-right text-slate-500">
                  {paramsA.material === paramsB.material ? 'Identical Material' : 'Different Substrates'}
                </td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2 pr-4 text-slate-500">Flow Restrictor Position</td>
                <td className="py-2 px-3 text-slate-900">{paramsA.flowRestrictor}</td>
                <td className="py-2 px-3 text-slate-900">{paramsB.flowRestrictor}</td>
                <td className="py-2 pl-3 text-right text-slate-500">
                  {paramsA.flowRestrictor === paramsB.flowRestrictor ? 'Matched Airflow' : 'Differing Airflow'}
                </td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2 pr-4 text-slate-500">Initial O₂ (% by vol)</td>
                <td className="py-2 px-3">{paramsA.initO2.toFixed(2)}%</td>
                <td className="py-2 px-3">{paramsB.initO2.toFixed(2)}%</td>
                <td className="py-2 pl-3 text-right text-slate-500">
                  {(paramsA.initO2 - paramsB.initO2).toFixed(2)}%
                </td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2 pr-4 text-slate-500">Final O₂ (% by vol)</td>
                <td className="py-2 px-3">{paramsA.finalO2.toFixed(2)}%</td>
                <td className="py-2 px-3">{paramsB.finalO2.toFixed(2)}%</td>
                <td className="py-2 pl-3 text-right text-slate-500">
                  {(paramsA.finalO2 - paramsB.finalO2).toFixed(2)}%
                </td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2 pr-4 text-slate-500">Initial CO₂ (% by vol)</td>
                <td className="py-2 px-3">{paramsA.initCO2.toFixed(2)}%</td>
                <td className="py-2 px-3">{paramsB.initCO2.toFixed(2)}%</td>
                <td className="py-2 pl-3 text-right text-slate-500">
                  {(paramsA.initCO2 - paramsB.initCO2).toFixed(2)}%
                </td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2 pr-4 text-slate-500">Final CO₂ (% by vol)</td>
                <td className="py-2 px-3">{paramsA.finalCO2.toFixed(2)}%</td>
                <td className="py-2 px-3">{paramsB.finalCO2.toFixed(2)}%</td>
                <td className="py-2 pl-3 text-right text-slate-500">
                  {(paramsA.finalCO2 - paramsB.finalCO2).toFixed(2)}%
                </td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2 pr-4 text-slate-500">Initial CO (ppm)</td>
                <td className="py-2 px-3">{paramsA.initCO.toFixed(0)} ppm</td>
                <td className="py-2 px-3">{paramsB.initCO.toFixed(0)} ppm</td>
                <td className="py-2 pl-3 text-right text-slate-500">
                  {(paramsA.initCO - paramsB.initCO).toFixed(0)} ppm
                </td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="py-2 pr-4 text-slate-500">Final CO (ppm)</td>
                <td className="py-2 px-3">{paramsA.finalCO.toFixed(0)} ppm</td>
                <td className="py-2 px-3">{paramsB.finalCO.toFixed(0)} ppm</td>
                <td className="py-2 pl-3 text-right text-slate-500">
                  {(paramsA.finalCO - paramsB.finalCO).toFixed(0)} ppm
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
