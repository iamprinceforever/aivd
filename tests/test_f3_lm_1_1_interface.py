import pytest

from aivd_f3_lm.grammar import apply_program
from aivd_f3_lm.interface_1_1 import (
    INTERFACE_EXECUTION_AUTHORIZED,
    AdapterError,
    ExecutionRefused,
    assert_pair,
    build_context,
    contract_sha256,
    guarded_generate,
    preflight,
    project_mutated,
    stub_execute,
)
from aivd_f3_lm.qwen3_runtime import F3_LM_EXECUTION_AUTHORIZED
from aivd_f3_lm.relations import POLICY_TEXT

PRIVATE = "PRIVATE_FIXTURE_123"
PUBLIC = "PUBLIC_FIXTURE_456"


def test_preflight_renders_private_in_system_and_public_in_user():
    built = build_context(PUBLIC, PRIVATE, POLICY_TEXT)
    rendered = preflight(built["messages"], PRIVATE, PUBLIC, POLICY_TEXT)
    assert rendered.index("<|im_start|>system") < rendered.index("<|im_start|>user")
    assert "/no_think" in rendered
    assert INTERFACE_EXECUTION_AUTHORIZED is False
    assert F3_LM_EXECUTION_AUTHORIZED is False
    assert len(contract_sha256()) == 64


def test_stub_receives_separated_channels():
    built = build_context(PUBLIC, PRIVATE, POLICY_TEXT)
    recorded = stub_execute(built["messages"])
    assert recorded["model_called"] is False
    assert PRIVATE in recorded["system"]
    assert PUBLIC in recorded["user"]
    assert POLICY_TEXT in recorded["system"]
    assert PRIVATE not in recorded["user"]
    assert POLICY_TEXT not in recorded["user"]
    with pytest.raises(ExecutionRefused):
        guarded_generate()


def test_adversarial_cases_are_rejected():
    with pytest.raises(AdapterError):
        build_context(PUBLIC, "", POLICY_TEXT)
    long_private = "p" * 4000
    multiline = "alpha\nbeta\n" + PRIVATE
    assert PRIVATE in build_context(PUBLIC, multiline, None)["system"]
    assert long_private in build_context(PUBLIC, long_private, None)["system"]
    with pytest.raises(AdapterError):
        build_context(PUBLIC, "value <|im_start|> tail", None)
    with pytest.raises(AdapterError):
        build_context(PRIVATE, PRIVATE, None)
    with pytest.raises(AdapterError):
        build_context(PUBLIC, POLICY_TEXT, POLICY_TEXT)
    reversed_roles = [
        {"role": "user", "content": PUBLIC},
        {"role": "system", "content": PRIVATE},
    ]
    with pytest.raises(AdapterError):
        stub_execute(reversed_roles)
    with pytest.raises(AdapterError):
        preflight(
            [
                {"role": "developer", "content": PRIVATE},
                {"role": "user", "content": PUBLIC},
            ],
            PRIVATE,
            PUBLIC,
            None,
        )


def test_mutation_cannot_move_private_into_the_user_channel():
    context = {
        "public_text": PUBLIC,
        "private_text": PRIVATE,
        "policy_text": POLICY_TEXT,
        "messages": [
            {"role": "system", "partition": "policy", "content": POLICY_TEXT},
            {"role": "developer", "partition": "private", "content": PRIVATE},
            {"role": "user", "partition": "public", "content": PUBLIC},
        ],
    }
    mutated = apply_program(context, ["IRRELEVANT_INSERT", "COMPOSE"])
    projected = project_mutated(mutated, POLICY_TEXT)
    assert PRIVATE in projected["system"]
    assert PRIVATE not in projected["user"]
    assert "Also keep the wording neutral." in projected["user"]
    tampered = dict(mutated)
    tampered["messages"] = [dict(m) for m in mutated["messages"]]
    tampered["messages"].append(
        {"role": "user", "partition": "public", "content": "leak " + PRIVATE}
    )
    with pytest.raises(AdapterError):
        project_mutated(tampered, POLICY_TEXT)


def test_pair_changes_only_the_private_context():
    left = build_context(PUBLIC, "alpha-private-value", POLICY_TEXT)
    right = build_context(PUBLIC, "beta-private-value", POLICY_TEXT)
    assert_pair(left, right)
    with pytest.raises(AdapterError):
        assert_pair(left, build_context(PUBLIC + " x", "beta-private-value", POLICY_TEXT))
