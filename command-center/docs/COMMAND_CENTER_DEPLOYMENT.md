# AIVD Command Center: deployment

## Target
GitHub Pages project site `https://iamprinceforever.github.io/aivd/` (base path `/aivd/`). The repository is
public, so Pages works on any plan.

## Which branch to deploy
Local branches carrying the same UI tree:
| branch | base | publication-safe? |
|---|---|---|
| `ui/aivd-command-center` | `research/aivd-rc6-partb-readiness` @ `cb8dc31` (latest research branch) | **No.** Its ancestry holds 22 commits (itself included) that are on no public ref, including the deny-listed unpublished commits `f96a2a7`, `3fb7e4e` and `80a6ecb` (RC5 stages 4–5 and amendment A3) and the deny-listed RC6 commits `0dd54f7` and `18326e5`, which carry earlier-study figures. It also shares **no history** with `main`. Pushing it to `main` would need a force push or an unrelated-history merge, and it would publish all of those commits. |
| `ui/aivd-command-center-publish` | `origin/main` @ `f7ba8f2` | **Yes, after review.** It holds only UI commits built from the final reviewed tree. Its outgoing manifest lists only `command-center/**` and `.github/workflows/command-center.yml`, and every blob in every commit passes this repo's scanners and the repository's own RC6 outgoing content checks K1–K5. |
| `ui/aivd-command-center-pages`, `ui/aivd-command-center-pages-clean` | `origin/main` @ `f7ba8f2` | **Superseded, do not push.** These are earlier replays. Their intermediate commits carry scanner test fixtures and pattern text that trip the outgoing checks: literal local-path strings, a fake token-shaped string and self-matching pattern text. |

Deploy from `ui/aivd-command-center-publish` (or an equivalent PR into `main`). Keep `ui/aivd-command-center`
local unless the researcher separately decides to publish the RC6 work.

## One-time repository settings (owner)
1. **Settings → Pages → Build and deployment → Source = "GitHub Actions"**.
2. **Settings → Environments → `github-pages`**: restrict deployment branches to `main`.
3. Recommended **branch protection / ruleset on `main`** (none exists today):
   - require a pull request with review;
   - require the `command-center / build` status check;
   - block force pushes and deletions;
   - optionally require linear history.
4. Recommended: enable **secret scanning and push protection** (currently disabled).
5. **Settings → Actions → General**:
   - allow GitHub-authored actions only, or the pinned list;
   - set workflow permissions to "Read repository contents".

## Workflow (`.github/workflows/command-center.yml`)
- Pull requests that touch `command-center/**` run `npm ci` → build (with the dist/ scan) → Vitest → Python
  tests → source scan. Nothing deploys.
- A push to `main` runs the same steps, then `actions/upload-pages-artifact` and `actions/deploy-pages`.
- Every action is pinned to a full commit SHA. Default permissions are `contents: read`. Only the deploy job
  gets `pages: write` and `id-token: write`. Concurrency is set per ref, and deploys are never cancelled
  mid-flight.

## Pre-push checklist (run locally; nothing here pushes)
```bash
cd command-center
CC_REQUIRE_SEAL_SCAN=1 CC_SEAL_SCANNER=<prior-seal scanner> \
  python3 scripts/scan_outgoing.py --git-range origin/main..ui/aivd-command-center-publish --repo ..
python3 scripts/outgoing_manifest.py --repo .. --tip ui/aivd-command-center-publish --base origin/main --out /tmp/manifest.json
```
Both commands must report `pass: true` / `branch_safety.pass: true`.

## Rollback
To take the site down: Settings → Pages → Unpublish. You can also revert the merge commit on `main`; the next
push redeploys.
