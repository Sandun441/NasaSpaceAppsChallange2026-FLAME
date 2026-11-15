import React, { useState, useRef, useEffect } from 'react';
import { flameApi } from '../../services/flameApi';
import { ModeBadge } from './components/ModeBadge';
import { ExecutedToolResult } from './components/ExecutedToolResult';
import { EvidenceCard } from './components/EvidenceCard';
import { SuggestedActionsPanel } from './components/SuggestedActionsPanel';
import { ScientificMarkdownViewer } from './components/ScientificMarkdownViewer';
import { MissionBadge } from '../landing/components/MissionBadge';
import { FlameHeroEffect } from '../landing/components/FlameHeroEffect';

const EXAMPLE_QUERIES = [
  {
    label: "Saffire-III Comparison",
    query: "Compare flame spread differences and sensor measurements between Saffire-III Sample 1 and Sample 2",
  },
  {
    label: "Oxygen & Flame Spread",
    query: "How does oxygen concentration affect solid material flame spread in microgravity?",
  },
  {
    label: "Cygnus Smoke Telemetry",
    query: "What smoke detection and obscuration telemetry measurements are available from the Cygnus vehicle?",
  },
  {
    label: "Saffire-III Ignition",
    query: "What does Saffire-III show about temperature during ignition?",
  },
  {
    label: "PMMA Fuel Experiments",
    query: "Which NASA combustion experiments used PMMA as fuel substrate and what was measured?",
  },
  {
    label: "Terrestrial Pyrolysis Transfer",
    query: "How do microgravity solid pyrolysis kinetics from BASS-II transfer to terrestrial industrial furnaces and clean combustion?",
  },
  {
    label: "Earth Fire Safety Transfer Limits",
    query: "What physical gravity and buoyant convection differences constrain applying NASA space fire research to Earth buildings?",
  },
  {
    label: "Missing Measurements Audit",
    query: "Which microgravity experiments have missing flame spread rates or uninstrumented flow velocities?",
  },
];

const EARTH_QUICK_INQUIRIES = [
  {
    label: "Physical Transfer Limits",
    query: "What are the gravity and buoyancy differences that limit direct transfer to 1g terrestrial combustion?",
  },
  {
    label: "Verified Observations",
    query: "What verified flight telemetry observations support this terrestrial application?",
  },
  {
    label: "Decoupled Buoyancy",
    query: "How does microgravity buoyancy decoupling isolate the underlying combustion kinetics?",
  },
  {
    label: "Terrestrial Validation Steps",
    query: "What additional terrestrial experiments or CFD modeling are required before engineering adoption?",
  },
  {
    label: "Commercial Adoption Status",
    query: "Has this NASA combustion finding been commercially adopted or deployed in terrestrial industry?",
  },
  {
    label: "Underlying Physics",
    query: "Explain the governing non-dimensional numbers (Froude, Richardson) for this transfer.",
  },
];

const GAP_QUICK_INQUIRIES = [
  {
    label: "Supporting Evidence",
    query: "What evidence supports this research gap in the indexed NASA records?",
  },
  {
    label: "Similar Experiments",
    query: "Which NASA combustion experiments investigated similar atmospheric or fuel conditions?",
  },
  {
    label: "Missing Measurements",
    query: "What specific sensor channels or scientific measurements are missing for this condition?",
  },
  {
    label: "Comparison Baselines",
    query: "Which experiment conditions can be compared against this gap regime?",
  },
  {
    label: "Proposed Next Steps",
    query: "What additional data, raw telemetry, or testing would address this gap?",
  },
  {
    label: "Available FLAME Data",
    query: "Are there relevant experiments or flight telemetry already available in FLAME for this regime?",
  },
];

// Presentation-only conversion: preserves Gemini text, never invents scientific conclusions.
function formatGeminiAnswer(value) {
  if (value == null) return '';
  if (typeof value === 'object') return formatGeminiObject(value);
  if (typeof value !== 'string') return String(value);
  const trimmed = value.trim();
  const jsonText = trimmed.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim();
  if (!jsonText.startsWith('{')) return value;
  try {
    const parsed = JSON.parse(jsonText);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return formatGeminiObject(parsed);
    }
  } catch (_) { /* Keep Gemini's original text if it is not valid JSON. */ }
  return value;
}

