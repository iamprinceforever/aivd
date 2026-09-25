"""Micro adapter. It calls the existing interpreter and does not translate CEL."""

from __future__ import annotations

from aivd.experiments.aivd40.stage_4_2.observation import BehavioralObservation, canonical_string
from aivd.science.micro import MAX_OUT_TOKENS, MAX_TOKEN_CHARS, apply_micro, eval_micro
from aivd.science.operators import join_prompt, split_prompt


def execute(program, probe: str) -> BehavioralObservation:
    if program is None or probe is None:
        return BehavioralObservation("INVALID_EXECUTION", None)
    try:
        tokens = split_prompt(probe)
        if not tokens:
            return BehavioralObservation("INVALID_EXECUTION", None)
        produced = [
            token[:MAX_TOKEN_CHARS]
            for token in eval_micro(tokens, program)[:MAX_OUT_TOKENS]
            if token
        ]
        if not produced:
            return BehavioralObservation("INVALID_EXECUTION", None)
        got = join_prompt(produced)
        if not got or apply_micro(probe, program) != got:
            return BehavioralObservation("AMBIGUOUS", None)
    except Exception:
        return BehavioralObservation("EXECUTION_FAILURE", None)
    canon = canonical_string(got)
    status = "VALID_IDENTITY" if canon == canonical_string(probe) else "VALID_OUTPUT"
    return BehavioralObservation(status, canon)


def classify(probe: str, evaluated: str | None, applied: str | None) -> BehavioralObservation:
    """Classify a pair of results. Used to test AMBIGUOUS without a new program."""
    if evaluated is None or applied is None or evaluated != applied:
        return BehavioralObservation("AMBIGUOUS", None)
    canon = canonical_string(evaluated)
    status = "VALID_IDENTITY" if canon == canonical_string(probe) else "VALID_OUTPUT"
    return BehavioralObservation(status, canon)
