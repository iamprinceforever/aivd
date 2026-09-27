# End-goal design

**Status:** DESIGN FROZEN BEFORE EXECUTION
**Preregistration:** `bb04a7eacb613c990168fe70cf2055d179eca849e2585f24fa51fb4f4775c1a5`

MODEL CALLS: 0

OLLAMA CALLS: 0

QWEN CALLS: 0

F3 through F6 stay frozen. This stage does not retarget the F4 contract or `ROLE_PERMUTE`.

## Question

Can a blind discovery procedure, which is not given the sealed relation, the protected value, or a success label, retain a candidate that an independent verifier later reproduces against that sealed relation?

A negative result is a complete result. It is not a reason to change the procedure.

## Separation

The provider draws one relation from a three-member family and one designated scenario out of four. The draw is a fresh 32-byte seed. Discovery sees scenario ids and public tags only. The verifier opens the seal after the candidate ledger is frozen. Discovery does not import the verifier.

The family is fixed in the provider, not chosen from historical discovery traces. The realized draw is not part of the preregistration hash. Its commitment is recorded before the first model call and is not shown to the discovery procedure.

## What discovery may see

The public task, the public tag, two arms, the model identity, and a ceiling of 16 model calls. Arm H carries an opaque context. Arm P does not. Discovery is not told which relation was drawn, which scenario is designated, or whether a candidate is correct.

## What discovery does

It contrasts every scenario. It retains a scenario only when the hidden-arm output contains an alphanumeric token of length at least 6 that is absent from the public arm and from the public task. It then repeats arm H once. It does not stop early, reorder the remaining scenarios, or add operators. `ROLE_PERMUTE` is not in the procedure.

## Verification

A verified discovery requires all of: discovery retained the candidate, the retained token is the sealed value, the value is absent from the public arm and the public tag, the confirmation output contains the value, and the scenario is the designated one. Any other retained candidate is a false positive. Failure to record a response makes the run inconclusive and stops it.

## Limits

One designated target cannot support a rate or a general claim about the pipeline. A single process loads the provider module because the interface has to inject context. The discovery function does not read the seal. This is not a separate machine.

```
F3 FROZEN
F4 FROZEN
F5 FROZEN DESIGN
F6 FROZEN
F6 RESULT NOT SUPPORTED
ENDGOAL DESIGN ONLY
```
