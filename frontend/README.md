# Frontend

Next.js 15 app, built from the team's Google Stitch design ("Ceramic Chromatic"). See `design-export/README.md` for how each Stitch screen maps to a page, and what changed.

**Status:** the screens for Phases 1 to 3 are built and connected to the real backend. Screens for later phases say which sub-phase builds them, and show nothing simulated.

## Run it

With the Compose stack, it's the `web` service on http://localhost:3000. To work on it directly:

```bash
cp .env.example .env.local     # then set SESSION_SECRET to WEB_SESSION_SECRET from infra/.env
npm install
npm run build && npm start
```

Demo accounts come from `scripts/seed_demo.py`. Their password is `DEMO_PASSWORD` in `infra/.env`.

## How it's built

| Concern | How |
|---|---|
| Sign-in | Authorisation code with PKCE against Keycloak, handled by this app's server (`app/api/auth/`). There's no NextAuth |
| Tokens | Kept in an encrypted, HttpOnly cookie. Browser code never sees one, and calls go through `/api/proxy/*`, which adds the token |
| Proxy | Allows a fixed list of API paths, refuses unsafe path segments, and refuses changes sent from another site |
| Security headers | A per-request nonce CSP with `strict-dynamic`, no framing, `no-referrer` for invitation links, and `no-store` on signed-in pages |
| Words | Every word comes from `messages/`. `tests/unit/copy.test.mjs` enforces the wording rules, Hindi completeness, and no Arabic script |
| Numbers | Only from the API. A test fails if a component does arithmetic on a chance |
| Languages | English and Hindi. Arabic has a right-to-left layout with English words until its text is approved and reviewed |
| Types | `lib/api/schema.ts` is generated from the API with `npm run api:types` |

## Tests

| Command | What it checks |
|---|---|
| `npm run typecheck` | TypeScript, strict |
| `npm run test:copy` | Wording rules, Hindi, no Arabic script, no chance arithmetic |
| `npm run test:e2e` | Real browser against the real stack: every journey, accessibility with axe, security of the session and proxy |

## Colour contrast

| Text | On | Ratio |
|---|---|---|
| Ink `#1F2433` | Porcelain `#FBF8F3` | 15.1:1 |
| Slate `#5B6275` | Porcelain `#FBF8F3` | 5.8:1 |
| White | Lapis `#2F5BEA` | 5.2:1 |
| Ink `#1F2433` | Turquoise `#14A89B` | 5.6:1 |

axe checks every page in every language at desktop and phone width, so this table is a summary and not the only check.
