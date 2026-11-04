# Phase 1: Foundation, Decisions and Compliance Baseline

**Status (5 Nov 2026):** 1.3 to 1.5 are built and tested. 1.1, 1.2 and 1.6 wait on the team. Evidence per check is in [CROSS_VERIFICATION.md](CROSS_VERIFICATION.md).

**Dates:** 5–6 Nov 2026 · **Build steps:** `backend.md` §9 steps 1–6 · **Requirements:** all (groundwork)

**Phase goal:** the entry is registered, scope and clinical rules are agreed, and an empty but secure system runs locally with a working audit log.

**Why first:** a wrong deadline, or an option that's unavailable in a given country, costs more the later it's found.

---

## 1.1 Competition gate and scope lock

**Goal:** confirm the entry is valid and the scope fits the team.

**Objectives**
- O1.1.1 Team registered before the 10 Nov deadline. Done, confirmed by the user on 5 Nov.
- O1.1.2 Rules and all FAQ answers read and recorded.
- O1.1.3 Scope tiers confirmed against actual team size.
- O1.1.4 Owners named for each phase.
- O1.1.5 The full requirements shared on registration are found and recorded.
- O1.1.6 Eligibility is confirmed: lead aged 18 or over, one team per person, and institution permission if needed.
- O1.1.7 Someone follows the Thursday live sessions.

