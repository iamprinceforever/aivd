"""AIVD-RC5-GENERALIZATION-V1 evaluator-side wire proxy for ONE model (separate process): frozen
aivd_rc3.wire.Wire, loaded with the ASSEMBLED 120-scenario seal, in front of local Ollama /api/chat. The only
run-time process that reads an RC5 seal. Makes no request until the blind runner sends one.
Refuses unless AIVD_RC5_RUN_AUTHORIZED=AIVD-RC5-GENERALIZATION-V1. NOT RUN in the design phase.

usage: rc5_gen_wire_proxy.py <model_id> <port> [--repeat]
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from aivd_rc3.wire import Wire

from aivd_rc5_gen import ASSEMBLED_SEAL_PATH, EXPERIMENT_ID, PROTECTED_DIR, RUN_ENV
from aivd_rc5_gen.models import MODEL_DIRS, MODELS
from aivd_post_rc3_local.ollama_backend import make_inner


def main(model_id: str, port: int, repeat: bool) -> None:
    if os.environ.get(RUN_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: evaluation not authorized")
    if model_id not in MODELS:
        sys.exit(f"unexpected model {model_id!r}")
    seal = json.loads(Path(ASSEMBLED_SEAL_PATH).read_text(encoding="utf-8"))
    if len(seal.get("targets", [])) != 120:
        sys.exit("assembled seal must hold 120 targets")
    wire_dir = Path(PROTECTED_DIR) / "wire" / (MODEL_DIRS[model_id] + ("_repeat" if repeat else ""))
    if wire_dir.exists():
        sys.exit("wire directory already exists; each model runs exactly once")
    inner = make_inner(model_id)
    wire = Wire(seal, inner, wire_dir)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                status, raw = wire(json.loads(body))
            except Exception:
                status, raw = 502, b""
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Post-RC3-Attempts", str(getattr(inner, "last_attempts", 1)))
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    flag = "--repeat" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--repeat"]
    if os.environ.get(RUN_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: evaluation not authorized")
    if len(args) != 2:
        sys.exit("usage: rc5_gen_wire_proxy.py <model_id> <port> [--repeat]")
    main(args[0], int(args[1]), flag)
