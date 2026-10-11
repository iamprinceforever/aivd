import { createContext, useContext, type ReactNode } from "react";
import { loadReportsIndex, loadSiteData } from "./data";
import type { ReportsIndex, SiteData } from "./types";
import { useAsync } from "./useAsync";

interface Ctx {
  site?: SiteData;
  index?: ReportsIndex;
  error?: string;
  loading: boolean;
}
const SiteCtx = createContext<Ctx>({ loading: true });

export function SiteProvider({ children }: { children: ReactNode }) {
  const s = useAsync(() => Promise.all([loadSiteData(), loadReportsIndex()]), []);
  return (
    <SiteCtx.Provider value={{ site: s.data?.[0], index: s.data?.[1], error: s.error, loading: s.loading }}>
      {children}
    </SiteCtx.Provider>
  );
}
export const useSite = () => useContext(SiteCtx);
