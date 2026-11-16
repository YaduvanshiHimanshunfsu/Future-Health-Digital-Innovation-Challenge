# 02 — Feasibility, Technical Design, Tech Stack & 6-Phase Plan

> **This is a design document, not a statement of what is built.** Where it describes content as
> reviewed, or a feature as present, read it as the intent. For what actually exists and what
> doesn't, see [docs/phases/CROSS_VERIFICATION.md](phases/CROSS_VERIFICATION.md) and
> [docs/submission/assumptions_and_limitations.md](submission/assumptions_and_limitations.md).

> **Scope update (5 Nov 2026):** Samvid is global by design. UAE and Abu Dhabi details in this document describe the first reference pack, not the limit of the product. Supported languages are English and Arabic. See [docs/07](07_Global_Design_and_Country_Packs.md).
>
> **Scope update (16 Nov 2026):** the prototype ships one country pack, Abu Dhabi, in English with an Arabic translation. The pack framework stays, so another country is settings rather than code, but no second pack is shipped or claimed.

> Companion to [01_Problem_Understanding.md](01_Problem_Understanding.md). This document is backend-first. The frontend is generated with **Google Stitch** (or a similar tool) and wired to the backend through a typed OpenAPI client.

---

## 1. Feasibility assessment

| Dimension | Verdict | Reasoning |
|---|---|---|
| **Technical** | ✅ High | Every component exists as mature open-source or cloud technology: Mendelian risk maths, RAG, ReBAC authorisation, PSI cryptography, FHIR. The novelty lies in **combining** them safely, not in inventing new science. |
| **Data** | ✅ Feasible with synthetic data | Real Emirati genomic data is not accessible, and must not be, for a hackathon. We generate **synthetic carrier reports** from published carrier frequencies (CTGA, gnomAD Middle-Eastern subset, Dubai and Abu Dhabi published conditions) and design to the **FHIR Genomics** format so real lab feeds can plug in later. |
| **Clinical safety** | ⚠ Medium (managed) | LLMs make errors (see JAMIA 2024). Mitigation: **the LLM never computes risk**. All numbers come from a deterministic, tested engine. The LLM only *phrases* pre-verified facts, and validators check every output. Clinical advice is always routed to humans. |
| **Regulatory** | ⚠ Medium | UAE Federal Law No. 2 of 2019 (health ICT) requires **in-country data storage** (Art. 13). The UAE PDPL and DoH **ADHICS** cybersecurity standard also apply. Design: UAE-region hosting (Azure UAE North / Core42), encryption, audit, consent. A pilot would need DoH approval. |
| **Cultural** | ⚠ Medium (core differentiator) | Requires Arabic-first content, a non-stigmatising lexicon and non-directive framing. We build a **lexicon guard** and plan validation with Emirati users and counsellors. |
| **Time (5 to 20 Nov 2026)** | ⚠ Tight, feasible with scope tiers | Scope: a working backend with all six requirements demonstrable end-to-end on synthetic data, plus Stitch UI screens and a metrics dashboard. |
| **Commercial / deployment** | ✅ Strong | Plugs into existing DoH screening, Malaffi and Al Amal pathways, and lowers counsellor workload, so there is a clear pilot path. |

---

## 2. Merging the different approaches into one solution

Each existing approach solves one part of the problem. We take the strongest idea from each and drop its weakness.

| Approach (prior work) | What we **take** | What we **avoid** |
|---|---|---|
| **National premarital programmes** (UAE, KSA, Iran, Cyprus) | Integration with mandatory screening, primary-care counselling, funded IVF/PGT | Treating marriage cancellation as success; a "certificate-only" process with no comprehension check |
| **Dor Yeshorim** (anonymous matching) | **Couple-only compatibility mode**: partners learn *whether* they share a risk without revealing each other's other carrier results | Withholding results from individuals by force. In our system blind matching is **opt-in**, and the person can always see their own result |
| **Chatbot counselling (Gia, LLM studies)** | 24/7, scalable, multilingual education; family-sharing links | Free-form LLM risk statements; unclear education vs advice boundary |
| **Decision aids (Ottawa, MMIC)** | Values clarification, balanced option cards, validated measurement (MMIC, SURE, GCOS) | Static leaflets that are not personalised |
| **Genomic privacy cryptography (PSI, HE)** | Private set intersection for compatibility; data minimisation | Heavy FHE that is too slow or complex for the MVP (kept for the roadmap) |
| **Dynamic consent / ReBAC** | Granular, revocable, per-relative, per-field sharing with a full audit trail | Blanket "I agree" consent |
| **Cascade testing tools (family letters)** | **Anonymous relative invitations** ("someone in your family suggests free screening") | Naming the index person without their consent |

