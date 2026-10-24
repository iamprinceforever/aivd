"""AIVD Command Center local controller (Python stdlib only).

Security model (see docs/COMMAND_CENTER_SECURITY.md):
  * binds 127.0.0.1 only; Host header must be 127.0.0.1:<port> or localhost:<port> (DNS-rebinding defence);
  * same-origin by default: the controller serves the built UI under /aivd/ and the API under /api/;
    extra origins only by exact match from the operator's config (no wildcard CORS, no credentials);
  * per-launch random secret (memory only) + one-time pairing code printed to the terminal and written to a
    0600 file in a state directory outside git; pairing yields an in-memory bearer session + CSRF token;
  * every POST needs: allowed Origin, application/json, Content-Length <= MAX_BODY, bearer session and the
    X-AIVD-CSRF header; bodies are validated against strict per-endpoint schemas (unknown keys rejected);
  * only allowlisted operations exist; the RC6 run/reveal operations call ONLY the repository's existing guarded
    entry scripts, after server-side checks of every gate; anything unverifiable FAILS CLOSED;
  * the controller never sets any authorization environment variable; the ONLY time it starts Ollama is an
    operator-requested model download (POST /api/ops/pull_model, or the pipeline's Model readiness step with the
    download confirmed): the configured binary's serve subcommand, bound to 127.0.0.1:<pull_port> with OLLAMA_NOPRUNE=1, stopped right after
    the pull; no model is loaded and no model call is made (see controller/models.py);
  * the audit log is redacted (no tokens, no local paths) and hash-chained.
"""

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from controller import models as MD
from controller import pipeline as PL
from controller import procs as PR
from controller import demo_ops as DEMO

VERSION = "0.3.0"
MAX_BODY = 4096
SOCKET_TIMEOUT = 10
STATUS_TIMEOUT = 30
MEMORY_THRESHOLD_KB = 7_600_000          # RC6 memory gate (unchanged from the research design)
ALLOWED_MODELS = ("qwen3:1.7b", "llama3.2:3b", "qwen3:8b")
ATTEMPT_RX = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
RUN_CONFIRM = "I AM THE AUTHORIZED OPERATOR AND AUTHORIZE THIS RC6 RUN"
REVEAL_CONFIRM = "I AM THE AUTHORIZED OPERATOR AND AUTHORIZE REVEAL AND SCORING"
GUARD_MODULE = "aivd_rc6_guard"
RUN_ENTRY = "scripts/rc6_partb_run.py"
REVEAL_ENTRY = "scripts/rc6_analyze.py"
PARTB_ENV = "AIVD_RC6_PARTB_AUTHORIZED"
PAIR_TTL = 600
PAIR_MAX_FAILS = 5
SESSION_IDLE = 1800
SESSION_MAX = 8 * 3600
LOCAL_PATH_RX = re.compile("(?:" + "|".join(("/" + "workspace", "/var" + "/tmp", r"/home/[^/\s]+", "/root", "/tmp"))
                           + r")(?:/[^\s\"'`,;)\]]*)?")
TOKEN_RX = re.compile("github" + r"_pat_[A-Za-z0-9_]+|\bgh[pousr]_[A-Za-z0-9]+|https?://[^/\s@]+@")
CONFIG_KEYS = {"research_worktree": str, "worktrees": dict, "runtime_files": list, "port": int,
               "extra_origins": list, "state_dir": str, "ui_dir": str, "max_run_seconds": int,
               "expected_research_branch": str,
               # one-click pipeline (all optional; all operator-local, never client-supplied)
               "test_python": str, "test_worktree": str, "cc_dir": str, "node": str, "seal_scanner": str,
               "pipeline_step_timeout_s": int, "pipeline_total_timeout_s": int,
               # model picker / downloads (all optional, operator-local)
               "model_store": str, "ollama_binary": str, "pull_enabled": bool, "pull_port": int,
               "pull_timeout_s": int, "model_catalog": str,
               # child stop escalation: SIGINT, wait, SIGTERM, wait, SIGKILL (seconds per wait; default 5)
               "stop_grace_s": int,
               # interview demo (optional; loopback one-click only)
               "demo_worktree": str, "demo_ollama_host": str}
APPROVAL_REASON_RX = re.compile(r"RC6_APPROVALS|environment authorization|approved preregistration|not listed")


class ConfigError(ValueError):
    pass


def redact(text) -> str:
    s = str(text)
    s = TOKEN_RX.sub("<redacted-token>", s)
    return LOCAL_PATH_RX.sub("<local-path>", s)


