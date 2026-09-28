"""Fail-closed POST-RC3 authorization. Separate from AIVD-RC3.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
"""

from aivd_stateful.hashing import digest

from aivd_post_rc3 import EXPERIMENT_ID
from aivd_post_rc3.config import MODEL_ALLOCATION
from aivd_post_rc3.stop import halt

_OPEN = False


class AuthorizationRefused(Exception):
    pass


def plan_commitment(corpus_commitment: str, model_id: str, allocation: int = MODEL_ALLOCATION) -> str:
    return digest({
        "experiment_id": EXPERIMENT_ID,
        "model_id": model_id,
        "corpus_commitment": corpus_commitment,
        "allocation": allocation,
        "provider": "Groq",
    })


def authorize(*, explicit: bool, experiment_id: str, plan_hash: str,
              corpus_commitment: str, model_id: str, allocation: int) -> dict:
    if _OPEN or not explicit or experiment_id != EXPERIMENT_ID:
        raise AuthorizationRefused("authorization refused")
    if plan_hash != plan_commitment(corpus_commitment, model_id, allocation):
        raise AuthorizationRefused("plan commitment mismatch")
    return {"kind": EXPERIMENT_ID, "experiment_id": experiment_id, "plan_hash": plan_hash,
            "corpus_commitment": corpus_commitment, "allocation": allocation, "model_id": model_id}


def open_run(token: dict) -> None:
    global _OPEN
    if _OPEN or token.get("kind") != EXPERIMENT_ID:
        raise AuthorizationRefused("run refused")
    expected = plan_commitment(token.get("corpus_commitment", ""), token.get("model_id", ""),
                               token.get("allocation", -1))
    if token.get("plan_hash") != expected:
        raise AuthorizationRefused("run refused")
    _OPEN = True


def close_run() -> None:
    global _OPEN
    _OPEN = False


def run_open() -> bool:
    return _OPEN


def require_open() -> None:
    if not _OPEN:
        halt("AUTHORIZATION_FAILURE: POST-RC3 run is closed")
