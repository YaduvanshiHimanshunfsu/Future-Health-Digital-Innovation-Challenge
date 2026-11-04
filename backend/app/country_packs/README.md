# Country packs loader [NEW]

Loads and validates the active country pack from `backend/packs/`. See [docs/07](../../../docs/07_Global_Design_and_Country_Packs.md).

**Rules:** core code reads country-specific values only through this package.

**Status:** stubs only. No code until requested.

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `schema.py` | Pack schema | 2.6 | S9, G3, G4 |
| `loader.py` | Loads and validates the active pack | 2.6 | S9, G1–G6 |
