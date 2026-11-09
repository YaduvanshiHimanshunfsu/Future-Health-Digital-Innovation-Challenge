# Phase 5: Care Pathway, Measurement and Frontend Integration

**Dates:** 15–17 Nov 2026 · **Build steps:** `backend.md` §9 steps 22–24 · **Requirements:** R5, R6

**Phase goal:** the whole journey runs from result to referral on screen, and the metrics show what happened, broken down fairly.

---

## 5.1 Care-pathway state machine

**Goal:** every step is traceable, and a person can always say no.

**Objectives**
- O5.1.1 One function handles all state changes.
- O5.1.2 Decline is possible from every active state.
- O5.1.3 Lost-to-follow-up and not-confirmed outcomes exist.
- O5.1.4 SLAs apply per step.

**Work** (step 22)
- State map, per-step SLA, stall detection in a worker that actually runs.
- At most one gentle, opt-out-able reminder.
- User-readable journey endpoint.

**Files:** `backend/app/pathway/*`, `backend/app/api/v1/pathway.py`, `backend/app/workers/*`, `frontend/app/[locale]/(app)/app/journey/`
**Issues to close:** **H10**, part of H14

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V5.1.1 | Every state change writes a step, including escalations | Test: step count equals change count |
| V5.1.2 | Invalid transition gives 409 | `tests/unit/test_state_machine.py` |
| V5.1.3 | A user can decline from each active state | Parametrised test (fails in the original spec) |
| V5.1.4 | After decline, no reminder is sent | Test |
| V5.1.5 | Advancing resets the SLA, so it doesn't instantly re-stall | Test |
| V5.1.6 | Worker runs in compose and flags an overdue case | Run log |
| V5.1.7 | Concurrent updates give one success and one 409 | Test |
| V5.1.8 | Lost-to-follow-up and not-confirmed outcomes are recorded | Test |
| V5.1.9 | A user can read their own journey, and others get 404 | API test |

---

## 5.2 Booking, referrals and FHIR mapping

**Goal:** a traceable hand-off from counselling to confirmatory testing and specialist services.

**Objectives**
- O5.2.1 Booking works on an internal calendar.
- O5.2.2 Referrals are valid FHIR, with the minimum data.
- O5.2.3 Centre finder supports access to screening.
- O5.2.4 Notifications contain no PHI.

**Work**
- Appointment model and booking endpoints.
- Referral builder and notes.
- `ServiceRequest` and `Task` mapping.
- Centre list from a public source, labelled by date.
- Mock notifier.

**Files:** `backend/app/booking/*`, `backend/app/pathway/fhir_mapper.py`, `backend/app/centres/*`, `backend/app/notifications/*`, `backend/app/api/v1/booking.py`, `backend/app/api/v1/referrals.py`, `backend/app/api/v1/centres.py`
**Issues to close:** part of H14

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V5.2.1 | Referral validates against `fhir.resources` | Unit test |
| V5.2.2 | Referral contains only the fields on an agreed list | Snapshot test |
| V5.2.3 | Double booking a slot is prevented | Test |
| V5.2.4 | No gene, condition or name in notifications | Template scan test |
| V5.2.5 | Result-to-referral timeline visible for a persona | Screenshot |
| V5.2.6 | The centre finder shows pack data with source and date, and works with no result on file | Test |

---

## 5.3 Assessments

**Goal:** measure understanding in a way that tests the explanation, not the person.

**Objectives**
- O5.3.1 Teach-back works pre and post, in both languages.
- O5.3.2 Adapted instruments are labelled honestly.
- O5.3.3 Failing twice offers help without judgement.

**Work** (step 23)
- Teach-back items reviewed by a counsellor, and by Arabic and Hindi speakers.
- Adapted MMIC and SURE, marked as "adapted, not validated in Arabic or Hindi" unless a validated version is found.
- Paired pre and post scoring.

**Files:** `backend/app/assessments/*`, `backend/app/api/v1/assessments.py`, `frontend/app/[locale]/(app)/app/check/`
**Issues to close:** S7 (prepares 6.2), H13 (confetti)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V5.3.1 | Scoring correct on known answers | Unit test |
| V5.3.2 | Arabic, Hindi and English items mean the same | Back-translation note |
| V5.3.3 | Two failures create a P3 case | Test |
| V5.3.4 | Licence or permission for each instrument is noted | Note in the file |
| V5.3.5 | Adapted instruments are labelled as adapted on screen and in reports | Screenshot |

---

## 5.4 Analytics, fairness and privacy metrics

