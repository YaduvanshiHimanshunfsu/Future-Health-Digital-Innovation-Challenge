# 03 — Features, Limitations & Future Advancements

> **Scope update (5 Nov 2026):** Samvid is global by design. UAE and Abu Dhabi details in this document describe the first reference pack, not the limit of the product. Supported languages are English, Arabic and Hindi. See [docs/07](07_Global_Design_and_Country_Packs.md).

> Companion to [01_Problem_Understanding.md](01_Problem_Understanding.md) and [02_Solution_Architecture_and_Plan.md](02_Solution_Architecture_and_Plan.md).

---

## 1. Feature list (mapped to challenge requirements)

Legend: **MVP** = built for the 20 Nov submission · **V2** = after selection / pilot · **R1–R6** = the challenge requirements.

### 1.1 For individuals and couples
| # | Feature | Req | Stage | Description |
|---|---|---|---|---|
| F1 | **Plain-language result card** | R1 | MVP | "What your result means" in Arabic or English at 3 literacy levels, opening with *"Being a carrier is not an illness."* |
| F2 | **Couple risk explainer** | R1 | MVP | Per-pregnancy risk with a 100-person icon array, a Punnett square, and a "chance has no memory" explanation |
| F3 | **Uncertainty panel** | R1 | MVP | Residual risk, what the panel does *not* test, the meaning of a VUS, and *risk ≠ diagnosis* |
| F4 | **Ask Samvid (AI companion)** | R1/R3 | MVP | 24/7 chat grounded in curated content. Numbers come only from the risk engine, and every answer shows its **boundary label** (education / decision support / "this needs a counsellor") |
| F5 | **Voice mode** | R1/R6 | MVP (basic) / V2 | Listen to explanations in a Gulf-Arabic voice and ask questions by voice, for low-literacy users |
| F6 | **Options explorer** | R2 | MVP | All clinically appropriate paths shown with equal weight: natural conception (± prenatal diagnosis), IVF + PGT-M (Al Amal funding info), donor options, adoption, more testing, time to think |
| F7 | **Values reflection tool** | R2 | MVP | Private sliders and prompts. The results are reflected back to the user and **never** turned into a recommendation |
| F8 | **Faith and culture library** | R2 | V2 | Scholar-reviewed content on religious perspectives about IVF/PGT, shown **only on request** |
| F9 | **Book a counsellor** | R3/R5 | MVP | One tap from any answer to a qualified counsellor (in person or tele-genetics) |
| F10 | **Partner sharing: 3 modes** | R4 | MVP | Private / **couple-match only** (PSI reveals just the shared genes) / full share with field-level choice |
| F11 | **Anonymous family invitation** | R4 | MVP | Invite relatives to free screening without revealing who you are or what you carry, unless you choose to |
| F12 | **Consent centre** | R4 | MVP | See, scope, set an expiry on and **revoke** every share. Revocation takes effect immediately |
| F13 | **"Who saw my data" log** | R4 | MVP | Every access to your data, by whom and why, in plain language |
| F14 | **My care journey tracker** | R5 | MVP | Shows where you are (result, counselling, confirmatory test, specialist referral) and what happens next |
| F15 | **Teach-back check** | R6 | MVP | A short, friendly quiz ("Let's check we explained it well"). It tests *our* explanation, not the user |
| F16 | **Pre-conception mode** | R2 | MVP | For couples who are already married: request screening, the IVF/PGT pathway, pregnancy-aware triage |

### 1.2 For counsellors and physicians
| # | Feature | Req | Stage |
|---|---|---|---|
| F17 | **Triage queue (P1–P4) with SLA timers** | R3/R5 | MVP |
| F18 | **Case co-pilot summary**: RiskFacts, user questions, comprehension score, and the values notes the user *chose* to share (human-verified, never auto-written into the clinical record) | R3 | MVP |
| F19 | **Primary-care physician quick card**: a 2-minute script, plus a rule for when to refer | R3 | MVP |
| F20 | **Break-glass access** with a stated reason and an audit flag | R4 | MVP |
| F21 | **Referral builder**: FHIR `ServiceRequest` to the confirmatory lab or reproductive genomics clinic | R5 | MVP (mock) / V2 (Malaffi) |

### 1.3 For DoH programme managers
| # | Feature | Req | Stage |
|---|---|---|---|
| F22 | **Outcomes dashboard**: comprehension delta, counselling uptake, median time to referral, stalled cases | R6 | MVP |
| F23 | **Equity view**: every metric by language, literacy level, age, gender and region, with gap alerts | R6 | MVP |
| F24 | **Privacy view**: blocked access attempts, revocation latency, break-glass count, PII-to-LLM leak tests | R6 | MVP |
| F25 | **AI safety monitor**: validator block rate, escalation rate, flagged answers for human review | R3/R6 | MVP |
| F26 | **Content governance**: versioned condition cards with reviewer sign-off and rollback | R1 | MVP (basic) |

