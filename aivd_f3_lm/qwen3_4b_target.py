"""Qwen3 4B target identity and memory admission. Does not load the model."""

import hashlib
import json

from aivd_f3_lm.qwen3_runtime import OLLAMA_EXECUTABLE_SHA256

F3_LM_EXECUTION_AUTHORIZED = False

OLLAMA_DIGEST = "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7"
MODEL_BLOB_SHA256 = "3e4cb14174460404e7a233e531675303b2fbf7749c02f91864fe311ab6344e4f"
MODEL_BLOB_SIZE = 2497280480
LOCAL_BYTE_COMMITMENT = "6b6b12104ea9d6d052a022d27f79d21961a412d6e25fe95347879bfa0eb5be45"
TEMPLATE_SHA256 = "2d54db2b9bb29ce7db54fea63a891f5859603813c555b1f88b5e0994652897f9"
GGUF_NAME = "Qwen3 4B Thinking 2507"
FILE_TYPE = 15
BLOCK_COUNT = 36
KV_HEADS = 8
HEAD_DIM = 80
NUM_CTX = 4096
NUM_PREDICT = 256
# Ollama 0.34.4 maps this template hash to thinking values [true] only.
THINKING_VALUES = (True,)
INTERFACE_CONTRACT_SHA256 = "ff87dbadee3b332d6a9ace66f08bee58c61698f0f51245783f5b3b53927d8e2c"
PUBLIC_BASELINE_SHA256 = "2dce1969c61b45204b3529e8b199005e5542e1a9a92f5a79b7d59174b1faa022"
OVERHEAD_BYTES = 512 * 1024 * 1024
SAFETY_FACTOR = 1.15

# Measured before any 4B load. The 8B result showed reported CPU buffers
# summed to about the artifact size, so weight load is estimated as the
# artifact size, not as a second copy.
HOST = {
    "mem_total_kib": 4024496,
    "mem_available_kib": 3752124,
    "mem_free_kib": 3810608,
    "swap_total_kib": 0,
    "gpu_vram_bytes": 0,
    "ollama_rss_bytes": 0,
    "llama_server_rss_bytes": 0,
    "concurrent_ollama": False,
}


def kv_bytes(num_ctx: int = NUM_CTX) -> int:
    return 2 * BLOCK_COUNT * KV_HEADS * HEAD_DIM * num_ctx * 2


def required_bytes(num_ctx: int = NUM_CTX) -> int:
    return MODEL_BLOB_SIZE + kv_bytes(num_ctx) + OVERHEAD_BYTES


def admission_reasons(env: dict) -> list:
    reasons = []
    if env.get("ollama_digest") != OLLAMA_DIGEST:
        reasons.append("wrong digest")
    if env.get("file_type") != FILE_TYPE or env.get("quantization") != "Q4_K_M":
        reasons.append("wrong quantization")
    if env.get("executable_sha256") != OLLAMA_EXECUTABLE_SHA256:
        reasons.append("wrong runtime")
    if env.get("local_byte_commitment") != LOCAL_BYTE_COMMITMENT:
        reasons.append("byte commitment mismatch")
    if env.get("num_ctx") != NUM_CTX:
        reasons.append("excessive num_ctx" if env.get("num_ctx", 0) > NUM_CTX else "num_ctx mismatch")
    if env.get("num_predict") != NUM_PREDICT or env.get("num_predict") == -1:
        reasons.append("excessive num_predict")
    if env.get("think_request") is not False or True not in THINKING_VALUES or False in THINKING_VALUES:
        reasons.append("thinking mode cannot be disabled")
    if False not in THINKING_VALUES:
        if "thinking mode cannot be disabled" not in reasons:
            reasons.append("thinking mode cannot be disabled")
    if env.get("network") is not False or env.get("tools") is not False:
        reasons.append("network or tools enabled")
    if env.get("concurrent_ollama") or env.get("duplicate_load"):
        reasons.append("concurrent or duplicate model load")
    if env.get("baseline_hash") != PUBLIC_BASELINE_SHA256:
        reasons.append("public baseline mismatch")
    if env.get("interface_contract_sha256") != INTERFACE_CONTRACT_SHA256:
        reasons.append("interface contract mismatch")
    available = int(env.get("mem_available_kib", 0)) * 1024
    needed = int(required_bytes(int(env.get("num_ctx") or NUM_CTX)) * SAFETY_FACTOR)
    if available < needed or env.get("swap_total_kib", 0) == 0 and available < required_bytes(NUM_CTX):
        reasons.append("insufficient RAM")
    if not F3_LM_EXECUTION_AUTHORIZED:
        reasons.append("execution not authorized")
    return reasons


def host_env() -> dict:
    return {
        "ollama_digest": OLLAMA_DIGEST,
        "file_type": FILE_TYPE,
        "quantization": "Q4_K_M",
        "executable_sha256": OLLAMA_EXECUTABLE_SHA256,
        "local_byte_commitment": LOCAL_BYTE_COMMITMENT,
        "num_ctx": NUM_CTX,
        "num_predict": NUM_PREDICT,
        "think_request": False,
        "network": False,
        "tools": False,
        "concurrent_ollama": False,
        "duplicate_load": False,
        "baseline_hash": PUBLIC_BASELINE_SHA256,
        "interface_contract_sha256": INTERFACE_CONTRACT_SHA256,
        **HOST,
    }


def manifest_document() -> dict:
    return {
        "tag": "qwen3:4b",
        "not_qwen3_8b": True,
        "gguf_name": GGUF_NAME,
        "ollama_digest": OLLAMA_DIGEST,
        "model_blob_sha256": MODEL_BLOB_SHA256,
        "model_blob_size": MODEL_BLOB_SIZE,
        "local_byte_commitment": LOCAL_BYTE_COMMITMENT,
        "template_sha256": TEMPLATE_SHA256,
        "thinking_values": ["true"],
        "think_request_required": False,
        "thinking_disable_possible": False,
        "num_ctx": NUM_CTX,
        "num_predict": NUM_PREDICT,
        "temperature": 0,
        "top_k": 1,
        "top_p": 1,
        "min_p": 0,
        "repeat_penalty": 1,
        "model_seed": 20260926,
        "discovery_seed": 748193,
        "executable_sha256": OLLAMA_EXECUTABLE_SHA256,
        "interface_contract_sha256": INTERFACE_CONTRACT_SHA256,
        "public_baseline_sha256": PUBLIC_BASELINE_SHA256,
        "host": HOST,
        "required_bytes": required_bytes(),
        "admission": "DENIED",
        "execution_authorized": False,
    }


def manifest_sha256() -> str:
    encoded = json.dumps(manifest_document(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class ExecutionRefused(Exception):
    pass


def guarded_generate(env: dict | None = None) -> None:
    reasons = admission_reasons(host_env() if env is None else env)
    raise ExecutionRefused("; ".join(reasons) if reasons else "no backend")
