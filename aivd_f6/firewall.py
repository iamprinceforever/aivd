"""F6 execution gate. A firewall flag does not grant a call."""


class ExecutionRefused(Exception):
    pass


EXECUTION_AUTHORIZED = False
MODEL_CALLS = 0


def dispatch(trial: dict, caller=None, authorization=None):
    from aivd_f6.authorize import capability_ok

    if not capability_ok(authorization):
        raise ExecutionRefused("F6 execution is not authorized")
    if caller is None:
        raise ExecutionRefused("F6 transport is not attached")
    return caller(trial)
