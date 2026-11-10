"""Superseded. The free-number and label-binding checks live in `rules.py`, with their word and phrase tables in
`patterns.py`, the text normalising in `text.py`, and the order they run in `pipeline.py`.

They were built as one module because every check shares the same normalised text and the same
`Flag` result, and splitting them meant normalising each answer five times. Nothing imports this
file. See `tests/unit/test_validators.py`.
"""
