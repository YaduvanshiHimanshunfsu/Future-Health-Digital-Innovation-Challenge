# 05 — Project Structure and File Index

Generated from the same manifest as the stubs, so the two agree. `[NEW]` marks items the review added beyond `backend.md` §10.

Every code-type file is a **documentation-only stub** until implementation is requested. Generated files, such as `uv.lock` and `package-lock.json`, are deliberately absent because tools must create them.

## Top level

```text
Future Health/
├── CLAUDE.md            Rules for AI assistants
├── brain.md             Mandatory project log
├── README.md            Project overview
├── problem statement.md Challenge text (original)
├── .gitignore
├── .pre-commit-config.yaml
├── .github/             PR template, CI stub
├── backend/             FastAPI modular monolith
│   ├── app/             Application code
│   ├── alembic/         Database migrations
│   ├── synthetic/       Synthetic data and personas
│   └── tests/           unit, api, eval
│   (backend/packs/ holds per-country settings)
├── frontend/            Next.js app
│   ├── app/             Routes (P1 to P19, Story Mode)
│   ├── components/      ui, layout, motion, risk, charts
│   ├── lib/             API client, auth, i18n
│   ├── messages/        English, Arabic and Hindi text
│   └── tests/e2e/       Playwright
├── infra/               Compose, OpenFGA, Keycloak, Postgres
├── scripts/             Runbooks
└── docs/                All documentation
    ├── phases/          6-phase plan
    ├── submission/      Portal deliverables
    ├── clinical/        Clinical decisions and review
    ├── compliance/      Legal baseline
    ├── security/        Threat model, checklist
    └── evaluation/      Safety report, comprehension test
```

## `./`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `.pre-commit-config.yaml` | Pre-commit hooks. | 1.3 |  | H16 |

## `.github/workflows/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `ci.yml` | CI pipeline: lint, types, security scans, tests, image scan. | 1.3 |  | H16 |

## `backend/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `.env.example` | Config template with no real secrets. | 1.3 |  | H15 |
| `Dockerfile` | API and worker container image. | 1.3 |  | H15 |
| `alembic.ini` | Alembic configuration. | 1.5 |  | H15 |
| `pyproject.toml` | Dependencies and tool config. | 1.3 |  | H15, H16 |

## `backend/alembic/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `env.py` | Alembic environment. | 1.5 |  | H15 |

## `backend/alembic/versions/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `0001_init.py` | Initial schema. | 1.5 | R4 | H18, M2 |

## `backend/app/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `main.py` | Application factory. | 1.4 |  | M12 |

## `backend/app/analytics/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `events.py` | Allow-listed events with a pseudonym and reporting groups, no free text. **Built.** | 5.4 | R6 | H11 |
| `fairness.py` | Gaps per dimension, with small and protecting cells withheld. **Built.** | 5.4 | R6 | H11 |
| `metrics.py` | Programme measures, each from named source rows. **Built.** | 5.4 | R6 | H10, H11, M9 |

## `backend/app/api/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `deps.py` | Shared dependencies. | 1.4 |  | H9 |

## `backend/app/api/v1/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `access_log.py` | Who saw my data. | 3.5 | R4 | H14 |
| `analytics.py` | Admin metrics. | 5.4 | R6 | H11 |
| `assessments.py` | Quizzes. | 5.3 | R6 |  |
| `booking.py` [NEW] | Booking. | 5.2 | R3, R5 | H14 |
| `break_glass.py` [NEW] | Break-glass. | 3.5 | R4 | H14 |
| `cases.py` | Counsellor queue. | 4.5 | R3 | C9, H14 |
| `centres.py` [NEW] | Centre finder. | 5.2 | R2 | H14 |
| `chat.py` | AI companion. | 4.3 | R1, R3 | C7, H9 |
| `consents.py` | Consent centre. | 3.2 | R4 | H7, H8 |
| `content.py` [NEW] | Content governance. | T3 | R1 | H14 |
| `couples.py` | Couples and match. | 3.3 | R4 | C1, C2, C7, H8 |
| `health.py` | Liveness and readiness. | 1.4 |  |  |
| `invitations.py` | Invitations. | 3.4 | R4 | H17 |
| `me.py` [NEW] | Profile. | 2.3 | R4 | H8, H14 |
| `options.py` | Option cards. | 4.4 | R2 | S5 |
| `pathway.py` | Pathway and journey. | 5.1 | R5 | H10, H14 |
| `referrals.py` [NEW] | Referral builder. | 5.2 | R5 | H14 |
| `reports.py` | Lab ingestion. | 2.3 | R4, R5 | C1 |
| `results.py` | My results and risk. | 2.5 | R1 | H5 |
| `shared.py` [NEW] | Read a shared report. | 3.2 | R4 | H8 |
| `values.py` [NEW] | Values reflection. | 4.4 | R2 | H14 |

