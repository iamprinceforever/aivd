"""AIVD 3.60 audit of representation_gap. Source and the stored log only."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "reports" / "aivd_3_54_sacred" / "runs" / "GATE_OPEN_B48_seed0.json"
REPORT_JSON = REPO / "reports" / "aivd_3_60_representation_gap_audit.json"
REPORT_MD = REPO / "reports" / "aivd_3_60_representation_gap_audit.md"
ABSENT = "MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))"
P1 = "cmp_atom_rd2_mapt_at_-1_atom_rd6_mapt_cat_at_-1_"
P2 = "cmp_atom_rd7_mapt_slice_1_2_tok_atom_rd8_mapt_ca"


def build() -> dict:
    designer = (REPO / "aivd/science/designer.py").read_text(encoding="utf-8")
    contrast = (REPO / "aivd/science/contrast.py").read_text(encoding="utf-8")
    if ABSENT in designer:
        raise RuntimeError("absent body is in designer")
    if "self.representation_gap" not in designer:
        raise RuntimeError("flag missing")
    # The flag is written. Nothing in science reads it back.
    reads = designer.count("self.representation_gap")
    if reads != 4:
        raise RuntimeError(f"unexpected flag sites: {reads}")
    gate = json.loads(GATE.read_text())
    log = gate["methods_log"]
    gaps = [e for e in log if e.get("event") == "representation_gap"]
    p2_at = next(i for i, e in enumerate(log) if e.get("event") == "representation_gap" and e.get("ops") == P2)
    nxt = log[p2_at + 1]["event"]
    return {
        "label": "AIVD 3.60 REPRESENTATION-GAP AUDIT",
        "intervention": "NO PRODUCTION INTERVENTION AUTHORIZED",
        "production_modified": False,
        "model_called": False,
        "absent_body": ABSENT,
        "absent_body_state": "NOT_GENERATED",
        "what_it_is": "A boolean log event and an unread flag. Not a stored number.",
        "formula": {
            "quote": "c.secret or (c.security_shaped and not c.greedy_metric) or (c.metric_delta >= 0.08 and c.error and not c.greedy_metric)",
            "gate": "that boolean, AND not c.secret, AND used_ops is non-empty, AND allow_intra",
            "dead_disjunct": "c.secret cannot open this gate, because the gate also requires not c.secret",
            "security_shaped": "secret or error_appeared or (error and metric >= 0.2)",
            "greedy_metric": "metric >= 0.55 and not secret and not error_appeared",
            "inputs": ["observation secret bit", "observation error", "observation metric", "metric delta versus the baseline observation"],
            "does_not_read": ["program body", "program outputs", "the 12-probe bank", "family label"],
            "threshold_intent": "NOT_RECORDED",
        },
        "history": {
            "residual_boolean": "b6e6f9c8 AIVD 3.21.0",
            "event_and_invent_call": "ed8059d2 AIVD 3.24.0",
            "declare_gap_call": "9a1bd064 AIVD 3.25",
            "formula_changed_later": False,
            "quality_definition": "NOT_RECORDED",
            "comment": "token-level residual without secret; current grammar may not preserve identity",
        },
        "sites": [
            "observe: the residual gate logs the event, then calls invent() and maybe _maybe_declare_gap()",
            "invent: logs a different why-string when hot indices exist and no intra-token method is compiled yet",
            "_maybe_declare_gap: sets the flag and does not log this event name",
        ],
        "flag_is_read": False,
        "consumers": {
            "the_flag": "never read",
            "the_branch": "calls _mark_hot_from_ops, invent(), and _maybe_declare_gap(). Those can add methods. They do not rank atom candidates.",
            "selection": "no read of the flag",
            "growth": "not an input to language growth or compose admission",
            "retirement": "retirement uses the lease boolean, which is computed earlier",
            "verification": "not an input",
            "secret": "the gate requires secret to be false",
            "termination": "not an input",
        },
        "usefulness": {
            "quote": 'reason = "secret" if c.secret else "computational_usefulness"',
            "introduced": "26615172 AIVD 3.36.0",
            "meaning": "the else branch of secret on an atom promote. Stored as the promote reason. Not a formula over outputs.",
            "related_to_gap": False,
        },
        "case": {
            "program_1": {
                "op": P1,
                "event": "not logged",
                "meaning": "The residual gate was false. This mode logs the event when the gate is true, and other events were logged, so this is not a silent true.",
                "metric": "NOT_RECORDED",
            },
            "program_2": {
                "op": P2,
                "event": "logged",
                "next_event": nxt,
                "invent_followed": nxt == "invent",
                "meaning": "The residual gate was true. invent() added no method, because the next log line is not invent. The program had already been retired by the lease path.",
                "metric": "NOT_RECORDED",
            },
            "n_gap_events": len(gaps),
        },
        "hypotheses": {},
        "unresolved": [
            "why metric_delta uses 0.08",
            "why security_shaped uses 0.2 and greedy uses 0.55",
            "the metric and error on either compose observation",
            "a definition of representation quality beyond the code comment",
        ],
        "limitation": "A logged gap is an observation-side gate. It is not evidence the program differed from its components, and a missing log is not evidence that it did not.",
    }


def _hypotheses(payload: dict) -> dict[str, str]:
    return {
        "H27a": "SUPPORTED as an observation-side boolean. It is not a stored numeric quality score.",
        "H27b": "NOT_SUPPORTED. The gate does not read program outputs.",
        "H27c": "PARTIAL. The same branch can call invent(). It does not rank candidates. On the second 3.54 program that call added nothing.",
        "H27d": "NOT_SUPPORTED as purely diagnostic. The flag is unread, but the branch calls invent().",
        "H27e": "SUPPORTED. Usefulness is the else of secret. The gap also requires the residual boolean. Either can occur without the other.",
        "H27f": "NOT_SUPPORTED. The gate requires secret to be false.",
        "H27g": "SUPPORTED. The comment says residual-without-secret. A definition of representation quality is NOT_RECORDED.",
        "H27-REJECT": "NOT the result. The gate is in the source.",
    }


def render_md(payload: dict) -> str:
    f = payload["formula"]
    case = payload["case"]
    lines = [
        "# AIVD 3.60 representation-gap audit",
        "",
        "Offline. The event is a boolean, not a score. No model. The doubled odd-stride body was not constructed.",
        "",
        f"**{payload['intervention']}**",
        "",
        "## Formula",
        "",
        f"`{f['quote']}`",
        "",
        f"The event is logged only when that value is true, secret is false, and the probe used an operator. {f['dead_disjunct']}.",
        "",
        f"`security_shaped` is `{f['security_shaped']}`. `greedy_metric` is `{f['greedy_metric']}`.",
        "",
        "Inputs are the observation's secret bit, error, metric, and metric delta. Program outputs, the 12-probe bank, and the family label are not inputs. Why 0.08: **NOT_RECORDED**.",
        "",
        "## What happens next",
        "",
        "The flag is written in three places and read in none. The observe branch then calls `invent()` and, when the mode allows it, `_maybe_declare_gap()`. Those can add methods. They do not rank atom candidates, admit a composition, retire a lease, or verify a secret.",
        "",
        "Retirement of the two compose programs used the lease boolean, which is computed earlier and is a different formula.",
        "",
        "## computational_usefulness",
        "",
        f"`{payload['usefulness']['quote']}`",
        "",
        "That string is the else of secret when an atom is promoted. It is stored as the reason. It is not the gap gate, and it is not an output comparison.",
        "",
        "## The two programs",
        "",
        f"`{case['program_1']['op']}`: event not logged. The gate was false. The metric is NOT_RECORDED.",
        "",
        f"`{case['program_2']['op']}`: event logged. The next log line is `{case['program_2']['next_event']}`, not `invent`, so that call added no method. The program was already retired. The metric is NOT_RECORDED.",
        "",
        "Both programs differ on the frozen bank. The gap does not say that, and its absence does not deny it.",
        "",
        "## History",
        "",
        f"The boolean is {payload['history']['residual_boolean']}. The event and the `invent()` call are {payload['history']['event_and_invent_call']}. The formula has not changed. A definition of representation quality is NOT_RECORDED. The code comment is: {payload['history']['comment']}.",
        "",
        "## Hypotheses",
        "",
    ]
    for k, v in payload["hypotheses"].items():
        lines.append(f"- **{k}.** {v}")
    lines += ["", "## Unresolved", ""]
    for item in payload["unresolved"]:
        lines.append(f"- {item}")
    lines += ["", "## Limit", "", payload["limitation"], "", "## Decision", "", "**NO PRODUCTION INTERVENTION AUTHORIZED.**", ""]
    return "\n".join(lines)


def write_reports() -> dict:
    payload = build()
    payload["hypotheses"] = _hypotheses(payload)
    REPORT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    REPORT_MD.write_text(render_md(payload))
    return payload


if __name__ == "__main__":
    print(json.dumps(write_reports()["hypotheses"], indent=2))
