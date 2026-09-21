"""ExperimentCondition — locked B×R cells that cannot silently mix."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

B32_BUDGET = 32
BH_BUDGET = 48  # preregistered; see reports/aivd_3_40_experiment_design.md

LOCKED_SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4, 7, 11)

FACTORIAL_CELLS: tuple[str, ...] = ("B32-R0", "B32-R1", "BH-R0", "BH-R1")

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


@dataclass(frozen=True)
class ExperimentCondition:
    """Single factorial or control condition — immutable per episode."""

    condition_id: str
    budget_level: str  # B32 | BH
    representation: str  # R0 | R1
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
        if self.representation not in ("R0", "R1"):
            raise ValueError(f"invalid representation: {self.representation}")
        expected = BH_BUDGET if self.budget_level == "BH" else B32_BUDGET
        if int(self.episode_budget) != expected:
            raise ValueError(
                f"episode_budget {self.episode_budget} != {expected} for {self.budget_level}"
            )
        if self.representation == "R1" and "_r1" not in self.invention_mode:
            raise ValueError("R1 requires invention_mode containing _r1")
        if self.representation == "R0" and "_r1" in self.invention_mode:
            raise ValueError("R0 must not use _r1 invention_mode")

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
    mode = "full_3_39_r1" if representation == "R1" else "full_3_39"
    if control == "NO-FIREWALL":
        mode += "_nofirewall"
    elif control == "NO-LANGUAGE-GROWTH":
        mode += "_nogrow"
    elif control == "NO-OPEN-SELECTION":
        mode += "_noopen"
    return mode


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
                # control alone defaults to B32-R0 base unless R1 implied
                core = "B32-R0"
            break

    if core not in FACTORIAL_CELLS and cid not in CONTROL_IDS:
        # Allow CONTROL attached to factorial: already peeled
        if core not in FACTORIAL_CELLS:
            raise ValueError(f"unknown condition_id: {condition_id}")

    budget_level, rep = core.split("-", 1)
    episode_budget = BH_BUDGET if budget_level == "BH" else B32_BUDGET
    representation = rep
    if control in ("NORMAL-R1",) or (control is None and representation == "R1"):
        pass
    if cid == "NORMAL-R1" or core.endswith("R1"):
        representation = "R1"
    if cid == "NORMAL-R0":
        representation = "R0"

    plants: tuple[str, ...] = (PLANT_S, PLANT_U)
    if control == "LEAKAGE-CANARY":
        plants = (PLANT_CANARY,)

    mode = _base_mode(representation, control if control not in ("NORMAL-R0", "NORMAL-R1") else None)
    return ExperimentCondition(
        condition_id=cid,
        budget_level=budget_level if core in FACTORIAL_CELLS else ("BH" if core.startswith("BH") else "B32"),
        representation=representation,
        episode_budget=episode_budget if core in FACTORIAL_CELLS else (
            BH_BUDGET if str(core).startswith("BH") else B32_BUDGET
        ),
        invention_mode=mode,
        plant_ids=plants,
        control=control,
        allow_sacred=False,
        notes="Step1+ framework; Sacred TinyLlama matrix not authorized",
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
    "CONTROL_IDS",
    "PLANT_S",
    "PLANT_U",
    "PLANT_CANARY",
    "ExperimentCondition",
    "condition_from_id",
    "locked_seeds",
    "all_factorial_conditions",
    "all_control_conditions",
]
