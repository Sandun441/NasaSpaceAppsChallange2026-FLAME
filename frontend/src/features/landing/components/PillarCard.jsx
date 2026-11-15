import React from 'react';
import { ToolIcon } from '../../../components/common/ToolIcon';

export function PillarCard({ tool, pillar, onSelectTab }) {
  const item = tool || pillar || {};
  const targetTab = item.id || item.targetTab;
  const title = item.title || item.label;
  const description = item.description || item.shortDesc;
  const actionText = item.actionText || 'Open Workspace →';
  const tag = item.tag || item.category;
  const icon = item.icon || 'Chart';

  return (
    <div className="p-5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 flex flex-col justify-between group shadow-xs">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-orange-50 border border-orange-200 text-orange-500 flex items-center justify-center group-hover:bg-orange-100 group-hover:border-orange-300 transition-colors">
            <ToolIcon icon={icon} className="w-4 h-4" />
          </div>
          {tag && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
              {tag}
            </span>
          )}
        </div>

        <div>
          <h3 className="text-sm font-semibold text-slate-900 tracking-tight group-hover:text-orange-600 transition-colors">
            {title}
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed mt-1.5 font-sans">
            {description}
          </p>
        </div>
      </div>

      <div className="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between">
        <button
          type="button"
          onClick={() => onSelectTab && onSelectTab(targetTab)}
          className="text-xs font-medium text-orange-600 hover:text-orange-700 flex items-center gap-1.5 transition-colors cursor-pointer group-hover:translate-x-0.5 duration-150"
        >
          <span>{actionText}</span>
        </button>
        <span className="text-[10px] font-mono text-slate-400">NASA FLAME</span>
      </div>
    </div>
  );
}
