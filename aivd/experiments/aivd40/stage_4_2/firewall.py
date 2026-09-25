"""Stops the frozen experiment from running during implementation."""

from __future__ import annotations

from aivd.experiments.aivd40.stage_4_2.freeze import FROZEN_CEL, MICRO_SEED


class ExperimentUnauthorized(RuntimeError):
    pass


def refuse_frozen_cel(expression: str) -> None:
    if expression in FROZEN_CEL:
        raise ExperimentUnauthorized("frozen CEL sample is not authorized")


def refuse_micro_sample(seed: str) -> None:
    if seed == MICRO_SEED:
        raise ExperimentUnauthorized("frozen Micro sample is not authorized")


def refuse_condition(name: str) -> None:
    if name in {"X1", "X2", "X3", "C"}:
        raise ExperimentUnauthorized("F2 experiment remains unauthorized")
