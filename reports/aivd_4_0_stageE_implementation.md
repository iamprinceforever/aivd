# AIVD 4.0 Stage E

Status: implemented and validated as machinery. This is not unknown-behavior discovery.

The engine is `aivd.behavior.discovery`. It is not imported by `aivd.science`, and it does not modify the existing `aivd.behavior` encoder package. The only execution primitive is `apply_micro`. There is no second executor.

`output == input` is `AMBIGUOUS_COPY`. That status is not agreement and not a distinction. A signature with any ambiguous probe or any execution failure does not mint a dimension. An insufficient comparison does not mint one either.

The content id is `hash(bank hash + sealed signature)`. It does not include a body key, a family, or a target. The public receipt carries an opaque handle only. `semantic_class_of` is not an input. `informative`, `secret`, and `representation_gap` are not inputs. A new dimension stays `UNEVALUATED`. The engine has no verifier.

Memory lasts for the epoch and is cleared at the firewall. Pairs are the lexicographic order of opaque handles already in memory. There is no depth parameter. Growth stops when no eligible pair remains or the pair reserve cannot pay. The budget is 256 `apply_micro` calls, split 128 / 128. It does not touch the episode budget, `max_executed`, or `invent_cap`.

The frozen discovery bank, hash `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5`, is refused and was not executed. Fixture probes are not that bank. The doubled-odd body was not constructed. Same-family stride separation on a fixture probe is `HISTORICAL_REPLAY` of the machinery, not a discovery claim.

Full regression after this stage, including Stage F's non-executing harness: 1387 passed.

**STAGE E = IMPLEMENTED / VALIDATED.**

**NO PRODUCTION INTERVENTION OUTSIDE `aivd.behavior.discovery`.**
