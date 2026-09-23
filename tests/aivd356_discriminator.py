"""Offline multi-context comparison of already-recorded program bodies.

Does not call a model. Does not construct the ungenerated doubled-odd body.
"""
from __future__ import annotations

import json
from pathlib import Path

from aivd.science.atom import semantic_class_of
from aivd.science.micro import Micro, apply_micro

REPO = Path(__file__).resolve().parents[1]
REPORT_JSON = REPO / "reports" / "aivd_3_56_multicontext_behavior.json"
REPORT_MD = REPO / "reports" / "aivd_3_56_multicontext_behavior.md"

# Frozen before any comparison. Not built around a planted fire predicate.
PROBES: tuple[str, ...] = (
    "",
    "a",
    "ab",
    "abc",
    "aaaa",
    "a,b",
    "ab cd efg hij",
    "x yy zzz",
    "z",
    "abcd e",
    "hi!",
    "aa bb",
)
KNOWN_PROBE = "ab cd efg hij"
KNOWN = {
    "MAPT(SLICE:0,2(TOK))": "a c eg hj",
    "MAPT(SLICE:1,2(TOK))": "b d f i",
}
ABSENT = "MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))"


def _tok() -> Micro:
    return Micro("TOK")


def _at(i: int) -> Micro:
    return Micro("AT", (i,))


def _slice(start: int, step: int) -> Micro:
    return Micro("SLICE", (start, step), (_tok(),))


def _mapt(inner: Micro) -> Micro:
    return Micro("MAPT", (), (inner,))


def _cat(a: Micro, b: Micro) -> Micro:
    return _mapt(Micro("CAT", (), (a, b)))


def inventory() -> list[dict[str, str]]:
    """Bodies whose keys already appear in 3.45–3.47 or the 3.54 seed-0 logs."""
    bodies = [
        (_mapt(_slice(0, 2)), "P0", "3.45, 3.46, 3.47, 3.54 baseline and gate"),
        (_mapt(_slice(1, 2)), "P1", "3.54 gate-open materialize"),
        (_cat(_tok(), _at(-1)), "index_glue", "3.45, 3.46, 3.47, 3.54"),
        (_cat(_tok(), _at(0)), "index_glue", "3.47 key; 3.54 gate-open materialize"),
        (_mapt(_at(-1)), "project", "3.45, 3.46, 3.47, 3.54"),
        (_cat(_at(-1), _slice(0, 1)), "explore_347", "3.46 and 3.47 explore body"),
        (_cat(_slice(0, 2), _slice(0, 2)), "even_double", "3.45, 3.46, 3.47, 3.54 growth"),
        (_cat(_slice(1, 1), _at(0)), "hybrid_stride", "3.46, 3.47, 3.54 materialize"),
        (_cat(_at(-1), _at(-1)), "project_double", "3.46, 3.47, 3.54 growth"),
        (_cat(_at(0), _at(-1)), "glue_ends", "3.47 key only; class field was absent"),
        (_mapt(_slice(0, 2)), "true_duplicate_of_P0", "3.54 rediscovery of the same key"),
    ]
    rows = []
    for body, role, source in bodies:
        key = body.key()
        if key == ABSENT:
            raise RuntimeError("absent body entered the inventory")
        rows.append({
            "key": key,
            "role": role,
            "source": source,
            "label": semantic_class_of(body),
            "body": body,
        })
    return rows


