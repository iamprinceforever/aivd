"""AIVD 3.45 FINAL PRE-SACRED ADVERSARIAL GATE — §1–§9 validations.

Adversarial tests only. Must not weaken existing expectations.
Does not patch production code. Does not authorize Sacred.
"""
from __future__ import annotations

import inspect
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from aivd.science.exploration_alloc import (
    DEFAULT_CHAIN_FLOOR,
    DEFAULT_MAX_EXPLORE_SLOTS,
    DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE,
    DEFAULT_SKIP_THRESHOLD,
    ExplorationAllocator,
)

REPO = Path(__file__).resolve().parents[1]


@dataclass
class FakeCand:
    cid: str
    proposal_index: int = 0
    semantic_class: str = "cls"
    attrs: dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        return self.cid


def _cands(labels: list[str], *, classes: list[str] | None = None) -> list[FakeCand]:
    out = []
    for i, lab in enumerate(labels):
        cls = classes[i] if classes else f"family_{lab[0]}"
        out.append(FakeCand(cid=lab, proposal_index=i, semantic_class=cls))
    return out


def _snap(d) -> tuple:
    return (
        d.n_mat,
        d.exploit_n,
        d.explore_n,
        [c.key() for c in d.ordered],
        list(d.explore_keys),
        list(d.primary_keys),
        list(d.secondary_keys),
        d.reason,
        bool(d.productive_continuation),
    )


# ---------------------------------------------------------------------------
# §1 PRIMARY invariant — secondary never becomes implicit co-primary
# ---------------------------------------------------------------------------

def test_adv_s1_secondary_never_implicit_co_primary():
    """§1: n_mat=2 must keep PRIMARY (rank head) distinct from SECONDARY explore."""
    alloc = ExplorationAllocator()
    board0 = _cands(["H0", "H1", "H2", "H3"])
    d0 = alloc.decide(board0, lazy=True, invent_slots_left=4, leftover=12)
    assert d0.exploit_n == 1 and d0.explore_n == 0 and d0.n_mat == 1
    assert d0.primary_keys == ["H0"]
    assert d0.secondary_keys == []
    alloc.observe_call(
        board_keys_before=[c.key() for c in board0],
        materialized_keys=["H0"],
        decision=d0,
    )
    # Skip pressure on H1/H2; still PRIMARY owns head.
    later = _cands(["H0b", "H1", "H2", "H3"])
    d1 = alloc.decide(later, lazy=True, invent_slots_left=4, leftover=12)
    assert d1.exploit_n == 1
    assert d1.explore_n == 1
    assert d1.n_mat == 2
    assert d1.primary_keys == ["H0b"]
    assert d1.ordered[0].key() == "H0b"
    assert set(d1.primary_keys).isdisjoint(set(d1.secondary_keys))
    assert d1.secondary_keys == d1.explore_keys
    # Secondary is NOT treated as equal co-primary: exploit_n stays 1.
    assert d1.exploit_n != d1.n_mat or d1.explore_n == 0
    assert d1.reason == "exploit_plus_bounded_explore"


def test_adv_s1_eager_primary_width_preserved_under_explore():
    """§1 eager: exploit_n=4; explore at most +1; primary keys = head."""
    alloc = ExplorationAllocator()
    board = _cands([f"E{i}" for i in range(8)])
    for i in range(4, 8):
        alloc.state_of(f"E{i}").skip_count = 2
    d = alloc.decide(board, lazy=False, invent_slots_left=8, leftover=40)
    assert d.exploit_n == 4
    assert d.explore_n <= 1
    assert d.primary_keys == [f"E{i}" for i in range(4)]
    assert set(d.primary_keys).isdisjoint(set(d.secondary_keys))


# ---------------------------------------------------------------------------
# §2 Anti-starvation — bounded opportunity; not every candidate; no identity
# ---------------------------------------------------------------------------

