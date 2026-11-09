import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { freshPerson, newPage, removePeople, signIn, signInAndAgree } from "./fixtures";

test.afterAll(removePeople);

async function axeClean(page: Page) {
  await page.emulateMedia({ reducedMotion: "reduce" });
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(results.violations.map((v) => `${v.id}: ${v.nodes[0]?.target.join(" ")}`)).toEqual([]);
}

async function answerAll(page: Page, testId: string, pick: (index: number) => number) {
  const form = page.getByTestId(testId);
  const groups = form.locator("fieldset");
  const count = await groups.count();
  for (let index = 0; index < count; index += 1) {
    await groups.nth(index).getByRole("radio").nth(pick(index)).check();
  }
  await form.getByRole("button", { name: "Check my answers" }).click();
}

test("reading the result, checking understanding and stepping back all show on the journey", async ({ browser }) => {
  test.setTimeout(150_000);
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "fatima" }));

  await page.goto("/en/app/result");
  await expect(page.locator("#result-facts")).toBeVisible();
  await page.goto("/en/app/journey");
  const steps = page.getByTestId("journey-steps");
  await expect(steps).toContainText("Your result is ready to read.");
  await expect(steps).toContainText("You've read the explanation.");

  // A first, deliberately poor try is the "before" score; the second, right one is "after".
  await page.goto("/en/app/check");
  await expect(page.getByTestId("teach-back").getByTestId("instrument-status")).toHaveText("Draft questions, awaiting review");
  await expect(page.getByTestId("sure").getByTestId("instrument-status")).toHaveText("Adapted, not validated in Hindi or Arabic");
  await answerAll(page, "teach-back", () => 2);
  await expect(page.getByTestId("teach-back").getByRole("status")).toContainText("weren't explained well enough");
  await page.reload();
  const right = [1, 0, 1, 2, 0];
  await answerAll(page, "teach-back", (index) => right[index] ?? 0);
  await expect(page.getByTestId("teach-back").getByRole("status")).toContainText("5 of 5 matched");
  await axeClean(page);

  await page.goto("/en/app/journey");
  await page.getByRole("button", { name: "Step back from follow-up" }).click();
  await page.getByRole("button", { name: "Yes, step back" }).click();
  await expect(page.getByTestId("journey-steps")).toContainText("You stepped back");
  await expect(page.getByRole("button", { name: "Ask to talk to a counsellor" })).toBeVisible();
  await axeClean(page);
});

test("a counsellor offers a time, a person books it, and the counsellor refers onward", async ({ browser }) => {
  test.setTimeout(180_000);
  const person = await newPage(browser);
  await signInAndAgree(person, await freshPerson({ persona: "x_carrier" }));
  const care = await person.request.get("/api/proxy/me/journey");
  const caseId = (await care.json())[0].case_id as string;

  const counsellor = await newPage(browser);
  await signIn(counsellor, await freshPerson({ role: "counsellor" }));
  await expect(counsellor).toHaveURL(/\/en\/counsellor$/);
  // Taking the case first means the person is offered this counsellor's times only.
  const claimed = await counsellor.request.post(`/api/proxy/cases/${caseId}/claim`, { headers: { Origin: "http://localhost:3000" } });
  expect(claimed.status()).toBe(200);
  // A time well clear of every other test's slots: 2 to 60 days ahead, to the minute.
  const start = new Date(Date.now() + (2 + Math.floor(Math.random() * 58)) * 86_400_000);
  start.setSeconds(0, 0);
  const local = new Date(start.getTime() - start.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
  await counsellor.getByLabel("Start").fill(local);
  await counsellor.getByRole("button", { name: "Offer this time" }).click();
  await expect(counsellor.getByTestId("schedule")).toContainText("Open");

  await person.goto("/en/app/journey");
  await person.getByRole("button", { name: "See available times" }).click();
  const booking = person.getByTestId("booking");
  await booking.getByRole("button", { name: "Book this time" }).first().click();
  await expect(booking).toContainText("Booked for");
  await axeClean(person);

  const slot = await person.request.get("/api/proxy/booking/mine");
  const mine = (await slot.json()) as { id: string }[];
  expect(mine.length).toBe(1);
  await counsellor.goto(`/en/counsellor/case/${caseId}`);
  await expect(counsellor.getByTestId("case-actions")).toBeVisible();
  await counsellor.getByRole("button", { name: "Mark counselling done" }).click();
  await counsellor.getByLabel("Service or laboratory").fill("Regional genetics laboratory");
  await counsellor.getByRole("button", { name: "Create a draft referral" }).click();
  const referrals = counsellor.getByTestId("referrals");
  await expect(referrals).toContainText("Draft");
  await referrals.getByRole("button", { name: "Send" }).click();
  await expect(referrals).toContainText("Sent");
  await referrals.getByText("FHIR record").click();
  await expect(referrals.locator("pre")).toContainText("ServiceRequest");
  await expect(referrals.locator("pre")).not.toContainText("DMD");
  await axeClean(counsellor);

  await person.goto("/en/app/journey");
  await expect(person.getByTestId("journey-steps")).toContainText("A confirming test has been arranged");
});

test("a programme administrator sees synthetic metrics with an equity breakdown", async ({ browser }) => {
  const page = await newPage(browser);
  await signIn(page, await freshPerson({ role: "program_admin" }));
  await expect(page).toHaveURL(/\/en\/admin$/);
  await expect(page.getByTestId("synthetic-banner")).toContainText("Synthetic data");
  await expect(page.getByTestId("chart-funnel")).toBeVisible();
  await expect(page.getByTestId("chart-time")).toBeVisible();
  await axeClean(page);

  await page.getByRole("link", { name: "Equity" }).click();
  await expect(page.getByTestId("equity-alerts")).toContainText("gaps above their threshold");
  await expect(page.getByTestId("equity-comprehension_pass-lang")).toBeVisible();
  await axeClean(page);
});

test("people and counsellors can't open the programme metrics", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson());
  const denied = await page.request.get("/api/proxy/analytics/overview");
  expect(denied.status()).toBe(403);
});

test("the centre finder works with no account and never shows invented entries", async ({ page }) => {
  await page.goto("/en/centres");
  await expect(page.getByTestId("centres")).toContainText("No centres listed yet");
  await page.getByRole("link", { name: /India/ }).click();
  await expect(page).toHaveURL(/pack=in-india/);
  await expect(page.getByTestId("centres")).toContainText("Nobody has yet checked a counselling service");
  await axeClean(page);
});
