## 3.29.0 — Lazy family inventory; INVENT_CAP unchanged

3.28 could not register a second-wave family on an 11-token seed because
the eager inventor was full (INVENT_CAP=48). 3.29 does **not** raise the
cap. It separates hypothesis-family representation from the executable
registry: revoked leases release slots; a deferred family materializes
one parameterization at a time.

- INVENT_CAP remains 48
- SU hash-field (TOKEN#body, long seed): 3.29 VERIFIED 7/7; 3.28 0/7
- ST/SO/SP/SM/SK still verified
- 3.25–3.28 sacred first-runs untouched
- No `|` / field_124 / cap bump

---

