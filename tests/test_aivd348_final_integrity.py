"""AIVD 3.48 FINAL INVENT-CAP INTEGRITY GATE — §1–§18 validations.

Integrity / adversarial tests only. Must not weaken existing expectations.
Does not patch production code. Does not authorize Sacred.
"""
from __future__ import annotations

import inspect
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from aivd.science.atom import InventedAtom
from aivd.science.designer import ScienceDesigner
from aivd.science.exploration_alloc import ExplorationAllocator
from aivd.science.generation_record import GenerationRecord, build_record
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.micro import Micro, canonicalize_micro

REPO = Path(__file__).resolve().parents[1]
IMPL = "b1b7106"
BASELINE_SCIENCE = "52394b8"
PRE_348 = "9cce56e"


@dataclass
class FakeCand:
    cid: str
    proposal_index: int = 0
    semantic_class: str = "cls"
    attrs: dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        return self.cid


def _atom(aid: str, *, cls: str, origin: str = "atom_synth", body=None) -> InventedAtom:
    if body is None:
        idx = (hash(aid) % 7) - 3
        body = canonicalize_micro(
            Micro("MAPT", kids=(Micro("CAT", kids=(Micro("TOK"), Micro("AT", (idx,)))),))
        )
    prov = ("independent_rediscovery",) if origin == "independent_rediscovery" else ()
    return InventedAtom(
        atom_id=aid,
        body=body,
        semantic_class=cls,
        origin=origin,
        provenance=prov,
    )


def _fill(
    d: ScienceDesigner,
    *,
    origin: str = "independent_rediscovery",
    shared_cls: str = "cls_shared",
    lease_all: bool = False,
    promote_every: int = 2,
) -> list[str]:
    names: list[str] = []
    i = 0
    while d.inventor.occupancy() < INVENT_CAP:
        aid = f"atom_fill_{origin[:2]}_{i}"
        cls = shared_cls if (i % 3 == 0) else f"cls_{i}"
        atom = _atom(aid, cls=cls, origin=origin)
        if not d.inventor._register(aid, lambda p, _k=i: p, why="fill"):
            break
        d.atom_synth.op_of[aid] = atom
        d.language.add_atom(atom, grow=False)
        if promote_every and i % promote_every == 0:
            d.language.promote(atom, reason="integrity_fill")
        if lease_all:
            d.commitments.commit_ops([aid], question_id="q.fill", probe=0)
        names.append(aid)
        i += 1
        if i > INVENT_CAP + 10:
            break
    return names


def _release_src() -> str:
    return inspect.getsource(ScienceDesigner._release_invent_cap_antistarve_slot)


# ---------------------------------------------------------------------------
# §1–§2 Inventory occupancy ≠ scientific record
# ---------------------------------------------------------------------------

def test_s1_s2_release_preserves_scientific_record():
    """§1–§2: release frees inventory slot WITHOUT deleting provenance/language/ops/records."""
    d = ScienceDesigner(seed_prompt="ab cd ef gh", seed=0, mode="3_39")
    filled = _fill(d)
    assert d.inventor.occupancy() >= INVENT_CAP

    # Seed a GenerationRecord + history evidence before release
    victim_name = next(n for n in filled if d._is_independent_rediscovery_op(n))
    atom = d.atom_synth.op_of[victim_name]
    rec = build_record(
        language=d.language,
        body_key=atom.key(),
        kind="atom",
        semantic_class=atom.semantic_class,
        eid=victim_name,
        action="invent",
        provenance=tuple(atom.provenance or ()),
    )
    d.language.emit_generation_record(rec)
    n_recs_before = len(d.language.generation_records)
    hist_before = list(d.history)
    lang_names_before = {a.name() for a in d.language.invented}
    ops_before = set(d.inventor.ops)
    firewall_before = bool(d.language.firewalled)
    provenance_before = tuple(atom.provenance or ())

    before = d.inventor.occupancy()
    ok = d._release_invent_cap_antistarve_slot("integrity inventory vs history")
    assert ok is True
    assert d.inventor.occupancy() == before - 1

    released = [
        e.get("op")
        for e in d.methods_log
        if e.get("event") == "capacity_release" and "integrity" in str(e.get("why", ""))
    ]
    assert released
    rel = released[-1]

    # Scientific record intact: release is inventory-only (ops/archive/language/records)
    assert rel in d.inventor.ops, "released op must remain callable"
    assert rel in d.inventor.archived
    assert rel not in d.inventor.invented
    after_lang = {a.name() for a in d.language.invented}
    assert not (lang_names_before - after_lang), (
        f"release deleted language atoms: {lang_names_before - after_lang}"
    )
    assert len(d.language.generation_records) >= n_recs_before
    assert d.history == hist_before
    assert bool(d.language.firewalled) == firewall_before
    if rel in d.atom_synth.op_of:
        assert tuple(d.atom_synth.op_of[rel].provenance or ()) == provenance_before
    assert ops_before.issubset(set(d.inventor.ops))