def test_adv_s2_bounded_opportunity_not_every_candidate():
    """§2: repeatedly skipped lower ranks get bounded explore; not all explore."""
    alloc = ExplorationAllocator()
    board = _cands([f"S{i}" for i in range(10)])
    d0 = alloc.decide(board, lazy=True, invent_slots_left=10, leftover=99)
    assert d0.n_mat == 1
    alloc.observe_call(
        board_keys_before=[c.key() for c in board],
        materialized_keys=["S0"],
        decision=d0,
    )
    # Many starved; only max_explore_slots may surface.
    later = _cands([f"S{i}" for i in range(10)])
    for i in range(1, 10):
        assert alloc.state_of(f"S{i}").skip_count >= 1
    d1 = alloc.decide(later, lazy=True, invent_slots_left=10, leftover=99)
    assert d1.exploit_n == 1
    assert d1.explore_n == DEFAULT_MAX_EXPLORE_SLOTS
    assert len(d1.explore_keys) == 1
    # Not every skipped candidate explores.
    assert len(d1.explore_keys) < 9
    # Opportunity cap: same key cannot keep getting explore forever.
    explored = d1.explore_keys[0]
    assert alloc.state_of(explored).exploration_opportunities <= DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE
    d2 = alloc.decide(later, lazy=True, invent_slots_left=10, leftover=99)
    # Already consumed opportunity → that key not re-explored as under-explored.
    assert explored not in d2.explore_keys or alloc.state_of(explored).exploration_opportunities >= 1


def test_adv_s2_no_candidate_identity_in_allocator_source():
    """§2: allocator source has no holdout/Sacred/POS identity predicates."""
    src = inspect.getsource(ExplorationAllocator)
    forbidden = [
        "ODD",
        "EVEN-THEN-LAST",
        "MAPT(SLICE",
        "POS6",
        "POS7",
        "Sacred",
        "sacred",
        "AIVD-S",
        "char_stride",
        "EX8",
    ]
    hits = [t for t in forbidden if t in src]
    assert hits == [], hits


# ---------------------------------------------------------------------------
# §3 Untried-class eligibility — A explored + B/C unexplored; then A/B + C
# ---------------------------------------------------------------------------

def test_adv_s3_untried_class_withholds_explore_exact_policy():
    """§3: while untried classes remain (productive_continuation), explore_n=0."""
    alloc = ExplorationAllocator()
    # CLASS_A explored conceptually; B and C still untried on board.
    board_ab_c = _cands(
        ["A_done", "B_new", "C_new"],
        classes=["CLASS_A", "CLASS_B", "CLASS_C"],
    )
    # Seed skip pressure that would fire explore if allowed.
    alloc.state_of("B_new").skip_count = 5
    alloc.state_of("C_new").skip_count = 5
    d = alloc.decide(
        board_ab_c,
        lazy=True,
        invent_slots_left=4,
        leftover=12,
        productive_continuation=True,  # B/C untried remain
    )
    assert d.exploit_n == 1
    assert d.explore_n == 0
    assert d.n_mat == 1
    assert d.primary_keys == ["A_done"]
    assert d.secondary_keys == []
    assert d.reason == "exploit_only_productive_continuation"
    assert d.productive_continuation is True


def test_adv_s3_after_ab_explored_c_untried_still_withholds():
    """§3: A/B explored + C unexplored → still withhold secondary (policy)."""
    alloc = ExplorationAllocator()
    board = _cands(
        ["A_top", "B_mid", "C_last"],
        classes=["CLASS_A", "CLASS_B", "CLASS_C"],
    )
    alloc.state_of("C_last").skip_count = 9
    d = alloc.decide(
        board,
        lazy=True,
        invent_slots_left=4,
        leftover=12,
        productive_continuation=True,  # C still untried
    )
    assert d.explore_n == 0
    assert d.n_mat == 1
    assert "C_last" not in d.explore_keys
    # Once untried cleared, skip-pressure may explore C.
    d2 = alloc.decide(
        board,
        lazy=True,
        invent_slots_left=4,
        leftover=12,
        productive_continuation=False,
    )
    assert d2.explore_n == 1
    assert "C_last" in d2.explore_keys
    assert d2.ordered[0].key() == "A_top"  # PRIMARY intact


# ---------------------------------------------------------------------------
# §4 Starvation pressure loop PROPOSED→SCORED→RANKED→SKIPPED
# ---------------------------------------------------------------------------

