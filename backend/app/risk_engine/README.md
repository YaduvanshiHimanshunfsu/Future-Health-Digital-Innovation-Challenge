# Risk engine

Deterministic risk maths. Requirement R1.

**Rules:** **Pure:** no I/O, no database, no LLM. Uncertain means no number. Most critical code in the project (C3, C4, C7, H1–H5).

**Status:** stubs only. No code until requested.

## Sub-folders

- `data/`

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `engine.py` | Orchestrates the rules. | 2.4 | C3, C4, C7, H1, H2, H3, H4, H5 |
| `frequencies.py` | Carrier frequency table. | 2.4 | H2 |
| `rules.py` | Mendelian maths. | 2.4 | C3, C4, H1, H5 |
| `types.py` | Domain types. | 2.4 | C3, C4 |
| `visuals.py` | Visual specs. | 2.5 | H5 |
