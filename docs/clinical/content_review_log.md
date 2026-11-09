# Content review log

**Sub-phase:** 4.1. This records who reviewed what in the knowledge base (`backend/app/kb/content/`) and where each piece came from. It is kept by hand. The front matter of each file must agree with it, and `app/kb/ingest.py` refuses any file whose front matter is missing.

## Status on 9 Nov 2026

**Nothing has been reviewed by a clinician or a native speaker yet.** Every document is a draft, and the app labels answers built from it as reviewed text only in the sense that the wording rules have passed. The pitch must not call this content clinically reviewed.

## Review log

| Document | Languages | Level | Version | Written by | Clinical review | Language review |
|---|---|---|---|---|---|---|
| `carrier_basics` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `recessive_inheritance` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `x_linked` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `related_couples` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `alpha_thal` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `beta_thal` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `sickle_cell` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `cystic_fibrosis` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `sma` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `cah` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |
| `g6pd_def` | en, hi | simple | 1 | Team (AI-assisted) | Not yet. The G6PD rule also waits on a counsellor | Hindi: not yet |
| `dmd` | en, hi | simple | 1 | Team (AI-assisted) | Not yet | Hindi: not yet |

Arabic has no documents. Arabic text waits on the user's approval and a reviewer (CLAUDE.md rule 5), so Arabic questions get the English answer with a note saying so.

## Coverage (V4.1.6)

All 12 documents exist in English and Hindi at the Simple level. No language has Standard or Detailed documents yet. Retrieval never crosses levels (V4.1.2), so at those levels the answer is the reviewed template with no retrieved passage. It's still correct, just less detailed.

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
