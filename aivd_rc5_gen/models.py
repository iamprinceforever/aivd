"""Frozen model / runtime / template identity for AIVD-RC5-GENERALIZATION-V1 (no additions, no removals).

Values re-read from the local Ollama store on disk (2026-09-29 IST) and identical to RC4's pins.
`verify_identity` is a FILESYSTEM check only (manifest bytes, layer blobs, runtime binary); it sends
no Ollama request and cannot load a model.
"""

import hashlib
import json
from pathlib import Path

from aivd_post_rc3_local.models import MANIFEST_DIGESTS, MODEL_DIRS, MODELS, RUNTIME, THINKING_MODELS

assert MODELS == ("qwen3:1.7b", "llama3.2:3b", "qwen3:8b")

FAMILY = {"qwen3:1.7b": "qwen3", "llama3.2:3b": "llama3.2", "qwen3:8b": "qwen3"}
MODEL_FAMILIES = ("qwen3", "llama3.2")

# Per-model frozen identity: Ollama manifest sha256, config blob, GGUF weights blob (the GGUF carries
# the tokenizer vocabulary/merges, so the weights digest also pins the tokenizer), chat-template blob
# (template identity), params blob (model-level default options; request options override
# temperature/top_p/seed/num_ctx/num_predict).
IDENTITY = {
    "qwen3:1.7b": {
        "manifest_sha256": "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7",
        "config_sha256": "517ccaff02fe9f99718ab2f478e611aa2813c36263eeed86c2427bc122d14ad8",
        "model_blob_sha256": "3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6",
        "template_sha256": "ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4",
        "params_sha256": "cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb",
        "model_family": "qwen3", "model_type": "2.0B", "file_type": "Q4_K_M",
    },
    "llama3.2:3b": {
        "manifest_sha256": "a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72",
        "config_sha256": "34bb5ab01051a11372a91f95f3fbbc51173eed8e7f13ec395b9ae9b8bd0e242b",
        "model_blob_sha256": "dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff",
        "template_sha256": "966de95ca8a62200913e3f8bfbf84c8494536f1b94b49166851e76644e966396",
        "params_sha256": "56bb8bd477a519ffa694fc449c2413c6f0e1d3b1c88fa7e3c9d88d3ae49d4dcb",
        "model_family": "llama", "model_type": "3.2B", "file_type": "Q4_K_M",
    },
    "qwen3:8b": {
        "manifest_sha256": "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41",
        "config_sha256": "05a61d37b08453e59290add468e3bb2f688e23a01e967fecb0e2fa41218cea76",
        "model_blob_sha256": "a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f",
        "template_sha256": "ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4",
        "params_sha256": "cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb",
        "model_family": "qwen3", "model_type": "8.2B", "file_type": "Q4_K_M",
    },
}
assert {m: v["manifest_sha256"] for m, v in IDENTITY.items()} == MANIFEST_DIGESTS

RUNTIME_IDENTITY = {
    "engine": RUNTIME["engine"], "version": RUNTIME["version"],       # Ollama 0.34.4
    "binary_path": RUNTIME["binary_path"], "binary_sha256": RUNTIME["binary_sha256"],
    "models_dir": RUNTIME["models_dir"], "base_url": RUNTIME["base_url"], "chat_path": RUNTIME["chat_path"],
    "remote_api": RUNTIME["remote_api"], "OLLAMA_MAX_LOADED_MODELS": 1, "OLLAMA_NUM_PARALLEL": 1,
}
assert RUNTIME_IDENTITY["binary_sha256"] == "ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4"

_MEDIA = {"application/vnd.ollama.image.model": "model_blob_sha256",
          "application/vnd.ollama.image.template": "template_sha256",
          "application/vnd.ollama.image.params": "params_sha256"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_path(model_id: str, models_dir: str) -> Path:
    name, tag = model_id.split(":")
    return Path(models_dir) / "manifests" / "registry.ollama.ai" / "library" / name / tag


def verify_identity(model_id: str, models_dir: str = RUNTIME["models_dir"], *, blobs: bool = False) -> dict:
    """Compare on-disk manifest / config / template / params digests with the frozen identity.
    With blobs=True every layer blob (incl. the multi-GB weights) is re-hashed as well."""
    if model_id not in MODELS:
        raise ValueError(f"unexpected model {model_id!r}")
    want = IDENTITY[model_id]
    raw = manifest_path(model_id, models_dir).read_bytes()
    manifest = json.loads(raw)
    got = {"manifest_sha256": hashlib.sha256(raw).hexdigest(),
           "config_sha256": manifest["config"]["digest"].split(":", 1)[1]}
    for layer in manifest["layers"]:
        key = _MEDIA.get(layer["mediaType"])
        if key:
            got[key] = layer["digest"].split(":", 1)[1]
    blob_dir = Path(models_dir) / "blobs"
    cfg = json.loads((blob_dir / ("sha256-" + got["config_sha256"])).read_bytes())
    got.update({"model_family": cfg.get("model_family"), "model_type": cfg.get("model_type"),
                "file_type": cfg.get("file_type")})
    out = {"model_id": model_id, "fields_ok": all(got.get(k) == v for k, v in want.items())}
    small = [got["config_sha256"], got["template_sha256"], got["params_sha256"]]
    out["small_blobs_ok"] = all(_sha256_file(blob_dir / ("sha256-" + d)) == d for d in small)
    if blobs:
        layers = [manifest["config"]] + list(manifest["layers"])
        out["blobs_ok"] = all(_sha256_file(blob_dir / ("sha256-" + l["digest"].split(":", 1)[1]))
                              == l["digest"].split(":", 1)[1] for l in layers)
    out["ok"] = out["fields_ok"] and out["small_blobs_ok"] and out.get("blobs_ok", True)
    return out


def verify_runtime(binary_path: str = RUNTIME["binary_path"]) -> dict:
    sha = _sha256_file(Path(binary_path))
    return {"binary_sha256": sha, "ok": sha == RUNTIME_IDENTITY["binary_sha256"]}


__all__ = ["MODELS", "MODEL_DIRS", "THINKING_MODELS", "FAMILY", "IDENTITY", "RUNTIME_IDENTITY",
           "verify_identity", "verify_runtime"]
