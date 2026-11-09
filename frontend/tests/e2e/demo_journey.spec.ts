import { expect, test } from "@playwright/test";
import { freshPerson, newPage, removePeople, signIn, signInAndAgree } from "./fixtures";

test.afterAll(removePeople);

test("public pages work with no account, and say this is a demo", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/en$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Understand your genetic results");
  await expect(page.getByText("Demo: synthetic data").first()).toBeVisible();
  for (const path of ["/en/learn/inheritance", "/en/learn/cousin-marriage", "/en/privacy"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  }
});

test("signed-in pages need a session", async ({ page }) => {
  await page.goto("/en/app/result");
  await expect(page).toHaveURL(/\/en\/start$/);
});

test("no result shows before service consent", async ({ browser }) => {
  const person = await freshPerson({ persona: "fatima" });
  const page = await newPage(browser);
  await signIn(page, person);
  await expect(page.getByRole("heading", { name: "Before you see any results" })).toBeVisible();
  await page.goto("/en/app/result");
  await expect(page).toHaveURL(/\/en\/start$/);
  expect(await page.locator("body").innerText()).not.toContain("HBB");
});

test("a carrier reads their result, with no number and no 25% square", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "fatima" }));
  await page.goto("/en/app/result");
  const text = await page.locator("main").innerText();
  expect(text).toContain("HBB");
  expect(text).toContain("Beta thalassaemia");
  expect(text).toContain("usually doesn't cause illness");
  expect(text).not.toContain("%");
  expect(text).not.toContain("c.20A");
  await expect(page.locator("figure")).toHaveCount(0);
});

test("an uncertain finding gets words and no number", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "uncertain" }));
  await page.goto("/en/app/result");
  const text = await page.locator("main").innerText();
  expect(text).toContain("can't give a number");
  expect(text).not.toContain("%");
});

test("an X-linked carrier gets her own picture, from the API's numbers", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "x_carrier" }));
  await page.goto("/en/app/result");
  await expect(page.getByText("How this passes on, for an X-linked gene")).toBeVisible();
  await expect(page.getByText("50%").first()).toBeVisible();
});

test("no report never reads as a negative result", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson());
  await page.goto("/en/app/result");
  await expect(page.getByText("This isn't a negative result")).toBeVisible();
});

test("the right not to know hides results everywhere, and a person is told someone will call", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "x_man" }));
  await page.goto("/en/app/privacy");
  await page.getByRole("button", { name: "Don't show me my results" }).click();
  await expect(page.getByRole("button", { name: "Show my results again" })).toBeVisible();
  await page.goto("/en/app/result");
  const text = await page.locator("main").innerText();
  expect(text).toContain("You've chosen not to see your results");
  expect(text).toContain("A counsellor will contact you");
  expect(text).not.toContain("DMD");
});

