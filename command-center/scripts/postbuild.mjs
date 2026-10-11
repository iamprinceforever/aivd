// Post-build: SPA fallback for GitHub Pages, .nojekyll, then the fail-closed content scan of dist/.
import { copyFileSync, writeFileSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";

if (!existsSync("dist/index.html")) {
  console.error("postbuild: dist/index.html missing");
  process.exit(1);
}
copyFileSync("dist/index.html", "dist/404.html");
writeFileSync("dist/.nojekyll", "");
const py = process.env.PYTHON || "python3";
const r = spawnSync(py, ["scripts/scan_outgoing.py", "--dist", "dist"], { stdio: "inherit" });
if (r.status !== 0) {
  console.error("postbuild: dist/ content scan FAILED; refusing to produce a deployable build");
  process.exit(1);
}
