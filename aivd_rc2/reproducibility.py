"""Evidence-backed reproducibility contract for RC2 (see AIVD_RC2_REPRODUCIBILITY.md).

Compares two ledgers (e.g. two passes over the same corpus, or two dev runs) level by level:
  L1 configuration, L2 request, L3 trajectory structure, L4 behavioral signature,
  L5 security decision, and bitwise (content) equality as a separate metric.
Ledgers may use different pass ids / seeds; comparisons are then keyed by scenario id, and the
request-level check (L2) is evaluated only between calls whose full preceding context matched.
"""

from collections import defaultdict

SUPPORTED_LEVEL = "L2"


def _by_scenario(ledger):
    return {c["scenario_id"]: c for c in ledger.get("candidates", [])}


def l1_configuration(a, b) -> bool:
    keys = ("model", "model_digest", "runtime_digest", "allocation", "corpus_commitment")
    return all(a.get(k) == b.get(k) for k in keys) and a.get("config_hashes") == b.get("config_hashes")


def l2_request(a, b) -> dict:
    """Same-pass-id replays: for call i, if every earlier content hash matched, request hashes must match."""
    ra, rb = a.get("requests", []), b.get("requests", [])
    checked = matched = 0
    prefix_equal = True
    for x, y in zip(ra, rb):
        if prefix_equal:
            checked += 1
            matched += x["request_hash"] == y["request_hash"]
        prefix_equal = prefix_equal and x.get("content_sha256") == y.get("content_sha256")
    return {"checked": checked, "matched": matched, "holds": checked == matched}


def l3_structure(a, b) -> dict:
    def shape(ledger):
        per = defaultdict(list)
        for d in ledger.get("decisions", []):
            per[d["action"]].append(1)
        return {k: len(v) for k, v in sorted(per.items())}, [s["reason"] for s in ledger.get("stops", [])], sorted(ledger.get("explored", []))
    sa, sb = shape(a), shape(b)
    return {"a": sa[0], "b": sb[0], "explored_equal": sa[2] == sb[2], "stops_equal": sa[1] == sb[1],
            "holds": sa == sb}


def l4_signature(a, b) -> dict:
    ca, cb = _by_scenario(a), _by_scenario(b)
    ids = set(ca) | set(cb)
    same = sum(1 for s in ids if (s in ca) == (s in cb) and (s not in ca or ca[s].get("slots") == cb[s].get("slots")))
    return {"scenarios": len(ids), "equal": same, "holds": same == len(ids)}


def l5_decision(a, b) -> dict:
    ca, cb = _by_scenario(a), _by_scenario(b)
    ids = sorted(set(a.get("explored", [])) | set(b.get("explored", [])))
    def dec(c, s):
        x = c.get(s)
        return (x.get("promotion"), x.get("verification_decision")) if x else (None, None)
    same = sum(1 for s in ids if dec(ca, s) == dec(cb, s))
    return {"scenarios": len(ids), "equal": same, "holds": same == len(ids)}


def bitwise(a, b) -> dict:
    ra, rb = a.get("requests", []), b.get("requests", [])
    n = min(len(ra), len(rb))
    eq = sum(1 for i in range(n) if ra[i].get("content_sha256") == rb[i].get("content_sha256"))
    return {"compared": n, "equal": eq, "holds": n == len(ra) == len(rb) and eq == n}


def compare(a, b, *, same_pass=False) -> dict:
    out = {"L1_configuration": l1_configuration(a, b),
           "L3_trajectory_structure": l3_structure(a, b),
           "L4_behavioral_signature": l4_signature(a, b),
           "L5_security_decision": l5_decision(a, b),
           "bitwise_content": bitwise(a, b),
           "supported_level": SUPPORTED_LEVEL}
    if same_pass:
        out["L2_request"] = l2_request(a, b)
    return out
