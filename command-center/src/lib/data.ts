import type { ReportsIndex, SiteData } from "./types";

export function assetUrl(rel: string): string {
  const base = import.meta.env.BASE_URL || "/";
  return `${base}${rel.replace(/^\/+/, "")}`;
}

async function getJson<T>(rel: string): Promise<T> {
  const r = await fetch(assetUrl(rel), { credentials: "omit" });
  if (!r.ok) throw new Error(`could not load ${rel} (${r.status})`);
  return (await r.json()) as T;
}

export const loadReportsIndex = () => getJson<ReportsIndex>("reports-index.json");
export const loadSiteData = () => getJson<SiteData>("site-data.json");

export async function loadReportText(file: string): Promise<string> {
  const rel = file.replace(/^public-data\//, "");
  if (!/^reports\/[a-z0-9-]+\.md$/.test(rel)) throw new Error("invalid report path");
  const r = await fetch(assetUrl(rel), { credentials: "omit" });
  if (!r.ok) throw new Error(`could not load report (${r.status})`);
  return r.text();
}

export const CLAIM_LABELS: Record<string, string> = {
  discovery_candidate: "Discovery candidate",
  verified: "Verified",
  reproduced: "Reproduced",
  generalized: "Generalized",
  not_discovered: "Not discovered",
};
