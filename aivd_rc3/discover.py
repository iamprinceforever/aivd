"""Generic stateful discovery for RC3. It knows NO behavioral label and NO seal.

Per scenario:
  two-step scenarios: open -> continue (history kept) and the same follow-up after a reset
  (history removed). A behavioral candidate is retained when the two outputs differ.
  branch scenarios: two declared prefixes, each continued with the shared follow-up. A
  candidate is retained when the branch outputs differ.

Retained candidates carry trajectory-level evidence forward (both outputs, turn ids, the
state-hash signature, the contrast trajectory, the branch id). Investigation slots are
declared from PUBLIC text only:
  prior_slot       a discovery output contains a token-like span absent from public text;
  auth_slot        public text declares an authorization state (AUTHORIZED/DENIED/REVOKED);
  transition_slot  a two-step scenario whose follow-up differs from its opening (every
                   continuation is a state transition that CF-F can hold fixed).
The frozen END-GOAL-3 policy also ran a behavioral repeat inside discovery; RC1 removes that
duplicate (the verification stage repeats independently), which frees discovery budget.
"""

from aivd_stateful.contract import MODEL_SEED
from aivd_stateful.model import BudgetExhausted, Config, candidate_from, create, replay, signature

from aivd_rc3.labeler import novel_spans

AUTH_WORDS = ("AUTHORIZED", "DENIED", "REVOKED")


def public_blob(scenario: dict) -> str:
    parts = list(scenario.get("steps") or []) + list(scenario.get("variants") or [])
    if scenario.get("probe"):
        parts.append(scenario["probe"])
    return "\n".join(parts)


def slots(scenario: dict, preserved: str, contrast: str) -> dict:
    blob = public_blob(scenario)
    steps = scenario.get("steps") or []
    return {
        "prior_slot": bool(novel_spans(preserved, blob) or novel_spans(contrast, blob)),
        "auth_slot": any(word in blob for word in AUTH_WORDS),
        "transition_slot": len(steps) >= 2 and steps[0] != steps[1],
    }


def order(public: list, discovery_seed: int) -> list:
    """Pass-specific exploration order. Scenarios never share history, so order is a
    scheduling choice only; it matters when the discovery budget runs out."""
    import random

    items = list(public)
    random.Random(discovery_seed).shuffle(items)
    return items


def run(public: list, session, config: Config | None = None, *, namespace: str = "", discovery_seed: int | None = None) -> dict:
    config = config or Config(model="qwen3:1.7b", seed=MODEL_SEED, runtime="ollama-0.34.4")
    if discovery_seed is not None:
        public = order(public, discovery_seed)
    decisions, retained, rejected, trajectories = [], [], [], []
    explored = []

    def choose(action, reason, tid):
        decisions.append({"action": action, "reason": reason, "trajectory_id": tid,
                          "budget_remaining": session.budget.limit - session.budget.turn_executions})

    stop = "FRONTIER_EMPTY"
    for scenario in public:
        if session.budget.turn_executions >= session.budget.limit:
            stop = "BUDGET_EXHAUSTED"
            break
        root = create(namespace + scenario["scenario_id"], config)
        session.budget.note_creation()
        try:
            if "variants" in scenario:
                probes = []
                for variant in scenario["variants"]:
                    choose("branch", "a declared prefix is still unexplored", root.trajectory_id)
                    opened = session.execute(root, variant, "branch", "a declared prefix is still unexplored")
                    choose("continue", "the shared follow-up is applied to this prefix", opened.trajectory_id)
                    probed = session.execute(opened, scenario["probe"], "continue", "the shared follow-up is applied to this prefix")
                    replay(probed)
                    probes.append(probed)
                trajectories.extend(probes)
                preserved, contrast = probes[0], probes[1]
                extra = {"branch_id": probes[1].trajectory_id}
            else:
                choose("start", "the scenario has no trajectory yet", root.trajectory_id)
                first = session.execute(root, scenario["steps"][0], "continue", "open the trajectory")
                choose("continue", "a follow-up exists and history is open", first.trajectory_id)
                preserved = session.execute(first, scenario["steps"][1], "continue", "a follow-up exists and history is open")
                choose("reset", "the same follow-up is run without inherited history", root.trajectory_id)
                contrast = session.execute(root, scenario["steps"][1], "reset", "the same follow-up is run without inherited history")
                replay(preserved)
                replay(contrast)
                trajectories.extend((preserved, contrast))
                extra = {}
        except BudgetExhausted:
            choose("stop", "BUDGET_EXHAUSTED", root.trajectory_id)
            stop = "BUDGET_EXHAUSTED"
            break
        explored.append(scenario["scenario_id"])
        p_out, c_out = preserved.turns[-1].output, contrast.turns[-1].output
        if preserved.turns[-1].output_hash != contrast.turns[-1].output_hash and len(signature(preserved)) >= 2:
            found = candidate_from(preserved)
            found.update({
                "contrast_trajectory_id": contrast.trajectory_id,
                "scenario_id": scenario["scenario_id"],
                "preserved_output": p_out,
                "setup_output": preserved.turns[0].output if len(preserved.turns) >= 2 else "",
                "contrast_output": c_out,
                "signature": list(signature(preserved)),
                "state_hash": preserved.state_hash(),
                "contrast_state_hash": contrast.state_hash(),
            })
            found.update(extra)
            found.update(slots(scenario, p_out, c_out))
            retained.append(found)
            choose("retain", "preserved and contrast outputs differ", preserved.trajectory_id)
        else:
            rejected.append(scenario["scenario_id"])
            choose("reject", "no behavioral difference", preserved.trajectory_id)
    choose("stop", stop, "")
    ids = [c["candidate_id"] for c in retained]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate candidate id")
    return {"decisions": decisions, "retained": retained, "rejected": rejected, "explored": explored,
            "trajectory_count": len(trajectories), "stop": stop}
