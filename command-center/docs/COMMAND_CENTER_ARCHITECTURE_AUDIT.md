# AIVD Command Center: architecture audit (Stage 1)

Recorded 2026-10-10 (IST), read-only. No fetch was needed: `git ls-remote origin` equals the local
remote-tracking refs. Remote URLs are redacted, and the embedded credential is never printed or stored.

## Remotes and visibility
- One remote, `origin` → `github.com/iamprinceforever/aivd`. It is **public**, the default branch is `main`, and
  `has_pages=false`.
- `main` has no rulesets and no classic branch protection. No branch on the remote is protected.
- The repo has 0 Actions workflows. Secret scanning and push protection are disabled on the remote.
- Pages works on a public repo on any plan, so no paid plan is needed. Pages is not enabled yet. The source
  must be set to "GitHub Actions" (an owner action, see COMMAND_CENTER_DEPLOYMENT.md).

## Branch topology (local object store = main clone)
- `origin/main` = `f7ba8f2` (AIVD 3.17 line). The RC lineage (`AIVD-RC1` tag → `aba2178` … `AIVD-RC3` →
  `7b2ada3`, POST-RC3, LOCAL-V1 `245c7ef`/`9b70ca9`, RC4 `83520c3`, RC5 design `365f513`, seal recovery
  `902dba3`) has **no common ancestor** with `main`.
- The remote also carries the 3.38–3.48 and 4.0 research branches and `AIVD-v3.38.0` (`fca251d`). That branch
  holds a `lab/` dashboard (React/Vite, Postgres/auth based). It is not on `main` and is not reused: its stack
  needs a database and auth server, which Pages cannot host.
- Latest local research branch by committer date: `research/aivd-rc6-partb-readiness` @ `cb8dc31`
  (2026-10-10 20:31 IST). Next is the publication candidate `ce12715` (20:27 IST).
- `cb8dc31` has 22 ancestors (itself included) that are on no public ref. They include the deny-listed RC5 commits `f96a2a7`,
  `3fb7e4e` and `80a6ecb`, and the outcome-bearing RC6 commits `0dd54f7` and `18326e5`.

## Worktrees (state at start; must stay unchanged)
| worktree | branch | HEAD | state |
|---|---|---|---|
| main clone | research/aivd-rc5-generalization-v1-design | aef0595 | 13 modified + 1 untracked; diff sha 142c318e… |
| aivd-rc5-exec | rc5-exec | 80a6ecb | 5 untracked report paths (unpublished) |
| aivd-rc6-diag | research/aivd-rc6-partb-readiness | cb8dc31 | 5 untracked RC6 docs (deny-listed names) |
| aivd-rc6-publication | research/aivd-rc6-publication-candidate | ce12715 | clean |
| aivd-protected-review | review/aivd-protected-path-untrack | 010e9ab | clean |

## Reports locations
- Top-level `AIVD_*.md`, `docs/rc1|rc2|post_rc3|rc4_multi_v1|rc5_generalization_v1/`, `reports/**.md`.
- 163 report files on public refs. Unpublished material: RC5 execution reports (rc5-exec, untracked) and RC6
  docs (readiness/diag branches).
- Public RC4 and LOCAL-V1 refs still track 36 files under `*/protected/`. These are excluded by rule.

## Runner APIs, entry scripts, guards
- `aivd_rc6_guard` (readiness branch only) provides `check/require/status`. `python -m aivd_rc6_guard` prints
  refusal reasons and exits 3 when refused. It is a pure read.
- `scripts/rc6_partb_run.py <model> <attempt>` is guarded by MODEL_CALL + START_RUNTIME,
  `AIVD_RC6_PARTB_AUTHORIZED` and a fresh memory gate (≥7,600,000 kB). It prints only its final status. It has
  **no cancel operation and no incremental progress**.
- `scripts/rc6_analyze.py` is guarded by REVEAL + SCORE.
- `tools/rc6_outgoing_check.py` runs K1–K5 (deny commits/blobs/names, protected paths, O1–O8, prior-seal scan).
  The prior-seal scanner lives outside git and runs locally only.
- The pre-push hook is installed only for the rc6-diag worktree (`extensions.worktreeConfig`). The new UI
  worktree does not inherit it.

## Deployment config
- No Pages, workflows or CNAME exist. The project Pages URL would be `https://iamprinceforever.github.io/aivd/`,
  so the base path is `/aivd/`.

## Safety risks
1. Pushing `ui/aivd-command-center` (based on `cb8dc31`) would publish 22 unpublished research commits.
   Use the UI-only series replayed onto `origin/main` instead.
2. Historical protected files are reachable on public refs. The archive must filter by path, not by ref.
3. Some public post-run reports contain prior-seal values: 5 files fail the prior-seal scan, and 7 more hit outcome patterns. All 12 are restricted pending human review.
4. The origin URL embeds a credential. Never print the remote, and never copy `.git/config`.
5. The live controller can reach guarded entry scripts. They must stay fail-closed, server-side, with no env
   authorization set by the controller.
6. `main` is unprotected and secret scanning is off. Branch protection is recommended before enabling deploys.
