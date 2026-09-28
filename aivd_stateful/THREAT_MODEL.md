# Stateful discovery threat model

This is an offline design threat model. It does not evaluate a model and it does not name a hidden target.

## Assets

The assets are trajectory identity, parent links, inherited prefixes, and the boundary between discovery state and any later verifier. A candidate may contain public inputs and supplied outputs. It must not contain a sealed relation, a protected value, a security label, or verifier state.

## Boundaries

`reject_hidden` refuses a metadata key in `relation`, `secret`, `protected_value`, `security_label`, `verifier_state`, `target`, or `target_token`. That is a key-name gate, not a scan of natural language. A later experiment still has to keep sealed files out of the discovery process.

`dispatch` refuses every call. `EXECUTION_AUTHORIZED` stays false. This package does not weaken the historical authorizers because it does not call them.

## Isolation failures

The failure this design is built to prevent is shared mutable history. Continue, branch, and reset return new objects. A branch prefix is a copied tuple of hashes, so a later parent object cannot change the child. A reset prefix is empty, so a preserved turn-2 state hash and a reset turn-2 state hash differ even when the public input matches. Two independent objects with the same inputs have the same digest, and advancing one does not change the other object.

## Budget hiding

A trajectory that takes several model calls must not be billed as one candidate. Each supplied output increments `turn_executions` by one. Branching and continuation have their own counters on top of that unit. An empty `create` is not a call.

## What this does not claim

Offline replay does not show that a model will exhibit a stateful behavior. It shows that a recorded trajectory can be checked without another model call. No discovery-performance claim follows from these tests.
