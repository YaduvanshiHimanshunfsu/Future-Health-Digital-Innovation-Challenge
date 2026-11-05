# Threat Model

**Version 1, 5 Nov 2026.** Written for sub-phase 1.2 and updated as the build goes on.
**Status:** drafted by the team's AI assistant. **Not reviewed by a security specialist or clinician.** V1.2.5 needs a human reviewer's sign-off.

## Assets and actors

| Asset | Why it matters |
|---|---|
| Carrier findings | Permanent, and they also say something about relatives |
| Couple relationship and match results | Can affect marriage prospects |
| Pregnancy status, case reasons | Highly sensitive and time-critical |
| Chat text | People may disclose anything |
| Audit trail | The proof of who saw what |
| Encryption and HMAC keys | Compromise exposes everything above |

| Actor | Motive |
|---|---|
| Curious or controlling relative or partner | To learn someone's result |
| A family member using a shared device | Opportunistic |
| Other users of the system | To read others' records |
| Staff with legitimate access | Curiosity beyond their assigned cases |
| Outside attacker | Data theft |
| A person with database access | Reading data or altering history |

## STRIDE

"Built" means implemented and tested in Phase 1. "Planned" names the sub-phase.

| Threat | Example | Control | Status |
|---|---|---|---|
| **S**poofing | Forged token | RS256 only, required claims, issuer and audience checks, `kid` required | Built: `tests/api/test_auth.py` |
| **S**poofing | Algorithm confusion (`alg=none`, HS256 using the public key) | Algorithm checked before any key lookup, and pinned on decode | Built |
| **S**poofing | ID token used as an access token | `typ` must be `Bearer` | Built |
| **S**poofing | Fake lab posting results | Client credentials now; signed bundles later | Role built. Signatures aren't built: `lab_attestation` is an honest setting, and `demo` is refused in production |
| **T**ampering | Editing or deleting audit rows | HMAC chain over the columns, insert-only role, triggers | Built: `tests/unit/test_audit_chain.py` |
| **T**ampering | Cutting off the newest audit rows | Head hash compared with a copy kept elsewhere | Check built; storing the copy is planned, 6.3 |
| **T**ampering | Swapping ciphertext between rows | AES-GCM with the row bound as associated data | Built: `tests/unit/test_crypto.py` |
| **R**epudiation | Staff deny viewing a record | Every access audited in the same transaction | Trail built; wired to each route as routes arrive |
| **I**nformation disclosure | Reading another person's record | Personal routes take no ID, so the token decides whose data is read. Shared data must pass both the ledger and OpenFGA, and a refusal looks like nothing being there | Built: `tests/api/test_bola.py`, `test_consents.py`, `test_authz.py` |
| **I**nformation disclosure | A partner's private findings leaking through the match or chat | Partner-safe view holding only the intersection | Built, with a scan for a marker gene across responses, logs, audit rows and AI context: `test_matching.py` (C7) |
| **I**nformation disclosure | Health data in logs or errors | Scrubbing, exception type only, route templates, no input echo | Built: `tests/unit/test_logging.py` |
| **I**nformation disclosure | Stolen database | Sensitive fields encrypted; see [data classification](data_classification.md) | Built: a test and `scripts/smoke_stack.py` search a real `pg_dump` for gene names and IDs |
| **I**nformation disclosure | Personal data sent to an LLM | Only listed words and fields pass, and any failure means no call | Built: `tests/unit/test_redaction.py`. Chat arrives in Phase 4 (H6) |
| **D**enial of service | Huge request bodies | Declared and actual size limits | Built |
| **D**enial of service | Random `kid` values hammering Keycloak | Refresh cooldown | Built |
| **D**enial of service | Flooding sensitive actions | Redis limits that close if Redis is down | Built; applied to routes as they arrive |
| **D**enial of service | Slow queries | 5 s statement timeout | Built |
| **S**poofing | Claiming someone's results by typing their national ID | The ID comes only from a verified token. The request can't carry it, and Keycloak treats the field as admin-only | Built: `tests/unit/test_realm.py`, `tests/api/test_results.py`, `scripts/smoke_stack.py` |
| **T**ampering | A report ID reused for another person cancels the first person's result | Refused as `report_subject_conflict` | Built: `tests/api/test_ingestion.py` |
| **T**ampering | Testing a list of genes against a partner's results | The match takes no input, and a request carrying any is refused | Built: `test_matching.py` |
| **I**nformation disclosure | Looking someone up to learn whether they use the service | No lookup exists. The person receiving a share creates a single-use code and passes it on themselves | Built: `test_consents.py` |
| **R**epudiation | Emergency access used and never questioned | Needs a reason, ends after an hour, is flagged in the subject's log, and is reviewed by someone else | Built: `test_transparency.py` |
| **D**enial of service | An OpenFGA outage | Reads are refused, revoking says 503 and changes nothing, and saved grants wait in the outbox | Built, and tested by stopping the real service: `scripts/smoke_stack.py` |
| **E**levation of privilege | Calling a staff route | Role checks, denied attempts audited | Built |
| **E**levation of privilege | Setting `role` in a request body | Unknown fields refused | Built |
| **E**levation of privilege | API role altering the schema or history | Separate roles, no DDL rights | Built: `tests/unit/test_schema.py` |

