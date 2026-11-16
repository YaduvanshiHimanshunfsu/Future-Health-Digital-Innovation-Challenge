# 01 — Problem Understanding

> **Scope update (5 Nov 2026):** Samvid is global by design. UAE and Abu Dhabi details in this document describe the first reference pack, not the limit of the product. Supported languages are English and Arabic. See [docs/07](07_Global_Design_and_Country_Packs.md).
>
> **Scope update (16 Nov 2026):** the prototype ships one country pack, Abu Dhabi, in English with an Arabic translation. The pack framework stays, so another country is settings rather than code, but no second pack is shipped or claimed.

**Hackathon:** Future Health Digital Innovation Challenge 2026 (Hack2skill)
**Track:** Fertility · Challenge 03: *Understanding and Reducing Inherited Disease Risk*
**Project name:** **Samvid** (Sanskrit संविद्: knowledge and understanding, and also agreement and consent).
**Team:** Vigyan_Viveka_Vijaya

---

## 1. About the hackathon

| Item | Detail |
|---|---|
| Organiser | *Future Health – A Global Initiative by Abu Dhabi*, curated and convened by the **Department of Health – Abu Dhabi (DoH)** |
| Founding partners | PureHealth, **M42** (runs the Emirati Genome Programme), Institute for Healthier Living Abu Dhabi, Mubadala Bio |
| Strategic / associate partners | Mediclinic Middle East / Burjeel Holdings |
| Co-creators (technical mentors) | **Inception42** (G42, makers of the *Jais* Arabic LLM), **MBZUAI** (AI university, *K2 Think*), **Microsoft** (Azure) |
| Theme | **"To Sense is to Predict"**: turn health signals into earlier insight and timelier action |
| Focus areas | Fertility · Population Health · Wellbeing |
| Requirement | Technology-neutral: "Use the AI, software, sensing, or hardware that best fits the problem." Ideas, existing solutions and early prototypes are eligible, and **a working prototype must be submitted** |
| Deadline | Registration closes **10 Nov 2026** (the team is registered). Working prototype due **20 Nov 2026**. Evaluation 20–30 Nov. The top three present at **GITEX 2026**, 7–11 Dec |
| Prizes | USD 50k / 35k / 20k (USD 105k pool), plus possible **validation, incubation and piloting** in Abu Dhabi |
| Links | [Hack2skill page](https://hack2skill.com/event/futurehealthchallenge/) · [Press release (Zawya)](https://www.zawya.com/en/press-release/companies-news/future-health-launches-global-challenge-to-move-health-innovation-towards-real-world-application-1680763) · [WAM](https://www.wam.ae/en/article/c2r7j8n-future-health-launches-global-challenge-move) · [Abu Dhabi Media Office topic page](https://www.mediaoffice.abudhabi/en/topic/future-health-challenge/) |

> Official requirements, judging criteria and FAQ answers are recorded in [submission/competition_requirements.md](submission/competition_requirements.md).

**What this tells us about the judges:** this is a government-led challenge with a real deployment path. They will reward solutions that (a) plug into the infrastructure Abu Dhabi already has (Emirati Genome Programme, premarital screening, the Malaffi health information exchange, DoH counselling clinics), (b) respect UAE data law, (c) are culturally intelligent, and (d) measure outcomes properly. A generic chatbot will not stand out. A **safe, auditable and privacy-first system** that a DoH pilot could actually run will.

---

## 2. The problem statement, decoded

> *"How might we help individuals, families and health systems identify, understand and reduce inherited disease risks associated with consanguinity through innovative, culturally appropriate and privacy-preserving technologies?"*

### 2.1 Key terms explained

| Term | Plain meaning |
|---|---|
| **Consanguinity** | Marriage between blood relatives (most often first or second cousins). |
| **Autosomal recessive (AR) disease** | A condition that appears only when a child inherits **two** faulty copies of the same gene, one from each parent. Examples: thalassaemia, sickle-cell disease, congenital adrenal hyperplasia (CAH), spinal muscular atrophy (SMA). |
| **Carrier** | A healthy person with **one** faulty copy. Carriers are almost always **not ill**. Most people carry several recessive variants. |
| **Couple-level compatibility** | Whether **both** partners carry a variant in the **same** gene. Only then is there a high (25%) risk per pregnancy. |
| **X-linked condition** | The gene sits on the X chromosome. A carrier mother has a 50% chance per son of an affected boy (e.g., G6PD deficiency, Duchenne muscular dystrophy). |
| **VUS** (variant of uncertain significance) | A DNA change whose effect is not yet known. It must **not** be treated as "positive". |
| **Residual risk** | The risk that remains after a negative test, because no test covers every gene or variant. |
| **Pre-marital vs pre-conception screening** | Pre-marital testing is done before the marriage contract (mandatory for Emiratis). Pre-conception testing is done before a pregnancy, including for couples who are already married. |
| **Reproductive options** | Natural conception with prenatal diagnosis, IVF with **PGT-M** (pre-implantation genetic testing for monogenic disease), donor gametes, adoption, or proceeding with informed acceptance. In the UAE, IVF/PGT for at-risk Emirati couples is government-funded through the **Al Amal initiative**. |

### 2.2 The core risk numbers (the engine must get these exactly right)

```
Both partners carriers of the SAME AR gene → each pregnancy:
   25%  affected child
   50%  healthy carrier child
   25%  child neither affected nor carrier
   (Chance has no memory: the risk is 25% for EVERY pregnancy.)

One partner carrier, other tested negative → small residual risk
   ≈ P(partner still a carrier despite negative test) × 1/4

First-cousin couple, no screening → added risk of a serious genetic
   condition or birth defect ≈ +1.7–2.8% above the population baseline of ~3–4%
   (NSGC recommendations, Bennett et al., 2002)

X-linked, carrier mother → each son 50% affected, each daughter 50% carrier
```

The key point: **consanguinity does not cause disease.** It raises the chance that both partners inherited the **same** rare variant from a shared ancestor. That is why the risk is shared across the whole family tree, and why one person's result says something about their relatives.

### 2.3 The six requirements, in plain words

| # | Requirement | What it really asks | Hidden difficulty |
|---|---|---|---|
| 1 | **Risk explanation** | Explain carrier status, couple risk and child risk in plain, non-stigmatising language, including uncertainty and *risk ≠ diagnosis* | Low health literacy and numeracy; Arabic (Gulf dialect) plus English; LLMs hallucinate numbers; the words chosen can stigmatise ("defective", "incompatible") |
| 2 | **Informed, values-sensitive choices** | Help people reach screening, counselling and reproductive options **without steering** them | Non-directiveness is a core ethic of genetic counselling. A system tuned to "reduce at-risk marriages" would breach it |
| 3 | **Qualified human counselling** | Escalate complex, high-impact or ambiguous findings to accredited professionals; keep **education / decision support / clinical advice** clearly separate | The workforce is small (around 40 genetic counsellors across the Arab region, mostly in KSA and UAE), so triage must be smart |
| 4 | **Privacy-preserving family workflows** | Explicit consent, role-based access, data minimisation, auditable sharing; individuals control what a partner or family member sees | Genetic data is *familial by nature*. Sharing with relatives creates real tension between privacy and a "duty to warn" |
| 5 | **Safe linkage to services** | A **traceable** path from result to counselling, confirmatory testing and specialist reproductive genomics | Today these hand-offs live in separate systems, and nobody measures time to referral |
| 6 | **Measurable comprehension and access** | Show better understanding, counselling uptake, time to referral, privacy protection and fairness across languages and literacy levels, **without** using cancelled marriages as the success metric | Needs validated instruments and stratified analytics designed in from day one |

---

## Global context

Couples related as second cousins or closer, and their children, were estimated at [10.4% of the world's population](https://pmc.ncbi.nlm.nih.gov/articles/PMC2868287) (a 2009-era estimate, known to be incomplete). Rates are highest in north and sub-Saharan Africa, the Middle East, and west, central and south Asia. The rest of this section uses Abu Dhabi as the worked example, because the challenge is hosted there and its programme is well documented.

## 3. Context: why Abu Dhabi, why now

### 3.1 Consanguinity in the UAE and region

- A study of 2,033 married UAE women (1994–95) found a **consanguinity rate of 50.5%**, up from 39% one generation earlier. First-cousin marriage was 26.2% and double first-cousin marriage 3.5%. It was higher in Al Ain (54.2%) than Dubai (40%). [Al-Gazali et al., *Consanguineous marriages in the UAE* (UAEU record)](https://research.uaeu.ac.ae/en/publications/consanguineous-marriages-in-the-united-arab-emirates/)
- An Al Ain births study found first-cousin marriage far more common among parents of babies with malformations (51% vs 30%), and concluded that genetic disorders account for a significant share of congenital malformations in the UAE. [Al-Gazali et al., J Med Genet](https://jmg.bmj.com/content/32/1/7)
- Newer local studies vary widely: **23.4%** in a Sharjah survey of 457 married adults, where 61.5% agreed that cousin marriage "keeps property within the family" and 75.9% knew it may affect children's health. Other convenience samples report up to about 65%. [Sharjah study (Egypt J Hosp Med)](https://www.ajol.info/index.php/ejhm/article/view/294631/277264) · [Bangladesh J Med review](https://banglajol.info/index.php/JOM/article/view/67269)
- Qatar is estimated at 35–54%. [Genome Medicine 2024](https://genomemedicine.biomedcentral.com/articles/10.1186/s13073-024-01307-6)
- The **CTGA database** (Centre for Arab Genomic Studies, Dubai) catalogues **665 genetic conditions and 1,365 variants in Emiratis**, including disorders unique to the Emirati population. [CTGA UAE paper, Frontiers in Genetics 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10194840/) · [CTGA portal](https://cags.org.ae/en/ctga-overview)

### 3.2 What Abu Dhabi has already built (the "strong foundation")

| Initiative | Status | Link |
|---|---|---|
| **Emirati Genome Programme** (DoH and M42) | About 750k+ genomes sequenced toward a 1M goal. It powers the premarital panel | [M42](https://m42.ae) |
| **Premarital genetic screening, Abu Dhabi** | Pilot in 2022, mandatory for Emiratis from **Oct 2024** (Abu Dhabi) and **Jan 2025** (UAE-wide). Covers **570 genes / 840+ recessive conditions**, with results in about 14 days at 22 primary-care centres | [WAM](https://www.wam.ae/en/article/b625ku2-genetic-testing-mandatory-for-premarital) · [MoHAP](https://mohap.gov.ae/en/w/mohap-announces-mandatory-genetic-testing-as-part-of-premarital-screening-for-emiratis-starting-early-january-2025) · [Gulf News explainer](https://gulfnews.com/uae/health/explained-mandatory-genetic-tests-in-uae-to-protect-future-generations-1.104274156) |
| **Outcomes to date (Abu Dhabi)** | **11,748 couples tested** from 2022 to July 2026, with **565 at-risk ("incompatible") couples (~5%)**. Most common conditions: CAH, inherited retinal disorders, primary ciliary dyskinesia, thalassaemia, sickle-cell disease, glaucoma. More than 100 Emirati doctors trained in genomics | [Gulf News, Oct 2026](https://gulfnews.com/uae/health/abu-dhabi-genetic-screening-flags-565-incompatible-cases-among-couples-1.500697261) |
| **Dubai programme (Nature Medicine, 2025)** | First 1,000 couples: **79 at risk (~8%)**. **80% chose to proceed with marriage** while considering funded IVF/PGT. In about 64% of at-risk couples both partners carried the *identical* variant, suggesting shared ancestry. **49% believed carrier status affects marriage suitability**, which is direct evidence of stigma | [360dx summary](https://www.360dx.com/molecular-diagnostics/mandatory-premarital-genetic-carrier-screening-program-dubai-ids-risk-couples) · [Nature conference page](https://precision-medicine.conferences.nature.com/journal-artciles/citywide-premarital-genomic-screening-middle-eastern-population) |
| **Abu Dhabi Programme for the Future of Reproductive Health** | Over 2,000 experts across 250+ facilities, with a roadmap to 2030 | [Media Office](https://www.mediaoffice.abudhabi/en/health/abu-dhabi-programme-for-the-future-of-reproductive-health-an-integrated-ecosystem-shaping-standards-research-and-innovation/) |
| **Malaffi** | Abu Dhabi's health information exchange, which any service must integrate with | [malaffi.ae](https://malaffi.ae) |

### 3.3 So what is the gap?

Abu Dhabi has solved **testing**. The challenge is about everything **after** the lab result:

```
 [Test done] ──► [Result understood?] ──► [Counselling?] ──► [Informed choice?] ──► [Care pathway?] ──► [Family informed?]
     ✅              ❌ weak                 ⚠ capacity-limited     ⚠ cultural pressure    ⚠ fragmented          ❌ privacy minefield
```

1. **Comprehension gap:** results are probabilistic, and people mix up *carrier* with *sick* and *25% risk* with *one in four children*.
2. **Counselling capacity gap:** there are few accredited genetic counsellors, and 565+ at-risk couples (plus every carrier with questions) compete for their time.
3. **Values gap:** cousin marriage is a long-standing, valued practice, and some see test results as *qadar* (destiny). Messaging must inform without judging.
4. **Privacy gap:** a carrier result implicates parents, siblings and cousins. Sharing it without consent can damage marriage prospects (especially for women) and family relationships.
5. **Pathway gap:** there is no single traceable path from result to counsellor to confirmatory test to IVF/PGT clinic, so drop-offs go unseen.
6. **Measurement gap:** success is implicitly measured by *cancelled marriages*, which is ethically wrong and does not capture informed choice.

---

## 4. Why this is a problem (impact)

| Dimension | Why it matters |
|---|---|
| **Health burden** | Recessive disorders such as thalassaemia, SMA and CAH cause lifelong illness, high treatment cost (for example, transfusions and chelation for thalassaemia; gene therapy for SMA costing over USD 2M), and child mortality. |
| **Psychological harm** | Misunderstood results cause anxiety, guilt ("my family's blood is bad"), false reassurance from a negative result, or **inappropriate certainty**. |
| **Social harm and stigma** | In Dubai, 49% believed carrier status affects marriage suitability. Disclosure can harm marriage prospects, women especially, and create family tension. |
| **Autonomy and ethics** | Coercive or directive systems breach the principles of genetic counselling and could erode trust in a national genomics programme that depends on public participation. |
| **System inefficiency** | Counsellors spend time repeating basic education instead of handling complex cases. Referrals are lost between centres. |
| **Evidence gap** | Earlier programmes in the region measured only marriages cancelled, so it is unknown whether people actually understood their results. |

### Lessons from the region's history

- **Saudi Arabia (2004–2009):** the premarital programme reduced at-risk couples by about 60% and cancellations rose from 9.2% to 51.9%. Even so, many at-risk couples married anyway (one citation puts it at 73%), often citing destiny or underestimating risk. Certificates were issued regardless of result. [Memish & Saeedi, Ann Saudi Med 2011](https://pubmed.ncbi.nlm.nih.gov/21623050/) · [Gosadi et al., Jazan 2021](https://doaj.org/article/75ddaabb9623436cbbbb38450e4b23d4)
- **Iran (1996 onward):** 2.7M couples screened in the first five years. Affected thalassaemia births fell from 2.53 to 0.82 per 1,000 in one region. Gaps came from couples who married before screening began and from under-served provinces, where 78.6% were not screened. [PMC527672](https://pmc.ncbi.nlm.nih.gov/articles/PMC527672) · [PMC3521888](https://pmc.ncbi.nlm.nih.gov/articles/PMC3521888)
- **Cyprus:** the classic thalassaemia success story combined screening, counselling, church and community engagement, and reproductive options. A review concludes that **screening works only when it is packaged with counselling and accessible reproductive options**. [Malaysian J Med review 2024](https://e-mjm.org/2024/v79n3/thalassaemia-screening.pdf)
- **Qatar:** premarital screening has been mandatory since 2009, but SCD and thalassaemia remain high. The panel covers only 4 of 37 locally relevant variants. [Qatar PSGC studies](https://pubmed.ncbi.nlm.nih.gov/30820415/) · [Frontiers 2023](https://www.frontiersin.org/articles/10.3389/fpubh.2023.1228010)

**Takeaway:** mandates and lab tests are not enough. **Understanding, trust, counselling and accessible options** decide the outcome. That is exactly the layer this challenge asks for.

---

## 5. Work done so far (global landscape)

### 5.1 Public screening programmes
| Programme | Approach | Link |
|---|---|---|
| UAE / Abu Dhabi premarital genomic screening | 570-gene panel, counselling at primary care, Al Amal IVF/PGT funding | See §3.2 |
| Saudi Premarital Screening & Genetic Counselling Program | Haemoglobinopathies; certificate issued regardless of result | [PubMed 21623050](https://pubmed.ncbi.nlm.nih.gov/21623050/) |
| Qatar PSGC | Mandatory since 2009 | [PubMed 30820415](https://pubmed.ncbi.nlm.nih.gov/30820415/) |
| Iran national thalassaemia programme | Primary-care screening and counselling | [PMC527672](https://pmc.ncbi.nlm.nih.gov/articles/PMC527672) |
| **Dor Yeshorim** (Orthodox Jewish community) | **Anonymous compatibility matching:** individuals get an ID and are *never told their own carrier status*. Two IDs are checked and only "compatible / not compatible" is returned. This is a **culturally adapted, privacy-first** model for a community that also practises arranged marriage | [Wikipedia](https://en.wikipedia.org/wiki/Dor_Yeshorim) · [Jewish Standard feature](https://jewishstandard.timesofisrael.com/screening-jewish-genes-4/) |

### 5.2 Clinical guidelines
- **ACMG 2021 practice resource:** Tier 3 (113 genes) for all preconception patients; **Tier 4 should be considered for consanguineous couples (second cousins or closer)**. [Gregg et al., Genet Med 2021](https://doi.org/10.1038/s41436-021-01203-z) · [Summary](https://www.obgproject.com/2021/07/25/acmg-recommendations-for-preconception-and-prenatal-carrier-screening/)
- **NSGC recommendations for consanguineous couples:** risk figures and a counselling approach. [Bennett et al., J Genet Couns 2002](https://doi.org/10.1023/A:1014593404915)

### 5.3 Digital genetic counselling and chatbots
| Work | What it showed | Link |
|---|---|---|
| **Gia** (Genetic Information Assistant, Clear Genetics / UVA / Geisinger) | Chatbot for pre-test education and **family sharing** of results. Being trialled for cascade testing, where usual uptake is only about 10% | [NCT04142333](https://clinicaltrials.gov/study/NCT04142333) · [NCT04428736](https://clinicaltrials.gov/study/NCT04428736) |
| LLM chatbot for positive hereditary-cancer results (JMIR Cancer 2025) | RAG plus few-shot GPT-4 is feasible but **needs program-specific accuracy work** | [JMIR Cancer e65848](https://cancer.jmir.org/2025/1/e65848/PDF) |
| GPT-3.5 vs GPT-4 on genetics questions (JAMIA 2024) | GPT-4 is better but **still makes notable errors** | [PMC11413464](https://pmc.ncbi.nlm.nih.gov/articles/PMC11413464/) |
| Generative AI for rare-disease counselling (Korea 2025) | Generally reliable, but **accuracy varies significantly by disease** | [PMC11941130](https://pmc.ncbi.nlm.nih.gov/articles/PMC11941130/) |
| CGT-LLM chatbot (open source, Hugging Face) | RAG over literature with ChromaDB, MIT licence. Useful reference code | [HF Space](https://huggingface.co/spaces/alrahrooh/cgt-llm-chatbot) |

**Gap:** there is no Arabic-first, consanguinity-aware tool that keeps an auditable boundary between AI education and human clinical advice.

### 5.4 Risk communication research
- Icon arrays (for example, 100-person grids) improve understanding, especially for low-numeracy users, and reduce *denominator neglect*. [MDM 2010](https://journals.sagepub.com/doi/10.1177/0272989X10369000) · [Uncertainty in icon arrays RCT](https://pmc.ncbi.nlm.nih.gov/articles/PMC9731905/) · [Birth-choice risk formats RCT](https://pmc.ncbi.nlm.nih.gov/articles/PMC12592780/)

### 5.5 Genomic privacy research
| Work | Relevance | Link |
|---|---|---|
| Baldi et al. 2011, *Countering GATTACA* | Private genetic **compatibility testing** using private set intersection (PSI) | [arXiv 1110.2478](https://arxiv.org/abs/1110.2478) |
| Ayday, Raisaro, Hubaux 2013 | Privacy-preserving disease-susceptibility test (homomorphic encryption) | [EPFL](https://infoscience.epfl.ch/handle/20.500.14299/94332) |
| Blatt et al. 2020 | GWAS on fully encrypted data | [ePrint 2020/563](https://eprint.iacr.org/2020/563) |
| FHE-Bloom genetic testing (2017) | Encrypted disease-variant lookup on an untrusted cloud | [BMC Med Genomics](https://link.springer.com/article/10.1186/s12920-017-0277-y) |
| Gymrek et al. 2013 / Erlich et al. 2018 | Genomes can be **re-identified**, and one person's DNA exposes relatives | [Science 2013](https://doi.org/10.1126/science.1229566) · [Science 2018](https://doi.org/10.1126/science.aau4832) |
| iDASH genomic privacy competitions | Benchmarks for secure genomic computation | [humangenomeprivacy.org](http://www.humangenomeprivacy.org) |
| Dynamic consent (Kaye et al. 2015) | Granular, revocable digital consent interface | [EJHG](https://www.nature.com/articles/ejhg201471) |

### 5.6 Regional cultural research
- UAE genetic counsellors on ethical, cultural and religious dynamics: themes include stigma, faith as resilience, and family decision-making. [PMC12619030](https://pmc.ncbi.nlm.nih.gov/articles/PMC12619030/)
- Genetic counselling in the Middle East: workforce and practice review. [medRxiv 2023](https://www.medrxiv.org/content/10.1101/2023.09.07.23292346.full.pdf)
- Qatar anthropology: risk, consanguinity, morality and gender are decided *through kinship*. [Kilshaw et al.](https://discovery-pp.ucl.ac.uk/10071603/1/Kilshaw_Arranging%28A%26M2015%29PBS.pdf)

### 5.7 Measurement instruments
- **MMIC** (Multidimensional Measure of Informed Choice: knowledge, attitude, behaviour), already adapted for reproductive carrier screening. [PMC4867447](https://pmc.ncbi.nlm.nih.gov/articles/PMC4867447) · [PMC5060463](https://pmc.ncbi.nlm.nih.gov/articles/PMC5060463)
- **Ottawa Decisional Conflict Scale / SURE test**. [Ottawa decision aids](https://decisionaid.ohri.ca/eval_dcs.html)
- **GCOS-24** (Genetic Counselling Outcome Scale, which measures patient empowerment). McAllister et al., *Eur J Hum Genet* 2011.

---

## 6. Problem summary (one paragraph for the pitch)

> Abu Dhabi now screens every Emirati couple for 840+ inherited conditions, and about 1 in 20 couples learns they share a risk. Results are probabilistic, deeply familial and culturally sensitive, and accredited counsellors are scarce. Today there is no private, Arabic-first and non-directive way for people to understand what their result means, decide in line with their own values, reach the right specialist quickly, and choose what to share with a partner or relatives. Without that layer, the national investment in genomics risks producing anxiety, stigma and lost referrals instead of informed choices.

## 7. Who we are building for (stakeholders)

| Persona | Need |
|---|---|
| **Fatima, 24, engaged to her cousin** | "Am I sick? Will our children be sick? Can we still marry? Who will know?" |
| **Couple who are already married, planning a pregnancy** | Pre-conception screening, IVF/PGT pathway, Al Amal funding |
| **Mother / family elder** | Wants to "know" a relative's result. Needs a respectful path that does **not** expose individual data |
| **Family physician at a primary-care centre** | Explains results in a short visit and needs a clear rule for when to refer |
| **Accredited genetic counsellor** | A triaged queue, a pre-summarised case, and more time for complex cases |
| **DoH programme manager** | Dashboards on comprehension, uptake, time to referral, fairness and privacy incidents |
