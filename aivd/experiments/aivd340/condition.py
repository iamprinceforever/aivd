"""ExperimentCondition — locked B×R cells that cannot silently mix."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

B32_BUDGET = 32
BH_BUDGET = 48  # preregistered; see reports/aivd_3_40_experiment_design.md

LOCKED_SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 7, 11)

FACTORIAL_CELLS: tuple[str, ...] = ("B32-R0", "B32-R1", "BH-R0", "BH-R1")
STAGE2_CELLS: tuple[str, ...] = ("BH-R1", "BH-R1b")

CONTROL_IDS: tuple[str, ...] = (
    "NORMAL-R0",
    "NORMAL-R1",
    "NO-FIREWALL",
    "NO-LANGUAGE-GROWTH",
    "NO-OPEN-SELECTION",
    "LEAKAGE-CANARY",
    "BEHAVIORAL-EQUIVALENCE",
    "TEXTUAL-DIFFERENCE",
)

PLANT_S = "AIVD340-LLAMA-ODDSTRIDE"
PLANT_U = "AIVD340-LLAMA-ROL1"
PLANT_CANARY = "AIVD340-LLAMA-CANARY"
PLANT_S2_S = "AIVD340-S2-S"
PLANT_S2_U = "AIVD340-S2-U"


@dataclass(frozen=True)
class ExperimentCondition:
    """Single factorial or control condition — immutable per episode."""

    condition_id: str
    budget_level: str  # B32 | BH
    representation: str  # R0 | R1 | R1b
    episode_budget: int
    invention_mode: str
    plant_ids: tuple[str, ...] = (PLANT_S, PLANT_U)
    seeds: tuple[int, ...] = LOCKED_SEEDS
    control: str | None = None
    allow_sacred: bool = False  # Step 1+: always False for TinyLlama matrix
    notes: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.budget_level not in ("B32", "BH"):
            raise ValueError(f"invalid budget_level: {self.budget_level}")
        if self.representation not in ("R0", "R1", "R1b"):
            raise ValueError(f"invalid representation: {self.representation}")
        expected = BH_BUDGET if self.budget_level == "BH" else B32_BUDGET
        if int(self.episode_budget) != expected:
            raise ValueError(
                f"episode_budget {self.episode_budget} != {expected} for {self.budget_level}"
            )
        mode = self.invention_mode
        if self.representation == "R1b":
            if "_r1b" not in mode:
                raise ValueError("R1b requires invention_mode containing _r1b")
        elif self.representation == "R1":
            if "_r1" not in mode or "_r1b" in mode:
                raise ValueError("R1 requires invention_mode containing _r1 (not _r1b)")
        elif self.representation == "R0":
            if "_r1" in mode:
                raise ValueError("R0 must not use _r1 / _r1b invention_mode")

    @property
    def mode(self) -> str:
        return self.invention_mode

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["plant_ids"] = list(self.plant_ids)
        d["seeds"] = list(self.seeds)
        return d


def locked_seeds() -> tuple[int, ...]:
    return LOCKED_SEEDS


def _base_mode(representation: str, control: str | None) -> str:
    if representation == "R1b":
        mode = "full_3_39_r1b"
    elif representation == "R1":
        mode = "full_3_39_r1"
    else:
        mode = "full_3_39"
    if control == "NO-FIREWALL":
        mode += "_nofirewall"
    elif control == "NO-LANGUAGE-GROWTH":
        mode += "_nogrow"
    elif control == "NO-OPEN-SELECTION":
        mode += "_noopen"
    return mode


def _parse_rep(core: str) -> str:
    if core.endswith("R1b") or core.endswith("-R1b"):
        return "R1b"
    if core.endswith("R1") or core.endswith("-R1"):
        return "R1"
    return "R0"


def condition_from_id(condition_id: str) -> ExperimentCondition:
    """Parse a factorial or control condition id into a locked ExperimentCondition."""
    cid = str(condition_id).strip()
    control: str | None = None
    core = cid
    for c in CONTROL_IDS:
        suffix = f"-{c}"
        if cid.endswith(suffix) and c not in ("NORMAL-R0", "NORMAL-R1"):
            control = c
            core = cid[: -len(suffix)]
            break
        if cid == c:
            control = c
            if c == "NORMAL-R0":
                core = "B32-R0"
            elif c == "NORMAL-R1":
                core = "B32-R1"
            else:
                core = "B32-R0"
            break

    known = set(FACTORIAL_CELLS) | set(STAGE2_CELLS)
    if core not in known and cid not in CONTROL_IDS:
        if core not in known:
            raise ValueError(f"unknown condition_id: {condition_id}")

    if "-" not in core:
        raise ValueError(f"unknown condition_id: {condition_id}")
    budget_level, _rep_raw = core.split("-", 1)
    representation = _parse_rep(core)
    episode_budget = BH_BUDGET if budget_level == "BH" else B32_BUDGET

    if cid == "NORMAL-R1" or (core.endswith("R1") and not core.endswith("R1b")):
        representation = "R1"
    elif cid == "NORMAL-R0":
        representation = "R0"

    plants: tuple[str, ...] = (PLANT_S, PLANT_U)
    if control == "LEAKAGE-CANARY":
        plants = (PLANT_CANARY,)

    mode = _base_mode(
        representation,
        control if control not in ("NORMAL-R0", "NORMAL-R1") else None,
    )
    return ExperimentCondition(
        condition_id=cid,
        budget_level=budget_level if core in known else ("BH" if core.startswith("BH") else "B32"),
        representation=representation,
        episode_budget=episode_budget if core in known else (
            BH_BUDGET if str(core).startswith("BH") else B32_BUDGET
        ),
        invention_mode=mode,
        plant_ids=plants,
        control=control,
        allow_sacred=False,
        notes="3.40 condition framework (Stage-1 factorial + Stage-2 R1b cells)",
    )


def stage2_condition(condition_id: str, *, plants: tuple[str, ...] | None = None) -> ExperimentCondition:
    """Stage-2 BH-R1 / BH-R1b with optional fresh plant IDs."""
    base = condition_from_id(condition_id)
    if condition_id not in STAGE2_CELLS:
        raise ValueError(f"not a Stage-2 cell: {condition_id}")
    pids = plants or (PLANT_S2_S, PLANT_S2_U)
    return ExperimentCondition(
        condition_id=base.condition_id,
        budget_level=base.budget_level,
        representation=base.representation,
        episode_budget=base.episode_budget,
        invention_mode=base.invention_mode,
        plant_ids=pids,
        seeds=base.seeds,
        control=base.control,
        allow_sacred=True,
        notes="Stage-2 Sacred BH48 × R1/R1b",
        meta={"stage": 2},
    )


def all_factorial_conditions() -> list[ExperimentCondition]:
    return [condition_from_id(c) for c in FACTORIAL_CELLS]


def all_control_conditions() -> list[ExperimentCondition]:
    out: list[ExperimentCondition] = []
    for c in CONTROL_IDS:
        out.append(condition_from_id(c))
    return out


__all__ = [
    "B32_BUDGET",
    "BH_BUDGET",
    "LOCKED_SEEDS",
    "FACTORIAL_CELLS",
    "STAGE2_CELLS",
    "CONTROL_IDS",
    "PLANT_S",
    "PLANT_U",
    "PLANT_CANARY",
    "PLANT_S2_S",
    "PLANT_S2_U",
    "ExperimentCondition",
    "condition_from_id",
    "stage2_condition",
    "locked_seeds",
    "all_factorial_conditions",
    "all_control_conditions",
]
