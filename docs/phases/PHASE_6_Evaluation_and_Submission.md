# Phase 6: Evaluation, Hardening and Submission

**Dates:** 18–20 Nov 2026 · **Build step:** `backend.md` §9 step 25 · **Requirements:** R6, and all as evidence

**Phase goal:** submit on **19 Nov** with honest proof, leaving 20 Nov as a buffer.

**Feature freeze:** end of 17 Nov. After that, only fixes.

**Deliverables named by the FAQ:** working prototype, technical documentation, and a clear statement of assumptions, dependencies and limitations, with every data source declared and the solution's maturity stated. The full requirements shared on registration may add more (see 1.1).

---

## 6.1 Safety and accuracy evaluation

**Goal:** measured results, including failures, from tests that aren't marking their own work.

**Objectives**
- O6.1.1 150+ golden and 50+ red-team items, balanced across English, Arabic and Hindi.
- O6.1.2 Results reported per language.
- O6.1.3 Independent humans score a sample.
- O6.1.4 Targets from `docs/03` §5 are reported as met or missed.

**Work** (step 25)
- Finish the eval sets; native speakers write the Arabic and Hindi items rather than translating them.
- Run, fix, and re-run. Record both rounds.
- Two people independently score a random sample for directiveness and stigma; report agreement.

**Files:** `backend/tests/eval/*`, `docs/evaluation/safety_and_accuracy_report.md`
**Issues to close:** C5, H12 (confirm), C6 (confirm)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V6.1.1 | Numeric accuracy 100% on the test set, or failures listed | Report |
| V6.1.2 | Clinical escalation at least 95% in each language | Report |
| V6.1.3 | Human-scored sample results are included, not only validator scores | Scoring sheet |
| V6.1.4 | Results in all three languages are shown side by side | Report |
| V6.1.5 | Any failure stays in the report | Reviewer compares raw output with the report |
| V6.1.6 | Golden and red-team set sizes are met, per language | Count in the report |
| V6.1.7 | Stigmatising and directive outputs are zero in the human-scored sample, or are listed | Scoring sheet |

---

## 6.2 Real-user comprehension test

**Goal:** the first real evidence that people understand better, honestly labelled.

**Objectives**
- O6.2.1 15–30 adult volunteers, in Hindi and English, and in Arabic where possible.
- O6.2.2 Voluntary, anonymous, with fake results only.
- O6.2.3 Pre and post teach-back.
- O6.2.4 Limits stated.

**Work**
- Book volunteers by **12 Nov**.
- Explain the purpose and get consent. Volunteers use synthetic personas and never their own results.
- Check whether your university requires ethics review, and record the answer.
- Provide a support note in case the topic is upsetting.
- Analyse paired changes.

**Files:** `docs/evaluation/comprehension_test_protocol.md`, `docs/evaluation/comprehension_test_results.md`
**Issues to close:** **S7**

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V6.2.1 | Consent recorded, no identifying data kept | Protocol, anonymised sheet |
| V6.2.2 | Sample size and how volunteers were found are stated | Results file |
| V6.2.3 | Reported as a small convenience sample, not as clinical validation | Reviewer |
| V6.2.4 | If the test couldn't run, the submission says so, and uses no simulated figures | Reviewer |
| V6.2.5 | Pre and post scores are paired per volunteer | Analysis sheet |

---

## 6.3 Security and privacy hardening

**Goal:** no known high-risk hole, and evidence of having looked.

**Objectives**
- O6.3.1 OWASP API and LLM checklists completed.
- O6.3.2 Scans are clean or exceptions are explained.
- O6.3.3 No PHI in logs, errors or prompts.

**Work**
- Run semgrep, bandit, pip-audit, npm audit, gitleaks (full history) and trivy.
- Manual attempts against BOLA, token misuse and invitations.
- Load smoke test.
- Finalise the threat model.

**Files:** `docs/security/threat_model.md`, `docs/security/security_checklist.md`
**Issues to close:** H6, H16, H18 (confirm)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V6.3.1 | Each scanner run has a saved output | Files or CI links |
| V6.3.2 | Each OWASP row has a test or a written reason | Checklist |
| V6.3.3 | Marker-value scan finds no PHI in a full demo's logs | Script output |
| V6.3.4 | Non-LLM endpoints p95 under 300 ms | Load result |
| V6.3.5 | No real data or secrets anywhere in Git history | gitleaks result, reviewer |

---

## 6.4 Technical documentation, assumptions, limitations, commercial plan

**Goal:** the documents the portal requires, plus coverage of the weakest criterion.

