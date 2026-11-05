# Frontend libraries

| Folder | What it holds |
|---|---|
| `api/` | `server.ts` for server components, `client.ts` for the browser, generated `schema.ts`, and `types.ts`. Run `npm run api:types` after a backend change |
| `auth/` | Sign-in with authorisation code and PKCE, and the encrypted session cookie |
| `i18n/` | Locales and translation |
| `risk/` | Turns a fact from the API into words. Numbers only ever come from the API |

**Tokens stay on the server.** Browser code calls `/api/proxy/*`, which adds the token, so a script in the page can't read one.
