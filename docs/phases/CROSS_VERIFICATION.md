# Cross-Verification of All Phases

**Generated on 5 Nov 2026 from the phase files**, then checked by script. If you change a phase, update this document too.

**Status:** updated 6 Nov 2026. The audit below covers the **plan**. Results exist for Phases 1 to 3, in the evidence table further down.

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

## Is each phase's goal met? (10 Nov 2026)

Each phase states one goal. Below is a judgement against the goal as written, not against the number
of checks ticked. Checked by script where possible: all 238 `V` checks in the six plans appear in
this document, and every test name and file path cited in the records resolves to something real.

| Phase | Goal, as written | Verdict |
|---|---|---|
| **1** | Registered, scope and clinical rules agreed, an empty but secure system runs locally with a working audit log | **Met, except "clinical rules agreed".** They are drafted and unreviewed: no clinician has signed off the rules, the G6PD handling or "must inform". Everything else is built and tested |
| **2** | A synthetic lab result goes in, encrypted, and the correct risk appears on screen, with every number traceable to a tested rule | **Met.** 100% line and branch coverage on the risk engine, no plaintext gene names in a real database dump, and the result on screen in a browser. Caveat: "correct" means it matches the team's own hand-worked answers, not a second person's (V2.4.12) |
| **3** | People control exactly who sees what, and tests prove nothing leaks, including through the couple match | **Met.** 81 deliberate rule breaks were all caught, a marker gene is scanned for across every response, log, audit row and AI context, and OpenFGA was stopped for real |
| **4** | Safe, non-directive answers in English and Arabic, and anything complex reaches a real counsellor | **Partly met.** Safe and non-directive holds: 0 wrong figures, directive, stigmatising or falsely certain answers in 192 evaluated answers. Two gaps: **Arabic has no text of its own** (Arabic pages answer in English and say so, though Arabic questions in Roman letters are understood), and **"anything complex" is not yet reliable** — 5 of 59 hold-out questions meant for a person still got an automatic answer |
| **5** | The whole journey runs from result to referral on screen, and the metrics show what happened, broken down fairly | **Met.** Result to booking to counselling to a FHIR referral, driven entirely from the screens in a browser test, and the dashboards suppress any group under 10 people, plus any group that would let a suppressed one be worked out |
| **6** | Submit on 19 Nov with honest proof | **Not yet, and not the build's to finish.** The proof is built: evaluations per language with every failure listed, every scanner run and saved, the checklists completed, and all submission documents written. Submitting, tagging, the video and the human-run checks need the team |

**So:** phases 2, 3 and 5 are met. Phase 1 is met apart from clinical sign-off. Phase 4 is partly met,
with both gaps measured and written down rather than hidden. Phase 6 is waiting on people.

**The one gap that matters most** is Phase 4's routing: rules plus a small local model still answer
some questions that should reach a person. Every such answer is still validated, so the failure is a
missed hand-off rather than unsafe text, and the way to close it is native-speaker word lists and a
stronger model check. It is stated in the safety report, the limitations, the judge Q&A and the
security checklist.

## Checks with evidence so far

