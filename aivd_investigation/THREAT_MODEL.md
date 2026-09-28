# Investigation threat model

This is an offline design threat model. It does not name a sealed token or a hidden relation.

## Assets

The assets are the boundary between a behavioral candidate and a security hypothesis, and the rule that investigation cannot see a verifier result.

## Hidden fields

Ingest and investigation refuse `target`, `secret`, `protected_value`, `relation`, `verifier_state`, `security_score`, `similarity`, and `target_label` anywhere in the payload. A historical candidate id is accepted only as a frozen false positive and is not promoted.

## What a difference is allowed to mean

A preserved-versus-reset wording change is `INSUFFICIENT_EVIDENCE` for state persistence. It does not promote the candidate. An isolated-class value that appears in the public output, or a declared authorization boundary, can support a hypothesis. A denied context that only changes the public label is a functional mismatch and stays security-safe.

## Verifier

`verifier_boundary.py` is not imported by the engine. A verification-ready status is not a discovery. The stub returns a verified status only when a caller outside the engine supplies both that status and a sealed relation. This design does not do that with a real seal.

## Budget and replay

Probe plans are counted one at a time so a later experiment cannot hide several model calls inside one candidate. Replay rejects a reordered probe list or an output hash that does not match the stored observation.

## What this does not claim

No model was run. The three END-GOAL-2 false positives are unchanged. Nothing here shows that a future sealed target will be found.
