# Security-relevance investigation

**Status:** DESIGN ONLY

MODEL CALLS: 0

OLLAMA CALLS: 0

QWEN CALLS: 0

END-GOAL-2 remains frozen. Its three retained candidates stay historical false positives. This stage does not reclassify them and does not open their sealed notes.

## What is missing

Stateful discovery can retain a reproduced output difference. That difference is not a security finding. The missing layer asks whether the difference is security-relevant, without being told which hidden relation or protected value was sealed.

## Layers

Discovery records a behavioral candidate. Investigation turns that record into evidence and hypotheses. An independent verifier, which this engine does not call, is the only stage that may later see a sealed relation.

## Lifecycle

`BEHAVIORAL_CANDIDATE` means the preserved and contrast outputs differ and the trajectory has at least two turns. `INVESTIGATED` means the fixed probe library was applied to supplied observations. Promotion is then one of `NO_SECURITY_EVIDENCE`, `SECURITY_RELEVANT_CANDIDATE`, or `VERIFICATION_READY`. A wording difference alone is not security evidence. A preregistered boundary observation can make the candidate verification-ready. This package never assigns a verified-discovery status.

## Probes

The library is CF-A through CF-F, in that order. A probe is used only when the candidate structure makes it valid: history, a prior-value slot, an authorization slot, a branch, or a mutation. The investigator may take the next unused library id. It cannot invent a probe. Each selected probe consumes one probe unit. Investigation review and later verification have separate counters.

## Hypotheses

H1 through H8 match S1 through S8. Each record is `SUPPORTED_BY_OBSERVATION`, `PLAUSIBLE_BUT_UNTESTED`, `CONTRADICTED_BY_OBSERVATION`, or `INSUFFICIENT_EVIDENCE`. There is no numeric security score. Authorization probes separate `FUNCTIONAL_MISMATCH` from `SECURITY_VIOLATION`.

## Boundary

The engine rejects a hidden field, does not import the END-GOAL-2 provider or verifier, and refuses model dispatch. Replay checks probe order and output hashes from the stored observations.

The investigation layer has not yet demonstrated security discovery. It establishes only a general mechanism for investigating retained behavioral anomalies for security relevance without access to the hidden security target.
