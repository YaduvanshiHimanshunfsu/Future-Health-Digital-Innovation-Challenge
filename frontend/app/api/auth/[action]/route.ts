import { NextResponse, type NextRequest } from "next/server";
import { beginLogin, endSession, exchangeCode, safeReturnPath, appOrigin, type PendingLogin } from "@/lib/auth/oidc";
import {
  LOGIN_COOKIE,
  allChunkNames,
  cookieOptions,
  readSession,
  seal,
  splitCookie,
  unseal,
} from "@/lib/auth/session";
import { isSameOrigin } from "@/lib/api/origin";
import { logEvent } from "@/lib/log";

const API_URL = () => process.env.API_URL ?? "http://127.0.0.1:8000";
const SESSION_SECONDS = 60 * 60;

export async function GET(request: NextRequest, { params }: { params: Promise<{ action: string }> }) {
  const { action } = await params;
  if (action === "login") return login(request);
  if (action === "callback") return callback(request);
  return new NextResponse(null, { status: 404 });
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ action: string }> }) {
  const { action } = await params;
  if (action !== "logout") return new NextResponse(null, { status: 404 });
  if (!isSameOrigin(request)) return new NextResponse(null, { status: 403 });
  return logout(request);
}

async function login(request: NextRequest) {
  const search = request.nextUrl.searchParams;
  const { url, pending } = await beginLogin(
    safeReturnPath(search.get("returnTo"), "/en/start"),
    search.get("pack"),
  );
  const response = NextResponse.redirect(url);
  response.cookies.set(LOGIN_COOKIE, await seal(pending, "login"), cookieOptions(600));
  logEvent("sign_in_started", { pack: pending.pack });
  return response;
}

async function callback(request: NextRequest) {
  const search = request.nextUrl.searchParams;
  const pending = await unseal<PendingLogin>(request.cookies.get(LOGIN_COOKIE)?.value, "login");
  const code = search.get("code");
  const origin = appOrigin();
  if (!pending || !code || search.get("state") !== pending.state) {
    logEvent("sign_in_refused", { reason: "state" });
    return NextResponse.redirect(`${origin}/en/start?error=sign_in`);
  }
  const session = await exchangeCode(code, pending.verifier);
  if (!session) {
    logEvent("sign_in_refused", { reason: "code_exchange" });
    return NextResponse.redirect(`${origin}/en/start?error=sign_in`);
  }

  // Creates the profile on first sign-in, and links it to any lab report for this national ID.
  // The ID comes from the verified token. Nothing sent here can claim one.
  const provisioned = await fetch(`${API_URL()}/v1/me`, {
    method: "POST",
    headers: { Authorization: `Bearer ${session.accessToken}`, "Content-Type": "application/json" },
    body: JSON.stringify(pending.pack ? { pack_code: pending.pack } : {}),
    cache: "no-store",
  }).catch(() => null);
  if (!provisioned?.ok) {
    const reason = provisioned?.status === 409 ? "already_linked" : "unavailable";
    logEvent("sign_in_refused", { reason });
    return NextResponse.redirect(`${origin}/en/start?error=${reason}`);
  }

  const response = NextResponse.redirect(`${origin}${pending.returnTo}`);
  response.cookies.delete(LOGIN_COOKIE);
  logEvent("signed_in", { pack: pending.pack });
  const parts = splitCookie(await seal(session, "session"));
  for (const [name, value] of Object.entries(parts)) {
    if (value) response.cookies.set(name, value, cookieOptions(SESSION_SECONDS));
    else response.cookies.delete(name);
  }
  return response;
}

async function logout(request: NextRequest) {
  const session = await readSession((name) => request.cookies.get(name)?.value);
  if (session) await endSession(session.refreshToken);
  const response = new NextResponse(null, { status: 204 });
  for (const name of allChunkNames()) response.cookies.delete(name);
  logEvent("signed_out", { had_session: session !== null });
  return response;
}