### The merged concept: **Samvid**, a privacy-first "genetic result companion"

```
         ┌──────────────── Deterministic core (safe) ────────────────┐
Result ─►│ Normalise → Risk Engine → RiskFacts (numbers + provenance) │
         └──────────────────────────────┬─────────────────────────────┘
                                        ▼
         ┌──────────── AI explanation layer (constrained) ───────────┐
User Q ─►│ Boundary router → RAG (curated AR/EN) → LLM phrasing       │──► Validators ──► Answer
         │ (education | decision support | clinical → HUMAN)         │     (numbers, stigma,
         └──────────────────────────────┬────────────────────────────┘      directiveness, reading level)
                                        ▼
         ┌─────── Human counselling + care pathway (traceable) ──────┐
         │ Triage → Counsellor queue (SLA) → Confirmatory test →      │
         │ Reproductive genomics (IVF/PGT-M, Al Amal) → Closed loop   │
         └──────────────────────────────┬────────────────────────────┘
                                        ▼
         ┌──────── Privacy fabric (cross-cutting, everywhere) ───────┐
         │ Consent ledger · ReBAC (partner/family) · PSI matching ·   │
         │ Field encryption · Hash-chained audit · "Who saw my data"  │
         └──────────────────────────────┬────────────────────────────┘
                                        ▼
         ┌──────── Measurement layer (Requirement 6) ────────────────┐
         │ Teach-back quiz · MMIC · SURE · time-to-referral ·         │
         │ fairness by language/literacy · privacy incidents          │
         └────────────────────────────────────────────────────────────┘
```

**Design principle:** *Numbers from code, words from AI, decisions from people, data stays with its owner.*

---

## 3. How each requirement is solved (technical detail)

### R1. Risk explanation

**3.1.1 Result normalisation**
- Input formats: FHIR Genomics Reporting (`DiagnosticReport` + `Observation` with variant components), a lab CSV, or VCF. For the MVP, a synthetic JSON or FHIR bundle.
- Output: a **minimal carrier summary** per person: `{gene, hgvs, classification (P/LP/VUS), zygosity, inheritance (AR/XL), condition_ids (OMIM/Orphanet)}`.
- **Data minimisation:** raw VCF is never stored in the app DB. Only reportable findings are kept, encrypted at field level.

**3.1.2 Deterministic Risk Engine** (pure Python, versioned, 100% unit-tested)

| Scenario | Rule |
|---|---|
| Both partners P/LP in same AR gene | Child affected 25%, carrier 50%, unaffected non-carrier 25%, **per pregnancy** |
| One partner P/LP, other negative for that gene | Residual: `P(B carrier | neg) = q(1−d) / (1 − q·d)` (q = carrier frequency, d = detection rate), so child risk = `P × 1/4` |
| One partner P/LP, other **untested** | Child risk = `q_pop × 1/4`. If consanguineous, use the kinship-adjusted probability that the partner shares the allele (e.g., first cousins: ~1/8 + (7/8)q) |
| Female P/LP in X-linked gene | Each son 50% affected, each daughter 50% carrier |
| VUS in either partner | **No numeric risk is generated.** Mark as `uncertain` and always escalate to counsellor review |
| Consanguinity, both negative | Present the empiric residual risk for genes outside the panel (NSGC: first cousins +1.7–2.8% over the 3–4% baseline). Suggest extended screening (ACMG Tier 4) as an **option** |
| Homozygous / compound findings, or an adult with possible disease | Out of scope for education. **Urgent escalation** (possible diagnosis, not carrier status) |

Every output is a `RiskFact` object: `{statement_id, value, unit, scenario, inputs_hash, rule_version, source_citation}`. The LLM receives these and **may not change them**.

