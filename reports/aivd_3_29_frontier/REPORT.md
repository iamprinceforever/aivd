# AIVD 3.29 Frontier Capability Tests A / B / C

**Architecture unmodified. INVENT_CAP = 48. Sacred first run. No retune.**

Implementation: `b81dcdad119e520def798ad052a732aef0417b2e` (AIVD 3.29.0)
Budget: 32. Seeds: 0,1,2,3,4,7,11. Model: TinyLlama 1.1B Chat (greedy, max_new=8).
Only `aivd/science/audit.py` gained forbidden-token strings. Compiler, designer,
families, gap, methods: **not changed**.

---

## A. Existing compiler ontology (evaluator only)

| Family | Constructor | Dynamic instances | Source |
|---|---|---|---|
| OMIT | omit_i{k}, omit_first/second/last | yes | operators + invent |
| SWAP_ADJACENT | swap_i{k}, swap_first/last_two | yes | operators + invent |
| REVERSE_TOKENS | reverse_content | no | unused primitive |
| WRAP_WHOLE | quotes, '', ``, (), [] | yes | WRAP_PAIRS |
| INSERT_SEPARATOR_TOKEN | `|,;/-:` as own token | yes | SEPARATORS |
| REPEAT_DUPLICATE | repeat_last, duplicate | no | operators |
| AFFIX_POLITENESS | suffix_q, prefix_please | no | operators |
| INTRA_TOKEN | revchar / caseflip / duphead at hot i | yes | invent_intra |
| HARVEST_REJOIN | one char at one mid boundary | yes | compile_from_harvest |
| RECORD_LABEL_NL | LABEL:\\n + body | yes | compile_from_structure |
| WHITESPACE_REJOIN | `\\n` / `\\t` at mid | yes | compile_from_structure |
| RECORD_EQUALS | LABEL=body | yes | compile_record_forms |
| QUOTE_SUFFIX | prefix + "suffix" | yes | compile_record_forms |
| FIELD_DELIMITER | LABEL + `\| # ~` + body | yes (lazy) | FIELD_DELIMS + FamilyInventory |
| LIVE_COMPOSE | typically depth-2 sequences | yes | designer.propose |

Not in ontology: join-all whitespace, cyclic shift, append-reversed,
non-adjacent permutation, XML tags, character-split, sort-by-length.

Existing-space enumerator (all of the above + 2-op battery compose +
harvest of `_ @ % & ^`) **cannot fire** any of the three plants.

---

## B. Test A — new intervention-family invention

**Plant:** identity tokens joined by `_` (`This_is_a_Llama-based_...`).
Family required: JOIN_ALL_WHITESPACE.

**Why outside ontology:** FIELD_DELIMITER prefixes one token then the
*spaced* body. HARVEST_REJOIN joins **one** boundary. INSERT puts `_` as
its own token with spaces. None produces join-all.

| Condition | Secret | Verified |
|---|---|---|
| off | 0/7 | 0/7 |
| full_3_29 | 0/7 | 0/7 |
| direct 3.29 | 0/7 | 0/7 |
| control | 0/7 | 0/7 |

Used 32/32. Gap heuristic 7/7. Leases 5, all revoked (label_eq, quote_tail,
label_nl, field_124 `|`, field_35 `#`). Then field_126 `~`. Never `_`.join.

Hypothesized dimension: always `gap.unknown_segmentation` / "rejoin harvested-char
at a token boundary" — **not** JOIN_ALL.

**Class: NEW_FAMILY_NOT_COMPILABLE**
(required family also **never hypothesized**.)

**Level reached: 3** (intra-exhaustion gap heuristic).
**Failed at: 4** (new family hypothesized as the required family).

---

## C. Test B — open-ended experiment-language construction

**Plant:** cycle tokens left by 1.
Required experiment: cyclic shift of the token sequence.

**Why not existing grammar:** swap is adjacent-pair only. reverse is full
order reverse. 2-op compose cannot bubble token 0 through 11 positions.
Not a FIELD_DELIMITER parameter.

