# Care pathway

State machine, FHIR mapping, stall detection. Requirement R5.

**Rules:** All changes go through one function. Declining is always possible and is never a failure.

**Status:** stubs only. No code until requested.

## Files

| File | Purpose | Phase | Issues |
|---|---|---|---|
| `fhir_mapper.py` | FHIR resources. | 5.2 |  |
| `scheduler.py` | SLA scan. | 5.1 | H10, H15 |
| `state_machine.py` | Pathway transitions. | 5.1 | H10 |
