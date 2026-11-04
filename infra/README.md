# Infrastructure

Docker Compose, OpenFGA model, Keycloak realm, Postgres bootstrap.

**Rules:** Ports stay on localhost. Secrets come from `.env`, never Git.

**Status:** built and running. See `docs/runbook_local_stack.md`. The OpenFGA model arrives in sub-phase 3.1.

## Sub-folders

- `keycloak/`
- `openfga/`
- `postgres/`

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `docker-compose.yml` | Local stack. | 1.3 | H15 |
