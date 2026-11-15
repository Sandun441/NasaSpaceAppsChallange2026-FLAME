import React, { useState, useMemo, useEffect, useRef } from 'react';
import { flameApi } from '../../services/flameApi';
import { ToolIcon } from './ToolIcon';

const WORKSPACE_EXAMPLES = {
  visualization: [
    {
      label: 'Sample 1 Multi-Channel Ignition',
      query: 'Visualize temperature, radiant heat flux, and airflow during Saffire-III Sample 1 ignition.',
      workspace: 'visualization',
    },
    {
      label: 'Radiant Heat Flux (Radiometer 1)',
      query: 'Plot Saffire-III Sample 1 radiant heat flux over full flight duration.',
      workspace: 'visualization',
    },
    {
      label: 'Plume Thermocouples (TC1-TC3)',
      query: 'Show thermocouple temperatures during Saffire-III Sample 1 ignition and spread.',
      workspace: 'visualization',
    },
    {
      label: 'Duct Inlet Flow & Temperature',
      query: 'Visualize airflow velocity and inlet temperature for Saffire-III Sample 1.',
      workspace: 'visualization',
    },
  ],
  comparison: [
    {
      label: 'Sample 1 vs Sample 2 (Heat Flux & Temp)',
      query: 'Compare the radiant heat flux and temperature measurements from Saffire-III Sample 1 and Sample 2.',
      workspace: 'comparison',
    },
    {
      label: 'BASS-II Glovebox Matrix',
      query: 'Compare BASS-II Cotton vs PMMA glovebox burn matrix.',
      workspace: 'comparison',
    },
    {
      label: 'Plume Exhaust Heating Comparison',
      query: 'Compare plume thermocouple response between Saffire-III Sample 1 and Sample 2.',
      workspace: 'comparison',
    },
    {
      label: 'Airflow Velocity Comparison',
      query: 'Compare duct airflow velocity between Saffire-III Sample 1 and Sample 2.',
      workspace: 'comparison',
    },
  ],
  modeling: [
    {
      label: 'BASS-II Flame Behavior (ML)',
      query: 'Prepare BASS-II experimental data to study flame behavior using oxygen concentration, material, and airflow.',
      workspace: 'modeling',
    },
    {
      label: 'Saffire-III Feature Extraction',
      query: 'Extract Saffire-III Sample 1 radiant heat flux and temperature features for ML modeling.',
      workspace: 'modeling',
    },
    {
      label: 'Predict Burn Duration',
      query: 'Prepare BASS-II data for predicting burn duration from initial oxygen and forced airflow.',
      workspace: 'modeling',
    },
    {
      label: 'Flame Spread Rate Feasibility',
      query: 'Evaluate flame spread rate prediction feasibility using Saffire telemetry.',
      workspace: 'modeling',
    },
  ],
  gap_detection: [
    {
      label: 'Low-O2 & Low-Flow Gaps',
      query: 'Find missing experimental coverage for low oxygen concentrations and low airflow in microgravity combustion.',
      workspace: 'gap_detection',
    },
    {
      label: 'Lunar & Martian Partial Gravity',
      query: 'What empirical combustion tests exist for lunar (0.16g) or Martian (0.38g) partial gravity?',
      workspace: 'gap_detection',
    },
    {
      label: 'Quiescent Smothering Limit',
      query: 'Can a solid fuel flame sustain in microgravity under complete zero-velocity quiescent airflow?',
      workspace: 'gap_detection',
    },
    {
      label: 'Carbon Monoxide Sensor Gap',
      query: 'Are direct carbon monoxide gas emissions recorded during Saffire-III flight burns?',
      workspace: 'gap_detection',
    },
  ],
  equipment: [
    {
      label: 'Spacecraft Smoke Detection',
      query: 'What NASA findings could help researchers improve spacecraft smoke detection?',
      workspace: 'equipment',
    },
    {
      label: 'Radiant Heat vs Plume Delay',
      query: 'How do Saffire broadband radiometers detect early ignition compared to plume thermocouples?',
      workspace: 'equipment',
    },
    {
      label: 'Low-Flow Fire Extinction',
      query: 'What microgravity evidence informs fire extinction limits in low-flow vehicle ducts?',
      workspace: 'equipment',
    },
    {
      label: 'Polymer Flammability Screening',
      query: 'How does microgravity flammability testing inform spacecraft material selection standards?',
      workspace: 'equipment',
    },
  ],
  earth_applications: [
    {
      label: 'Building & Conduit Fire Safety',
      query: 'How could BASS-II microgravity results inform fire safety research in buildings on Earth?',
      workspace: 'earth_applications',
    },
    {
      label: 'Wildfire Radiative Spread Hypothesis',
      query: 'What microgravity findings provide insights into low-ventilation wildfire embers and spread?',
      workspace: 'earth_applications',
    },
    {
      label: 'Aerosol Agglomeration in Detectors',
      query: 'How does microgravity smoke particle agglomeration inform terrestrial optical fire detectors?',
      workspace: 'earth_applications',
    },
    {
      label: 'Polymer Pyrolysis & Flame Retardants',
      query: 'How do buoyancy-free solid polymer degradation tests support terrestrial flammability standards?',
      workspace: 'earth_applications',
    },
  ],
};

