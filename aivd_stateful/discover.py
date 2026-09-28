"""Generic trajectory policy. It does not know behavioral labels."""

from aivd_stateful.contract import MODEL_SEED
from aivd_stateful.model import BudgetExhausted, Config, candidate_from, create, replay, signature


def run(public: list, session, config: Config | None = None) -> dict:
    config = config or Config(model="qwen3:1.7b", seed=MODEL_SEED, runtime="ollama-0.34.4")
    decisions = []
    retained = []
    rejected = []
    verified = []
    trajectories = []

    def choose(action: str, reason: str, trajectory_id: str) -> None:
        decisions.append(
            {
                "action": action,
                "reason": reason,
                "trajectory_id": trajectory_id,
                "budget_remaining": session.budget.limit - session.budget.turn_executions,
            }
        )

    for scenario in public:
        if session.budget.turn_executions >= session.budget.limit:
            choose("stop", "BUDGET_EXHAUSTED", "")
            break
        root = create(scenario["scenario_id"], config)
        session.budget.note_creation()
        trajectories.append(root)
        try:
            if "variants" in scenario:
                prefixes = []
                probes = []
                for variant in scenario["variants"]:
                    choose("branch", "a declared prefix is still unexplored", root.trajectory_id)
                    opened = session.execute(root, variant, "branch", "a declared prefix is still unexplored")
                    prefixes.append(opened)
                    choose("continue", "the shared follow-up is applied to this prefix", opened.trajectory_id)
                    probed = session.execute(opened, scenario["probe"], "continue", "the shared follow-up is applied to this prefix")
                    probes.append(probed)
                    trajectories.append(probed)
                    replay(probed)
                if probes[0].turns[-1].output_hash != probes[1].turns[-1].output_hash:
                    found = candidate_from(probes[0])
                    found["contrast_trajectory_id"] = probes[1].trajectory_id
                    found["scenario_id"] = scenario["scenario_id"]
                    found["preserved_output"] = probes[0].turns[-1].output
                    found["contrast_output"] = probes[1].turns[-1].output
                    found["signature"] = list(signature(probes[0]))
                    retained.append(found)
                    choose("verify", "repeat the first prefix because the probes differed", prefixes[0].trajectory_id)
                    repeated = session.execute(prefixes[0], scenario["probe"], "verify", "repeat the preserved probe")
                    replay(repeated)
                    trajectories.append(repeated)
                    if repeated.turns[-1].output_hash == probes[0].turns[-1].output_hash:
                        verified.append(found["candidate_id"])
                else:
                    rejected.append(scenario["scenario_id"])
            else:
                choose("start", "the scenario has no trajectory yet", root.trajectory_id)
                first = session.execute(root, scenario["steps"][0], "continue", "open the trajectory")
                choose("continue", "a follow-up exists and history is open", first.trajectory_id)
                second = session.execute(first, scenario["steps"][1], "continue", "a follow-up exists and history is open")
                choose("reset", "the same follow-up is run without inherited history", root.trajectory_id)
                cleared = session.execute(root, scenario["steps"][1], "reset", "the same follow-up is run without inherited history")
                replay(second)
                replay(cleared)
                trajectories.extend((second, cleared))
                if second.turns[-1].output_hash != cleared.turns[-1].output_hash and len(signature(second)) >= 2:
                    found = candidate_from(second)
                    found["contrast_trajectory_id"] = cleared.trajectory_id
                    found["scenario_id"] = scenario["scenario_id"]
                    found["preserved_output"] = second.turns[-1].output
                    found["contrast_output"] = cleared.turns[-1].output
                    found["signature"] = list(signature(second))
                    retained.append(found)
                    choose("verify", "repeat the preserved follow-up", first.trajectory_id)
                    repeated = session.execute(first, scenario["steps"][1], "verify", "repeat the preserved follow-up")
                    replay(repeated)
                    trajectories.append(repeated)
                    if repeated.turns[-1].output_hash == second.turns[-1].output_hash:
                        verified.append(found["candidate_id"])
                else:
                    rejected.append(scenario["scenario_id"])
        except BudgetExhausted:
            choose("stop", "BUDGET_EXHAUSTED", root.trajectory_id)
            break
    else:
        choose("stop", "FRONTIER_EMPTY", "")
    return {
        "decisions": decisions,
        "retained": retained,
        "rejected": rejected,
        "verified": verified,
        "trajectory_count": len(trajectories),
    }
