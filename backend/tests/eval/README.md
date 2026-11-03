# Evaluation sets

Golden and red-team sets. `.jsonl` stubs are empty because JSON Lines can't hold comments. Each line will be one case: question, language, expected label, key facts.

**Rules:** Arabic items are written by Arabic speakers. Report per language.

**Status:** stubs only. No code until requested.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `golden_qa.jsonl` | Golden questions: 150+ with expected labels and key facts. | 6.1 | C6 |
| `redteam.jsonl` | Red-team prompts: 50+. | 6.1 | H12 |
| `test_llm_eval.py` | Runs golden and red-team sets. | 6.1 | C5, H12 |
