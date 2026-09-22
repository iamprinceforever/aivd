#!/usr/bin/env python3
"""AIVD 3.48 offline mock: never-materialized PRIMARY invents after invent-cap release.

No Sacred. No TinyLlama. Deterministic unit-harness mock only.
"""
from __future__ import annotations

import json
from pathlib import Path

from aivd.science.atom import InventedAtom
from aivd.science.designer import ScienceDesigner
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import Micro, canonicalize_micro

REPO = Path(__file__).resolve().parents[1]


def _atom(aid: str, *, cls: str, origin: str) -> InventedAtom:
    idx = (hash(aid) % 7) - 3
    body = canonicalize_micro(
        Micro("MAPT", kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (idx,)))),))
    )
    prov = ("independent_rediscovery",) if origin == "independent_rediscovery" else ()
    return InventedAtom(
        atom_id=aid, body=body, semantic_class=cls, origin=origin, provenance=prov
    )


def main() -> dict:
    d = ScienceDesigner(seed_prompt="ab cd ef gh ij", seed=0, mode="3_39")
    # Saturate invent_cap with independent_rediscovery / redundant entries
    i = 0
    while d.inventor.occupancy() < INVENT_CAP:
        aid = f"atom_rd_fill_{i}"
        cls = "cls_shared" if i % 3 == 0 else f"cls_{i}"
        atom = _atom(aid, cls=cls, origin="independent_rediscovery")
        if not d.inventor._register(aid, lambda p, _k=i: p, why="fill"):
            break
        d.atom_synth.op_of[aid] = atom
        d.language.add_atom(atom, grow=False)
        if i % 2 == 0:
            d.language.promote(atom, reason="mock")
        i += 1

    occ_before = d.inventor.occupancy()
    primary = _atom("atom_primary_nm", cls="cls_untried", origin="atom_synth")
    d.atom_synth.board.remaining = [primary]
    never_mat = d.atom_explore.primary_target_never_materialized(
        list(d.atom_synth.board.remaining)
    )
    released = False
    if occ_before >= INVENT_CAP and never_mat:
        released = d._release_invent_cap_antistarve_slot(
            "slot for never-materialized primary atom"
        )
    occ_after_release = d.inventor.occupancy()
    registered = False
    if released and occ_after_release < INVENT_CAP:
        registered = d.inventor._register(
            primary.name(), lambda p: p, why="primary after antistarve"
        )
        if registered:
            d.atom_synth.op_of[primary.name()] = primary
            d.language.add_atom(primary, grow=False)
            d.atom_explore.observe_call(
                board_keys_before=[primary.key()],
                materialized_keys=[primary.key()],
                decision=d.atom_explore.decide(
                    [primary], lazy=True, invent_slots_left=1, leftover=12
                ),
            )

    result = {
        "invent_cap": INVENT_CAP,
        "occupancy_before": occ_before,
        "primary_never_materialized": never_mat,
        "released": released,
        "occupancy_after_release": occ_after_release,
        "primary_registered": registered,
        "primary_key": primary.key(),
        "primary_name": primary.name(),
        "antistarve_events": [
            e for e in d.methods_log if e.get("event") == "capacity_release"
        ],
        "verdict": (
            "PASS"
            if (released and registered and occ_before >= INVENT_CAP)
            else "FAIL"
        ),
    }
    out = REPO / "reports" / "aivd_3_48_offline_mock.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
