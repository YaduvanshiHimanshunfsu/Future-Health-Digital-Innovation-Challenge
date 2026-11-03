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
