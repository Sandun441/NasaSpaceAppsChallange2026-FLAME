import React, { useState } from 'react';
import { useFlameSimulation } from '../hooks/useFlameSimulation';

export function FlameHeroEffect() {
  const { canvasRef, mode, setMode } = useFlameSimulation();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative w-full max-w-xs mx-auto flex flex-col items-center my-1 z-10">
      {/* Compact Interactive Physics Mode Selector */}
      <div className="inline-flex items-center gap-1 p-0.5 rounded-full bg-slate-100 border border-slate-200 text-[10px] font-mono shadow-xs">
        <button
          type="button"
          onClick={() => {
            setMode('microgravity');
            setIsOpen(true);
          }}
          className={`px-2.5 py-0.5 rounded-full transition-all duration-150 cursor-pointer ${
            mode === 'microgravity'
              ? 'bg-sky-100 text-sky-800 border border-sky-300 font-medium'
              : 'text-slate-600 hover:text-slate-900'
          }`}
          title="NASA Microgravity Spherical Diffusion Flame"
        >
          <span className="inline-block w-1 h-1 rounded-full bg-sky-500 mr-1 animate-pulse" />
          0g Diffusion
        </button>

        <button
          type="button"
          onClick={() => {
            setMode('buoyant');
            setIsOpen(true);
          }}
          className={`px-2.5 py-0.5 rounded-full transition-all duration-150 cursor-pointer ${
            mode === 'buoyant'
              ? 'bg-orange-100 text-orange-800 border border-orange-300 font-medium'
              : 'text-slate-600 hover:text-slate-900'
          }`}
          title="Earth 1g Upward Buoyant Plume"
        >
          <span className="inline-block w-1 h-1 rounded-full bg-orange-500 mr-1" />
          1g Buoyant
        </button>

        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-slate-500 hover:text-slate-800 px-1.5 py-0.5 text-[9px] font-mono cursor-pointer"
          title={isOpen ? 'Hide flame preview' : 'Show flame physics simulation preview'}
        >
          {isOpen ? '▲' : '▼ Visual'}
        </button>
      </div>

      {/* Collapsible/Compact Visualizer Canvas */}
      {isOpen && (
        <div className="relative w-48 h-20 flex items-center justify-center overflow-hidden rounded-lg mt-1 border border-slate-200 bg-slate-950 animate-in fade-in duration-200">
          <canvas
            ref={canvasRef}
            className="w-full h-full block cursor-pointer"
            title="NASA Microgravity vs Earth 1g simulation"
          />
          <div
            className={`absolute inset-0 pointer-events-none transition-colors duration-500 ${
              mode === 'buoyant'
                ? 'bg-gradient-to-t from-orange-500/10 via-transparent to-transparent'
                : 'bg-gradient-to-t from-sky-500/10 via-transparent to-transparent'
            }`}
          />
        </div>
      )}
    </div>
  );
}
