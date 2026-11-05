import { readFileSync } from "node:fs";
import { randomBytes, randomInt } from "node:crypto";
import { resolve } from "node:path";
import { expect, type Browser, type Page } from "@playwright/test";

const ROOT = resolve(__dirname, "../../..");
const env = Object.fromEntries(
  readFileSync(resolve(ROOT, "infra/.env"), "utf-8")
    .split(/\r?\n/)
    .filter((line) => line.includes("=") && !line.startsWith("#"))
    .map((line) => [line.slice(0, line.indexOf("=")), line.slice(line.indexOf("=") + 1)]),
) as Record<string, string>;

const KEYCLOAK = "http://localhost:8080";
const API = "http://127.0.0.1:8000";
const ABU_DHABI = "ae-abu-dhabi";

export type Person = { username: string; password: string; id: string };
const created: string[] = [];

async function form(url: string, body: Record<string, string>) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(body),
  });
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  return response.json() as Promise<{ access_token: string }>;
}

async function adminHeaders() {
  const { access_token } = await form(`${KEYCLOAK}/realms/master/protocol/openid-connect/token`, {
    grant_type: "password",
    client_id: "admin-cli",
    username: "admin",
    password: env.KEYCLOAK_ADMIN_PASSWORD!,
  });
  return { Authorization: `Bearer ${access_token}`, "Content-Type": "application/json" };
}

/** A new fictional person with a new made-up ID, so runs never collide. */
export async function freshPerson(options: { persona?: string; role?: string } = {}): Promise<Person> {
  const { persona, role } = options;
  const username = `e2e-${persona ?? role ?? "person"}-${randomBytes(4).toString("hex")}`;
  const password = randomBytes(18).toString("base64url");
  let nationalId: string | undefined;
  if (persona) {
    const path = resolve(ROOT, `backend/synthetic/out/${ABU_DHABI}/personas/${persona}.json`);
    const bundle = JSON.parse(readFileSync(path, "utf-8"));
    nationalId = `784-0000-${String(randomInt(10_000_000)).padStart(7, "0")}-8`;
    bundle.entry[0].resource.identifier[0].value = nationalId;
    bundle.entry[1].resource.identifier[0].value = `E2E-${username}`;
    const { access_token } = await form(`${KEYCLOAK}/realms/samvid/protocol/openid-connect/token`, {
      grant_type: "client_credentials",
      client_id: "samvid-lab",
      client_secret: env.LAB_CLIENT_SECRET!,
    });
    const posted = await fetch(`${API}/v1/reports:ingest`, {
      method: "POST",
      headers: { Authorization: `Bearer ${access_token}`, "Content-Type": "application/json", "X-Country-Pack": ABU_DHABI },
      body: JSON.stringify(bundle),
    });
    expect(posted.status).toBe(201);
  }
  const headers = await adminHeaders();
  const response = await fetch(`${KEYCLOAK}/admin/realms/samvid/users`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      username,
      enabled: true,
      attributes: nationalId ? { national_id: [nationalId] } : {},
      credentials: [{ type: "password", value: password, temporary: false }],
    }),
  });
  expect(response.status).toBe(201);
  const id = response.headers.get("location")!.split("/").pop()!;
  created.push(id);
  if (role) {
    const found = await fetch(`${KEYCLOAK}/admin/realms/samvid/roles/${role}`, { headers });
    await fetch(`${KEYCLOAK}/admin/realms/samvid/users/${id}/role-mappings/realm`, {
      method: "POST",
      headers,
      body: JSON.stringify([await found.json()]),
    });
  }
  return { username, password, id };
}

export async function removePeople() {
  const headers = await adminHeaders();
  await Promise.all(created.splice(0).map((id) => fetch(`${KEYCLOAK}/admin/realms/samvid/users/${id}`, { method: "DELETE", headers })));
}

/** The real browser flow, through Keycloak's own page. */
export async function signIn(page: Page, person: Person, locale = "en") {
  await page.goto(`/${locale}/start`);
  await page.getByRole("button", { name: /sign in \(demo\)|साइन इन/i }).click();
  await page.waitForURL(/localhost:8080/);
  await page.locator("#username").fill(person.username);
  await page.locator("#password").fill(person.password);
  await page.locator("#kc-login").click();
  await page.waitForURL((url) => url.port === "3000");
}

export async function signInAndAgree(page: Page, person: Person, locale = "en") {
  await signIn(page, person, locale);
  await page.getByRole("button", { name: /I understand and agree|सहमत हूँ/ }).click();
  await page.waitForURL(new RegExp(`/${locale}/app$`));
}

export async function newPage(browser: Browser): Promise<Page> {
  const context = await browser.newContext({ baseURL: "http://localhost:3000", locale: "en-GB", permissions: ["clipboard-read", "clipboard-write"] });
  return context.newPage();
}
