import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { useActivity } from "./activity";
import { useController } from "./controller";
import { useModels } from "./models";
import type { PipelineRun, RunSummary } from "./types";

/** The fixed, server-defined step list (mirrors controller/pipeline.py STEP_DEFS; shown when offline). */
export const PIPELINE_STEPS = [
  { id: "preflight", label: "Environment preflight" },
  { id: "guard", label: "Authorization / guard status" },
  { id: "rc6_tests", label: "RC6 research test suites" },
  { id: "full_suite", label: "Full research test suite" },
  { id: "cc_tests", label: "Command Center tests" },
  { id: "scans", label: "Publication & contamination scans" },
  { id: "model", label: "Model readiness (selected model)" },
  { id: "partb", label: "RC6 Part B experiment (guarded)" },
  { id: "summary", label: "Summary (7-state lifecycle)" },
];
export const POLL_MS = 1000;
const MAX_CLIENT_LOG = 4000;

export interface StartOpts {
  full_suite: boolean;
  partb_confirm: string;
  model_id: string;
  attempt_id: string;
  auto_pull: boolean;
}

interface Ctx {
  run: PipelineRun | null;
  history: RunSummary[];
  starting: boolean;
  error: string | null;
  start: (o: StartOpts) => Promise<string | null>;
  load: (id: string) => Promise<void>;
  loadHistory: () => Promise<void>;
}
const PipelineCtx = createContext<Ctx | null>(null);

