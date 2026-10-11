import { screen, within } from "@testing-library/react";
import siteData from "../public-data/site-data.json";
import index from "../public-data/reports-index.json";
import { renderApp } from "./helpers";

describe("research journey", () => {
  it("bundled data covers RC1 through guarded Part B, with Part B not authorized and no result recorded", () => {
    const ids = siteData.research_journey.map((s) => s.id);
    expect(ids).toEqual(["rc1_rc3", "post_rc3_rc4", "rc5_design", "rc5_execution", "rc6_design", "rc6_part_a", "rc6_partb_readiness", "rc6_partb_guarded"]);
    const exec = siteData.research_journey.find((s) => s.id === "rc5_execution")!;
    expect(exec.outcome).toBe("RESTRICTED");
    expect(exec.refs).toEqual([]);
    const partb = siteData.research_journey.find((s) => s.id === "rc6_partb_guarded")!;
    expect(partb.status).toBe("NOT_AUTHORIZED");
    expect(partb.outcome).toBe("NOT_RECORDED");
    expect(siteData.policy.some((p) => p.id === "rc6-not-authorized" && /not authorized/.test(p.statement))).toBe(true);
    expect(siteData.research_tip.on_public_ref).toBe(false);
    // journey text never carries a fraction-of-N style figure
    expect(JSON.stringify(siteData.research_journey)).not.toMatch(/\b\d{1,3}\s*\/\s*(60|120|180)\b/);
  });

  it("staged RC6 documents are pinned to the research tip and mapped to a journey stage", () => {
    const staged = index.reports.filter((r) => "journey_stage" in r);
    expect(staged.length).toBe(index.staged_source.included);
    for (const r of staged) {
      expect(r.source_ref).toBe(index.staged_source.ref);
      expect(r.series).toMatch(/^RC6/);
      expect(r.path).not.toMatch(/PREREGISTRATION_DRAFT|PART_A_RESULTS|DECISION_REPORT|BASELINE_AUDIT/);
    }
  });

  it("renders the journey, the built process and the pipeline steps", async () => {
    await renderApp("/journey");
    expect(screen.getByRole("heading", { level: 1, name: /End-to-end research journey and process/ })).toBeInTheDocument();
    const list = screen.getByRole("list", { name: /Research journey, RC1 to guarded RC6 Part B/ });
    expect(within(list).getAllByRole("listitem")).toHaveLength(8);
    expect(within(list).getByText("RC5 execution phase")).toBeInTheDocument();
    expect(within(list).getAllByText("Outcome restricted").length).toBeGreaterThan(0);
    expect(within(list).getByText("Not authorized")).toBeInTheDocument();
    const proc = screen.getByRole("list", { name: "Built process steps" });
    for (const id of ["preflight", "guard", "rc6_tests", "full_suite", "cc_tests", "scans", "model", "partb", "summary"]) {
      expect(within(proc).getByText(id)).toBeInTheDocument();
    }
    expect(screen.getByText("LOCAL ONLY")).toBeInTheDocument();
  });

  it("overview shows the compact journey with a link to the full page", async () => {
    await renderApp("/");
    expect(screen.getByRole("heading", { name: "End-to-end research journey" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open the full journey and built process/ })).toHaveAttribute("href", "#/journey");
  });
});
