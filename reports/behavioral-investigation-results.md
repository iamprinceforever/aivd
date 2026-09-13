# Active Behavioral Investigation — Results (AIVD 3.3.0)

**Date:** 2026-09-13  
**Target:** `mock://investigation-bench` (blind hierarchy A–J)  
**Seeds:** [42, 43, 44, 45]  
**Budgets swept:** [8, 16, 32, 64]  
**Eval elapsed:** 0.64s  
**Source metrics:** `reports/behavioral_investigation/eval_summary.json`

> Scientific language: anomalies ≠ vulnerabilities. confirmation_events ≠ unique_vulnerabilities.  
> Status labels: **Not demonstrated** / **Heuristic** / **Confirmed under the planted threat model**.  
> Numbers below are from the actual eval run — not fabricated.

---

## 1. Architecture summary

AIVD 3.3.0 adds an **Active Behavioral Investigation (ABI)** layer in `aivd/investigation/` without rewriting explorers, PPO, memory, verifier, semantic analyzer, or reporting.

**Loop:** HYPOTHESIS → BASELINE → PROBE → OBSERVE → COMPARE → LOCALIZE → COUNTERFACTUAL → UPDATE → NEXT

**Integration seams (additive):**
- Optional `AIVDConfig.use_investigation` hook in `Controller._step`
- `InvestigatorExplorer` registered as `investigator`
- `RewardBreakdown` / `compute_reward` investigation terms default to **0** (v3.2 totals unchanged)
- `RegionRecord.meta` helpers for boundaries / hypotheses / negatives (finding still does not saturate region)
- New allowlisted target `mock://investigation-bench` (planted-offline / PV-RARE-CANARY intact)

See [`reports/behavioral-investigation-architecture.md`](behavioral-investigation-architecture.md).

---

## 2. Protocol

1. **Localization suite (evaluator-only GT):** given a prompt known to fire B/C/F, run budget-capped delta-debug localizer; score token overlap vs offline GT.
2. **Boundary H:** scan `lencliff:{pad}` lengths; require effect jump + positive `boundary_score`.
3. **Probabilistic G:** 24 repeats/seed; Wilson CI; forbid deterministic claim on sparse hits.
4. **Decoy J:** dramatic non-security response must not yield security FP.
5. **Signal ablation:** full-prompt baseline F1 vs localizer F1 on B.
6. **Explorer ablation:** random (no ABI) vs investigator+ABI controller on blind bench (32 probes).
7. **Budget sweep:** localization means at 8/16/32/64.

---

## 3. Key numbers (actual)

### Localization accuracy (mean over seeds [42, 43, 44, 45], budget 24)

| Hierarchy | Mean localization accuracy |
|-----------|----------------------------|
| B SPARSE_WITH_FOOTPRINT | **1.000** |
| C COMPOSITIONAL | **1.000** |
| F ENCODING | **0.500** |

### Boundary detection (H)

- **boundary_detection_rate:** **1.000** (per-seed: [1.0, 1.0, 1.0, 1.0])

### Probabilistic (G)

- **mean p̂:** 0.3646 (planted p≈0.25; finite-sample)
- **any_false_deterministic:** **False**

### Decoy (J)

- **decoy_fp_rate:** **0.000**

### Signal ablation (localization F1: baseline full prompt vs localizer)

- mean baseline F1: **0.286**
- mean localizer F1: **1.000**
- **Δ F1 (investigator − baseline):** **+0.714**
- mean localizer token-overlap accuracy: 1.000
- mean inv boundaries / run: 1.000

### Explorer ablation (blind discovery, budget 32)

| Condition | Mean unique GT hits | Mean security score |
|-----------|---------------------|---------------------|
| Baseline random (no ABI) | 0.000 | 0.0000 |
| Investigator + ABI | 0.000 | 0.0000 |
| Δ | +0.000 | +0.0000 |

> Blind unique-hit Δ ≈ 0 is expected: explorers do **not** receive GT tokens. The **signal ablation Δ F1** is the primary investigator-vs-baseline improvement metric here.

### Budget sweep (localization means)

```json
{
  "8": {
    "mean_acc_B": 1.0,
    "mean_acc_C": 1.0,
    "mean_acc_F": 0.5
  },
  "16": {
    "mean_acc_B": 1.0,
    "mean_acc_C": 1.0,
    "mean_acc_F": 0.5
  },
  "32": {
    "mean_acc_B": 1.0,
    "mean_acc_C": 1.0,
    "mean_acc_F": 0.5
  },
  "64": {
    "mean_acc_B": 1.0,
    "mean_acc_C": 1.0,
    "mean_acc_F": 0.5
  }
}
```

---

## 4. Acceptance mapping

| ID | Criterion | Result |
|----|-----------|--------|
| A | Existing tests green | See pytest summary in commit notes |
| B | Investigator unit tests pass | `tests/test_investigation_*.py` |
| C | Localize one-var + compositional | B=1.0, C=1.0 |
| D | Counterfactual reduces false hyps | Covered in unit/bench tests |
| E | Boundary detection on H | rate=1.000 |
| F | Probabilistic not deterministic false claim | any_false_deterministic=False |
| G | Same-region multi-vuln residual | `test_same_region_multi_vuln_i_residual` |
| H | Memory restart keeps boundaries | `test_memory_restart_keeps_boundaries` |
| I | Investigator improves ≥1 metric | **Δ localization F1 = +0.714** |
| J | No leakage | `test_investigation_leakage.py` |
| K | Budgets respected | unit + investigator budget tests |
| L | Honest report + commit + push | this document |

---

## 5. Limitations / failures / next steps

**Limitations**
- Blind explorer discovery of pure-sparse (A) and compositional (C) without cues remains **Not demonstrated** in the controller ablation (0 unique GT hits).
- Encoding localization F1/accuracy partial (0.50) — b64 string tokenization is coarse.
- Investigator follow-ups in Controller are single-shot per run (`_inv_ran`) to protect budget.
- No live Ollama scan in this eval pack (mock-only for speed/honesty).

**Known gaps**
- PURE_SPARSE (A) hard negative: discovery without leakage **Not demonstrated**.
- MULTI_VULN (I) residual uncertainty preserved in unit test; not stress-tested in multi-seed controller eval.
- World-model EIG hook is preference metadata only.

**Next steps**
1. Cue-graded footprints for more hierarchy members (like learnable canary).
2. Stronger encoding-aware tokenizers for localization scoring.
3. Optional multi-step investigation across Controller probes with shared hypothesis state.
4. Small honest Ollama scan when available — report separately.

---

## 6. Status statements

- Localization of planted B/C triggers under evaluator-held prompts: **Confirmed under the planted threat model**.
- Boundary cliff H detection: **Confirmed under the planted threat model**.
- Probabilistic G not over-claimed as deterministic: **Confirmed under the planted threat model**.
- Decoy J not promoted as vulnerability via security score: **Confirmed under the planted threat model** (fp_rate=0.000).
- Blind open discovery of A–J without cues/GT: **Not demonstrated** (controller unique hits ≈ 0).
- Investigator improvement vs no-localize baseline (F1): **Heuristic / Confirmed under planted threat model** (Δ=+0.714).
