# Content review log

**Sub-phase:** 4.1. This records who reviewed what in the knowledge base (`backend/app/kb/content/`) and where each piece came from. It is kept by hand. The front matter of each file must agree with it, and `app/kb/ingest.py` refuses any file whose front matter is missing.

## Status on 9 Nov 2026

**Nothing has been reviewed by a clinician or a native speaker yet.** Every document is a draft, and the app labels answers built from it as reviewed text only in the sense that the wording rules have passed. The pitch must not call this content clinically reviewed.

## Review log

| Document | Languages | Level | Version | Written by | Clinical review | Language review |
|---|---|---|---|---|---|---|
| `carrier_basics` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `recessive_inheritance` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `x_linked` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `related_couples` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `alpha_thal` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `beta_thal` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `sickle_cell` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `cystic_fibrosis` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `sma` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `cah` | en | simple | 1 | Team (AI-assisted) | Not yet | |
| `g6pd_def` | en | simple | 1 | Team (AI-assisted) | Not yet. The G6PD rule also waits on a counsellor | |
| `dmd` | en | simple | 1 | Team (AI-assisted) | Not yet | |

English only. The Arabic interface was drafted on 15 Nov 2026, but these are clinical passages: they wait on a reviewer, so an Arabic question gets the English answer with a note saying so. The Hindi set was removed on 16 Nov 2026 with the India pack.

## Coverage (V4.1.6)

All 12 documents exist in English at the Simple level. No language has Standard or Detailed documents yet. Retrieval never crosses levels (V4.1.2), so at those levels the answer is the reviewed template with no retrieved passage. It's still correct, just less detailed.

## Risk wording per condition (V4.1.7)

Answers never state a chance themselves: numbers come only from the risk engine, filled into `{fact:ID}` placeholders, and the validators block free numbers. Wording that allows for reduced penetrance or variable severity (for example G6PD, CAH, alpha thalassaemia) is **not yet signed off**: it needs the clinician named above.

## Faith and culture content (V4.1.8)

There is none. It is left out until a pack asks for it and someone from that community reviews it.

## Source licences (M7)

| Source | Used for | Licence | Status |
|---|---|---|---|
| Team-written text | All 12 documents | Ours | No outside text was copied |
| Risk figures | None in the documents | Not applicable | Figures come from `backend/app/risk_engine`, cited per rule in `docs/clinical/risk_rules_review.md` |

When outside material is adapted later, each source gets a row here with its licence before the document is merged.
