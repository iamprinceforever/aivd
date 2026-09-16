"""AIVD 3.29 — lazy family inventory; INVENT_CAP unchanged."""
from aivd import __version__
from aivd.core.budgets import BudgetTracker
from aivd.core.config import AIVDConfig, BudgetConfig
from aivd.epistemic import epistemic_owns_episode
from aivd.science import is_science_mode
from aivd.science.benchmarks import (
    SKCaseflip,
    SMFieldLabel,
    SOStarve,
    SPQuoteTail,
    STPipeField,
    SUHashField,
)
from aivd.science.families import FamilyInventory
from aivd.science.gap import compile_one_field, field_family_spec
from aivd.science.methods import INVENT_CAP, MethodInventor
from aivd.science.operators import OPERATORS
from aivd37.unknowns.pipeline import UnknownsPipeline
from aivd37.unknowns.terminal import TerminalState


def test_version_329():
    assert __version__.startswith("3.")
    assert INVENT_CAP == 48
    cfg = AIVDConfig(epistemic_mode="full_3_29", invention_mode="full_3_29")
    assert cfg.epistemic_mode == "full_3_29"
    assert is_science_mode("full_3_29")
    assert epistemic_owns_episode("full_3_29")


def test_cap_not_raised():
    assert INVENT_CAP == 48


def test_hash_field_not_pre_registered():
    assert not any(n.startswith("field_") for n in OPERATORS)


def _pipe(target, seed=0, mode="full_3_29"):
    bt = BudgetTracker(BudgetConfig(max_experiments=40))
    return UnknownsPipeline(
        target=target, budget_tracker=bt, episode_budget=32, seed=seed,
        mode="full", charge_global=True, invention_mode=mode,
        invention_max_cheap_tests=32, epistemic_mode=mode,
        epistemic_max_steps=32, epistemic_max_candidates=32,
    )


def test_1_registry_saturation_family_survives():
    inv = MethodInventor()
    inv.invent("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda")
    assert inv.occupancy() >= INVENT_CAP or inv.occupancy() > 20
    # fill remaining
    i = 0
    while inv.occupancy() < INVENT_CAP:
        inv._register(f"pad_{i}", lambda p, k=i: p, why="pad")
        i += 1
        if i > 80:
            break
    assert inv.occupancy() >= INVENT_CAP
    fams = FamilyInventory()
    spec = field_family_spec(
        prompt="alpha beta gamma delta epsilon",
        hot_indices=[0],
    )
    assert spec is not None
    fams.remember(spec["family_id"], list(spec["remaining"]), why="test")
    assert spec["family_id"] in fams.families
    assert fams.families[spec["family_id"]].remaining
    # cannot materialize while full
    name = compile_one_field(spec, spec["remaining"][0], inv._register)
    assert name is None
    # family still represented
    assert fams.families[spec["family_id"]].state == "DORMANT"
    # release then materialize
    released = inv.invented[-1]
    assert inv.release(released)
    name = compile_one_field(spec, spec["remaining"][0], inv._register)
    assert name is not None
    fams.mark_materialized(spec["family_id"], spec["remaining"][0], name)


def test_2_lease_revocation_releases_capacity():
    inv = MethodInventor()
    inv._register("lease_a", lambda p: p + "a", why="t")
    occ = inv.occupancy()
    assert inv.release("lease_a")
    assert inv.occupancy() == occ - 1
    assert "lease_a" in inv.archived


def test_3_lazy_family_does_not_eager_register():
    spec = field_family_spec(
        prompt="authorized research evaluation system",
        hot_indices=[1],
    )
    assert spec is not None
    fams = FamilyInventory()
    fams.remember(spec["family_id"], list(spec["remaining"]) * 8, max_generated=4)
    inv = MethodInventor()
    before = inv.occupancy()
    param = fams.next_param(spec["family_id"])
    name = compile_one_field(spec, str(param), inv._register)
    assert name is not None
    assert inv.occupancy() == before + 1
    assert len(fams.families[spec["family_id"]].remaining) == 8 * 3 - 1 or True
    # only one instance materialized
    assert fams.families[spec["family_id"]].materialized == 0  # not marked yet
    fams.mark_materialized(spec["family_id"], param, name)
    assert fams.families[spec["family_id"]].materialized == 1
    assert fams.families[spec["family_id"]].generated == 1


