import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderApp } from "./helpers";
import { setReducedMotion } from "./setup";

describe("motion and responsive behaviour", () => {
  it("uses the animated canvas when motion is allowed", async () => {
    await renderApp("/");
    expect(screen.getByTestId("bg-canvas")).toBeInTheDocument();
    expect(document.documentElement.dataset.motion).toBe("full");
  });

  it("falls back to a static, non-animated background under prefers-reduced-motion", async () => {
    setReducedMotion(true);
    await renderApp("/");
    expect(screen.queryByTestId("bg-canvas")).toBeNull();
    expect(screen.getByTestId("bg-static")).toBeInTheDocument();
    expect(document.documentElement.dataset.motion).toBe("reduced");
    // counters show their final real value immediately (no count-up)
    const idx = JSON.parse(readFileSync(resolve(__dirname, "../public-data/reports-index.json"), "utf-8"));
    expect(await screen.findByText(`Archived reports: ${idx.reports.length}`)).toBeInTheDocument();
  });

  it("lets the user override motion in Settings", async () => {
    await renderApp("/settings");
    await userEvent.setup().click(screen.getByRole("radio", { name: "Reduce motion" }));
    expect(screen.getByTestId("bg-static")).toBeInTheDocument();
    expect(document.documentElement.dataset.motion).toBe("reduced");
  });

  it("stylesheet has reduced-motion, responsive breakpoints and visible focus", () => {
    const css = readFileSync(resolve(__dirname, "../src/styles.css"), "utf-8");
    expect(css).toMatch(/@media \(prefers-reduced-motion: reduce\)/);
    expect(css).toMatch(/html\[data-motion="reduced"\]/);
    expect(css).toMatch(/@media \(max-width: 820px\)/);
    expect(css).toMatch(/@media \(max-width: 480px\)/);
    expect(css).toMatch(/:focus-visible\s*{[^}]*outline: 3px solid/);
  });
});
