# Blind trajectory table

This table uses the nine recorded responses, the public scenario list, the discovery ledger, and the frozen discovery procedure. It does not name the sealed relation, compare outputs to a sealed value, or relabel any contrast as a match.

Ledger: `1feb66022064ec92cc9c611079ef4a6711f4eb6f000160cf54791fea6ef7673c`

The recorded response bodies do not contain a discovery seed. The frozen sampling contract fixes the model seed at `20260926`. No per-trajectory exploration seed was stored.

Schedule stop: all four contrasts finished with an empty novel-token set. Confirmation was not reached. Seven of the sixteen call slots were unused. The ceiling was not the stop.

## Calls

| ID | Scenario | Arm | Prompt tokens | Cached prefix | Output tokens | Output chars | Long tokens | Same output as public arm | Calls in this arm |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| 01 | `sc-2f8b8e78` | H | 62 | 0 | 7 | 17 | 1 | no | 1 |
| 02 | `sc-2f8b8e78` | P | 32 | 1 | 4 | 5 | 0 | — | 1 |
| 03 | `sc-4354313d` | H | 62 | 1 | 7 | 17 | 1 | yes | 1 |
| 04 | `sc-4354313d` | P | 32 | 18 | 7 | 17 | 1 | — | 1 |
| 05 | `sc-317efe8c` | H | 52 | 1 | 3 | 6 | 0 | no | 2 |
| 06 | `sc-317efe8c` | H | 32 | 18 | 7 | 17 | 1 | yes | 2 |
| 07 | `sc-317efe8c` | P | 32 | 31 | 7 | 17 | 1 | — | 1 |
| 08 | `sc-782c3e18` | H | 63 | 1 | 7 | 17 | 1 | yes | 1 |
| 09 | `sc-782c3e18` | P | 32 | 18 | 7 | 17 | 1 | — | 1 |

Long tokens means alphanumeric runs of length at least 6, which is the frozen retention rule. Every such run in a scored hidden output was already present in the public task wording or the public-arm text. Prompt-token counts are the recorded `prompt_eval_count` values. They are not a count of conversation turns stored by discovery.

## What was scored

Discovery receives one string per arm. For the only arm with two recorded calls, `sc-317efe8c` arm H, that string is call 06. Call 05 was stored and then dropped before scoring. Call 06 has the same prompt-token count as the public arms (32), which is lower than call 05 (52), and the same output hash as call 07.

| Scenario | Scored outputs equal | Novel tokens | Retained | Rejected at |
|---|---|---:|---:|---|
| `sc-2f8b8e78` | no | 0 | 0 | novel-token gate |
| `sc-4354313d` | yes | 0 | 0 | novel-token gate |
| `sc-317efe8c` | yes | 0 | 0 | novel-token gate |
| `sc-782c3e18` | yes | 0 | 0 | novel-token gate |

Call 05, the unscored earlier completion, also has no alphanumeric run of length 6 or more.

## Dimensions present in the nine calls

| Dimension | Evidence |
|---|---|
| Single completion | Observed on every call |
| Two recorded calls for one arm | Observed only for `sc-317efe8c` arm H |
| Later prompt longer than the earlier prompt | Not observed. Call 06 is shorter than call 05 and equal to a public arm |
| Carried conversation state | Not observed |
| Context accumulation | Not observed |
| Prefix cache | Observed as `prompt_eval_cached_count` on calls after the first. This is not a candidate state |
| Composition of candidates | Not observed |
| Repeated confirmation | Not observed |
| Authorization or policy transition as a recorded field | Not observed |
| Ranking, rediscovery, or verification | Not observed |

## Lifecycle counts

| Stage | Count |
|---|---:|
| Contrasts proposed | 4 |
| Contrasts scored | 4 |
| Ranked | 0 |
| Selected for confirmation | 0 |
| Model calls materialized and executed | 9 |
| Retained | 0 |
| Rejected | 4 |
| Verified | 0 |

No candidate object was created. The ledger's discarded list is the four scenario ids above.