const DEFAULT_EXAMPLES = [
  {
    label: 'Oxygen & Flame Behavior',
    query: 'How does oxygen concentration affect solid material flame spread in microgravity?',
    workspace: 'auto',
  },
  {
    label: 'BASS-II PMMA vs Cotton',
    query: 'Compare the flammability parameter space of PMMA and Cotton in BASS-II.',
    workspace: 'comparison',
  },
  {
    label: 'Spacecraft Smoke Detection',
    query: 'How does aerosol particle agglomeration affect smoke detector response times in spacecraft?',
    workspace: 'equipment',
  },
  {
    label: 'Lunar 0.16g Fire Gaps',
    query: 'What combustion research gaps exist for lunar (0.16g) and Martian (0.38g) habitats?',
    workspace: 'gap_detection',
  },
  {
    label: 'Terrestrial Fire Safety',
    query: 'How can microgravity combustion research inform terrestrial building conduit fires?',
    workspace: 'earth_applications',
  },
  {
    label: 'Predictive Modeling (BASS-II)',
    query: 'Prepare BASS-II data for predicting burn duration from initial oxygen and forced airflow.',
    workspace: 'modeling',
  },
];

const TAB_TO_WORKSPACE = {
  'dataset-explorer': 'visualization',
  'experiment-comparison': 'comparison',
  'modeling-extraction': 'modeling',
  'gap-detection': 'gap_detection',
  'equipment-research': 'equipment',
  'earth-applications': 'earth_applications',
};

