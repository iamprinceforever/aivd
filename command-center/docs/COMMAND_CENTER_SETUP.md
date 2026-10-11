# AIVD Command Center: setup

The app lives in `command-center/`. It is self-contained: React 19 + TypeScript + Vite 7, with dependencies
pinned exactly in `package-lock.json`. The controller and scanners use only the Python 3 standard library.

## Requirements
- Node.js ≥ 20.19 (CI uses 22) and npm ≥ 10. The Debian-packaged npm 9.2 crashes in `npm ci` (an arborist bug),
  so use `npx -y npm@10.9.2 ci` there.
- Python ≥ 3.10.

## Build and test
```bash
cd command-center
npm ci --ignore-scripts      # lockfile only
npm run build                # tsc + vite build + 404.html/.nojekyll + fail-closed dist/ scan
npm test                     # Vitest + Testing Library + axe-core (jsdom)
npm run test:py              # controller, scanner, manifest and workflow tests (unittest)
npm run preview              # serves dist/ on http://127.0.0.1:4173/aivd/ (loopback only)
```

## Regenerating the bundled data (maintainer only, read-only against git)
```bash
python3 scripts/build_site_data.py --repo <path to a clone with origin refs> --out .
python3 scripts/build_reports_archive.py --repo <clone> --out . --seal-scanner <prior-seal scanner>
```
- Both scripts only read remote-tracking refs and tags (`ls-tree`, `log`, `cat-file`). They never check out
  anything or write to any worktree.
- The prior-seal value scanner lives outside git, because its seal lists never leave the researcher's machine.
  Without it, every report is restricted (fail closed).

## Running the local controller (optional)
1. Copy `controller/config.example.json` to a location **outside git**. Fill in absolute paths and the pinned
   sha256 values.
2. Build the UI (`npm run build`), then point `ui_dir` at `dist/`.
3. `python3 -m controller --config /path/outside/git/config.json` (run from `command-center/`).
4. Open `http://127.0.0.1:<port>/aivd/`. Go to Settings and enter the one-time pairing code from the terminal.

Authorization variables are **never** set by the controller. See COMMAND_CENTER_SECURITY.md.

## One-click full check: run it locally and click "Run full check"
The static Pages site only shows the button as disabled ("Requires the local controller"). To use it:

1. **Install once** (from `command-center/`):
   ```bash
   npx -y npm@10.9.2 ci --ignore-scripts      # or: npm ci --ignore-scripts with npm >= 10
   npm run build                              # the controller serves dist/ at /aivd/
   ```
2. **Make a Python env with pytest** for the research suites, outside git:
   ```bash
   python3 -m venv ~/.local/share/aivd-command-center/venv-pytest
   ~/.local/share/aivd-command-center/venv-pytest/bin/pip install pytest==9.1.1
   ```
3. **Write the controller config outside git**: copy `controller/config.example.json` to
   `~/.config/aivd-command-center/config.json` and fill in the following.
   - `research_worktree`: the research worktree the guard and Part B gates are read from (for example the
     `research/aivd-rc6-partb-readiness` worktree). Set `expected_research_branch` to match.
   - `test_worktree`: a **clean** checkout of the same research commit where the suites run. The `ui/aivd-command-center`
     worktree works, because it contains the research tree at cb8dc31 and has no untracked protected files.
   - `worktrees`: every worktree you want snapshotted. The pipeline FAILS a test step if any of them changes.
   - `test_python`: the venv's `bin/python`. Optionally set `node` (absolute path) and `seal_scanner` (the prior-seal
     value scanner kept outside git). Also set `cc_dir` (this `command-center/` directory), `ui_dir` (`dist/`) and
     `state_dir` (outside git; run history and the audit log go here).
   - `runtime_files`: the Ollama binary and the model blobs with their pinned sha256. They are hashed and never executed.
4. **Start the controller from your own shell** (it binds 127.0.0.1 only):
   ```bash
   cd command-center
   python3 -m controller --config ~/.config/aivd-command-center/config.json
   ```
   The terminal prints `http://127.0.0.1:8765/aivd/` and a one-time pairing code. The code is also in
   `<state_dir>/pairing-<launch>.json` (mode 0600).