### 1.4 Platform and safety features (behind the scenes)
- **Deterministic risk engine**: the LLM never computes numbers.
- **5-layer output validators**: numeric consistency, stigma lexicon, directiveness, diagnosis claims, readability.
- **Template fallback**: if the LLM is unavailable or blocked, the system serves pre-approved text, so it never fails silently.
- **PII redaction** before every LLM call; sovereign LLM option (Jais via vLLM, in-country).
- **Hash-chained audit log**; envelope encryption; data minimisation (no raw genomes stored).
- **FHIR-native** to ease Malaffi / DoH integration.

---

## 2. What makes this solution different (pitch points)

1. **"Numbers from code, words from AI, decisions from people."** A safety architecture judges can verify, not just a chatbot.
2. **Dor Yeshorim-style blind matching, rebuilt with cryptography and choice.** Couples learn about *shared* risk without exposing every carrier finding, which directly addresses stigma.
3. **Non-directive by design and by test.** Directiveness is a measured metric with a target of zero, and cancelled marriages are explicitly *not* a KPI.
4. **Arabic-first and literacy-adaptive**, with voice mode and fairness metrics broken down by language and literacy.
5. **Closes the loop**: a traceable path from result to counsellor to confirmatory test to IVF/PGT, with SLA and stall alerts.
6. **Built for Abu Dhabi's real stack**: FHIR/Malaffi, UAE data residency, Keycloak ↔ UAE PASS, Jais/K2 (co-creator models), Azure UAE North (co-creator cloud).

---

## 3. Cons, limitations and risks (with mitigations)

### 3.1 Technical limitations
| Limitation | Impact | Mitigation |
|---|---|---|
| **Synthetic data only** in the MVP | We cannot claim real clinical validity | Use published carrier frequencies, design to the FHIR format, and pursue sandbox access with M42/DoH as a finalist |
| **LLM errors / hallucination** | Wrong or misleading statements | The LLM is limited to phrasing; numeric validator; template fallback; human review of flagged answers |
| **Arabic dialect coverage** | MSA may feel formal, and Gulf dialect quality varies across models | Use Jais (Arabic-strong); have native speakers review content; offer a "simpler Arabic" level |
| **PSI reveals the intersection** | The shared gene itself is revealed by design, since the couple needs to know it | Optional PSI-cardinality ("shared: yes/no") mode, with details released only in counselling |
| **Server still holds the data** in the MVP | The backend operator is trusted | Field encryption, strict RBAC/ReBAC, audit, and break-glass now. Roadmap: confidential computing, on-device keys and FHE |
| **Panel limits** (570 genes) | A negative result does not mean zero risk | Prominent residual-risk messaging; extended screening offered as an *option* for consanguineous couples |
| **Consanguinity input is self-reported** | Wrong kinship leads to an imprecise residual risk | The field is optional; ranges are shown instead of point estimates; the counsellor confirms |
| **Latency of LLM + validators** | Slower chat | Streaming, cached answers for common questions, a small router model |

