# Cross-Verification of All Phases

**Generated on 5 Nov 2026 from the phase files**, then checked by script. If you change a phase, update this document too.

**Status:** updated 5 Nov 2026. The audit below covers the **plan**. Results exist for Phases 1 and 2, in the evidence table further down.

## Audit result

| Audit | Result |
|---|---|
| Sub-phases with a goal, objectives and checks | 33 of 33 |
| Objectives with at least one check | 135 of 135 |
| Checks tied to an objective | 238 of 238 |
| Review issues with a sub-phase and a check | 62 of 62, plus M6, fixed on 3 Nov |
| Measurable targets with a check | 13 of 13 |
| File paths named in the phase plans that exist | All |
| Phase dates | Continuous from 5 to 20 Nov, with no gaps or overlaps |

## What the audit found and fixed

- **19 objectives had no check or only a partial one:** O1.1.4, O1.2.3, O1.6.2, O1.6.3, O2.2.1, O3.2.4, O3.3.2, O4.1.1, O4.3.4, O4.5.1, O5.1.3, O5.2.3, O5.3.2, O5.4.4, O5.5.1, O6.1.1, O6.2.3, O6.5.2, O6.6.3. Each now has one.
- **Several issues had no direct check:** C3 (homozygous female), C8 (triage triggers), C10 (coercion), H4, H5, H19, M1, M2, M10, M11, M12, M13, G4, G6, G8 and G9. Each now has one.
- **14 issue links were missing** between a sub-phase and an issue its checks cover, and were added.
- **Phase 1 was due to end on 5 Nov with nothing built,** so Phases 1 to 3 were re-baselined. Phases 4 to 6 keep their dates.
- **New official requirements were missing:** data source declaration, dependencies, maturity statement, code sharing, and the full requirements sent on registration (S10, S11).
- **Stale statements were corrected** in `docs/01`, `02`, `03`, `CLAUDE.md` and the README: the 15 Nov date, the "could not read the page" warning, and the simulated +30 pp target.

## Known risks in the plan

An audit can show a plan is consistent. It can't show that it's achievable.

| Risk | Why it matters | Response |
|---|---|---|
| **Team size is still unknown** | The scope assumes 4 to 5 people | Confirm it, then apply the scope tiers |
| **Phase 3 has only 2 days for 5 sub-phases** | It's the heart of the privacy claim | Cut break-glass UI and invitation polish first; never cut 3.2 or 3.3 |
| **No clinician is confirmed** | V1.2.1, V2.4.12 and V4.1.4 will end as stated limitations | Keep looking, and label content honestly |
| **Arabic text isn't approved yet** | V1.6.3, V4.2.2, V4.3.1 and V5.5.1 can't pass in Arabic without it | Approve it, and name a native speaker |
| **Full requirements are unread** | They may change the deliverables | Find them first |
| **Self-verification** | Many checks ask for a second person, which a very small team can't always provide | State who verified each one |

## Phase goals and targets

| Phase | Dates | Exit target | Sub-phases | Objectives | Checks |
|---|---|---|---|---|---|
| **1** | 5–6 Nov | Rules recorded; scope locked; stack runs from a clean clone; audit tamper test passes | 6 | 29 | 41 |
| **2** | 7–9 Nov | Hand-worked risk answers match; correct risk on screen; pack swap works | 6 | 26 | 47 |
| **3** | 10–11 Nov | Privacy suite green; no partner-only data in any output; revoke shown working | 5 | 21 | 32 |
| **4** | 12–14 Nov | Safe answers in 3 languages, even with the LLM off; cases reach a counsellor | 5 | 19 | 41 |
| **5** | 15–17 Nov | Full demo journey in 3 languages; metrics trace to events | 5 | 19 | 38 |
| **6** | 18–20 Nov | Honest safety report and limitations; submitted with confirmation saved | 6 | 21 | 39 |

## Measurable targets

