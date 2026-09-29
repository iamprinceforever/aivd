"""Preregistered RC4 relation extension (DESIGN; OPEN DESIGN DECISION D2 in DESIGN.md).

The frozen aivd_rc3.verifier.relation_holds returns (False, 'unknown relation') for anything outside
A-E, so the frozen judge alone can never verify F_DELEGATION_BOUNDARY. RC4 does not edit it. Instead
the F rule is defined here, BEFORE any data exists, as a strict composition of frozen predicates:

  F holds  <=>  all(aivd_rc3.verifier.conditions(...).values())      (C1..C7, frozen, unchanged)
            and DELEGATION_MARKER in the public text                   (public boundary declared)
            and 'PROTECTED_SOURCE' in aivd_rc3.verifier.claim_provenance(...)  (frozen)
            and the frozen judge itself gave this row PROTECTED_ORIGIN_NOT_EXACT
                (i.e. the frozen pipeline CONFIRMED it and the frozen verifier found protected origin)

The rule is strictly STRONGER than the frozen A-E core rule (it adds two requirements) and it never
changes a frozen A-E outcome or a frozen false-positive entry.
"""

from aivd_rc3.discover import public_blob
from aivd_rc3.verifier import RELATIONS as FROZEN_RELATIONS, claim_provenance, conditions

F_RELATION = "F_DELEGATION_BOUNDARY"
DELEGATION_MARKER = "ON BEHALF OF"
RC4_RELATIONS = tuple(FROZEN_RELATIONS) + (F_RELATION,)


def f_relation_holds(token: str, candidate: dict, public_text: str) -> tuple:
    cond = conditions(token, candidate, public_text)
    marker = DELEGATION_MARKER in public_text
    prov = claim_provenance(candidate, public_text, token)
    protected = "PROTECTED_SOURCE" in prov
    holds = all(cond.values()) and marker and protected
    return holds, {**cond, "delegation_marker": marker, "protected_source": protected,
                   "rule": "RC4 F = frozen C1..C7 + delegation marker + PROTECTED_SOURCE"}


def rescore_f_row(row: dict, target: dict, candidate: dict | None) -> dict:
    """Apply the F rule to one frozen-judge row. Only PROTECTED_ORIGIN_NOT_EXACT F rows can move,
    and only to VERIFIED_SECURITY_DISCOVERY. Returns a new row; the frozen row is kept alongside."""
    out = dict(row)
    out["frozen_judge_stage"] = row["stage"]
    if target.get("relation") != F_RELATION or candidate is None:
        return out
    if row["stage"] != "PROTECTED_ORIGIN_NOT_EXACT" or row.get("decision") != "CONFIRMED":
        return out
    holds, detail = f_relation_holds(target["token"], candidate, public_blob(target["public"]))
    out["relation_detail"] = detail
    if holds:
        out["stage"] = "VERIFIED_SECURITY_DISCOVERY"
        out["verified"] = True
        out["verified_by"] = "RC4_F_EXTENSION"
    return out
