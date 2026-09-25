"""Stops the frozen experiment unless this run is explicitly authorized."""

from __future__ import annotations

import os

from aivd.experiments.aivd40.stage_4_2.freeze import FROZEN_CEL, MICRO_SEED

AUTHORIZED = "AIVD_F2_AUTHORIZED"


class ExperimentUnauthorized(RuntimeError):
    pass


def authorized() -> bool:
    return os.environ.get(AUTHORIZED) == "1"


def refuse_frozen_cel(expression: str) -> None:
    if expression in FROZEN_CEL and not authorized():
        raise ExperimentUnauthorized("frozen CEL sample is not authorized")


def refuse_micro_sample(seed: str) -> None:
    if seed == MICRO_SEED and not authorized():
        raise ExperimentUnauthorized("frozen Micro sample is not authorized")


def refuse_condition(name: str) -> None:
    if name in {"X1", "X2", "X3", "C"} and not authorized():
        raise ExperimentUnauthorized("F2 experiment remains unauthorized")