| Target | Value | Verified by |
|---|---|---|
| Numeric accuracy of risk statements | 100% on the test set | V2.4.10, V4.2.1, V6.1.1 |
| Stigmatising or directive outputs | 0 in the human-scored sample | V6.1.3, V6.1.7 |
| Correct escalation of clinical questions | At least 95% in each language | V4.3.3, V6.1.2 |
| Comprehension improvement | Measured in a real test, with no simulated figures | V6.2.3, V6.2.5 |
| Comprehension gap between languages | Under 5 pp, with alerts | V5.4.1, V5.4.9 |
| Gap between literacy levels | Under 10 pp, with alerts | V5.4.9 |
| PII sent to the LLM | 0 in automated tests | V3.5.3, V3.5.4, V3.5.5 |
| Consent revocation time | Under 1 s | V3.2.2 |
| Risk engine coverage | 100% branch coverage | V2.4.10 |
| Non-LLM API speed | p95 under 300 ms | V6.3.4 |
| Eval set size | 150+ golden and 50+ red-team items, balanced across 3 languages | V6.1.6 |
| Volunteers in the comprehension test | 15 to 30 adults | V6.2.2 |
| Submission date | 19 Nov, with 20 Nov as the deadline | V6.6.1, V6.6.3 |

## Objectives to checks

Each objective is written out in its phase file.

### Phase 1

| Sub-phase | Goal | Objective | Checks |
|---|---|---|---|
| **1.1** Competition gate and scope lock | confirm the entry is valid and the scope fits the team. | O1.1.1 | V1.1.1 |
|  |  | O1.1.2 | V1.1.2, V1.1.3 |
|  |  | O1.1.3 | V1.1.4 |
|  |  | O1.1.4 | V1.1.5 |
|  |  | O1.1.5 | V1.1.6 |
|  |  | O1.1.6 | V1.1.7 |
|  |  | O1.1.7 | V1.1.8 |
| **1.2** Clinical, legal and cultural baseline | correct the spec's clinical and legal assumptions before anything is built on them. | O1.2.1 | V1.2.1 |
|  |  | O1.2.2 | V1.2.2 |
|  |  | O1.2.3 | V1.2.7 |
|  |  | O1.2.4 | V1.2.3 |
|  |  | O1.2.5 | V1.2.5 |
|  |  | O1.2.6 | V1.2.6 |
|  |  | O1.2.7 | V1.2.8 |
|  |  | O1.2.8 | V1.2.4, V1.2.9, V1.2.10 |
| **1.3** Repository, tooling and local stack | one command brings up all services on a clean machine. | O1.3.1 | V1.3.1, V1.3.2 |
|  |  | O1.3.2 | V1.3.5 |
|  |  | O1.3.3 | V1.3.3, V1.3.4 |
| **1.4** API skeleton and security core | a hardened API shell where every request is authenticated and logged safely. | O1.4.1 | V1.4.1 |
|  |  | O1.4.2 | V1.4.2, V1.4.6 |
|  |  | O1.4.3 | V1.4.3, V1.4.4 |
|  |  | O1.4.4 | V1.4.5 |
| **1.5** Data model, migrations and audit chain | the full schema exists, and tampering with the audit log is detectable. | O1.5.1 | V1.5.1, V1.5.5, V1.5.6 |
|  |  | O1.5.2 | V1.5.2 |
|  |  | O1.5.3 | V1.5.3 |
|  |  | O1.5.4 | V1.5.4, V1.5.7 |
| **1.6** Design system and frontend skeleton (parallel track) | an accessible design system, with screen designs for the main path. | O1.6.1 | V1.6.1 |
|  |  | O1.6.2 | V1.6.4 |
|  |  | O1.6.3 | V1.6.2, V1.6.3, V1.6.5 |

### Phase 2

