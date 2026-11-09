# brain.md: Project Log

This file is the project's memory: **what we did, how we did it, and why.**

---

## The mandate

**Anyone who changes this project must log it here, whether a person or an AI assistant. This rule has no exceptions.**

| # | Rule |
|---|---|
| 1 | **Read first.** Before starting work, read the latest entries and any open follow-ups. |
| 2 | **Log before finishing.** Add your entry before your session ends and before you commit. Work isn't done until it's logged. |
| 3 | **Log everything that changes the project:** code, docs, config, decisions, content, scope, and anything learned from outside, such as a mentor's answer or a rule change. |
| 4 | **Append only.** Never edit or delete an old entry, even if it's wrong. Add a new entry that says `Corrects: #NNN`. |
| 5 | **Newest at the bottom,** numbered in order (`#001`, `#002`, and so on). |
| 6 | **Explain why.** The reason and the rejected alternatives matter most, since the code can't tell you those later. |
| 7 | **Report honestly.** Say what failed, what was skipped, and what you didn't verify. A claim of "done" needs evidence. |
| 8 | **Link to IDs.** Reference phase checks (`V2.4.3`) and issue IDs (`C5`). |
| 9 | **Never log secrets or personal data:** no keys, tokens, real names of participants, Emirates IDs or real genetic results. |
| 10 | **Reviews check this.** A pull request that changes the project without a matching entry isn't ready to merge. |

### What counts as one entry

Use one entry per sub-phase, decision or work session, whichever is smaller. A one-line fix can use the short form.

### Full entry template

Copy this block to the bottom of the file:

```markdown
## #NNN · YYYY-MM-DD · Short title

- **Author:** name, or AI assistant and who directed it
- **Phase:** e.g. 2.4 · **Issues:** e.g. C3, C4 · **Checks:** e.g. V2.4.1

### What we did
The changes, and the files or decisions they affected.

### How we did it
The approach, tools and important steps, so someone else could repeat it.

### Why we did it
The reason, plus the alternatives considered and why they were rejected.

### Verification
What was run or checked, and the actual result. State what was not verified.

### Follow-ups
- [ ] Open items, with an owner if known
```

### Short form, for small changes

```markdown
## #NNN · YYYY-MM-DD · Short title
**What:** … **How:** … **Why:** … **Verified:** …
```

---

# Log

## #001 · 2026-11-03 · Full project review, phase plan and documented skeleton

- **Author:** AI assistant (Claude Code), directed by Himanshu Yadav
- **Phase:** pre-Phase 1 · **Issues:** raised S1–S8, C1–C10, H1–H19, M1–M13; fixed M6 · **Checks:** none yet

### What we did
- Read all seven existing files in full.
- Wrote the review: [docs/04_Project_Review_Issues_and_Improvements.md](docs/04_Project_Review_Issues_and_Improvements.md).
- Wrote the phase plan: [docs/phases/](docs/phases/00_PHASE_OVERVIEW.md), with 6 phases, 32 sub-phases and 176 cross-verification checks, each sub-phase with a goal and objectives.
- Created the full folder and file skeleton from the architecture. All stubs contain documentation only and no code.
- Added this log and its mandate, plus `CLAUDE.md` so future AI sessions pick up the rules.
- Added the file index, traceability matrix and documentation map.
- Replaced `README.md` and added `.gitignore`.
- Saved the project location and rules to the assistant's memory.
- Did **not** change `problem statement.md`, `docs/01`, `02`, `03`, `backend.md` or `frontend.md`.
- Did **not** commit anything.

### How we did it
- Extracted the spec's Python from `backend.md` into a temporary scratch folder outside the repo and ran it with test inputs, which is the source of the `[RUN]` findings. The scratch code wasn't added to the project.
- Checked the challenge page, the human genome law text, UAE government pages, law-firm commentary and PyPI.
- Generated the skeleton from one manifest, so stub headers and the file index can't disagree. The generator refused to overwrite existing files.

### Why we did it
- **User request:** understand the project, plan it in 6 phases, surface problems, create the structure without code, and mandate this log.
- **Ran the code rather than only reading it:** reading alone would have given a false positive. The Arabic diacritics regex looked wrong on screen because of right-to-left rendering, but its bytes are correct. Running also confirmed real bugs, such as the حامل routing error.
- **Original docs left unchanged:** the user asked to be told about issues, so changing the specs is their call. `docs/README.md` states which document wins when they conflict.
- **Phases keep the spec's order but use new dates:** the portal shows a 20 Nov prototype deadline. Rejected: keeping the 15 Nov plan, which starts in the past and uses the wrong date.
- **Added `[NEW]` stubs beyond the spec's file list:** MVP features such as booking and break-glass had no home. They're marked so they can be cut.
- **`ci.yml.stub` rather than `ci.yml`:** a comment-only workflow would show as invalid on GitHub if pushed.
- **Generated lock files weren't created:** tools must generate these, so a hand-made one would be wrong.

