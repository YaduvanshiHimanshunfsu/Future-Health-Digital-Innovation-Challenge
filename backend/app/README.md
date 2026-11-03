# Application package

Hexagonal layout: API, domain services, repositories, adapters.

**Rules:** Domain logic must not import from the API layer.

**Status:** stubs only. No code until requested.

## Sub-folders

- `analytics/`
- `api/`
- `assessments/`
- `booking/`
- `centres/`
- `core/`
- `db/`
- `decision/`
- `explain/`
- `ingestion/`
- `kb/`
- `models/`
- `notifications/`
- `pathway/`
- `privacy/`
- `repositories/`
- `risk_engine/`
- `schemas/`
- `speech/`
- `triage/`
- `workers/`

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `main.py` | Application factory. | 1.4 | M12 |
