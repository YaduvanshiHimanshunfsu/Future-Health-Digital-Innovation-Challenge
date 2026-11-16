# Deploying to Vercel

**Read this first: Vercel alone cannot run Samvid.** The web app can, and the API can, but the API
needs four other services that Vercel does not host. Without them the site loads and every page
that needs data fails closed, which is the designed behaviour, not a bug you can configure away.

## What runs where

| Part | On Vercel? | Why |
|---|---|---|
| `frontend` (Next.js) | **Yes** | Ordinary Next.js app |
| `backend` (FastAPI) | **Yes**, as functions | Stateless request handling |
| PostgreSQL | No | Needs a hosted database. Neon or Supabase both work, and both speak the `postgresql+asyncpg://` URL the app expects |
| Redis | No | Needs a hosted Redis. Upstash works |
| Keycloak | No | A long-running Java server. Needs a small VM or container host |
| OpenFGA | No | A long-running server, same |
| The Celery worker and beat | No | Long-running processes. Vercel functions stop when the response is sent |

The worker applies authorisation changes and sends reminders. Without it, shares still work (the
API applies them inline) but reminders never go out.

**If a working live demo matters more than using Vercel,** run the existing Compose stack on one
small server: `docker compose -f infra/docker-compose.yml up -d`. That is one command and
everything works, including the parts above.

## `vercel.json`

Two services. Only the web app is public; the API is reached through a binding, so it is not
exposed to the internet:

- `frontend` is public at `/`. It owns `/api/auth/*` (sign-in) and `/api/proxy/*`, which is how the
  browser reaches the API without ever holding a token.
- `backend` is internal. The binding injects its URL as `API_URL`, which is the variable the three
  server-side callers already read.

Do not add a public `/api/(.*)` rewrite to the backend: it would collide with the web app's own
`/api/auth` and `/api/proxy`, and break sign-in.

## Environment variables

Set these in the Vercel project. `scripts/generate_env.py` writes the same names locally, so an
`infra/.env` from a local run is a working reference for the shapes.

**On the `backend` service**

| Variable | Example | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host/db` | The app's role, not the owner |
| `REDIS_URL` | `rediss://default:pass@host:6379/0` | |
| `OIDC_ISSUER` | `https://keycloak.example/realms/samvid` | What browsers are sent to |
| `OIDC_JWKS_URL` | `https://keycloak.example/realms/samvid/protocol/openid-connect/certs` | |
| `OIDC_AUDIENCE` | `samvid-api` | |
| `OPENFGA_API_URL` | `https://openfga.example` | |
| `OPENFGA_TOKEN` | | |
| `LOCAL_KEK_B64` or Vault | | Key encryption key. `KMS_PROVIDER=vault` for a real deployment |
| `AUDIT_HMAC_KEY`, `INVITE_HMAC_KEY`, `NATIONAL_ID_HMAC_KEY`, `ANALYTICS_HMAC_KEY` | | 32 random bytes, base64 |
| `ENV` | `prod` | Production refuses an unreviewed country pack, so Abu Dhabi has to be reviewed first |

**On the `frontend` service**

| Variable | Notes |
|---|---|
| `APP_ORIGIN` | The public URL of the deployment |
| `KEYCLOAK_PUBLIC_ISSUER`, `KEYCLOAK_INTERNAL_ISSUER` | Both the public URL when Keycloak is hosted outside |
| `KEYCLOAK_CLIENT_ID` | `samvid-web` |
| `SESSION_SECRET` | 32 random bytes, base64 |
| `SESSION_COOKIE_SECURE` | `true` over HTTPS |

`API_URL` is **not** set by hand: the binding in `vercel.json` injects it.

## Before the first deploy

1. Run the migrations against the hosted database: `alembic upgrade head` with
   `MIGRATION_DATABASE_URL` set to the owner role. Vercel does not run them.
2. Import `infra/keycloak/realm-samvid.json` into the hosted Keycloak, and set the redirect URI to
   the deployment's URL.
3. Load the OpenFGA model from `infra/openfga/model.fga`.
4. `ENV=prod` refuses a pack that no clinician has reviewed. Abu Dhabi is a reference pack today,
   so a production deploy fails until it is reviewed, on purpose. Use `ENV=staging` for a demo.

## Known limits

- `python -m app.ops.seed_counsellors` and `scripts/seed_demo.py` run against a reachable API, so
  demo data has to be seeded separately after the first deploy.
- The backend opens a database connection per function instance. Use a pooled connection string
  (Neon's pooler, Supabase's transaction pooler) or connections will run out.
