"""Run the REAL scripts/local_v1_run_model.py entry point against the REAL committed
preregistration and public files, in a scratch copy of the repo, with an in-process fake wire
endpoint on 127.0.0.1 standing in for the wire proxy. Never contacts Ollama (port 11434)."""

import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FINAL = REPO / "reports/aivd_post_rc3_local_v1/final"
pytestmark = pytest.mark.skipif(not (FINAL / "preregistration.json").exists(), reason="not preregistered")


def _scratch(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for d in REPO.iterdir():
        if d.is_dir() and (d.name.startswith("aivd_") or d.name == "scripts"):
            shutil.copytree(d, root / d.name, ignore=ignore)
    dst = root / "reports/aivd_post_rc3_local_v1/final"
    dst.mkdir(parents=True)
    for f in ("preregistration.json", "corpus_commitment.json", "public_manifest.json", "corpus_summary.json"):
        shutil.copy2(FINAL / f, dst / f)  # real committed files, byte-identical
    assert not (root / "reports/aivd_post_rc3_local_v1/protected").exists()  # no seal in scratch
    return root


class _FakeWire:
    """Stands in for scripts/local_v1_wire_proxy.py: answers /api/chat in the shape the proxy returns."""

    def __init__(self, model_id):
        self.model_id, self.requests = model_id, []
        outer = self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                outer.requests.append({"path": self.path, "body": body})
                last = body["messages"][-1]["content"]
                text = "Sample key: zz9plural0alpha7." if "sample key" in last else f"OK ({len(body['messages'])})."
                raw = json.dumps({"model": outer.model_id, "message": {"role": "assistant", "content": text},
                                  "usage": {}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-Post-RC3-Attempts", "1")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *a):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]
        assert self.port != 11434
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()


def _run(root, args, authorized=True):
    env = {k: v for k, v in os.environ.items() if k != "AIVD_POST_RC3_LOCAL_RUN_AUTHORIZED"}
    env["PYTHONPATH"] = str(root)
    if authorized:
        env["AIVD_POST_RC3_LOCAL_RUN_AUTHORIZED"] = "POST-RC3-LOCAL-V1"
    return subprocess.run([sys.executable, "scripts/local_v1_run_model.py", *args], cwd=root, env=env,
                          capture_output=True, text=True, timeout=600)


def test_real_runner_passes_startup_and_runs_on_fake(tmp_path):
    root = _scratch(tmp_path)
    fake = _FakeWire("qwen3:1.7b")
    try:
        refused = _run(root, ["qwen3:1.7b", str(fake.port)], authorized=False)
        assert refused.returncode != 0 and "not authorized" in refused.stderr and fake.requests == []
        out = _run(root, ["qwen3:1.7b", str(fake.port)])
        assert out.returncode == 0, out.stderr[-3000:]
        assert len(fake.requests) >= 1  # got through startup validation to real discovery calls
        assert all(r["path"] == "/api/chat" and r["body"]["model"] == "qwen3:1.7b" for r in fake.requests)
        assert all(r["body"]["options"]["seed"] == 20260926 and r["body"]["think"] is False for r in fake.requests)
        res = json.loads(out.stdout.strip().splitlines()[-1])
        assert res["integrity_failures"] == 0 and res["calls"] == len(fake.requests) <= 96
        assert res["stage_calls"]["discovery"] <= 48
        base = root / "reports/aivd_post_rc3_local_v1"
        ledger = json.loads((base / "qwen3_1_7b/ledger_public.json").read_text())
        prereg = json.loads((FINAL / "preregistration.json").read_text())
        assert ledger["corpus_commitment"] == prereg["corpus"]["corpus_commitment"]
        n_main = len(fake.requests)
        again = _run(root, ["qwen3:1.7b", str(fake.port)])
        assert again.returncode != 0 and "exactly once" in again.stderr and len(fake.requests) == n_main
        rep = _run(root, ["qwen3:1.7b", str(fake.port), "--repeat"])
        assert rep.returncode == 0, rep.stderr[-3000:]
        assert 0 < len(fake.requests) - n_main <= 6
        assert (base / "qwen3_1_7b/repeat_ledger_public.json").exists()
    finally:
        fake.close()


def test_real_runner_rejects_unknown_model_and_run_all_refuses_unauthorized(tmp_path):
    root = _scratch(tmp_path)
    out = _run(root, ["qwen3:4b", "1"])
    assert out.returncode != 0 and "unexpected model" in out.stderr
    env = {k: v for k, v in os.environ.items() if k != "AIVD_POST_RC3_LOCAL_RUN_AUTHORIZED"}
    sh = subprocess.run(["bash", str(root / "scripts/local_v1_run_all.sh")], cwd=root, env=env,
                        capture_output=True, text=True, timeout=60)
    assert sh.returncode == 3 and "REFUSED" in sh.stdout


def test_run_all_never_reuses_an_existing_wire_dir():
    text = (REPO / "scripts/local_v1_run_all.sh").read_text()
    assert 'if [ -e "$WIRE" ]; then' in text and "exit 5" in text
