"""Memory for X1, X2, and X3. The frozen run itself is refused."""

from __future__ import annotations

from aivd.experiments.aivd40.stage_4_2.firewall import refuse_condition
from aivd.experiments.aivd40.stage_4_2.observation import BehavioralMemory, BehavioralSignature


def empty() -> BehavioralMemory:
    return BehavioralMemory()


def run_named(name: str) -> None:
    refuse_condition(name)


def fill(memory: BehavioralMemory, rows: list[tuple[BehavioralSignature, str, str]]) -> None:
    for signature, handle, language in rows:
        memory.add(signature, handle, language)
