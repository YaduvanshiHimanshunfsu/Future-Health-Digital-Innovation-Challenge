# Phase 1: Foundation, Decisions and Compliance Baseline

**Dates:** 3–5 Nov 2026 · **Build steps:** `backend.md` §9 steps 1–6 · **Requirements:** all (groundwork)

**Phase goal:** the entry is registered, scope and clinical rules are agreed, and an empty but secure system runs locally with a working audit log.

**Why first:** a wrong deadline, or an option that's unavailable in the UAE, costs more the later it's found.

---

## 1.1 Competition gate and scope lock

**Goal:** confirm the entry is valid and the scope fits the team.

**Objectives**
- O1.1.1 Team registered before the 10 Nov deadline.
- O1.1.2 Rules and all FAQ answers read and recorded.
- O1.1.3 Scope tiers confirmed against actual team size.
- O1.1.4 Owners named for each phase.

**Work**
- Register on Hack2skill and read the rules page and FAQ while logged in.
- Record the submission format, permitted data, and IP terms.
- Confirm or change the scope tiers in [00_PHASE_OVERVIEW.md](00_PHASE_OVERVIEW.md#scope-tiers).
- Confirm which LLM and cloud credits are available.

**Files:** `docs/submission/competition_requirements.md`, `brain.md`
**Issues to close:** S1, S2, S3

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.1.1 | Registration confirmed | Confirmation email or portal screenshot |
| V1.1.2 | Every FAQ answer is copied into the requirements file | Second person compares with the portal |
| V1.1.3 | Dates in the requirements file match the live page | Dated screenshot |
| V1.1.4 | Scope tiers agreed | `brain.md` decision entry |

---

## 1.2 Clinical, legal and cultural baseline

**Goal:** correct the spec's clinical and legal assumptions before anything is built on them.

**Objectives**
- O1.2.1 A named clinician or counsellor is reviewing, or the gap is openly stated as a limitation.
- O1.2.2 The options list is correct for Abu Dhabi.
- O1.2.3 Risk rules are reviewed against the issues list.
- O1.2.4 Duties under the human genome law are mapped to features.
- O1.2.5 Threat model version 1 exists.

**Work**
- Contact a counsellor through mentors, the university or LinkedIn.
- Decide how to handle donor, adoption or fostering, and prenatal diagnosis content.
- Ask how premarital couple results are actually delivered, to resolve S6.
- Get verified support contacts for the distress path.
- Seed the lexicon, including `حامل` handling and Gulf-dialect directive terms, with an Arabic speaker.
- Write STRIDE threat model v1.

**Files:** `docs/clinical/options_by_jurisdiction.md`, `docs/clinical/risk_rules_review.md`, `docs/clinical/support_contacts.md`, `docs/compliance/legal_baseline.md`, `docs/security/threat_model.md`
**Issues to close:** S4, S5, S6, H4, H13, H19 (decisions; implementation comes later)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.2.1 | Reviewer named, or "no clinical review" recorded under limitations | `brain.md` |
| V1.2.2 | Each option has a jurisdiction note and source | Options file, reviewer initials |
| V1.2.3 | Each genome-law article in review S4 maps to a feature or a stated limitation | Legal baseline table |
| V1.2.4 | Support contacts come from an official source | Link and date in file |
| V1.2.5 | Threat model covers shared-device, partner-pressure and elder-pressure cases | Reviewer sign-off |

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

**Files:** `backend/pyproject.toml`, `backend/Dockerfile`, `backend/.env.example`, `infra/docker-compose.yml`, `infra/postgres/init.sql`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml.stub`
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

**Work** (steps 3–4)
- App factory, config with production guards, middleware, PHI-safe logs, error handlers, rate limiter, i18n loader.

**Files:** `backend/app/main.py`, `backend/app/core/*`, `backend/app/api/deps.py`, `backend/app/api/v1/health.py`
**Issues to close:** M12

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.4.1 | Expired, tampered, `alg=none` and wrong-audience tokens all get 401 | `tests/api/test_auth.py` |
| V1.4.2 | Security headers appear on 200, 404, 422 and 500 | Test output |
| V1.4.3 | A log line with an Emirates ID or phone number is scrubbed | Unit test |
| V1.4.4 | Validation errors don't echo input | Unit test |
| V1.4.5 | Production config refuses local KEK and wildcard origins | Unit test |

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

**Files:** `frontend/design-export/`, `frontend/app/globals.css`, `frontend/tailwind.config.ts`
**Issues to close:** M5, M13, parts of H13 and S8

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V1.6.1 | All text and background pairs reach 4.5:1 | Contrast table in the frontend README |
| V1.6.2 | "You are healthy", DoH and M42 logos, and confetti are absent | Reviewer checks screens |
| V1.6.3 | Arabic screen reviewed by a native speaker | Reviewer's name |

---

## Phase 1 exit gate

- [ ] Registered, with rules recorded (1.1)
- [ ] Options, legal baseline and threat model written (1.2)
- [ ] A second person ran the stack from a clean clone (1.3)
- [ ] Auth tests pass (1.4)
- [ ] Audit tamper test passes (1.5)
- [ ] `brain.md` is up to date

**If behind:** the first two items are not optional. Reduce 1.6 to the component sheet plus 3 screens.