### Verification
- Ran the spec code: results recorded in the review under `[RUN]`.
- Scaffold checks, by script: 485 files in 118 folders; 0 non-comment lines in stubs; the six original spec files show no Git diff; no broken relative links in new Markdown; all 50 issue IDs appear in the review. Every file in `backend.md` §10.1 exists, except `ci.yml`, which is deliberately `ci.yml.stub`.
- **Not verified:** legal points are from reading and summaries, not from a lawyer. `[READ]` findings need a database or services, so weren't run. The Challenge rules page and FAQ answers wouldn't load, so they need a logged-in person. Citations in `docs/01` weren't checked in general.

### Follow-ups
- [ ] Register on Hack2skill by 10 Nov, if not already done (user)
- [ ] Read the rules and FAQ while logged in (user)
- [ ] Confirm team size, scope tiers, LLM and cloud credits, and whether a clinician is available (user)
- [ ] Decide whether to apply review corrections directly to `docs/01`, `02`, `03`, `backend.md` and `frontend.md` (user)
- [ ] Commit this work when the user asks

## #002 · 2026-11-03 · Diagram-led README

**What:** Rewrote the root `README.md` with 12 Mermaid diagrams: the gap after the lab, inheritance chances, safety layers, system architecture, risk logic, chat pipeline, couple match, care pathway, sharing modes, what the AI can see, metrics, and the delivery plan. It also has tables for requirements, triage, tech stack and status.

**How:** Wrote the diagrams, rendered each with mermaid-cli 11 in a scratch folder in light and dark themes, viewed the images, then fixed layouts that were too wide or too tall and text that overflowed.

**Why:** The user asked for a detailed, good-looking, diagrammatic README. Mermaid renders natively on GitHub and stays editable as text, unlike exported images. The diagrams show the corrected design from `docs/04`, not the spec's known bugs: three match outcomes, decline at any step, and no donor or adoption options. The README states clearly that no code exists yet, so it doesn't overclaim. DoH and M42 aren't named, to avoid implying endorsement (S8).

**Verified:** All 12 diagrams render. No broken relative links or section anchors, by script. **Not verified:** the page as displayed on GitHub itself, since nothing was pushed, so the callouts and badges haven't been seen in place. mermaid-cli and GitHub may lay diagrams out slightly differently.

## #003 · 2026-11-05 · Project name options suggested
**What:** Suggested replacements for the placeholder name Silah, recommending Baseera. No files were renamed, and the decision is with the user. **How:** Compared candidates on meaning, fit with the team name Vigyan_Viveka_Vijaya, and how they read in Arabic and English, then ran quick web searches for conflicts. **Why:** The user asked. Also, "Silah" in Latin script reads as "weapon" in Turkish and is close to the Arabic word for weapon. **Verified:** Searches found no UAE genetics or health product using Baseera, Bayan or Rafeeq. This is not a trademark check, and no native speaker has reviewed the names.

## #004 · 2026-11-05 · Sanskrit and Indian name options suggested
**What:** Suggested Sanskrit and Indian names on request, recommending Samvid. No files were renamed, and the decision is with the user. **How:** Checked Samvid and Anvaya against dictionary entries on Wisdom Library, and ran quick searches for conflicts. **Why:** The user asked. Anvaya was not recommended because its senses include race and lineage, which is risky for a genetics product. **Verified:** Dictionary entries list knowledge, understanding and consent for samvid. Searches found no health or genetics product named Samvid, Anvaya, Anubodh or Sanmati. This is not a trademark check. The other names were suggested from general knowledge, not checked.

## #005 · 2026-11-05 · Renamed project to Samvid, added team name, removed Arabic script
- **Author:** AI assistant (Claude Code), directed by the user
- **Phase:** cross-cutting · **Issues:** none closed · **Checks:** none

### What we did
- Renamed the project from Silah to Samvid in every file, including database roles, the login realm, logger names and `infra/keycloak/realm-samvid.json`.
- Added the team name, Vigyan_Viveka_Vijaya, to `README.md`, `CLAUDE.md`, `docs/01` and the Story Mode slide in `docs/frontend.md`.
- Removed all Arabic script from project files, and added the rule to `CLAUDE.md`.

### How we did it
- One checked script with exact line targets. It stopped if a target line did not match.
- Prose: Arabic examples now use Roman letters with their English meaning.
- `docs/backend.md` code: character-level rules now use Unicode escapes, which keep the same behaviour. Arabic word lists became placeholders named after their meaning, to come from a reviewed lexicon.
- `docs/frontend.md`: the Arabic headline became a note asking for a native-speaker translation.

### Why we did it
- The user chose the name and team name, and asked that nothing be written in Urdu or Arabic.
- Earlier log entries keep the old name, because this log is append-only. Silah is the former name of Samvid.
- Arabic support stays in the product design, because the challenge asks for linguistically appropriate communication in Abu Dhabi. The rule covers text written in project files. The user has been asked to confirm this reading.

### Verification
Script scan: no old name and no Arabic script outside `brain.md`. Past log entries keep both, by the append-only rule. Compared with commit `65f155c`, the escaped diacritics, digit, normalising and sentence-split rules in `docs/backend.md` behave the same across the 256 Arabic-block characters. All 67 Python samples in `docs/backend.md` still compile. The commit still holds the original Arabic text. **Known effects:** four named placeholders (`AR_DIAGNOSIS_PATTERN`, `AR_DIRECTIVE_PATTERN`, `AR_DIRECTIVE_SAMPLE`, `AR_STIGMA_SAMPLE_WITH_DIACRITICS`) are not defined yet, so those samples can't run until the Arabic text exists. The spec's router sample no longer contains the bug described in C6, but the review keeps it as a warning. **Not verified:** the Roman-letter spellings have not been checked by an Arabic speaker. Nothing has been committed.

