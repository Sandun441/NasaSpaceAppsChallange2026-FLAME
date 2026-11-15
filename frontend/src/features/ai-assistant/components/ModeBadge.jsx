import React from 'react';

export function ModeBadge({ status, llmProviderStatus }) {
  if (status === 'ai_unavailable') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-800 text-[11px] font-mono shadow-xs">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
        <span>Gemini Unavailable</span>
      </div>
    );
  }

  if (
    status === 'gemini_conversation' ||
    status === 'conversational_gemini' ||
    status === 'educational_gemini'
  ) {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-50 border border-sky-200 text-sky-800 text-[11px] font-mono shadow-xs">
        <span className="w-1.5 h-1.5 rounded-full bg-sky-500 animate-pulse" />
        <span>Gemini Conversational AI</span>
      </div>
    );
  }

  if (status === 'grounded_llm_answer') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-mono shadow-xs">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
        <span>Grounded Gemini AI ({llmProviderStatus?.model || 'Gemini'})</span>
      </div>
    );
  }

  if (status === 'insufficient_evidence') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-mono shadow-xs">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
        <span>Insufficient NASA Evidence</span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-mono">
      <span>Gemini AI</span>
    </div>
  );
}