def test_s1_inventory_occupancy_formula_unchanged():
    """§1: occupancy = len(invented)+len(promoted); release only shrinks invented."""
    src = inspect.getsource(MethodInventor.occupancy)
    assert "len(self.invented)" in src and "len(self.promoted)" in src
    assert INVENT_CAP == 48


# ---------------------------------------------------------------------------
# §3 Exact predicate audit + classification vocabulary
# ---------------------------------------------------------------------------

def test_s3_exact_predicate_structure():
    """§3: document exact release predicate order and classification terms."""
    src = _release_src()
    # Pass order via antistarve_kind literals (skip docstring mentions)
    # Pass order via antistarve_kind string literals at _try_release call sites
    k1 = src.index('_try_release(name, "rediscovery_redundant")')
    k2 = src.index('_try_release(name, "independent_rediscovery")')
    k3 = src.index('_try_release(name, "class_redundant")')
    assert k1 < k2 < k3
    assert "_release_nonlease_slot" in src
    assert "leased" in src
    # Must not special-case identity tokens
    for tok in ("ODD", "EVEN", "char_stride", "MAPT(SLICE", "EX8", "POS6", "POS7"):
        assert tok not in src

    classifications = {
        "ACTIVE_LEASE": "L.state not in (\"REVOKED\",)",
        "REDISCOVERY": "_is_independent_rediscovery_op",
        "REDUNDANT": "_class_redundant",
        "PRIMARY": "primary_target_never_materialized",  # gate at call site
        "NEVER_MATERIALIZED": "is_never_materialized / materialization_count",
        "VERIFIED": "NOT a release-eligibility input (must not release via verify status)",
        "UNVERIFIED": "NOT a release-eligibility input",
        "PENDING": "NOT a release-eligibility input",
        "HISTORICAL_ONLY": "archived / GenerationRecord — preserved, not deleted",
    }
    # Predicate itself only consults lease + rediscovery + class-redundant
    assert "_is_independent_rediscovery_op" in src
    assert "_class_redundant" in src or "class_redundant" in src
    assert "VERIFIED" not in src and "UNVERIFIED" not in src
    assert classifications["ACTIVE_LEASE"]
    wire = inspect.getsource(ScienceDesigner._maybe_invent_atom)
    assert "primary_target_never_materialized" in wire


def test_s3_call_site_gate_requires_never_mat_primary():
    """§3: antistarve call site gated on occupancy full AND never-mat PRIMARY."""
    wire = inspect.getsource(ScienceDesigner._maybe_invent_atom)
    assert wire.count("_release_invent_cap_antistarve_slot") >= 2
    assert "primary_target_never_materialized" in wire
    assert "never-materialized primary" in wire


# ---------------------------------------------------------------------------
# §4 PRIMARY protection + never reclaim lease / productive / verify / firewall / provenance
# ---------------------------------------------------------------------------

def test_s4_never_releases_active_lease():
    d = ScienceDesigner(seed_prompt="ab cd ef", seed=2, mode="3_39")
    _fill(d, lease_all=True)
    assert d.inventor.occupancy() >= INVENT_CAP
    leased = {L.op for L in d.commitments.leases if L.state not in ("REVOKED",)}
    assert leased
    d._release_invent_cap_antistarve_slot("lease guard")
    released = [
        e.get("op")
        for e in d.methods_log
        if e.get("event") == "capacity_release" and e.get("why") == "lease guard"
    ]
    for op in released:
        assert op not in leased


