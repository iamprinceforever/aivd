import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import catalogJson from "../../controller/models_catalog.json";
import { useActivity } from "./activity";
import { useController } from "./controller";
import type { ModelEntry, ModelsListing, RamEstimate } from "./types";

/**
 * Model picker state. With a paired local controller the list comes from GET /api/models (installed models are
 * read from the configured store's manifests; RAM from /proc; listing never starts Ollama). Without a controller
 * (e.g. on GitHub Pages) only the bundled catalog is shown, read-only: fit and install status are "Not verified".
 */
interface RawCatalogModel {
  name: string;
  family: string;
  params?: string;
  quant?: string;
  rc6_allowlisted?: boolean;
  size_bytes: number;
  size_is_exact?: boolean;
  arch: { layers: number; kv_heads: number; head_dim: number };
  pins: { manifest_sha256: string; model_blob_sha256: string } | null;
}
interface RawCatalog {
  estimate: { num_ctx: number; kv_bytes_per_element: number; compute_overhead_mib: number; runtime_overhead_mib: number; headroom_mib: number };
  models: RawCatalogModel[];
}
const MIB = 1024 * 1024;

export function estimateRam(m: RawCatalogModel, est: RawCatalog["estimate"]): RamEstimate {
  const w = m.size_bytes / MIB;
  const kv = (2 * m.arch.layers * m.arch.kv_heads * m.arch.head_dim * est.kv_bytes_per_element * est.num_ctx) / MIB;
  const total = w + kv + est.compute_overhead_mib + est.runtime_overhead_mib;
  return {
    weights_mib: Math.round(w),
    kv_cache_mib: Math.round(kv),
    compute_mib: est.compute_overhead_mib,
    runtime_mib: est.runtime_overhead_mib,
    headroom_mib: est.headroom_mib,
    estimate_kb: Math.floor(total * 1024),
    recommended_kb: Math.floor((total + est.headroom_mib) * 1024),
    num_ctx: est.num_ctx,
    approximate: !m.size_is_exact,
  };
}

/** Bundled catalog as read-only entries (no fit/install verdicts: those need the local controller). */
export const STATIC_CATALOG: ModelEntry[] = (catalogJson as unknown as RawCatalog).models.map((m) => {
  const ram = estimateRam(m, (catalogJson as unknown as RawCatalog).estimate);
  const allow = m.rc6_allowlisted === true;
  return {
    name: m.name,
    family: m.family,
    params: m.params ?? "",
    quant: m.quant ?? "",
    rc6_allowlisted: allow,
    size_bytes: m.size_bytes,
    size_is_exact: m.size_is_exact === true,
    pins: m.pins,
    ram,
    fit: { verdict: "NOT_VERIFIED", reason: "Requires the local controller (reads MemAvailable)", required_kb: ram.estimate_kb, recommended_kb: ram.recommended_kb, available_kb: null, total_kb: null },
    install: { status: "not_verified", reason: "Requires the local controller (reads the model store)" },
    part_b_eligible: allow,
    part_b_note: allow ? "in the RC6 preregistration allowlist (Part B still needs every gate)" : "catalog extra: NOT in the RC6 preregistration allowlist; it can never be used for Part B",
  };
});

export const fmtGB = (bytes: number) => (bytes < 1e7 ? `${(bytes / 1e6).toFixed(1)} MB` : `${(bytes / 1e9).toFixed(bytes < 1e9 ? 2 : 1)} GB`);
export const fmtKB = (kb: number | null | undefined) => (kb === null || kb === undefined ? "—" : `${(kb / 1024 / 1024).toFixed(2)} GiB`);

interface Ctx {
  data: ModelsListing | null;
  live: boolean;
  entries: ModelEntry[];
  selected: string | null;
  selectedEntry: ModelEntry | null;
  select: (name: string) => void;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  pull: (name: string) => Promise<{ ok: boolean; message: string }>;
  cancelPull: () => Promise<void>;
}
const ModelsCtx = createContext<Ctx | null>(null);
const POLL_MS = 1000;

export function ModelsProvider({ children }: { children: ReactNode }) {
  const { conn, get, post } = useController();
  const { log } = useActivity();
  const [data, setData] = useState<ModelsListing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const userPicked = useRef(false);
  const live = conn === "paired" && data !== null;

  const refresh = useCallback(async () => {
    if (conn !== "paired") return;
    setLoading(true);
    try {
      const r = await get("/api/models");
      if (r.code === 200) {
        setData(r.body as ModelsListing);
        setError(null);
      } else setError((r.body as { error?: string })?.error ?? `HTTP ${r.code}`);
    } finally {
      setLoading(false);
    }
  }, [conn, get]);

  useEffect(() => {
    if (conn === "paired") void refresh();
    else setData(null);
  }, [conn, refresh]);

  // Auto-select the controller's recommendation until the operator picks one themselves.
  useEffect(() => {
    if (!data) return;
    const names = data.catalog.map((e) => e.name);
    if (!userPicked.current || !selected || !names.includes(selected)) {
      setSelected(data.recommendation.model_id ?? null);
    }
  }, [data, selected]);

  const pulling = data?.pull?.state === "running";
  useEffect(() => {
    if (!pulling || conn !== "paired") return;
    const t = window.setInterval(() => void refresh(), POLL_MS);
    return () => window.clearInterval(t);
  }, [pulling, conn, refresh]);

  const pull = useCallback(
    async (name: string) => {
      const r = await post("pull_model", { model_id: name });
      const b = (r.body ?? {}) as { status?: string; error?: string; reasons?: string[] };
      let msg: string;
      if (r.code === 202) msg = `Download of ${name} started (local controller, 127.0.0.1 only).`;
      else if (r.code === 200) msg = `${name} is already installed.`;
      else msg = `Download refused: ${b.reasons?.join("; ") ?? b.error ?? `HTTP ${r.code}`}`;
      log(r.code === 202 || r.code === 200 ? "info" : "warn", msg);
      void refresh();
      return { ok: r.code === 202 || r.code === 200, message: msg };
    },
    [post, log, refresh],
  );

  const cancelPull = useCallback(async () => {
    const r = await post("cancel_pull", {});
    log("info", r.code === 202 ? "Download cancel requested." : "No download in progress.");
    void refresh();
  }, [post, log, refresh]);

  const select = useCallback((name: string) => {
    userPicked.current = true;
    setSelected(name);
  }, []);

  const entries = useMemo(() => (live && data ? data.catalog : STATIC_CATALOG), [live, data]);
  const selectedEntry = entries.find((e) => e.name === selected) ?? null;
  return (
    <ModelsCtx.Provider value={{ data, live, entries, selected: live ? selected : null, selectedEntry: live ? selectedEntry : null, select, loading, error, refresh, pull, cancelPull }}>
      {children}
    </ModelsCtx.Provider>
  );
}

export function useModels(): Ctx {
  const c = useContext(ModelsCtx);
  if (!c) throw new Error("ModelsProvider missing");
  return c;
}
