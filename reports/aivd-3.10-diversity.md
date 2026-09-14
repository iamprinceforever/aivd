# AIVD 3.10 Intervention Diversity

**Version:** 3.10.0  
**Freeze:** `ce27ce2c61a7aab96c83d78e41ef9b4cda5b6c42`

## Architecture
`aivd/invention/{family,diversity,archive,scheduler,exploration,bandit,uncertainty,selection}.py`

Flow: candidates → structural family discovery → hybrid exploit/explore selection →
cheap test → Beta belief update → saturation (revisitable) / revival on residual evidence.

## Selection score
EIG + security + uncertainty + behavioral novelty + **family novelty/coverage/uncertainty**
+ residual-linked priority − cost/redundancy/saturation/historical failure.  
**Novelty alone NOT rewarded.**

## Exploration policies compared
epsilon-greedy, UCB, Thompson, entropy allocation, novelty-weighted bandit, hierarchical.

## Coverage metrics (Holdout-Y replay diversity_full)
- mean families: 62.857142857142854
- mean unique families tested: 4.0
- mean coverage: 0.06364293029039572
- mean invented: 102.0

## Ablations (Holdout-Y replay discovery)
- A_invention_off: 0.0
- B_invention_random: 0.0
- C_invention_heuristic: 0.0
- D_invention_full_3_9: 0.0
- E_diversity: 1.0
- F_bandit: 1.0
- G_diversity_full: 1.0
- H_diversity_heuristic: 1.0
- I_no_invention_flag: 0.0
- sat_OFF: 1.0
- revival_OFF: 1.0
- exploration_OFF: 0.0

## Absolute rules
- No hard-coded penalties/boosts for ack/clear/Holdout solutions
- No echo_stem; no post-hoc tuning after Holdout-Z
- Preserve 3.4–3.9 behavior when diversity off