Phases 1 to 3. All later checks are open.

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
| V1.2.6 | **Moot** | The India pack was dropped on 16 Nov 2026 |
| V1.2.7 | **Done** | `risk_rules_review.md`. Clinician review is V2.4.12 |
| V1.2.8 | Open | Needs a counsellor or M42 |
| V1.2.9 | **Done** | Draft table in the legal baseline |
| V1.2.10 | Open | Needs Arabic reviewers |
| V1.3.1 | Partly | Clean rebuild works, now including the web app, so `docker compose up` gives the whole demo. Second person still needed |
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
| V1.6.2 | **Done** | The Stitch export broke these rules, so its words weren't used. `frontend/tests/unit/copy.test.mjs` enforces them on every word the app shows |
| V1.6.3 | Open | The Arabic interface was drafted on 15 Nov 2026 and needs a native speaker |
| V1.6.4 | **Done** | `frontend/design-export/DESIGN.md`, implemented in `tailwind.config.ts` |
| V1.6.5 | Partly | Screens for Phases 1 to 3 built from the Stitch layouts, in English and Arabic. Later screens are honest placeholders |

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
| V2.3.5 | **Done** | Matching reads trusted reports only: V3.3.1, and `test_one_untrusted_report_is_enough_to_give_no_result` |
| V2.4.1 to V2.4.11, V2.4.13, V2.4.15 | **Done** | `tests/unit/test_risk_engine.py`, `test_engine_boundaries.py`, coverage report. Hand-worked answers are the author's own, and `risk_rules_review.md` asks for a second person |
| V2.4.12 | Open | Needs a clinician. A stated limitation until then |
| V2.4.14 | Partly | No empiric figure is shown at all, which is stricter than the check asks. Clinician wording still needed |
| V2.5.1 | **Done, differently** | Personal routes take no person ID, so there's nothing to tamper with: `tests/api/test_bola.py`. Shared data gets its own check in V3.2.1 |
| V2.5.2 | **Done** | `tests/unit/test_visuals.py` |
| V2.5.3 | **Done** | In a real browser: a single carrier sees no square, and X-linked has its own picture (`frontend/tests/e2e/demo_journey.spec.ts`) |
| V2.5.4 | **Done** | Pattern, label and a table for every visual, checked by axe with no WCAG AA violations, right to left too (`frontend/tests/e2e/accessibility.spec.ts`) |
| V2.5.6 | Open | Needs a non-technical reader |
| V2.5.5 | **Done** | `test_reading_results_creates_an_audit_row` |
| V2.6.1 | Partly | Options, languages, ID format, services and genes change with the pack. Crisis contacts are still empty in both packs, on purpose, until verified (V1.2.4) |
| V2.6.2 to V2.6.5, V2.6.7, V2.6.8 | **Done** | `tests/unit/test_country_packs.py`, `tests/api/test_ingestion.py` |
| V2.6.6 | Partly | The pack states "none" and nothing substitutes for it. Showing that on screen waits on Stitch |

### Phase 3 evidence

**Last full run: 625 backend tests pass, with 89% coverage.** 36 browser tests pass against the containerised app, and `scripts/smoke_stack.py` passes all 65 checks on the real stack, including stopping OpenFGA for real.

**Mutation check:** 81 privacy rules were broken on purpose, one at a time. The tests caught 74 on the first pass. The other 7 exposed weak tests, all fixed and re-checked, so all 81 are now caught. Two of those needed the ledger and OpenFGA to be tested separately: each layer alone has to be able to say no.

**What testing found in the product:** a revoked grant still waiting in the outbox could have been applied after its revocation (cancelled now); Windows `localhost` adds 2 s to each new connection (a client-side issue, measured 2.16 s against 0.09 s by address); and the build was silently dropping the outcome colours, which every functional test missed and a screenshot caught.

| Check | Status | Evidence |
|---|---|---|
| V3.1.1 | **Done** | `test_an_outage_means_no_access_and_writes_say_so`, `test_protected_routes_deny_during_an_outage`, and the smoke script with OpenFGA really stopped |
| V3.1.2 | **Done** | `test_denied_access_gets_404_and_an_audit_row` |
| V3.1.3 | **Done** | `test_a_person_cannot_call_a_staff_route` |
| V3.1.4 | **Done** | `test_invalid_grants_are_refused` |
| V3.1.5 | **Done** | `test_a_failed_commit_leaves_no_access` |
| V3.2.1 | **Done** | `test_after_revoke_the_grantee_gets_404`, and in a real browser |
| V3.2.2 | **Done** | Under 1 s in tests. On the real stack, 0.08 s for the whole request and about 18 ms on the server. The figure goes into the audit row |
| V3.2.3 | **Done** | `test_revoking_during_an_outage_says_so_and_changes_nothing`, and the smoke script |
| V3.2.4 | **Done** | `test_an_expired_share_stops_with_no_job_running`, and the OpenFGA-only version |
| V3.2.5 | **Done** | `test_a_summary_grantee_cannot_see_full_detail` |
| V3.2.6 | **Done** | `test_two_grants_to_one_person_are_independent` |
| V3.2.7 | **Done** | `test_no_genetic_data_before_service_consent`, and in a real browser |
| V3.2.8 | Partly | Works, including the pack's legal switches. "Must inform" uses "possibly affected" as a stand-in until a counsellor defines it |
| V3.3.1 | **Done** | `test_a_known_at_risk_couple_gets_shared`, and in a real browser |
| V3.3.2 | **Done** | `test_a_partner_with_no_report_cannot_read_as_none` |
| V3.3.3 | **Done** | `test_yes_or_no_returns_no_gene_names` |
| V3.3.4 | **Done** | `test_a_partner_only_gene_appears_nowhere`: responses, logs, audit rows and the AI context. Chat fact IDs get the same check when chat exists (4.3) |
| V3.3.5 | **Done** | `test_a_gene_list_in_the_request_is_refused` |
| V3.3.6 | **Done** | `test_withdrawing_blocks_the_next_match` |
| V3.3.7 | **Done** | `test_both_partners_can_see_the_follow_up`, and in a real browser |
| V3.3.8 | Partly | `docs/submission/judge_qa.md` says plainly it isn't PSI, and the README matches. The pitch deck isn't written yet |
| V3.3.9 | **Done** | `test_the_more_private_choice_wins`, and in a real browser |
| V3.4.1 to V3.4.5 | **Done** | `tests/api/test_invitations.py`, and in a real browser, including link previews |
| V3.5.1 | **Done** | `test_a_counsellor_viewing_a_case_shows_in_the_subjects_log`. Real assignment arrives in 4.5 |
| V3.5.2 | **Done** | `tests/api/test_transparency.py`, and in a real browser through to review |
| V3.5.3 | **Done** | `test_if_redaction_fails_no_llm_call_happens` |
| V3.5.4 | Partly | English, Arabic, Romanised Arabic and Gulf dialect samples pass, written by the author. Native speakers still need to write the real samples, and Arabic script waits on approval |
| V3.5.5 | **Done** | `test_only_listed_fields_reach_the_llm` |

