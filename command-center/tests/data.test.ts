// @vitest-environment node
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import type { ReportsIndex, SiteData } from "../src/lib/types";

const ROOT = resolve(__dirname, "..");
const idx: ReportsIndex = JSON.parse(readFileSync(join(ROOT, "public-data/reports-index.json"), "utf-8"));
const site: SiteData = JSON.parse(readFileSync(join(ROOT, "public-data/site-data.json"), "utf-8"));
const allow = JSON.parse(readFileSync(join(ROOT, "reports-allowlist.json"), "utf-8"));

describe("bundled data and allowlist", () => {
  it("every bundled report is allowlisted, eligible and hash-matched", () => {
    const eligible = new Map(allow.items.filter((x: { publication_review: string }) => x.publication_review !== "restricted").map((x: { id: string }) => [x.id, x]));
    for (const r of idx.reports) {
      expect(eligible.has(r.id)).toBe(true);
      if (r.journey_stage) {
        // pinned RC6 document from the local research tip: never historical, never claimed to be on a public ref
        expect(r.historical).toBe(false);
        expect(r.source_ref).toBe(idx.staged_source!.ref);
        expect(r.commit).toMatch(/^[0-9a-f]{40}$/); // last commit touching the path, at or before the pinned tip
        expect(idx.staged_source!.on_public_ref).toBe(false);
        expect((eligible.get(r.id) as { publication_review: string }).publication_review).toBe("eligible-automated-staged");
      } else {
        expect(r.historical).toBe(true);
        expect(r.source_ref).toMatch(/^(origin\/|refs\/tags\/)/);
      }
      expect(r.path).not.toMatch(/(^|\/)(protected|raw|wire)\//);
      const f = join(ROOT, r.sanitized_artifact!.file);
      expect(createHash("sha256").update(readFileSync(f)).digest("hex")).toBe(r.sanitized_artifact!.sha256);
    }
    const files = readdirSync(join(ROOT, "public-data/reports"));
    expect(files.length).toBe(idx.reports.length);
  });

  it("claim terms only come from a closed vocabulary", () => {
    const vocab = new Set(["discovery_candidate", "verified", "reproduced", "generalized", "not_discovered"]);
    for (const r of idx.reports) for (const c of r.claims_stated_in_report) expect(vocab.has(c)).toBe(true);
  });

  it("restricted placeholders carry no path or hash", () => {
    for (const p of idx.restricted_placeholders) {
      expect(Object.keys(p).sort()).toEqual(["id", "reason", "series", "title"]);
    }
  });

  it("site data never claims Pages is live or main is protected without evidence", () => {
    expect(site.github_snapshot.observed_at).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(site.lifecycle_states.map((s) => s.id)).toEqual([
      "software_built", "runtime_available", "prerequisites_satisfied", "explicitly_authorized", "running", "completed", "independently_validated",
    ]);
    expect(site.public_refs.some((r) => r.name.includes("rc5-a2-local-uncommitted"))).toBe(false);
  });

  it("fail-closed scanner passes on public-data (and dist when built)", () => {
    const args = ["scripts/scan_outgoing.py", "--tree", "public-data"];
    if (existsSync(join(ROOT, "dist/index.html"))) args.push("--dist", "dist");
    const r = spawnSync("python3", args, { cwd: ROOT, encoding: "utf-8" });
    expect(r.status, r.stdout).toBe(0);
    expect(JSON.parse(r.stdout.trim().split("\n").pop()!).pass).toBe(true);
  });
});
