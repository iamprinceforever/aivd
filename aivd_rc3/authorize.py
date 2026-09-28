"""Fail-closed RC3 authorization, one open run at a time, bound to model+runtime+plan."""

from aivd_stateful.contract import MODEL, OLLAMA_DIGEST, OLLAMA_EXECUTABLE_SHA256
from aivd_stateful.hashing import digest

EXPERIMENT_ID = "AIVD-RC3"
_OPEN = False


class AuthorizationRefused(Exception):
    pass


def plan_commitment(corpus_commitment: str, allocation: int, pass_id: str) -> str:
    return digest(
        {
            "experiment_id": EXPERIMENT_ID,
            "pass_id": pass_id,
            "corpus_commitment": corpus_commitment,
            "model": MODEL,
            "model_digest": OLLAMA_DIGEST,
            "runtime_digest": OLLAMA_EXECUTABLE_SHA256,
            "allocation": allocation,
        }
    )


def authorize(*, explicit: bool, experiment_id: str, plan_hash: str, corpus_commitment: str,
              allocation: int, pass_id: str) -> dict:
    if _OPEN or not explicit or experiment_id != EXPERIMENT_ID:
        raise AuthorizationRefused("authorization refused")
    if plan_hash != plan_commitment(corpus_commitment, allocation, pass_id):
        raise AuthorizationRefused("plan commitment mismatch")
    return {"kind": EXPERIMENT_ID, "experiment_id": experiment_id, "plan_hash": plan_hash,
            "corpus_commitment": corpus_commitment, "allocation": allocation, "pass_id": pass_id}


def open_run(token: dict) -> None:
    global _OPEN
    if _OPEN or token.get("kind") != EXPERIMENT_ID:
        raise AuthorizationRefused("run refused")
    if token.get("plan_hash") != plan_commitment(
        token.get("corpus_commitment", ""), token.get("allocation", -1), token.get("pass_id", "")):
        raise AuthorizationRefused("run refused")
    _OPEN = True


def close_run() -> None:
    global _OPEN
    _OPEN = False


def run_open() -> bool:
    return _OPEN
