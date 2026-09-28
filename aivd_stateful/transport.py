"""Chat request builder. The network transport is injected by the caller."""

import json

from aivd_stateful.contract import (
    MIN_P,
    MODEL,
    MODEL_SEED,
    NUM_CTX,
    NUM_PREDICT,
    REPEAT_PENALTY,
    TEMPERATURE,
    THINK,
    TOP_K,
    TOP_P,
)


def build_request(messages: list) -> dict:
    return {
        "model": MODEL,
        "messages": messages,
        "think": THINK,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "top_k": TOP_K,
            "top_p": TOP_P,
            "min_p": MIN_P,
            "repeat_penalty": REPEAT_PENALTY,
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
            "seed": MODEL_SEED,
        },
    }


def request_bytes(messages: list) -> bytes:
    return json.dumps(build_request(messages), sort_keys=True).encode()
