import type { Session } from "./session";

const CLIENT_ID = () => process.env.KEYCLOAK_CLIENT_ID ?? "samvid-web";
const publicIssuer = () => required("KEYCLOAK_PUBLIC_ISSUER");
const internalIssuer = () => process.env.KEYCLOAK_INTERNAL_ISSUER ?? publicIssuer();
export const appOrigin = () => required("APP_ORIGIN");
const redirectUri = () => `${appOrigin()}/api/auth/callback`;

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is not set`);
  return value;
}

function randomText(bytes: number): string {
  const values = crypto.getRandomValues(new Uint8Array(bytes));
  let text = "";
  for (const value of values) text += String.fromCharCode(value);
  return btoa(text).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export type PendingLogin = { state: string; verifier: string; returnTo: string; pack: string | null };

export async function beginLogin(returnTo: string, pack: string | null) {
  const verifier = randomText(48);
  const state = randomText(16);
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  let text = "";
  for (const value of new Uint8Array(digest)) text += String.fromCharCode(value);
  const challenge = btoa(text).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const query = new URLSearchParams({
    client_id: CLIENT_ID(),
    response_type: "code",
    scope: "openid",
    redirect_uri: redirectUri(),
    code_challenge: challenge,
    code_challenge_method: "S256",
    state,
  });
  const pending: PendingLogin = { state, verifier, returnTo, pack };
  return { url: `${publicIssuer()}/protocol/openid-connect/auth?${query}`, pending };
}

function toSession(tokens: { access_token: string; refresh_token: string; expires_in: number }): Session {
  return {
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    expiresAt: Math.floor(Date.now() / 1000) + tokens.expires_in,
  };
}

async function tokenRequest(body: Record<string, string>): Promise<Session | null> {
  try {
    const response = await fetch(`${internalIssuer()}/protocol/openid-connect/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ client_id: CLIENT_ID(), ...body }),
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    return response.ok ? toSession(await response.json()) : null;
  } catch {
    return null;
  }
}

export function exchangeCode(code: string, verifier: string) {
  return tokenRequest({
    grant_type: "authorization_code",
    code,
    redirect_uri: redirectUri(),
    code_verifier: verifier,
  });
}

export function refresh(refreshToken: string) {
  return tokenRequest({ grant_type: "refresh_token", refresh_token: refreshToken });
}

/** Ends the session at Keycloak too, so the next sign-in on a shared device asks for a password. */
export async function endSession(refreshToken: string): Promise<void> {
  try {
    await fetch(`${internalIssuer()}/protocol/openid-connect/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ client_id: CLIENT_ID(), refresh_token: refreshToken }),
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
  } catch {
    // The local cookie still goes, which is what protects this device.
  }
}

/** Only a path on this site, never another site, so a crafted link can't redirect someone away. */
export function safeReturnPath(value: string | null, fallback: string): string {
  if (!value || !/^\/[a-zA-Z0-9/_-]*$/.test(value) || value.startsWith("//")) return fallback;
  return value;
}
