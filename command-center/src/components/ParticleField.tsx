import { useEffect, useRef } from "react";
import { useMotion } from "../lib/motion";

/** Lightweight animated network (canvas). Fully disabled under reduced motion; pauses when the tab is hidden. */
export function ParticleField() {
  const ref = useRef<HTMLCanvasElement>(null);
  const { reduced } = useMotion();
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || reduced) return;
    const ctx = canvas.getContext?.("2d");
    if (!ctx) return;
    let raf = 0;
    let w = 0;
    let h = 0;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const n = window.innerWidth < 700 ? 26 : 48;
    const pts = Array.from({ length: n }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.00035,
      vy: (Math.random() - 0.5) * 0.00035,
    }));
    const resize = () => {
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);
    const step = () => {
      if (document.hidden) {
        raf = requestAnimationFrame(step);
        return;
      }
      ctx.clearRect(0, 0, w, h);
      for (const p of pts) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > 1) p.vx *= -1;
        if (p.y < 0 || p.y > 1) p.vy *= -1;
      }
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          const dx = (pts[i].x - pts[j].x) * w;
          const dy = (pts[i].y - pts[j].y) * h;
          const d = Math.hypot(dx, dy);
          if (d < 140) {
            ctx.strokeStyle = `rgba(94,231,255,${(1 - d / 140) * 0.18})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(pts[i].x * w, pts[i].y * h);
            ctx.lineTo(pts[j].x * w, pts[j].y * h);
            ctx.stroke();
          }
        }
      }
      for (const p of pts) {
        ctx.fillStyle = "rgba(182,156,255,0.55)";
        ctx.beginPath();
        ctx.arc(p.x * w, p.y * h, 1.6, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [reduced]);
  if (reduced) return <div className="bg-static" aria-hidden="true" data-testid="bg-static" />;
  return <canvas ref={ref} className="bg-canvas" aria-hidden="true" data-testid="bg-canvas" />;
}
