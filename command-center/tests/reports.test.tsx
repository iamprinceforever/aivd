import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { Markdown } from "../src/components/Markdown";
import { renderApp } from "./helpers";
import type { ReportsIndex } from "../src/lib/types";

const idx: ReportsIndex = JSON.parse(readFileSync(resolve(__dirname, "../public-data/reports-index.json"), "utf-8"));

describe("reports archive", () => {
  it("lists every allowlisted report with a HISTORICAL label and provenance", async () => {
    await renderApp("/reports");
    const list = await screen.findByRole("list", { name: "Reports" });
    const items = within(list).getAllByRole("listitem");
    expect(items).toHaveLength(idx.reports.length);
    for (const it of items.slice(0, 10)) {
      expect(within(it).getByText("HISTORICAL")).toBeInTheDocument();
      expect(within(it).getByText("Commit")).toBeInTheDocument();
      expect(within(it).getByText("sha256 (original)")).toBeInTheDocument();
    }
    expect(screen.getByRole("status")).toHaveTextContent(`${idx.reports.length} of ${idx.reports.length} reports`);
  });

  it("searches and filters by series and stated claim", async () => {
    await renderApp("/reports");
    const user = userEvent.setup();
    const target = idx.reports[0];
    await user.type(screen.getByRole("searchbox"), target.path);
    const list = screen.getByRole("list", { name: "Reports" });
    expect(within(list).getAllByRole("listitem").length).toBeGreaterThanOrEqual(1);
    expect(within(list).getAllByText(target.path).length).toBeGreaterThanOrEqual(1);
    await user.clear(screen.getByRole("searchbox"));
    const series = idx.reports[idx.reports.length - 1].series;
    await user.selectOptions(screen.getByRole("combobox", { name: "Series" }), series);
    const n = idx.reports.filter((r) => r.series === series).length;
    expect(screen.getByRole("status")).toHaveTextContent(`${n} of ${idx.reports.length}`);
    await user.selectOptions(screen.getByRole("combobox", { name: "Series" }), "");
    await user.selectOptions(screen.getByRole("combobox", { name: "Claim stated" }), "reproduced");
    const m = idx.reports.filter((r) => r.claims_stated_in_report.includes("reproduced")).length;
    expect(screen.getByRole("status")).toHaveTextContent(`${m} of ${idx.reports.length}`);
  });

  it("shows restricted placeholders without paths, hashes or findings", async () => {
    await renderApp("/reports");
    const panel = screen.getByRole("region", { name: "Restricted placeholders" });
    for (const p of idx.restricted_placeholders) expect(within(panel).getByText(p.title)).toBeInTheDocument();
    expect(panel.textContent).not.toMatch(/[0-9a-f]{40}/);
    expect(panel.textContent).not.toMatch(/\.md|\.json/);
  });

  it("opens a report with provenance header and rendered text", async () => {
    const r = idx.reports.find((x) => x.sanitized_artifact)!;
    await renderApp(`/reports/${r.id}`);
    expect(await screen.findByRole("heading", { level: 1, name: r.title })).toBeInTheDocument();
    expect(screen.getAllByText("HISTORICAL").length).toBeGreaterThan(0);
    expect(screen.getByText(r.commit.slice(0, 12))).toBeInTheDocument();
    const article = await screen.findByRole("article", { name: "Report text" });
    await within(article).findAllByText(/\S/);
  });

  it("markdown renderer never injects HTML", () => {
    const { container } = render(<Markdown text={'# T\n<script>alert(1)</script>\n<img src=x onerror=alert(1)>\n[x](javascript:alert(1))'} />);
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("a")).toBeNull();
    expect(container.textContent).toContain("<script>alert(1)</script>");
  });
});
