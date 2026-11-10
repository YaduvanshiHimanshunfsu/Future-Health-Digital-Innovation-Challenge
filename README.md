<div align="center">

# Samvid · संविद्

### Understand inherited disease risk: privately, kindly, in your own language

*Numbers from code. Words from AI. Decisions from people. Data stays with its owner.*

<br/>

![Status: early build](https://img.shields.io/badge/status-early%20build%20%C2%B7%20phases%201%E2%80%935%20built%2C%206%20in%20progress-F4B740?style=for-the-badge)
![Prototype due 20 Nov 2026](https://img.shields.io/badge/prototype%20due-20%20Nov%202026-2F5BEA?style=for-the-badge)
![Synthetic data only](https://img.shields.io/badge/data-synthetic%20only-14A89B?style=for-the-badge)
![Global by design](https://img.shields.io/badge/scope-global%20by%20design-0E7C72?style=for-the-badge)
![Multilingual](https://img.shields.io/badge/languages-English%20%C2%B7%20Arabic%20%C2%B7%20Hindi-7A4FD6?style=for-the-badge)
![Team Vigyan_Viveka_Vijaya](https://img.shields.io/badge/team-Vigyan__Viveka__Vijaya-E2725B?style=for-the-badge)

**Future Health Digital Innovation Challenge 2026 · Fertility · Challenge 03**

[The problem](#the-problem) · [The solution](#the-solution) · [Global design](#global-by-design) · [Architecture](#system-architecture) · [Workflows](#core-workflows) · [Privacy](#privacy-by-design) · [Measurement](#what-we-measure) · [Roadmap](#delivery-plan) · [Docs](#documentation)

</div>

---

> [!IMPORTANT]
> **This is a working prototype on synthetic data.** The whole journey runs on one machine: the risk
> engine, the explanation pipeline with its safety checks, consent and family sharing, the care
> pathway, and the screens for people, counsellors and programme staff. Run it with
> `python Run_Samvid.py`.
>
> **Not yet done, and said plainly throughout:** no clinician has reviewed the content or the
> rules, no native speaker has reviewed the Hindi, Arabic text is pending approval, nobody has
> user-tested it, and no country's settings are reviewed. Details in
> [assumptions and limitations](docs/submission/assumptions_and_limitations.md).

## At a glance

| | |
|---|---|
| **Team** | Vigyan_Viveka_Vijaya |
| **The name** | *Samvid* (संविद्) is Sanskrit for knowledge and understanding, and also agreement and consent |
| **Languages** | English, Arabic and Hindi first, with more added per country |
| **What** | A companion that explains genetic carrier results, supports informed choices, and links people to qualified counsellors |
| **Who for** | Individuals and couples, families, genetic counsellors, physicians, and health programme managers |
| **Where** | Global by design, with per-country settings. Abu Dhabi is the first reference, and no country is supported until its settings are reviewed locally |
| **What makes it different** | Risk numbers come only from tested code, AI only explains them, and every sharing decision belongs to the individual |
| **What it never does** | Diagnose, tell anyone whether to marry or conceive, or contact relatives without the person's action |

---

## The problem

Couples related as second cousins or closer, and their children, were estimated at [10.4% of the world's population](https://pmc.ncbi.nlm.nih.gov/articles/PMC2868287), mostly across Africa, the Middle East and Asia (a 2009-era estimate). Screening is growing, but a result only helps once people understand it and can act on it. Abu Dhabi, which hosts this challenge, shows the pattern: its programme covers [570 genes and over 840 conditions](https://www.360dx.com/molecular-diagnostics/mandatory-premarital-genetic-carrier-screening-program-dubai-ids-risk-couples), yet the hardest part still comes **after the lab**.

```mermaid
flowchart LR
    A["<b>Screening</b><br/>Growing, varies by country"]:::warn --> B["<b>Result understood?</b><br/>Probabilistic, confusing"]:::bad
    B --> C["<b>Counselling</b><br/>Few accredited counsellors"]:::warn
    C --> D["<b>Informed choice</b><br/>Family and cultural pressure"]:::warn
    D --> E["<b>Care pathway</b><br/>Fragmented hand-offs"]:::warn
    E --> F["<b>Family informed</b><br/>A result implicates relatives"]:::bad

    classDef good fill:#E3F1D6,stroke:#5E8F36,color:#1F2433,stroke-width:2px
    classDef warn fill:#FDF0CF,stroke:#B8860B,color:#1F2433,stroke-width:2px
    classDef bad fill:#FBE0DA,stroke:#C9543C,color:#1F2433,stroke-width:2px
```

**Why getting this right matters**

- Misread results cause anxiety, stigma, family tension or false certainty.
- A carrier result says something about parents, siblings and cousins, so one person's data is never only theirs.
- Consanguineous marriage is a long-standing practice in many communities, so a good system supports **informed choice**, not judgement.
- Success can't be measured by cancelled marriages. That would be coercive, and it says nothing about understanding.

### The genetics in one picture

Consanguinity doesn't cause disease. It raises the chance that both partners inherited the same rare gene change from a shared ancestor. When both partners carry a change in the same recessive gene, **each pregnancy** has these chances:

```mermaid
%%{init: {"theme":"base","themeVariables":{"pie1":"#5FC9BD","pie2":"#A98CE8","pie3":"#D9CDB8","pieOpacity":"1","pieStrokeColor":"#1F2433","pieStrokeWidth":"1px","pieOuterStrokeColor":"#6B7280","pieSectionTextColor":"#1F2433","pieSectionTextSize":"16px","pieLegendTextColor":"#6B7280","pieLegendTextSize":"14px","pieTitleTextColor":"#6B7280","pieTitleTextSize":"16px"}}}%%
pie showData title Chances in each pregnancy
    "Carrier, like the parents" : 50
    "Inherits two copies" : 25
    "Inherits neither copy" : 25
```

Chance has no memory, so these are the same for every pregnancy. They're chances, not a count of children, and risk is not a diagnosis.

---

## The solution

Each layer does only what it can be trusted to do. **The AI never computes a risk number, and a person always makes the decision.**

```mermaid
flowchart TB
    IN(["Lab result, or a person's question"]):::io

    subgraph L1["1 · NUMBERS FROM CODE"]
        direction LR
        A1["Normalise result"]:::code --> A2["Deterministic<br/>risk engine"]:::code --> A3["Verified facts,<br/>with sources"]:::code
    end

    subgraph L2["2 · WORDS FROM AI"]
        direction LR
        B1["Boundary router"]:::ai --> B2["Curated content +<br/>constrained LLM"]:::ai --> B3["Output validators<br/>or approved template"]:::ai
    end

    subgraph L3["3 · DECISIONS FROM PEOPLE"]
        direction LR
        C1["Triage"]:::human --> C2["Accredited<br/>counsellor"]:::human --> C3["Confirmatory test and<br/>specialist care, if chosen"]:::human
    end

    OUT(["Understanding, informed choice, access to care"]):::io

    subgraph ALL["APPLIES TO EVERY LAYER ABOVE"]
        direction LR
        P["<b>Privacy fabric</b><br/>Consent ledger · access rules<br/>Encryption · tamper-evident audit"]:::privacy ~~~ M["<b>Measurement</b><br/>Comprehension · uptake<br/>Time to referral · privacy · equity"]:::measure
    end

    IN --> L1 --> L2 --> L3 --> OUT
    OUT ~~~ ALL

    classDef io fill:#FFFFFF,stroke:#5B6275,color:#1F2433,stroke-width:2px
    classDef code fill:#DCE6FF,stroke:#2F5BEA,color:#1F2433
    classDef ai fill:#E9E1FB,stroke:#7A4FD6,color:#1F2433
    classDef human fill:#D3F3EF,stroke:#0E7C72,color:#1F2433
    classDef privacy fill:#FDF0CF,stroke:#B8860B,color:#1F2433
    classDef measure fill:#E3F1D6,stroke:#5E8F36,color:#1F2433
    style L1 fill:#F2F6FF,stroke:#2F5BEA,color:#1F2433
    style L2 fill:#F7F3FE,stroke:#7A4FD6,color:#1F2433
    style L3 fill:#EEFBF9,stroke:#0E7C72,color:#1F2433
    style ALL fill:#FBF8F3,stroke:#8C7B62,color:#1F2433,stroke-dasharray:6 4
```

### How the six challenge requirements are met

| | Requirement | Planned approach | Main modules |
|---|---|---|---|
| **R1** | Risk explanation | Exact risk figures, icon arrays, three reading levels, plain English, Arabic and Hindi | `risk_engine` `explain` `kb` |
| **R2** | Values-sensitive choices | Options shown with equal weight, plus private values reflection that's never scored | `decision` `centres` |
| **R3** | Qualified human counselling | Every question labelled, with clinical or complex cases escalated to people | `explain/router` `triage` `booking` |
| **R4** | Privacy-preserving family workflows | Granular, revocable consent, couple-only match, anonymous family invitations, access log | `privacy` |
| **R5** | Safe linkage to services | Traceable pathway from result to counselling, testing and specialist care | `pathway` |
| **R6** | Measurable comprehension and access | Teach-back, uptake and time-to-referral metrics, split by language and literacy | `assessments` `analytics` |

---

## Global by design

Samvid isn't tied to one country. The safety core stays the same everywhere, and everything that differs by country is held in a **country pack**: settings, not code. Abu Dhabi is the first reference pack, because the challenge is hosted there.

```mermaid
flowchart TB
    subgraph CORE["GLOBAL CORE · the same everywhere"]
        direction LR
        C1["Risk rules"]:::core ~~~ C2["Safety validators<br/>and boundary router"]:::core ~~~ C3["Consent, audit,<br/>encryption"]:::core ~~~ C4["Care pathway<br/>and metrics"]:::core
    end

    L["<b>Pack loader</b><br/>Blocks unreviewed packs in production<br/>A pack can never switch off a safety rule"]:::gate

    subgraph PACKS["COUNTRY PACKS · settings, not code"]
        direction LR
        P1["<b>Abu Dhabi</b><br/>First reference pack<br/>Arabic, English"]:::first ~~~ P2["<b>India</b><br/>Illustrative demo pack<br/>Hindi, English"]:::next ~~~ P3["<b>Template</b><br/>For any new country"]:::next
    end

    subgraph HAS["EACH PACK HOLDS"]
        direction LR
        H1["Languages and<br/>word lists"]:::has ~~~ H2["Law and reproductive<br/>options"]:::has ~~~ H3["Gene panel and<br/>frequencies"]:::has ~~~ H4["Services, funding,<br/>support contacts"]:::has ~~~ H5["Identity, records,<br/>hosting region"]:::has
    end

    CORE -->|reads settings through| L --> PACKS
    PACKS -.-> HAS

    classDef core fill:#DCE6FF,stroke:#2F5BEA,color:#1F2433
    classDef gate fill:#FDF0CF,stroke:#B8860B,color:#1F2433,stroke-width:2px
    classDef first fill:#D3F3EF,stroke:#0E7C72,color:#1F2433,stroke-width:2px
    classDef next fill:#FFFFFF,stroke:#5B6275,color:#1F2433,stroke-dasharray:5 4
    classDef has fill:#E9E1FB,stroke:#7A4FD6,color:#1F2433
    style CORE fill:#F2F6FF,stroke:#2F5BEA,color:#1F2433
    style PACKS fill:#F2FBFA,stroke:#0E7C72,color:#1F2433
    style HAS fill:#F7F3FE,stroke:#7A4FD6,color:#1F2433
```

- **First two packs:** Abu Dhabi (Arabic and English) and India (Hindi and English). India is labelled illustrative until it's reviewed.
- **Adding a country needs no code change**, only a reviewed pack.
- **No country counts as supported until local clinicians and legal advisers have reviewed its pack.** "Global" describes the design, not today's coverage.
- **Where accredited counsellors are scarce,** the pack names the qualified human. If nobody qualified is available, the product says so honestly, and AI never fills the gap.
- **Genetic data stays in its country** by default, with a separate deployment per country or region.

Read the full design in [docs/07](docs/07_Global_Design_and_Country_Packs.md).

---

## System architecture

A **modular monolith**: quick to build as one deployable app, with clear boundaries so modules can split later.

```mermaid
flowchart TB
    subgraph USERS["PEOPLE AND SYSTEMS"]
        direction LR
        U1["Individuals<br/>and couples"]:::user ~~~ U2["Counsellors<br/>and physicians"]:::user ~~~ U3["Programme<br/>managers"]:::user ~~~ U4["Screening lab<br/>FHIR feed"]:::user
    end

    FE["<b>Next.js frontend</b><br/>Right-to-left and left-to-right languages · typed API client"]:::web

    subgraph API["FASTAPI BACKEND · versioned REST API"]
        direction TB
        GW["Authentication · rate limits<br/>Strict validation"]:::gate
        subgraph DOM["Domain modules"]
            direction LR
            D1["ingestion"]:::dom ~~~ D2["risk_engine<br/>pure, no I/O"]:::core ~~~ D3["explain<br/>LangGraph"]:::dom ~~~ D4["decision"]:::dom
            D5["privacy"]:::dom ~~~ D6["triage"]:::dom ~~~ D7["pathway"]:::dom ~~~ D8["assessments<br/>analytics"]:::dom ~~~ D9["country_packs<br/>per-country settings"]:::core
        end
        GW --> DOM
    end

    subgraph DATA["DATA"]
        direction LR
        S1[("PostgreSQL<br/>+ pgvector")]:::store ~~~ S2[("Redis")]:::store ~~~ S3[("Hash-chained<br/>audit log")]:::store
    end

    subgraph EXT["EXTERNAL, BEHIND ADAPTERS"]
        direction LR
        E1["Keycloak"]:::ext ~~~ E2["OpenFGA"]:::ext ~~~ E3["Key<br/>management"]:::ext
        E4["LLM or<br/>template mode"]:::ext ~~~ E5["FHIR systems<br/>(future)"]:::ext
    end

    USERS --> FE --> API
    API --> DATA
    API --> EXT

    classDef user fill:#FFFFFF,stroke:#5B6275,color:#1F2433
    classDef web fill:#E9E1FB,stroke:#7A4FD6,color:#1F2433
    classDef gate fill:#FDF0CF,stroke:#B8860B,color:#1F2433
    classDef dom fill:#DCE6FF,stroke:#2F5BEA,color:#1F2433
    classDef core fill:#2F5BEA,stroke:#1E3FA8,color:#FFFFFF,stroke-width:2px
    classDef store fill:#D3F3EF,stroke:#0E7C72,color:#1F2433
    classDef ext fill:#F3EDE4,stroke:#8C7B62,color:#1F2433
    style USERS fill:#FAFAFA,stroke:#B5BAC6,color:#1F2433
    style API fill:#F7F9FF,stroke:#2F5BEA,color:#1F2433
    style DOM fill:#EEF3FF,stroke:#8FA8F0,color:#1F2433
    style DATA fill:#F2FBFA,stroke:#0E7C72,color:#1F2433
    style EXT fill:#FBF8F3,stroke:#8C7B62,color:#1F2433
```

### Design principles

| Principle | What it means in practice |
|---|---|
| **Deterministic core** | The risk engine has no I/O or LLM access, so all its maths can be tested exhaustively |
| **Fail closed** | If authorisation, redaction or validation fails, the answer is deny or a safe fallback |
| **Uncertain means no number** | A variant of uncertain significance, an unknown gene or missing data produces no figure, and goes to a human |
| **Least privilege** | The LLM has no tools. The app's database role can't alter audit rows |
| **Graceful degradation** | With the AI off, approved templates still work and a human is always reachable |
| **Interoperable** | FHIR R4 in and out, to ease future health-system integration |

---

## Core workflows

### 1. From lab result to verified facts

The engine checks the riskiest cases first, and any uncertainty produces a referral instead of a number.

```mermaid
flowchart TD
    S(["Findings for each gene"]):::start --> K{{"Known gene and inheritance?"}}:::q
    K -- No --> R1["No number<br/>Refer to counsellor"]:::refer
    K -- Yes --> V{{"Any uncertain variant in this gene?"}}:::q
    V -- Yes --> R2["No number<br/>Explain uncertainty<br/>Counsellor review"]:::refer
    V -- No --> H{{"Possibly affected?<br/>Two copies, or X-linked male"}}:::q
    H -- Yes --> R3["Not carrier information<br/>Urgent counsellor review"]:::urgent
    H -- No --> X{{"Inheritance?"}}:::q
    X -- "X-linked" --> X1["Rules by sex and zygosity<br/>Counsellor offered"]:::fact
    X -- Recessive --> B{{"Do both partners carry it?"}}:::q
    B -- Yes --> F1["Per-pregnancy chances<br/>Counsellor offered"]:::fact
    B -- "One carrier" --> F2["Residual chance,<br/>adjusted for kinship"]:::fact
    F1 --> OUT(["Verified facts with source and rule version"]):::start
    F2 --> OUT
    X1 --> OUT

    classDef start fill:#FFFFFF,stroke:#5B6275,color:#1F2433,stroke-width:2px
    classDef q fill:#DCE6FF,stroke:#2F5BEA,color:#1F2433
    classDef fact fill:#D3F3EF,stroke:#0E7C72,color:#1F2433
    classDef refer fill:#FDF0CF,stroke:#B8860B,color:#1F2433
    classDef urgent fill:#E9E1FB,stroke:#7A4FD6,color:#1F2433,stroke-width:2px
```

### 2. From a question to a safe answer

Every message gets a boundary label. The LLM refers to verified facts by ID, and code fills in the numbers, so a figure can't be invented or swapped.

```mermaid
flowchart TD
    Q(["Person's question"]):::start --> RD["Redact personal details<br/>If this fails, the LLM isn't called"]:::guard
    RD --> RT{{"Boundary router"}}:::q
    RT -- "Education or<br/>decision support" --> CTX["Load the person's own facts<br/>and retrieve curated content"]:::ai
    RT -- "Clinical advice" --> CL["Explain the boundary kindly<br/>Offer a counsellor"]:::human
    RT -- "Distress or coercion" --> DS["Verified support contacts now<br/>Alert a person"]:::urgent
    CTX --> GEN["LLM drafts text<br/>No tools, facts by ID only"]:::ai
    GEN --> VAL{{"Validators: numbers · stigma<br/>directive · diagnosis · reading level"}}:::guard
    VAL -- Pass --> ANS(["Answer, with boundary label"]):::start
    VAL -- "Fail or LLM down" --> TPL["Approved template<br/>plus counsellor offer"]:::human
    TPL --> ANS
    CL --> ANS
    DS --> ANS

    classDef start fill:#FFFFFF,stroke:#5B6275,color:#1F2433,stroke-width:2px
    classDef q fill:#DCE6FF,stroke:#2F5BEA,color:#1F2433
    classDef ai fill:#E9E1FB,stroke:#7A4FD6,color:#1F2433
    classDef guard fill:#FDF0CF,stroke:#B8860B,color:#1F2433
    classDef human fill:#D3F3EF,stroke:#0E7C72,color:#1F2433
    classDef urgent fill:#FBE0DA,stroke:#C9543C,color:#1F2433,stroke-width:2px
```

### 3. Couple-only match

Partners can compare results without exposing their other findings. If they choose different settings, the more private one wins. "No data" is never reported as "no shared finding".

```mermaid
sequenceDiagram
    autonumber
    actor A as Partner A
    actor B as Partner B
    participant S as Samvid
    participant C as Counsellor queue

    A->>S: Invite partner
    B->>S: Accept
    A->>S: Consent, choosing "show shared genes"
    B->>S: Consent, choosing "yes or no only"
    Note over S: More private choice wins:<br/>yes or no only
    A->>S: Run match
    S->>S: Compare lab-attested<br/>findings only
    alt A finding is shared
        S-->>A: Yes, you share a finding
        S-->>B: Yes, you share a finding
        S->>C: Open a priority case
    else No finding is shared
        S-->>A: No shared finding, and what that means
        S-->>B: No shared finding, and what that means
    else Data is missing
        S-->>A: Can't determine yet
        S-->>B: Can't determine yet
    end
    Note over A,B: Non-shared findings are never revealed.<br/>Consent can be withdrawn.
```

> [!NOTE]
> Couple-only match limits what partners see. The server still processes the data, and a person with one finding can infer the gene from a "yes". The product will say so plainly. Private set intersection is planned for matching **between institutions**.

### 4. Care pathway

**A person can decline at any point**, and that's a valid choice, not a failure. P1 and P2 cases go straight to counselling, and a confirmatory test that doesn't confirm the finding is recorded as its own outcome.

```mermaid
flowchart TB
    START(["Result released"]):::io --> ACTIVE

    subgraph ACTIVE["ACTIVE CARE · every step timestamped and audited"]
        direction TB
        subgraph S1["1 · Understand"]
            direction LR
            EV["Education<br/>viewed"]:::a --> CC["Comprehension<br/>checked"]:::a
        end
        subgraph S2["2 · Counselling"]
            direction LR
            CR["Requested"]:::b --> CB["Booked"]:::b --> CD["Done"]:::b
        end
        subgraph S3["3 · Confirm and refer, if chosen"]
            direction LR
            CO["Confirmatory<br/>test ordered"]:::c --> CF["Result<br/>confirmed"]:::c --> RF["Specialist<br/>referral"]:::c --> RA["Referral<br/>accepted"]:::c
        end
        S1 --> S2 --> S3
    end

    ACTIVE -->|"decline at any step"| DE["Declined by user<br/><b>A valid choice</b>"]:::choice
    DE -.->|"changes mind"| ACTIVE
    ACTIVE -->|"no response"| LF["Lost to follow-up<br/>Alert to coordinator"]:::alert
    LF -.->|"returns"| ACTIVE
    ACTIVE -->|"complete, or nothing further chosen"| CL(["Closed"]):::io

    classDef io fill:#FFFFFF,stroke:#5B6275,color:#1F2433,stroke-width:2px
    classDef a fill:#DCE6FF,stroke:#2F5BEA,color:#1F2433
    classDef b fill:#D3F3EF,stroke:#0E7C72,color:#1F2433
    classDef c fill:#E9E1FB,stroke:#7A4FD6,color:#1F2433
    classDef choice fill:#E3F1D6,stroke:#5E8F36,color:#1F2433,stroke-width:2px
    classDef alert fill:#FDF0CF,stroke:#B8860B,color:#1F2433
    style ACTIVE fill:#FBF8F3,stroke:#8C7B62,color:#1F2433
    style S1 fill:#F2F6FF,stroke:#2F5BEA,color:#1F2433
    style S2 fill:#EEFBF9,stroke:#0E7C72,color:#1F2433
    style S3 fill:#F7F3FE,stroke:#7A4FD6,color:#1F2433
```

### 5. Triage: who gets a human, and when

Transparent, reviewable rules, not a black-box model. Every case records why it got its priority.

| Priority | Triggered by | Target time |
|---|---|---|
| **P1 Urgent** | Distress, a shared finding during pregnancy, or a possibly affected adult | 24 hours. Distress also gets support contacts immediately |
| **P2 High** | Both partners carry the same gene, an X-linked finding in a woman, or several shared genes | 72 hours |
| **P3 Standard** | Uncertain variant, questions on extended testing, or teach-back missed twice | 7 days |
| **P4 Optional** | A person asks for a human, with no other trigger | Next available |

These rules and times are configurable, and need clinical review.

---

## Privacy by design

Genetic data is permanent and shared across a family, so the most private setting is the default.

### Each person chooses how much to share

```mermaid
flowchart LR
    O(["Your result"]):::me
    O --> P["<b>Private</b><br/>Nothing shared"]:::a
    O --> M["<b>Couple-only match</b><br/>Only shared findings, or yes/no"]:::b
    O --> F["<b>Selected sharing</b><br/>Chosen fields, chosen person,<br/>time-limited"]:::c
    O --> I["<b>Anonymous family invitation</b><br/>Generic screening info,<br/>no name, no result"]:::d
    M --> R(["Revocable at any time, and every access is logged"]):::me
    F --> R
    I --> L(["Relative decides for themselves"]):::me

    classDef me fill:#FFFFFF,stroke:#5B6275,color:#1F2433,stroke-width:2px
    classDef a fill:#E3F1D6,stroke:#5E8F36,color:#1F2433
    classDef b fill:#D3F3EF,stroke:#0E7C72,color:#1F2433
    classDef c fill:#DCE6FF,stroke:#2F5BEA,color:#1F2433
    classDef d fill:#E9E1FB,stroke:#7A4FD6,color:#1F2433
```

### What the AI is allowed to see

```mermaid
flowchart LR
    subgraph NEVER["NEVER REACHES THE LLM"]
        direction TB
        N1["Names and national IDs"]:::no ~~~ N2["Phone numbers and emails"]:::no ~~~ N3["Exact variant details"]:::no ~~~ N4["A partner's non-shared findings"]:::no ~~~ N5["Any relative's data"]:::no
    end

    G{{"Redaction and<br/>field allowlist<br/><b>fails closed</b>"}}:::gate

    subgraph ALLOWED["MAY REACH THE LLM"]
        direction TB
        Y1["Gene name and scenario"]:::yes ~~~ Y2["Fact IDs, not raw numbers"]:::yes ~~~ Y3["Curated, reviewed content"]:::yes ~~~ Y4["The redacted question"]:::yes
    end

    NEVER -. blocked .-> G
    G --> ALLOWED
    ALLOWED --> LLM["LLM<br/>No tools<br/>or actions"]:::ai

    classDef no fill:#FBE0DA,stroke:#C9543C,color:#1F2433
    classDef yes fill:#D3F3EF,stroke:#0E7C72,color:#1F2433
    classDef gate fill:#FDF0CF,stroke:#B8860B,color:#1F2433,stroke-width:2px
    classDef ai fill:#E9E1FB,stroke:#7A4FD6,color:#1F2433
    style NEVER fill:#FEF6F4,stroke:#C9543C,color:#1F2433
    style ALLOWED fill:#F2FBFA,stroke:#0E7C72,color:#1F2433
```

**Other planned controls**

| Control | Purpose |
|---|---|
| Field-level AES-256-GCM encryption | Genetic findings are unreadable in the database, and ciphertext is bound to its row |
| Relationship-based access (OpenFGA) | Models partners, relatives and counsellors, and denies access if the check fails |
| Hash-chained audit log | Tampering becomes detectable, and it powers the "who saw my data" view |
| Break-glass access | Access outside an assignment needs a stated reason and is flagged for review |
| Data minimisation | No raw genomes stored, and benign variants dropped on arrival |

---

## What we measure

Requirement 6 asks for evidence, so each metric is designed to be split by **language and literacy level**, to show who the system is failing.

```mermaid
flowchart LR
    C(("<b>Evidence</b>")):::hub
    C --> A["<b>Understanding</b><br/>Paired teach-back, before and after"]:::m
    C --> B["<b>Access</b><br/>Counselling uptake<br/>Time from result to referral"]:::m
    C --> D["<b>Privacy</b><br/>Blocked access attempts<br/>Time to revoke, PII sent to AI"]:::m
    C --> E["<b>AI safety</b><br/>Validator blocks, correct escalation<br/>Human-scored samples"]:::m
    C --> F["<b>Equity</b><br/>Gaps by language, literacy,<br/>age, gender, region"]:::m
    C --> X["<b>Never a success metric</b><br/>Cancelled marriages<br/>Any single personal choice"]:::x

    classDef hub fill:#2F5BEA,stroke:#1E3FA8,color:#FFFFFF
    classDef m fill:#DCE6FF,stroke:#2F5BEA,color:#1F2433
    classDef x fill:#FBE0DA,stroke:#C9543C,color:#1F2433,stroke-width:2px
```

---

## Delivery plan

Six phases from 5 to 20 November 2026, with a target to submit a day early. Every objective, check and issue is cross-verified in [CROSS_VERIFICATION.md](docs/phases/CROSS_VERIFICATION.md).

```mermaid
gantt
    title Build plan (5–20 Nov 2026)
    dateFormat YYYY-MM-DD
    axisFormat %d %b
    tickInterval 2day
    todayMarker off

    section Milestones
    Registration closes, team registered :milestone, 2026-11-10, 0d
    Submit target             :milestone, 2026-11-19, 0d
    Prototype deadline        :crit, milestone, 2026-11-20, 0d

    section Phases
    1 Foundation and decisions       :p1, 2026-11-05, 2d
    2 Data and risk engine           :p2, after p1, 3d
    3 Privacy and family sharing     :p3, after p2, 2d
    4 AI and human escalation        :p4, after p3, 3d
    5 Pathway, metrics, integration  :p5, after p4, 3d
    6 Evaluation and submission      :p6, after p5, 3d

    section Frontend
    Design system and screens        :f1, 2026-11-05, 5d
    Build and wire screens           :f2, 2026-11-10, 8d
```

| Phase | Goal | Done when | Plan |
|---|---|---|---|
| **1** | Foundation, decisions, compliance baseline | Registered, scope locked, stack runs from a clean clone, audit tamper test passes | [Phase 1](docs/phases/PHASE_1_Foundation.md) |
| **2** | Genomic data and deterministic risk engine | Hand-worked risk answers match, and correct risk appears on screen | [Phase 2](docs/phases/PHASE_2_Genomic_Data_and_Risk_Engine.md) |
| **3** | Privacy fabric and family sharing | Privacy tests pass, and no partner-only data appears in any output | [Phase 3](docs/phases/PHASE_3_Privacy_and_Family_Sharing.md) |
| **4** | AI explanation and human escalation | Safe answers in English, Arabic and Hindi, even with the LLM off, and cases reach a counsellor | [Phase 4](docs/phases/PHASE_4_AI_Explanation_and_Escalation.md) |
| **5** | Care pathway, measurement, integration | Full demo journey works in both languages, with traceable metrics | [Phase 5](docs/phases/PHASE_5_Care_Pathway_Measurement_Integration.md) |
| **6** | Evaluation, hardening, submission | Honest safety report and limitations, and submitted with confirmation saved | [Phase 6](docs/phases/PHASE_6_Evaluation_and_Submission.md) |

### Run it

```bash
python Run_Samvid.py
```

On a first run it introduces the project, checks what you have installed and offers to install
what's missing, asks for a Gemini API key if you have one and saves it for you, builds everything,
creates demo accounts with synthetic lab reports, prints where to go, and then shows live activity
from the web app and the API in your terminal. Each run is also written to `logs/`, with secrets
removed.

**You need Docker Desktop.** Everything else it can install or do without:

| | |
|---|---|
| [uv](https://docs.astral.sh/uv/) | For the demo accounts. The launcher offers to install it |
| [Ollama](https://ollama.com) | Optional. With `ollama pull qwen2.5:3b`, an AI model drafts answers without anything leaving your computer |
| A Gemini API key | Optional, from [aistudio.google.com/apikey](https://aistudio.google.com/apikey). Without any model, reviewed text answers instead |
| Node.js | Only for the browser tests; the web app is built inside Docker |

| Command | Does |
|---|---|
| `python Run_Samvid.py` | Set up if needed, start everything, show live activity |
| `--setup` | Walk through the first-run setup again, including the AI key |
| `--status` | What's running, and which AI model will answer |
| `--check` / `--verify` | The smoke test, or that plus the load test and a scan of the logs for personal data |
| `--eval` | The safety evaluations, per language |
| `--security` | Every scanner, with the outputs saved |
| `--stop` / `--reset` | Stop, or delete all the data (it asks first) |

### Current status

| Area | State |
|---|---|
| Backend foundation: API security, database, audit trail, local stack | **Built and tested** |
| Risk engine, encryption, lab report ingestion, synthetic data, country packs | **Built and tested**, on placeholder gene values with no clinical review |
| Consent ledger, couple match, family invitations, access log, break-glass, redaction | **Built and tested** |
| Screens for people, counsellors and programme staff, in English and Hindi | **Built and tested** in a real browser against the real stack |
| AI explanation with safety checks, options, values, counsellor queue | **Built and tested**. Gemini or local Ollama, with reviewed text as the fallback |
| Care pathway, booking, FHIR referrals, centre finder, understanding checks, dashboards | **Built and tested** |
| Safety evaluation, security scans, submission documents | **Built**, with results and gaps in [docs/evaluation](docs/evaluation/) and [docs/security](docs/security/) |
| Routing recall target (95% per language) | **Not met**: measured at 5 of 59 hold-out questions still answered automatically. Reported, not hidden |
| Clinical review | **Not started**: no reviewer yet |
| Native-speaker review; Arabic text | **Not started**: Hindi unreviewed, Arabic pending approval |
| User testing | **Not run**: the protocol is ready, and no figures are invented in its place |

---

## Tech stack

All planned, per [docs/backend.md](docs/backend.md) and [docs/frontend.md](docs/frontend.md). Versions get pinned during Phase 1.

| Layer | Choice | Why |
|---|---|---|
| **Backend** | Python 3.12, FastAPI, Pydantic v2 | Strong AI and genomics ecosystem, strict validation, generated API contract |
| **Data** | PostgreSQL 16 with pgvector, SQLAlchemy 2, Alembic, Redis, Celery | One store for relational data and vectors, plus background jobs |
| **Identity and access** | Keycloak (OIDC), OpenFGA | Standard login, and relationship-based rules that fit family data |
| **AI** | LangGraph, an OpenAI-compatible LLM (Azure OpenAI or Jais), BGE-M3 embeddings | Explicit, testable pipeline with strong Arabic options |
| **Privacy and security** | AES-256-GCM, Vault or Key Vault, OpenFGA, word-list redaction | Envelope encryption, relationship checks that deny on any failure, and only listed words reaching an LLM. Private set intersection between institutions is a possible later step, and isn't built |
| **Interoperability** | FHIR R4 | Common language of health-system integration |
| **Note** | The challenge is technology-neutral, so these are our choices, not requirements | |
| **Frontend** | Next.js 15, TypeScript, Tailwind, shadcn/ui, next-intl | Fast multi-page build with accessible components and right-to-left support |
| **Visuals** | Custom SVG, Recharts or ECharts, Motion | Precise risk visuals, with a reduced-motion option |
| **Quality** | pytest, Hypothesis, Playwright, axe-core, ruff, mypy, gitleaks, trivy | Property tests for risk maths, plus accessibility and security checks |

---

## Repository structure

```text
Future Health/
├── README.md                 You are here
├── brain.md                  Mandatory project log: what, how and why
├── CLAUDE.md                 Rules for AI assistants
├── problem statement.md      The challenge text
│
├── backend/
│   ├── app/
│   │   ├── risk_engine/      Deterministic risk maths (pure, no I/O)
│   │   ├── explain/          Router, LLM pipeline, validators, templates
│   │   ├── privacy/          Encryption, audit, consent, matching, invitations
│   │   ├── triage/           Priorities, assignment, case summaries
│   │   ├── pathway/          Care state machine, FHIR mapping
│   │   ├── decision/         Options and values reflection
│   │   ├── kb/               Curated content (English, Arabic, Hindi; 3 levels)
│   │   ├── assessments/      Teach-back and adapted instruments
│   │   ├── analytics/        Metrics and fairness
│   │   ├── ingestion/        Lab results to minimal encrypted findings
│   │   ├── country_packs/    Loads and validates per-country settings
│   │   └── api/, core/, db/, models/, schemas/, repositories/, ...
│   ├── alembic/              Database migrations
│   ├── packs/                Country packs: law, options, languages, services
│   ├── synthetic/            Synthetic population and demo personas
│   └── tests/                unit, api, eval
│
├── frontend/
│   ├── app/                  Public site, user app, counsellor console, dashboards
│   ├── components/           ui, layout, motion, risk, charts
│   ├── lib/                  API client, auth, i18n
│   ├── messages/             English, Arabic and Hindi text
│   └── tests/e2e/            End-to-end and accessibility tests
│
├── infra/                    Docker Compose, OpenFGA model, Keycloak, Postgres
├── scripts/                  Runbooks
└── docs/
    ├── phases/               The 6-phase plan with verification checks
    ├── submission/           Technical docs, limitations, pilot plan, demo
    ├── clinical/             Options, rule review, content review
    ├── compliance/           Legal baseline
    ├── security/             Threat model, checklist
    └── evaluation/           Safety report, comprehension test
```

---

## Documentation

| Read this | To… |
|---|---|
| [Documentation map](docs/README.md) | Find anything, and see which document wins when they disagree |
| [Project review](docs/04_Project_Review_Issues_and_Improvements.md) | See known issues and what to do first |
| [Competition requirements](docs/submission/competition_requirements.md) | See official dates, FAQ answers and judging criteria |
| [Phase overview](docs/phases/00_PHASE_OVERVIEW.md) | See the plan, scope tiers and critical path |
| [Global design](docs/07_Global_Design_and_Country_Packs.md) | See how Samvid works across countries |
| [Problem statement](problem%20statement.md) · [Problem understanding](docs/01_Problem_Understanding.md) | Understand the challenge and evidence |
| [Solution and plan](docs/02_Solution_Architecture_and_Plan.md) · [Features and roadmap](docs/03_Features_Limitations_Roadmap.md) | Understand the concept, features and limits |
| [Stitch prompts](docs/STITCH_PROMPTS.md) · [Backend guide](docs/backend.md) · [Frontend guide](docs/frontend.md) | Get engineering and design detail |
| [Project structure](docs/05_Project_Structure.md) · [Traceability](docs/06_Traceability_Matrix.md) | Trace requirements through files, tests and checks |

> [!WARNING]
> The specs contain known errors, including bugs in the sample code in `docs/backend.md`. Read them alongside the [project review](docs/04_Project_Review_Issues_and_Improvements.md).

---

## Getting started

Run the foundation built so far:

```bash
python scripts/generate_env.py
cd infra
docker compose up -d --build --wait
docker compose exec api python -m app.ops.check_services
```

The [runbook](docs/runbook_local_stack.md) covers tests and everything else. To contribute:

1. Read the latest entries in [brain.md](brain.md).
2. Pick up the next open sub-phase in the [phase plan](docs/phases/00_PHASE_OVERVIEW.md).
3. Work toward its cross-verification checks, and close the issues it lists.
4. **Log what you did, how and why in [brain.md](brain.md).** This is mandatory for every change.

## Responsible use

- **Synthetic data only.** This repo must never contain real genetic or personal data. The organisers provide no data, so we generate our own and [declare every source](docs/submission/data_sources.md).
- **Not medical advice.** This is a competition prototype on synthetic data. It isn't a medical device and has not been clinically validated.
- **Legal review pending.** A real pilot in any country would need a licensed local health partner and regulatory approval.

## Competition

Built by team **Vigyan_Viveka_Vijaya** for the [Future Health Digital Innovation Challenge 2026](https://hack2skill.com/event/futurehealthchallenge/). The team is registered, and prototypes are due 20 Nov 2026. Dates may change, so check the challenge page. This is an independent entry, with no endorsement from any organiser or partner implied.

**IP and licence:** intellectual property stays with the team, under the challenge FAQ, and the code may be requested for evaluation. No licence has been chosen yet.
