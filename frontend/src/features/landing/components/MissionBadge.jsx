import React from 'react';

export function MissionBadge() {
  return (
    <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-slate-200 bg-white text-xs text-slate-700 shadow-xs backdrop-blur-sm">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
      </span>
      <span className="font-medium tracking-tight">Artemis & Moon-to-Mars Fire Safety Data</span>
      <span className="text-[10px] text-slate-500 font-mono pl-1 border-l border-slate-200">PSI v2.4</span>
    </div>
  );
}
