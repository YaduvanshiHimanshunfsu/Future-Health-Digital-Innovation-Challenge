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
| **S**poofing | Fake lab posting results | Client credentials now; signed bundles later | Role built; signatures planned, 2.3 |
| **T**ampering | Editing or deleting audit rows | HMAC chain over the columns, insert-only role, triggers | Built: `tests/unit/test_audit_chain.py` |
| **T**ampering | Cutting off the newest audit rows | Head hash compared with a copy kept elsewhere | Check built; storing the copy is planned, 6.3 |
| **T**ampering | Swapping ciphertext between rows | AES-GCM with the row bound as associated data | Planned, 2.1 |
| **R**epudiation | Staff deny viewing a record | Every access audited in the same transaction | Trail built; wired to each route as routes arrive |
| **I**nformation disclosure | Reading another person's record | Object-level checks, 404 on denial | Planned, 3.1 |
| **I**nformation disclosure | A partner's private findings leaking through the match or chat | Partner-safe view holding only the intersection | Planned, 2.4 and 3.3 (C7) |
| **I**nformation disclosure | Health data in logs or errors | Scrubbing, exception type only, route templates, no input echo | Built: `tests/unit/test_logging.py` |
| **I**nformation disclosure | Stolen database | Sensitive fields encrypted; see [data classification](data_classification.md) | Schema built; encryption planned, 2.1 |
| **I**nformation disclosure | Personal data sent to an LLM | Field allowlist and redaction that fails closed | Planned, 3.5 (H6) |
| **D**enial of service | Huge request bodies | Declared and actual size limits | Built |
| **D**enial of service | Random `kid` values hammering Keycloak | Refresh cooldown | Built |
| **D**enial of service | Flooding sensitive actions | Redis limits that close if Redis is down | Built; applied to routes as they arrive |
| **D**enial of service | Slow queries | 5 s statement timeout | Built |
| **E**levation of privilege | Calling a staff route | Role checks, denied attempts audited | Built |
| **E**levation of privilege | Setting `role` in a request body | Unknown fields refused | Built |
| **E**levation of privilege | API role altering the schema or history | Separate roles, no DDL rights | Built: `tests/unit/test_schema.py` |

## Threats specific to families

Ordinary security models miss these, and they matter most for this product.

| Threat | Example | Design response | Sub-phase |
|---|---|---|---|
| **Shared device** | A relative opens the app on a family phone | Tokens held server-side, idle logout after 15 minutes, no result details in notifications | 5.5 |
| **Partner pressure** | "Show me your result or else" | Sharing only from a person's own session, revocable at any time, and no record of a refusal shown to the partner. A coercion path reaches a human | 3.2, 4.3 |
| **Elder or family pressure** | A parent demands access | Family education packs hold no personal data. No "family account" exists by design | 3.4 |
| **Inference from "yes"** | A person with one finding learns the gene from a "shared" result | Stated plainly before consent (S8) | 3.3 |
| **Inference from an invitation** | A relative guesses who sent an anonymous invite | Generic wording, and the sender can always choose not to send one | 3.4 |
| **Harm that falls unevenly** | Women's marriage prospects harmed by disclosure | Most private defaults, and harm monitoring by gender | 3.2, 5.4 |
| **Coerced consent** | Someone consents under pressure | Consent is revocable, with expiry on every share | 3.2 |
| **Duty to warn** | A relative is at high risk | Never automated. Goes to a human under local policy | 4.5 |

## Residual risks

Known and accepted for the prototype. These go in the limitations statement.

- **The server is trusted.** It holds the keys and can decrypt. Couple matching runs on the server.
- **Relationships are visible to database administrators.** See [data classification](data_classification.md).
- **Keycloak runs in development mode** on an internal database, and there's no TLS between containers in the local stack.
- **One audit chain** serialises all audit writes. Fine for a pilot. At scale it should be split by day or tenant.
- **No third-party penetration test** has been done.
