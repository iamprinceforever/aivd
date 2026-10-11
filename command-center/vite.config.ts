/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { execSync } from "node:child_process";

function buildCommit(): string {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA.slice(0, 12);
  try {
    return execSync("git rev-parse --short=12 HEAD", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
  } catch {
    return "unknown";
  }
}

export default defineConfig({
  base: "/aivd/",
  publicDir: "public-data",
  plugins: [react()],
  define: {
    __BUILD_COMMIT__: JSON.stringify(buildCommit()),
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    emptyOutDir: true,
  },
  preview: { host: "127.0.0.1" },
  server: { host: "127.0.0.1" },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
