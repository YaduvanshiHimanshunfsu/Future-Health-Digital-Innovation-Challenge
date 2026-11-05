# Risk Rules Review

**Status:** checked against the project review's issue list on 5 Nov 2026 (V1.2.7). **No clinician or geneticist has reviewed these rules, so V2.4.12 stays open.** Without a reviewer, the submission must state this as a limitation.

This table is the specification for the risk engine in sub-phase 2.4. A person other than the author works out the expected answers by hand first.

## Rule table

| # | Input | Result | Number? | Escalation | Issue | Check |
|---|---|---|---|---|---|---|
| 1 | Gene not in the pack, or inheritance unknown | Refer | No | Counsellor | H2 | V2.4.5 |
| 2 | Any VUS in a gene, even alongside P or LP | Uncertain | No | P3 review | C4 | V2.4.4 |
| 3 | One person: homozygous P/LP, recessive | Possibly affected, not carrier information | No | P1 | C4 | V2.4.3 |
| 4 | One person: two different P/LP variants in one gene | Possibly affected (phase unknown) | No | P1 | C4 | V2.4.3 |
| 5 | Male: hemizygous P/LP, X-linked | Possibly affected, never "carrier" | No | Per condition | C3 | V2.4.1 |
| 6 | Female: homozygous P/LP, X-linked | Possibly affected. Each son 1/1 | Yes, for sons | P1 | C3 | V2.4.13 |
| 7 | Female: heterozygous P/LP, X-linked | Each son 1/2 affected, each daughter 1/2 carrier | Yes | P2 | H5 | V2.4.15 |
| 8 | Couple: both heterozygous, same recessive gene | 1/4 two copies, 1/2 carrier, 1/4 neither | Yes | P2 | C4 | V2.4.7 |
| 9 | Couple: homozygous × heterozygous, same gene | 1/2 two copies, 1/2 carrier | Yes | P1, via rule 3 | C4 | V2.4.2 |
| 10 | Couple: homozygous × homozygous, same gene | 1/1 two copies | Yes | P1, via rule 3 | C4 | V2.4.2 |
| 11 | Couple: findings in different genes of one risk group (HBA1, HBA2) | Flag for review | No | P2 | H3 | V2.4.8 |
| 12 | One carrier, partner tested negative | `p = prior(1−d) / (1 − prior·d)`, child risk `p/4`, where prior is adjusted for kinship | Yes | Offered | H1 | V2.4.6 |
| 13 | One carrier, partner untested | `p = r + (1−r)q`, child risk `p/4` | Yes | Offered | | V2.4.6 |
| 14 | Related couple, no shared finding | Clinician-approved wording. **Never** shown as residual risk after a negative panel | Only as approved | Extended testing offered as an option | H4 | V2.4.14 |
| 15 | Father X-linked P/LP, mother not a carrier | Daughters are obligate carriers, sons unaffected | Yes | P2 | H5 | V2.4.15 |
| 16 | Partner has no report | Can't determine. Never "no shared finding" | No | | C2 | V3.3.2 |

Where `q` is carrier frequency, `d` is detection rate, and `r` is the coefficient of relationship.

## Coefficients

| Relationship | r |
|---|---|
| Double first cousins | 1/4 |
| First cousins | 1/8 |
| First cousins once removed | 1/16 |
| Second cousins | 1/32 |
| Unrelated or unknown | 0 |

## Questions for a clinician

1. **Rule 5:** which conditions need P1 and which don't? G6PD could make about 8% of men "urgent", on placeholder frequencies. **For now**, the packs mark G6PD `routine_when_hemizygous`, which gives P3. This is an engineering default awaiting a clinician's decision.
2. **Rule 4:** is "possibly affected" the right wording when the phase of two variants is unknown?
3. **Rule 14:** what can honestly be said about added risk after a negative panel, and for double first cousins?
4. **Rule 11:** which other gene groups need this treatment?
5. **Reduced penetrance (M11):** which conditions need "inherits two copies" instead of "has the condition"?
6. **SMN1 and CYP21A2:** do these need special handling for detection limits, given silent carriers and pseudogenes?
