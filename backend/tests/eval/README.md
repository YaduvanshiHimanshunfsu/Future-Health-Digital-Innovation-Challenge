# Evaluation sets

Golden and red-team sets. `.jsonl` stubs are empty because JSON Lines can't hold comments. Each line will be one case: question, language, expected label, key facts.

**Rules:** Arabic and Hindi items are written by native speakers. Report per language.

**Status:** the golden and red-team sets are stubs for Phase 6.1. The two router sets are the Phase 4 early evaluation.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `golden_qa.jsonl` | Golden questions: 150+ with expected labels and key facts. | 6.1 | C6 |
| `redteam.jsonl` | Red-team prompts: 50+. | 6.1 | H12 |
| `test_llm_eval.py` | Runs golden and red-team sets. | 6.1 | C5, H12 |
| `router_early.jsonl` | Early router check, 84 questions in English, Hindi and Arabic (Roman letters). The development set: it shaped the rules after the first run, so it now guards against regressions (`test_the_development_set_has_no_dangerous_misses`). | 4.3 | C6 |
| `router_holdout.jsonl` | 59 questions written after the rules were fixed. Never used to tune them: its score is the honest one. | 4.3 | C6 |

Both router sets were drafted by the team, not by native speakers, and each Arabic line carries its meaning. Run `cd backend && uv run python ../scripts/eval_router.py`; it writes `docs/evaluation/router_early_eval.md`.