### Follow-ups
- [ ] Confirm whether the product should still support Arabic users (user)
- [ ] Decide how Arabic interface text and test data get written at implementation time, since the no-Arabic rule blocks them (user)
- [ ] Have a Gulf Arabic speaker confirm the Roman-letter examples and the word lists when a reviewer is available
- [ ] Rename the GitHub repository only if wanted; it does not use the old name

## #006 · 2026-11-05 · Re-scoped the project as global, using country packs

- **Author:** AI assistant (Claude Code), directed by the user
- **Phase:** cross-cutting, adds sub-phase 2.6 · **Issues:** raised S9 and G1–G9 · **Checks:** added V2.6.1–V2.6.6, V4.4.5, V6.4.6

### What we did
- Wrote `docs/07_Global_Design_and_Country_Packs.md`: a global core, with everything country-specific in a country pack.
- Updated `README.md` (new diagram, global framing), `CLAUDE.md`, the phase plans, review, traceability matrix and file index.
- Added a scope note to `docs/01`, `02`, `03`, `backend.md` and `frontend.md`, plus a global context section in `docs/01`.
- Added stubs: `backend/app/country_packs/`, `backend/packs/_template/`, `backend/packs/ae-abu-dhabi/`, and a pack test.
- Moved the options and centre-list stubs into the pack, deleting `backend/app/decision/options_abu_dhabi.yaml` and `backend/app/centres/data/centres.yaml`. Both were empty stubs.

### How we did it
- Read the challenge page, then searched for global evidence (Bittles and Black, PNAS 2010, and reviews of the counsellor shortage).
- Applied edits with a checked script that stopped on any mismatch.
- Rendered the changed diagrams in light and dark themes and viewed them.

### Why we did it
- The user asked that the project not be limited to Abu Dhabi, and the page asks for "solutions to global health needs".
- **Kept Abu Dhabi as the first reference pack, not removed:** the Challenge 03 text is framed around it, and it's the likeliest first pilot. Depth in one place is more credible than a thin product claimed everywhere.
- **Settings, not separate code:** law, options and languages differ by country, but safety rules must not. A pack can tighten a rule and can never switch one off.
- **Sample code in `backend.md` not rewritten:** G1–G9 list what must change when it's implemented, so the spec stays reviewable.
- Rejected: a find-and-replace removal of UAE details. It would destroy the only worked example and its evidence.

### Verification
- Scripted scan: 33 sub-phases, 184 checks, no code lines in stubs, no broken links or anchors in new and updated docs, and no Arabic script outside `brain.md`. All 13 README diagrams render.
- All new issue IDs appear in the review and are assigned to a phase.
- **Not verified:** the laws listed in `docs/07` section 6 are starting points that nobody has reviewed. The 10.4% figure is a 2009-era estimate. The FAQ answer to "Do we need to be in the UAE?" wouldn't load. Nothing has been committed.

### Follow-ups
- [ ] Confirm the second country pack; India is recommended (user)
- [ ] Read the FAQ answer to "Do we need to be in the UAE?" while logged in (user)
- [ ] Confirm whether the product should still support Arabic users (user)
- [ ] Register by 10 Nov, if not already done (user)

## #007 · 2026-11-05 · Applied user decisions: India pack, three languages, registered

- **Author:** AI assistant (Claude Code), directed by the user
- **Phase:** cross-cutting, updates 1.1, 1.2, 2.6 and Phases 3 to 6 · **Issues:** raised G10 · **Checks:** added V1.2.6, V4.2.8, V4.3.10

### What we did
- Recorded three user answers. India is the second country pack. The product supports English, Arabic and Hindi. The team is already registered.
- Updated `README.md`, `CLAUDE.md`, `docs/07`, the review, phase plans, file index and scope notes.
- Added stubs: `backend/packs/in-india/`, `system_hi.txt`, `frontend/messages/hi.json`, and Hindi copies of the template and knowledge-base stubs.
- Added India starting points to the legal and options skeletons, labelled unreviewed.

### How we did it
Applied checked edits with a script that stopped on any mismatch, then rendered the changed diagrams and rescanned the project.

### Why we did it
- **User decisions.** Registration is recorded as confirmed by the user. Evidence for check V1.1.1 (an email or screenshot) is still to be added.
- **Packs:** Abu Dhabi uses Arabic and English, India uses Hindi and English. Rejected: all languages in all packs, which adds review work with no benefit.
- **Simple level first:** three languages raises the content load by half, so the Simple reading level is T1, and Standard and Detailed move to T2.
- **G10 raised honestly:** national survey data puts the highest consanguinity in Tamil Nadu, Karnataka and Andhra Pradesh, where Hindi isn't the main language. Hindi stays as the user chose, and Tamil, Kannada and Telugu go on the roadmap.
- **The no-Arabic rule stays for project files.** The user confirmed Arabic support for the product, but didn't lift the rule, so Arabic interface text and test data still need their go-ahead.