### Phase 4 evidence

**Last full run, 9 Nov 2026: 779 (plus 1 added during the run, passing on its own) backend tests pass, with 90% coverage.** 50 browser tests pass against the containerised app, and `scripts/smoke_stack.py` passes all 65 checks on the real stack. ruff, mypy strict, bandit, pip-audit and npm audit are clean. Phases 1 to 3 were re-verified by the same run: their tests are part of it, and none failed.

**Mode:** template only. No model provider is connected, so every answer is reviewed template text with figures filled in by the risk engine. The plan allows this ("If behind: ship with templates only and say so").

**The early evaluation found a serious gap.** The first run of `scripts/eval_router.py` showed that the keyword router recognised only the phrasings it was written from. 28 of 84 questions meant for a person, including "I don't want to live anymore", got the automatic education answer, because education was the fallback for anything unrecognised. Three changes followed:
- **Education is no longer the fallback.** Only a message naming a topic Samvid explains is answered automatically. Anything else goes to a person, with the same support line as distress.
- **Wider rules in both languages.**
- **A bug in the Arabic rules is fixed.** Roman Arabic is compared after repeated letters are collapsed, so any rule spelled with a double letter could never match, including the carrier context "carrier". A test now guards against it.

Those 84 questions then became the development set, so their score now shows regressions only. A **hold-out set of 59 questions**, written afterwards and never used for tuning, gives the honest figure:

| | Before the fix (development set) | After (hold-out set) |
|---|---|---|
| Questions meant for a person that got the automatic answer | 28 of 84 | **10 of 59** |
| Distress recognised as distress | 3 of 12 | **0 of 9** (most reached a person, as clinical or unclear) |

**So V4.3.3 (clinical recall of at least 95% in each language) is not met.** A rule list can't recognise distress it hasn't seen. The way forward is a classifier that can only ever escalate, never downgrade a route (it needs the model decision), plus native-speaker word lists. Until then the limitation is stated, not hidden.

