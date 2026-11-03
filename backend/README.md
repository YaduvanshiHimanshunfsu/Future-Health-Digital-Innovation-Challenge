# Backend

The FastAPI modular monolith: all logic, data and safety controls.

**Rules:** Start with `docs/backend.md` and the corrections in `docs/04`. Files are stubs until implementation is requested.

**Status:** stubs only. No code until requested.

## Sub-folders

- `alembic/`
- `app/`
- `synthetic/`
- `tests/`

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `.env.example` | Config template with no real secrets. | 1.3 | H15 |
| `Dockerfile` | API and worker container image. | 1.3 | H15 |
| `alembic.ini` | Alembic configuration. | 1.5 | H15 |
| `pyproject.toml` | Dependencies and tool config. | 1.3 | H15, H16 |