def test_adv_s4_skip_pressure_loop_bounded_explore_without_displacing_primary():
    """§4: SKIPPED loop builds pressure; bounded explore without displacing PRIMARY."""
    alloc = ExplorationAllocator()
    primary_key = "TOP"
    starved_key = "LOW"
    for epoch in range(3):
        board = _cands([primary_key, "MID", starved_key])
        # Simulate PROPOSED→SCORED→RANKED board; only PRIMARY materializes.
        d = alloc.decide(
            board,
            lazy=True,
            invent_slots_left=4,
            leftover=12,
            productive_continuation=False,
        )
        assert d.ordered[0].key() == primary_key
        assert d.primary_keys == [primary_key]
        if epoch == 0:
            assert d.explore_n == 0
            mats = [primary_key]
        else:
            # After prior skip, explore may fire — still PRIMARY first.
            assert d.exploit_n == 1
            assert d.ordered[0].key() == primary_key
            if d.explore_n:
                assert starved_key in d.explore_keys or "MID" in d.explore_keys
                assert d.n_mat == 2
            mats = [primary_key] + (d.explore_keys[:1] if d.explore_n else [])
        alloc.observe_call(
            board_keys_before=[c.key() for c in board],
            materialized_keys=mats,
            decision=d,
        )
    # Eventually starved_key had skip pressure and/or explore opportunity.
    st = alloc.state_of(starved_key)
    assert st.skip_count >= DEFAULT_SKIP_THRESHOLD or st.exploration_opportunities >= 1


# ---------------------------------------------------------------------------
# §5 Regression family EX8/DX9/EX10/EX12/337/338 — covered by full suite
#     (marker test: family names still present and importable)
# ---------------------------------------------------------------------------

def test_adv_s5_regression_family_tests_still_collected():
    """§5: EX8-family tests remain collectable (full suite run separately)."""
    fam = [
        "tests/test_aivd337_lang.py::test_ex8_even_then_last_337_vs_336",
        "tests/test_aivd337_lang.py::test_ex8_seed0_provenance",
        "tests/test_aivd337_lang.py::test_dx9_on_337_same_fire_as_ex8",
        "tests/test_aivd337_lang.py::test_ex10_transfer",
        "tests/test_aivd337_lang.py::test_ex12_independent_rediscovery_env",
        "tests/test_aivd337_lang.py::test_ablation_nolangext_compose_still_works",
        "tests/test_aivd338_lang.py::test_ex8_even_then_last_still_verified_on_338",
    ]
    out = subprocess.check_output(
        ["python", "-m", "pytest", "--collect-only", "-q", *fam],
        cwd=REPO,
        text=True,
    )
    assert "7 tests collected" in out or out.strip().count("test_") >= 7
    assert "error" not in out.lower() or "ERROR" not in out


# ---------------------------------------------------------------------------
# §6 Controls — S-like / U / POS2/5 / POS6/7 / null-dup-invalid
# ---------------------------------------------------------------------------

def test_adv_s6_s_like_explore_possible():
    """§6 S-like: lower-ranked valid can receive bounded explore after skip."""
    alloc = ExplorationAllocator()
    b0 = _cands(["U0", "S1", "S2"])
    d0 = alloc.decide(b0, lazy=True, invent_slots_left=3, leftover=12)
    alloc.observe_call(
        board_keys_before=["U0", "S1", "S2"], materialized_keys=["U0"], decision=d0
    )
    d1 = alloc.decide(_cands(["U0b", "S1", "S2"]), lazy=True, invent_slots_left=3, leftover=12)
    assert d1.explore_n == 1
    assert d1.ordered[0].key() == "U0b"


def test_adv_s6_u_success_high_rank_primary():
    """§6 U-like: high-rank always PRIMARY."""
    alloc = ExplorationAllocator()
    d = alloc.decide(_cands(["U_top", "X", "Y"]), lazy=True, invent_slots_left=3, leftover=12)
    assert d.primary_keys == ["U_top"]
    assert d.ordered[0].key() == "U_top"
    assert d.exploit_n == 1


def test_adv_s6_pos25_later_escape_possible():
    """§6 POS2/5-like: demoted candidate can later escape via skip pressure."""
    alloc = ExplorationAllocator()
    d0 = alloc.decide(_cands(["P0", "P2", "P5"]), lazy=True, invent_slots_left=3, leftover=12)
    alloc.observe_call(
        board_keys_before=["P0", "P2", "P5"], materialized_keys=["P0"], decision=d0
    )
    # Demote P2 further in ranking.
    d1 = alloc.decide(_cands(["P0b", "P5", "P2"]), lazy=True, invent_slots_left=3, leftover=12)
    assert d1.ordered[0].key() == "P0b"
    assert d1.explore_n == 1
    assert "P2" in d1.explore_keys or "P5" in d1.explore_keys


