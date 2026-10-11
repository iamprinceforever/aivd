# AIVD Command Center: security model

## Static site (GitHub Pages)
- It is read-only and serves only sanitized data files. It holds no tokens or secrets, writes nothing to browser
  storage and sets no cookies.
- A CSP meta tag limits scripts to `'self'` and network connections to `'self'` plus loopback
  (`127.0.0.1` / `localhost`). Report Markdown is rendered into React elements and never into innerHTML. Only
  `https:` links are allowed.
- With no live controller, every live value shows **Not verified / Local runner not connected**. Nothing is
  invented.

## Local controller (`controller/server.py`, stdlib only)
The chosen design is **same-origin**: the controller serves the built UI at `http://127.0.0.1:<port>/aivd/`
and the API at `/api/`. It was chosen because it needs no CORS at all.
| property | implementation |
|---|---|
| Network exposure | binds `127.0.0.1` only. The `Host` header must be `127.0.0.1:<port>` or `localhost:<port>` (defends against DNS rebinding) |
| Session secret | 32 random bytes per launch, held in memory only, used to MAC session tokens |
| Pairing | one-time code (`XXXX-XXXX-XXXX`) printed to the terminal and written as `pairing-<launch>.json` (0600) in a state dir outside git. It is single use, expires after 10 min, allows 5 failures before lockout, and the file is deleted after pairing |
| Session | bearer token + CSRF token, both kept only in the page's memory. 30 min idle and 8 h maximum lifetime |
| Origin | exact allowlist: the controller's own origins plus `extra_origins` from config (exact `scheme://host[:port]`, no wildcard, no credentials). A POST without an allowed Origin is rejected. Cross-origin use from the Pages site needs an explicit `extra_origins` entry and answers Private Network Access preflights only for that origin |
| CSRF | every state change needs `Authorization: Bearer`, `X-AIVD-CSRF` (constant-time compare), `Content-Type: application/json` and an allowed Origin |
| Input | strict per-endpoint schema (exact key set, types, lengths), body ≤ 4096 bytes, 10 s socket timeout, 30 s timeout per status probe |
| Operations | allowlist only: `GET /api/health`, `GET /api/status`, `GET /api/audit`, `POST /api/pair`, `POST /api/ops/rc6_run`, `POST /api/ops/rc6_reveal`, `POST /api/ops/cancel` (always 501). Anything else returns 404 or 405. No arbitrary commands, paths, models or output destinations |
| Read-only probes | MemAvailable from `/proc/meminfo` (threshold 7,600,000 kB); sha256 of the configured runtime files (probes **never** start the runtime; the only start is an operator-requested model download, see below); a read-only scan of `/proc/*/comm` for a running Ollama; `git status` of the configured worktrees (counts and hashes only, never file names); `python -m aivd_rc6_guard` status |
| Run / reveal | wired **only** to the existing guarded entry scripts `scripts/rc6_partb_run.py` and `scripts/rc6_analyze.py`. The server re-checks every gate first (guard START_RUNTIME/MODEL_CALL or REVEAL/SCORE, operator env present, memory, runtime hashes, no foreign runtime, no concurrent run, model allowlist, optional expected branch) and requires an exact typed confirmation phrase. Anything unverifiable is NOT_VERIFIED and refuses. The entry scripts and `aivd_rc6_guard` then check everything again |
| Cancel | **unavailable**. The entry script documents no cancel operation, so the controller does not signal it. On a run timeout (`max_run_seconds`) it sends SIGINT once, so the script's own `finally` stops its children |
| Progress | real only. The runner reports no incremental progress, so the UI shows elapsed time and the final status JSON (counts and status, with local paths redacted) |
| Audit log | `audit.jsonl` (0600) in the state dir: hash-chained entries with op, outcome and reason codes. Tokens and local paths are redacted. No request logging to stderr |
| Config | strict validation. Unknown keys, relative paths, wildcard origins, a state dir inside the research worktree or bad hashes all make the controller refuse to start |

## One-click pipeline (`controller/pipeline.py`)
- **Endpoints.** `POST /api/ops/run_pipeline` has the same Host, Origin, session, CSRF, JSON, size and strict-schema
  checks as every other POST. `GET /api/runs` and `GET /api/runs/<id>?since=<n>` need a paired session. The run id
  format is validated, and no other query parameter is accepted. Progress is delivered by polling, not SSE, because
  EventSource cannot send the bearer header and the session must not leave memory.
