"""AIVD-RC4-MULTI-V1 test fixtures. No network, no Ollama, no model call, no real seal."""

import urllib.request

import pytest

SYNTH_SEED = b"\x5a" * 32  # throwaway synthetic seed; never the real corpus


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("real network call attempted in tests")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    yield


@pytest.fixture
def rc4_bound(monkeypatch):
    """Apply aivd_rc4_multi.bind for one test and restore every bound module attribute afterwards."""
    import aivd_post_rc3.authorize as auth
    import aivd_post_rc3.config as cfg
    import aivd_post_rc3.driver as drv
    import aivd_post_rc3.session as sess
    from aivd_rc4_multi.bind import BOUND, bind
    mods = {"authorize": auth, "config": cfg, "driver": drv, "session": sess}
    for mod, name in BOUND:
        monkeypatch.setattr(mods[mod], name, getattr(mods[mod], name))
    bind()
    yield


@pytest.fixture
def synthetic_local_v1():
    """Synthetic stand-in for the frozen LOCAL-V1 seal (NOT the real one)."""
    return {"values": {"feedfacecafe0001", "Synthetic note feedfacecafe0001."},
            "identities": {"sc-000000synth1", "sc-000000synth2"}}
