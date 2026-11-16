# Assumptions, dependencies and limitations

A required deliverable. Written to be candid: where something isn't done, it says so.

## Assumptions

1. **People already have a carrier screening result**, from a programme such as the UAE premarital screening. Samvid explains results; it doesn't test anyone.
2. **A qualified person is reachable.** Every hard question is handed to a counsellor, so a real deployment needs counsellor time. Where a country pack says no service has been checked, the app says so instead of implying one.
3. **Results arrive as FHIR genetics reports** from an authenticated laboratory system.
4. **Partners and relatives choose to take part.** Nothing is shared with anyone without the person's consent, and a couple check needs both partners.
5. **The rules in the country packs are right for their country.** They are placeholders until clinically reviewed (see below).

## Dependencies

| Dependency | Needed for | If it's missing |
|---|---|---|
| Docker, PostgreSQL, Redis, Keycloak, OpenFGA | Running at all | Nothing works. Each is open source and runs locally |
| An AI model: Gemini (key) or Ollama (local) | Drafted explanations and the routing double-check | Reviewed templates answer instead. Every safety rule still holds |
| Genetic counsellors | Every case the app hands to a person | The core promise fails. A pilot needs them |
| Clinical reviewers | Signing off gene tables, risk wording, options and knowledge-base content | Content stays labelled as draft |
| Native speakers (Arabic) | Reviewing text, word lists and evaluation sets | The Arabic stays labelled as unreviewed; Arabic text isn't added |
| A licensed local partner | Storing or transferring genetic data in a pilot (Decree-Law 49/2023, Art. 28) | No real data can be used |
| Each country's screening services | The centre finder, referrals | Lists stay empty, and the screen says so |

## Limitations

### What the prototype is
- **Synthetic data only.** No real person, result or family is in it. Demo numbers are labelled synthetic on screen.
- **Placeholder carrier frequencies.** Every gene entry is marked `source: placeholder`. They aren't measurements of any population.
- **No clinical review.** No clinician has signed off the gene tables, the risk rules (including G6PD), the "must inform" rule, or the knowledge base. All of it is labelled draft.
- **No native-speaker review.** The Arabic interface and all non-English evaluation items were written by the team.
- **Arabic:** the interface is in Arabic (Modern Standard Arabic, right to left), approved by the user on 15 Nov 2026. **It was drafted without a native speaker's review**, and every Arabic page says so in a banner. Backend text is still English in Arabic mode: explanations from reviewed templates, error messages, and names that come from the country packs (country, region, city and centre names). Arabic questions typed in Roman letters are understood; Arabic script goes to a person.

### Safety
- **Routing misses some unfamiliar phrasing.** On questions never used to write the rules, 10 of 59 meant for a person got an automatic answer with rules alone; 5 of 59 with a local model double-checking. The target of 95% recall in each language is **not met**. Each of those answers was still validated, so the failure is a missed hand-off, not an unsafe sentence. See [docs/evaluation/](../evaluation/).
- **Gemini is untested live.** The key on the development machine is rejected by Google; the client is tested against a fake service only. Local Ollama is tested live.
- **No human scoring yet** of answers for tone, and no penetration test by an outsider.

### Evidence
- **No user testing yet.** The comprehension test is designed but hasn't run, so there is no evidence people understand better, and none is claimed.
- **The equity dashboard runs on invented activity.** Any gap it shows is noise.

### Mocks in this prototype
| Feature | State |
|---|---|
| Notifications (reminders, appointment changes) | Mock: recorded, never sent |
| Lab attestation | "demo" mode: authenticated lab reports are trusted. Refused in production |
| Centre finder | Real, with empty lists until filled from a public source |
| Story-mode slides, content governance screen, read-aloud on all pages | Not built (the story page says so) |

## Legal questions still open

From the team's reading of UAE law (see `docs/04`, S4 to S6). Not legal advice; a lawyer needs to confirm each.
- **Art. 28, Decree-Law 49/2023:** genetic data needs a licensed party to store or transfer it. A pilot must run under one.
- **Art. 15(2):** the premarital programme informs couples of results. Samvid's private couple mode protects each partner's *non-shared* findings, and doesn't promise a partner never learns a shared one.
- **Art. 9(3):** results that threaten life must be disclosed, which limits the right not to know. A counsellor needs to define that rule; it isn't built.
- **Federal Law 2/2019:** health data stays in the UAE (Art. 13) and is kept at least 25 years (Art. 20). The prototype's retention isn't aligned yet.
- **Options:** donor gametes and adoption aren't offered in the Abu Dhabi pack (fostering, kafala, is), pending a counsellor's confirmation.
