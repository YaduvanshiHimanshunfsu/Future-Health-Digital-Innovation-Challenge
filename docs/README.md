# Documentation Map

## Start here

| If you want to… | Read |
|---|---|
| See what's wrong and what to do first | [04 Review](04_Project_Review_Issues_and_Improvements.md) |
| See the plan and what to do next | [Phase overview](phases/00_PHASE_OVERVIEW.md) |
| See what happened and why | [brain.md](../brain.md) |
| Find a file | [05 Project structure](05_Project_Structure.md) |
| Check that a requirement is covered | [06 Traceability](06_Traceability_Matrix.md) |

## All documents

| Document | Contents |
|---|---|
| [problem statement.md](../problem%20statement.md) | The challenge text, with requirements R1–R6 |
| [01 Problem understanding](01_Problem_Understanding.md) | Context, evidence, stakeholders. *Dates out of date (S1)* |
| [02 Solution and plan](02_Solution_Architecture_and_Plan.md) | Feasibility, design per requirement, stack. *Phase dates out of date* |
| [03 Features and roadmap](03_Features_Limitations_Roadmap.md) | Features F1–F26, limits, roadmap, targets |
| [backend.md](backend.md) | Backend diagrams, workflows, security, and code spec. *Has known bugs: read with 04* |
| [frontend.md](frontend.md) | Design system, Stitch prompts, charts, motion |
| [04 Review](04_Project_Review_Issues_and_Improvements.md) | Issues S1–S8, C1–C10, H1–H19, M1–M13 |
| [05 Structure](05_Project_Structure.md) | Every folder and file, with purpose, phase and issues |
| [06 Traceability](06_Traceability_Matrix.md) | Requirements to code to tests to checks |
| [phases/](phases/00_PHASE_OVERVIEW.md) | 6 phases, sub-phases, goals, objectives, checks |
| [submission/](submission/) · [clinical/](clinical/) · [compliance/](compliance/) · [security/](security/) · [evaluation/](evaluation/) | Skeleton documents, filled in during the phases |

## Where the architecture and workflows are documented

| Topic | Location |
|---|---|
| Merged concept and safety layers | `02` §2 |
| System context, layers, request lifecycle, data model, deployment | `backend.md` §3 |
| Ingestion, risk logic, chat pipeline, matching, invitations, revocation, pathway, triage | `backend.md` §7 |
| Security model | `backend.md` §8 |
| Site map and screen-to-endpoint table | `frontend.md` §4 |

## When documents disagree

Higher in this list wins:

1. The live competition portal and rules
2. 04 Review
3. Phase plans
4. `backend.md` and `frontend.md`
5. `02`, `03`, `01`

The original specs have **not** been corrected. The review is the record of what needs to change.
