// Every word a person reads lives in messages/, so the project's wording rules can be enforced here.
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { test } from "node:test";

const ROOT = resolve(import.meta.dirname, "../..");
const en = JSON.parse(readFileSync(join(ROOT, "messages/en.json"), "utf-8"));
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

const ARABIC_SCRIPT = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;

test("Arabic script appears only in messages/ar.json", () => {
  // Approved by the user on 15 Nov 2026 for the interface text only (CLAUDE.md, rule 5). Code,
  // tests and the other catalogues stay free of it, so every Arabic word is in one reviewable file.
  const offenders = filesUnder(ROOT)
    .filter((path) => !path.endsWith(join("messages", "ar.json")))
    .filter((path) => ARABIC_SCRIPT.test(readFileSync(path, "utf-8")));
  assert.deepEqual(offenders, []);
});

test("Arabic has the same keys and the same placeholders as English", () => {
  assert.deepEqual(Object.keys(ar).sort(), Object.keys(en).sort());
  for (const key of Object.keys(en)) {
    const names = (text) => (text.match(/\{\w+\}/g) ?? []).sort();
    assert.deepEqual(names(ar[key]), names(en[key]), key);
  }
});

test("Arabic text is really Arabic, not English left behind", () => {
  // Names such as "Samvid" may stay in Roman letters. A sentence must be in Arabic script.
  const untranslated = Object.entries(ar).filter(
    ([key, text]) => en[key].split(" ").length > 2 && !ARABIC_SCRIPT.test(text) && !key.startsWith("brand."),
  );
  assert.deepEqual(untranslated, []);
});

// The rules above, for Arabic. Written as escapes so this file holds no Arabic script.
const NEVER_AR = [
  // laa khatar ("no risk"), khaali min al-khatar ("free of risk")
  ["certainty", /\u0644\u0627 \u062E\u0637\u0631|\u062E\u0627\u0644\u064D? \u0645\u0646 \u0627\u0644\u062E\u0637\u0631/],
  // anta saleem / anti saleema ("you are healthy"): saleem is banned outright, as "healthy" is
  ["certainty", /\u0633\u0644\u064A\u0645/],
  // nansah, nusi ("we advise", "we recommend"), yajib 'alayk ("you must"), al-afdal laka ("best for you")
  ["directing a decision", /\u0646\u0646\u0635\u062D|\u0646\u0648\u0635\u064A|\u064A\u062C\u0628 \u0639\u0644\u064A\u0643|\u0627\u0644\u0623\u0641\u0636\u0644 \u0644\u0643/],
  // ghayr mutawafiq ("incompatible"), mu'ib ("defective")
  ["stigma", /\u063A\u064A\u0631 \u0645\u062A\u0648\u0627\u0641\u0642|\u0645\u0639\u064A\u0628/],
  // majjani ("free of charge")
  ["unconfirmed cost", /\u0645\u062C\u0627\u0646/],
];

for (const [name, pattern] of NEVER_AR) {
  test(`no Arabic wording of the kind: ${name}`, () => {
    assert.deepEqual(Object.entries(ar).filter(([, text]) => pattern.test(text)), []);
  });
}

test("Arabic never says 'carrier' in a way that can read as 'pregnant'", () => {
  // hamil means both "pregnant" and "carrier" (CLAUDE.md). Every use must be followed by the word
  // for "change" (taghayyur), as in hamil lil-taghayyur, "carrying the change".
  const hamil = /(\S*\u062d\u0627\u0645\u0644\S*)(\s+\S+)?/g;
  const bare = [];
  for (const [key, text] of Object.entries(ar)) {
    for (const match of text.matchAll(hamil)) {
      if (!(match[2] ?? "").includes("\u062a\u063a\u064a\u0651\u0631")) bare.push([key, match[1]]);
    }
  }
  assert.deepEqual(bare, []);
});

test("the Arabic wording rules can actually catch something", () => {
  // laa khatar 'alayk ("there is no risk to you"), nansahuka ("we advise you")
  assert.ok(NEVER_AR[0][1].test("\u0644\u0627 \u062E\u0637\u0631 \u0639\u0644\u064A\u0643"));
  assert.ok(NEVER_AR[2][1].test("\u0646\u0646\u0635\u062D\u0643"));
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
