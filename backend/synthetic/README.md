# Synthetic data

Generator and demo personas. Output goes in `out/`, which Git ignores.

**Rules:** Never real data. Every scenario must be represented.

**Status:** built in Phase 2. Run `uv run python -m synthetic.generate`.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `generate.py` | Synthetic population. | 2.2 | M3 |
| `personas.yaml` | Named demo personas. | 2.2 | C3, C4 |