### Verification
Script scan: 33 sub-phases, 187 checks, no code lines in stubs, no broken links or anchors, and no Arabic script outside `brain.md`. All 13 README diagrams render, and the two changed ones were viewed. **Not verified:** the India legal points are unreviewed starting points, and the survey figures come from a secondary summary of NFHS-5, not the official fact sheets. No Hindi content exists yet. Nothing has been committed.

### Follow-ups
- Closed from #006: second pack chosen, Arabic support confirmed, registration done.
- [ ] Add registration evidence for V1.1.1 (user)
- [ ] Read the rules and FAQ while logged in, including "Do we need to be in the UAE?" and "What do we need to submit?" (user)
- [ ] Decide who writes Arabic interface text and test data, and approve adding it (user)
- [ ] Find Hindi and Arabic native-speaker reviewers (user)

## #008 · 2026-11-05 · Added official requirements, re-baselined and cross-verified all phases

- **Author:** AI assistant (Claude Code), directed by the user
- **Phase:** cross-cutting, all phases · **Issues:** raised S10, S11 · **Checks:** evidence added for V1.1.3; V1.1.1 and V1.1.2 are partial

### What we did
- Recorded the FAQ answers word for word, with dates, criteria and awards, in `docs/submission/competition_requirements.md`, and saved three screenshots in `docs/submission/evidence/`.
- Added `data_sources.md` and `maturity_statement.md`, a dependencies section, and filled in the submission checklist.
- Corrected stale statements in `docs/01`, `02`, `03`, the review, `CLAUDE.md` and `README.md`.
- Re-baselined the phases from 5 Nov: Phase 1 is 5–6 Nov, Phase 2 is 7–9 Nov, Phase 3 is 10–11 Nov. Phases 4 to 6 are unchanged.
- Audited every phase and generated `docs/phases/CROSS_VERIFICATION.md`.

### How we did it
- Mapped each objective to its checks and each issue to its checks by hand, reading the phase files. This is what exposed the gaps.
- A script asserted the mapping was complete and generated the document. A second script, reading only the finished files, then recounted everything.

### Why we did it
- The user supplied the official answers and asked for all phases to be made consistent and cross-verified.
- **Findings that changed the plan:** the organisers provide no data and every source must be declared; dependencies and maturity must be stated; code may be requested; full requirements are shared on registration.
- **Audit gaps fixed:** 19 objectives had no check or only a partial one, and several issues had no direct check.
- **Phases 1 to 3 compressed, not Phase 6:** evaluation and honest documentation are judged directly, and feature freeze stays at the end of 17 Nov. Rejected: moving the 19 Nov submission target, which removes the buffer.
- **Correction to my earlier statement:** the page does allow ideas and early prototypes as eligible entries, but a working prototype must still be submitted. Review S2 is updated.

### Verification
- Both scripts agree: 33 sub-phases, 135 objectives, 238 checks, 62 open issues each with a check, 13 targets each with a check. Check numbering has no gaps, dates are continuous, there are no broken links, and no Arabic script outside `brain.md`.
- All 13 README diagrams render.
- **This verifies the plan's consistency, not its feasibility.** No code exists, so almost no check has evidence: only V1.1.3 is done.
- **Not verified:** the full requirements, which are still unread. Nothing has been committed.

### Follow-ups
- [ ] Find the full requirements shared on registration (user)
- [ ] Add registration evidence for V1.1.1 (user)
- [ ] Confirm team size, clinician access and AI model access (user)
- [ ] Approve Arabic content, and name who writes it (user)
- [ ] Give the go-ahead to start building Phase 1 (user)

## #009 · 2026-11-05 · Agreed work split and code standard, before Phase 1
**What:** Recorded the user's rules in `CLAUDE.md` and assistant memory. Claude writes backend, security and database code, Stitch prompts and frontend integration. The user builds screens with Stitch or similar. Phase 1 starts on the user's next explicit command, so no code was written. **How:** Added a section to `CLAUDE.md`. **Why:** The user asked for complete, secure code with no shortcuts that doesn't read as AI-written. This will be met through code quality and natural style. Authorship won't be faked or hidden, and this log keeps recording AI involvement, because the user mandated it. **Verified:** Nothing to verify; documentation only.

## #010 · 2026-11-05 · Phase 1: built the secure foundation, drafted the baseline documents

- **Author:** AI assistant (Claude Code), directed by the user
- **Phase:** 1.2 to 1.6 · **Issues:** progressed H15, H16, H18, M2, M5, M12 · **Checks:** see `docs/phases/CROSS_VERIFICATION.md`

### What we did
- **1.3:** project config and lockfile, Docker image, Compose stack (Postgres, Redis, Keycloak, OpenFGA, API, worker, scheduler), secret generator, CI and pre-commit config.
- **1.4:** app factory, settings with production guards, JWT verification with its own key cache, security headers, body limits, health-safe logging, error handling in English and Hindi, rate limiter.
- **1.5:** all 21 tables, first migration, separate database roles, tamper-evident audit trail, data classification enforced by a test.
- **1.2 drafts:** threat model, legal baseline with article map and retention table, options by country, risk rule table, lexicon seeds. All unreviewed.
- **1.6:** accessible colour tokens and corrected Stitch prompts, plus new prompts P21 to P23.

