"""Closed. This design stage cannot dispatch a model call."""

from aivd_investigation.spec import EXECUTION_AUTHORIZED


class ExecutionRefused(Exception):
    pass


def dispatch(*_args, **_kwargs) -> None:
    if EXECUTION_AUTHORIZED:
        raise ExecutionRefused("investigation design does not authorize execution")
    raise ExecutionRefused("model dispatch is not part of the investigation design")