| Sub-phase | Goal | Objective | Checks |
|---|---|---|---|
| **2.1** Encryption and key management | genetic findings are never stored readable, and a ciphertext can't be moved to another row. | O2.1.1 | V2.1.1, V2.1.4 |
|  |  | O2.1.2 | V2.1.2, V2.1.3 |
|  |  | O2.1.3 | V1.4.5 |
| **2.2** Reference data and synthetic population | realistic, reproducible, clearly fake data that exercises every clinical scenario. | O2.2.1 | V2.2.5 |
|  |  | O2.2.2 | V2.2.2, V2.2.7 |
|  |  | O2.2.3 | V2.2.1 |
|  |  | O2.2.4 | V2.2.3, V2.2.4 |
|  |  | O2.2.5 | V2.2.6 |
| **2.3** Results ingestion | only the reportable minimum is kept, safely and traceably. | O2.3.1 | V2.3.4 |
|  |  | O2.3.2 | V2.3.1 |
|  |  | O2.3.3 | V2.3.2, V2.3.3 |
|  |  | O2.3.4 | V2.3.6 |
|  |  | O2.3.5 | V2.3.5 |
|  |  | O2.3.6 | V2.3.7 |
| **2.4** Risk engine | every number is exactly right, and any uncertain case produces no number. | O2.4.1 | V2.4.1, V2.4.2, V2.4.3, V2.4.7, V2.4.13, V2.4.15 |
|  |  | O2.4.2 | V2.4.4, V2.4.5, V2.4.8 |
|  |  | O2.4.3 | V2.4.6, V2.4.12, V2.4.14 |
|  |  | O2.4.4 | V2.4.9 |
|  |  | O2.4.5 | V2.4.10, V2.4.11 |
| **2.5** Results API, visuals and first demo slice | a person logs in and sees correct, understandable results, so the first end-to-end slice is working. | O2.5.1 | V2.5.1 |
|  |  | O2.5.2 | V2.5.2, V2.5.3, V2.5.4, V2.5.6 |
|  |  | O2.5.3 | V2.5.5 |
| **2.6** Country pack framework | a new country can be added through settings, with no code change and no weakening of safety rules. | O2.6.1 | V2.6.5, V2.6.7, V2.6.8 |
|  |  | O2.6.2 | V2.6.1 |
|  |  | O2.6.3 | V2.6.3 |
|  |  | O2.6.4 | V2.6.2, V2.6.4, V2.6.6 |

### Phase 3

| Sub-phase | Goal | Objective | Checks |
|---|---|---|---|
| **3.1** Identity, roles and relationship authorisation | every object access is checked, and any failure means denial. | O3.1.1 | V3.1.3, V3.1.4 |
|  |  | O3.1.2 | V3.1.2 |
|  |  | O3.1.3 | V3.1.1 |
|  |  | O3.1.4 | V3.1.5 |
| **3.2** Consent ledger | all sharing lives in one ledger, is scoped and time-limited, and can be revoked at once. | O3.2.1 | V3.2.1, V3.2.4, V3.2.6 |
|  |  | O3.2.2 | V3.2.2, V3.2.3 |
|  |  | O3.2.3 | V3.2.5 |
|  |  | O3.2.4 | V3.2.7, V3.2.8 |
| **3.3** Couple linking and minimal-disclosure match | a couple learns only what both agreed to, and a positive result can't be missed or faked. | O3.3.1 | V3.3.1, V3.3.2 |
|  |  | O3.3.2 | V3.3.3, V3.3.9 |
|  |  | O3.3.3 | V3.3.4 |
|  |  | O3.3.4 | V3.3.5 |
|  |  | O3.3.5 | V3.3.6 |
|  |  | O3.3.6 | V3.3.7 |
|  |  | O3.3.7 | V3.3.8 |
| **3.4** Family invitations | a person can encourage relatives to get screened without identifying themselves or their result. | O3.4.1 | V3.4.2, V3.4.3, V3.4.4 |
|  |  | O3.4.2 | V3.4.1 |
|  |  | O3.4.3 | V3.4.5 |
| **3.5** Transparency: access log, break-glass and redaction | users can see who accessed their data, exceptional access is visible, and PII doesn't reach the LLM. | O3.5.1 | V3.5.1 |
|  |  | O3.5.2 | V3.5.2 |
|  |  | O3.5.3 | V3.5.3, V3.5.4, V3.5.5 |

### Phase 4

| Sub-phase | Goal | Objective | Checks |
|---|---|---|---|
| **4.1** Knowledge base and content governance | a small body of accurate, licensed, versioned content. | O4.1.1 | V4.1.2, V4.1.3, V4.1.6, V4.1.7, V4.1.8 |
|  |  | O4.1.2 | V4.1.1, V4.1.4 |
|  |  | O4.1.3 | V4.1.5 |
| **4.2** Output validators and lexicon | an answer can't reach a user with a wrong number, stigmatising words, a directive, or a diagnosis. | O4.2.1 | V4.2.1, V4.2.2 |
|  |  | O4.2.2 | V4.2.4, V4.2.8 |
|  |  | O4.2.3 | V4.2.3, V4.2.5, V4.2.6 |
|  |  | O4.2.4 | V4.2.7 |
| **4.3** Boundary router and explanation pipeline | each question is correctly classified, and the pipeline can't skip safety steps. | O4.3.1 | V4.3.1, V4.3.2, V4.3.10 |
|  |  | O4.3.2 | V4.3.3 |
|  |  | O4.3.3 | V4.3.4, V4.3.12 |
|  |  | O4.3.4 | V4.3.5, V4.3.6, V4.3.9, V4.3.11, V4.3.13 |
|  |  | O4.3.5 | V4.3.7, V4.3.8 |
| **4.4** Options and values reflection | people see correct, unranked options, and the system never turns their values into a recommendation. | O4.4.1 | V4.4.1, V4.4.5 |
|  |  | O4.4.2 | V4.4.2 |
|  |  | O4.4.3 | V4.4.3, V4.4.4 |
| **4.5** Triage, assignment and counsellor console | the right case reaches a real person on time, with useful context and no extra data. | O4.5.1 | V4.5.4, V4.5.6 |
|  |  | O4.5.2 | V4.5.2, V4.5.3 |
|  |  | O4.5.3 | V4.5.1 |
|  |  | O4.5.4 | V4.5.5, V4.5.7 |

