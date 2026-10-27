---
name: azmx-brand
description: "Apply the official AZMX brand identity to any deliverable, built on the AZM X Design System. Use whenever work involves AZMX branding, AZMX presentations, proposals, emails, newsletters, reports, social graphics, web pages, product UI, React or Tailwind components, Figma designs, documents, printed A4 documents, fillable PDF forms, or copywriting in the AZMX voice, or when the user mentions the AZM X Design System, @azmxsa/cli, AZMX colors, black grounds, the chevron, Electric blue, thmanyah serif, or Azm X fonts. Also covers the unified communication strategy: communication planning, content plans and editorial calendars, social posts and captions for LinkedIn, Instagram or Twitter/X, blog articles, messaging and positioning, audience personas and segments, B2G/B2B/B2C motions, creative briefs, tone of voice, English-to-Arabic localization, and the AZM X brands Colab, Majarah, Clix and Anatomi. Provides the link to the design system's components, blocks and tokens, the full color palette, typography rules, logo and chevron files, web fonts, the email design system, the Figma-to-fillable-PDF form pipeline, the voice and tone guide, and the channel, governance and content-prompt references."
---

# AZMX Brand Skill

AZMX is a leading Saudi digital consultancy, and the parent house for four brands: Colab, Majarah, Clix, and Anatomi. Its philosophy line is **"Designing the Future of Experience."** This skill encodes its official brand and communication system so every deliverable comes out on-brand without re-briefing. Never describe AZMX as a studio, an agency, or a boutique.

One-line ethos: black grounds, electric blue, generous white space, serif personality, the chevron as the only recurring graphic device. **Restraint is the luxury.**

## The AZM X Design System comes first

**Since v3.0.0 (27 October 2026), the AZM X Design System is the source for every AZM X design: code, Figma, documents, decks, emails, any UI and any screen.** It is a private repository (`Gamaleldientarek/azmx-design-system`) of React, Tailwind and Radix components, blocks and tokens, with a dashboard at https://azmx-design-system.vercel.app (behind a Vercel login) and a public installer on npm, `@azmxsa/cli`. Where an older rule in this skill or its references disagrees with the design system, the design system wins. The 13 rulings that settled the differences are in `CHANGELOG.md` (v3.0.0).

**Read `references/design-system-link.md` before building anything visual.** It maps every skill concept (eyebrow, stat, numbered card, quote, table, tag, list, org chart, logo wall, chevron, footer…) to its design-system part and dashboard page, and gives the install steps.

