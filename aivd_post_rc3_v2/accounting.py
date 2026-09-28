"""Stage accounting for POST-RC3-GROQ-V2.

Successful model calls and retry attempts consume the same stage budget unit:
Budget.charge increments turn_executions by one for the initial action and again
for every extra retry. They are counted separately and never change stage.

This module does not score candidates or call a model.
"""

STAGES = ("discovery", "investigation", "verification")

FAILURE_STATUS = {
    "discovery": "DISCOVERY_INFRASTRUCTURE_FAILURE",
    "investigation": "INVESTIGATION_INFRASTRUCTURE_FAILURE",
    "verification": "VERIFICATION_INFRASTRUCTURE_FAILURE",
}

BUDGET_POLICY = (
    "A successful model call and each retry attempt consume the same stage-budget unit. "
    "Budget.charge increments turn_executions by 1 for the initial action and by 1 for each "
    "extra retry. Successful responses, API attempts, and retries are counted separately. "
    "A retry cannot move a call into another stage."
)

RECORDING_FAILURE_STATUSES = frozenset({
    "transport_failed", "retry_budget", "not_persisted", "parse_failed", "turn_identity", "model_mismatch",
})


def empty_stage_calls() -> dict:
    return {stage: 0 for stage in STAGES}


def assign_successful(stage_calls: dict, successful_calls: int, stage: str) -> dict:
    """Attribute successes so far to the active stage. Never touches later stages."""
    if stage not in stage_calls:
        raise ValueError(f"unknown stage {stage}")
    accounted = sum(stage_calls.values())
    if successful_calls < accounted:
        raise ValueError("successful calls went backwards")
    stage_calls[stage] = successful_calls - accounted
    return stage_calls


def assert_invariants(ledger: dict) -> None:
    attempts = ledger["attempts"]
    seen = set()
    by_id = {}
    for attempt in attempts:
        if attempt["stage"] not in STAGES:
            raise AssertionError("call missing a single known stage")
        if attempt["attempt_id"] in seen:
            raise AssertionError("duplicate attempt id")
        seen.add(attempt["attempt_id"])
        by_id[attempt["attempt_id"]] = attempt
        if attempt["success"] and attempt["recording_status"] != "persisted":
            raise AssertionError("recording failure counted as a successful call")
        if attempt["recording_status"] in RECORDING_FAILURE_STATUSES and attempt["success"]:
            raise AssertionError("recording failure counted as a successful call")
        if attempt["success"] and not attempt["call_id"]:
            raise AssertionError("successful response missing call id")
    for attempt in attempts:
        if not attempt["retry_of"]:
            continue
        prior = by_id.get(attempt["retry_of"])
        if prior is None or prior["retry_of"]:
            raise AssertionError("retry must reference exactly one original attempt")
        if prior["stage"] != attempt["stage"] or prior["logical_call_id"] != attempt["logical_call_id"]:
            raise AssertionError("retry changed stage or logical call")
    logical = {}
    for attempt in attempts:
        logical.setdefault(attempt["logical_call_id"], []).append(attempt)
    for group in logical.values():
        if sum(1 for item in group if item["success"]) > 1:
            raise AssertionError("retry created a duplicate successful call")
        stages = {item["stage"] for item in group}
        if len(stages) != 1:
            raise AssertionError("attempts of one call span multiple stages")
    successful = [item for item in attempts if item["success"]]
    for stage in STAGES:
        got = sum(1 for item in successful if item["stage"] == stage)
        if ledger["stage_calls"][stage] != got:
            raise AssertionError(f"stage total mismatch for {stage}")
    if ledger["calls"] != sum(ledger["stage_calls"].values()) or ledger["calls"] != len(successful):
        raise AssertionError("total calls do not equal the sum of stage calls")
    if ledger["successful_responses"] != len(successful):
        raise AssertionError("successful responses mixed with attempts")
    if ledger["api_attempts"] != len(attempts):
        raise AssertionError("api attempts do not equal attempt records")
    retries = [item for item in attempts if item["retry_of"]]
    if ledger["retry_attempts"] != len(retries):
        raise AssertionError("retry count mismatch")
    failures = [item for item in attempts if item["recording_status"] in RECORDING_FAILURE_STATUSES]
    if ledger["recording_failures"] != len(failures):
        raise AssertionError("recording failure count mismatch")
    status = ledger["final_status"]
    if status.endswith("INFRASTRUCTURE_FAILURE"):
        stage = ledger["failure_stage"]
        if status != FAILURE_STATUS[stage] or ledger["failure_report"]["FAILURE_STAGE"] != stage:
            raise AssertionError("failure-path stage was not preserved")
        if stage in ledger["stages_completed"]:
            raise AssertionError("stopped stage claimed completed")
        order = list(STAGES)
        for later in order[order.index(stage) + 1:]:
            if ledger["stage_calls"][later] or later in ledger["stages_completed"]:
                raise AssertionError("stopped run claimed a later stage")
        if stage == "discovery" and ledger["discovery_completed"] is not False:
            raise AssertionError("unfinished discovery reported as completed")
    elif status == "COMPLETED":
        if ledger["failure_stage"] is not None:
            raise AssertionError("completed run has a failure stage")
        if ledger["stages_completed"] != list(STAGES):
            raise AssertionError("completed run missing a stage")
    else:
        raise AssertionError(f"unknown final status {status}")