- **Fixed sequence.** The steps, every argv, every working directory, the pytest flags and the test exclusions are
  constants in `pipeline.py`. The body schema is exactly `{full_suite: bool, partb_confirm: str<=120, model_id: str<=40,
  attempt_id: str<=32, auto_pull: bool}`, and a non-empty `model_id` must be a catalog name (400 otherwise). Any extra key (for example `steps`, `command` or `cwd`) is rejected with 400. Client values
  never reach any argv. The model and attempt are only compared against the allowlist and regex for the Part B handoff.
- **Limits.** One pipeline runs at a time (409 otherwise), and none starts while an RC6 run is active. There is a
  per-step timeout and a total timeout. On timeout the whole process group gets SIGTERM, then SIGKILL, and the
  remaining steps are SKIPPED. Logs are capped at 4000 lines of 400 characters.
- **Environment.** Every variable whose name contains `AUTHORI` is removed from the environment of test and scan
  subprocesses. So are `PYTEST_ADDOPTS`, `PYTHONSTARTUP` and `NODE_OPTIONS`. `PYTHONDONTWRITEBYTECODE=1` is set and
  pytest runs with `-p no:cacheprovider --tb=no`, so no tracebacks or data values reach the log.
- **Worktrees.** Before and after each research test step, every configured worktree (plus `test_worktree`) is
  snapshotted by hashing `git status --porcelain --ignored` and `git diff`. Any change FAILS the step.
- **Excluded tests** (fixed, and shown in the UI with these reasons):
  - `tests/post_rc3_local/test_runner_entrypoint.py`: it sets a run-authorization variable in a subprocess.
  - Two `tests/rc6_diag/test_containment_isolation.py` tests: they attempt a connection to 127.0.0.1:11434.
  - The endgame tests were inspected. They neither execute the Ollama binary nor open sockets, so they run.
- **Historical failures.** The 4 known `tests/rc5_gen/test_design.py` failures at the research tip are listed in
  `HISTORICAL_FAILURES` and labelled pre-existing/historical. Any other failure FAILS the step.
- **Redaction.** Log lines go through the controller's token and local-path redaction, the shared secret patterns,
  and replacement of 32+ character hex runs. Any line matching an O1–O8 outcome pattern is replaced by
  `<line withheld: matched an outcome pattern>`.
- **Persistence.** Each run is written atomically, mode 0600, to `<state_dir>/runs/<id>.json`. The newest 50 are
  kept. State lives outside git, and start, completion and Part B decisions are recorded in the hash-chained audit log.
- **Part B.** The step builds a checklist (prereg approval, OSF registration, G_AUTHOR, G_AUDIT, G_FROZEN, G_CORPUS,
  operator env, `AIVD_RC6_PARTB_AUTHORIZED`, memory, runtime hashes, no foreign Ollama, no active run, entry script,
  research branch, model/attempt, confirmation phrase), each with its exact reason and how to fix it.
  - OSF registration is not machine-checkable. It counts as satisfied only through an APPROVED `RC6_APPROVALS.json`
    and fails closed otherwise.
  - If anything is open, the step is BLOCKED and nothing is started.
  - The handoff calls the existing guarded `op_run`. That re-checks every gate server-side, and
    `scripts/rc6_partb_run.py` checks `aivd_rc6_guard` again.
  - In tests, the handoff is always a mock.
- **Verdict.** The summary uses the 7-state lifecycle. It never says "experiment ready" or "succeeded". The pipeline
  itself never runs the experiment; a handoff only starts the guarded runner, whose own result is reported separately.

## Model picker and downloads (`controller/models.py`)
- **Endpoints.** `GET /api/models` needs a paired session. It is read-only: it scans the configured store's manifest
  files (no symlinks, at most 200 manifests, each ≤ 64 KB), reads `/proc`, `/dev` and `/sys`, never starts Ollama
  and never touches the network. `POST /api/ops/pull_model {model_id}` and `POST /api/ops/cancel_pull {}` carry the
  same Host, Origin, session, CSRF, JSON, size and exact-schema checks as every other POST.
- **Allowlist.** Only names in the validated catalog (`controller/models_catalog.json`, or `model_catalog` from the
  operator config) can be pulled or selected. Anything else gets 400. The catalog loader refuses an entry marked
  `rc6_allowlisted` unless its name is in the controller's fixed `ALLOWED_MODELS`, and refuses RC6 entries without
  pinned digests. Extras carry no digest: none is invented.