### Phase 5

| Sub-phase | Goal | Objective | Checks |
|---|---|---|---|
| **5.1** Care-pathway state machine | every step is traceable, and a person can always say no. | O5.1.1 | V5.1.1, V5.1.2, V5.1.7 |
|  |  | O5.1.2 | V5.1.3, V5.1.4 |
|  |  | O5.1.3 | V5.1.8 |
|  |  | O5.1.4 | V5.1.5, V5.1.6, V5.1.9 |
| **5.2** Booking, referrals and FHIR mapping | a traceable hand-off from counselling to confirmatory testing and specialist services. | O5.2.1 | V5.2.3 |
|  |  | O5.2.2 | V5.2.1, V5.2.2, V5.2.5 |
|  |  | O5.2.3 | V5.2.6 |
|  |  | O5.2.4 | V5.2.4 |
| **5.3** Assessments | measure understanding in a way that tests the explanation, not the person. | O5.3.1 | V5.3.1, V5.3.2 |
|  |  | O5.3.2 | V5.3.4, V5.3.5 |
|  |  | O5.3.3 | V5.3.3 |
| **5.4** Analytics, fairness and privacy metrics | every R6 metric has a real data source and is broken down correctly. | O5.4.1 | V5.4.2, V5.4.3, V5.4.5, V5.4.6, V5.4.7 |
|  |  | O5.4.2 | V5.4.1, V5.4.9 |
|  |  | O5.4.3 | V5.4.4 |
|  |  | O5.4.4 | V5.4.8 |
| **5.5** Frontend integration and end-to-end journey | the complete demo story works without touching a database or a script. | O5.5.1 | V5.5.7 |
|  |  | O5.5.2 | V5.5.1, V5.5.4, V5.5.5, V5.5.6, V5.5.9 |
|  |  | O5.5.3 | V5.5.2, V5.5.8 |
|  |  | O5.5.4 | V5.5.3 |

### Phase 6

| Sub-phase | Goal | Objective | Checks |
|---|---|---|---|
| **6.1** Safety and accuracy evaluation | measured results, including failures, from tests that aren't marking their own work. | O6.1.1 | V6.1.6 |
|  |  | O6.1.2 | V6.1.4 |
|  |  | O6.1.3 | V6.1.3, V6.1.7 |
|  |  | O6.1.4 | V6.1.1, V6.1.2, V6.1.5 |
| **6.2** Real-user comprehension test | the first real evidence that people understand better, honestly labelled. | O6.2.1 | V6.2.2 |
|  |  | O6.2.2 | V6.2.1 |
|  |  | O6.2.3 | V6.2.5 |
|  |  | O6.2.4 | V6.2.3, V6.2.4 |
| **6.3** Security and privacy hardening | no known high-risk hole, and evidence of having looked. | O6.3.1 | V6.3.2, V6.3.4 |
|  |  | O6.3.2 | V6.3.1 |
|  |  | O6.3.3 | V6.3.3, V6.3.5 |
| **6.4** Technical documentation, assumptions, limitations, commercial plan | the documents the portal requires, plus coverage of the weakest criterion. | O6.4.1 | V6.4.1 |
|  |  | O6.4.2 | V6.4.2, V6.4.3, V6.4.6, V6.4.8, V6.4.10 |
|  |  | O6.4.3 | V6.4.4, V6.4.5 |
|  |  | O6.4.4 | V6.4.7, V6.4.9 |
| **6.5** Demo, deck and rehearsal | a clear, reliable story, even if the live demo breaks. | O6.5.1 | V6.5.1, V6.5.2 |
|  |  | O6.5.2 | V6.5.3, V6.5.4, V6.5.6 |
|  |  | O6.5.3 | V6.5.5 |
| **6.6** Submit and freeze | a complete submission accepted a day early. | O6.6.1 | V6.6.1, V6.6.3, V6.6.4 |
|  |  | O6.6.2 | V6.6.2, V6.6.5 |
|  |  | O6.6.3 | V6.6.6 |

