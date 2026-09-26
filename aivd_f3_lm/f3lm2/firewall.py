"""Execution gate. Closed until a later authorization."""

EXECUTION_AUTHORIZED = False


class ExecutionRefused(Exception):
    pass


def dispatch(trial: dict, caller=None, **kwargs):
    if not EXECUTION_AUTHORIZED:
        raise ExecutionRefused("F3-LM-2 execution is not authorized")
    if caller is None:
        raise ExecutionRefused("model dispatch is not implemented in this phase")
    from aivd_f3_lm.f3lm2.bridge import execute_trial

    return execute_trial(trial, transport=caller, authorized=True, **kwargs)
