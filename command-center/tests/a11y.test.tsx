import axe from "axe-core";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderApp } from "./helpers";

const ROUTES = ["/", "/control", "/pipeline", "/demo", "/reports", "/runtime", "/integrity", "/deployment", "/settings"];

describe("accessibility (axe-core in jsdom)", () => {
  for (const route of ROUTES) {
    it(`has no axe violations on ${route}`, async () => {
      const { container } = await renderApp(route);
      // color-contrast needs real layout/rendering, which jsdom lacks; contrast is checked numerically below.
      const res = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
      const summary = res.violations.map((v) => `${v.id}: ${v.nodes.length}`);
      expect(summary).toEqual([]);
    });
  }
});

function hex(h: string): [number, number, number] {
  const m = h.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(m.slice(i, i + 2), 16)) as [number, number, number];
}
function lum([r, g, b]: [number, number, number]) {
  const f = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
function ratio(a: string, b: string) {
  const [x, y] = [lum(hex(a)), lum(hex(b))].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

describe("WCAG AA contrast of the palette", () => {
  const css = readFileSync(resolve(__dirname, "../src/styles.css"), "utf-8");
  const v = (name: string) => new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})`).exec(css)![1];
  const backgrounds = [v("bg"), v("bg2"), v("panel-solid"), "#0a1122"];
  for (const fg of ["text", "muted", "cyan", "violet", "green", "red", "amber"]) {
    it(`--${fg} meets 4.5:1 on every background`, () => {
      for (const bg of backgrounds) expect(ratio(v(fg), bg)).toBeGreaterThanOrEqual(4.5);
    });
  }
  it("focus ring meets 3:1 (non-text)", () => {
    for (const bg of backgrounds) expect(ratio(v("focus"), bg)).toBeGreaterThanOrEqual(3);
  });
});
