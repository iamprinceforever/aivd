"""Qwen3 8B Ollama target identity. Does not load or run the model."""

import hashlib
import json
import platform

F3_LM_EXECUTION_AUTHORIZED = False

REPOSITORY = "library/qwen3"
TAG = "8b"
QUANTIZATION = "Q4_K_M"
GGUF_FILE_TYPE = 15
OLLAMA_DIGEST = "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41"
LOCAL_BYTE_COMMITMENT = "e56d3bf948b1809641c48913c2a86d25277580ce1983e8904a9a3d6b6220feb1"
TEMPLATE_SHA256 = "ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4"
MODEL_BLOB_SHA256 = "a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f"
MODEL_BLOB_SIZE = 5225374496
CONTEXT_LENGTH = 40960

RUNTIME_MANIFEST = {
    "target": "ollama-qwen3-8b-q4km",
    "not_llama_4_scout": True,
    "ollama_cli": "NOT_INSTALLED",
    "ollama_version": None,
    "acquisition": "registry.ollama.ai/v2/library/qwen3/manifests/8b",
    "auto_update": False,
    "auto_pull": False,
    "os": platform.platform(),
    "machine": platform.machine(),
    "gpu": None,
    "cuda": None,
    "context_length": CONTEXT_LENGTH,
    "num_ctx": None,
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "min_p": None,
    "repeat_penalty": 1.0,
    "stop": ["<|im_start|>", "<|im_end|>"],
    "seed_policy": "no seed in the published params blob",
    "thinking_mode": "not forced; template supports /think and /no_think only if IsThinkSet",
    "tools": False,
    "network_at_inference": False,
    "model_executed": False,
}


def runtime_hash() -> str:
    encoded = json.dumps(RUNTIME_MANIFEST, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class ExecutionRefused(Exception):
    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


class ExecutionIntegrityFailure(Exception):
    pass


def firewall_reasons(env: dict, baseline_hash: str) -> list:
    reasons = []
    if not F3_LM_EXECUTION_AUTHORIZED:
        reasons.append("F3_LM_EXECUTION_AUTHORIZED is false")
    if env.get("execution_lock") is not True:
        reasons.append("unauthorized model call")
    if env.get("ollama_digest") != OLLAMA_DIGEST:
        reasons.append("model digest mismatch")
    if env.get("local_byte_commitment") != LOCAL_BYTE_COMMITMENT:
        reasons.append("local byte commitment mismatch")
    if env.get("template_sha256") != TEMPLATE_SHA256:
        reasons.append("template mismatch")
    if env.get("runtime_hash") != runtime_hash():
        reasons.append("runtime mismatch")
    if env.get("auto_update") is not False or env.get("auto_pull") is not False:
        reasons.append("model update is not disabled")
    if env.get("baseline_frozen") is not True or env.get("baseline_hash") != baseline_hash:
        reasons.append("public-record baseline missing or mismatched")
    if env.get("tools") is not False or env.get("network_at_inference") is not False:
        reasons.append("tools or network are not disabled")
    return reasons


def guarded_generate(env: dict, baseline_hash: str) -> None:
    reasons = firewall_reasons(env, baseline_hash)
    if reasons:
        raise ExecutionRefused(reasons)
    raise ExecutionIntegrityFailure("Qwen3 execution is not linked")