def validate_config(raw) -> dict:
    """Strict config validation; raises ConfigError (the controller refuses to start)."""
    if not isinstance(raw, dict):
        raise ConfigError("config must be a JSON object")
    unknown = set(raw) - set(CONFIG_KEYS)
    if unknown:
        raise ConfigError(f"unknown config keys: {sorted(unknown)}")
    for k, t in CONFIG_KEYS.items():
        if k in raw and not isinstance(raw[k], t) or (t is int and isinstance(raw.get(k), bool)):
            raise ConfigError(f"config key {k} must be {t.__name__}")
    if "research_worktree" not in raw:
        raise ConfigError("research_worktree is required")
    cfg = {"port": 8765, "worktrees": {}, "runtime_files": [], "extra_origins": [], "max_run_seconds": 12 * 3600,
           "ui_dir": None, "expected_research_branch": None,
           "state_dir": str(Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
                            / "aivd-command-center"), **raw}
    if not 1024 <= cfg["port"] <= 65535:
        raise ConfigError("port must be 1024-65535")
    if not 60 <= cfg["max_run_seconds"] <= 48 * 3600:
        raise ConfigError("max_run_seconds out of range")
    rw = Path(cfg["research_worktree"])
    if not rw.is_absolute() or not rw.is_dir():
        raise ConfigError("research_worktree must be an existing absolute directory")
    for name, p in cfg["worktrees"].items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", name) or not isinstance(p, str) or not Path(p).is_absolute():
            raise ConfigError("worktrees must map short names to absolute paths")
    for f in cfg["runtime_files"]:
        if (not isinstance(f, dict) or set(f) != {"name", "path", "sha256"} or not Path(str(f["path"])).is_absolute()
                or not re.fullmatch(r"[0-9a-f]{64}", str(f["sha256"]))
                or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,60}", str(f["name"]))):
            raise ConfigError("runtime_files entries need name, absolute path, sha256 (64 hex)")
    for o in cfg["extra_origins"]:
        if not isinstance(o, str) or not re.fullmatch(r"https?://[A-Za-z0-9.-]+(:\d{1,5})?", o) or "*" in o:
            raise ConfigError("extra_origins must be exact scheme://host[:port] origins (no wildcard, no path)")
    for k in ("test_python", "node", "seal_scanner"):
        if k in cfg and not (Path(cfg[k]).is_absolute() and Path(cfg[k]).is_file()):
            raise ConfigError(f"{k} must be an existing absolute file path")
    for k in ("test_worktree", "cc_dir"):
        if k in cfg and not (Path(cfg[k]).is_absolute() and Path(cfg[k]).is_dir()):
            raise ConfigError(f"{k} must be an existing absolute directory")
    if not 30 <= cfg.get("pipeline_step_timeout_s", 900) <= 7200:
        raise ConfigError("pipeline_step_timeout_s out of range (30-7200)")
    if not 60 <= cfg.get("pipeline_total_timeout_s", 3600) <= 14400:
        raise ConfigError("pipeline_total_timeout_s out of range (60-14400)")
    if not 1 <= cfg.get("stop_grace_s", PR.DEFAULT_GRACE_S) <= 120:
        raise ConfigError("stop_grace_s out of range (1-120)")
    if "model_store" in cfg and not (Path(cfg["model_store"]).is_absolute() and Path(cfg["model_store"]).is_dir()):
        raise ConfigError("model_store must be an existing absolute directory")
    for k in ("ollama_binary", "model_catalog"):
        if k in cfg and not (Path(cfg[k]).is_absolute() and Path(cfg[k]).is_file()):
            raise ConfigError(f"{k} must be an existing absolute file path")
    if not 1024 <= cfg.get("pull_port", 11535) <= 65535 or cfg.get("pull_port") == MD.DEFAULT_RUNTIME_PORT:
        raise ConfigError("pull_port must be 1024-65535 and not the default research runtime port")
    if not 60 <= cfg.get("pull_timeout_s", 3600) <= 4 * 3600:
        raise ConfigError("pull_timeout_s out of range (60-14400)")
    if cfg.get("pull_enabled") and not ("model_store" in cfg and "ollama_binary" in cfg):
        raise ConfigError("pull_enabled needs model_store and ollama_binary")
    if "demo_worktree" in cfg:
        dw = Path(cfg["demo_worktree"])
        if not (dw.is_absolute() and dw.is_dir()):
            raise ConfigError("demo_worktree must be an existing absolute directory")
        if not (dw / "demo" / "aivd_interview" / "run_demo.py").is_file():
            raise ConfigError("demo_worktree must contain demo/aivd_interview/run_demo.py")
    if "demo_ollama_host" in cfg:
        h = cfg["demo_ollama_host"]
        if not isinstance(h, str) or not re.fullmatch(r"http://(127\.0\.0\.1|localhost):\d{2,5}", h):
            raise ConfigError("demo_ollama_host must be http://127.0.0.1:<port> or http://localhost:<port>")
    if "model_store" in cfg and (Path(cfg["model_store"]).resolve() == rw.resolve()
                                 or rw.resolve() in Path(cfg["model_store"]).resolve().parents):
        raise ConfigError("model_store must be outside the research worktree")
    try:
        MD.load_catalog(cfg.get("model_catalog"), ALLOWED_MODELS)
    except MD.CatalogError as e:
        raise ConfigError(str(e)) from None
    sd = Path(cfg["state_dir"])
    if not sd.is_absolute():
        raise ConfigError("state_dir must be absolute")
    if sd.resolve() == rw.resolve() or rw.resolve() in sd.resolve().parents:
        raise ConfigError("state_dir must be outside the research worktree (outside git)")
    for k in ("test_worktree", "cc_dir"):
        if k in cfg and (sd.resolve() == Path(cfg[k]).resolve() or Path(cfg[k]).resolve() in sd.resolve().parents):
            raise ConfigError("state_dir must be outside git (it is inside a configured worktree)")
    return cfg


