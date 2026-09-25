"""CEL adapter. It calls the pinned cel-go binary and does not import Micro."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aivd.experiments.aivd40.stage_4_2.firewall import refuse_frozen_cel
from aivd.experiments.aivd40.stage_4_2.observation import BehavioralObservation, canonical_string

_BIN = Path("/tmp/aivd-f2-celbin")
_DIR = Path(__file__).resolve().parent / "celbin"


def binary() -> Path:
    if not _BIN.exists():
        subprocess.check_call(["go", "build", "-o", str(_BIN), "."], cwd=_DIR)
    return _BIN


def execute(expression: str, probe: str) -> BehavioralObservation:
    if not expression or not isinstance(probe, str):
        return BehavioralObservation("INVALID_EXECUTION", None)
    refuse_frozen_cel(expression)
    raw = subprocess.check_output(
        [str(binary())],
        input=json.dumps({"expression": expression, "input": probe}).encode(),
    )
    try:
        payload = json.loads(raw.decode())
    except json.JSONDecodeError:
        return BehavioralObservation("AMBIGUOUS", None)
    if payload.get("kind") == "blocked":
        refuse_frozen_cel(expression)
        return BehavioralObservation("INVALID_EXECUTION", None)
    if payload.get("kind") == "unsupported":
        return BehavioralObservation("UNSUPPORTED_OUTPUT", None)
    if not payload.get("ok"):
        return BehavioralObservation("EXECUTION_FAILURE", None)
    canon = payload.get("canonical")
    if not isinstance(canon, dict) or "t" not in canon:
        return BehavioralObservation("AMBIGUOUS", None)
    status = "VALID_IDENTITY" if canon == canonical_string(probe) else "VALID_OUTPUT"
    return BehavioralObservation(status, canon)
