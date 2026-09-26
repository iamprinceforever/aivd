"""Exploration plan. It does not rank contracts by an expected failure."""

import hashlib

from aivd_f3_lm.grammar import OPERATORS

from aivd_f3_lm.f3lm2.contracts import DISCOVERY_SEED, MODEL_SEED, TRIAL_BUDGET
from aivd_f3_lm.f3lm2.generate import generate_contracts
from aivd_f3_lm.f3lm2.prompts import InvalidTrial, base_messages, mutate_messages


def _params(operator: str) -> tuple:
    if operator in ("REPEAT", "SERIALIZE", "FORMAT"):
        return (1, 2)
    return (0,)


def build_plan() -> list:
    plan = []
    contracts = generate_contracts()
    for contract in contracts:
        branch = "B" if contract["type"] == "STATE" else "A"
        plan.append(
            {
                "trial_id": contract["contract_id"] + "-base",
                "contract_id": contract["contract_id"],
                "operator": None,
                "messages": base_messages(contract, branch),
                "model_seed": MODEL_SEED,
                "kind": "baseline",
            }
        )
        ranked = sorted(
            OPERATORS,
            key=lambda name: hashlib.sha256(f"{DISCOVERY_SEED}|{contract['contract_id']}|{name}".encode()).hexdigest(),
        )
        chosen = 0
        for operator in ranked:
            for param in _params(operator):
                try:
                    messages = mutate_messages(contract, operator, param, branch)
                except InvalidTrial:
                    continue
                plan.append(
                    {
                        "trial_id": f"{contract['contract_id']}-{operator}-{param}",
                        "contract_id": contract["contract_id"],
                        "operator": operator,
                        "messages": messages,
                        "model_seed": MODEL_SEED,
                        "kind": "mutation",
                    }
                )
                chosen += 1
                break
            if chosen == 3:
                break
        if chosen != 3:
            raise RuntimeError("contract did not receive three non-vacuous mutations")
    if len(plan) != TRIAL_BUDGET:
        raise RuntimeError(f"plan size {len(plan)} != {TRIAL_BUDGET}")
    if any(item["kind"] == "PIPELINE_CONTROL" for item in plan):
        raise RuntimeError("positive control entered the exploration plan")
    return plan


def plan_sha256() -> str:
    ids = [item["trial_id"] for item in build_plan()]
    return hashlib.sha256(("\n".join(ids) + f"|{DISCOVERY_SEED}").encode()).hexdigest()
