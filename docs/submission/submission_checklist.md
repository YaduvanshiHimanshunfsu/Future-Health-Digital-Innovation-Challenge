# Submission checklist

Final check before submitting on **19 Nov 2026** (deadline 20 Nov). A second person ticks each item against the portal (V6.6.1).

## Required items

| Item | Where | State on 10 Nov |
|---|---|---|
| Working prototype | `python Run_Samvid.py` | Done; runs from one command |
| Technical documentation | [technical_documentation.md](technical_documentation.md) | Done |
| Assumptions, dependencies and limitations | [assumptions_and_limitations.md](assumptions_and_limitations.md) | Done |
| Every data source declared | [data_sources.md](data_sources.md) | Done; recheck against the code on the day (V6.4.7) |
| Maturity statement | [maturity_statement.md](maturity_statement.md) | Done |
| Code shareable, with no secrets | gitleaks over full history: clean (`docs/security/scans/`) | Done; rerun on the release commit |
| Anything else in the full requirements | [competition_requirements.md](competition_requirements.md) | **Find the registration email's requirements** and add them |

## Also submit

- [ ] Demo video, 3 to 5 minutes, recorded from [demo_script.md](demo_script.md) in template mode
- [ ] Pitch deck from [pitch_deck_outline.md](pitch_deck_outline.md)
- [ ] Safety report: [docs/evaluation/safety_and_accuracy_report.md](../evaluation/safety_and_accuracy_report.md)

## Needs people (can't be done by the build)

- [ ] Native-speaker check of the Arabic text
- [ ] Two independent scorers fill in [human_scoring_sheet.md](../evaluation/human_scoring_sheet.md)
- [ ] Ethics answer, then the volunteer comprehension test, or a note that it didn't run
- [ ] A new Gemini API key, if the demo should use Gemini (Ollama works without one)
- [ ] Someone outside the team runs the demo from the README alone, timed (V6.4.1)
- [ ] A rehearsal with a recorded backup

## Links tested logged out

- [ ] Every link in the submission opens in a private window (V6.6.4)

## Release tag

- [ ] Commit the final state, tag it (for example `v1.0-submission`), and build it from a clean clone (V6.6.2). Only the team commits and tags.

## Confirmation saved

- [ ] Screenshot or email of the portal's confirmation, saved in `docs/submission/evidence/` (V6.6.3)
- [ ] Who would present at GITEX, 7 to 11 Dec, if placed (V6.6.6)
