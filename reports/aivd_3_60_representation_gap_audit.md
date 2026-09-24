# AIVD 3.60 representation-gap audit

Offline. The event is a boolean, not a score. No model. The doubled odd-stride body was not constructed.

**NO PRODUCTION INTERVENTION AUTHORIZED**

## Formula

`c.secret or (c.security_shaped and not c.greedy_metric) or (c.metric_delta >= 0.08 and c.error and not c.greedy_metric)`

The event is logged only when that value is true, secret is false, and the probe used an operator. c.secret cannot open this gate, because the gate also requires not c.secret.

`security_shaped` is `secret or error_appeared or (error and metric >= 0.2)`. `greedy_metric` is `metric >= 0.55 and not secret and not error_appeared`.

Inputs are the observation's secret bit, error, metric, and metric delta. Program outputs, the 12-probe bank, and the family label are not inputs. Why 0.08: **NOT_RECORDED**.

## What happens next

The flag is written in three places and read in none. The observe branch then calls `invent()` and, when the mode allows it, `_maybe_declare_gap()`. Those can add methods. They do not rank atom candidates, admit a composition, retire a lease, or verify a secret.

Retirement of the two compose programs used the lease boolean, which is computed earlier and is a different formula.

## computational_usefulness

`reason = "secret" if c.secret else "computational_usefulness"`

That string is the else of secret when an atom is promoted. It is stored as the reason. It is not the gap gate, and it is not an output comparison.

## The two programs

`cmp_atom_rd2_mapt_at_-1_atom_rd6_mapt_cat_at_-1_`: event not logged. The gate was false. The metric is NOT_RECORDED.

`cmp_atom_rd7_mapt_slice_1_2_tok_atom_rd8_mapt_ca`: event logged. The next log line is `generation_decision`, not `invent`, so that call added no method. The program was already retired. The metric is NOT_RECORDED.

Both programs differ on the frozen bank. The gap does not say that, and its absence does not deny it.

## History

The boolean is b6e6f9c8 AIVD 3.21.0. The event and the `invent()` call are ed8059d2 AIVD 3.24.0. The formula has not changed. A definition of representation quality is NOT_RECORDED. The code comment is: token-level residual without secret; current grammar may not preserve identity.

## Hypotheses

- **H27a.** SUPPORTED as an observation-side boolean. It is not a stored numeric quality score.
- **H27b.** NOT_SUPPORTED. The gate does not read program outputs.
- **H27c.** PARTIAL. The same branch can call invent(). It does not rank candidates. On the second 3.54 program that call added nothing.
- **H27d.** NOT_SUPPORTED as purely diagnostic. The flag is unread, but the branch calls invent().
- **H27e.** SUPPORTED. Usefulness is the else of secret. The gap also requires the residual boolean. Either can occur without the other.
- **H27f.** NOT_SUPPORTED. The gate requires secret to be false.
- **H27g.** SUPPORTED. The comment says residual-without-secret. A definition of representation quality is NOT_RECORDED.
- **H27-REJECT.** NOT the result. The gate is in the source.

## Unresolved

- why metric_delta uses 0.08
- why security_shaped uses 0.2 and greedy uses 0.55
- the metric and error on either compose observation
- a definition of representation quality beyond the code comment

## Limit

A logged gap is an observation-side gate. It is not evidence the program differed from its components, and a missing log is not evidence that it did not.

## Decision

**NO PRODUCTION INTERVENTION AUTHORIZED.**
