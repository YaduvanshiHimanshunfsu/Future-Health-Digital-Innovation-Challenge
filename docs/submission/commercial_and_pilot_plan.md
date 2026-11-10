# Commercial and pilot plan

Covers the "commercial viability and path to pilot" criterion. **Every figure here is an assumption or an estimate, labelled as one**, with the working shown so a reader can change it. None is a measurement or a quote.

## Who buys and who uses

| Role | Who | Why they'd want it |
|---|---|---|
| **Buyer** | A health authority's screening programme, or the licensed provider running it | Results reach people as explanations instead of letters; counsellor time goes to the couples who need it; uptake and equity become measurable |
| **Users** | People with a carrier result, their partners, relatives they choose to tell | Private, plain-language understanding, and a person when they need one |
| **Staff users** | Genetic counsellors, coordinators | A queue ordered by urgency, summaries to verify, booking and referrals in one place |

It's sold to the programme, never to individuals: nobody pays to understand their own result.

## Value: the counsellor-time model (estimates)

The aim is not fewer counsellors. It's counsellor time spent where it changes something.

| Assumption | Value used | Change it if |
|---|---|---|
| Results per year in the programme | *N* (to be supplied by the partner) | |
| Share that are carriers needing explanation only | *c* | Local carrier rates differ |
| Share that are at-risk couples needing counselling | *r* | |
| Counsellor minutes per carrier, explaining by hand | 20 (assumption) | Partner's own figure |
| Minutes per carrier with Samvid, for questions it hands over | 5 (assumption) | Measured in the pilot |

Counsellor minutes freed per year ≈ *N* × *c* × (20 − 5). With *N* = 10,000 and *c* = 0.1, that's about 15,000 minutes, around **250 hours**, available for at-risk couples. **This is an illustration of the formula, not a forecast.** The pilot measures the real figures.

## Costs (structure, not quotes)

| Item | What drives it | Note |
|---|---|---|
| Hosting in the UAE region | Requests and storage; the stack is eight small containers | Required by Federal Law 2/2019 (Art. 13). To be quoted by a UAE cloud region |
| AI model | Questions asked × tokens | Optional: templates work alone. A local model on the same hosting has no per-call cost |
| Counsellors | Cases handed over | Already funded by the programme; Samvid redistributes their time |
| Clinical and language review | Content, per country and language | One-off per pack, then per change |
| Support and maintenance | Releases, security updates | |

Pricing model for discussion: an annual licence per programme, sized by results per year, with country packs priced as setup work. No price is set until the pilot measures the value.

## Licensed partner (Art. 28, Decree-Law 49/2023)

Storing or transferring genetic data in the UAE requires a Health Authority licence. Samvid can't hold real data alone, so the pilot runs **under a licensed partner**: a screening provider or hospital group that already holds the licence, hosts the system in its environment, and remains the data controller.

## Phased pilot

| Phase | What happens | Exit criterion |
|---|---|---|
| 0. Review (about 2 months) | Clinical sign-off of the Abu Dhabi pack, content and rules; Arabic text written and reviewed by native speakers; legal review of the open questions | Pack status set to "reviewed" by a named clinician |
| 1. Shadow (about 1 month) | Counsellors use the queue and summaries on synthetic and historical cases; no patient sees anything | Counsellors rate the summaries useful; routing recall measured on real phrasing |
| 2. Small live pilot (about 3 months) | Opt-in for a few hundred people receiving premarital results; every case also reviewed by a counsellor | Comprehension before and after, uptake, time to counselling, equity gaps, zero numeric errors |
| 3. Programme rollout | Under the partner's licence and hosting | Agreed with the authority |

## What we need from the first pilot partner

- The licence to hold genetic data, and UAE hosting.
- Two or more genetic counsellors' time for review and the shadow phase.
- Native Arabic and Hindi reviewers.
- Access to how results are delivered today, to settle the Art. 15(2) question about couples.
- A data processing agreement before any hosted AI model is used (the code refuses one in production until this exists).

## How new countries are added

A new country is a new **country pack** (`backend/packs/<code>/`): gene panel and frequencies, options allowed there, support contacts, centres, time targets, reporting groups, legal settings. No code changes. The India pack shows this already: switching pack changes the options and contacts. A pack counts as supported only once its clinical reviewer signs it off; until then the app shows it as unreviewed.
