import type { NextRequest } from "next/server";

/** Refuses a change sent from another site. Browsers set Origin on these requests. */
export function isSameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  const expected = process.env.APP_ORIGIN;
  return Boolean(origin && expected && origin === expected);
}
