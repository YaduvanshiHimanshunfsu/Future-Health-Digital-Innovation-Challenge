# Security checklist

**Sub-phase:** 6.3. **Last updated:** 10 Nov 2026, against the code at that date.

Each row has evidence (a test, a scan or a script) or a written reason. "Built" means a test proves it; "Partly" says what's missing. Scanner outputs are saved in [`scans/`](scans/).

## OWASP API Security Top 10 (2023)

| Risk | Control in Samvid | Evidence | Status |
|---|---|---|---|
| API1 Broken object level authorisation | Personal routes take no ID: the token decides whose data is read. Shared data needs both a live consent and an OpenFGA check. Cases need an "assigned" tuple. A refusal looks like "not found" and is audited | `tests/api/test_bola.py` walks every route; `test_consents.py`, `test_authz.py`, `test_pathway.py`, `test_booking.py` | Built |
| API2 Broken authentication | RS256 only, algorithm pinned before key lookup, issuer, audience and `typ` checked, required claims, JWKS refresh cooldown. Tokens stay on the web server in an encrypted HttpOnly cookie | `tests/api/test_auth.py`; `demo_journey.spec.ts` (no tokens in browser storage) | Built |
| API3 Broken object property level authorisation | Every input model refuses unknown fields; every output model lists its fields; the partner view holds only the shared intersection | `extra="forbid"` on every `*In` schema; `test_matching.py` marker scan | Built |
| API4 Unrestricted resource consumption | Body size limits (declared and actual), Redis rate limits that close if Redis is down, 5 s statement timeout, query string limit at the proxy, model deadlines | `tests/unit/test_rate_limit.py`, middleware tests, `scripts/load_smoke.py` | Built |
| API5 Broken function level authorisation | Role checks on every staff route, audited when denied; a role in a request body is refused | `test_bola.py`, `test_cases.py` (people and physicians can't use the queue), `test_analytics.py` | Built |
| API6 Unrestricted access to sensitive business flows | Booking is one conditional update (no double booking); invitations are single-use with hashed tokens; receive codes replace lookups, so nobody can learn whether someone uses the service | `test_booking.py`, `test_invitations.py`, `test_consents.py` | Built |
| API7 Server-side request forgery | The API calls only fixed, configured hosts (Keycloak, OpenFGA, model providers); no route takes a URL to fetch | Code review: `app/explain/providers.py`, `app/privacy/authz.py`, `app/core/security.py` | Built |
| API8 Security misconfiguration | Production refuses a local key, demo attestation, wildcard hosts, plain-HTTP identity, and an unapproved hosted model. Containers are read-only, run as an unprivileged user, drop all capabilities. CSP with nonces, no framing, no referrer | `tests/unit/test_config.py`, `infra/docker-compose.yml`, `demo_journey.spec.ts` (CSP) | Built |
| API9 Improper inventory management | The OpenAPI schema is the inventory; the BOLA test fails on any route it doesn't know; docs are off in production | `test_bola.py` (`EXPECTED` and `PUBLIC` lists) | Built |
| API10 Unsafe consumption of APIs | Model output is never trusted: validated, rendered as plain text, figures filled by the engine. Lab reports are FHIR-validated; OpenFGA failure means deny | `test_pipeline.py`, `phase4.spec.ts` (markup renders as text), `test_ingestion.py`, `test_authz.py` | Built |

## OWASP Top 10 for LLM Applications (2025)

| Risk | Control in Samvid | Evidence | Status |
|---|---|---|---|
| LLM01 Prompt injection | The model has no tools and no data access; its draft is validated and replaced by the reviewed template on any rule break; its route opinion can only escalate | `test_pipeline.py`, `test_providers.py`, `answers_eval_*.md` (red-team set) | Built. Rules-based routing still misses some phrasing: see "Open" below |
| LLM02 Sensitive information disclosure | Allow-list redaction (unknown words masked), only listed fact fields, no figures sent; one person's facts never in another's context | `test_redaction.py`, `test_matching.py`, `test_providers.py` (model never sees a figure) | Built |
| LLM03 Supply chain | Model called over plain HTTPS or locally; no model weights in the image; dependencies audited | `scans/pip_audit.txt`, `scans/npm_audit.txt`, `scans/trivy_*.txt` | Built |
| LLM04 Data and model poisoning | No training or fine-tuning; the knowledge base is versioned files refused at load if any wording rule fails | `tests/unit/test_kb.py` | Built |
| LLM05 Improper output handling | Plain text only, no markup or links; figures only from `{fact:ID}` placeholders filled by code | `phase4.spec.ts`, `test_validators.py` | Built |
| LLM06 Excessive agency | The model can't act: no tools, no database transaction open during a call | `test_no_transaction_is_open_while_the_answer_is_drafted` | Built |
| LLM07 System prompt leakage | The prompt holds no secrets; the evaluation checks answers never repeat it | `answers_eval_*.md` (red-team item r-*-12) | Built |
| LLM08 Vector and embedding weaknesses | No embeddings: keyword retrieval over reviewed passages in the person's language and level only | `tests/unit/test_kb.py` | Not applicable by design |
| LLM09 Misinformation | Numbers from the deterministic engine only; uncertain means no number; validators block certainty and directive wording | `tests/unit/test_risk_engine.py`, `test_validators.py`, `answers_eval_*.md` | Built. Content still awaits clinical review |
| LLM10 Unbounded consumption | Per-call timeouts, a 20 s answer deadline, 20 chat messages a minute per person, 1000-character questions | `test_chat.py`, `app/explain/graph.py` | Built |

## Scanner results (10 Nov 2026)

| Scanner | Scope | Result | Output |
|---|---|---|---|
| gitleaks 8.21.2 | Full git history (7 commits) and every source folder of the working tree | No leaks | `scans/gitleaks_history.json` |
| Trivy 0.58.1 | Backend and web images, HIGH and CRITICAL with a fix available | 0 and 0, after two fixes: system updates in the backend image, and removing npm and yarn (unused at run time) from the web image, which held all 10 web findings | `scans/trivy_samvid-backend.txt`, `scans/trivy_samvid-web.txt` |
| bandit | `backend/app` | 0 issues | `scans/bandit.txt` |
| pip-audit | Backend dependencies | No known vulnerabilities | `scans/pip_audit.txt` |
| npm audit | Frontend dependencies | 0 vulnerabilities | `scans/npm_audit.txt` |
| ruff and mypy (strict) | Backend and scripts | Clean | CI and local runs |
| semgrep | Not run | Its container image wasn't pulled in time. bandit and ruff's security rules cover the Python side | Gap |

## Manual and scripted tests

| Test | How | Result |
|---|---|---|
| BOLA, token misuse, invitations | Automated in the API suites above, plus `scripts/smoke_stack.py` on the real stack (65 checks, including a stranger reading another person's data and an ID lock) | Pass |
| Personal data in logs (V6.3.3) | `scripts/scan_logs.py` after the full browser suite: IDs, 11 gene symbols, persona names, tokens and emails across every service | **Nothing found** in 12,875 lines (`scans/log_scan.txt`) |
| Load (V6.3.4) | `scripts/load_smoke.py`: 400 requests on 10 non-AI routes, 10 at a time | **p95 106 ms**, 0 errors, from inside the Docker network. Through Docker Desktop's forwarded port on Windows: p95 482 ms, the port proxy being the limit (`scans/load_smoke.txt`) |
| OpenFGA outage | The smoke script stops the real service: reads refused, revoking says 503, the worker recovers | Pass |

## Open

- **Router recall on unfamiliar phrasing** (V4.3.3): rules plus a local model still send some questions meant for a person to the automatic answer. Measured and listed in `docs/evaluation/`. Every such answer is still validated, so the risk is a missed hand-off, not unsafe text.
- **semgrep** not run.
- **No penetration test by anyone outside the team.**