### 3.2 Clinical and ethical risks
| Risk | Mitigation |
|---|---|
| Users treat AI explanations as medical advice | Visible boundary labels, a refusal-and-escalation pattern for clinical questions, a disclaimer on every screen |
| **Subtle directive bias** (e.g., listing IVF first) | Neutral or randomised ordering of options; directiveness red-team tests; counsellor review of content |
| Family pressure to share (e.g., a parent demanding to see results) | Sharing happens only from the individual's own authenticated session; "safe decline" wording; family packs carry no individual data |
| Gender-specific harm (women's marriage prospects) | Privacy defaults set to most private; anonymous invitations; gender-stratified harm monitoring |
| Anxiety from detailed information | Layered disclosure (summary first, details on request); distress detection leads to human support |
| Over-reliance shrinks human counselling | The system *routes to* counsellors and never replaces them; uptake of counselling is itself a KPI |
| Duty-to-warn dilemmas (a relative at high risk) | Out of scope for AI. Escalated to counsellors and handled under DoH policy |

### 3.3 Regulatory and adoption risks
| Risk | Mitigation |
|---|---|
| Data localisation (Federal Law No. 2 of 2019, Art. 13) | All hosting in the UAE region; sovereign LLM option; no cross-border LLM calls in production |
| AI as medical device classification | Keep to education and decision support with a clear boundary. Seek DoH regulatory guidance before any pilot |
| Integration effort with the lab, Malaffi and booking systems | FHIR-native design; integration adapters; start with a read-only feed |
| Trust and uptake among Emiratis | Co-design with Emirati users, endorsement by DoH and counsellors, culturally grounded branding |
| Counsellor workload rises because escalations increase | Triage priorities, co-pilot summaries, and AI handling of the basic education that currently takes counsellor time |

### 3.4 Honest scope boundaries (what Samvid does **not** do)
- It does not diagnose disease or interpret raw genomes.
- It does not recommend whether to marry, conceive or use any reproductive option.
- It does not contact relatives without the individual's explicit action.
- It does not replace accredited genetic counsellors or the physician–patient relationship.

---

## 4. Future advancements (roadmap)

### Near term (pilot, 3–6 months)
- **Real integration**: M42 / Emirati Genome Programme report feed, Malaffi FHIR, booking systems, **UAE PASS** login.
- **Co-designed content** with Emirati focus groups (men, women, elders, low-literacy groups) and DoH counsellors.
- **Clinical validation study**: a randomised comparison of Samvid plus usual care against usual care, measuring MMIC, SURE, GCOS-24, uptake and time to referral (IRB-approved).
- **More languages** for resident communities (Urdu, Hindi, Malayalam, Tagalog, Bengali), useful for wider pre-conception screening.
- **WhatsApp channel** (the dominant messaging app in the UAE) with the same guardrails.

### Mid term (6–18 months)
- **Confidential computing**: run the matching and explanation services in Azure Confidential Containers / Intel TDX enclaves so that even operators cannot read the data.
- **Client-held keys**: genetic findings encrypted with keys in the user's own wallet (UAE PASS vault), so the server stores only ciphertext.
- **Homomorphic encryption** (SEAL / OpenFHE) for population analytics on encrypted carrier data.
- **Federated learning** across hospitals for a better boundary router and triage models without centralising chats.
- **Expanded risk models**: polygenic and multifactorial context (for counsellors only), X-linked and dominant late-onset secondary findings with separate consent.
- **Pedigree-aware risk**: a family-tree builder (pedigreejs) that computes kinship coefficients from a user-drawn tree.
- **Avatar or video explanations** in Gulf Arabic, and a sign-language option.

### Long term (18 months+)
- **National cascade screening network**: privacy-preserving, consent-driven invitations at population scale, with a measurable rise in screening among relatives.
- **Newborn and prenatal continuity**: link premarital findings to newborn screening and prenatal care, with consent.
- **Population-health intelligence for DoH**: de-identified, differentially private maps of where comprehension or uptake lag, to target outreach (not to target families).
- **Open standard**: publish the Samvid safety framework (boundary labels, validators, metrics) as an open guideline for AI genetic education in Arabic.
- **Regional expansion**: adapt to KSA, Qatar, Oman, Bahrain and Kuwait premarital programmes with local panels and dialects.

---

## 5. Success metrics and targets (what we will show judges)

| Metric | MVP target (on the test set) | Pilot target |
|---|---|---|
| Numeric accuracy of risk statements | 100% | 100% |
| Stigmatising or directive outputs | 0 | < 0.1%, all reviewed |
| Correct escalation of clinical-advice questions | ≥ 95% | ≥ 98% |
| Teach-back comprehension improvement (pre → post) | Measured in a small real test, with no simulated figures | +25 pp vs usual care |
| Counselling uptake among at-risk couples | n/a | ≥ 90% |
| Median time from result to counselling (at-risk) | Tracked | ≤ 7 days |
| Comprehension gap between languages | < 5 pp | < 5 pp |
| Low vs high literacy gap | < 10 pp | < 10 pp |
| PII sent to the LLM | 0 (automated test) | 0 |
| Consent revocation latency | < 1 s | < 1 s |

> **Not measured as success:** number of marriages cancelled or any specific reproductive choice.

---

## 6. Likely judge questions (prepare answers)

1. **"Why not just use ChatGPT?"** Because of numeric hallucinations, no clinical boundary, no audit trail and no data residency. We show validator results.
2. **"How do you avoid coercion?"** Neutral option ordering, values reflection without scoring, directiveness tests, and cancelled marriages excluded from the KPIs.
3. **"How is family privacy protected?"** Three sharing modes, PSI blind matching, anonymous invitations, ReBAC, revocation and the access log.
4. **"What happens with a VUS?"** No number is shown; the user gets an "uncertain" explanation and a mandatory counsellor review.
5. **"How does this fit DoH systems?"** FHIR, Malaffi mapping, UAE hosting, Keycloak ↔ UAE PASS.
6. **"How will you prove it works?"** Built-in MMIC / SURE / teach-back instruments, stratified fairness metrics and a pilot study design.
7. **"What if the AI is down?"** Template fallback and booking a human are always available.