## `backend/app/assessments/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `instruments.py` | Teach-back (draft) and adapted SURE, honestly labelled. **Built.** | 5.3 | R6 | S7 |
| `scoring.py` | Server-side scores and paired change. **Built.** | 5.3 | R6 | H11 |

## `backend/app/booking/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `service.py` [NEW] | Counsellor booking. | 5.2 | R3, R5 | H14 |

## `backend/app/centres/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `service.py` [NEW] | Screening and counselling centre finder. | 5.2 | R2 | H14 |

## `backend/app/core/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `config.py` | Typed settings. | 1.4 |  | M12 |
| `errors.py` | Error handling. | 1.4 |  |  |
| `i18n.py` | Localisation. | 1.4 |  |  |
| `logging.py` | PHI-safe logging. | 1.4 |  |  |
| `middleware.py` | HTTP hardening. | 1.4 |  | M12 |
| `rate_limit.py` | Abuse prevention. | 1.4 |  |  |
| `security.py` | Authentication. | 1.4 |  |  |

## `backend/app/db/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `base.py` | ORM base. | 1.5 |  |  |
| `session.py` | Database engine and sessions. | 1.5 |  | H9 |

## `backend/app/decision/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `options.py` | Option cards. | 4.4 | R2 | S5 |
| `values.py` | Values reflection. | 4.4 | R2 | H14 |

## `backend/app/explain/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `context.py` | Requester's fact set. | 4.3 | R1, R3 | C7 |
| `graph.py` | LangGraph pipeline. | 4.3 | R1, R3 | C5, H9, M1, M4 |
| `llm.py` | LLM adapter. | 4.3 | R1, R3 | H9 |
| `retriever.py` | RAG retrieval. | 4.3 | R1, R3 | H15 |
| `router.py` | Boundary classification. | 4.3 | R1, R3 | C6, C10 |
| `state.py` | Graph state. | 4.3 | R1, R3 |  |

## `backend/app/explain/lexicon/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `directive_terms.yaml` [NEW] | Directive phrases. | 4.2 | R2 | H12 |
| `general_facts.yaml` [NEW] | Approved general facts. | 4.2 | R1 | C5 |
| `number_words.yaml` [NEW] | Number words. | 4.2 | R1 | C5 |
| `terms.yaml` | Stigma lexicon. | 4.2 | R1 | H12 |

## `backend/app/explain/prompts/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `judge_directive.txt` [NEW] | Directiveness judge prompt. | 4.2 | R2 | H12 |
| `router_system.txt` [NEW] | Router prompt. | 4.3 | R3 | C6 |
| `system_ar.txt` | Arabic system prompt. | 4.3 | R1 | C5, H13 |
| `system_hi.txt` [NEW] | Hindi system prompt. | 4.3 | R1 | C5, H13 |
| `system_en.txt` | English system prompt. | 4.3 | R1 | C5, H13 |

## `backend/app/explain/validators/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `diagnosis.py` | Diagnosis guard. | 4.2 | R1, R2 | H13 |
| `directive.py` | Non-directive guard. | 4.2 | R1, R2 | H12 |
| `lexicon.py` | Stigma guard. | 4.2 | R1, R2 |  |
| `numeric.py` | Numeric guard. | 4.2 | R1, R2 | C5 |
| `pipeline.py` | Runs all validators. | 4.2 | R1, R2 | H11 |
| `readability.py` | Literacy guard. | 4.2 | R1, R2 |  |

## `backend/app/ingestion/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `fhir_parser.py` | Parses FHIR bundles. | 2.3 | R1, R4 | M8 |
| `loinc.py` | LOINC and answer-code constants. | 2.3 | R1 |  |
| `service.py` | Ingestion use-case. | 2.3 | R4, R5 | C1, C8, H7, M8, M10 |

## `backend/app/kb/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `embedder.py` | Embeddings. | 4.1 | R1 | H15 |
| `ingest.py` | Knowledge-base loader. | 4.1 | R1 | M7 |

