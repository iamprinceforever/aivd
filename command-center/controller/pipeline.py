"""One-click check pipeline for the AIVD Command Center controller (Python stdlib only).

The step list, every command, every argument, every path and every exclusion is defined HERE, server-side.
The client can only choose two things: whether to include the full research suite, and (for the RC6 Part B
step) supply the typed confirmation phrase + a preregistered model id + an attempt id. Nothing else.

Safety properties (see docs/COMMAND_CENTER_SECURITY.md, "One-click pipeline"):
  * at most one pipeline at a time; per-step and total timeouts (process groups are terminated on timeout);
  * subprocesses run with every *AUTHORI* variable REMOVED from their environment, PYTHONDONTWRITEBYTECODE=1 and
    pytest's cache provider disabled; research worktrees are snapshotted (git status --ignored + diff hash) before
    and after every research test step and the step FAILS if anything changed;
  * tests that execute the Ollama binary, open a socket to 127.0.0.1:11434 or set authorization env vars are
    excluded by a fixed, documented list (shown in the UI with the reason);
  * log lines are redacted (tokens, secrets, local paths, long hex values) and lines matching any RC5/RC6
    outcome pattern are withheld; logs are capped; nothing outside the redacted summary is persisted;
  * the RC6 Part B step never starts Ollama: it evaluates every server-side gate and reports BLOCKED with each
    exact reason; only when every gate passes AND the operator's own authorization env is present AND the exact
    confirmation phrase was typed does it hand off to the existing guarded entry script.
"""

import datetime
import hashlib
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from controller import procs as PR

try:  # shared scan rules (outcome / secret patterns); optional so the controller still starts without them
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import scan_rules as _rules  # noqa: E402
except Exception:  # pragma: no cover - defensive
    _rules = None
finally:
    sys.path.pop(0)

STEP_DEFS = (
    ("preflight", "Environment preflight"),
    ("guard", "Authorization / guard status"),
    ("rc6_tests", "RC6 research test suites"),
    ("full_suite", "Full research test suite"),
    ("cc_tests", "Command Center tests"),
    ("scans", "Publication & contamination scans"),
    ("model", "Model readiness (selected model)"),
    ("partb", "RC6 Part B experiment (guarded)"),
    ("summary", "Summary (7-state lifecycle)"),
)
STATUSES = ("PASS", "FAIL", "BLOCKED", "SKIPPED", "ERROR")
RC6_SUITES = ("rc6_diag", "rc6_gen", "rc6_run", "rc6_provider", "rc6_analysis", "rc6_evidence", "rc6_hygiene")
# Fixed exclusions: (pytest node id or file, reason shown to the operator). Never client-supplied.
EXCLUDED_TESTS = (
    ("tests/post_rc3_local/test_runner_entrypoint.py",
     "sets the LOCAL-V1 run-authorization variable in a subprocess (runs the real runner against a fake server)"),
    ("tests/rc6_diag/test_containment_isolation.py::test_no_socket_to_ollama_port",
     "attempts a socket connection to 127.0.0.1:11434 (expected to be intercepted, but the pipeline never opens one)"),
    ("tests/rc6_diag/test_containment_isolation.py::test_real_transport_construction_fails",
     "attempts an HTTP request to 127.0.0.1:11434 (expected to be intercepted, but the pipeline never opens one)"),
)
# Known failures at the research tip that predate the Command Center (design-phase assertions that later
# research commits superseded). Labelled "pre-existing/historical" in the UI; any OTHER failure fails the step.
HISTORICAL_FAILURES = (
    "tests/rc5_gen/test_design.py::test_preregistration_frozen_at_design_without_d1_d4_gate",
    "tests/rc5_gen/test_design.py::test_corpus_dependent_fields_and_authorizations_pending",
    "tests/rc5_gen/test_design.py::test_provider_gate_requires_frozen_design_and_nothing_drawn",
    "tests/rc5_gen/test_design.py::test_preflight_refuses_at_design_and_passes_when_fully_bound",
)
RUN_ID_RX = re.compile(r"^r\d{8}T\d{6}-[0-9a-f]{6}$")
MAX_LOG_LINES = 4000
MAX_LINE = 400
HISTORY_KEEP = 50
DEFAULT_STEP_TIMEOUT = 900
DEFAULT_TOTAL_TIMEOUT = 3600
HEX_RX = re.compile(r"\b[0-9a-f]{32,}\b", re.I)
SUMMARY_RX = re.compile(r"(\d+) (passed|failed|skipped|xfailed|xpassed|errors?|deselected|warnings?)")
VITEST_RX = re.compile(r"^\s*Tests\s+(.*)$")
UNITTEST_RAN_RX = re.compile(r"^Ran (\d+) tests? in")
UNITTEST_FAIL_RX = re.compile(r"^FAILED \((.*)\)")

