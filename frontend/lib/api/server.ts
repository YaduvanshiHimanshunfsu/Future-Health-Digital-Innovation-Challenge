import "server-only";
import { cookies, headers } from "next/headers";
import { readSession } from "@/lib/auth/session";

const API_URL = () => process.env.API_URL ?? "http://127.0.0.1:8000";

export type ApiResult<T> = { ok: true; status: number; data: T } | { ok: false; status: number; code: string };

/** For server components. The token never leaves this server. */
export async function api<T>(path: string): Promise<ApiResult<T>> {
  const store = await cookies();
  const session = await readSession((name) => store.get(name)?.value);
  const language = (await headers()).get("accept-language");
  const response = await fetch(`${API_URL()}/v1${path}`, {
    headers: {
      Accept: "application/json",
      ...(session ? { Authorization: `Bearer ${session.accessToken}` } : {}),
      ...(language ? { "Accept-Language": language } : {}),
    },
    cache: "no-store",
    signal: AbortSignal.timeout(15000),
  }).catch(() => null);
  if (!response) return { ok: false, status: 503, code: "service_unavailable" };
  if (response.ok) return { ok: true, status: response.status, data: (await response.json()) as T };
  const body = (await response.json().catch(() => ({}))) as { code?: string };
  return { ok: false, status: response.status, code: body.code ?? "error" };
}

export async function isSignedIn(): Promise<boolean> {
  const store = await cookies();
  return (await readSession((name) => store.get(name)?.value)) !== null;
}

/** Roles decide which menus appear. The backend decides what anyone can actually do. */
export async function currentRoles(): Promise<string[]> {
  const store = await cookies();
  const session = await readSession((name) => store.get(name)?.value);
  const payload = session?.accessToken.split(".")[1];
  if (!payload) return [];
  try {
    const text = Buffer.from(payload, "base64url").toString("utf-8");
    const claims = JSON.parse(text) as { realm_access?: { roles?: string[] } };
    return claims.realm_access?.roles ?? [];
  } catch {
    return [];
  }
}
