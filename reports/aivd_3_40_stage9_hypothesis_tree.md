# AIVD 3.40 Stage-9 — Hypothesis Tree (H9a…H9i + H9D + H9-REJECT)

**Document type:** Stage-9 hypothesis tree (DOCS ONLY — **NOT EXECUTED / NOT ANALYZED**)  
**Recorded:** 2026-09-21 21:26 IST  
**Parent charter:** `reports/aivd_3_40_stage9_charter.md`  
**Stage-8 prior:** `reports/aivd_3_40_stage8_results.md` (tip `a447649` / design `129a2e9`)  
**Authority:** Stage-8 PARTIAL — integration+semantics PASS; axis-3 null; D=0; S 0/7; `UNRESOLVED_INVISIBLE`; autonomous S never expressed Stage-4/5 bottleneck as fate D  
**R1b caveat:** `7a3457e` — do not auto-rerun R1b  
**Authorization:** `DESIGN_ONLY_NOT_EXECUTED`

**Scientific goal:** Localize the earliest observable disappearance of autonomous S progress from already-recorded Stage-8 trajectories, and score which causal hypotheses are supported / weakly supported / inconclusive / against — **without** merging CONTROLLED Stage-4/5 equivalence-filter findings into AUTONOMOUS Stage-8 failure, and **without** manufacturing `NOT_RECORDED` fields.

---

## 0. Inherited macroscopic status (immutable)

| Macro | Stage-9 stance |
|-------|----------------|
| **H2c** (Stage-4) | SUPPORTED — controlled odd CAT-self constructed then `FILTER_BEHAVIORAL_DUP` | cite as **CONTROLLED_FILTER**; not Stage-8 autonomous fate D |
| **H5b** (Stage-5) | **SUPPORTED** — FALSE_DUPLICATE | **do not weaken**; **do not** claim Stage-8 invalidated it |
| **H5d** (Stage-5) | **SUPPORTED** — context-dependent equivalence | cite |
| **H8a** | supported — integration + semantics | prerequisite for reading Stage-8 trajectories as repair-faithful |
| **H8b** | not_supported — no axis-3 mechanism change (D already 0) | motivates H9D AGAINST-scoped |
| **H8c** | not_supported — no verify uplift | S remains null |
| **H8d** | supported | rediscovery honesty |
| **H8e** | report_only_null_ok | I=0 |
| **H8f** | applicable | S-null reportable |
| **H8-REJECT** | not_supported | re-test as H9-REJECT for audit protocol |

**Epistemic fence:** “Stage-5 FALSE_DUPLICATE SUPPORTED” ≠ “Stage-8 autonomous S failed because of equivalence filter.” “Stage-8 D=0” ≠ “FALSE_DUPLICATE never occurs.” “Fate E common” ≠ “selection is the cause” if selection detail is `NOT_RECORDED`. “Absence from report” ≠ “did not occur.”

---

## Causal / logical order among H9 leaves

```
Preflight
  H9-REJECT   protocol / evidence-manufacture / namespace-merge violations
Observation integrity
  H9i  observation/instrumentation gaps explain unresolved localization
Trajectory waypoints (earliest → later)
  H9a  representation / invention (S-direction atoms never invented)
  H9b  language-growth (invented but language store / growth path stalls)
  H9c  composition (composed S-direction body fails / never formed)
  H9d  candidate-pool (composed but absent from pool; not yet equiv)
  H9D  equivalence filter active as autonomous S bottleneck (fate D)
  H9e  candidate-selection (survived equiv / pool but not selected)
  H9f  verification (selected but failed verify)
  H9g  rediscovery / firewall (independence / firewall path)
  H9h  budget / stopping (BH / invent_cap / stop_reason truncates progress)
INCONCLUSIVE when NOT_RECORDED blocks separation
Do NOT force a single winner among H9a…H9i / H9D
```

Notes:

- Score leaves **independently** where evidence allows; retain multi-hypothesis ties.
- **H9D** is explicit and separate from H9d (pool) and from Stage-5 H5b.
- **H9e** defaults to **INCONCLUSIVE** when ranking/score/select detail is `NOT_RECORDED`, even if fate **E** dominates counts.
- **H9i** is not a “failure of S”; it is a claim that localization is blocked by missing instrumentation.
- Earliest-supported leaf among OBSERVED waypoints outranks later leaves for “where disappearance begins,” but later leaves may remain WEAKLY SUPPORTED as co-factors.

---

## Confidence vocabulary (binding)

