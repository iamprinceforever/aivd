import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type MotionPref = "system" | "reduce" | "full";
interface MotionCtx {
  pref: MotionPref;
  setPref: (p: MotionPref) => void;
  reduced: boolean;
}
const Ctx = createContext<MotionCtx>({ pref: "system", setPref: () => {}, reduced: true });

function systemReduced(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return true;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function MotionProvider({ children }: { children: ReactNode }) {
  const [pref, setPref] = useState<MotionPref>("system");
  const [sys, setSys] = useState<boolean>(systemReduced);
  useEffect(() => {
    if (!window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const on = () => setSys(mq.matches);
    mq.addEventListener?.("change", on);
    return () => mq.removeEventListener?.("change", on);
  }, []);
  const reduced = pref === "reduce" || (pref === "system" && sys);
  useEffect(() => {
    document.documentElement.dataset.motion = reduced ? "reduced" : "full";
  }, [reduced]);
  return <Ctx.Provider value={{ pref, setPref, reduced }}>{children}</Ctx.Provider>;
}

export const useMotion = () => useContext(Ctx);