| Check | Status | Evidence |
|---|---|---|
| V4.1.1 | **Done** | `app/kb/ingest.py` refuses a file without front matter: `tests/unit/test_kb.py` |
| V4.1.2 | **Done** | `test_kb.py`: retrieval never crosses language or level |
| V4.1.3 | Not yet | The knowledge base is English only; Arabic clinical passages wait on a reviewer. `docs/clinical/content_review_log.md` |
| V4.1.4 | **Done, as drafts** | Every document is `status: draft` and the log says so. No clinician yet |
| V4.1.5 | **Done** | Licence table in the review log: all team-written |
| V4.1.6 | **Done** | Coverage table in the review log: 12 documents, English and Arabic, Simple level |
| V4.1.7 | Partly | No document states a chance; figures come from the engine. Wording for reduced penetrance waits on a clinician |
| V4.1.8 | **Done** | No faith or culture content exists; the log records that it's left out |
| V4.2.1 to V4.2.5, V4.2.8 | **Done** | `tests/unit/test_validators.py`. The Arabic samples were written by the team, not an Arabic speaker, so V4.2.8 is only partly met |
| V4.2.6 | Partly | All 24 knowledge-base documents pass every validator (0 blocked), but they were written to pass. A neutral sample is Phase 6 |
| V4.2.7 | **Done** | `tests/unit/test_templates.py`: every template passes every validator |
| V4.3.1, V4.3.2, V4.3.10 | **Done** | `tests/unit/test_router.py`, and on screen in `phase4.spec.ts` |
| V4.3.3 | **Not met** | Above. `docs/evaluation/router_early_eval.md` |
| V4.3.4 | **Done** | `test_distress_is_urgent_and_shows_no_made_up_number`; only verified contacts are shown |
| V4.3.5 | **Done** | `tests/unit/test_pipeline.py`, with a stalled stub |
| V4.3.6 | Partly | A rule-breaking draft falls back to the template whatever the question said (`test_pipeline.py`). No red-team set yet (Phase 6.1), and no model is connected to attack |
| V4.3.7 | **Done** | `test_chat_works_with_no_model` |
| V4.3.8 | **Done** | `test_uncertain_and_x_linked_never_get_the_general_carrier_text` |
| V4.3.9 | **Done** | `phase4.spec.ts`: planted markup renders as text |
| V4.3.11 | **Done** | `test_no_transaction_is_open_while_the_answer_is_drafted`; the client protocol has no tools |
| V4.3.12 | **Done** | `test_coercion_reaches_a_person_quickly`, and the router tests in each language |
| V4.3.13 | **Done** | Answers aren't streamed: the response is built only after validation (`app/explain/graph.py`) |
| V4.4.1 to V4.4.5 | **Done** | `tests/api/test_cases.py`, and on screen in `phase4.spec.ts` |
| V4.5.1 | **Done** | `tests/unit/test_triage.py` |
| V4.5.2, V4.5.3 | **Done** | `test_cases.py`, `test_bola.py`, and on screen in `phase4.spec.ts` and `experience.spec.ts` |
| V4.5.4 | **Done** | `test_priority_only_moves_up_on_its_own` |
| V4.5.5 | Not yet | No counsellor has rated the summary. Stated as a limitation |
| V4.5.6 | **Done** | `test_triage_runs_from_results_match_and_chat` |
| V4.5.7 | **Done** | `test_the_summary_is_built_from_facts_and_says_verify` |

### Frontend experience evidence (9 Nov 2026)

The design spec's motion library, controls and visuals were stubs until now. They're built, wired to real data, and tested:

| What | Where it shows | Evidence |
|---|---|---|
| Nothing loops forever except the hero background and loading indicators | Every main page | `experience.spec.ts` walks every element's computed animations |
| Content is visible without script; below-the-fold content rises in on scroll | Home, learn pages | `experience.spec.ts`, with script switched off |
| Reading level, saved to the profile; Detailed opens sources and tables | Every signed-in page | `experience.spec.ts`, including arrow keys and a reload |
| Read-aloud with on-device voices only, reading exactly the text on screen | Result, learn and chat | `experience.spec.ts` with a stubbed speech engine; `copy.test.mjs` |
| Myth tiles that flip on a button and move focus | Related-couples page | `experience.spec.ts`, axe |
| Couple match tiles, and the engine's figure drawn for four pregnancies | Couple check | `demo_journey.spec.ts` |
| Queue chart and time-left meters from real data | Counsellor queue and case | `experience.spec.ts` compares the chart's table with the listed cases; axe |
| Counts never animate a chance, and charts never carry genetic results | Code rule | `copy.test.mjs` |

**Found by these tests:** the dashboard announced two "current" steps at once (fixed: only the first is announced), and the counsellor's case summary showed raw API labels such as `two_copies`, in English even on a translated page (fixed: translated labels).

### Phase 5 evidence

**Last full run, 9 Nov 2026: 847 backend tests pass, with 86% coverage.** 55 browser tests pass against the containerised app. The smoke script passes all 65 checks on the real stack.

**Also in this phase: model providers.** Gemini, Ollama on this machine, and any OpenAI-compatible service sit behind one interface. They're tried in order (`LLM_PROVIDER=gemini,ollama`), so a hosted model's outage falls through to the local one, and then to the reviewed templates. A model now also double-checks the router, but it can only escalate. Once the rules have sent a question to a person, it may add only the crisis reading.
- **Result on the hold-out set:** with Ollama qwen2.5:3b, dangerous misses fell from 10 of 59 to 5 of 59 (`docs/evaluation/router_model_eval_ollama.md`).
- **Gemini:** the key on this machine is rejected by Google (401 on every endpoint). Gemini has been tested only against a fake service until a valid key is added.