## Checks with evidence so far

Phases 1 and 2. All later checks are open.

| Check | Status | Evidence |
|---|---|---|
| V1.1.1 | Partly | User confirmed. Confirmation still to add |
| V1.1.2 | Partly | FAQ copied. Second-person check to do |
| V1.1.3 | **Done** | Screenshots in `docs/submission/evidence/` |
| V1.1.4 to V1.1.8 | Open | Needs the team: scope, owners, full requirements, eligibility, session notes |
| V1.2.1 | Open | No reviewer yet. Limitation stated in the clinical documents |
| V1.2.2 | Partly | Sources listed, reviewer initials missing |
| V1.2.3 | **Done** | Article map in the legal baseline |
| V1.2.4 | Open | Contacts deliberately empty until verified |
| V1.2.5 | Partly | Threat model covers these cases. Reviewer sign-off missing |
| V1.2.6 | **Done** | India sections, labelled unreviewed |
| V1.2.7 | **Done** | `risk_rules_review.md`. Clinician review is V2.4.12 |
| V1.2.8 | Open | Needs a counsellor or M42 |
| V1.2.9 | **Done** | Draft table in the legal baseline |
| V1.2.10 | Open | Needs Arabic and Hindi reviewers |
| V1.3.1 | Partly | Clean rebuild: 72 s, all healthy (first build 148 s). Second person still needed |
| V1.3.2 | **Done** | `check_services`: all reachable, and a real Keycloak token verified |
| V1.3.3 | **Done** | Planted token blocked by the gitleaks hook, exit 1 |
| V1.3.4 | Partly | Every step passes locally. CI itself hasn't run, since nothing is pushed |
| V1.3.5 | Partly | Works on this Windows machine. Other team machines unknown |
| V1.4.1 | **Done** | `tests/api/test_auth.py` |
| V1.4.2 | **Done** | `tests/api/test_http_hardening.py` |
| V1.4.3 | **Done** | `tests/unit/test_logging.py`, and pack formats in `test_country_packs.py` |
| V1.4.4 | **Done** | `test_http_hardening.py` |
| V1.4.5 | **Done** | `tests/unit/test_config.py` |
| V1.4.6 | **Done** | `test_http_hardening.py` |
| V1.5.1 | **Done** | `tests/unit/test_schema.py`, which also checks models and migrations match |
| V1.5.2 | **Done** | `tests/unit/test_audit_chain.py` |
| V1.5.3 | **Done** | Same, for every column, deleted rows and forged hashes |
| V1.5.4 | **Done** | `tests/api/test_denied_audit.py` |
| V1.5.5 | Partly | Every column classified and enforced by a test, and encryption built in 2.1. Reviewer missing |
| V1.5.6 | **Done** | `test_schema.py`, and the realm and code use the same roles |
| V1.5.7 | **Done** | `tests/api/test_ingestion.py`: ingestion writes its audit row last, and the chain verifies with concurrent deliveries |
| V1.6.1 | **Done** | Calculated table in `frontend/README.md` |
| V1.6.2 | Partly | Removed from the Stitch prompts. Screens not generated yet |
| V1.6.3 to V1.6.5 | Open | Waiting on Stitch screens from the team |

### Phase 2 evidence

**Last full test run: 453 passed, 1 failed, with 92% coverage overall and 100% branch coverage on the risk engine.** It took 21.5 minutes, against the usual 2 to 3. The failure was `test_malformed_input_gets_422_and_stores_nothing[no_entries]`, which then passed alone and with its group of 25. **So the suite has not yet had a fully clean run, and that intermittent failure is unexplained.** `scripts/smoke_stack.py` passes against the real stack.

**Mutation check:** 44 safety rules were broken on purpose, one at a time, in a throwaway copy. The tests caught 42 straight away. The other two exposed real gaps, both now fixed and re-checked:
- **The database dump search was blind.** `pg_dump` writes binary columns as hex, so it passed even with encryption switched off. It now decodes those columns, and a test confirms it still can.
- **Nothing tested that the "yes or no" view hides a person's private facts.** The code was right, and now a test protects it.

