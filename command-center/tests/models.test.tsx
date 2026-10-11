import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { BASE, installController, json, modelsListing, refusingStatus, renderApp } from "./helpers";
import { setReducedMotion } from "./setup";
import { STATIC_CATALOG, estimateRam } from "../src/lib/models";
import catalog from "../controller/models_catalog.json";
import type { ControllerStatus, ModelsListing, PipelineRun, PullJob } from "../src/lib/types";

const RID = "r20261011T031500-abc123";
const STEPS: [string, string][] = [
  ["preflight", "Environment preflight"], ["guard", "Authorization / guard status"], ["rc6_tests", "RC6 research test suites"],
  ["full_suite", "Full research test suite"], ["cc_tests", "Command Center tests"], ["scans", "Publication & contamination scans"],
  ["model", "Model readiness (selected model)"], ["partb", "RC6 Part B experiment (guarded)"], ["summary", "Summary (7-state lifecycle)"],
];
const status = (): ControllerStatus => ({ ...refusingStatus(), pipeline: { available: true, running_run_id: null, steps: STEPS.map(([id, label]) => ({ id, label })) } });

function pullJob(state: PullJob["state"], percent: number): PullJob {
  return {
    id: "p1", model_id: "qwen3:4b", origin: "operator", state, started_at: "2026-10-11T03:00:00+05:30", finished_at: state === "running" ? null : "2026-10-11T03:01:00+05:30",
    duration_s: state === "running" ? null : 60.2,
    progress: { status: state === "running" ? "pulling 3d0b790534fe" : "success", percent, completed: percent * 25_000_000, total: 2_500_000_000, layers: [{ digest: "3d0b790534fe", total: 2_500_000_000, completed: percent * 25_000_000, percent }] },
    log: [], result: state === "running" ? null : { outcome: "succeeded", reason: "downloaded and verified" },
  };
}

async function paired(route: string, opts: Parameters<typeof installController>[0] = {}) {
  const calls = installController({ status: status(), ...opts });
  await renderApp("/settings", BASE);
  const user = userEvent.setup();
  await screen.findByText("FOUND, NOT PAIRED");
  await user.type(screen.getByLabelText(/One-time pairing code/), "AB12-CD34-EF56");
  await user.click(screen.getByRole("button", { name: "Pair" }));
  await screen.findByText("PAIRED");
  await user.click(within(screen.getByRole("navigation", { name: "Sections" })).getByRole("link", { name: new RegExp(route) }));
  return { calls, user };
}

const picker = () => screen.getByRole("region", { name: "Model for vulnerability testing" });