5. **Pair**: open the URL, go to **Settings & Activity**, enter the code and press **Pair**.
6. **Click Run full check** on Overview, Experiment Control or **Run Pipeline**. In the dialog you can tick *Include the
   full research suite*. Optionally, open *Also request the RC6 Part B handoff* (see below). Then press
   **Start pipeline**.
7. **Watch it run** on the Run Pipeline page. Each step is a node, connected by flowing lines. The active step pulses
   and finished steps turn green (PASS), red (FAIL/ERROR), amber (BLOCKED) or violet (SKIPPED). Each step has its own
   timer, there is a total timer, and the log streams redacted output.
8. **Read the results**: the verdict card (7-state lifecycle, total time, run id and timestamps), the step cards with
   reasons and durations, the timeline, the test-count donuts (historical failures are shown separately), the Part B
   gate checklist with *how to fix* for each gate, and the excluded tests with their reasons. **Export JSON** and
   **Export Markdown** download the redacted record. *Run history* lists past runs, and ticking two of them compares
   them side by side.
9. Stop the controller with Ctrl+C.

The fixed steps are: environment preflight, then aivd_rc6_guard status, then the RC6 suites (`tests/rc6_*`), then the
optional full suite, then the Command Center tests (Vitest and Python), then the content scan and outgoing manifest,
then **Model readiness** for the model you picked, then the RC6 Part B gate check, then the summary. Default timeouts are 1200 s per step and 3600 s in total (configurable;
bounded by the controller).

**Stopping children.** Every child the controller starts (test runners, scans, the guarded runner, a download's
`ollama serve`) runs in its own session with SIGINT and SIGTERM reset to their defaults, so a controller started in the
background (`cmd &`, nohup, a service manager, where SIGINT is ignored and that would be inherited) can still stop
them. On a timeout or cancel the controller sends SIGINT to the child's process group, waits `stop_grace_s` (default
5 s, 1-120), then SIGTERM, waits again, then SIGKILL, and records which signal ended it (`stopped_by`). Without
process groups (Windows) it falls back to terminate() then kill().

**Publishing a run for the hosted dashboard.** The hosted site has no controller. To show a finished run there,
export its JSON and run `python3 scripts/publish_run.py --run <run>.json`: it writes a sanitized copy (no log, no local
paths, host names, process ids, state/log locations, commands or environment; re-checked fail-closed) to
`public-data/runs/<id>.json`, `runs/latest.json` and `runs/index.json`. Scan it with
`scripts/scan_outgoing.py --tree . --seal-scanner <scanner> --require-seal-scan`, rebuild, and the view is at
`#/runs/latest` (also linked from Overview and Run Pipeline), labelled with the run's time in IST and its run id.
For the Pages publish commit, check it with
`scripts/outgoing_manifest.py --repo <repo> --tip <publish> --base origin/main --allow-pages-build --out <file>`:
the opt-in flag accepts only the build output under docs/ (index.html, 404.html identical to it, an empty .nojekyll,
hashed assets, and data files byte-identical to command-center/public-data), added or modified, never a path already
on main. Without the flag docs/ stays out of scope.

**Part B.** With any gate open, the Part B step is **BLOCKED** and lists every reason. Ollama is not started. Only when
every server-side gate passes, the operator's own shell exported the authorization variables before starting the
controller, and the exact phrase was typed in the dialog does the controller hand off to `scripts/rc6_partb_run.py`
through the existing guarded `rc6_run` path. Typing the phrase never bypasses a gate.

## Choosing the model to test with (model picker)
The **Run Pipeline** page (and, in compact form, Experiment Control) has a *Model for vulnerability testing* picker.
On the hosted Pages site it is read-only ("Requires local controller"): the catalog is listed with its approximate RAM
need, but fit and install status are *Not verified* and nothing can be selected or downloaded.

