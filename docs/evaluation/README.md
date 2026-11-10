# Evaluation

Measured results, including every failure. Generated reports say so at the top; don't edit them by hand, re-run the script.

| File | What it is | Made by |
|---|---|---|
| [safety_and_accuracy_report.md](safety_and_accuracy_report.md) | The summary: method, results per language, failures, limits | By hand, from the reports below |
| `router_early_eval.md` | Router, rules only: hold-out and development sets | `scripts/eval_router.py` |
| `router_model_eval_<model>.md` | Router with a model's escalate-only second opinion | `scripts/eval_router.py --model ollama` |
| `answers_eval_template.md` | 96 golden and red-team answers, templates only | `scripts/eval_answers.py` |
| `answers_eval_<model>.md` | The same 96, with a model drafting and double-checking | `scripts/eval_answers.py --model ollama` |
| [human_scoring_sheet.md](human_scoring_sheet.md) | How two people score a sample by hand | By hand; not done yet |
| [comprehension_test_protocol.md](comprehension_test_protocol.md) | The volunteer test | Ready; not run |
| [comprehension_test_results.md](comprehension_test_results.md) | Its results | None yet, and none simulated |

Run all of them with `python Run_Samvid.py --eval`.

**Rule:** every question set was drafted by the team, not native speakers, and Arabic is in Roman letters. The hold-out router set is never used to tune the rules.
