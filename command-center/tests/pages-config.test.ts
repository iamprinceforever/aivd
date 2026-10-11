// @vitest-environment node
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import config from "../vite.config";

const ROOT = resolve(__dirname, "..");

describe("static build and GitHub Pages configuration", () => {
  it("uses base path /aivd/ and bundles public-data", () => {
    expect(config.base).toBe("/aivd/");
    expect(config.publicDir).toBe("public-data");
    expect(config.build?.sourcemap).toBe(false);
  });

  it("uses HashRouter (works on Pages without server rewrites)", () => {
    const app = readFileSync(join(ROOT, "src/App.tsx"), "utf-8");
    expect(app).toMatch(/HashRouter/);
    expect(app).not.toMatch(/BrowserRouter/);
  });

  it("never stores tokens in web storage", () => {
    const walk = (d: string): string[] => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? walk(join(d, f)) : [join(d, f)]));
    for (const f of walk(join(ROOT, "src"))) {
      const t = readFileSync(f, "utf-8");
      expect(t, f).not.toMatch(/localStorage|sessionStorage|document\.cookie|indexedDB/);
    }
  });

  const dist = join(ROOT, "dist");
  it.skipIf(!existsSync(join(dist, "index.html")))("built dist has 404 fallback, .nojekyll and /aivd/ asset URLs", () => {
    const index = readFileSync(join(dist, "index.html"), "utf-8");
    expect(readFileSync(join(dist, "404.html"), "utf-8")).toBe(index);
    expect(existsSync(join(dist, ".nojekyll"))).toBe(true);
    expect(index).toMatch(/src="\/aivd\/assets\//);
    expect(index).toMatch(/Content-Security-Policy/);
    expect(existsSync(join(dist, "reports-index.json"))).toBe(true);
    expect(existsSync(join(dist, "site-data.json"))).toBe(true);
    expect(readdirSync(dist).some((f) => f.endsWith(".map"))).toBe(false);
  });
});
