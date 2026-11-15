import React from 'react';
import { Button } from '../../../components/common/Button';

export function ActionLauncherBanner({ actions = [], onNavigate }) {
  if (!actions || actions.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-sm space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-1">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-orange-600">
            Interactive Dashboard Navigation
          </span>
          <h3 className="text-sm font-semibold text-slate-900">
            Recommended Tools for this Fire-Safety Investigation
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500">
          Seamless cross-module research handover
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {actions.map((act) => (
          <button
            key={act.action_id}
            type="button"
            onClick={() => onNavigate(act.tab_id, act.params)}
            className="bg-slate-50 hover:bg-orange-50/50 border border-slate-200 hover:border-orange-300 rounded-xl p-3 text-left transition-all space-y-1.5 group cursor-pointer flex flex-col justify-between"
          >
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-orange-600 uppercase font-bold">
                  {act.tool_name}
                </span>
                <span className="text-xs group-hover:translate-x-0.5 transition-transform text-orange-600">
                  →
                </span>
              </div>
              <h4 className="text-xs font-semibold text-slate-900 group-hover:text-orange-700 transition-colors line-clamp-1">
                {act.label}
              </h4>
              <p className="text-[11px] text-slate-600 leading-tight font-sans line-clamp-2">
                {act.description}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
