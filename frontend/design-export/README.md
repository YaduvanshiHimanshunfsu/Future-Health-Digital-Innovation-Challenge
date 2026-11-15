# Design export

The team designed the screens in Google Stitch. The export arrived as `stitch_samvid_story_mode_deck.zip`: 56 HTML screens with screenshots, and a design system file.

**What's kept here:** `DESIGN.md`, the design system, unchanged. Its colours, type, radii and shadows are in `tailwind.config.ts`, and its components are in `app/globals.css` and `components/`.

**What isn't kept, and why:** the screens' HTML and screenshots. They're the visual reference for the build, but their sample text breaks the project's rules in ways that mustn't end up in the repo:
- Privacy claims the product doesn't make, such as "zero-knowledge proof inside browser memory" and "your data stays on your device". The couple check runs on our server.
- Certifications we don't hold (HIPAA, ISO 27001), invented study results ("p < 0.001"), and a made-up clinical sign-off.
- Names of real hospitals and health authorities, which would suggest an endorsement we don't have.
- "You are healthy and safe", "free screening", pressure on a partner ("Send reminder", "active 8 mins ago"), and the partner's exact variant shown to the other partner.
- Arabic and Urdu script. Since 15 Nov 2026 the user has approved Arabic interface text in `messages/ar.json` only, drafted and awaiting a native speaker's review; the design's own Arabic samples are still not used.

So the layouts follow Stitch, and every word comes from `messages/`, where `tests/unit/copy.test.mjs` enforces the wording rules.

## Screens and where they went

| Stitch screen | Built as | Notes |
|---|---|---|
| P1 Home (desktop, mobile, Hindi) | `/[locale]` | Wording rewritten. A "what we can and can't promise" panel replaces the on-device claims |
| P2, P3 Learn | `/[locale]/learn/...` | Textbook visuals use the same components as real results |
| P4 Privacy promise | `/[locale]/privacy` | Only promises the code enforces, plus its limits |
| P5 Sign-in and consent | `/[locale]/start` | Country choice, real sign-in, service consent, detail level |
| P6 My journey | `/[locale]/app` | Steps come from real data: report, partner, care |
| P7 My result, P7b, P7c | `/[locale]/app/result` | Built from scratch for no report, nothing found, uncertain, chosen not to know, and "a counsellor will contact you" |
| P8 Couple view | `/[locale]/app/couple` | Shows only what the API returns. No partner variant, no molecular detail |
| P11 Partner sharing | `/[locale]/app/partner` | Invite, join, choose what a result may show, accept the disclosure, run. "Send reminder" and the partner's activity are gone |
| P13 Consent centre and access log | `/[locale]/app/privacy` | Not in the export, so built in the same style |
| P12, P22 Family invitation | `/[locale]/app/family`, `/[locale]/i/[token]` | No cost claims. Names nobody unless the sender chooses |
| P16, P17 Counsellor | `/[locale]/counsellor`, `.../case/[id]` | Opening a case and emergency access. The queue arrives in 4.5 |
| P18, P19 Dashboards | `/[locale]/admin` | Waits for real metrics in 5.4, rather than showing invented ones |
| P9, P10, P14, P15, P21, S1 | Placeholders saying which sub-phase builds them | Nothing simulated |
| P20 Component sheet, P23 Country switch | `components/`, `/[locale]/start` | |
