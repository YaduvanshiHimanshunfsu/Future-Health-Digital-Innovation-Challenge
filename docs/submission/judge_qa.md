# Judge Q&A

Short answers the team should be able to give without notes (V6.5.5). Each points to proof.

## Why not just ChatGPT?

A general chatbot writes its own numbers, has no clinical boundary, keeps no audit trail, and sends the question abroad. In Samvid a model never sees a figure: it gets placeholders, and code fills in the engine's exact numbers. Every draft is checked against wording rules, and any failure falls back to reviewed text. Clinical questions and distress never get a model's answer. Across 96 evaluated answers there were no wrong figures, no other person's gene and no ID (`docs/evaluation/`).

## How do you avoid coercion?

Options are shown with equal weight and no ranking or "recommended" badge, and the person's values never change them (a test proves options don't depend on values). Wording rules block directive language in English and Arabic. Messages about pressure from family go to a person. No metric counts a marriage or any one choice as success: there's a test for that too.

## Is it really PSI?

No. The couple match runs on our server, which decrypts both partners' findings in memory to compare them. It isn't a blind protocol, and we don't describe it as one. What it guarantees is minimal disclosure: only the view built for each partner leaves the server, a partner's other findings appear in no response, log or AI context, and a test scans for exactly that (V3.3.4).

Two limits we state plainly:
- A person with one finding learns the gene from a "yes", because it can only be that one. The product says so, and people have to accept that before agreeing.
- If a programme already tells couples their shared result, as Article 15(2) in the UAE may mean, our couple mode can't promise that a partner never learns it. What it protects is each partner's non-shared findings (S6).

Private set intersection is a possible later step for partners tested at different institutions. It isn't built.

## Which options are legal here?

The options come from each country's pack, not from code. For Abu Dhabi, donor gametes and adoption aren't offered, because our reading of the law says they aren't available; fostering (kafala) is. That list still needs a counsellor's sign-off, and the app shows the pack as unreviewed until then.

## What happens with an uncertain result?

No number is ever shown for it. The person gets words saying the meaning isn't known yet, and the case goes to a counsellor. The general carrier text, "usually doesn't cause illness", is never shown for uncertain or X-linked results, because it would falsely reassure (V4.3.8).

## What's the evidence people understand?

Honestly, none yet. The product records each person's before-and-after understanding scores, and the volunteer test protocol is ready, but it hasn't run. We show no simulated figures in its place.

## What if the AI is down?

Nothing breaks. Gemini falls through to the local model, and that falls through to reviewed templates. Booking a person is always available. The demo is recorded in template mode for that reason.

## How does it fit the health system?

Lab results come in as FHIR genetics reports. Referrals go out as FHIR R5 `ServiceRequest` and `Task` records with only the minimum fields. Sign-in is standard OIDC, so a national identity provider can sit behind Keycloak. Health data must stay in the UAE, so production hosting must be there.

## What does this cost, and who pays?

The screening programme pays, never the individual. The main value is counsellor time moved from explaining routine results to the couples who need counselling. The pilot measures that; we show the formula, not a forecast (`commercial_and_pilot_plan.md`).

## How do you know the routing works?

Partly. We measured it on questions that were never used to write the rules: rules alone missed 10 of 59 questions meant for a person; with a local model double-checking, 5 of 59. Our target is 95% in each language, and it isn't met yet. A miss means a lost hand-off, not unsafe text: every answer is still validated. The fix is native-speaker word lists and a stronger model check, and we report it rather than hide it.