| Label | Use |
|-------|-----|
| **SUPPORTED** | Direct Stage-8 recorded evidence favors the claim; no decisive counter-evidence in matrix |
| **WEAKLY SUPPORTED** | Consistent with recorded aggregates / terminals but lacks stage-local detail |
| **INCONCLUSIVE** | Missing evidence (`NOT_RECORDED`) or conflicting signals prevent decision |
| **AGAINST** | Recorded evidence contradicts the claim **in the scoped domain** |

Avoid: PROVEN, DEFINITELY, ROOT CAUSE, “the” cause (singular) unless multiple leaves are explicitly tied.

Per leaf, future EXECUTION must record: observed evidence, counter-evidence, missing evidence, alternatives, confidence.

---

## H9a — Representation / invention

**Claim:** Autonomous S disappears at (or before) invention: S-direction atoms / odd-stride body keys are never invented under Stage-8 autonomous plants (representation or invent pathway does not produce the historical S behavioral direction).

### Evidence directions (design)

- **For:** Stage-8 generation records / s_diagnostic show odd-stride / odd CAT-self **NOT_OBSERVED** while invent events for other atoms **OBSERVED**; failure_class implicating invent/planning if recorded.
- **Against:** Odd-stride body keys appear in invent records but fail later.
- **Missing:** Fine-grained invent-attempt logs for rejected S-direction proposals if not recorded → do not upgrade absence-from-summary to H9a alone without checking H9i.

### Accept / reject sketch

- **SUPPORTED** if OBSERVED invent pathway + explicit NOT_OBSERVED for S-direction bodies across seeds, with later stages NOT_APPLICABLE.
- **INCONCLUSIVE** if invent attempts for S-direction are NOT_RECORDED.
- **AGAINST** if S-direction bodies are OBSERVED invented.

---

## H9b — Language growth

**Claim:** S-direction content is invented (or admissible) but language-growth / store evolution fails to retain or extend the trajectory toward historical S behavior.

### Evidence directions

- **For:** Invented S-direction atoms OBSERVED; subsequent language occupancy / growth edges show stall specific to that lineage.
- **Against:** Language growth proceeds and S-direction compositions appear.
- **Missing:** Per-step language-store diffs if NOT_RECORDED → H9b INCONCLUSIVE.

---

## H9c — Composition

**Claim:** S-direction atoms exist in language but composition into the critical S body (e.g. odd CAT-self class) fails or never occurs under autonomous growth.

### Evidence directions

- **For:** Atoms OBSERVED; composition attempts for S-body NOT_OBSERVED or recorded fail; contrasts with Stage-4 controlled composition success.
- **Against:** Successful S-body composition OBSERVED in Stage-8 runs.
- **Missing:** Composition-attempt ledgers if NOT_RECORDED.

**Fence:** Stage-4 offline IR composition success is CONTROLLED / offline — cite as contrast, not as Stage-8 autonomous composition observation.

---

## H9d — Candidate pool (pre-equivalence)

**Claim:** An S-direction body is composed but never enters the candidate pool (fate **C**-class), independent of equivalence removal.

### Evidence directions

- **For:** Composition OBSERVED; pool-entry NOT_OBSERVED for that body; structural filters other than behavioral-dup recorded if present.
- **Against:** Pool entry OBSERVED (then later stages apply).
- **Missing:** Pool-admission traces beyond aggregate `n_pool_entered` if body-level absent.

---

## H9D — Equivalence filter as active autonomous S bottleneck

**Claim (scoped):** In the Stage-8 autonomous S matrix, equivalence filtering (`FILTER_BEHAVIORAL_DUP` / repair duplicate removal) is the **active** bottleneck that removes S-progress (fate **D**).

### Binding scope language

> Score **AGAINST** when Stage-8 shows D=0 / no duplicate removals for autonomous S plants: “equivalence filter is **not observed as an active bottleneck in the Stage-8 autonomous S matrix**.”  
> Do **not** conclude “equivalence filter can never be a bottleneck.”  
> Do **not** weaken Stage-5 H5b FALSE_DUPLICATE (CONTROLLED_FILTER / OFFLINE_EVAL).

### Evidence directions

- **For:** Fate **D** OBSERVED on S-direction bodies under autonomous Stage-8; repair vs baseline flips D.
- **Against (scoped):** D_rate=0.0 all conditions/seeds; `n_duplicate=0`; odd CAT-self never reaches equiv decision; Stage-8 axis-3 null because baseline D already 0.
- **Missing:** None required for scoped AGAINST if D aggregates and equiv_decision ledgers are OBSERVED zeros.

### Accept / reject sketch

- Expected prior from Stage-8 COMPLETE: **AGAINST** (scoped). Reconfirm under audit; do not upgrade to universal never-claim.

---

## H9e — Candidate selection

**Claim:** S-direction (or other) bodies survive equivalence / enter selectable pool but are not selected for verification due to ranking / scoring / selection policy.

