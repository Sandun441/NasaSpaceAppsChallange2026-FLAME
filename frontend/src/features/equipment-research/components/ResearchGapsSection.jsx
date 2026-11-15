import React from 'react';
import { Button } from '../../../components/common/Button';

export function ResearchGapsSection({ gaps = [], onNavigate }) {
  if (!gaps || gaps.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-3 border-b border-slate-100">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-orange-600">
            Research Opportunities & Missing Evidence
          </span>
          <h3 className="text-sm sm:text-base font-semibold text-slate-900">
            Linked Findings from NASA FLAME Research Gap Detection Engine (RG2)
          </h3>
        </div>
        <span className="text-[10px] font-mono text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
          {gaps.length} Target Gaps
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {gaps.map((gap) => (
          <div
            key={gap.finding_id}
            className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2.5 flex flex-col justify-between hover:border-orange-300 transition-all"
          >
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-1 flex-wrap">
                <span className="font-mono text-[10px] text-orange-700 font-bold bg-orange-50 px-1.5 py-0.5 rounded border border-orange-200">
                  {gap.finding_id}
                </span>
                <span className="font-mono text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                  Priority: {gap.research_priority}
                </span>
              </div>

              <h4 className="text-xs font-semibold text-slate-900 leading-tight">
                {gap.title}
              </h4>

              <p className="text-[11px] text-slate-600 leading-relaxed font-sans line-clamp-3">
                {gap.summary}
              </p>
            </div>

            <div className="pt-2 border-t border-slate-200 flex justify-end">
              <Button
                size="sm"
                variant="outline"
                onClick={() =>
                  onNavigate('gap-detection', {
                    finding_id: gap.finding_id,
                    sub_tab: 'matrix',
                  })
                }
                className="text-[10px] py-1 text-amber-700 border-amber-200 hover:bg-amber-50 w-full justify-center"
              >
                🔎 Inspect in Gap Matrix →
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
