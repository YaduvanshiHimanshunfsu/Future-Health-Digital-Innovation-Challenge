# Phase 2: Genomic Data and Deterministic Risk Engine

**Dates:** 7–9 Nov 2026 · **Build steps:** `backend.md` §9 steps 7–11 · **Requirements:** R1, R4 (minimisation), R5 (start of trace)

**Status (5 Nov 2026):** backend built and tested, ahead of the 7 Nov start. Three things keep this phase open: clinical review of the rules, the screens, and a comprehension check. Evidence per check is in [CROSS_VERIFICATION.md](CROSS_VERIFICATION.md).

**Phase goal:** a synthetic lab result goes in, encrypted, and the correct risk appears on screen, with every number traceable to a tested rule.

**Why here:** every explanation, triage decision and metric depends on these numbers. This is where the review found the most dangerous bugs.

---

## 2.1 Encryption and key management

**Goal:** genetic findings are never stored readable, and a ciphertext can't be moved to another row.

**Objectives**
- O2.1.1 Envelope encryption with a fresh key per record.
- O2.1.2 Ciphertext bound to its row.
- O2.1.3 Local key mode is refused in production.

**Work** (step 7): key provider interface (local for dev, Vault as T3), field cipher, encryption of the fields decided in 1.5.

**Files:** `backend/app/privacy/kms.py`, `backend/app/privacy/crypto.py`
**Issues to close:** H18

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V2.1.1 | Round trip returns the original | `tests/unit/test_crypto.py` |
| V2.1.2 | Wrong AAD or a swapped row raises an error | Same |
| V2.1.3 | Tampered ciphertext is rejected | Same |
| V2.1.4 | A raw DB dump contains no gene names | Inspect a query result; attach to `brain.md` |

---

## 2.2 Reference data and synthetic population

**Goal:** realistic, reproducible, clearly fake data that exercises every clinical scenario.

**Objectives**
- O2.2.1 A gene table covers the conditions most common in the reference pack, held in that pack.
- O2.2.2 Every engine scenario appears in the data.
- O2.2.3 Output is reproducible from a seed.
- O2.2.4 Nothing could be mistaken for real data.
- O2.2.5 Every data input is legal to use, and declared.

**Work** (step 8)
- Expand the gene table, including retinal and glaucoma genes, with each value marked as a placeholder and sourced where possible.
- Add a risk-group field for cases such as HBA1/HBA2.
- Generator for people, couples and FHIR bundles.
- The organisers provide no data, so we generate it all and list every input source.
- Named demo personas, for Abu Dhabi and India: at-risk couple, X-linked carrier, VUS, hemizygous male, compound finding, one-carrier cousins, unrelated with no findings.

**Files:** `backend/app/risk_engine/data/carrier_frequencies.yaml`, `backend/synthetic/generate.py`, `backend/synthetic/personas.yaml`, `docs/submission/data_sources.md`
**Issues to close:** M3, part of H3, S10

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V2.2.1 | Same seed gives identical output | Compare file hashes |
| V2.2.2 | Each scenario appears at least once | Coverage report from the generator |
| V2.2.3 | National IDs are obviously fake and the placeholder label is in the file header | Reviewer |
| V2.2.4 | Observed carrier rates are close to table values | Summary table |
| V2.2.5 | The gene table covers the listed conditions, each marked as a placeholder with its source | Reviewer |
| V2.2.6 | Every input is listed in `data_sources.md`, with its licence checked | Reviewer |
| V2.2.7 | Personas exist for both packs | Generator report |

---

## 2.3 Results ingestion

**Goal:** only the reportable minimum is kept, safely and traceably.

**Objectives**
- O2.3.1 Malformed input is rejected cleanly.
- O2.3.2 Benign variants are dropped.
- O2.3.3 Replays are harmless, and a second or amended report works.
- O2.3.4 Triage runs on arrival.
- O2.3.5 Attestation status is meaningful.
- O2.3.6 A person is linked to their own results safely on first sign-in.

**Work** (step 9)
- Validate with `fhir.resources`, then parse.
- Decide attestation: real signature check, or an explicit demo-attested flag.
- Add a person provisioning route to link the lab identity to login.
- Add report versioning.

**Files:** `backend/app/ingestion/*`, `backend/app/api/v1/reports.py`, `backend/app/api/v1/me.py`
**Issues to close:** **C1**, C8 (hook), H7 (duplicates), M8, part of H14

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V2.3.1 | Benign variant absent after ingest | API test |
| V2.3.2 | Replay gives the same report and no duplicate rows | API test |
| V2.3.3 | A second report for one person succeeds | API test (this fails in the original spec) |
| V2.3.4 | Malformed types give 422, not 500 | Parametrised test |
| V2.3.5 | Demo-attested data is visible to matching | Test ties to V3.3.1 |
| V2.3.6 | Possibly-affected finding creates P1 on ingest | Test ties to 4.5 |
| V2.3.7 | First sign-in links to the lab identity, and an unlinked user sees no data | API test |

---

## 2.4 Risk engine

**Goal:** every number is exactly right, and any uncertain case produces no number.

**Objectives**
- O2.4.1 Handles zygosity, X-linked and multiple variants correctly.
- O2.4.2 Unknown data results in "no number, refer", never a guess.
- O2.4.3 Kinship is used in residual risk.
- O2.4.4 A partner-safe view can't leak non-shared findings.
- O2.4.5 No I/O or LLM imports in the engine.

