import React from 'react';

export function SuggestedActionsPanel({ actions = [], onNavigateTool }) {
  if (!actions || actions.length === 0) return null;

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3 shadow-xs">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-slate-800 uppercase tracking-wider font-mono flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-orange-500" />
          Recommended Dashboard Actions
        </h4>
        <span className="text-[10px] text-slate-500 font-mono">
          Context-Aware Tool Routing
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {actions.map((act, idx) => (
          <button
            key={idx}
            onClick={() => onNavigateTool && onNavigateTool(act.tab_id, act.params)}
            className="text-left p-3 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 hover:border-orange-300 transition-all duration-150 group cursor-pointer flex flex-col justify-between shadow-xs hover:shadow-sm"
          >
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[10px] font-mono text-orange-600">
                <span>{act.category || 'Dashboard Tool'}</span>
                <span className="group-hover:translate-x-0.5 transition-transform">→</span>
              </div>
              <div className="text-xs font-semibold text-slate-900 group-hover:text-orange-600 tracking-tight">
                {act.label}
              </div>
              <div className="text-[11px] text-slate-600 line-clamp-2">
                {act.description}
              </div>
            </div>

            <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500 font-mono">
              <span>Tool: {act.tool_name}</span>
              <span className="text-orange-600 group-hover:text-orange-700 font-medium">Launch view</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
