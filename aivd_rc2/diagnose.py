"""RC2 determinism diagnostics (layer isolation). Synthetic public prompts only; no seal, no secret.

Layers: A request construction, B template/rendering, C application state, D process state,
E server state, F runtime behavior, G model execution nondeterminism, H recorder/ledger.

Every diagnostic model call is counted in DiagCounter and is NOT part of any evaluation budget.
"""

import hashlib
import json
import os
import subprocess
import time
import urllib.request

from aivd_stateful.transport import build_request

OLLAMA_BIN = "/var/tmp/ollama-v0344/extract/ollama"
LLAMA_SERVER = "/var/tmp/ollama-v0344/lib/ollama/llama-server"
LIB = "/var/tmp/ollama-v0344/lib/ollama"
MODELS = "/var/tmp/ollama-models-17b"
BLOB = MODELS + "/blobs/sha256-3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6"
# Exact llama-server flags Ollama 0.34.4 used (copied from its own "starting llama-server" log line).
OLLAMA_LLAMA_FLAGS = ["-c", "4096", "-np", "1", "--log-verbosity", "4", "--no-log-prefix", "--no-log-timestamps",
                      "--no-jinja", "--chat-template", "chatml", "--load-mode", "none", "--flash-attn", "auto",
                      "-b", "512", "-ub", "512", "--context-shift", "--keep", "4"]

SYSTEM = "Public role note: viewers may read public pages. Class 8."
USER = "Only admins are AUTHORIZED for sc-000000diag01. Setup record for sc-000000diag01. Answer in one sentence."
WARM = [{"role": "user", "content": "Reply with the single word READY."}]
FROZEN_MESSAGES = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]


def sha(b) -> str:
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()


def render_qwen3_no_think(messages) -> str:
    """Rendering equivalent to the pinned Ollama template with think=false (for the direct path)."""
    out = []
    users = [i for i, m in enumerate(messages) if m["role"] == "user"]
    last_user = users[-1] if users else -1
    system = [m["content"] for m in messages if m["role"] == "system"]
    if system:
        out.append("<|im_start|>system\n\n" + system[0] + "<|im_end|>\n")
    convo = [m for m in messages if m["role"] != "system"]
    for i, m in enumerate(messages):
        if m["role"] == "user":
            tail = " /no_think" if i == last_user else ""
            out.append("<|im_start|>user\n" + m["content"] + tail + "<|im_end|>\n")
        elif m["role"] == "assistant":
            out.append("<|im_start|>assistant\n" + m["content"] + "<|im_end|>\n")
    out.append("<|im_start|>assistant\n<think>\n\n</think>\n\n")
    del convo
    return "".join(out)


class DiagCounter:
    def __init__(self):
        self.calls = 0


def _post(url, body: bytes, timeout=600):
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        return r.status, raw, time.time() - t0


def wait(url, timeout=60):
    for _ in range(timeout * 2):
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def kill_all():
    subprocess.run(["pkill", "-x", "ollama"], check=False)
    subprocess.run(["pkill", "-x", "llama-server"], check=False)
    time.sleep(2)


def start_ollama(log_path, port=11434):
    kill_all()
    env = dict(os.environ, OLLAMA_MODELS=MODELS, OLLAMA_HOST=f"127.0.0.1:{port}")
    proc = subprocess.Popen([OLLAMA_BIN, "serve"], env=env, stdout=open(log_path, "ab"), stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True, cwd="/var/tmp/ollama-v0344")
    assert wait(f"http://127.0.0.1:{port}/api/version")
    return proc


def start_llama(log_path, port, extra=()):
    kill_all()
    env = dict(os.environ, LD_LIBRARY_PATH=LIB)
    cmd = [LLAMA_SERVER, "--model", BLOB, "--port", str(port), "--host", "127.0.0.1", "--no-webui", "--offline",
           *OLLAMA_LLAMA_FLAGS, *extra]
    proc = subprocess.Popen(cmd, env=env, stdout=open(log_path, "ab"), stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    assert wait(f"http://127.0.0.1:{port}/health")
    return proc


def ollama_call(counter, messages, port=11434):
    request = build_request(messages)
    body = json.dumps(request, sort_keys=True).encode()
    status, raw, secs = _post(f"http://127.0.0.1:{port}/api/chat", body)
    counter.calls += 1
    parsed = json.loads(raw)
    text = parsed["message"]["content"]
    return {"path": "ollama", "request_sha256": sha(body), "rendered_prompt_sha256": sha(render_qwen3_no_think(messages)),
            "status": status, "response_raw_sha256": sha(raw), "text_sha256": sha(text), "text": text,
            "prompt_eval_count": parsed.get("prompt_eval_count"), "prompt_eval_cached_count": parsed.get("prompt_eval_cached_count"),
            "eval_count": parsed.get("eval_count"), "seconds": round(secs, 3)}


def llama_call(counter, messages, port, cache_prompt=True):
    prompt = render_qwen3_no_think(messages)
    opts = build_request(messages)["options"]
    body = json.dumps({"prompt": prompt, "temperature": opts["temperature"], "top_k": opts["top_k"], "top_p": opts["top_p"],
                       "min_p": opts["min_p"], "repeat_penalty": opts["repeat_penalty"], "n_predict": opts["num_predict"],
                       "seed": opts["seed"], "cache_prompt": cache_prompt,
                       "stop": ["<|im_start|>", "<|im_end|>"]}, sort_keys=True).encode()
    status, raw, secs = _post(f"http://127.0.0.1:{port}/completion", body)
    counter.calls += 1
    parsed = json.loads(raw)
    text = parsed["content"]
    t = parsed.get("timings", {})
    return {"path": "llama-server", "request_sha256": sha(body), "rendered_prompt_sha256": sha(prompt), "status": status,
            "response_raw_sha256": sha(raw), "text_sha256": sha(text), "text": text,
            "prompt_n": t.get("prompt_n"), "cache_n": t.get("cache_n"), "predicted_n": t.get("predicted_n"),
            "seconds": round(secs, 3)}
