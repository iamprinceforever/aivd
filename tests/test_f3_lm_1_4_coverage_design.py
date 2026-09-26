import json
from pathlib import Path

import pytest

from aivd_f3_lm.coverage_1_4 import (
    FORBIDDEN,
    MISSING_CATEGORIES,
    ExecutionRefused,
    TrialNotApplicable,
    attempt_model_execution,
    coverage_document,
    exercise,
    matrix_rows,
    matrix_sha256,
)
from aivd_f3_lm.grammar import apply_operator
from aivd_f3_lm.coverage_1_4 import _context, carrier_task, serialized_user
from aivd_f3_lm.private_context import generate_private_value
from aivd_f3_lm.coverage_1_4 import MASTER


def test_matrix_is_closed_and_nonvacuous():
    rows = matrix_rows()
    assert [row["category"] for row in rows if row["kind"] == "missing_category"] == list(MISSING_CATEGORIES)
    assert len(rows) == 13
    document = coverage_document()
    assert document["pair_count"] == 13
    assert document["calls"] == 27
    assert document["execution_authorized"] is False
    assert len(matrix_sha256()) == 64
    report = json.loads((Path(__file__).resolve().parents[1] / "reports" / "aivd_f3_lm_1_4_coverage_design.json").read_text())
    assert report["matrix_sha256"] == matrix_sha256()
    assert report["execution_authorized"] is False
    for row in rows:
        left = exercise(row, "A")
        right = exercise(row, "B")
        assert left["user_changed"] and right["user_changed"]
        assert left["private_in_user"] is False
        lowered = row["task"].lower()
        assert not any(phrase in lowered for phrase in FORBIDDEN)


def test_prior_noop_parameter_is_rejected_and_firewall_stays_closed():
    task = carrier_task()
    private = generate_private_value(MASTER, "vacuous-a", "hex64", task)
    baseline = _context(task, private, False)
    mutated = apply_operator(baseline, "FORMAT", 0)
    assert serialized_user(baseline) == serialized_user(mutated)
    with pytest.raises(TrialNotApplicable):
        exercise(
            {
                "row_id": "bad-00",
                "operator": "FORMAT",
                "param": 0,
                "second_user": False,
                "task": task,
            },
            "A",
        )
    with pytest.raises(ExecutionRefused):
        attempt_model_execution()
