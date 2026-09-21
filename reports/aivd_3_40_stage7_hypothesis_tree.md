# AIVD 3.40 Stage-7 — Hypothesis Tree (H7a…H7e + H7-REJECT)

**Document type:** Stage-7 hypothesis tree (DOCS ONLY — **NOT EXECUTED / NOT IMPLEMENTED**)  
**Recorded:** 2026-09-21 19:55 IST  
**Parent charter:** `reports/aivd_3_40_stage7_charter.md`  
**Stage-6 prior:** `reports/aivd_3_40_stage6_results.md` (tip `000a4d8` / design `ac152c6`)  
**Authority:** Stage-6 established offline SUCCESS for R-A…R-D on the Stage-6 bench; this document decomposes whether those wins **generalize**, whether offline specs match isolated executables, and whether S-diagnostic conflicts must be reported without retuning  
**R1b caveat:** `7a3457e` — do not auto-rerun R1b  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

**Scientific goal:** Before modifying the live AIVD pipeline, determine which repair mechanism (if any) generalizes beyond Stage-6 and can be implemented without changing discovery semantics. Distinguish **benchmark overfitting** | **genuine equivalence-repair generalization** | **implementation/specification mismatch**. Unresolved S remains valid. Do **not** make S pass. Do **not** authorize Sacred from Stage-7.

---

## 0. Inherited macroscopic status (immutable)

| Macro | Stage-7 stance |
|-------|----------------|
| **H2c** (Stage-4) | SUPPORTED — constructed then `FILTER_BEHAVIORAL_DUP` | retained as location prior |
| **H5b** (Stage-5) | **SUPPORTED** — over-collapse / FALSE_DUPLICATE | **do not weaken** |
| **H5d** (Stage-5) | **SUPPORTED** — context-dependent equivalence | **do not weaken** |
| **H6a** (Stage-6) | **SUPPORTED** (offline bench) — generic mechanism joint retention | cite as **offline-only**; do not treat as discovery |
| **H6b** (Stage-6) | **SUPPORTED** (offline) — identity necessary-but-insufficient | retained |
| **H6c** (Stage-6) | **SUPPORTED** (offline) — ambiguity-aware policies | retained; Stage-6 AR=0 limited stress |
| **H6d** (Stage-6) | **NOT_TESTED** | may inform H7d cost ranking |
| **H6-REJECT** | **AGAINST** (offline) | retained; re-test as H7-REJECT on Phase-A/B |
| **H1 / H3** | Not primary Stage-7 | not reopened unless evidence forces |

**Epistemic fence:** “Offline Stage-6 SUCCESS” ≠ “generalizes.” “Generalizes on Phase-A” ≠ “executable matches spec.” “Spec↔impl match” ≠ “Sacred authorized” ≠ “live filter may be replaced.” “Fails S diagnostic” ≠ “must retune repair.”

---

## Causal / logical order among H7 leaves

```
Phase A
  H7a  ≥1 family genuinely generalizes on independent Phase-A bench
  H7b  Stage-6 wins are overfitting (independent Phase-A fails)
  H7e  S / HO diagnostic may conflict with independent generalization (report; no retune)
Phase B (only for Phase-A passers)
  H7c  offline spec ≡ isolated executable (decisions / ambiguity / provenance / cost)
  H7d  cost–quality ranking separates practical from impractical passers
H7-REJECT  target-specific / critical-special / live mutation / contamination → FAILED
INCONCLUSIVE when evidence cannot separate the above under frozen matrix
```

Notes:

- **H7a** and **H7b** are mutually exclusive primary readings of Phase-A for a given family (a family may FAIL H7a / SUPPORT H7b).
- **H7e** is orthogonal: diagnostic conflict does not by itself refute H7a if independent evidence holds.
- **H7c** is the primary Phase-B claim; mismatch = implementation/specification mismatch mode.
- **H7d** ranks passers; does not license Sacred BH48.
- **H7-REJECT** overrides apparent metric wins.

Future EXECUTION emits per-phase gates (SUCCESS / PARTIAL / FAILED / INCONCLUSIVE / COST_IMPRACTICAL) with H7* stances as supporting evidence.

---

## H7a — Genuine equivalence-repair generalization

**Claim:** At least one Stage-6 SUCCESS family (R-A…R-D), evaluated on the **independent** Phase-A generalization benchmark (pairs labeled `INDEPENDENT`; frozen before outcomes), simultaneously:

1. collapses true-dup / text-diff-beh-eq pairs (DCR ≥ prereg threshold), and  
2. preserves known-nondup / context-dependent / composition-sensitive / state-sensitive / text-eq-beh-diff distinctions (FDR ≤ ceiling; DPR ≥ floor), and  
3. stays within Stage-7 cost envelope without degeneracy or target-specific rules.

### Stage-6 prior weight

| Evidence | Effect |
|----------|--------|
| R-A…R-D all SUCCESS on Stage-6 bench | Motivates testing generalization; does **not** establish H7a |
| All four families identical primary rates on Stage-6 | Phase-A may separate them; do not assume interchangeability |
| S6-CD-01 shares bodies with S6-HO-CRIT | Warns that Stage-6 “held-out” proximity is limited — Phase-A must be stricter |

### Reject H7a (for a family) if

- Family fails prereg bands on `INDEPENDENT` Phase-A pairs, **or**  
- Apparent pass depends only on `RELATED` / `S6_REPLAY` / S diagnostic cells, **or**  
- H7-REJECT patterns present.