**Goal:** every R6 metric has a real data source and is broken down correctly.

**Objectives**
- O5.4.1 Each dashboard number traces to events.
- O5.4.2 Fairness compares groups correctly, per dimension.
- O5.4.3 Small groups stay hidden.
- O5.4.4 Marriages cancelled is never a metric.

**Work** (step 23)
- Events with strata (language, literacy, age band, gender, region).
- Time-to-referral measured from `RESULT_RELEASED`.
- Paired comprehension change.
- Privacy metrics from security events and revocation timing.
- AI metrics from stored validator flags.
- Complementary suppression.

**Files:** `backend/app/analytics/*`, `backend/app/api/v1/analytics.py`, `frontend/app/[locale]/(admin)/`, `frontend/components/charts/*`
**Issues to close:** **H11**, M9, S7

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V5.4.1 | Fairness on the test rows reports the real 30 pp spread | Unit test (reports 2.0 in the original spec) |
| V5.4.2 | Escalated cases are included in time-to-referral | Test |
| V5.4.3 | A hand-calculated metric on a small dataset matches | Worked example in the test |
| V5.4.4 | Cells under 10 are hidden and can't be derived by subtraction | Test |
| V5.4.5 | Events have no free text | Schema test |
| V5.4.6 | Each KPI in `docs/03` §5 has a query or a stated gap | Table reviewed |
| V5.4.7 | The dashboard says "synthetic data" | Screenshot |
| V5.4.8 | No metric, schema field or dashboard treats cancelled marriages or any one choice as success | Schema and screen review |
| V5.4.9 | Gap alerts fire at the set thresholds: 5 pp between languages, 10 pp between literacy levels | Test |

---

## 5.5 Frontend integration and end-to-end journey

**Goal:** the complete demo story works without touching a database or a script.

**Objectives**
- O5.5.1 Typed client generated from the API.
- O5.5.2 T1 screens are wired up.
- O5.5.3 Tokens stay server-side.
- O5.5.4 Right-to-left and left-to-right languages work on the main path, using Arabic and Hindi.

**Work** (step 24)
- Generate the client, BFF proxy and login.
- Wire T1 screens, loading, empty and error states.
- Playwright journey.
- Seed script for the demo.

**Demo journey to pass**
1. Fatima signs in and reads her result in Arabic.
2. She asks what being a carrier means and gets an education answer.
3. She and her partner consent and run the match.
4. They see the shared finding and icon array.
5. "Should we do IVF?" gets a respectful refusal and a booking offer.
6. A counsellor claims the case and advances it to referral.
7. Fatima stops a share and sees it in her access log.
8. An admin sees the metrics, with an equity breakdown.
9. Switching to the India pack changes the language to Hindi, and changes the options and contacts, with no code change.

**Files:** `frontend/lib/*`, `frontend/app/api/proxy/`, `frontend/middleware.ts`, `frontend/tests/e2e/*`, `scripts/seed_demo.md`
**Issues to close:** M2, S8, G8

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V5.5.1 | The journey passes in English, Arabic and Hindi | Playwright report |
| V5.5.2 | No tokens in browser storage | Automated check |
| V5.5.3 | axe has no serious issues on T1 screens | Report |
| V5.5.4 | Consent revoke waits for the server | Test with a delayed response |
| V5.5.5 | A person outside the team completes the journey unaided | Observation note |
| V5.5.6 | Demo resets from one command | Timed run |
| V5.5.7 | The client is generated from OpenAPI, with no hand-written request types | Code review |
| V5.5.8 | Sign-in is outside the role guard, and guards are tested | Test |
| V5.5.9 | Switching pack changes screen content | Playwright report |

---

## Phase 5 exit gate

- [ ] Demo journey passes in all three languages. **Partly:** it passes in English on screen, and Hindi screens pass the accessibility run. Arabic has no text of its own until its text is approved
- [x] Dashboard numbers trace to events: each measure names its source rows (`sources` in `/v1/analytics/overview`)
- [x] Fairness and time-to-referral tests pass (`tests/unit/test_fairness.py`, `tests/api/test_analytics.py`)
- [ ] Rehearsal run done with a recorded backup. **Not yet:** it needs a person to run and record it
- [x] `brain.md` is up to date (#018)

**Status, 9 Nov 2026:** built and tested; see `docs/phases/CROSS_VERIFICATION.md`. Booking and the centre finder are real, not mocked. The centre lists are empty until filled from a public source, and the screen says so. Notifications are mocked: nothing is really sent.

**If behind:** mock booking and centre finder and label them. Keep the pathway and metrics real.