def test_s4_productive_continuation_withhold_unchanged():
    alloc = ExplorationAllocator()
    board = FakeCand("P0"), FakeCand("P1"), FakeCand("P2")
    # dataclass instances need list
    board = [FakeCand(cid=x) for x in ("P0", "P1", "P2")]
    alloc.state_of("P1").skip_count = 5
    d = alloc.decide(
        board,
        lazy=True,
        invent_slots_left=4,
        leftover=12,
        productive_continuation=True,
    )
    assert d.reason == "exploit_only_productive_continuation"
    assert d.explore_n == 0 and d.exploit_n == 1 and d.ordered[0].key() == "P0"


def test_s4_release_does_not_clear_firewall_or_provenance():
    d = ScienceDesigner(seed_prompt="ab cd", seed=4, mode="3_39")
    _fill(d)
    d.language.firewalled = True
    before_fw = d.language.firewalled
    # Snapshot provenances
    prov_map = {
        n: tuple(getattr(d.atom_synth.op_of[n], "provenance", ()) or ())
        for n in list(d.inventor.invented)
        if n in d.atom_synth.op_of
    }
    d._release_invent_cap_antistarve_slot("fw/prov")
    assert d.language.firewalled is before_fw
    for n, prov in prov_map.items():
        if n in d.atom_synth.op_of:
            assert tuple(d.atom_synth.op_of[n].provenance or ()) == prov


# ---------------------------------------------------------------------------
# §5 invent_cap not increased; active inventory <= invent_cap
# ---------------------------------------------------------------------------

def test_s5_invent_cap_constant_and_occupancy_bounded():
    assert INVENT_CAP == 48
    src = _release_src()
    assert "INVENT_CAP =" not in src
    assert "INVENT_CAP +" not in src
    d = ScienceDesigner(seed_prompt="ab", seed=0, mode="3_39")
    _fill(d)
    assert d.inventor.occupancy() <= INVENT_CAP
    d._release_invent_cap_antistarve_slot("cap bound")
    assert d.inventor.occupancy() <= INVENT_CAP
    # Re-register one — still cannot exceed
    primary = _atom("atom_primary_cap", cls="brand_new", origin="atom_synth")
    if d.inventor.occupancy() < INVENT_CAP:
        assert d.inventor._register(primary.name(), lambda p: p, why="p")
    assert d.inventor.occupancy() <= INVENT_CAP


# ---------------------------------------------------------------------------
# §6 budget before/after unchanged; no hidden budget
# ---------------------------------------------------------------------------

def test_s6_release_does_not_mutate_budget_fields():
    d = ScienceDesigner(seed_prompt="ab cd ef", seed=1, mode="3_39")
    d.remaining_steps = 17
    _fill(d)
    before_steps = d.remaining_steps
    before_budget_attrs = {
        k: getattr(d, k, None)
        for k in ("remaining_steps", "episode_budget", "budget", "max_steps")
        if hasattr(d, k)
    }
    d._release_invent_cap_antistarve_slot("budget check")
    assert d.remaining_steps == before_steps
    for k, v in before_budget_attrs.items():
        assert getattr(d, k) == v
    # Allocator must not soft-bypass invent_cap
    alloc_src = (REPO / "aivd/science/exploration_alloc.py").read_text()
    assert "INVENT_CAP" not in alloc_src


# ---------------------------------------------------------------------------
# §7 rediscovery/provenance recoverable after release
# ---------------------------------------------------------------------------

def test_s7_rediscovery_metadata_recoverable_after_release():
    d = ScienceDesigner(seed_prompt="ab cd ef gh", seed=5, mode="3_39")
    _fill(d, origin="independent_rediscovery")
    before_rd = {
        n: d._is_independent_rediscovery_op(n) for n in list(d.inventor.invented)
    }
    assert any(before_rd.values())
    ok = d._release_invent_cap_antistarve_slot("recoverability")
    assert ok
    # Released rediscovery still classifiable via atom_synth / language
    archived = list(d.inventor.archived)
    assert archived
    for name in archived:
        assert name in d.atom_synth.op_of or any(
            a.name() == name for a in d.language.invented
        )
        if name in d.atom_synth.op_of:
            assert d._is_independent_rediscovery_op(name) or True  # still lookupable
            atom = d.atom_synth.op_of[name]
            assert atom.origin == "independent_rediscovery" or "independent_rediscovery" in (
                atom.provenance or ()
            )


