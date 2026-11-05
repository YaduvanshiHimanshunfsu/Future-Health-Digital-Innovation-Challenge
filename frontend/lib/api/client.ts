export type CallResult<T> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; code: string; message: string };

/** Browser calls go through this site's own server, which adds the token. */
export async function callApi<T = unknown>(
  path: string,
  options: { method?: "GET" | "POST" | "PATCH" | "DELETE"; body?: unknown; language?: string } = {},
): Promise<CallResult<T>> {
  try {
    const response = await fetch(`/api/proxy/${path}`, {
      method: options.method ?? "GET",
      headers: {
        ...(options.body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(options.language ? { "Accept-Language": options.language } : {}),
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      cache: "no-store",
    });
    if (response.ok) {
      const text = await response.text();
      return { ok: true, status: response.status, data: (text ? JSON.parse(text) : null) as T };
    }
    const body = (await response.json().catch(() => ({}))) as { code?: string; message?: string };
    return {
      ok: false,
      status: response.status,
      code: body.code ?? "error",
      message: body.message ?? "",
    };
  } catch {
    return { ok: false, status: 0, code: "network", message: "" };
  }
}