test("the full couple journey shows only what's shared", async ({ browser }) => {
  test.setTimeout(150_000);
  const [first, second] = [await newPage(browser), await newPage(browser)];
  await signInAndAgree(first, await freshPerson({ persona: "fatima" }));
  await signInAndAgree(second, await freshPerson({ persona: "khalid" }));

  await first.goto("/en/app/partner");
  await first.getByRole("button", { name: "Create a code" }).click();
  const code = await first.getByTestId("invite-code").innerText();
  await second.goto("/en/app/partner");
  await second.getByLabel("Code", { exact: true }).fill(code);
  await second.getByRole("button", { name: "Join" }).click();
  await expect(second.getByText("Your partner has joined.")).toBeVisible();
  await first.goto("/en/app/partner");

  // One says "genes" and the other "yes or no", so the more private choice has to win.
  await first.getByRole("radio", { name: /Show the shared gene names/ }).check();
  await first.getByRole("checkbox").check();
  await first.getByRole("button", { name: "Agree to a couple check" }).click();
  await expect(first.getByTestId("my-agreement")).toBeVisible();

  // Before the partner agrees, nothing shows, and nothing says why.
  await first.getByRole("link", { name: "Run the check" }).click();
  await expect(first.getByText("Not ready yet")).toBeVisible();

  await second.getByRole("checkbox").check();
  await second.getByRole("button", { name: "Agree to a couple check" }).click();
  await expect(second.getByTestId("my-agreement")).toBeVisible();
  await second.getByRole("link", { name: "Run the check" }).click();

  await expect(second.getByRole("heading", { name: "You share a finding" })).toBeVisible();
  const text = await second.locator("main").innerText();
  expect(text).not.toContain("HBB");
  expect(text).toContain("25% chance (1 in 4)");
  await expect(second.locator("figure").first()).toBeVisible();
  await expect(second.getByRole("img").first()).toHaveAttribute("aria-label", /25 \/ 100/);
  // The two tiles settle on the outcome, and each pregnancy shows the engine's same figure.
  await expect(second.locator(".match-box")).toHaveAttribute("data-state", "shared");
  const strip = second.getByTestId("pregnancy-strip");
  await expect(strip.locator("li")).toHaveCount(4);
  for (const item of await strip.locator("li").all()) await expect(item).toContainText("25% chance of two copies");
  await expect(second.getByText("A counsellor has been asked to follow this up")).toBeVisible();

  // The partner who didn't run it still gets care, and can see what happened.
  await first.goto("/en/app");
  await expect(first.getByText("A counsellor will be in touch.")).toBeVisible();
  await first.goto("/en/app/privacy");
  const log = first.getByTestId("access-log");
  await expect(log).toContainText("Your partner");
  await expect(log).toContainText("A couple check was run");

  await second.goto("/en/app/partner");
  await second.getByRole("button", { name: "Withdraw my agreement" }).click();
  await expect(second.getByRole("button", { name: "Agree to a couple check" })).toBeVisible();
  await first.goto("/en/app/partner");
  await first.getByRole("link", { name: "Run the check" }).click();
  await expect(first.getByText("Not ready yet")).toBeVisible();
});

test("sharing, then stopping it, cuts access straight away", async ({ browser }) => {
  const [owner, grantee] = [await newPage(browser), await newPage(browser)];
  await signInAndAgree(owner, await freshPerson({ persona: "fatima" }));
  await signInAndAgree(grantee, await freshPerson());

  await grantee.goto("/en/app/privacy");
  await grantee.getByRole("button", { name: "Create a share code" }).click();
  const code = await grantee.getByTestId("receive-code").innerText();

  await owner.goto("/en/app/privacy");
  await owner.getByLabel("Their share code").fill(code);
  await owner.getByRole("button", { name: "Share", exact: true }).click();
  await expect(owner.getByTestId("share-row")).toContainText("Summary");

  await grantee.reload();
  await grantee.getByRole("link", { name: "Open" }).click();
  await expect(grantee.getByTestId("summary-facts")).toContainText("HBB");
  expect(await grantee.locator("main").innerText()).not.toContain("%");
  const sharedUrl = grantee.url();

  await owner.getByRole("button", { name: "Stop sharing" }).click();
  await expect(owner.getByTestId("share-row")).toContainText("Ended");
  await grantee.goto(sharedUrl);
  await expect(grantee.getByRole("heading", { name: "This isn't available" })).toBeVisible();
  expect(await grantee.locator("main").innerText()).not.toContain("HBB");

  await owner.reload();
  await expect(owner.getByTestId("access-log")).toContainText("Someone was refused access");
});

test("an invitation survives link previews, names nobody, and works once", async ({ browser }) => {
  const sender = await newPage(browser);
  await signInAndAgree(sender, await freshPerson());
  await sender.goto("/en/app/family");
  await sender.getByRole("button", { name: "Create a private link" }).click();
  const link = await sender.getByTestId("invite-link").innerText();

  const stranger = await newPage(browser);
  const response = await stranger.goto(link);
  expect(response?.headers()["referrer-policy"]).toBe("no-referrer");
  await stranger.reload();
  await stranger.reload();
  await expect(stranger.getByRole("heading", { level: 2 }).first()).toContainText("Someone who cares about you");
  const text = await stranger.locator("main").innerText();
  expect(text).not.toMatch(/sibling|brother|free/i);
  await stranger.getByRole("button", { name: "I've read this" }).click();
  await expect(stranger.getByText("Thank you.")).toBeVisible();
  await stranger.reload();
  await expect(stranger.getByRole("heading", { name: "This link isn't available" })).toBeVisible();
});

