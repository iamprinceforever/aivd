"""Explicit production authorization for the frozen F3-LM-2 plan. Default is closed."""

from contextlib import contextmanager
from secrets import token_hex

from aivd_f3_lm.f3lm2 import firewall as firewall_gate
from aivd_f3_lm.f3lm2.bridge import FROZEN_MODEL, FROZEN_PLAN_SHA256
from aivd_f3_lm.f3lm2.explore import build_plan, plan_sha256
from aivd_f3_lm.qwen3_1_7b_target import OLLAMA_DIGEST

_LIVE = set()


class AuthorizationDenied(Exception):
    pass


class Authorization:
    def __init__(self, key: str, plan_hash: str, model_digest: str):
        self._key = key
        self.plan_hash = plan_hash
        self.model_digest = model_digest
        self.valid = True

    def revoke(self) -> None:
        self.valid = False
        _LIVE.discard(self._key)


def capability_ok(authorization) -> bool:
    return (
        type(authorization) is Authorization
        and authorization.valid
        and authorization._key in _LIVE
        and authorization.plan_hash == FROZEN_PLAN_SHA256
        and authorization.model_digest == OLLAMA_DIGEST
    )


def authorize_execution(
    *,
    explicit: bool,
    plan_hash: str,
    model: str,
    model_digest: str,
    baseline: int,
    mutations: int,
    total: int,
    test_override: bool = False,
) -> Authorization:
    if firewall_gate.EXECUTION_AUTHORIZED:
        raise AuthorizationDenied("the firewall flag must stay false")
    if not explicit or test_override:
        raise AuthorizationDenied("authorization must be an explicit production request")
    if plan_hash != FROZEN_PLAN_SHA256 or plan_sha256() != FROZEN_PLAN_SHA256:
        raise AuthorizationDenied("plan hash mismatch")
    if model != FROZEN_MODEL or model_digest != OLLAMA_DIGEST:
        raise AuthorizationDenied("model identity mismatch")
    if (baseline, mutations, total) != (64, 192, 256):
        raise AuthorizationDenied("trial allocation mismatch")
    plan = build_plan()
    base = sum(item["kind"] == "baseline" for item in plan)
    changed = sum(item["kind"] == "mutation" for item in plan)
    if (base, changed, len(plan)) != (64, 192, 256):
        raise AuthorizationDenied("live plan allocation mismatch")
    key = token_hex(16)
    issued = Authorization(key, plan_hash, model_digest)
    _LIVE.add(key)
    return issued


@contextmanager
def production_session(**request):
    authorization = authorize_execution(**request)
    try:
        yield authorization
    finally:
        authorization.revoke()
