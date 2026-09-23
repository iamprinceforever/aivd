"""Research-only boundary around AtomSynthesizer.next_atom.

Does not change AtomInventory.max_executed. Does not read a candidate key.
ARM A must not install this. ARM B installs it for the cell and then removes it.
"""
from __future__ import annotations

from typing import Any

from aivd.science.atom_synth import AtomSynthesizer

_ORIG = None
_LOG: list[dict[str, Any]] = []
_INSTALLED = False


def install(*, open_gate: bool) -> None:
    """Install a process-local wrapper.

    The cap is skipped only while executed is still the value that first
    blocked a non-empty board. That lets the in-flight batch pop. A later
    lease, which increments executed, is subject to the real cap again.
    """
    global _ORIG, _INSTALLED
    if _INSTALLED:
        raise RuntimeError("execution-gate wrapper already installed")
    _ORIG = AtomSynthesizer.next_atom
    first_blocked_at: dict[str, int | None] = {"executed": None}

    def wrapped(self):
        before = int(self.board.executed)
        cap = int(self.board.max_executed)
        n_remaining = len(self.board.remaining)
        blocked = before >= cap
        opened = False
        allow = False
        if open_gate and blocked and n_remaining:
            if first_blocked_at["executed"] is None:
                first_blocked_at["executed"] = before
            allow = before == first_blocked_at["executed"]
        if allow:
            # One pop. The cap is restored before return, including on error.
            # executed is not incremented here; a later lease does that.
            self.board.max_executed = before + 1
            opened = True
            try:
                atom = _ORIG(self)
            finally:
                self.board.max_executed = cap
        else:
            atom = _ORIG(self)
        _LOG.append({
            "executed_before": before,
            "executed_after": int(self.board.executed),
            "max_executed": cap,
            "gate_would_block": blocked,
            "gate_opened": opened,
            "remaining_before": n_remaining,
            "dispensed_key": atom.key() if atom is not None else None,
            "dispensed": atom is not None,
        })
        return atom

    AtomSynthesizer.next_atom = wrapped
    _INSTALLED = True


def uninstall() -> None:
    global _INSTALLED
    if _ORIG is not None:
        AtomSynthesizer.next_atom = _ORIG
    _INSTALLED = False


def take_log() -> list[dict[str, Any]]:
    out = list(_LOG)
    _LOG.clear()
    return out