export function ResearchPromptBar({
  initialWorkspace = 'auto',
  onResultReceived = null,
  onResult = null,
  onActionTriggered = null,
  onNavigate = null,
  className = '',
  renderInlineResults = true,
  handoffContext = null,
  isHomepage = false,
}) {
  const [query, setQuery] = useState('');
  const [workspace, setWorkspace] = useState(initialWorkspace);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  // Track executed handoff ID to prevent duplicate requests on rerenders (Step 5/6 Mandate)
  const lastExecutedHandoffRef = useRef(null);
  // Monotonic sequence ref to prevent stale responses overriding current results (Step 5)
  const reqSeqRef = useRef(0);

  // Unified callback dispatchers
  const dispatchResult = (val) => {
    if (onResultReceived) onResultReceived(val);
    else if (onResult) onResult(val);
  };

  // Automatic One-Time Research Continuation Handler
  useEffect(() => {
    const incomingQuery = handoffContext?.query || handoffContext?.objective || handoffContext?.prompt;
    const handoffKey = handoffContext?.handoffId || (handoffContext?.handoff && incomingQuery ? `handoff-${incomingQuery}` : null);

    if (handoffKey && lastExecutedHandoffRef.current !== handoffKey) {
      lastExecutedHandoffRef.current = handoffKey;
      if (incomingQuery) {
        setQuery(incomingQuery);
        const rawTarget = handoffContext.targetWorkspace || initialWorkspace;
        const targetWs = TAB_TO_WORKSPACE[rawTarget] || rawTarget;
        if (targetWs && targetWs !== 'auto') {
          setWorkspace(targetWs);
        }
        executePrompt(incomingQuery, targetWs);
      }
    }
  }, [handoffContext, initialWorkspace]);

  // Determine active examples
  const activeExamples = useMemo(() => {
    if (workspace && WORKSPACE_EXAMPLES[workspace]) {
      return WORKSPACE_EXAMPLES[workspace];
    }
    if (initialWorkspace && WORKSPACE_EXAMPLES[initialWorkspace]) {
      return WORKSPACE_EXAMPLES[initialWorkspace];
    }
    return DEFAULT_EXAMPLES;
  }, [workspace, initialWorkspace]);

  const executePrompt = async (overrideQuery = null, overrideWs = null) => {
    const q = (overrideQuery !== null ? overrideQuery : query).trim();
    const rawWs = overrideWs !== null ? overrideWs : workspace;
    const ws = TAB_TO_WORKSPACE[rawWs] || rawWs;

    if (!q) return;

    const currentSeq = ++reqSeqRef.current;
    setIsLoading(true);
    setError(null);

    try {
      const res = await flameApi.submitPromptResearch({
        objective: q,
        workspace: ws,
        context_filters: null,
      });

      if (currentSeq !== reqSeqRef.current) return;

      setResponse(res);
      setShowDetails(false);

      dispatchResult(res);
    } catch (err) {
      if (currentSeq !== reqSeqRef.current) return;
      console.error('Prompt research failed:', err);
      setError(err.message || 'Failed to process research inquiry');
    } finally {
      if (currentSeq === reqSeqRef.current) {
        setIsLoading(false);
      }
    }
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    executePrompt();
  };

  const handleSelectExample = (ex) => {
    setQuery(ex.query);
    setWorkspace(ex.workspace);
    executePrompt(ex.query, ex.workspace);
  };

  const handleSelectClarification = (opt) => {
    setQuery(opt);
    executePrompt(opt, workspace);
  };

  const handleClear = () => {
    setQuery('');
    setResponse(null);
    setError(null);
    dispatchResult(null);
  };

  const handleActionClick = (action) => {
    const handoffId = `handoff_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const canonicalWs = action.target_workspace || TAB_TO_WORKSPACE[action.tab_id] || action.tab_id;
    const augmentedAction = {
      ...action,
      payload: {
        ...(action.payload || {}),
        query: query || response?.objective,
        handoff: true,
        handoffId: handoffId,
        targetWorkspace: canonicalWs,
      },
    };

    if (onActionTriggered) {
      onActionTriggered(augmentedAction);
    } else if (onNavigate) {
      onNavigate(action.tab_id, augmentedAction.payload);
    }
  };

  return (
    <div className={`bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm ${className}`}>
      {/* Top Header Strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-xs font-semibold text-slate-900 tracking-wider uppercase font-mono">
            {isHomepage ? 'Natural-Language Scientific Research' : 'Specialist Research Prompt'}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 font-mono">
            Grounded RAG & Flight Telemetry
          </span>
        </div>

        {response && (
          <div className="flex items-center gap-1.5 text-[10px] font-mono">
            <span
              className={`px-2 py-0.5 rounded border ${
                response.execution_mode === 'llm_assisted'
                  ? 'bg-purple-50 border-purple-200 text-purple-700'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-700'
              }`}
            >
              {response.execution_mode === 'llm_assisted' ? 'LLM-Assisted (Gemini)' : 'Deterministic Grounding (PSI)'}
            </span>
            <span className="px-2 py-0.5 rounded bg-sky-50 border border-sky-200 text-sky-700">
              Verified Evidence
            </span>
          </div>
        )}
      </div>

      {/* Main Form Input */}
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5 mb-3">
        <div className="relative flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              workspace === 'comparison'
                ? "Compare NASA combustion experiments (e.g. 'Compare radiant heat flux between Saffire-III Sample 1 and Sample 2')..."
                : workspace === 'modeling'
                ? "Inquire about predictive modeling (e.g. 'Prepare BASS-II data for predicting burn duration from oxygen and airflow')..."
                : workspace === 'equipment'
                ? "Inquire about spacecraft fire safety equipment (e.g. 'How do smoke detectors perform in microgravity?')..."
                : "Ask any research question (e.g. 'How does oxygen concentration affect flame spread in BASS-II?')..."
            }
            disabled={isLoading}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 font-sans shadow-xs transition-all"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 text-xs cursor-pointer px-1 py-0.5"
              title="Clear input"
            >
              ✕
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {!isHomepage && (
            <select
              value={workspace}
              onChange={(e) => setWorkspace(e.target.value)}
              disabled={isLoading}
              className="bg-white border border-slate-200 rounded-xl px-3 py-3 text-xs text-slate-700 font-mono focus:outline-none focus:ring-2 focus:ring-orange-500/20 cursor-pointer shadow-xs"
            >
              <option value="auto">Auto Router</option>
              <option value="visualization">Visualization</option>
              <option value="comparison">Comparison</option>
              <option value="modeling">Modeling</option>
              <option value="gap_detection">Gap Detection</option>
              <option value="equipment">Equipment</option>
              <option value="earth_applications">Earth Apps</option>
            </select>
          )}

          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-5 py-3 bg-orange-500 hover:bg-orange-600 disabled:bg-slate-100 disabled:text-slate-400 text-white disabled:cursor-not-allowed font-semibold rounded-xl text-xs tracking-wide transition-all shadow-xs cursor-pointer flex items-center justify-center gap-2 min-w-[110px]"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <span>Research</span>
                <span className="text-xs">↵</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Example Prompt Chips */}
      <div className="flex flex-wrap items-center gap-1.5 mb-2">
        <span className="text-[11px] text-slate-500 font-mono mr-1">Inquiry suggestions:</span>
        {activeExamples.map((ex, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSelectExample(ex)}
            disabled={isLoading}
            className="text-[11px] px-2.5 py-1 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-700 hover:text-orange-600 border border-slate-200 transition-colors font-sans cursor-pointer shadow-xs"
          >
            {ex.label}
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start gap-2">
          <span className="font-bold">Error:</span>
          <span>{error}</span>
        </div>
      )}

      {/* Ambiguity / Clarification Needed Banner */}
      {response && response.status === 'ambiguous' && (
        <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl animate-in fade-in duration-200">
          <div className="flex items-center gap-2 mb-2 text-amber-800 text-xs font-semibold">
            <span>⚠ Clarification Required</span>
          </div>
          <p className="text-xs text-amber-900 mb-3">
            {response.key_findings?.[0] || 'Please select a specific NASA experiment or measurement channel to proceed:'}
          </p>
          {response.suggested_actions && response.suggested_actions.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {response.suggested_actions.map((act) => (
                <button
                  key={act.id}
                  type="button"
                  onClick={() => handleSelectClarification(act.label)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-white hover:bg-amber-100/60 border border-amber-200 text-amber-800 font-mono transition-colors cursor-pointer shadow-xs"
                >
                  {act.label} →
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Compact Interpretation Strip (When renderInlineResults is false in specialist workspaces) */}
      {response && response.status === 'ok' && !renderInlineResults && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-slate-500 font-mono text-[11px]">Active Workspace:</span>
            <span className="font-semibold text-orange-600 uppercase font-mono text-[11px] px-2 py-0.5 rounded bg-orange-50 border border-orange-200">
              {response.workspace.replace('_', ' ')}
            </span>
            {response.interpreted_intent?.dataset_id && (
              <span className="text-slate-700 font-mono text-[11px] px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                {response.interpreted_intent.dataset_id}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleClear}
              className="text-[11px] text-slate-500 hover:text-slate-900 font-mono cursor-pointer underline"
            >
              Reset Query
            </button>
          </div>
        </div>
      )}

      {/* STEP 4 & 5: GROUNDED SCIENTIFIC ANSWER & SMART TOOL RECOMMENDATIONS */}
      {response && response.status === 'ok' && renderInlineResults && (
        <div className="mt-4 pt-4 border-t border-slate-100 space-y-4 animate-in fade-in duration-200">
          {/* Grounded Scientific Answer Box (2-4 concise sentences) */}
          <div className="p-4 sm:p-5 rounded-xl bg-slate-50 border border-slate-200 text-left space-y-3 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs font-semibold text-slate-900 tracking-tight uppercase font-mono">
                  Grounded Scientific Finding
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800">
                  Verified Data
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                  {response.workspace.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>

            <p className="text-sm text-slate-800 leading-relaxed font-sans font-normal">
              {response.grounded_answer || response.key_findings?.[0]}
            </p>

            {/* Scientific Caveat / Transport Limitation Alert */}
            {response.scientific_caveats && response.scientific_caveats.length > 0 && (
              <div className="text-xs text-amber-900 bg-amber-50 border border-amber-200 p-2.5 rounded-lg flex items-start gap-2">
                <span className="text-amber-600 font-bold">Caveat:</span>
                <span className="leading-normal">{response.scientific_caveats[0]}</span>
              </div>
            )}
          </div>

          {/* STEP 5: SMART TOOL RECOMMENDATIONS ("What would you like to explore next?") */}
          {response.suggested_actions && response.suggested_actions.length > 0 && (
            <div className="space-y-2.5 text-left pt-1">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-semibold text-slate-900 uppercase font-mono tracking-wider flex items-center gap-1.5">
                    <span className="text-orange-500">⚡</span>
                    <span>What would you like to explore next?</span>
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Select a specialist tool to automatically continue your research with this question:
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {response.suggested_actions.slice(0, 3).map((act) => (
                  <button
                    key={act.id}
                    type="button"
                    onClick={() => handleActionClick(act)}
                    className="p-3 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 hover:border-orange-400 text-left transition-all duration-150 flex flex-col justify-between group cursor-pointer shadow-xs hover:shadow-sm"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-orange-600 text-xs font-medium">
                        <ToolIcon icon={act.icon || act.tab_id} className="w-3.5 h-3.5" />
                        <span className="truncate">{act.label}</span>
                      </div>
                      <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                        {act.description || `Examine empirical measurements and analysis in the ${act.tab_id.replace('-', ' ')} workspace.`}
                      </p>
                    </div>
                    <div className="pt-2 mt-2 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-500 group-hover:text-orange-600">
                      <span>Launch Tool</span>
                      <span className="group-hover:translate-x-1 transition-transform">→</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Collapsible Source Provenance & Technical Findings */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <button
              type="button"
              onClick={() => setShowDetails(!showDetails)}
              className="text-slate-500 hover:text-slate-900 font-mono flex items-center gap-1 cursor-pointer transition-colors"
            >
              <span>{showDetails ? '▲ Hide Evidence Details & Citations' : '▼ View Verified Citations & Findings'}</span>
            </button>

            <span className="text-slate-400 font-mono text-[10px]">
              Zero synthetic data generated
            </span>
          </div>

          {showDetails && (
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-left text-xs animate-in fade-in duration-150">
              {/* Citations List */}
              {response.provenance_citations && response.provenance_citations.length > 0 && (
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 block mb-1.5">
                    Source Citations:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {response.provenance_citations.map((cit) => (
                      <span
                        key={cit.id}
                        className="px-2.5 py-1 rounded bg-white border border-slate-200 text-slate-700 font-mono text-[10px] flex items-center gap-1.5 shadow-xs"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        <span>{cit.title}</span>
                        {cit.reference && <span className="text-slate-500">({cit.reference})</span>}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed Findings List */}
              {response.key_findings && response.key_findings.length > 1 && (
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 block mb-1">
                    Verified Empirical Observations:
                  </span>
                  <ul className="space-y-1 text-slate-700 text-[11px] list-disc list-inside">
                    {response.key_findings.slice(1).map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
