"""Evaluator entry. Reads the seed from stdin only after discovery has locked."""

from __future__ import annotations

import sys
from pathlib import Path

from aivd.experiments.aivd40.f1.evaluate import evaluate


def main() -> None:
    seed = sys.stdin.buffer.read()
    if len(seed) != 32:
        raise SystemExit(2)
    evaluate(Path(sys.argv[1]), seed)


if __name__ == "__main__":
    main()
