import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { freshPerson, newPage, removePeople, signIn, signInAndAgree } from "./fixtures";

test.afterAll(removePeople);

// Only these may run forever: the home page's slow background and what shows while something loads.
const ALLOWED_LOOPS = /^(drift-a|drift-b|flow|bead)$/;

async function endlessAnimations(page: Page) {
  return page.evaluate(() =>
    [...document.querySelectorAll("*")].flatMap((element) =>
      ["", "::before", "::after"].flatMap((pseudo) => {
        const style = getComputedStyle(element, pseudo || null);
        const names = style.animationName.split(",").map((name) => name.trim());
        const counts = style.animationIterationCount.split(",").map((count) => count.trim());
        return names
          .map((name, index) => ({ name, count: counts[index % counts.length] }))
          .filter((item) => item.name !== "none" && item.count === "infinite")
          .map((item) => `${element.tagName.toLowerCase()}.${String(element.className).slice(0, 30)}${pseudo}: ${item.name}`);
      }),
    ),
  );
}

async function stubSpeech(page: Page, voices: { lang: string; localService: boolean }[]) {
  await page.addInitScript((list) => {
    const spoken: string[] = [];
    (window as unknown as { __spoken: string[] }).__spoken = spoken;
    const synth = {
      getVoices: () => list.map((voice, index) => ({ ...voice, name: `voice-${index}`, default: index === 0, voiceURI: `v${index}` })),
      speak: (utterance: { text: string }) => spoken.push(utterance.text),
      cancel: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    };
    Object.defineProperty(window, "speechSynthesis", { value: synth, configurable: true });
    (window as unknown as { SpeechSynthesisUtterance: unknown }).SpeechSynthesisUtterance = class {
      text: string;
      voice: unknown = null;
      lang = "";
      onend: unknown = null;
      onerror: unknown = null;
      constructor(text: string) {
        this.text = text;
      }
    };
  }, voices);
}

test("nothing loops forever except the hero background and loading beads", async ({ browser }) => {
  const page = await newPage(browser);
  await page.goto("/en");
  expect((await endlessAnimations(page)).filter((line) => !ALLOWED_LOOPS.test(line.split(": ")[1] ?? ""))).toEqual([]);

  await signInAndAgree(page, await freshPerson({ persona: "x_carrier" }));
  for (const path of ["/en/app", "/en/app/result", "/en/app/ask", "/en/app/options"]) {
    await page.goto(path);
    expect(await endlessAnimations(page), path).toEqual([]);
  }
  await page.goto("/en/app");
  const current = page.locator("[aria-current=step]");
  await expect(current).toHaveCSS("animation-iteration-count", "3");
});

test("the reading level is saved, changes the page, and Detailed opens the sources", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "x_carrier" }));
  await page.goto("/en/app/result");
  const main = page.locator("main");
  await expect(main).toHaveAttribute("data-reading", "simple");
  await expect(page.getByText(/^Source:/)).toHaveCount(0);

  await page.getByTestId("reading-level").getByText("Detailed").click();
  await expect(main).toHaveAttribute("data-reading", "detailed");
  await expect(page.getByText(/^Source:/).first()).toBeVisible();

  await page.reload();
  await expect(main).toHaveAttribute("data-reading", "detailed");
  await expect(page.getByRole("radio", { name: "Detailed" })).toBeChecked();

  // Keyboard: arrow keys move between levels, as native radios do.
  await page.getByRole("radio", { name: "Detailed" }).focus();
  await page.keyboard.press("ArrowLeft");
  await expect(main).toHaveAttribute("data-reading", "standard");
});

test("Listen appears only with a voice on this device, and reads exactly what's on screen", async ({ browser }) => {
  const person = await freshPerson({ persona: "x_carrier" });

  const cloudOnly = await newPage(browser);
  await stubSpeech(cloudOnly, [{ lang: "en-GB", localService: false }]);
  await signInAndAgree(cloudOnly, person);
  await cloudOnly.goto("/en/app/result");
  await expect(cloudOnly.locator("#result-facts")).toBeVisible();
  await expect(cloudOnly.getByTestId("listen")).toHaveCount(0);

  const local = await newPage(browser);
  await stubSpeech(local, [{ lang: "en-GB", localService: true }]);
  await signIn(local, person);
  await local.goto("/en/app/result");
  await local.getByTestId("listen").click();
  await expect(local.getByTestId("listen")).toHaveAttribute("aria-pressed", "true");
  const spoken = await local.evaluate(() => (window as unknown as { __spoken: string[] }).__spoken);
  const onScreen = (await local.locator("#result-facts").innerText()).trim();
  expect(spoken).toEqual([onScreen]);
  expect(onScreen).toContain("DMD");
});