def read_meminfo(path="/proc/meminfo"):
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def ollama_process_running(proc="/proc"):
    """Read-only scan of /proc/*/comm. Returns None when it cannot be determined."""
    try:
        for d in Path(proc).iterdir():
            if d.name.isdigit():
                try:
                    if (d / "comm").read_text().strip().startswith("ollama"):
                        return True
                except OSError:
                    continue
        return False
    except OSError:
        return None


class Controller:
    """All decisions live here (HTTP-free, unit-testable). env/meminfo/proc readers are injectable for tests."""

    def __init__(self, cfg, env=None, meminfo=read_meminfo, proc_check=ollama_process_running, python=None,
                 popen=subprocess.Popen):
        self.cfg = cfg
        self.env = os.environ if env is None else env      # inherited from the operator's shell; never modified
        self.meminfo = meminfo
        self.proc_check = proc_check
        self.python = python or sys.executable
        self.root = Path(cfg["research_worktree"])
        self.secret = secrets.token_bytes(32)
        self.launch_id = secrets.token_hex(4)
        self.pair_code = "-".join(secrets.token_hex(2).upper() for _ in range(3))
        self.pair_issued = time.time()
        self.pair_fails = 0
        self.pair_used = False
        self.sessions = {}
        self.lock = threading.Lock()
        self.run = {"state": "idle"}
        self.proc = None
        self._hash_cache = {}
        self._last_audit = "0" * 64
        self.audit_lock = threading.Lock()
        sd = Path(cfg["state_dir"])
        sd.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.audit_path = sd / "audit.jsonl"
        self.pair_file = sd / f"pairing-{self.launch_id}.json"
        fd = os.open(self.pair_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            json.dump({"launch_id": self.launch_id, "pairing_code": self.pair_code, "port": cfg["port"],
                       "expires_unix": int(self.pair_issued + PAIR_TTL)}, fh)
        self.models = MD.ModelManager(cfg, self.env, lambda: self.proc_check(), redact, self.audit, ALLOWED_MODELS,
                                      popen=popen)
        self.pipeline = PL.Pipeline(self)
        self.demo = DEMO.DemoRunner(self)

    # ---------- sessions ----------
    def pair(self, code: str):
        with self.lock:
            if self.pair_used:
                return None, "pairing code already used (restart the controller to pair again)"
            if self.pair_fails >= PAIR_MAX_FAILS:
                return None, "too many failed pairing attempts (restart the controller)"
            if time.time() - self.pair_issued > PAIR_TTL:
                return None, "pairing code expired (restart the controller)"
            if not hmac.compare_digest(code.strip().upper(), self.pair_code):
                self.pair_fails += 1
                return None, "wrong pairing code"
            self.pair_used = True
            try:
                self.pair_file.unlink()
            except OSError:
                pass
            sid = secrets.token_urlsafe(32)
            token = sid + "." + hmac.new(self.secret, sid.encode(), hashlib.sha256).hexdigest()[:32]
            csrf = secrets.token_urlsafe(24)
            now = time.time()
            self.sessions[hashlib.sha256(token.encode()).hexdigest()] = {"csrf": csrf, "created": now, "seen": now}
            return {"session": token, "csrf": csrf, "idle_timeout_s": SESSION_IDLE}, None

    def session_for(self, token):
        if not token or "." not in token:
            return None
        sid, mac = token.rsplit(".", 1)
        if not hmac.compare_digest(mac, hmac.new(self.secret, sid.encode(), hashlib.sha256).hexdigest()[:32]):
            return None
        key = hashlib.sha256(token.encode()).hexdigest()
        with self.lock:
            s = self.sessions.get(key)
            now = time.time()
            if not s or now - s["seen"] > SESSION_IDLE or now - s["created"] > SESSION_MAX:
                self.sessions.pop(key, None)
                return None
            s["seen"] = now
            return s

    # ---------- audit ----------
    def audit(self, op, outcome, reasons=()):
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "launch": self.launch_id, "op": op, "outcome": outcome,
                 "reasons": [redact(r)[:300] for r in list(reasons)[:20]], "prev": self._last_audit}
        with self.audit_lock:
            entry["prev"] = self._last_audit
            line = json.dumps(entry, sort_keys=True)
            self._last_audit = hashlib.sha256(line.encode()).hexdigest()
            fd = os.open(self.audit_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "a") as fh:
                fh.write(line + "\n")

    def audit_tail(self, n=50):
        try:
            lines = self.audit_path.read_text().splitlines()[-n:]
        except OSError:
            return []
        out = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out

    # ---------- read-only probes ----------
    def memory(self):
        kb = self.meminfo()
        if kb is None:
            return {"state": "NOT_VERIFIED", "mem_available_kb": None, "threshold_kb": MEMORY_THRESHOLD_KB,
                    "reason": "MemAvailable unreadable"}
        ok = kb >= MEMORY_THRESHOLD_KB
        return {"state": "PASS" if ok else "FAIL", "mem_available_kb": kb, "threshold_kb": MEMORY_THRESHOLD_KB,
                "reason": f"MemAvailable {kb} kB {'>=' if ok else '<'} {MEMORY_THRESHOLD_KB} kB"}

    def _sha_file(self, p: Path, deadline):
        st = p.stat()
        key = (str(p), st.st_size, st.st_mtime_ns)
        if key in self._hash_cache:
            return self._hash_cache[key]
        h = hashlib.sha256()
        with p.open("rb") as fh:
            while chunk := fh.read(1 << 20):
                h.update(chunk)
                if time.time() > deadline:
                    raise TimeoutError
        self._hash_cache[key] = h.hexdigest()
        return self._hash_cache[key]

    def runtime(self, timeout=STATUS_TIMEOUT):
        files, deadline = [], time.time() + timeout
        for f in self.cfg["runtime_files"]:
            p = Path(f["path"])
            try:
                got = self._sha_file(p, deadline)
                st = "MATCH" if got == f["sha256"] else "MISMATCH"
            except FileNotFoundError:
                st = "MISSING"
            except TimeoutError:
                st = "NOT_VERIFIED"
            except OSError:
                st = "NOT_VERIFIED"
            files.append({"name": f["name"], "expected_sha256_prefix": f["sha256"][:12], "state": st})
        running = self.proc_check()
        if not files:
            state, reason = "NOT_VERIFIED", "no runtime files configured"
        elif all(x["state"] == "MATCH" for x in files):
            state, reason = "PASS", "all configured runtime files match their pinned sha256 (runtime NOT started)"
        else:
            state, reason = "FAIL", "runtime file missing, mismatched or unverifiable"
        return {"state": state, "reason": reason, "files": files, "ollama_process_running": running,
                "started_by_controller": False}

    def worktrees(self):
        out = []
        for name, p in sorted(self.cfg["worktrees"].items()):
            try:
                def g(*a):
                    return subprocess.run(["git", "--no-optional-locks", "-C", p, *a], capture_output=True, timeout=STATUS_TIMEOUT,
                                          check=True).stdout
                por = g("status", "--porcelain=v1").decode("utf-8", "replace").splitlines()
                out.append({"name": name, "branch": g("branch", "--show-current").decode().strip(),
                            "head": g("rev-parse", "--short=12", "HEAD").decode().strip(),
                            "modified": sum(1 for x in por if not x.startswith("??")),
                            "untracked": sum(1 for x in por if x.startswith("??")),
                            "diff_sha256": hashlib.sha256(g("diff")).hexdigest()})
            except (subprocess.SubprocessError, OSError):
                out.append({"name": name, "error": "git status unavailable"})
        return out

    def guard(self):
        if not (self.root / GUARD_MODULE / "__init__.py").exists():
            return {"available": False, "error": "guard module not found in research worktree", "actions": {}}
        try:
            r = subprocess.run([self.python, "-m", GUARD_MODULE], cwd=self.root, capture_output=True, text=True,
                               timeout=STATUS_TIMEOUT, env={**self.env, "PYTHONDONTWRITEBYTECODE": "1"})
            data = json.loads(r.stdout)
            if not isinstance(data, dict) or not all(isinstance(v, list) for v in data.values()):
                raise ValueError
            return {"available": True, "actions": {k: [redact(x) for x in v] for k, v in data.items()}}
        except (subprocess.SubprocessError, OSError, ValueError):
            return {"available": False, "error": "guard status unreadable (fail closed)", "actions": {}}

    # ---------- gates ----------
    def run_gates(self, model_id=None, guard=None, mem=None, rt=None):
        guard = guard or self.guard()
        mem = mem or self.memory()
        rt = rt or self.runtime()
        acts = guard.get("actions", {})
        gates = []

        def add(gid, label, ok, reasons):
            gates.append({"id": gid, "label": label,
                          "state": "PASS" if ok is True else ("FAIL" if ok is False else "NOT_VERIFIED"),
                          "reasons": [] if ok is True else list(reasons)})
        add("ENTRY", "Guarded entry script present", (self.root / RUN_ENTRY).exists(),
            ["entry script not found; run operation unavailable"])
        for act in ("START_RUNTIME", "MODEL_CALL"):
            if not guard.get("available"):
                add(f"GUARD_{act}", f"aivd_rc6_guard allows {act}", None, [guard.get("error", "guard unavailable")])
            elif act not in acts:
                add(f"GUARD_{act}", f"aivd_rc6_guard allows {act}", None, [f"guard did not report {act}"])
            else:
                add(f"GUARD_{act}", f"aivd_rc6_guard allows {act}", not acts[act], acts[act])
        add("PARTB_ENV", f"{PARTB_ENV} supplied by the operator's shell", bool(self.env.get(PARTB_ENV)),
            [f"{PARTB_ENV} not present in the controller's inherited environment"])
        add("MEMORY", f"MemAvailable >= {MEMORY_THRESHOLD_KB} kB", {"PASS": True, "FAIL": False}.get(mem["state"]),
            [mem["reason"]])
        add("RUNTIME_FILES", "Runtime files match pinned hashes", {"PASS": True, "FAIL": False}.get(rt["state"]),
            [rt["reason"]])
        running = rt.get("ollama_process_running")
        add("NO_FOREIGN_RUNTIME", "No Ollama process already running", None if running is None else not running,
            ["an Ollama process is already running" if running else "process table unreadable"])
        with self.lock:
            idle = self.run.get("state") != "running"
        add("NO_ACTIVE_RUN", "No run already in progress", idle, ["a run is already in progress"])
        if model_id is not None:
            add("MODEL_ALLOWLIST", "Model is preregistered", model_id in ALLOWED_MODELS,
                ["model is not in the allowlist"])
        exp = self.cfg.get("expected_research_branch")
        if exp:
            try:
                br = subprocess.run(["git", "--no-optional-locks", "-C", str(self.root), "branch", "--show-current"], capture_output=True,
                                    text=True, timeout=STATUS_TIMEOUT).stdout.strip()
                add("RESEARCH_BRANCH", "Research worktree on expected branch", br == exp, ["unexpected branch"])
            except (subprocess.SubprocessError, OSError):
                add("RESEARCH_BRANCH", "Research worktree on expected branch", None, ["git unavailable"])
        return gates

    def reveal_gates(self, guard=None):
        guard = guard or self.guard()
        acts = guard.get("actions", {})
        gates = []
        ok = (self.root / REVEAL_ENTRY).exists()
        gates.append({"id": "ENTRY", "label": "Guarded analysis entry present", "state": "PASS" if ok else "FAIL",
                      "reasons": [] if ok else ["analysis entry not found; reveal unavailable"]})
        for act in ("REVEAL", "SCORE"):
            if not guard.get("available") or act not in acts:
                gates.append({"id": f"GUARD_{act}", "label": f"aivd_rc6_guard allows {act}", "state": "NOT_VERIFIED",
                              "reasons": [guard.get("error", f"guard did not report {act}")]})
            else:
                gates.append({"id": f"GUARD_{act}", "label": f"aivd_rc6_guard allows {act}",
                              "state": "FAIL" if acts[act] else "PASS", "reasons": acts[act]})
        with self.lock:
            st = self.run.get("state")
        gates.append({"id": "NO_ACTIVE_RUN", "label": "No run in progress", "state": "FAIL" if st == "running" else
                      "PASS", "reasons": ["a run is in progress"] if st == "running" else []})
        return gates

    def lifecycle(self, guard, mem, rt):
        acts = guard.get("actions", {})

        def st(ok, reasons):
            return {"state": "PASS" if ok is True else ("FAIL" if ok is False else "NOT_VERIFIED"),
                    "reasons": [] if ok is True else reasons}
        built = (self.root / GUARD_MODULE / "__init__.py").exists() and (self.root / RUN_ENTRY).exists()
        pre_reasons, auth_reasons = [], []
        for a in ("START_RUNTIME", "MODEL_CALL"):
            for r in acts.get(a, []):
                (auth_reasons if APPROVAL_REASON_RX.search(r) else pre_reasons).append(f"{a}: {r}")
        if mem["state"] != "PASS":
            pre_reasons.append(mem["reason"])
        if not self.env.get(PARTB_ENV):
            auth_reasons.append(f"{PARTB_ENV} absent")
        with self.lock:
            run = dict(self.run)
        g_ok = guard.get("available")
        return {
            "software_built": st(built, ["guard module or entry script missing"]),
            "runtime_available": st({"PASS": True, "FAIL": False}.get(rt["state"]), [rt["reason"]]),
            "prerequisites_satisfied": st(None if not g_ok else not pre_reasons,
                                          pre_reasons or [guard.get("error", "guard unavailable")]),
            "explicitly_authorized": st(None if not g_ok else not auth_reasons,
                                        auth_reasons or [guard.get("error", "guard unavailable")]),
            "running": st(run.get("state") == "running", ["no run in progress"]),
            "completed": st(run.get("state") == "completed", ["no completed run in this controller session"]),
            "independently_validated": st(None, ["requires an independent human reviewer; the controller never "
                                                 "asserts this"]),
        }

    def status(self):
        guard, mem, rt = self.guard(), self.memory(), self.runtime()
        rg = self.run_gates(guard=guard, mem=mem, rt=rt)
        vg = self.reveal_gates(guard=guard)
        with self.lock:
            run = dict(self.run)
        if run.get("state") == "running":
            run["elapsed_s"] = int(time.time() - run["started"])
            run["progress"] = "runner reports no incremental progress; elapsed time only"
        return {"controller": {"version": VERSION, "launch_id": self.launch_id},
                "memory": mem, "runtime": rt, "worktrees": self.worktrees(), "guard": guard,
                "lifecycle": self.lifecycle(guard, mem, rt),
                "ops": {"rc6_run": {"available": all(g["state"] == "PASS" for g in rg), "gates": rg},
                        "rc6_reveal": {"available": all(g["state"] == "PASS" for g in vg), "gates": vg},
                        "cancel": {"available": False, "reason": "the RC6 entry script documents no cancel "
                                   "operation; the controller will not signal it"},
                        "run_demo": {"available": bool(self.cfg.get("demo_worktree")),
                                     "label": DEMO.LABEL}},
                "run": run, "allowed_models": list(ALLOWED_MODELS),
                "pipeline": self.pipeline_status(),
                "demo": self.demo.status()}

    def pipeline_status(self):
        pl = self.pipeline
        with pl.lock:
            cur = pl.current
            running = cur["id"] if cur and cur.get("state") == "running" else None
        return {"available": True, "running_run_id": running, "run_confirm_phrase_required_for_partb": True,
                "steps": [{"id": s, "label": lbl} for s, lbl in PL.STEP_DEFS]}

    # ---------- guarded operations ----------
    def _spawn(self, op, argv):
        p = subprocess.Popen([self.python, *argv], cwd=self.root, env=dict(self.env), stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, **PR.spawn_kwargs())
        with self.lock:
            self.proc = p
            self.run = {"state": "running", "op": op, "started": time.time()}
        threading.Thread(target=self._wait, args=(op, p), daemon=True).start()

    def _wait(self, op, p):
        stopped_by = None
        try:
            out, _ = p.communicate(timeout=self.cfg["max_run_seconds"])
            timed_out = False
        except subprocess.TimeoutExpired:
            # SIGINT first (lets the entry script's finally stop its own children), then SIGTERM, then SIGKILL.
            stopped_by = PR.stop(p, self.cfg.get("stop_grace_s", PR.DEFAULT_GRACE_S))
            try:
                out, _ = p.communicate(timeout=5)
            except (subprocess.TimeoutExpired, ValueError, OSError):
                out = b""
            timed_out = True
        summary = {}
        try:
            doc = json.loads(out.decode("utf-8", "replace")[-65536:])
            summary = {k: doc.get(k) for k in ("status", "charged_calls", "failure") if k in doc}
        except ValueError:
            pass
        rc = p.returncode
        state = "timeout" if timed_out else ("refused" if rc == 3 else ("completed" if rc == 0 else "failed"))
        with self.lock:
            self.run = {"state": state, "op": op, "exit_code": rc, "finished": time.time(),
                        "summary": json.loads(redact(json.dumps(summary)))}
            if stopped_by:
                self.run["stopped_by"] = stopped_by
            self.proc = None
        self.audit(op, state, [f"exit {rc}"] + ([f"stopped by {stopped_by}"] if stopped_by else []))

    def op_run(self, body):
        model, attempt = body["model_id"], body["attempt_id"]
        if body["confirm"] != RUN_CONFIRM:
            return 400, {"error": "confirmation phrase mismatch"}
        if model not in ALLOWED_MODELS or not ATTEMPT_RX.fullmatch(attempt):
            self.audit("rc6_run", "rejected", ["invalid model or attempt id"])
            return 400, {"error": "model not in allowlist or invalid attempt id"}
        gates = self.run_gates(model_id=model)
        failed = [g for g in gates if g["state"] != "PASS"]
        if failed:
            self.audit("rc6_run", "refused", [f"{g['id']}:{g['state']}" for g in failed])
            return 403, {"status": "REFUSED", "gates": gates}
        self.audit("rc6_run", "started", [model])
        self._spawn("rc6_run", [RUN_ENTRY, model, attempt])
        return 202, {"status": "STARTED", "gates": gates}

    def op_pull(self, body):
        """Operator-requested download of ONE catalog model. Never authorizes anything."""
        name = body["model_id"]
        model = self.models.by_name.get(name)
        if model is None:
            self.audit("pull_model", "rejected", ["model not in catalog"])
            return 400, {"error": "model not in the AIVD catalog (arbitrary names are rejected)"}
        with self.lock:
            if self.run.get("state") == "running":
                return 409, {"error": "an RC6 run is in progress"}
        with self.pipeline.lock:
            if self.pipeline.current is not None and self.pipeline.current.get("state") == "running":
                return 409, {"error": "a pipeline is running; it downloads the selected model itself if needed"}
        if self.models.puller.busy():
            return 409, {"error": "another download is in progress"}
        a = self.models.assess(name)
        if a["install"]["status"] in MD.INSTALLED_OK:
            return 200, {"status": "ALREADY_INSTALLED", "install": a["install"]["status"]}
        pre = self.models.pull_preconditions(model)
        if pre:
            self.audit("pull_model", "refused", [name] + pre)
            return 403, {"status": "BLOCKED", "reasons": pre}
        self.audit("pull_model", "started", [name])
        threading.Thread(target=self.models.puller.pull, args=(model, "operator"), daemon=True).start()
        return 202, {"status": "STARTED", "model_id": name}

    def op_reveal(self, body):
        if body["confirm"] != REVEAL_CONFIRM:
            return 400, {"error": "confirmation phrase mismatch"}
        gates = self.reveal_gates()
        failed = [g for g in gates if g["state"] != "PASS"]
        if failed:
            self.audit("rc6_reveal", "refused", [f"{g['id']}:{g['state']}" for g in failed])
            return 403, {"status": "REFUSED", "gates": gates}
        self.audit("rc6_reveal", "started")
        self._spawn("rc6_reveal", [REVEAL_ENTRY])
        return 202, {"status": "STARTED", "gates": gates}


