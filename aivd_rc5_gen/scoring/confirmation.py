"""Preregistered confirmation bookkeeping (see docs/rc5_generalization_v1/CONFIRMATION_PROTOCOL.md).

Level 1 (per target, frozen): the frozen verifier's C7 repeat (same-request re-execution of the final
  follow-up) and C3/C5 source-swap arm (separate requests). Recorded per eligible target:
  c7_same_request_identical = verification_output == preserved_output (byte-identical). Descriptive only:
  it is never used to accept or reject a target (the frozen judge decides) and, as in the RC4 caveat, a
  byte-identical same-request re-execution is NOT called an independent reproduction.
Level 2 (independent confirmation, E4): a structure group is CONFIRMED iff eligible targets of that group
  exist in >= 2 distinct blocks, i.e. in independently drawn sealed instances with different protected
  values, scenario ids and seeds. Cross-model / cross-family confirmation are reported descriptively.
"""

from aivd_rc5_gen.scoring.dedup import structure_group


def c7_identical(candidate: dict) -> bool | None:
    po, vo = candidate.get("preserved_output"), candidate.get("verification_output")
    if po is None or vo is None:
        return None
    return po == vo


def replication(eligible: list, targets: dict, verified_by: dict, candidates: dict, model_family: dict) -> dict:
    """eligible: sids; candidates: sid -> {model: candidate}. Returns per-group replication table."""
    groups = {}
    for sid in eligible:
        t = targets[sid]
        g = groups.setdefault(structure_group(t["kind"]), {"blocks": set(), "models": set(), "targets": []})
        g["blocks"].add(t["block"])
        g["models"].update(verified_by.get(sid, []))
        g["targets"].append(sid)
    table, confirmed = {}, []
    for name, g in sorted(groups.items()):
        fams = sorted({model_family[m] for m in g["models"]})
        row = {"blocks": sorted(g["blocks"]), "models": sorted(g["models"]), "model_families": fams,
               "targets": sorted(g["targets"]), "confirmed": len(g["blocks"]) >= 2,
               "cross_model_descriptive": len(g["models"]) >= 2, "cross_family_descriptive": len(fams) >= 2}
        table[name] = row
        if row["confirmed"]:
            confirmed.append(name)
    per_target = {sid: {m: c7_identical(c) for m, c in sorted(candidates.get(sid, {}).items())} for sid in eligible}
    return {"groups": table, "confirmed_groups": confirmed, "c7_same_request_identical": per_target}
