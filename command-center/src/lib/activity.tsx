import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

export interface ActivityEntry {
  at: string;
  kind: "info" | "warn" | "error" | "ok";
  text: string;
}
interface Ctx {
  entries: ActivityEntry[];
  log: (kind: ActivityEntry["kind"], text: string) => void;
}
const ActivityCtx = createContext<Ctx>({ entries: [], log: () => {} });

/** In-memory only: nothing is persisted in browser storage or cookies. */
export function ActivityProvider({ children }: { children: ReactNode }) {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const log = useCallback((kind: ActivityEntry["kind"], text: string) => {
    setEntries((e) => [{ at: new Date().toISOString(), kind, text }, ...e].slice(0, 200));
  }, []);
  return <ActivityCtx.Provider value={{ entries, log }}>{children}</ActivityCtx.Provider>;
}
export const useActivity = () => useContext(ActivityCtx);