| Check | Status | Evidence |
|---|---|---|
| V2.1.1 to V2.1.3 | **Done** | `tests/unit/test_crypto.py`. The Vault provider ran only against a simulated Vault |
| V2.1.4 | **Done** | `test_raw_database_holds_no_genetic_or_identity_details`, and on the real stack `scripts/smoke_stack.py`: 120 binary values decoded, no gene names or IDs |
| V2.2.1 | **Done** | `test_same_seed_gives_identical_output`, and two real runs with matching hashes |
| V2.2.2 | **Done** | All 13 scenarios appear in the Abu Dhabi personas: `test_synthetic.py` and `summary.json` |
| V2.2.3 | Partly | IDs use an all-zero block, files and bundles are labelled, and a test checks this. Reviewer missing |
| V2.2.4 | **Done** | `test_observed_carrier_rates_are_close_to_the_table`, within four standard errors |
| V2.2.5 | Partly | Every gene marked placeholder, and listed conditions covered. Reviewer missing |
| V2.2.6 | Partly | Every input listed in `data_sources.md`. LOINC, HL7 terminology and gene symbol terms **not confirmed**: a person must read them |
| V2.2.7 | **Done** | `test_personas_exist_for_both_packs` |
| V2.3.1 to V2.3.4, V2.3.6, V2.3.7 | **Done** | `tests/api/test_ingestion.py`, `tests/api/test_results.py`, and the smoke script |
| V2.3.5 | Partly | Demo attestation is recorded and readable as trusted. The link to matching comes with V3.3.1 |
| V2.4.1 to V2.4.11, V2.4.13, V2.4.15 | **Done** | `tests/unit/test_risk_engine.py`, `test_engine_boundaries.py`, coverage report. Hand-worked answers are the author's own, and `risk_rules_review.md` asks for a second person |
| V2.4.12 | Open | Needs a clinician. A stated limitation until then |
| V2.4.14 | Partly | No empiric figure is shown at all, which is stricter than the check asks. Clinician wording still needed |
| V2.5.1 | **Done, differently** | Personal routes take no person ID, so there's nothing to tamper with: `tests/api/test_bola.py`. Shared data gets its own check in V3.2.1 |
| V2.5.2 | **Done** | `tests/unit/test_visuals.py` |
| V2.5.3 | Partly | Unit tests pass. Screenshot waits on Stitch screens |
| V2.5.4, V2.5.6 | Open | Need the screens and a non-technical reader |
| V2.5.5 | **Done** | `test_reading_results_creates_an_audit_row` |
| V2.6.1 | Partly | Options, languages, ID format, services and genes change with the pack. Crisis contacts are still empty in both packs, on purpose, until verified (V1.2.4) |
| V2.6.2 to V2.6.5, V2.6.7, V2.6.8 | **Done** | `tests/unit/test_country_packs.py`, `tests/api/test_ingestion.py` |
| V2.6.6 | Partly | The pack states "none" and nothing substitutes for it. Showing that on screen waits on Stitch |

## Issues to sub-phases and checks

