// Every word a person reads lives in messages/, so the project's wording rules can be enforced here.
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { test } from "node:test";

const ROOT = resolve(import.meta.dirname, "../..");
const en = JSON.parse(readFileSync(join(ROOT, "messages/en.json"), "utf-8"));
const hi = JSON.parse(readFileSync(join(ROOT, "messages/hi.json"), "utf-8"));
const ar = JSON.parse(readFileSync(join(ROOT, "messages/ar.json"), "utf-8"));

function filesUnder(folder, found = []) {
  for (const name of readdirSync(folder)) {
    if (["node_modules", ".next", "test-results", "playwright-report"].includes(name)) continue;
    const path = join(folder, name);
    if (statSync(path).isDirectory()) filesUnder(path, found);
    else if (/\.(ts|tsx|json|css|mjs|md)$/.test(name)) found.push(path);
  }
  return found;
}

const NEVER = [
  // Claims of no risk. Warnings that a result never means no risk are required, and allowed.
  ["certainty", /you are healthy|you're healthy|carriers are healthy|there is no risk|you (have|are at) no risk|risk.free|zero risk/i],
  ["stigma", /incompatible|defective|bad genes/i],
  ["directing a decision", /you should|we recommend|best option|recommended/i],
  ["diagnosis wording", /your child will have/i],
  ["unconfirmed cost", /free (genetic )?(screening|test)/i],
  ["marriage as an outcome", /marriages? (prevented|avoided|cancelled)|cancelled marriages/i],
  ["false privacy claims", /zero.knowledge|enclave|on your device|device memory|browser memory|client.side|homomorphic|cryptographically|fully blind|\bPSI\b/i],
  ["false certificates", /HIPAA|ISO.?27|GDPR compliant|certified by|clinician.reviewed|doctor.approved/i],
  ["implied endorsement", /\bDoH\b|\bM42\b|AIIMS|\bSEHA\b|Department of Health|Sheikh Khalifa/i],
];

for (const [name, pattern] of NEVER) {
  test(`no wording of the kind: ${name}`, () => {
    const found = Object.entries(en).filter(([, text]) => pattern.test(text));
    assert.deepEqual(found, []);
  });
}

test("Hindi has the same keys and the same placeholders as English", () => {
  assert.deepEqual(Object.keys(hi).sort(), Object.keys(en).sort());
  for (const key of Object.keys(en)) {
    const names = (text) => (text.match(/\{\w+\}/g) ?? []).sort();
    assert.deepEqual(names(hi[key]), names(en[key]), key);
  }
});

test("Hindi text is really Hindi, not English left behind", () => {
  // Names, codes and short labels may stay in Roman letters. Sentences shouldn't.
  const untranslated = Object.entries(hi).filter(
    ([key, text]) => text === en[key] && text.split(" ").length > 2 && !key.startsWith("brand."),
  );
  assert.deepEqual(untranslated, []);
});

test("no Arabic or Urdu script anywhere in the frontend", () => {
  assert.deepEqual(ar, {}, "Arabic text waits on the user's approval and a reviewer");
  const script = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
  const offenders = filesUnder(ROOT).filter((path) => script.test(readFileSync(path, "utf-8")));
  assert.deepEqual(offenders, []);
});

test("the wording rules can actually catch something", () => {
  const privacy = NEVER.find(([name]) => name === "false privacy claims")[1];
  assert.ok(privacy.test("Zero-knowledge proof inside browser memory"));
  assert.ok(NEVER.find(([name]) => name === "certainty")[1].test("You are healthy and safe"));
  assert.ok(NEVER.find(([name]) => name === "certainty")[1].test("Good news: there is no risk."));
});

test("no screen calculates a chance", () => {
  // Numbers come from the risk engine. Arithmetic on percent or one_in here would be a second engine.
  const code = filesUnder(join(ROOT, "components/risk")).concat(filesUnder(join(ROOT, "lib/risk")));
  for (const path of code) {
    const text = readFileSync(path, "utf-8");
    assert.doesNotMatch(text, /(percent|one_in)\s*[*/+-]\s*\d|\d\s*[*/+-]\s*(fact|child)\.(percent|one_in)|Math\.(round|floor|ceil)\([^)]*percent/, path);
  }
});

test("chances never animate, and charts never carry genetic results", () => {
  // A rolling number adds drama to a figure someone should read calmly, so counting motion is kept
  // away from anything that shows a chance. Charts show counts of things, never a person's result.
  const risk = filesUnder(join(ROOT, "components/risk")).concat(filesUnder(join(ROOT, "lib/risk")));
  for (const path of risk) assert.doesNotMatch(readFileSync(path, "utf-8"), /CountUp/, path);
  for (const path of filesUnder(join(ROOT, "components/charts"))) {
    assert.doesNotMatch(readFileSync(path, "utf-8"), /(Fact|MyRisk|IconArrayVisual|percent|one_in)/, path);
  }
});

test("speech uses only voices on this device", () => {
  const text = readFileSync(join(ROOT, "components/layout/ListenButton.tsx"), "utf-8");
  assert.match(text, /voice\.localService/);
});
