# F3 source audit

**F3 SOURCE AUDIT COMPLETE**

**NO-QUALIFYING-SOURCE-FOUND**

No benchmark was executed. No label was treated as a discovery. The frozen relations were not changed. F3 is not implemented.

The two relations stay: non-interference, as public agreement across four sealed pairs that change only a private channel, and policy equality, only when a policy arrived with the artifact. A source that merely says "security" does not match either one.

## What was inspected

| Source | Class | Pin | Publication | License at the pin | Classification |
|---|---|---|---|---|---|
| IFSpec, downstream copy inside Co-Inflow | A | `HarvardPL/Co-InflowPrototype` `d1c7f3bed6bed734268bf36bdcb9cf5f89af78d7` | Hamann, Herda, Mantel, Mohr, Schneider, Tasch, NordSec 2018, LNCS 11252, DOI `10.1007/978-3-030-03638-6_27`. First online 2 November 2018 | Downstream repository: MIT. Original suite license: `NOT_RECORDED` | `INSUFFICIENT_RELATION` |
| Securibench Micro | D | `too4words/securibench-micro` `6a5a72488ea830d99f9464fc1f0562c4f864214b` | Stanford Griffin project. Version 1.08 described by the maintainers. Date of the paper series is 2005 | Apache-2.0 | `NOT_APPLICABLE` |
| DroidBench | D, taint suite | `secure-software-engineering/DroidBench` `a57fa6f42f278591695672f1aa8b37c275139370` | FlowDroid line of work. This pin is a git HEAD, not a release tag | `NOT_RECORDED` (no `LICENSE` file at that commit) | `NOT_APPLICABLE` |
| Public CVE corpora | D | not pinned | labels are the published vulnerabilities | not inspected | `NOT_APPLICABLE` |
| Self-generated or commissioned artifacts | E, F | none | none | none | not evidence |

`stg-tud/IFSpec` and `secure-software-engineering/IFSpec` do not exist. The 2018 paper points at `www.spp-rs3.de/IFSpec`. That site was not retrieved as a pin. The Harvard tree is a later copy, not the 2018 release commit. The original release hash is `NOT_RECORDED`.

## IFSpec

The suite predates AIVD. It was built to test information-flow analyzers, not to produce a result for this study. Each sample carries a RIFL policy. The schema uses domains, a flow relation, and handles for sources and sinks. High and low are the domain names. That policy is the authors' noninterference specification. It was not written because AIVD asked for a leak.

It still does not contain the frozen measurement. There is no set of four sealed inputs that change only a private channel, and no stored public outputs for those inputs. The published result is a secure or insecure classification of each program. Recomputing that classification is not the same question as "do all four pairs disagree." Inventing the four pairs here would change the relation. That is why the source is `INSUFFICIENT_RELATION`, not a match.

The classification is also public. Directory names in the downstream tree include the words secure and insecure. Hiding a copy of those names would not make the result unknown. This audit saw that naming scheme, so this experimenter is not blind to it.

| Claim | Does IFSpec support it? |
|---|---|
| Unknown to a future engine, if names and tags are stripped by someone else | Only as an engineering possibility |
| Unknown to this experimenter | No |
| Unknown to an evaluator | No. The evaluator would be checking a public label |
| Genuinely unknown security finding | No |

A later sealed protocol could give the engine an opaque handle, a commitment, and the RIFL roles, and withhold the secure/insecure tag. The verifier would still be recomputing the authors' label, or a new differential that the artifact does not contain. Neither is the frozen F3 test. IFSpec is not selected, and no subset rule is authorized.

## The others

Securibench Micro is a set of small Java web programs with planted injection, scripting, splitting, and path bugs. The maintainers say most cases contain a vulnerability. That is a scanner test, not non-interference across four private pairs, and not a policy that arrived as an equality relation. The vulnerabilities are the point of the suite and are public. It cannot support an unknown finding.

DroidBench is an Android taint suite: sources and sinks, with categories that describe the leak. Flow from a source to a sink is not the frozen non-interference test and not policy equality. The license at this pin was not found. It is not a qualifying source.

A CVE corpus names known vulnerabilities. A hidden copy of a public CVE is still a known vulnerability. It is not used.

No file in this audit was checked by running a program. One RIFL document was read for its schema. It uses high and low domains. It does not use the historical AIVD marker strings. A search of the whole trees was not done, so any other overlap is `NOT_RECORDED`. Nothing in the schema leaks an AIVD body.

## Verifier

For these sources, an independent party can read a public label and compare it to an analyzer. That answers "does the label say insecure?" It does not answer the frozen relation. There is nothing for a verifier to recompute under the F3 rule without adding inputs the artifact does not have.

## Next step

Do not implement F3. Do not execute these suites. Do not strip their labels and call the result unknown. A qualifying artifact would already contain either the four-pair non-interference measurement or an attached policy-equality relation, would predate the study, and would still be unread. None of the inspected sources is that artifact.

**F3 IMPLEMENTATION NOT AUTHORIZED. F3 EXPERIMENT NOT AUTHORIZED.**
