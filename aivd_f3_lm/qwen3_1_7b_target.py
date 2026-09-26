"""Qwen3 1.7B target identity. Does not load the model."""

import hashlib
import json

from aivd_f3_lm.interface_1_1 import contract_sha256
from aivd_f3_lm.qwen3_runtime import OLLAMA_EXECUTABLE_SHA256, OLLAMA_VERSION

F3_LM_EXECUTION_AUTHORIZED = False

OLLAMA_DIGEST = "8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7"
MODEL_BLOB_SHA256 = "3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6"
MODEL_BLOB_SIZE = 1359279776
LOCAL_BYTE_COMMITMENT = "1c2e6a06ba5ea1724c42ab5b9566fba3b4fb64dd0a1fdc03d3cf721bdec1dd0f"
TEMPLATE_SHA256 = "ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4"
GGUF_NAME = "Qwen3 1.7B"
FILE_TYPE = 15
BLOCK_COUNT = 28
KV_HEADS = 8
HEAD_DIM = 128
NUM_CTX = 4096
NUM_PREDICT = 256
TEMPERATURE = 0.0
TOP_K = 1
TOP_P = 1.0
MIN_P = 0.0
REPEAT_PENALTY = 1.0
PUBLIC_BASELINE_SHA256 = "1af2fd6e6ef0f15c7fa120e7d8cd4bdbe209a9ea342aac5ae1725273b785653e"
OVERHEAD_BYTES = 512 * 1024 * 1024
SAFETY_FACTOR = 1.15
# This template hash is the Ollama 0.34.4 boolean control: false and true,
# default true. think:false must be sent so the template appends /no_think.
THINKING_VALUES = (False, True)

HOST = {
    "mem_total_kib": 4024496,
    "mem_available_kib": 3667560,
    "mem_free_kib": 1265340,
    "swap_total_kib": 0,
    "gpu_vram_bytes": 0,
    "ollama_rss_bytes": 0,
    "llama_server_rss_bytes": 0,
}


def kv_bytes(num_ctx: int = NUM_CTX) -> int:
    return 2 * BLOCK_COUNT * KV_HEADS * HEAD_DIM * num_ctx * 2


def required_bytes(num_ctx: int = NUM_CTX) -> int:
    return MODEL_BLOB_SIZE + kv_bytes(num_ctx) + OVERHEAD_BYTES


def admission_reasons(env: dict) -> list:
    reasons = []
    if env.get("ollama_digest") != OLLAMA_DIGEST:
        reasons.append("digest mismatch")
    if env.get("local_byte_commitment") != LOCAL_BYTE_COMMITMENT:
        reasons.append("byte commitment mismatch")
    if env.get("ollama_version") != OLLAMA_VERSION or env.get("executable_sha256") != OLLAMA_EXECUTABLE_SHA256:
        reasons.append("runtime mismatch")
    if env.get("template_sha256") != TEMPLATE_SHA256:
        reasons.append("template mismatch")
    if env.get("think_request") is not False or False not in THINKING_VALUES:
        reasons.append("thinking mode mismatch")
    if env.get("file_type") != FILE_TYPE:
        reasons.append("quantization mismatch")
    ctx = int(env.get("num_ctx") or 0)
    if ctx != NUM_CTX:
        reasons.append("context mismatch")
    if env.get("num_predict") != NUM_PREDICT:
        reasons.append("output limit mismatch")
    if (
        env.get("temperature") != TEMPERATURE
        or env.get("top_k") != TOP_K
        or env.get("top_p") != TOP_P
        or env.get("min_p") != MIN_P
        or env.get("repeat_penalty") != REPEAT_PENALTY
        or env.get("model_seed") != 20260926
    ):
        reasons.append("sampling mismatch")
    if env.get("baseline_hash") != PUBLIC_BASELINE_SHA256 or env.get("baseline_present") is not True:
        reasons.append("public baseline missing")
    if env.get("interface_contract_sha256") != contract_sha256():
        reasons.append("interface contract mismatch")
    if env.get("network") is not False or env.get("tools") is not False:
        reasons.append("network or tools enabled")
    available = int(env.get("mem_available_kib", 0)) * 1024
    needed = int(required_bytes(ctx or NUM_CTX) * SAFETY_FACTOR)
    if available < needed:
        reasons.append("insufficient memory")
    if not F3_LM_EXECUTION_AUTHORIZED:
        reasons.append("execution not authorized")
    return reasons


def host_env() -> dict:
    return {
        "ollama_digest": OLLAMA_DIGEST,
        "local_byte_commitment": LOCAL_BYTE_COMMITMENT,
        "ollama_version": OLLAMA_VERSION,
        "executable_sha256": OLLAMA_EXECUTABLE_SHA256,
        "template_sha256": TEMPLATE_SHA256,
        "think_request": False,
        "file_type": FILE_TYPE,
        "num_ctx": NUM_CTX,
        "num_predict": NUM_PREDICT,
        "temperature": TEMPERATURE,
        "top_k": TOP_K,
        "top_p": TOP_P,
        "min_p": MIN_P,
        "repeat_penalty": REPEAT_PENALTY,
        "model_seed": 20260926,
        "baseline_hash": PUBLIC_BASELINE_SHA256,
        "baseline_present": True,
        "interface_contract_sha256": contract_sha256(),
        "network": False,
        "tools": False,
        **HOST,
    }


def memory_admitted(env: dict | None = None) -> bool:
    env = host_env() if env is None else env
    return "insufficient memory" not in admission_reasons(env)


def manifest_document() -> dict:
    return {
        "tag": "qwen3:1.7b",
        "gguf_name": GGUF_NAME,
        "not_qwen3_4b": True,
        "not_qwen3_8b": True,
        "ollama_digest": OLLAMA_DIGEST,
        "model_blob_sha256": MODEL_BLOB_SHA256,
        "model_blob_size": MODEL_BLOB_SIZE,
        "local_byte_commitment": LOCAL_BYTE_COMMITMENT,
        "template_sha256": TEMPLATE_SHA256,
        "thinking": "DISABLED",
        "think_mechanism": "API think=false sets IsThinkSet; this template appends /no_think",
        "thinking_disable_possible": False in THINKING_VALUES,
        "num_ctx": NUM_CTX,
        "num_predict": NUM_PREDICT,
        "temperature": TEMPERATURE,
        "top_k": TOP_K,
        "top_p": TOP_P,
        "min_p": MIN_P,
        "repeat_penalty": REPEAT_PENALTY,
        "model_seed": 20260926,
        "discovery_seed": 748193,
        "executable_sha256": OLLAMA_EXECUTABLE_SHA256,
        "ollama_version": OLLAMA_VERSION,
        "interface_contract_sha256": contract_sha256(),
        "public_baseline_sha256": PUBLIC_BASELINE_SHA256,
        "host": HOST,
        "required_bytes": required_bytes(),
        "memory_preflight": "PASS" if memory_admitted() else "DENIED",
        "execution_authorized": False,
        "model_loaded": False,
    }


def manifest_sha256() -> str:
    encoded = json.dumps(manifest_document(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class ExecutionRefused(Exception):
    pass


def guarded_generate(env: dict | None = None) -> None:
    reasons = admission_reasons(host_env() if env is None else env)
    raise ExecutionRefused("; ".join(reasons) if reasons else "no backend")
