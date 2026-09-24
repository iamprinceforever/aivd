# AIVD 4.0 state machine

Design only. States describe the behavior engine. They are not new values of `failure_class`, and they do not replace `UNRESOLVED` or `VERIFIED`.

## Program states

```
UNCHARACTERIZED
    -> EXPERIMENT_RUNNING        bank hash fixed, apply_micro in order
    -> SIGNATURE_SEALED          outputs frozen, no comparison yet
    -> COMPARED
         -> KNOWN_OBSERVATION    OBSERVED_EQUIVALENT to one dimension
         -> NEW_DIMENSION        OBSERVED_DISTINCT from every dimension
         -> INSUFFICIENT         at least one comparison cannot be made
```

`INSUFFICIENT` does not fall through to `NEW_DIMENSION`. A retry uses the same bank. It does not add probes.

`NEW_DIMENSION` writes one `BehavioralDimension` and moves the body to `IN_MEMORY`.

## Memory and frontier

```
IN_MEMORY
    -> ON_FRONTIER               its body may be composed with other in-memory bodies
    -> SELECTED                  behavior budget charged
    -> COMPOSED                  sequential apply, the existing compose shape
    -> EXPERIMENT_RUNNING        the composition is just another program
```

A composition that becomes `KNOWN_OBSERVATION` leaves the frontier. A composition that becomes `NEW_DIMENSION` enters memory and may be selected later. There is no state named level, depth, or generation cap. The longest parent chain is a measurement taken at the end.

The behavior budget is a counter of executor calls. At zero, `SELECTED` is refused and the machine stops. The episode budget and `board.executed` are not this counter.

## Security, off to the side

```
IN_MEMORY
    -> SECURITY_UNEVALUATED      the initial security state of every dimension
    -> SECURITY_CHARACTERIZED    a later stage ran
         -> NOT_A_FINDING
         -> CANDIDATE_FINDING
```

`CANDIDATE_FINDING` is not `VERIFIED`. Only the existing verifier, using its existing substring-and-reproduction rule, can set verified. The behavior machine does not call that verifier and does not write `secret_found`.

A transition on the security side does not change the signature, the dimension id, or the frontier. Novelty does not move a dimension to `CANDIDATE_FINDING`.

## What is deliberately absent

- no edge from `informative` to `NEW_DIMENSION`
- no edge from `representation_gap` to `NEW_DIMENSION`
- no edge from a family label to `NEW_DIMENSION`
- no edge from `NEW_DIMENSION` to `VERIFIED`
- no edge that raises `max_executed`

## Stop

This machine is not implemented. Production code is unchanged until the design is reviewed.
