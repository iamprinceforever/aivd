"""F6 execution gate. Closed during design."""


class ExecutionRefused(Exception):
    pass


EXECUTION_AUTHORIZED = False
MODEL_CALLS = 0


def dispatch(trial: dict, caller=None) -> None:
    if not EXECUTION_AUTHORIZED:
        raise ExecutionRefused("F6 execution is not authorized")
    raise ExecutionRefused("F6 model dispatch is not part of the design phase")
