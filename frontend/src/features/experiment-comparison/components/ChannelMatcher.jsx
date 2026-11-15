import React, { useMemo } from 'react';

/**
 * ChannelMatcher
 * Displays shared measurement channels between Dataset A and B with unit compatibility checks.
 */
export function ChannelMatcher({
  sharedChannels = [],
  aOnlyChannels = [],
  bOnlyChannels = [],
  activeChannelId,
  onSelectChannel,
}) {
  // Group shared channels by category
  const groupedShared = useMemo(() => {
    const map = new Map();
    sharedChannels.forEach((ch) => {
      const key = ch.category;
      if (!map.has(key)) {
        map.set(key, {
          category: ch.category,
          categoryLabel: ch.categoryLabel,
          unit: ch.unit,
          channels: [],
        });
      }
      map.get(key).channels.push(ch);
    });
    return Array.from(map.values());
  }, [sharedChannels]);

  if (sharedChannels.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-white border border-slate-200 text-xs font-mono text-slate-500 text-center shadow-sm">
        No shared measurement channels detected between the selected datasets.
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 space-y-3 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
            Shared Measurement Channels
          </span>
          <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded font-semibold">
            {sharedChannels.length} compatible channels
          </span>
        </div>

        {(aOnlyChannels.length > 0 || bOnlyChannels.length > 0) && (
          <span className="text-[11px] font-mono text-slate-500">
            {aOnlyChannels.length} unique to A • {bOnlyChannels.length} unique to B
          </span>
        )}
      </div>

      {/* Grouped Channel Chips */}
      <div className="space-y-3 max-h-52 overflow-y-auto pr-1">
        {groupedShared.map((group) => (
          <div key={group.category} className="space-y-1.5">
            <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500">
              <span className="font-medium text-slate-800">{group.categoryLabel}</span>
              {group.unit && (
                <span className="text-[10px] text-orange-700 bg-orange-50 px-1 rounded border border-orange-200">
                  [{group.unit}]
                </span>
              )}
              <span className="text-slate-500">({group.channels.length})</span>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {group.channels.map((ch) => {
                const isActive = ch.id === activeChannelId;

                return (
                  <button
                    key={ch.id}
                    onClick={() => onSelectChannel(ch.id)}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono border transition cursor-pointer ${
                      isActive
                        ? 'bg-orange-50 border-orange-300 text-orange-900 font-semibold shadow-xs'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300 hover:text-slate-900'
                    }`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full shrink-0 ${
                        isActive ? 'bg-orange-500 animate-pulse' : 'bg-slate-400'
                      }`}
                    />
                    <span className="truncate max-w-[160px]" title={ch.label}>
                      {ch.label}
                    </span>
                    {ch.unit && (
                      <span className="text-[9px] text-slate-500">
                        {ch.unit}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
