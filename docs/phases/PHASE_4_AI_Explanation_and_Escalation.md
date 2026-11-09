# Phase 4: AI Explanation, Guardrails and Human Escalation

**Dates:** 12–14 Nov 2026 · **Build steps:** `backend.md` §9 steps 17–21 · **Requirements:** R1, R2, R3

**Phase goal:** people get safe, non-directive answers in English, Arabic and Hindi, and anything complex reaches a real counsellor.

**Build order matters:** validators come before LLM output, and templates come before the LLM, so the safety net exists first.

---

## 4.1 Knowledge base and content governance

**Goal:** a small body of accurate, licensed, versioned content.

**Objectives**
- O4.1.1 T1 conditions covered in English, Arabic and Hindi at the agreed levels.
- O4.1.2 Every document shows source, version and review status.
- O4.1.3 Reuse rights checked.

**Work** (step 17)
- Write original text from sources that allow it.
- Start with general carrier content plus T1 conditions at the Simple level; add other levels if time permits.
- Embed and search; keep the embedding model out of the event loop and available offline.

**Files:** `backend/app/kb/content/**`, `backend/app/kb/embedder.py`, `backend/app/kb/ingest.py`, `docs/clinical/content_review_log.md`
**Issues to close:** M7, M11, H13, G9, S8 (labels), part of H15

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V4.1.1 | Each file has source, reviewer status and version | Lint run on front matter |
| V4.1.2 | Retrieval never returns another language or level | Test |
| V4.1.3 | Arabic and Hindi content is checked by native speakers | Name in the review log |
| V4.1.4 | Clinician reviewed T1 content, or it's labelled as a draft | Review log |
| V4.1.5 | Licence noted for each source | Table in the review log |
| V4.1.6 | A coverage table shows T1 conditions complete in each language at the Simple level | Review log |
| V4.1.7 | Risk wording is set per condition, allowing for reduced penetrance | Review log |
| V4.1.8 | Faith and culture content is per pack and on request only, and is reviewed or left out | Review log |

---

## 4.2 Output validators and lexicon

**Goal:** an answer can't reach a user with a wrong number, stigmatising words, a directive, or a diagnosis.

**Objectives**
- O4.2.1 Numbers are tied to meaning, not merely present.
- O4.2.2 Validators work as well in each pack's languages and dialects as in English, including Arabic, Gulf dialect and Hindi.
- O4.2.3 Normal text isn't over-blocked.
- O4.2.4 Failure falls back safely.

**Work** (step 18)
- Fact-ID placeholder approach, approved general-facts set, Arabic and Hindi number words.
- Lexicon and directive patterns from 1.2, plus an LLM judge.
- Add "you are healthy" style certainty to the diagnosis checks.

**Files:** `backend/app/explain/validators/*`, `backend/app/explain/lexicon/terms.yaml`
**Issues to close:** **C5**, H12, H13, M4, G1

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V4.2.1 | Swapped 25/50 text is blocked | `tests/unit/test_validators.py` (passes wrongly in the original spec) |
| V4.2.2 | *nisf atfalikuma sayusabun* ("half of your children will be affected") is blocked | Same |
| V4.2.3 | "You carry one changed copy" passes | Same |
| V4.2.4 | `lazim tsawwun` and "It would be best to" are flagged | Same |
| V4.2.5 | "You are healthy" is flagged | Same |
| V4.2.8 | Hindi stigma, directive and number-word samples, written by a Hindi speaker, are handled correctly | Same |
| V4.2.6 | Over-blocking on approved content is under an agreed limit | Rate reported from a clean sample |
| V4.2.7 | Fallback templates themselves pass all validators | Test over every template |

---

## 4.3 Boundary router and explanation pipeline

**Goal:** each question is correctly classified, and the pipeline can't skip safety steps.

**Objectives**
- O4.3.1 `hamil` is handled correctly.
- O4.3.2 Clinical questions are refused kindly with a booking offer.
- O4.3.3 Distress is handled immediately.
- O4.3.4 The LLM has no tools, sees no PII, and holds no DB transaction.
- O4.3.5 Template mode works with no LLM.

**Work** (step 19)
- Router with reviewed Arabic and Hindi patterns and a conservative merge.
- Graph: redact, route, retrieve, generate, validate, fallback.
- Close DB work before LLM calls; set one overall deadline.
- Respond once validated (no token streaming).
- Add a coercion path.