## Threats specific to families

Ordinary security models miss these, and they matter most for this product.

| Threat | Example | Design response | Sub-phase |
|---|---|---|---|
| **Shared device** | A relative opens the app on a family phone | Tokens held server-side, idle logout after 15 minutes, no result details in notifications | 5.5 |
| **Partner pressure** | "Show me your result or else" | Sharing only from a person's own session, revocable at any time, and no record of a refusal shown to the partner (tested in `test_matching.py`). A coercion path reaches a human in Phase 4 | 3.2, 4.3 |
| **Elder or family pressure** | A parent demands access | Family education packs hold no personal data. No "family account" exists by design | 3.4 |
| **Inference from "yes"** | A person with one finding learns the gene from a "shared" result | Stated plainly before consent (S8) | 3.3 |
| **Inference from an invitation** | A relative guesses who sent an anonymous invite | Generic wording, and the sender can always choose not to send one | 3.4 |
| **Harm that falls unevenly** | Women's marriage prospects harmed by disclosure | Most private defaults, and harm monitoring by gender | 3.2, 5.4 |
| **Coerced consent** | Someone consents under pressure | Consent is revocable, with expiry on every share | 3.2 |
| **Duty to warn** | A relative is at high risk | Never automated. Goes to a human under local policy | 4.5 |

## Residual risks

Known and accepted for the prototype. These go in the limitations statement.

- **The server is trusted.** It holds the keys and can decrypt. Couple matching runs on the server, so it isn't a blind protocol.
- **A match can still be inferred from behaviour.** A partner who sees "not ready" knows the other hasn't agreed, though not whether they declined, haven't got to it, or withdrew.
- **Redaction has a known gap.** A name that's also an everyday word on a word list would survive. Arabic has no word list yet, so every Arabic word is masked. The Hindi list needs a native speaker's review.
- **Couples can't be dissolved yet.** Withdrawing consent stops the match, but the link between two people stays on record.
- **Public invitation pages are limited by client address.** Behind a proxy, that address needs configuring, or everyone shares one limit.
- **Relationships are visible to database administrators.** See [data classification](data_classification.md).
- **Keycloak runs in development mode** on an internal database, and there's no TLS between containers in the local stack.
- **One audit chain** serialises all audit writes. Fine for a pilot. At scale it should be split by day or tenant.
- **No third-party penetration test** has been done.
- **Lab reports aren't signature-checked.** An authenticated lab client is trusted, and the demo marks its reports `demo`.
- **The Vault key provider has only been tested against a simulated Vault.** The local stack uses a local key.
- **National IDs in the demo are set by an administrator.** A real deployment needs them from a verified identity provider, and each country pack needs its own decision on that.
