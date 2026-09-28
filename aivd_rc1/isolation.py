"""Process-level read isolation for a blind pass.

`install(forbidden)` adds a Python audit hook that raises on any attempt to open a path under
one of the forbidden prefixes (the protected seal directory and every other pass's output
directory). It cannot be removed once installed. Used by scripts/rc1_run_pass.py so Pass 2
cannot read Pass 1 outputs and no pass can read the seal.
"""

import os
import sys


class IsolationViolation(PermissionError):
    pass


def _norm(path) -> str:
    return os.path.realpath(os.fspath(path))


def install(forbidden) -> None:
    prefixes = tuple(_norm(p).rstrip("/") + "/" for p in forbidden)
    exact = tuple(_norm(p) for p in forbidden)

    def hook(event, args):
        if event in ("open", "os.listdir", "os.scandir") and args:
            target = args[0]
            if isinstance(target, int) or target is None:
                return
            try:
                path = _norm(target)
            except Exception:
                return
            if path in exact or path.startswith(prefixes):
                raise IsolationViolation(f"blind pass may not read {path}")

    sys.addaudithook(hook)
