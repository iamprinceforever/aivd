# AIVD 3.18 Audit

## Q1. Did we add another discovery algorithm?
No. `GlobalEpistemicArbiter` allocates a single 32-slot experiment budget across
existing proposers (residual, axis, invention, openworld). Discovery logic is
reused through `ExperimentProposal`. Default `epistemic_mode=off` ≈ 3.17.

## Q2. Did we inflate budget to pass?
No. Primary 32. Every environment interaction charges `GlobalLedger`.
`sum(experiment_costs) <= global_budget` is a unit invariant.

## Q3. Did we special-case OpenWorld (`if openworld: reserve 13`)?
No. Soft protected floor is evidence-driven, revocable, subsystem-agnostic.
A branch *earns* continuation when evidence is causal/behavioral, uncertainty
remains, a completion path is plausible, and work is not a failed repeat.

## Q4. Did we use greedy EIG alone?
No. Score includes `ΔP_completion × expected_terminal_value`. Synthetic trap:
greedy path_share=0.0, arbiter path_share=1.0.

## Q5. Did we retune vs sacred holdouts X–V / W?
No. Sacred first-run results are immutable. No holdout-named rules in
`aivd/epistemic/` discovery path (`scan_epistemic_source` PASS).

## Q6. Default off?
Yes. `epistemic_mode=off`. Shadow vs authoritative are explicit opt-in.

## Q7. Reservations revocable?
Yes. `ReservationBook` suggestions expire / release / revoke. No subsystem
silently consumes a reservation without global accounting.

## Q8. Shadow mode before authoritative?
Yes. `epistemic_shadow` logs LEGACY vs ARBITER without changing execution
authority until `epistemic_full` / `full_3_18`.

## Q9. Leakage / evaluator GT in discovery?
`scan_epistemic_source` PASS. EA–EF oracles live in `epistemic/benchmarks.py`
(evaluator). Controller does not import secrets as GT.

## Q10. Invisible / noncausal FP?
EF: secret_found=false, correct=true. OW-7: FP=0. Terminal
`UNRESOLVED_INVISIBLE`, never SAFE, never VERIFIED from absence of signal.

## Q11. Activity vs discovery?
Mandatory split. Slot efficiency answers "how effectively did 32 experiments
convert into progress toward a verified discovery?" Secret-found is not
implied by probes_used > 0.

## Q12. Pipeline integration?
Authoritative mode skips sequential axis spend so the arbiter includes
`AxisProposer` in the same 32. InventionController early-returns to
`EpistemicController` when `epistemic_enabled`.

## Q13. OW-3 XOR regression?
Honest negative. epistemic_full @32 misses OW-3 (3.17 openworld_full found it).
Do not patch against OW-3 or Holdout-V.

## Q14. Remaining bottleneck?
(1) Harvest still requires primitives to appear in observation.
(2) Arbiter can starve a specialized operator (XOR) that 3.17's grammar
prioritized. (3) Outer pipeline smoke/sweep/gates still consume slots before
the arbiter — authoritative mode skips axis, not residual sweep.
(4) Holdout-18 sacred first run: **NOT_DISCOVERED**. Direct arbiter@32 rate 1.0.
Remaining bottleneck is outer pipeline budget peel, not greedy EIG scoring.
Do not retune after seeing Holdout-18.

## Q15. Tests at freeze
589 passed. Holdout-18 evaluator oracles added only after freeze. First-run
locked in `reports/aivd_3_18/holdout_18.json`. No post-hoc agent patch.
