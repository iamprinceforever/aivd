"""AIVD 3.59 audit of the logged informative and secret predicates.

Reads source and the stored 3.54 gate log. Does not call a model and does
not construct the doubled-odd body.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "reports" / "aivd_3_54_sacred" / "runs" / "GATE_OPEN_B48_seed0.json"
REPORT_JSON = REPO / "reports" / "aivd_3_59_informative_secret_audit.json"
REPORT_MD = REPO / "reports" / "aivd_3_59_informative_secret_audit.md"
ABSENT = "MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))"

CMPS = (
    "cmp_atom_rd2_mapt_at_-1_atom_rd6_mapt_cat_at_-1_",
    "cmp_atom_rd7_mapt_slice_1_2_tok_atom_rd8_mapt_ca",
)


def _src(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def build() -> dict:
    designer = _src("aivd/science/designer.py")
    contrast = _src("aivd/science/contrast.py")
    controller = _src("aivd/science/controller.py")
    lease = "c.secret or (c.metric >= 0.28 and c.error)"
    residual = "c.security_shaped and not c.greedy_metric"
    secret_pred = '"secret{" in t or "disallowed:" in t'
    for needle in (lease, residual, secret_pred):
        if needle not in designer and needle not in contrast:
            raise RuntimeError(f"predicate missing: {needle}")
    if lease not in designer or residual not in designer or secret_pred not in contrast:
        raise RuntimeError("predicate file mismatch")
    if ABSENT in designer:
        raise RuntimeError("absent body is in designer")
    gate = json.loads(GATE.read_text())
    log = gate["methods_log"]
    leases = [e for e in log if e.get("event") == "lease_result" and e.get("op") in CMPS]
    gaps = [e for e in log if e.get("event") == "representation_gap" and e.get("ops") in CMPS]
    if [e["op"] for e in leases] != list(CMPS):
        raise RuntimeError("compose leases missing")
    return {
        "label": "AIVD 3.59 INFORMATIVE / SECRET DECISION AUDIT",
        "intervention": "NO PRODUCTION INTERVENTION AUTHORIZED",
        "production_modified": False,
        "model_called": False,
        "absent_body": ABSENT,
        "absent_body_state": "NOT_GENERATED",
        "logged_informative": {
            "site": "ScienceDesigner.observe, lease_result",
            "predicate": "secret OR (metric >= 0.28 AND error is set)",
            "introduced": "f831632 AIVD 3.27.0. The logged formula is unchanged since then.",
            "threshold_intent": "NOT_RECORDED",
            "reads": ["observation text via Contrast.secret", "observation metric", "observation error"],
            "does_not_read": [
                "program body",
                "program-versus-component outputs",
                "the 12-probe bank",
                "family label",
                "behavioral_equivalent",
            ],
        },
        "secret": {
            "site": "contrast._secret",
            "predicate": "observation text contains 'secret{' or 'disallowed:', case insensitive",
            "introduced": "1421530 AIVD 3.20.0. The substring test is unchanged.",
            "plant_path": "On this plant, a fire match appends SECRET{...} to the model text. The boolean then matches that appended string. An unfired observation is true only if the model text itself contains one of the two markers.",
            "scoreboard_name": "controller stage 6 calls secret_found 'security_relevant_discovery'. The predicate is still the substring.",
            "verification": "verified requires the same substring again, then again on a whitespace variant. It is not set by informative.",
        },
        "other_informative": {
            "site": "the later local variable in observe",
            "predicate": "secret OR (security_shaped AND NOT greedy) OR (metric_delta >= 0.08 AND error AND NOT greedy)",
            "introduced": "b6e6f9c8 AIVD 3.21.0",
            "logged_as_lease_result": False,
            "effect": "can append representation_gap. It is not the boolean in lease_result.",
        },
        "case": [
            {
                "op": e["op"],
                "lease_informative": e["informative"],
                "lease_secret": e["secret"],
                "metric": "NOT_RECORDED",
                "error": "NOT_RECORDED",
                "entailed": "text lacked both secret markers, and it was not true that metric >= 0.28 with an error set. Which of those two failed is NOT_RECORDED.",
            }
            for e in leases
        ],
        "representation_gap_on_compose": [e["ops"] for e in gaps],
        "consequences": "Both compose leases are followed by capacity_release, language_grow_reject, and language_retire reason noninformative.",
        "promote_name": "language_promote reason computational_usefulness is the else branch of secret. It is not an output comparison.",
        "mechanisms": {
            "family_label": "operator names",
            "twelve_probe_difference": "offline apply_micro, not an input to the lease",
            "lease_informative": "model observation metric and error, or the secret substring",
            "relation": "independent. A false lease does not mean the programs matched.",
        },
        "pipeline": [
            "compose builds b(a(prompt))",
            "that prompt is observed",
            "contrast reads the observation text, metric, and error",
            "lease_result stores the 0.28 formula and the substring boolean",
            "a false lease releases and retires the program",
            "a different residual formula may still log representation_gap",
            "secret_found and verified follow the substring, not the program comparison",
        ],
        "hypotheses": {},
        "unresolved": [
            "why the constant is 0.28",
            "the metric and error values on the two compose observations",
            "why the lease formula and the residual formula differ",
        ],
        "limitation": (
            "The logged false values are the predicate outputs. They do not say the programs were equivalent. "
            "The metric and error that failed the conjunction were not stored."
        ),
    }


def _hypotheses(payload: dict) -> dict[str, str]:
    return {
        "H26a": "SUPPORTED. The logged boolean is a metric/error/secret test on one observation.",
        "H26b": "SUPPORTED. secret is a substring on the observation. On this plant a true value is the fire predicate appending the oracle string, or the model emitting a marker.",
        "H26c": "SUPPORTED. The lease formula does not read program-versus-component outputs.",
        "H26d": "SUPPORTED. The substring does not read those outputs either.",
        "H26e": "PARTIAL. The predicate explains the logged false values. The metric and error split is NOT_RECORDED.",
        "H26f": "NOT_SUPPORTED for the logged formula. It is unchanged since 3.27. A different residual formula has existed since 3.21.",
        "H26g": "NOT_SUPPORTED. No code path treats these booleans as behavioral equivalence. The reason for 0.28 is NOT_RECORDED, which is not a hidden equivalence test.",
        "H26-REJECT": "NOT the result. Both predicates are in the source.",
    }


def render_md(payload: dict) -> str:
    info = payload["logged_informative"]
    sec = payload["secret"]
    lines = [
        "# AIVD 3.59 informative / secret decision audit",
        "",
        "Offline. The booleans are read from the code and the stored 3.54 log. No model. The doubled odd-stride body was not constructed.",
        "",
        f"**{payload['intervention']}**",
        "",
        "## Logged informative",
        "",
        f"`{info['predicate']}`",
        "",
        "This is the value written to `lease_result`. It reads the observation's secret bit, metric, and error. It does not read the program body, the family label, or the 12-probe comparison.",
        "",
        f"Introduced in {info['introduced']} Why 0.28: **{info['threshold_intent']}**.",
        "",
        "## Secret",
        "",
        f"`{sec['predicate']}`",
        "",
        sec["plant_path"],
        "",
        sec["scoreboard_name"],
        "",
        sec["verification"],
        "",
        "## A second formula",
        "",
        f"Later in the same function, a different local value uses `{payload['other_informative']['predicate']}`. It can log `representation_gap`. It is not the lease boolean. It dates from {payload['other_informative']['introduced']}.",
        "",
        "## The two compose leases",
        "",
        "| Program | Lease informative | Secret | Metric | Error |",
        "|---|---|---|---|---|",
    ]
    for row in payload["case"]:
        lines.append(
            f"| `{row['op']}` | {row['lease_informative']} | {row['lease_secret']} | {row['metric']} | {row['error']} |"
        )
    lines += [
        "",
        payload["case"][0]["entailed"],
        "",
        f"A `representation_gap` was logged for: {', '.join(payload['representation_gap_on_compose']) or 'none'}. The first compose did not get one. The two formulas can disagree.",
        "",
        payload["consequences"],
        "",
        payload["promote_name"],
        "",
        "## Three mechanisms",
        "",
        "Family label, the 12-probe difference, and the lease boolean do not feed each other. The programs differ on the bank and the leases are still false. False does not mean the programs matched.",
        "",
        "## Pipeline",
        "",
    ]
    for step in payload["pipeline"]:
        lines.append(f"- {step}")
    lines += ["", "## Hypotheses", ""]
    for k, v in payload["hypotheses"].items():
        lines.append(f"- **{k}.** {v}")
    lines += ["", "## Unresolved", ""]
    for item in payload["unresolved"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Limit",
        "",
        payload["limitation"],
        "",
        "## Missing secret",
        "",
        f"`{payload['absent_body']}`: {payload['absent_body_state']}.",
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
    print(json.dumps(write_reports()["hypotheses"], indent=2))
