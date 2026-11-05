import { NextResponse, type NextRequest } from "next/server";
import { DEFAULT_LOCALE, LOCALES, isLocale } from "@/lib/i18n/config";
import { refresh } from "@/lib/auth/oidc";
import { logEvent, pathPattern } from "@/lib/log";
import {
  allChunkNames,
  cookieOptions,
  readSession,
  seal,
  splitCookie,
} from "@/lib/auth/session";

const SESSION_SECONDS = 60 * 60;
const REFRESH_MARGIN_SECONDS = 30;
const SIGNED_IN = /^\/(en|hi|ar)\/(app|counsellor|admin)(\/|$)/;

function contentSecurityPolicy(nonce: string): string {
  const development = process.env.NODE_ENV === "development";
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${development ? " 'unsafe-eval'" : ""}`,
    // Computed widths and positions on charts use style attributes.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    `connect-src 'self'${development ? " ws:" : ""}`,
    "frame-ancestors 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "object-src 'none'",
  ].join("; ");
}

function preferredLocale(request: NextRequest) {
  const header = request.headers.get("accept-language") ?? "";
  for (const part of header.split(",")) {
    const code = part.trim().split(/[-;]/)[0];
    if (isLocale(code) && code !== "ar") return code;
  }
  return DEFAULT_LOCALE;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isApi = pathname.startsWith("/api/");

  if (!isApi && !LOCALES.some((l) => pathname === `/${l}` || pathname.startsWith(`/${l}/`))) {
    const url = request.nextUrl.clone();
    url.pathname = `/${preferredLocale(request)}${pathname === "/" ? "" : pathname}`;
    return NextResponse.redirect(url);
  }

  const read = (name: string) => request.cookies.get(name)?.value;
  let session = await readSession(read);
  let refreshedCookies: Record<string, string> | null = null;
  let signedOut = false;

  // Pages can't set cookies once rendering starts, so an expiring token is renewed here.
  const now = Math.floor(Date.now() / 1000);
  if (session && session.expiresAt - now < REFRESH_MARGIN_SECONDS) {
    const renewed = await refresh(session.refreshToken);
    if (renewed) {
      session = renewed;
      refreshedCookies = splitCookie(await seal(renewed, "session"));
    } else {
      session = null;
      signedOut = true;
    }
  }

  const locale = pathname.split("/")[1];
  if (!session && SIGNED_IN.test(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = `/${isLocale(locale) ? locale : DEFAULT_LOCALE}/start`;
    url.search = "";
    const redirect = NextResponse.redirect(url);
    if (signedOut) for (const name of allChunkNames()) redirect.cookies.delete(name);
    return redirect;
  }

  const nonce = btoa(crypto.randomUUID());
  const policy = contentSecurityPolicy(nonce);
  const headers = new Headers(request.headers);
  headers.set("x-nonce", nonce);
  // Layouts use these for the language switch and for pages with no locale parameter.
  headers.set("x-path", pathname.replace(/^\/(en|hi|ar)/, "") || "");
  headers.set("x-locale", isLocale(locale) ? locale : DEFAULT_LOCALE);
  headers.set("Content-Security-Policy", policy);
  if (refreshedCookies) {
    // This request is rendered with the renewed token too.
    const others = request.cookies
      .getAll()
      .filter((cookie) => !allChunkNames().includes(cookie.name))
      .map((cookie) => `${cookie.name}=${cookie.value}`);
    const fresh = Object.entries(refreshedCookies)
      .filter(([, value]) => value)
      .map(([name, value]) => `${name}=${value}`);
    headers.set("cookie", [...others, ...fresh].join("; "));
  }

  const response = NextResponse.next({ request: { headers } });
  // Next.js fetches linked pages ahead of time. Those aren't visits, so they'd only add noise.
  const prefetch = request.headers.has("next-router-prefetch") || request.headers.get("purpose") === "prefetch";
  if (!isApi && !prefetch) {
    logEvent("page", {
      method: request.method,
      path: pathPattern(pathname),
      signed_in: session !== null,
      renewed: refreshedCookies !== null,
    });
  }
  if (!isApi) response.headers.set("Content-Security-Policy", policy);
  if (SIGNED_IN.test(pathname)) response.headers.set("Cache-Control", "no-store");
  if (refreshedCookies) {
    for (const [name, value] of Object.entries(refreshedCookies)) {
      if (value) response.cookies.set(name, value, cookieOptions(SESSION_SECONDS));
      else response.cookies.delete(name);
    }
  }
  if (signedOut) for (const name of allChunkNames()) response.cookies.delete(name);
  return response;
}

export const config = {
  // Everything except built files. Auth routes stay out, because they manage these cookies themselves.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/auth|illustrations).*)"],
};
