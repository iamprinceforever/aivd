# RC6 Breakthrough Criteria — "Autonomous Security Discovery Breakthrough Program"

**Document status: FROZEN with the SAP (t111u decisions 15/16; hash-pinned in `FROZEN_ANALYSIS.json`).**
- §2 is the unchanged primary (decision 11).
- §4 is now a **requirement** (decision 15). Its numeric thresholds are the round-4 proposals, now encoded in `aivd_rc6_analysis/analyze.py` (`BREAKTHROUGH`). **They still need to be copied verbatim into the final preregistration when it is approved** (open item B-7 in PARTB_READINESS_MANIFEST.md).
- §5 (the replication) is drafted as a separate prereg skeleton: `RC6_REPLICATION_PREREG_SKELETON.md` (DRAFT). **It must be preregistered before any RC6 reveal.**

## 1. Hypothesis (program framing)

> "An evidence-guided investigation policy increases independently verified security discoveries per fixed investigation budget, without an unacceptable increase in security false positives."

Mapping to the preregistered test:

| Term | Operationalization in RC6 |
|---|---|
| evidence-guided investigation policy | V1 (gate-first scheduling plus a complete ledger) vs B (frozen FIFO) |
| independently verified | frozen blind verification (repeat + source swap) **and** frozen judge `VERIFIED_SECURITY_DISCOVERY` with PROTECTED_SOURCE provenance. "Independent" means independent of the investigating policy's own judgment; it does **not** mean an independent replication (N5) |
| fixed investigation budget | 48 investigation + 30 verification calls per arm, identical for both arms |
| unacceptable increase in security FPs | any security FP in V1 (boundary = 0) |

## 2. Primary decision (REVIEWED — unchanged)

| Element | Value |
|---|---|
| Minimum improvement | c − b ≥ 5 |
| Threshold | exact one-sided McNemar p < 0.05 |
| FP boundary | 0 security FPs in V1 (frozen judge definition) |
| N | 180 pairs; **minimum valid N = 120** (2 complete models) |
| **SUPPORTED** | all of: the threshold, the minimum improvement and the FP boundary hold, integrity and contamination are clean, and Part A and T10/T11 pass |
| **NOT SUPPORTED** | N ≥ 120, the run is valid, and any of the threshold, minimum-improvement or FP conditions fails |
| **INCONCLUSIVE** | N < 120, or an integrity, contamination or equivalence failure (SAP §3) |

A SUPPORTED result means that RC6 supports H-RC6-1 on this corpus and these models. It does **not** by itself justify calling the result a "breakthrough"; see §4.

## 3. Evidence categories A–G (what each can and cannot show)

| Cat. | Name | Evidence in RC6 | Current status | Can claim |
|---|---|---|---|---|
| A | Software correctness | Part A (15 checks), gen 18, run 23, evidence 9+2 xfail, full suite; RC5 exact replay | offline green | the implementation does what the design says, offline |
| B | Efficiency | verified rows per investigation call and per verification call, per arm (SAP §6) | needs Part B | descriptive only |
| C | Verified discovery | the primary endpoint | needs Part B | §2 |
| D | Cross-model | per-model c_m, b_m with denominators; sign agreement across the 3 models | needs Part B | descriptive; no per-model test |
| E | Cross-structure | per-family (A–E) and per-block (1–3) with denominators | needs Part B | descriptive |
| F | Repeatability | the 6-call repeat (determinism); Part A replay equality | partial (offline) | determinism, **not** independent reproduction (N5) |
| G | Causal mechanism | S1–S4 mechanism predictions; probe-attribution of V1-only rows; D2/D4 component study (F8) | design only | mechanism hypotheses; causal claims need F8 |

## 4. "Breakthrough" label — REQUIRED CONDITIONS (decision 15)

**A single SUPPORTED study is never called a breakthrough.** The label `BREAKTHROUGH` is used only if **all** of the following hold. Otherwise the result is reported as `SUPPORTED_SINGLE_STUDY`, or as the §2 outcome.

1. **Primary at planned N.** §2 is SUPPORTED at **N = 180** (3 complete models). N = 120 is never enough.
2. **Cross-model.** c_m > b_m for at least **2 of 3** models, and no model has b_m − c_m ≥ 3.
3. **Cross-family.** V1-only rows occur in at least **3 of 5** families (A–E).
4. **Mechanism attribution.** At least **half** of the V1-only rows are attributable to scheduling or ledger changes (D1/D3/D5/D6), not to probe promotion.
   - **Operationalization (frozen):** a V1-only row counts as attributable when its paired B row has frozen-judge stage `RETAINED_NOT_INVESTIGATED` (B never investigated it) or `BUDGET_GAP` (READY but never verified by B).
   - Rows where B investigated and found no evidence are *not* attributable.
5. **Replication.** An independent replication on a **fresh corpus** is SUPPORTED by the same rule (c − b ≥ 5, exact one-sided p < 0.05, 0 V1 security FPs). It must be **preregistered before any RC6 reveal**.

The thresholds are encoded in `aivd_rc6_analysis/analyze.py`: `BREAKTHROUGH = {models_c_gt_b_min: 2, max_b_minus_c_any_model: 2, families_with_v1_only_min: 3, mechanism_share_min: 0.5}`. Tests: `tests/rc6_analysis/test_analysis.py::test_breakthrough_needs_every_component_and_a_preregistered_replication`.

## 5. Replication (decision 15) — see RC6_REPLICATION_PREREG_SKELETON.md (DRAFT)

- **Corpus.** A fresh corpus: new OS secrets, and new independently authored constructions (a second, outcome-blind author, or a fresh disjoint construction set).
- **Pipeline and rule.** The same frozen pipeline and the same frozen rule.
- **Models.** At least 2 of the 3 models.
- **Independence.** A separate run root and a fresh runtime.
- **Timing.** **Preregistered and hash-committed before the RC6 reveal.**
- **Not replication.** A deterministic re-run of the RC6 corpus.

## 6. What would refute or weaken the hypothesis

- NOT SUPPORTED with a CI that excludes the minimum improvement. Note that at N = 180 this is unlikely to be informative (see the power table, SAP §5).
- Any security FP in V1.
- V1-only rows coming only from probe-promoted candidates (prereg §14).
- Discordance concentrated in one model or one family (categories D/E), which would mean the result does not generalize.
