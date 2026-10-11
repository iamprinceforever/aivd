import { render, screen, waitFor } from "@testing-library/react";
import App from "../src/App";
import { setControllerHandler } from "./setup";
import type { ControllerStatus, ModelEntry, ModelsListing } from "../src/lib/types";
import { STATIC_CATALOG } from "../src/lib/models";

export async function renderApp(route = "/", initialBase: string | null = null) {
  window.location.hash = `#${route}`;
  const r = render(<App initialBase={initialBase} />);
  await screen.findByRole("heading", { level: 1 }, { timeout: 3000 });
  await waitFor(() => expect(screen.queryByText("Loading bundled data…")).toBeNull(), { timeout: 3000 });
  return r;
}

export const BASE = "http://127.0.0.1:8765";

function gate(id: string, state: "PASS" | "FAIL" | "NOT_VERIFIED", reasons: string[] = []) {
  return { id, label: id, state, reasons };
}

/** A controller status as the real controller returns it when the guard refuses (the expected state today). */
export function refusingStatus(): ControllerStatus {
  const refuse = ["no APPROVED RC6_APPROVALS.json", "G_AUDIT: historical protected-path audit is not resolved"];
  return {
    controller: { version: "0.1.0", launch_id: "abcd1234" },
    memory: { state: "FAIL", mem_available_kb: 6640000, threshold_kb: 7600000, reason: "MemAvailable 6640000 kB < 7600000 kB" },
    runtime: { state: "NOT_VERIFIED", reason: "no runtime files configured", files: [], ollama_process_running: false, started_by_controller: false },
    worktrees: [{ name: "rc6-diag", branch: "research/x", head: "cb8dc31fc0c7", modified: 0, untracked: 5, diff_sha256: "e3b0c44298fc" }],
    guard: { available: true, actions: { START_RUNTIME: refuse, MODEL_CALL: refuse, REVEAL: ["G_VALIDITY: validity gates not built"], SCORE: ["G_VALIDITY: validity gates not built"] } },
    lifecycle: {
      software_built: { state: "PASS", reasons: [] },
      runtime_available: { state: "NOT_VERIFIED", reasons: ["no runtime files configured"] },
      prerequisites_satisfied: { state: "FAIL", reasons: ["MODEL_CALL: G_AUDIT: historical protected-path audit is not resolved"] },
      explicitly_authorized: { state: "FAIL", reasons: ["MODEL_CALL: no APPROVED RC6_APPROVALS.json"] },
      running: { state: "FAIL", reasons: ["no run in progress"] },
      completed: { state: "FAIL", reasons: ["no completed run in this controller session"] },
      independently_validated: { state: "NOT_VERIFIED", reasons: ["requires an independent human reviewer; the controller never asserts this"] },
    },
    ops: {
      rc6_run: {
        available: false,
        gates: [gate("ENTRY", "PASS"), gate("GUARD_START_RUNTIME", "FAIL", refuse), gate("GUARD_MODEL_CALL", "FAIL", refuse), gate("PARTB_ENV", "FAIL", ["AIVD_RC6_PARTB_AUTHORIZED not present in the controller's inherited environment"]), gate("MEMORY", "FAIL", ["MemAvailable 6640000 kB < 7600000 kB"])],
      },
      rc6_reveal: { available: false, gates: [gate("GUARD_REVEAL", "FAIL", ["G_VALIDITY: validity gates not built"])] },
      cancel: { available: false, reason: "the RC6 entry script documents no cancel operation; the controller will not signal it" },
    },
    run: { state: "idle" },
    allowed_models: ["qwen3:1.7b", "llama3.2:3b", "qwen3:8b"],
  };
}

export function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

export function installController(opts: { status?: ControllerStatus; code?: string; onOp?: (url: string, init?: RequestInit) => Response; onGet?: (url: string) => Response | null } = {}) {
  const calls: { url: string; init?: RequestInit }[] = [];
  setControllerHandler((url, init) => {
    if (!url.startsWith(BASE)) return null;
    calls.push({ url, init });
    if (url.endsWith("/api/health")) return json({ service: "aivd-command-center-controller", version: "0.1.0", pairing_required: true });
    if (url.endsWith("/api/pair")) {
      const b = JSON.parse(String(init?.body ?? "{}"));
      return b.code === (opts.code ?? "AB12-CD34-EF56") ? json({ session: "sess.tok", csrf: "csrf-tok", idle_timeout_s: 1800 }) : json({ error: "wrong pairing code" }, 403);
    }
    if (url.endsWith("/api/status")) return json(opts.status ?? refusingStatus());
    if (url.includes("/api/ops/")) return opts.onOp ? opts.onOp(url, init) : json({ status: "REFUSED", gates: [] }, 403);
    if (url.endsWith("/api/models")) {
      const r = opts.onGet?.(url);
      return r ?? json(modelsListing());
    }
    if (url.includes("/api/runs")) {
      const r = opts.onGet?.(url);
      if (r) return r;
      if (url.endsWith("/api/runs")) return json({ runs: [] });
    }
    return json({ error: "unknown operation" }, 404);
  });
  return calls;
}

/** A GET /api/models response shaped like the real controller's (MemAvailable 6.5 GB, CPU only, balloon present). */
export function modelsListing(over: Partial<ModelsListing> = {}): ModelsListing {
  const avail = 6_500_000;
  const entry = (name: string, install: ModelEntry["install"]["status"]): ModelEntry => {
    const e = STATIC_CATALOG.find((x) => x.name === name)!;
    const need = e.ram.estimate_kb;
    const verdict = avail < need ? "EXCEEDS" : avail < e.ram.recommended_kb ? "TIGHT" : "FITS";
    return {
      ...e,
      fit: { verdict, reason: `needs ~${need} kB, MemAvailable is ${avail} kB${verdict === "EXCEEDS" ? ": NOT RECOMMENDED, will likely OOM" : ""}`, required_kb: need, recommended_kb: e.ram.recommended_kb, available_kb: avail, total_kb: 16_397_616 },
      install: { status: install, reason: install === "installed" ? "manifest and weights digests match the pins" : "not in the configured model store" },
      group: verdict === "EXCEEDS" ? "too_large" : install === "installed" ? "installed_fits" : "fits_not_installed",
    };
  };
  return {
    system: { mem_total_kb: 16_397_616, mem_available_kb: avail, swap_total_kb: 0, rc6_memory_gate_kb: 7_600_000, rc6_memory_gate_met: false, cpu_count: 8, cpu_model: "Intel(R) Xeon(R) Processor", gpu: { present: false, kinds: [], render_nodes: 0 }, balloon: true, notes: ["virtio_balloon driver present: MemAvailable can change.", "No GPU compute device found: models run on the CPU only."] },
    catalog: [entry("llama3.2:3b", "installed"), entry("qwen3:1.7b", "installed"), entry("qwen3:0.6b", "missing"), entry("qwen3:4b", "missing"), entry("llama3.2:1b", "missing"), entry("qwen3:8b", "installed")],
    installed_other: [],
    recommendation: { model_id: "llama3.2:3b", reason: "best installed model that fits MemAvailable (RC6-allowlisted first, then largest that fits)" },
    pull: null,
    policy: { store_configured: true, pull_enabled: true, pull_disabled_reason: "", listing_starts_ollama: false, rc6_allowlist: ["qwen3:1.7b", "llama3.2:3b", "qwen3:8b"] },
    ...over,
  };
}
