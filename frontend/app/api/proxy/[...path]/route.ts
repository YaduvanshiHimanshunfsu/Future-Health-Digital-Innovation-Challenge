import { NextResponse, type NextRequest } from "next/server";
import { readSession } from "@/lib/auth/session";
import { isSameOrigin } from "@/lib/api/origin";
import { logEvent, pathPattern } from "@/lib/log";

const API_URL = () => process.env.API_URL ?? "http://127.0.0.1:8000";

// A list, so a new backend route isn't reachable from a browser until someone adds it here. The
// lab's report route is deliberately missing.
const ALLOWED_ROOTS = new Set([
  "me",
  "packs",
  "consents",
  "shared",
  "couples",
  "invitations",
  "cases",
  "break-glass",
]);
const SAFE_SEGMENT = /^[A-Za-z0-9_-]+$/;
const MAX_BODY_BYTES = 64 * 1024;

async function forward(request: NextRequest, segments: string[]) {
  const [root] = segments;
  if (!root || !ALLOWED_ROOTS.has(root) || !segments.every((s) => SAFE_SEGMENT.test(s))) {
    return NextResponse.json({ code: "not_found" }, { status: 404 });
  }
  const changing = request.method !== "GET";
  if (changing && !isSameOrigin(request)) {
    return NextResponse.json({ code: "forbidden" }, { status: 403 });
  }

  const headers: Record<string, string> = { Accept: "application/json" };
  const language = request.headers.get("accept-language");
  if (language) headers["Accept-Language"] = language;
  const session = await readSession((name) => request.cookies.get(name)?.value);
  if (session) headers.Authorization = `Bearer ${session.accessToken}`;

  let body: string | undefined;
  if (changing) {
    const text = await request.text();
    if (text.length > MAX_BODY_BYTES) {
      return NextResponse.json({ code: "too_large" }, { status: 413 });
    }
    if (text) {
      body = text;
      headers["Content-Type"] = "application/json";
    }
  }

  const started = Date.now();
  const upstream = await fetch(`${API_URL()}/v1/${segments.join("/")}`, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
    signal: AbortSignal.timeout(15000),
  }).catch(() => null);
  logEvent("api_call", {
    method: request.method,
    path: pathPattern(`/v1/${segments.join("/")}`),
    status: upstream?.status ?? 503,
    duration_ms: Date.now() - started,
  });
  if (!upstream) return NextResponse.json({ code: "service_unavailable" }, { status: 503 });

  const text = await upstream.text();
  return new NextResponse(upstream.status === 204 ? null : text, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
      "Cache-Control": "no-store",
    },
  });
}

type Context = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, { params }: Context) {
  return forward(request, (await params).path);
}
export async function POST(request: NextRequest, { params }: Context) {
  return forward(request, (await params).path);
}
export async function PATCH(request: NextRequest, { params }: Context) {
  return forward(request, (await params).path);
}
export async function DELETE(request: NextRequest, { params }: Context) {
  return forward(request, (await params).path);
}