# How each Part B checklist item can be fixed (shown in the UI). Wording is design-level only.
FIXES = {
    "PREREG_APPROVAL": "Complete the separate review of the redacted preregistration and commit an APPROVED "
                       "RC6_APPROVALS.json naming its current sha256 and listing START_RUNTIME and MODEL_CALL.",
    "OSF_REGISTRATION": "Register the approved preregistration on OSF before the approval is recorded; the "
                        "controller can only see it through the APPROVED RC6_APPROVALS.json.",
    "G_AUTHOR": "Have an independent, outcome-blind author produce the construction set and a different human "
                "reviewer accept and pin it (G_AUTHOR).",
    "G_AUDIT": "Resolve the historical protected-path audit and record a resolution naming the audit file's "
               "current sha256 (G_AUDIT).",
    "G_FROZEN": "Restore or re-freeze the frozen analysis manifest so every pinned hash matches (G_FROZEN).",
    "G_CORPUS": "A committed RC6 corpus is required; it can only be created after authorization (G_CORPUS).",
    "OPERATOR_ENV": "The authorized operator exports AIVD_RC6_AUTHORIZE_START_RUNTIME / _MODEL_CALL "
                    "(\"<ACTION>:<approved prereg sha256>\") in their OWN shell before starting the controller.",
    "PARTB_ENV": "The authorized operator exports AIVD_RC6_PARTB_AUTHORIZED in their own shell before starting "
                 "the controller; the controller never sets it.",
    "MEMORY": "Free memory until MemAvailable is at least 7,600,000 kB (close other workloads).",
    "RUNTIME_FILES": "Configure runtime_files with the pinned sha256 of the Ollama binary and model blobs.",
    "NO_FOREIGN_RUNTIME": "Stop the already-running Ollama process yourself; the controller never signals it.",
    "NO_ACTIVE_RUN": "Wait for the current run to finish.",
    "ENTRY": "The guarded entry script scripts/rc6_partb_run.py must exist in the research worktree.",
    "RESEARCH_BRANCH": "Check out the expected research branch in the research worktree.",
    "CONFIRM_PHRASE": "Type the exact confirmation phrase in the run dialog (only once every other gate passes).",
    "MODEL_READY": "Select a catalog model that fits MemAvailable; if it is missing, confirm the download so the Model "
                   "readiness step can fetch and verify it (a download never authorizes Part B).",
    "MODEL_ATTEMPT": "Choose a preregistered model and a valid attempt id (lowercase letters, digits, - and _).",
}


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def make_run_id():
    return "r" + time.strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(3)