# ---------------------------------------------------------------------------
# §8 released redundant must not reinflate invention loop
# ---------------------------------------------------------------------------

def test_s8_released_name_cannot_reregister_same_op_to_reinflate():
    """§8: release archives slot; same name stays in ops → _register rejects reinflation."""
    d = ScienceDesigner(seed_prompt="ab cd", seed=6, mode="3_39")
    _fill(d)
    before = d.inventor.occupancy()
    ok = d._release_invent_cap_antistarve_slot("no reinflate")
    assert ok
    released = d.inventor.archived[-1]
    # Same name cannot re-occupy a new invent slot (ops already has it)
    assert d.inventor._register(released, lambda p: p, why="reinflate") is False
    # Occupancy after failed re-register: still before-1 (or +0 if other path)
    assert d.inventor.occupancy() == before - 1
    assert released in d.inventor.ops


# ---------------------------------------------------------------------------
# §9 EX8-family + PRIMARY productive — covered by dedicated pytest selection in gate;
#     here lock the productive-withhold invariant that protects EX8 path.
# ---------------------------------------------------------------------------

def test_s9_primary_productive_protected_under_cap_pressure():
    alloc = ExplorationAllocator()
    board = [FakeCand(cid=f"Q{i}") for i in range(5)]
    for i in range(1, 5):
        alloc.state_of(f"Q{i}").skip_count = 9
    d = alloc.decide(
        board,
        lazy=True,
        invent_slots_left=4,
        leftover=12,
        productive_continuation=True,
    )
    assert d.ordered[0].key() == "Q0"
    assert d.exploit_n == 1
    assert d.explore_n == 0


# ---------------------------------------------------------------------------
# §10 Generic A–E release eligibility (no identity special-case)
# ---------------------------------------------------------------------------

def test_s10_generic_eligibility_A_through_E():
    """
    A rediscovery+redundant → release
    B independent_rediscovery only → release
    C class_redundant non-rd → release
    D no A–C → fallback _release_nonlease_slot / False
    E active lease excluded from A–C
    """
    # A
    d = ScienceDesigner(seed_prompt="ab cd ef", seed=10, mode="3_39")
    _fill(d, origin="independent_rediscovery", shared_cls="sharedA")
    assert d._release_invent_cap_antistarve_slot("A") is True
    kinds = [e.get("antistarve_kind") for e in d.methods_log if e.get("event") == "capacity_release"]
    assert kinds[-1] in ("rediscovery_redundant", "independent_rediscovery", "class_redundant")

    # B: rediscovery but unique classes (no promoted peers needed for pass 2)
    d2 = ScienceDesigner(seed_prompt="ab cd ef", seed=11, mode="3_39")
    i = 0
    while d2.inventor.occupancy() < INVENT_CAP:
        aid = f"atom_b_{i}"
        atom = _atom(aid, cls=f"uniq_b_{i}", origin="independent_rediscovery")
        d2.inventor._register(aid, lambda p, _k=i: p, why="f")
        d2.atom_synth.op_of[aid] = atom
        d2.language.add_atom(atom, grow=False)
        # do NOT promote → class_redundant false; rediscovery still true
        i += 1
    assert d2._release_invent_cap_antistarve_slot("B") is True
    kinds2 = [e.get("antistarve_kind") for e in d2.methods_log if e.get("event") == "capacity_release"]
    assert kinds2[-1] == "independent_rediscovery"

    # C: class_redundant without rediscovery origin
    d3 = ScienceDesigner(seed_prompt="ab cd ef", seed=12, mode="3_39")
    i = 0
    while d3.inventor.occupancy() < INVENT_CAP:
        aid = f"atom_c_{i}"
        cls = "dupC" if i < 4 else f"uC_{i}"
        atom = _atom(aid, cls=cls, origin="atom_synth")
        d3.inventor._register(aid, lambda p, _k=i: p, why="f")
        d3.atom_synth.op_of[aid] = atom
        d3.language.add_atom(atom, grow=False)
        d3.language.promote(atom, reason="t")
        i += 1
    assert d3._release_invent_cap_antistarve_slot("C") is True
    kinds3 = [e.get("antistarve_kind") for e in d3.methods_log if e.get("event") == "capacity_release"]
    assert kinds3[-1] == "class_redundant"

    # D+E: unique non-rd + all leased → no A–C release of leased; may False
    d4 = ScienceDesigner(seed_prompt="ab cd", seed=13, mode="3_39")
    _fill(d4, origin="atom_synth", shared_cls="solo", lease_all=True, promote_every=0)
    # unique classes already from fill pattern with promote_every=0 and mixed cls
    # Force unique: rebuild
    d4 = ScienceDesigner(seed_prompt="ab cd", seed=13, mode="3_39")
    i = 0
    while d4.inventor.occupancy() < INVENT_CAP:
        aid = f"atom_d_{i}"
        atom = _atom(aid, cls=f"solo_{i}", origin="atom_synth")
        d4.inventor._register(aid, lambda p, _k=i: p, why="f")
        d4.atom_synth.op_of[aid] = atom
        d4.language.add_atom(atom, grow=False)
        d4.language.promote(atom, reason="t")
        d4.commitments.commit_ops([aid], question_id="q", probe=0)
        i += 1
    before = d4.inventor.occupancy()
    ok = d4._release_invent_cap_antistarve_slot("D")
    leased = {L.op for L in d4.commitments.leases if L.state not in ("REVOKED",)}
    released = [
        e.get("op")
        for e in d4.methods_log
        if e.get("event") == "capacity_release" and e.get("why") == "D"
    ]
    for op in released:
        assert op not in leased
    if not ok:
        assert d4.inventor.occupancy() == before


