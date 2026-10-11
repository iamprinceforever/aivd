import { useEffect, useState } from "react";
import { useMotion } from "../lib/motion";

/** Animated count-up for a REAL value. Shows the final value immediately under reduced motion. */
export function Counter({ value, label, sub }: { value: number | null; label: string; sub?: string }) {
  const { reduced } = useMotion();
  const [shown, setShown] = useState<number>(reduced || value === null ? (value ?? 0) : 0);
  useEffect(() => {
    if (value === null) return;
    if (reduced) {
      setShown(value);
      return;
    }
    let raf = 0;
    const t0 = performance.now();
    const tick = (t: number) => {
      const k = Math.min(1, (t - t0) / 900);
      setShown(Math.round(value * (1 - Math.pow(1 - k, 3))));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, reduced]);
  return (
    <div className="counter glow">
      <div className="counter-value" aria-hidden="true">
        {value === null ? "—" : shown.toLocaleString("en-US")}
      </div>
      <div className="counter-label">{label}</div>
      {sub && <div className="counter-sub">{sub}</div>}
      <span className="sr-only">{value === null ? `${label}: not verified` : `${label}: ${value}`}</span>
    </div>
  );
}