### How we did it
- Generated the migration from the models against a real database, then added grants and triggers by hand. A test confirms no drift between the two.
- Tested with real Postgres and Redis containers, using the same `init.sql` as the stack, and real RSA keys for tokens.
- Ran the whole stack from a clean state and verified a real Keycloak token inside the API container.

### Why we did it
Decisions that differ from `backend.md`:
- **The audit hash covers the columns, not a stored copy.** In the spec, `actor` or `resource` could be edited unnoticed, and the access log reads those columns.
- **Audit sequence numbers come from the chain, not a database sequence,** so a rollback can't leave a gap that looks like a deletion.
- **Own JWKS cache instead of `PyJWKClient`:** adds a refresh cooldown against random `kid` floods, and a maximum key age during outages.
- **Everything about a finding is encrypted,** including classification (H18). Even "has a pathogenic finding" is sensitive.
- **Own error boundary middleware:** Starlette's catch-all handler runs outside user middleware, so 500s would lose the security headers.
- **Least privilege by table:** the API role can't delete consents, findings or persons, and can't update pathway steps.
- **`national_id_hash` and per-language settings from the start,** so the core stays global (G1, G2).

Bugs found by testing, and fixed: error handlers read global settings; FastAPI turned oversized chunked uploads into a 400; `packaging` was only present through dev tools, which stopped the worker in the real image; the migration lacked an import; an independent audit write could wait on a lock its own caller held; and cached signing keys never aged out. One of my own was caught on review before it ran: production HTTPS checks were skipped in template mode.

### Verification
- 160 tests pass, with 90% coverage. ruff, mypy strict, bandit and pip-audit are clean.
- Clean rebuild: all services healthy in 72 s (first build 148 s).
- `check_services`: Postgres, Redis, Keycloak and OpenFGA reachable, and a real token verified with `lab_service`.
- A planted secret was blocked by the gitleaks hook, and the repo's history scan found no leaks.
- Trivy scanned the image (Debian packages and Python packages): 0 fixable HIGH or CRITICAL vulnerabilities.
- **Not verified:** CI hasn't run, since nothing is pushed. No second person has run the stack. Encryption, OpenFGA rules and all domain logic are later phases. No clinician, lawyer, security specialist or native speaker has reviewed anything, including the Hindi error messages. Nothing has been committed.

### Follow-ups
- [ ] Find the full requirements (user)
- [ ] Confirm team size, scope tiers, phase owners and eligibility (user)
- [ ] Find a clinician, and ask how couple results are delivered (user)
- [ ] Generate the design system and T1 screens in Stitch from `docs/frontend.md` (user)
- [ ] Have a Hindi speaker check `backend/app/core/messages/hi.json` (user)
- [ ] Have a second person run the stack from a clean clone (user)
- [ ] Commit and push when asked, which also runs CI for V1.3.4

## #011 · 2026-11-05 · Wrote the complete Stitch prompt file
**What:** Added `docs/STITCH_PROMPTS.md`: a design system prompt, a component sheet, every screen and its other states, Hindi, mobile and right-to-left variants, fix-up prompts, motion plan, hand-over steps and a screen-to-endpoint map. It replaces §3 and §5 of `docs/frontend.md`. **How:** Rewrote each prompt with the review's fixes built in, and structured them per Stitch's own guidance of one screen per prompt. A script checked for banned wording, Arabic script, colour contrast and that every prompt appears in the order table. **Why:** The user asked for one detailed prompt file, and builds the screens themselves. New states were added for results the spec missed: uncertain finding, talk to a counsellor first, no shared finding, and can't determine yet. The Arabic variant holds no Arabic text, because the rule still stands, so Stitch would translate it, which needs approval and a native reviewer. **Verified:** The script's checks passed. **Not verified:** No prompt has been run in Stitch. Stitch export options and limits come from secondary sources. The Hindi glossary hasn't been checked by a native speaker.

## #012 · 2026-11-05 · Built the Phase 2 backend: encryption, packs, ingestion, risk engine, synthetic data
**What:** On "do phase 2", built envelope encryption with Local and Vault key providers, country packs for Abu Dhabi and India, FHIR report ingestion, triage at ingest, the case state machine, the risk engine with visuals, the provisioning, consent and results APIs, the synthetic generator with personas, and `scripts/smoke_stack.py`. The user then asked to move to Phase 3 if Phases 1 and 2 are complete, and stopped the session for the day before that happened. **Phase 3 has not started:** its plan and stubs were read, and no Phase 3 code was written.

**How:** Pure risk engine using exact fractions, with expected values worked out by hand. Real Postgres and Redis containers in tests. Then the real Compose stack with real tokens through the browser sign-in flow, followed by a deliberate mutation check: 44 rules broken one at a time in a throwaway copy.

