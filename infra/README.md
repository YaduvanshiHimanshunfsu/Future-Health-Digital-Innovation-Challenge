# Infrastructure

Docker Compose, OpenFGA model, Keycloak realm, Postgres bootstrap.

**Rules:** Ports stay on localhost. Secrets come from `.env`, never Git.

**Status:** stubs only. No code until requested.

## Sub-folders

- `keycloak/`
- `openfga/`
- `postgres/`

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `docker-compose.yml` | Local stack. | 1.3 | H15 |
