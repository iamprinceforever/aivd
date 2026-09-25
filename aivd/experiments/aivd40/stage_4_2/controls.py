"""Public control expectations. They do not run the frozen programs."""

from __future__ import annotations

EXPECTED = {
    "C1": "same",
    "C2": "distinct",
    "C3": "same",
    "C4": "same",
    "C5": "none",
    "C6": "none",
}


class StopExperiment(RuntimeError):
    pass


def judge(control: str, observed: str) -> None:
    if observed != EXPECTED[control]:
        raise StopExperiment(control)
