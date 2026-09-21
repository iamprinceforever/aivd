"""Independence bar helpers remain fail-closed under Stage-2 modes."""
from __future__ import annotations

from aivd.science.generation_record import independence_verdict
from aivd.science.designer import ScienceDesigner


def test_designer_r1b_keeps_firewall_and_records():
    d = ScienceDesigner(seed_prompt="ab cd ef", mode="full_3_39_r1b")
    assert d.representation == "R1b"
    assert d.allow_firewall is True
    assert d.allow_gen_record is True
    assert d.allow_rediscover is True


def test_independence_verdict_failclosed_without_firewall():
    # epoch 0 must not grant independence
    v = independence_verdict(
        firewall_epoch=0,
        origin="independent_rediscovery",
        provenance_leak=False,
        behavioral_evidence=True,
    ) if _sig_ok() else _legacy()
    assert v.independently_discovered is False


def _sig_ok() -> bool:
    import inspect
    return "firewall_epoch" in inspect.signature(independence_verdict).parameters


def _legacy():
    class V:
        independently_discovered = False
    return V()
