"""Pinned Ollama v0.34.4 inference contract. Does not call the model."""

import hashlib
import json
import platform
import random

from aivd_f3_lm.commitments import DESIGN_COMMIT
from aivd_f3_lm.qwen3_target import (
    LOCAL_BYTE_COMMITMENT,
    OLLAMA_DIGEST,
    TEMPLATE_SHA256,
)

F3_LM_EXECUTION_AUTHORIZED = False

OLLAMA_VERSION = "0.34.4"
OLLAMA_RELEASE_COMMIT = "b2da9e468af2479058ae18c6d908ed29de410684"
OLLAMA_EXECUTABLE_SHA256 = "ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4"
OLLAMA_ARCHIVE_SHA256 = "c238986e61d40c0cc5f4a9b9e40b9eea104350b77efa34741fc134e105cb9533"
PUBLIC_BASELINE_SHA256 = "8b7e2a597262ac4069e37e6a5de91c70ac2643bee972477155b052c99802c3e6"

# Request field think=false. Ollama v0.34.4 maps this exact template hash to
# boolean thinking whose default is true, so the field must be present.
# IsThinkSet is true only when the field is set. The frozen template then
# appends /no_think. Omitting think is not this contract.
THINKING = "DISABLED"
THINK_REQUEST = False

NUM_CTX = 8192
NUM_PREDICT = 256
TEMPERATURE = 0.0
TOP_K = 1
TOP_P = 1.0
MIN_P = 0.0
REPEAT_PENALTY = 1.0
MODEL_SEED = 20260926
DISCOVERY_SEED = 748193
STOP = ["<|im_start|>", "<|im_end|>"]

RUNTIME_MANIFEST = {
    "role": "f3_lm_1_inference_contract",
    "not_llama_4_scout": True,
    "ollama_version": OLLAMA_VERSION,
    "ollama_release_commit": OLLAMA_RELEASE_COMMIT,
    "ollama_executable_sha256": OLLAMA_EXECUTABLE_SHA256,
    "ollama_archive_sha256": OLLAMA_ARCHIVE_SHA256,
    "rejects_latest_tag": True,
    "os": platform.platform(),
    "architecture": platform.machine(),
    "cpu": "Intel(R) Xeon(R) Platinum 8481C CPU @ 2.70GHz",
    "cpu_count": 2,
    "gpu": None,
    "driver": None,
    "cuda": None,
    "model_digest": OLLAMA_DIGEST,
    "model_byte_commitment": LOCAL_BYTE_COMMITMENT,
    "template_sha256": TEMPLATE_SHA256,
    "thinking": THINKING,
    "think_request": THINK_REQUEST,
    "thinking_mechanism": "API think=false sets IsThinkSet and Think=false; frozen template appends /no_think",
    "temperature": TEMPERATURE,
    "top_k": TOP_K,
    "top_p": TOP_P,
    "min_p": MIN_P,
    "repeat_penalty": REPEAT_PENALTY,
    "num_ctx": NUM_CTX,
    "num_predict": NUM_PREDICT,
    "stop": STOP,
    "model_seed": MODEL_SEED,
    "discovery_seed": DISCOVERY_SEED,
    "network": False,
    "tools": False,
    "modelfile_created": False,
    "model_executed": False,
    "design_commit": DESIGN_COMMIT,
    "public_baseline_sha256": PUBLIC_BASELINE_SHA256,
    "temperature_semantics": "frozen as numeric 0; not proven deterministic until an authorized execution",
}


def runtime_manifest_hash() -> str:
    encoded = json.dumps(RUNTIME_MANIFEST, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class ExecutionRefused(Exception):
    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


class ExecutionIntegrityFailure(Exception):
    pass


def firewall_reasons(env: dict) -> list:
    reasons = []
    if not F3_LM_EXECUTION_AUTHORIZED:
        reasons.append("F3_LM_EXECUTION_AUTHORIZED is false")
    if env.get("execution_lock") is not True or env.get("experiment_authorized") is not True:
        reasons.append("experiment authorization is absent")
    if env.get("tag") == "latest" or env.get("ollama_version") == "latest":
        reasons.append("latest tags are rejected")
    if env.get("ollama_digest") != OLLAMA_DIGEST:
        reasons.append("model digest mismatch")
    if env.get("local_byte_commitment") != LOCAL_BYTE_COMMITMENT:
        reasons.append("model byte commitment mismatch")
    if env.get("ollama_version") != OLLAMA_VERSION:
        reasons.append("runtime version mismatch")
    if env.get("ollama_executable_sha256") != OLLAMA_EXECUTABLE_SHA256:
        reasons.append("runtime hash mismatch")
    if env.get("template_sha256") != TEMPLATE_SHA256:
        reasons.append("template mismatch")
    if env.get("thinking") != THINKING or env.get("think_request") is not False:
        reasons.append("thinking mode mismatch")
    if env.get("temperature") != TEMPERATURE:
        reasons.append("temperature mismatch")
    if env.get("top_k") != TOP_K:
        reasons.append("top_k mismatch")
    if env.get("top_p") != TOP_P:
        reasons.append("top_p mismatch")
    if env.get("num_ctx") != NUM_CTX:
        reasons.append("num_ctx mismatch")
    if env.get("num_predict") != NUM_PREDICT or env.get("num_predict") == -1:
        reasons.append("num_predict mismatch")
    if env.get("model_seed") != MODEL_SEED:
        reasons.append("seed mismatch")
    if env.get("network") is not False:
        reasons.append("network enabled")
    if env.get("tools") is not False:
        reasons.append("tools enabled")
    if env.get("baseline_hash") != PUBLIC_BASELINE_SHA256 or env.get("baseline_frozen") is not True:
        reasons.append("public-record baseline missing")
    if env.get("design_commit") != DESIGN_COMMIT:
        reasons.append("F3-LM design hash missing")
    if env.get("runtime_manifest_hash") != runtime_manifest_hash():
        reasons.append("runtime manifest hash mismatch")
    return reasons


def guarded_generate(env: dict) -> None:
    reasons = firewall_reasons(env)
    if reasons:
        raise ExecutionRefused(reasons)
    raise ExecutionIntegrityFailure("model execution is not linked")


class SeparatedRNG:
    """Discovery draws do not move the model seed, and the reverse is also true."""

    def __init__(self):
        self._discovery = random.Random(DISCOVERY_SEED)
        self.model_seed = MODEL_SEED

    def discovery_draw(self) -> int:
        return self._discovery.randrange(2**31)

    def model_seed_for_call(self) -> int:
        return self.model_seed
