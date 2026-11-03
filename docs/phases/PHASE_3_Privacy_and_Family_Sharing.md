# Phase 3: Privacy Fabric, Consent and Family Sharing

**Dates:** 9–11 Nov 2026 · **Build steps:** `backend.md` §9 steps 12–16 · **Requirements:** R4 (main), R6 (privacy metrics)

**Phase goal:** people control exactly who sees what, and tests prove that nothing leaks, including through the couple match.

**Why here:** genetic data is shared across families by nature, and this is the part of the pitch judges are most likely to probe.

---

## 3.1 Identity, roles and relationship authorisation

**Goal:** every object access is checked, and any failure means denial.

**Objectives**
- O3.1.1 All roles are defined, including the lab service.
- O3.1.2 Relationships are modelled in OpenFGA.
- O3.1.3 Outage means deny.
- O3.1.4 Writes are idempotent and consistent with the database.

**Work** (step 12): Keycloak realm with an audience mapper, OpenFGA model and bootstrap, adapter that fails closed, outbox or reconcile for tuple writes.

**Files:** `infra/keycloak/realm-silah.json`, `infra/openfga/model.fga`, `backend/app/privacy/authz.py`, `backend/app/privacy/outbox.py`, `scripts/bootstrap_openfga.md`
**Issues to close:** H7, M2 (roles)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V3.1.1 | With OpenFGA stopped, protected routes deny | Test with the service down |
| V3.1.2 | Denied access gets 404 and an audit event | API test |
| V3.1.3 | User calling a counsellor route gets 403 | Role test |
| V3.1.4 | `role` in a body is rejected | Mass-assignment test |
| V3.1.5 | Forcing a commit failure leaves no orphan access | Fault-injection test |

---

## 3.2 Consent ledger

**Goal:** all sharing lives in one ledger, is scoped and time-limited, and can be revoked at once.

**Objectives**
- O3.2.1 Grant, list, revoke and expiry all work.
- O3.2.2 Revocation removes access first.
- O3.2.3 Grantees have a real read path, limited to scope.
- O3.2.4 Service consent is captured at onboarding, and the right not to know is supported.

**Work** (step 13)
- Ledger including couple-match consent.
- Expiry via OpenFGA conditions.
- Shared-report endpoint.
- Onboarding consent and AI disclosure.
- Right-not-to-know flow, shaped by Art. 9(2)–(3) and counsellor input.

**Files:** `backend/app/privacy/consent_service.py`, `backend/app/api/v1/consents.py`, `backend/app/api/v1/shared.py`, `backend/app/models/consent.py`
**Issues to close:** H8, H19 (purpose codes)

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V3.2.1 | After revoke, the grantee gets 404 on the next request | `tests/api/test_consents.py` |
| V3.2.2 | Revocation latency is under 1 s | Timed test, emitted as a metric |
| V3.2.3 | Revoke during OpenFGA outage gives 503 and the consent stays visibly active | Test |
| V3.2.4 | Expired consent denies access without a job running | Test with the clock moved |
| V3.2.5 | Summary-scope grantee can't see full detail | Test |
| V3.2.6 | Two grants to one person work, and revoking one behaves as documented | Test |
| V3.2.7 | No genetic data is shown before service consent | Test |

---

## 3.3 Couple linking and minimal-disclosure match

**Goal:** a couple learns only what both agreed to, and a positive result can't be missed or faked.

**Objectives**
- O3.3.1 Three outcomes: shared, none shared, can't determine.
- O3.3.2 The most private choice wins.
- O3.3.3 Non-shared findings never leave the server, in any field.
- O3.3.4 Inputs come only from attested records.
- O3.3.5 Consent can be withdrawn.
- O3.3.6 Both partners get care, not just the person who ran the match.

**Work** (step 14)
- Couple invite and accept, consent, match.
- Case for both partners after a positive match, subject to the S6 outcome.
- Clear user text explaining what "yes" reveals.
- PSI as an optional T3 extra, described accurately.

