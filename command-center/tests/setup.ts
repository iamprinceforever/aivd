import "@testing-library/jest-dom/vitest";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

/**
 * Test fetch: serves the REAL bundled files from public-data/ for /aivd/<file> URLs. Controller URLs are
 * answered by per-test handlers (tests/controllerMock.ts); without one, the controller is unreachable.
 */
export const PUBLIC = resolve(__dirname, "..", "public-data");
export type Handler = (url: string, init?: RequestInit) => Response | Promise<Response> | null;
let handler: Handler | null = null;
export function setControllerHandler(h: Handler | null) {
  handler = h;
}

let reduce = false;
export function setReducedMotion(v: boolean) {
  reduce = v;
}

beforeEach(() => {
  reduce = false;
  handler = null;
  if (typeof window === "undefined") return;
  window.location.hash = "#/";
  window.matchMedia = ((q: string) => ({
    matches: q.includes("prefers-reduced-motion") ? reduce : false,
    media: q,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
  HTMLCanvasElement.prototype.getContext = (() => null) as never;
  window.scrollTo = (() => {}) as never;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      if (url.startsWith("/")) {
        const p = resolve(PUBLIC, url.replace(/^\/aivd\//, "/").slice(1));
        if (!p.startsWith(PUBLIC) || !existsSync(p)) return new Response("not found", { status: 404 });
        const body = readFileSync(p, "utf-8");
        return new Response(body, { status: 200, headers: { "Content-Type": p.endsWith(".json") ? "application/json" : "text/markdown" } });
      }
      if (handler) {
        const r = await handler(url, init);
        if (r) return r;
      }
      throw new TypeError("Failed to fetch");
    }),
  );
});

afterEach(() => {
  if (typeof window === "undefined") return;
  cleanup();
  vi.unstubAllGlobals();
});
