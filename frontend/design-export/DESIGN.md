<!-- From the Stitch export ("Ceramic Chromatic"), unchanged. tailwind.config.ts and app/globals.css implement it. -->
---
name: Ceramic Chromatic
colors:
  surface: '#faf8ff'
  surface-dim: '#d5d9ee'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e3e7fc'
  surface-container-highest: '#dee2f6'
  on-surface: '#161b2a'
  on-surface-variant: '#434655'
  inverse-surface: '#2b303f'
  inverse-on-surface: '#eef0ff'
  outline: '#747686'
  outline-variant: '#c4c5d8'
  surface-tint: '#1f4fdf'
  primary: '#0040cf'
  on-primary: '#ffffff'
  primary-container: '#2f5bea'
  on-primary-container: '#e5e8ff'
  inverse-primary: '#b7c4ff'
  secondary: '#006a62'
  on-secondary: '#ffffff'
  secondary-container: '#79f4e5'
  on-secondary-container: '#006f66'
  tertiary: '#5f31ba'
  on-tertiary: '#ffffff'
  tertiary-container: '#784dd4'
  on-tertiary-container: '#f0e5ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001452'
  on-primary-fixed-variant: '#0038b7'
  secondary-fixed: '#7df6e7'
  secondary-fixed-dim: '#5edacb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#eaddff'
  tertiary-fixed-dim: '#d1bcff'
  on-tertiary-fixed: '#24005b'
  on-tertiary-fixed-variant: '#5523af'
  background: '#faf8ff'
  on-background: '#161b2a'
  surface-variant: '#dee2f6'
typography:
  display:
    fontFamily: Space Grotesk
    fontSize: 3rem
    fontWeight: '600'
    lineHeight: '1.2'
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 2rem
    fontWeight: '600'
    lineHeight: '1.3'
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: '1.3'
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 1.5rem
    fontWeight: '500'
    lineHeight: '1.35'
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 1.25rem
    fontWeight: '500'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: '1.4'
  label-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: '1.4'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2.5rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system expresses the "Ceramic Chromatic" aesthetic—a bespoke atmosphere inspired by artisanal glazed tiles, hand-pressed terracotta, and geometric mosaic craft. Designed for sensitive, private genetic carrier screening and counseling, the interface avoids the cold sterility of traditional clinical diagnostics in favor of warm porcelain surfaces, luminous top-edge glazes, and intentional chromatic accents.

### Personality & Tone
- **Warm & Non-Directive:** Information is presented clearly, non-judgmentally, and gently, empowering informed personal choices without alarmism.
- **Calm & Hopeful:** Tactile warmth grounded in sand and porcelain balances clinical precision with emotional reassurance.
- **Artisanal Rigor:** Distinct geometric silhouettes evoke handcrafted ceramic mosaics rather than impersonal software widgets.
- **Strict Clinical Boundaries:** No celebratory visual tropes (e.g., confetti) and zero reliance on traditional binary green/red health indicators.

## Colors

The palette is strictly tuned for light mode, evoking layered porcelain, unglazed clay, and colored mineral glazes. 

### Foundation Surfaces
- **Canvas (Porcelain):** `#FBF8F3` — Ambient page foundation featuring a subtle 8-point geometric star tile pattern.
- **Surface (Glaze White):** `#FFFFFF` — Primary content cards and layered plates.
- **Subtle Surface (Sand):** `#F3EDE4` — Inset areas, secondary well containers, and muted backgrounds.
- **Structural Line:** `#E6DED2` — Crisp division borders, soft structural frames, and mosaic grouting.

### Text & Hierarchies
- **Ink Primary:** `#1F2433` — High-contrast primary reading text and icons.
- **Slate Secondary:** `#5B6275` — Supporting text, metadata, form labels, and subtle outlines.

### Primary Interaction
- **Lapis:** `#2F5BEA` — The definitive call-to-action hue, reserved for focused navigational pathways, verified actions, and active selection rings. Displays exclusively with white text.

### Chromatic Accent System
Accents denote genetic statuses, counselor specialties, and condition categorization.
- **Fill Tokens (Paired with Ink `#1F2433` text):**
  - Turquoise: `#14A89B`
  - Terracotta: `#E2725B`
  - Saffron: `#F4B740`
  - Rose Clay: `#E58FA8`
  - Olive: `#7BAE4E`
  - Lilac: `#B9AEF7`
- **Plum (Deep Accent):** `#7A4FD6` — Always paired with white text `#FFFFFF`.
- **Text & Stroke Contrast Tokens (Used over light/tinted backgrounds):**
  - Deep Turquoise: `#0E776E`
  - Deep Terracotta: `#A55342`
  - Deep Saffron: `#866523`
  - Deep Rose: `#905A6A`
  - Deep Olive: `#517333`
  - Deep Lapis: `#2F5BEA`
  - Deep Plum: `#7A4FD6`

### Genetic Outcome Coding (Strictly Non-Red/Green)
To eliminate panic, stigma, and false reassurance, genetic carrier statuses strictly avoid green and red:
- **Inherits Two Copies:** Plum (`#7A4FD6`) with a 45° diagonal tactile hatching texture.
- **Carrier (One Copy):** Turquoise (`#14A89B`) with a subtle stippled dot matrix texture.
- **Neither Copy Detected:** Sand (`#E9DFCF`) container with a solid `#E6DED2` structural outline.

## Typography

The type scale pairs geometric presence with utilitarian reading comfort:

