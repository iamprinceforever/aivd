# Probe library

The investigator may select only these probes, in this order.

| Id | Pair | When it is valid | What it holds fixed |
|---|---|---|---|
| CF-A | history / preserved | trajectory has at least two turns | the recorded follow-up, history kept |
| CF-B | history / reset | same | the same follow-up, history removed |
| CF-C | sensitivity / public-class | candidate declares a prior slot | prior value is the class token `public-class-1`, not a sealed value |
| CF-D | authorization / declared-state | candidate declares an authorization slot | the probe states `AUTHORIZED` or `DENIED` |
| CF-E | branch / alternate | candidate names a branch | the other recorded branch only |
| CF-F | mutation / without-mutation | candidate names a mutation | the follow-up without that state change |

CF-C's isolated counterpart is an observation the harness may supply later. The library text itself uses `public-class-1` and does not contain a sealed token.

A later probe is chosen by walking this table. If the candidate does not have the required slot, that row is skipped. A probe id outside the table is rejected. Observing an interesting output does not add a new probe class.

Authorization observations use two prefixes. `FUNCTIONAL_ONLY:` records a functional mismatch and contradicts a security hypothesis. `SECURITY_BOUNDARY:` supports the authorization hypothesis. The engine does not consult a hidden rule to decide which prefix applies. The observation has to state it.

No probe is executed in this stage. Materializing a probe only builds the text, the counterfactual id, and the input hash.