def evaluate(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        cells = []
        for probe in PROBES:
            try:
                got = apply_micro(probe, row["body"])
                cells.append({
                    "input": probe,
                    "output": got,
                    "output_length": len(got),
                    "ok": True,
                    "exception": None,
                })
            except Exception as exc:  # noqa: BLE001
                cells.append({
                    "input": probe,
                    "output": None,
                    "output_length": None,
                    "ok": False,
                    "exception": type(exc).__name__,
                })
        signature = tuple(c["output"] for c in cells)
        out.append({
            "key": row["key"],
            "role": row["role"],
            "source": row["source"],
            "label": row["label"],
            "signature": signature,
            "cells": cells,
        })
    return out


def _kind(same_label: bool, same_behavior: bool) -> str:
    if same_label and same_behavior:
        return "LABEL_SAME_BEHAVIOR_SAME"
    if same_label and not same_behavior:
        return "LABEL_SAME_BEHAVIOR_DIFFERENT"
    if not same_label and same_behavior:
        return "LABEL_DIFFERENT_BEHAVIOR_SAME"
    return "LABEL_DIFFERENT_BEHAVIOR_DIFFERENT"


def pairs(rows: list[dict]) -> list[dict]:
    found = []
    for i, a in enumerate(rows):
        for b in rows[i + 1 :]:
            diffs = [
                PROBES[k]
                for k, (x, y) in enumerate(zip(a["signature"], b["signature"]))
                if x != y
            ]
            same_label = a["label"] == b["label"]
            same_behavior = not diffs
            found.append({
                "a": a["key"],
                "a_role": a["role"],
                "b": b["key"],
                "b_role": b["role"],
                "label_a": a["label"],
                "label_b": b["label"],
                "same_label": same_label,
                "same_output_on_every_probe": same_behavior,
                "n_differing_probes": len(diffs),
                "first_differing_probe": diffs[0] if diffs else None,
                "classification": _kind(same_label, same_behavior),
                "wording": (
                    "no observed distinction under these probes"
                    if same_behavior
                    else "observably distinguishable under the frozen probe bank"
                ),
            })
    return found


def build() -> dict:
    rows = evaluate(inventory())
    if any(r["key"] == ABSENT for r in rows):
        raise RuntimeError("absent body was evaluated")
    table = pairs(rows)
    p0 = next(r for r in rows if r["role"] == "P0")
    p1 = next(r for r in rows if r["role"] == "P1")
    known_i = PROBES.index(KNOWN_PROBE)
    if p0["cells"][known_i]["output"] != KNOWN[p0["key"]]:
        raise RuntimeError("known P0 probe mismatch")
    if p1["cells"][known_i]["output"] != KNOWN[p1["key"]]:
        raise RuntimeError("known P1 probe mismatch")
    primary = next(p for p in table if {p["a_role"], p["b_role"]} == {"P0", "P1"})
    same_label_different = [
        p for p in table
        if p["classification"] == "LABEL_SAME_BEHAVIOR_DIFFERENT"
    ]
    same_output = [p for p in table if p["same_output_on_every_probe"]]
    distinct_keys = [r for r in rows if r["role"] != "true_duplicate_of_P0"]
    return {
        "label": "AIVD 3.56 MULTI-CONTEXT BEHAVIORAL DISCRIMINATOR",
        "intervention": "NO PRODUCTION INTERVENTION AUTHORIZED",
        "production_modified": False,
        "model_called": False,
        "model_completion_equivalence": "NOT_RECORDED",
        "absent_body": ABSENT,
        "absent_body_state": "NOT_GENERATED",
        "plant_metric_used_as_equivalence": False,
        "stage5_relationship": "SEPARATE. This run does not call the identity filter.",
        "class_interpretation": "family label. Not an equivalence relation. Not a behavioral-identity label.",
        "probes": list(PROBES),
        "n_probes": len(PROBES),
        "bodies": [
            {
                "key": r["key"],
                "role": r["role"],
                "source": r["source"],
                "label": r["label"],
                "signature": list(r["signature"]),
            }
            for r in rows
        ],
        "n_body_rows": len(rows),
        "n_distinct_keys": len({r["key"] for r in distinct_keys}),
        "output_matrix": [
            {"key": r["key"], "role": r["role"], "label": r["label"], "cells": r["cells"]}
            for r in rows
        ],
        "pairs": table,
        "primary_pair": primary,
        "n_same_label_behavior_different": len(same_label_different),
        "same_label_behavior_different": [
            {"a": p["a"], "b": p["b"], "n_differing_probes": p["n_differing_probes"], "first": p["first_differing_probe"]}
            for p in same_label_different
        ],
        "same_output_pairs": [
            {"a": p["a"], "b": p["b"], "classification": p["classification"]}
            for p in same_output
        ],
        "known_probe_validated": True,
        "hypotheses": _hypotheses(primary, same_label_different, same_output, table),
        "limitation": (
            "Finite probe bank. Signatures are apply_micro outputs, which return "
            "the original prompt when a transform yields no tokens, so some raw "
            "character differences are not visible. A difference is observed "
            "distinguishability, not a proof about every string. Matching outputs "
            "are no observed distinction under these probes, not a proof of "
            "semantic equivalence. TinyLlama completions were not compared."
        ),
    }


def _hypotheses(primary, same_label_different, same_output, table) -> dict[str, str]:
    cross = [p for p in table if p["classification"] == "LABEL_DIFFERENT_BEHAVIOR_SAME"]
    same_label_same = [p for p in same_output if p["classification"] == "LABEL_SAME_BEHAVIOR_SAME"]
    return {
        "H23a": "SUPPORTED" if same_label_different else "NOT_SUPPORTED",
        "H23b": (
            "SUPPORTED"
            if primary["classification"] == "LABEL_SAME_BEHAVIOR_DIFFERENT"
            and primary["n_differing_probes"] > 1
            else "NOT_SUPPORTED"
        ),
        "H23c": "SUPPORTED as too coarse for behavioral identity under this bank. Not a universal claim.",
        "H23d": "SUPPORTED. The code bins by operator names. The bank shows those bins are families.",
        "H23e": (
            "SUPPORTED only for the recorded rediscovery of the same key. "
            "No two distinct keys with the same label matched on every probe."
            if same_label_same and all(p["a"] == p["b"] for p in same_label_same)
            else ("SUPPORTED" if same_label_same else "NOT_SUPPORTED")
        ),
        "H23f": "SUPPORTED" if cross else "NOT_SUPPORTED. No different-label pair matched on every probe.",
        "H23-REJECT": "NOT the result",
    }


def render_md(payload: dict) -> str:
    p = payload["primary_pair"]
    lines = [
        "# AIVD 3.56 multi-context behavioral discriminator",
        "",
        "Offline program outputs only. No model. No discovery run. The doubled odd-stride body was not constructed.",
        "",
        f"**{payload['intervention']}**",
        "",
        "## Frozen probe bank",
        "",
    ]
    for i, probe in enumerate(payload["probes"], 1):
        shown = repr(probe)
        lines.append(f"{i}. {shown}")
    lines += [
        "",
        f"Probe count: {payload['n_probes']}.",
        "",
        "## Bodies",
        "",
        "| Role | Key | Label |",
        "|---|---|---|",
    ]
    for b in payload["bodies"]:
        lines.append(f"| {b['role']} | `{b['key']}` | {b['label']} |")
    lines += [
        "",
        "## P0 and P1",
        "",
        f"Same label: {p['same_label']}. Differing probes: {p['n_differing_probes']} of {payload['n_probes']}.",
        f"First difference: {p['first_differing_probe']!r}.",
        "Known probe `ab cd efg hij` still yields `a c eg hj` and `b d f i`.",
        "Wording: observably distinguishable under the frozen probe bank. Not a proof about every string.",
        "",
        "## Same label, different outputs",
        "",
        f"{payload['n_same_label_behavior_different']} pairs.",
        "",
    ]
    for row in payload["same_label_behavior_different"]:
        lines.append(
            f"- `{row['a']}` vs `{row['b']}`: {row['n_differing_probes']} probes, first {row['first']!r}"
        )
    lines += ["", "## No observed distinction", ""]
    if payload["same_output_pairs"]:
        for row in payload["same_output_pairs"]:
            lines.append(f"- `{row['a']}` vs `{row['b']}`: {row['classification']}")
    else:
        lines.append("None.")
    lines += [
        "",
        "Matching outputs mean no observed distinction under these probes. They do not prove semantic equivalence.",
        "",
        "## What the class label is",
        "",
        payload["class_interpretation"],
        "",
        "## Stage 5",
        "",
        payload["stage5_relationship"],
        "",
        "## Limit",
        "",
        payload["limitation"],
        "",
        "Model completion equivalence: NOT_RECORDED.",
        "",
        f"Absent body `{payload['absent_body']}`: {payload['absent_body_state']}.",
        "",
        "## Hypotheses",
        "",
    ]
    for k, v in payload["hypotheses"].items():
        lines.append(f"- **{k}.** {v}")
    lines += ["", "## Decision", "", "**NO PRODUCTION INTERVENTION AUTHORIZED.**", ""]
    return "\n".join(lines)


def write_reports() -> dict:
    payload = build()
    # Bodies carry no live Micro objects at this point.
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    REPORT_MD.write_text(render_md(payload))
    return payload


if __name__ == "__main__":
    result = write_reports()
    print(json.dumps({
        "n_probes": result["n_probes"],
        "n_bodies": result["n_body_rows"],
        "primary": result["primary_pair"]["classification"],
        "n_diff": result["primary_pair"]["n_differing_probes"],
        "same_label_different": result["n_same_label_behavior_different"],
        "same_output": result["same_output_pairs"],
        "hypotheses": result["hypotheses"],
    }, indent=2))