**Files:** `backend/app/explain/*`, `backend/app/api/v1/chat.py`, `backend/app/explain/prompts/*`, `backend/app/explain/templates/*`, `frontend/app/[locale]/(app)/app/ask/`
**Issues to close:** **C6, C10**, H9, M1, M4

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V4.3.1 | *madha ya'ni annani hamil lil-jin?* ("What does it mean that I'm a carrier?") routes to Education | Eval set (fails in the original spec) |
| V4.3.2 | *ana hamil fi al-shahr al-thalith* ("I'm three months pregnant") routes to Clinical | Eval set |
| V4.3.3 | Clinical routing recall is at least 95% in **each** language | Eval report |
| V4.3.4 | Distress shows verified contacts in one response and alerts a human | Test |
| V4.3.5 | A 30 s LLM stall returns a template, with no DB error | Test using a slow stub |
| V4.3.6 | Prompt-injection attempts cause no rule break | Red-team results |
| V4.3.7 | Works with LLM provider set to `template` | Test |
| V4.3.8 | VUS and X-linked users never get the general carrier template | Test |
| V4.3.9 | Answers render as plain text | Frontend test |
| V4.3.10 | A Hindi question about carrier status gets an education answer, and a Hindi pregnancy question goes to a human | Eval set |
| V4.3.11 | The LLM client has no tools, and no database transaction is open during a call | Test |
| V4.3.12 | A coercion message reaches a human, in each language | Eval set |
| V4.3.13 | No answer text reaches the client before validation finishes | Test |

---

## 4.4 Options and values reflection

**Goal:** people see correct, unranked options, and the system never turns their values into a recommendation.

**Objectives**
- O4.4.1 Options come from the signed-off jurisdiction table.
- O4.4.2 Equal weight and neutral order.
- O4.4.3 Values are private by default, and never scored.

**Work** (step 20)
- Options service, neutral ordering rule, values save and optional share.
- Faith content only on request, if a reviewer is available (otherwise T3).

**Files:** `backend/app/decision/*`, `backend/app/api/v1/options.py`, `backend/app/api/v1/values.py`, `frontend/app/[locale]/(app)/app/options/`
**Issues to close:** **S5**, part of H14

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V4.4.1 | Output equals the signed-off table for each scenario | Test |
| V4.4.5 | Switching pack changes the options, using each pack's signed-off table | Test |
| V4.4.2 | All cards have the same fields, with no rank or recommended badge | Test, screenshot |
| V4.4.3 | Changing values doesn't change option content or order | Property test |
| V4.4.4 | A counsellor sees values only after the user shares | API test |

---

## 4.5 Triage, assignment and counsellor console

**Goal:** the right case reaches a real person on time, with useful context and no extra data.

**Objectives**
- O4.5.1 Triage runs on results, match and chat.
- O4.5.2 Cases can actually be assigned and seen.
- O4.5.3 Every case explains its priority.
- O4.5.4 The summary is built from facts, marked "verify before use".

**Work** (step 21)
- Scoring with a G6PD-style rule per condition.
- Unassigned pool, claim, coordinator assignment.
- Co-pilot summary from structured data, so an LLM can't add clinical claims.
- Console screens.

**Files:** `backend/app/triage/*`, `backend/app/api/v1/cases.py`, `frontend/app/[locale]/(counsellor)/`
**Issues to close:** **C8, C9**, G7, part of H14

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V4.5.1 | Each persona produces the expected priority and reasons | Table-driven test |
| V4.5.2 | A P2 case appears in the pool and can be claimed | E2E (the queue is empty in the original spec) |
| V4.5.3 | Other counsellors get 404 on a claimed case | `test_bola.py` |
| V4.5.4 | Priority only moves up automatically | Test |
| V4.5.5 | A counsellor rates the summary useful and the rules sensible | Note, or a stated limitation |
| V4.5.6 | Triage runs from results, from the match and from chat | Test for each trigger |
| V4.5.7 | The summary is marked "verify before use" and holds only structured facts | Test |

---

## Phase 4 exit gate

- [x] Arabic "carrier" question gets an education answer on screen (`phase4.spec.ts`)
- [x] Clinical question gets a refusal and booking offer, in all three languages (`phase4.spec.ts`)
- [x] Chat works with the LLM switched off (template mode is the default; `test_chat_works_with_no_model`)
- [x] P2 case reaches a counsellor's screen (`phase4.spec.ts`, `experience.spec.ts`)
- [x] Early eval run done, with failures logged (`docs/evaluation/router_early_eval.md`). It found a serious gap, now narrowed but **not closed**: see brain.md #017
- [x] `brain.md` is up to date (#017)

**Status, 9 Nov 2026:** shipped in template mode, as the line below allows. No model provider is connected; that decision is the user's.

**If behind:** ship with templates only and say so. That's safer and still demonstrates the architecture.