| Condition | Secret | Verified |
|---|---|---|
| off | 0/7 | 0/7 |
| full_3_29 | 0/7 | 0/7 |
| direct | 0/7 | 0/7 |
| control | 0/7 | 0/7 |

Same 3.29 path as A: known families leased and revoked. No rotate/cycle
operator constructed. n_tok in {4,10,11,12,19,20} — never a permutation
of the 11 identity tokens that is a 1-cycle.

Observable primitives available: tokens, positions, characters, residuals,
action history. AIVD did not assemble them into a cyclic-shift program.

**Class: LANGUAGE_CONSTRUCTION_NOT_REPRESENTABLE**

**Level reached: 3. Failed at: 9** (and at 4/5: no new representation).

---

## D. Test C — unknown-unknown, no target gap flag

**Plant:** append reversed token sequence (`toks + reversed(toks)`).
Mild residuals (omit 0.16, intra 0.15, lengthen 0.19). Target does **not**
set ontology_gap / compiler_insufficient / required_family.

duplicate = toks+toks. reverse_content = reversed only. Neither is append-rev.

| Condition | Secret | Verified |
|---|---|---|
| off | 0/7 | 0/7 |
| full_3_29 | 0/7 | 0/7 |
| direct | 0/7 | 0/7 |
| control | 0/7 | 0/7 |

First anomaly: omit_long / intra (mild). AIVD still emitted
`KNOWN_INTERVENTIONS_INSUFFICIENT` after intra tests — that is the
**architecture heuristic**, not a target-injected oracle and not recognition
of append-reverse.

time_to_self_detected_experiment_insufficiency: after intra battery (gap=1).
time_to_new_intervention_hypothesis (required family): never.
time_to_new_intervention_execution: never.
time_to_verified_finding: never.

**Class: NEW_FAMILY_NOT_COMPILABLE**

**Level reached: 3 (heuristic). Failed at: 4 and 10.**

---

## E. Capability matrix

| Capability | A | B | C |
|---|---|---|---|
| Detect anomaly | yes | yes | yes (mild) |
| Form hypothesis | yes (generic segmentation) | yes (same) | yes (same) |
| Detect experimental insufficiency | heuristic gap after intra | heuristic | heuristic (not from target) |
| Invent new family | **no** | **no** | **no** |
| Represent new family | no | no | no |
| Execute new family | no | no | no |
| Causal discovery | no (wrong family) | no | no |
| Independent verification | 0/7 | 0/7 | 0/7 |

No overall score.

---

## F. Scientific conclusion

1. **3.29 can:** observe residuals, declare a generic ontology gap after
   intra, lease compiler families, release slots, continue FIELD_DELIMITER
   (`| # ~`), reproduce/verify **when the plant is inside that compiler**.

2. **3.29 cannot:** invent a family that is not already a constructor
   (join-all, cyclic shift, append-reverse), or build a new executable
   experiment language from primitives.

3. **A first failure:** required JOIN_ALL never hypothesized or compiled.
   Known families ran and were revoked.

4. **B first failure:** cyclic shift never represented. Swap/reverse/compose-2
   are the only reorderings.

5. **C first failure:** same compiler wall. Self-detected gap is the intra
   heuristic, not discovery of append-reverse.

6. **Open-world intervention invention:** no.

7. **Open-ended experiment-language construction:** no.

8. **Unknown-unknown discovery:** no.

9. **Next bottleneck:** the compiler **is** the experiment language.
   Lazy inventory only explores families the architecture already knows.
   Closing Levels 4–10 requires runtime construction of operators that
   are not in `gap.py` / `methods.py` / `operators.py`.

Do not treat this as a product bug. It is the measured frontier of 3.29.

Anti-cheat: INVENT_CAP=48; budget=32; no plant in `aivd/science` except
audit blocklist; no holdout retune; existing-space oracle miss on all
three; controls 0/7; evaluator_verify private pass.
