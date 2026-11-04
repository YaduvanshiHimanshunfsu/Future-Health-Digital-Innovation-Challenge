# Running the Local Stack

Needs Docker Desktop, Python 3, and [uv](https://docs.astral.sh/uv/) for running tests. These commands work in Git Bash, PowerShell or a Linux shell.

## Start

```bash
python scripts/generate_env.py     # once only: creates infra/.env with random secrets
cd infra
docker compose up -d --build --wait
```

The first build took about 2.5 minutes here, and later clean starts about 70 seconds.

| Service | Address | Notes |
|---|---|---|
| API | http://localhost:8000 | `/docs` in development |
| Keycloak | http://localhost:8080 | Admin password is in `infra/.env` |
| OpenFGA | http://localhost:8081 | |
| Postgres | localhost:5432 | Three roles: `postgres`, `samvid_owner`, `samvid_app` |
| Redis | localhost:6379 | |

All ports bind to localhost only.

## Check it's working

```bash
docker compose ps
docker compose exec api python -m app.ops.check_services
```

The second command checks Postgres, Redis, Keycloak and OpenFGA from inside the API container, then fetches a real token and verifies it the way the API would.

## Run the tests

```bash
cd backend
uv sync
uv run pytest
uv run ruff check . && uv run mypy && uv run bandit -q -r app
```

Database tests start their own Postgres and Redis containers through Testcontainers, using the same `infra/postgres/init.sql` as the stack. Docker must be running.

## Add a database change

```bash
cd backend
MIGRATION_DATABASE_URL="postgresql+asyncpg://samvid_owner:PASSWORD@127.0.0.1:5432/samvid" \
  uv run alembic revision --autogenerate -m "describe the change"
```

Then add the new table to a grant list and classify its columns in [data_classification.md](security/data_classification.md). Tests fail until you do.

## Stop

```bash
docker compose down        # keeps data
docker compose down -v     # deletes data for a clean start
```

Deleting `infra/.env` without `-v` locks you out of the existing database, because the roles keep their old passwords.

## Pre-commit hooks

```bash
uvx pre-commit install
```

## Windows notes

- `openmined.psi` has no Windows wheels, so it's an optional extra. The default install works on Windows.
- `.gitattributes` keeps `*.sh` files on LF line endings, because a Windows line ending stops them starting inside a container.
