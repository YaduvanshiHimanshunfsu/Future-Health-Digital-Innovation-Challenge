# Samvid: Stitch Frontend Prompts

Every prompt you need to design the Samvid frontend in [Google Stitch](https://stitch.withgoogle.com). Each code block is ready to paste.

**Who does what:** you generate the screens here and export them. I then turn them into the working Next.js app, add real animation, and connect the backend.

**This file replaces §3 and §5 of `docs/frontend.md`.** It has the review's fixes built in.

---

## 1. How to use this file

1. **Create one Stitch project** called "Samvid", in web mode. Keep every screen in this one project so the style stays consistent.
2. **Paste Prompt 0 first** (the design system). Check that the result looks right before going on.
3. **Generate the style sheet next** (Prompt P20). This locks the look for every later screen.
4. **Work through the screens in the order in section 3,** one prompt at a time.
5. **Fix problems with small follow-up prompts** (section 7), not by starting over.
6. **Check each screen against section 2** before you accept it.
7. **Export and hand over** using section 9.

### What Stitch does, and what I do afterwards

| Stitch gives you | I add in code |
|---|---|
| Layout, colour, type, illustration | Real animation, using the notes under each prompt |
| Sample text and numbers | Live data from the backend |
| Screen-to-screen click-through | Real sign-in, routing and permissions |
| How each state looks (loading, empty, error) | Switching between states automatically |
| English, Hindi and right-to-left designs | Real language switching |

So when a prompt says "motion", you're only leaving room for it. Don't spend generations trying to make Stitch animate things.

> Stitch changes often. If a feature named here looks different in your version, or you can't find HTML export, tell me what you see. Some reports put the free limit at about 350 standard generations a month, so check your own limit in the tool.

---

## 2. Rules every screen must pass

Reject or fix any screen that breaks one of these. They come from the project review and aren't a matter of taste.

### Words

| Never show | Show instead | Why |
|---|---|---|
| "You are healthy" | "Being a carrier usually doesn't cause illness" | Inappropriate certainty |
| "Incompatible", "defective", "bad genes" | "Share a genetic finding", "a change in a gene" | Stigma |
| "You should", "we recommend", "best option" | "Your options", "The choice is yours" | Never direct a decision |
| "Your child will have" | "A 1 in 4 chance in each pregnancy" | Risk isn't a diagnosis |
| "Has the condition", as a chance outcome | "Inherits two copies" | Not everyone with two copies is affected the same way |
| "Free screening" | "Screening" | Not confirmed everywhere |
| Cancelled marriages as a good outcome | Understanding, access, informed choice | Banned as a success measure |

### Look

- **No red or green for genetic outcomes.** Use plum, turquoise and sand, always with a pattern and a text label.
- **No logos** of DoH, M42 or any other organisation. It would imply endorsement.
- **No confetti or celebration** on anything to do with results.
- **No sad, sick or frightened people** in illustrations. Modest dress, diverse ages, families from many cultures.
- **Text contrast of at least 4.5:1.** Light accents are for fills and borders. Use the darker text colours in Prompt 0 for words.
- **Touch targets of at least 44 px,** with visible focus rings.

### Honesty

- **Signed-in screens show a "Demo: synthetic data" chip.** Dashboards show a full-width banner.
- **National ID sign-in is labelled "(demo)".**
- **Options are never ranked,** and all cards have the same size and fields.

---

## 3. Order of work

| Order | Prompt | Screen | Priority | Variants to make |
|---|---|---|---|---|
| 1 | Prompt 0 | Design system | Must | |
| 2 | P20 | Style sheet of all components | Must | English, Hindi |
| 3 | P23 | Country and language switch | Must | Desktop |
| 4 | P1 | Home | Must | Desktop, mobile, Hindi |
| 5 | P5 | Sign-in, consent, preferences | Must | Desktop, mobile, Hindi |
| 6 | P6 | My journey dashboard | Must | Desktop, mobile, Hindi |
| 7 | P7, P7b, P7c | My result, and its other states | Must | Desktop, mobile, Hindi |
| 8 | P8, P8b | Couple view, and its other states | Must | Desktop, mobile, Hindi |
| 9 | P9 | Ask Samvid | Must | Desktop, mobile, Hindi |
| 10 | P11 | Partner sharing and couple match | Must | Desktop, mobile |
| 11 | P13 | Consent centre and access log | Must | Desktop, mobile |
| 12 | P14 | Care journey and booking | Must | Desktop, mobile |
| 13 | P15 | Understanding check | Must | Desktop, mobile, Hindi |
| 14 | P16 | Counsellor queue | Must | Desktop |
| 15 | P17 | Case detail | Must | Desktop |
| 16 | P18 | Outcomes dashboard | Must | Desktop |
| 17 | P19 | Equity and privacy dashboard | Must | Desktop |
| 18 | P10 | Options and values | Should | Desktop, mobile |
| 19 | P12, P22 | Invite family, and the invitation page | Should | Desktop, mobile |
| 20 | P21 | Centre finder | Should | Desktop |
| 21 | P2, P3, P4 | Learn pages and privacy promise | Should | Desktop |
| 22 | S1 | Story Mode pitch slides | Should | Desktop |

**If time runs short,** do "Must" screens on desktop first, then Hindi for the main path (P5 to P9). The Arabic version comes last, and only once you've approved it and found a native speaker (section 6).

---

## 4. Prompt 0: the design system

Paste this first. If your Stitch version offers a DESIGN.md or design system panel, this text can go there too.

```text
Create the design system for "Samvid", a web app that helps people around the world understand genetic carrier screening results privately and kindly, and reach qualified genetic counsellors. Samvid is a Sanskrit word for understanding and consent. Users include people anxious about a result, some with low literacy, plus counsellors and health programme managers.

STYLE: "Ceramic Chromatic", LIGHT THEME ONLY. Calm, hopeful, premium, glossy. Never clinical-cold, never alarming. Think glazed ceramic tiles and soft clay, inspired by geometric tile mosaics from many cultures.

DEPTH (three layers):
1. Background: warm porcelain with a faint 8-point star tile pattern at 5% opacity.
2. Surface: white glazed cards with soft clay shadows and a glossy white highlight along the top edge.
3. Floating: chips, buttons and focused cards that sit visibly above the surface with a deeper shadow.

COLOURS:
Backgrounds: porcelain #FBF8F3, glaze white #FFFFFF, sand #F3EDE4, lines #E6DED2.
Text: ink #1F2433, secondary slate #5B6275.
Primary actions: lapis #2F5BEA with white text.
Accent fills (always with ink #1F2433 text on them): turquoise #14A89B, terracotta #E2725B, saffron #F4B740, rose clay #E58FA8, olive #7BAE4E, lilac #B9AEF7. Plum #7A4FD6 takes white text.
Coloured text on light backgrounds uses only these darker versions: turquoise #0E776E, terracotta #A55342, saffron #866523, rose #905A6A, olive #517333, lapis #2F5BEA, plum #7A4FD6.
Risk visuals: "inherits two copies" = plum with diagonal hatching. "Carrier" = turquoise with dots. "Neither" = sand #E9DFCF with an outline. Always a pattern and a text label. Never red or green.

TYPE: Readex Pro for headings, Inter for body, Noto Sans Devanagari for Hindi, IBM Plex Sans Arabic for Arabic. Large and readable, line height 1.6, at most 68 characters per line.

SHAPE: cards 24px radius, inputs 16px with a visible slate border, chips 12px, buttons fully rounded pills. Minimum touch target 44px. Focus ring 3px lapis.

ILLUSTRATION: friendly, rounded, flat-3D clay style. Diverse families from many cultures, modest clothing, hopeful and calm. DNA drawn as colourful glossy ceramic beads. Family trees drawn as connected ceramic tiles. No sick or sad people.

VOICE: warm, private, respectful, non-judgmental. Never tell people what to do. A carrier result is common.

LAYOUT: responsive web, 1440 desktop and 390 mobile. Generous spacing. Thin multicolour mosaic strips as section dividers.

Show this as one style overview page.
```

---

## 5. The screens

Each screen has its route, the data I'll connect, and motion notes for the code stage. Paste only the code block into Stitch.

### P20: Style sheet

**Generate this before any page.** Every later screen should match it.

```text
Using the Samvid design system, create one component sheet showing every UI piece on a single long page, with English examples.

Buttons: primary pill, secondary outlined pill, ghost, pressed clay state, disabled.
Inputs: text field in default, focus and error states, with a lilac-toned helper message instead of red. Toggle, slider with a ceramic thumb, dropdown, checkbox.
Navigation: top bar, tabs, stepper, mobile bottom bar, language switch, reading level toggle (Simple, Standard, Detailed).
Chips: "Private" with a lock, "Demo: synthetic data", "Education", "Your options", "A counsellor can help", "Support", and priority chips P1 to P4.
Cards: clay card, stat tile, list row, modal, mobile bottom sheet, tooltip.
Feedback toasts: success in olive, information in lapis, attention in saffron. No red anywhere.
Risk visuals legend: plum hatched "Inherits two copies", turquoise dotted "Carrier", sand outlined "Neither".
States: empty state with a closed ceramic box, loading with skeleton clay cards and three ceramic beads, error reading "Something went wrong on our side. Your data is safe." with a Try again button and a small reference code, a page-not-found state with one tile missing from a mosaic, an offline banner.
```

### P23: Country and language switch

**Data:** the active country pack and its languages.

```text
Using the Samvid design system and the component sheet, create a component page for the country and language settings.

Show a compact switch for the top bar, opened as a floating clay menu with two countries:
"Abu Dhabi" with the languages English and Arabic, and a chip "Reference: review pending".
"India" with the languages Hindi and English, and a chip "Illustrative: not reviewed".
Below it, show the two countries side by side as "before and after" panels, so it's clear what changes: the options list, the support contacts card, the funding note and the language. Each panel has a small note "Settings change by country. The safety rules never do."
```

### P1: Home

**Route:** `/[locale]` · **Data:** none · **Motion:** helix slowly rotates, cards rise in one after another.

```text
Using the Samvid design system, create the public HOME page.

HERO: porcelain background with a soft lapis, turquoise and saffron glaze at 15%. Left: headline "Understand your genetic results: privately, kindly, in your language." Supporting text: "Samvid explains screening results in plain words, connects you with qualified genetic counsellors, and lets you decide what to share." Buttons: primary "Start privately", secondary "How it works". Trust row: lock "You control sharing", person "Real counsellors for complex results", globe "Built to keep data in your country". Right: a large glossy DNA helix made of colourful ceramic beads, with small tile-shaped family icons around it.

"WHAT SAMVID DOES": four equal glazed cards with icons: "Explains your result", "Shows your options. The choice is yours.", "Connects you to a counsellor", "Protects your family's privacy".

"DID YOU KNOW": three stat tiles with mosaic borders: "Being a carrier usually doesn't cause illness", "1 in 4 is a chance for each pregnancy, not a count of children", "Most people carry a few recessive gene changes".

"HOW IT WORKS": five connected ceramic tiles: Screening, Your result explained, Ask questions, Talk to a counsellor, Your informed choice.

FOOTER: language switch, country switch, privacy promise, accessibility statement, and the small line "A prototype by team Vigyan_Viveka_Vijaya. Not medical advice." No partner or government logos anywhere.
```

### P5: Sign-in, consent and preferences

**Route:** `/[locale]/start` · **Data:** sign-in, service consent, preferences · **Motion:** stepper fills, cards settle.

```text
Using the Samvid design system, create a 4-step onboarding screen with a top stepper: 1 Sign in, 2 Your agreement, 3 Language, 4 Reading level. Centre a large glazed card, with a calm clay illustration of a person reading on a phone at the right on desktop. Show all four steps stacked so each design is visible.

Step 1 "Sign in securely": primary pill "Continue with national ID (demo)", secondary "Sign in with email", and a note "We never share your data without your permission."

Step 2 "Before we start, here's what you're agreeing to": four short clay rows with icons:
"We use your screening result only to explain it to you."
"Our AI explains results. It doesn't diagnose, and it never decides anything for you."
"Nothing goes to a partner or relative unless you choose."
"You can stop at any time."
A checkbox "I understand and agree", a primary "Continue", and a quiet link "I'd rather not see my result for now".

Step 3 "Choose your language": selectable clay tiles for the languages of the chosen country, showing English and Hindi here.

Step 4 "How would you like explanations?": three selectable cards with a sample sentence: Simple (big text and pictures), Standard, Detailed (more science). A toggle "Read explanations aloud". Primary "Continue".
```

### P6: My journey dashboard

**Route:** `/[locale]/app` · **Data:** results summary, journey state, partner status, active shares · **Motion:** cards stagger in, current step pulses 3 times.

```text
Using the Samvid design system, create the signed-in dashboard "My journey".

TOP BAR: Samvid logo, language switch, reading level toggle, profile avatar, chips "Private" and "Demo: synthetic data".
GREETING: "Welcome, Fatima".

Grid of glazed cards at different sizes:
Large card "Your result is ready": the line "You carry a change in one gene. This is common." Button "Understand my result".
Card "Couple view": partner avatar placeholder, status "Waiting for your partner's agreement", button "Manage partner sharing".
Wide card "My care journey": a horizontal stepper of six ceramic tiles: Result released (done), Explained (done), Understood (current, highlighted), Counselling, Next steps, Done. A note "You can pause or decline any step."
Card "Ask Samvid": a chat preview with question chips "What does carrier mean?", "Can we still have children without the condition?", "What are our options?"
Card "Privacy": "2 active shares", a mini list of who viewed your data, link "Manage".
Card "Talk to a counsellor": clay illustration of a counsellor, button "Book a session".
```

### P7: My result

**Route:** `/[locale]/app/result` · **Data:** `GET /v1/me/results` · **Motion:** tiles rise, helper panel fades in.

```text
Using the Samvid design system, create the "My result" page.

HEADER: "Your screening result", date and lab name placeholders, a Listen button, reading level toggle, chip "Demo: synthetic data". A small line "Not ready to read this? You can come back any time."

HERO CARD in a soft turquoise glaze: "You carry one changed copy of the HBB gene." Below: "Being a carrier usually doesn't cause illness. Some carriers notice mild effects, and a counsellor can tell you more."

THREE EQUAL TILES:
"What it means for you": you have one changed copy and one working copy.
"What it could mean for children": this only matters if a partner carries a change in the same gene.
"What we don't know": no test checks every gene.

COLLAPSIBLE CARD "About this gene": a plain-language description, a small ceramic bead DNA picture, and "Read more" with a source label.

LILAC PANEL "Uncertainty, explained": "A test can't check every gene. A negative partner result lowers the chance, but doesn't remove it."

SIDE CARD on desktop: "Risk is not a diagnosis", with a simple icon and two short sentences.

ACTIONS: "See couple view", "Ask a question", "Talk to a counsellor".
```

### P7b: Result state, uncertain finding

```text
Using the same "My result" layout, create the state for an uncertain finding. The hero card, in a soft lilac glaze, says: "We found a change in a gene, and science doesn't yet know what it means." Below: "This is not a positive result. It's called a variant of uncertain significance. We won't show a number, because nobody knows the chance yet. A counsellor will review it with you." Show no percentages or risk visuals anywhere. Primary button: "See when a counsellor can review this".
```

### P7c: Result state, please talk to someone

```text
Using the same "My result" layout, create the state for a finding that needs a counsellor first. The hero card, in a calm lapis tint, says: "Your result is best explained by a counsellor." Below: "This result needs a person to go through it with you. It isn't a diagnosis. We've asked a counsellor to contact you, and you can also book a time." Show no gene details, numbers or risk visuals. Primary button "Book a time". Secondary "Who can see this?" Keep the tone calm, with no warning colours or alert icons.
```

### P8: Couple view

**Route:** `/[locale]/app/couple` · **Data:** `GET /v1/me/risk`, `POST /v1/couples/{id}/match` · **Motion:** icons fill in group by group, tiles flip one by one.

```text
Using the Samvid design system, create the "Couple view", the most important explanation screen.

HEADER: two avatar tiles joined by a ceramic bridge, chips "Couple-only match: only shared findings are shown" and "Demo: synthetic data".

MAIN CARD: "You both carry a change in the same gene (HBB)." Below: "This doesn't mean either of you is ill. Here's what it means for each pregnancy."

VISUAL 1, ICON ARRAY: a 10 by 10 grid of 100 small rounded ceramic figures: 25 plum with diagonal hatching labelled "Inherits two copies", 50 turquoise with dots labelled "Carrier, like the parents", 25 sand with an outline labelled "Inherits neither". Legend with patterns and labels. Caption: "Out of 100 pregnancies like yours, about 25 would inherit two copies."

VISUAL 2, PUNNETT SQUARE: a 2 by 2 grid of glossy tiles with parent tiles along the top and side.

VISUAL 3, "EVERY PREGNANCY": four pregnancy cards with the same small 25, 50, 25 ring. Caption: "Chance has no memory. It's the same each time."

"YOUR OPTIONS": a row of equal chips, with no ranking: Fostering, IVF with embryo testing, More testing, Natural pregnancy, Prenatal testing, Take time to decide. Note: "There's no right or wrong choice." Buttons "Explore options" and "Talk to a counsellor". Small note: "You can ask a counsellor whenever you're ready."
```

### P8b: Couple view, other results

```text
Using the same "Couple view" layout, create two more states as separate frames.

FRAME 1, no shared finding: main card "You and your partner don't share a finding on this panel." Below: "This lowers the chance of a shared inherited condition, but doesn't remove it. No test covers every gene." Show a calm lilac panel "What this does and doesn't mean", and a link "Talk to a counsellor". No celebration, and no icon array.

FRAME 2, can't determine yet: main card "We can't compare your results yet." Below: "This isn't a result. One of you may not have a report on file yet." A status row: "Your report: ready", "Partner's report: waiting". No percentages. Button "What happens next".
```

### P9: Ask Samvid

**Route:** `/[locale]/app/ask` · **Data:** `POST /v1/chat` · **Motion:** three ceramic beads while an answer is checked, bubbles rise in.

```text
Using the Samvid design system, create the "Ask Samvid" chat page. Left column: suggested topics as ceramic chips. Centre: chat. Right column: "Facts used in this answer".

Samvid's bubbles are lilac-white glaze with a ceramic bead avatar. Each answer starts with a label chip, a Listen icon and "Was this clear?" thumbs. Show these exchanges:

User: "What does being a carrier mean?"
Samvid, chip "Education": "A carrier has one changed copy of a gene and one working copy. Most carriers don't have the condition."

User: "If we're both carriers, will our first child have it?"
Samvid, chip "Education": "Not necessarily. In each pregnancy there's a 25% chance the baby inherits two copies. The chance is the same each time." Include a small icon array.

User: "Should we do IVF?"
Samvid, chip "A counsellor can help": "That's a personal decision, and I can't advise on it. A genetic counsellor can talk it through with you." Button "Book a counsellor".

User: "I can't cope with this."
Samvid, chip "Support": "I'm sorry this feels so heavy. You don't have to deal with it alone. Here are people you can talk to now." A card "Support contacts for your country" with placeholder lines, and "A person from our team has been told."

Also show a waiting state: three ceramic beads and "Checking this answer...". Input bar: "Type your question...", mic button, send button, and the note "Please don't include names or ID numbers." Small footer: "Samvid explains. It doesn't diagnose or give medical advice." Right panel tiles: "25% per pregnancy. Source: Mendelian inheritance."
```

### P11: Partner sharing and couple match

**Route:** `/[locale]/app/partner` · **Data:** `/v1/couples`, consent, match · **Motion:** tiles slide into a glass box, and only the overlap glows.

```text
Using the Samvid design system, create the "Partner sharing" page with three step cards.

Step 1 "Invite your partner": a code in large mosaic digits, buttons "Copy" and "Share", status chip "Partner joined".

Step 2 "Choose how to compare": three equal selectable clay cards:
"Keep private": nothing is shared.
"Couple-only match": "Learn only whether you share a finding. Everything else stays private." Inside it, a choice between "Show yes or no" and "Show the shared gene names".
"Share selected details": a checklist of what to share, and a dropdown for how long.
A note: "If you choose differently, the more private choice is used. You can change your mind at any time."
A lilac information panel: "Good to know: if you only have one finding, a 'yes' will tell you which gene is shared."

Step 3 "Run the match": a frosted glass box illustration with tiles from each side and the button "Run match", shown disabled with the text "Waiting for your partner's agreement". Below, three small result previews: "You share a finding. A counsellor can go through it with you.", "You don't share a finding on this panel.", "We can't compare yet."
```

### P13: Consent centre and access log

**Route:** `/[locale]/app/privacy` · **Data:** `/v1/consents`, `/v1/me/access-log` · **Motion:** rows slide out only after the server confirms.

```text
Using the Samvid design system, create the "Privacy and sharing" page. Top banner with a lock: "Your data is encrypted. You decide who sees it."

SECTION "Who can see my information": clay rows with a role avatar, a chip for what they can see (Summary, Full report, Couple match only), an expiry chip, and a "Stop sharing" pill in terracotta outline. Button "Share with someone". Also show the empty state: a closed ceramic box and "Nothing shared".

CONFIRMATION MODAL: "Stop sharing with Ahmed? They'll lose access straight away." Buttons "Cancel" and "Stop sharing". Show a second small state, "Stopping..." with a spinner, and a third, "We couldn't stop sharing just now. Nothing has changed. Please try again."

SECTION "Who viewed my data": a timeline with icons: "You viewed your result, today 10:24", "Counsellor viewed your case, yesterday", "Partner ran the couple-only match, 2 days ago", and one flagged entry "Access attempt refused, 3 days ago". Filter chips: All, Me, Partner, Counsellor. Button "Download my access report".
```

### P14: Care journey and booking

**Route:** `/[locale]/app/journey` · **Data:** journey state, `/v1/booking` · **Motion:** the path draws from left to right, the current tile pulses.

```text
Using the Samvid design system, create the "My care journey" page.

TOP: a large pathway of connected ceramic tiles: Result released, Explained, Understood, Counselling, Confirmatory test (if needed), Specialist referral (if chosen), Done. Finished tiles are olive with a check, the current tile is lapis, and future tiles are sand. Under it: "You can pause or decline any step. That's a valid choice." with a secondary pill "Pause or decline".

BOOKING CARD, left: "Talk to a genetic counsellor": choose In person or Video call, a language dropdown, a calendar with available slots as chips, and "Confirm booking".

CARD, right: "What to expect": three short bullets, a counsellor illustration, and a checklist "Bring your questions".

ACCORDION, bottom: "Next steps after counselling": confirmatory test, specialist clinics, funding information.

Also show a small empty state for places without a service: "We don't have a verified counselling service listed for your area yet. Here's what you can do." with two links. Don't suggest that the AI can replace a counsellor.
```

### P15: Understanding check

**Route:** `/[locale]/app/check` · **Data:** `POST /v1/assessments` · **Motion:** tiles settle into place, gentle answer feedback.

```text
Using the Samvid design system, create a friendly quiz, "Let's check we explained it well", with the subtitle "This tests our explanation, not you." One question per card, big text, and a progress bar of 5 ceramic tiles.

Question: "If both partners carry a change in the same gene, what's the chance for EACH pregnancy?" Four large clay answer buttons with icons: "1 in 4", "Every child", "No chance", "Only the first child".

Show two feedback panels: turquoise "That's right." and lilac "Let's look at it another way." with a small Punnett square. Never use red or a cross.

End screen: a calm row of ceramic tiles settling into place, "Thanks. This helps us explain better." Buttons "Review the explanation" and "Talk to a counsellor". A note: "If this felt confusing, that's on us. A counsellor is happy to help." No confetti, scores or grades.
```

### P16: Counsellor queue

**Route:** `/[locale]/counsellor` · **Data:** `GET /v1/cases` · **Motion:** SLA rings animate, a new case slides in.

```text
Using the Samvid design system in a denser, professional layout, create the counsellor console "My queue". Left sidebar: Queue, Calendar, Cases, Settings.

KPI tiles: "P1 urgent: 2", "P2 high: 7", "Due today: 4", "Stalled: 1".

Two tabs: "Unassigned" and "My cases". The Unassigned tab is open, with a "Claim" button on each row.

TABLE in a glazed card, columns: Priority chip (P1 strong plum, P2 lapis, P3 turquoise, P4 sand), anonymised Case ID, Reason chips ("Shared finding", "Pregnant", "Uncertain finding"), Language, Country, SLA countdown ring, Current step, Action.

Filters: priority, language, reason, SLA. Search by case ID. A drawer on the right previews the selected case, with the note "Opening this case is logged." Chip "Demo: synthetic data".
```

### P17: Case detail

**Route:** `/[locale]/counsellor/case/[id]` · **Data:** `GET /v1/cases/{id}`, pathway, referrals · **Motion:** SLA ring, timeline draws.

```text
Using the Samvid design system in the same professional layout, create the counsellor's case page.

HEADER: case ID, chip P2, SLA ring "41h left", step chip "Counselling booked", buttons "Advance step" and "Add note". A note "Your access is logged."

LEFT: lilac card "Case summary: verify before use", built from structured facts only: risk facts as tiles ("HBB shared: 25%, 50%, 25% per pregnancy"), why this priority, questions asked, understanding score as a ring (3 of 5), and values the client chose to share as chips. Show one empty section: "The client hasn't shared this."

MIDDLE: "Care pathway" vertical timeline with timestamps, and a "Declined by client" example styled neutrally.

RIGHT: "Counsellor notes" private editor. "Referral" card: choose Confirmatory lab or Reproductive genomics clinic, then "Create referral".

BOTTOM: a saffron banner state for opening a case that isn't assigned to you: "This isn't your case. Give a reason to continue. This will be reviewed." with a text box, and buttons "Cancel" and "Continue".
```

### P18: Outcomes dashboard

**Route:** `/[locale]/admin` · **Data:** `GET /v1/analytics/metrics` · **Motion:** charts draw on load, numbers count up.

```text
Using the Samvid design system, create the programme dashboard "Outcomes", colourful but calm.

FULL-WIDTH BANNER: "Synthetic demo data, not real patients."
FILTERS: country, date range, region, language, reading level.
KPI ROW, six clay tiles with sparklines: Understanding gain +31 points, Counselling uptake 92%, Median time to counselling 3.2 days, Referrals completed 87%, Privacy incidents 0, Questions passed to a person 14%.

CHART GRID:
1. Line chart "Understanding before and after": slate dashed, lapis solid.
2. Funnel "Care pathway": Result, Explained, Understood, Counselling, Referral.
3. Bars "Time to counselling by priority", P1 to P4, with a target line.
4. Donut "Types of questions": Education, Options, Counsellor, Support.
5. Stacked bars "Counselling uptake by region".
Each chart has a "View as table" link.

NOTE CARD: "Cancelled marriages are not a success measure. Informed choice is." Small text: "Groups under 10 people are hidden to protect privacy."
```

### P19: Equity and privacy dashboard

**Route:** `/[locale]/admin/equity` · **Data:** `GET /v1/analytics/metrics?stratify=…` · **Motion:** bars grow, heatmap fades in.

```text
Using the Samvid design system, create the "Equity and privacy" dashboard, with the full-width banner "Synthetic demo data, not real patients."

SECTION EQUITY: grouped bars "Understanding gain by language" (English, Arabic, Hindi) and "by reading level" (Simple, Standard, Detailed). Gap badges: olive "Gap 3 points, within target", saffron "Gap 12 points, needs attention". Also bars by gender and age band. Heatmap "Counselling uptake by region and age band" in a turquoise scale, with hidden cells showing "<10" over a hatch pattern.

SECTION PRIVACY: tiles "Access attempts blocked: 128", "Time to stop sharing: 0.4 s", "Exceptional access: 2, reviewed", "Personal details sent to AI: 0". Line chart "Shares created and stopped". Table "Exceptional access reviews": reviewer, reason, date.

SECTION AI SAFETY: bars "Answers blocked by check type": numbers, stigma words, directive wording, diagnosis, reading level. Tile "Answers using approved templates: 18%".
```

### P10: Options and values

**Route:** `/[locale]/app/options` · **Data:** `GET /v1/options`, `/v1/values` · **Motion:** slider thumbs spring, reflection card fades in.

```text
Using the Samvid design system, create "Your options" with two tabs.

TAB "Options": banner "There's no right or wrong choice." A grid of six equal clay cards, the same size and fields, in alphabetical order, with no "recommended" badge: Fostering, IVF with embryo testing, More testing, Natural pregnancy, Prenatal testing, Take time to decide. Each has an illustration, "What it involves", "Things to think about", and "Learn more". IVF has a small note "Funding may be available. Ask your counsellor." Small line: "These options are for your country and have not yet been clinically reviewed."

TAB "What matters to me": five clay sliders with ceramic thumbs: "Having a biological child", "Avoiding medical procedures", "My family's views", "My faith", "Certainty about the baby's health". Below, a card "Here's what you told us matters most", which reflects the answers back with no score and no suggestion. Buttons "Save privately" and "Share with my counsellor (optional)".
```

### P12: Invite family privately

**Route:** `/[locale]/app/family` · **Data:** `POST /v1/invitations` · **Motion:** tiles connect softly.

```text
Using the Samvid design system, create "Let family know privately". Intro: "Relatives may share the same gene changes. You can let them know screening exists, without saying who you are or what you carry."

LEFT, form card: relationship chips (Parent, Sibling, Cousin, Aunt or uncle, Child, Other). A toggle "Include my name", off by default. Buttons "Create private link" and "Copy link". Notes: "Links expire in 30 days and work once." and "Up to 5 a day."

RIGHT, preview card, "What they'll see": "A family member wanted you to know about genetic screening." Then a short explanation, with no name and no result.

A family tree of ceramic tiles with soft lines, purely as decoration, with no real relatives. A small note: "It's fine not to send this. It's your choice."
```

### P22: Invitation page

**Route:** `/[locale]/i/[token]` · **Data:** invitation view and redeem, public.

```text
Using the Samvid design system, create a calm public page for someone who received a private link. Heading: "A family member wanted you to know about genetic screening." Three short clay cards: "What screening is", "It's your choice", "How your privacy is protected". Primary pill "Continue" and a quiet link "Not now". No names, no results, and no suggestion that anyone is ill.

Also show the state for an old link: "This link isn't available any more. You can still read about screening." with a link, and nothing that says why.
```

### P21: Centre finder

**Route:** `/[locale]/centres` · **Data:** `GET /v1/centres`, public.

```text
Using the Samvid design system, create "Find screening and counselling". A search bar and region chips at the top, then a list of clay cards: centre name, services, contact, and a small line "Source and date checked". Show that no sign-in is needed. Also show the empty state: "We don't have a verified list for this country yet. Here's who to ask." with a closed ceramic box.
```

### P2: How inheritance works

**Route:** `/[locale]/learn/inheritance` · **Motion:** tiles flip chapter by chapter, with a sticky progress rail.

```text
Using the Samvid design system, create "How inheritance works": a vertical scroll story of five full-width glazed panels, with an illustration on one side and simple text on the other, and a sticky rail of five ceramic dots.

1 "Genes come in pairs": two clay figures, each holding two ceramic gene tiles.
2 "What is a carrier?": one tile has a plum dot pattern. "A carrier has one changed copy and one working copy. Carriers usually don't have the condition."
3 "When both parents carry the same change": a 2 by 2 square of glossy tiles labelled 25%, 50%, 25%.
4 "Chance has no memory": four pregnancy cards with the same square, captioned "The same chance each time."
5 "Why family matters": a family tree of tiles, captioned "Results are shared only if you choose."
End card: "See what your own result means" and "Talk to a counsellor". Reading level toggle at the top.
```

### P3: Related couples, facts and myths

**Route:** `/[locale]/learn/cousin-marriage` · **Motion:** cards flip on tap.

```text
Using the Samvid design system, create a respectful page, "Marrying a relative: facts, not myths". Header illustration: a warm family gathering in clay style. Intro: "Marrying a relative is a long-standing tradition in many communities around the world. Genetics can help families make informed choices, whatever they decide."

"MYTH OR FACT": six flip cards, showing the answer side in turquoise or lilac:
"Marrying a cousin always causes illness": Myth. Most children of cousins don't have a genetic condition.
"Relatives are more likely to carry the same change": Fact.
"A negative test means no chance at all": Myth. It lowers the chance, but doesn't remove it.
"Carriers are ill": Myth. Carriers usually don't have the condition.
"Screening can support any choice": Fact.
"My result must be shared with my family": Myth. You decide.

A placeholder card "How much does the chance change?" with the text "Figures appear here after clinical review." Do not show any numbers.
Three tiles: "Find screening", "Talk to a counsellor", "Ask a question".
```

### P4: Privacy promise

**Route:** `/[locale]/privacy` · **Motion:** tiles slide into the glass box, and only the match glows.

```text
Using the Samvid design system, create "Our privacy promise". Hero: a large glossy ceramic padlock with a family tree pattern. Headline: "Your genetic information belongs to you."

"OUR PROMISES": six clay cards: "You decide who sees what", "Couple-only match shows only what's shared", "Let relatives know without saying who you are", "Stop sharing at any time", "See who viewed your data", "The AI never sees your name or ID".

"HOW COUPLE-ONLY MATCH WORKS": three steps: tiles from two people enter a frosted glass box, and only the overlapping tile comes out, labelled "Shared finding". Below it, plainly: "Our secure server does this comparison. If you only have one finding, a 'yes' tells you which one."

"WHERE YOUR DATA LIVES": a small globe with a lock pin: "Designed so genetic data stays in your country." An accordion of five questions.
```

### S1: Story Mode pitch slides

**Route:** `/[locale]/story` · **Motion:** a different animation per slide, in the table in `docs/frontend.md` §6.

```text
Using the Samvid design system, design a 10-slide, full-screen presentation at 16:9, with a mosaic tile progress bar at the bottom. Big type, one idea per slide. No logos.

1 "Samvid: understanding inherited risk, privately and kindly." A ceramic bead helix. "Team Vigyan_Viveka_Vijaya. Future Health Challenge 2026, Fertility Challenge 03."
2 "A global need": stat tiles "About 1 in 10 people worldwide (2009 estimate)", "Screening is growing", "Counsellors are scarce".
3 "The gap comes after the lab": a broken path of tiles: Test, Understanding, Counselling, Choice, Family privacy.
4 "The human question": a person reading a result, with a bubble "Am I ill? Who will know?"
5 "Five pillars" as tall ceramic columns: Explain, Choose freely, Human counsellors, Private sharing, Measured outcomes.
6 "Numbers from code, words from AI, decisions from people": three tile layers inside a privacy shield.
7 "Couple-only match": tiles entering a glass box, and only the shared one emerging.
8 "Global by design": one core, with Abu Dhabi and India packs. "Settings change. Safety rules don't."
9 "Measured honestly": metric tiles, labelled "Synthetic demo data", and the line "We don't count cancelled marriages."
10 "Next": Pilot, Partner review, More countries. "Built for the world, proven first in Abu Dhabi."
```

---

## 6. Language and mobile variants

Run these while the finished desktop screen is selected. Do mobile and Hindi on the "Must" screens first.

### Mobile

```text
Create the 390px mobile version of this screen. Use a single column, a bottom navigation bar, and bottom sheets instead of side panels. Keep the same content, colours and components. Keep touch targets at 44px or more.
```

### Hindi

```text
Create the Hindi version of this screen, left to right. Translate all visible text into simple, respectful everyday Hindi in Devanagari, using Noto Sans Devanagari for body text. Keep English gene names such as HBB. Use these terms: carrier = वाहक, genetic counsellor = आनुवंशिक परामर्शदाता, consent = सहमति, privacy = निजता, risk = जोखिम. "Risk is not a diagnosis" = "जोखिम का मतलब बीमारी नहीं है". Keep the same layout and colours. Avoid words that suggest blame or that something is wrong with a person.
```

**Check:** a Hindi speaker must review every Hindi screen. This glossary is my starting point, and nobody has reviewed it.

### Arabic, right to left

**Wait for two things first:** your approval to add Arabic, and a native speaker to check it. Under your project rule I haven't written any Arabic here, so Stitch would translate it, and machine translation of medical wording can be wrong.

```text
Create the Arabic version of this screen. Mirror the layout right to left, translate all visible text into simple, respectful Arabic, and use IBM Plex Sans Arabic for body text. Keep numerals in Western digits and keep gene names such as HBB in English. Flip arrows and directional icons. Don't mirror charts' numeric axes. Avoid words that suggest blame, defect or incompatibility.
```

---

## 7. Fix-up prompts

Change one or two things at a time, and reuse these as needed.

| Problem | Paste this |
|---|---|
| Look has drifted | `Match the component sheet exactly: same cards, chips, buttons, shadows and colours.` |
| Not glossy enough | `Make the cards feel more like glazed ceramic: a brighter highlight along the top edge, a softer clay shadow, and more depth between background, surface and floating chips.` |
| Too flat | `Add more depth. Lift the main card above the others with a deeper shadow, and make chips float above their cards.` |
| Hard to read | `Make all coloured text use the darker text colours from the design system. Body text should be at least 16px.` |
| Colours too dull | `Add more mosaic colour through tile accents, icon backgrounds and section dividers. Keep text ink and backgrounds light.` |
| Red appeared | `Remove all red and green. Use plum, turquoise, sand and saffron from the design system.` |
| Too crowded | `Increase the space between cards to 32px, and show less text in each card.` |
| Dark mode appeared | `Keep this light theme only.` |
| Wrong language | `Keep all text in English on this version.` |
| Directive wording | `Rewrite the text so it describes options without telling the person what to do.` |
| Too clinical | `Make this warmer: rounder shapes, a friendly clay illustration, and calmer wording.` |
| Prototype links | `Link the "Understand my result" button on this screen to the My result screen.` |

---

## 8. Motion I'll add in code

You don't need to do anything for this. It's here so you can see what's planned, and so you can leave room for it.

| Name | Where | What it does |
|---|---|---|
| Rise in | Cards, sections | Fades in and lifts 16 px, one after another |
| Count up | Stats, KPIs | Numbers count up when scrolled into view |
| Icon fill | Icon array | Fills group by group, in about a second |
| Tile flip | Punnett square, myth cards | 3D flip of a ceramic tile |
| Path draw | Care journey, diagrams | Line draws itself |
| Current step | Steppers | Soft pulse, 3 times, then rests |
| Bead wait | Chat | Three beads bounce while an answer is checked |
| Glass match | Couple match | Tiles slide in, and only the shared one glows and exits |
| Helix | Home | Slow 3D rotation, paused when off screen |
| Clay press | Buttons | Presses in slightly with a soft spring |
| Page change | All routes | Quick fade and slide |

**People who've asked for less motion** get simple fades, automatically. Nothing flashes, and nothing loops forever.

---

## 9. Export and hand-over

1. **Export each screen** as HTML with Tailwind if your version offers it. If it doesn't, tell me which export options you see.
2. **Save them** using this structure:

```text
frontend/design-export/
  p01-home/desktop.html
  p01-home/mobile.html
  p01-home/hindi.html
  p08-couple/desktop.html
  ...
```

3. **Also export** the component sheet (P20) and your DESIGN.md, if Stitch produced one.
4. **Tell me** when the "Must" screens are in that folder, and I'll start building from them.

You can send screens in batches. Don't wait for all of them.

### Final check per screen

- [ ] Passes every rule in section 2
- [ ] Matches the component sheet
- [ ] All text is real, not lorem ipsum
- [ ] Empty, loading or error state exists if the prompt asked for one
- [ ] Hindi checked by a Hindi speaker, where a Hindi version exists
- [ ] A person outside the team understands it in under a minute

---

## 10. Screen and backend map

Today, only `/v1/health` and `/v1/ready` exist. The other endpoints arrive in the phases shown, and I'll connect the screens as they do.

| Screen | Route | Endpoints | Phase |
|---|---|---|---|
| P1 Home | `/[locale]` | None | 5.5 |
| P2, P3 Learn | `/[locale]/learn/…` | None | 5.5 |
| P4 Privacy promise | `/[locale]/privacy` | None | 5.5 |
| P5 Sign-in | `/[locale]/start` | Sign-in, `PATCH /v1/me` | 2.3, 3.2 |
| P6 Dashboard | `/[locale]/app` | `/v1/me/results`, journey | 2.5, 5.1 |
| P7 My result | `/[locale]/app/result` | `/v1/me/results` | 2.5 |
| P8 Couple view | `/[locale]/app/couple` | `/v1/me/risk`, `/v1/couples/{id}/match` | 2.5, 3.3 |
| P9 Ask Samvid | `/[locale]/app/ask` | `/v1/chat` | 4.3 |
| P10 Options | `/[locale]/app/options` | `/v1/options`, `/v1/values` | 4.4 |
| P11 Partner | `/[locale]/app/partner` | `/v1/couples/*` | 3.3 |
| P12 Family | `/[locale]/app/family` | `/v1/invitations` | 3.4 |
| P13 Privacy | `/[locale]/app/privacy` | `/v1/consents`, `/v1/me/access-log` | 3.2, 3.5 |
| P14 Journey | `/[locale]/app/journey` | Journey, `/v1/booking` | 5.1, 5.2 |
| P15 Check | `/[locale]/app/check` | `/v1/assessments` | 5.3 |
| P16 Queue | `/[locale]/counsellor` | `/v1/cases` | 4.5 |
| P17 Case | `/[locale]/counsellor/case/[id]` | `/v1/cases/{id}`, pathway, referrals | 4.5, 5.2 |
| P18, P19 Dashboards | `/[locale]/admin…` | `/v1/analytics/metrics` | 5.4 |
| P21 Centres | `/[locale]/centres` | `/v1/centres` | 5.2 |
| P22 Invitation | `/[locale]/i/[token]` | `/v1/invitations/{token}` | 3.4 |
| S1 Story | `/[locale]/story` | None | 6.5 |
