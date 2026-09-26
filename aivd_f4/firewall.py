"""F4 execution gate. Closed during design."""

EXECUTION_AUTHORIZED = False


class ExecutionRefused(Exception):
    pass


def dispatch(trial: dict, caller=None) -> None:
    if not EXECUTION_AUTHORIZED:
        raise ExecutionRefused("F4 execution is not authorized")
    raise ExecutionRefused("F4 model dispatch is not part of the design phase")
