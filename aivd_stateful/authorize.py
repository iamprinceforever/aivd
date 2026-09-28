"""One-run authorization for STATEFUL-1. Closed unless a bound token is inside a session."""

from aivd_stateful.contract import (
    DESIGN_COMMIT,
    EXPERIMENT_ID,
    HOLDOUT_CALLS,
    MODEL,
    OLLAMA_DIGEST,
    OLLAMA_EXECUTABLE_SHA256,
    SMOKE_CALLS,
)
from aivd_stateful.hashing import digest

_OPEN = False


class AuthorizationRefused(Exception):
    pass


def plan_commitment(corpus_commitment: str) -> str:
    return digest(
        {
            "experiment_id": EXPERIMENT_ID,
            "design_commit": DESIGN_COMMIT,
            "model": MODEL,
            "model_digest": OLLAMA_DIGEST,
            "runtime_digest": OLLAMA_EXECUTABLE_SHA256,
            "corpus_commitment": corpus_commitment,
            "smoke_calls": SMOKE_CALLS,
            "holdout_calls": HOLDOUT_CALLS,
        }
    )


def authorize_execution(*, explicit: bool, experiment_id: str, plan_hash: str, corpus_commitment: str):
    if _OPEN or not explicit or experiment_id != EXPERIMENT_ID:
        raise AuthorizationRefused("authorization refused")
    expected = plan_commitment(corpus_commitment)
    if plan_hash != expected:
        raise AuthorizationRefused("plan commitment mismatch")
    return {
        "experiment_id": experiment_id,
        "plan_hash": plan_hash,
        "corpus_commitment": corpus_commitment,
        "kind": "STATEFUL-1",
    }


def session_open() -> bool:
    return _OPEN


def open_session(token: dict) -> None:
    global _OPEN
    if _OPEN or token.get("kind") != "STATEFUL-1" or token.get("experiment_id") != EXPERIMENT_ID:
        raise AuthorizationRefused("session refused")
    if token.get("plan_hash") != plan_commitment(token.get("corpus_commitment", "")):
        raise AuthorizationRefused("session refused")
    _OPEN = True


def close_session() -> None:
    global _OPEN
    _OPEN = False