**Start of every AZM X task** (the scripts live in this skill's folder; run them with Node):

1. `node scripts/check-update.mjs` prints one line. If it says the skill is out of date, tell the person to run `npx skills@latest update -g` and restart Claude Code, then carry on.
2. `node scripts/design-system.mjs status` says whether this person can read the design system. It uses their own GitHub sign-in (`gh auth login`, or `GITHUB_TOKEN`); this skill is public, so it carries no key.
   - **Access:** build from the design system as below.
   - **No access:** say so once ("you aren't on the AZM X Design System yet; ask the owner to add your GitHub account, then run `gh auth login`"), then work from this skill's own files. They carry the same rulings: `azmx-tokens.css`, the 2.004 fonts in `assets/fonts/`, and the official chevron in `assets/chevron/`. Never block the work.

**Build by deliverable:**

| Deliverable | Take it from |
|---|---|
| React, Next.js, Tailwind | The installer. `npx @azmxsa/cli init` (sets the project up on Radix), `npx @azmxsa/cli add tokens`, `npx @azmxsa/cli list`, then `npx @azmxsa/cli add <name…>` for each part and block. Never hand-build a part the registry has. Add `-o` in a project shadcn already set up. Fonts: `node scripts/design-system.mjs fetch-fonts src/fonts`, then load them as the design system's Install page shows. |
| Plain HTML: pages, one-page reports, emails, HTML-to-PDF | `node scripts/design-system.mjs fetch-tokens <folder>` writes the system's `azmx-tokens.css`. Use its variables (`var(--surface-page)`, `var(--text-primary)`, `var(--accent-base)`), `data-palette` on a section to change palette, `.dark` on a section to make it black. Without access, use this skill's `azmx-tokens.css` (`--azmx-*` names, same values). |
| Figma | Bind to tokens by the design system's names and values below. The Figma library's variables still carry the old values (navy grounds, the old spacing and radius names) until they're updated, so check each binding against these rules. |
| Decks, Word, PowerPoint, PDF documents | The same tokens and rules, applied by hand: black grounds, Neutral 900 headings, the site spacing scale, the radius names, no coloured lines. Slide geometry (1920 × 1080 canvas) stays as in `references/design-system.md`. |
| A part the system doesn't have | Build it from the system's tokens and parts, in its look, and tell the person it's a candidate for the design system. |

`node scripts/design-system.mjs drift` compares this skill's tokens with the system's pinned release (`config/design-system.json`) and lists any difference nobody has ruled on.

For the complete handbook (component specs, slide archetypes, Figma implementation), read `references/design-system.md`. For every color tone, read `references/colors.md`. **Before touching a Figma file, read `references/design-tokens-usage.md`**: the guide to using the token system, including which tier to bind to and why the signature colour is not the text colour. For the Figma variables as they were exported (all 550 across five collections), read `references/figma-tokens.md`. **For the parent-brand/sub-brand inheritance model** (what Colab, Majarah, Clix, and Anatomi inherit from AZM X, what they override, and how to onboard a sixth brand), **read `references/brand-inheritance-model.md`** and the configuration files in `config/sub-brands/`. For any HTML email or newsletter, read `references/email-design-system.md`. For any written copy, follow `references/voice-and-tone.md`. When a deliverable needs imagery, pick from the 240 brand images (served from the jsDelivr CDN, not shipped in the skill folder) catalogued in `references/image-library.md` (selection and colour-pairing rules) and `references/image-index.md` (every file with its three concept tags, dominant colour, safe text colour, and direct download link). To convert an image to another colour theme, use the tested prompts in `references/recolor-prompts.md`. For icons, read `references/icons.md`. For any printed A4 document or fillable PDF form, follow `references/pdf-forms.md`: it documents the validated Figma → export → pdf-lib pipeline and the `scripts/build-pdf-form.mjs` tool that stamps form fields at exact coordinates. To turn a deck built as Figma frames into a keyboard-driven presentation, read `references/presentation-transitions.md` and run `scripts/figma-slide-transitions.js`. **When you hit errors with scripts, tools, or workflows, consult `references/troubleshooting.md`**: it consolidates gotchas, common mistakes, validation failures, and tested fixes across the entire brand system.

For any communication planning, channel ownership, or governance question, read `references/communication-strategy.md`. Before writing a single line of copy, load `references/audiences-and-messaging.md` for the audience and its verbatim core message, then `references/voice-and-tone.md` for AZM X's voice or `references/sub-brand-voices.md` for Colab, Majarah, Clix, and Anatomi. For cadence, weekly themes, optimal posting times, and the nineteen internal initiatives, read `references/editorial-calendar.md`. For ready-made content prompts, use `references/content-prompts.md`: it holds 15 tested templates covering blog SEO briefs, long-form articles, case studies, reports, email newsletters, internal memos, press releases, event invitations, video scripts, presentation talking points, social media customization (LinkedIn, Instagram, Twitter/X), WhatsApp messages, and English-to-Arabic localization.

Images are dark surfaces. Every section except White measures below 0.18 luminance, so text over them follows the dark row of the text-colour table: White title, Blue 100 body, Light Blue eyebrow. Never Electric for text on an image; Electric appears over imagery only as a chevron tick. The White section is the one exception, taking Neutral 900 text with Electric accents. Photos stay clean: no dark wash or colour scrim over a photo. Keep text readable with a soft text shadow, a darker crop, or a narrow band behind the text.

## Core palette

| Token | Hex | Role |
|---|---|---|
| Electric | `#001AFF` | Hero accent. Use like punctuation: sparse, decisive. Never a large fill behind text. |
| Black | `#000000` | **The dark ground**: dark sections, dividers, closings, bios, the email footer card, the navigation glass. In every palette. |
| Neutral 900 | `#111927` | Body text **and headings** on light surfaces. Also the raised surface on black (cards, menus on a dark section). |
| Light Blue | `#5D8FFF` | The accent partner on dark surfaces. Safe for large soft fills. |
| White | `#FFFFFF` | Default editorial light surface, and text on dark. |
| Blue 50 | `#F0F5FF` | Quiet secondary light surface, panels, table zebra. |

**Navy is retired as a ground and as a text colour** (owner decision, 27 Oct 2026). Dark Navy `#040038` stays only as Blue 1000 in the ramp and as the colour of the official logo artwork, which isn't redrawn.

The two blues have strict roles. Electric is the call-to-attention on light surfaces: eyebrows, key numerals, the one highlighted word. Light Blue plays that role on black, where Electric fails contrast at small sizes. Never swap them.

**Gradient** (event surfaces only: covers, dividers, closings): linear 145 degrees, black `#000000` to Electric `#001AFF`, through `#01006E` at 55 percent (`#0200D3` is the mid-alt stop). Never behind dense body copy. The gradient follows the active palette: it always starts at black and ends at the palette's signature, so an orange deck gets black to orange.

**The animated footer gradient.** azmx.sa's footer runs a moving version of the gradient: the `AZMXFooterGradient` code component, drawn in WebGL on a black base. It's a continuous blue choreography on a 26-second loop that follows the cursor, with no image or video file. It holds still for reduced motion, dithers to hide colour banding, and pauses off screen. Its still fallback is a radial gradient over black: `#B5D4E9` 0 %, `#267EE3` 35 %, `#052DB6` 55 %, `#000038` 76 %, transparent at 100 %, anchored bottom-left. Use it as the reference for any footer or closing surface that moves. The design system's Footer doesn't include it yet.

## Six palettes

Blue is the house default. **Five secondary palettes can carry a whole deliverable** when the subject calls for it; the Hospitals Report runs entirely in orange. A deck picks one palette, and the accent and the gradient follow it. The dark ground stays black in every palette.

| Palette | Signature | Deep |
|---|---|---|
| **Blue** | Electric `#001AFF` | `#01006E` |
| **Orange** | `#F47A48` | `#842C09` |
| **Green** | `#22C36F` | `#012F02` |
| **Yellow** | `#FED340` | `#693F02` |
| **Purple** | `#C68FFF` | `#2E0068` |
| **Red** | `#FF2B3C` | `#640000` |

Each runs a full twelve-step ramp. **Never mix two palettes on one surface.** In the design system a palette is one attribute, `data-palette="orange"`, on a page or a section.

**The signature is a fill colour, not a text colour.** Blue is the exception: Electric is dark, so it reads at 8.1:1 and doubles as the accent text. Every secondary signature is a vivid *light* tone; white on yellow `#FED340` measures 1.44:1. Use `surface/accent` for a fill and `text/accent` when it must be read; the token system picks the right step for each palette.

Red, Yellow and Green also serve as the RAG data dots (`#FF2B3C`, `#FED340`, `#22C36F`). That use is separate from the palettes and unaffected by which palette a deck runs in.

Colab and Majarah have their own greens and purples, and they are **different values**. Never substitute one for the other; load `colab-design` or `majarah-design`.

## Typography

Two families carry the entire voice.

- **thmanyah serif display**: titles, stats, quotes, brand numerals. Weights: Light, Regular, Medium, Bold, Black. It has no italic; express emphasis through scale, weight, and color only.
- **Azm X** (sans, English and Arabic): body, labels, tables, UI. **Use Azm X v3 (3.007), the file azmx.sa serves, when it's available**: `node scripts/design-system.mjs fetch-fonts <folder>` downloads it with the person's design-system access, or it may already be installed on their machine. **Otherwise use the 2.004 files this skill ships** in `assets/fonts/azmx/` (`assets/fonts.css` has ready `@font-face` rules). v3 is still in beta and not everyone has it. The two draw the same sizes and shapes; v3 overlaps Arabic joins slightly so no hairline seam shows.

Rules: serif carries personality, sans carries information. Never set body copy in serif, never set a hero in sans. **Letter-spacing is 0** on everything: Arabic is never tracked, and English follows it. Stat numerals pair a serif figure with a sans Medium suffix on one baseline.

**Eyebrows** use the design system's `label-lg`: Azm X Medium 14 px, line height 140 %, in the accent colour (Electric on light, Light Blue on black), **written as is: no UPPERCASE, no tracking**, the same in Arabic and English.

On the web and in product UI, use the design system's text styles (`text-display`, `text-h1` … `text-label-lg`, `text-lead`, `text-quote`), which step down at its breakpoints. Decks on the 1920 × 1080 canvas use the slide scale in `references/design-system.md`.

## The chevron

The rightward chevron is the only graphic device, and it is **functional, never background decoration**. **Use only the official file**: `assets/chevron/azmx-chevron-right.svg` and `azmx-chevron-left.svg` (41 × 58, the brand's soft curve, the same file azmx.sa serves). Place it **as a mask over a colour fill**, so it takes any colour (`mask-image` in CSS, an image fill or mask in Figma, the `chevron` library in the design system). **Never redraw it, never stretch it, and mirror it in Arabic** so it points in the reading direction. The old drawn caret (60 degrees, 1 : 1.3) and its Stroked and White-outline variants are retired.

Sanctioned uses: photo mask, stacked-in-motion hero trio (foreground compositional art), section tick, and list bullet. One big chevron gesture per surface. No clip art, no 3D blobs, no glows, no drop-shadow cards. Phosphor icons are permitted alongside the chevron once the user has confirmed them; see the Icons section.

**Banned (owner decision, 2026-07-20): chevrons as backgrounds.** No oversized ghost chevrons bleeding off corners, no low-opacity chevron field textures, no concentric chevron arc backdrops, no chevron art placed behind or under content. Backgrounds stay clean: solid surface, gradient (event surfaces only), and nothing else. If a layout feels empty without a background device, the answer is negative space, not a chevron.

## Layout essentials

- **Spacing: the site scale, `2 · 4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64 · 80 · 96 · 120 · 160 · 200`** (plus 0). These are the only permitted values. Section padding on the web is 120 / 48 on desktop and 80 / 32 or 80 / 20 on smaller screens; heroes start at 160 or 200. Vary spacing deliberately; uniform 16 px everywhere is an AI tell.
- **Radius**: `xs 4 · sm 8 · md 12 · lg 16 · xl 24 · full`. Buttons, fields, tabs and small media use **sm (8)**; cards and panels use **md (12)**. There is no 2 px step.
- **No coloured lines, ever** (owner decision, 27 Oct 2026). No coloured side line, underline, top bar, quote bar or active rule on anything. A selected tab, the current page, a key person in an org chart, a pull quote: each is a **filled shape** (a black pill, a grey Neutral 100 pill, a tinted panel), never a line.
- **Hairlines** are neutral and structural only: the `border/subtle` token (Neutral 200 `#E5E7EB` on light, white at 20 % on black), 1 px, for table rows, field outlines and a box's frame. Nothing else.
- **Flat by default.** Cards never get shadows. Only floating layers (menus, popovers, dialogs) take the design system's soft `shadow-menu` or `shadow-overlay`, and only the navigation takes black glass (black at 35 % with a 30 px blur) as the page scrolls. No glows.
- **Fields** have the 8 px radius and the accent focus ring. Form errors stay visible: a wrong field gets the red border and its message under it, on every wrong field at once.
- Left-aligned, top-weighted, asymmetric by default. Only closings are centered.
- Decoration is exactly three things: chevron, gradient, hairline.
- One deliberate grid-break per surface signals human craft.
- Presentation canvas: 1920 x 1080, margins 120 left/right, safe area 100 px, body measure 6 to 7 columns max.
- Scroll-in animations play once, never again on every scroll, and every motion respects reduced motion.

## Icons

Phosphor Icons (MIT, free for client work) is the only icon library, as in the design system (`@phosphor-icons/react`). **Icons are permitted on any surface (decks, reports, covers, printed documents, product UI), but you must ask the user before adding them.** Never decide either way on their behalf: adding an unasked icon row and stripping icons because a surface "feels editorial" are both wrong. Ask once, then proceed. Icons never replace the chevron as bullet, tick, or mask; they sit alongside it.

Locked usage: weight Regular (Light on dark where Regular reads heavy), size 20 px inline / 24 px standalone / 32 px feature anchor. Never Fill or Duotone. On light surfaces use Neutral 900 with at most one Electric accent icon; on black use White with Light Blue for secondary, never Electric. Prefer icon plus label; a standalone icon still needs an `aria-label`. Full rules in `references/icons.md`.

## Human-craft guardrails

These read as AI or template tells, or break a ruling; never do them: rounded-corner cards with drop shadows everywhere, coloured side lines or underlines on anything, navy dark grounds, UPPERCASE tracked eyebrows, a hand-drawn chevron, centered everything, equal-length padded columns, plain numerals in default sans, scattered decorative icon rows standing in for content, Electric as a large text background, gradients behind paragraphs, uniform 16 px spacing everywhere, scattered chevrons, colour washes over photos.

## Communication and content

Any copy task, on any surface, starts by fixing three things: the brand, the audience, the surface.

| Brand | What it is | Motions | Voice |
|---|---|---|---|
| AZM X | The consultancy | B2G · B2B · Internal | Visionary Expert and Strategic Partner |
| Colab | UX research platform | B2G · B2B · B2C | The Empathetic Analyst |
| Majarah | Community and event hub | B2C | The Inclusive Mentor |
| Clix | ERP for SMEs | B2B | The Trusted Operator |
| Anatomi | Design benchmark library | B2G · B2B · B2C | The Analyst–Curator |

**This skill's visual system is AZM X only.** No palette, logo, font, or layout rule here belongs to the other four. Apply a sub-brand's voice freely; before applying visuals to a sub-brand deliverable, ask the user which visual system to use. Two sub-brands have their own installed skills: Colab → `colab-design`, Majarah → `majarah-design`. Use them for anything visual in those brands. Clix and Anatomi have no visual skill yet; ask.

**Never invent a message.** Three internal segments, three external motions, and eight personas each carry a verbatim core message in `references/audiences-and-messaging.md`. Quote it, or write a tighter line that keeps the same claim. Do not soften it, and do not move a message between brands.

**House voice beats the strategy deck.** The deck permits 3 to 5 hashtags per post, 5 to 10 on Instagram, encourages emojis, and mandates a CTA on every post. All three are superseded: **three hashtags maximum at the end, no emojis in copy, no mandatory CTA**, on every channel and every brand. Never restore the deck's figures. The one emoji carve-out is the email design system's section-header and digest chip glyph (C03, C04, C07, C16), which is a visual component rather than copy.

**The creative bar is level 5, "Strategically Creative"**: right brand, right audience, builds equity, earns attention. Level 3, a decent idea decently made that does not build the brand, is a fail. The riskiest idea is the one nobody notices.

**Brief before you make.** Every brief needs a clear objective, a real audience insight, honest success criteria, and the three-sentence story: the audience wants ______, the obstacle is ______, our brand can facilitate it because ______. If those three will not close cleanly, the strategy is not ready and craft will not save it.

For channel roles, the POEM model, the RACI matrix, the content and social workflows, the three operating rituals, and the full creative evaluation framework, read `references/communication-strategy.md`.

## Emails

**One email system, with two designs.** Public emails (website confirmations, welcome, thank-you, marketing) use the design system's email look: white cards, black buttons, the compact black footer card. Their templates are in the design system's Emails section. The **internal newsletter** has its own design: this skill's email components (`references/email-design-system.md`, `assets/templates/`) with every v3 ruling applied (black grounds, no coloured bars, label-lg eyebrows). A new internal-newsletter design will follow in the design system. Arabic RTL rules are non-negotiable in both.

## Assets

| Asset | Path | Use |
|---|---|---|
| Logo, colored | `assets/logo/azmx-logo-colored.svg` | Default on white |
| Logo, navy dark | `assets/logo/azmx-logo-navy-dark.svg` | Monochrome on light surfaces (the logo artwork keeps its navy) |
| Logo, white | `assets/logo/azmx-logo-white.svg` | On black or gradient |
| Favicon | `assets/logo/azmx-favicon.png` | Browser-tab icon for any AZMX web deliverable: the white chevron on Electric, 100 x 100 px |
| Chevron | `assets/chevron/azmx-chevron-right.svg`, `azmx-chevron-left.svg` | The official chevron, 41 × 58. Use as a mask, never redraw |
| Azm X fonts | `assets/fonts/azmx/*.ttf` | Sans, EN + AR, version 2.004: the fallback when v3 isn't available |
| thmanyah fonts | `assets/fonts/thmanyah/*.woff2` (web), `*.otf` (desktop) | Serif display |
| Font-face CSS | `assets/fonts.css` | Drop into any HTML deliverable (2.004) |
| Tokens | `azmx-tokens.css` · `assets/tokens/azmx-tokens.json` | Every token as `--azmx-*` CSS variables and as data, with the v3 rulings |
| Design-system link | `config/design-system.json` · `scripts/design-system.mjs` | The pinned design-system release; status, tokens, fonts and the drift check |
| Image library | CDN: `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>.jpg` | 240 AZMX brand images in 8 sections, served from jsDelivr (not in the skill folder). `references/image-index.md` lists every file with its link. Default to `gradient/` and `blue/`; see `references/image-library.md` |
| Email skeleton | `assets/templates/email-starter-skeleton.html` | Blank ready-to-fill internal-newsletter email, default blue theme |
| Email components | `assets/templates/email-component-showcase.html` | Every internal-newsletter component rendered once, copy-paste markup |

Logos are optically centered, never bounding-box centered, and never cross the 100 px safe area. On dark surfaces use the White variant, on light use Navy Dark or Colored.

## Use the image library

Any visual deliverable that needs imagery **uses this library** rather than generic stock, a placeholder, a flat colour block, or a newly generated image. 240 images are catalogued; there is almost always a fit.

**Where the images are:** they are not shipped inside the skill folder (that keeps the install at ~8 MB instead of ~60 MB). Every image is served from the jsDelivr CDN at

`https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>.jpg`

for example `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/blue/blue-014.jpg`. The index of what exists is `references/image-index.md`: it lists every file with its concept tags, dominant colour, safe text colour, and its direct link. Search that file for a concept to shortlist candidates, then use the link it gives.

**How to reference them, by deliverable type:**

- **HTML, email, or web page**: use the CDN URL directly so the file works for anyone who opens it:
  `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/blue/blue-014.jpg`
- **Word, PowerPoint, PDF, or any document build**: download the file first, then embed the local copy:
  `curl -L -o blue-014.jpg "https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/blue/blue-014.jpg"`
- **Figma**: download the file the same way, upload it as an image fill, and prefer the chevron photo mask over a plain rectangle.
- **Anything the user will hand-edit later**: give them the filename and the gallery link, https://gamaleldientarek.github.io/azmx-brand/

Old `assets/images/<section>/<file>.jpg` paths and `raw.githubusercontent.com/.../assets/images/...` URLs no longer exist; a local `assets/images/` folder is only present if someone keeps an offline copy.

**Recolouring an image to another theme:** the library ships tested prompts in `references/recolor-prompts.md` that convert an image between colour themes while holding lighting, grain, frosted highlights, composition, and pure white constant. Use the matching prompt with the Seeddance Edit V5 model, and never hand-write a recolour prompt when one exists. Recoloured output belongs in the section it was converted to, added through `scripts/add-images.py`.

**Picking one: match the concept first.**

Every image carries three concept tags (`momentum`, `precision`, `growth`, `clarity`, `foundation`, `craft`, and so on) describing what it can represent, not what it literally shows. **Choose by meaning, then by colour.** Read the message of the surface (a section about scaling a business wants `growth` or `scale`; a methodology page wants `structure` or `precision`; a closing wants `horizon` or `potential`), then search `references/image-index.md` for that tag and pick from the matches.

An image whose concept contradicts the copy is worse than no image. Never pick one purely because it looks good in isolation.

1. Read the surface's message and search the index for the matching concept tag.
2. Within those matches, default to `blue/` for general surfaces and `gradient/` for covers, dividers, and closings.
3. Check the index for the image's dominant colour and safe text colour before laying type over it.
4. When several images fit, name two or three candidates and let the user choose. Do not silently pick, exactly as with colour tokens.
5. Never invent or download outside imagery for an AZMX deliverable without saying so first. If nothing in the library fits, say that plainly and ask before sourcing elsewhere.

Images are dark surfaces: White titles, Blue 100 body, Light Blue eyebrows, and Electric only as a chevron tick. The `white/` section is the exception, taking Neutral 900 text with Electric accents.

## Ask before you color

**First fix the palette, then the token.** If the deliverable's palette is not already obvious, ask which of the six it runs in. That decision drives every accent and the gradient, so making it late means reworking. Blue unless there is a reason.

Then confirm the accent token:

> "Which token should I use here: the palette accent (`surface/accent` for a fill, `text/accent` where it must be read), or a specific step: a neutral, a deep tone, a ramp step?"

Rules for this step:

- Never silently pick an accent color when more than one token could fit. One short question, then proceed.
- **Never hand-pick a hex when a token exists.** In code use the design system's variables (`var(--accent-base)`, `bg-brand`, `text-fg-accent`) or this skill's `--azmx-*` variables; in Figma bind the semantic token. A raw hex cannot follow the palette or the theme.
- If the user names a token that is not in `references/colors.md`, ask them to share its hex value. Use the value they give, and offer to add it to `references/colors.md` so the palette stays the single source of truth.
- Skip the question only when the choice is already forced by the system (for example: body text and headings on white are always Neutral 900, a dark ground is always black, text on black is always White or the palette's step 100, RAG dots are always Red / Yellow / Green).

## Workflow

1. **Check the version and the design-system access** (`node scripts/check-update.mjs`, `node scripts/design-system.mjs status`; see "The AZM X Design System comes first").
2. **Pick the source by deliverable**: the installer for React and Tailwind, the system's `azmx-tokens.css` for plain HTML, the same tokens and rules for Figma and documents. Never hand-build a part the design system has.
3. **Fix the palette** (one of the six; Blue unless there is a reason). Everything downstream depends on it.
4. Identify the surface (black, white, palette tint, or gradient) and apply its text colors from `references/colors.md`.
5. Confirm the accent color token with the user (see "Ask before you color" above). For anything built in Figma, read `references/design-tokens-usage.md` before binding.
6. Load the fonts: Azm X v3 when available, otherwise 2.004 (`assets/fonts.css` for HTML; embed the TTF/OTF files for documents).
7. If the deliverable needs imagery, pick from the image library (see "Use the image library" above). Never substitute generic stock or a placeholder.
8. Place the correct logo variant for the surface.
9. Apply one chevron gesture maximum, with the official file, pointing in the reading direction.
10. Ask the user whether they want icons on this deliverable (see "Icons" above). Ask once, before placing the first one. Never decide either way silently; this applies to decks and reports exactly as it applies to product UI.
11. For emails: public emails start from the design system's email templates; the internal newsletter follows `references/email-design-system.md` and the templates here. Arabic RTL rules are non-negotiable.
12. For all written copy, in this order: identify the brand and audience and take the verbatim core message from `references/audiences-and-messaging.md`; load the voice (`references/voice-and-tone.md` for AZM X, `references/sub-brand-voices.md` for Colab, Majarah, Clix, or Anatomi) and apply its no-AI-tells mechanics; for any content creation (articles, reports, case studies, social posts, emails, press releases, presentations, videos, or localization), start from one of the 15 tested prompts in `references/content-prompts.md`.
13. Check the guardrails above before delivering: no coloured lines, no navy grounds, no shadows on cards, spacing on the scale. `python3 scripts/brand-check.py <file>` lints HTML, CSS and SVG against these rules. When in doubt, remove decoration. Restraint is the luxury.
14. For anything that will be published, run the 6-point pre-publish checklist in `references/voice-and-tone.md` last. Three hashtags maximum, no emojis in copy (the email chip glyph is the one exception), and no CTA unless a genuine next step exists.
