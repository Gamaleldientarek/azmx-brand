---
name: azmx-brand
description: "Apply the official AZMX brand identity to any deliverable. Use whenever work involves AZMX branding, AZMX presentations, proposals, emails, newsletters, reports, social graphics, web pages, documents, printed A4 documents, fillable PDF forms, or copywriting in the AZMX voice, or when the user mentions AZMX colors, the chevron, Dark Navy, Electric blue, thmanyah serif, or Azm X fonts. Also covers the unified communication strategy: communication planning, content plans and editorial calendars, social posts and captions for LinkedIn, Instagram or Twitter/X, blog articles, messaging and positioning, audience personas and segments, B2G/B2B/B2C motions, creative briefs, tone of voice, English-to-Arabic localization, and the AZM X brands Colab, Majarah, Clix and Anatomi. Provides the full color palette, typography rules, logo files, web fonts, the email design system, the Figma-to-fillable-PDF form pipeline, the voice and tone guide, and the channel, governance and content-prompt references."
---

# AZMX Brand Skill

## Figma single-file resource handling

This Markdown file is the complete custom-skill upload for the Figma agent. It embeds the two advanced design guides; no supporting folders are included in the upload. Installing it adds instructions, not fonts, images, Figma variables, components, or a library connection.

The original brand rules below refer to resources that “ship with the skill.” In this Figma edition, those resources live in the [AZMX repository](https://github.com/Gamaleldientarek/azmx-brand), not in an accessible local skill folder. Read the linked reference when its workflow requires it. If web or connector access cannot retrieve it, ask for the specific missing reference instead of reconstructing it.

- **Brand imagery:** use the [image library rules](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/image-library.md), [concept index](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/image-index.md), and [gallery](https://gamaleldientarek.github.io/azmx-brand/). Select by meaning and the approved palette. Preserve the original selection and confirmation rules below. Use a verified direct image URL from the index when supported; otherwise request that selected image as an attachment. Do not treat the gallery link as an image fill or assume that linking a repository imports its images.
- **Resource paths:** interpret `references/…` as files under the repository’s `main` branch. Interpret `assets/…` and `scripts/…` the same way; for individual downloadable assets the base is `https://raw.githubusercontent.com/Gamaleldientarek/azmx-brand/main/`. Verify the actual file exists before use; folder paths are not downloadable files.
- **Figma resources:** inspect enabled libraries and available fonts, variables, and components separately. A token export documents a system but does not establish live bindings. Never claim to have imported or enabled a library merely by reading this skill.
- **Scripts:** linked scripts are reference resources. Run them only in an available, supported execution environment with the needed files and authorization. If the Figma agent cannot execute them, explain the limitation instead of simulating completion.
- **Embedded guides:** references to `figma-advanced-design.md` and `figma-presentation-design.md` mean the full embedded sections below. Do not try to fetch these two newly added guides from the repository; they have not been published there.


AZMX is a leading Saudi digital consultancy, and the parent house for four brands: Colab, Majarah, Clix, and Anatomi. Its philosophy line is **"Designing the Future of Experience."** This skill encodes its official brand and communication system so every deliverable comes out on-brand without re-briefing. Never describe AZMX as a studio, an agency, or a boutique.

One-line ethos: deep navy, electric blue, generous white space, serif personality, the chevron as the only recurring graphic device. **Restraint is the luxury.**

For the complete handbook (component specs, slide archetypes, Figma implementation), read [references/design-system.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/design-system.md). For every color tone, read [references/colors.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/colors.md). **Before touching a Figma file, read [references/design-tokens-usage.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/design-tokens-usage.md)** — the seven-step guide to using the token system, including which tier to bind to and why the signature colour is not the text colour. For the exact live variables (all 550 across five collections: six palettes, Light/Dark, component and canvas tokens), read [references/figma-tokens.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/figma-tokens.md). For any HTML email or newsletter, read [references/email-design-system.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/email-design-system.md) and start from `assets/templates/email-starter-skeleton.html`. For any written copy, follow [references/voice-and-tone.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/voice-and-tone.md). When a deliverable needs imagery, pick from the 242 brand images catalogued in [references/image-library.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/image-library.md) (selection and colour-pairing rules) and [references/image-index.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/image-index.md) (every file with its three concept tags, dominant colour, safe text colour, and direct download link). To convert an image to another colour theme, use the tested prompts in [references/recolor-prompts.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/recolor-prompts.md). For icons, read [references/icons.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/icons.md). For any printed A4 document or fillable PDF form, follow [references/pdf-forms.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/pdf-forms.md) — it documents the validated Figma → export → pdf-lib pipeline and the `scripts/build-pdf-form.mjs` tool that stamps form fields at exact coordinates. To turn a deck built as Figma frames into a keyboard-driven presentation, read [references/presentation-transitions.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/presentation-transitions.md) and run `scripts/figma-slide-transitions.js`.

For any communication planning, channel ownership, or governance question, read [references/communication-strategy.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/communication-strategy.md). Before writing a single line of copy, load [references/audiences-and-messaging.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/audiences-and-messaging.md) for the audience and its verbatim core message, then [references/voice-and-tone.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/voice-and-tone.md) for AZM X's voice or [references/sub-brand-voices.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/sub-brand-voices.md) for Colab, Majarah, Clix, and Anatomi. For cadence, weekly themes, optimal posting times, and the nineteen internal initiatives, read [references/editorial-calendar.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/editorial-calendar.md). For ready-made article, social, and English-to-Arabic prompts, use [references/content-prompts.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/content-prompts.md).

Images are dark surfaces. Every section except White measures below 0.18 luminance, so text over them follows the Navy row of the text-colour table: White title, Blue 100 body, Light Blue eyebrow. Never Electric for text on an image; Electric appears over imagery only as a chevron tick or a single active rule. The White section is the one exception, taking Navy text with Electric accents.


## Advanced Figma design workflow

For AZMX work in **Figma Design or Figma Slides**, also read the embedded **Advanced Figma design practice** section below. For presentations, read the embedded **Presentation direction and Figma Slides** section below. These references add construction, editorial judgment, and verification to the existing brand system; they do not authorize new brand values, assets, publication, or changes to shared libraries.

Work as an editorial designer and a design-system builder together: make the argument clear, make the composition distinctive within AZMX, and make the result easy to edit. More layers, variables, or components are not measures of design quality.

1. **Inspect before building.** Identify the audience, decision, presentation versus reading use, final format, and existing file structure. Inspect available libraries, variables, styles, fonts, and tool capabilities. Use the existing token references; never infer that a named token is already available or bound.
2. **Choose the right structure.** Use fixed slide canvases with flexible internal layouts. Use Auto Layout for content-dependent relationships, intentional coordinates for spatial graphics, and approved spacing throughout. Test longer copy and optional content before multiplying a pattern.
3. **Build the reusable core.** Reuse approved components. Expose text, visibility, and instance-swap controls; reserve variants for meaningful structural or visual choices. Use supported slots where flexible instance content warrants them. Preserve editable text and linked instances.
4. **Bind by meaning.** Use existing semantic or approved component tokens for visible properties. Preserve the distinction between accent fills and readable accent text. Inspect resolved modes and actual bindings; styling that looks correct is not proof of a functioning token system.
5. **Direct the composition.** Establish a clear first read, purposeful whitespace, meaningful imagery, optical alignment, and a deliberate relationship between evidence and headline. Let the information determine the layout while keeping recurring anchors consistent.
6. **Verify in layers.** Review the argument and full-deck rhythm, inspect actual component/layout/token structure, exercise representative edits, and inspect the required final export. State which checks were performed and which could not be performed.

**Figma Design and Figma Slides are different surfaces.** Verify supported operations, access, and export behavior before choosing a build strategy. In particular, do not assume Slides can author variable modes or place every native object inside a main component. The presentation reference records the official limitations and sources, checked 2026-09-08.

**Use alongside the existing references.** The advanced guidance is embedded below. Original fonts, logos, imagery, token definitions, scripts, and brand handbooks remain in the linked repository. If a required dependency is unavailable, identify it and pause the affected work rather than inventing its contents.

## Core palette

| Token | Hex | Role |
|---|---|---|
| Electric | `#001AFF` | Hero accent. Use like punctuation: sparse, decisive. Never a large fill behind text. |
| Dark Navy | `#040038` | The premium dark surface. |
| Light Blue | `#5D8FFF` | The accent partner on dark surfaces. Safe for large soft fills. |
| White | `#FFFFFF` | Default editorial light surface, and text on dark. |
| Blue 50 | `#F0F5FF` | Quiet secondary light surface, table zebra, panels. |
| Neutral 900 | `#111927` | Body text on light. |

The two blues have strict roles. Electric is the call-to-attention on light surfaces: eyebrows, key numerals, the one highlighted word. Light Blue plays that role on navy, where Electric fails contrast at small sizes. Never swap them.

Gradient (event surfaces only: covers, dividers, closings): linear 145 degrees, `#040038` to `#001AFF`, mid-stop `#01006E` at 55 percent. Never behind dense body copy. The gradient follows the active palette — an orange deck gets an orange gradient.

## Six palettes

Blue is the house default. **Five secondary palettes can carry a whole deliverable** when the subject calls for it — the Hospitals Report runs entirely in orange. A deck picks one palette; the accent, the dark ground and the gradient all follow it.

| Palette | Signature | Deep |
|---|---|---|
| **Blue** | Electric `#001AFF` | Dark Navy `#040038` |
| **Orange** | `#F47A48` | `#842C09` |
| **Green** | `#22C36F` | `#012F02` |
| **Yellow** | `#FED340` | `#693F02` |
| **Purple** | `#C68FFF` | `#2E0068` |
| **Red** | `#FF2B3C` | `#640000` |

Each runs a full twelve-step ramp. **Never mix two palettes on one surface.**

**The signature is a fill colour, not a text colour.** Blue is the exception — Electric is dark, so it reads at 8.1:1 and doubles as the accent text. Every secondary signature is a vivid *light* tone: white on yellow `#FED340` measures 1.44:1. In Figma use `surface/accent` for a fill and `text/accent` when it must be read; the token system picks the right step for each palette.

Red, Yellow and Green also serve as the RAG data dots (`#FF2B3C`, `#FED340`, `#22C36F`). That use is separate from the palettes and unaffected by which palette a deck runs in.

Colab and Majarah have their own greens and purples, and they are **different values**. Never substitute one for the other — load `colab-design` or `majarah-design`.

## Typography

Two families carry the entire voice. Font files ship in `assets/fonts/`, ready-made CSS in `assets/fonts.css`.

- **thmanyah serif display**: titles, stats, quotes, brand numerals. Weights: Light, Regular, Medium, Bold, Black. It has no italic; express emphasis through scale, weight, and color only.
- **Azm X Variable** (sans, supports English and Arabic): body, labels, tables, UI. Weights: Thin, ExtraLight, Light, Regular, Medium, SemiBold, Bold, Heavy.

Rules: serif carries personality, sans carries information. Never set body copy in serif, never set a hero in sans. Eyebrows are Azm X SemiBold, UPPERCASE, tracked wide. Stat numerals pair a serif figure with a sans Medium suffix on one baseline.

## The chevron

The rightward chevron is the only graphic device, and it is **functional, never background decoration**. Sanctioned uses: photo mask, stacked-in-motion hero trio (foreground compositional art), section tick, and list bullet. One big chevron gesture per surface, always pointing in the reading direction. No clip art, no 3D blobs, no glows, no drop-shadow cards. Phosphor icons are permitted alongside the chevron once the user has confirmed them — see the Icons section.

**Banned (owner decision, 2026-07-20): chevrons as backgrounds.** No oversized ghost chevrons bleeding off corners, no navy-on-navy or low-opacity chevron field textures, no concentric chevron arc backdrops, no chevron art placed behind or under content. Backgrounds stay clean: solid surface, gradient (event surfaces only), and nothing else. If a layout feels empty without a background device, the answer is negative space, not a chevron.

## Layout essentials

- 8 px baseline grid. Spacing scale, the only permitted values: 8, 16, 24, 40, 64, 96, 128, 160 — plus 0 and 4 for hairline cases. Never 12, never 20.
- Left-aligned, top-weighted, asymmetric by default. Only closings are centered.
- Decoration is exactly three things: chevron, gradient, hairline (1 px rules).
- One deliberate grid-break per surface signals human craft.
- Presentation canvas: 1920 x 1080, margins 120 left/right, safe area 100 px, body measure 6 to 7 columns max.

## Icons

Phosphor Icons (MIT, free for client work) is the only icon library. **Icons are permitted on any surface — decks, reports, covers, printed documents, product UI — but you must ask the user before adding them.** Never decide either way on their behalf: adding an unasked icon row and stripping icons because a surface "feels editorial" are both wrong. Ask once, then proceed. Icons never replace the chevron as bullet, tick, or mask; they sit alongside it.

Locked usage: weight Regular (Light on dark where Regular reads heavy), size 20 px inline / 24 px standalone / 32 px feature anchor. Never Fill or Duotone. On light surfaces use Neutral 900 with at most one Electric accent icon; on dark use White with Light Blue for secondary, never Electric. Prefer icon plus label; a standalone icon still needs an `aria-label`. Full rules in [references/icons.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/icons.md).

## Human-craft guardrails

These read as AI or template tells; never do them: rounded-corner cards with drop shadows everywhere, centered everything, equal-length padded columns, plain numerals in default sans, scattered decorative icon rows standing in for content, Electric as a large text background, gradients behind paragraphs, uniform 16 px spacing everywhere, scattered chevrons.

## Communication and content

Any copy task, on any surface, starts by fixing three things: the brand, the audience, the surface.

| Brand | What it is | Motions | Voice |
|---|---|---|---|
| AZM X | The consultancy | B2G · B2B · Internal | Visionary Expert and Strategic Partner |
| Colab | UX research platform | B2G · B2B · B2C | The Empathetic Analyst |
| Majarah | Community and event hub | B2C | The Inclusive Mentor |
| Clix | ERP for SMEs | B2B | The Trusted Operator |
| Anatomi | Design benchmark library | B2G · B2B · B2C | The Analyst–Curator |

**This skill's visual system is AZM X only.** No palette, logo, font, or layout rule here belongs to the other four. Apply a sub-brand's voice freely; before applying visuals to a sub-brand deliverable, ask the user which visual system to use. Two sub-brands have their own installed skills: Colab → `colab-design`, Majarah → `majarah-design`. Use them for anything visual in those brands. Clix and Anatomi have no visual skill yet — ask.

**Never invent a message.** Three internal segments, three external motions, and eight personas each carry a verbatim core message in [references/audiences-and-messaging.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/audiences-and-messaging.md). Quote it, or write a tighter line that keeps the same claim. Do not soften it, and do not move a message between brands.

**House voice beats the strategy deck.** The deck permits 3 to 5 hashtags per post, 5 to 10 on Instagram, encourages emojis, and mandates a CTA on every post. All three are superseded: **three hashtags maximum at the end, no emojis in copy, no mandatory CTA**, on every channel and every brand. Never restore the deck's figures. The one emoji carve-out is the email design system's section-header and digest chip glyph (C03, C04, C07, C16), which is a visual component rather than copy.

**The creative bar is level 5, "Strategically Creative"**: right brand, right audience, builds equity, earns attention. Level 3, a decent idea decently made that does not build the brand, is a fail. The riskiest idea is the one nobody notices.

**Brief before you make.** Every brief needs a clear objective, a real audience insight, honest success criteria, and the three-sentence story: the audience wants ______, the obstacle is ______, our brand can facilitate it because ______. If those three will not close cleanly, the strategy is not ready and craft will not save it.

For channel roles, the POEM model, the RACI matrix, the content and social workflows, the three operating rituals, and the full creative evaluation framework, read [references/communication-strategy.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/communication-strategy.md).

## Assets

| Asset | Path | Use |
|---|---|---|
| Logo, colored | `assets/logo/azmx-logo-colored.svg` | Default on white |
| Logo, navy dark | `assets/logo/azmx-logo-navy-dark.svg` | Monochrome on light surfaces |
| Logo, white | `assets/logo/azmx-logo-white.svg` | On navy or gradient |
| Favicon | `assets/logo/azmx-favicon.png` | Browser-tab icon for any AZMX web deliverable: the white chevron on Electric, 100 x 100 px |
| Azm X fonts | `assets/fonts/azmx/*.ttf` | Sans, EN + AR |
| thmanyah fonts | `assets/fonts/thmanyah/*.woff2` (web), `*.otf` (desktop) | Serif display |
| Font-face CSS | `assets/fonts.css` | Drop into any HTML deliverable |
| Image library | `assets/images/` | 242 AZMX brand images in 8 sections. Default to `gradient/` and `blue/`; see [references/image-library.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/image-library.md) |
| Email skeleton | `assets/templates/email-starter-skeleton.html` | Blank ready-to-fill AZMX email, default blue theme |
| Email components | `assets/templates/email-component-showcase.html` | Every email component rendered once, copy-paste markup |

Logos are optically centered, never bounding-box centered, and never cross the 100 px safe area. On dark surfaces use the White variant, on light use Navy Dark or Colored.

## Use the image library

Any visual deliverable that needs imagery **uses this library** rather than generic stock, a placeholder, a flat colour block, or a newly generated image. 242 images ship with the skill; there is almost always a fit.

**How to reference them, by deliverable type:**

- **HTML, email, or web page**: use the public URL so the file works for anyone who opens it —
  `https://raw.githubusercontent.com/Gamaleldientarek/azmx-brand/main/assets/images/blue/blue-014.jpg`
  Local relative paths only when the deliverable ships alongside the skill folder.
- **Word, PowerPoint, PDF, or any document build**: embed the local file from `assets/images/<section>/`.
- **Figma**: upload the local file as an image fill, and prefer the chevron photo mask over a plain rectangle.
- **Anything the user will hand-edit later**: give them the filename and the gallery link, https://gamaleldientarek.github.io/azmx-brand/

**Recolouring an image to another theme:** the library ships tested prompts in [references/recolor-prompts.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/recolor-prompts.md) that convert an image between colour themes while holding lighting, grain, frosted highlights, composition, and pure white constant. Use the matching prompt with the Seeddance Edit V5 model, and never hand-write a recolour prompt when one exists. Recoloured output belongs in the section it was converted to, added through `scripts/add-images.py`.

**Picking one — match the concept first:**

Every image carries three concept tags (`momentum`, `precision`, `growth`, `clarity`, `foundation`, `craft`, and so on) describing what it can represent, not what it literally shows. **Choose by meaning, then by colour.** Read the message of the surface — a section about scaling a business wants `growth` or `scale`; a methodology page wants `structure` or `precision`; a closing wants `horizon` or `potential` — then search [references/image-index.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/image-index.md) for that tag and pick from the matches.

An image whose concept contradicts the copy is worse than no image. Never pick one purely because it looks good in isolation.

1. Read the surface's message and search the index for the matching concept tag.
2. Within those matches, default to `blue/` for general surfaces and `gradient/` for covers, dividers, and closings.
3. Check the index for the image's dominant colour and safe text colour before laying type over it.
4. When several images fit, name two or three candidates and let the user choose. Do not silently pick, exactly as with colour tokens.
5. Never invent or download outside imagery for an AZMX deliverable without saying so first. If nothing in the library fits, say that plainly and ask before sourcing elsewhere.

Images are dark surfaces: White titles, Blue 100 body, Light Blue eyebrows, and Electric only as a chevron tick or single rule. The `white/` section is the exception, taking Navy text with Electric accents.

## Ask before you color

**First fix the palette, then the token.** If the deliverable's palette is not already obvious, ask which of the six it runs in — that decision drives every accent, the dark ground and the gradient, so making it late means reworking. Blue unless there is a reason.

Then confirm the accent token:

> "Which token should I use here: the palette accent (`surface/accent` for a fill, `text/accent` where it must be read), or a specific step — a neutral, a deep tone, a ramp step?"

Rules for this step:

- Never silently pick an accent color when more than one token could fit. One short question, then proceed.
- **Never hand-pick a hex when a token exists.** In Figma bind the semantic token; in HTML use the CSS variable from `scripts/tokens-to-css.mjs`. A raw hex cannot follow the palette or the theme.
- If the user names a token that is not in [references/colors.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/colors.md), ask them to share its hex value. Use the value they give, and offer to add it to [references/colors.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/colors.md) so the palette stays the single source of truth.
- Skip the question only when the choice is already forced by the system (for example: body text on white is always Neutral 900, text on a dark ground is always White or the palette's step 100, RAG dots are always Red / Yellow / Green).

## Workflow

1. **Fix the palette first** — which of the six the deliverable runs in. Blue unless there is a reason. Everything downstream depends on it.
2. Identify the surface (dark ground, white, palette tint, or gradient) and apply its text colors from [references/colors.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/colors.md).
3. Confirm the accent color token with the user (see "Ask before you color" above). For anything built in Figma, read [references/design-tokens-usage.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/design-tokens-usage.md) before binding.
4. Load the two font families from `assets/fonts.css` for any HTML/web deliverable, or embed the TTF/OTF files for documents.
5. If the deliverable needs imagery, pick from the image library (see "Use the image library" above). Never substitute generic stock or a placeholder.
6. Place the correct logo variant for the surface.
7. Apply one chevron gesture maximum, pointing right.
8. Ask the user whether they want icons on this deliverable (see "Icons" above). Ask once, before placing the first one. Never decide either way silently — this applies to decks and reports exactly as it applies to product UI.
9. For emails and newsletters: follow [references/email-design-system.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/email-design-system.md) (Arabic RTL rules are non-negotiable) and build from the email skeleton template.
10. For all written copy, in this order: identify the brand and audience and take the verbatim core message from [references/audiences-and-messaging.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/audiences-and-messaging.md); load the voice — [references/voice-and-tone.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/voice-and-tone.md) for AZM X, [references/sub-brand-voices.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/sub-brand-voices.md) for Colab, Majarah, Clix, or Anatomi — and apply its no-AI-tells mechanics; for an article, a social adaptation, or an English-to-Arabic localization, start from a tested prompt in [references/content-prompts.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/content-prompts.md).
11. Check the guardrails table above before delivering. When in doubt, remove decoration. Restraint is the luxury.
12. For anything that will be published, run the 6-point pre-publish checklist in [references/voice-and-tone.md](https://github.com/Gamaleldientarek/azmx-brand/blob/main/references/voice-and-tone.md) last. Three hashtags maximum, no emojis in copy (the email chip glyph is the one exception), and no CTA unless a genuine next step exists.


---

## Advanced Figma design practice

Use for AZMX work in Figma Design or Figma Slides. This is construction guidance, not a replacement brand system. The existing brand references own colors, spacing, typography, imagery, and voice. These recommendations are design judgments unless a linked source identifies a product capability. Research checked 2026-09-08; recheck plan-dependent or newly introduced features when needed.

### 1. Establish the design contract

Identify the audience, intended decision, surface, dimensions, language, source content, editing owner, and final delivery format from the brief and existing file. Ask only for material gaps; preserve decisions already supplied. Distinguish a live presentation from a reading deck: the former needs pacing and presenter support; the latter must explain itself.

Inspect the existing file before changing it: pages/slides, representative frames, local and enabled library components, text styles, variable collections and modes, font availability, and export constraints. Reuse the system actually present. Names in a reference are not proof that a library is enabled or that a binding exists.

Confirm the editor surface and available tools. Figma Design frames, Figma Slides, and FigJam are different document models. Never promise a manipulation merely because a similarly named UI feature exists. Read the tool's supported operations; use only verified capabilities. If an operation is unavailable, state the specific limitation and complete independent work.

For new work, establish a representative composition with real content, then test its editing behavior before repeating it. For an existing artifact, make a focused repair rather than rebuilding the whole file without a reason.

### 2. Auto Layout is a content contract

Choose layout from how content must behave, not from a rule that every layer needs Auto Layout. Use it for titles and body stacks, lists, metric groups, table rows, captions, navigation, footers, and other content-dependent arrangements. Retain deliberate free positioning for charts, masks, diagrams, and editorial art where spatial relationships carry meaning.

| Situation | Structure and sizing | Check |
|---|---|---|
| Title and explanatory copy | Vertical stack; constrained width, height grows with text | Longer heading pushes content rather than overlaps it |
| Label with optional mark | Horizontal stack, text-led sizing; fixed mark dimensions | Hide mark; no empty gap remains |
| Row that spans a page | Fill width inside a parent with a defined width | Parent resize preserves alignment |
| Repeated comparison units | Shared column geometry; vertical stacks within cells | Longest content does not break peer alignment |
| Two-dimensional editorial arrangement | Grid Auto Layout when supported | Track sizes and spans behave as intended |
| Photo or logo | Fixed or bounded dimensions and deliberate aspect treatment | Resize does not stretch artwork |
| Presentation canvas | Fixed outer slide; nested content layout | Content stays within the approved safe area |

Figma supports horizontal, vertical, and grid Auto Layout. Layout guides are visual alignment aids; they do not create reflow behavior. Use nested horizontal/vertical frames as a supported fallback when the available tool cannot configure grid. [Figma Auto Layout](https://help.figma.com/hc/en-us/articles/360040451373-Guide-to-auto-layout), [grid flow](https://help.figma.com/hc/en-us/articles/31289469907863-Use-the-grid-auto-layout-flow).

Choose sizing per axis: Hug for content-driven size, Fill for taking available parent space, Fixed for deliberate dimensions. Avoid a parent that must Hug an axis while its child needs that same undefined space to Fill. Constrain width for wrapping body text and allow height to grow. Use supported minimum/maximum sizes when they express a real limit. Wrapping is useful for a responsive list; it is usually wrong for a comparison whose columns must stay aligned. [Sizing guidance](https://help.figma.com/hc/en-us/articles/31289464393751-Use-the-horizontal-and-vertical-flows-in-auto-layout).

Choose fixed gaps for a stable editorial rhythm and distributed spacing only when content must occupy the available extent. Bind approved spacing tokens where supported. Never insert blank text, repeated spaces, invisible spacer rectangles, or arbitrary line breaks to simulate layout. Keep nesting only when a frame owns a meaningful padding, alignment, wrapping, or resizing behavior.

Use Ignore Auto Layout/absolute positioning only for intentional overlap or anchoring. Give it an understandable layer name and inspect the result after resizing. Clipping should implement an intentional viewport or mask; it must not conceal overflowing copy. A valid fixed slide can still contain flexible internal components.

Stress-test with longer real copy, the longest label, one missing optional element, and the maximum plausible item count. Test an alternative width only if the deliverable needs resizing. Repair in this order: improve wording without changing meaning, adjust grouping, choose a better composition, split content, then adjust within the approved type scale. Do not solve overload with unreadably small type.

### 3. Variables, modes, and styles

Inspect existing tokens before creating new ones. Use the existing AZMX token references as the source of truth; do not reconstruct all collections from the examples below or assume a documented token count is current.

Keep raw palette values in primitives, intent in semantic tokens, and component-specific aliases only where components have distinct reusable needs. Bind visible surfaces and text to semantic or approved component tokens. A layer named after a token is not bound to it. Avoid parallel collections that encode the same fact under different names.

Use color variables for supported color fields, numbers for supported spacing and dimensional properties, strings for supported shared content/font properties, and booleans for shared visibility where useful. Use text styles for reusable typography combinations; variables can parameterize supported fields without replacing the entire style. Do not make each unique slide sentence a global variable. [Supported bindings and detachment](https://help.figma.com/hc/en-us/articles/15343107263511-Apply-variables-to-designs).

Examples such as `surface/accent` and `text/accent` illustrate distinct roles: a vivid fill is not necessarily a readable text color. Bind the actual existing tokens. Retain data status semantics independently of the presentation palette; color alone must not communicate status.

Modes represent deliberate contexts such as light/dark or palette selection. Keep independent contexts in the existing collection structure rather than multiplying combinations indiscriminately. Use parent inheritance where intended, with explicit overrides for deliberately different sections. Inspect resolved values as well as the names of bindings. Do not assume resizing a frame automatically selects a different mode. [Variable modes](https://help.figma.com/hc/en-us/articles/15343816063383-Modes-for-variables).

When editing a system, trace alias dependencies before changing a source value. Preserve types and check every affected mode for unresolved aliases, accidental overrides, and contrast regressions. Limit variable scopes and describe ambiguous tokens where the editor supports this. Validate one representative component and composition under every supported context, expanding checks to anything affected by a failure.

Figma warns that dragging on-canvas gap or padding controls can detach number-variable bindings. Recheck bindings after visual adjustment. A screenshot can confirm appearance; it cannot prove that semantic tokens or component links remain attached.

### 4. Components that other people can edit

Componentize repeating structures or elements whose updates need to propagate. A one-off composition can remain an ordinary frame. Prefer small reusable parts assembled into flexible patterns over one component with hundreds of combinations.

Use the existing library before making local substitutes. Useful presentation candidates include title groups, footers, citations, metric units, comparison headings, process steps, and approved image masks. Only create patterns actually needed by the content. A component's purpose is repeatability and safe editing, not merely appearing in the Assets panel.

| Editing need | Preferred control |
|---|---|
| Change title, metric, or caption | Text property |
| Show or hide optional content | Boolean property |
| Choose approved nested visual | Instance swap; preferred choices where supported |
| Change a meaningful structure, size, or state | Small, purposeful variant set |
| Flexible child content without detaching | Slot property if available in the editor and tool |
| Change a theme shared across elements | Existing semantic variables and modes |

Figma documents these property types, including slots; verify support before using them. Boolean component properties control visibility and should not replace distinct interactive states that require prototype connections. [Component properties](https://help.figma.com/hc/en-us/articles/5579474826519-Explore-component-properties).

Expose only the nested controls an editor needs. Avoid variants for arbitrary copy, every number, or each optional visibility combination. Preserve consistent layer names and hierarchy across related variants to support override preservation. Test actual swaps; do not assume names alone guarantee preserved content.

Use clear names such as `Presentation/Metric`, `Editorial/Caption`, and `Diagram/Step` when they fit the existing naming scheme. Document purpose, editable controls, width/content limits, and an example with realistic content. Identify the source of shared components and keep main components separate from final output where the document model allows it. [Figma component management](https://help.figma.com/hc/en-us/articles/39747637290263-Components-collection-Tips-for-component-management).

Keep instances linked. If a one-off request exceeds a component's contract, first consider a supported property, a nested component, or a new justified pattern. Detach only when the exception is intentional and explain the maintenance consequence. Treat changes to shared main components as affecting every instance; assess impact before editing them and retain existing publication approval boundaries.

### 5. Art direction beyond mechanical consistency

Choose a visual thesis tied to the message: evidence-led, typographic, documentary, comparative, or spatial. Express it with the approved brand system. Do not substitute stylistic adjectives for decisions about hierarchy, density, image selection, and pacing.

Build a clear first read, supporting read, and detail read. Assign prominence according to importance, not equal-sized containers. Align optically as well as mathematically: inspect logos, serif numerals with suffixes, image crops, and punctuation. Keep recurring anchors consistent while allowing content to dictate composition.

Use negative space to separate thoughts and establish emphasis. Do not add a decorative object because an area is empty. An intentional grid break must improve the narrative hierarchy and remain within content safety constraints. Vary compositions because the information changes; do not force every slide into a new layout or every slide into the same template.

Preserve live text and editable vectors wherever the required format allows them. Use imagery as evidence or a meaningful metaphor. Inspect focal points, resolution at output size, crop behavior, and text contrast at the actual placement. An image's overall luminance does not guarantee contrast beneath a specific word.

### 6. Files beyond presentations

- **Reports:** use a consistent reading order, editorial columns, running information, figure captions, and source notes. Define page breaks deliberately; Auto Layout does not provide automatic print pagination. Verify physical page dimensions and output requirements for print.
- **Social and campaign formats:** recompose for the aspect ratio and platform safe areas. Share typography and content patterns; do not uniformly scale a wide design into a square. Check image focal points and message visibility at feed size.
- **Product screens:** model content states, user flow, responsive limits, and interaction states that the brief requires. Inspect target widths and longer content. Handoff must identify behavior that a static screen cannot establish.
- **Diagrams:** choose spatial encoding by relationship: sequence, hierarchy, comparison, or flow. Keep connectors, reading direction, and labels unambiguous. Use Auto Layout for repeatable units, with deliberate coordinates where geometry itself conveys meaning.

### 7. Quality gates and handoff

Check visual and structural quality separately. For a deck, read `figma-presentation-design.md` as well.

1. **Message:** the viewer can identify the intended takeaway; important evidence and sources are present.
2. **Craft:** hierarchy, whitespace, alignment, crops, type, and color roles follow the brand and serve the content.
3. **Structure:** inspect actual Auto Layout sizing, token bindings, component links, properties, and layer names. Representative content edits do not cause collisions or conceal content.
4. **Accessibility:** use WCAG AA contrast as a screening baseline—4.5:1 for normal text and 3:1 for qualifying large text. Evaluate at the actual rendered size, not merely large Figma pixel values. Use labels or another cue alongside color. This is a design check, not a claim of full accessible-export compliance. [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
5. **Delivery:** inspect the actual export for fonts, line breaks, image quality, order, hyperlinks where required, and editing behavior. Verify content rather than only confirming a file exists.

In Figma Design, use the existing file organization; for a new substantial file, separate guidance, reusable elements, working explorations, and delivery content only as needed. In Figma Slides, preserve the slide order and use supported deck organization rather than prescribing Design pages. Exclude exploratory content from exports without deleting unrelated user work.

Handoff identifies the final file or frames, editable controls, dependencies, tested modes/sizes and exports, and remaining limitations. Distinguish visually reviewed, structurally inspected, and export-tested. Never claim checks that the tools did not perform.


---

## Presentation direction and Figma Slides

Use alongside `figma-advanced-design.md` for live decks, reading decks, pitches, proposals, and reports presented as slides. The editorial practices below are recommended defaults, not universal Figma requirements.

### Build the argument before the layouts

Define the audience's starting belief, the decision or understanding required, and the evidence needed to get there. Choose a structure that fits the task; a sales proposal and a research readout should not inherit the same story arc.

Write the slide headlines as a continuous argument. Prefer a supported conclusion to a generic topic label when the slide is making a claim. Each slide should have a clear job: frame the issue, establish evidence, compare choices, explain a mechanism, recommend a direction, or state a next step. Merge repetition; move secondary proof into a readable appendix when appropriate.

For live delivery, keep supporting detail in presenter notes when available. For reading decks, preserve enough definitions and connective language to stand alone. Do not impose a fixed word count or the same density on both. Figma's presentation guidance emphasizes storytelling and alignment; it also notes that clarity can justify more slides rather than denser ones. [On pitching and presenting](https://www.figma.com/blog/on-pitching-and-presenting/).

### Choose the visual argument

| Content job | Useful visual structure | Common failure |
|---|---|---|
| Establish a thesis | Strong title with one meaningful visual or proof point | Slogan without evidence |
| Prove scale or change | Hero metric with baseline, period, and implication | Large number with no denominator |
| Compare options | Aligned criteria, units, and evidence | Unequal categories or decorative cards |
| Explain a mechanism | Flow or staged diagram | Paragraphs inside disconnected boxes |
| Show evidence | Chart, artifact, or meaningful annotated image | Stock image that proves nothing |
| Explain a roadmap | Time axis plus outcomes and dependencies | Identical boxes without dates or sequencing |
| Support a recommendation | Decision, rationale, tradeoff, next action | Recap with no decision |
| Preserve technical detail | Readable appendix with cross-reference | Shrinking text to keep slide count down |

These are starting points, not a requirement to include every archetype. Build the minimum useful set of reusable patterns. Create actual examples with representative content before multiplying them across the deck.

### Establish a deck system

Use the established AZMX canvas and geometry where applicable. Reuse the approved title, body, label, citation, and numeral styles. Do not invent pixel sizes when the design system defines them. When the type scale is missing, propose a small role-based scale and validate it at viewing size; report it as a proposed extension.

Maintain stable title anchors, footer behavior, content bounds, and citation treatment. Choose column proportions by the information, not by automatic symmetry. Give long titles a supported second-line layout and allow copy to grow inside the content structure.

For live decks, judge readability at presentation size and expected viewing distance. Use a thumbnail/contact-sheet pass to inspect pacing, then a full-slide pass for hierarchy, then a detail pass for typography, data, and spacing. Reading decks also need a realistic laptop/PDF viewing check.

Alternate dense proof with moments of emphasis where the argument needs relief. Dark/light shifts and dividers should mark meaningful transitions within the approved palette. Avoid repeated ornamental sections that interrupt the story. Treat a cover, a comparison slide, and a dense appendix as different editorial problems sharing a common system.

### Data and evidence

Choose the chart from the question: bars for magnitude comparisons, lines for a continuous time trend, scatterplots for relationships, and tables when exact lookup is the primary task. Avoid 3D chart effects and distorted area encodings. Bar-chart baselines should normally begin at zero; disclose and justify nonzero axes in other chart types when they change interpretation.

Show units, time periods, denominators, and sources. Keep comparable charts on consistent scales or explicitly explain differences. Distinguish observed results, estimates, targets, and scenarios. Preserve the source values and calculation assumptions outside the visual so revisions can be checked.

Highlight the evidence supporting the headline; reduce irrelevant gridlines and labels. Prefer direct labeling when it reduces lookup effort. Use color alongside words, shapes, or patterns rather than as the only indicator of meaning. Never invent a source or a number to finish a slide.

### Figma Slides capability boundaries

Checked against official help on 2026-09-08; verify the active seat, permissions, and tool support before relying on these features.

- Design mode exposes Auto Layout and advanced layer controls and requires a Full seat. Variable modes cannot be created in Slides; Figma documents authoring them in Design and making them available through a published library. Do not publish a library without the user's required authorization. [Design mode in Slides](https://help.figma.com/hc/en-us/articles/25423848723863-Use-design-mode-in-Figma-Slides).
- Create main components in design mode; instances can be inserted in slides mode or design mode. Native tables, shapes with text, code blocks, live interactions, and prototypes cannot be included in main components. Keep these as supported native objects and compose reusable headers/captions around them instead of wrapping everything in a component. [Components in Slides](https://help.figma.com/hc/en-us/articles/30630178611991-Create-components-in-Figma-Slides).
- Slides provides presenter notes and a grid view for the deck overview. Use those native facilities where appropriate. Design frames do not automatically provide the same presentation workflow. [Explore Slides](https://help.figma.com/hc/en-us/articles/24170630629911-Explore-Figma-Slides).

A fixed-size slide with nested Auto Layout is a legitimate design. Do not turn a slide into a responsive website or force unsupported objects into a component merely to satisfy a structural checklist. If slide-wide component reuse conflicts with editor constraints, reuse subcomponents and native slide templates instead.

### Motion and final export

Use motion to reveal sequence, establish continuity, or focus attention. Avoid animating every element by default. Keep a complete static reading path for PDF/PPTX delivery; information should not disappear when an animation or interaction becomes static. Check the actual presentation playback when motion is part of the requested result.

Figma Slides exports PDF and PPTX. PPTX export offers editable equivalents or bitmap flattening for shapes/images, but Figma documents font substitution when a font is unavailable in PowerPoint, static images for live interactions/code blocks, and gradients becoming solid fills. [Export documentation](https://help.figma.com/hc/en-us/articles/24848334599447-Export-from-Figma-Slides).

For AZMX, test a gradient cover, a serif statistic with a suffix, and a dense body slide early if PPTX is required. If editable export loses fidelity, explain the specific tradeoff: a flattened visual can preserve appearance but reduces editability. Keep the editable Figma original and use a format appropriate to the user's delivery requirement; never quietly substitute a flattened deck for an editable one.

Inspect final slide order and all exported pages for clipping, missing text, altered fonts, broken crops, and failed contrast. Check the exported file in its intended viewer. For interactive source decks, also verify notes and required interactions in the native presentation environment. If the export or target viewer is unavailable, mark that check as unperformed.

### Editing tests before handoff

Exercise relevant cases on representative patterns, and fix the source pattern when failures repeat:

- Replace a short title with the longest actual title: following content should reflow without colliding with the footer.
- Change a metric and its suffix: alignment and emphasis should remain deliberate.
- Hide an optional subtitle/source control: surrounding space should close appropriately, without removing a required citation.
- Swap an approved image: crop and focal point should survive the intended aspect ratio.
- Change the supported palette/theme: text, fills, and rules should resolve through the intended tokens.
- Update a recurring footer/main component: intended instances should update while local copy stays correct.
- Export the most complex slide: compare native appearance and editability with the required final format.

Report only tests actually performed. Passing structural checks does not replace editorial review; an editable, perfectly aligned deck can still make a weak argument.