describe("model picker", () => {
  it("client RAM estimate mirrors the controller formula (qwen3:8b KV 1152 MiB at num_ctx 8192)", () => {
    const q8 = (catalog as { models: { name: string }[] }).models.find((m) => m.name === "qwen3:8b")!;
    const ram = estimateRam(q8 as never, (catalog as never as { estimate: never }).estimate);
    expect(ram.kv_cache_mib).toBe(1152);
    expect(ram.weights_mib).toBe(4983);
    expect(ram.recommended_kb - ram.estimate_kb).toBe(1024 * 1024);
    expect(STATIC_CATALOG.filter((m) => m.rc6_allowlisted).map((m) => m.name).sort()).toEqual(["llama3.2:3b", "qwen3:1.7b", "qwen3:8b"]);
    for (const m of STATIC_CATALOG.filter((x) => !x.rc6_allowlisted)) expect(m.pins).toBeNull();
  });

  it("static build: picker is visible read-only with 'Requires local controller' and nothing selectable", async () => {
    await renderApp("/pipeline");
    const p = picker();
    expect(within(p).getByText(/Requires local controller\./)).toBeInTheDocument();
    const radios = within(p).getAllByRole("radio");
    expect(radios.length).toBe(STATIC_CATALOG.length);
    radios.forEach((r) => expect(r).toBeDisabled());
    expect(within(p).getByRole("button", { name: "Download selected" })).toBeDisabled();
    expect(within(p).getAllByText("Not verified").length).toBeGreaterThanOrEqual(STATIC_CATALOG.length);
    expect(within(p).getByText("qwen3:8b")).toBeInTheDocument();
  });

  it("lists models grouped installed+fits → needs download → too large, auto-selects the recommendation, filters by search", async () => {
    const { user } = await paired("Run Pipeline");
    const p = picker();
    await within(p).findByText(/MemTotal/);
    const titles = within(p).getAllByRole("heading", { level: 3 }).map((h) => h.textContent);
    expect(titles[0]).toMatch(/Installed and fits/);
    expect(titles[1]).toMatch(/needs a download/);
    expect(titles[2]).toMatch(/NOT RECOMMENDED/);
    await waitFor(() => expect(within(p).getByRole("radio", { name: /llama3\.2:3b/ })).toBeChecked());
    const q8 = within(p).getByRole("radio", { name: /qwen3:8b/ }).closest("li")!;
    expect(within(q8).getByText("Exceeds")).toBeInTheDocument();
    expect(within(q8).getByText(/NOT RECOMMENDED/)).toBeInTheDocument();
    expect(within(q8).getByText("RC6-allowlisted")).toBeInTheDocument();
    const q4 = within(p).getByRole("radio", { name: /qwen3:4b/ }).closest("li")!;
    expect(within(q4).getByText("Missing")).toBeInTheDocument();
    expect(within(q4).getByText("Not in RC6 prereg")).toBeInTheDocument();
    expect(within(p).getByText(/none \(CPU only\)/)).toBeInTheDocument();
    expect(within(p).getByText(/not met/)).toBeInTheDocument();
    await user.type(within(p).getByRole("searchbox"), "llama");
    expect(within(p).getAllByRole("radio").map((r) => (r as HTMLInputElement).value).sort()).toEqual(["llama3.2:1b", "llama3.2:3b"]);
  });

  it("Download selected asks for confirmation with the size, posts only the model id, shows progress and can cancel", async () => {
    let listing: ModelsListing = modelsListing();
    const posts: { url: string; body: unknown }[] = [];
    const { user } = await paired("Run Pipeline", {
      onGet: () => json(listing),
      onOp: (url, init) => {
        posts.push({ url, body: JSON.parse(String(init?.body)) });
        if (url.endsWith("/pull_model")) {
          listing = modelsListing({ pull: pullJob("running", 42) });
          return json({ status: "STARTED", model_id: "qwen3:4b" }, 202);
        }
        return json({ status: "CANCELLING" }, 202);
      },
    });
    const p = picker();
    const dl = within(p).getByRole("button", { name: "Download selected" });
    await waitFor(() => expect(within(p).getByRole("radio", { name: /llama3\.2:3b/ })).toBeChecked());
    expect(dl).toBeDisabled();
    expect(dl).toHaveAccessibleDescription(/Already installed/);
    await user.click(within(p).getByRole("radio", { name: /qwen3:4b/ }));
    await waitFor(() => expect(dl).toBeEnabled());
    await user.click(dl);
    expect(within(p).getByText(/This will download/)).toHaveTextContent("~2.5 GB");
    await user.click(within(p).getByRole("button", { name: /Download ~2\.5 GB/ }));
    await waitFor(() => expect(posts[0]).toEqual({ url: `${BASE}/api/ops/pull_model`, body: { model_id: "qwen3:4b" } }));
    const bar = await within(p).findByRole("progressbar", { name: /Download progress qwen3:4b/ });
    expect(bar).toHaveAttribute("aria-valuenow", "42");
    await user.click(within(p).getByRole("button", { name: "Cancel download" }));
    await waitFor(() => expect(posts[1]).toEqual({ url: `${BASE}/api/ops/cancel_pull`, body: {} }));
  });

  it("exceeding models cannot be downloaded", async () => {
    const { user } = await paired("Run Pipeline");
    const p = picker();
    await user.click(await within(p).findByRole("radio", { name: /qwen3:8b/ }));
    const dl = within(p).getByRole("button", { name: "Download selected" });
    expect(dl).toBeDisabled();
    expect(dl).toHaveAccessibleDescription(/Does not fit MemAvailable/);
  });

  it("Run dialog: a missing model needs the explicit '~X GB' download confirmation; it is sent as auto_pull", async () => {
    const bodies: unknown[] = [];
    const { user } = await paired("Run Pipeline", {
      onOp: (_url, init) => {
        bodies.push(JSON.parse(String(init?.body)));
        return json({ error: "stop here" }, 409);
      },
    });
    const p = picker();
    await user.click(await within(p).findByRole("radio", { name: /qwen3:0\.6b/ }));
    const btn = screen.getByRole("button", { name: /Run full check/ });
    await waitFor(() => expect(btn).toBeEnabled());
    await user.click(btn);
    const dlg = screen.getByRole("dialog");
    expect(within(dlg).getByText(/Model: qwen3:0\.6b/)).toBeInTheDocument();
    expect(within(dlg).getByText(/Without this the Model readiness step reports BLOCKED/)).toBeInTheDocument();
    await user.click(within(dlg).getByLabelText(/this will download ~0\.52 GB/));
    await user.click(within(dlg).getByRole("button", { name: "Start pipeline" }));
    await waitFor(() => expect(bodies).toEqual([{ full_suite: false, partb_confirm: "", model_id: "qwen3:0.6b", attempt_id: "", auto_pull: true }]));
  });

  it("Run dialog: an exceeding model warns BLOCKED and never sends auto_pull", async () => {
    const bodies: unknown[] = [];
    const { user } = await paired("Run Pipeline", { onOp: (_u, init) => (bodies.push(JSON.parse(String(init?.body))), json({ error: "x" }, 409)) });
    await user.click(await within(picker()).findByRole("radio", { name: /qwen3:8b/ }));
    const btn = screen.getByRole("button", { name: /Run full check/ });
    await waitFor(() => expect(btn).toBeEnabled());
    await user.click(btn);
    const dlg = screen.getByRole("dialog");
    expect(within(dlg).getByText(/will be BLOCKED/)).toBeInTheDocument();
    expect(within(dlg).queryByLabelText(/download/i)).toBeNull();
    await user.click(within(dlg).getByRole("button", { name: "Start pipeline" }));
    await waitFor(() => expect(bodies[0]).toMatchObject({ model_id: "qwen3:8b", auto_pull: false }));
  });

  it("live pipeline shows the model download progress; results show the model card with digest verification", async () => {
    const base = (state: "running" | "completed"): PipelineRun => ({
      id: RID, started_at: "2026-10-11T03:15:00+05:30", finished_at: state === "running" ? null : "2026-10-11T03:20:00+05:30", state,
      options: { full_suite: false, partb_handoff_requested: false, model_id: "qwen3:1.7b", auto_pull: true },
      steps: STEPS.map(([id, label], i) => ({
        id, label,
        status: state === "running" ? (i < 6 ? "PASS" : i === 6 ? "RUNNING" : "PENDING") : id === "partb" ? "BLOCKED" : "PASS",
        reason: id === "model" && state === "completed" ? "qwen3:1.7b downloaded in 61.3 s and verified" : "",
        started_at: "2026-10-11T03:15:00+05:30", ended_at: null, duration_s: state === "running" && i >= 6 ? null : 3,
        details: id === "model"
          ? state === "running"
            ? { progress: { status: "pulling 3d0b790534fe", percent: 37, completed: 5e8, total: 1.36e9, layers: [{ digest: "3d0b790534fe", total: 1.36e9, completed: 5e8, percent: 37 }] } }
            : {
                model_id: "qwen3:1.7b", family: "qwen3", rc6_allowlisted: true, selection: "matches the controller's recommendation: best installed model that fits",
                fit: { verdict: "FITS", reason: "needs ~2,654,000 kB; MemAvailable is 6,500,000 kB", required_kb: 2654000, recommended_kb: 3702000, available_kb: 6500000, total_kb: 16397616 },
                install_before: "missing", install_after: "installed", part_b_note: "in the RC6 preregistration allowlist (Part B still needs every gate)",
                pull: { outcome: "succeeded", reason: "ok", duration_s: 61.3, bytes_total: 1359296000, layers: 5, serve: { started: true, stopped: true, bind: "127.0.0.1:11535" } },
                verify: { ok: true, reason: "manifest and weights match the pinned digests", checks: [
                  { what: "manifest sha256", expected: "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7", observed: "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7", match: true },
                  { what: "weights blob sha256 (re-hashed)", expected: "3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6", observed: "3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6", match: true },
                ] },
              }
          : {},
      })),
      log: [{ t: 1, step: "model", line: "layer 3d0b790534fe: 30% of 1,296.3 MiB" }], log_total: 1, log_offset: 0,
      verdict: state === "running" ? null : { overall: "BLOCKED", headline: "Software built: PASS", lifecycle: [], experiment_ran: false, note: "The experiment did not run." },
      total_duration_s: state === "running" ? null : 300,
    });
    let doc = base("running");
    const st = status();
    st.pipeline!.running_run_id = RID;
    await paired("Run Pipeline", { status: st, onGet: (url) => (url.includes(RID) ? json(doc) : null) });
    const bar = await screen.findByRole("progressbar", { name: "Model download progress" });
    expect(bar).toHaveAttribute("aria-valuenow", "37");
    expect(screen.getByText(/downloading 37%/)).toBeInTheDocument();
    await act(async () => {
      doc = base("completed");
      await new Promise((r) => setTimeout(r, 1300));
    });
    const card = await screen.findByRole("region", { name: "Model readiness" });
    expect(within(card).getByText("qwen3:1.7b")).toBeInTheDocument();
    expect(within(card).getByText(/matches the controller's recommendation/)).toBeInTheDocument();
    expect(within(card).getByText(/succeeded in 61\.3 s/)).toBeInTheDocument();
    expect(within(card).getByText(/127\.0\.0\.1:11535, stopped/)).toBeInTheDocument();
    expect(within(card).getAllByText("MATCH").length).toBe(2);
    expect(within(card).getByText(/FITS: needs/)).toBeInTheDocument();
  });

  it("is accessible (axe) and honours reduced motion on the download bar", async () => {
    setReducedMotion(true);
    await paired("Run Pipeline", { onGet: () => json(modelsListing({ pull: pullJob("running", 10) })) });
    const p = picker();
    await within(p).findByRole("progressbar", { name: /Download progress/ });
    expect(p.querySelector(".mp-pull")!.className).not.toMatch(/\banim\b/);
    const res = await axe.run(p, { rules: { "color-contrast": { enabled: false } } });
    expect(res.violations.map((v) => v.id)).toEqual([]);
    setReducedMotion(false);
  });
});
