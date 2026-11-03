# 04 — Project Review: Issues and Improvements

**Reviewed:** all seven files in the repo, on 3 Nov 2026 (`problem statement.md`, `README.md`, `docs/01`, `02`, `03`, `backend.md`, `frontend.md`).
**State of the project:** specification only. No application code exists yet, so every issue below is cheapest to fix now.

**Overall view:** the core idea is strong. "Numbers from code, words from AI, decisions from people" fits the challenge well. But the competition dates are wrong, and the spec's code has clinical and privacy bugs in exactly the places the pitch promises safety. If built as written, it would tell at-risk couples they share no finding.

## How to read this document

Issue IDs are permanent. Stub files, phase plans and `brain.md` all refer to them.

| Severity | Meaning |
|---|---|
| **S** Strategic | Affects whether the entry is eligible, credible or legally sound |
| **C** Critical | Could harm a user, break a privacy promise, or make a headline claim false |
| **H** High | A required feature or metric would not work or would give a wrong result |
| **M** Medium | Worth fixing, but will not sink the entry |

| Evidence tag | Meaning |
|---|---|
| **[RUN]** | The spec's code was extracted from `backend.md` and run. The result is shown |
| **[SOURCE]** | Checked against an external source (see [Sources](#sources)) |
| **[READ]** | Found by reading the spec's logic. Not run, because it needs a database or external service |

> Legal points here come from reading the law text or law-firm summaries. They are not legal advice. Have DoH or qualified counsel confirm them before any pilot.

---

## 1. Act on these first

| # | Action | Deadline | Issue |
|---|---|---|---|
| 1 | **Register on Hack2skill**, if you haven't already | **10 Nov** | S1 |
| 2 | Log in and read the Challenge rules and the FAQ answers ("What do we need to submit?", "What data can we use?", "Can we apply with an existing product?") | Today | S2 |
| 3 | Find one genetic counsellor or clinician to review content and triage rules | This week | S5, H13 |
| 4 | Decide team and scope tiers, because the current scope assumes 4 to 5 people | Today | S3 |

---

## 2. Strategic issues

### S1. The competition dates in the docs are wrong [SOURCE]
`docs/01` §1 and `docs/02` plan around "15 November". The Hack2skill page says:

| Milestone | Date |
|---|---|
| Registration closes | **10 Nov 2026** |
| Working prototypes due | **20 Nov 2026** |
| Expert panel evaluation | 20–30 Nov |
| Awards and presentations at GITEX | 7–11 Dec |

The 15 Nov date appears in press coverage, so it was probably superseded. The page also says dates may change, so re-check it weekly.

**Effect:** you have 5 more build days than planned, but a registration gate 5 days earlier. All phase plans here use the portal dates.

### S2. The docs misread what must be submitted and how it is judged [SOURCE]
`docs/01` says the page could not be read and that "a new concept, an early prototype or an adapted existing solution are all accepted". The page now says: *"Submit your working prototype by 20 November, with technical documentation, assumptions, and limitations."* The page states no concept-only route.

The six judging criteria, which the docs never mention (no weights published):

| Criterion | Current coverage | Gap |
|---|---|---|
| Health impact and clinical relevance | Strong story | No clinician involved yet |
| Technical depth and architecture | Very strong | None |
| Working solution and demonstration quality | Planned | Depends on C1–C10 being fixed |
| Responsible AI, safety and data governance | Strong on paper | Validators can't prove the claims yet (C5, H6, H12) |
| Scalability and deployment readiness | Good design | The one-command demo doesn't start as written (H15) |
| **Commercial viability and path to pilot** | **One line in `docs/02` §1** | **No buyer, pricing, cost model or pilot plan** |

**Fix:** add a commercial and pilot document (stub at [docs/submission/commercial_and_pilot_plan.md](submission/commercial_and_pilot_plan.md)). Treat "assumptions" and "limitations" as required deliverables. `docs/03` §3 is a good start.

### S3. The schedule has slipped and the scope assumes a full team [READ]
The plan started on 31 Oct and no code exists. The Git history shows one author. The MVP covers 7+ services, 25 build steps, 20 screens in 3 variants each, a 10-slide story site, about 90 knowledge-base documents, and 150+ evaluation questions.

**Fix:** use the scope tiers in [phases/00_PHASE_OVERVIEW.md](phases/00_PHASE_OVERVIEW.md#scope-tiers). Everything on the main demo path gets built properly. Other items get a labelled mock or move to the roadmap.

### S4. The most relevant law is missing from the docs [SOURCE]
The docs cite Federal Law 2/2019 and the PDPL but never mention **Federal Decree-Law No. 49 of 2023 Regulating the Use of the Human Genome**. I read the text on the DHA site. Key points for this project:

| Article | What it says (paraphrased) | Effect on Silah |
|---|---|---|
| 9(2) | A person can state in writing that they don't want to know their results | **No "right not to know" flow exists.** Add one |
| 9(3) | Informing the person is obligatory if results threaten their life or a foetus's life | Limits opt-outs. Needs a counsellor-defined rule |
| 9(4) | A specialist provides genetic counselling after results are issued | Supports "AI never replaces counsellors". Cite this in the pitch |
| 9(5)–(6), 33 | Limits on disclosing lineage and non-targeted findings, with criminal penalties | Keep untargeted findings out of the product |
| 15(2) | A marriage contract needs evidence of the exam, and the couple are informed of results | See S6 |
| 25(1)–(2) | Genetic data is confidential. No discrimination based on genetic traits | Strong support for the privacy and stigma design |
| 25(3) | Publishing data from the UAE Genome Programme needs approval | Stay on synthetic data. Don't cite programme data beyond what's already public |
| 28 | Storing or transferring genetic data requires a Health Authority licence | **A real pilot must run under a licensed partner.** Say so in the pilot plan |

Also, the PDPL generally carves out health data that has its own legislation, so `docs/02` overstates its role. Federal Law 2/2019 is the main one.

### S5. Two "equally valid options" are not available as written [SOURCE]
`frontend.md` P8 and P10 and `backend.md` §11.20 present **Donor options** and **Adoption** as equally valid options.

| Option | Finding |
|---|---|
| **Donor gametes** | Law-firm commentary on the UAE's assisted-reproduction law says third-party eggs and sperm remain barred, though sources differ on some details of the 2023 amendment |
| **Adoption** | The UAE government portal says *"adoption is not allowed"*, while eligible people can foster and raise a child of unknown parentage (kafala) |

A DoH judge would likely notice this immediately, and in a real product it could mislead a couple or offend them.

**Fix:**
- Remove the donor option from the Abu Dhabi configuration, pending counsellor confirmation.
- Replace "Adoption" with "Fostering (kafala)" and describe it accurately.
- Make the options list a **jurisdiction-specific table signed off by a clinician**, not a hard-coded list.
- Have a counsellor decide what to say about prenatal diagnosis, since its follow-up decisions are legally and religiously sensitive.

Al Amal funding for IVF and PGT **checks out** against published reporting, but eligibility details are not confirmed. Word that note carefully.

### S6. "Private" couple mode may not match how the programme works [SOURCE, READ]
Article 15(2) says the couple are informed of results, and published figures count at-risk *couples*. So the premarital programme may already tell couples their shared result. In that case, Silah's "keep private" mode cannot mean "my partner never learns we share a risk".

The idea still has value, since it protects each partner's *non-shared* findings, and it matters more for preconception and family sharing. **Ask a counsellor or M42 how results are actually delivered**, then reword the feature. Until then, describe it as protecting non-shared findings.

### S7. Simulated results must not be presented as evidence [READ]
`docs/02` Phase 6 proposes a "simulated comprehension study" using synthetic personas, and `docs/03` targets "+30 pp (simulated)". `frontend.md` P18 shows numbers such as "Uptake 92%". Synthetic personas can't show that people understand anything, and evaluators are told to look for real proof.

**Fix:** run a small real test with 15–30 volunteers in Arabic and English (sub-phase 6.2) and report it honestly as a small convenience sample. Label every demo dashboard "synthetic data".

### S8. Some pitch claims aren't backed by the design [READ]

| Claim | Reality in the spec | Fix |
|---|---|---|
| "PSI couple-only match with cryptographic guarantees" (`docs/02`, `03`, definition of done) | `matching.py` decrypts both sets on the server and runs `a & b`. Nothing calls `psi_adapter.py` | Say "server-side minimal disclosure" for the MVP and present PSI as cross-institution mode, or actually demo it between two services |
| "Yes/no" reveal hides the gene | A person with one finding learns the gene from "yes", since they know their own result | Tell users this plainly. Don't call it fully blind |
| "Your data stays in the UAE" on a demo | False unless it is actually hosted there | Word it as the production design |
| DoH and M42 logos under "Built with" (P1) | Implies endorsement | Remove them |
| "Continue with UAE PASS" (P5) | Mock | Label it as a mock |
| "Clinician-reviewed content" | No clinician yet | Label as "draft, pending clinical review" |

---

## 3. Critical issues

### C1. Couple match always answers "no shared finding" [READ]
`reports.py` hard-codes `sig_ok = False  # TODO`, so every report has `lab_signature_valid = False`. `matching.py` reads only `attested_only=True` findings, so both sets are always empty and `any_shared` is always false.

**Harm:** false reassurance, the worst failure this product can have, and it would look like a normal result.
**Fix:** verify signatures, or for the demo use an explicit "demo-attested" flag. Add a test that a known shared couple returns true.

### C2. "No data" looks the same as "no shared finding" [READ]
If a partner has no report, `match_couple` also returns `any_shared = False`.
**Fix:** return three outcomes: `shared`, `none_shared`, `cannot_determine`. Only the first two are results.

### C3. X-linked results are wrong [RUN]

| Input | Spec output | Should be |
|---|---|---|
| Male, hemizygous P, G6PD | `carrier_self / carrier` | Not "carrier". He may be affected. Escalate |
| Female, homozygous P, X-linked | Sons 1/2 affected | Sons 1/1. Possibly affected herself. Escalate |

The flowchart in §7.2 shows this escalation, but the code limits it to `inheritance == "AR"`. The synthetic generator produces hemizygous males routinely, so this path would run constantly. A common condition like G6PD also needs its own rule, or 8% of males become urgent cases.

### C4. Zygosity and multiple variants are ignored [RUN]

| Input | Spec output | Problem |
|---|---|---|
| One person with two P/LP variants in HBB | Two `carrier` facts | Possible compound heterozygote. `docs/02` says to escalate |
| Homozygous × heterozygous couple | 1/4, 1/2, 1/4 | The maths assumes both are carriers. Affected should be 1/2 |
| Partner A has VUS **and** P in one gene | Numeric 25% | The dict keeps only the last finding, which **breaks the "VUS never produces a number" rule** |

The spec's own VUS test misses the third case.

### C5. The numeric validator can't support "0 numeric hallucinations" [RUN]

| Text | Result | Problem |
|---|---|---|
| "50% chance the baby has the condition and 25% chance of being a carrier" (swapped) | **Passes** | It checks that a number exists, not what it describes |
| نصف أطفالكما سيصابون ("half of your children will be affected") | **Passes** | Arabic number words aren't checked |
| "You carry one changed copy of the gene." | **Blocked** | "one" is flagged, so normal English falls back to templates |
| "If both partners are carriers the chance is 25%" (user is a single carrier) | **Blocked** | The most common education answer is rejected |
| "The background chance is 3 to 4%" | **Blocked** | Not in the allowed set |

**Fix:** pair each number with its label by having the LLM reference fact IDs that get filled in by code, such as `{{fact:couple_shared_ar:HBB:affected}}`. Then the LLM can't write numbers at all. Add a small approved "general facts" set and check Arabic number words.

### C6. In Arabic, "carrier" is routed as a clinical question [RUN]
The router's clinical pattern includes `حامل` to catch "pregnant", but **حامل also means "carrier"**.

| Question | Route |
|---|---|
| ماذا يعني أنني حامل للجين؟ ("What does it mean that I'm a carrier?") | `CLINICAL_ADVICE` |
| هل كوني حامل للمرض يعني أنني مريضة؟ ("Does being a carrier mean I'm ill?") | `CLINICAL_ADVICE` |
| What does carrier mean? | `EDUCATION` |

So the most basic question gets a refusal in the default language, and each one opens a case. The merge logic means the LLM can't correct it. This would also show up as an unfair Arabic-versus-English gap in the very metric R6 asks for.

**Fix:** match pregnancy through context (`أنا حامل`, `حامل في الشهر`, `حملي`), exclude `حامل لـ / حامل للـ`, and have Arabic speakers build the test set.

### C7. Blind matching leaks the partner's private findings [RUN]
`couple_facts` loops over the **union** of both partners' genes. With a partner-only finding it returned:
```
['couple_one_carrier_tested_negative:SMN1:affected']
```
`chat.py` returns `fact_ids` to the requester and puts the facts into the LLM context. So once match consent exists, A can read B's non-shared gene from an API response, which defeats the headline feature (R4).

**Fix:** make two functions. One builds a partner's view from the intersection only. The internal one never reaches a response or a prompt. Add a test asserting that no partner-only gene appears in any response.

### C8. Triage doesn't run when results arrive [READ]
`open_result_case` always creates P4. `score()` is called only from chat, and P2 only from match. So a possibly affected adult (P1) or a VUS (mandatory review) waits unless they happen to chat, and a couple who never run the match never become P2.
**Fix:** run triage during ingestion and whenever the facts change.

### C9. The counsellor queue is always empty [READ]
`my_queue` filters on `counsellor_id == me`, but nothing in the spec ever sets `counsellor_id` or writes the `assigned_counsellor` tuple. So P16 shows nothing, escalation reaches no one, and the demo's main human hand-off fails.
**Fix:** add an unassigned pool, a claim action, and a coordinator assignment rule.

### C10. Distress handling isn't safe enough [READ]
Distress opens a case with a 24-hour SLA, in a queue nobody sees (C9). The template's hotline is undefined. Distress detection is a short keyword list. Someone in crisis needs immediate help.
**Fix:** show verified UAE support contacts immediately (a counsellor must supply them, and never let an LLM produce them), alert a human at once, and test with Arabic and Gulf phrasing. Add a path for family coercion too, which the problem statement names and the router doesn't handle.

---

## 4. High-priority issues

### Risk and genetics

| ID | Issue | Evidence | Fix |
|---|---|---|---|
| **H1** | Residual risk ignores kinship when the partner tests negative. First cousins get the same figure as unrelated couples | [RUN] 0.00026 vs about 0.00101 kinship-adjusted, about 3.8× low on placeholder values | Use the kinship-adjusted prior in the Bayes formula, and have a geneticist confirm it |
| **H2** | A gene outside the table crashes, and unknown genes default to AR. DMD, which is X-linked, is labelled AR | [RUN] `KeyError 'ABCA4'`; `inheritance("DMD") = AR` | Fail safe: "no number, refer to counsellor". Never assume inheritance |
| **H3** | Gene-level matching misses alpha-thalassaemia across HBA1 and HBA2 | [RUN] Intersection empty for two alpha-thal carriers | Match by a clinician-reviewed "risk group", and flag condition-specific cases |
| **H4** | The NSGC empiric 1.7–2.8% is from unscreened couples, yet it's shown as residual risk after a negative 570-gene panel. Double first cousins get the same range | [READ] | Have a clinician reword it and set ranges. Don't present it as post-panel residual |
| **H5** | Couple-level X-linked risk isn't computed. AR Punnett squares are returned for X-linked genes and for single carriers with no partner | [RUN] | Add X-linked rules and a visual, and show squares only when the scenario applies |

### Privacy and consent

| ID | Issue | Evidence | Fix |
|---|---|---|---|
| **H6** | PII redaction fails open. Arabic names are never redacted (`lang == "en"` only), and a Presidio or spaCy failure silently disables it. The spaCy model isn't in the dependencies | [READ] | Fail closed. Add Arabic name handling plus an allowlist approach, and test in Arabic. "0 PII to LLM" can't be claimed until then |
| **H7** | The OpenFGA write and DB commit aren't atomic. If the commit fails after the write, **access exists with no consent record**. Duplicate tuples also error, which breaks a second grant or a second report | [READ] | Use an outbox plus a reconcile job, and idempotent writes |
| **H8** | Consent lifecycle gaps: couple-match consent can't be withdrawn and isn't in the ledger; expiry depends on a periodic job; a grantee has no endpoint to view a shared report; onboarding has no consent step; no "right not to know" (S4) | [READ] | Put all sharing in one ledger, use OpenFGA conditions for expiry, and add the missing flows |
| **H17** | The single-use invitation link is redeemed by a `GET`, so WhatsApp and SMS link previews will burn it | [READ] | `GET` shows the page. An explicit `POST` redeems it |
| **H18** | Encryption covers gene and variant, but `classification`, `zygosity`, `inheritance`, `is_pregnant`, `relationship_degree` and `case.reasons` are plaintext | [READ] | Encrypt them, or justify and document each exception |
| **H19** | Retention conflicts: Federal Law 2/2019 Art. 20 requires at least 25 years, while the spec has 90-day chat retention, cascade deletes and no erasure design. DUO is a research vocabulary, not a fit for sharing with a partner | [SOURCE] | Write a retention table, have counsel review it, and use a custom purpose vocabulary, with DUO for research only |

### Reliability and metrics

| ID | Issue | Evidence | Fix |
|---|---|---|---|
| **H9** | `get_db` opens a transaction before the LLM call. `idle_in_transaction_session_timeout` is 10 s, so slow answers lose the connection. Worst case is about 135 s (15 s timeout × 3 tries × 3 calls) | [READ] | Close the transaction before calling the LLM. Cut retries and set an overall deadline |
| **H10** | Pathway: direct `case.state =` assignments skip `PathwayStep`, so **escalated cases, the at-risk group, disappear from time-to-referral**. Users **can't decline after a test or referral is ordered**, despite "decline any step". `LOST_TO_FOLLOW_UP` and "not confirmed" don't exist. One `sla_due` per case | [READ] | Route every change through one function. Allow decline from all active states. Set SLAs per step |
| **H11** | Analytics: the fairness code overwrites rows, reporting a **2.0 pp gap when the real spread is 30 pp**. Age and gender aren't collected. Denied access attempts aren't recorded because the audit row rolls back with the failure, so that KPI has no data. Validator flags aren't stored | [RUN] for fairness, [READ] for the rest | Aggregate per dimension, add strata, and write security events in a separate transaction |
| **H12** | The directive validator misses Gulf dialect and soft phrasing (`لازم تسوون`, `المفروض`, "It would be best to", "Consider cancelling the wedding"). `docs/02` promises an LLM judge that the code lacks. Scoring validators with themselves is **circular** | [RUN] | Add a judge and dialect patterns, and have **independent humans** score a sample |

### Content, features and delivery

| ID | Issue | Evidence | Fix |
|---|---|---|---|
| **H13** | Copy breaks the project's own rules: "**You are healthy**" (P7) is inappropriate certainty and passes the diagnosis validator; "Carriers are healthy" overlooks trait symptoms and some X-linked carriers; "free genetic screening" for relatives is unverified; "confetti" after a risk quiz is the wrong tone | [RUN], [READ] | Use "Being a carrier usually doesn't cause illness", confirm eligibility, remove confetti, and have a clinician review all copy |
| **H14** | MVP features with no backend home. See the table below | [READ] | Added as `[NEW]` stubs, or cut per scope tiers |
| **H15** | The one-command demo fails: API container points at `127.0.0.1`; Redis requires a password that the URL lacks; no worker or beat service, so SLA jobs never run; issuer mismatch between `localhost` and `keycloak`; `alembic` runs as a role without DDL rights; BGE-M3 and torch on a read-only filesystem. **`openmined.psi` has no Windows wheels**, so `uv sync` will fail on this Windows machine | [READ], [SOURCE: PyPI] | Fix the compose file, make PSI an optional extra, and develop in Docker or WSL. This machine has Python 3.11; `uv` can install the required 3.12 |
| **H16** | CI fails as written: `pytest-cov` isn't a dependency; ruff `S` rules flag every `assert` in tests; the 100% risk-engine gate runs only one test file | [READ] | Add the dependency and per-file ignores, and widen the gate |

**H14 detail: features the docs mark as MVP with no module or endpoint**

| Feature | Missing |
|---|---|
| Sign-up and profile (P5) | Nothing creates a `Person` or links Emirates ID to login. `PATCH /v1/me` is called by the frontend but doesn't exist |
| Journey view (P6, P14) | Users can't read their own case, because `cases.py` is limited to counsellor roles |
| Booking (F9) | No model or endpoint |
| Values reflection (F7) | No endpoint for saving or sharing |
| Counsellor notes, referral builder (F18, F21) | No model or endpoint |
| Co-pilot summary (F18) | No module |
| Break-glass (F20) | No module or endpoint |
| Screening and centre finder (R2) | No module, endpoint or page, though R2 explicitly asks for access to screening |
| Voice (F5) | No module |
| Content governance (F26) | No endpoint |
| Invitation landing page (F11) | Not in the site map |
| Amended results (variant reclassified later) | No flow |

---

## 5. Medium-priority issues

| ID | Issue | Fix |
|---|---|---|
| **M1** | `docs/02` promises streaming chat, but validators need the full answer first. Streaming would show unvalidated text | Don't stream LLM tokens. Show a progress state |
| **M2** | Doc conflicts: SHA-256 vs HMAC audit chain; HAPI FHIR in the plan but not in compose; `frontend/src/api` vs `frontend/lib/api`; P5 sign-in placed inside the role guard; `lab_service` missing from the role list; `case` is a reserved SQL word | `backend.md` wins unless this document says otherwise. Rename to `care_case` |
| **M3** | The demo table has 8 genes while the plan says about 30. It has none for retinal disorders or glaucoma, two of Abu Dhabi's most common findings | Add representative genes, marked as placeholders |
| **M4** | Only one fallback template is written. `render_template` serves `general_carrier` to VUS and X-linked users, which is incorrect. Full coverage is about 60 files | Select by scenario and fail safe. Tier-1 scenarios first |
| **M5** | **Palette contrast fails the doc's own 4.5:1 rule** [RUN]: turquoise 2.96, terracotta 3.09, olive 2.62, rose 2.38, saffron 1.80 on white. Turquoise is used for chips and secondary actions. Neumorphic shadows make it worse | Keep these for fills with dark text, or add darker text variants |
| **M6** | `README.md` was UTF-16, so Git treated it as binary. No `.gitignore`, so `.env` could be committed | **Fixed in this session** |
| **M7** | OMIM, GeneReviews and Orphanet have reuse limits, while MedlinePlus is public domain | Check each licence, and write original text with citations |
| **M8** | `fhir.resources` is listed but the parser walks raw dicts, and malformed types cause 500s. Amended reports aren't handled | Validate first and add a report-version flow |
| **M9** | Small-cell suppression can be defeated by subtracting from totals | Add complementary suppression |
| **M10** | The global audit lock is held across OpenFGA network calls during ingestion | Write the audit row last |
| **M11** | "Has the condition" overstates risk for conditions with reduced penetrance, such as some glaucoma genes | Say "inherits two copies", with per-condition wording reviewed by a clinician |
| **M12** | The API's CSP blanks `/docs` in dev. Production guards skip LLM provider and key length | Relax the CSP on dev docs only, and extend the guards |
| **M13** | 20 screens × desktop, mobile and Arabic is 60 designs, plus a 10-slide story site | Tier-1 screens only in all variants |

---

## 6. Improvements worth adding

These go beyond fixing bugs and map to the judging criteria.

| Improvement | Why it helps | Criterion |
|---|---|---|
| **Fact-ID placeholders** so the LLM can't write numbers (C5) | Makes the safety claim actually true, and it is a strong demo moment | Responsible AI |
| **Live "try to break it" demo** of red-team prompts in Arabic and English | Proof, not claims | Responsible AI, demonstration |
| **Small real comprehension test** (S7) | Likely to stand out, and it answers R6 honestly | Health impact |
| **Commercial and pilot plan**: buyer, per-couple cost, counsellor hours saved, licensed partner (S4) | Currently the weakest criterion | Commercial viability |
| **Counsellor time-saved estimate**, clearly labelled as a model | Links to the workforce shortage | Commercial viability, impact |
| **Template-only demo mode as default** for recording | No LLM bill or outage risk on demo day | Demonstration |
| **Replace Keycloak and OpenFGA with mocks only if the team is 1 or 2 people** | Protects the core safety work | Working solution |
| **Enforce the `brain.md` rule in the PR template** | Keeps the log honest | Technical depth |

---

## 7. Checked and found correct

So nobody spends time re-checking these:

- **Arabic diacritics regex** in `lexicon.py`: it looks broken on screen because of right-to-left rendering, but the bytes form the correct ranges.
- **Residual-risk formula**: `q(1−d)/(1−q·d)` is correct Bayes. Only the prior needs fixing (H1).
- **Kinship coefficients**: 1/4, 1/8, 1/16 and 1/32 are correct.
- **At-risk rates**: 565/11,748 ≈ 4.8%, and 79/1,000 ≈ 7.9%, match the docs' "about 1 in 20" and "about 8%".
- **Al Amal**: reporting confirms government funding for IVF and PGT.
- **Core design**: deterministic engine, boundary labels, most-private-reveal-wins, 404 on denied access, and insert-only audit are all sound.

**Not verified:** the news and study citations in `docs/01` generally, LOINC codes against the current FHIR IG (spec marks these `VERIFY`), and Azure OpenAI availability in UAE North.

---

## Sources

- [Future Health Digital Innovation Challenge, Hack2skill](https://hack2skill.com/event/futurehealthchallenge/)
- [Federal Decree-Law 49 of 2023, Human Genome (DHA copy)](https://dha.gov.ae/uploads/062024/Federal%20Law_49_2023_Regulating%20the%20Use%20of%20the%20Human%20Genome202466484.pdf)
- [UAE government portal: fostering children of unknown parentage](https://u.ae/en/information-and-services/social-affairs/children/fostering-and-sponsoring-children-of-unknown-parentage)
- [Law-firm commentary on the UAE's 2023 IVF changes](https://www.mondaq.com/family-law/1394724/uaes-new-ivf-regulations-a-comprehensive-overview) · [BSA Law update](https://bsalaw.com/?p=4512)
- [Federal Law 2 of 2019, Article 20 retention (official text extract)](https://www.ehs.gov.ae/app_content/legislations/php-law-en-77/files/basic-html/page7.html)
- [Baker McKenzie: UAE data and cyber laws](https://resourcehub.bakermckenzie.com/en/resources/global-data-and-cyber-handbook/emea/uae/topics/key-data-and-cybersecurity-laws) · [Taylor Wessing on the PDPL](https://www.taylorwessing.com/de/insights-and-events/insights/2022/01/me-personal-data-protection-in-the-uae)
- [360Dx: Dubai premarital screening and Al Amal](https://www.360dx.com/molecular-diagnostics/mandatory-premarital-genetic-carrier-screening-program-dubai-ids-risk-couples)
- [PyPI: openmined.psi](https://pypi.org/project/openmined.psi/)