test("emergency access needs a reason, is flagged to the person, and gets reviewed", async ({ browser }) => {
  test.setTimeout(150_000);
  const subject = await newPage(browser);
  await signInAndAgree(subject, await freshPerson({ persona: "x_man" }));
  const care = await subject.request.get("/api/proxy/me/care");
  const caseId = (await care.json())[0].case_id as string;

  const doctor = await newPage(browser);
  await signIn(doctor, await freshPerson({ role: "physician" }));
  await expect(doctor).toHaveURL(/\/en\/counsellor$/);
  await doctor.getByLabel("Case ID").fill(caseId);
  await doctor.getByRole("button", { name: "Open case" }).click();
  await expect(doctor.getByRole("heading", { name: "You don't have access to this case" })).toBeVisible();
  const open = doctor.getByRole("button", { name: "Open with emergency access" });
  await expect(open).toBeDisabled();
  await doctor.getByLabel(/Reason/).fill("Unconscious patient, treating team needs this");
  await open.click();
  await expect(doctor.getByTestId("case-priority")).toHaveText("P1");
  await expect(doctor.getByText("You're viewing this through emergency access")).toBeVisible();

  await subject.goto("/en/app/privacy");
  await expect(subject.getByTestId("access-log")).toContainText("Emergency access");
  await expect(subject.getByTestId("access-log")).toContainText("A doctor");

  const auditor = await newPage(browser);
  await signIn(auditor, await freshPerson({ role: "auditor" }));
  await expect(auditor.getByText("Unconscious patient, treating team needs this")).toBeVisible();
  const before = await auditor.getByRole("button", { name: "Mark as reviewed" }).count();
  await auditor.getByRole("button", { name: "Mark as reviewed" }).first().click();
  await expect(auditor.getByRole("button", { name: "Mark as reviewed" })).toHaveCount(before - 1);
});

test("tokens never reach browser code, and the proxy keeps to its list", async ({ browser, request }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "fatima" }));
  await page.goto("/en/app/result");
  expect(await page.evaluate(() => document.cookie)).toBe("");
  const session = (await page.context().cookies()).filter((c) => c.name.startsWith("samvid_session"));
  expect(session.length).toBeGreaterThan(0);
  for (const cookie of session) {
    expect(cookie.httpOnly).toBe(true);
    expect(cookie.value.startsWith("eyJ")).toBe(false);
  }
  expect(await page.content()).not.toContain("eyJhbGci");

  const refused = await page.request.post("/api/proxy/reports:ingest", {
    headers: { Origin: "http://localhost:3000" },
    data: {},
  });
  expect(refused.status()).toBe(404);
  const traversal = await page.request.get("/api/proxy/me/..%2F..%2Fhealth");
  expect(traversal.status()).toBe(404);

  const crossSite = await page.request.post("/api/proxy/me/results-preference", {
    headers: { Origin: "https://evil.example" },
    data: { withhold: true, terms_version: "1" },
  });
  expect(crossSite.status()).toBe(403);

  const response = await request.get("/en");
  const policy = response.headers()["content-security-policy"] ?? "";
  expect(policy).toContain("frame-ancestors 'none'");
  expect(policy).toMatch(/script-src 'self' 'nonce-/);
  expect(response.headers()["x-powered-by"]).toBeUndefined();
});

test("signing out ends the session here and at Keycloak", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "fatima" }));
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.waitForURL(/\/en$/);
  await page.goto("/en/app/result");
  await expect(page).toHaveURL(/\/en\/start$/);
  await page.getByRole("button", { name: /sign in \(demo\)/i }).click();
  await page.waitForURL(/localhost:8080/);
  await expect(page.locator("#password"), "a shared device has to ask for the password again").toBeVisible();
});

test("Hindi and the right-to-left layout both work", async ({ page }) => {
  await page.goto("/hi");
  await expect(page.locator("html")).toHaveAttribute("lang", "hi");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("आनुवंशिक");
  await page.goto("/ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.getByText("Arabic text is waiting for a reviewer")).toBeVisible();
  const text = await page.locator("body").innerText();
  expect(text).not.toMatch(/[\u0600-\u06FF]/);
});

test("the parts not built yet say so and show nothing simulated", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson());
  for (const path of ["/en/app/check", "/en/app/journey"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { name: "This part isn't built yet" })).toBeVisible();
  }
});
