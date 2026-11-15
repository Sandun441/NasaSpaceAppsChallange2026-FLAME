import React from 'react';
import { PillarCard } from '../components/PillarCard';
import { RESEARCH_TOOLS, PILLARS_DATA } from '../../../lib/constants';

export function PillarsSection({ onSelectTab }) {
  const tools = RESEARCH_TOOLS && RESEARCH_TOOLS.length > 0 ? RESEARCH_TOOLS : PILLARS_DATA;

  return (
    <section className="pt-6 sm:pt-10">
      <div className="flex items-center justify-between pb-3 mb-5 border-b border-slate-200">
        <div>
          <h2 className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold">
            Specialist Research Workspaces
          </h2>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Six empirical research tools synthesizing verified NASA microgravity combustion data
          </p>
        </div>
        <span className="text-[10px] font-mono text-slate-600 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full">
          NASA Open Science PSI
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-left">
        {tools.map((tool) => (
          <PillarCard key={tool.id} tool={tool} onSelectTab={onSelectTab} />
        ))}
      </div>
    </section>
  );
}
