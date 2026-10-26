"""DEMO – not a research result. Allowlisted one-click interview-demo runner (loopback controller only)."""
from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from pathlib import Path

LABEL = "DEMO – not a research result"
DEMO_CONFIRM = "I AM THE AUTHORIZED OPERATOR AND AUTHORIZE THIS DEMO RUN"
DEMO_ENTRY = ["-m", "demo.aivd_interview"]
LOCAL_PATH_RX = re.compile(
    "(?:" + "|".join(("/" + "workspace", "/var" + "/tmp", r"/home/[^/\s]+", "/root", "/tmp"))
    + r")(?:/[^\s\"'`,;)\]]*)?"
)


def sanitize_doc(doc: dict) -> dict:
    """Drop absolute paths and rewrite any residual local-path strings before the UI/Pages see them."""
    raw = LOCAL_PATH_RX.sub("<local-path>", json.dumps(doc))
    out = json.loads(raw)
    out.pop("_paths", None)
    out["label"] = LABEL
    out["publication_safe"] = True
    return out


class DemoRunner:
    """Owns the demo subprocess and the latest sanitized report. Never talks to the research runner."""

    def __init__(self, ctl):
        self.ctl = ctl
        self.lock = threading.Lock()
        self.state = {"state": "idle", "label": LABEL}
        self.proc = None
        self.latest = None
        # Prefer a previously published static report if present next to the UI.
        baked = Path(ctl.cfg.get("cc_dir") or ".") / "public-data" / "demo" / "latest.json"
        if baked.is_file():
            try:
                self.latest = sanitize_doc(json.loads(baked.read_text()))
            except (OSError, ValueError):
                self.latest = None

    def status(self) -> dict:
        with self.lock:
            st = dict(self.state)
        # Surface live progress.json while a run is in flight (real file, not invented).
        demo_wt = self.ctl.cfg.get("demo_worktree")
        if demo_wt and st.get("state") == "running":
            prog = Path(demo_wt) / "demo" / "aivd_interview" / "reports" / "progress.json"
            if prog.is_file():
                try:
                    st["progress"] = json.loads(prog.read_text())
                except (OSError, ValueError):
                    pass
        return st

    def get_latest(self) -> dict | None:
        with self.lock:
            return self.latest

    def start(self, body: dict):
        if body.get("confirm") != DEMO_CONFIRM:
            return 400, {"error": "confirmation phrase mismatch", "label": LABEL}
        demo_wt = self.ctl.cfg.get("demo_worktree")
        if not demo_wt:
            return 503, {"error": "demo_worktree is not configured on this controller", "label": LABEL}
        root = Path(demo_wt)
        if not (root / "demo" / "aivd_interview" / "run_demo.py").is_file():
            return 503, {"error": "demo package missing from demo_worktree", "label": LABEL}
        with self.ctl.lock:
            if self.ctl.run.get("state") == "running":
                return 409, {"error": "an RC6 run is in progress", "label": LABEL}
        with self.ctl.pipeline.lock:
            if self.ctl.pipeline.current is not None and self.ctl.pipeline.current.get("state") == "running":
                return 409, {"error": "a pipeline is running", "label": LABEL}
        if self.ctl.models.puller.busy():
            return 409, {"error": "a model download is in progress", "label": LABEL}
        with self.lock:
            if self.state.get("state") == "running":
                return 409, {"error": "a demo run is already in progress", "label": LABEL}
            self.state = {"state": "running", "op": "run_demo", "started": time.time(), "label": LABEL}
        mode = "auto"
        host = self.ctl.cfg.get("demo_ollama_host") or "http://127.0.0.1:11536"
        env = dict(self.ctl.env)
        env["PYTHONPATH"] = str(root) + ((":" + env["PYTHONPATH"]) if env.get("PYTHONPATH") else "")
        env["AIVD_DEMO_OLLAMA_HOST"] = host
        argv = [self.ctl.python, *DEMO_ENTRY, "--mode", mode, "--host", host]
        try:
            p = subprocess.Popen(
                argv,
                cwd=str(root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as e:
            with self.lock:
                self.state = {"state": "failed", "op": "run_demo", "error": "spawn failed", "label": LABEL}
            self.ctl.audit("run_demo", "failed", [str(type(e).__name__)])
            return 500, {"error": "could not start demo", "label": LABEL}
        self.proc = p
        self.ctl.audit("run_demo", "started", ["mode=" + mode])
        threading.Thread(target=self._wait, args=(p, root), daemon=True).start()
        return 202, {"status": "STARTED", "label": LABEL}

    def _wait(self, p: subprocess.Popen, root: Path):
        try:
            out, err = p.communicate(timeout=self.ctl.cfg.get("max_run_seconds", 3600))
            timed_out = False
        except subprocess.TimeoutExpired:
            p.kill()
            try:
                out, err = p.communicate(timeout=5)
            except Exception:
                out, err = b"", b""
            timed_out = True
        rc = p.returncode
        latest_path = root / "demo" / "aivd_interview" / "reports" / "latest.json"
        loaded = None
        if latest_path.is_file():
            try:
                loaded = sanitize_doc(json.loads(latest_path.read_text()))
            except (OSError, ValueError):
                loaded = None
        # Mirror into the Command Center public-data so a rebuild can ship the new static report.
        cc = self.ctl.cfg.get("cc_dir")
        if loaded and cc:
            dest = Path(cc) / "public-data" / "demo"
            try:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / "latest.json").write_text(json.dumps(loaded, indent=2) + "\n")
                expl = root / "demo" / "aivd_interview" / "reports" / "EXPLAINER.md"
                if expl.is_file():
                    text = LOCAL_PATH_RX.sub("<local-path>", expl.read_text())
                    if LABEL not in text.splitlines()[0]:
                        text = f"# {LABEL}\n\n" + text
                    (dest / "EXPLAINER.md").write_text(text)
            except OSError:
                pass
        state = "timeout" if timed_out else ("completed" if rc == 0 and loaded else "failed")
        summary = {}
        if loaded:
            summary = {
                "label": LABEL,
                "mode_used": loaded.get("mode_used"),
                "per_target": [
                    {
                        "target": r["target"],
                        "planted": r["planted"],
                        "deterministic_verified": r["deterministic"]["verified"],
                        "any_model_verified": any(m["verified"] for m in r["models"]),
                    }
                    for r in loaded.get("per_target_summary", [])
                ],
            }
        with self.lock:
            self.state = {
                "state": state,
                "op": "run_demo",
                "exit_code": rc,
                "finished": time.time(),
                "summary": summary,
                "label": LABEL,
            }
            if loaded:
                self.latest = loaded
            self.proc = None
        self.ctl.audit("run_demo", state, [f"exit {rc}"])
