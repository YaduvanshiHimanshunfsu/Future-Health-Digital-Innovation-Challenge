# Technical documentation

**Samvid** explains genetic carrier screening results privately, in plain words, in English and Arabic (right to left; the Arabic is drafted and unreviewed) (pending), and hands anything clinical or upsetting to a person. It is a working prototype on synthetic data. Every claim below points to code or a test; anything not built says so.

## Overview

| Who | What they do in Samvid |
|---|---|
| A person with a result | Reads their result with pictures from the risk engine, asks questions, checks their understanding, shares or stops sharing, runs a couple check with a partner, books a counsellor, or steps back |
| A counsellor | Takes cases from a queue ordered by urgency, sees a "verify before use" summary, offers appointment times, moves the case on, and refers onward as a FHIR record |
| A programme administrator | Sees aggregate metrics and equity gaps, with small groups withheld |
| An auditor | Reviews emergency access |

## Architecture

All of it runs from one command (`python Run_Samvid.py`) as containers on one machine.

| Service | Built with | Role |
|---|---|---|
| `web` | Next.js 15, React 19, TypeScript, Tailwind | Pages, plus a backend-for-frontend: sign-in, an encrypted session cookie, and a proxy that adds the token. No token ever reaches browser code |
| `api` | Python 3.12, FastAPI, SQLAlchemy 2 (async), Pydantic 2 | Every rule: risk engine, consent, matching, chat pipeline, pathway, booking, referrals, analytics |
| `worker`, `beat` | Celery | Applies authorisation changes (outbox), reconciles OpenFGA, scans for overdue care steps every 5 minutes |
| `postgres` | PostgreSQL 16 | Data. Sensitive fields are envelope-encrypted per row; the audit log is an HMAC chain with an insert-only role |
| `redis` | Redis 7 | Rate limits, single-use codes |
| `keycloak` | Keycloak 26 | Sign-in (OIDC with PKCE), roles |
| `openfga` | OpenFGA 1.8 | Relationship-based access: who may see what, and until when |
| Models (optional) | Gemini API, or Ollama on the same machine | Drafts explanations and double-checks routing. Off by default: reviewed templates answer instead |

Country rules live in **country packs** (`backend/packs/`): the gene panel, carrier frequencies, options, support contacts, centres, time targets and reporting groups. Abu Dhabi is the one pack the prototype ships, and `_template/` is what a second country starts from. Abu Dhabi is not clinically reviewed, and the app says so on screen.

## Data flows

1. **A lab report arrives** (`POST /v1/reports:ingest`, lab client credentials): FHIR-validated, the national ID turned into a keyed hash, findings encrypted, and a care case opened at the right priority. Nothing is shown until the person has accepted the service terms.
2. **The person reads their result**: the deterministic risk engine (`app/risk_engine/`) turns findings into facts with exact fractions, and the visuals (icon array, Punnett square, X-linked diagram) are drawn from those facts. An uncertain finding produces words and no number.
3. **They ask a question** (`POST /v1/chat`): the question is routed by rules, double-checked by a model if one is configured (it can only escalate), and then either answered or handed to a person. An answer is a reviewed template or a model draft that passed every validator, with figures filled in by code at the end.
4. **They share** (`/v1/consents`): a share needs both a live consent row and an OpenFGA tuple; either one alone can refuse. Stopping a share removes access first, and fails safe if OpenFGA is down.
5. **A couple check** (`/v1/couples`): both must agree; each partner sees only what they both share, at the more private of the two chosen levels.
6. **Care**: every step is a row in `pathway_step`. Booking takes a slot in one conditional update. Referrals are FHIR R5 `ServiceRequest` and `Task` records with a pseudonymous subject.
7. **Metrics** (`/v1/analytics/overview`): computed from those rows, with groups under 10 people withheld, plus whatever group would let a withheld one be worked out.

## Safety model

- **Numbers come from code.** The engine is pure and deterministic, and 100% branch-covered. A model never sees a figure: it gets `{fact:ID}` placeholders, and validators block any number it writes.
- **Uncertain means no number**, and a person follows up.
- **"No data" is not "no risk."** No report, or nothing found, is never shown as a negative.
- **Never direct a decision.** Validators catch directive wording in English and Arabic; options are shown with equal weight and no ranking.
- **Clinical questions and distress go to people.** Rules route first, a model can only escalate, and anything the rules can't place goes to a person with the support line shown.
- **Fail closed.** Any authorisation, redaction or validation failure means deny or the reviewed template.

Measured results: [docs/evaluation/safety_and_accuracy_report.md](../evaluation/safety_and_accuracy_report.md).

## Privacy model

- Personal routes take no ID: the token decides whose data is read.
- Shares, couple checks and invitations are consent-first; invitations are single-use and name nobody.
- A person can choose not to know their results (Decree-Law 49/2023, Art. 9(2)).
- An access log shows the person who saw their data. Emergency access needs a reason, ends after an hour, is flagged to the person, and is reviewed by someone else.
- What a model may receive is an allow-list: listed words, listed fact fields, approved passages.
- Full classification of every column: [docs/security/data_classification.md](../security/data_classification.md). Threats and controls: [threat_model.md](../security/threat_model.md), [security_checklist.md](../security/security_checklist.md).

## Deployment

**Today:** Docker Compose on one machine, for demonstration.

**For a real deployment**, the settings already refuse to start in production without: a Vault-held key instead of a local one, OpenFGA over HTTPS with a token, HTTPS identity endpoints, real lab attestation, no wildcard hosts, and approval before any hosted model. Still to do: hosting in the UAE region (Federal Law 2/2019 requires health data to stay in the country), managed Postgres with backups, retention aligned with Art. 20 of that law, and a licensed partner for storing genetic data (Decree-Law 49/2023, Art. 28).

## How to run

```bash
python Run_Samvid.py            # everything, with demo accounts and live activity in the terminal
python Run_Samvid.py --status   # what's running, and which AI model will answer
python Run_Samvid.py --check    # plus the 65-check smoke test on the real stack
```

Needs Docker Desktop and `uv`. Optional: Ollama with `qwen2.5:3b`, and `GEMINI_API_KEY`. Full steps: [docs/runbook_local_stack.md](../runbook_local_stack.md).

## Tests

| Suite | Size | What it shows |
|---|---|---|
| Backend (pytest) | 847 tests, 86% coverage | Unit, property and API tests against real Postgres, Redis and OpenFGA containers |
| Browser (Playwright) | 55 tests | Every journey on the containerised app, axe accessibility checks, tokens absent from the browser |
| Smoke (`scripts/smoke_stack.py`) | 65 checks | The real stack, including a real OpenFGA outage and a database dump scan |
| Evaluations (`scripts/eval_*.py`) | 143 router and 96 answer items | Per language, with every failure listed |
