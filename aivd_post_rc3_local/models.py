"""Exact local model IDs and Ollama manifest digests for POST-RC3-LOCAL-V1. No substitution.

Reading manifests/blobs is a filesystem check only; it makes no Ollama request.
"""

import hashlib
import json
from pathlib import Path

MODELS = ("qwen3:1.7b", "llama3.2:3b", "qwen3:8b")

MANIFEST_DIGESTS = {
    "qwen3:1.7b": "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7",
    "llama3.2:3b": "a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72",
    "qwen3:8b": "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41",
}

MODEL_DIRS = {"qwen3:1.7b": "qwen3_1_7b", "llama3.2:3b": "llama3_2_3b", "qwen3:8b": "qwen3_8b"}

# Qwen3 exposes a thinking switch; llama3.2 does not (see config.PER_MODEL_OMISSIONS).
THINKING_MODELS = frozenset({"qwen3:1.7b", "qwen3:8b"})

RUNTIME = {
    "provider": "LOCAL",
    "remote_api": "NONE",
    "engine": "Ollama",
    "version": "0.34.4",
    "binary_path": "/var/tmp/ollama-v0344/extract/ollama",
    "binary_sha256": "ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4",
    "models_dir": "/var/tmp/ollama-models-17b",
    "base_url": "http://127.0.0.1:11434",
    "chat_path": "/api/chat",
}


def manifest_path(model_id: str, models_dir: str = RUNTIME["models_dir"]) -> Path:
    name, tag = model_id.split(":")
    return Path(models_dir) / "manifests" / "registry.ollama.ai" / "library" / name / tag


def verify_model(model_id: str, models_dir: str = RUNTIME["models_dir"], *, blobs: bool = True) -> dict:
    """Re-read the manifest, compare its sha256 to the pin, optionally re-hash every layer blob."""
    if model_id not in MODELS:
        raise ValueError(f"unexpected model {model_id!r}")
    raw = manifest_path(model_id, models_dir).read_bytes()
    out = {"model_id": model_id, "manifest_sha256": hashlib.sha256(raw).hexdigest()}
    out["manifest_ok"] = out["manifest_sha256"] == MANIFEST_DIGESTS[model_id]
    if blobs:
        manifest = json.loads(raw)
        layers = [manifest["config"]] + list(manifest["layers"])
        checks = []
        for layer in layers:
            want = layer["digest"].split(":", 1)[1]
            path = Path(models_dir) / "blobs" / ("sha256-" + want)
            h = hashlib.sha256()
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 22), b""):
                    h.update(chunk)
            checks.append({"digest": want, "size": path.stat().st_size, "ok": h.hexdigest() == want
                           and path.stat().st_size == layer["size"]})
        out["blobs"] = checks
        out["blobs_ok"] = all(c["ok"] for c in checks)
    return out
