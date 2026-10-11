"""Model catalog, system specs, model-store scan, RAM fit, digest verification and the single-slot puller.

Listing (GET /api/models) NEVER starts Ollama and never touches the network: installed models are read from the
configured store's manifest files (names come from the manifest paths; nothing is invented), digests from the
manifests, and RAM/CPU/GPU from /proc, /dev and /sys.

Pulling (POST /api/ops/pull_model, or the pipeline's "Model readiness" step with download confirmed) is the ONLY
place Ollama is started: the configured binary runs `serve` bound to 127.0.0.1:<pull_port> with OLLAMA_MODELS set
to the configured store and OLLAMA_NOPRUNE=1 (so it can never prune existing blobs), the model is pulled through that
server's /api/pull stream, and the server is stopped in a finally block. The model is never loaded and no model
call is made. One pull at a time; overall timeout; cancel stops the server. After the pull every layer blob is
re-hashed and the manifest + weights digests are compared with the catalog pins; a mismatch FAILS.
Downloading a model does not authorize anything: Part B keeps every gate.
"""

import hashlib
import http.client
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path

from controller import procs as PR

CATALOG_PATH = Path(__file__).with_name("models_catalog.json")
NAME_RX = re.compile(r"^[a-z0-9][a-z0-9._-]{0,30}:[a-z0-9][a-z0-9._-]{0,20}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MIB = 1024 * 1024
RC6_MEMORY_GATE_KB = 7_600_000
REGISTRY = "registry.ollama.ai"
DEFAULT_RUNTIME_PORT = 11434      # the research runtime port; the puller never uses it
MAX_MANIFESTS = 200
PULL_LOG_CAP = 300
FIT_ORDER = {"FITS": 0, "TIGHT": 1, "NOT_VERIFIED": 2, "EXCEEDS": 3}
INSTALLED_OK = ("installed", "installed_unpinned")
SERVE_ENV_PASS = ("PATH", "LANG", "LC_ALL", "TZ", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy",
                  "NO_PROXY", "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR")


class CatalogError(ValueError):
    pass


# ---------------------------------------------------------------- catalog
def load_catalog(path=None, rc6_allowed=()):
    p = Path(path) if path else CATALOG_PATH
    try:
        raw = json.loads(p.read_text())
    except (OSError, ValueError) as e:
        raise CatalogError(f"model catalog unreadable: {type(e).__name__}") from None
    if not isinstance(raw, dict) or not isinstance(raw.get("models"), list) or not isinstance(raw.get("estimate"), dict):
        raise CatalogError("model catalog must have 'estimate' and 'models'")
    est = raw["estimate"]
    for k in ("num_ctx", "kv_bytes_per_element", "compute_overhead_mib", "runtime_overhead_mib", "headroom_mib"):
        if not isinstance(est.get(k), int) or isinstance(est.get(k), bool) or est[k] < 0:
            raise CatalogError(f"estimate.{k} must be a non-negative integer")
    seen, models = set(), []
    for m in raw["models"]:
        if not isinstance(m, dict) or not NAME_RX.fullmatch(str(m.get("name", ""))) or m["name"] in seen:
            raise CatalogError("every catalog model needs a unique name like family:tag")
        if not isinstance(m.get("size_bytes"), int) or m["size_bytes"] <= 0 or not isinstance(m.get("family"), str):
            raise CatalogError(f"{m['name']}: size_bytes and family required")
        a = m.get("arch") or {}
        if not all(isinstance(a.get(k), int) and a[k] > 0 for k in ("layers", "kv_heads", "head_dim")):
            raise CatalogError(f"{m['name']}: arch.layers/kv_heads/head_dim required")
        pins = m.get("pins")
        if pins is not None and not (isinstance(pins, dict) and set(pins) == {"manifest_sha256", "model_blob_sha256"}
                                     and all(HEX64.fullmatch(str(v)) for v in pins.values())):
            raise CatalogError(f"{m['name']}: pins must be null or both 64-hex digests")
        allow = m.get("rc6_allowlisted") is True
        # The catalog can never widen the RC6 allowlist: that list is fixed in the controller source.
        if allow and m["name"] not in rc6_allowed:
            raise CatalogError(f"{m['name']}: rc6_allowlisted is true but the model is not in the RC6 allowlist")
        if allow and pins is None:
            raise CatalogError(f"{m['name']}: RC6 models must carry pinned digests")
        seen.add(m["name"])
        models.append({"name": m["name"], "family": m["family"], "params": str(m.get("params", "")),
                       "quant": str(m.get("quant", "")), "rc6_allowlisted": allow, "size_bytes": m["size_bytes"],
                       "size_is_exact": m.get("size_is_exact") is True, "arch": {k: a[k] for k in
                                                                                ("layers", "kv_heads", "head_dim")},
                       "pins": pins})
    return {"estimate": est, "models": models, "note": str(raw.get("note", ""))[:600]}


def estimate_ram(model, est):
    a = model["arch"]
    weights = model["size_bytes"] / MIB
    kv = 2 * a["layers"] * a["kv_heads"] * a["head_dim"] * est["kv_bytes_per_element"] * est["num_ctx"] / MIB
    total = weights + kv + est["compute_overhead_mib"] + est["runtime_overhead_mib"]
    return {"weights_mib": round(weights), "kv_cache_mib": round(kv), "compute_mib": est["compute_overhead_mib"],
            "runtime_mib": est["runtime_overhead_mib"], "headroom_mib": est["headroom_mib"],
            "estimate_kb": int(total * 1024), "recommended_kb": int((total + est["headroom_mib"]) * 1024),
            "num_ctx": est["num_ctx"], "approximate": not model["size_is_exact"]}


def fit_verdict(ram, specs):
    need, rec = ram["estimate_kb"], ram["recommended_kb"]
    avail, total = specs.get("mem_available_kb"), specs.get("mem_total_kb")
    base = {"required_kb": need, "recommended_kb": rec, "available_kb": avail, "total_kb": total}
    if avail is None or total is None:
        return {**base, "verdict": "NOT_VERIFIED", "reason": "MemAvailable/MemTotal unreadable"}
    if total < need:
        return {**base, "verdict": "EXCEEDS", "reason": f"needs ~{need:,} kB but this machine has only {total:,} kB "
                "in total: NOT RECOMMENDED, cannot fit"}
    if avail < need:
        return {**base, "verdict": "EXCEEDS", "reason": f"needs ~{need:,} kB, MemAvailable is {avail:,} kB: NOT "
                "RECOMMENDED, will likely OOM"}
    if avail < rec:
        return {**base, "verdict": "TIGHT", "reason": f"needs ~{need:,} kB and MemAvailable is {avail:,} kB, "
                f"below the {rec:,} kB recommended with 1 GiB headroom"}
    return {**base, "verdict": "FITS", "reason": f"needs ~{need:,} kB (+1 GiB headroom = {rec:,} kB); "
            f"MemAvailable is {avail:,} kB"}


# ---------------------------------------------------------------- system specs
def read_specs(proc="/proc", dev="/dev", sys_root="/sys"):
    mem = {}
    try:
        for line in Path(proc, "meminfo").read_text().splitlines():
            k, _, v = line.partition(":")
            if k in ("MemTotal", "MemAvailable", "SwapTotal"):
                mem[k] = int(v.split()[0])
    except (OSError, ValueError, IndexError):
        pass
    cpu_model = None
    try:
        for line in Path(proc, "cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()[:80]
                break
    except OSError:
        pass
    gpus = []
    for pat, kind in (("nvidia[0-9]*", "NVIDIA"), ("kfd", "AMD ROCm")):
        gpus += [kind for _ in Path(dev).glob(pat)]
    dri = sorted(p.name for p in Path(dev, "dri").glob("renderD*")) if Path(dev, "dri").is_dir() else []
    balloon = Path(sys_root, "bus", "virtio", "drivers", "virtio_balloon").exists()
    notes = []
    if balloon:
        notes.append("virtio_balloon driver present: the hypervisor can inflate the memory balloon, so MemAvailable "
                     "can drop (or recover) between this reading and a run. Re-check right before running.")
    if not gpus:
        notes.append("No GPU compute device (/dev/nvidia*, /dev/kfd) found: models run on the CPU only." +
                     (f" Render nodes present: {', '.join(dri)} (not used for inference)." if dri else ""))
    return {"mem_total_kb": mem.get("MemTotal"), "mem_available_kb": mem.get("MemAvailable"),
            "swap_total_kb": mem.get("SwapTotal"), "rc6_memory_gate_kb": RC6_MEMORY_GATE_KB,
            "rc6_memory_gate_met": (mem.get("MemAvailable") or 0) >= RC6_MEMORY_GATE_KB,
            "cpu_count": os.cpu_count(), "cpu_model": cpu_model,
            "gpu": {"present": bool(gpus), "kinds": sorted(set(gpus)), "render_nodes": len(dri)},
            "balloon": balloon, "notes": notes}


# ---------------------------------------------------------------- store scan / verification
def manifest_path(store, name):
    model, tag = name.split(":", 1)
    ns, _, model = model.rpartition("/")
    return Path(store, "manifests", REGISTRY, ns or "library", model, tag)


def blob_path(store, digest):
    return Path(store, "blobs", digest.replace(":", "-"))


def _parse_manifest(store, name, p):
    raw = p.read_bytes()
    if len(raw) > 65536:
        return None
    doc = json.loads(raw)
    layers = [l for l in (doc.get("layers") or []) if isinstance(l, dict)]
    cfg = doc.get("config") if isinstance(doc.get("config"), dict) else None
    entries = layers + ([cfg] if cfg else [])
    model_layer = next((l for l in layers if str(l.get("mediaType", "")).endswith("image.model")), None)
    missing, wrong_size = 0, 0
    for l in entries:
        d = str(l.get("digest", ""))
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", d):
            missing += 1
            continue
        bp = blob_path(store, d)
        try:
            if bp.is_symlink() or bp.stat().st_size != int(l.get("size", -1)):
                wrong_size += 1
        except OSError:
            missing += 1
    return {"name": name, "manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "model_blob_sha256": str(model_layer.get("digest", ""))[7:] if model_layer else None,
            "model_blob_bytes": int(model_layer.get("size", 0)) if model_layer else None,
            "total_bytes": sum(int(l.get("size", 0)) for l in entries), "layers": len(entries),
            "blobs_missing": missing, "blobs_wrong_size": wrong_size,
            "blobs_complete": missing == 0 and wrong_size == 0 and model_layer is not None}


def scan_store(store):
    """Installed models = manifest files present in the store (read-only)."""
    out, base = [], Path(store, "manifests", REGISTRY) if store else None
    if not base or not base.is_dir():
        return out
    for ns in sorted(base.iterdir()):
        if not ns.is_dir() or ns.is_symlink():
            continue
        for model in sorted(ns.iterdir()):
            if not model.is_dir() or model.is_symlink():
                continue
            for tag in sorted(model.iterdir()):
                if len(out) >= MAX_MANIFESTS:
                    return out
                if not tag.is_file() or tag.is_symlink():
                    continue
                name = f"{model.name}:{tag.name}" if ns.name == "library" else f"{ns.name}/{model.name}:{tag.name}"
                try:
                    m = _parse_manifest(store, name, tag)
                except (OSError, ValueError, TypeError):
                    m = None
                out.append(m or {"name": name, "unreadable": True, "blobs_complete": False})
    return out


def install_status(model, inst):
    if inst is None:
        return "missing", "not in the configured model store"
    if inst.get("unreadable"):
        return "incomplete", "manifest unreadable"
    if not inst["blobs_complete"]:
        return "incomplete", f"{inst['blobs_missing']} blob(s) missing, {inst['blobs_wrong_size']} with wrong size"
    pins = model.get("pins") if model else None
    if pins:
        bad = [k for k in ("manifest_sha256", "model_blob_sha256") if inst.get(k) != pins[k]]
        if bad:
            return "differs_from_pin", "installed copy differs from the pinned digest (" + ", ".join(bad) + ")"
        return "installed", "manifest and weights digests match the pins (manifest hashed; blobs size-checked)"
    return "installed_unpinned", "installed; no pinned digest exists for this model (recorded digest only)"


_HASH_CACHE, _HASH_LOCK = {}, threading.Lock()


def sha256_file(p, cancel=None):
    st = p.stat()
    key = (str(p), st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    with _HASH_LOCK:
        if key in _HASH_CACHE:
            return _HASH_CACHE[key]
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(4 * MIB), b""):
            if cancel is not None and cancel.is_set():
                raise InterruptedError("cancelled")
            h.update(chunk)
    d = h.hexdigest()
    with _HASH_LOCK:
        _HASH_CACHE[key] = d
    return d


def verify_deep(store, name, model, cancel=None):
    """Re-hash every blob of the installed manifest and compare manifest/weights digests with the pins."""
    p = manifest_path(store, name)
    checks = []
    try:
        raw = p.read_bytes()
        doc = json.loads(raw)
    except (OSError, ValueError):
        return {"ok": False, "reason": "manifest missing or unreadable", "checks": checks}
    pins = (model or {}).get("pins")
    man = hashlib.sha256(raw).hexdigest()
    checks.append({"what": "manifest sha256", "expected": pins["manifest_sha256"] if pins else None,
                   "observed": man, "match": (man == pins["manifest_sha256"]) if pins else None})
    entries = [l for l in (doc.get("layers") or []) if isinstance(l, dict)]
    if isinstance(doc.get("config"), dict):
        entries.append(doc["config"])
    bad = 0
    for l in entries:
        d = str(l.get("digest", ""))
        want = d[7:] if d.startswith("sha256:") else ""
        try:
            got = sha256_file(blob_path(store, d), cancel) if HEX64.fullmatch(want) else None
        except OSError:
            got = None
        ok = got == want
        bad += not ok
        is_model = str(l.get("mediaType", "")).endswith("image.model")
        if is_model:
            pin = pins["model_blob_sha256"] if pins else None
            checks.append({"what": "weights blob sha256 (re-hashed)", "expected": pin or want, "observed": got,
                           "match": (got == pin) if pin else ok})
            if pin and want != pin:
                bad += 1
    checks.append({"what": f"all {len(entries)} blobs re-hashed equal their manifest digests",
                   "expected": None, "observed": f"{len(entries) - min(bad, len(entries))}/{len(entries)}",
                   "match": bad == 0})
    pin_ok = all(c["match"] is not False for c in checks)
    if not pin_ok:
        reason = "DIGEST MISMATCH: " + "; ".join(c["what"] for c in checks if c["match"] is False)
    elif pins:
        reason = "manifest and weights match the pinned digests; every blob re-hashed OK"
    else:
        reason = "every blob re-hashed OK; no pin exists for this model (digest recorded, not compared to a pin)"
    return {"ok": pin_ok, "reason": reason, "checks": checks, "pinned": bool(pins)}


# ---------------------------------------------------------------- puller
def _port_free(port):
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # same semantics as the server's own listen()
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


class Puller:
    """Single pull slot. pull() is blocking (called from the pipeline thread or a worker thread)."""

    def __init__(self, mgr, popen=subprocess.Popen, clock=time.monotonic):
        self.mgr = mgr
        self.popen = popen
        self.clock = clock
        self.lock = threading.Lock()
        self.job = None
        self.cancel_ev = threading.Event()
        self._proc = None
        self._on_line = self._on_progress = None
        self._timed_out = False

    def busy(self):
        with self.lock:
            return bool(self.job and self.job["state"] == "running")

    def snapshot(self):
        with self.lock:
            return json.loads(json.dumps(self.job)) if self.job else None

    def cancel(self):
        with self.lock:
            if not (self.job and self.job["state"] == "running"):
                return False
            self.cancel_ev.set()
        self._stop_serve()
        return True

    def _log(self, line):
        line = self.mgr.redact(line)[:300]
        with self.lock:
            if self.job is not None:
                lg = self.job["log"]
                lg.append({"t": round(self.clock() - self.job["_t0"], 1), "line": line})
                del lg[:-PULL_LOG_CAP]
        if self._on_line:
            self._on_line(line)

    def _progress(self, prog):
        with self.lock:
            if self.job is not None:
                self.job["progress"] = prog
        if self._on_progress:
            self._on_progress(json.loads(json.dumps(prog)))

    def pull(self, model, origin, on_line=None, on_progress=None, timeout=None):
        cfg = self.mgr.cfg
        with self.lock:
            if self.job and self.job["state"] == "running":
                return {"outcome": "busy", "reason": "another download is in progress"}
            self.cancel_ev.clear()
            self.job = {"id": "p" + secrets.token_hex(4), "model_id": model["name"], "origin": origin,
                        "state": "running", "started_at": _iso(), "finished_at": None, "duration_s": None,
                        "progress": {"status": "starting", "percent": 0, "completed": 0, "total": 0, "layers": []},
                        "log": [], "result": None, "_t0": self.clock()}
        self._on_line, self._on_progress = on_line, on_progress
        t0 = self.clock()
        res = {"model_id": model["name"], "serve": {"started": False, "stopped": None, "bind": None}}
        try:
            res.update(self._pull(model, timeout or cfg.get("pull_timeout_s") or 3600, res))
        except Exception as e:  # never leak a traceback
            res.update(outcome="failed", reason=f"pull raised {type(e).__name__}")
        finally:
            if res["serve"]["started"]:
                res["serve"]["stopped"] = self._stop_serve()
                self._log("ollama serve stopped" if res["serve"]["stopped"] else
                          "WARNING: could not confirm the ollama serve process stopped")
        if self.cancel_ev.is_set() and res.get("outcome") not in ("succeeded",):
            res.update(outcome="cancelled", reason="cancelled by the operator; partial blobs may remain for resume")
        res["duration_s"] = round(self.clock() - t0, 2)
        with self.lock:
            self.job.update(state=res["outcome"], finished_at=_iso(), duration_s=res["duration_s"],
                            result={k: v for k, v in res.items()})
            out = {k: v for k, v in self.job.items() if not k.startswith("_")}
        self.mgr.ctl_audit("pull_model", res["outcome"], [model["name"], res.get("reason", "")])
        return json.loads(json.dumps(out["result"]))

    def _pull(self, model, timeout, res):
        cfg, store, name = self.mgr.cfg, self.mgr.store, model["name"]
        deadline = self.clock() + timeout
        pre = self.mgr.pull_preconditions(model)
        if pre:
            self._log("refused: " + "; ".join(pre))
            return {"outcome": "blocked", "reason": "; ".join(pre)}
        port = cfg.get("pull_port", 11535)
        home = Path(cfg["state_dir"]) / "ollama-home"
        home.mkdir(parents=True, exist_ok=True, mode=0o700)
        env = {k: v for k, v in self.mgr.env.items() if k in SERVE_ENV_PASS}
        env.update({"HOME": str(home), "OLLAMA_HOST": f"127.0.0.1:{port}", "OLLAMA_MODELS": str(store),
                    "OLLAMA_NOPRUNE": "1", "OLLAMA_KEEP_ALIVE": "0", "OLLAMA_NOHISTORY": "1"})
        logf = Path(cfg["state_dir"]) / "ollama-pull-serve.log"
        fd = os.open(logf, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as fh:
            self._proc = self.popen([cfg["ollama_binary"], "serve"], env=env, stdout=fh, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, cwd=str(home), **PR.spawn_kwargs())
        res["serve"].update(started=True, bind=f"127.0.0.1:{port}")
        self._log(f"started ollama serve on 127.0.0.1:{port} (OLLAMA_NOPRUNE=1; model store from config)")
        ready_by = min(deadline, self.clock() + 30)
        while True:
            if self.cancel_ev.is_set():
                return {"outcome": "cancelled", "reason": "cancelled before the server was ready"}
            if self._proc.poll() is not None:
                return {"outcome": "failed", "reason": f"ollama serve exited early (code {self._proc.returncode})"}
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            try:
                c.request("GET", "/api/version")
                r = c.getresponse()
                ver = json.loads(r.read() or b"{}").get("version")
                if r.status == 200:
                    res["serve"]["version"] = str(ver)[:40]
                    break
            except (OSError, ValueError, http.client.HTTPException):
                pass
            finally:
                c.close()
            if self.clock() > ready_by:
                return {"outcome": "failed", "reason": "ollama serve did not become ready within 30 s"}
            time.sleep(0.25)
        watchdog = threading.Timer(max(1, deadline - self.clock()), self._timeout_kill)
        watchdog.daemon = True
        self._timed_out = False
        watchdog.start()
        layers, status, last_logged = {}, "", {}
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=300)
        try:
            c.request("POST", "/api/pull", body=json.dumps({"name": name, "model": name, "stream": True}),
                      headers={"Content-Type": "application/json"})
            r = c.getresponse()
            if r.status != 200:
                return {"outcome": "failed", "reason": f"pull request refused (HTTP {r.status})"}
            ok = False
            for raw in iter(r.readline, b""):
                try:
                    ev = json.loads(raw)
                except ValueError:
                    continue
                if ev.get("error"):
                    return {"outcome": "failed", "reason": "registry/ollama error: " + self.mgr.redact(ev["error"])[:200]}
                st = str(ev.get("status", ""))[:80]
                dg = str(ev.get("digest", ""))
                if dg and isinstance(ev.get("total"), int):
                    L = layers.setdefault(dg, {"digest": dg[7:19], "total": ev["total"], "completed": 0})
                    L["completed"] = int(ev.get("completed") or L["completed"])
                    pct = int(100 * L["completed"] / L["total"]) if L["total"] else 100
                    if pct // 10 != last_logged.get(dg, -1):
                        last_logged[dg] = pct // 10
                        self._log(f"layer {L['digest']}: {pct}% of {L['total'] / MIB:,.1f} MiB")
                elif st != status:
                    self._log(st)
                status = st
                tot = sum(l["total"] for l in layers.values())
                done = sum(min(l["completed"], l["total"]) for l in layers.values())
                self._progress({"status": status, "total": tot, "completed": done,
                                "percent": round(100 * done / tot, 1) if tot else 0,
                                "layers": [dict(l, percent=round(100 * l["completed"] / l["total"], 1) if l["total"]
                                                else 100.0) for l in layers.values()]})
                if st == "success":
                    ok = True
        except (OSError, http.client.HTTPException):
            if self.cancel_ev.is_set():
                return {"outcome": "cancelled", "reason": "cancelled by the operator"}
            if self._timed_out:
                return {"outcome": "timeout", "reason": f"download exceeded {timeout} s and was stopped"}
            return {"outcome": "failed", "reason": "connection to the local ollama server failed or stalled"}
        finally:
            watchdog.cancel()
            c.close()
        if self.cancel_ev.is_set():
            return {"outcome": "cancelled", "reason": "cancelled by the operator"}
        if self._timed_out:
            return {"outcome": "timeout", "reason": f"download exceeded {timeout} s and was stopped"}
        if not ok:
            return {"outcome": "failed", "reason": "stream ended without success"}
        res["bytes_total"] = sum(l["total"] for l in layers.values())
        res["layers"] = len(layers)
        self._log("verifying: re-hashing every blob and comparing with the pinned digests")
        v = verify_deep(store, name, model, self.cancel_ev)
        res["verify"] = v
        self._log(v["reason"])
        if not v["ok"]:
            return {"outcome": "failed", "reason": v["reason"]}
        return {"outcome": "succeeded", "reason": "downloaded and verified: " + v["reason"]}

    def _timeout_kill(self):
        self._timed_out = True
        self._stop_serve()

    def _stop_serve(self):
        p = self._proc
        if p is None:
            return True
        # only ever the `ollama serve` this puller started itself (own process group); SIGINT, SIGTERM, SIGKILL
        self.stopped_by = PR.stop(p, self.mgr.cfg.get("stop_grace_s", PR.DEFAULT_GRACE_S))
        return p.poll() is not None


def _iso():
    import datetime
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------- manager
class ModelManager:
    def __init__(self, cfg, env, proc_check, redact, audit, rc6_allowed, proc_root="/proc", dev="/dev",
                 sys_root="/sys", popen=subprocess.Popen):
        self.cfg, self.env, self.proc_check, self.redact, self.ctl_audit = cfg, env, proc_check, redact, audit
        self.rc6_allowed = tuple(rc6_allowed)
        self.store = cfg.get("model_store")
        self.roots = (proc_root, dev, sys_root)
        self.catalog = load_catalog(cfg.get("model_catalog"), self.rc6_allowed)
        self.by_name = {m["name"]: m for m in self.catalog["models"]}
        self.puller = Puller(self, popen=popen)

    def specs(self):
        return read_specs(*self.roots)

    def installed(self):
        return {m["name"]: m for m in scan_store(self.store)} if self.store else {}

    def assess(self, name, specs=None, installed=None):
        m = self.by_name.get(name)
        if m is None:
            return None
        specs = specs or self.specs()
        inst = (installed if installed is not None else self.installed()).get(name)
        ram = estimate_ram(m, self.catalog["estimate"])
        status, why = install_status(m, inst) if self.store else ("not_verified", "no model_store configured")
        return {**{k: m[k] for k in ("name", "family", "params", "quant", "rc6_allowlisted", "size_bytes",
                                     "size_is_exact", "pins")},
                "ram": ram, "fit": fit_verdict(ram, specs), "install": {"status": status, "reason": why,
                                                                        "observed": inst},
                "part_b_eligible": m["rc6_allowlisted"],
                "part_b_note": "in the RC6 preregistration allowlist (Part B still needs every gate)"
                if m["rc6_allowlisted"] else "catalog extra: NOT in the RC6 preregistration allowlist; it can never "
                                             "be used for Part B"}

    def recommend(self, entries):
        def fits(e):
            return e["fit"]["verdict"] in ("FITS", "TIGHT")

        def key(e):
            return (not e["rc6_allowlisted"], FIT_ORDER[e["fit"]["verdict"]], -e["size_bytes"])
        inst = sorted([e for e in entries if fits(e) and e["install"]["status"] in INSTALLED_OK], key=key)
        if inst:
            return {"model_id": inst[0]["name"], "reason": "best installed model that fits MemAvailable "
                    "(RC6-allowlisted first, then largest that fits)"}
        cat = sorted([e for e in entries if fits(e)], key=key)
        if cat:
            return {"model_id": cat[0]["name"], "reason": "no installed model fits; best fitting catalog model "
                    "(needs a download)"}
        return {"model_id": None, "reason": "no catalog model fits the current MemAvailable"}

    def listing(self):
        specs, inst = self.specs(), self.installed()
        entries = [self.assess(n, specs, inst) for n in self.by_name]

        def group(e):
            f = e["fit"]["verdict"] in ("FITS", "TIGHT", "NOT_VERIFIED")
            if e["fit"]["verdict"] == "EXCEEDS":
                return 2
            return 0 if (f and e["install"]["status"] in INSTALLED_OK) else 1
        entries.sort(key=lambda e: (group(e), not e["rc6_allowlisted"], FIT_ORDER[e["fit"]["verdict"]],
                                    e["size_bytes"]))
        for e in entries:
            e["group"] = ["installed_fits", "fits_not_installed", "too_large"][group(e)]
        extra = [{"name": n, "total_bytes": i.get("total_bytes"), "in_catalog": False,
                  "note": "installed in the store but not in the AIVD catalog (cannot be selected)"}
                 for n, i in sorted(inst.items()) if n not in self.by_name]
        pull = self.puller.snapshot()
        if pull:
            pull = {k: v for k, v in pull.items() if not k.startswith("_")}
        return {"system": specs, "catalog": entries, "installed_other": extra,
                "recommendation": self.recommend(entries), "pull": pull,
                "policy": {"store_configured": bool(self.store), "pull_enabled": self.pull_enabled(),
                           "pull_disabled_reason": self.pull_disabled_reason(),
                           "listing_starts_ollama": False,
                           "ram_rule": self.catalog["estimate"], "catalog_note": self.catalog["note"],
                           "rc6_allowlist": list(self.rc6_allowed)}}

    def pull_enabled(self):
        return not self.pull_disabled_reason()

    def pull_disabled_reason(self):
        c = self.cfg
        if not c.get("pull_enabled"):
            return "downloads are disabled in the controller config (pull_enabled is false)"
        if not self.store:
            return "no model_store configured"
        if not c.get("ollama_binary"):
            return "no ollama_binary configured"
        return ""

    def pull_preconditions(self, model):
        """Every reason a pull must not start. Empty list = OK to start the local server and pull."""
        out = []
        dis = self.pull_disabled_reason()
        if dis:
            return [dis]
        if not Path(self.cfg["ollama_binary"]).is_file():
            out.append("configured ollama binary not found")
        if not Path(self.store).is_dir() or not os.access(self.store, os.W_OK):
            out.append("model store missing or not writable")
        running = self.proc_check()
        if running:
            out.append("an Ollama process is already running (never signalled; stop it yourself)")
        elif running is None:
            out.append("process table unreadable")
        port = self.cfg.get("pull_port", 11535)
        if not _port_free(port):
            out.append(f"127.0.0.1:{port} is in use")
        a = self.assess(model["name"])
        if a["fit"]["verdict"] == "EXCEEDS":
            out.append("RAM: " + a["fit"]["reason"] + " (not downloaded)")
        if a["install"]["status"] == "differs_from_pin":
            out.append("an installed copy differs from the pinned digest; refusing to pull over it")
        try:
            free = shutil.disk_usage(self.store).free
            need = int(model["size_bytes"] * 1.1) + 512 * MIB
            if free < need:
                out.append(f"disk: {free // MIB:,} MiB free in the model store, ~{need // MIB:,} MiB needed")
        except OSError:
            out.append("disk space unreadable")
        return out
