"""AIVD-RC5-GENERALIZATION-V1 test fixtures. No network, no Ollama, no model call, no real seal."""

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
    from aivd_rc5_gen.bind import BOUND, bind
    mods = {"authorize": auth, "config": cfg, "driver": drv, "session": sess}
    for mod, name in BOUND:
        monkeypatch.setattr(mods[mod], name, getattr(mods[mod], name))
    bind()
    yield


@pytest.fixture
def synthetic_prior():
    """Synthetic stand-ins for the frozen LOCAL-V1 and RC4 records (NOT the real ones)."""
    from aivd_rc5_gen.scan.contamination import gen_key_fingerprints, rc4_f_fingerprints
    return {"LOCAL_V1": {"values": {"feedfacecafe0001", "Synthetic note feedfacecafe0001."},
                         "identities": {"sc-000000synth1", "sc-000000synth2"}, "fingerprints": gen_key_fingerprints()},
            "RC4": {"values": {"feedfacecafe0004", "Synthetic note feedfacecafe0004."},
                    "identities": {"sc-00000synth41", "sc-00000synth42"}, "fingerprints": rc4_f_fingerprints()}}


@pytest.fixture
def synth_blocks():
    from aivd_rc5_gen.provider.generator import draw_block
    return {b: draw_block(b, SYNTH_SEEDS[b], synthetic=True) for b in (1, 2, 3)}