## `backend/app/models/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `analytics.py` | De-identified events. | 1.5 | R6 | H11 |
| `appointment.py` [NEW] | Counsellor appointments. | 5.2 | R3, R5 | H14 |
| `assessment.py` | Quiz and instrument scores. | 1.5 | R6 | H11 |
| `audit.py` | Audit log. | 1.5 | R4 |  |
| `break_glass.py` [NEW] | Break-glass events. | 3.5 | R4 | H14 |
| `case.py` | Care cases and pathway steps. | 1.5 | R3, R5 | H10, H18, M2 |
| `case_note.py` [NEW] | Counsellor notes. | 4.5 | R3 | H14 |
| `centre.py` [NEW] | Screening and counselling centres. | 5.2 | R2 | H14 |
| `consent.py` | Consent ledger. | 1.5 | R4 | H8, H19 |
| `conversation.py` | Chat history. | 1.5 | R1, R3 | H11, H19 |
| `couple.py` | Couples. | 1.5 | R4 | H8, H18 |
| `genetic.py` | Reports and carrier findings. | 1.5 | R4 | H18, M8 |
| `invitation.py` | Relative invitations. | 1.5 | R4 | H17 |
| `kb.py` | Knowledge-base chunks. | 1.5 | R1 | M7 |
| `outbox.py` [NEW] | Authorisation outbox. | 3.1 | R4 | H7 |
| `person.py` | Person table. | 1.5 | R4 | H11, H14, H18 |
| `referral.py` [NEW] | Referrals. | 5.2 | R5 | H14 |
| `values_note.py` [NEW] | Values reflection answers. | 4.4 | R2 | H14 |

## `backend/app/notifications/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `service.py` | SMS and email. | 5.2 | R5 |  |

## `backend/app/pathway/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `fhir_mapper.py` | FHIR R5 ServiceRequest and Task, minimum necessary. **Built.** | 5.2 | R5 |  |
| `scheduler.py` | Overdue scan: stalled flag, one reminder, lost to follow-up. **Built.** | 5.1 | R5 | H10, H15 |
| `state_machine.py` | Pathway transitions. | 5.1 | R5 | H10 |

## `backend/app/privacy/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `audit.py` | Audit chain. | 1.5 | R4 | H11, M10 |
| `authz.py` | OpenFGA adapter. | 3.1 | R4 | H7, H11 |
| `break_glass.py` [NEW] | Break-glass access. | 3.5 | R4 | H14 |
| `consent_service.py` | Consent use-cases. | 3.2 | R4 | H7, H8, H19 |
| `crypto.py` | Envelope encryption. | 2.1 | R4 | H18 |
| `invitations.py` | Relative invitations. | 3.4 | R4 | H17 |
| `kms.py` | Key providers. | 2.1 | R4 |  |
| `matching.py` | Couple matching. | 3.3 | R4 | C1, C2, C7, H3, S8 |
| `outbox.py` [NEW] | Authorisation outbox. | 3.1 | R4 | H7 |
| `psi_adapter.py` | PSI protocol. | 3.3 | R4 | H15, S8 |
| `redaction.py` | PII redaction and LLM allowlist. | 3.5 | R4 | H6 |
| `right_not_to_know.py` [NEW] | Right not to know. | 3.2 | R4 | S4, H8 |

## `backend/app/repositories/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `cases.py` | Case and queue queries. | 4.5 | R4 | C9 |
| `consents.py` | Consent queries. | 3.2 | R4 |  |
| `couples.py` | Couple queries. | 3.3 | R4 |  |
| `genetic.py` | Findings queries. | 2.3 | R4 | C1 |
| `persons.py` | Person queries. | 2.3 | R4 |  |

## `backend/app/risk_engine/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `engine.py` | Orchestrates the rules. | 2.4 | R1, R4 | C3, C4, C7, H1, H2, H3, H4, H5 |
| `frequencies.py` | Carrier frequency table. | 2.4 | R1 | H2 |
| `rules.py` | Mendelian maths. | 2.4 | R1 | C3, C4, H1, H5 |
| `types.py` | Domain types. | 2.4 | R1 | C3, C4 |
| `visuals.py` | Visual specs. | 2.5 | R1 | H5 |

## `backend/app/schemas/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `analytics.py` | Metric contracts, with suppressed cells. | 5.4 | R6 |  |
| `assessments.py` [NEW] | Assessment contracts. | 5.3 | R6 |  |
| `booking.py` [NEW] | Booking and referral contracts. | 5.2 | R5 | H14 |
| `cases.py` | Case and queue contracts, with reasons. | 4.5 | R3 |  |
| `chat.py` | Chat contract. Returned fact IDs must be partner-safe. | 4.3 | R1, R3 | C7 |
| `common.py` | Shared types plus StrictIn (extra=forbid) and Out bases. | 1.5 |  |  |
| `consent.py` | Consent contracts. | 3.2 | R4 |  |
| `couples.py` | Couple link, consent and match contracts. Match returns shared, none_shared or cannot_determine. | 3.3 | R4 | C2 |
| `invitations.py` | Invitation contracts. | 3.4 | R4 |  |
| `me.py` [NEW] | Profile and preference contracts. | 2.3 |  | H14 |
| `options.py` [NEW] | Options and values contracts. | 4.4 | R2 | H14 |
| `pathway.py` [NEW] | Journey and pathway contracts. | 5.1 | R5 | H14 |
| `results.py` | My results and risk contracts. | 2.5 | R1 |  |