**Files:** `backend/app/privacy/matching.py`, `backend/app/privacy/psi_adapter.py`, `backend/app/api/v1/couples.py`, `frontend/app/[locale]/(app)/app/partner/`
**Issues to close:** **C1, C2, C7**, S6, S8

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V3.3.1 | Known at-risk couple returns "shared" | `tests/api/test_matching.py` (this fails in the original spec) |
| V3.3.2 | Partner with no report returns "can't determine", not "none" | Test |
| V3.3.3 | `yes_no` mode returns no gene names | Test |
| V3.3.4 | A partner-only gene appears in **no** response, chat fact ID, log or LLM context | Scan-style test using a marker gene |
| V3.3.5 | Client-supplied gene lists are rejected | Test |
| V3.3.6 | Withdrawn consent blocks the next match | Test |
| V3.3.7 | Both partners can see the follow-up | Test |
| V3.3.8 | Pitch wording matches what the code does | Reviewer checks the deck against S8 |

---

## 3.4 Family invitations

**Goal:** a person can encourage relatives to get screened without identifying themselves or their result.

**Objectives**
- O3.4.1 Tokens are single-use, hashed and expiring.
- O3.4.2 Link previews don't burn tokens.
- O3.4.3 The recipient's page reveals nothing about the sender by default.

**Work** (step 15)
- Create invitation, `GET` shows page, `POST` redeems.
- Landing page and generic content.
- Wording checked for eligibility claims.

**Files:** `backend/app/privacy/invitations.py`, `backend/app/api/v1/invitations.py`, `frontend/app/[locale]/i/[token]/`
**Issues to close:** H17, H13 ("free" claim), part of H14

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V3.4.1 | Multiple `GET`s don't redeem | `tests/api/test_invitations.py` |
| V3.4.2 | Reuse, expiry and unknown tokens return identical responses | Test |
| V3.4.3 | Only the hash is stored | DB inspection |
| V3.4.4 | Sixth invite in a day gets 429 | Test |
| V3.4.5 | Response contains no sender data unless opted in | Test |

---

## 3.5 Transparency: access log, break-glass and redaction

**Goal:** users can see who accessed their data, exceptional access is visible, and PII doesn't reach the LLM.

**Objectives**
- O3.5.1 The access log includes counsellor and partner actions, in plain language.
- O3.5.2 Break-glass needs a reason and raises a flag.
- O3.5.3 Redaction fails closed and covers Arabic.

**Work** (step 16)
- Access log that joins case and couple resources to the person.
- Break-glass endpoint and review list.
- Redaction with Arabic handling, and the LLM allowlist.

**Files:** `backend/app/api/v1/access_log.py`, `backend/app/privacy/break_glass.py`, `backend/app/privacy/redaction.py`, `frontend/app/[locale]/(app)/app/privacy/`
**Issues to close:** **H6**, part of H11, part of H14

**Cross-verification**
| ID | Check | Evidence |
|---|---|---|
| V3.5.1 | A counsellor viewing a case appears in the subject's log | API test |
| V3.5.2 | Break-glass without a reason is refused; with one, it's flagged | Test |
| V3.5.3 | If the redaction engine fails, no LLM call happens | Fault-injection test |
| V3.5.4 | Arabic and English PII samples are redacted, including Arabic names | Parametrised test; a native speaker writes the samples |
| V3.5.5 | The LLM context has only allowlisted fields | Unit test with a recording stub |

---

## Phase 3 exit gate

- [ ] Privacy test suite green, including V3.3.4
- [ ] Revoke-then-deny shown on screen
- [ ] At-risk couple flow works from consent to result
- [ ] Threat model updated with what was learned
- [ ] `brain.md` is up to date

**If behind:** cut break-glass UI and invitation polish. Don't cut 3.2 or 3.3.
