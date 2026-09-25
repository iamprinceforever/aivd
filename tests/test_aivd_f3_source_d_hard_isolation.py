"""The discovery process is malicious. A denial from an API is not the evidence."""

import pytest

from aivd.experiments.aivd40.source_d.claim import evaluate
from aivd.experiments.aivd40.source_d.hard_isolation import run_audit
from aivd.experiments.aivd40.source_d.isolate import HISTORY_FIELDS, qualify


@pytest.fixture(scope="module")
def audit():
    return run_audit()


def _ok(audit, name):
    assert audit["attack_matrix"][name] == "PASS"


def test_process_and_filesystem_namespaces(audit):
    assert audit["isolation_level"] == "FILESYSTEM_ISOLATED"
    assert {"mnt", "pid", "net", "ipc"} <= set(audit["namespaces"])
    assert audit["uid"] == 0
    assert audit["distinct_uid"] == "NOT_VERIFIED"
    assert audit["image_hash"] == "NOT_RECORDED"


def test_modules_are_absent(audit):
    _ok(audit, "import_vault_absent")
    _ok(audit, "import_sealer_absent")
    _ok(audit, "import_aivd_absent")
    _ok(audit, "import_corpus_absent")
    _ok(audit, "dynamic_import_absent")
    _ok(audit, "pythonpath_injection_absent")


def test_secrets_fds_and_network_are_absent(audit):
    _ok(audit, "env_has_no_secrets")
    _ok(audit, "env_allowlist")
    _ok(audit, "no_extra_fds")
    _ok(audit, "no_loopback_service")
    _ok(audit, "no_host_shm")
    _ok(audit, "subprocess_contained")


def test_filesystem_escapes_fail_and_the_handle_remains(audit):
    _ok(audit, "vault_files_absent")
    _ok(audit, "host_workspace_absent")
    _ok(audit, "guessed_vault_path_absent")
    _ok(audit, "parent_stays_inside")
    _ok(audit, "symlink_escape_empty")
    _ok(audit, "pid_namespace")
    _ok(audit, "legitimate_handle")
    _ok(audit, "legitimate_has_no_plaintext")
    assert audit["passed"] is True


def test_claim_refuses_ready_and_rejects_weaker_boundaries(audit):
    assert audit["claim_status"] == "HISTORY_ISOLATION_UNVERIFIED"
    assert audit["provider_history_isolation"] == "NOT_VERIFIED"
    empty = qualify({})
    assert evaluate(empty, leakage_clean=True, corpus_valid=True, sealed=True)["status"] == "SAME_INTERPRETER_INVALID"
    assert (
        evaluate(empty, leakage_clean=True, corpus_valid=True, sealed=True, architecture="logical_only")["status"]
        == "LOGICAL_ONLY_SEPARATION"
    )
    verified = qualify({name: "TRUE" for name in HISTORY_FIELDS})
    assert (
        evaluate(verified, leakage_clean=True, corpus_valid=True, sealed=True, architecture="filesystem")["status"]
        != "SOURCE_D_READY"
    )


def test_matrix_repeats():
    first = run_audit()
    second = run_audit()
    assert first["attack_matrix"] == second["attack_matrix"]
    assert first["matrix_sha256"] == second["matrix_sha256"]
    assert first["audit_sha256"] == second["audit_sha256"]
    assert first["claim_status"] == second["claim_status"]