**Work**
- FAQ answers were recorded on 5 Nov. Find the full requirements shared on registration, and read the rules page.
- Watch the Thursday live sessions (5, 12, 19 Nov), and ask open questions there.
- Record the submission format, permitted data, and IP terms.
- Confirm or change the scope tiers in [00_PHASE_OVERVIEW.md](00_PHASE_OVERVIEW.md#scope-tiers).
- Confirm which LLM and cloud credits are available.

**Files:** `docs/submission/competition_requirements.md`, `docs/submission/evidence/`, `brain.md`
**Issues to close:** S1, S2, S3, S11

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.1.1 | Registration confirmed | Confirmation email or portal screenshot |
| V1.1.2 | Every FAQ answer is copied into the requirements file | Second person compares with the portal |
| V1.1.3 | Dates in the requirements file match the live page | Dated screenshot |
| V1.1.4 | Scope tiers agreed | `brain.md` decision entry |
| V1.1.5 | An owner is named for each phase | Table in `brain.md` |
| V1.1.6 | Full requirements are recorded, and the plan is updated if they differ | Requirements file |
| V1.1.7 | Eligibility is confirmed for every team member | `brain.md` note |
| V1.1.8 | Notes from each live session are recorded | `brain.md` entries |

---

## 1.2 Clinical, legal and cultural baseline

**Goal:** correct the spec's clinical and legal assumptions before anything is built on them.

**Objectives**
- O1.2.1 A named clinician or counsellor is reviewing, or the gap is openly stated as a limitation.
- O1.2.2 The options list is correct for the Abu Dhabi reference pack.
- O1.2.3 Risk rules are reviewed against the issues list.
- O1.2.4 Duties under the human genome law are mapped to features.
- O1.2.5 Threat model version 1 exists.
- O1.2.6 India legal and options starting points are recorded, and labelled unreviewed.
- O1.2.7 How premarital couple results are actually delivered is understood.
- O1.2.8 Support contacts, the retention table and lexicon seeds are started.

**Work**
- Contact a counsellor through mentors, the university or LinkedIn.
- Decide how to handle donor, adoption or fostering, and prenatal diagnosis content.
- Ask how premarital couple results are actually delivered, to resolve S6.
- Get verified support contacts for the distress path.
- Seed the lexicon, including `hamil` handling and Gulf-dialect directive terms, with an Arabic speaker.
- Seed the Hindi lexicon with a Hindi speaker, looking for words with two meanings, as with `hamil`.
- Write STRIDE threat model v1.

**Files:** `docs/clinical/lexicon_seeds.md`, `docs/clinical/options_by_jurisdiction.md`, `docs/clinical/risk_rules_review.md`, `docs/clinical/support_contacts.md`, `docs/compliance/legal_baseline.md`, `docs/security/threat_model.md`
**Issues to close:** S4, S5, S6, S9, H4, H13, H19 (decisions; implementation comes later), C10

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.2.1 | Reviewer named, or "no clinical review" recorded under limitations | `brain.md` |
| V1.2.2 | Each option has a jurisdiction note and source | Options file, reviewer initials |
| V1.2.3 | Each genome-law article in review S4 maps to a feature or a stated limitation | Legal baseline table |
| V1.2.4 | Support contacts come from an official source | Link and date in file |
| V1.2.5 | Threat model covers shared-device, partner-pressure and elder-pressure cases | Reviewer sign-off |
| V1.2.6 | India starting points are recorded and labelled unreviewed | Legal baseline and options files |
| V1.2.7 | Each rule in the risk table is checked against the review's issues | `docs/clinical/risk_rules_review.md` |
| V1.2.8 | The answer on couple result delivery is recorded, and couple mode wording follows it | `brain.md` decision |
| V1.2.9 | A draft retention table exists per pack | Legal baseline |
| V1.2.10 | Lexicon seeds are reviewed by Arabic and Hindi speakers | Reviewers' names |

---

## 1.3 Repository, tooling and local stack

**Goal:** one command brings up all services on a clean machine.

**Objectives**
- O1.3.1 `docker compose up` gets all core services healthy.
- O1.3.2 Windows limits are handled.
- O1.3.3 Secret scanning and linting run before each commit.

**Work** (steps 1–2)
- Project config, lockfile, pre-commit, CI (with the H16 fixes).
- Compose with the H15 fixes: service hostnames, Redis credentials, worker and beat, consistent Keycloak issuer, a separate migration role.
- Make PSI an optional extra, and develop in Docker or WSL.

**Files:** `backend/pyproject.toml`, `backend/Dockerfile`, `backend/.env.example`, `infra/docker-compose.yml`, `infra/postgres/init.sql`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`
**Issues to close:** H15, H16, M2 (naming)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.3.1 | Fresh clone to all healthy, following only the README | Second person's run log, with time taken |
| V1.3.2 | API container can reach Postgres, Redis, Keycloak and OpenFGA | Health-check output |
| V1.3.3 | A test secret is blocked by gitleaks | Hook output |
| V1.3.4 | CI is green on an empty test | CI run link |
| V1.3.5 | Install succeeds on the team's Windows machines | Log in `brain.md` |

---

## 1.4 API skeleton and security core

**Goal:** a hardened API shell where every request is authenticated and logged safely.

**Objectives**
- O1.4.1 JWT verification is pinned to RS256 with required claims.
- O1.4.2 Security headers and a body limit are on all responses, including errors.
- O1.4.3 Logs and errors can't contain PHI.
- O1.4.4 Production settings refuse unsafe configuration.

**Work** (steps 3–4)
- App factory, config with production guards, middleware, PHI-safe logs, error handlers, rate limiter, i18n loader.

**Files:** `backend/app/main.py`, `backend/app/core/*`, `backend/app/api/deps.py`, `backend/app/api/v1/health.py`
**Issues to close:** M12

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.4.1 | Expired, tampered, `alg=none` and wrong-audience tokens all get 401 | `tests/api/test_auth.py` |
| V1.4.2 | Security headers appear on 200, 404, 422 and 500 | Test output |
| V1.4.3 | A log line with a national ID or phone number is scrubbed, using the pack's formats | Unit test |
| V1.4.4 | Validation errors don't echo input | Unit test |
| V1.4.5 | Production config refuses local KEK and wildcard origins | Unit test |
| V1.4.6 | `/docs` works in development and is off in production | Test |

---

## 1.5 Data model, migrations and audit chain

**Goal:** the full schema exists, and tampering with the audit log is detectable.

**Objectives**
- O1.5.1 Migrations cover all tables, including the `[NEW]` ones.
- O1.5.2 The app's database role can't change audit rows.
- O1.5.3 Chain verification detects edits.
- O1.5.4 Security events persist even when the action fails.

**Work** (steps 5–6)
- Models, schemas, first migration, separate owner and app roles.
- Audit append and verify, plus a separate transaction for denied attempts.
- Rename `case` to `care_case`.

**Files:** `backend/app/db/*`, `backend/app/models/*`, `backend/alembic/*`, `backend/app/privacy/audit.py`
**Issues to close:** H18, M2, M10, part of H11

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.5.1 | Upgrade and downgrade both run on an empty DB | Command output |
| V1.5.2 | `UPDATE` and `DELETE` on the audit table fail as the app role | `tests/unit/test_audit_chain.py` |
| V1.5.3 | An edited row is detected by `verify_chain` (with DB owner rights) | Same test |
| V1.5.4 | A denied request leaves an audit row after rollback | API test |
| V1.5.5 | Sensitive columns are encrypted or have a written reason | Reviewer checks the schema against H18 |
| V1.5.6 | The table is `care_case`, and role names match across docs and code | Schema review |
| V1.5.7 | During ingestion the audit row is written after network calls, so the lock isn't held across them | Test or code review |

---

## 1.6 Design system and frontend skeleton (parallel track)

**Goal:** an accessible design system, with screen designs for the main path.

**Objectives**
- O1.6.1 Colour tokens pass contrast rules.
- O1.6.2 A style-lock sheet exists.
- O1.6.3 T1 screens are designed.

**Work**
- Adjust tokens for contrast before generating screens.
- Generate the P20 component sheet first, then T1 screens from `frontend.md`, with copy fixes applied.

**Files:** `docs/STITCH_PROMPTS.md`, `frontend/design-export/`, `frontend/app/globals.css`, `frontend/tailwind.config.ts`
**Issues to close:** M5, M13, G8, parts of H13 and S8

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.6.1 | All text and background pairs reach 4.5:1 | Contrast table in the frontend README |
| V1.6.2 | "You are healthy", DoH and M42 logos, and confetti are absent | Reviewer checks screens |
| V1.6.3 | Arabic and Hindi screens reviewed by native speakers | Reviewers' names |
| V1.6.4 | The style-lock component sheet exists | Design export |
| V1.6.5 | T1 screens exist in the agreed variants, including Hindi | List checked against scope tiers |

---

## Phase 1 exit gate

- [x] Registered, confirmed by the user on 5 Nov
- [ ] Full requirements and rules recorded (1.1). FAQ is done
- [x] Options, legal baseline and threat model drafted (1.2), all still unreviewed
- [ ] A second person ran the stack from a clean clone (1.3). Clean rebuild works here
- [x] Auth tests pass (1.4)
- [x] Audit tamper test passes (1.5)
- [x] `brain.md` is up to date

**If behind:** the first two items are not optional. Reduce 1.6 to the component sheet plus 3 screens.
