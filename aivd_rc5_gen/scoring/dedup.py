"""Preregistered dedup / independence bookkeeping (same rules as RC4; re-implemented, no RC4 import).

Identity levels, all computed from frozen artifacts:
  target     sealed scenario_id (distinct rows of the committed block corpora; blocks never share ids)
  body       digest of the verified candidate's preserved_output; two different targets sharing a body
             digest -> both AMBIGUOUS (not counted)
  behavior   (structure_group(kind), frozen aivd_rc3.discover.slots(public, preserved, contrast)).
             Verified targets in the same behavioral class count as ONE independent discovery; the class
             representative is chosen deterministically (min scenario_id). The three RC3 public-id lexical
             transforms share one structure group.
  lineage    any verified row whose kind is excluded, or whose public/preserved text contains a
             POST-RC3-LOCAL-V1 or RC4 identity or value -> HISTORICAL (never counted)
Anything the rules cannot resolve (missing preserved/contrast output, slot error) -> AMBIGUOUS.
"""

from aivd_stateful.hashing import digest

from aivd_rc3.discover import slots

from aivd_rc5_gen import EXCLUDED_KINDS

STRUCTURE_GROUP = {"id_upper": "rc3_id_transform", "id_mixed": "rc3_id_transform",
                   "id_punct": "rc3_id_transform"}


def structure_group(kind: str) -> str:
    return STRUCTURE_GROUP.get(kind, kind)


def behavior_key(target: dict, candidate: dict):
    po, co = candidate.get("preserved_output"), candidate.get("contrast_output")
    if not po or co is None:
        return None
    try:
        s = slots(target["public"], po, co)
    except Exception:
        return None
    return (structure_group(target["kind"]), tuple(sorted(s.items())))


def classify(verified: list, targets: dict, *, historical_check=None) -> dict:
    """verified: (row, candidate) pairs with frozen stage VERIFIED_SECURITY_DISCOVERY, pooled over any
    set of (model, block) runs. The same target verified by several models is ONE target.
    Returns eligible / counted / ambiguous / historical / behavior_duplicates (scenario ids)."""
    ambiguous, historical, dup = set(), set(), set()
    bodies, keys = {}, {}
    for r, c in verified:
        sid = r["scenario_id"]
        t, c = targets[sid], c or {}
        if t["kind"] in EXCLUDED_KINDS or (historical_check and historical_check(t, c)):
            historical.add(sid)
            continue
        key = behavior_key(t, c)
        if key is None:
            ambiguous.add(sid)
            continue
        keys.setdefault(sid, key)
        bodies.setdefault(digest({"b": c["preserved_output"]}), set()).add(sid)
    for sids in bodies.values():
        if len(sids) > 1:
            ambiguous.update(sids)
    classes = {}
    for sid, key in keys.items():
        if sid in ambiguous or sid in historical:
            continue
        classes.setdefault(key, []).append(sid)
    counted = []
    for key, sids in classes.items():
        rep = min(sids)
        counted.append(rep)
        dup.update(s for s in sids if s != rep)
    eligible = sorted(s for sids in classes.values() for s in sids)
    return {"eligible": eligible, "counted": sorted(counted), "ambiguous": sorted(ambiguous),
            "historical": sorted(historical), "behavior_duplicates": sorted(dup)}