test("myth tiles flip on a button, move focus, and keep the answer without script", async ({ browser }) => {
  const page = await newPage(browser);
  await page.goto("/en/learn/cousin-marriage");
  const first = page.getByTestId("myths").locator("li").first();
  await first.getByRole("button", { name: "See the answer" }).click();
  await expect(first.locator(".tile-flip")).toHaveAttribute("data-flipped", "true");
  await expect(first.getByRole("button", { name: "Back to the question" })).toBeFocused();
  await expect(first.getByText(/Most children of related couples/)).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(first.getByRole("button", { name: "See the answer" })).toBeFocused();
  await page.emulateMedia({ reducedMotion: "reduce" });
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(results.violations.map((v) => v.id)).toEqual([]);

  const noScript = await browser.newContext({ javaScriptEnabled: false });
  const plain = await noScript.newPage();
  await plain.goto("/en/learn/cousin-marriage");
  await expect(plain.getByText(/Most children of related couples/)).toBeVisible();
  await expect(plain.getByText(/A screening panel looks at particular genes/)).toBeVisible();
  await noScript.close();
});

test("content below the fold is visible without script, and appears on scroll with it", async ({ browser }) => {
  const noScript = await browser.newContext({ javaScriptEnabled: false });
  const plain = await noScript.newPage();
  await plain.goto("/en");
  const cards = plain.locator("[data-reveal]");
  expect(await cards.count()).toBeGreaterThan(3);
  for (const opacity of await cards.evaluateAll((items) => items.map((item) => getComputedStyle(item).opacity))) {
    expect(opacity).toBe("1");
  }
  await noScript.close();

  const page = await newPage(browser);
  await page.setViewportSize({ width: 1280, height: 600 });
  await page.goto("/en");
  const last = page.locator("[data-reveal]").last();
  await last.scrollIntoViewIfNeeded();
  await expect(last).toHaveAttribute("data-reveal", "shown");
  await expect(last).toHaveCSS("opacity", "1");
});

test("the dashboard counts active shares, and a suggested question gets an answer", async ({ browser }) => {
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "fatima" }));
  await page.goto("/en/app");
  await expect(page.getByTestId("active-shares")).toContainText("0");
  await expect(page.getByTestId("active-shares")).toContainText("active shares");

  await page.goto("/en/app/ask");
  await page.getByRole("button", { name: "What does being a carrier mean?" }).click();
  const answer = page.getByTestId("chat-answer").last();
  await expect(answer).toBeVisible({ timeout: 60_000 });
  await expect(answer).toHaveAttribute("data-boundary", "EDUCATION");
  await expect(page.getByRole("button", { name: "What does being a carrier mean?" })).toHaveCount(0);
});

test("the counsellor queue charts real counts and shows time left as a meter", async ({ browser }) => {
  test.setTimeout(120_000);
  const subject = await newPage(browser);
  await signInAndAgree(subject, await freshPerson({ persona: "x_carrier" }));

  const counsellor = await newPage(browser);
  await signIn(counsellor, await freshPerson({ role: "counsellor" }));
  await expect(counsellor).toHaveURL(/\/en\/counsellor$/);
  const items = counsellor.getByTestId("queue-pool").getByTestId("queue-item");
  const waiting = await items.count();
  expect(waiting).toBeGreaterThan(0);

  const chart = counsellor.getByTestId("queue-chart");
  await chart.getByText("Show this as a table").click();
  const rows = chart.locator("tbody tr");
  let total = 0;
  for (const row of await rows.all()) {
    const priority = (await row.locator("td").first().innerText()).trim();
    const count = Number((await row.locator("td").nth(1).innerText()).trim());
    const listed = await counsellor.getByTestId("queue-pool").getByTestId("queue-item").filter({ has: counsellor.locator("p", { hasText: new RegExp(`^${priority}$`) }) }).count();
    expect(count, priority).toBe(listed);
    total += count;
  }
  expect(total).toBe(waiting);
  await expect(counsellor.getByTestId("queue-counts")).toContainText(String(waiting));

  const ring = items.first().getByRole("meter", { name: "Time left for this step" });
  const value = Number(await ring.getAttribute("aria-valuenow"));
  expect(value).toBeGreaterThanOrEqual(0);
  expect(value).toBeLessThanOrEqual(100);
  await expect(ring).toHaveAttribute("aria-valuetext", /left|Past its due time/);

  await counsellor.emulateMedia({ reducedMotion: "reduce" });
  const results = await new AxeBuilder({ page: counsellor }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(results.violations.map((v) => v.id)).toEqual([]);
});
