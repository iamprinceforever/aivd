import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { BASE, installController, json, refusingStatus, renderApp } from "./helpers";
import { setReducedMotion } from "./setup";
import { RUN_CONFIRM } from "../src/lib/constants";
import { runToMarkdown } from "../src/lib/pipeline";
import type { ControllerStatus, PipelineRun, PipelineStep, StepStatus } from "../src/lib/types";

const RID = "r20261011T001500-abc123";
const HIST = "tests/rc5_gen/test_design.py::test_corpus_dependent_fields_and_authorizations_pending";
const STEPS: [string, string][] = [
  ["preflight", "Environment preflight"],
  ["guard", "Authorization / guard status"],
  ["rc6_tests", "RC6 research test suites"],
  ["full_suite", "Full research test suite"],
  ["cc_tests", "Command Center tests"],
  ["scans", "Publication & contamination scans"],
  ["partb", "RC6 Part B experiment (guarded)"],
  ["summary", "Summary (7-state lifecycle)"],
];

function withPipeline(running: string | null = null): ControllerStatus {
  return { ...refusingStatus(), pipeline: { available: true, running_run_id: running, steps: STEPS.map(([id, label]) => ({ id, label })) } };
}

function step(id: string, label: string, status: StepStatus, extra: Partial<PipelineStep> = {}): PipelineStep {
  const done = !["PENDING", "RUNNING"].includes(status);
  return { id, label, status, reason: done ? `${label} reason` : "", started_at: status === "PENDING" ? null : "2026-10-11T00:15:00+05:30", ended_at: done ? "2026-10-11T00:15:05+05:30" : null, duration_s: done ? 5 : null, details: {}, ...extra };
}

function runningRun(): PipelineRun {
  return {
    id: RID, started_at: "2026-10-11T00:15:00+05:30", finished_at: null, state: "running",
    options: { full_suite: false, partb_handoff_requested: false },
    steps: STEPS.map(([id, label], i) => step(id, label, i === 0 ? "PASS" : i === 1 ? "RUNNING" : "PENDING")),
    log: [{ t: 0.1, step: "preflight", line: "== Environment preflight ==" }, { t: 0.4, step: "preflight", line: "MemAvailable 6640000 kB < 7600000 kB" }],
    log_total: 2, log_offset: 0, verdict: null, total_duration_s: null,
  };
}

export function finishedRun(): PipelineRun {
  const checklist = [
    { id: "PREREG_APPROVAL", label: "Redacted preregistration approved (RC6_APPROVALS.json)", state: "FAIL" as const, reasons: ["no APPROVED RC6_APPROVALS.json"], fix: "Complete the separate review.", source: "aivd_rc6_guard" },
    { id: "G_AUDIT", label: "Historical protected-path audit resolved", state: "FAIL" as const, reasons: ["G_AUDIT: historical protected-path audit is not resolved"], fix: "Resolve the audit (G_AUDIT).", source: "aivd_rc6_guard" },
    { id: "MEMORY", label: "MemAvailable >= 7600000 kB", state: "FAIL" as const, reasons: ["MemAvailable 6640000 kB < 7600000 kB"], fix: "Free memory.", source: "controller" },
    { id: "CONFIRM_PHRASE", label: "Exact confirmation phrase typed", state: "FAIL" as const, reasons: ["confirmation phrase not typed"], fix: "Type it.", source: "operator" },
  ];
  const statuses: Record<string, StepStatus> = { preflight: "FAIL", guard: "BLOCKED", rc6_tests: "PASS", full_suite: "PASS", cc_tests: "PASS", scans: "PASS", partb: "BLOCKED", summary: "FAIL" };
  return {
    ...runningRun(), state: "completed", finished_at: "2026-10-11T00:17:00+05:30", total_duration_s: 120.5,
    excluded_tests: [{ id: "tests/post_rc3_local/test_runner_entrypoint.py", reason: "sets the LOCAL-V1 run-authorization variable" }],
    steps: STEPS.map(([id, label]) =>
      step(id, label, statuses[id], {
        details:
          id === "full_suite" ? { counts: { passed: 1112, failed: 1, skipped: 4, xfailed: 2 }, failing_new: [], failing_historical: [HIST], worktrees_unchanged: true }
          : id === "rc6_tests" ? { counts: { passed: 400, skipped: 2 }, failing_new: [], failing_historical: [], worktrees_unchanged: true }
          : id === "cc_tests" ? { vitest: { counts: { passed: 60 } }, python: { counts: { passed: 70, failed: 0 } } }
          : id === "partb" ? { checklist } : {},
      }),
    ),
    verdict: {
      overall: "FAIL",
      headline: "Software built: PASS; Runtime available: NOT VERIFIED; Prerequisites: FAIL; Authorized: NO; Experiment: NOT RUN",
      lifecycle: [
        { id: "software_built", label: "Software built", value: "PASS" },
        { id: "runtime_available", label: "Runtime available", value: "NOT VERIFIED" },
        { id: "prerequisites_satisfied", label: "Prerequisites", value: "FAIL" },
        { id: "explicitly_authorized", label: "Authorized", value: "NO" },
        { id: "running", label: "Experiment", value: "NOT RUN" },
        { id: "completed", label: "Completed", value: "NO" },
        { id: "independently_validated", label: "Independently validated", value: "NOT VERIFIED" },
      ],
      experiment_ran: false,
      note: "The experiment did not run. Nothing here means 'experiment ready'.",
    },
  };
}

