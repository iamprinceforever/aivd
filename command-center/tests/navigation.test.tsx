import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NAV } from "../src/App";
import { renderApp } from "./helpers";

describe("navigation", () => {
  it("renders all sections (A–G plus Run Pipeline) and navigates with hash routing", async () => {
    await renderApp("/");
    const nav = screen.getByRole("navigation", { name: "Sections" });
    const links = within(nav).getAllByRole("link");
    expect(links.map((l) => l.textContent?.replace(/^[A-GR]/, ""))).toEqual(NAV.map((n) => n.label));
    const user = userEvent.setup();
    const expected: Record<string, RegExp> = {
      "Experiment Control": /Guarded RC6 operations/,
      "Run Pipeline": /One-click full check/,
      "Reports Archive": /Sanitized historical reports/,
      "Models & Runtime": /Models and local runtime/,
      "Research Integrity": /Integrity gates and evidence boundaries/,
      "GitHub & Deployment": /Repository and Pages deployment/,
      "Settings & Activity": /Connection, preferences and activity log/,
      Overview: /Research operations at a glance/,
    };
    for (const [label, heading] of Object.entries(expected)) {
      await user.click(within(nav).getByRole("link", { name: new RegExp(label.replace("&", "&")) }));
      expect(await screen.findByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
      expect(within(nav).getByRole("link", { name: new RegExp(label) })).toHaveAttribute("aria-current", "page");
      expect(window.location.hash).toMatch(/^#\//);
    }
  });

  it("supports keyboard navigation: skip link first, then nav links via Tab", async () => {
    await renderApp("/");
    const user = userEvent.setup();
    await user.tab();
    expect(screen.getByText("Skip to content")).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(document.getElementById("main")).toHaveFocus();
  });

  it("deep links work (Pages-safe hash route)", async () => {
    await renderApp("/reports");
    expect(screen.getByRole("heading", { level: 1, name: /Sanitized historical reports/ })).toBeInTheDocument();
  });

  it("mobile menu button toggles the nav with aria-expanded", async () => {
    await renderApp("/");
    const btn = screen.getByRole("button", { name: "Menu" });
    expect(btn).toHaveAttribute("aria-expanded", "false");
    await userEvent.setup().click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
    expect(document.getElementById("sidenav")).toHaveClass("open");
  });
});
