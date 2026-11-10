"""Not built, and not claimed. The couple match compares both partners' findings on the server.

What it does guarantee is minimal disclosure: only the view built for each partner leaves the
server, and a partner's other findings appear in no response, log or AI context (`matching.py`, and
`tests/api/test_matching.py` scans for exactly that). Private set intersection would matter for
partners tested at different institutions, which is a later step, and
`docs/submission/judge_qa.md` states the limits plainly.
"""
