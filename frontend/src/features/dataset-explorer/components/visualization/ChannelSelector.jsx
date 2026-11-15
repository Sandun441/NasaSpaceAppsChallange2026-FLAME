import React, { useMemo } from 'react';

/**
 * ChannelSelector
 * Grouped measurement channel selector with real-time physical unit compatibility analysis.
 */
export function ChannelSelector({
  availableChannels = [],
  selectedChannelIds = [],
  axisCompatibility,
  onToggleChannel,
  onClearSelection,
  onSelectAllInCategory,
}) {
  // Group available channels by category
  const groupedChannels = useMemo(() => {
    const map = new Map();
    availableChannels.forEach((ch) => {
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
  }, [availableChannels]);

  return (
    <div className="space-y-3 bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
      {/* Header and Quick Actions */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
            Measurement Channels
          </span>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            {selectedChannelIds.length} of {availableChannels.length} active
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onClearSelection}
            disabled={selectedChannelIds.length === 0}
            className="text-[11px] font-mono text-slate-500 hover:text-rose-600 disabled:opacity-40 transition cursor-pointer"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Axis Compatibility & Scientific Safeguard Alert */}
      {axisCompatibility && (
        <div>
          {axisCompatibility.mode === 'single' && (
            <div className="flex items-center gap-2 text-xs font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Single Y-Axis: Uniform scale [{axisCompatibility.leftUnit}]</span>
            </div>
          )}

          {axisCompatibility.mode === 'dual' && (
            <div className="flex items-center gap-2 text-xs font-mono text-indigo-800 bg-indigo-50 border border-indigo-200 px-3 py-1.5 rounded-lg font-semibold">
              <span className="w-2 h-2 rounded-full bg-indigo-500" />
              <span>
                Dual Y-Axes: Left = [{axisCompatibility.leftUnit}], Right = [{axisCompatibility.rightUnit}]
              </span>
            </div>
          )}

          {axisCompatibility.mode === 'incompatible' && (
            <div className="flex items-start gap-2 text-xs font-mono text-rose-800 bg-rose-50 border border-rose-200 p-2.5 rounded-lg font-semibold">
              <span className="text-sm">⚠️</span>
              <div className="space-y-1">
                <span className="font-semibold">Scientific Safeguard: Incompatible Units Detected</span>
                <p className="text-[11px] text-rose-700 leading-tight font-normal">
                  {axisCompatibility.message}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Grouped Category Accordions / Channel Chips */}
      <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
        {groupedChannels.map((group) => {
          const activeInGroup = group.channels.filter((c) =>
            selectedChannelIds.includes(c.id)
          ).length;

          return (
            <div key={group.category} className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                <span className="font-medium text-slate-800 flex items-center gap-1.5">
                  <span>{group.categoryLabel}</span>
                  {group.unit && (
                    <span className="text-[10px] text-orange-700 bg-orange-50 px-1 rounded border border-orange-200">
                      [{group.unit}]
                    </span>
                  )}
                  <span className="text-slate-500">
                    ({activeInGroup}/{group.channels.length})
                  </span>
                </span>
                <button
                  onClick={() => onSelectAllInCategory(group.category)}
                  className="text-[10px] text-slate-500 hover:text-orange-600 transition cursor-pointer"
                >
                  Select Group
                </button>
              </div>

              {/* Channel Chips */}
              <div className="flex flex-wrap gap-1.5">
                {group.channels.map((ch) => {
                  const isSelected = selectedChannelIds.includes(ch.id);

                  return (
                    <button
                      key={ch.id}
                      onClick={() => onToggleChannel(ch.id)}
                      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono border transition cursor-pointer ${
                        isSelected
                          ? 'bg-orange-50 border-orange-300 text-orange-900 font-semibold shadow-xs'
                          : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300 hover:text-slate-900'
                      }`}
                    >
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: isSelected ? ch.color : '#94a3b8' }}
                      />
                      <span className="truncate max-w-[150px]" title={ch.label}>
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
          );
        })}
      </div>
    </div>
  );
}
