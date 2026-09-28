# Next end-goal design

**Status:** DESIGN ONLY. Not executed. No sealed security target was created.

STATEFUL-1 showed that the pinned `qwen3:1.7b` runtime can keep a prior turn in the next request, that reset and branch requests do not inherit the wrong history, and that a label-blind policy can retain a trajectory-level signature for four non-security behaviors. That is not evidence of security discovery.

A later experiment, if it is separately preregistered, would need all of the following before any model call:

- a new experiment id, not `STATEFUL-1`, `F6`, or `F3-LM-2`
- a fresh sealed corpus whose security relation is drawn after the discovery code is frozen
- discovery code that cannot import the seal
- the same pinned model, runtime, and sampling, unless the preregistration changes them in advance
- one call per recorded turn, with raw bytes stored before scoring
- a frozen call ceiling
- confirmation by a repeat of the retained trajectory, then an evaluator that runs only after the ledger hash is frozen

This document does not define that corpus, that relation, or that ceiling. Writing them here would create the target this stage was forbidden to create.