async function paired(route: string, opts: Parameters<typeof installController>[0] = {}) {
  const calls = installController({ status: withPipeline(), ...opts });
  await renderApp("/settings", BASE);
  const user = userEvent.setup();
  await screen.findByText("FOUND, NOT PAIRED");
  await user.type(screen.getByLabelText(/One-time pairing code/), "AB12-CD34-EF56");
  await user.click(screen.getByRole("button", { name: "Pair" }));
  await screen.findByText("PAIRED");
  await user.click(within(screen.getByRole("navigation", { name: "Sections" })).getByRole("link", { name: new RegExp(route) }));
  return { calls, user };
}

describe("one-click pipeline", () => {
  it("static build: the button is disabled with 'Requires the local controller' on Overview, Control and Run Pipeline", async () => {
    for (const route of ["/", "/control", "/pipeline"]) {
      const r = await renderApp(route);
      const btn = screen.getByRole("button", { name: /Run full check/ });
      expect(btn).toBeDisabled();
      expect(btn).toHaveAccessibleDescription(/Requires the local controller/);
      r.unmount();
    }
  });

  it("opens a confirmation dialog (Escape closes, focus returns) and posts only the allowed fields", async () => {
    const bodies: unknown[] = [];
    const { user } = await paired("Overview", {
      onOp: (url, init) => {
        bodies.push({ url, body: JSON.parse(String(init?.body)) });
        return json({ run_id: RID, status: "STARTED" }, 202);
      },
      onGet: (url) => (url.includes(RID) ? json(runningRun()) : null),
    });
    const btn = await screen.findByRole("button", { name: /Run full check/ });
    await waitFor(() => expect(btn).toBeEnabled());
    await user.click(btn);
    const dlg = screen.getByRole("dialog", { name: "Run full check" });
    expect(dlg).toHaveAttribute("aria-modal", "true");
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(btn).toHaveFocus();
    await user.click(btn);
    await user.click(within(screen.getByRole("dialog")).getByLabelText(/Include the full research suite/));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Start pipeline" }));
    await screen.findByRole("heading", { level: 1, name: /One-click full check/ });
    expect(bodies).toEqual([{ url: `${BASE}/api/ops/run_pipeline`, body: { full_suite: true, partb_confirm: "", model_id: "llama3.2:3b", attempt_id: "", auto_pull: false } }]);
  });

  it("renders the Run dialog in a portal under document.body, above the page, with Start enabled and Part B closed", async () => {
    const { user } = await paired("Experiment Control");
    const btn = await screen.findByRole("button", { name: /Run full check/ });
    await waitFor(() => expect(btn).toBeEnabled());
    await user.click(btn);
    const dlg = screen.getByRole("dialog", { name: "Run full check" });
    const backdrop = dlg.parentElement!;
    expect(backdrop).toHaveClass("modal-backdrop");
    expect(backdrop.parentElement).toBe(document.body);          // portalled: no panel ancestor can trap its z-index
    expect(document.getElementById("main")!.contains(dlg)).toBe(false);
    expect(dlg).toHaveAttribute("aria-modal", "true");
    expect(within(dlg).getByRole("button", { name: "Start pipeline" })).toBeEnabled();
    expect(dlg.querySelector("details.partb-box")).not.toHaveAttribute("open");
    expect(within(dlg).getByLabelText(/Include the full research suite/)).not.toBeChecked();
    await user.tab({ shift: true });                                // focus trap still keeps focus inside the dialog
    expect(dlg.contains(document.activeElement)).toBe(true);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(btn).toHaveFocus();
  });

  it("Part B section requires the exact typed phrase before Start is enabled", async () => {
    const { user } = await paired("Experiment Control");
    const btn = await screen.findByRole("button", { name: /Run full check/ });
    await waitFor(() => expect(btn).toBeEnabled());
    await user.click(btn);
    const dlg = screen.getByRole("dialog");
    await user.click(within(dlg).getByText(/Also request the RC6 Part B handoff/));
    const start = within(dlg).getByRole("button", { name: "Start pipeline" });
    await user.type(within(dlg).getByLabelText(/Type the confirmation phrase/), RUN_CONFIRM.toLowerCase());
    expect(start).toBeDisabled();
    await user.clear(within(dlg).getByLabelText(/Type the confirmation phrase/));
    await user.type(within(dlg).getByLabelText(/Type the confirmation phrase/), RUN_CONFIRM);
    expect(start).toBeEnabled();
  });

  it("renders live progress from polled events, then the results page", async () => {
    let n = 0;
    const { user } = await paired("Overview", {
      onOp: () => json({ run_id: RID, status: "STARTED" }, 202),
      onGet: (url) => {
        if (!url.includes(RID)) return null;
        n += 1;
        return json(n < 2 ? runningRun() : { ...finishedRun(), log: [{ t: 120, step: "summary", line: "-> FAIL: done" }] });
      },
    });
    const btn = await screen.findByRole("button", { name: /Run full check/ });
    await waitFor(() => expect(btn).toBeEnabled());
    await user.click(btn);
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Start pipeline" }));
    expect(await screen.findByRole("heading", { name: "Pipeline running" })).toBeInTheDocument();
    expect(document.querySelector('[aria-current="step"]')?.textContent).toContain("Authorization / guard status");
    expect(screen.getByRole("log", { name: "Pipeline log" }).textContent).toContain("MemAvailable 6640000 kB < 7600000 kB");
    expect(await screen.findByRole("heading", { name: "Some checks failed" }, { timeout: 4000 })).toBeInTheDocument();
    expect(screen.getByText(/Experiment: NOT RUN/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pipeline finished" })).toBeInTheDocument();
    const log = screen.getByRole("log", { name: "Pipeline log" });
    expect(log.textContent).toContain("MemAvailable");
    expect(log.textContent).toContain("-> FAIL: done");
  });

  it("results page: verdict, lifecycle, per-step cards, gate checklist with fixes, historical failures, exports", async () => {
    await paired("Run Pipeline", { status: withPipeline(RID), onGet: (url) => (url.includes(RID) ? json(finishedRun()) : null) });
    expect(await screen.findByRole("heading", { name: "Some checks failed" })).toBeInTheDocument();
    expect(screen.getByText("2 min 1 s", { selector: ".hero-time" })).toBeInTheDocument();
    const chips = screen.getByRole("list", { name: "Seven-state lifecycle" });
    expect(within(chips).getAllByRole("listitem")).toHaveLength(7);
    expect(within(chips).getByText("NOT RUN")).toBeInTheDocument();
    const gates = screen.getByRole("region", { name: "Part B gates table" });
    expect(within(gates).getByText("G_AUDIT: historical protected-path audit is not resolved")).toBeInTheDocument();
    expect(within(gates).getByText("Resolve the audit (G_AUDIT).")).toBeInTheDocument();
    expect(screen.getByText(/1 pre-existing\/historical failure/)).toBeInTheDocument();
    expect(screen.getAllByText("HISTORICAL").length).toBeGreaterThan(0);
    expect(screen.getByText("Failed (pre-existing/historical):")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export JSON" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Export Markdown" })).toBeEnabled();
    expect(screen.getByText("tests/post_rc3_local/test_runner_entrypoint.py")).toBeInTheDocument();
    const text = (document.body.textContent ?? "").replace(finishedRun().verdict!.note, "").toLowerCase();
    expect(text).not.toMatch(/experiment (is )?ready|experiment succeeded/);
  });

  it("markdown export carries steps, durations, reasons and gates; never claims the experiment ran", () => {
    const md = runToMarkdown(finishedRun());
    expect(md).toContain(`# AIVD Command Center pipeline run ${RID}`);
    expect(md).toContain("| RC6 Part B experiment (guarded) | BLOCKED | 5.0 s |");
    expect(md).toContain("Total time: 2 min 1 s");
    expect(md).toContain("pre-existing/historical: `" + HIST + "`");
    expect(md).toContain("| Historical protected-path audit resolved | FAIL |");
    expect(md).toContain("Experiment: NOT RUN");
    expect(md.toLowerCase()).not.toContain("succeeded");
  });

  it("run history lists past runs and compares two", async () => {
    const a = finishedRun();
    const summary = (id: string, total: number) => ({ id, started_at: a.started_at, finished_at: a.finished_at, state: "completed", total_duration_s: total, verdict: a.verdict, options: a.options, steps: a.steps.map((s) => ({ id: s.id, label: s.label, status: s.status, duration_s: s.duration_s })) });
    const { user } = await paired("Run Pipeline", { onGet: (url) => (url.endsWith("/api/runs") ? json({ runs: [summary(RID, 120.5), summary("r20261010T230000-def456", 90)] }) : null) });
    const table = await screen.findByRole("region", { name: "Run history table" });
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    await user.click(within(table).getByLabelText(`Compare ${RID}`));
    await user.click(within(table).getByLabelText("Compare r20261010T230000-def456"));
    const cmp = screen.getByRole("region", { name: "Run comparison table" });
    expect(within(cmp).getByText("1 min 30 s")).toBeInTheDocument();
    expect(within(cmp).getByText("2 min 1 s")).toBeInTheDocument();
  });

  it("reduced motion: static pipeline view and no animated bars/donuts", async () => {
    setReducedMotion(true);
    await paired("Run Pipeline", { status: withPipeline(RID), onGet: (url) => (url.includes(RID) ? json(finishedRun()) : null) });
    await screen.findByRole("heading", { name: "Some checks failed" });
    expect(document.querySelector(".pipe")?.classList.contains("pipe-static")).toBe(true);
    expect(document.querySelector(".bar-anim")).toBeNull();
    expect(document.querySelector(".donut-anim")).toBeNull();
  });

  it("has no axe violations on the results page and in the open dialog", async () => {
    const { user } = await paired("Run Pipeline", { status: withPipeline(RID), onGet: (url) => (url.includes(RID) ? json(finishedRun()) : null) });
    await screen.findByRole("heading", { name: "Some checks failed" });
    let res = await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } });
    expect(res.violations.map((v) => `${v.id}: ${v.nodes.length}`)).toEqual([]);
    await act(async () => {});
    const btn = screen.getByRole("button", { name: /Run full check|Pipeline running/ });
    if (!btn.hasAttribute("disabled")) {
      await user.click(btn);
      res = await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } });
      expect(res.violations.map((v) => `${v.id}: ${v.nodes.length}`)).toEqual([]);
    }
  });
});
