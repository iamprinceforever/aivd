"""Evaluator-side wire as a SEPARATE PROCESS. The pass process never loads the seal.

Listens on 127.0.0.1:<port>, injects the sealed note for a scenario when the transcript carries
its setup mark (aivd_rc3.wire.Wire), forwards to the pinned Ollama server and records every
wire request/response under the protected directory.
"""

import json
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from aivd_rc3.wire import Wire

OLLAMA = "http://127.0.0.1:11434/api/chat"


def ollama(request):
    call = urllib.request.Request(OLLAMA, data=json.dumps(request).encode(),
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def main(seal_path: str, wire_dir: str, port: int) -> None:
    seal = json.loads(Path(seal_path).read_text(encoding="utf-8"))
    wire = Wire(seal, ollama, Path(wire_dir))

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                status, raw = wire(json.loads(body))
            except Exception:
                status, raw = 502, b""
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)  # sequential: one request at a time
    server.serve_forever()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
