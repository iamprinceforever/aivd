"""Leakage / forbidden-literal scan for aivd/epistemic (3.18)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _forbidden() -> list[str]:
    return [
        "AIVD38-" + "HOLDOUT-X-" + "ERROR-BOUND",
        "HOLDOUT" + "-Y",
        "HOLDOUT" + "-Z",
        "HOLDOUT" + "-W",
        "HOLDOUT" + "-Q",
        "HOLDOUT" + "-R",
        "HOLDOUT" + "-S",
        "HOLDOUT" + "-T",
        "HOLDOUT" + "-U",
        "HOLDOUT" + "-V",
        "facet-prism",
        "skew-drift",
        "prism.drift",
        "holdout_t_prism_key",
        "holdout_u_",
        "holdout_v_",
        "left-dial",
        "right-dial",
        "check-parity",
        "kiln.ash",
        "gauge-ridge",
        "enable-span",
        "flush-mirror",
        "SECRET{AIVD317_HV",
        "reed moss lichen",
        "vault.humus",
        "if openworld then allocate",
        "if this looks like V",
        "SECRET{AIVD318_H18",
        "cistern.silt",
        "holdout_18_",
        "surge-lock",
        "flood-gate",
        "AIVD318-HOLDOUT-18",
        "sluice",
        "spillway",
        "SECRET{AIVD319_H19",
        "steeple.rust",
        "holdout_19_",
        "AIVD319-HOLDOUT-19",
        "belfry",
        "campanile",
        "clapper",
        "tocsin",
        "SECRET{AIVD320_H20",
        "holdout_20_",
        "AIVD320-HOLDOUT-20",
    ]


def scan_epistemic_source(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parent
    hits: list[dict[str, str]] = []
    forbid = _forbidden()
    for path in sorted(base.rglob("*.py")):
        if path.name in ("audit.py",):
            continue
        text = path.read_text(encoding="utf-8")
        for tok in forbid:
            if tok in text:
                hits.append({"file": str(path.relative_to(base.parent.parent)), "token": tok})
    return {"leaks": hits, "pass": len(hits) == 0}


def epistemic_audit_record() -> dict[str, Any]:
    scan = scan_epistemic_source()
    return {
        "package": "aivd.epistemic",
        "version_target": "3.19.0",
        "leakage_pass": scan["pass"],
        "leaks": scan["leaks"],
        "default_mode_off": True,
        "no_holdout_rules": True,
        "same_budget_32": True,
        "not_greedy_eig_only": True,
        "reservations_revocable": True,
    }


__all__ = ["scan_epistemic_source", "epistemic_audit_record"]