**Work** (step 10)
- Rules for: het × het, hom × het, hom × hom, compound, XL by sex and zygosity, male XL, VUS (including VUS mixed with P), tested negative with kinship prior, untested, unknown gene.
- Group findings by gene as a list, not a dict.
- Separate the internal function from the partner-safe view.

**Files:** `backend/app/risk_engine/*`
**Issues to close:** **C3, C4, C7**, H1, H2, H3, H4, H5

**Cross-verification** (a person who didn't write the engine works the expected answers by hand first)
| ID | Check | Evidence |
|---|---|---|
| V2.4.1 | Hemizygous XL male is never "carrier" | `tests/unit/test_risk_engine.py` |
| V2.4.2 | Homozygous × heterozygous gives 1/2 affected | Same |
| V2.4.3 | Two P variants in one gene escalates | Same |
| V2.4.4 | Any VUS in a gene means no number for that gene, including mixed findings | Hypothesis property |
| V2.4.5 | Unknown gene gives "refer", no crash | Same |
| V2.4.6 | First-cousin residual exceeds unrelated residual | Property test |
| V2.4.7 | Outcome probabilities sum to 1 | Property test |
| V2.4.8 | HBA1 × HBA2 flags review | Test |
| V2.4.9 | Partner view contains only intersection genes | Property test |
| V2.4.10 | 100% branch coverage | Coverage report |
| V2.4.11 | Engine imports nothing from DB, API or LLM layers | Import-boundary test |
| V2.4.12 | Clinician reviewed the rule table | Name and date in `docs/clinical/risk_rules_review.md`, or a stated limitation |
| V2.4.13 | Homozygous X-linked female: sons 1/1, and escalates | Test |
| V2.4.14 | The empiric consanguinity range uses clinician wording, and is never shown as post-panel residual | Test, reviewer |
| V2.4.15 | Couple-level X-linked results are correct | Test |

---

## 2.5 Results API, visuals and first demo slice

**Goal:** a person logs in and sees correct, understandable results, so the first end-to-end slice is working.

**Objectives**
- O2.5.1 Owners see only their own data.
- O2.5.2 Visuals match the scenario.
- O2.5.3 Each view is audited.

**Work** (step 11)
- `/me/results`, `/me/risk` and scenario-correct visual specs.
- Frontend: icon array and Punnett components, P7 and P8 with T1 copy.
- Use template text at this stage.

**Files:** `backend/app/api/v1/results.py`, `backend/app/risk_engine/visuals.py`, `frontend/components/risk/*`, `frontend/app/[locale]/(app)/app/result/`, `frontend/app/[locale]/(app)/app/couple/`
**Issues to close:** H5, H13 (P7 and P8 copy)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V2.5.1 | User B reading A's data gets 404 | `tests/api/test_bola.py` |
| V2.5.2 | Icon counts sum to the total and match facts | Unit test |
| V2.5.3 | A single carrier sees no 25% square; X-linked uses its own visual | Unit test, screenshot |
| V2.5.4 | Visuals have pattern, label and a table alternative, in RTL too | axe report, screenshot |
| V2.5.5 | A read creates an audit row | API test |
| V2.5.6 | A non-technical person explains the screen correctly | Note in `brain.md` |

---

## 2.6 Country pack framework

**Goal:** a new country can be added through settings, with no code change and no weakening of safety rules.

**Objectives**
- O2.6.1 Everything country-specific is read from a pack.
- O2.6.2 The Abu Dhabi reference pack and a small India pack exist, each labelled with its review status.
- O2.6.3 A pack can't switch off a safety rule.
- O2.6.4 Missing or unreviewed data fails safe.

**Work**
- Pack schema and loader, with validation on start-up.
- Move options, panel, services, contacts, identity formats and equity strata into the pack.
- Replace UAE-specific names with generic ones, such as `national_id_hash`.
- Build the template, and a small India pack with Hindi and English, labelled illustrative.

**Files:** `backend/app/country_packs/*`, `backend/packs/_template/*`, `backend/packs/ae-abu-dhabi/*`, `backend/packs/in-india/*`, `backend/tests/unit/test_country_packs.py`
**Issues to close:** S9, G1, G2, G3, G4, G5, G6, G7 (other parts in Phases 4 and 5)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V2.6.1 | Switching pack changes options, language and contacts, with no code change | Test using the Abu Dhabi and India packs |
| V2.6.2 | A gene missing from the pack gives "no number, refer" | Test |
| V2.6.3 | A pack that tries to disable a validator or consent rule is rejected at load | Test |
| V2.6.4 | An unreviewed pack is refused in production and labelled in demo mode | Test |
| V2.6.5 | A search of `backend/app` finds no UAE-specific values outside adapters | Scripted search |
| V2.6.6 | A pack with no qualified human service shows that honestly, and no AI substitute | Test |
| V2.6.7 | Legal rules come from the pack, and a missing rule gives the most restrictive behaviour | Test |
| V2.6.8 | Equity strata and SLAs come from the pack | Test |

---

## Phase 2 exit gate

- [ ] All V2.4 checks pass, including the hand-worked answers. **All pass except V2.4.12, which needs a clinician.** The hand-worked answers were worked out by the author, not by a second person as `risk_rules_review.md` asks
- [x] All demo personas give correct results
- [x] Pack swap test passes (V2.6.1)
- [ ] Results and risk visible on screen for the at-risk couple. **The API serves one person's results and risk. The couple view arrives in 3.3, and the screens wait on Stitch**
- [x] No plaintext gene names in the database
- [x] `brain.md` is up to date

**If behind:** cut gene count and visual polish. Don't cut V2.4.
