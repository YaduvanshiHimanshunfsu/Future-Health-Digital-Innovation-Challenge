# Data sources declaration

**Why this exists:** the FAQ says "Use only data you have the legal right to use, declare every data source, and avoid personal data you do not need". The organisers provide no data, including no sample genetic data.

**Status (5 Nov 2026):** updated after sub-phase 2.2. Sub-phase 6.4 completes it. The licence column says how each one was checked, and "Not confirmed" means nobody has read the terms yet.

## Used in the prototype today

| Source | Used for | Personal data? | Licence |
|---|---|---|---|
| Team-generated synthetic population (`backend/synthetic/`) | Demo people, couples and lab reports. Seeded and reproducible | No, fully generated | Own work |
| Gene values in `backend/packs/*/panel.yaml` | Carrier frequencies and detection rates for the demo | No | Own work. **Placeholders, not measurements of any population.** Every entry says so |
| LOINC codes (`backend/app/ingestion/loinc.py`) | The codes a FHIR genetics report uses for gene, variant, significance and allelic state | No | **Not confirmed from the primary text.** HL7's licence page says LOINC is free of charge. A Regenstrief licence review says a short notice is needed when LOINC is part of a product, so the notice below is included. loinc.org refused an automated fetch, so a person still has to read loinc.org/license |
| HL7 FHIR R4B (report structure) | The format of lab reports | No | CC0, read at hl7.org/fhir/R4B/license.html on 5 Nov 2026. HL7 and FHIR names are trademarks |
| HL7 `v3-ActReason` code `HTEST` | Labels every synthetic report as test data | No | **Not confirmed.** The terminology pages we could reach state no licence |
| HGVS variant notation | How variants are written | No | A naming convention, with no data taken from it |
| HGNC-style gene symbols | Naming genes such as HBB | No | **Not confirmed** |

| Synthetic programme activity (`backend/app/ops/seed_metrics.py`) | The metrics dashboard: 360 invented people with invented journeys and scores | No, fully generated, with no account, ID or findings | Own work. No group is given worse odds on purpose, so any gap it shows is noise |
| SURE test (Légaré et al., Can Fam Physician 2010) | A four-item decision check, in the team's adapted wording | No | **Not confirmed.** The authors make it available with citation; written permission still to be confirmed. Labelled "adapted, not validated in Hindi or Arabic" on screen |

### Services the prototype sends data to

| Service | What it receives | What it never receives | Status |
|---|---|---|---|
| Google Gemini API (when `LLM_PROVIDER` includes `gemini` and a key is set) | The **redacted** question (unknown words masked), listed fact fields without any figures, and approved knowledge-base passages | Names, ID numbers, figures, the person's own words outside the word list, the user's email | Hosted model, so a data processor. Production refuses it until `LLM_EXTERNAL_APPROVED=true`, after a data processing agreement. The free tier's terms allow Google to use inputs to improve its products, which is acceptable only because every input here is synthetic |
| Ollama on the same machine (`LLM_PROVIDER` includes `ollama`) | The same as Gemini | The same | Runs locally: nothing leaves the machine. Model `qwen2.5:3b` (Apache 2.0, per its model card; to confirm) |
| Browser speech (Listen button) | The text on screen, spoken by an on-device voice | Anything, if no on-device voice exists: then there is no button | On-device only; network voices are filtered out |

**About the variants in the personas:** a few, such as `c.20A>T` in HBB, are written like well-known textbook variants, and others are made up. They're attached only to fictional people. The random population's variants are generated, and don't correspond to anything on purpose.

**LOINC notice:** This material contains content from LOINC (http://loinc.org). LOINC is copyright Regenstrief Institute, Inc. and the Logical Observation Identifiers Names and Codes (LOINC) Committee, and is available at no cost under the license at http://loinc.org/license. LOINC is a registered United States trademark of Regenstrief Institute, Inc. The wording comes from secondary sources, so check it, and the copyright years, against the primary text.

## Planned, and not used so far

Nothing has been taken from these yet. Check each licence before use, and remove anything still unused by sub-phase 6.4.

| Source | Would be used for | Personal data? | Licence checked? |
|---|---|---|---|
| gnomAD | Replacing placeholder carrier frequencies | No, aggregate | To check |
| ClinVar | Variant reference | No | To check |
| Published literature cited in `docs/01` | Context and evidence | No | Cite only |
| CTGA, GeneReviews, Orphanet, OMIM | Reference while writing content (M7) | No | To check; reuse limits may apply |
| MedlinePlus Genetics | Reference while writing content | No | To check |
| Volunteer comprehension test (sub-phase 6.2) | Pre and post scores | Anonymous, using synthetic personas only | Own collection, with consent |
| National Family Health Survey (India) summary | Context on consanguinity in India | No, aggregate | To check |

**Never used:** real patient data, real genetic results, or data from the Emirati Genome Programme.
