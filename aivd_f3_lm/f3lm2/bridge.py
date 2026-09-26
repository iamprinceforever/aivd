"""Connect a frozen F3-LM-2 trial to the existing recorder. Does not authorize a run."""

import json
import urllib.request

from aivd_f3_lm.f3lm2.explore import plan_sha256
from aivd_f3_lm.f3lm2.firewall import ExecutionRefused
from aivd_f3_lm.f3lm2.semantics import assess
from aivd_f3_lm.qwen3_1_7b_target import (
    NUM_CTX,
    NUM_PREDICT,
    OLLAMA_DIGEST,
    REPEAT_PENALTY,
    TEMPERATURE,
    TOP_K,
    TOP_P,
    MIN_P,
)
from aivd_f3_lm.qwen3_runtime import OLLAMA_EXECUTABLE_SHA256, OLLAMA_VERSION
from aivd_f3_lm.recorder_1_2 import DuplicateTrial, PersistenceFailure, Recorder

FROZEN_PLAN_SHA256 = "ffd476d0597da77530442da9e282c72f125a0886f40787b0f6f5ef7b14e2dc51"
FROZEN_MODEL = "qwen3:1.7b"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


class PlanMismatch(Exception):
    pass


class ModelMismatch(Exception):
    pass


class DispatchFailure(Exception):
    pass


def build_request(trial: dict) -> dict:
    return {
        "model": FROZEN_MODEL,
        "messages": trial["messages"],
        "think": False,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "top_k": TOP_K,
            "top_p": TOP_P,
            "min_p": MIN_P,
            "repeat_penalty": REPEAT_PENALTY,
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
            "seed": trial["model_seed"],
        },
    }


def ollama_transport(request: dict) -> tuple[int, bytes]:
    payload = json.dumps(request).encode("utf-8")
    call = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(call, timeout=600) as response:
        return response.status, response.read()


def _identity(model_digest: str, runtime_sha: str) -> None:
    if model_digest != OLLAMA_DIGEST or runtime_sha != OLLAMA_EXECUTABLE_SHA256:
        raise ModelMismatch("model or runtime identity does not match the frozen target")
    if OLLAMA_VERSION != "0.34.4":
        raise ModelMismatch("runtime version does not match the frozen target")


def _record_failure(recorder: Recorder, trial_id: str, error: str) -> None:
    path = recorder.root / "failures" / f"{trial_id}.json"
    if path.exists():
        return
    payload = {"trial_id": trial_id, "status": "DISPATCH_FAILURE", "error": error, "raw_text": None}
    from aivd_f3_lm.recorder_1_2 import atomic_write

    atomic_write(path, json.dumps(payload).encode("utf-8"))


def execute_trial(
    trial: dict,
    *,
    authorized: bool,
    plan_hash: str,
    model_digest: str,
    runtime_sha: str,
    transport,
    recorder: Recorder,
    contract: dict | None = None,
    sequence: int = 1,
    authorization=None,
) -> dict:
    from aivd_f3_lm.f3lm2.authorize import capability_ok

    if not authorized or not capability_ok(authorization):
        raise ExecutionRefused("F3-LM-2 execution is not authorized")
    if plan_hash != FROZEN_PLAN_SHA256 or plan_sha256() != FROZEN_PLAN_SHA256:
        raise PlanMismatch("plan hash does not match the frozen F3-LM-2 plan")
    _identity(model_digest, runtime_sha)
    trial_id = trial["trial_id"]
    if recorder.is_executed(trial_id):
        raise DuplicateTrial("RECOVERY_REQUIRED")
    request = build_request(trial)
    request_hash = __import__("hashlib").sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()

    def call():
        try:
            status, raw = transport(request)
        except Exception as exc:
            _record_failure(recorder, trial_id, type(exc).__name__)
            raise DispatchFailure("model dispatch failed") from exc
        if not isinstance(raw, (bytes, bytearray)):
            _record_failure(recorder, trial_id, "missing raw response")
            raise DispatchFailure("model dispatch returned no raw response")
        return int(status), bytes(raw)

    try:
        status, raw = recorder.submit(trial_id, request_hash, sequence, call)
    except DuplicateTrial:
        raise
    except DispatchFailure:
        raise
    except Exception as exc:
        _record_failure(recorder, trial_id, type(exc).__name__)
        raise DispatchFailure("model dispatch failed") from exc
    try:
        meta = {
            "request_id": request_hash,
            "model_digest": model_digest,
            "runtime_manifest_hash": runtime_sha,
            "experiment_authorization_hash": plan_hash,
        }
        observation = recorder.process(trial_id, status, raw, meta)
    except PersistenceFailure:
        _record_failure(recorder, trial_id, "PersistenceFailure")
        raise
    text = (observation.get("response_text") or {}).get("value") or ""
    assessment = assess(contract, text) if contract is not None else None
    return {
        "trial_id": trial_id,
        "response_sha256": observation["raw_response_hash"]["value"],
        "observation": observation,
        "assessment": assessment,
    }
