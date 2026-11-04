# CLAUDE.md: Rules for AI assistants on this project

**Project:** Samvid, by team Vigyan_Viveka_Vijaya, for the Future Health Digital Innovation Challenge 2026, Fertility Challenge 03.
**Location:** `E:\Competition\Future Health`

## Always

1. **Read the latest entries in [brain.md](brain.md) first, and add an entry before finishing.** This is mandatory. The rules and template are at the top of that file. Never edit past entries.
2. **No implementation code until the user explicitly asks.** Files are documentation-only stubs for now. When asked, implement only what was named, then remove that file's `STUB` header.
3. **Don't commit or push unless asked.**
4. **Follow the plan.** Work from [docs/phases/](docs/phases/00_PHASE_OVERVIEW.md). A sub-phase is done only when its cross-verification checks have evidence.
5. **No Arabic or Urdu script in project files.** Write in English, and spell any Arabic examples in Roman letters with their meaning. The product supports English, Arabic and Hindi, so ask the user before adding Arabic interface text or test data. Hindi may be written in Devanagari.
6. **Global by design.** Nothing country-specific goes in the core. It goes in a country pack (see [docs/07](docs/07_Global_Design_and_Country_Packs.md)), with Abu Dhabi as the first reference pack and India as an illustrative second pack. Don't claim a country is supported without a reviewed pack.
7. **Close the listed issues.** Each stub's header lists issue IDs from the [review](docs/04_Project_Review_Issues_and_Improvements.md). The spec's code has known bugs, so don't copy it unchanged.

## Work split and code standard

- **Claude:** backend, security and database code, Stitch prompts, and integrating the backend into the frontend.
- **User:** builds the frontend screens with Google Stitch or a similar tool: multi-page, light theme, glossy, animated, fully dynamic.
- **Code standard:** complete, secure code with strong logic and no shortcuts. Write as a careful engineer would: natural naming, comments only where the reason isn't obvious, no boilerplate.
- **Phases start only on the user's explicit command.**

## Which document wins

Listed in order of priority:

1. Competition portal (live page and rules)
2. [docs/04 review](docs/04_Project_Review_Issues_and_Improvements.md)
3. [docs/07 global design](docs/07_Global_Design_and_Country_Packs.md)
4. [docs/phases/](docs/phases/00_PHASE_OVERVIEW.md)
5. [docs/backend.md](docs/backend.md) and [docs/frontend.md](docs/frontend.md)
6. `docs/02`, `docs/03`, `docs/01`

## Dates

The team is registered (confirmed by the user on 5 Nov 2026). Prototype due **20 Nov 2026**, with a target of 19 Nov. Official requirements are in [docs/submission/competition_requirements.md](docs/submission/competition_requirements.md).

## Safety rules that must never be broken

- **Numbers come from code.** The risk engine is pure and deterministic. An LLM never computes or writes risk numbers.
- **Uncertain means no number.** A VUS, unknown gene or missing data produces no number, and goes to a human.
- **"No data" is not "no risk".** Never report a negative result when the system couldn't determine one.
- **Never direct a decision.** Don't recommend whether to marry, conceive or use an option. Cancelled marriages are never a success metric.
- **Never diagnose or give false certainty.** That includes "you are healthy".
- **One person's data never reaches another without consent,** in any response field, log, ID or prompt.
- **Fail closed.** Authorisation, redaction or validation errors mean deny or a safe fallback.
- **AI answers stay on the education side of the boundary.** Clinical questions and distress go to humans.
- **Synthetic data only.** No real genetic or personal data anywhere. Label demo numbers as synthetic. Declare every data source in [docs/submission/data_sources.md](docs/submission/data_sources.md).
- **Every supported language is first-class.** Test every text rule in each language and dialect, including Arabic, Gulf dialect and Hindi, for example `hamil` means both "pregnant" and "carrier".
- **Don't overclaim.** Pitch and docs must match what the code does, and mocks are labelled as mocks.

## Environment notes

Windows machine with Docker, uv and Node. System Python is 3.11, and the project needs 3.12 (`uv` can install it). `openmined.psi` has no Windows wheels, so keep it optional or use Docker or WSL.
