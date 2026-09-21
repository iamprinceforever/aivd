"""Phase-2 ExperimentCondition factories (P2-R1-INSTR / P2-R1-MODEB-ODD)."""
from __future__ import annotations

from aivd.experiments.aivd340.condition import BH_BUDGET, ExperimentCondition, LOCKED_SEEDS
from aivd.experiments.aivd340.phase2_constants import (
    CONDITION_INSTR,
    CONDITION_MODEB,
    CONDITION_R1B_OPTIONAL,
    SEEDS,
)
from aivd37.unknowns.llama_340_phase2 import PLANT_P2_S, PLANT_P2_U

PLANT_P2 = (PLANT_P2_S, PLANT_P2_U)


def phase2_condition(condition_id: str) -> ExperimentCondition:
    """Locked BH48 × R1 conditions for Phase-2. Fresh P2 plants. allow_sacred=True."""
    cid = str(condition_id).strip()
    if cid == CONDITION_INSTR:
        return ExperimentCondition(
            condition_id=cid,
            budget_level="BH",
            representation="R1",
            episode_budget=BH_BUDGET,
            invention_mode="full_3_39_r1",
            plant_ids=PLANT_P2,
            seeds=tuple(SEEDS) if SEEDS else LOCKED_SEEDS,
            allow_sacred=True,
            notes="Phase-2 Mode A P2-R1-INSTR — observational instrumentation only",
            meta={
                "phase": 2,
                "mode": "A",
                "autonomous_discovery_credit": True,
                "controlled_availability": False,
            },
        )
    if cid == CONDITION_MODEB:
        return ExperimentCondition(
            condition_id=cid,
            budget_level="BH",
            representation="R1",
            episode_budget=BH_BUDGET,
            invention_mode="full_3_39_r1",
            plant_ids=PLANT_P2,
            seeds=tuple(SEEDS) if SEEDS else LOCKED_SEEDS,
            allow_sacred=True,
            notes="Phase-2 Mode B P2-R1-MODEB-ODD — CONTROLLED_INPUT odd-stride availability",
            meta={
                "phase": 2,
                "mode": "B",
                "autonomous_discovery_credit": False,
                "controlled_availability": True,
            },
        )
    if cid == CONDITION_R1B_OPTIONAL:
        # Optional continuity — not auto-launched by Phase-2 primary runner.
        return ExperimentCondition(
            condition_id=cid,
            budget_level="BH",
            representation="R1b",
            episode_budget=BH_BUDGET,
            invention_mode="full_3_39_r1b",
            plant_ids=PLANT_P2,
            seeds=tuple(SEEDS) if SEEDS else LOCKED_SEEDS,
            allow_sacred=True,
            notes="OPTIONAL P2-R1b-SACRED-AS-EXECUTED — historical-replication; NOT Commit-B identity",
            meta={
                "phase": 2,
                "mode": "A",
                "optional_continuity": True,
                "autonomous_discovery_credit": True,
                "controlled_availability": False,
                "commit_b_prereg_identity": False,
            },
        )
    raise ValueError(f"unknown Phase-2 condition_id: {condition_id}")


__all__ = ["phase2_condition", "PLANT_P2"]