**Configure** (optional keys in the controller config, all outside git):
- `model_store`: the Ollama model store to read (and, if enabled, download into). Use the RC5/RC6 store recorded in the research branches'
  `aivd_post_rc3_local/models.py` (`RUNTIME`). If the temp directory was wiped, restore it from your verified backup.
- `ollama_binary`: the pinned Ollama 0.34.4 binary at the path recorded in that same `RUNTIME` table.
- `pull_enabled`: `false` by default. Set it to `true` to allow downloads.
- `pull_port` (default 11535; 11434 is refused) and `pull_timeout_s` (default 3600).
- `model_catalog`: optional path to an alternative catalog (validated the same way; it can never widen the RC6 allowlist).

**What the picker shows.** `GET /api/models` reads the store's manifest files (installed names come only from the
manifest paths), MemTotal/MemAvailable/SwapTotal from `/proc/meminfo`, the CPU count/model, whether a GPU compute device
exists (`/dev/nvidia*`, `/dev/kfd`; this box has none, so it is CPU only), and whether the VM memory balloon driver is
present. Listing **never starts Ollama** and makes no network call; *Refresh models* simply re-reads the store.

Each catalog model shows name, family, size, RAM need, a fit badge (**Fits** / **Tight** / **Exceeds**), an install
badge (**Installed** / **Missing** / **Incomplete** / **Differs from pin**) and whether it is **RC6-allowlisted**. Models
are grouped: installed and fits, then fits but needs a download, then too large (NOT RECOMMENDED, will likely run out of
memory). The controller recommends the best installed model that fits (RC6-allowlisted first, then the largest), or else
the best fitting catalog model, and the picker pre-selects it until you choose.

**RAM rule.** estimate = weights blob size + f16 KV cache at num_ctx 8192 (2 × layers × kv_heads × head_dim × 2 bytes ×
8192) + 300 MiB compute + 100 MiB runtime processes; recommended = estimate + 1 GiB headroom. *Fits*: MemAvailable ≥
recommended. *Tight*: estimate ≤ MemAvailable < recommended. *Exceeds*: MemAvailable < estimate (or MemTotal < estimate).
The RC6 memory gate (MemAvailable ≥ 7,600,000 kB before any runtime start) is separate and still applies to Part B.

**Downloads.** *Download selected* (after a confirmation that shows the size), or the run dialog's *Download it
automatically if missing (~X GB)* checkbox, asks the controller to fetch the model. Only catalog names are accepted. The
controller refuses if downloads are disabled, the model exceeds RAM, an Ollama process is already running, the port is
busy, disk space is short, or an installed copy differs from its pin. Otherwise it starts the configured binary's
`serve` on 127.0.0.1:`pull_port` with `OLLAMA_MODELS=<model_store>` and `OLLAMA_NOPRUNE=1`, streams `/api/pull`
progress into the UI and the run log, stops the server, then re-hashes every blob and compares the manifest and weights
digests with the pins. A mismatch FAILS. No model is loaded and no model call is made. One download runs at a time,
and *Cancel download* stops the server (partial blobs stay in the store for a later resume).

All three RC6 models are already installed and pinned in the RC5 store, so in practice a download is only needed
for catalog extras or after the store was lost. Pulling qwen3:8b (~5.2 GB) or the others is slow. No real pull was run
while this feature was built: the tests and the screenshot of download progress use a test double
(`controller/tests/fake_ollama.py`) that streams a pull response shaped like Ollama's and writes fixture blobs into a temp store.

**In the pipeline.** The *Model readiness* step records the choice, why it was chosen (the recommendation or an operator
choice), the RAM verdict with numbers, the install status before and after, any download time and the digest checks.
- Exceeds: **BLOCKED** with required versus available kB. Nothing is downloaded or started.
- Missing without the download confirmed: **BLOCKED**.
- Differs from pin: **FAIL**. The installed copy is never used or overwritten.
- Installed: every blob is re-hashed (cached by inode, size and mtime) and compared with the pins.
The Part B checklist then adds MODEL_READY. **A download never authorizes Part B**: catalog extras can never be used for
it, and every other gate still applies.

