"""Fail-closed execution firewall. No weight loading."""

from aivd_f3_lm.commitments import (
    BYTE_VERIFICATION_COMPLETE,
    BYTE_VERIFIED_COMMITMENT,
    CHECKPOINT_COMMITMENT,
    DESIGN_COMMIT,
    DTYPE,
    QUANTIZATION,
    REVISION,
    TOKENIZER_BYTE_MANIFEST_HASH,
    TOKENIZER_CONTENT_SHA256,
)
from aivd_f3_lm.relations import POLICY_SHA256

# Hard guard. This phase does not authorize execution.
F3_LM_EXECUTION_AUTHORIZED = False


class ExecutionRefused(Exception):
    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


class ExecutionIntegrityFailure(Exception):
    pass


def firewall_reasons(env: dict) -> list:
    reasons = []
    if not F3_LM_EXECUTION_AUTHORIZED:
        reasons.append("F3_LM_EXECUTION_AUTHORIZED is false")
    if not env.get("execution_lock"):
        reasons.append("execution lock is not explicitly enabled")
    if env.get("experiment_authorized") is not True:
        reasons.append("experiment authorization is absent")
    if env.get("design_commit") != DESIGN_COMMIT:
        reasons.append("experiment commit does not match the design freeze")
    if env.get("revision") != REVISION:
        reasons.append("stale or substituted checkpoint revision")
    if env.get("checkpoint_commitment") != CHECKPOINT_COMMITMENT:
        reasons.append("checkpoint commitment mismatch")
    if TOKENIZER_CONTENT_SHA256 is None or env.get("tokenizer_sha256") != TOKENIZER_CONTENT_SHA256:
        reasons.append("tokenizer content hash is not frozen to locally verified bytes")
    if env.get("runtime_hash") != env.get("expected_runtime_hash"):
        reasons.append("runtime manifest mismatch")
    if not env.get("expected_runtime_hash"):
        reasons.append("runtime hash missing")
    if env.get("baseline_frozen") is not True:
        reasons.append("public-record baseline is not frozen")
    if env.get("baseline_hash") != env.get("expected_baseline_hash"):
        reasons.append("public-record baseline hash mismatch")
    if env.get("dtype") != DTYPE:
        reasons.append("dtype is not the frozen bfloat16 setting")
    if env.get("quantization") != QUANTIZATION:
        reasons.append("quantization is not NONE")
    if env.get("policy_sha256") != POLICY_SHA256:
        reasons.append("policy text hash changed")
    if env.get("chat_template_sha256") != env.get("expected_chat_template_sha256"):
        reasons.append("chat template hash mismatch")
    if env.get("do_sample") is not False or env.get("temperature") != 0.0:
        reasons.append("generation sampling is not the frozen deterministic setting")
    if not BYTE_VERIFICATION_COMPLETE:
        reasons.append("byte verification is incomplete")
    if BYTE_VERIFIED_COMMITMENT is None or env.get("byte_verified_commitment") != BYTE_VERIFIED_COMMITMENT:
        reasons.append("byte-verified checkpoint commitment is not frozen")
    if TOKENIZER_BYTE_MANIFEST_HASH is None or env.get("tokenizer_byte_manifest_hash") != TOKENIZER_BYTE_MANIFEST_HASH:
        reasons.append("tokenizer byte commitment is not frozen")
    if env.get("second_pass") != "PASS":
        reasons.append("second-pass byte verification is not PASS")
    return reasons


def guarded_generate(env: dict, trial: dict) -> None:
    """The only invocation entry point. It never loads weights."""
    reasons = firewall_reasons(env)
    if reasons:
        raise ExecutionRefused(reasons)
    # Even a fully matching environment cannot execute in this phase.
    raise ExecutionIntegrityFailure(
        "backend invocation is not linked in the F3-LM pre-execution freeze"
    )