class Pipeline:
    """Owns the single pipeline slot, the fixed step sequence, logs and persisted history."""

    def __init__(self, ctl, run_cmd=None, partb_handoff=None, clock=time.monotonic):
        self.ctl = ctl
        cfg = ctl.cfg
        self.state_dir = Path(cfg["state_dir"]) / "runs"
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.step_timeout = cfg.get("pipeline_step_timeout_s") or DEFAULT_STEP_TIMEOUT
        self.total_timeout = cfg.get("pipeline_total_timeout_s") or DEFAULT_TOTAL_TIMEOUT
        self.stop_grace = cfg.get("stop_grace_s") or PR.DEFAULT_GRACE_S
        self.last_stop_signal = None
        self.run_cmd = run_cmd or self._run_cmd
        self.partb_handoff = partb_handoff or self._default_handoff
        self.clock = clock
        self.lock = threading.Lock()
        self.current = None          # the run doc being executed (shared, guarded by self.lock)
        self.thread = None

    # ---------- persistence ----------
    def _path(self, rid):
        return self.state_dir / f"{rid}.json"

    def _persist(self, doc):
        p = self._path(doc["id"])
        tmp = p.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            json.dump(doc, fh)
        os.replace(tmp, p)
        files = sorted(self.state_dir.glob("r*.json"))
        for old in files[:-HISTORY_KEEP]:
            try:
                old.unlink()
            except OSError:
                pass

    def history(self):
        out = []
        for p in sorted(self.state_dir.glob("r*.json"), reverse=True)[:HISTORY_KEEP]:
            try:
                d = json.loads(p.read_text())
            except (OSError, ValueError):
                continue
            out.append({k: d.get(k) for k in ("id", "started_at", "finished_at", "state", "total_duration_s",
                                                "verdict", "options")}
                       | {"steps": [{k: s.get(k) for k in ("id", "label", "status", "duration_s")}
                                    for s in d.get("steps", [])]})
        return out

    def get(self, rid, since=0):
        if not RUN_ID_RX.fullmatch(rid or ""):
            return None
        with self.lock:
            if self.current and self.current["id"] == rid:
                doc = json.loads(json.dumps(self.current))
            else:
                doc = None
        if doc is None:
            try:
                doc = json.loads(self._path(rid).read_text())
            except (OSError, ValueError):
                return None
        since = max(0, int(since))
        doc["log_offset"] = since
        doc["log"] = doc.get("log", [])[since:]
        return doc

    # ---------- logging ----------
    @staticmethod
    def redact_line(line):
        s = str(line).rstrip("\n")[:MAX_LINE * 2]
        if _rules is not None:
            if _rules.outcome_hits(s):
                return "<line withheld: matched an outcome pattern>"
            for rx in _rules.SECRET_RX.values():
                s = rx.sub("<redacted-secret>", s)
        s = _srv().redact(s)
        s = HEX_RX.sub("<hex>", s)
        return s[:MAX_LINE]

    def _log(self, doc, step, line):
        with self.lock:
            doc["log_total"] = doc.get("log_total", 0) + 1
            if len(doc["log"]) < MAX_LOG_LINES:
                doc["log"].append({"t": round(self.clock() - doc["_t0"], 2), "step": step,
                                   "line": self.redact_line(line)})
            elif len(doc["log"]) == MAX_LOG_LINES:
                doc["log"].append({"t": round(self.clock() - doc["_t0"], 2), "step": step,
                                   "line": "<log cap reached; further lines dropped>"})

    # ---------- process execution ----------
    def _run_cmd(self, argv, cwd, env, timeout, on_line):
        """Run a FIXED argv (never shell); stream lines; on timeout stop the process group (SIGINT, SIGTERM, SIGKILL
        with a grace period between each; see controller/procs.py) and record which signal ended it."""
        self.last_stop_signal = None
        p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, **PR.spawn_kwargs())
        lines = []

        def pump():
            for raw in iter(p.stdout.readline, b""):
                ln = raw.decode("utf-8", "replace")
                lines.append(ln)
                if len(lines) > 5000:
                    del lines[:1000]
                on_line(ln)
        t = threading.Thread(target=pump, daemon=True)
        t.start()
        timed_out = False
        try:
            p.wait(timeout=max(1, timeout))
        except subprocess.TimeoutExpired:
            timed_out = True
            self.last_stop_signal = PR.stop(p, self.stop_grace)
            on_line(f"<step timeout: process group stopped by {self.last_stop_signal}>")
        t.join(timeout=5)
        try:
            p.stdout.close()
        except OSError:
            pass
        return p.returncode, lines, timed_out

    def _env(self):
        env = {k: v for k, v in self.ctl.env.items()
               if "AUTHORI" not in k.upper() and k not in ("PYTEST_ADDOPTS", "PYTHONSTARTUP", "NODE_OPTIONS")}
        env.update({"PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1", "FORCE_COLOR": "0", "CI": "1"})
        return env

    # ---------- public entry ----------
    def start(self, opts):
        mid = opts.get("model_id") or ""
        mm = getattr(self.ctl, "models", None)
        if mid and mm is not None and mid not in mm.by_name:
            return 400, {"error": "model_id is not in the AIVD model catalog (arbitrary names are rejected)"}
        if mm is not None and mm.puller.busy():
            return 409, {"error": "a model download is in progress; wait for it or cancel it"}
        with self.ctl.lock:
            if self.ctl.run.get("state") == "running":
                return 409, {"error": "an RC6 run is in progress; the pipeline will not start"}
        with self.lock:
            if self.current is not None and self.current.get("state") == "running":
                return 409, {"error": "a pipeline is already running", "run_id": self.current["id"]}
            rid = make_run_id()
            doc = {"id": rid, "schema": 1, "started_at": now_iso(), "finished_at": None, "state": "running",
                   "options": {"full_suite": bool(opts.get("full_suite")),
                               "partb_handoff_requested": bool(opts.get("partb_confirm")),
                               "model_id": mid or None, "auto_pull": bool(opts.get("auto_pull"))},
                   "limits": {"step_timeout_s": self.step_timeout, "total_timeout_s": self.total_timeout},
                   "excluded_tests": [{"id": i, "reason": r} for i, r in EXCLUDED_TESTS],
                   "steps": [{"id": sid, "label": lbl, "status": "PENDING", "reason": "", "started_at": None,
                              "ended_at": None, "duration_s": None, "details": {}} for sid, lbl in STEP_DEFS],
                   "log": [], "log_total": 0, "verdict": None, "total_duration_s": None, "_t0": self.clock()}
            self.current = doc
        self.ctl.audit("run_pipeline", "started", [rid])
        self.thread = threading.Thread(target=self._execute, args=(doc, dict(opts)), daemon=True)
        self.thread.start()
        return 202, {"run_id": rid, "status": "STARTED", "steps": [s for s, _ in STEP_DEFS]}

    def _public(self, doc):
        return {k: v for k, v in doc.items() if not k.startswith("_")}

    def _execute(self, doc, opts):
        t0 = doc["_t0"]
        total_deadline = t0 + self.total_timeout
        ctx = {"opts": opts, "results": {}}
        for step in doc["steps"]:
            sid = step["id"]
            fn = getattr(self, f"step_{sid}")
            now = self.clock()
            if now >= total_deadline and sid != "summary":
                self._finish_step(doc, step, now, now, "SKIPPED", "total pipeline timeout reached before this step")
                continue
            deadline = min(now + self.step_timeout, total_deadline) if sid != "summary" else now + 30
            with self.lock:
                step["status"], step["started_at"] = "RUNNING", now_iso()
            self._log(doc, sid, f"== {step['label']} ==")
            box = {}

            def target():
                try:
                    box["r"] = fn(doc, ctx, deadline)
                except Exception as e:  # never leak a traceback; record a redacted error
                    box["r"] = ("ERROR", f"step raised {type(e).__name__}: {e}", {})
            th = threading.Thread(target=target, daemon=True)
            th.start()
            th.join(timeout=max(1, deadline - self.clock()) + 15)
            end = self.clock()
            if "r" not in box:
                status, reason, details = "ERROR", "step exceeded its timeout and was abandoned", {}
            else:
                status, reason, details = box["r"]
            ctx["results"][sid] = (status, reason, details)
            self._finish_step(doc, step, now, end, status, reason, details)
        with self.lock:
            doc["state"] = "completed"
            doc["finished_at"] = now_iso()
            doc["total_duration_s"] = round(self.clock() - t0, 2)
            doc["verdict"] = ctx.get("verdict")
            pub = self._public(doc)
        self._persist(pub)
        self.ctl.audit("run_pipeline", "completed", [doc["id"], (doc["verdict"] or {}).get("headline", "")])

    def _finish_step(self, doc, step, start, end, status, reason, details=None):
        redact = _srv().redact
        assert status in STATUSES
        with self.lock:
            step.update({"status": status, "reason": redact(reason)[:2000], "ended_at": now_iso(),
                         "duration_s": round(end - start, 2),
                         "details": json.loads(redact(json.dumps(details or {})))})
            if not step["started_at"]:
                step["started_at"] = step["ended_at"]
            pub = self._public(doc)
        self._log(doc, step["id"], f"-> {status}: {reason}")
        self._persist(pub)

    # ---------- helpers ----------
    def _snapshot(self):
        snap = {}
        roots = dict(self.ctl.cfg["worktrees"])
        roots["test_worktree"] = str(self._test_root())
        for name, p in sorted(roots.items()):
            try:
                st = subprocess.run(["git", "--no-optional-locks", "-C", p, "status", "--porcelain=v1", "--ignored"],
                                    capture_output=True, timeout=60, check=True).stdout
                df = subprocess.run(["git", "--no-optional-locks", "-C", p, "diff"], capture_output=True, timeout=60,
                                    check=True).stdout
                snap[name] = hashlib.sha256(st).hexdigest() + hashlib.sha256(df).hexdigest()
            except (subprocess.SubprocessError, OSError):
                snap[name] = "unavailable"
        return snap

    def _test_root(self):
        return Path(self.ctl.cfg.get("test_worktree") or self.ctl.cfg["research_worktree"])

    def _cc_dir(self):
        return Path(self.ctl.cfg.get("cc_dir") or Path(__file__).resolve().parents[1])

    def _remaining(self, deadline):
        return max(1, deadline - self.clock())

    @staticmethod
    def parse_pytest(lines):
        counts = {}
        for ln in reversed(lines):
            if "==" in ln or re.search(r"\d+ (passed|failed)", ln):
                found = SUMMARY_RX.findall(ln)
                if found and ("passed" in ln or "failed" in ln or "error" in ln or "skipped" in ln):
                    for n, k in found:
                        k = {"error": "errors", "warning": "warnings"}.get(k, k)
                        counts[k] = counts.get(k, 0) + int(n)
                    break
        failing = []
        for ln in lines:
            m = re.match(r"^(FAILED|ERROR) (\S+)", ln.strip())
            if m:
                failing.append(m.group(2))
        return counts, failing

    def _pytest_step(self, doc, sid, paths, deadline):
        py = self.ctl.cfg.get("test_python")
        root = self._test_root()
        if not py or not Path(py).is_file():
            return "ERROR", "no test interpreter configured (config key test_python must point at a Python with pytest)", {}
        probe_rc, _, _ = self.run_cmd([py, "-c", "import pytest"], str(root), self._env(), 60, lambda ln: None)
        if probe_rc != 0:
            return "ERROR", "configured test interpreter cannot import pytest", {}
        paths = [p for p in paths if (root / p).exists()]
        if not paths:
            return "ERROR", "no matching test directories in the test worktree", {}
        argv = [py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=no", "-rfE", "--color=no", *paths]
        for tid, _ in EXCLUDED_TESTS:
            argv += ["--deselect", tid] if "::" in tid else ["--ignore", tid]
        before = self._snapshot()
        rc, lines, timed_out = self.run_cmd(argv, str(root), self._env(), self._remaining(deadline),
                                            lambda ln: self._log(doc, sid, ln))
        after = self._snapshot()
        changed = sorted(k for k in before if before[k] != after.get(k))
        counts, failing = self.parse_pytest(lines)
        hist = [f for f in failing if f in HISTORICAL_FAILURES]
        new = [f for f in failing if f not in HISTORICAL_FAILURES]
        details = {"counts": counts, "failing_new": [self.redact_line(f) for f in new][:100],
                   "failing_historical": hist, "excluded": [i for i, _ in EXCLUDED_TESTS],
                   "suites": paths, "worktrees_unchanged": not changed, "worktrees_changed": changed,
                   "exit_code": rc}
        if timed_out:
            details["stopped_by"] = self.last_stop_signal
            return "ERROR", f"pytest exceeded the step timeout and was stopped ({self.last_stop_signal or 'signal'})", \
                details
        if changed:
            return "FAIL", f"research worktree state changed during tests: {', '.join(changed)}", details
        if not counts:
            return "ERROR", f"could not parse the pytest summary (exit {rc})", details
        summ = ", ".join(f"{v} {k}" for k, v in counts.items() if k not in ("warnings",))
        if new or counts.get("errors"):
            return "FAIL", f"{summ}; {len(new)} failing test(s) not on the historical list", details
        if hist:
            return "PASS", f"{summ}; the {len(hist)} failure(s) are pre-existing/historical (rc5_gen design-phase " \
                           f"assertions superseded by later research commits)", details
        return "PASS", summ, details

    # ---------- steps (fixed) ----------
    def step_preflight(self, doc, ctx, deadline):
        mem = self.ctl.memory()
        rt = self.ctl.runtime(timeout=self._remaining(deadline))
        wts = self.ctl.worktrees()
        running = rt.get("ollama_process_running")
        problems = []
        if mem["state"] != "PASS":
            problems.append(f"memory gate: {mem['reason']}")
        if rt["state"] != "PASS":
            problems.append(f"runtime files: {rt['reason']}")
        if running:
            problems.append("an Ollama process is already running (never signalled)")
        elif running is None:
            problems.append("process table unreadable")
        for w in wts:
            self._log(doc, "preflight", f"worktree {w['name']}: " + (w.get("error") or
                      f"{w['branch']} @ {w['head']} modified={w['modified']} untracked={w['untracked']}"))
        self._log(doc, "preflight", mem["reason"])
        for f in rt["files"]:
            self._log(doc, "preflight", f"runtime file {f['name']}: {f['state']}")
        details = {"memory": mem, "runtime": rt, "worktrees": wts, "ollama_started_by_controller": False}
        ctx["preflight"] = details
        if problems:
            return "FAIL", "; ".join(problems), details
        return "PASS", "memory gate met, runtime files match pinned hashes (Ollama not started), no foreign runtime", details

    def step_guard(self, doc, ctx, deadline):
        g = self.ctl.guard()
        ctx["guard"] = g
        if not g.get("available"):
            return "ERROR", g.get("error", "guard unavailable (fail closed)"), {"guard": g}
        gates = {}
        for act in ("START_RUNTIME", "MODEL_CALL", "REVEAL", "SCORE"):
            for r in g["actions"].get(act, []):
                m = re.match(r"^(G_[A-Z]+):\s*(.*)$", r)
                key = m.group(1) if m else ("APPROVALS" if "RC6_APPROVALS" in r or "preregistration" in r
                                             else ("OPERATOR_ENV" if "environment authorization" in r else "OTHER"))
                gates.setdefault(key, set()).add(r)
        for k, v in sorted(gates.items()):
            for r in sorted(v):
                self._log(doc, "guard", f"{k}: {r}")
        details = {"actions": g["actions"], "gates": {k: sorted(v) for k, v in sorted(gates.items())}}
        blocked = [a for a in ("START_RUNTIME", "MODEL_CALL") if g["actions"].get(a)]
        if blocked or "START_RUNTIME" not in g["actions"]:
            return "BLOCKED", "aivd_rc6_guard refuses " + ", ".join(blocked or ["START_RUNTIME"]) + ": " + \
                "; ".join(sorted(gates)) + " open", details
        return "PASS", "aivd_rc6_guard reports no open gate for START_RUNTIME and MODEL_CALL", details

    def step_rc6_tests(self, doc, ctx, deadline):
        return self._pytest_step(doc, "rc6_tests", [f"tests/{s}" for s in RC6_SUITES], deadline)

    def step_full_suite(self, doc, ctx, deadline):
        if not ctx["opts"].get("full_suite"):
            return "SKIPPED", "not requested (enable \"Include full research suite\")", {}
        return self._pytest_step(doc, "full_suite", ["tests"], deadline)

    def step_cc_tests(self, doc, ctx, deadline):
        cc = self._cc_dir()
        env = self._env()
        details = {}
        node = self.ctl.cfg.get("node") or _which("node")
        vit = cc / "node_modules" / "vitest" / "vitest.mjs"
        ok = True
        reasons = []
        if node and vit.is_file():
            rc, lines, to = self.run_cmd([node, str(vit), "run"], str(cc), env, self._remaining(deadline),
                                         lambda ln: self._log(doc, "cc_tests", ln))
            v = {}
            for ln in lines:
                m = VITEST_RX.match(re.sub(r"\x1b\[[0-9;]*m", "", ln))
                if m:
                    v = {k: int(n) for n, k in re.findall(r"(\d+) (passed|failed|skipped|todo)", m.group(1))}
            details["vitest"] = {"counts": v, "exit_code": rc, "timed_out": to}
            if to:
                details["vitest"]["stopped_by"] = self.last_stop_signal
            if to or rc != 0 or not v:
                ok = False
                reasons.append("vitest " + ("timed out" if to else f"failed (exit {rc})"))
            else:
                reasons.append(f"vitest {v.get('passed', 0)} passed")
        else:
            ok = False
            reasons.append("vitest unavailable (node or node_modules missing: run npm ci in command-center/)")
            details["vitest"] = {"counts": {}, "unavailable": True}
        py_total, py_fail, py_ok = 0, 0, True
        for args in (["-m", "unittest", "discover", "-s", "controller/tests", "-t", "."],
                     ["-m", "unittest", "discover", "-s", "scripts/tests", "-t", "scripts"]):
            rc, lines, to = self.run_cmd([sys.executable, *args], str(cc), env, self._remaining(deadline),
                                         lambda ln: self._log(doc, "cc_tests", ln))
            for ln in lines:
                m = UNITTEST_RAN_RX.match(ln.strip())
                if m:
                    py_total += int(m.group(1))
                m = UNITTEST_FAIL_RX.match(ln.strip())
                if m:
                    py_fail += sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", m.group(1)))
            if to or rc != 0:
                py_ok = False
        details["python"] = {"counts": {"passed": py_total - py_fail, "failed": py_fail}, "ok": py_ok}
        reasons.append(f"python {py_total - py_fail}/{py_total} passed" if py_ok else
                       f"python tests failed ({py_fail} of {py_total})")
        ok = ok and py_ok
        return ("PASS" if ok else "FAIL"), "; ".join(reasons), details

    def step_scans(self, doc, ctx, deadline):
        cc = self._cc_dir()
        env = self._env()
        argv = [sys.executable, "scripts/scan_outgoing.py", "--tree", "."]
        if (cc / "dist").is_dir():
            argv += ["--dist", "dist"]
        seal = self.ctl.cfg.get("seal_scanner")
        if seal:
            argv += ["--seal-scanner", seal, "--require-seal-scan"]
        rc, lines, to = self.run_cmd(argv, str(cc), env, self._remaining(deadline), lambda ln: None)
        res = _last_json(lines)
        details = {"content_scan": {k: res.get(k) for k in ("files_scanned", "files_with_hits", "hit_counts",
                                                            "prior_seal_scan", "pass")} if res else None}
        reasons, ok = [], True
        if to or not res:
            ok = False
            reasons.append("content scan did not complete")
        else:
            ok = ok and res.get("pass") is True
            reasons.append(f"content scan: {res.get('files_scanned')} files, {res.get('files_with_hits')} with hits"
                           + ("" if seal else " (prior-seal scan not configured)"))
            self._log(doc, "scans", f"content scan counts: {json.dumps(res.get('hit_counts'))}")
        top = subprocess.run(["git", "--no-optional-locks", "-C", str(cc), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=30)
        if top.returncode == 0:
            out = self.state_dir / f"{doc['id']}-manifest.json"
            rc, lines, to = self.run_cmd([sys.executable, "scripts/outgoing_manifest.py", "--repo", top.stdout.strip(),
                                          "--tip", "HEAD", "--base", "origin/main", "--out", str(out)],
                                         str(cc), env, self._remaining(deadline), lambda ln: None)
            m = _last_json(lines)
            if m:
                details["manifest"] = {k: m.get(k) for k in ("outgoing_commits", "outgoing_file_changes",
                                                             "deny_listed", "unpublished_non_ui", "branch_safety")}
                bs = (m.get("branch_safety") or {})
                reasons.append(f"manifest vs origin/main: {m.get('outgoing_commits')} commits, "
                               f"{m.get('deny_listed')} deny-listed, branch safety {'PASS' if bs.get('pass') else 'FAIL'}")
                for r in bs.get("reasons", []):
                    self._log(doc, "scans", f"branch safety: {r}")
                ok = ok and bs.get("pass") is True
            else:
                ok = False
                reasons.append("outgoing manifest did not complete")
        return ("PASS" if ok else "FAIL"), "; ".join(reasons), details

    # ---------- model readiness ----------
    def _step_progress(self, doc, sid, prog):
        with self.lock:
            for st in doc["steps"]:
                if st["id"] == sid and st["status"] == "RUNNING":
                    st["details"] = {**st.get("details", {}), "progress": prog}

    def step_model(self, doc, ctx, deadline):
        mm = getattr(self.ctl, "models", None)
        opts = ctx["opts"]
        mid = opts.get("model_id") or ""
        if mm is None:
            return "ERROR", "model manager unavailable", {}
        if not mid:
            return "SKIPPED", "no model selected (choose one in the model picker)", {}
        a = mm.assess(mid)
        if a is None:   # start() already rejects these; defensive
            return "BLOCKED", "model not in the AIVD catalog", {}
        rec = mm.recommend([mm.assess(n) for n in mm.by_name])
        sel = ("matches the controller's recommendation: " + rec["reason"]) if rec["model_id"] == mid else \
            (f"operator choice (the controller recommends {rec['model_id']}: {rec['reason']})" if rec["model_id"]
             else "operator choice (no recommendation: " + rec["reason"] + ")")
        details = {"model_id": mid, "family": a["family"], "rc6_allowlisted": a["rc6_allowlisted"],
                   "part_b_note": a["part_b_note"], "selection": sel, "fit": a["fit"], "ram": a["ram"],
                   "install_before": a["install"]["status"], "install_after": a["install"]["status"],
                   "pins": a["pins"], "pull": None, "verify": None, "ollama_started": False,
                   "size_bytes": a["size_bytes"]}
        self._log(doc, "model", f"selected {mid} ({a['family']}, {a['params']} {a['quant']}); {sel}")
        self._log(doc, "model", f"RAM {a['fit']['verdict']}: {a['fit']['reason']}")
        self._log(doc, "model", f"install status: {a['install']['status']} ({a['install']['reason']})")
        if a["fit"]["verdict"] == "EXCEEDS":
            return "BLOCKED", f"{mid} does not fit: required ~{a['fit']['required_kb']:,} kB vs MemAvailable " \
                f"{a['fit']['available_kb']:,} kB (MemTotal {a['fit']['total_kb']:,} kB). Not downloaded, " \
                "Ollama not started.", details
        if a["fit"]["verdict"] == "NOT_VERIFIED":
            return "BLOCKED", "RAM could not be read (fail closed); not downloaded", details
        st = a["install"]["status"]
        if st == "differs_from_pin":
            return "FAIL", f"{mid}: {a['install']['reason']}; refusing to use or overwrite it", details
        if st == "not_verified":
            return "BLOCKED", "no model_store configured; install status cannot be verified", details
        if st in ("missing", "incomplete"):
            gb = a["size_bytes"] / 1e9
            size_txt = f"{a['size_bytes'] / 1e6:.1f} MB" if a["size_bytes"] < 1e7 else f"{gb:.1f} GB"
            if not opts.get("auto_pull"):
                return "BLOCKED", f"{mid} is not installed ({a['install']['reason']}); download (~{size_txt}) " \
                    "was not confirmed in the run dialog", details
            self._log(doc, "model", f"auto-download confirmed by the operator: ~{size_txt}")
            res = mm.puller.pull(mm.by_name[mid], "pipeline", on_line=lambda ln: self._log(doc, "model", ln),
                                 on_progress=lambda pr: self._step_progress(doc, "model", pr),
                                 timeout=self._remaining(deadline))
            details["pull"] = {k: res.get(k) for k in ("outcome", "reason", "duration_s", "bytes_total", "layers",
                                                       "serve")}
            details["ollama_started"] = bool((res.get("serve") or {}).get("started"))
            details["verify"] = res.get("verify")
            details["install_after"] = mm.assess(mid)["install"]["status"]
            if res.get("outcome") != "succeeded":
                status = "BLOCKED" if res.get("outcome") in ("blocked", "busy") else "FAIL"
                return status, f"download of {mid} {res.get('outcome')}: {res.get('reason')}", details
            return "PASS", f"{mid} downloaded in {res.get('duration_s')} s and verified ({res['verify']['reason']}); " \
                f"RAM {a['fit']['verdict']}", details
        self._log(doc, "model", "verifying installed copy: re-hashing every blob (cached after the first run)")
        v = MD_verify(mm, mid)
        details["verify"] = v
        if not v["ok"]:
            return "FAIL", f"{mid}: {v['reason']}", details
        note = "" if a["rc6_allowlisted"] else " NOTE: catalog extra, not in the RC6 allowlist, so Part B cannot use it."
        return "PASS", f"{mid} installed and verified ({v['reason']}); RAM {a['fit']['verdict']} " \
            f"(~{a['fit']['required_kb']:,} kB of {a['fit']['available_kb']:,} kB available).{note}", details

    def partb_checklist(self, opts, guard=None, model_step=None):
        """Every Part B gate with state, exact reasons and how to fix it. Pure evaluation; starts nothing."""
        guard = guard or self.ctl.guard()
        gates = self.ctl.run_gates(model_id=opts.get("model_id") or None, guard=guard)
        acts = guard.get("actions", {})
        reasons = sorted(set(acts.get("START_RUNTIME", [])) | set(acts.get("MODEL_CALL", [])))
        items = []

        def add(gid, label, state, rs, source):
            items.append({"id": gid, "label": label, "state": state, "reasons": rs,
                          "fix": "" if state == "PASS" else FIXES.get(gid, ""), "source": source})
        g_ok = guard.get("available")
        appr = [r for r in reasons if "RC6_APPROVALS" in r or "preregistration" in r]
        add("PREREG_APPROVAL", "Redacted preregistration approved (RC6_APPROVALS.json)",
            "NOT_VERIFIED" if not g_ok else ("FAIL" if appr else "PASS"),
            appr or ([] if g_ok else [guard.get("error", "guard unavailable")]), "aivd_rc6_guard")
        add("OSF_REGISTRATION", "OSF registration of the approved preregistration",
            "NOT_VERIFIED" if not g_ok else ("FAIL" if appr else "PASS"),
            (["not recorded: no APPROVED RC6_APPROVALS.json (the readiness report lists OSF registration as not done)"]
             if appr else []) if g_ok else [guard.get("error", "guard unavailable")],
            "readiness report; verifiable only via the approval record")
        for gid, label in (("G_AUTHOR", "Independent outcome-blind author + separate human reviewer"),
                           ("G_AUDIT", "Historical protected-path audit resolved"),
                           ("G_FROZEN", "Frozen analysis manifest intact"),
                           ("G_CORPUS", "Committed RC6 corpus")):
            rs = [r for r in reasons if r.startswith(gid + ":")]
            add(gid, label, "NOT_VERIFIED" if not g_ok else ("FAIL" if rs else "PASS"), rs, "aivd_rc6_guard")
        envr = [r for r in reasons if "environment authorization" in r]
        add("OPERATOR_ENV", "Operator authorization env (START_RUNTIME, MODEL_CALL)",
            "NOT_VERIFIED" if not g_ok else ("FAIL" if envr else "PASS"), envr, "aivd_rc6_guard")
        for g in gates:
            if g["id"].startswith("GUARD_"):
                continue
            gid = "MODEL_ATTEMPT" if g["id"] == "MODEL_ALLOWLIST" else g["id"]
            add(gid, g["label"], g["state"], g["reasons"], "controller")
        model, attempt = opts.get("model_id") or "", opts.get("attempt_id") or ""
        srv = _srv()
        ALLOWED_MODELS, ATTEMPT_RX, RUN_CONFIRM = srv.ALLOWED_MODELS, srv.ATTEMPT_RX, srv.RUN_CONFIRM
        if not any(i["id"] == "MODEL_ATTEMPT" for i in items):
            add("MODEL_ATTEMPT", "Preregistered model + valid attempt id",
                "PASS" if model in ALLOWED_MODELS and ATTEMPT_RX.fullmatch(attempt) else "FAIL",
                [] if model in ALLOWED_MODELS and ATTEMPT_RX.fullmatch(attempt) else
                ["no preregistered model / valid attempt id supplied"], "controller")
        elif not ATTEMPT_RX.fullmatch(attempt):
            for i in items:
                if i["id"] == "MODEL_ATTEMPT":
                    i.update(state="FAIL", reasons=i["reasons"] + ["invalid or missing attempt id"],
                             fix=FIXES["MODEL_ATTEMPT"])
        if model_step is not None:
            ms, mr, _ = model_step
            add("MODEL_READY", "Selected model installed, digest-verified and fits RAM", "PASS" if ms == "PASS" else
                "FAIL", [] if ms == "PASS" else [f"Model readiness step {ms}: {mr}"], "controller (model readiness)")
        phrase = opts.get("partb_confirm") or ""
        add("CONFIRM_PHRASE", "Exact confirmation phrase typed",
            "PASS" if phrase == RUN_CONFIRM else "FAIL",
            [] if phrase == RUN_CONFIRM else (["confirmation phrase not typed"] if not phrase
                                              else ["confirmation phrase does not match exactly"]), "operator")
        return items, gates

    def step_partb(self, doc, ctx, deadline):
        opts = ctx["opts"]
        items, gates = self.partb_checklist(opts, guard=ctx.get("guard"),
                                            model_step=ctx["results"].get("model", ("SKIPPED", "not run", {})))
        failed = [i for i in items if i["state"] != "PASS"]
        details = {"checklist": items, "ollama_started": False, "handoff": False}
        ctx["partb"] = details
        for i in failed:
            self._log(doc, "partb", f"{i['id']}: {i['state']} - " + "; ".join(i["reasons"]))
        # Server-side re-check: ALL controller gates (which include the guard's START_RUNTIME/MODEL_CALL verdicts and
        # the operator env) must PASS, and the phrase must match. Anything else is BLOCKED; nothing is started.
        if failed or not gates or any(g["state"] != "PASS" for g in gates):
            self.ctl.audit("partb_step", "blocked", [f"{i['id']}:{i['state']}" for i in failed])
            return "BLOCKED", "Part B not started (Ollama not started): " + "; ".join(
                f"{i['label']}: {('; '.join(i['reasons']) or i['state'])}" for i in failed), details
        self.ctl.audit("partb_step", "handoff", [opts["model_id"]])
        code, res = self.partb_handoff(opts["model_id"], opts["attempt_id"])
        details["handoff"] = code == 202
        details["handoff_response"] = {"code": code, "status": (res or {}).get("status")}
        if code == 202:
            return "PASS", "all gates passed and the phrase matched: handed off to scripts/rc6_partb_run.py " \
                           "(progress is tracked by the guarded runner, see Experiment Control)", details
        return "BLOCKED", f"guarded entry refused the handoff (HTTP {code})", details

    def _default_handoff(self, model, attempt):
        return self.ctl.op_run({"model_id": model, "attempt_id": attempt, "confirm": _srv().RUN_CONFIRM})

    def step_summary(self, doc, ctx, deadline):
        r = ctx["results"]

        def st(sid):
            return r.get(sid, ("SKIPPED", "", {}))[0]
        built_ok = st("rc6_tests") == "PASS" and st("cc_tests") == "PASS" and st("full_suite") in ("PASS", "SKIPPED")
        pre = ctx.get("preflight", {})
        rt_state = (pre.get("runtime") or {}).get("state", "NOT_VERIFIED")
        items = (ctx.get("partb") or {}).get("checklist", [])
        # Authorization = approvals + operator-supplied inputs (env, phrase, model/attempt choice); everything else is
        # a research/environment prerequisite.
        auth_ids = {"PREREG_APPROVAL", "OSF_REGISTRATION", "OPERATOR_ENV", "PARTB_ENV", "CONFIRM_PHRASE", "MODEL_ATTEMPT"}
        prereq_fail = [i["id"] for i in items if i["id"] not in auth_ids and i["state"] != "PASS"]
        auth_fail = [i["id"] for i in items if i["id"] in auth_ids and i["state"] != "PASS"]
        handed = bool((ctx.get("partb") or {}).get("handoff"))
        lifecycle = [
            {"id": "software_built", "label": "Software built", "value": "PASS" if built_ok else "FAIL"},
            {"id": "runtime_available", "label": "Runtime available",
             "value": {"PASS": "PASS", "FAIL": "FAIL"}.get(rt_state, "NOT VERIFIED")},
            {"id": "prerequisites_satisfied", "label": "Prerequisites",
             "value": "PASS" if items and not prereq_fail else "FAIL", "open": prereq_fail},
            {"id": "explicitly_authorized", "label": "Authorized", "value": "YES" if items and not auth_fail else "NO",
             "open": auth_fail},
            {"id": "running", "label": "Experiment", "value": "HANDED OFF (see runner status)" if handed else "NOT RUN"},
            {"id": "completed", "label": "Completed", "value": "NO"},
            {"id": "independently_validated", "label": "Independently validated", "value": "NOT VERIFIED"},
        ]
        headline = "; ".join(f"{x['label']}: {x['value']}" for x in lifecycle[:5])
        counts = {}
        for sid in ("rc6_tests", "full_suite"):
            c = r.get(sid, ("", "", {}))[2].get("counts")
            if c:
                counts[sid] = c
        statuses = [st(s) for s, _ in STEP_DEFS if s != "summary"]
        overall = "ERROR" if "ERROR" in statuses else ("FAIL" if "FAIL" in statuses else
                                                       ("BLOCKED" if "BLOCKED" in statuses else "PASS"))
        md = r.get("model", ("SKIPPED", "", {}))
        model_summary = {"status": md[0], "reason": md[1], **{k: md[2].get(k) for k in (
            "model_id", "rc6_allowlisted", "selection", "install_before", "install_after") if md[2]}}
        ctx["verdict"] = {"overall": overall, "headline": headline, "lifecycle": lifecycle, "model": model_summary,
                          "experiment_ran": False, "note": "The experiment did not run in this pipeline; a "
                          "handoff only starts the guarded runner, whose own result is reported separately."
                          if handed else "The experiment did not run. Nothing here means 'experiment ready'."}
        return overall, headline, {"lifecycle": lifecycle}


def MD_verify(mm, name):
    from controller import models as MD
    return MD.verify_deep(mm.store, name, mm.by_name[name])


def _srv():
    """The controller server module (imported lazily: server.py imports this module)."""
    return sys.modules.get("controller.server") or __import__("controller.server", fromlist=["redact"])


def _which(name):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        p = Path(d) / name
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return None


def _last_json(lines):
    for ln in reversed(lines):
        ln = ln.strip()
        if ln.startswith("{"):
            try:
                return json.loads(ln)
            except ValueError:
                continue
    return None
