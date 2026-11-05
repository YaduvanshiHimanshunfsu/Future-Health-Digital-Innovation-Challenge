// One JSON line per event, the same shape as the API's logs, so Run_Samvid.py can show both.
// Paths are reduced to their pattern first: IDs, invitation tokens and codes never reach a log.

const UUID = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
const TOKEN_LIKE = /^[A-Za-z0-9_-]{16,}$/;

export function pathPattern(path: string): string {
  const clean = path.split("?")[0] ?? "";
  const parts = clean.split("/").map((part, index, all) => {
    if (all[index - 1] === "i") return ":token";
    if (UUID.test(part)) return part.replace(UUID, ":id");
    return TOKEN_LIKE.test(part) ? ":token" : part;
  });
  UUID.lastIndex = 0;
  return parts.join("/") || "/";
}

export function logEvent(msg: string, ctx: Record<string, string | number | boolean | null>) {
  // A log line is never allowed to break a request.
  try {
    console.log(JSON.stringify({ ts: new Date().toISOString(), level: "INFO", logger: "samvid.web", msg, ctx }));
  } catch {
    // Nothing to do: logging is best effort.
  }
}
