import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { freshPerson, newPage, removePeople, signInAndAgree } from "./fixtures";

test.afterAll(removePeople);

async function clean(page: Page, label: string) {
  await page.emulateMedia({ reducedMotion: "reduce" });
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  const problems = results.violations.map((v) => `${v.id}: ${v.nodes.slice(0, 2).map((n) => n.target.join(" ")).join(" | ")}`);
  expect(problems, label).toEqual([]);
}

for (const locale of ["en", "hi", "ar"]) {
  for (const path of ["", "/learn/inheritance", "/learn/cousin-marriage", "/privacy", "/start"]) {
    test(`public ${locale}${path || "/"} has no WCAG AA problems`, async ({ page }) => {
      await page.goto(`/${locale}${path}`);
      await clean(page, `${locale}${path}`);
    });
  }
}

test("signed-in pages have no WCAG AA problems, on desktop and at phone width", async ({ browser }) => {
  test.setTimeout(180_000);
  const page = await newPage(browser);
  await signInAndAgree(page, await freshPerson({ persona: "x_carrier" }));
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const path of ["/en/app", "/en/app/result", "/en/app/partner", "/en/app/family", "/en/app/privacy", "/hi/app/result", "/en/app/ask", "/en/app/options", "/hi/app/options"]) {
      await page.goto(path);
      await clean(page, `${path} at ${width}`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow, `${path} at ${width} scrolls sideways`).toBeLessThanOrEqual(0);
    }
  }
});

test("visuals have a label and a table, and read the same right to left", async ({ page }) => {
  await page.goto("/ar/learn/inheritance");
  await expect(page.getByRole("img").first()).toHaveAttribute("aria-label", /25/);
  await page.getByText("Show this as a table").first().click();
  await expect(page.getByRole("table").first()).toBeVisible();
  await clean(page, "visuals rtl");
});

test("entrance animations stop for anyone who asks for reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/en");
  const duration = await page.locator(".animate-rise").first().evaluate((el) => getComputedStyle(el).animationDuration);
  expect(parseFloat(duration)).toBeLessThan(0.01);
});

test("outcome colours actually ship: plum, turquoise and sand, never red or green", async ({ page }) => {
  // The build once dropped these classes, leaving an empty grid that every other test passed.
  await page.goto("/en/learn/inheritance");
  const colours = await page.evaluate(() =>
    ["two_copies", "carrier", "neither"].map((key) => {
      const probe = document.createElement("span");
      probe.className = `outcome-${key}`;
      document.body.append(probe);
      const colour = getComputedStyle(probe).backgroundColor;
      probe.remove();
      return colour;
    }),
  );
  expect(colours).toEqual(["rgb(122, 79, 214)", "rgb(20, 168, 155)", "rgb(233, 223, 207)"]);
  const icons = page.locator("figure [role=img] span");
  await expect(icons).toHaveCount(100);
  const box = await icons.first().boundingBox();
  expect(box?.width ?? 0).toBeGreaterThan(4);
});

test("the home page has its colour and motion, and keeps contrast", async ({ page }) => {
  await page.goto("/en");
  await expect(page.locator(".aurora")).toHaveCount(1);
  const before = await page.locator(".aurora").evaluate((el) => getComputedStyle(el, "::before").animationName);
  expect(before).toBe("drift-a");
  await clean(page, "home with motion settled");
});

