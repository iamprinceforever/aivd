"""Experimenter process. It never reads the seed pipe or the seal."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def experimenter_run(out: Path) -> dict[str, int]:
    read_fd, write_fd = os.pipe()
    evaluator = subprocess.Popen(
        [sys.executable, "-m", "aivd.experiments.aivd40.f1.evaluate_entry", str(out)],
        stdin=read_fd,
    )
    os.close(read_fd)
    env = os.environ.copy()
    env["AIVD41_SEED_FD"] = str(write_fd)
    discovery = subprocess.Popen(
        [sys.executable, "-m", "aivd.experiments.aivd40.f1.discovery_entry", str(out)],
        stdout=subprocess.PIPE,
        env=env,
        pass_fds=(write_fd,),
    )
    os.close(write_fd)
    raw = discovery.stdout.read()
    if discovery.wait() != 0 or evaluator.wait() != 0:
        raise RuntimeError("discovery or evaluation failed")
    summary = json.loads(raw)
    ledger = json.loads((out / "discovery_ledger.json").read_text())
    if "body_key" in json.dumps(ledger):
        raise RuntimeError("ledger exposed a body field")
    return summary
