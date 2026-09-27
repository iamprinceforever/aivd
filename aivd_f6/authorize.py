"""One-run authorization for the frozen F6 plan. It does not authorize F3-LM-2."""

import hashlib
import json
from contextlib import contextmanager
from secrets import token_hex

from aivd_f3_lm.qwen3_1_7b_target import OLLAMA_DIGEST
from aivd_f3_lm.qwen3_runtime import OLLAMA_EXECUTABLE_SHA256, OLLAMA_RELEASE_COMMIT, OLLAMA_VERSION
from aivd_f4.spec import MODEL
from aivd_f6 import firewall as firewall_gate
from aivd_f6.pairs import commitment
from aivd_f6.preregistration import preregistration_hash
from aivd_f6.spec import CONDITIONS, EXPERIMENT, FROZEN_INTERVENTION_HASH, MAX_CALLS, PAIRED_CALLS

EXPERIMENT_ID = EXPERIMENT
F6_PREREGISTRATION = "1cb07df37fe82d1924d19398b234587256169fc323ec629100c5310d096c81f9"
RUNTIME_VERSION = OLLAMA_VERSION
RUNTIME_COMMIT = OLLAMA_RELEASE_COMMIT
RUNTIME_DIGEST = OLLAMA_EXECUTABLE_SHA256
ALLOCATION = {"conditions": CONDITIONS, "paired_calls": PAIRED_CALLS, "max_calls": MAX_CALLS}

_LIVE = set()


class AuthorizationDenied(Exception):
    pass


class Authorization:
    def __init__(self, key: str, plan_hash: str, preregistration: str, intervention: str):
        self._key = key
        self.experiment_id = EXPERIMENT_ID
        self.plan_hash = plan_hash
        self.preregistration = preregistration
        self.intervention = intervention
        self.model = MODEL
        self.model_digest = OLLAMA_DIGEST
        self.runtime_version = RUNTIME_VERSION
        self.runtime_commit = RUNTIME_COMMIT
        self.runtime_digest = RUNTIME_DIGEST
        self.allocation = dict(ALLOCATION)
        self.valid = True

    def revoke(self) -> None:
        self.valid = False
        _LIVE.discard(self._key)


def execution_plan_commitment() -> str:
    body = {
        "experiment_id": EXPERIMENT_ID,
        "preregistration": F6_PREREGISTRATION,
        "intervention": FROZEN_INTERVENTION_HASH,
        "model": MODEL,
        "model_digest": OLLAMA_DIGEST,
        "runtime_version": RUNTIME_VERSION,
        "runtime_commit": RUNTIME_COMMIT,
        "runtime_digest": RUNTIME_DIGEST,
        "allocation": ALLOCATION,
    }
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def capability_ok(authorization) -> bool:
    from aivd_f6.pairs import commitment as live_intervention
    from aivd_f6.preregistration import preregistration_hash as live_preregistration

    return (
        firewall_gate.EXECUTION_AUTHORIZED is False
        and type(authorization) is Authorization
        and authorization.valid
        and authorization._key in _LIVE
        and authorization.experiment_id == EXPERIMENT_ID
        and authorization.plan_hash == execution_plan_commitment()
        and authorization.preregistration == live_preregistration() == F6_PREREGISTRATION
        and authorization.intervention == live_intervention() == FROZEN_INTERVENTION_HASH
        and authorization.model == MODEL
        and authorization.model_digest == OLLAMA_DIGEST
        and authorization.runtime_version == RUNTIME_VERSION
        and authorization.runtime_commit == RUNTIME_COMMIT
        and authorization.runtime_digest == RUNTIME_DIGEST
        and authorization.allocation == ALLOCATION
    )


def authorize_execution(
    *,
    explicit: bool,
    experiment_id: str,
    preregistration: str,
    intervention: str,
    model: str,
    model_digest: str,
    runtime_version: str,
    runtime_commit: str,
    runtime_digest: str,
    conditions: int,
    paired_calls: int,
    max_calls: int,
    test_override: bool = False,
) -> Authorization:
    if firewall_gate.EXECUTION_AUTHORIZED:
        raise AuthorizationDenied("the firewall flag must stay false")
    if not explicit or test_override:
        raise AuthorizationDenied("authorization must be an explicit production request")
    if experiment_id != EXPERIMENT_ID:
        raise AuthorizationDenied("experiment identifier mismatch")
    if preregistration != F6_PREREGISTRATION or preregistration_hash() != F6_PREREGISTRATION:
        raise AuthorizationDenied("preregistration mismatch")
    if intervention != FROZEN_INTERVENTION_HASH or commitment() != FROZEN_INTERVENTION_HASH:
        raise AuthorizationDenied("intervention-set mismatch")
    if model != MODEL:
        raise AuthorizationDenied("model identity mismatch")
    if model_digest != OLLAMA_DIGEST:
        raise AuthorizationDenied("model digest mismatch")
    if runtime_version != RUNTIME_VERSION or runtime_commit != RUNTIME_COMMIT:
        raise AuthorizationDenied("runtime identity mismatch")
    if runtime_digest != RUNTIME_DIGEST:
        raise AuthorizationDenied("runtime digest mismatch")
    if (conditions, paired_calls, max_calls) != (CONDITIONS, PAIRED_CALLS, MAX_CALLS):
        raise AuthorizationDenied("allocation mismatch")
    key = token_hex(16)
    issued = Authorization(key, execution_plan_commitment(), preregistration, intervention)
    _LIVE.add(key)
    return issued


@contextmanager
def production_session(**request):
    authorization = authorize_execution(**request)
    try:
        yield authorization
    finally:
        authorization.revoke()
