# Tests

`unit/`, `api/`, `eval/`.

**Rules:** Tests in the phase checks must exist before a sub-phase is called done.

**Status:** foundation tests are real, and other files are stubs until their phase.

## Sub-folders

- `api/`
- `eval/`
- `unit/`

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `conftest.py` | Shared fixtures. | 1.3 |  |