## `backend/app/speech/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `service.py` [NEW] | Voice mode adapter. | T3 | R1, R6 | H14 |

## `backend/app/triage/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `assignment.py` [NEW] | Counsellor assignment. | 4.5 | R3 | C9 |
| `copilot.py` [NEW] | Case summary. | 4.5 | R3 | H14 |
| `scoring.py` | Priority rules. | 4.5 | R3 | C3, C8 |
| `service.py` | Case creation. | 4.5 | R3, R5 | C8, H10 |

## `backend/app/workers/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `celery_app.py` | Celery application. | 5.1 | R5 | H15 |
| `tasks.py` | Background jobs. | 5.1 | R5 | H7, H15 |

## `backend/synthetic/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `generate.py` | Synthetic population. | 2.2 |  | M3 |
| `personas.yaml` [NEW] | Named demo personas and couples for both packs. | 2.2 |  | C3, C4 |

## `backend/tests/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `conftest.py` | Shared fixtures. | 1.3 |  |  |

## `backend/tests/api/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `test_auth.py` | Expired, tampered, alg=none and wrong-audience tokens. | 1.4 |  |  |
| `test_bola.py` | Another user always gets 404. | 2.5 |  |  |
| `test_cases.py` [NEW] | Pool, claim, isolation. | 4.5 |  | C9 |
| `test_chat.py` [NEW] | Slow LLM, template mode, no leaks. | 4.3 |  | C7, H9 |
| `test_consents.py` | Grant, revoke, expiry, duplicates, outage. | 3.2 |  | H7, H8 |
| `test_ingestion.py` [NEW] | Benign dropped, replay, second report, malformed input. | 2.3 |  | C1, H7, M8 |
| `test_invitations.py` | Link previews don't burn tokens; identical failures; rate limit. | 3.4 |  | H17 |
| `test_matching.py` | Shared couple is found; no data is not 'none'; no partner-only leaks. | 3.3 |  | C1, C2, C7 |

## `backend/tests/eval/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `golden_qa.jsonl` | Golden questions: 150+ with expected labels and key facts. | 6.1 | R1, R3 | C6 |
| `redteam.jsonl` | Red-team prompts: 50+. | 6.1 | R2, R3 | H12 |
| `test_llm_eval.py` | Runs golden and red-team sets. | 6.1 | R1, R3, R6 | C5, H12 |

## `backend/tests/unit/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `test_audit_chain.py` | Tamper evidence and insert-only role. | 1.5 |  |  |
| `test_crypto.py` | Encryption round trip and tamper checks. | 2.1 |  |  |
| `test_engine_boundaries.py` [NEW] | Risk engine imports nothing from DB, API or LLM layers. | 2.4 |  |  |
| `test_fairness.py` [NEW] | Equity gaps and suppression. | 5.4 |  | H11, M9 |
| `test_redaction.py` [NEW] | English, Arabic and Hindi PII, plus failing closed. | 3.5 |  | H6 |
| `test_risk_engine.py` | Risk maths and invariants, including all V2.4 checks. | 2.4 |  | C3, C4, H1, H2, H3, H5 |
| `test_router.py` [NEW] | Boundary routing. Includes the hamil (pregnant or carrier) pair. | 4.3 |  | C6 |
| `test_state_machine.py` | Transitions, decline from each state, SLA. | 5.1 |  | H10 |
| `test_triage.py` | Priorities for every persona. | 4.5 |  | C8 |
| `test_validators.py` | Validators in English, Arabic and Hindi, including all V4.2 checks. | 4.2 |  | C5, H12, H13 |

## `docs/clinical/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `content_review_log.md` [NEW] | Who reviewed what, and source licences. | 4.1 |  |  |
| `options_by_jurisdiction.md` [NEW] | The source for the options table. See S5. | 1.2 |  |  |
| `risk_rules_review.md` [NEW] | Clinician review of the engine's rule table. | 1.2 |  |  |
| `support_contacts.md` [NEW] | Verified contacts for distress templates. See C10. Never invent these. | 1.2 |  |  |

## `docs/compliance/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `legal_baseline.md` [NEW] | Maps law to features. Not legal advice. See S4 and H19. | 1.2 |  |  |

