# AIVD 4.0 leakage model

Design only. Discovery and evaluation are different packages. Discovery does not import evaluation.

## Discovery may read

- a program body that the existing generator already emitted
- the frozen bank
- `apply_micro` results on that bank
- dimension ids and signatures already stored in this epoch
- body keys and generation ids as provenance

## Discovery may not read

- secret strings, including `SECRET{...}`
- `fire_odd_double` or any other plant predicate
- the doubled-odd body, its key, or a template that builds it
- planted vulnerability identifiers and ground-truth ids
- historical reports whose purpose is to name the target behavior
- `informative`, `secret`, and `representation_gap` as features
- `semantic_class_of` as a feature
- model completions
- a probe list edited after a comparison

The known doubled-odd program is a historical reference in this document so that reviewers can see the exclusion. It is not an input. Writing it into a discovery fixture, a default probe, or a unit test that the engine runs during search is leakage.

## Held-out evaluation

The evaluation package may contain one hidden key. It runs after memory is sealed. It may answer whether any stored representative key equals the hidden key. It may not insert a dimension, add a probe, or change a signature. The answer is not passed back to the frontier.

If the hidden key was never generated, the evaluation result is `NOT_GENERATED`. The engine is not run again to change that.

## The historical bank

The 3.56 probe list separates `MAPT(SLICE:0,2(TOK))` from `MAPT(SLICE:1,2(TOK))`. That fact is published. A discovery bank copied from that list is contaminated for any claim of the form "the engine found the odd/even distinction by itself." Replay on that list is allowed only under the label `HISTORICAL_REPLAY`.

The discovery bank is specified by structural categories before any body is executed: empty, one character, two characters, a repeated character, a short word, two words, punctuation, a longer multi-word line. The exact strings are fixed in the protocol file and hashed. They are not selected by measuring which string splits a named pair and keeping the ones that do.

## Epochs

Memory does not cross a firewall. A dimension id from epoch 1 is not a hit in epoch 2. Otherwise an independent rediscovery is scored as already known, which is a provenance leak.

## Budget

Behavior experiments do not change `board.executed`, `invent_cap`, or the episode budget. A change to those numbers in a branch that claims to be this engine is a failed isolation check, even if the signatures look right.

## Provenance

Each dimension records the body key that was executed and the parent dimension ids. A parent id that does not exist, or a body key that was not in the input set, is a failed integrity check. The engine does not invent a parent to make a chain look recursive.
