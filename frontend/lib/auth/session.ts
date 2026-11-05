// Tokens stay on this server, in an encrypted, HttpOnly cookie. Browser code never sees them, so a
// script running in the page can't steal one. Uses Web Crypto, because middleware runs on the Edge.

export const SESSION_COOKIE = "samvid_session";
export const LOGIN_COOKIE = "samvid_login";
const CHUNK_SIZE = 3600;
const MAX_CHUNKS = 4;

export type Session = {
  accessToken: string;
  refreshToken: string;
  /** Seconds since the epoch. */
  expiresAt: number;
};

function secretBytes(): Uint8Array<ArrayBuffer> {
  const secret = process.env.SESSION_SECRET;
  if (!secret) throw new Error("SESSION_SECRET is not set");
  const bytes = Uint8Array.from(atob(secret), (c) => c.charCodeAt(0));
  if (bytes.length !== 32) throw new Error("SESSION_SECRET must be 32 bytes, base64 encoded");
  return bytes;
}

function toBase64Url(bytes: Uint8Array): string {
  let text = "";
  for (const byte of bytes) text += String.fromCharCode(byte);
  return btoa(text).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(value: string): Uint8Array<ArrayBuffer> {
  const text = atob(value.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(text, (c) => c.charCodeAt(0));
}

async function key(): Promise<CryptoKey> {
  return crypto.subtle.importKey("raw", secretBytes(), "AES-GCM", false, ["encrypt", "decrypt"]);
}

export async function seal(value: unknown, purpose: string): Promise<string> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = new TextEncoder().encode(JSON.stringify(value));
  const cipher = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv, additionalData: new TextEncoder().encode(purpose) },
    await key(),
    data,
  );
  return `${toBase64Url(iv)}.${toBase64Url(new Uint8Array(cipher))}`;
}

/** Anything tampered with, expired or unreadable comes back as null, which means signed out. */
export async function unseal<T>(sealed: string | undefined, purpose: string): Promise<T | null> {
  if (!sealed) return null;
  const [iv, cipher] = sealed.split(".");
  if (!iv || !cipher) return null;
  try {
    const plain = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: fromBase64Url(iv), additionalData: new TextEncoder().encode(purpose) },
      await key(),
      fromBase64Url(cipher),
    );
    return JSON.parse(new TextDecoder().decode(plain)) as T;
  } catch {
    return null;
  }
}

export function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.SESSION_COOKIE_SECURE !== "false",
    path: "/",
    maxAge,
  };
}

/** Tokens can outgrow one cookie, so a long session is split across a few. */
export function splitCookie(value: string): Record<string, string> {
  const parts: Record<string, string> = {};
  for (let index = 0; index < MAX_CHUNKS; index += 1) {
    const part = value.slice(index * CHUNK_SIZE, (index + 1) * CHUNK_SIZE);
    parts[`${SESSION_COOKIE}.${index}`] = part;
  }
  return parts;
}

export function joinCookie(read: (name: string) => string | undefined): string | undefined {
  let joined = "";
  for (let index = 0; index < MAX_CHUNKS; index += 1) {
    joined += read(`${SESSION_COOKIE}.${index}`) ?? "";
  }
  return joined || undefined;
}

export async function readSession(
  read: (name: string) => string | undefined,
): Promise<Session | null> {
  return unseal<Session>(joinCookie(read), "session");
}

export function allChunkNames(): string[] {
  return Array.from({ length: MAX_CHUNKS }, (_, index) => `${SESSION_COOKIE}.${index}`);
}
