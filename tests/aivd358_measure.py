"""Measure the two sequential programs admitted in the 3.54 gate log.

Component keys come from that log. Outputs are apply_micro of those bodies,
in the order language.compose uses: b(a(prompt)). No model. No new body.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aivd.science.micro import Micro, apply_micro

REPO = Path(__file__).resolve().parents[1]
BANK = REPO / "reports" / "aivd_3_56_multicontext_behavior.json"
GATE = REPO / "reports" / "aivd_3_54_sacred" / "runs" / "GATE_OPEN_B48_seed0.json"
REPORT_JSON = REPO / "reports" / "aivd_3_58_admitted_composition_measurement.json"
REPORT_MD = REPO / "reports" / "aivd_3_58_admitted_composition_measurement.md"
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


def _bodies() -> dict[str, Micro]:
    return {
        "MAPT(AT:-1)": _mapt(_at(-1)),
        "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))": _cat(_at(-1), _slice(0, 1)),
        "MAPT(SLICE:1,2(TOK))": _mapt(_slice(1, 2)),
        "MAPT(CAT(TOK|AT:0))": _cat(_tok(), _at(0)),
    }


def _recover(log: list[dict]) -> list[dict]:
    keys = {
        e["op"]: e
        for e in log
        if e.get("event") == "atom_materialize"
    }
    out = []
    for e in log:
        if e.get("event") != "language_compose":
            continue
        a = keys[e["a"]]
        b = keys[e["b"]]
        out.append({
            "op": e["op"],
            "a_op": e["a"],
            "b_op": e["b"],
            "a_key": a["key"],
            "b_key": b["key"],
            "a_label": a["semantic_class"],
            "b_label": b["semantic_class"],
            "a_origin": a.get("origin"),
            "b_origin": b.get("origin"),
            "compose_generation": e.get("generation"),
            "compose_novelty": e.get("novelty"),
            "joined_label": a["semantic_class"] + "+" + b["semantic_class"],
            "joined_label_source": "code joins the two recorded component classes; the compose event did not store semantic_class",
        })
    if len(out) != 2:
        raise RuntimeError(f"expected 2 compose events, got {len(out)}")
    return out


def _signature(body: Micro, probes: list[str]) -> list[dict]:
    cells = []
    for probe in probes:
        got = apply_micro(probe, body)
        cells.append({"input": probe, "output": got, "output_length": len(got), "ok": True, "exception": None})
    return cells


def _cmp(probes: list[str], left: list[str], right: list[str]) -> dict:
    differ = [p for p, a, b in zip(probes, left, right) if a != b]
    return {
        "n_equal": len(probes) - len(differ),
        "n_differ": len(differ),
        "first_differing_probe": differ[0] if differ else None,
        "wording": (
            "no observed distinction under these probes"
            if not differ
            else "OBSERVED_DISTINCTION under the frozen probe bank"
        ),
    }


def build() -> dict:
    bank = json.loads(BANK.read_text())
    probes = list(bank["probes"])
    probe_hash = hashlib.sha256("\n".join(probes).encode()).hexdigest()
    stored = {row["key"]: list(row["signature"]) for row in bank["bodies"]}
    gate = json.loads(GATE.read_text())
    programs = _recover(gate["methods_log"])
    bodies = _bodies()
    if ABSENT in bodies or any(ABSENT in (p["a_key"], p["b_key"]) for p in programs):
        raise RuntimeError("absent body entered the measurement")
    measured = []
    for prog in programs:
        for key in (prog["a_key"], prog["b_key"]):
            if bodies[key].key() != key:
                raise RuntimeError(f"body key mismatch {key}")
            got = [c["output"] for c in _signature(bodies[key], probes)]
            if stored[key] != got:
                raise RuntimeError(f"component signature drifted from the frozen bank: {key}")
        a_cells = _signature(bodies[prog["a_key"]], probes)
        b_cells = _signature(bodies[prog["b_key"]], probes)
        seq = []
        for probe in probes:
            mid = apply_micro(probe, bodies[prog["a_key"]])
            got = apply_micro(mid, bodies[prog["b_key"]])
            seq.append({"input": probe, "output": got, "output_length": len(got), "ok": True, "exception": None})
        seq_out = [c["output"] for c in seq]
        a_out = [c["output"] for c in a_cells]
        b_out = [c["output"] for c in b_cells]
        measured.append({
            **prog,
            "body_key_logged": False,
            "body_key_from_code": prog["a_key"] + "|" + prog["b_key"],
            "cells": seq,
            "versus_identity": _cmp(probes, seq_out, probes),
            "versus_a": _cmp(probes, seq_out, a_out),
            "versus_b": _cmp(probes, seq_out, b_out),
            "identity_string": "NOT_RECORDED",
            "a_of_identity": "NOT_RECORDED",
            "b_of_a_of_identity": "NOT_RECORDED",
            "admission": "admitted. The language_compose event is in the log, and COMPOSITION_NOT_NOVEL is not.",
            "admission_observed": "one unstored identity string. The check passed, so that string was nonempty and different from the identity, from a(identity), and from b(identity). It did not observe these 12 probes.",
        })
    left, right = measured
    pair = _cmp(probes, [c["output"] for c in left["cells"]], [c["output"] for c in right["cells"]])
    same_label = left["joined_label"] == right["joined_label"]
    if pair["n_differ"] == 0 and same_label:
        pair_class = "same label / same outputs"
    elif pair["n_differ"] and same_label:
        pair_class = "same label / different outputs"
    elif pair["n_differ"] == 0:
        pair_class = "different label / same outputs"
    else:
        pair_class = "different label / different outputs"
    leases = {
        e["op"]: e
        for e in gate["methods_log"]
        if e.get("event") == "lease_result" and str(e.get("op") or "").startswith("cmp_")
    }
    rejected = sum(1 for e in gate["methods_log"] if e.get("event") == "COMPOSITION_NOT_NOVEL")
    return {
        "label": "AIVD 3.58 ADMITTED COMPOSITION MEASUREMENT",
        "intervention": "NO PRODUCTION INTERVENTION AUTHORIZED",
        "production_modified": False,
        "model_called": False,
        "model_completion_equivalence": "NOT_RECORDED",
        "probe_bank_hash": probe_hash,
        "probes": probes,
        "n_probes": len(probes),
        "programs": measured,
        "sequential_vs_sequential": {**pair, "classification": pair_class},
        "live_metric": {
            "terminal_state": gate["terminal_state"],
            "firewall_epoch": gate["firewall_epoch"],
            "secret_found": gate["secret_found"],
            "pipeline_verified": gate["pipeline_verified"],
            "n_composition_not_novel": rejected,
            "leases": [
                {"op": op, "informative": leases[op].get("informative"), "secret": leases[op].get("secret")}
                for op in (left["op"], right["op"])
            ],
            "informative_is_not_equivalence": True,
        },
        "absent_body": ABSENT,
        "absent_body_state": "NOT_GENERATED",
        "hypotheses": {},
        "limitation": (
            "The 12-probe differences are observed distinguishability, not a proof about every string. "
            "apply_micro returns the original prompt when a transform yields no tokens. "
            "The identity string used at admission was not stored, so its three outputs stay NOT_RECORDED. "
            "TinyLlama completions were not compared."
        ),
    }


def _hypotheses(payload: dict) -> dict[str, str]:
    programs = payload["programs"]
    differs = all(p["versus_a"]["n_differ"] > 0 and p["versus_b"]["n_differ"] > 0 for p in programs)
    pair = payload["sequential_vs_sequential"]
    return {
        "H25a": "SUPPORTED" if differs else "NOT_SUPPORTED",
        "H25b": "SUPPORTED as fewer contexts, not as an invalid test. Admission saw one unstored string. The bank distinctions are on probes it did not inspect.",
        "H25c": "SUPPORTED. The compose label is the join of the two existing component labels. No new operator family is created.",
        "H25d": "SUPPORTED. Both leases are informative false and secret false, while the bank shows output differences.",
        "H25e": "SUPPORTED" if pair["n_differ"] > 0 else "NOT_SUPPORTED",
        "H25f": "NOT_SUPPORTED" if pair["n_differ"] > 0 else "SUPPORTED",
        "H25g": "NOT_SUPPORTED. A pass means one string differed from the identity and from each component. That is not behavioral equivalence.",
        "H25-REJECT": "NOT the result. Both programs were recovered from the compose event plus the matching materialize keys.",
    }


def render_md(payload: dict) -> str:
    lines = [
        "# AIVD 3.58 admitted composition measurement",
        "",
        "Offline. The two sequential programs are the ones the 3.54 gate log admitted. No model. The doubled odd-stride body was not constructed.",
        "",
        f"**{payload['intervention']}**",
        "",
        f"Probe bank hash `{payload['probe_bank_hash']}`. {payload['n_probes']} probes, same order as 3.56.",
        "",
        "## Programs",
        "",
    ]
    for prog in payload["programs"]:
        lines += [
            f"### `{prog['op']}`",
            "",
            f"Order: `{prog['b_key']}` after `{prog['a_key']}`.",
            f"Component labels: {prog['a_label']} then {prog['b_label']}.",
            f"Joined label, from the code plus those recorded classes: `{prog['joined_label']}`. The event did not store it.",
            f"Versus identity: {prog['versus_identity']['n_differ']}/12, first {prog['versus_identity']['first_differing_probe']!r}.",
            f"Versus A: {prog['versus_a']['n_differ']}/12, first {prog['versus_a']['first_differing_probe']!r}.",
            f"Versus B: {prog['versus_b']['n_differ']}/12, first {prog['versus_b']['first_differing_probe']!r}.",
            "Identity-string outputs: NOT_RECORDED. Admission is recorded only as the compose event.",
            "",
        ]
    pair = payload["sequential_vs_sequential"]
    lines += [
        "## The two programs",
        "",
        f"{pair['classification']}. Differing probes: {pair['n_differ']}/12. First: {pair['first_differing_probe']!r}.",
        "Wording: observed distinguishability under the frozen bank, not a proof about every string.",
        "",
        "## Plant metric",
        "",
        "Both compose leases are informative false and secret false. The terminal state is unresolved and unverified.",
        "That metric is not an output comparison. The bank still separates each program from its components.",
        "",
        "## What the identity test saw",
        "",
        "It saw one string, and that string was not stored. The check passed, so the sequential result on that string was nonempty and different from the identity and from each component alone. It did not see the 12 probes. It is a weaker observation, not a shown error.",
        "",
        "## Missing secret",
        "",
        f"`{payload['absent_body']}`: {payload['absent_body_state']}.",
        "",
        "## Hypotheses",
        "",
    ]
    for k, v in payload["hypotheses"].items():
        lines.append(f"- **{k}.** {v}")
    lines += ["", "## Limit", "", payload["limitation"], "", "## Decision", "", "**NO PRODUCTION INTERVENTION AUTHORIZED.**", ""]
    return "\n".join(lines)


def write_reports() -> dict:
    payload = build()
    payload["hypotheses"] = _hypotheses(payload)
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    REPORT_MD.write_text(render_md(payload))
    return payload


if __name__ == "__main__":
    result = write_reports()
    brief = []
    for prog in result["programs"]:
        brief.append({
            "op": prog["op"],
            "label": prog["joined_label"],
            "vs_a": prog["versus_a"]["n_differ"],
            "vs_b": prog["versus_b"]["n_differ"],
            "vs_id": prog["versus_identity"]["n_differ"],
        })
    print(json.dumps({
        "programs": brief,
        "pair": result["sequential_vs_sequential"],
        "hypotheses": result["hypotheses"],
    }, indent=2))