## `docs/evaluation/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `comprehension_test_protocol.md` [NEW] | Voluntary test using synthetic personas only. See S7. | 6.2 |  |  |
| `comprehension_test_results.md` [NEW] | Report as a small convenience sample. | 6.2 |  |  |
| `safety_and_accuracy_report.md` [NEW] | Report failures as well as passes. | 6.1 |  |  |

## `docs/security/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `security_checklist.md` [NEW] | OWASP API and LLM evidence. | 6.3 |  |  |
| `threat_model.md` [NEW] | STRIDE, starting from backend.md §8.1. | 1.2 |  |  |

## `docs/submission/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `assumptions_and_limitations.md` [NEW] | A required deliverable. Be candid. | 6.4 |  |  |
| `commercial_and_pilot_plan.md` [NEW] | Covers the 'commercial viability and path to pilot' criterion. See S2 and S4. | 6.4 |  |  |
| `competition_requirements.md` [NEW] | What the portal requires. Fill in while logged in. | 1.1 |  |  |
| `demo_script.md` [NEW] | Follows the journey in sub-phase 5.5. | 6.5 |  |  |
| `judge_qa.md` [NEW] | Extends docs/03 §6. | 6.5 |  |  |
| `pitch_deck_outline.md` [NEW] | Follows the six judging criteria. | 6.5 |  |  |
| `submission_checklist.md` [NEW] | Final check before submitting on 19 Nov. | 6.6 |  |  |
| `technical_documentation.md` [NEW] | A required deliverable. Must match the code. | 6.4 |  |  |

## Frontend: what changed when it was built (6 Nov 2026)

The folders below are the original plan. Building the frontend changed these files:

| Change | Files | Why |
|---|---|---|
| Removed | `app/api/auth/[...nextauth]/route.ts`, `app/layout.tsx`, `lib/api/hooks.ts`, `app/[locale]/dev/` | Sign-in is handled by this app's own server instead of NextAuth, and `app/[locale]/layout.tsx` is the root layout |
| Added | `app/api/auth/[action]/route.ts`, `lib/auth/oidc.ts`, `lib/api/server.ts`, `lib/api/origin.ts`, `lib/api/types.ts` | Sign-in with PKCE, server-side API calls, and the cross-site check |
| Added | `app/[locale]/(app)/app/shared/[id]/`, `app/[locale]/(admin)/admin/break-glass/` | Reading a share, and reviewing emergency access |
| Added | `components/forms/`, `components/risk/FactList.tsx`, `components/risk/Visuals.tsx`, `components/layout/SiteShell.tsx`, `I18nProvider.tsx`, `Later.tsx` | Interactive parts, the page shell, and honest placeholders |
| Added | `lib/i18n/translate.ts`, `lib/i18n/server.ts`, `lib/risk/words.ts` | Translation without a library, and words for facts |
| Added | `Dockerfile`, `.dockerignore`, `postcss.config.mjs`, `tests/unit/copy.test.mjs`, `tests/e2e/fixtures.ts` | Container build, wording rules, and test helpers |
| Added outside `frontend/` | `backend/app/api/v1/packs.py`, `scripts/seed_demo.py` | The public country list, and demo accounts |

## `frontend/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `.env.example` | Frontend config template. | 1.6 |  |  |
| `middleware.ts` | Routing guard. | 5.5 |  | M2 |
| `next.config.ts` | Next.js config. | 1.6 |  |  |
| `package.json` | Frontend dependencies. Empty placeholder, since JSON can't hold comments. See frontend/README.md. | 1.6 |  |  |
| `playwright.config.ts` | End-to-end config. | 5.5 |  |  |
| `tailwind.config.ts` | Tailwind tokens. | 1.6 |  | M5 |
| `tsconfig.json` | TypeScript config. Empty placeholder. | 1.6 |  |  |

## `frontend/app/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `globals.css` | Global styles and design tokens. | 1.6 |  |  |
| `layout.tsx` | Root layout. | 1.6 |  |  |

## `frontend/app/[locale]/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `error.tsx` | Error page. | 1.6 |  |  |
| `layout.tsx` | Locale layout. | 1.6 |  |  |
| `not-found.tsx` | 404 page. | 1.6 |  |  |
| `template.tsx` | Page transition wrapper. | 1.6 |  |  |

## `frontend/app/[locale]/(admin)/admin/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P18 Outcomes dashboard. Scope tier T1. | 5.4 | R6 | S7 |

## `frontend/app/[locale]/(admin)/admin/equity/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P19 Equity and privacy dashboard. Scope tier T1. | 5.4 | R6 | H11, M9 |

## `frontend/app/[locale]/(app)/app/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P6 My journey dashboard. Scope tier T1. | 5.5 | R5 |  |

## `frontend/app/[locale]/(app)/app/ask/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P9 Ask Samvid. Scope tier T1. | 4.3 | R1, R3 | M1 |