export function PipelineProvider({ children }: { children: ReactNode }) {
  const { conn, post, get, status } = useController();
  const { log } = useActivity();
  const { refresh: refreshModels } = useModels();
  const [run, setRun] = useState<PipelineRun | null>(null);
  const [history, setHistory] = useState<RunSummary[]>([]);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runRef = useRef<PipelineRun | null>(null);
  runRef.current = run;

  const loadHistory = useCallback(async () => {
    const r = await get("/api/runs");
    if (r.code === 200) setHistory(((r.body as { runs?: RunSummary[] })?.runs ?? []).slice(0, 50));
  }, [get]);

  const load = useCallback(
    async (id: string) => {
      const r = await get(`/api/runs/${id}`);
      if (r.code === 200) {
        setRun(r.body as PipelineRun);
        setError(null);
      } else setError((r.body as { error?: string })?.error ?? `HTTP ${r.code}`);
    },
    [get],
  );

  const start = useCallback(
    async (o: StartOpts) => {
      setStarting(true);
      setError(null);
      try {
        const r = await post("run_pipeline", { ...o });
        const b = r.body as { run_id?: string; error?: string };
        if (r.code === 202 && b?.run_id) {
          log("info", `Pipeline ${b.run_id} started (fixed server-defined steps).`);
          setRun({
            id: b.run_id,
            started_at: new Date().toISOString(),
            finished_at: null,
            state: "running",
            options: { full_suite: o.full_suite, partb_handoff_requested: !!o.partb_confirm, model_id: o.model_id || null, auto_pull: o.auto_pull },
            steps: PIPELINE_STEPS.map((s) => ({ ...s, status: "PENDING", reason: "", started_at: null, ended_at: null, duration_s: null, details: {} })),
            log: [],
            verdict: null,
            total_duration_s: null,
          });
          return b.run_id;
        }
        const msg = b?.error ?? `HTTP ${r.code}`;
        setError(msg);
        log("warn", `Pipeline refused: ${msg}`);
        return null;
      } finally {
        setStarting(false);
      }
    },
    [post, log],
  );

  // Poll the running pipeline (incremental log via ?since=n). Stops when the run completes.
  const runningId = run?.state === "running" ? run.id : null;
  useEffect(() => {
    if (!runningId || conn !== "paired") return;
    let alive = true;
    const tick = async () => {
      const cur = runRef.current;
      if (!cur || cur.id !== runningId) return;
      const since = (cur.log_offset ?? 0) + cur.log.length;
      const r = await get(`/api/runs/${runningId}?since=${since}`);
      if (!alive || r.code !== 200) return;
      const d = r.body as PipelineRun;
      setRun((prev) => {
        if (!prev || prev.id !== d.id) return prev;
        const merged = [...prev.log, ...(d.log ?? [])];
        const drop = Math.max(0, merged.length - MAX_CLIENT_LOG);
        return { ...d, log: merged.slice(drop), log_offset: (prev.log_offset ?? 0) + drop };
      });
      if (d.state !== "running") {
        log(d.verdict?.overall === "PASS" ? "ok" : "warn", `Pipeline ${d.id} finished: ${d.verdict?.headline ?? d.state}`);
        void loadHistory();
        void refreshModels();
      }
    };
    void tick();
    const t = window.setInterval(() => void tick(), POLL_MS);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, [runningId, conn, get, log, loadHistory, refreshModels]);

  // Pick up a pipeline that is already running (e.g. after a page reload and re-pair).
  const serverRunning = status?.pipeline?.running_run_id ?? null;
  useEffect(() => {
    if (serverRunning && runRef.current?.id !== serverRunning) void load(serverRunning);
  }, [serverRunning, load]);

  useEffect(() => {
    if (conn === "paired") void loadHistory();
  }, [conn, loadHistory]);

  return <PipelineCtx.Provider value={{ run, history, starting, error, start, load, loadHistory }}>{children}</PipelineCtx.Provider>;
}

export function usePipeline(): Ctx {
  const c = useContext(PipelineCtx);
  if (!c) throw new Error("PipelineProvider missing");
  return c;
}

export function fmtDuration(s: number | null | undefined): string {
  if (s === null || s === undefined || !Number.isFinite(s)) return "—";
  if (s < 60) return `${s.toFixed(s < 10 ? 1 : 0)} s`;
  const m = Math.floor(s / 60);
  const r = Math.round(s - m * 60);
  return m < 60 ? `${m} min ${r} s` : `${Math.floor(m / 60)} h ${m % 60} min`;
}

/** Markdown export of a finished run (only fields the controller already redacted). */
export function runToMarkdown(r: PipelineRun): string {
  const L: string[] = [];
  L.push(`# AIVD Command Center pipeline run ${r.id}`, "");
  L.push(`- Started: ${r.started_at}`, `- Finished: ${r.finished_at ?? "—"}`, `- Total time: ${fmtDuration(r.total_duration_s)}`);
  if (r.verdict) L.push(`- Overall: **${r.verdict.overall}**`, `- Verdict: ${r.verdict.headline}`, `- Note: ${r.verdict.note}`);
  L.push("", "## Steps", "", "| Step | Status | Duration | Reason |", "|---|---|---|---|");
  for (const s of r.steps) L.push(`| ${s.label} | ${s.status} | ${fmtDuration(s.duration_s)} | ${s.reason.replace(/\|/g, "/")} |`);
  if (r.verdict) {
    L.push("", "## Lifecycle (7 states)", "");
    for (const x of r.verdict.lifecycle) L.push(`- ${x.label}: ${x.value}${x.open?.length ? ` (open: ${x.open.join(", ")})` : ""}`);
  }
  const ms = r.steps.find((s) => s.id === "model");
  const md = (ms?.details ?? {}) as { model_id?: string; selection?: string; fit?: { verdict: string; reason: string }; install_before?: string; install_after?: string; pull?: { outcome: string; duration_s: number | null } | null; verify?: { ok: boolean; reason: string } | null };
  if (ms && md.model_id) {
    L.push("", "## Model readiness", "", `- Model: \`${md.model_id}\` (${ms.status})`, `- Why chosen: ${md.selection ?? "—"}`);
    L.push(`- RAM: ${md.fit?.verdict ?? "—"}: ${md.fit?.reason ?? ""}`, `- Install: before ${md.install_before ?? "—"}, after ${md.install_after ?? "—"}`);
    L.push(`- Download: ${md.pull ? `${md.pull.outcome} in ${md.pull.duration_s ?? "—"} s` : "none needed"}`, `- Digest verification: ${md.verify ? md.verify.reason : "—"}`);
  }
  const partb = r.steps.find((s) => s.id === "partb");
  const items = partb?.details.checklist ?? [];
  if (items.length) {
    L.push("", "## RC6 Part B gate checklist", "", "| Gate | State | Reason | How to fix |", "|---|---|---|---|");
    for (const i of items) L.push(`| ${i.label} | ${i.state} | ${i.reasons.join("; ").replace(/\|/g, "/") || "—"} | ${i.fix.replace(/\|/g, "/") || "—"} |`);
  }
  for (const s of r.steps) {
    const h = s.details.failing_historical ?? [];
    const n = s.details.failing_new ?? [];
    if (h.length || n.length) {
      L.push("", `## ${s.label}: failing tests`, "");
      for (const f of n) L.push(`- NEW: \`${f}\``);
      for (const f of h) L.push(`- pre-existing/historical: \`${f}\``);
    }
  }
  if (r.excluded_tests?.length) {
    L.push("", "## Excluded tests (fixed server-side policy)", "");
    for (const e of r.excluded_tests) L.push(`- \`${e.id}\`: ${e.reason}`);
  }
  L.push("");
  return L.join("\n");
}

export function download(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