**3.1.3 Explanation generation**
- **Condition cards** (curated, clinician-reviewed) for the most common conditions in the Abu Dhabi panel findings: thalassaemia, SCD, CAH, inherited retinal disorders, PCD, SMA, glaucoma, G6PD, etc. Sources: [MedlinePlus Genetics](https://medlineplus.gov/genetics/) (public domain), [GeneReviews](https://www.ncbi.nlm.nih.gov/books/NBK1116/), [Orphanet](https://www.orpha.net), [CTGA](https://cags.org.ae/en/ctga-overview).
- **Three literacy levels** (simple / standard / detailed) × **English + Arabic (MSA and Gulf-friendly)**, with later expansion (Urdu, Malayalam, Tagalog, Bengali, Tagalog, Malayalam for residents).
- **Visuals generated by the backend as JSON specs**: a 100-person icon array, a Punnett square and a family-tree sketch, rendered by the frontend.
- **Uncertainty language templates**: "A negative result lowers, but does not remove, the chance…"; "Being a carrier is not an illness."

**3.1.4 Output validators** (run on every AI answer)
1. **Numeric consistency**: every number or percentage in the text must match a `RiskFact`. Otherwise the answer is blocked and regenerated, or falls back to a template.
2. **Stigma lexicon guard**: an Arabic and English blocklist with replacements (e.g., "defective genes" → "a gene change"; "incompatible couple" → "a couple with a shared genetic finding"; "bad blood" is banned).
3. **Directiveness detector**: an LLM-as-judge plus regex flags imperative or judgmental advice ("you should not marry", "you must do IVF").
4. **Diagnosis-claim detector**: blocks "your child will have…" and "you have the disease".
5. **Reading-level check**: Flesch-Kincaid (EN) and [OSMAN Arabic readability](https://github.com/drelhaj/OsmanReadability) (AR).

### R2. Informed, values-sensitive choices
- **Options engine**: returns *all* clinically appropriate options for the scenario with equal visual weight, in a neutral order (or randomised): proceed and natural conception (with optional prenatal diagnosis), IVF + PGT-M (with Al Amal eligibility info), donor gametes, adoption, more testing, more time to think.
- **Values clarification** (Ottawa decision-aid style): sliders such as "importance of having a biological child", "comfort with medical procedures", "role of family in this decision", "faith considerations". These are **reflected back** to the user and **never scored into a recommendation**.
- **Faith-sensitive content**: a neutral library of published religious rulings on IVF/PGT (to be reviewed by an Islamic scholar advisor) that the user can open *only on request*.
- **Access**: a finder for screening and counselling centres (22 primary-care centres), plus a pre-conception screening request flow for couples who are already married.

### R3. Qualified human counselling and the boundary
**Boundary router** (classifier: fine-tuned small model plus rules) labels each user turn:

| Label | System behaviour |
|---|---|
| `EDUCATION` | AI answers from curated content |
| `DECISION_SUPPORT` | AI shows options and values tools, never a recommendation |
| `CLINICAL_ADVICE` ("Should I do PGT?", "Is my pregnancy affected?") | AI says it cannot advise, explains why, and **offers booking** with a counsellor |
| `DISTRESS / SAFETY` | Immediate supportive message, a hotline, and an urgent human flag |

**Triage score** creates a counsellor case automatically:

| Priority | Triggers | SLA (configurable) |
|---|---|---|
| P1 Urgent | At-risk couple **and currently pregnant**; distress cues; possible affected adult (homozygous) | 24 h |
| P2 High | At-risk couple (same gene, P/LP); X-linked carrier female; multiple shared genes | 72 h |
| P3 Standard | VUS; consanguineous couple asking about extended testing; repeated confusion (failed teach-back twice) | 7 days |
| P4 Optional | Single carrier who asks for a human | Next available |

**Counsellor co-pilot**: the case arrives with a structured, **human-verified** summary (RiskFacts, the questions asked, comprehension score, values notes the user *chose* to share). The counsellor's notes are their own. The AI never writes clinical advice into the record.

### R4. Privacy-preserving family workflows
**Sharing modes with a partner (each partner chooses):**
1. **Private**: nothing shared.
2. **Couple-match only (blind)**: a private set intersection (PSI) over the two partners' P/LP gene sets reveals **only the shared genes** (or only "shared: yes/no"). Each partner's *other* carrier findings stay private. This is Dor Yeshorim's idea with cryptographic guarantees and individual choice.
   - MVP implementation: [OpenMined PSI](https://github.com/OpenMined/PSI) (ECDH-PSI, Python bindings). Optional: PSI-cardinality to reveal only the *count*.
3. **Full share**: a selected report, with field-level choice (e.g., share gene names but not variant details).

**Family cascade (relatives):**
- **Anonymous invitation**: the user picks a relationship type (sibling, cousin, parent) and the system generates a link or SMS: *"A family member recommends free genetic screening. Here is what it involves."* No name or result is included unless the user opts in.
- **Named disclosure**: only with explicit consent, scoped to a specific relative and a chosen subset, time-limited, and revocable.
- **Elders and guardians**: a "family-level education" pack about recessive inheritance in general that contains **no individual data**.

**Authorisation model:** relationship-based access control with [OpenFGA](https://github.com/openfga/openfga) (Google Zanzibar style):
```
type user
type report
  relations
    define owner: [user]
    define partner_match_viewer: [user]   # sees only PSI output
    define full_viewer: [user]
    define counsellor: [user]             # assigned clinician only
    define can_view_full: owner or full_viewer or counsellor
```
Plus RBAC roles via Keycloak: `individual`, `counsellor`, `physician`, `program_admin`, `auditor`.

**Consent ledger** (dynamic consent): every consent is a versioned record `{who, what_data, to_whom, purpose, expiry, revoked_at}`, with purposes coded after the [GA4GH Data Use Ontology (DUO)](https://github.com/EBISPOT/DUO). Revocation takes effect immediately in OpenFGA.

**Audit:** an append-only, **hash-chained** audit log where each entry holds the SHA-256 of the previous one, so tampering is evident (optional: [immudb](https://github.com/codenotary/immudb)). Users get a *"Who viewed my data"* screen. Access by counsellors outside their assigned case requires **break-glass** with a stated reason and is flagged.

**Encryption:** TLS 1.3 in transit. AES-256-GCM **envelope encryption** at field level for genetic findings, with keys in [HashiCorp Vault](https://github.com/hashicorp/vault) or Azure Key Vault (UAE region). PII is redacted before any LLM call with [Microsoft Presidio](https://github.com/microsoft/presidio). The LLM sees only "gene: HBB, status: carrier", never names or IDs.

### R5. Safe linkage to services
**Care-pathway state machine** (each transition timestamped and audited):
```
RESULT_RELEASED → EDUCATION_VIEWED → COMPREHENSION_CHECKED
   → COUNSELLING_REQUESTED → COUNSELLING_BOOKED → COUNSELLING_DONE
   → CONFIRMATORY_TEST_ORDERED → CONFIRMED
   → REPRO_GENOMICS_REFERRED (IVF/PGT-M, Al Amal) → REFERRAL_ACCEPTED → CLOSED
   (each step may also lead to: DECLINED_BY_USER (valid choice, not a failure) | LOST_TO_FOLLOW_UP (alert))
```
- Modelled as FHIR `ServiceRequest` / `Task` / `Appointment` resources ([HL7 FHIR Genomics Reporting IG](https://hl7.org/fhir/uv/genomics-reporting/), [HAPI FHIR](https://github.com/hapifhir/hapi-fhir)), so integration with **Malaffi** is a mapping exercise, not a rewrite.
- **Stall detector**: a scheduled job flags cases stuck past their SLA, then nudges the user (gently and opt-out-able) and alerts the care coordinator.
- MVP: a simple state machine in Postgres plus an APScheduler or Celery beat job. Roadmap: [Temporal](https://github.com/temporalio/temporal) for durable workflows.

### R6. Measurable comprehension and access
| Metric | How we measure it |
|---|---|
| **Comprehension** | Pre/post **teach-back quiz** (5 adaptive items: "If both of you are carriers, what is the chance for each pregnancy?"); knowledge sub-scale of an **MMIC** adaptation |
| **Informed choice** | MMIC (knowledge + attitude + deliberation), **SURE** 4-item decisional conflict |
| **Counselling uptake** | % of P1–P2 cases with counselling done; % of offered counselling accepted |
| **Time to appropriate referral** | Median hours from `RESULT_RELEASED` to `COUNSELLING_DONE` and to `REPRO_GENOMICS_REFERRED` |
| **Privacy protection** | Unauthorised access attempts blocked; consent revocation latency; % of shares that are scoped (not full); break-glass events; zero PII sent to the LLM (verified by tests) |
| **Equity** | Every metric stratified by **language** (AR/EN/…), **literacy level** chosen, age band, gender and region (Abu Dhabi / Al Ain / Al Dhafra), with a gap alert when a group falls more than 10 pp behind |
| **Explicitly NOT a success metric** | Marriages cancelled or reproductive choices made. These are recorded only as *anonymised, optional, aggregated* outcomes and never optimised |

Dashboards use de-identified events only. Aggregates are suppressed below k = 10 and can add differential-privacy noise ([OpenDP](https://github.com/opendp/opendp)).

---

## 4. System architecture (backend)

Built as a **modular monolith** for the hackathon (fast to build, easy to split later):

```
                        ┌──────────── Frontend (Stitch → React/Next.js) ────────────┐
                        │  Individual app · Counsellor console · Admin dashboard     │
                        └──────────────────────────┬─────────────────────────────────┘
                                                   │ HTTPS / OpenAPI (typed client)
                                     ┌─────────────▼─────────────┐
                                     │ API Gateway (FastAPI)      │◄── Keycloak (OIDC; UAE PASS mock)
                                     │ rate-limit · authN · i18n  │
                                     └─────────────┬─────────────┘
     ┌───────────────┬───────────────┬─────────────┼──────────────┬───────────────┬───────────────┐
     ▼               ▼               ▼             ▼              ▼               ▼               ▼
 ingestion      risk_engine     explain_agent   consent_share   triage_cases   care_pathway   analytics
 (FHIR/VCF→     (deterministic  (LangGraph:     (consent ledger, (score, queue, (state machine, (events, metrics,
  carrier       Mendelian       router→RAG→     OpenFGA, PSI,    SLA, counsellor FHIR Task,      fairness,
  summary)      rules)          LLM→validators) invitations)     co-pilot)       stall detector) DP/k-anon)
     │               │               │             │              │               │               │
     └───────────────┴───────┬───────┴─────────────┴──────────────┴───────────────┴───────────────┘
                             ▼
   PostgreSQL 16 (+pgvector)   Redis (cache/queues)   Vault/KMS (keys)   Audit log (hash-chain)   Object store (reports)
                             ▼
           LLM providers: Azure OpenAI (UAE North)  |  Jais / K2 via vLLM (sovereign, on-prem)  |  Template-only fallback
```

### 4.1 Core data model (simplified)
```
person(id, keycloak_sub, preferred_lang, literacy_level, region, created_at)
couple(id, person_a, person_b, relationship_degree NULLABLE, status)
genetic_report(id, person_id, source, received_at, panel_version)
carrier_finding(id, report_id, gene, hgvs_enc, classification, zygosity, inheritance, condition_ids[])
risk_fact(id, couple_id|person_id, scenario, value, rule_version, inputs_hash, citation)
consent(id, grantor, grantee|grantee_type, scope_json, purpose_duo, expires_at, revoked_at)
share_event(id, consent_id, mode{private,psi,full}, created_at)
invitation(id, sender, relation_type, token_hash, disclose_identity bool, redeemed_at)
conversation(id, person_id, lang) ; message(id, conv_id, role, boundary_label, validator_flags, content_enc)
case(id, couple_id|person_id, priority, sla_due, counsellor_id, status)
pathway_step(id, case_id, state, ts, actor, fhir_ref)
assessment(id, person_id, instrument{teachback,mmic,sure,gcos}, phase{pre,post}, score)
audit_log(id, ts, actor, action, resource, prev_hash, hash)
kb_chunk(id, condition_id, lang, level, text, embedding vector(1024), source_url, reviewed_by)
```

### 4.2 Key API endpoints (FastAPI, auto-documented OpenAPI)
```
POST /v1/reports:ingest               (lab/FHIR bundle → findings)       [lab role]
GET  /v1/me/results                   (my findings, plain-language)       [owner]
GET  /v1/me/risk                      (RiskFacts + visual specs)          [owner]
POST /v1/couples                      (link partner by invite)            [owner]
POST /v1/couples/{id}/match           (PSI couple-only compatibility)     [both consented]
POST /v1/chat                         (streamed answer + boundary label)  [owner]
GET  /v1/options?scenario=…           (balanced options cards)            [owner]
POST /v1/consents  | DELETE /v1/consents/{id}                            [owner]
POST /v1/invitations                  (anonymous relative invite)         [owner]
GET  /v1/me/access-log                (who viewed my data)                [owner]
POST /v1/cases | GET /v1/cases?queue=mine | PATCH /v1/cases/{id}          [counsellor]
POST /v1/pathway/{case}/advance                                           [counsellor/system]
POST /v1/assessments                  (teach-back, MMIC, SURE)            [owner]
GET  /v1/analytics/metrics?stratify=lang,literacy                         [program_admin]
```

### 4.3 Repository layout
```
samvid/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers (v1)
│   │   ├── core/           # config, security, i18n, logging
│   │   ├── ingestion/      # FHIR/VCF parsers → carrier summary
│   │   ├── risk_engine/    # rules.py, residual.py, xlinked.py, consanguinity.py
│   │   ├── explain/        # langgraph graph, prompts/, validators/, lexicon/
│   │   ├── kb/             # condition cards (ar/en, 3 levels), embed + ingest
│   │   ├── privacy/        # consent, openfga client, psi, crypto, audit
│   │   ├── triage/         # scoring, queues, SLA
│   │   ├── pathway/        # state machine, fhir mapping, scheduler
│   │   ├── analytics/      # events, metrics, fairness, dp
│   │   └── models/         # SQLAlchemy + Pydantic schemas
│   ├── tests/              # unit, property-based (hypothesis), LLM eval suites
│   ├── synthetic/          # synthetic population + report generator
│   └── alembic/
├── infra/                  # docker-compose, openfga model, keycloak realm
├── frontend/               # Stitch export → React components
└── docs/
```

---

## 5. Tech stack and why

| Layer | Choice | Why |
|---|---|---|
| Language | **Python 3.12** | The best ecosystem for genomics (cyvcf2, hail), AI (LangGraph, transformers) and crypto bindings |
| API | **FastAPI + Pydantic v2** | Async, fast, auto OpenAPI, so the Stitch frontend gets a generated typed client |
| DB | **PostgreSQL 16 + pgvector** | One database for relational data, JSONB and vectors. Row-level security is available |
| ORM / migrations | SQLAlchemy 2 + Alembic | Standard and reliable |
| Cache / queue | **Redis + Celery (or Arq)** | Background jobs: PSI, embeddings, SLA scans, notifications |
| Identity | **Keycloak** (OIDC) | Roles, MFA, and easy mock of **UAE PASS** (the national digital ID) |
| Authorisation | **OpenFGA** (ReBAC) | Family and partner relationships are a graph, and Zanzibar-style rules model them cleanly |
| LLM orchestration | **LangGraph** | Explicit state graph (router → retrieve → generate → validate → escalate) that is auditable and testable, unlike a free agent |
| LLM (cloud) | **Azure OpenAI (UAE North)** | Microsoft is a co-creator, and the UAE region satisfies data residency |
| LLM (sovereign / Arabic) | **Jais 2 / Jais family** ([HF: inceptionai](https://huggingface.co/inceptionai)) or **K2 Think** ([HF](https://huggingface.co/LLM360/K2-Think)) served with **vLLM** ([GitHub](https://github.com/vllm-project/vllm)) | Inception42 and MBZUAI are co-creators, Arabic quality is strong, and it can run fully on-prem |
| Embeddings | **BGE-M3** ([HF](https://huggingface.co/BAAI/bge-m3)) | Strong multilingual model with good Arabic support, 1024-dimensional |
| Guardrails | Custom validators + [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) (optional) | Rails for boundary topics; our own numeric and lexicon checks |
| PII redaction | **Microsoft Presidio** | Strips names and IDs before LLM calls, with custom Emirates ID recogniser |
| PSI | **OpenMined PSI** | Production-grade ECDH PSI with Python bindings |
| Crypto / keys | `cryptography` (AES-GCM) + **Vault / Azure Key Vault** | Envelope encryption and key rotation |
| Audit | Postgres hash-chain (MVP) → **immudb** | Tamper-evident trail |
| Interop | **FHIR R4** via `fhir.resources` + HAPI FHIR (docker) | DoH / Malaffi speak HL7, and the Genomics Reporting IG covers variants |
| Analytics privacy | **OpenDP** | Differential privacy on aggregate dashboards |
| Eval | pytest, **hypothesis** (property tests on the risk maths), [promptfoo](https://github.com/promptfoo/promptfoo) / [Ragas](https://github.com/explodinggradients/ragas) | Proves safety and accuracy to the judges with numbers |
| Speech (low literacy) | [Whisper](https://github.com/openai/whisper) (STT) + Azure Neural TTS (Arabic Gulf voices) | Voice-first mode for low-literacy users |
| Observability | OpenTelemetry + Prometheus/Grafana | Latency, validator block rate, SLA breaches |
| DevOps | Docker Compose → Azure Container Apps (UAE North) / Core42 | One-command demo, sovereign deployment path |
| Frontend | **Google Stitch** ([stitch.withgoogle.com](https://stitch.withgoogle.com)) → exported HTML/Tailwind → React (Next.js) + `openapi-typescript` client | Fast, professional UI so the team can focus on the backend |

---

## 6. External resources (papers, repos, data, standards)

### Code and libraries
| Resource | Use |
|---|---|
| [OpenMined/PSI](https://github.com/OpenMined/PSI) | Couple-only compatibility matching |
| [openfga/openfga](https://github.com/openfga/openfga) | Relationship-based access |
| [microsoft/presidio](https://github.com/microsoft/presidio) | PII de-identification |
| [microsoft/SEAL](https://github.com/microsoft/SEAL) · [OpenMined/TenSEAL](https://github.com/OpenMined/TenSEAL) · [openfheorg/openfhe-development](https://github.com/openfheorg/openfhe-development) | Homomorphic encryption (roadmap) |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | Agent workflow |
| [pgvector/pgvector](https://github.com/pgvector/pgvector) | Vector search in Postgres |
| [hapifhir/hapi-fhir](https://github.com/hapifhir/hapi-fhir) · [fhir.resources](https://github.com/nazrulworld/fhir.resources) | FHIR server / Python models |
| [brentp/cyvcf2](https://github.com/brentp/cyvcf2) | VCF parsing |
| [CCGE-BOADICEA/pedigreejs](https://github.com/CCGE-BOADICEA/pedigreejs) | Family-tree drawing (frontend) |
| [EBISPOT/DUO](https://github.com/EBISPOT/DUO) | Consent purpose codes |
| [phenopackets/phenopacket-schema](https://github.com/phenopackets/phenopacket-schema) · [ga4gh/vrs](https://github.com/ga4gh/vrs) | GA4GH genomic data standards |
| [drelhaj/OsmanReadability](https://github.com/drelhaj/OsmanReadability) | Arabic readability scoring |
| [CGT-LLM chatbot (HF Space)](https://huggingface.co/spaces/alrahrooh/cgt-llm-chatbot) | Reference RAG genetic-counselling bot (MIT) |
| [opendp/opendp](https://github.com/opendp/opendp) | Differential privacy |

### Knowledge and data sources
[ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) · [gnomAD](https://gnomad.broadinstitute.org) (carrier frequencies, including Middle Eastern ancestry) · [ClinGen](https://clinicalgenome.org) · [OMIM](https://omim.org) · [Orphanet](https://www.orpha.net) · [GeneReviews](https://www.ncbi.nlm.nih.gov/books/NBK1116/) · [MedlinePlus Genetics](https://medlineplus.gov/genetics/) · [CTGA](https://cags.org.ae/en/ctga-overview) · [UAE CTGA analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC10194840/)

### Key papers (see Doc 01 §5 for the full list)
- Gregg et al. 2021, ACMG carrier screening practice resource: [doi](https://doi.org/10.1038/s41436-021-01203-z)
- Bennett et al. 2002, NSGC consanguinity recommendations: [doi](https://doi.org/10.1023/A:1014593404915)
- Baldi et al. 2011, *Countering GATTACA* (private genomic tests): [arXiv](https://arxiv.org/abs/1110.2478)
- Kaye et al. 2015, *Dynamic consent*: [EJHG](https://www.nature.com/articles/ejhg201471)
- Dubai premarital genomic screening (Nature Medicine 2025): [summary](https://www.360dx.com/molecular-diagnostics/mandatory-premarital-genetic-carrier-screening-program-dubai-ids-risk-couples)
- JMIR Cancer 2025, LLM chatbot for returning genomic results: [paper](https://cancer.jmir.org/2025/1/e65848/PDF)
- Icon-array uncertainty RCT: [PMC9731905](https://pmc.ncbi.nlm.nih.gov/articles/PMC9731905/)

### Regulatory references
- UAE Federal Law No. 2 of 2019 (Health ICT, data localisation): [Al Tamimi overview](https://tamimi.com/law-update-articles/the-federal-law-regulating-the-use-of-information-and-communication-technology-in-the-uae-healthcare-sector) · [PwC](https://www.pwc.com/m1/en/publications/healthcare-data-protection-in-the-uae.html) · [UAE Gov portal](https://beta.government.ae/en/about-the-uae/digital-uae/whole-of-government-approach/digital-health/ict-in-the-health-sector)
- UAE PDPL (Federal Decree-Law No. 45 of 2021), DoH **ADHICS** standard, DoH AI policy. Get the official texts from DoH.

### Human help to seek (via hackathon mentors)
- **M42 / Emirati Genome Programme** for panel structure and the report format (FHIR or lab-specific).
- **DoH genetic counsellors** to review condition cards, the triage rules and the lexicon.
- **Inception42 / MBZUAI** for Jais deployment and Arabic evaluation.
- **Microsoft** for Azure UAE North credits, Azure OpenAI and Confidential Containers.
- An **Islamic bioethics advisor** for the faith-sensitive content library.

---

## 7. Project plan: 6 phases (backend-focused)

> **Superseded on 5 Nov 2026.** Current dates, goals and checks are in [docs/phases/](phases/00_PHASE_OVERVIEW.md). This section is kept for its task detail only.

### Phase 1: Foundation & design
- Finalise scope, personas and user journeys (individual, couple, counsellor, admin).
- Repo, Docker Compose (Postgres + pgvector, Redis, Keycloak, OpenFGA, HAPI FHIR), CI (lint, tests).
- FastAPI skeleton, config, logging, i18n framework (AR/EN), error model.
- Data model and Alembic migrations. Hash-chained audit-log middleware **from day one**.
- **Deliverables:** running stack, OpenAPI skeleton, ERD, threat model (STRIDE) v1.
- *Frontend track:* create Stitch designs for ~10 key screens and export Tailwind/HTML.

### Phase 2: Genomic data & deterministic risk engine
- **Synthetic data generator**: ~2,000 synthetic people and 1,000 couples, with carrier frequencies for ~30 panel genes, optional consanguinity labels (first or second cousin), and VUS and X-linked cases. Output as FHIR Genomics bundles.
- Ingestion: FHIR/JSON → `carrier_finding` (encrypted fields).
- Risk engine: AR, X-linked, residual, untested partner, consanguinity, and VUS handling. Produces `RiskFact` objects with citations.
- **Property-based tests** with hypothesis (probabilities sum to 1; risk never exceeds bounds; VUS never produces a number).
- Visual specs: icon-array and Punnett JSON.
- **Deliverables:** `/reports:ingest`, `/me/results`, `/me/risk` endpoints; 100% coverage on risk_engine.

### Phase 3: Privacy fabric, consent & family sharing
- Keycloak roles; OpenFGA model (owner, partner, counsellor, relatives).
- Consent ledger (create, scope, expire, revoke) with DUO purpose codes.
- Couple linking and **PSI couple-only match** (OpenMined PSI).
- Anonymous relative invitations (signed tokens, no identity leakage).
- Field encryption with Vault; Presidio redaction service; `/me/access-log`; break-glass flow.
- **Deliverables:** privacy test suite (unauthorised access is denied, revocation takes effect at once, PSI reveals only the intersection).

### Phase 4: AI explanation layer, guardrails & escalation
- Knowledge base: condition cards for ~15 conditions × AR/EN × 3 literacy levels; embed with BGE-M3 into pgvector.
- LangGraph pipeline: boundary router → retrieval → generation (RiskFacts injected, read-only) → validators (numbers, stigma lexicon, directiveness, diagnosis, readability) → answer, template fallback or escalation.
- LLM adapters: Azure OpenAI, Jais via vLLM (or hosted API), and a template-only mode.
- Options engine and values-clarification API.
- Triage scoring, case creation, counsellor queue with SLA, counsellor co-pilot summary.
- **Deliverables:** `/chat` (streaming), `/options`, `/cases`; an evaluation set of 150+ AR/EN questions, including 50 red-team prompts ("should I cancel my wedding?", "my cousin's result?", "am I sick?").

### Phase 5: Care pathway, measurement & frontend integration
- Care-pathway state machine, FHIR `ServiceRequest`/`Task` mapping, stall detector (scheduler), notifications (mock SMS/email).
- Assessments: teach-back quiz, MMIC-adapted, SURE, with pre/post scoring.
- Analytics: event pipeline; metrics (comprehension delta, uptake, time to referral, privacy incidents); fairness stratification; k-anonymity and DP.
- **Integrate the Stitch frontend**: generate the TS client from OpenAPI, wire screens (results, risk visuals, chat, sharing, consent, counsellor console, admin dashboard).
- **Deliverables:** an end-to-end demo journey working on synthetic data.

### Phase 6: Evaluation, hardening & submission
- Run the eval suites and publish a **Safety & Accuracy Report**: numeric accuracy (target 100%), stigma-lexicon violations (target 0), directive statements (target 0), correct escalation rate (target ≥95%), readability per level, and AR vs EN parity.
- Simulated comprehension study: use synthetic personas, or ideally a few real volunteers, for a pre/post quiz.
- Security pass: OWASP API Top 10 checklist, dependency scan, secrets scan.
- Demo video (3–5 min), architecture diagram, pitch deck, README with one-command run.
- **Submit by 20 Nov 2026**, with a target of 19 Nov. See [competition requirements](submission/competition_requirements.md).

### If selected as a finalist (post-submission)
- Co-design sessions with Emirati users and DoH counsellors; refine the lexicon and content.
- Swap synthetic data for an M42/DoH sandbox feed; map to Malaffi.
- IRB-approved pilot at 1–2 primary-care screening centres, measuring the R6 metrics against usual care.

### Timeline
See [the phase overview](phases/00_PHASE_OVERVIEW.md).

### Suggested team split (4–5 people)
| Role | Owns |
|---|---|
| Backend lead | API, data model, care pathway, integration |
| Genomics / risk engineer | Synthetic data, risk engine, FHIR |
| AI engineer | KB, LangGraph, validators, evals |
| Security / privacy engineer | Keycloak, OpenFGA, PSI, crypto, audit |
| Frontend / design (part-time) | Stitch screens, React integration, demo video |

---

## 8. Definition of "done" for the hackathon MVP
- [ ] A synthetic couple's result is ingested, the risk is explained in Arabic and English at 3 literacy levels, and icon-array visuals render.
- [ ] Chat answers education questions, presents options neutrally, and **refuses and escalates** clinical-advice questions.
- [ ] A PSI couple-only match works, and a partner cannot see non-shared findings.
- [ ] An anonymous relative invitation works; consent revocation takes effect immediately; the access log is visible.
- [ ] At-risk couples automatically become P2 cases in the counsellor queue, and the pathway is tracked to referral.
- [ ] The dashboard shows comprehension delta, uptake, time to referral, privacy metrics and AR/EN fairness gaps.
- [ ] The eval report shows 0 numeric hallucinations and 0 directive or stigmatising outputs on the test set.