## `frontend/app/[locale]/(app)/app/check/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P15 Teach-back. Scope tier T1. | 5.3 | R6 | H13 |

## `frontend/app/[locale]/(app)/app/couple/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P8 Couple risk explainer. Scope tier T1. | 2.5 | R1 | S5, H5 |

## `frontend/app/[locale]/(app)/app/family/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P12 Invite family. Scope tier T2. | 3.4 | R4 | H13 |

## `frontend/app/[locale]/(app)/app/journey/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P14 Care journey and booking. Scope tier T1. | 5.1 | R3, R5 | H10 |

## `frontend/app/[locale]/(app)/app/options/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P10 Options and values. Scope tier T2. | 4.4 | R2 | S5 |

## `frontend/app/[locale]/(app)/app/partner/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P11 Partner sharing. Scope tier T1. | 3.3 | R4 | C2, S6, S8 |

## `frontend/app/[locale]/(app)/app/privacy/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P13 Consent centre and access log. Scope tier T1. | 3.2 | R4 |  |

## `frontend/app/[locale]/(app)/app/result/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P7 My result. Scope tier T1. | 2.5 | R1 | H13 |

## `frontend/app/[locale]/(counsellor)/counsellor/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P16 Triage queue. Scope tier T1. | 4.5 | R3 | C9 |

## `frontend/app/[locale]/(counsellor)/counsellor/case/[id]/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P17 Case detail. Scope tier T1. | 4.5 | R3, R5 | H14 |

## `frontend/app/[locale]/(public)/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P1 Home. Scope tier T1. | 1.6 |  | S8 |

## `frontend/app/[locale]/(public)/centres/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` [NEW] | Centre finder (new). Scope tier T2. | 5.2 | R2 | H14 |

## `frontend/app/[locale]/(public)/learn/cousin-marriage/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P3 Facts, not myths. Scope tier T2. | 1.6 | R1 | H4, H13 |

## `frontend/app/[locale]/(public)/learn/inheritance/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P2 How inheritance works. Scope tier T2. | 1.6 | R1 | H13 |

## `frontend/app/[locale]/(public)/privacy/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P4 Privacy promise. Scope tier T2. | 1.6 | R4 | S8 |

## `frontend/app/[locale]/(public)/story/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | Story Mode. Scope tier T2. | 6.5 |  | S8, M13 |

## `frontend/app/[locale]/dev/visuals/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | Development preview of risk visuals. Scope tier T3. | 2.5 |  |  |

## `frontend/app/[locale]/i/[token]/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` [NEW] | Invitation landing (new). Scope tier T2. | 3.4 | R4 | H14, H17 |

## `frontend/app/[locale]/start/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `page.tsx` | P5 Sign-in and preferences. Scope tier T1. | 5.5 | R4 | H8, M2, S8 |

## `frontend/app/api/auth/[...nextauth]/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `route.ts` | Sign-in route. | 5.5 |  |  |

## `frontend/app/api/proxy/[...path]/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `route.ts` | Backend proxy. | 5.5 |  |  |

## `frontend/components/charts/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `ceramicTheme.ts` | Chart theme: palette, Western digits, suppressed counts as null and shown as "<10". **Built.** | 5.4 |  | M5, M9 |
| `ChartFrame.tsx` | Title, a sentence saying what the chart shows, and the same numbers as a table. **Built.** | 5.4 |  |  |
| `BarChart.tsx` | HTML bars that grow from the reading side, with an optional reference line. **Built.** | 5.4 |  |  |
| `DonutChart.tsx` | Parts of a whole, total in the middle. **Built.** | 5.4 |  |  |
| `LineChart.tsx` | A trend; suppressed points break the line. **Built.** | 5.4 |  |  |
| `Heatmap.tsx` | A real table with shaded cells; suppressed cells hatched. **Built.** | 5.4 |  | M9 |
| `SlaRing.tsx` | Time left in a step, as a meter. Used on the queue and case pages. **Built.** | 4.5 |  |  |
| `BoundaryDonut.tsx` | Boundary labels donut. Stub: builds on `DonutChart` once the analytics endpoint exists. | 5.4 |  |  |
| `ComprehensionLine.tsx` | Comprehension chart. Stub: builds on `LineChart`. | 5.4 |  |  |
| `EquityBars.tsx` | Equity bars with gap badge. Stub: builds on `BarChart`. | 5.4 |  | H11 |
| `PathwayFunnel.tsx` | Pathway funnel. Stub: builds on `BarChart`. | 5.4 |  |  |
| `RegionAgeHeatmap.tsx` | Region and age heatmap. Stub: builds on `Heatmap`. | 5.4 |  | M9 |
| `TimeToCounselling.tsx` | Time-to-counselling bars. Stub: builds on `BarChart` with the SLA line. | 5.4 |  |  |

