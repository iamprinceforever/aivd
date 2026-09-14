# Unknown Unknowns Through Classification (AIVD 3.7)

## Purpose

Complete terminal semantics for open-ended unknown discovery:

```text
residual-channel sweep
  → UNRESOLVED_INVISIBLE   (AO / invisible-class; is_vulnerability=false)
  → VERIFIED               (observable unknown vuln after gates; classify LAST)
```

Same architecture for both outcomes. **No AO special-case cheat.** Novelty ≠ vulnerability.

## Terminal states

| State | is_vulnerability | Meaning |
|-------|------------------|---------|
| VERIFIED | **true** | Falsify + reproduce + invariant passed on security-shaped residual |
| UNRESOLVED | false | Incomplete / quota / transport — **not** absence claim |
| UNRESOLVED_INVISIBLE | false | Full sweep; no actionable security-shaped residual (AO family) |
| REJECTED | false | Gates failed / adversarial |

**Never** map AO miss → SAFE. **Never** map Gemini 429 → UNRESOLVED_INVISIBLE or SAFE/vuln.

## Security-shaped channels

Prefer: `state.*`, `tool.*`, `error`, `out.refusal`.  
`out.hash` / `out.len` / `metric` alone are **not** sufficient for a vuln claim.

## Classification (LAST)

After verify only. Labels include: `invisible_unresolved`, `unclassified_mechanism`, `state_injection`, `delayed_trigger`, `interaction_gate`, `tool_channel`, …

## H7

Blind / open sparse discovery remains **Not demonstrated**. Planted observable unknowns (Vuln A/B) are a different threat model.

## Package

`aivd37/unknowns/` — see modules `channels`, `residual_sweep`, `open_axes`, `terminal`, `pipeline`, `benchmarks`, `classify`, `leakage`.