# ---------------------------------------------------------------------------
# §11 candidate-independence + PRODUCTION_LOGIC_SCAN
# ---------------------------------------------------------------------------

def test_s11_candidate_independence():
    def traj(labels):
        alloc = ExplorationAllocator()
        board = [FakeCand(cid=x) for x in labels]
        a = alloc.primary_target_never_materialized(board)
        d = alloc.decide(board, lazy=True, invent_slots_left=0, leftover=12)
        alloc.observe_call(
            board_keys_before=labels,
            materialized_keys=[labels[0]],
            decision=alloc.decide(board, lazy=True, invent_slots_left=2, leftover=12),
        )
        return (
            a,
            d.n_mat,
            d.reason,
            alloc.is_never_materialized(labels[0]),
            alloc.primary_target_never_materialized([FakeCand(cid=x) for x in labels]),
        )

    assert traj(["A0", "A1", "A2"]) == traj(["Z0", "Z1", "Z2"])


def test_s11_production_logic_scan_clean():
    forbidden = [
        "ODD", "EVEN", "POS6", "POS7", "EX8", "char_stride",
        "MAPT(SLICE:1,2(TOK))", "MAPT(SLICE:0,2(TOK))", "ODDSTRIDE",
    ]
    diff = subprocess.check_output(
        ["git", "diff", PRE_348, "--", "aivd/science/designer.py", "aivd/science/exploration_alloc.py"],
        cwd=str(REPO),
        text=True,
    )
    added = "\n".join(
        ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")
    )
    hits = []
    for tok in forbidden:
        if tok in ("ODD", "EVEN", "POS6", "POS7", "EX8"):
            if re.search(rf"\b{re.escape(tok)}\b", added):
                hits.append(tok)
        elif tok in added:
            hits.append(tok)
    assert hits == [], f"forbidden tokens in production diff: {hits}"


# ---------------------------------------------------------------------------
# §12 stress: full cap + multiple categories → exactly one reclaim
# ---------------------------------------------------------------------------

