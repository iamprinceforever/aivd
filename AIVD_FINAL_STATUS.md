# AIVD — Final Status (RC1)

**Release commit (frozen code):** `aba2178f7d5638a276505e6c6605713ee750b363`, tag `AIVD-RC1`. Implementation commit: `907de80b13e2b854db9881f7a1514114f91f17a3`.
**Branch:** `research/aivd-endgame-3-autonomous-security-discovery`. **Tests:** 213 passed, 0 failed.
**Model / runtime:** qwen3:1.7b `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` / Ollama 0.34.4 `ad9c53441752620a2314a65a798a888d98df3636c8815ca044de591f82892ff4`.

## What AIVD can do
- Run blind, budgeted, fully recorded stateful trajectories (continue, reset, branch) against a pinned local model, with replayable hash chains and fail-closed authorization.
- Investigate retained candidates with a fixed generic probe library. Hypotheses accumulate evidence for and against, and a matched reset counterfactual is required before a candidate is promoted.
- Separate discovery, investigation and verification budgets, with every model call counted exactly once.
- Freeze and commit blind ledgers before any reveal, isolate passes from each other and from the seal, and keep protected values out of Git (tested).

## What it cannot yet do
- Discovery does not discriminate: every scenario is retained, because free-text outputs always differ.
- The novelty rule is case-sensitive, so a case-folded public identifier can be mistaken for a restricted value. This caused 1 security FP and 1 behavioral FP. The defect was found after the freeze and is not patched.
- Bit-level reproduction of a pass is not possible on this runtime, because outputs are nondeterministic under the pinned contract.
- Most generic violation types (10 of 12 targets) were not observed from this model under these prompts and predicates.

## Experimentally demonstrated
On fresh, sealed, pre-committed targets, a frozen pipeline autonomously verified 2 security targets (context isolation in both passes; information flow in Pass 2 only). Contamination and integrity checks held.

## Not demonstrated
Broad coverage across dimensions. Stable verification across passes: only 1 of 2 verified targets repeated. A false-positive-free verifier. Deterministic replay of model outputs. No claim is made about discoverability in general, about general model insecurity, or about future discovery rates.

## Outcomes
- Fresh targets verified: 2 (context isolation: both passes; information flow: P2 only).
- Targets missed: 10 (all INVESTIGATED_NO_SECURITY_EVIDENCE in both passes).
- False positives: 1 behavioral (P1), 1 security verification (P2), on two different benign information-flow distractors, both caused by the case-folding defect.
- Contaminated: no (NONE detected).
- Reproducible: at decision level, partially (retention 12/12, verification 1 of 2). At bit level, no.

## Final metrics

```
SECURITY TARGETS: 12
BENIGN DISTRACTORS: 12
PASSES: 2
TARGETS DISCOVERED: 12
TARGETS VERIFIED: 2
TARGETS MISSED: 10
BEHAVIORAL FPs: 1
SECURITY VERIFICATION FPs: 1
CONTAMINATION: NONE
INTEGRITY FAILURES: 0
TOTAL CALLS: 215
DISCOVERY CALLS: 150
INVESTIGATION CALLS: 61
VERIFICATION CALLS: 4
BUDGET: 215/384
DISCOVERED IN BOTH PASSES: 12
PASS ONLY DISCOVERIES: 0
```

## Completion gate
**Not VALIDATED.** Condition (2), dev E2E criteria, failed on E8 (runtime determinism). The
security verification FP and the post-freeze labeler defect are also reported. Conditions (1),
(3)–(13) otherwise held: suite passes, stateful execution/replay/investigation/authorization/
verifier and target isolation tests pass, no contamination, corpus sealed through both passes,
both ledgers complete, results reconstructable from the frozen commit plus the protected store, and
no historical stage modified (`tests/test_rc1_frozen.py`).

AIVD-RC1 completed a frozen, blinded, two-pass end-to-end security evaluation. The observed limitations are reported without post-hoc tuning.

After the reveal: stopped. There were no code changes, no retuning, no target replacement and no reruns.
