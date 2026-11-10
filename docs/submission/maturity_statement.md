# Maturity statement

**Why this exists:** the FAQ asks teams to "tell us how mature your solution is now and what you will build or improve during the Challenge".

## Before the build (to 4 Nov 2026)

An idea and its specification, with **no working code**. The repository held research, a solution design, a review listing the specification's own errors, a phase plan with checks for each step, and a file skeleton whose every file was a documentation stub (`brain.md` #001 to #009).

## Built during the challenge (5 to 10 Nov 2026)

Everything that runs was written in this period, phase by phase, each with its own checks (`brain.md` #010 to #018, `docs/phases/CROSS_VERIFICATION.md`):

| Phase | Built | Proof |
|---|---|---|
| 1 Foundation | Secure API, sign-in, audit chain, local stack, CI configuration | API and unit tests |
| 2 Data and risk engine | Envelope encryption, FHIR lab ingestion, deterministic risk engine, country packs, synthetic population | 100% branch coverage on the engine; database dump scan |
| 3 Privacy and sharing | Consent ledger with OpenFGA, couple check, family invitations, access log, emergency access, right not to know | 81 deliberate rule breaks all caught by tests; real OpenFGA outage test |
| Frontend | Web app from the team's Stitch design, in English and Hindi, wired to the backend; motion, charts, reading levels, read-aloud | 55 browser tests with accessibility checks |
| 4 AI and escalation | Validated answers, router, knowledge base, options, values, counsellor queue; Gemini and Ollama providers with template fallback | Router and answer evaluations, per language |
| 5 Care and measurement | Care pathway, booking, FHIR referrals, centre finder, understanding checks, metrics and equity dashboards | API and browser tests per check |
| 6 Evaluation and hardening (in progress) | Evaluation harnesses, scanner runs, log and load checks, submission documents | `docs/evaluation/`, `docs/security/` |

## Maturity at submission

**A working prototype on synthetic data**, technology readiness about TRL 4: the whole journey works on a single machine, validated against its own tests, never with real people or real results.

| Not yet | Why it matters |
|---|---|
| Clinical review of gene tables, rules and content | Every clinical statement is still a draft |
| Native-speaker review; Arabic text | Hindi is unreviewed; Arabic shows English |
| User testing | No evidence yet that people understand better |
| Routing recall target (95% per language) | Some unfamiliar phrasing still gets an automatic answer |
| A licensed partner, UAE hosting, retention rules | Required before any real data |

Country packs: **Abu Dhabi** is the reference pack and **India** an illustrative second. Neither is reviewed, so neither country is "supported" yet, and the app says so on screen.