### Accept H7a (for a family) if

- Prereg Phase-A SUCCESS criteria met on `INDEPENDENT` population, **and**  
- Fair ablation vs BASELINE attributes gains to equivalence mechanism, **and**  
- H7-REJECT not supported.

---

## H7b — Benchmark overfitting (Stage-6-specific wins)

**Claim:** One or more Stage-6 SUCCESS families fail to meet Phase-A independent generalization bands, indicating Stage-6 SUCCESS was **bench-specific** (overfitting / limited coverage / critical-class proximity) rather than genuine equivalence-repair generalization.

### Accept H7b (for a family) if

- Stage-6 SUCCESS cited, **and** Phase-A `INDEPENDENT` gate is FAILED or INCONCLUSIVE for that family without protocol violation explaining away the miss, **and**  
- Failure concentrates on classes absent or thin in Stage-6 (e.g., stronger composition / state / text-eq-beh-diff) **or** on truly novel body keys.

### Reject H7b if

- Family meets H7a SUCCESS on independent pairs.

**Reporting rule:** Supporting H7b for all families is a valid Stage-7 scientific outcome (no repair ready for Phase B / future consideration). Do **not** rescue by adding Stage-6-like pairs post-hoc.

---

## H7c — Offline spec ≡ isolated executable

**Claim:** For every family that passes Phase A, an isolated experimental module consuming the same inputs as the offline repair spec produces **identical** labels, ambiguity states, provenance fields, and cost accounting on the complete frozen benchmark. Differences ⇒ **implementation/specification mismatch** (Phase-B FAILED for that family).

### Reject H7c if

- Any disagreement on label / ambiguity / provenance / cost fields under frozen inputs, **or**  
- Module reaches into live discovery path / mutates `grow.py` / replaces `FILTER_BEHAVIORAL_DUP`.

### Accept H7c if

- Exact equivalence matrix PASS for all frozen Phase-A (+ Phase-B fixture) pairs, **and**  
- Isolation / no-pipeline-mutation flags true, **and**  
- Promised property tests PASS.

**Honesty rule:** Do not silently edit offline reference or executable to force agreement.

---

## H7d — Cost–quality ranking under Stage-7 envelopes

**Claim:** Among Phase-A (and Phase-B) passers, Stage-7 cost metrics (total, per-pair mean/median/max/worst-case) separate **practical** candidates from **COST_IMPRACTICAL** ones without consuming Sacred BH48. Accuracy alone is insufficient for live-consideration ranking.

### Stage-6 prior weight

| Evidence | Effect |
|----------|--------|
| R-B calls_mean ≈ 2.08 vs R-A/C/D ≈ 0.85 on Stage-6 | Mild prior that cost may separate families even when quality ties |
| H6d NOT_TESTED | Stage-7 may partially address via ranking, not full budget sweep |

### Accept H7d if

- Ranking by preregistered cost–quality rule is computable and stable under freeze, **and**  
- At least one passer is practical **or** all passers are honestly labeled COST_IMPRACTICAL.

### Reject H7d if

- Cost accounting incomplete / Sacred touched / unbounded expansion used to buy DPR.

---

## H7e — S / critical diagnostic conflict is reportable, not a retune signal

**Claim:** A repair may pass independent Phase-A generalization yet fail (or hard-collapse) the critical S / Stage-6 HO diagnostic pair class. That conflict must be **reported**; it must **not** determine winner selection and must **not** authorize modifying the repair to recover S.

### Accept H7e as operative rule if

- Protocol forbids S-driven selection / retuning (charter binding), **and**  
- EXECUTION reports conflict table when present.

### Protocol violation (H7-REJECT path) if

- Winner chosen primarily because it alone recovers S diagnostic, **or**  
- Family hyperparameters / contexts changed after seeing S diagnostic failure to make S pass.

---

## H7-REJECT — Target-specific / contamination / live mutation

**Claim:** Apparent Phase-A or Phase-B gains require any of:

- S / odd-stride / CAT-self / critical body-key special cases  
- Textual-only decisions that fail adversarial behavioral labels  
- Counting `RELATED` pairs as independent generalization  
- Post-hoc pair/context addition  
- Silent offline↔executable patching  
- Live `FILTER_BEHAVIORAL_DUP` replacement / `grow.py` discovery mutation / Sacred BH draws  

→ design or execution **FAILED**.

### Accept H7-REJECT if any such pattern is observed.

### Against H7-REJECT if ablation + independence labels + isolation flags are clean.

---

## Aggregate interpretation map

| Pattern | Reading |
|---------|---------|
| H7a SUPPORTED, H7b AGAINST, H7c PASS, H7-REJECT AGAINST | Genuine generalization + faithful impl — **still no Sacred / no live wire** |
| H7b SUPPORTED for all families | Overfitting diagnosis — do not proceed to live integration |
| H7a SUPPORTED, H7c FAIL | Generalizes in offline spec but **impl/spec mismatch** — fix under new revision; do not live-wire |
| H7a SUPPORTED, H7e conflict observed | Report conflict; keep independent ranking; do not retune for S |
| H7d COST_IMPRACTICAL only passers | Accurate but impractical — classify accordingly |
| H7-REJECT SUPPORTED | FAILED regardless of averages |

---

## Final gate (design)

```
STAGE-7 DESIGN READY: EXECUTION REQUIRES SEPARATE AUTHORIZATION
```

No Phase-A/B EXECUTION or Sacred is authorized by this document alone.
