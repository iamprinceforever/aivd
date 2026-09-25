"""F2 machinery tests. They use fixtures, not the frozen sample."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest

from aivd.experiments.aivd40.stage_4_2.cel_exec import binary, execute as execute_cel
from aivd.experiments.aivd40.stage_4_2.conditions import empty, fill, run_named
from aivd.experiments.aivd40.stage_4_2.controls import StopExperiment, judge
from aivd.experiments.aivd40.stage_4_2.firewall import (
    ExperimentUnauthorized,
    refuse_frozen_cel,
    refuse_micro_sample,
)
from aivd.experiments.aivd40.stage_4_2.freeze import (
    BANK_HASH,
    CEL_COMMIT,
    CEL_VERSION,
    FROZEN_CEL,
    MICRO_SEED,
    SELECTION_HASH,
    FreezeRejected,
    document_hash,
    require_bank,
    require_selection,
    selection_document,
)
from aivd.experiments.aivd40.stage_4_2.ledger import public_row
from aivd.experiments.aivd40.stage_4_2.micro_exec import classify, execute as execute_micro
from aivd.experiments.aivd40.stage_4_2.observation import (
    BehavioralObservation,
    BehavioralSignature,
    canonical_string,
    make_signature,
)
from aivd.experiments.aivd40.stage_g2.micro_key import parse_micro_key

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "aivd" / "experiments" / "aivd40" / "stage_4_2"
PROBE = "qq"


def _sig(status: str, canon: dict | None, bank: str = BANK_HASH) -> BehavioralSignature:
    return make_signature(bank, (BehavioralObservation(status, canon),))


def test_frozen_documents_match_their_hashes():
    assert document_hash(require_bank()) == BANK_HASH
    assert document_hash(require_selection()) == SELECTION_HASH
    assert len(selection_document()["cel"]["sources"]) == 4


def test_probe_or_candidate_mutation_is_rejected():
    bank = require_bank()
    changed = json.loads(json.dumps(bank))
    changed["probes"][0]["value"] = "changed"
    with pytest.raises(FreezeRejected):
        require_bank(changed)
    selection = require_selection()
    mutated = json.loads(json.dumps(selection))
    mutated["cel"]["sources"].append("input + input + input")
    with pytest.raises(FreezeRejected):
        require_selection(mutated)


def test_micro_identity_and_difference_and_invalid():
    identity = execute_micro(parse_micro_key("TOK"), PROBE)
    other = execute_micro(parse_micro_key("AT:0"), PROBE)
    invalid = execute_micro(parse_micro_key("TOK"), "")
    assert identity.status == "VALID_IDENTITY"
    assert identity.canonical == canonical_string(PROBE)
    assert other.status == "VALID_OUTPUT"
    assert invalid.status == "INVALID_EXECUTION"
    again = execute_micro(parse_micro_key("TOK"), PROBE)
    assert again == identity


def test_cel_identity_difference_failure_and_types():
    identity = execute_cel("(input)", PROBE)
    other = execute_cel('input + "z"', PROBE)
    failed = execute_cel("no_such", PROBE)
    sized = execute_cel("size(input)", PROBE)
    unsupported = execute_cel("1.5", PROBE)
    assert identity.status == "VALID_IDENTITY"
    assert other.status == "VALID_OUTPUT"
    assert other.canonical == canonical_string(PROBE + "z")
    assert failed.status == "EXECUTION_FAILURE"
    assert sized.status == "VALID_OUTPUT"
    assert sized.canonical == {"t": "int", "v": "2"}
    assert unsupported.status == "UNSUPPORTED_OUTPUT"
    assert execute_cel("(input)", PROBE) == identity


def test_same_observations_match_across_languages():
    micro = execute_micro(parse_micro_key("TOK"), PROBE)
    cel = execute_cel("(input)", PROBE)
    left = make_signature(BANK_HASH, (micro,))
    right = make_signature(BANK_HASH, (cel,))
    assert left.content_id() == right.content_id()
    assert "language" not in BehavioralSignature.__dataclass_fields__
    different = make_signature(BANK_HASH, (execute_cel('input + "z"', PROBE),))
    assert left.content_id() != different.content_id()


def test_language_source_and_handle_do_not_enter_the_signature():
    row = BehavioralObservation("VALID_IDENTITY", canonical_string(PROBE))
    assert make_signature(BANK_HASH, (row,)).content_id() == make_signature(BANK_HASH, (row,)).content_id()
    fields = set(BehavioralSignature.__dataclass_fields__)
    assert fields == {"bank_hash", "results"}


def test_ambiguous_and_failure_do_not_create_dimensions():
    memory = empty()
    ambiguous = classify(PROBE, "ab", "a")
    assert ambiguous.status == "AMBIGUOUS"
    assert memory.add(_sig("AMBIGUOUS", None), "h", "fixture") is None
    assert memory.add(_sig("EXECUTION_FAILURE", None), "h", "fixture") is None
    assert memory.add(_sig("INVALID_EXECUTION", None), "h", "fixture") is None
    assert memory.add(_sig("UNSUPPORTED_OUTPUT", None), "h", "fixture") is None
    assert memory.dimensions() == ()


def test_conditions_are_isolated_until_the_shared_memory():
    row = _sig("VALID_IDENTITY", canonical_string(PROBE))
    other = _sig("VALID_OUTPUT", canonical_string("other"))
    x1 = empty()
    x2 = empty()
    fill(x1, [(row, "m", "micro")])
    fill(x2, [(other, "c", "cel")])
    assert x1.dimensions() != x2.dimensions()
    shared = empty()
    fill(shared, [(row, "m", "micro"), (other, "c", "cel")])
    assert set(shared.dimensions()) == set(x1.dimensions()) | set(x2.dimensions())
    fill(shared, [(row, "c2", "cel")])
    assert len(shared.dimensions()) == 2
    assert {item["language"] for item in shared.provenance} == {"micro", "cel"}


def test_named_conditions_and_frozen_samples_are_refused():
    for name in ("X1", "X2", "X3"):
        with pytest.raises(ExperimentUnauthorized):
            run_named(name)
    with pytest.raises(ExperimentUnauthorized):
        refuse_micro_sample(MICRO_SEED)
    for source in FROZEN_CEL:
        with pytest.raises(ExperimentUnauthorized):
            refuse_frozen_cel(source)
        with pytest.raises(ExperimentUnauthorized):
            execute_cel(source, PROBE)


def test_control_mismatch_stops():
    judge("C1", "same")
    with pytest.raises(StopExperiment):
        judge("C1", "distinct")
    with pytest.raises(StopExperiment):
        judge("C5", "same")


def test_ledger_has_no_source_text():
    row = public_row("h", 0, BehavioralObservation("VALID_IDENTITY", canonical_string(PROBE)))
    assert "expression" not in row
    assert "key" not in row


def test_cel_binary_blocks_the_frozen_sample_and_does_not_import_science():
    raw = subprocess.check_output(
        [str(binary())],
        input=json.dumps({"expression": "input", "input": PROBE}).encode(),
    )
    assert json.loads(raw.decode())["kind"] == "blocked"
    text = (PACKAGE / "cel_exec.py").read_text(encoding="utf-8")
    go = (PACKAGE / "celbin" / "main.go").read_text(encoding="utf-8")
    pin = (PACKAGE / "celbin" / "PIN").read_text(encoding="utf-8").strip()
    gomod = (PACKAGE / "celbin" / "go.mod").read_text(encoding="utf-8")
    assert "aivd.science" not in text
    assert "aivd.science" not in go
    assert "apply_micro" not in text
    assert pin == CEL_COMMIT
    assert f"github.com/google/cel-go {CEL_VERSION}" in gomod
    tree = ast.parse((PACKAGE / "micro_exec.py").read_text(encoding="utf-8"))
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert "aivd.science.micro" in imports


def test_cel_path_does_not_call_the_micro_interpreter(monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("micro was called from the CEL path")

    monkeypatch.setattr("aivd.science.micro.apply_micro", boom)
    monkeypatch.setattr("aivd.science.micro.eval_micro", boom)
    assert execute_cel("(input)", PROBE).status == "VALID_IDENTITY"


def test_package_has_no_historical_target_markers():
    needles = (
        "doubled-odd",
        "doubled-even",
        "reverse-each",
        "ODD",
        "secret{",
        "disallowed:",
        "Stage-5",
        "Stage-8",
        "Stage-9",
        "representation_gap",
    )
    for path in PACKAGE.rglob("*"):
        if path.suffix not in {".py", ".go", ".mod"}:
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            assert needle not in text