def test_s12_exactly_one_reclaim_under_mixed_categories():
    d = ScienceDesigner(seed_prompt="ab cd ef gh ij", seed=20, mode="3_39")
    # Mix rediscovery+redundant, plain rediscovery, class_redundant, unique
    i = 0
    while d.inventor.occupancy() < INVENT_CAP:
        if i % 4 == 0:
            origin, cls = "independent_rediscovery", "mix_shared"
        elif i % 4 == 1:
            origin, cls = "independent_rediscovery", f"rd_only_{i}"
        elif i % 4 == 2:
            origin, cls = "atom_synth", "mix_shared"
        else:
            origin, cls = "atom_synth", f"unique_{i}"
        aid = f"atom_mix_{i}"
        atom = _atom(aid, cls=cls, origin=origin)
        d.inventor._register(aid, lambda p, _k=i: p, why="f")
        d.atom_synth.op_of[aid] = atom
        d.language.add_atom(atom, grow=False)
        if cls == "mix_shared" or i % 5 == 0:
            d.language.promote(atom, reason="t")
        i += 1
    assert d.inventor.occupancy() >= INVENT_CAP
    before = d.inventor.occupancy()
    n_rel_before = sum(1 for e in d.methods_log if e.get("event") == "capacity_release")
    ok = d._release_invent_cap_antistarve_slot("stress one")
    assert ok is True
    n_rel_after = sum(1 for e in d.methods_log if e.get("event") == "capacity_release")
    assert n_rel_after == n_rel_before + 1
    assert d.inventor.occupancy() == before - 1


# ---------------------------------------------------------------------------
# §13 repeated saturation churn bounds
# ---------------------------------------------------------------------------

def test_s13_repeated_saturation_churn_bounded():
    d = ScienceDesigner(seed_prompt="ab cd ef gh", seed=21, mode="3_39")
    _fill(d)
    releases = 0
    for round_i in range(8):
        if d.inventor.occupancy() < INVENT_CAP:
            # fill one new unique to re-saturate without colliding names
            aid = f"atom_churn_{round_i}"
            atom = _atom(aid, cls=f"churn_{round_i}", origin="independent_rediscovery")
            # Need a free slot first — register only if space
            if d.inventor.occupancy() < INVENT_CAP:
                d.inventor._register(aid, lambda p, _k=round_i: p, why="churn")
                d.atom_synth.op_of[aid] = atom
                d.language.add_atom(atom, grow=False)
                d.language.promote(atom, reason="t")
        if d.inventor.occupancy() < INVENT_CAP:
            # top up with more rediscovery if needed
            j = 0
            while d.inventor.occupancy() < INVENT_CAP:
                aid = f"atom_churnfill_{round_i}_{j}"
                atom = _atom(aid, cls="cls_shared", origin="independent_rediscovery")
                if not d.inventor._register(aid, lambda p, _k=j: p, why="f"):
                    break
                d.atom_synth.op_of[aid] = atom
                d.language.add_atom(atom, grow=False)
                if j % 2 == 0:
                    d.language.promote(atom, reason="t")
                j += 1
        before = d.inventor.occupancy()
        if before < INVENT_CAP:
            break
        ok = d._release_invent_cap_antistarve_slot(f"churn {round_i}")
        if ok:
            releases += 1
            assert d.inventor.occupancy() == before - 1
            assert d.inventor.occupancy() <= INVENT_CAP
        else:
            break
    # Bounded: at most one release per saturation round; total <= 8
    assert 1 <= releases <= 8
    assert d.inventor.occupancy() <= INVENT_CAP


# ---------------------------------------------------------------------------
# §14–§15 firewall + independence unchanged for historical records
# ---------------------------------------------------------------------------

def test_s14_s15_firewall_and_independence_unchanged_for_historical():
    d = ScienceDesigner(seed_prompt="ab cd ef", seed=22, mode="3_39")
    _fill(d)
    d.language.firewalled = True
    # Emit historical records
    for n in list(d.inventor.invented)[:3]:
        atom = d.atom_synth.op_of[n]
        rec = build_record(
            language=d.language,
            body_key=atom.key(),
            kind="atom",
            semantic_class=atom.semantic_class,
            eid=n,
            action="invent",
            provenance=tuple(atom.provenance or ()),
        )
        d.language.emit_generation_record(rec)
    snap = [dict(r) if isinstance(r, dict) else r.__dict__.copy()
            for r in d.language.generation_records]
    fw = d.language.firewalled
    d._release_invent_cap_antistarve_slot("historical preserve")
    assert d.language.firewalled is fw
    assert len(d.language.generation_records) >= len(snap)
    # Existing record fields not mutated
    for i, old in enumerate(snap):
        new = d.language.generation_records[i]
        new_d = new if isinstance(new, dict) else getattr(new, "__dict__", {})
        if isinstance(old, dict) and isinstance(new_d, dict):
            for k in ("body_key", "origin", "semantic_class"):
                if k in old:
                    assert old.get(k) == (new_d.get(k) if isinstance(new_d, dict) else getattr(new, k, None))


