# Privacy fabric

Encryption, audit, authorisation, consent, matching, invitations, redaction. Requirement R4.

**Rules:** Fail closed. One person's data never reaches another without consent.

**Status:** stubs only. No code until requested.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `audit.py` | Audit chain. | 1.5 | H11, M10 |
| `authz.py` | OpenFGA adapter. | 3.1 | H7, H11 |
| `break_glass.py` | Break-glass access. | 3.5 | H14 |
| `consent_service.py` | Consent use-cases. | 3.2 | H7, H8, H19 |
| `crypto.py` | Envelope encryption. | 2.1 | H18 |
| `invitations.py` | Relative invitations. | 3.4 | H17 |
| `kms.py` | Key providers. | 2.1 |  |
| `matching.py` | Couple matching. | 3.3 | C1, C2, C7, H3, S8 |
| `outbox.py` | Authorisation outbox. | 3.1 | H7 |
| `psi_adapter.py` | PSI protocol. | 3.3 | H15, S8 |
| `redaction.py` | PII redaction and LLM allowlist. | 3.5 | H6 |
| `right_not_to_know.py` | Right not to know. | 3.2 | S4, H8 |