function formatGeminiObject(obj) {
  return Object.entries(obj).map(([key, value]) => {
    const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const content = Array.isArray(value)
      ? value.map(item => `- ${typeof item === 'string' ? item : JSON.stringify(item)}`).join('\n')
      : (typeof value === 'object' && value !== null ? JSON.stringify(value, null, 2) : String(value ?? ''));
    return `### ${label}\n\n${content}`;
  }).join('\n\n');
}

export function ScientificAiAssistant({
  onSelectTab,
  initialContext,
  messages: externalMessages,
  setMessages: externalSetMessages,
  inputQuery: externalInputQuery,
  setInputQuery: externalSetInputQuery,
  activeFinding: externalActiveFinding,
  setActiveFinding: externalSetActiveFinding,
  activeEarthEvidence: externalActiveEarthEvidence,
  setActiveEarthEvidence: externalSetActiveEarthEvidence,
  isHomepage = false,
}) {
  // Support both lifted state (from App.jsx) and local state
  const [internalInputQuery, setInternalInputQuery] = useState('');
  const [internalMessages, setInternalMessages] = useState([]);
  const [internalActiveFinding, setInternalActiveFinding] = useState(null);
  const [internalActiveEarthEvidence, setInternalActiveEarthEvidence] = useState(null);

  const inputQuery = externalInputQuery !== undefined ? externalInputQuery : internalInputQuery;
  const setInputQuery = externalSetInputQuery || setInternalInputQuery;

  const messages = externalMessages !== undefined ? externalMessages : internalMessages;
  const setMessages = externalSetMessages || setInternalMessages;

  const activeFinding = externalActiveFinding !== undefined ? externalActiveFinding : internalActiveFinding;
  const setActiveFinding = externalSetActiveFinding || setInternalActiveFinding;

  const activeEarthEvidence = externalActiveEarthEvidence !== undefined ? externalActiveEarthEvidence : internalActiveEarthEvidence;
  const setActiveEarthEvidence = externalSetActiveEarthEvidence || setInternalActiveEarthEvidence;

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const handledContextRef = useRef(null);

  // Handle incoming investigation context from Research Gap Detection Explorer or Earth Applications
  useEffect(() => {
    if (initialContext?.initialFindingId && handledContextRef.current !== initialContext.initialFindingId) {
      handledContextRef.current = initialContext.initialFindingId;
      const findingInfo = {
        id: initialContext.initialFindingId,
        title: initialContext.initialFindingTitle || initialContext.initialFindingId,
        finding: initialContext.initialFinding || null,
        gapType: initialContext.initialFinding?.gap_type || null,
      };
      setActiveFinding(findingInfo);
      setActiveEarthEvidence(null);

      const q =
        initialContext.initialQuery ||
        `Investigate scientific evidence and coverage status for research gap ${initialContext.initialFindingId}: ${initialContext.initialFindingTitle || ''}`;
      handleAsk(q, initialContext.initialFindingId);
    } else if (
      (initialContext?.evidence_id || initialContext?.source === 'earth-applications') &&
      handledContextRef.current !== (initialContext.evidence_id || initialContext.finding_id)
    ) {
      const evId = initialContext.evidence_id || initialContext.finding_id;
      handledContextRef.current = evId;
      const evInfo = {
        id: evId,
        title: initialContext.title || evId,
        categoryId: initialContext.category_id || initialContext.category || null,
        investigationId: initialContext.investigation_id || initialContext.investigation || null,
      };
      setActiveEarthEvidence(evInfo);
      setActiveFinding(null);

      const q =
        initialContext.question ||
        `Investigate terrestrial combustion application and physical transfer limits for ${evId}: ${initialContext.title || ''}`;
      handleAsk(q, null, evId, evInfo.categoryId, evInfo.investigationId);
    }
  }, [initialContext]);

  const handleAsk = async (
    queryToSubmit,
    findingIdOverride = null,
    evidenceIdOverride = null,
    earthCategoryOverride = null,
    investigationIdOverride = null,
  ) => {
    const q = (queryToSubmit || inputQuery).trim();
    if (!q || isLoading) return;

    const targetFindingId =
      findingIdOverride !== null ? findingIdOverride : activeFinding?.id || null;
    const targetEvidenceId =
      evidenceIdOverride !== null ? evidenceIdOverride : activeEarthEvidence?.id || null;
    const targetCategory =
      earthCategoryOverride !== null ? earthCategoryOverride : activeEarthEvidence?.categoryId || null;
    const targetInvestigation =
      investigationIdOverride !== null ? investigationIdOverride : activeEarthEvidence?.investigationId || null;

    setError(null);
    setInputQuery('');

    // Append user message
    const userMsg = {
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      role: 'user',
      content: q,
      findingId: targetFindingId,
      evidenceId: targetEvidenceId,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // Build conversation history for API (max 8 turns)
      const history = messages.slice(-8).map((m) => ({
        role: m.role,
        content: typeof m.content === 'string' ? m.content : '',
      }));

      const apiResponse = await fetch('/api/ai/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: q,
          conversation_history: history,
          context_filters: {
            finding_id: targetFindingId,
            evidence_id: targetEvidenceId,
            category: targetCategory,
            investigation_id: targetInvestigation,
          },
        }),
      });
      if (!apiResponse.ok) throw new Error(`Research AI request failed (HTTP ${apiResponse.status})`);
      const response = await apiResponse.json();

      const assistantMsg = {
        id: `asst_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        role: 'assistant',
        content: formatGeminiAnswer(response.answer),
        toolResult: response.tool_result || null,
        status: response.status,
        retryable: response.retryable,
        errorCode: response.error_code,
        errorMessage: response.error_message,
        citations: response.evidence_citations || [],
        relevantRecords: response.relevant_records || [],
        warnings: response.quality_warnings || [],
        limitations: response.scientific_limitations || [],
        suggestedActions: response.status === 'tool_executed' ? [] : (response.suggested_actions || []),
        claimValidation: response.claim_validation || null,
        llmStatus: response.llm_provider_status || {},
        findingId: targetFindingId,
        evidenceId: targetEvidenceId,
        userQuery: q,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err.message || 'Failed to retrieve grounded scientific answer.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setError(null);
  };

  // Unified automatic research continuation router
  const handleNavigateTool = (tabId, params = {}) => {
    if (!onSelectTab) return;

    const TAB_TO_WORKSPACE = {
      'dataset-explorer': 'visualization',
      'experiment-comparison': 'comparison',
      'modeling-extraction': 'modeling',
      'gap-detection': 'gap_detection',
      'equipment-research': 'equipment',
      'earth-applications': 'earth_applications',
    };
    const targetWs = TAB_TO_WORKSPACE[tabId] || tabId;
    const handoffId = `handoff_${Date.now()}_${Math.random().toString(36).substr(2, 7)}`;
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    const researchQuery = params.query || lastUserMsg?.content || params.label || 'Investigate microgravity combustion data';

    const continuationContext = {
      handoffId,
      query: researchQuery,
      objective: researchQuery,
      targetWorkspace: targetWs,
      actionId: params.action_id || 'suggested_action',
      actionPayload: params,
      dataset_id: params.dataset_id || params.datasetId || params.exp1,
      dataset_a_id: params.exp1 || params.dataset_a_id,
      dataset_b_id: params.exp2 || params.dataset_b_id,
      investigation_id: params.investigation_id,
      channel_ids: params.channel_ids,
      category: params.category,
      evidence_id: params.evidence_id,
      finding_id: params.finding_id,
      view: params.view || 'visualize',
      filters: params.filters || {},
      timestamp: Date.now(),
      source: 'ai-assistant',
    };

    onSelectTab(tabId, continuationContext);
  };

  return (
    <div className="w-full space-y-6">
      {/* 1. Header Section */}
      {isHomepage ? (
        <div className="text-center space-y-4 pt-1 pb-2 max-w-4xl mx-auto">
          <div className="flex flex-col items-center gap-1.5">
            <MissionBadge />
            <FlameHeroEffect />
          </div>

          <div className="space-y-2">
            <h1 className="text-3xl sm:text-5xl font-semibold tracking-tight text-slate-900 leading-tight">
              Understand Fire in Microgravity
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 max-w-2xl mx-auto leading-relaxed">
              An AI-powered scientific intelligence platform synthesizing NASA microgravity combustion experiments. Ask any research question to retrieve verified flight evidence and seamlessly launch specialist tools.
            </p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
              <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
                Scientific AI Research Assistant
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-orange-50 text-orange-600 border border-orange-200">
                  Grounded Intelligence
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl font-mono">
              Prompt-driven inquiry across verified NASA microgravity combustion datasets (BASS-II, Saffire-III, and Cygnus telemetry). Every claim is validated against indexed experimental records with zero synthetic hallucinations.
            </p>
          </div>

          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-600 hover:text-slate-900 text-xs font-mono transition-colors cursor-pointer self-start sm:self-auto"
            >
              Clear Conversation
            </button>
          )}
        </div>
      )}

      {/* 2. Active Research Gap Finding Investigation Banner */}
      {activeFinding && (
        <div className="bg-gradient-to-r from-orange-50 via-white to-white border border-orange-200 rounded-2xl p-4 sm:p-5 space-y-3.5 shadow-sm animate-in fade-in slide-in-from-top-2 duration-200 text-left">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-2.5 border-b border-orange-200">
            <div className="flex flex-wrap items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
              <span className="text-[10px] font-mono uppercase tracking-wider text-orange-600 font-bold">
                Active Grounded Research Gap Investigation
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200 font-bold">
                {activeFinding.id}
              </span>
              {activeFinding.gapType && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-orange-100 text-orange-800 border border-orange-200">
                  {activeFinding.gapType}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {onSelectTab && (
                <button
                  type="button"
                  onClick={() =>
                    onSelectTab('gap-detection', {
                      finding_id: activeFinding.id,
                      finding: activeFinding.finding,
                      sub_tab: 'matrix',
                    })
                  }
                  className="text-[11px] font-mono text-orange-600 hover:text-orange-700 underline cursor-pointer"
                >
                  ← Back to Gap Explorer
                </button>
              )}
              <button
                type="button"
                onClick={() => setActiveFinding(null)}
                className="text-xs text-slate-500 hover:text-slate-800 px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 border border-slate-200 font-mono transition-colors cursor-pointer"
                title="Exit finding inquiry context"
              >
                Exit Finding Mode ✕
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
              {activeFinding.title}
            </h3>
            <p className="text-xs text-slate-600 mt-1">
              Scientific inquiry is deterministically grounded against finding {activeFinding.id} from the Phase RG2 engine and the 155 indexed microgravity records.
            </p>
          </div>

          {/* Quick Inquiry Action Chips */}
          <div className="space-y-1.5 pt-1">
            <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider block">
              Quick Research Inquiries:
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              {GAP_QUICK_INQUIRIES.map((inq, idx) => (
                <button
                  key={idx}
                  type="button"
                  disabled={isLoading}
                  onClick={() => handleAsk(inq.query, activeFinding.id)}
                  className="p-2 text-left rounded-lg bg-white hover:bg-orange-50 border border-slate-200 hover:border-orange-300 text-[11px] font-mono transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group shadow-xs"
                >
                  <div className="text-orange-600 font-semibold text-[10.5px] group-hover:text-orange-700">
                    {inq.label}
                  </div>
                  <div className="text-[9.5px] text-slate-500 truncate mt-0.5" title={inq.query}>
                    {inq.query}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 3. Active Earth Application Investigation Banner */}
      {activeEarthEvidence && (
        <div className="bg-gradient-to-r from-emerald-50 via-white to-white border border-emerald-200 rounded-2xl p-4 sm:p-5 space-y-3.5 shadow-sm animate-in fade-in slide-in-from-top-2 duration-200 text-left">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-2.5 border-b border-emerald-200">
            <div className="flex flex-wrap items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-700 font-bold">
                Active Grounded Earth Applications Investigation
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200 font-bold">
                {activeEarthEvidence.id}
              </span>
              {activeEarthEvidence.investigationId && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-200 uppercase">
                  {activeEarthEvidence.investigationId.replace('_', ' ')}
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {onSelectTab && (
                <button
                  type="button"
                  onClick={() =>
                    onSelectTab('earth-applications', {
                      evidence_id: activeEarthEvidence.id,
                      category_id: activeEarthEvidence.categoryId,
                    })
                  }
                  className="text-[11px] font-mono text-emerald-700 hover:text-emerald-800 underline cursor-pointer"
                >
                  ← Back to Earth Applications
                </button>
              )}
              <button
                type="button"
                onClick={() => setActiveEarthEvidence(null)}
                className="text-xs text-slate-500 hover:text-slate-800 px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 border border-slate-200 font-mono transition-colors cursor-pointer"
                title="Exit Earth application context"
              >
                Exit Earth App Mode ✕
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
              {activeEarthEvidence.title}
            </h3>
            <p className="text-xs text-slate-600 mt-1">
              Investigating terrestrial transfer mechanics, buoyancy decoupling, and 1g physical scaling limitations for evidence {activeEarthEvidence.id}.
            </p>
          </div>

          {/* Quick Inquiry Action Chips */}
          <div className="space-y-1.5 pt-1">
            <span className="text-[10px] font-mono uppercase text-slate-500 tracking-wider block">
              Quick Terrestrial Transfer Inquiries:
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              {EARTH_QUICK_INQUIRIES.map((inq, idx) => (
                <button
                  key={idx}
                  type="button"
                  disabled={isLoading}
                  onClick={() =>
                    handleAsk(
                      inq.query,
                      null,
                      activeEarthEvidence.id,
                      activeEarthEvidence.categoryId,
                      activeEarthEvidence.investigationId,
                    )
                  }
                  className="p-2 text-left rounded-lg bg-white hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 text-[11px] font-mono transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group shadow-xs"
                >
                  <div className="text-emerald-700 font-semibold text-[10.5px] group-hover:text-emerald-800">
                    {inq.label}
                  </div>
                  <div className="text-[9.5px] text-slate-500 truncate mt-0.5" title={inq.query}>
                    {inq.query}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 4. One Prominent Conversational AI Prompt Bar (Step 2 Focus) */}
      <div className="text-left max-w-4xl mx-auto">
        <div className="bg-white border border-slate-200 rounded-2xl p-3 shadow-md transition-all focus-within:border-orange-500 focus-within:ring-2 focus-within:ring-orange-500/20">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-orange-50 border border-orange-200 text-orange-500 flex items-center justify-center font-bold text-xs shrink-0">
              Δ
            </div>
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Ask a scientific research question (e.g. 'How does oxygen concentration affect flame behavior in microgravity?')..."
              className="flex-1 bg-transparent px-2 py-2 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
            />
            <button
              onClick={() => handleAsk()}
              disabled={!inputQuery.trim() || isLoading}
              className="px-4 py-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:bg-slate-100 disabled:text-slate-400 text-white font-semibold text-xs transition-all duration-150 cursor-pointer disabled:cursor-not-allowed shrink-0 flex items-center gap-1.5 shadow-xs"
            >
              {isLoading ? (
                <span className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
              ) : (
                <span>Ask FLAME →</span>
              )}
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-between px-3 pt-2 text-[10px] text-slate-500 font-mono border-t border-slate-100 mt-2">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Grounded: 155 verified NASA flight records • Zero synthetic hallucination
            </span>
            <span>Press Enter ↵ to submit</span>
          </div>
        </div>
      </div>

      {/* 5. Suggested Prompt Chips (when no messages active) */}
      {messages.length === 0 && !activeFinding && !activeEarthEvidence && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-3 max-w-4xl mx-auto text-left shadow-xs">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500">
            <span className="uppercase tracking-wider flex items-center gap-1.5 font-semibold text-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
              Example Research Inquiries
            </span>
            <span className="text-[10.5px] text-slate-500">Click chip to run query</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {EXAMPLE_QUERIES.map((item, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleAsk(item.query)}
                className="text-left p-3 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 hover:border-orange-300 transition-all duration-150 group cursor-pointer flex flex-col justify-between shadow-xs hover:shadow-sm"
              >
                <div className="text-xs font-semibold text-orange-600 group-hover:text-orange-700">
                  {item.label}
                </div>
                <div className="text-[10.5px] text-slate-600 mt-1 line-clamp-2">
                  {item.query}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 6. Conversation Thread (Scrollable container to prevent pushing tool cards out of reach) */}
      {messages.length > 0 && (
        <div className="max-w-4xl mx-auto space-y-4 text-left">
          <div className="flex items-center justify-between px-1 text-xs font-mono text-slate-600">
            <span className="flex items-center gap-2 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Conversation Thread ({messages.length} {messages.length === 1 ? 'turn' : 'turns'})
            </span>
            <button
              onClick={handleClearChat}
              className="text-[11px] font-mono text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
            >
              Clear Conversation ✕
            </button>
          </div>

          <div
            ref={scrollContainerRef}
            className="max-h-[580px] overflow-y-auto pr-1 space-y-5 rounded-2xl bg-slate-50 border border-slate-200 p-4 scrollbar-thin scrollbar-thumb-slate-300"
          >
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.role === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                {/* User Message */}
                {msg.role === 'user' ? (
                  <div className="max-w-2xl bg-orange-50 border border-orange-200 rounded-2xl rounded-tr-sm p-4 text-slate-900 shadow-xs">
                    <div className="flex items-center justify-between gap-4 mb-1 text-[10px] font-mono text-orange-700/80">
                      <div className="flex items-center gap-1.5">
                        <span>Researcher Inquiry</span>
                        {msg.findingId && (
                          <span className="px-1.5 py-0.2 rounded bg-white border border-orange-200 text-orange-700 text-[9px] font-mono">
                            {msg.findingId}
                          </span>
                        )}
                        {msg.evidenceId && (
                          <span className="px-1.5 py-0.2 rounded bg-white border border-emerald-200 text-emerald-700 text-[9px] font-mono">
                            {msg.evidenceId}
                          </span>
                        )}
                      </div>
                      <span>{msg.timestamp}</span>
                    </div>
                    <p className="text-xs sm:text-sm font-medium leading-relaxed">{msg.content}</p>
                  </div>
                ) : msg.status === 'ai_unavailable' || (!msg.content && !msg.toolResult) ? (
                  /* AI Unavailable Error Card */
                  <div className="w-full bg-rose-50 border border-rose-200 rounded-2xl p-4 sm:p-5 space-y-3 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-3 pb-2.5 border-b border-rose-200">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                        <span className="text-xs font-semibold text-rose-800 font-mono">
                          FLAME AI Unavailable
                        </span>
                      </div>
                      <ModeBadge
                        status={msg.status}
                        llmProviderStatus={msg.llmStatus}
                      />
                    </div>
                    <div className="text-xs text-rose-800 leading-relaxed space-y-1">
                      <p>FLAME AI is temporarily unavailable. Please try again.</p>
                      {msg.llmStatus?.reason && (
                        <p className="text-[10.5px] text-rose-700 font-mono">
                          Detail: {msg.llmStatus.reason}
                        </p>
                      )}
                    </div>
                    {msg.retryable && msg.userQuery && (
                      <div className="pt-2">
                        <button
                          type="button"
                          onClick={() => handleAsk(msg.userQuery)}
                          className="px-3 py-1.5 rounded-lg bg-rose-100 hover:bg-rose-200 border border-rose-300 text-rose-900 text-xs font-mono transition-colors cursor-pointer flex items-center gap-1.5"
                        >
                          <span>↻</span> Retry Question
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  /* Assistant Response */
                  <div className="w-full bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 space-y-4 shadow-sm">
                    {/* Header Meta */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
                      <div className="flex items-center gap-2.5">
                        <div className="w-6 h-6 rounded bg-orange-500 text-white flex items-center justify-center font-bold text-xs shrink-0">
                          Δ
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-slate-900 tracking-tight flex items-center gap-1.5">
                            <span>NASA FLAME Scientific Intelligence</span>
                            {msg.findingId && (
                              <span className="text-[9.5px] font-mono px-1.5 py-0.2 rounded bg-orange-50 text-orange-700 border border-orange-200">
                                {msg.findingId}
                              </span>
                            )}
                            {msg.evidenceId && (
                              <span className="text-[9.5px] font-mono px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                                {msg.evidenceId}
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-slate-500 font-mono">
                            {msg.timestamp}
                          </div>
                        </div>
                      </div>

                      <ModeBadge
                        status={msg.status}
                        llmProviderStatus={msg.llmStatus}
                      />
                    </div>

                    {/* Answer Content */}
                    <div className="max-w-none text-slate-800 text-xs sm:text-sm leading-relaxed font-sans">
                      <ScientificMarkdownViewer content={msg.content} />
                    </div>
                    {msg.toolResult && <ExecutedToolResult result={msg.toolResult} />}

                    {/* Evidence Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pt-2 space-y-2.5">
                        <div className="flex items-center justify-between text-xs font-mono text-slate-700">
                          <span className="uppercase tracking-wider font-semibold flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            Verified Grounded Citations ({msg.citations.length})
                          </span>
                          <span className="text-[10px] text-slate-500">
                            100% Verified against Index
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {msg.citations.map((ev, cIdx) => (
                            <EvidenceCard
                              key={ev.record_id || cIdx}
                              evidence={ev}
                              index={cIdx + 1}
                              onNavigateTool={handleNavigateTool}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Quality & Validation Warnings */}
                    {msg.warnings && msg.warnings.length > 0 && (
                      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-[11px] font-mono text-amber-900 space-y-1">
                        <div className="font-semibold uppercase tracking-wider text-amber-800 flex items-center gap-1.5">
                          <span>⚠</span> Documented Data Quality Screening Notes
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 text-[10px] text-amber-800">
                          {msg.warnings.slice(0, 4).map((w, wIdx) => (
                            <li key={wIdx}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Scientific Limitations */}
                    {!msg.toolResult && msg.limitations && msg.limitations.length > 0 && (
                      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-[11px] text-slate-600 space-y-1">
                        <div className="font-semibold text-slate-800 font-mono text-[10px] uppercase tracking-wider">
                          Scientific Scope & Limitations:
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 text-[10px]">
                          {msg.limitations.map((lim, lIdx) => (
                            <li key={lIdx}>{lim}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Contextual Recommended Interactive Actions (Step 4 & 5) */}
                    {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                      <SuggestedActionsPanel
                        actions={msg.suggestedActions}
                        onNavigateTool={handleNavigateTool}
                      />
                    )}
                  </div>
                )}
              </div>
            ))}

            {/* Loading Spinner */}
            {isLoading && (
              <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-3 text-slate-700 text-xs font-mono shadow-xs animate-pulse">
                <div className="w-4 h-4 rounded-full border-2 border-orange-500 border-t-transparent animate-spin shrink-0" />
                <span>Retrieving scientific flight records, ranking evidence with RRF, and assembling response...</span>
              </div>
            )}

            {/* Error Notification */}
            {error && (
              <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-xs text-rose-800 font-mono flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-rose-600 font-bold">Error:</span>
                  <span>{error}</span>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="text-rose-600 hover:text-rose-800 ml-2 text-xs cursor-pointer"
                >
                  ✕
                </button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}
