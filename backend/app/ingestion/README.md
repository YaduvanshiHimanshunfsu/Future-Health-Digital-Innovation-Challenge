# Ingestion

Lab results to minimal, encrypted findings. Requirements R4 and R5.

**Rules:** Benign variants are dropped. Triage runs on arrival (C8).

**Status:** built and tested in Phase 2. Signed lab reports remain a limitation: see `lab_attestation`.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `fhir_parser.py` | Parses FHIR bundles. | 2.3 | M8 |
| `loinc.py` | LOINC and answer-code constants. | 2.3 |  |
| `service.py` | Ingestion use-case. | 2.3 | C1, C8, H7, M8, M10 |