**Why these decisions:**
- **No empiric consanguinity figure (H4).** Published figures describe unscreened couples, so quoting one after a negative panel would mislead.
- **The "yes or no" view hides residual facts as well,** since seeing which of your genes has a figure would show which one was shared.
- **National ID comes only from a verified token, and is admin-only in Keycloak.** Otherwise anyone could type someone's number and read their results.
- **Unknown significance codes are refused, not dropped,** because a dropped code could be a pathogenic finding.
- **G6PD is P3 when hemizygous.** An engineering default, flagged for a clinician in `risk_rules_review.md`.
- **Keycloak user profile added to the realm.** Keycloak 26 drops undeclared attributes, so the national ID needed declaring anyway, and declaring it let us lock it.

**Bugs found by testing, all fixed:**
- **The database dump check proved nothing.** `pg_dump` writes binary columns as hex, so it passed with encryption switched off. Only the mutation check revealed this. The real data was encrypted throughout. My first two attempts at the fix were also wrong, one matching nothing and one a regex error, which a new "found at least one binary value" check and re-running the mutation exposed. The mutation had looked caught both times for the wrong reason.
- **No test covered the yes-or-no view hiding private facts.** The code was right, and it's now protected.
- **A reused report ID naming another person would have cancelled the first person's result.** Now refused.
- **Two first reports arriving together returned a 500,** and two tabs signing in together got a false conflict.
- **My route-walking security tests checked nothing** on this FastAPI version, because its route objects changed. They now use the published schema and assert that the routes exist.
- **A country-specific example** sat in a comment in `schema.py`. The search test found it.

### Verification
- Last complete test run: 453 passed, 1 failed, with 92% coverage and 100% branch coverage on the risk engine. The failure was the dump-search pattern, since fixed, and its 3 tests pass. **The final full run after that fix did not finish.** It was still going after 20 minutes, against the usual 2 to 3, when the user stopped the session. The database was still answering, so it doesn't look like a lock, but the cause wasn't found. Re-run it first.
- ruff, mypy strict, bandit, pip-audit and Trivy (0 fixable HIGH or CRITICAL) are clean.
- All 44 mutations are now caught. The first 42 were run together, and the last 2 re-run individually after their fixes.
- Smoke script against the real stack passes, and repeats safely. It includes proof that a user can edit their profile but is refused on `national_id`.
- **Not verified:** the Vault provider has only met a simulated Vault. CI hasn't run. No clinician has reviewed any rule, and the hand-worked answers are the author's own, with no second person checking them. No screens exist, so V2.5.3, V2.5.4 and V2.5.6 stay open. LOINC, HL7 terminology and gene symbol licence terms aren't confirmed: LOINC's site refused an automated fetch.

### Follow-ups
- [ ] Re-run the full test suite, and find out why the last run was slow (Claude, first thing next session)
- [ ] Start Phase 3 on the user's word. Before V3.5.4, ask how to handle Arabic test samples, since project files can't hold Arabic script (Claude)
- [ ] Read the LOINC terms and add any required notice (user)
- [ ] Find a clinician to review the rules, including the G6PD default (user)
- [ ] Have a second person work the expected answers by hand (user)
- [ ] Generate the Stitch screens (user)

## #013 · 2026-11-05 · Correction to #012: the final test run did finish, with one unexplained failure
**What:** #012 says the final full run didn't finish and was stopped. That's wrong. It finished on its own moments before the kill command, which found no process: 453 passed, 1 failed, in 21.5 minutes, with 92% coverage.

**How:** The failure was `test_malformed_input_gets_422_and_stores_nothing[no_entries]`, a different test from the dump-search one fixed in #012. Re-run alone it passed, and its group of 25 passed too.

**Why it's logged:** the suite has **not** had a fully clean run since the last fixes, and this failure is unexplained. The output of that run was filtered down to summary lines, so its error message is lost. It may be connected to the unusual slowness, but that's a guess.

### Verification
- The single test passes alone (1 passed), and with its group (25 passed).
- **Not verified:** the cause of the failure or the slowness. No clean full run yet.

### Follow-ups
- [ ] Re-run the full suite with the complete output kept, and with no other heavy Docker work going on. If that test fails again, read the error before changing anything (Claude, first thing next session)

## #014 · 2026-11-06 · Phase 3 privacy fabric, and the frontend built from the Stitch design
**What:**
- **Phase 3 backend:** OpenFGA model and adapter that deny on any failure, an outbox with reconciliation, the consent ledger with receive codes, the shared-report read path, right not to know, the couple match with three outcomes, family invitations, the access log, break-glass with review, and word-list redaction.
- **Frontend:** built in Next.js from the team's Stitch export (56 screens), with sign-in on the app's own server, an allow-listed proxy, English and Hindi, a right-to-left Arabic layout, and colour and motion.
- **Stack and tooling:** the `web` service in Compose, `scripts/seed_demo.py`, and the public `/v1/packs` and `/v1/me/care` routes.

**How:** Real OpenFGA and Postgres containers in backend tests. A real browser against the real stack for the frontend, signing in through Keycloak's own page. Then a deliberate mutation check of 81 privacy rules, and screenshots read by eye.

