"""Pinned runtime values for STATEFUL-1. Does not call a model."""

from aivd_f3_lm.qwen3_1_7b_target import (
    MIN_P,
    NUM_CTX,
    NUM_PREDICT,
    OLLAMA_DIGEST,
    REPEAT_PENALTY,
    TEMPERATURE,
    TOP_K,
    TOP_P,
)
from aivd_f3_lm.qwen3_runtime import MODEL_SEED, OLLAMA_EXECUTABLE_SHA256, OLLAMA_VERSION

EXPERIMENT_ID = "STATEFUL-1"
MODEL = "qwen3:1.7b"
THINK = False
SMOKE_CALLS = 8
HOLDOUT_CALLS = 20
DESIGN_COMMIT = "d7ea887ee76727e39c42b224ec491e78d6eee915"

__all__ = [
    "DESIGN_COMMIT",
    "EXPERIMENT_ID",
    "HOLDOUT_CALLS",
    "MIN_P",
    "MODEL",
    "MODEL_SEED",
    "NUM_CTX",
    "NUM_PREDICT",
    "OLLAMA_DIGEST",
    "OLLAMA_EXECUTABLE_SHA256",
    "OLLAMA_VERSION",
    "REPEAT_PENALTY",
    "SMOKE_CALLS",
    "TEMPERATURE",
    "THINK",
    "TOP_K",
    "TOP_P",
]
