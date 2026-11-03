# Schemas

API contracts.

**Rules:** Inputs reject unknown fields. Outputs list explicit fields.

**Status:** stubs only. No code until requested.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `analytics.py` | Metric contracts, with suppressed cells. | 5.4 |  |
| `assessments.py` | Assessment contracts. | 5.3 |  |
| `booking.py` | Booking and referral contracts. | 5.2 | H14 |
| `cases.py` | Case and queue contracts, with reasons. | 4.5 |  |
| `chat.py` | Chat contract. Returned fact IDs must be partner-safe. | 4.3 | C7 |
| `common.py` | Shared types plus StrictIn (extra=forbid) and Out bases. | 1.5 |  |
| `consent.py` | Consent contracts. | 3.2 |  |
| `couples.py` | Couple link, consent and match contracts. Match returns shared, none_shared or cannot_determine. | 3.3 | C2 |
| `invitations.py` | Invitation contracts. | 3.4 |  |
| `me.py` | Profile and preference contracts. | 2.3 | H14 |
| `options.py` | Options and values contracts. | 4.4 | H14 |
| `pathway.py` | Journey and pathway contracts. | 5.1 | H14 |
| `results.py` | My results and risk contracts. | 2.5 |  |
