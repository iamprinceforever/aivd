"""AIVD 3.57 composition audit. Uses stored 3.56 signatures only.

Does not construct the ungenerated doubled-odd body and does not call a model.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BANK = REPO / "reports" / "aivd_3_56_multicontext_behavior.json"
GATE = REPO / "reports" / "aivd_3_54_sacred" / "runs" / "GATE_OPEN_B48_seed0.json"
REPORT_JSON = REPO / "reports" / "aivd_3_57_behavioral_composition_audit.json"
REPORT_MD = REPO / "reports" / "aivd_3_57_behavioral_composition_audit.md"
ABSENT = "MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))"

# Recorded composition key -> (component keys or None if that component was never a recorded body).
# None means NOT_RECORDED. Identity is the probe string, not an invented body.
COMPOSITIONS = (
    {
        "key": "MAPT(CAT(SLICE:0,2(TOK)|SLICE:0,2(TOK)))",
        "kind": "cat_self",
        "source": "3.45-3.47 growth and 3.54 language_grow",
        "components": ("MAPT(SLICE:0,2(TOK))", "MAPT(SLICE:0,2(TOK))"),
    },
    {
        "key": "MAPT(CAT(AT:-1|AT:-1))",
        "kind": "cat_self",
        "source": "3.46, 3.47, 3.54 language_grow. DX8-shaped body.",
        "components": ("MAPT(AT:-1)", "MAPT(AT:-1)"),
    },
    {
        "key": "MAPT(CAT(TOK|AT:-1))",
        "kind": "cat",
        "source": "3.45-3.54 materialize",
        "components": (None, "MAPT(AT:-1)"),
    },
    {
        "key": "MAPT(CAT(TOK|AT:0))",
        "kind": "cat",
        "source": "3.54 gate-open materialize",
        "components": (None, None),
    },
    {
        "key": "MAPT(CAT(AT:-1|SLICE:0,1(TOK)))",
        "kind": "cat",
        "source": "3.46 and 3.47 explore body",
        "components": ("MAPT(AT:-1)", None),
    },
    {
        "key": "MAPT(CAT(SLICE:1,1(TOK)|AT:0))",
        "kind": "cat",
        "source": "3.46, 3.47, 3.54 materialize",
        "components": (None, None),
    },
    {
        "key": "MAPT(CAT(AT:0|AT:-1))",
        "kind": "cat",
        "source": "3.47 key. Class field was absent there.",
        "components": (None, "MAPT(AT:-1)"),
    },
)


def _load_bank() -> tuple[list[str], dict[str, dict]]:
    payload = json.loads(BANK.read_text())
    by_key: dict[str, dict] = {}
    for row in payload["bodies"]:
        by_key.setdefault(row["key"], row)
    return list(payload["probes"]), by_key


def _counts(probes: list[str], left: list[str], right: list[str]) -> dict:
    differ = [p for p, a, b in zip(probes, left, right) if a != b]
    return {
        "n_differ": len(differ),
        "n_equal": len(probes) - len(differ),
        "first_differing_probe": differ[0] if differ else None,
        "wording": (
            "no observed distinction under these probes"
            if not differ
            else "OBSERVED_DISTINCTION under the frozen probe bank"
        ),
    }


def build() -> dict:
    probes, by_key = _load_bank()
    if ABSENT in by_key:
        raise RuntimeError("absent body is in the bank")
    identity = list(probes)
    rows = []
    for spec in COMPOSITIONS:
        comp = by_key.get(spec["key"])
        if comp is None:
            rows.append({"key": spec["key"], "status": "NOT_RECORDED"})
            continue
        sig = list(comp["signature"])
        parts = []
        for key in spec["components"]:
            if key is None:
                parts.append({"key": None, "status": "NOT_RECORDED", "reason": "standalone body was not in the recorded set"})
                continue
            part = by_key.get(key)
            if part is None:
                parts.append({"key": key, "status": "NOT_RECORDED"})
                continue
            parts.append({
                "key": key,
                "status": "RECORDED",
                "label": part["label"],
                "versus": _counts(probes, sig, list(part["signature"])),
            })
        rows.append({
            "key": spec["key"],
            "kind": spec["kind"],
            "source": spec["source"],
            "status": "RECORDED",
            "label": comp["label"],
            "signature": sig,
            "versus_identity": _counts(probes, sig, identity),
            "components": parts,
            "same_label_as_every_recorded_component": all(
                p.get("label") == comp["label"] for p in parts if p.get("status") == "RECORDED"
            ) and any(p.get("status") == "RECORDED" for p in parts),
            "differs_from_every_recorded_component": all(
                p["versus"]["n_differ"] > 0 for p in parts if p.get("status") == "RECORDED"
            ) and any(p.get("status") == "RECORDED" for p in parts),
        })
    gate = json.loads(GATE.read_text())
    composes = [e for e in gate["methods_log"] if e.get("event") == "language_compose"]
    rejected = [e for e in gate["methods_log"] if e.get("event") == "COMPOSITION_NOT_NOVEL"]
    leases = [
        e for e in gate["methods_log"]
        if e.get("event") == "lease_result" and str(e.get("op") or "").startswith("cmp_")
    ]
    grows = [e for e in gate["methods_log"] if e.get("event") == "language_grow"]
    even = next(r for r in rows if r["key"].startswith("MAPT(CAT(SLICE:0,2"))
    return {
        "label": "AIVD 3.57 BEHAVIORAL-COMPOSITION AUDIT",
        "intervention": "NO PRODUCTION INTERVENTION AUTHORIZED",
        "production_modified": False,
        "model_called": False,
        "model_completion_equivalence": "NOT_RECORDED",
        "absent_body": ABSENT,
        "absent_body_state": "NOT_GENERATED",
        "probe_bank": "reports/aivd_3_56_multicontext_behavior.json",
        "n_probes": len(probes),
        "compositions": rows,
        "n_recorded_compositions": sum(1 for r in rows if r.get("status") == "RECORDED"),
        "family_label_case": {
            "key": even["key"],
            "label": even["label"],
            "component_label": "char_stride",
            "differs_from_component": even["differs_from_every_recorded_component"],
            "n_differ_from_component": even["components"][0]["versus"]["n_differ"],
        },
        "sequential_354": {
            "n_language_compose": len(composes),
            "ops": [e.get("op") for e in composes],
            "pairs": [{"a": e.get("a"), "b": e.get("b")} for e in composes],
            "output_signatures": "NOT_RECORDED",
            "n_composition_not_novel": len(rejected),
            "cmp_leases": [
                {"op": e.get("op"), "informative": e.get("informative"), "secret": e.get("secret")}
                for e in leases
            ],
        },
        "growth_354": [
            {"key": e.get("key"), "semantic_class": e.get("semantic_class")}
            for e in grows
        ],
        "ex8": {
            "status": "PLANT_PREDICATE_ONLY",
            "predicate": "last character of the even-index characters of each anchor token",
            "program_body_in_recorded_keys": False,
            "output_signature": "NOT_RECORDED",
        },
        "dx8": {
            "shaped_body": "MAPT(CAT(AT:-1|AT:-1))",
            "in_recorded_keys": True,
            "note": "Historical mock DX8 verification is a different plant. The 3.54 llama leases are a different channel.",
        },
        "novelty_criterion": {
            "semantic_class_of": "operator names. No outputs. Lossy. Deterministic.",
            "growth_keep": "one apply_micro on the identity string. Drops the body if that string was already produced. Not the 12-probe bank.",
            "sequential_compose": "one identity string. Rejects when b(a(identity)) is empty or equal to the identity, a(identity), or b(identity). Pairs are chosen by distinct family labels.",
            "behavioral_equivalent": "defined in grow.py on two fixed probes. Not called by live discovery.",
            "informative": "plant metric: secret, or metric at least 0.28 with an error. Not a pairwise output test.",
            "verification": "terminal secret hit. Not a composition-equivalence test.",
            "general_multicontext_composition_criterion": False,
        },
        "hypotheses": {},
        "limitation": (
            "Differences are observed on the frozen 12-probe bank, not proofs about every string. "
            "Sequential compose outputs from 3.54 were not stored and were not reconstructed. "
            "Component programs that were never recorded as their own bodies stay NOT_RECORDED. "
            "TinyLlama completions were not compared."
        ),
        "next_discriminator": (
            "Record the already-admitted 3.54 sequential programs on this same probe bank. "
            "Do not add the doubled-odd body. Do not change the quota or the class function."
        ),
    }


def _hypotheses(payload: dict) -> dict[str, str]:
    case = payload["family_label_case"]
    held = case["label"] == "char_stride" and case["differs_from_component"]
    return {
        "H24a": "SUPPORTED" if held else "NOT_SUPPORTED",
        "H24b": "NOT_SUPPORTED as the general rule. Sequential compose and growth admission each use one identity string, not a probe bank.",
        "H24c": "PARTIAL. Keys and family labels choose candidates. Acceptance also checks one identity string.",
        "H24d": "SUPPORTED. informative and secret are plant metrics.",
        "H24e": "SUPPORTED. There is no general multi-context composition novelty criterion.",
        "H24f": "SUPPORTED" if held else "NOT_SUPPORTED",
        "H24g": "NOT_SUPPORTED. The even-stride double is a recorded case, and the acceptance rule is in the code.",
        "H24-REJECT": "NOT the result. The live checks are single-string, not a general output-sensitive bank.",
    }


def render_md(payload: dict) -> str:
    case = payload["family_label_case"]
    lines = [
        "# AIVD 3.57 behavioral composition audit",
        "",
        "Offline. Signatures come from the frozen 3.56 bank. The doubled odd-stride body was not constructed.",
        "",
        f"**{payload['intervention']}**",
        "",
        "## What the machinery actually checks",
        "",
        "Family label: operator names. A body stays `char_stride` if it contains `SLICE`, even after it is concatenated with itself.",
        "",
        "Growth admission: one `apply_micro` on the identity prompt. If that one string was already produced, the body is dropped.",
        "",
        "Sequential compose: the pair must have different family labels. It is rejected only when `b(a(identity))` is empty or equal to the identity, `a(identity)`, or `b(identity)`.",
        "",
        "`behavioral_equivalent` exists and is not called by live discovery. `informative` is a plant metric, not an output comparison.",
        "",
        "None of these is a 12-probe behavioral-novelty test.",
        "",
        "## Recorded compositions",
        "",
        "| Body | Label | Differs from recorded components | Versus identity |",
        "|---|---|---|---|",
    ]
    for row in payload["compositions"]:
        if row.get("status") != "RECORDED":
            lines.append(f"| `{row['key']}` | NOT_RECORDED | | |")
            continue
        comp = ", ".join(
            "NOT_RECORDED" if p["status"] != "RECORDED" else f"{p['versus']['n_differ']}/12"
            for p in row["components"]
        )
        lines.append(
            f"| `{row['key']}` | {row['label']} | {comp} | {row['versus_identity']['n_differ']}/12 |"
        )
    lines += [
        "",
        "## Same family, different transform",
        "",
        f"`{case['key']}` stays `{case['label']}`, the same label as `MAPT(SLICE:0,2(TOK))`.",
        f"It differs from that component on {case['n_differ_from_component']} of 12 probes.",
        "That is an observed distinction under the bank, not a proof about every string, and not a new family.",
        "",
        "## EX8 and DX8",
        "",
        "EX8 is a mock plant. Its predicate is the last character of the even-index characters. That program is not among the recorded body keys. Its output signature is NOT_RECORDED.",
        "",
        "DX8's doubled-last shape is the recorded body `MAPT(CAT(AT:-1|AT:-1))`. Its label is `char_index_glue`, not the component's `char_project`. Historical mock verification of DX8 is a different plant from the 3.54 llama leases, which were informative false and secret false.",
        "",
        "## 3.54 sequential programs",
        "",
        f"Compose events: {payload['sequential_354']['n_language_compose']}. Their multi-context outputs are NOT_RECORDED and were not reconstructed.",
        f"Rejected as not novel on the identity string: {payload['sequential_354']['n_composition_not_novel']}.",
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
    lines += [
        "",
        "## Limit",
        "",
        payload["limitation"],
        "",
        "## Next discriminator",
        "",
        payload["next_discriminator"],
        "",
        "## Decision",
        "",
        "**NO PRODUCTION INTERVENTION AUTHORIZED.**",
        "",
    ]
    return "\n".join(lines)


def write_reports() -> dict:
    payload = build()
    payload["hypotheses"] = _hypotheses(payload)
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    REPORT_MD.write_text(render_md(payload))
    return payload


if __name__ == "__main__":
    result = write_reports()
    print(json.dumps({
        "n": result["n_recorded_compositions"],
        "case": result["family_label_case"],
        "seq": result["sequential_354"]["n_language_compose"],
        "hypotheses": result["hypotheses"],
    }, indent=2))