SCHEMAS = {
    "/api/pair": {"code": (str, 4, 32)},
    "/api/ops/rc6_run": {"model_id": (str, 1, 40), "attempt_id": (str, 1, 32), "confirm": (str, 1, 120)},
    "/api/ops/rc6_reveal": {"confirm": (str, 1, 120)},
    "/api/ops/cancel": {},
    # The client may choose ONLY these fields; the step list, commands, paths and args are fixed server-side.
    "/api/ops/run_pipeline": {"full_suite": (bool, None, None), "partb_confirm": (str, 0, 120),
                              "model_id": (str, 0, 40), "attempt_id": (str, 0, 32), "auto_pull": (bool, None, None)},
    "/api/ops/pull_model": {"model_id": (str, 1, 40)},
    "/api/ops/cancel_pull": {},
    "/api/ops/run_demo": {"confirm": (str, 1, 120)},
}


def validate_body(path, body):
    schema = SCHEMAS[path]
    if not isinstance(body, dict):
        return "body must be a JSON object"
    if set(body) != set(schema):
        return f"body keys must be exactly {sorted(schema)}"
    for k, (t, lo, hi) in schema.items():
        v = body[k]
        if t is bool:
            if not isinstance(v, bool):
                return f"field {k} invalid"
        elif not isinstance(v, t) or isinstance(v, bool) or not lo <= len(v) <= hi:
            return f"field {k} invalid"
    return None


MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
        ".md": "text/markdown; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon",
        ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8"}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'none'")


def make_handler(ctl: Controller):
    port = ctl.cfg["port"]
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}", *ctl.cfg["extra_origins"]}
    extra = set(ctl.cfg["extra_origins"])

    class H(BaseHTTPRequestHandler):
        server_version = "aivd-cc"
        sys_version = ""
        timeout = SOCKET_TIMEOUT

        def log_message(self, *a):  # no request logging to stderr (would include paths/tokens)
            pass

        def _send(self, code, obj=None, raw=None, ctype="application/json"):
            body = raw if raw is not None else json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("Cache-Control", "no-store")
            o = self.headers.get("Origin")
            if o and o in extra:
                self.send_header("Access-Control-Allow-Origin", o)
                self.send_header("Vary", "Origin")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _host_ok(self):
            return self.headers.get("Host") in hosts

        def _origin_ok(self, required):
            o = self.headers.get("Origin")
            if o is None:
                return not required and self.headers.get("Sec-Fetch-Site") not in ("cross-site",)
            return o in origins

        def _session(self):
            a = self.headers.get("Authorization", "")
            return ctl.session_for(a[7:]) if a.startswith("Bearer ") else None

        def do_OPTIONS(self):
            o = self.headers.get("Origin")
            if not self._host_ok() or o not in extra:
                return self._send(403, {"error": "origin not allowed"})
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", o)
            self.send_header("Access-Control-Allow-Methods", "GET, POST")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-AIVD-CSRF")
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Vary", "Origin")
            if self.headers.get("Access-Control-Request-Private-Network") == "true":
                self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):
            if not self._host_ok():
                return self._send(421, {"error": "host not allowed"})
            path = self.path.split("?", 1)[0]
            if path.startswith("/api/"):
                if not self._origin_ok(required=False):
                    return self._send(403, {"error": "origin not allowed"})
                if path == "/api/health":
                    return self._send(200, {"service": "aivd-command-center-controller", "version": VERSION,
                                            "pairing_required": True})
                run_m = re.fullmatch(r"/api/runs/([A-Za-z0-9-]{1,40})", path)
                if path not in ("/api/status", "/api/audit", "/api/runs", "/api/models", "/api/demo/latest") and not run_m:
                    return self._send(404, {"error": "unknown operation"})
                if not self._session():
                    return self._send(401, {"error": "not paired"})
                if path == "/api/status":
                    return self._send(200, ctl.status())
                if path == "/api/runs":
                    return self._send(200, {"runs": ctl.pipeline.history()})
                if path == "/api/models":   # read-only: never starts Ollama, no network
                    return self._send(200, ctl.models.listing())
                if path == "/api/demo/latest":
                    doc = ctl.demo.get_latest()
                    return self._send(200, doc) if doc else self._send(404, {"error": "no demo report yet", "label": DEMO.LABEL})
                if run_m:
                    q = self.path.split("?", 1)[1] if "?" in self.path else ""
                    since = 0
                    m = re.fullmatch(r"since=(\d{1,6})", q)
                    if q and not m:
                        return self._send(400, {"error": "only ?since=<n> is accepted"})
                    if m:
                        since = int(m.group(1))
                    doc = ctl.pipeline.get(run_m.group(1), since)
                    return self._send(200, doc) if doc else self._send(404, {"error": "unknown run id"})
                return self._send(200, {"entries": ctl.audit_tail()})
            return self._static(path)

        def _static(self, path):
            ui = ctl.cfg.get("ui_dir")
            if not ui:
                return self._send(404, {"error": "UI not configured"})
            if path in ("/", "/aivd"):
                self.send_response(302)
                self.send_header("Location", "/aivd/")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if not path.startswith("/aivd/"):
                return self._send(404, {"error": "not found"})
            rel = path[len("/aivd/"):] or "index.html"
            base = Path(ui).resolve()
            target = (base / rel).resolve()
            try:
                target.relative_to(base)
            except ValueError:
                return self._send(404, {"error": "not found"})
            if not target.is_file() or target.suffix not in MIME:
                return self._send(404, {"error": "not found"})
            return self._send(200, raw=target.read_bytes(), ctype=MIME[target.suffix])

        def do_POST(self):
            if not self._host_ok():
                return self._send(421, {"error": "host not allowed"})
            path = self.path.split("?", 1)[0]
            if not self._origin_ok(required=True):
                ctl.audit(path, "rejected", ["origin"])
                return self._send(403, {"error": "origin not allowed"})
            if path not in SCHEMAS:
                return self._send(404, {"error": "unknown operation"})
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self._send(415, {"error": "application/json required"})
            try:
                n = int(self.headers.get("Content-Length", ""))
            except ValueError:
                return self._send(411, {"error": "Content-Length required"})
            if n < 0 or n > MAX_BODY:
                return self._send(413, {"error": f"body larger than {MAX_BODY} bytes"})
            try:
                body = json.loads(self.rfile.read(n) or b"null")
            except (ValueError, OSError):
                return self._send(400, {"error": "invalid JSON"})
            err = validate_body(path, body)
            if err:
                return self._send(400, {"error": err})
            if path == "/api/pair":
                res, why = ctl.pair(body["code"])
                ctl.audit("pair", "ok" if res else "rejected", [] if res else [why])
                return self._send(200, res) if res else self._send(403, {"error": why})
            s = self._session()
            if not s:
                return self._send(401, {"error": "not paired"})
            if not hmac.compare_digest(self.headers.get("X-AIVD-CSRF", ""), s["csrf"]):
                ctl.audit(path, "rejected", ["csrf"])
                return self._send(403, {"error": "CSRF token missing or wrong"})
            if path == "/api/ops/cancel":
                ctl.audit("cancel", "unavailable")
                return self._send(501, {"error": "cancel unavailable: the runner documents no cancel operation"})
            if path == "/api/ops/pull_model":
                code, res = ctl.op_pull(body)
                return self._send(code, res)
            if path == "/api/ops/cancel_pull":
                ok = ctl.models.puller.cancel()
                ctl.audit("cancel_pull", "ok" if ok else "none")
                return self._send(202, {"status": "CANCELLING"}) if ok else self._send(409, {"error": "no download in progress"})
            if path == "/api/ops/run_pipeline":
                code, res = ctl.pipeline.start(body)
                if code != 202:
                    ctl.audit("run_pipeline", "refused", [res.get("error", "")])
                return self._send(code, res)
            if path == "/api/ops/run_demo":
                code, res = ctl.demo.start(body)
                return self._send(code, res)
            code, res = ctl.op_run(body) if path == "/api/ops/rc6_run" else ctl.op_reveal(body)
            return self._send(code, res)

        def do_PUT(self):
            self._send(405, {"error": "method not allowed"})

        do_DELETE = do_PATCH = do_PUT

    return H


def serve(cfg, env=None):
    ctl = Controller(cfg, env=env)
    httpd = ThreadingHTTPServer(("127.0.0.1", cfg["port"]), make_handler(ctl))
    httpd.daemon_threads = True
    return ctl, httpd


def main(argv=None):
    ap = argparse.ArgumentParser(description="AIVD Command Center local controller (127.0.0.1 only)")
    ap.add_argument("--config", required=True, help="operator-local JSON config (keep outside git)")
    a = ap.parse_args(argv)
    try:
        cfg = validate_config(json.loads(Path(a.config).read_text()))
    except (OSError, ValueError) as e:
        print(f"refusing to start: {redact(e)}", file=sys.stderr)
        return 2
    ctl, httpd = serve(cfg)
    print(f"AIVD Command Center controller {VERSION} on http://127.0.0.1:{cfg['port']}/aivd/  (launch {ctl.launch_id})", flush=True)
    print(f"One-time pairing code (valid {PAIR_TTL // 60} min): {ctl.pair_code}", flush=True)
    print("Also written (0600) to the state directory as pairing-<launch>.json. Ctrl+C to stop.", flush=True)
    ctl.audit("start", "ok")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        ctl.audit("stop", "ok")
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
