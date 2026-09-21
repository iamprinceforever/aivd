"""Phase-2 observational instrumentation tests — no Sacred required."""
from __future__ import annotations

from aivd.experiments.aivd340.phase2_constants import (
    MODE_B_ORIGIN,
    ODD_CAT_SELF_BODY_KEY,
    ODD_STRIDE_BODY_KEY,
    SEEDS,
)
from aivd.experiments.aivd340.phase2_hooks import observational_session
from aivd.experiments.aivd340.phase2_mode_b import build_odd_stride_atom, inject_odd_stride_controlled
from aivd.experiments.aivd340.phase2_recorder import Phase2Recorder, candidate_entry
from aivd.science.grow import pick_generation_action, propose_growth
from aivd.science.language import ExperimentLanguage
from aivd.science.lifecycle import rank_atoms
from aivd.science.representation import propose_growth_candidates


def test_seeds_frozen():
    assert list(SEEDS) == [0, 1, 2, 3, 4, 7, 11]


def test_odd_stride_body_key_historical():
    assert ODD_STRIDE_BODY_KEY == "MAPT(SLICE:1,2(TOK))"
    assert ODD_CAT_SELF_BODY_KEY == "MAPT(CAT(SLICE:1,2(TOK)|SLICE:1,2(TOK)))"


def test_build_mode_b_atom_provenance():
    atom = build_odd_stride_atom()
    assert atom.key() == ODD_STRIDE_BODY_KEY
    assert atom.origin == MODE_B_ORIGIN
    assert "controlled_availability_mode_b" in atom.provenance
    assert atom.novelty == "CONTROLLED_INPUT"


def test_candidate_entry_schema():
    c = candidate_entry(
        candidate_id="a",
        body_key=ODD_STRIDE_BODY_KEY,
        origin=MODE_B_ORIGIN,
        parent_id=None,
        representation_id="R1",
        growth_or_composition_op="INVENT",
        score=1.0,
        rank=1,
    )
    assert c["in_pool"] is True
    assert c["body_key"] == ODD_STRIDE_BODY_KEY


def test_pick_generation_identity_with_hooks():
    """Instrumented pick must return identical action to uninstrumented."""
    lang = ExperimentLanguage()
    # empty cands → None both ways
    a1 = pick_generation_action(lang, growth_cands=[], compose_pair=None, leftover=10)
    rec = Phase2Recorder(episode_id="id", condition_id="P2-R1-INSTR", mode="A", seed=0)
    with observational_session(rec, mode_b_inject=False):
        import aivd.science.designer as d

        a2 = d.pick_generation_action(lang, growth_cands=[], compose_pair=None, leftover=10)
    assert a1 == a2


def test_rank_atoms_identity_with_hooks():
    from aivd.science.atom_synth import propose_atoms

    atoms = propose_atoms(prompt="ab cd ef gh", question=True)[:4]
    r1 = rank_atoms(atoms, rejected_classes=set(), leftover=20, invariant_ready=True)
    rec = Phase2Recorder(episode_id="id", condition_id="P2-R1-INSTR", mode="A", seed=0)
    with observational_session(rec, mode_b_inject=False):
        import aivd.science.designer as d

        r2 = d.rank_atoms(atoms, rejected_classes=set(), leftover=20, invariant_ready=True)
    assert [a.key() for a in r1] == [a.key() for a in r2]
    # recorder should have invent pre_selection
    assert any(r.get("event_kind") == "invent" for r in rec.records)


def test_propose_growth_unchanged_under_hooks():
    lang = ExperimentLanguage()
    # no promoted → empty
    g1 = propose_growth_candidates(lang, identity="ab cd ef", leftover=20, policy="R1")
    rec = Phase2Recorder(episode_id="id", condition_id="P2-R1-INSTR", mode="A", seed=0)
    with observational_session(rec, mode_b_inject=False):
        g2 = propose_growth_candidates(lang, identity="ab cd ef", leftover=20, policy="R1")
    assert [a.key() for a in g1] == [a.key() for a in g2]


def test_mode_b_injection_labels_controlled():
    from aivd.science.designer import ScienceDesigner

    d = ScienceDesigner(seed_prompt="ab cd ef gh ij kl", seed=0, mode="full_3_39_r1")
    rec = Phase2Recorder(
        episode_id="b",
        condition_id="P2-R1-MODEB-ODD",
        mode="B",
        autonomous_discovery_credit=False,
        controlled_availability=True,
        seed=0,
    )
    did = inject_odd_stride_controlled(d, rec, enabled=True)
    assert did is True
    assert rec.mode_b_injected is True
    assert any(a.key() == ODD_STRIDE_BODY_KEY for a in d.language.invented)
    assert d.language.state_of(
        next(a for a in d.language.invented if a.key() == ODD_STRIDE_BODY_KEY).name()
    ) == "PROMOTED"
    # second call idempotent
    assert inject_odd_stride_controlled(d, rec, enabled=True) is False
    assert any(r.get("event_kind") == "mode_b_availability" for r in rec.records)
    assert any(e.get("event") == "mode_b_availability" for e in d.methods_log)


def test_mode_b_does_not_inject_finished_cat_self():
    atom = build_odd_stride_atom()
    assert atom.key() != ODD_CAT_SELF_BODY_KEY
    assert "CAT(" not in atom.key() or atom.key() == ODD_STRIDE_BODY_KEY


def test_autonomous_controlled_namespaces_separate():
    from aivd.experiments.aivd340.phase2_analyze import aggregate_outcomes

    eps = [
        {
            "mode": "A",
            "target_role": "S",
            "seed": 0,
            "mechanism": {"outcome": 1, "reading": "H2/earlier growth"},
            "instrumentation": {"integrity_ok": True, "records": []},
            "generation_records": [],
        },
        {
            "mode": "B",
            "target_role": "S",
            "seed": 0,
            "mechanism": {"outcome": 2, "reading": "H3 selection pressure"},
            "instrumentation": {"integrity_ok": True, "records": [], "mode_b_injected": True},
            "generation_records": [],
        },
    ]
    a = aggregate_outcomes(eps, mode="A", role="S")
    b = aggregate_outcomes(eps, mode="B", role="S")
    assert a["autonomous_discovery_credit"] is True
    assert b["autonomous_discovery_credit"] is False
    assert a["n"] == 1 and b["n"] == 1


def test_phase2_condition_locks():
    from aivd.experiments.aivd340.phase2_condition import phase2_condition
    from aivd.science.grow import REDISCOVERY_FLOOR
    from aivd.science.methods import INVENT_CAP

    a = phase2_condition("P2-R1-INSTR")
    b = phase2_condition("P2-R1-MODEB-ODD")
    assert a.episode_budget == 48 and b.episode_budget == 48
    assert a.representation == "R1" and b.representation == "R1"
    assert a.meta["mode"] == "A" and b.meta["mode"] == "B"
    assert b.meta["autonomous_discovery_credit"] is False
    assert REDISCOVERY_FLOOR == 5
    assert INVENT_CAP == 48


def test_fresh_plants_not_stage2():
    from aivd37.unknowns.llama_340_phase2 import PLANT_P2_S, PLANT_P2_U

    assert PLANT_P2_S == "AIVD340-P2-S"
    assert PLANT_P2_U == "AIVD340-P2-U"
    assert "S2" not in PLANT_P2_S and "S2" not in PLANT_P2_U
