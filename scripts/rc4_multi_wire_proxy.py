"""AIVD-RC4-MULTI-V1 evaluator-side wire proxy (separate process): frozen aivd_rc3.wire.Wire in front of
local Ollama /api/chat. The only run-time process that reads the RC4 seal. Makes no request until the
blind runner sends one. Refuses unless AIVD_RC4_RUN_AUTHORIZED=AIVD-RC4-MULTI-V1. NOT RUN in design.

usage: rc4_multi_wire_proxy.py <seal_path> <wire_dir> <port> <model_id>
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from aivd_rc3.wire import Wire

from aivd_rc4_multi import EXPERIMENT_ID, RUN_ENV
from aivd_post_rc3_local.models import MODELS
from aivd_post_rc3_local.ollama_backend import make_inner


def main(seal_path: str, wire_dir: str, port: int, model_id: str) -> None:
    if os.environ.get(RUN_ENV) != EXPERIMENT_ID:
        sys.exit("REFUSED: evaluation not authorized")
    if model_id not in MODELS:
        sys.exit(f"unexpected model {model_id!r}")
    seal = json.loads(Path(seal_path).read_text(encoding="utf-8"))
    inner = make_inner(model_id)
    wire = Wire(seal, inner, Path(wire_dir))

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
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])
