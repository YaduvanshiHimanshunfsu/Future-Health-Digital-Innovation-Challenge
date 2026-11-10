"""Superseded by `scripts/eval_router.py` and `scripts/eval_answers.py`.

The evaluations run as scripts, not as tests, because they need a real model, take half an hour, and
produce a report to read rather than a pass or fail. What belongs in the test suite is the
regression gate: `tests/unit/test_router.py::test_the_development_set_has_no_dangerous_misses`.
Run them with `python Run_Samvid.py --eval`; reports land in `docs/evaluation/`.
"""
