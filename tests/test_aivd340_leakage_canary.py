"""AIVD 3.40 — leakage canary; R0 and R1 must both pass."""
from __future__ import annotations

from pathlib import Path

from aivd.science.audit import scan_discovery_target_leakage, scan_science_source
from aivd.science.representation import propose_atom_candidates, R0, R1


def test_discovery_target_leakage_clean():
    result = scan_discovery_target_leakage()
    assert result["pass"], result["leaks"]


def test_science_source_scan_clean():
    result = scan_science_source()
    assert result["pass"], result["leaks"]


def test_representation_module_in_leakage_scope():
    # representation.py is scanned; ensure file exists and is clean
    assert Path("aivd/science/representation.py").is_file()
    result = scan_discovery_target_leakage()
    assert not any(h.get("file") == "representation.py" for h in result["leaks"])


def test_r0_and_r1_candidate_bodies_lack_plant_secrets():
    prompt = "ab cd ef gh ij kl mn op"
    for pol in (R0, R1):
        cands = propose_atom_candidates(prompt=prompt, question=True, policy=pol)
        blob = " ".join(c.atom_id + c.why + c.key() for c in cands)
        for tok in (
            "AIVD340-LLAMA", "AIVD339-LLAMA", "SECRET{AIVD340_LLAMA",
            "SECRET{AIVD339_LLAMA", "Level-14", "FX8DoubleEven",
        ):
            assert tok not in blob


def test_canary_tokens_listed_in_audit():
    text = Path("aivd/science/audit.py").read_text()
    assert "AIVD340-LLAMA-CANARY" in text
    assert "AIVD340-LLAMA-ODDSTRIDE" in text
    assert "AIVD340-LLAMA-ROL1" in text
