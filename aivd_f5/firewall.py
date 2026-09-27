"""F5 execution gate. Closed during design."""


class ExecutionRefused(Exception):
    pass


EXECUTION_AUTHORIZED = False


def dispatch(trial: dict, caller=None) -> None:
    if not EXECUTION_AUTHORIZED:
        raise ExecutionRefused("F5 execution is not authorized")
    raise ExecutionRefused("F5 model dispatch is not part of the design phase")
