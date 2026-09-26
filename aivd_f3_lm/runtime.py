"""Frozen future runtime description. Nothing here loads a model."""

import hashlib
import json
import platform
import sys

GENERATION_CONFIG = {
    "do_sample": False,
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": None,
    "max_new_tokens": 256,
    "repetition_penalty": 1.0,
    "stop": ["<|eot|>"],
    "seed_policy": "sampling disabled; no seed is consumed",
}

RUNTIME_MANIFEST = {
    "role": "freeze_authoring_host_not_inference_host",
    "primary_backend": "transformers",
    "backend_installed": False,
    "backend_executed": False,
    "python": sys.version.split()[0],
    "os": platform.platform(),
    "cuda": None,
    "driver": None,
    "gpu": None,
    "torch": None,
    "transformers": None,
    "dtype": "bfloat16",
    "quantization": "NONE",
    "attention_implementation": "frozen-as-upstream-default-no-override",
    "deterministic": True,
    "automatic_quantization": False,
    "automatic_dtype_change": False,
    "generation": GENERATION_CONFIG,
    "nondeterminism": "MoE routing on the future inference host is unmeasured because the model was not loaded. Sampling is frozen off. Reproduction rule remains N>=3 if a later authorized host is not bit-exact.",
}


def runtime_hash() -> str:
    encoded = json.dumps(RUNTIME_MANIFEST, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
