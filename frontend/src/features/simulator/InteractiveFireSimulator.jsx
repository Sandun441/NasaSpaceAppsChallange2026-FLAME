import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  computeFirePhysics,
  SUPPORTED_FUELS,
  SIMULATION_PRESETS,
} from './firePhysicsModel';

export function InteractiveFireSimulator({ className = '' }) {
  // Simulator state parameters
  const [o2Percent, setO2Percent] = useState(20.95);
  const [gravityG, setGravityG] = useState(1.0);
  const [tempC, setTempC] = useState(20.0);
  const [pressureKpa, setPressureKpa] = useState(101.325);
  const [airflowVelocity, setAirflowVelocity] = useState(0.0);
  const [fuelType, setFuelType] = useState('pmma');
  const [isPlaying, setIsPlaying] = useState(true);
  const [showMethodology, setShowMethodology] = useState(false);
  const [activePreset, setActivePreset] = useState('earth_ref');

  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const particlesRef = useRef([]);
  const timeRef = useRef(0);

  // Compute physics state deterministically
  const physics = useMemo(() => {
    return computeFirePhysics({
      o2Percent,
      gravityG,
      tempC,
      pressureKpa,
      airflowVelocity,
      fuelType,
    });
  }, [o2Percent, gravityG, tempC, pressureKpa, airflowVelocity, fuelType]);

  // Handle Preset selection
  const handleSelectPreset = (preset) => {
    setActivePreset(preset.id);
    setO2Percent(preset.params.o2Percent);
    setGravityG(preset.params.gravityG);
    setTempC(preset.params.tempC);
    setPressureKpa(preset.params.pressureKpa);
    setAirflowVelocity(preset.params.airflowVelocity);
    setFuelType(preset.params.fuelType);
  };

  const handleReset = () => {
    handleSelectPreset(SIMULATION_PRESETS[0]);
  };

  // Canvas 2D Particle Animation Engine
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    // Set canvas dimensions
    const width = 380;
    const height = 320;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // Initialize or adapt particle pool
    const MAX_PARTICLES = 160;
    if (particlesRef.current.length === 0) {
      for (let i = 0; i < MAX_PARTICLES; i++) {
        particlesRef.current.push({
          x: 0,
          y: 0,
          vx: 0,
          vy: 0,
          life: Math.random(),
          maxLife: 0.6 + Math.random() * 0.8,
          size: 4 + Math.random() * 6,
          hue: 25,
        });
      }
    }

    let lastTime = performance.now();

    const render = (now) => {
      const dt = Math.min(0.05, (now - lastTime) / 1000);
      lastTime = now;

      if (isPlaying) {
        timeRef.current += dt;
      }

      const t = timeRef.current;
      const { visual, isExtinct, naturalFlickerHz, airflowVelocity: uAir, gravityG: gVal } = physics;

      // Clear frame with deep slate background
      ctx.fillStyle = '#090D16';
      ctx.fillRect(0, 0, width, height);

      // Draw subtle measurement grid & scale
      ctx.strokeStyle = '#1E293B';
      ctx.lineWidth = 0.5;
      for (let x = 40; x < width; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 30; y < height; y += 30) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Draw Fuel Sample Base / Burner
      const centerX = width / 2;
      const centerY = height * 0.72;

      ctx.fillStyle = '#334155';
      ctx.strokeStyle = '#475569';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.roundRect(centerX - 35, centerY, 70, 16, [3, 3, 0, 0]);
      ctx.fill();
      ctx.stroke();

      // Fuel label
      ctx.font = '9px monospace';
      ctx.fillStyle = '#94A3B8';
      ctx.textAlign = 'center';
      ctx.fillText(`${physics.fuel.formula} Sample`, centerX, centerY + 11);

      // Environment telemetry overlay in canvas
      ctx.textAlign = 'left';
      ctx.font = '10px monospace';
      ctx.fillStyle = '#64748B';
      ctx.fillText(`g: ${gVal.toFixed(2)}g | O2: ${physics.o2Percent.toFixed(1)}%`, 14, 20);
      ctx.fillText(`P: ${physics.pressureKpa.toFixed(1)} kPa | u: ${uAir.toFixed(2)} m/s`, 14, 34);

      // Gravity vector indicator
      ctx.textAlign = 'right';
      if (gVal > 0.02) {
        ctx.fillStyle = '#F97316';
        ctx.fillText(`g-vector ↓ (${gVal.toFixed(2)}g)`, width - 14, 20);
      } else {
        ctx.fillStyle = '#38BDF8';
        ctx.fillText(`Microgravity (0g)`, width - 14, 20);
      }

      if (isExtinct) {
        // Extinguished state: Draw extinguished smoke puffs
        ctx.font = '12px monospace';
        ctx.fillStyle = '#F43F5E';
        ctx.textAlign = 'center';
        ctx.fillText('FLAME EXTINGUISHED', centerX, centerY - 60);
        ctx.font = '10px monospace';
        ctx.fillStyle = '#94A3B8';
        ctx.fillText('(Below Sustained Flammability Limit)', centerX, centerY - 42);

        // Wispy smoke trail
        ctx.fillStyle = 'rgba(148, 163, 184, 0.15)';
        for (let i = 0; i < 18; i++) {
          const smokeX = centerX + Math.sin(t * 2 + i) * (8 + i * 2) + uAir * 60;
          const smokeY = centerY - 6 - i * 4;
          const smokeR = 3 + i * 1.5;
          ctx.beginPath();
          ctx.arc(smokeX, smokeY, smokeR, 0, Math.PI * 2);
          ctx.fill();
        }
      } else {
        // Active Flame Simulation
        const flickerPhase = Math.sin(t * (naturalFlickerHz * Math.PI * 2 || 3.0));
        const flickerScale = 1.0 + flickerPhase * visual.flickerAmp;

        const tiltRad = (visual.flowTiltDeg * Math.PI) / 180;
        const flameR = visual.radius * flickerScale;
        const flameH = flameR * visual.aspectRatio;

        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(tiltRad);

        // Draw Chemiluminescent Outer Halo (0g / Blue emission)
        if (visual.blueChemiRatio > 0.05) {
          const haloGrad = ctx.createRadialGradient(
            0, -flameH * 0.35, flameR * 0.2,
            0, -flameH * 0.35, flameR * 1.45
          );
          haloGrad.addColorStop(0, `rgba(56, 189, 248, ${0.45 * visual.blueChemiRatio})`);
          haloGrad.addColorStop(0.5, `rgba(14, 165, 233, ${0.25 * visual.blueChemiRatio})`);
          haloGrad.addColorStop(1, 'rgba(14, 165, 233, 0)');

          ctx.fillStyle = haloGrad;
          ctx.beginPath();
          // Microgravity: circular/spherical envelope; 1g: oval
          ctx.ellipse(0, -flameH * 0.45, flameR * 1.25, flameH * 0.65, 0, 0, Math.PI * 2);
          ctx.fill();
        }

        // Draw Core Luminous Flame (Soot & Hydrocarbon combustion)
        const coreGrad = ctx.createRadialGradient(
          0, -flameH * 0.2, flameR * 0.1,
          0, -flameH * 0.45, flameH * 0.85
        );

        if (gVal <= 0.05) {
          // Pure 0g Microgravity Flame: Hemispherical/Spherical, Blue dominant, faint amber edge
          coreGrad.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
          coreGrad.addColorStop(0.2, 'rgba(56, 189, 248, 0.85)');
          coreGrad.addColorStop(0.65, 'rgba(2, 132, 199, 0.65)');
          coreGrad.addColorStop(0.9, 'rgba(245, 158, 11, 0.3)');
          coreGrad.addColorStop(1, 'rgba(14, 165, 233, 0)');
        } else {
          // Buoyant Flame: Yellow incandescence at tip, blue at base
          coreGrad.addColorStop(0, 'rgba(255, 255, 255, 0.98)');
          coreGrad.addColorStop(0.2, 'rgba(254, 240, 138, 0.95)');
          coreGrad.addColorStop(0.55, 'rgba(249, 115, 22, 0.85)');
          coreGrad.addColorStop(0.85, 'rgba(225, 29, 72, 0.5)');
          coreGrad.addColorStop(1, 'rgba(249, 115, 22, 0)');
        }

        ctx.fillStyle = coreGrad;
        ctx.beginPath();

        if (gVal <= 0.05) {
          // Spherical/hemispherical diffusion cap
          ctx.arc(0, -flameR * 0.5, flameR, 0, Math.PI * 2);
        } else {
          // Elongated buoyant teardrop
          ctx.moveTo(-flameR * 0.65, 0);
          ctx.bezierCurveTo(
            -flameR * 0.8, -flameH * 0.35,
            -flameR * 0.3, -flameH * 0.8,
            0, -flameH * (1.05 + flickerPhase * 0.08)
          );
          ctx.bezierCurveTo(
            flameR * 0.3, -flameH * 0.8,
            flameR * 0.8, -flameH * 0.35,
            flameR * 0.65, 0
          );
          ctx.closePath();
        }
        ctx.fill();

        // Dynamic reactive particles (Soot & Convective turbulent motion)
        const activeCount = gVal > 0.05 ? MAX_PARTICLES : Math.round(MAX_PARTICLES * 0.4);
        for (let i = 0; i < activeCount; i++) {
          const p = particlesRef.current[i];
          if (isPlaying) {
            p.life += dt / p.maxLife;
            if (p.life >= 1.0) {
              p.life = 0;
              p.x = (Math.random() - 0.5) * (flameR * 0.8);
              p.y = -Math.random() * 6;
              // Microgravity: isotropic diffusion drift; Earth: strong buoyant upward acceleration
              if (gVal <= 0.05) {
                const angle = Math.random() * Math.PI * 2;
                const speed = 8 + Math.random() * 14;
                p.vx = Math.cos(angle) * speed;
                p.vy = Math.sin(angle) * speed;
              } else {
                p.vx = (Math.random() - 0.5) * 18;
                p.vy = -35 - gVal * 90 - Math.random() * 40;
              }
            }

            p.x += p.vx * dt;
            p.y += p.vy * dt;
          }

          const alpha = Math.sin(p.life * Math.PI) * (gVal <= 0.05 ? 0.35 : 0.7);
          const pSize = p.size * (1 - p.life * 0.4);

          ctx.fillStyle = gVal <= 0.05
            ? `rgba(56, 189, 248, ${alpha})`
            : `rgba(251, 146, 60, ${alpha})`;
          ctx.beginPath();
          ctx.arc(p.x, p.y, pSize, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.restore();
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [physics, isPlaying]);

  return (
    <div className={`w-full bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden text-left ${className}`}>
      {/* 1. Header Bar */}
      <div className="px-5 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50/60">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-orange-50 border border-orange-200 flex items-center justify-center text-orange-600">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2c1.1 0 2 .9 2 2 0 .7-.4 1.4-1 1.7V7c2.8 0 5 2.2 5 5 0 1.2-.4 2.3-1.1 3.2l-.7-.7C16.7 13.8 17 12.9 17 12c0-2.2-1.8-4-4-4v1.3c-.6-.3-1-1-1-1.7 0-1.1.9-2 2-2zm-2 15c-1.7 0-3-1.3-3-3 0-1.2.7-2.2 1.7-2.7L8 10.6C6.2 11.4 5 13.1 5 15c0 2.8 2.2 5 5 5 1.9 0 3.6-1.2 4.4-3l-.7-.7c-.5 1-1.5 1.7-2.7 1.7zm2-11c.6 0 1 .4 1 1s-.4 1-1 1-1-.4-1-1 .4-1 1-1z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Interactive Microgravity Fire Simulator
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-orange-100 text-orange-800 border border-orange-300 font-semibold">
                Physics-Informed
              </span>
            </div>
            <p className="text-xs text-slate-500 font-mono">
              Deterministic fluid mechanics & combustion equations • Zero LLM generation
            </p>
          </div>
        </div>

        {/* Play/Pause & Reset buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsPlaying(!isPlaying)}
            className="px-3 py-1.5 rounded-lg text-xs font-mono font-medium border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs"
            title={isPlaying ? 'Pause animation' : 'Resume animation'}
          >
            {isPlaying ? (
              <>
                <span className="w-2 h-2 bg-amber-500 rounded-xs" /> Pause
              </>
            ) : (
              <>
                <span className="w-0 h-0 border-y-4 border-y-transparent border-l-6 border-l-emerald-600" /> Resume
              </>
            )}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="px-3 py-1.5 rounded-lg text-xs font-mono border border-slate-200 bg-white hover:bg-slate-100 text-slate-600 transition-colors cursor-pointer shadow-xs"
            title="Reset to Earth 1g Reference"
          >
            ↺ Reset
          </button>
        </div>
      </div>

      {/* 2. Quick Presets Bar */}
      <div className="px-5 py-2.5 bg-slate-100/70 border-b border-slate-200 flex items-center gap-2 overflow-x-auto text-xs font-mono">
        <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold shrink-0">
          Flight Presets:
        </span>
        {SIMULATION_PRESETS.map((p) => {
          const isSelected = activePreset === p.id;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => handleSelectPreset(p)}
              className={`px-2.5 py-1 rounded-lg text-[11px] whitespace-nowrap transition-all cursor-pointer font-medium border ${
                isSelected
                  ? 'bg-orange-500 text-white border-orange-600 shadow-xs'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
              title={p.description}
            >
              {p.name}
            </button>
          );
        })}
      </div>

      {/* 3. Main Simulator Body: Canvas + Interactive Sliders */}
      <div className="p-5 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: 2D Canvas Visualization + Live Telemetry */}
        <div className="lg:col-span-5 flex flex-col items-center space-y-3">
          <div className="relative rounded-xl overflow-hidden border border-slate-800 shadow-md bg-slate-950 w-full max-w-[380px] aspect-[380/320]">
            <canvas
              ref={canvasRef}
              style={{ width: '100%', height: '100%' }}
              className="block"
            />
          </div>

          {/* Real-Time Dimensionless Numbers Grid */}
          <div className="w-full max-w-[380px] grid grid-cols-3 gap-2 text-center font-mono">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2">
              <span className="text-[10px] text-slate-500 uppercase block">Rayleigh (Ra)</span>
              <span className="text-xs font-bold text-slate-900">
                {physics.Ra > 1000 ? physics.Ra.toExponential(1) : physics.Ra}
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2">
              <span className="text-[10px] text-slate-500 uppercase block">Grashof (Gr)</span>
              <span className="text-xs font-bold text-slate-900">
                {physics.Gr > 1000 ? physics.Gr.toExponential(1) : physics.Gr}
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2">
              <span className="text-[10px] text-slate-500 uppercase block">Reynolds (Re)</span>
              <span className="text-xs font-bold text-slate-900">{physics.Re}</span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2">
              <span className="text-[10px] text-slate-500 uppercase block">P(O2) kPa</span>
              <span className="text-xs font-bold text-orange-600">{physics.pO2_kpa}</span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2">
              <span className="text-[10px] text-slate-500 uppercase block">Flame Temp</span>
              <span className="text-xs font-bold text-slate-900">{physics.flameTempK} K</span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2">
              <span className="text-[10px] text-slate-500 uppercase block">Flicker Hz</span>
              <span className="text-xs font-bold text-slate-900">
                {physics.naturalFlickerHz > 0 ? `${physics.naturalFlickerHz} Hz` : '0 (Steady)'}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Interactive Controls + Dynamic Scientific Analysis */}
        <div className="lg:col-span-7 space-y-4">
          {/* Regime Badge & Deterministic Scientific Explanation */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider font-semibold">
                Active Combustion Regime:
              </span>
              <span className={`text-[11px] font-mono px-2.5 py-0.5 rounded-full border font-bold ${physics.regimeBadgeColor}`}>
                {physics.regimeName}
              </span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed font-sans">
              {physics.regimeSummary}
            </p>
          </div>

          {/* Interactive Sliders */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            {/* Oxygen Slider */}
            <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-700 font-semibold">Oxygen (O2)</span>
                <span className="text-orange-600 font-bold bg-orange-50 px-2 py-0.5 rounded border border-orange-200">
                  {o2Percent.toFixed(1)} %
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                step="0.5"
                value={o2Percent}
                onChange={(e) => {
                  setO2Percent(parseFloat(e.target.value));
                  setActivePreset('custom');
                }}
                className="w-full accent-orange-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>0% (Quench)</span>
                <span>21% (Earth)</span>
                <span>30% (High O2)</span>
              </div>
            </div>

            {/* Gravity Slider */}
            <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-700 font-semibold">Gravity Level (g)</span>
                <span className={`font-bold px-2 py-0.5 rounded border ${gravityG <= 0.05 ? 'bg-sky-50 text-sky-800 border-sky-300' : 'bg-slate-100 text-slate-800 border-slate-200'}`}>
                  {gravityG.toFixed(2)} g
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1.0"
                step="0.02"
                value={gravityG}
                onChange={(e) => {
                  setGravityG(parseFloat(e.target.value));
                  setActivePreset('custom');
                }}
                className="w-full accent-orange-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>0.0g (ISS 0g)</span>
                <span>0.17g (Moon)</span>
                <span>1.0g (Earth)</span>
              </div>
            </div>

            {/* Ambient Pressure Slider */}
            <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-700 font-semibold">Ambient Pressure (P)</span>
                <span className="text-slate-800 font-bold bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                  {pressureKpa.toFixed(1)} kPa
                </span>
              </div>
              <input
                type="range"
                min="20"
                max="150"
                step="1"
                value={pressureKpa}
                onChange={(e) => {
                  setPressureKpa(parseFloat(e.target.value));
                  setActivePreset('custom');
                }}
                className="w-full accent-orange-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>20 kPa</span>
                <span>101.3 kPa (1 atm)</span>
                <span>150 kPa</span>
              </div>
            </div>

            {/* Airflow Velocity Slider */}
            <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-700 font-semibold">Ventilation Airflow (u)</span>
                <span className="text-slate-800 font-bold bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                  {airflowVelocity.toFixed(2)} m/s
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="0.50"
                step="0.02"
                value={airflowVelocity}
                onChange={(e) => {
                  setAirflowVelocity(parseFloat(e.target.value));
                  setActivePreset('custom');
                }}
                className="w-full accent-orange-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>0 m/s (Quiescent)</span>
                <span>0.2 m/s (Saffire)</span>
                <span>0.5 m/s</span>
              </div>
            </div>

            {/* Ambient Temperature */}
            <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-700 font-semibold">Ambient Temp (T)</span>
                <span className="text-slate-800 font-bold bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                  {tempC.toFixed(0)} °C
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={tempC}
                onChange={(e) => {
                  setTempC(parseFloat(e.target.value));
                  setActivePreset('custom');
                }}
                className="w-full accent-orange-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>0 °C</span>
                <span>20 °C (Room)</span>
                <span>100 °C</span>
              </div>
            </div>

            {/* Fuel Type Selector */}
            <div className="space-y-1.5 bg-white p-3 rounded-xl border border-slate-200">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-700 font-semibold">Combustion Fuel</span>
                <span className="text-orange-600 font-bold text-[10px] font-mono">
                  LOI: {physics.fuel.loiPercent}%
                </span>
              </div>
              <select
                value={fuelType}
                onChange={(e) => {
                  setFuelType(e.target.value);
                  setActivePreset('custom');
                }}
                className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-mono text-slate-800 focus:outline-none focus:border-orange-500 cursor-pointer"
              >
                {Object.values(SUPPORTED_FUELS).map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name} ({f.category})
                  </option>
                ))}
              </select>
              <div className="text-[10px] font-mono text-slate-500 truncate" title={physics.fuel.literatureRef}>
                Ref: {physics.fuel.literatureRef}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Scientific Honesty & Methodology Section */}
      <div className="px-5 py-3 border-t border-slate-200 bg-slate-50/70 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-600 font-mono text-[11px]">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="font-semibold text-slate-800">
            Physics-Informed Educational Simulation
          </span>
          <span className="text-slate-400">•</span>
          <span>Not a Validated CFD Prediction</span>
        </div>

        <button
          type="button"
          onClick={() => setShowMethodology(!showMethodology)}
          className="text-orange-600 hover:text-orange-700 font-mono text-xs font-semibold underline cursor-pointer"
        >
          {showMethodology ? 'Hide Governing Equations ▲' : 'View Governing Equations & Physics ▼'}
        </button>
      </div>

      {/* 5. Collapsible Methodology & Governing Equations Drawer */}
      {showMethodology && (
        <div className="px-5 py-4 border-t border-slate-200 bg-slate-50 space-y-3 font-mono text-xs text-slate-700 animate-in fade-in duration-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                Dimensionless Transport Numbers
              </h4>
              <div className="space-y-1.5 text-[11px]">
                <p>
                  <strong>Grashof Number (Gr):</strong>{' '}
                  <code className="text-slate-900 bg-slate-100 px-1 py-0.5 rounded">
                    Gr = g · β · (T_f - T_∞) · L³ / ν²
                  </code>
                  <br />
                  <span className="text-slate-500">Quantifies ratio of buoyancy forces to viscous forces. At g = 0, Gr = 0.</span>
                </p>
                <p>
                  <strong>Rayleigh Number (Ra):</strong>{' '}
                  <code className="text-slate-900 bg-slate-100 px-1 py-0.5 rounded">
                    Ra = Gr · Pr
                  </code>{' '}
                  (Pr_air ≈ 0.71)
                </p>
                <p>
                  <strong>Richardson Number (Ri):</strong>{' '}
                  <code className="text-slate-900 bg-slate-100 px-1 py-0.5 rounded">
                    Ri = Gr / Re²
                  </code>
                  <br />
                  <span className="text-slate-500">Ri &gt;&gt; 1 indicates buoyancy dominance; Ri &lt; 1 indicates forced convection dominance.</span>
                </p>
              </div>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
                Combustion & Flame Dynamics
              </h4>
              <div className="space-y-1.5 text-[11px]">
                <p>
                  <strong>Cetegen Natural Puffing Frequency:</strong>{' '}
                  <code className="text-slate-900 bg-slate-100 px-1 py-0.5 rounded">
                    f ≈ 1.5 · √(g / L)
                  </code>
                  <br />
                  <span className="text-slate-500">Periodic shear-layer instability in buoyant plume; vanishes in microgravity.</span>
                </p>
                <p>
                  <strong>Oxygen Partial Pressure:</strong>{' '}
                  <code className="text-slate-900 bg-slate-100 px-1 py-0.5 rounded">
                    P_O2 = (O2% / 100) · P
                  </code>
                </p>
                <p>
                  <strong>Extinction Threshold:</strong> Flame extinguishes deterministically when{' '}
                  <code className="text-slate-900 bg-slate-100 px-1 py-0.5 rounded">
                    O2% &lt; LOI
                  </code>{' '}
                  or{' '}
                  <code className="text-slate-900 bg-slate-100 px-1 py-0.5 rounded">
                    P &lt; 25 kPa
                  </code>.
                </p>
              </div>
            </div>
          </div>

          <p className="text-[10px] text-slate-500 leading-normal pt-1">
            * Literature Basis: Glassman & Yetter (Combustion, 4th ed.), Drysdale (Introduction to Fire Dynamics), Cetegen & Ahmed (Combust. Flame 1993), and published NASA BASS-II and Saffire-III microgravity flight findings. This module is an educational, physics-informed demonstrator, not an authoritative computational fluid dynamics (CFD) code.
          </p>
        </div>
      )}
    </div>
  );
}
