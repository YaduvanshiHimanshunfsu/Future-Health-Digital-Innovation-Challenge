# Models

SQLAlchemy tables.

**Rules:** Sensitive fields are encrypted or carry a written reason (H18).

**Status:** built and tested. Column decisions are in `docs/security/data_classification.md`.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `analytics.py` | De-identified events. | 1.5 | H11 |
| `appointment.py` | Counsellor appointments. | 5.2 | H14 |
| `assessment.py` | Quiz and instrument scores. | 1.5 | H11 |
| `audit.py` | Audit log. | 1.5 |  |
| `break_glass.py` | Break-glass events. | 3.5 | H14 |
| `case.py` | Care cases and pathway steps. | 1.5 | H10, H18, M2 |
| `case_note.py` | Counsellor notes. | 4.5 | H14 |
| `centre.py` | Screening and counselling centres. | 5.2 | H14 |
| `consent.py` | Consent ledger. | 1.5 | H8, H19 |
| `conversation.py` | Chat history. | 1.5 | H11, H19 |
| `couple.py` | Couples. | 1.5 | H8, H18 |
| `genetic.py` | Reports and carrier findings. | 1.5 | H18, M8 |
| `invitation.py` | Relative invitations. | 1.5 | H17 |
| `kb.py` | Knowledge-base chunks. | 1.5 | M7 |
| `outbox.py` | Authorisation outbox. | 3.1 | H7 |
| `person.py` | Person table. | 1.5 | H11, H14, H18 |
| `referral.py` | Referrals. | 5.2 | H14 |
| `values_note.py` | Values reflection answers. | 4.4 | H14 |
