"""TEST DOUBLE for the Ollama binary (`<copy> serve`). It is NOT Ollama: it never loads or runs a model.

It serves GET /api/version and a streaming POST /api/pull shaped like Ollama's documented pull stream
({"status": ...}, {"status": "pulling <id>", "digest", "total", "completed"}, ..., {"status": "success"}),
writing the blobs + manifest given in fixture.json (next to the copied script) into $OLLAMA_MODELS.
It records the environment KEYS it received (never values) into env_keys.json so tests can assert on them, and
refuses to run unless OLLAMA_NOPRUNE=1 and OLLAMA_HOST is a 127.0.0.1 address.
"""
import base64
import hashlib
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(sys.argv[0]).resolve().parent


def main():
    if sys.argv[1:] != ["serve"]:
        print("fake ollama: only `serve` is supported", file=sys.stderr)
        return 2
    env = os.environ
    (HERE / "env_keys.json").write_text(json.dumps(sorted(env.keys())))
    host = env.get("OLLAMA_HOST", "")
    if env.get("OLLAMA_NOPRUNE") != "1" or not host.startswith("127.0.0.1:"):
        print("fake ollama: refusing (OLLAMA_NOPRUNE must be 1 and OLLAMA_HOST must be loopback)", file=sys.stderr)
        return 3
    store = Path(env["OLLAMA_MODELS"])
    fixture = json.loads((HERE / "fixture.json").read_text())
    port = int(host.rsplit(":", 1)[1])

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path == "/api/version":
                b = json.dumps({"version": "0.0.0-fake"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)
            else:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()

        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n) or b"{}")
            name = req.get("name") or req.get("model")
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            def emit(obj):
                b = (json.dumps(obj) + "\n").encode()
                self.wfile.write(f"{len(b):x}\r\n".encode() + b + b"\r\n")
                self.wfile.flush()
            m = fixture["models"].get(name)
            emit({"status": "pulling manifest"})
            if m is None:
                emit({"error": f"pull model manifest: file does not exist"})
            else:
                delay, chunk = m.get("delay", 0.0), m.get("chunk", 1 << 20)
                (store / "blobs").mkdir(parents=True, exist_ok=True)
                for blob in m["blobs"]:
                    data = base64.b64decode(blob["b64"])
                    digest = "sha256:" + hashlib.sha256(data).hexdigest()
                    if m.get("tamper") and blob.get("model"):
                        data = data[::-1]
                    done = 0
                    while True:
                        emit({"status": f"pulling {digest[7:19]}", "digest": digest, "total": len(data),
                              "completed": done})
                        if done >= len(data):
                            break
                        done = min(len(data), done + chunk)
                        time.sleep(delay)
                    (store / "blobs" / digest.replace(":", "-")).write_bytes(data)
                if m.get("error_after_layers"):
                    emit({"error": m["error_after_layers"]})
                else:
                    emit({"status": "verifying sha256 digest"})
                    emit({"status": "writing manifest"})
                    model, tag = name.split(":")
                    mp = store / "manifests" / "registry.ollama.ai" / "library" / model / tag
                    mp.parent.mkdir(parents=True, exist_ok=True)
                    mp.write_text(m["manifest_text"])
                    emit({"status": "success"})
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()

    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
