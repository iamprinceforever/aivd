"""One-run token for the end-goal budget. Default is closed."""

from contextlib import contextmanager
from secrets import token_hex

from aivd_endgame.spec import (
    EXPERIMENT,
    EXECUTION_AUTHORIZED,
    MAX_MODEL_CALLS,
    MODEL,
    MODEL_DIGEST,
    PREREGISTRATION_HASH,
    RUNTIME_DIGEST,
)

_LIVE = set()


class AuthorizationDenied(Exception):
    pass


class Authorization:
    def __init__(self, key: str):
        self._key = key
        self.experiment_id = EXPERIMENT
        self.valid = True

    def revoke(self) -> None:
        self.valid = False
        _LIVE.discard(self._key)


def capability_ok(authorization) -> bool:
    return (
        EXECUTION_AUTHORIZED is False
        and type(authorization) is Authorization
        and authorization.valid
        and authorization._key in _LIVE
        and authorization.experiment_id == EXPERIMENT
    )


def authorize_execution(*, explicit: bool, experiment_id: str, preregistration: str, model: str, model_digest: str, runtime_digest: str, max_calls: int, test_override: bool = False) -> Authorization:
    if EXECUTION_AUTHORIZED or not explicit or test_override:
        raise AuthorizationDenied("authorization refused")
    if experiment_id != EXPERIMENT or preregistration != PREREGISTRATION_HASH or not PREREGISTRATION_HASH:
        raise AuthorizationDenied("preregistration mismatch")
    if model != MODEL or model_digest != MODEL_DIGEST or runtime_digest != RUNTIME_DIGEST:
        raise AuthorizationDenied("model or runtime mismatch")
    if max_calls != MAX_MODEL_CALLS:
        raise AuthorizationDenied("budget mismatch")
    key = token_hex(16)
    issued = Authorization(key)
    _LIVE.add(key)
    return issued


@contextmanager
def production_session(**request):
    authorization = authorize_execution(**request)
    try:
        yield authorization
    finally:
        authorization.revoke()
