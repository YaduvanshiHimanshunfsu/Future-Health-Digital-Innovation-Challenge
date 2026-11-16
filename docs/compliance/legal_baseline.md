# Legal Baseline

**Status:** draft, 5 Nov 2026. **This is not legal advice, and no lawyer has reviewed it.** It comes from reading the decree-law text and law-firm summaries. Confirm it with counsel or the regulator before any pilot.

## Abu Dhabi reference pack: Federal Decree-Law 49/2023 article map

Text read from the [Dubai Health Authority copy](https://dha.gov.ae/uploads/062024/Federal%20Law_49_2023_Regulating%20the%20Use%20of%20the%20Human%20Genome202466484.pdf). Paraphrased.

| Article | What it says | Feature or limitation | Where |
|---|---|---|---|
| 6 | Informed consent, written and explicit, on the Health Authority's form, for voluntary screening | Samvid doesn't run screening. Service consent covers our processing, and isn't a substitute for the screening consent | 3.2 |
| 8 | A person can withdraw from voluntary screening at any stage | Stated in content. Withdrawal is handled by the screening entity | Limitation |
| 9(1) | A person may request their own results | `/me/results` | 2.5 |
| 9(2) | A person can state in writing that they don't want to know | Right-not-to-know flow | 3.2 |
| 9(3) | Informing is obligatory if results threaten the person's or a foetus's life | Exception in `legal.yaml`, set by a clinician | 2.6, 3.2 |
| 9(4) | A specialist provides genetic counselling after results | The basis for "AI never replaces counsellors" | 4.5 |
| 9(5) | Lineage results only to the sample's owner | Never produced or shown | Limitation |
| 9(6) | Non-targeted findings only after consent to know them | Only targeted panel findings are ingested | 2.3 |
| 11 | Gamete and embryo screening is for hereditary disease, under a specialist's approval | Described as an option, and provided by clinics | 4.4 |
| 15(1) | Screening is obligatory for couples marrying | Context for the pack | Pack |
| 15(2) | Marriage contract needs evidence of the exam, and the couple are informed of results | Limits what "keep private" can mean. **Open question below** | 3.3 |
| 25(1) | Genetic data is confidential | Consent ledger, encryption, audit | 2.1, 3 |
| 25(2) | No discrimination based on genetic traits | Non-stigmatising language, equity reporting | 4.2, 5.4 |
| 25(3) | Publishing Genome Programme data needs approval | Synthetic data only | 2.2 |
| 26 | Screening entities supply data to a National Genomic Database | Samvid isn't a screening entity, and sends nothing there. Confirm with counsel | Open question |
| 28 | Storing or transferring genetic data needs a Health Authority licence | **A pilot must run under a licensed partner.** The prototype holds synthetic data only | 6.4 |
| 33 | Penalties for breaching 9(5) and 9(6), including imprisonment | Reinforces the design above | Risk |

## Other UAE law

| Law | Relevance | Confidence |
|---|---|---|
| Federal Law 2/2019 (health data), Art. 13 | Health data generally stays in the UAE, with exceptions | Law-firm summaries |
| Federal Law 2/2019, Art. 20 | Keep health information at least 25 years from the last procedure | Official extract |
| PDPL (Decree-Law 45/2021), Art. 2 | Generally carves out health data that has its own legislation | Secondary sources; exact wording not confirmed |
| Assisted reproduction law, amended 2023 | Third-party gametes reported as barred. Details disputed | Law-firm commentary only |
| Decree-Law 24/2022 on children of unknown parentage, amended 2025 | Fostering (kafala). Adoption isn't allowed, per the UAE government portal | Official portal |

## Retention table

A first draft, per pack. Nothing below is final.

| Data | Abu Dhabi pack (draft) | Reason |
|---|---|---|
| Findings and results | 25 years from the last health procedure | Federal Law 2/2019, Art. 20 |
| Care cases, pathway steps, case notes | 25 years | Same |
| Audit log | Same as the records it covers | Must outlive what it proves |
| Consent records | Same as the records they cover | Proof of permission |
| Chat messages | **Open question:** are they health records? Default: treat as records until counsel says otherwise | The spec's 90 days may conflict (H19) |
| Analytics events | As long as useful, since de-identified | No identity held |
| Invitations | Delete 90 days after expiry | Data minimisation |

**Erasure:** the API's database role can't delete findings or consents, by design. A person's erasure request goes through an administrative process that respects the retention rule.

## Questions for counsel and regulators

1. How are couple results delivered in practice under Art. 15(2)? (S6)
2. Does Samvid count as an entity providing services "related to Human Genomes" under Art. 28, and under whose licence would a pilot run?
3. Do chat messages count as health records for the 25-year rule?
4. Does the AI explanation layer count as a medical device under DoH rules?
5. Is any cross-border processing permitted for LLM calls, or must all of it stay in-country?
6. Which UAE assisted-reproduction options may be described, and with what wording?
## Other countries

Each country pack adds its own table. Starting points are in [docs/07](../07_Global_Design_and_Country_Packs.md), section 6.
