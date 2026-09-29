"""AIVD-RC5-GENERALIZATION-V1 test fixtures. No network, no Ollama, no model call, no real RC5 seal."""

import urllib.request

import pytest

SYNTH_SEEDS = {1: b"\x51" * 32, 2: b"\x52" * 32, 3: b"\x53" * 32}  # throwaway synthetic seeds; never real


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("real network call attempted in tests")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    yield


@pytest.fixture
def rc5_bound(monkeypatch):
    """Apply aivd_rc5_gen.bind for one test and restore every bound module attribute afterwards."""
    import aivd_post_rc3.authorize as auth
    import aivd_post_rc3.config as cfg
    import aivd_post_rc3.driver as drv
    import aivd_post_rc3.session as sess
    from aivd_rc5_gen.bind import BOUND
    mods = {"authorize": auth, "config": cfg, "driver": drv, "session": sess}
    for mod, name in BOUND:
        monkeypatch.setattr(mods[mod], name, getattr(mods[mod], name))
    yield


@pytest.fixture
def synthetic_prior():
    """Synthetic stand-ins for the frozen prior records (NOT the real ones)."""
    from aivd_rc5_gen.scan.contamination import gen_kind_fingerprints, rc4_template_fingerprints
    return {"RC3": {"values": {"feedfacecafe0003"}, "identities": {"sc-00000synth31"}, "fingerprints": set()},
            "LOCAL_V1": {"values": {"feedfacecafe0001", "Synthetic note feedfacecafe0001."},
                         "identities": {"sc-000000synth1", "sc-000000synth2"}, "fingerprints": gen_kind_fingerprints()},
            "RC4": {"values": {"feedfacecafe0004", "Synthetic note feedfacecafe0004."},
                    "identities": {"sc-00000synth41", "sc-00000synth42"}, "fingerprints": rc4_template_fingerprints()}}


@pytest.fixture
def synth_blocks():
    from aivd_rc5_gen.provider.generator import draw_block
    return {b: draw_block(b, SYNTH_SEEDS[b], synthetic=True) for b in (1, 2, 3)}


@pytest.fixture
def synth_corpus(synth_blocks):
    """Synthetic assembled corpus + common order + ordered manifest."""
    from aivd_rc3.provider import commit, public_manifest
    from aivd_rc5_gen.assemble import assemble
    from aivd_rc5_gen.orders import order_record, ordered_manifest
    asm = assemble(synth_blocks)
    cc = commit(asm)
    rec = order_record({b: public_manifest(synth_blocks[b]) for b in synth_blocks}, cc)
    return {"blocks": synth_blocks, "assembled": asm, "commitment": cc, "order": rec,
            "ordered": ordered_manifest(public_manifest(asm), rec["order"])}