## `frontend/components/layout/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `LanguageSwitch.tsx` | Language switch. | 1.6 |  |  |
| `ListenButton.tsx` | Reads an explanation aloud, with on-device voices only; absent where none exists. **Built.** | T3 |  | H14 |
| `LiteracyToggle.tsx` | Simple, Standard or Detailed, saved to the profile. **Built.** | 1.6 |  |  |
| `MosaicDivider.tsx` | Mosaic divider that settles in once. **Built.** | 1.6 |  |  |
| `PrivacyBadge.tsx` | Lock chip to the privacy centre; names a place, claims nothing. **Built.** | 1.6 |  |  |
| `TilePattern.tsx` | Sand band with the 8-point star tile. **Built.** | 1.6 |  |  |

## `frontend/components/motion/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `CountUp.tsx` | Count-up for counts of things, never for a chance (a test enforces it). **Built.** | 1.6 |  |  |
| `PageTransition.tsx` | Fade and short rise on every navigation. **Built.** | 1.6 |  |  |
| `PathDraw.tsx` | An SVG line that draws itself once when seen. **Built.** | 1.6 |  |  |
| `PulseCurrent.tsx` | Three pulses, then rest. **Built.** | 1.6 |  |  |
| `RiseIn.tsx` | Below-the-fold content rises in once; visible without script. **Built.** | 1.6 |  |  |
| `TileFlip.tsx` | Question and answer tile on a real button; both sides readable without script. **Built.** | 1.6 |  |  |

## `frontend/components/risk/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `CoupleMatchBox.tsx` | Two partner tiles slide together; the same motion for every outcome. **Built.** | 3.3 |  |  |
| `IconArray.tsx` | Icon array. | 2.5 |  | H5 |
| `PregnancyStrip.tsx` | The engine's same figure drawn for four pregnancies. **Built.** | 2.5 |  |  |
| `PunnettSquare.tsx` | Punnett square. | 2.5 |  | H5 |
| `XLinkedDiagram.tsx` | X-linked inheritance visual. | 2.5 |  | H5 |

## `frontend/components/ui/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `Chip.tsx` | Chip. | 1.6 |  | M5 |
| `ClayCard.tsx` | Clay card. | 1.6 |  | M5 |
| `PillButton.tsx` | Pill button. | 1.6 |  | M5 |
| `Stepper.tsx` | Stepper. | 1.6 |  |  |

## `frontend/design-export/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `README.md` | Stitch HTML and Tailwind exports go here, before conversion. | 1.6 |  | M13 |

## `frontend/lib/api/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `client.ts` | Typed API client. | 5.5 |  |  |
| `hooks.ts` | TanStack Query hooks. | 5.5 |  |  |
| `schema.ts` | Generated API types. | 5.5 |  | M2 |

## `frontend/lib/auth/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `session.ts` | Session helpers. | 5.5 |  |  |

## `frontend/lib/i18n/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `config.ts` | next-intl config. | 1.6 |  |  |

## `frontend/messages/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `ar.json` | Arabic UI text. Empty placeholder for now. | 1.6 |  | H13 |
| `hi.json` [NEW] | Hindi UI text. Empty placeholder for now. | 1.6 |  | H13 |
| `en.json` | English UI text. Empty placeholder for now. | 1.6 |  | H13 |

## `frontend/public/illustrations/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `README.md` | Illustrations and Lottie or Rive assets. | 1.6 |  |  |

## `frontend/tests/e2e/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `accessibility.spec.ts` | axe checks on T1 screens. | 5.5 |  | M5 |
| `demo_journey.spec.ts` | End-to-end demo journey. | 5.5 |  |  |

## `infra/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `docker-compose.yml` | Local stack. | 1.3 |  | H15 |

## `infra/keycloak/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `realm-samvid.json` | Keycloak realm export. | 3.1 | R4 | M2 |

## `infra/openfga/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `model.fga` | Authorisation model. | 3.1 | R4 | H8 |

## `infra/postgres/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `init.sql` | Database bootstrap. | 1.3 | R4 | H15 |

## `scripts/`

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `README.md` [NEW] | Operational runbooks, written up before any scripts exist. | 1.3 |  |  |
| `bootstrap_openfga.md` [NEW] | Runbook: create the OpenFGA store and model, and record IDs in .env. | 3.1 |  | H15 |
| `export_openapi.md` [NEW] | Runbook: export OpenAPI and generate the TypeScript client. | 5.5 |  | M2 |
| `seed_demo.md` [NEW] | Runbook: reset and seed the demo personas in one command. | 5.5 |  |  |
| `verify_audit_chain.md` [NEW] | Runbook: verify the audit chain before a demo. | 6.3 |  |  |