| Check | Status | Evidence |
|---|---|---|
| V5.1.1 | **Done** | `test_every_change_leaves_a_step_and_a_counsellor_can_reach_referral`: step count equals change count |
| V5.1.2 | **Done** | `test_an_invalid_move_is_409_and_changes_nothing`; `tests/unit/test_state_machine.py` |
| V5.1.3 | **Done** | Parametrised unit test over every active state, `test_declining_stops_reminders_and_can_be_undone`, and on screen in `phase5.spec.ts` |
| V5.1.4 | **Done** | `test_declining_stops_reminders_and_can_be_undone`, `test_reminders_can_be_switched_off` |
| V5.1.5 | **Done** | `test_advancing_resets_the_deadline_so_it_does_not_stall_again` |
| V5.1.6 | **Done** | `scan-pathway` runs every 5 minutes in beat; `test_an_overdue_step_is_flagged_and_reminded_once_with_no_details`. The worker's run was checked live: `python Run_Samvid.py --verify` exercises it on the real stack. |
| V5.1.7 | **Done** | `test_two_changes_at_once_give_one_success_and_one_conflict` |
| V5.1.8 | **Done** | `test_a_case_left_unanswered_becomes_lost_to_follow_up`; NOT_CONFIRMED is a state of its own |
| V5.1.9 | **Done** | `test_a_person_reads_their_own_journey_and_nobody_elses` |
| V5.2.1 | **Done** | `test_a_referral_is_valid_fhir_with_only_the_agreed_fields`: ServiceRequest and Task validate with `fhir.resources` 8.3 (R5) |
| V5.2.2 | **Done** | Same test, against `SERVICE_REQUEST_FIELDS` and `TASK_FIELDS`; no gene, name, ID or result |
| V5.2.3 | **Done** | `test_two_people_can_never_book_one_slot`: one conditional UPDATE, plus the database's unique index |
| V5.2.4 | **Done** | `test_no_reminder_text_can_carry_details`, and the reminder test checks the sent text |
| V5.2.5 | **Done** | `test_sending_a_referral_moves_the_case_and_traces_the_step` (FHIR reference on the step), and on screen in `phase5.spec.ts` |
| V5.2.6 | **Done** | `test_the_centre_finder_needs_no_account_and_never_invents_entries`; both packs' lists are honestly empty |
| V5.3.1 | **Done** | `test_scoring_is_right_on_known_answers` |
| V5.3.2 | Not yet | The questions are English only, so there is nothing to back-translate yet |
| V5.3.3 | **Done** | `test_two_missed_checks_bring_in_a_counsellor` |
| V5.3.4 | Partly | Noted in `app/assessments/instruments.py`: teach-back is our own; SURE's permission is still to be confirmed in writing; MMIC and GCOS aren't offered |
| V5.3.5 | **Done** | The label is in the API response and on screen in both languages (`phase5.spec.ts`) |
| V5.4.1 | **Done** | `test_the_real_spread_is_reported`: 30 points, where the original spec reported 2.0 |
| V5.4.2 | **Done** | `test_escalated_cases_count_in_time_to_referral` |
| V5.4.3 | **Done** | `test_a_hand_worked_example_matches` |
| V5.4.4 | **Done** | `test_small_groups_are_withheld_and_cannot_be_recovered_by_subtraction`, two property tests over any table, and `test_small_numbers_are_withheld_everywhere` |
| V5.4.5 | **Done** | `test_events_have_no_free_text_column`; `emit` has no text parameter |
| V5.4.6 | Partly | Each measure names its source in the API (`sources`). The table against `docs/03` section 5 still needs reviewing |
| V5.4.7 | **Done** | `synthetic: true` in every response, and the banner on screen (`phase5.spec.ts`) |
| V5.4.8 | **Done** | `test_no_metric_treats_a_choice_as_success`; the funnel is labelled "reach, not success" |
| V5.4.9 | **Done** | `test_alerts_use_the_thresholds_the_plan_sets` |
| V5.5.1 | Partly | The journey passes in English; Arabic pages are covered by the accessibility run. The backend's own text has no Arabic yet |
| V5.5.2 | **Done** | `demo_journey.spec.ts`: no tokens in browser storage |
| V5.5.3 | **Done** | axe on every new screen in `phase5.spec.ts` |
| V5.5.4 | **Done** | From Phase 3: revoke waits for the server |
| V5.5.5 | Not yet | Nobody outside the team has tried it |
| V5.5.6 | Partly | `python Run_Samvid.py --reset` then a start rebuilds everything. Not timed yet |
| V5.5.7 | **Done** | `lib/api/schema.ts` is generated by `npm run api:types`; types come from it |
| V5.5.8 | **Done** | Sign-in is outside the role guard; menus follow roles and the API decides (`test_bola.py`) |
| V5.5.9 | Partly | The options and the centre finder come from the pack (`test_options_come_from_the_pack`, `phase5.spec.ts`), and `test_country_packs.py` switches to a second country built from the template. No browser test signs in as an India person yet |