- **When Ollama runs.** Only during an operator-requested download (the button, or the run dialog's explicit `~X GB`
  confirmation, which sends `auto_pull: true`). Before it starts, the controller refuses if downloads are disabled,
  the binary or store is missing, an Ollama process is already running (never signalled), the port is busy, RAM is
  *Exceeds*, disk space is short, or an installed copy differs from its pin.
  - Argv is fixed: `[ollama_binary, "serve"]`. The environment is an allowlist: PATH, locale, TZ, proxy and CA
    variables, plus `HOME=<state_dir>/ollama-home` (0700, so the keypair Ollama creates stays outside git and the
    user's home), `OLLAMA_HOST=127.0.0.1:<pull_port>` (11434 refused), `OLLAMA_MODELS=<model_store>`,
    `OLLAMA_NOPRUNE=1` (so the server can never prune existing blobs, including the RC5 store), `OLLAMA_KEEP_ALIVE=0`
    and `OLLAMA_NOHISTORY=1`. No `*AUTHORI*`, token or secret variable is passed.
  - The server is stopped (SIGTERM, then SIGKILL to its process group) in a `finally` block, and also on cancel and
    on timeout.
  - No model is loaded and no generate/chat call exists in the code.
- **Verification.** After a pull, every blob is re-hashed against its manifest digest, and the manifest and weights
  digests are compared with the pins. Any mismatch FAILS. The installed copy is reported as *Differs from pin* and is
  never used or overwritten.
- **Limits.** One download at a time, and none while a pipeline or an RC6 run is active (the pipeline's own Model
  readiness step uses the same slot). There is an overall timeout and a 300 s stall timeout. The progress log is capped at 300
  redacted lines. Registry errors are redacted. The server's own output goes to `<state_dir>/ollama-pull-serve.log`
  (0600) and is never served.
- **Part B.** A download, or a PASS of *Model readiness*, only satisfies the MODEL_READY checklist item. Part B still
  needs every guard gate, the operator's own authorization environment, the memory gate and the typed phrase, and
  only the three preregistered models pass MODEL_ATTEMPT.
- **Static site.** The Pages bundle contains only the public catalog (names, sizes, the public pins), and the picker
  is disabled there. There is no download path without the paired local controller, and CI never starts Ollama.

## Authorization variables (never set by the controller)
The controller passes its **inherited** environment unchanged to the guard and the entry scripts. An
authorized operator who holds an approved prereg supplies the variables in their own shell before starting the
controller:
```bash
# only after RC6_APPROVALS.json is APPROVED for the action and every readiness gate passes
export AIVD_RC6_AUTHORIZE_START_RUNTIME="START_RUNTIME:<approved prereg sha256>"
export AIVD_RC6_AUTHORIZE_MODEL_CALL="MODEL_CALL:<approved prereg sha256>"
export AIVD_RC6_PARTB_AUTHORIZED=<as defined by aivd_rc6_run.transport_policy>
python3 -m controller --config /path/outside/git/config.json
```
`aivd_rc6_guard` validates the values. A test checks that the controller source contains no env assignment.

## Tests proving fail-closed behaviour
`controller/tests/test_controller.py` covers:
- refusal for each gate on its own;
- guard missing, unreadable or incomplete;
- insufficient or unreadable memory, runtime mismatch, foreign runtime and missing entry script;
- invalid model, attempt or confirmation;
- CSRF, Origin, Host, size, type, schema, unknown ops, pairing lockout and expiry, traversal and slow clients;
- the mocked runner completing, failing, refusing (exit 3) and timing out, plus no concurrent runs;
- a read-only check that the repository's real `aivd_rc6_guard` refuses run and reveal.

The real research runner is never invoked by the tests.

## Build and publication scanners
`scripts/scan_outgoing.py` runs after every build and fails it on any of these:
- a protected path;
- a deny-listed RC6 document name or blob;
- outcome patterns O1–O8 (unless reviewed and allowlisted by path + sha256 + id);
- a local machine path;
- a secret pattern;
- a seal-like key;
- a failed prior-seal value scan, when the scanner is supplied.

It prints counts only. The files that must contain these rules are exempt from text rules but still get
path/blob checks. A separate full regex secret scan with no exemptions runs at publication time.