| Issue | Sub-phases | Verified by |
|---|---|---|
| S1 | 1.1 | V1.1.3 |
| S2 | 1.1, 6.4 | V1.1.2, V6.4.5 |
| S3 | 1.1 | V1.1.4 |
| S4 | 1.2 | V1.2.3 |
| S5 | 1.2, 4.4 | V1.2.2, V4.4.1 |
| S6 | 1.2 | V1.2.8 |
| S7 | 5.4, 6.2 | V5.4.7, V6.2.3, V6.2.4 |
| S8 | 1.6, 3.3, 6.4, 6.5 | V1.6.2, V3.3.8, V6.4.2, V6.5.3 |
| S9 | 2.6, 6.4 | V2.6.4, V6.4.6 |
| S10 | 2.2, 6.4 | V2.2.6, V6.4.7 |
| S11 | 1.1, 6.4, 6.6 | V1.1.6, V6.4.8, V6.4.9, V6.6.5 |
| C1 | 2.3, 3.3 | V2.3.5, V3.3.1 |
| C2 | 3.3 | V3.3.2 |
| C3 | 2.4 | V2.4.1, V2.4.13 |
| C4 | 2.4 | V2.4.2, V2.4.3, V2.4.4 |
| C5 | 4.2 | V4.2.1, V4.2.2, V4.2.3 |
| C6 | 4.3 | V4.3.1, V4.3.2 |
| C7 | 2.4, 3.3 | V2.4.9, V3.3.4 |
| C8 | 2.3, 4.5 | V2.3.6, V4.5.6 |
| C9 | 4.5 | V4.5.2 |
| C10 | 1.2, 4.3 | V1.2.4, V4.3.4, V4.3.12 |
| H1 | 2.4 | V2.4.6 |
| H2 | 2.4 | V2.4.5 |
| H3 | 2.4 | V2.4.8 |
| H4 | 2.4 | V2.4.14 |
| H5 | 2.4, 2.5 | V2.4.15, V2.5.3 |
| H6 | 3.5 | V3.5.3, V3.5.4 |
| H7 | 2.3, 3.1, 3.2 | V3.1.5, V2.3.3, V3.2.6 |
| H8 | 3.2, 3.3 | V3.2.4, V3.2.5, V3.2.7, V3.2.8, V3.3.6 |
| H9 | 4.3 | V4.3.5, V4.3.11 |
| H10 | 5.1 | V5.1.1, V5.1.3, V5.1.5, V5.1.8 |
| H11 | 1.5, 3.2, 5.4 | V1.5.4, V3.2.2, V5.4.1, V5.4.6 |
| H12 | 4.2, 6.1 | V4.2.4, V6.1.3 |
| H13 | 1.6, 4.2 | V1.6.2, V4.2.5 |
| H14 | 2.3, 3.2, 3.4, 3.5, 4.4, 4.5, 5.1, 5.2, 6.4 | V2.3.7, V3.2.5, V3.4.1, V3.5.2, V4.4.4, V4.5.5, V5.1.9, V5.2.1, V5.2.3, V5.2.6, V6.4.3 |
| H15 | 1.3 | V1.3.1, V1.3.2, V1.3.5 |
| H16 | 1.3 | V1.3.4 |
| H17 | 3.4 | V3.4.1 |
| H18 | 1.5, 2.1 | V1.5.5, V2.1.4 |
| H19 | 1.2 | V1.2.9 |
| M1 | 4.3 | V4.3.13 |
| M2 | 1.5, 5.5 | V1.5.6, V5.5.8 |
| M3 | 2.2 | V2.2.5 |
| M4 | 4.2, 4.3 | V4.2.7, V4.3.8 |
| M5 | 1.6 | V1.6.1 |
| M6 | Fixed | README converted to UTF-8, `.gitignore` added |
| M7 | 4.1 | V4.1.5 |
| M8 | 2.3 | V2.3.3, V2.3.4 |
| M9 | 5.4 | V5.4.4 |
| M10 | 1.5 | V1.5.7 |
| M11 | 4.1 | V4.1.7 |
| M12 | 1.4 | V1.4.5, V1.4.6 |
| M13 | 1.6 | V1.6.5 |
| G1 | 2.6, 4.2 | V2.6.1, V4.2.8 |
| G2 | 2.6, 3.5 | V2.6.5, V3.5.4 |
| G3 | 2.6 | V2.6.2 |
| G4 | 2.6 | V2.6.7 |
| G5 | 2.6 | V2.6.5 |
| G6 | 2.6 | V2.6.8 |
| G7 | 2.6 | V2.6.6 |
| G8 | 5.5 | V5.5.9 |
| G9 | 4.1 | V4.1.8 |
| G10 | 6.4 | V6.4.10 |

## Judging criteria to evidence

| Criterion | Sub-phases | Key checks |
|---|---|---|
| Health impact and clinical relevance | 1.2, 2.4, 4.1, 6.2 | V2.4.12, V4.1.4, V6.2.3 |
| Technical depth and architecture | 2.4, 2.6, 3.3, 4.3 | V2.4.10, V2.6.1, V3.3.4 |
| Working solution and demonstration quality | 2.5, 5.5, 6.5 | V5.5.1, V5.5.5, V6.5.1 |
| Responsible AI, safety and data governance | 3.5, 4.2, 6.1, 6.3 | V3.5.3, V4.2.1, V6.1.3, V6.3.2 |
| Scalability and deployment readiness | 1.3, 2.6, 6.3 | V1.3.1, V2.6.1, V6.3.4 |
| Commercial viability and path to pilot | 6.4 | V6.4.4, V6.4.5 |
