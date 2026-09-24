# AIVD 4.0 experiment protocol

Design only. No run is authorized by this document.

## Bank

The bank is a list of strings, ordered, hashed, and frozen before any body is signed. The hash is part of every signature. Changing the bank is a different experiment, not a continuation.

The contexts have to vary token count, token length, character position, repetition, punctuation, and empty or minimal strings. They are chosen from that structural list, not from a target's expected output. The protocol does not know which string will separate which pair. That ignorance is a requirement.

The 12 probes used in 3.56 and 3.58 are a historical instrument. They were used after the odd/even difference was already the object of study. Using that list as the discovery bank would carry that study into the instrument. It may be used only as a labeled replay: "does the engine reproduce the already published distinctions?" A replay is not a discovery claim. The discovery bank is a different frozen list, written down before any target comparison, and it is not edited afterward.

Probes are not added because a pair looked equivalent and someone wanted a split. Probes are not removed because a pair looked distinct and someone wanted a merge.

## Execution

Each body is run on each probe by `apply_micro`, in bank order, once. No model. No plant. No secret string. Failures are statuses, not invented outputs. The signature is sealed before any comparison, and comparison does not rewrite it.

A rediscovery is the same procedure on a second body. There is no short circuit that copies the first body's signature because the keys look similar.

## Comparison outcomes

Only `OBSERVED_EQUIVALENT`, `OBSERVED_DISTINCT`, and `INSUFFICIENT_EVIDENCE`. Reports use those words. They do not say "equivalent," "redundant," or "novel behavior" without the observed-on-this-bank qualifier.

## Benchmark, before any live integration

The benchmark is a fixed set of already recorded bodies, named by key, plus compositions of those bodies under the general sequential rule. It includes:

- two runs of one even-stride body, which must be one dimension
- `MAPT(SLICE:0,2(TOK))` and `MAPT(SLICE:1,2(TOK))`, which must be distinct if and only if the frozen discovery bank separates them; the test does not add a probe to force the split
- the recorded even-stride double against its component
- the two 3.54 sequential programs against their recorded components
- a pair whose family labels differ
- a pair whose family labels match
- a lease that was `informative=false`, which must not by itself merge or split signatures

The benchmark does not include the doubled-odd body as an input. A test that constructs it in order to "see if the engine finds it" is a leak and fails review.

The benchmark measures, separately, false merge, false split, novelty, replay, provenance, recursion, and independence. It does not produce one score.

## Recursive mock

Start with an empty memory. Characterize recorded bodies in a declared order. The order is fixed before the run. Grow only by composing bodies already in memory. Admit a composition only by the signature rule. Record every parent link. Stop at the declared behavior budget.

A passing mock shows at least one dimension that is not the first body's dimension, and at least one later dimension whose parents are earlier dimensions. The pass is the parent link and the signature difference. It is not a hard-coded depth.

If the budget runs out before a second new dimension, the result is "budget exhausted," not a reason to raise `max_executed` or the episode budget.

## Twin

The existing designer path runs as it does now. The behavior path runs beside it on the same bodies the designer already emitted. The behavior path must not register an operator, must not release a slot, and must not write `methods_log`. Existing terminal states stay comparable to the pre-4.0 path.

## Fresh plant

Not in this phase. When it is authorized, the plant is new, the memory starts empty, the bank hash is the pre-registered one, and nothing is tuned after the first observation. Behavior experiments still do not increment `board.executed`.

## Held-out

A separate evaluation module may name a hidden target after discovery has finished. The discovery package must not import that module. The evaluation may say whether a stored dimension's representative body matches a held-out key. That sentence is an evaluation result. It is not fed back into memory.
