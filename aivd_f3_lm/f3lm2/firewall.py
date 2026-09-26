"""Execution gate. Closed until a later authorization."""

EXECUTION_AUTHORIZED = False


class ExecutionRefused(Exception):
    pass


def dispatch(trial: dict, caller) -> None:
    if not EXECUTION_AUTHORIZED:
        raise ExecutionRefused("F3-LM-2 execution is not authorized")
    raise ExecutionRefused("model dispatch is not implemented in this phase")
