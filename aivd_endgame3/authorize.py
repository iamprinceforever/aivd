"""Fail-closed ENDGAME-3 authorization. It does not open an older experiment gate."""

from aivd_stateful.contract import MODEL, OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from aivd_stateful.hashing import digest

from aivd_endgame3.spec import (
    ALLOCATION,
    DESIGN_SHA256,
    EXPERIMENT_ID,
    PREREGISTRATION_SHA256,
)

_OPEN = False


class AuthorizationRefused(Exception):
    pass


def plan_commitment(corpus_commitment: str) -> str:
    return digest(
        {
            "experiment_id": EXPERIMENT_ID,
            "design_sha256": DESIGN_SHA256,
            "preregistration_sha256": PREREGISTRATION_SHA256,
            "corpus_commitment": corpus_commitment,
            "model": MODEL,
            "model_digest": OLLAMA_DIGEST,
            "runtime_digest": OLLAMA_EXECUTABLE_SHA256,
            "allocation": ALLOCATION,
        }
    )


def authorize(*, explicit: bool, experiment_id: str, plan_hash: str, corpus_commitment: str) -> dict:
    if _OPEN or not explicit or experiment_id != EXPERIMENT_ID:
        raise AuthorizationRefused("authorization refused")
    if plan_hash != plan_commitment(corpus_commitment):
        raise AuthorizationRefused("plan commitment mismatch")
    return {
        "kind": EXPERIMENT_ID,
        "experiment_id": experiment_id,
        "plan_hash": plan_hash,
        "corpus_commitment": corpus_commitment,
    }


def open_run(token: dict) -> None:
    global _OPEN
    if _OPEN or token.get("kind") != EXPERIMENT_ID:
        raise AuthorizationRefused("run refused")
    if token.get("plan_hash") != plan_commitment(token.get("corpus_commitment", "")):
        raise AuthorizationRefused("run refused")
    _OPEN = True


def close_run() -> None:
    global _OPEN
    _OPEN = False


def run_open() -> bool:
    return _OPEN
