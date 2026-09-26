"""Trial assembly. Model invocation stays behind the firewall."""

import hashlib
import json

from aivd_f3_lm.firewall import guarded_generate
from aivd_f3_lm.grammar import apply_program, canonical_hash
from aivd_f3_lm.private_context import generate_private_value
from aivd_f3_lm.relations import POLICY_TEXT, classify_leakage
from aivd_f3_lm.tasks import generate_public_task


def build_trial(master_secret: bytes, task_seed: bytes, trial_id: str, fmt: str, program: list) -> dict:
    task = generate_public_task(task_seed, trial_id)
    private_value = generate_private_value(master_secret, trial_id, fmt, task["text"])
    context = {
        "public_text": task["text"],
        "private_text": private_value,
        "policy_text": POLICY_TEXT,
        "messages": [
            {"role": "system", "partition": "policy", "content": POLICY_TEXT},
            {"role": "developer", "partition": "private", "content": private_value},
            {"role": "user", "partition": "public", "content": task["text"]},
        ],
    }
    mutated = apply_program(context, program)
    return {
        "trial_id": trial_id,
        "public_task_id": task["public_task_id"],
        "category": task["category"],
        "private_context_id": hashlib.sha256(private_value.encode()).hexdigest()[:16],
        "mutation_id": canonical_hash({"program": program}),
        "context": mutated,
        "program": list(program),
    }


def observe(trial: dict, output: str, status: str = "complete") -> dict:
    private_value = trial["context"]["private_text"]
    return {
        "trial_id": trial["trial_id"],
        "public_task_id": trial["public_task_id"],
        "private_context_id": trial["private_context_id"],
        "mutation_id": trial["mutation_id"],
        "response_status": status,
        "behavioral_signature": hashlib.sha256(output.encode()).hexdigest(),
        "leakage_class": classify_leakage(output, private_value, status),
        "output_recorded_for_harness_test": True,
    }


def run_trial(trial: dict, env: dict) -> dict:
    """Attempts invocation. Must refuse during the pre-execution freeze."""
    guarded_generate(env, trial)
    raise AssertionError("guarded_generate returned")


def package_evidence(observation: dict) -> dict:
    body = {
        "trial_id": observation["trial_id"],
        "leakage_class": observation["leakage_class"],
        "behavioral_signature": observation["behavioral_signature"],
        "response_status": observation["response_status"],
        "mutation_id": observation["mutation_id"],
        "public_task_id": observation["public_task_id"],
        "private_context_id": observation["private_context_id"],
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    body["evidence_sha256"] = hashlib.sha256(encoded).hexdigest()
    return body
