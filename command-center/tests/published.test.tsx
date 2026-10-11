import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { screen, within } from "@testing-library/react";
import axe from "axe-core";
import { renderApp } from "./helpers";
import { PUBLIC } from "./setup";
import { fmtIST, publishedLabel, RUN_ID_RX } from "../src/lib/published";

const RUNS = join(PUBLIC, "runs");
const index = JSON.parse(readFileSync(join(RUNS, "index.json"), "utf-8"));
const latest = JSON.parse(readFileSync(join(RUNS, "latest.json"), "utf-8"));

describe("published run data (public-data/runs)", () => {
  it("index points at latest.json, which is byte-identical to its run file", () => {
    expect(RUN_ID_RX.test(index.latest)).toBe(true);
    expect(latest.id).toBe(index.latest);
    expect(readFileSync(join(RUNS, "latest.json"), "utf-8")).toBe(readFileSync(join(RUNS, `${index.latest}.json`), "utf-8"));
    for (const r of index.runs) expect(readdirSync(RUNS)).toContain(`${r.id}.json`);
  });

  it("every published file is sanitized: no log, local paths, hosts, pids or session material", () => {
    const local = new RegExp(["/" + "workspace", "/var" + "/tmp", "/home" + "/box", "/Users/", "/root/"].map((x) => x.replace(/\//g, "\\/")).join("|"));
    for (const f of readdirSync(RUNS)) {
      const text = readFileSync(join(RUNS, f), "utf-8");
      expect(text, f).not.toMatch(local);
      expect(text, f).not.toMatch(/"(pid|pids|ppid|pgid|hostname|state_dir|cwd|argv|env|session|csrf|token)"\s*:/);
      expect(text, f).not.toMatch(/\bpid[ =:]+\d+/i);
      if (f !== "index.json") {
        const d = JSON.parse(text);
        expect(d.log, f).toEqual([]);
        expect(d.published.sanitized).toBe(true);
        expect(d.state).toBe("completed");
        expect(d.verdict.lifecycle).toHaveLength(7);
      }
    }
  });

  it("labels runs with IST time", () => {
    expect(fmtIST("2026-10-11T14:47:15+00:00")).toMatch(/11 Oct 2026, 20:17 IST/);
    expect(publishedLabel({ id: "r20261011T144715-c8b1d0", started_at: "2026-10-11T14:47:15+00:00", published: { source: "research computer" } }))
      .toMatch(/^Run on the research computer, 11 Oct 2026, 20:17 IST, run id r20261011T144715-c8b1d0$/);
  });
});

describe("hosted results view without a controller", () => {
  it("#/runs/latest renders verdict, 7-state lifecycle, timeline, test counts and the Part B checklist", async () => {
    await renderApp("/runs/latest");
    expect(await screen.findByRole("heading", { name: new RegExp(`^Run on the research computer, .* IST, run id ${latest.id}$`) })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Verdict|checks|blocked/i, level: 2, hidden: false })).toBeInTheDocument();
    const life = screen.getByRole("list", { name: "Seven-state lifecycle" });
    expect(within(life).getAllByRole("listitem")).toHaveLength(7);
    expect(within(life).getByText("Software built")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Timeline" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Test counts" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "RC6 Part B gate checklist" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Step results" })).toBeInTheDocument();
    expect(screen.getAllByText(/Full research test suite/).length).toBeGreaterThan(0);
    expect(document.title).toMatch(/^Published run · /);
    const res = await axe.run(document.body, { rules: { "color-contrast": { enabled: false } } });
    expect(res.violations.map((v) => v.id)).toEqual([]);
  });

  it("an unknown or malformed run id shows an error, never a fetch outside runs/", async () => {
    await renderApp("/runs/..%2Fsite-data");
    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid run id/);
  });

  it("Run Pipeline shows the latest published run when no controller is paired", async () => {
    await renderApp("/pipeline");
    const card = (await screen.findByRole("heading", { name: "Latest published run" })).closest("section")!;
    expect(within(card).getByText(new RegExp(`run id ${latest.id}`))).toBeInTheDocument();
    expect(within(card).getByRole("link", { name: /Open the full results/ })).toHaveAttribute("href", "#/runs/latest");
  });

  it("Overview links to the published results", async () => {
    await renderApp("/");
    expect(screen.getByRole("link", { name: /Latest results from the research computer/ })).toHaveAttribute("href", "#/runs/latest");
  });
});
