# Components

| Folder | What's in it |
|---|---|
| `ui/` | Cards, chips, buttons and the stepper, in the Ceramic Chromatic style |
| `layout/` | Page shell, language switch, sign-out, and the "not built yet" placeholder |
| `risk/` | Fact lists, icon arrays, Punnett squares and the X-linked diagram. Every number comes from the API |
| `forms/` | Everything a person fills in or presses |
| `motion/` | Entrances, drawing lines, the finite pulse, flip tiles and page transitions. Each is visible without script and stops for reduced motion. Hooks are in `lib/motion.ts` |
| `charts/` | The chart kit: bars, donut, line, heatmap and the time-left ring, each with a summary sentence and a table. Charts show counts of things, never a person's genetic result |

**Motion rules** (docs/frontend.md section 2.5): only the home page's slow background, and indicators shown while something loads, may loop. Everything else plays once, or three times for the current step. A browser test walks every element on the main pages and fails on any other endless animation.

**Stubs:** the six Phase 5.4 dashboard charts in `charts/` (`BoundaryDonut`, `ComprehensionLine`, `EquityBars`, `PathwayFunnel`, `RegionAgeHeatmap`, `TimeToCounselling`). Each names the kit component it will build on once the analytics endpoint exists.
