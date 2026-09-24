# F1 behavior bank

Hash: `e417e460fcc050b8ee7cf44c891e3ae44dda0b7bf4348c9b045430b9972d223c`

The Stage G bank cannot yield a complete signature, because its empty probe is returned before any program runs. This bank is a different object. It was fixed before the official corpus was generated. No candidate output was used to choose a probe.

| Probe | Why it is here |
|---|---|
| `a` | one character, so a negative index and a reverse have a boundary |
| `ab` | two characters |
| `abcd` | four characters |
| `abcdefgh` | eight characters |
| `ab cd` | two tokens |
| `ab cd ef gh` | four tokens |
| `a1b2` | a digit inside a token |
| `a,b` | a comma inside a token |

Every probe has at least one token. The empty string is excluded because Phase 0 showed it is not evaluated. Corpus size 64. The first 16, in generator order, are measured. The order is not changed after the fact.
