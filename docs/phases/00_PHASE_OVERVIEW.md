# Phase Overview: 6 Phases of Development

This is the master plan. Each phase has its own file with sub-phases, goals, objectives and cross-verification checks.

**Status on 5 Nov 2026:** specification and skeleton only. No application code yet. The team is registered.
**Scope:** global by design, with Abu Dhabi as the first reference pack. See [docs/07](../07_Global_Design_and_Country_Packs.md).
**Dates:** re-baselined on 5 Nov 2026 from the [official requirements](../submission/competition_requirements.md), with 15 days left. Phase 3 is the tightest at 2 days, so cut its T2 items first.
**Cross-verification:** every objective, check, issue and target is audited in [CROSS_VERIFICATION.md](CROSS_VERIFICATION.md).
**Live sessions:** Thursdays 5, 12 and 19 Nov, also recorded. Use them to ask open questions.

## Timeline

| Phase | File | Dates | Outcome |
|---|---|---|---|
| **1** | [Foundation, decisions, compliance](PHASE_1_Foundation.md) | 5–6 Nov | Registered, scope locked, stack running, audit chain working |
| **2** | [Genomic data and risk engine](PHASE_2_Genomic_Data_and_Risk_Engine.md) | 7–9 Nov | Correct risk numbers on screen from synthetic results |
| **3** | [Privacy fabric and family sharing](PHASE_3_Privacy_and_Family_Sharing.md) | 10–11 Nov | Consent, couple match and invitations proven private |
| **4** | [AI explanation and human escalation](PHASE_4_AI_Explanation_and_Escalation.md) | 12–14 Nov | Safe chat in English, Arabic and Hindi, with cases reaching a counsellor |
| **5** | [Care pathway, measurement, integration](PHASE_5_Care_Pathway_Measurement_Integration.md) | 15–17 Nov | Full demo journey works, with metrics |
| **6** | [Evaluation, hardening, submission](PHASE_6_Evaluation_and_Submission.md) | 18–20 Nov | **Submitted on 19 Nov**, with 20 Nov as buffer |

**Hard external dates:** team registered (done) · prototype due **20 Nov** · evaluation 20–30 Nov · GITEX 7–11 Dec.

```
          Nov 5  6 | 7  8  9 |10 11 |12 13 14 |15 16 17 |18 19 20
Phase 1     ████   |         |      |         |         |
Phase 2            | ███████ |      |         |         |
Phase 3            |         | ████ |         |         |
Phase 4            |         |      | ███████ |         |
Phase 5            |         |      |         | ███████ |
Phase 6            |         |      |         |         | ███████
Frontend    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
Live        Thu 5                    Thu 12                Thu 19
Milestones                                                 ▲ Submit 19 Nov
```

## Working rules for every phase

1. **Gate, then move on.** A phase ends when its exit gate passes, not when its dates end. If a gate slips, cut scope using the tiers below instead of skipping checks.
2. **Cross-verify with evidence.** Each check has an ID (such as `V2.4.3`). Tick it only with evidence: a test name, command output, screenshot or reviewer's name. Someone other than the author verifies wherever the team size allows.
3. **Log it.** Each sub-phase finished gets a `brain.md` entry. See the mandate at the top of [brain.md](../../brain.md).
4. **Issues are requirements.** Each sub-phase lists the issue IDs it must close, from the [review](../04_Project_Review_Issues_and_Improvements.md).
5. **No code until asked.** Files stay stubs until implementation is explicitly requested.

## Scope tiers

These are recommendations, pending your confirmation of team size.

| Tier | Meaning | Items |
|---|---|---|
| **T1 Must work for real** | The demo fails without it | Country pack framework, the Abu Dhabi reference pack and a small India pack, content in English, Arabic and Hindi at the Simple level, synthetic results, risk engine, risk visuals, templates in all three languages, chat with validators and boundary, couple match, consent and revoke, access log, triage queue with assignment, pathway to referral, teach-back, outcomes and equity dashboard, audit chain |
| **T2 Build if on schedule** | Strong additions | Standard and Detailed reading levels, LLM generation (templates are the fallback), invitations, options and values, co-pilot summary, break-glass, booking, centre finder, right-not-to-know flow, Story Mode |
| **T3 Labelled mock or roadmap** | Say so openly | UAE PASS, Malaffi, lab mTLS and JWS, real SMS, Vault, cross-institution PSI, differential privacy, voice, content-governance UI, Jais self-hosting, HAPI FHIR server, mobile and Arabic variants of T2 screens |

**If the team is 1–2 people:** also consider a simple local authorisation table and a mock OIDC token behind the same interfaces as OpenFGA and Keycloak. The architecture story survives, and the time goes into safety work.

## Critical path

Later work can't start or be trusted until these are done:

1. Rules and FAQ read (1.1). Registration is done
2. Options and legal baseline agreed (1.2)
3. Risk engine rules correct (2.4), since all numbers depend on them
4. Couple match returning correct, private results (3.3)
5. Validators (4.2) before any LLM output is shown
6. Triage assignment (4.5) before the escalation demo
7. Real volunteers booked by 12 Nov for testing around 18 Nov (6.2)
8. Full requirements found and recorded (1.1), since they override this plan

## Judging criteria to phases

| Criterion | Mainly proved in | Evidence you'll have |
|---|---|---|
| Health impact and clinical relevance | 1.2, 2.4, 4.1, 6.2 | Clinician sign-off, real comprehension test |
| Technical depth and architecture | 2, 3, 4 | Architecture doc, test suites |
| Working solution and demonstration quality | 2.5, 5.5, 6.5 | End-to-end demo, video |
| Responsible AI, safety and data governance | 3, 4.2, 6.1, 6.3 | Safety report, privacy tests, threat model |
| Scalability and deployment readiness | 1.3, 2.6, 6.3, 6.4 | One-command stack, country pack swap, deployment doc |
| Commercial viability and path to pilot | 1.1, 6.4 | Commercial and pilot plan |

## Requirements to phases

| Requirement | Phases | Traceability |
|---|---|---|
| R1 Risk explanation | 2, 4 | See [traceability matrix](../06_Traceability_Matrix.md) |
| R2 Values-sensitive choices | 1.2, 4.4 | |
| R3 Qualified human counselling | 4.3, 4.5 | |
| R4 Privacy-preserving family workflows | 2.1, 3 | |
| R5 Safe linkage to services | 5.1, 5.2 | |
| R6 Measurable comprehension and access | 5.3, 5.4, 6.1, 6.2 | |

## How each sub-phase is written

Each sub-phase states its **goal** (the single result), **objectives** (what must be true), **work**, **files**, **issues to close**, and **cross-verification** (how someone else confirms it). Copy this structure for anything added later.