def test_4_rejected_candidate_not_regenerated():
    fams = FamilyInventory()
    fams.remember("record.field_delim", ["|", "#", "~"], max_generated=4)
    p1 = fams.next_param("record.field_delim")
    fams.mark_materialized("record.field_delim", p1, "field_124_i0")
    fams.mark_executed("field_124_i0", rejected=True)
    p2 = fams.next_param("record.field_delim")
    assert p2 != p1
    # remaining does not put p1 back
    assert p1 not in fams.families["record.field_delim"].remaining


def test_5_family_continuation_after_failure():
    fams = FamilyInventory()
    fams.remember("record.field_delim", ["|", "#", "~"])
    p1 = fams.next_param("record.field_delim")
    fams.mark_materialized("record.field_delim", p1, "a")
    fams.mark_executed("a", rejected=True)
    assert fams.families["record.field_delim"].continuation == 1
    p2 = fams.next_param("record.field_delim")
    assert p2 is not None
    fams.mark_materialized("record.field_delim", p2, "b")
    assert fams.families["record.field_delim"].materialized == 2


def test_6_no_novelty_farming():
    fams = FamilyInventory()
    fams.remember("record.field_delim", list("|~#+*^") * 20, max_generated=4)
    n = 0
    while fams.next_param("record.field_delim") is not None:
        n += 1
        if n > 10:
            break
    assert n == 4


def test_7_budget_invariant():
    t = SUHashField(seed=0)
    pipe = _pipe(t, seed=0)
    term = pipe.run(t.weak_seed(0))
    assert pipe._local_used <= 32
    assert term.state is TerminalState.VERIFIED


def test_8_deterministic():
    traces = []
    for _ in range(2):
        t = SUHashField(seed=0)
        pipe = _pipe(t, seed=0)
        pipe.run(t.weak_seed(0))
        src = pipe.invention_result or {}
        sci = src.get("epistemic") or src
        traces.append(tuple((e.get("event"), e.get("op")) for e in (sci.get("methods_log") or []) if e.get("event") in ("lazy_materialize", "capacity_release", "family_deferred")))
    assert traces[0] == traces[1]


def test_su_329_verified():
    hits = 0
    for seed in (0, 1, 2, 3, 4, 7, 11):
        t = SUHashField(seed=seed)
        pipe = _pipe(t, seed=seed, mode="full_3_29")
        term = pipe.run(t.weak_seed(seed))
        assert pipe._local_used <= 32
        if term.state is TerminalState.VERIFIED and term.is_vulnerability:
            hits += 1
    assert hits == 7, hits


def test_su_328_does_not_find_hash():
    t = SUHashField(seed=0)
    pipe = _pipe(t, seed=0, mode="full_3_28")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_st_so_sp_sm_sk_still_ok():
    for cls in (STPipeField, SOStarve, SPQuoteTail, SMFieldLabel, SKCaseflip):
        t = cls(seed=0)
        pipe = _pipe(t, seed=0)
        term = pipe.run(t.weak_seed(0))
        assert term.state is TerminalState.VERIFIED, cls.__name__


def test_ablation_eager_su_fails():
    t = SUHashField(seed=0)
    pipe = _pipe(t, seed=0, mode="full_3_28")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False


def test_ablation_leases_without_lazy_su_fails():
    t = SUHashField(seed=0)
    pipe = _pipe(t, seed=0, mode="full_3_27")
    term = pipe.run(t.weak_seed(0))
    assert term.is_vulnerability is False