**Why these decisions:**
- **Every share must be live in the ledger and in OpenFGA.** Each layer alone can refuse, and tests now prove each one does.
- **One OpenFGA tuple per grant.** Two grants to one person expire and revoke independently, and a duplicate write can't break a second grant (H7).
- **Access is written after commit (outbox) and removed before commit (revoke).** A failed commit can't leave access, and a failed revoke says 503 and changes nothing.
- **Receive codes instead of looking people up.** Nobody can find out whether someone uses the service, and no result arrives unasked.
- **Redaction keeps only listed words.** No model detects Arabic or Hindi names reliably, so unknown words are masked. Arabic loses every word until it has a list, which costs answer quality, never privacy.
- **Stitch's words weren't used.** 43 of 56 screens claimed things the product doesn't do: zero-knowledge, on-device, HIPAA and ISO certificates, invented study results, and real hospitals' names. The layouts are Stitch's, and every word comes from `messages/`, where a test enforces the rules.
- **Tokens never reach browser code.** They sit in an encrypted HttpOnly cookie, and the browser calls a proxy.

**Bugs found by testing, all fixed:**
- **A grant still waiting in the outbox could be applied after its revocation.** The revoke now cancels it, under the same row lock.
- **The build silently dropped the outcome colours,** because Tailwind removes class names it can't see written in full. The icon array was empty, and every functional test passed regardless. A screenshot caught it, and a test now checks the colours.
- **On phones, a wide table made the privacy page scroll sideways,** and keyboard users couldn't scroll it.
- **On Windows, `localhost` adds 2 s to every new connection.** This is client side: measured at 2.16 s, against 0.09 s by address.
- **My own mistakes, caught along the way:**
  - One browser run I reported as "against the container" actually reached a stray local server still answering on IPv6 `localhost`. It was repeated properly: 36 passed against the container.
  - Shell escaping put two invisible backspace characters into a test, and broke a script once.
  - One mutation definition was itself broken.

### Verification
- 625 backend tests pass, with 89% coverage. ruff, mypy strict, bandit, pip-audit and npm audit are clean.
- 36 browser tests pass against the containerised app: every journey, sign-out ending the Keycloak session, tokens absent from the browser, the proxy list, the cross-site refusal, and axe at desktop and phone width in all three locales.
- The smoke script passes all 65 checks on the real stack, including stopping OpenFGA for real and the worker recovering afterwards.
- All 81 mutations are caught. 74 were caught on the first pass, and the other 7 led to better tests.
- **Not verified:**
  - No native speaker has read the Hindi.
  - Arabic text waits on approval.
  - No counsellor has defined "must inform".
  - No pitch deck is written yet.
  - CI hasn't run, because nothing is pushed.
  - Nobody outside the team has used the screens.

### Follow-ups
- [ ] Hindi review of `frontend/messages/hi.json` and `backend/app/privacy/safe_words/hi.txt` (user)
- [ ] Decide on Arabic text and test data (user)
- [ ] A counsellor to define "must inform" and review the G6PD rule (user)
- [ ] Phase 4 needs AI model access, or ships in template mode, which the plan allows (user)
- [ ] Commit and push when asked

## #015 · 2026-11-06 · Solved the intermittent test failure, and added Run_Samvid.py
**What:**
- **The intermittent failure from #013 is explained.** `test_malformed_input_gets_422_and_stores_nothing` searched every refused response for "784", the start of every Abu Dhabi ID. But each response carries a random hexadecimal request ID, which contains "784" by chance in about 1 run in 12 across the 25 inputs. The product was never at fault. The test now checks for the ID's real format.
- **Added `Run_Samvid.py` at the repository root,** at the user's request. One command starts the whole stack, prepares demo data, prints where to go and which demo accounts to use, then shows live, readable activity from the web app, the API and the workers. It says which phases are done and gets updated after every phase.
- **The web app now logs one privacy-safe line per page and API call,** with paths reduced to their pattern, so the launcher can show frontend activity. Tokens, IDs and invitation codes never appear.

**Why:** the user asked for a single launcher, with frontend and backend activity visible in the terminal.

