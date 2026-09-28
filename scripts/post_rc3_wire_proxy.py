"""POST-RC3 evaluator-side wire proxy as a SEPARATE PROCESS.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
Reuses the FROZEN aivd_rc3.wire.Wire to inject a scenario's sealed note (and the
source-swap value under condition B) only when the transcript carries its setup mark.
Forwards to Groq via the OpenAI-compatible adapter. Records every wire request/response
under the protected directory. Reads GROQ_API_KEY only from env; never logs it.

usage: post_rc3_wire_proxy.py <seal_path> <wire_dir> <port> <model_id>
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from aivd_rc3.wire import Wire

from aivd_post_rc3.groq_client import GroqTransportError, chat_completion
from aivd_post_rc3.models import MODELS


def make_inner(model_id: str):
    def inner(request: dict):
        # request is the OpenAI-shaped body already (built by PostRC3Session). Wire only
        # cares about request["messages"]; pass those to the model.
        state = {"attempts": 1}
        def on_attempt(entry):
            state["attempts"] = entry["attempt"]
        try:
            parsed, raw, attempts = chat_completion(model_id, request["messages"], on_attempt=on_attempt)
        except GroqTransportError as exc:
            inner.last_attempts = state["attempts"]
            return (exc.status or 502), b""
        inner.last_attempts = len(attempts)
        content = parsed["choices"][0]["message"]["content"]
        shaped = {"model": parsed.get("model", model_id),
                  "message": {"role": "assistant", "content": content},
                  "usage": parsed.get("usage") or {}}
        return 200, json.dumps(shaped).encode()
    inner.last_attempts = 1
    return inner


def main(seal_path: str, wire_dir: str, port: int, model_id: str) -> None:
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
            # propagate retry count to the session via a header
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
