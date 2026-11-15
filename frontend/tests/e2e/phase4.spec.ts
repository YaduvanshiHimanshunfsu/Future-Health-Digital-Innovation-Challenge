import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { freshPerson, newPage, removePeople, signIn, signInAndAgree } from "./fixtures";

test.afterAll(removePeople);

async function ask(page: Page, question: string) {
  await page.goto("/en/app/ask");
  await page.getByLabel("Your question").fill(question);
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  const answer = page.getByTestId("chat-answer").last();
  // With a real model behind it an answer can take a while, so the wait is generous.
  await expect(answer).toBeVisible({ timeout: 60_000 });
  return answer;
}

test("an Arabic carrier question gets an education answer on screen", async ({ browser }) => {
  // Phase 4 exit gate. Roman letters: "what does it mean that I'm a carrier of the gene?".
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "fatima" }));
  const answer = await ask(page, "madha ya'ni annani hamil lil-jin?");
  await expect(answer).toHaveAttribute("data-boundary", "EDUCATION");
  // The reviewed template always names the gene. A checked model draft may word it differently.
  if ((await answer.innerText()).includes("Reviewed text")) await expect(answer).toContainText("HBB");
  await expect(answer).not.toContainText("A counsellor has been alerted");
});

for (const question of [
  "I'm 12 weeks pregnant, what should I do?",
  "\u0623\u0646\u0627 \u062d\u0627\u0645\u0644\u060c \u0645\u0627\u0630\u0627 \u0623\u0641\u0639\u0644\u061f",
  "ana hamil fi al-shahr al-thalith",
]) {
  test(`a clinical question reaches a person: ${question.slice(0, 20)}`, async ({ browser }) => {
    // Phase 4 exit gate: English, Arabic script (no rule reads it, so a person does), and Arabic in Roman letters.
    const page = await newPage(browser);
    await signInAndAgree(page, await freshPerson());
    const answer = await ask(page, question);
    await expect(answer).toHaveAttribute("data-boundary", "CLINICAL_ADVICE");
    await expect(answer).toContainText("A counsellor has been alerted");
    await expect(answer).toContainText("book");
  });
}

test("an answer is shown as text, never as markup", async ({ browser }) => {
  // V4.3.9. The question is echoed in the log, so it's the easiest way to plant markup.
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson());
  await ask(page, '<img src=x onerror="window.__owned=1"> what is a carrier?');
  expect(await page.evaluate(() => (window as unknown as { __owned?: number }).__owned)).toBeUndefined();
  await expect(page.getByTestId("chat-log").locator("img")).toHaveCount(0);
});

test("options are equal cards with no ranking, and values stay private until shared", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "x_carrier" }));
  await page.goto("/en/app/options");
  const cards = page.getByTestId("options").locator("li");
  expect(await cards.count()).toBeGreaterThan(3);
  const text = (await page.getByTestId("options").innerText()).toLowerCase();
  expect(text).not.toMatch(/recommend|best|preferred/);
  const sizes = await cards.evaluateAll((items) => items.map((item) => item.querySelectorAll("h2").length));
  expect(new Set(sizes)).toEqual(new Set([1]));

  await page.getByLabel(/What matters most/).fill("Time with family");
  await page.getByRole("button", { name: "Save privately" }).click();
  await expect(page.getByRole("button", { name: "Share with my counsellor" })).toBeVisible();
  await page.getByRole("button", { name: "Share with my counsellor" }).click();
  await expect(page.getByText("Shared with your counsellor.")).toBeVisible();
});

test("a P2 case reaches a counsellor's screen and can be taken on", async ({ browser }) => {
  // Phase 4 exit gate.
  test.setTimeout(150_000);
  const subject = await newPage(browser);
  await signInAndAgree(subject, await freshPerson({ persona: "x_carrier" }));
  const care = await subject.request.get("/api/proxy/me/care");
  const caseId = (await care.json())[0].case_id as string;

  const counsellor = await newPage(browser);
  await signIn(counsellor, await freshPerson({ role: "counsellor" }));
  await expect(counsellor).toHaveURL(/\/en\/counsellor$/);
  const item = counsellor.getByTestId("queue-pool").locator("li", { hasText: "X-linked carrier" }).first();
  await expect(item).toBeVisible();
  await expect(counsellor.getByTestId("queue-pool")).not.toContainText("DMD");

  // Several fresh cases may be waiting. Take this person's one by opening it directly.
  const claim = await counsellor.request.post(`/api/proxy/cases/${caseId}/claim`, {
    headers: { Origin: "http://localhost:3000" },
  });
  expect(claim.status()).toBe(200);
  await counsellor.goto(`/en/counsellor/case/${caseId}`);
  await expect(counsellor.getByTestId("case-priority")).toHaveText("P2");
  await expect(counsellor.getByText("Verify before use")).toBeVisible();
  await expect(counsellor.getByTestId("case-summary")).toContainText("DMD");
  await expect(counsellor.getByText("You're viewing this through emergency access")).toHaveCount(0);

  const results = await new AxeBuilder({ page: counsellor }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(results.violations.map((v) => v.id)).toEqual([]);
});