### Evidence directions

- **For:** Fate **E** OBSERVED **and** recorded rank/score/select decisions show S-direction (or relevant) bodies ranked below cutoff.
- **Against:** Selection of S-direction bodies OBSERVED (then H9f+).
- **Missing (critical):** If Stage-8 artifacts lack rank/score/select detail → **H9e INCONCLUSIVE** even if E dominates. Do **not** treat “E common” as proof of selection causation.

---

## H9f — Verification

**Claim:** Relevant bodies are selected but fail verification predicates.

### Evidence directions

- **For:** `n_selected>0` with verify failures recorded for S-direction bodies.
- **Against:** `n_selected=0` / no verify attempts → H9f NOT_APPLICABLE or AGAINST as earliest cause.
- **Missing:** Verify-failure reasons if NOT_RECORDED after selection OBSERVED.

---

## H9g — Rediscovery / firewall

**Claim:** Autonomous S disappearance is explained by rediscovery/firewall dynamics (floor, epoch, independence path) rather than earlier invention→pool waypoints.

### Evidence directions

- **For:** Firewall/rediscovery records show S-direction progress truncated at H/I pathway with earlier waypoints OBSERVED successful.
- **Against:** Firewall armed/epoch normal while S-direction bodies never appear earlier; H counts reflect non-S bodies only.
- **Missing:** Per-body firewall eligibility traces if NOT_RECORDED.

---

## H9h — Budget / stopping

**Claim:** Episode stopping (BH exhaustion, invent_cap, stop_reason) truncates a trajectory that was otherwise progressing toward S.

### Evidence directions

- **For:** stop_reason / budget fields OBSERVED **and** mid-trajectory S-direction progress OBSERVED that would continue under larger budget (requires recorded unfinished S-path — do not invent).
- **Against:** Budget exhausted with **no** OBSERVED S-direction progress at any waypoint (budget may co-occur without explaining disappearance locus).
- **Weak:** Universal BUDGET_EXHAUSTED without S-path evidence → WEAKLY SUPPORTED at most as terminal envelope, not earliest locus.

---

## H9i — Observation / instrumentation

**Claim:** The apparent disappearance cannot be honestly localized because critical waypoints are `NOT_RECORDED` (instrumentation gap), so Stage-9 must report missing instrumentation rather than force a causal winner.

### Evidence directions

- **For:** Schema inventory shows required fields for H9a–H9h absent from Stage-8 run artifacts; analysis_spec marks them NOT_RECORDED.
- **Against:** All waypoints needed for earliest-divergence are OBSERVED or explicit NOT_OBSERVED.
- **Note:** H9i may be WEAKLY SUPPORTED alongside a SUPPORTED earlier leaf when some but not all distinctions remain blocked.

---

## H9-REJECT — Protocol / evidence integrity reject

**Claim:** Stage-9 analysis (if executed) is invalid because of one or more:

- Manufactured fields / inferred selection-ranking without records  
- Mutation of Stage-8 results or 3.38/3.39  
- New Sacred / plant / grow.py experiment under “Stage-9” label  
- Merging CONTROLLED_FILTER and AUTONOMOUS_DISCOVERY into one causal claim that Stage-8 D=0 “refutes” H5b  
- Post-hoc seed selection / winner coercion among R-A/R-C/R-D  
- Retune of repairs / revival of R-B / budget cheating  
- Converting `NOT_RECORDED` into failure or absence-from-report into “did not occur”

### Accept H9-REJECT if any above OBSERVED in the audit process.  
### Else not_supported.

---

## Multi-hypothesis policy

Do **not** force a single hypothesis if insufficient. Allowed EXECUTION outputs:

- One SUPPORTED earliest leaf + INCONCLUSIVE later leaves  
- Tie among H9a/H9b/H9c when records cannot separate invention vs growth vs composition  
- “Localizes before equivalence (H9D AGAINST scoped); earliest among H9a–H9d unresolved because …”  
- Dominant fate E with H9e INCONCLUSIVE due to missing rank/score/select  

---

## Mapping to Stage-8 A–I fates (continuity)

| Fate | Primary H9 interest |
|------|---------------------|
| A | H9a |
| B | H9c |
| C | H9d |
| D | H9D |
| E | H9e (only if selection detail OBSERVED; else INCONCLUSIVE) |
| F | H9f |
| G | (success path; not disappearance) |
| H | H9g |
| I | H9g / recursion secondary |
| UNOBSERVED / NOT_RECORDED | H9i |

Stopping envelope fields (`stop_reason`, `failure_class`, budget) feed **H9h** without automatically overriding earlier leaves.