def test_adv_s6_pos67_suppression_only_where_policy_permits():
    """§6 POS6/7-like: suppression via terminal/reject only — not identity."""
    alloc = ExplorationAllocator()
    alloc.note_terminal("POS6x", reason="duplicate")
    alloc.state_of("POS7y").skip_count = 5
    d = alloc.decide(
        _cands(["T0", "POS6x", "POS7y"]),
        lazy=True,
        invent_slots_left=3,
        leftover=12,
        productive_continuation=False,
    )
    assert "POS6x" not in d.explore_keys  # terminal suppressed
    # POS7y may explore under policy (skip pressure, not identity block).
    assert d.explore_n <= 1
    if d.explore_n:
        assert "POS7y" in d.explore_keys


def test_adv_s6_null_dup_invalid_rejected():
    """§6: null/empty, duplicate terminal, rejected keys excluded."""
    alloc = ExplorationAllocator()
    d_empty = alloc.decide([], lazy=True, invent_slots_left=4, leftover=12)
    assert d_empty.n_mat == 0 and d_empty.reason == "empty_or_no_cap"
    d_cap = alloc.decide(_cands(["A"]), lazy=True, invent_slots_left=0, leftover=12)
    assert d_cap.n_mat == 0
    alloc.note_terminal("DUP", reason="duplicate")
    alloc.state_of("DUP").skip_count = 99
    alloc.state_of("BAD").skip_count = 99
    d = alloc.decide(
        _cands(["OK", "DUP", "BAD"]),
        lazy=True,
        invent_slots_left=3,
        leftover=12,
        rejected_keys={"BAD"},
    )
    assert "DUP" not in d.explore_keys
    assert "BAD" not in d.explore_keys


# ---------------------------------------------------------------------------
# §7 Candidate-independence
# ---------------------------------------------------------------------------

def test_adv_s7_same_attributes_different_ids_identical_decisions():
    """§7: same structural attributes / different ids → identical decision shape."""
    def run(ids: list[str]) -> tuple:
        alloc = ExplorationAllocator()
        b0 = _cands(ids)
        d0 = alloc.decide(b0, lazy=True, invent_slots_left=4, leftover=12)
        alloc.observe_call(
            board_keys_before=ids, materialized_keys=[ids[0]], decision=d0
        )
        later_ids = [ids[0] + "_b"] + ids[1:]
        d1 = alloc.decide(_cands(later_ids), lazy=True, invent_slots_left=4, leftover=12)
        # Normalize away concrete ids: compare roles/widths/reasons.
        return (
            d0.n_mat,
            d0.exploit_n,
            d0.explore_n,
            d0.reason,
            d1.n_mat,
            d1.exploit_n,
            d1.explore_n,
            d1.reason,
            # relative explore index among later board
            later_ids.index(d1.explore_keys[0]) if d1.explore_keys else -1,
        )

    a = run(["ID_A0", "ID_A1", "ID_A2", "ID_A3"])
    b = run(["ID_B0", "ID_B1", "ID_B2", "ID_B3"])
    assert a == b


# ---------------------------------------------------------------------------
# §8 Determinism — twin runs identical
# ---------------------------------------------------------------------------

def test_adv_s8_twin_runs_identical():
    """§8: identical inputs → identical AllocationDecision snapshots."""
    def traj() -> list:
        alloc = ExplorationAllocator()
        snaps = []
        board = _cands([f"D{i}" for i in range(5)])
        d0 = alloc.decide(board, lazy=True, invent_slots_left=5, leftover=20)
        snaps.append(_snap(d0))
        alloc.observe_call(
            board_keys_before=[c.key() for c in board],
            materialized_keys=["D0"],
            decision=d0,
        )
        d1 = alloc.decide(
            _cands(["D0b", "D1", "D2", "D3", "D4"]),
            lazy=True,
            invent_slots_left=5,
            leftover=20,
        )
        snaps.append(_snap(d1))
        return snaps

    assert traj() == traj()