**Objectives**
- O6.4.1 Someone new can run and understand the project.
- O6.4.2 Assumptions and limitations are candid.
- O6.4.3 Commercial viability and path to pilot are credibly covered.
- O6.4.4 Data sources, dependencies and maturity are stated as the FAQ requires.

**Work**
- Technical doc: architecture, data flows, safety model, deployment.
- Assumptions, dependencies and limitations, covering synthetic data, placeholder frequencies, review status, T3 mocks, S6 outcome.
- Commercial and pilot plan: buyer, costs, counsellor-time model, first pilot in Abu Dhabi with a licensed partner under Art. 28, then how new countries are added.
- Check every claim against the code.

**Files:** `docs/submission/technical_documentation.md`, `docs/submission/assumptions_and_limitations.md`, `docs/submission/data_sources.md`, `docs/submission/maturity_statement.md`, `docs/submission/commercial_and_pilot_plan.md`, `README.md`
**Issues to close:** **S2, S4, S8**, G10, S9, S10, S11, H14

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V6.4.1 | A new person runs the demo from the README alone | Timed run note |
| V6.4.2 | Each claim in the docs maps to a test or is labelled a design goal | Claims table |
| V6.4.3 | Each T3 mock is listed as a limitation | Compare with the scope tiers |
| V6.4.4 | Cost figures show assumptions and are labelled as estimates | Reviewer |
| V6.4.5 | All six criteria addressed | Mapping table |
| V6.4.6 | Global claims name only reviewed packs, and everything else is called a design goal | Reviewer |
| V6.4.7 | Every data source used is declared, and nothing declared is unused | Compare with the code |
| V6.4.8 | Assumptions, dependencies and limitations are each stated clearly | Reviewer |
| V6.4.9 | The maturity statement separates what existed from what was built during the challenge | Compare with `brain.md` |
| V6.4.10 | The Hindi coverage limit (G10) is stated | Reviewer |

---

## 6.5 Demo, deck and rehearsal

**Goal:** a clear, reliable story, even if the live demo breaks.

**Objectives**
- O6.5.1 Video of 3–5 minutes (or as the rules require).
- O6.5.2 Deck follows the six criteria.
- O6.5.3 Answers ready for hard questions.

**Work**
- Record in template mode, or with a verified LLM run.
- Include a live red-team moment in Arabic or Hindi.
- Show "Synthetic data, not real patients" on screen.
- Update the judge Q&A from `docs/03` §6, adding the options, law and PSI questions.

**Files:** `docs/submission/demo_script.md`, `docs/submission/pitch_deck_outline.md`, `docs/submission/judge_qa.md`, `frontend/app/[locale]/(public)/story/`
**Issues to close:** S8

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V6.5.1 | Video shows the actual product | Compare with the build |
| V6.5.2 | A non-team viewer can state the problem and solution after watching | Note |
| V6.5.3 | No DoH or M42 logos implying endorsement | Reviewer |
| V6.5.4 | Each demo number is labelled synthetic | Reviewer |
| V6.5.5 | Team answers the Q&A list without notes | Rehearsal |
| V6.5.6 | The deck covers all six judging criteria | Mapping table |

---

## 6.6 Submit and freeze

**Goal:** a complete submission accepted a day early.

**Objectives**
- O6.6.1 Submitted by 19 Nov.
- O6.6.2 The submitted version is tagged and reproducible.
- O6.6.3 Ready for the GITEX stage if selected.

**Work**
- Final checklist against `docs/submission/competition_requirements.md`.
- Tag the release, submit, save the confirmation.
- Write the final `brain.md` entry.
- List post-submission priorities, and prepare for 7–11 Dec.

**Files:** `docs/submission/submission_checklist.md`, `brain.md`

**Issues to close:** S11

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V6.6.1 | Every required item is uploaded | Second person checks the portal |
| V6.6.2 | The tagged commit builds from a clean clone | Run log |
| V6.6.3 | Confirmation saved | Screenshot or email |
| V6.6.4 | Links work when logged out, if links are submitted | Incognito test |
| V6.6.5 | The code can be shared on request: it builds, and holds no secrets | gitleaks result, clean clone |
| V6.6.6 | If placed in the top three, the team knows who presents in person at GITEX, 7–11 Dec | `brain.md` note |

---

## Phase 6 exit gate

- [ ] Submitted, with confirmation saved
- [ ] Safety report and limitations are honest and complete
- [ ] Release tagged
- [ ] Final `brain.md` entry written

**If behind:** the order to protect is: submission, then prototype working, then documentation, then video polish.
