# Pitch deck outline

Ten slides, one or two per judging criterion. Every number on a slide is either from a test report in this repository or labelled as an estimate or synthetic. No logos of any authority or company.

| # | Slide | Criterion | Content | Source |
|---|---|---|---|---|
| 1 | Samvid | | One line: understanding genetic carrier results, privately, with a person when it matters | |
| 2 | The problem | Health impact | Carrier results arrive as terms people misread: "carrier" heard as "sick", "no shared finding" as "no risk". Counsellors are few, and stigma keeps people quiet | `docs/01` (cite published sources only) |
| 3 | What Samvid does | Health impact | Explain in plain words, in the person's language; hand clinical questions and distress to a person; share only by consent | Screens |
| 4 | Demo | Working solution | The 4-minute journey (video) | `demo_script.md` |
| 5 | How it's built | Technical depth | Deterministic risk engine; consent ledger plus OpenFGA; validated AI with template fallback; FHIR in and out; country packs | `technical_documentation.md` |
| 6 | Safety, measured | Responsible AI | Zero wrong figures, other people's genes or IDs across 96 evaluated answers; routing recall per language, including what's **not** yet met | `docs/evaluation/` |
| 7 | Privacy and governance | Responsible AI | No ID in personal routes, minimum-necessary FHIR, small groups hidden, access log, right not to know; scanners clean | `docs/security/` |
| 8 | Scale | Scalability | A new country is a pack, not code; one-command stack; production refuses unsafe settings | Country packs, `test_config.py` |
| 9 | Path to pilot | Commercial | Buyer, counsellor-time model (labelled estimate), licensed partner under Art. 28, phased pilot | `commercial_and_pilot_plan.md` |
| 10 | Honest status | All | Synthetic data; drafts awaiting clinical and language review; what's next | `assumptions_and_limitations.md` |

## Words to avoid on slides

Anything the copy rules forbid: "zero-knowledge", "on-device", "certified", "clinically validated", "prevents" anything, or any claim that a choice is the right one. Never present a cancelled marriage as an outcome.