### Verification
- 625 backend tests pass, with no failures.
- The launcher passes ruff and mypy in strict mode. Its live view was checked against the real stack (see #016, or the next entry).

## #016 · 2026-11-06 · Checked Run_Samvid.py for real, and fixed what that showed
**What:** Ran `python Run_Samvid.py` against the real stack, signed in as a demo person in a real browser, and read what the launcher printed.

**What the check showed:**
- **Start-up works.** Every service came up, and the launcher reported the web app, API and sign-in ready, then printed the demo accounts.
- **The live view works.** It shows each page opened, each call the browser makes through the web app, and each API request with its status and time. An invitation link appears only as `/en/i/:token`, and the API shows its route pattern.
- **Seeding took 3 minutes, which was a bug.** Every Keycloak call went to `localhost`, and on Windows each one cost about 2 s while IPv6 was tried first. Server-to-server calls now use `127.0.0.1`, which tokens accept because Keycloak's hostname is fixed. Browser sign-in stays on `localhost`. Seeding now takes 14 s.
- **Next.js prefetches cluttered the view.** They're hidden now, since they aren't visits.

### Verification
- Seeding ran in 13.9 s.
- The smoke script passes all 65 checks after the change, including the browser sign-in.
- 36 browser tests pass against the rebuilt container.
- The launcher passes ruff, and mypy in strict mode.

## #017 · 2026-11-09 · Cross-checked Phases 1 to 4, built the frontend's motion and chart layer, and found a router safety gap
**What:**
- **Cross-verification.** Re-ran everything on the real stack: the full backend suite (Phases 1 to 4), the smoke script, every browser test, and all the scanners. The user had committed and pushed in the meantime, and no secret files are tracked.
- **Frontend: 14 design-spec components were still empty stubs.** They are now built and wired to real data:
  - Motion: rise-in on scroll, count-up for counts, self-drawing lines, a pulse that stops after three, flip tiles, and page transitions. Hooks are in `frontend/lib/motion.ts`.
  - Layout: the reading-level switch, a read-aloud button, a privacy badge, the mosaic divider and the tile band.
  - Risk visuals: the couple-match tiles and the per-pregnancy strip.
  - A chart kit: bars, donut, line, heatmap and a time-left ring.
- **Where it shows:**
  - Dashboard: a progress rail and an active-share count.
  - Chat: starter questions, typing beads and listen buttons.
  - Related-couples page: myth flip tiles.
  - Couple check: the match and pregnancy visuals.
  - Counsellor queue: a priority chart, counts, and a time-left ring per case.
  - Home: mosaic dividers and scroll reveals.
  - Detailed reading level: sources and tables open by default.
- **Backend, for the time-left ring.** Queue and case responses now carry `window_hours`, the step window from the country pack, so the ring has a real basis. Pack codes come from one query for the whole queue, not one query per case.
- **Phase 4 records:**
  - The early evaluation: `scripts/eval_router.py`, with two question sets.
  - The content review log.
  - The exit gate, threat model, Phase 4 evidence table and project structure.
  - `Run_Samvid.py`: Phase 4 marked done, in template mode; demo-counsellor added.

**The router gap (the most important finding):**
- **What the first evaluation showed.** The keyword router recognised only the phrasings it was written from. 28 of 84 questions meant for a person got the automatic education answer, including "I don't want to live anymore". The cause was that education was the fallback for anything unrecognised.
- **Fix 1, the fallback.** Education is no longer the fallback. Only a message naming a topic Samvid explains gets an automatic answer. Anything else goes to a person, with the support line shown as for distress.
- **Fix 2, the rules.** They are wider in all three languages.
- **Fix 3, an Arabic matching bug.** Roman Arabic is compared after repeated letters are collapsed, so every rule spelled with a double letter could never match. That included the old carrier-context rule for the English word "carrier". A test now checks every Arabic rule.
- **How it was measured honestly.** The 84 questions became the development set, now used as a regression gate. A new hold-out set of 59 questions, never used for tuning, gives the real figure: **10 of 59 questions meant for a person still got the automatic answer, and distress was recognised as distress 0 of 9 times**. Most of those still reached a person, as clinical or unclear.
- **What's left.** V4.3.3 isn't met. Rules can't recognise distress they haven't seen. Closing the gap needs a classifier that can only escalate a route, never downgrade it (that depends on the model decision), plus native-speaker word lists.

**Why:** the user asked for the phases to be cross-checked and for a dynamic frontend with colour, motion, transitions and room for graphs, with no shortcuts. The evaluation is the Phase 4 exit gate's last item, and it mattered more than any visual.

**Design choices:**
- **Everything renders visible on the server.** Entrances only hide content that is below the fold once script is running, so nothing depends on JavaScript.
- **Only the hero background and loading indicators loop.** That is the spec's rule, and a browser test now enforces it on every element. The header strip and the step pulse used to loop forever.
- **Count-up never touches a chance.** A rolling number adds drama to a figure someone should read calmly, and a test keeps CountUp out of risk components.
- **Read-aloud uses only on-device voices.** A cloud voice would send the person's result to a speech service, so with no local voice there is no button.
- **The couple-match motion is the same for every outcome.** Nothing is celebrated and nothing looks alarming.
- **Charts take suppressed counts as null and draw "<10".** A suppressed count is never drawn as zero.

**Bugs found by testing, all fixed:**
- The dashboard announced two "current" steps at once.
- The counsellor's summary showed raw labels such as `two_copies`, in English even on the Hindi page.
- The Arabic rule bug above.

### Verification
- 779 (plus 1 added during the run, passing on its own) backend tests pass (90% coverage). The 772 from the start of the session passed too, before any change.
- 50 browser tests pass against the container. Only the container serves port 3000.
- Smoke script: 65 of 65 checks pass on the real stack.
- 16 wording tests pass.
- ruff, ruff format, mypy strict, bandit, pip-audit and npm audit are clean.
- **Not verified:**
  - No native speaker has read the Hindi or the Roman Arabic evaluation questions.
  - No clinician has reviewed the content.
  - No counsellor has rated the summary.
  - The real listen button has only been tested with a stubbed speech engine.
  - CI hasn't run on these changes, which aren't committed.

### Follow-ups
- [ ] Decide the model provider. That unblocks an escalate-only classifier for the router gap (user)
- [ ] Native speakers to write the Phase 6.1 evaluation set and widen the word lists (user)
- [ ] Hindi review of the new interface text (31 keys, plus 13 counsellor labels) (user)
- [ ] Clinician for the knowledge base; counsellor for "must inform" and G6PD (user)
- [ ] Phase 5 analytics endpoints, then wire the six dashboard charts to the kit
- [ ] Commit and push when asked
