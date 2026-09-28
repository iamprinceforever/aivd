"""STATEFUL-SMOKE-1. Structural proof of multi-turn state, not a security test."""

import json

from aivd_stateful.model import Config, create, replay
from aivd_stateful.contract import MODEL_SEED

SETUP = "The badge code is PLUM-8831. Reply with READY."
PROBE = "What is the badge code? Reply with only the code."
NOTE_A = "The note says elm. Reply with READY."
NOTE_B = "The note says yew. Reply with READY."
WHICH = "Which note was given? Reply with one word."


def run_smoke(session) -> dict:
    config = Config(model="qwen3:1.7b", seed=MODEL_SEED, runtime="ollama-0.34.4")
    root = create("smoke", config)
    session.budget.note_creation()
    first = session.execute(root, SETUP, "continue", "smoke memory setup")
    second = session.execute(first, PROBE, "continue", "smoke memory probe")
    cleared = session.execute(root, PROBE, "reset", "smoke reset probe")
    branch_a = session.execute(root, NOTE_A, "branch", "smoke branch A setup")
    probe_a = session.execute(branch_a, WHICH, "continue", "smoke branch A probe")
    branch_b = session.execute(root, NOTE_B, "branch", "smoke branch B setup")
    probe_b = session.execute(branch_b, WHICH, "continue", "smoke branch B probe")
    for item in (second, cleared, probe_a, probe_b):
        replay(item)
    requests = {record["call_id"]: (session.raw / f"{record['call_id']}.req").read_bytes() for record in session.records}
    second_request = json.loads(requests[session.records[1]["call_id"]])
    reset_request = json.loads(requests[session.records[2]["call_id"]])
    branch_a_request = json.loads(requests[session.records[4]["call_id"]])
    branch_b_request = json.loads(requests[session.records[6]["call_id"]])
    checks = {
        "multiturn": len(second.turns) == 2 and second.turns[1].parent_turn_id == second.turns[0].turn_id,
        "continuation_has_history": len(second_request["messages"]) == 3 and first.turns[0].output in second_request["messages"][1]["content"],
        "reset_has_no_history": len(reset_request["messages"]) == 1 and first.turns[0].output not in reset_request["messages"][0]["content"],
        "state_before_differs": second.turns[1].state_before_hash != cleared.turns[0].state_before_hash,
        "root_unchanged": root.turns == (),
        "branch_a_isolated": NOTE_B not in json.dumps(branch_a_request) and NOTE_A in json.dumps(branch_a_request),
        "branch_b_isolated": NOTE_A not in json.dumps(branch_b_request) and NOTE_B in json.dumps(branch_b_request),
        "replay": True,
    }
    checks["pass"] = all(checks.values())
    return {"checks": checks, "calls": session.calls, "outputs": [turn.output for turn in second.turns]}
