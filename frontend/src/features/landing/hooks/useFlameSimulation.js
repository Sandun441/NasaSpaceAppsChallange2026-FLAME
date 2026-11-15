import { useEffect, useRef, useState } from 'react';

/**
 * useFlameSimulation:
 * High-performance, realistic flowing fire simulation on HTML5 Canvas.
 * Models fluid thermal convection, temperature-based blackbody coloration,
 * organic turbulence, and ember dynamics.
 */
export function useFlameSimulation(_options = {}) {
  const canvasRef = useRef(null);
  const animationFrameId = useRef(null);
  const [mode, setMode] = useState('microgravity'); // 'microgravity' (spherical cool flame) or 'buoyant' (convective flowing flame)

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width = (canvas.width = canvas.parentElement?.clientWidth || 400);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 280);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };

    window.addEventListener('resize', handleResize);

    // Particle pool for zero garbage collection overhead
    const MAX_PARTICLES = 160;
    const MAX_EMBERS = 25;
    const particles = [];
    const embers = [];

    class FlameParticle {
      constructor() {
        this.reset();
      }

      reset() {
        this.x = width / 2 + (Math.random() - 0.5) * (mode === 'microgravity' ? 24 : 32);
        this.y = mode === 'microgravity' ? height / 2 + 15 : height - 25;
        this.vx = (Math.random() - 0.5) * (mode === 'microgravity' ? 0.7 : 0.9);
        this.vy = mode === 'microgravity' 
          ? (Math.random() - 0.5) * 0.7 - 0.1 
          : -(Math.random() * 2.2 + 1.2);
        this.life = 0;
        this.maxLife = mode === 'microgravity' 
          ? Math.random() * 60 + 50 
          : Math.random() * 55 + 40;
        this.size = mode === 'microgravity' 
          ? Math.random() * 22 + 14 
          : Math.random() * 18 + 10;
        this.heat = 1.0; // 1.0 = hottest core, 0.0 = dissipated smoke
        this.swaySpeed = Math.random() * 0.08 + 0.04;
        this.swayOffset = Math.random() * Math.PI * 2;
      }

      update(time) {
        this.life++;
        const progress = this.life / this.maxLife;
        this.heat = Math.max(0, 1 - progress);

        // Turbulence and buoyant lift
        if (mode === 'buoyant') {
          this.x += this.vx + Math.sin(time * this.swaySpeed + this.swayOffset) * 0.45;
          this.y += this.vy;
          this.vy -= 0.02; // Buoyancy acceleration
          this.size = (1 - progress * 0.4) * (this.maxLife * 0.35);
        } else {
          // Microgravity: isotropic diffusion & spherical boundary
          const angle = Math.atan2(this.y - height / 2, this.x - width / 2);
          this.x += Math.cos(angle) * 0.3 + this.vx * 0.5;
          this.y += Math.sin(angle) * 0.3 + this.vy * 0.5;
          this.size = (1 - progress * 0.2) * (this.maxLife * 0.45);
        }

        if (this.life >= this.maxLife) {
          this.reset();
        }
      }

      draw(context) {
        const rad = Math.max(1, this.size);
        const grad = context.createRadialGradient(this.x, this.y, 0, this.x, this.y, rad);

        if (mode === 'buoyant') {
          // Convective fire palette: White core -> Bright Yellow -> Fiery Orange -> Deep Red/Smoke
          if (this.heat > 0.75) {
            grad.addColorStop(0, `rgba(255, 255, 240, ${0.85 * this.heat})`);
            grad.addColorStop(0.3, `rgba(255, 215, 60, ${0.75 * this.heat})`);
            grad.addColorStop(0.7, `rgba(255, 100, 15, ${0.45 * this.heat})`);
            grad.addColorStop(1, 'rgba(180, 25, 0, 0)');
          } else if (this.heat > 0.35) {
            grad.addColorStop(0, `rgba(255, 170, 30, ${0.7 * this.heat})`);
            grad.addColorStop(0.5, `rgba(240, 70, 10, ${0.4 * this.heat})`);
            grad.addColorStop(1, 'rgba(80, 15, 0, 0)');
          } else {
            grad.addColorStop(0, `rgba(200, 45, 10, ${0.35 * this.heat})`);
            grad.addColorStop(0.6, `rgba(70, 15, 10, ${0.15 * this.heat})`);
            grad.addColorStop(1, 'rgba(20, 5, 5, 0)');
          }
        } else {
          // NASA Microgravity Cool Flame palette: Pale cyan/blue core -> Ghostly azure diffusion sphere -> Faint amber fringe
          if (this.heat > 0.7) {
            grad.addColorStop(0, `rgba(210, 245, 255, ${0.85 * this.heat})`);
            grad.addColorStop(0.4, `rgba(56, 189, 248, ${0.65 * this.heat})`);
            grad.addColorStop(0.8, `rgba(37, 99, 235, ${0.35 * this.heat})`);
            grad.addColorStop(1, 'rgba(30, 58, 138, 0)');
          } else if (this.heat > 0.3) {
            grad.addColorStop(0, `rgba(96, 165, 250, ${0.55 * this.heat})`);
            grad.addColorStop(0.6, `rgba(147, 51, 234, ${0.25 * this.heat})`);
            grad.addColorStop(1, 'rgba(15, 23, 42, 0)');
          } else {
            grad.addColorStop(0, `rgba(249, 115, 22, ${0.2 * this.heat})`);
            grad.addColorStop(0.6, `rgba(225, 29, 72, ${0.1 * this.heat})`);
            grad.addColorStop(1, 'rgba(2, 6, 23, 0)');
          }
        }

        context.fillStyle = grad;
        context.beginPath();
        context.arc(this.x, this.y, rad, 0, Math.PI * 2);
        context.fill();
      }
    }

    class EmberParticle {
      constructor() {
        this.reset();
      }

      reset() {
        this.x = width / 2 + (Math.random() - 0.5) * (mode === 'microgravity' ? 30 : 40);
        this.y = mode === 'microgravity' ? height / 2 + (Math.random() - 0.5) * 20 : height - 30;
        this.vx = (Math.random() - 0.5) * 0.8;
        this.vy = mode === 'microgravity' ? (Math.random() - 0.5) * 0.6 : -(Math.random() * 2.8 + 1.0);
        this.size = Math.random() * 1.8 + 0.8;
        this.alpha = Math.random() * 0.8 + 0.2;
        this.life = 0;
        this.maxLife = Math.random() * 70 + 40;
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life++;
        this.alpha = (1 - this.life / this.maxLife) * 0.9;
        if (this.life >= this.maxLife) {
          this.reset();
        }
      }

      draw(context) {
        context.fillStyle = mode === 'buoyant'
          ? `rgba(255, 190, 80, ${this.alpha})`
          : `rgba(147, 197, 253, ${this.alpha})`;
        context.beginPath();
        context.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        context.fill();
      }
    }

    // Initialize particle arrays
    for (let i = 0; i < MAX_PARTICLES; i++) {
      const p = new FlameParticle();
      p.life = Math.floor(Math.random() * p.maxLife); // Stagger
      particles.push(p);
    }
    for (let i = 0; i < MAX_EMBERS; i++) {
      const e = new EmberParticle();
      e.life = Math.floor(Math.random() * e.maxLife);
      embers.push(e);
    }

    let time = 0;

    const render = () => {
      time += 0.05;
      ctx.clearRect(0, 0, width, height);

      // Base thermal glow backdrop
      const centerX = width / 2;
      const centerY = mode === 'microgravity' ? height / 2 : height - 40;
      const glowGrad = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, mode === 'microgravity' ? 90 : 120
      );

      if (mode === 'buoyant') {
        glowGrad.addColorStop(0, 'rgba(255, 120, 20, 0.22)');
        glowGrad.addColorStop(0.5, 'rgba(255, 60, 0, 0.08)');
        glowGrad.addColorStop(1, 'rgba(2, 6, 23, 0)');
      } else {
        glowGrad.addColorStop(0, 'rgba(56, 189, 248, 0.25)');
        glowGrad.addColorStop(0.5, 'rgba(37, 99, 235, 0.09)');
        glowGrad.addColorStop(1, 'rgba(2, 6, 23, 0)');
      }

      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, mode === 'microgravity' ? 90 : 120, 0, Math.PI * 2);
      ctx.fill();

      // Draw flowing particles with additive screen blending for luminosity
      ctx.globalCompositeOperation = 'screen';

      for (let i = 0; i < particles.length; i++) {
        particles[i].update(time);
        particles[i].draw(ctx);
      }

      for (let i = 0; i < embers.length; i++) {
        embers[i].update();
        embers[i].draw(ctx);
      }

      // Reset composite operation
      ctx.globalCompositeOperation = 'source-over';

      // Burner source / droplet anchor indicator (clean scientific representation)
      ctx.fillStyle = mode === 'microgravity' ? 'rgba(148, 163, 184, 0.6)' : 'rgba(203, 213, 225, 0.5)';
      ctx.beginPath();
      if (mode === 'microgravity') {
        // MDCA fuel droplet suspension
        ctx.arc(centerX, centerY, 2.5, 0, Math.PI * 2);
      } else {
        // Flat circular burner orifice
        ctx.ellipse(centerX, centerY + 20, 16, 4, 0, 0, Math.PI * 2);
      }
      ctx.fill();

      animationFrameId.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, [mode]);

  return { canvasRef, mode, setMode };
}