## `backend/app/country_packs/` [NEW]

| File | Purpose | Phase | Req | Issues |
|---|---|---|---|---|
| `schema.py` [NEW] | Pack schema. | 2.6 |  | S9, G3, G4 |
| `loader.py` [NEW] | Loads and validates the active pack. | 2.6 |  | S9, G1–G6 |

## `backend/packs/_template/`, `ae-abu-dhabi/` and `in-india/` [NEW]

All three folders hold the same files. See `docs/07`.

| File | Purpose | Issues |
|---|---|---|
| `pack.yaml` | Pack identity. | G1, S9 |
| `options.yaml` | Reproductive options available here. | S5, G3 |
| `legal.yaml` | Legal rules. | G4 |
| `panel.yaml` | Screening panel and gene data. | G3, H2, H3 |
| `services.yaml` | Local care services. | G3, G7 |
| `support_contacts.yaml` | Crisis and support contacts. | C10, G3 |
| `identity.yaml` | Identity and records. | G2, G5 |
| `lexicon.yaml` | Word list selection. | G1, G9, H12 |
| `strata.yaml` | Equity strata and SLAs. | G6 |

## Added in Phase 1

| File | Purpose |
|---|---|
| `backend/app/asgi.py` | Entry point for the server |
| `backend/app/models/enums.py` | Shared value lists and their database checks |
| `backend/app/core/messages/` | Error messages in English and Hindi |
| `backend/app/ops/check_services.py` | Operator check of every dependency, including a real token |
| `backend/tests/api/test_http_hardening.py`, `test_denied_audit.py` | Headers, limits, errors, denied-access auditing |
| `backend/tests/unit/test_config.py`, `test_logging.py`, `test_i18n.py`, `test_rate_limit.py`, `test_schema.py` | Foundation tests |
| `infra/postgres/init.sh` | Passes role passwords to `init.sql` |
| `scripts/generate_env.py` | Creates local secrets |
| `scripts/smoke_stack.py` | Checks the running stack end to end with real tokens and a real database dump |
| `scripts/seed_demo.py` | Creates demo accounts and synthetic reports on the local stack |
| `docs/runbook_local_stack.md` | How to run everything |
| `docs/STITCH_PROMPTS.md` | Every frontend prompt, replacing §3 and §5 of `docs/frontend.md` |
| `docs/security/data_classification.md` | Every database column, and why it's stored as it is |
| `docs/clinical/lexicon_seeds.md` | Starting word lists for review |
| `.github/workflows/ci.yml` | CI, replacing the earlier stub |

## `docs/submission/` additions

| File | Purpose |
|---|---|
| `competition_requirements.md` | Official dates, FAQ answers and judging criteria |
| `data_sources.md` | Declaration of every data source |
| `maturity_statement.md` | What existed, and what was built during the challenge |
| `evidence/` | Screenshots of the challenge page |

## `backend/app/explain/templates/` (pattern)

`<scenario>.<lang>.<level>.j2`, 90 stubs. Languages: `en`, `ar`, `hi`. Levels: `simple`, `standard`, `detailed`.

| Scenario | Used for |
|---|---|
| `carrier_self` | Single carrier |
| `couple_shared_ar` | Couple sharing an AR finding |
| `couple_one_carrier_tested_negative` | One carrier, partner tested negative |
| `couple_one_carrier_untested` | One carrier, partner untested |
| `xl_carrier_female` | X-linked carrier female |
| `possible_affected` | Possibly affected, escalation message |
| `uncertain_vus` | VUS, no numbers |
| `consanguinity_background` | Related couple, background risk wording set by a clinician |
| `clinical_boundary` | Clinical question: boundary and booking offer |
| `distress_support` | Distress: verified contacts and human alert |

## `backend/app/kb/content/` (pattern)

`<condition>/<lang>_<level>.md`, 99 stubs.

| Condition folder | Topic |
|---|---|
| `general` | General carrier and inheritance basics |
| `beta_thal` | Beta-thalassaemia |
| `alpha_thal` | Alpha-thalassaemia |
| `sickle_cell` | Sickle-cell disease |
| `cah` | Congenital adrenal hyperplasia |
| `inherited_retinal` | Inherited retinal disorders |
| `pcd` | Primary ciliary dyskinesia |
| `sma` | Spinal muscular atrophy |
| `glaucoma` | Inherited glaucoma |
| `g6pd_def` | G6PD deficiency |
| `cystic_fibrosis` | Cystic fibrosis |
