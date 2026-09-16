## 3.30.0 — Open-world intervention IR synthesis

The 3.29 compiler was the experiment language. 3.30 keeps that compiler
as the fast path and adds a question-directed IR synthesizer (SWAP any
indices, MOVE, WRAP_EACH) only after known leases fail to distinguish.
INVENT_CAP stays 48. Budget 32. No JOIN_ALL / CYCLIC_SHIFT / APPEND_REVERSED
constructors.

- OW1 swap-ends, OW2 wrap-each, OW3 move-last, OW5 continuation, OW6 after cap: 7/7
- 3.29 cannot find OW1
- SU/ST/SO still verified on 3.30
- 3.25–3.29 sacred first-runs untouched

---