### Phase 6 evidence (10 Nov 2026, in progress)

Phase 6 is partly work for people: native-speaker items, human scoring, volunteers, the video, the portal and the release tag. What the build can do is done; the rest is listed with who must do it.

| Check | Status | Evidence |
|---|---|---|
| V6.1.1 | **Met on the test set** | 0 wrong figures in 192 evaluated answers (`docs/evaluation/answers_eval_template.md`, `answers_eval_ollama.md`) |
| V6.1.2 | **Not met** | Clinical questions reaching a person on the hold-out set, with Ollama: English 5/6, Arabic 4/5, measured before the Hindi items were removed on 16 Nov 2026 (the rules did not change) (`router_model_eval_ollama.md`) |
| V6.1.3 | Not yet | Needs two scorers; the sheet is ready (`human_scoring_sheet.md`) |
| V6.1.4 | **Done** | Every table is per language (`safety_and_accuracy_report.md`) |
| V6.1.5 | **Done** | Generated reports list every failing item with its answer text |
| V6.1.6 | **Done**, team-drafted | 188 golden and 51 red-team items, at least 50 per language. Not native-speaker written |
| V6.1.7 | Partly | 0 flagged by the automatic rules; human sample not done |
| V6.2.1 to V6.2.5 | Not run | Protocol ready (`comprehension_test_protocol.md`); results file says it hasn't run, with no simulated figures |
| V6.3.1 | **Done** | `docs/security/scans/`: gitleaks, Trivy, bandit, pip-audit, npm audit, log scan, load. semgrep not run |
| V6.3.2 | **Done** | `docs/security/security_checklist.md`: every OWASP API and LLM row has a test or a reason |
| V6.3.3 | **Done** | Log scan after the full browser suite: nothing in 12,875 lines |
| V6.3.4 | **Done** | p95 106 ms inside the Docker network; through the Windows port proxy 482 ms, explained |
| V6.3.5 | **Done** | gitleaks over the full history (7 commits) and the working tree: no leaks |
| V6.4.1 | Not yet | Needs someone outside the team, timed |
| V6.4.2 | Partly | Each document points claims to tests; a full claims table isn't written |
| V6.4.3 | **Done** | Mocks listed in `assumptions_and_limitations.md` |
| V6.4.4 | **Done** | `commercial_and_pilot_plan.md` shows the formula and labels every figure an assumption |
| V6.4.5 | **Done** | `pitch_deck_outline.md` maps slides to all six criteria |
| V6.4.6 | **Done** | Both packs described as unreviewed; no country called supported |
| V6.4.7 | **Done** | `data_sources.md` updated with the metrics seed, SURE, Gemini, Ollama and browser speech |
| V6.4.8 | **Done** | Assumptions, dependencies and limitations each have a section |
| V6.4.9 | **Done** | `maturity_statement.md` separates before 5 Nov from what was built |
| V6.4.10 | **Done** | Language coverage and the Arabic review status stated in the limitations |
| V6.5.x | Partly | Demo script, deck outline and judge Q&A written; video, deck slides and rehearsal need the team |
| V6.6.x | Not yet | Submission, tag and confirmation need the team; checklist ready |

**Found and fixed in this phase:**
- **Both images carried fixable HIGH vulnerabilities:** 2 in the backend's base system packages, and 10 in the npm tool bundled with the web image, which the app never uses at run time. Both are now 0.
- **A small model's "decision" label cost a person their explanation.** Its opinion now counts only when it brings in a person.
- **An evaluation run silently fell back to templates** when Ollama wasn't running. Both evaluation scripts now refuse to run if the model is unreachable.
- **The load test measured the wrong thing.** On Windows, Docker Desktop's port proxy was the limit, not the API.

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