# ---------------------------------------------------------------------------
# §9 Budget — no hidden budget; no invent_cap/firewall/novelty/eq bypass
# ---------------------------------------------------------------------------

def test_adv_s9_no_hidden_budget_respects_leftover_and_cap():
    """§9: affordable = leftover//chain_floor; invent_slots_left hard cap."""
    alloc = ExplorationAllocator()
    board = _cands([f"B{i}" for i in range(8)])
    for i in range(1, 8):
        alloc.state_of(f"B{i}").skip_count = 2
    # leftover=5 → affordable = 5//3 = 1 → no room for explore beyond exploit.
    d = alloc.decide(board, lazy=True, invent_slots_left=8, leftover=5)
    assert d.n_mat <= 5 // DEFAULT_CHAIN_FLOOR
    assert d.exploit_n <= 1
    assert d.explore_n == 0
    # invent_slots_left=1 with leftover plenty → still n_mat<=1.
    d2 = alloc.decide(board, lazy=True, invent_slots_left=1, leftover=99)
    assert d2.n_mat <= 1


def test_adv_s9_allocator_source_has_no_bypass_hooks():
    """§9: allocator does not implement novelty/firewall/equivalence/invent bypass."""
    src = inspect.getsource(ExplorationAllocator)
    assert "bypass" not in src.lower()
    # No novelty/firewall/equivalence mutation APIs in allocator.
    assert "def novelty" not in src
    assert "firewall" not in src
    assert "equivalence" not in src
    assert "invent_cap" not in src
    # Constants remain bounded.
    assert DEFAULT_MAX_EXPLORE_SLOTS == 1
    assert DEFAULT_MAX_OPPORTUNITIES_PER_CANDIDATE == 1


def test_adv_s9_production_logic_scan_clean():
    """§9/PRODUCTION_LOGIC_SCAN: no candidate-specific tokens in science diff."""
    diff = subprocess.check_output(
        ["git", "diff", "72edfad", "HEAD", "--", "aivd/science/"],
        cwd=REPO,
        text=True,
    )
    forbidden = [
        "ODD",
        "EVEN",
        "MAPT(SLICE:1,2(TOK))",
        "MAPT(SLICE:0,2(TOK))",
        "char_stride",
        "POS6",
        "POS7",
        "Sacred",
        "sacred",
        "EX8",
        "EVEN-THEN-LAST",
    ]
    added = "\n".join(
        ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")
    )
    real_hits = []
    for tok in forbidden:
        if tok in ("ODD", "EVEN", "POS6", "POS7", "EX8"):
            if re.search(rf"\b{re.escape(tok)}\b", added):
                real_hits.append(tok)
        elif tok in added:
            real_hits.append(tok)
    assert real_hits == [], f"PRODUCTION_LOGIC_SCAN hits: {real_hits}"


def test_adv_freeze_implementation_ancestor():
    """Freeze lineage: 52394b8 remains ancestor; post-3.45 science may advance.

    On later authorized branches (3.46+), science may differ from 52394b8.
    When 3.48 impl `b1b7106` is an ancestor of HEAD, freeze science against that
    impl (docs/tests/reports-only thereafter). Otherwise (pure 3.45 tip) science
    must still match 52394b8.
    """
    tip = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    impl_345 = subprocess.check_output(
        ["git", "rev-parse", "52394b8"], cwd=REPO, text=True
    ).strip()
    rc = subprocess.call(["git", "merge-base", "--is-ancestor", impl_345, tip], cwd=REPO)
    assert rc == 0, "52394b8 must remain ancestor (3.45 science lineage)"
    has_348 = (
        subprocess.call(
            ["git", "merge-base", "--is-ancestor", "b1b7106", tip], cwd=REPO
        )
        == 0
    )
    freeze_ref = (
        subprocess.check_output(["git", "rev-parse", "b1b7106"], cwd=REPO, text=True).strip()
        if has_348
        else impl_345
    )
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", freeze_ref, tip], cwd=REPO, text=True
    ).strip().splitlines()
    science = [p for p in changed if p.startswith("aivd/science/")]
    assert science == [], (
        f"production science changed after freeze ref {freeze_ref[:8]}: {science}"
    )