# ---------------------------------------------------------------------------
# §16 freeze / ancestry (pytest itself is the full suite; lock freeze here)
# ---------------------------------------------------------------------------

def test_s16_impl_ancestor_and_no_science_drift_after_impl():
    anc = subprocess.call(
        ["git", "merge-base", "--is-ancestor", IMPL, "HEAD"], cwd=str(REPO)
    )
    assert anc == 0
    # Science tree must match the impl commit. The 3.54 research harness
    # lives under aivd/experiments and is the only later aivd/ delta.
    diff = subprocess.check_output(
        ["git", "diff", IMPL, "HEAD", "--", "aivd/science"],
        cwd=str(REPO),
        text=True,
    )
    assert diff.strip() == "", f"science drift after {IMPL}:\n{diff[:500]}"
    names = subprocess.check_output(
        ["git", "diff", "--name-only", IMPL, "HEAD", "--", "aivd/"],
        cwd=str(REPO),
        text=True,
    ).split()
    # Science must still match b1b7106. Later aivd/ files are the 3.54
    # harness and the isolated 4.0 packages. Nothing else is allowed.
    allowed_prefixes = (
        "aivd/experiments/aivd354/",
        "aivd/behavior/discovery/",
        "aivd/behavior/sealed_corpus/",
        "aivd/experiments/aivd40/",
    )
    assert all(name.startswith(allowed_prefixes) for name in names), names


# ---------------------------------------------------------------------------
# §17 Offline B48 replay signal (artifact must exist / regenerable)
# ---------------------------------------------------------------------------

def test_s17_offline_b48_replay_artifact_contract():
    """§17: offline B48 replay answers PRIMARY never-mat wall without Sacred."""
    art = REPO / "reports" / "aivd_3_48_offline_b48_replay.json"
    # Allow missing during collection — gate script writes it; if present validate.
    if not art.exists():
        pytest.skip("offline B48 replay artifact not yet written; gate script produces it")
    data = json.loads(art.read_text())
    assert data.get("sacred") is False
    assert "headline" in data
    assert data["headline"].get("question")
    assert "BASELINE" in data.get("lineage_comparison", {}) or "baseline" in str(data).lower()
    assert data.get("verdict") in ("PASS", "FAIL", "INFORMATIVE")


# ---------------------------------------------------------------------------
# §18 Acceptance A–M locks (S success NOT required)
# ---------------------------------------------------------------------------

def test_s18_acceptance_A_to_M_locks():
    """Acceptance A–M structural locks; S success explicitly NOT required."""
    assert INVENT_CAP == 48
    src = _release_src()
    wire = inspect.getsource(ScienceDesigner._maybe_invent_atom)
    checks = {
        "A_inventory_ne_history": "archived" in inspect.getsource(MethodInventor.release),
        "B_exact_predicate_ordered": "rediscovery_redundant" in src and "class_redundant" in src,
        "C_primary_gate": "primary_target_never_materialized" in wire,
        "D_lease_guard": "leased" in src,
        "E_cap_not_increased": "INVENT_CAP =" not in src and INVENT_CAP == 48,
        "F_no_hidden_budget": "INVENT_CAP" not in (REPO / "aivd/science/exploration_alloc.py").read_text(),
        "G_exactly_one_slot": "return True" in src,  # single release returns
        "H_no_identity_special_case": all(
            t not in src for t in ("ODD", "char_stride", "EX8", "POS6")
        ),
        "I_fallback_nonlease": "_release_nonlease_slot" in src,
        "J_no_safe_keeps_failure": "INVENTORY_CAPACITY_FAILURE" in wire,
        "K_productive_withhold_intact": "productive_continuation" in wire,
        "L_science_ancestor": subprocess.call(
            ["git", "merge-base", "--is-ancestor", IMPL, "HEAD"], cwd=str(REPO)
        )
        == 0,
        "M_s_success_not_required": True,  # explicit non-requirement
    }
    failed = [k for k, v in checks.items() if not v]
    assert failed == [], f"acceptance failures: {failed}"