- **Headlines:** Display and section headings leverage clean geometric proportions with architectural discipline.
- **Body & Controls:** Body copy uses Inter, calibrated to a relaxed `1.6` line height for extended clinical readability, reduced cognitive fatigue, and calm scannability.
- **Multilingual Support:** For Hindi localization, font fallback cascades seamlessly to Noto Sans Devanagari, maintaining identical vertical metrics and clear ascender/descender breathing space.

## Layout & Spacing

Layouts conform to a responsive 12-column grid system centered within a maximum container width of `1200px`.

### Grid Behavior
- **Desktop (1024px+):** 12 columns, `margin: 2.5rem`, `gutter: 1.5rem`.
- **Tablet (768px - 1023px):** 8 columns, `margin: 1.5rem`, `gutter: 1.25rem`.
- **Mobile (< 768px):** 4 columns, `margin-mobile: 1rem`, `gutter-mobile: 1rem`.

### Composition Principles
- Content breathes through generous vertical pacing (`space-xl` between modular diagnostic groups).
- Critical medical counseling results are housed within focused single- or double-column layouts to avoid visual clutter and overwhelming data density.

## Elevation & Depth

Elevation in this design system mimics physical glazed ceramic tiles set into soft architectural clay:

### Layer 1: Ambient Canvas
- Porcelain background (`#FBF8F3`) enriched with an SVG tile mask depicting an 8-point geometric star pattern at `3%` opacity in `#1F2433`.

### Layer 2: Ceramic Glazed Surfaces (Default Cards)
- Background: Glaze White (`#FFFFFF`).
- Border: `1px solid #E6DED2`.
- Top-Edge Ceramic Highlight: An inner specular stroke created via `box-shadow: inset 0 1.5px 0 0 rgba(255, 255, 255, 0.95)`.
- Base Clay Shadow: Dual diffused drop shadow: `0 4px 16px -2px rgba(91, 98, 117, 0.06), 0 1px 3px 0 rgba(91, 98, 117, 0.04)`.

### Layer 3: Floating Glazes (Interactive Elements, Chips, & Active Cards)
- Applied to buttons, active interactive chips, and counseling session booking cards.
- Glaze Highlight: `box-shadow: inset 0 1.5px 0 0 rgba(255, 255, 255, 1)`.
- Floating Depth: `0 10px 24px -4px rgba(31, 36, 51, 0.08), 0 2px 6px -1px rgba(31, 36, 51, 0.04)`.

## Shapes

Shapes blend structural architectural discipline with organic smoothness:

- **Plates & Cards:** `24px` corner radius, evoking rounded ceramic tiles.
- **Form Inputs & Selectors:** `16px` corner radius, framed by a soft slate stroke (`#5B6275` at 40% opacity).
- **Metadata Chips & Badges:** `12px` corner radius, acting as small modular tesserae.
- **Buttons & Core Interactive Targets:** Fully rounded pill shapes (`9999px`) to invite gentle, approachable touch.

## Components

### Buttons
- **Primary:** Pill shape, minimum touch target `48px`, background Lapis `#2F5BEA`, text `#FFFFFF`, top glaze highlight `inset 0 1px 0 rgba(255, 255, 255, 0.3)`. Focus states display an outer `3px solid #2F5BEA` ring offset by `2px`.
- **Secondary:** Pill shape, glaze white `#FFFFFF` surface, `1px solid #E6DED2`, text Ink `#1F2433`. Hover transitions to background Sand `#F3EDE4`.
- **Tertiary / Ghost:** Pill shape, transparent surface, text Secondary Slate `#5B6275`.

### Chips & Badges
- Corner radius `12px`, padding `6px 12px`, minimum height `32px`.
- **Status Badges:** Paired with thematic color fills and high-contrast text tokens.
- **Synthetic Data Chips:** Displayed with an unglazed Sand `#F3EDE4` fill, Slate `#5B6275` text, and a micro-label indicating "Sample Result" or "Simulated Profile".

### Cards
- Radius `24px`, background Glaze White `#FFFFFF`, border `1px solid #E6DED2`. Includes the top-edge specular highlight (`inset 0 1.5px 0 0 rgba(255,255,255,0.95)`) and base clay ambient shadow.
- Inset cards use background Sand `#F3EDE4` with no drop shadow and border radius `16px`.

### Inputs & Form Controls
- Height `48px`, radius `16px`, background Glaze White `#FFFFFF`, border `1px solid #5B6275`.
- Active focus invokes a `3px` solid Lapis `#2F5BEA` ring with `2px` white offset.
- Checkboxes and radio buttons enforce a minimum hit target of `44px x 44px` with a visual icon size of `20px`. Selected state fills with Lapis `#2F5BEA`.

### Diagnostic Carrier Status Modules
- Structural container with `24px` radius.
- Visual status graphic anchors the card:
  - **Inherits Two Copies:** Plum accent with diagonal SVG hatching (repeating lines angled at 45°).
  - **Carrier:** Turquoise accent with an SVG dot grid overlay (3px interval).
  - **Neither Detected:** Sand `#E9DFCF` filled outline with structural border `#E6DED2`.
- Text utilizes non-alarmist, explanatory headers: "Carrier Identification", "Two Alterations Identified", or "No Targeted Alterations Detected".

### Genetic Counselor Profiles
- Horizontal glazed tile layout.
- Circular portrait frame with a `2px` unglazed Sand border.
- Integrated chips highlighting language proficiencies (e.g., English, Hindi) and clinical specializations.
- Direct booking action via primary pill button.