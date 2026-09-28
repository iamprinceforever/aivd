"""Closed gate. This design stage cannot dispatch a model call."""

from aivd_stateful.spec import EXECUTION_AUTHORIZED, MODEL_CALLS


class ExecutionRefused(Exception):
    pass


def dispatch(*_args, **_kwargs) -> None:
    if EXECUTION_AUTHORIZED or MODEL_CALLS:
        raise ExecutionRefused("stateful design does not authorize execution")
    raise ExecutionRefused("model dispatch is not part of the stateful design")
