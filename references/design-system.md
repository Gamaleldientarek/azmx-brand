# AZMX Design System

> **v3.0.0 amendment (27 Oct 2026).** The AZM X Design System is now the source for every AZM X deliverable: code, Figma, documents, decks, emails and any screen. Read [`design-system-link.md`](design-system-link.md) first. Where anything below still disagrees with these rulings, the rulings win.
>
> - **Dark grounds** are pure black `#000000`. Dark Navy `#040038` is no longer a ground.
> - **Headings on light** are Neutral 900 `#111927`, the same ink as body text. Navy is no longer a heading colour.
> - **Event gradient:** `#000000` → `#01006E` at 55 % → Electric `#001AFF`, 145°. Dividers may end on `#0200D3`. The start is black in every palette.
> - **Spacing:** 0, 2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 120, 160, 200. "Never 12, never 20" is retired.
> - **Radius:** xs 4, sm 8, md 12, lg 16, xl 24, full. Buttons, fields, tabs and small media use sm. Cards and panels use md. The 2 px step is gone.
> - **Eyebrows:** `label-lg`. Azm X Medium 14 px, in the accent colour, case as written. No uppercase, no tracking, in both languages.
> - **Chevron:** only the official SVG, true ratio 41 : 58 (`assets/chevron/azmx-chevron-right.svg` and `azmx-chevron-left.svg`), used as a mask over a colour fill so it takes any colour. Never redrawn. Arabic uses the left-pointing file. The drawn 60° caret (1 : 1.3) and its Stroked and White-outline variants are retired.
> - **No coloured lines.** No side line, underline, top bar, quote bar or active rule on anything. Selected or important items are filled shapes: pills, tinted panels, a black active pill.
> - **Hairlines:** neutral `border/subtle` only. Neutral 200 `#E5E7EB` on light, white at 20 % on dark. Use them only where structure needs them: table rows, field outlines, a box's frame.
> - **Shadows and blur:** flat by default. Cards never take shadows. Only floating layers (menus, popovers, dialogs) take the soft `shadow-menu` or `shadow-overlay`. Only the navigation takes the black glass (35 %, 30 px blur). No glows.
> - **Tracking:** 0 on labels and eyebrows. Arabic is never tracked.
> - **Fonts:** Azm X v3 (3.007) when it's available from the private design system, otherwise the 2.004 files this skill ships. thmanyah serif display is unchanged.
> - **Emails:** one email system with two designs. Public emails use the design system's email look. The internal newsletter keeps its own design (see `email-design-system.md`).
>
> The sections below have been corrected line by line. This box is the summary.

**The official AZMX brand and presentation design handbook.**
Editorial brand-book system for AZMX — a leading Saudi digital consultancy — as encoded in the *New Direction Library* Figma file and applied to the 66-slide PIF "StudioSpace" proposal.

> One-line ethos: Black and white grounds, electric blue, generous white space, serif personality, the chevron as the only recurring graphic device. **Restraint is the luxury.**

---

## Table of Contents

1. [Introduction & Principles](#1-introduction--principles)
2. [Color](#2-color)
3. [Typography](#3-typography)
4. [The Chevron Motif System](#4-the-chevron-motif-system)
5. [Layout & Spacing](#5-layout--spacing)
6. [RTL (Right-to-Left) Implementation](#6-rtl-right-to-left-implementation)
7. [Components](#7-components)
8. [Slide Archetypes / Patterns](#8-slide-archetypes--patterns)
9. [Implementation Notes (Figma)](#9-implementation-notes-figma)
10. [Changelog](#10-changelog)

---

## 1. Introduction & Principles

### 1.1 What this system is

AZMX's design system is an **editorial brand-book system**, not a UI kit. It is built to make work that reads like a spread in a premium brand book — expensive, catchy, hand-crafted by elite designers — at an Apple / Nike / Tesla / Fortune-5 level of craft. It was developed to rebuild a Financial & Technical Proposal for **PIF (Public Investment Fund)** in AZMX's electric-blue identity, and it is general enough to govern any AZMX brand surface.

The system has a single governing idea: **restraint is the luxury.** The palette is mostly black + electric blue + white. The only recurring graphic device is the chevron. Decoration is deliberately small: chevron + gradient + neutral hairline is the entire kit. Everything else is type, scale, and negative space doing the work.

### 1.2 The editorial brand-book ethos

- Every surface should feel **art-directed**, like an editorial spread — not templated, not generated.
- **Intentional asymmetry, dramatic scale contrast, generous (and unequal) negative space, editorial type hierarchy.**
- **Optical alignment** over mechanical alignment: serif entry-strokes overhang the margin, numerals are figure-aligned, logos are optically (not bounding-box) centred.
- **One deliberate grid-break per surface** — an oversized numeral bleeding a rule, a 1.15× hero cell — to prove a human hand made the decision.
- A **single hidden horizon line** shared across a sequence (e.g. case-study device tops on one baseline) — invisible discipline that reads as money.

### 1.3 The de-AI / human-craft principles (art-direction §8)

This system is defined as much by what it refuses as by what it allows. The following are **instant AI / template tells — avoid them:**

| Avoid (AI / template tell) | Do instead |
|---|---|
| Rounded-corner card + drop-shadow on every block | White space; flat cards with no shadow; neutral hairlines only where structure needs them |
| Centred everything | Default left-aligned, top-weighted, asymmetric (only the closing is centred) |
| Equal-length columns padded to match | Let measures differ — real content |
| Plain `01 / 02 / 03` in default sans | Styled serif brand numerals |
| Clip-art, 3D blobs, geometric scatter, glows, blurs, decorative icon rows standing in for content | The chevron is the system's own graphic device. Phosphor icons are permitted on any surface once the user confirms them — always ask first, see `icons.md` |
| Logos pasted at equal pixel size | Normalise to equal *visual* mass |
| Body copy in serif; heroes in sans | Serif = personality, sans = information |
| Electric `#001AFF` as a large fill behind text (it vibrates) | Electric as punctuation only |
| Gradient behind dense paragraphs; gradient everywhere | Gradient = event surface only |
| Visible 12-col grid lines, default auto-layout look, uniform 16-px-everything spacing | Vary deliberately within the spacing scale (§5.2) and hide the grid |
| Chevrons scattered or pointing against reading direction | One big chevron gesture, always pointing in reading direction |

**Signals of a human elite designer — do these:**

- Optical alignment (serif overhang 4–8 px; figure-aligned numerals; optically centred logos).
- Dramatic scale contrast (e.g. a 168 px hero against a 14 px eyebrow on one surface).
- One deliberate grid-break per surface.
- A hidden horizon line shared across a sequence.
- Restraint: one big chevron gesture + one electric accent per surface, the rest black / white / space.
- Meaningful composition (stepped cards ascend; chevrons connect a process; arcs radiate from a word).
- A consistent micro-system: the same chevron bullet, the same footer, the same page-number flow-tick everywhere.
- Generous, unequal negative space — the page is allowed to breathe and be intentionally lopsided.

### 1.4 Voice & tone

- **Bilingual brand.** The system works in **English and Arabic**; copy is typically English, but Arabic logo lockups appear. Type and brand assets are chosen for EN + AR support.
- **Tagline territory:** *Forward · Human Always · Moving Ideas Forward.*
- **Tone:** confident, editorial, human, premium. Never templated, never "code-looking," never AI-generated in feel.
- **Type voice rule:** serif carries personality (titles, stats, quotes, numerals); sans carries information (body, labels, tables). See §3.

---

## 2. Color

The palette is the **`Colors`** Figma collection (single mode). The discipline is severe on purpose: most surfaces use only black + the two blues + white. Secondary colors are reserved for categorical / semantic data and appear almost nowhere else.

### 2.1 Primary

| Token | Hex | Figma variable | Variable ID | Usage |
|---|---|---|---|---|
| Primary / Electric | `#001AFF` | `Electric` | `1:177` | The hero accent and call-to-attention. Use like punctuation: sparse, decisive. |
| Black | `#000000` | — | — | The dark ground (v3.0.0): dividers, capability slides, full-page bios, closing. |
| Primary / Dark Navy | `#040038` | `Dark Navy` | `1:176` | Blue 1000. Since v3.0.0 it is no longer a ground or a heading colour. It stays in the ramp and in the Navy Dark logo variant. |
| Primary / Light Blue | `#5D8FFF` | `Light Blue` | `1:170` | The dark-surface accent partner to Electric; safe for large soft fills. |
| Primary / White | `#FFFFFF` | `White` | `1:166` | The "editorial light" workhorse surface and on-dark text. |

### 2.2 Blue ramp (50–1000)

| Step | Hex | Notes |
|---|---|---|
| Blue / 50 | `#F0F5FF` | Soft light surface — panels, table zebra, image backings *(var `1:167`)* |
| Blue / 100 | `#DDE8FF` | Body text on dark *(var `1:164`)* |
| Blue / 200 | `#BFD5FF` | Meta / caption on dark *(var `1:130`)* |
| Blue / 300 | `#93B6FF` | — |
| Blue / 400 | `#5D8FFF` | = Light Blue |
| Blue / 500 | `#2661FF` | — |
| Blue / 600 | `#001AFF` | = Electric |
| Blue / 700 | `#0200D3` | Divider gradient stop1 *(var `1:169`)* |
| Blue / 800 | `#01009B` | — |
| Blue / 900 | `#01006E` | Cover gradient mid-stop *(var `1:157`)* |
| Blue / 950 | `#010040` | *(var `1:154`)* |
| Blue / 1000 | `#040038` | = Dark Navy. No longer the gradient start or a ground (v3.0.0) *(var `1:179`)* |

### 2.3 Neutrals (25–950)

| Step | Hex | Notes |
|---|---|---|
| Neutral / 25 | `#FCFCFD` | — |
| Neutral / 50 | `#F9FAFB` | — |
| Neutral / 100 | `#F3F4F6` | — |
| Neutral / 200 | `#E5E7EB` | Grey image-placeholder fill; the `border/subtle` hairline on light *(var `1:160`)* |
| Neutral / 300 | `#D2D6DB` | — |
| Neutral / 400 | `#9DA4AE` | *(var `1:137`)* |
| Neutral / 500 | `#6C737F` | — |
| Neutral / 600 | `#4D5761` | *(var `1:155`)* |
| Neutral / 700 | `#384250` | — |
| Neutral / 800 | `#1F2A37` | — |
| Neutral / 900 | `#111927` | Body text and headings on light *(var `1:138`)* |
| Neutral / 950 | `#0D121C` | Deepest neutral |

### 2.4 Secondary / Alert (RAG)

Permitted **only** for semantic / categorical data — chiefly RAG risk dots. Used as 10 px dots with no labels-in-color. Outside that, the palette is black + two blues + white; Orange and Purple appear nowhere unless a client logo carries them.

| Token | Hex | Figma variable | Variable ID | RAG meaning |
|---|---|---|---|---|
| Secondary / Red | `#FF2B3C` | `Red` | `1:173` | High risk / impact |
| Secondary / Yellow | `#FED340` | `Yellow` | `1:147` | Medium |
| Secondary / Green | `#22C36F` | `Green` | `1:171` | Low |
| Secondary / Orange | `#F47A48` | `Orange` | — | Categorical only (rare) |
| Secondary / Purple | `#C68FFF` | `Purple` | — | Categorical only (rare) |

> Full Alert sets (Red / Yellow / Orange / Blue / Green, each with BG / Border / Text and dark variants) exist in the collection for data-UI contexts, but are out of scope for editorial brand surfaces.

### 2.5 Surface roles

Four surfaces, each with a job. Do not mix them arbitrarily.

| Surface | Fill | Use for | Mood |
|---|---|---|---|
| Solid Black | `#000000` | Dividers, capability slides, closing, full-page bios | "Premium dark" |
| White | `#FFFFFF` | Default content (exec summary, methodology, values, tables, org chart, JDs) | "Editorial light" |
| Blue-50 | `#F0F5FF` | Secondary light panels, table zebra, image backings, soft section breaks | Quiet light |
| Black→Electric gradient | `#000000` → `#01006E` → `#001AFF`, 145° | **Event surfaces only:** cover, dividers, closing, one case-study feature panel | The "moment" |

Gradient detail (v3.0.0): linear 145°, stop0 `#000000` (top-left) → mid-stop `#01006E` (Blue-900) at 55% → stop1 `#001AFF` (bottom-right). Dividers may run slightly darker (stop1 `#0200D3`, the mid-alt). The start is black in every palette, because it follows the dark ground; the middle and end follow the active palette. **Never** place a gradient behind dense body copy.

### 2.6 Text color by surface

| Surface | Title | Body | Eyebrow | Meta / caption |
|---|---|---|---|---|
| Black / gradient | White `#FFFFFF` | Blue-100 `#DDE8FF` @ 88% | Light Blue `#5D8FFF` | Blue-200 `#BFD5FF` @ 70% |
| White | Neutral-900 `#111927` | Neutral-900 `#111927` | Electric `#001AFF` | Neutral-900 @ 55% |
| Blue-50 | Neutral-900 `#111927` | Neutral-900 `#111927` | Electric `#001AFF` | Neutral-900 @ 55% |

### 2.7 The two blues — strict roles

This is the most important color rule in the system.

- **Electric `#001AFF` = the primary accent / call-to-attention.** Eyebrows on light, key numerals, the active page number on light, the single filled hero chevron, the one highlighted word. Never as a line or rule (v3.0.0: no coloured lines).
  - **Do** use it like punctuation — sparse and decisive.
  - **Don't** use it as a large fill behind text (it vibrates), and **don't** set Electric text on black or the gradient at small sizes (contrast fails — switch to Light Blue).
- **Light Blue `#5D8FFF` = the dark-surface partner.** Eyebrows / accents on black where Electric would be too dim, secondary chevrons, the active page number on dark, and large soft fills. Hairlines on dark are neutral (white at 20 %), not Light Blue.

> Secondary color only when needed: outside RAG semantics and (at most) one categorical tag system, no secondary color appears. Restraint is the rule, not the exception.

---

## 3. Typography

Two families, drawn from the **`Fonts`** collection. The entire voice of the system is carried by the contrast between them.

### 3.1 Families

| Role | Family | Figma variable | Variable ID | Notes |
|---|---|---|---|---|
| Display / Titles | **thmanyah serif display** | `Display` | `1:980` | Elegant serif. Personality: titles, stats, quotes, brand numerals. |
| Body / Information | **Azm X Variable** | `Body` | `1:979` | Variable sans, supports **EN + Arabic**. Body, labels, tables, UI. |

**Font version (v3.0.0):** use Azm X v3 (3.007) when it's available, from the private design system or an installed copy. Otherwise use the 2.004 files this skill ships. thmanyah serif display is unchanged.

### 3.2 Weights

Azm X Variable weight set: **ExtraLight · Light · Regular · Medium · SemiBold · Bold · Black.** thmanyah display ships a smaller set (Regular · Light · Medium · Bold · Black). Each weight is a `font-weights/*` variable, with values stored as the **exact installed PascalCase style name** so `fontStyle` can bind live (see §8).

| Weight | Variable ID |
|---|---|
| ExtraLight | `1:978` |
| Light | `1:976` |
| Regular | `1:975` |
| Medium | `1:974` |
| SemiBold | `1:973` |
| Bold | `1:977` |
| Black | `1:981` |

### 3.3 Type scale

Tracking is given in px at the stated size (Figma letter-spacing). Since v3.0.0 labels and eyebrows carry no tracking, as in the design system. The negative values below apply to Latin serif display only. Arabic is never tracked.

| Role | Font | Size / Line-height | Weight | Tracking | Case / Style |
|---|---|---|---|---|---|
| Cover hero display | thmanyah serif | 168 / 156 | Regular | −2 px | Mixed-case |
| Divider title | thmanyah serif | 120 / 112 | Medium | −1.5 px | Mixed-case |
| Closing hero word | thmanyah serif | 220 / 200 | Regular | −3 px | Mixed-case |
| Slide title (H1) | thmanyah serif | 64 / 68 | Regular | −0.5 px | Mixed-case |
| Section / card title (H2) | thmanyah serif | 36 / 44 | Medium | 0 | Mixed-case |
| Sub-label / role title | Azm X Variable | 22 / 28 | SemiBold | 0 | Mixed-case |
| **Eyebrow** (`label-lg`) | Azm X Variable | 14 / 20 | Medium | 0 | Case as written, in the accent colour |
| Body | Azm X Variable | 22 / 32 | Regular | 0 | Sentence |
| Lead / intro body | Azm X Variable | 26 / 38 | Light | 0 | Sentence |
| Caption / meta | Azm X Variable | 14 / 20 | Medium | 0 | Sentence / case as written |
| Stat numeral | thmanyah serif | 88 / 84 | Regular | −1 px | with sans suffix |
| Stat label | Azm X Variable | 16 / 22 | Medium | 0 | Case as written |
| Brand numeral (TOC/section) | thmanyah serif | 64 / 64 | Regular | 0 | `01`–`06` |
| Table header | Azm X Variable | 14 / 20 | SemiBold | 0 | Case as written |
| Table cell | Azm X Variable | 18 / 26 | Regular | 0 | Sentence |
| Quote / testimonial | thmanyah serif | 44 / 56 | Regular | −0.5 px | — |

The eyebrow is the design system's `label-lg` (14 px, line height 140 %) on every surface and in both languages. The 16 px SemiBold UPPERCASE eyebrow with +2.4 px tracking is retired (v3.0.0).

### 3.4 Rules of voice

- **Serif = personality** (titles, stats, quotes, brand numerals). **Sans = information** (body, labels, tables, UI).
  - **Never** set body copy in serif. **Never** set a hero in sans.
- **Stat numerals** use serif for the figure and **sans Medium** for the `+` / unit suffix — e.g. serif `4,000` + sans `+`. The suffix is baseline-aligned to the figure.
- **No italics.** The installed `thmanyah serif display` has **no italic style.** Emphasis is expressed through **scale, weight, and color only** — never a faux or substituted italic. (This supersedes earlier art-direction drafts that called for italic accents; the client confirmed serif-display, no-italics.)

### 3.5 Bilingual note

The gradient brand identity and type system are **bilingual (EN + Arabic).** Azm X Variable carries both scripts; thmanyah display anchors the Latin display voice. Arabic logo lockups (the AZMX wordmark with Hamaa) appear alongside English copy.

---

## 4. The Chevron Motif System

The **chevron `›`** is AZMX's signature graphic and the **only recurring graphic device** in the system. It replaces all generic decoration.

**Geometry (v3.0.0):** only the official chevron SVG, true ratio **41 : 58** (taller than wide). It ships as `assets/chevron/azmx-chevron-right.svg` and `assets/chevron/azmx-chevron-left.svg`. Use it as a **mask over a colour fill**, so one file takes any colour. Never redraw it, never trace it, never stretch it. In Arabic use the left-pointing file. There is one form only: the drawn 60° caret (aspect 1 : 1.3) and its Filled / Stroked / White-outline variants are retired.

> **v1.1 amendment (2026-07-20, owner decision): chevrons are banned as background decoration.** Uses 2 (oversized bleed element) and 4 (concentric chevron arcs) are retired. No ghost chevron field textures, no low-opacity chevron backdrops, no chevron art behind or under content. Backgrounds are solid surface or gradient only. The remaining sanctioned uses are functional/foreground: photo mask, stacked-in-motion hero, section tick, list bullet.

### 4.1 Six sanctioned uses (uses 2 and 4 retired — see v1.1 amendment above)

| # | Use | Description | Where |
|---|---|---|---|
| 1 | **Photo mask** *(signature move)* | Portraits / partnership photos clipped inside a large chevron silhouette (the official SVG at 41 : 58), point leading into white space (motion = "forward"). Typically 620–820 px tall, bleeding off one edge. | About photo, bios, partnerships, client visit, testimonials |
| 2 | **Oversized bleed element** *(retired v1.1)* | One giant ghost chevron anchored to a corner, bleeding off-canvas. **Do not use.** | — |
| 3 | **Stacked-in-motion** | 3–5 chevrons marching in one direction, opacity 100→20%, 32–48 px offset — velocity. Electric→Light Blue fade on light; White→transparent on dark. | Cover hero device, section-flow accents |
| 4 | **Concentric chevron arcs** *(retired v1.1; the stroked chevron it used is retired in v3.0.0)* | Nested open chevrons (3–5, stroke 2–4 px, increasing radius, opacity stepping 60→15%), parked top-right of every divider. **Do not use.** | — |
| 5 | **Section / divider accent tick** | A single Electric chevron (the official SVG as a mask), 40–64 px tall, just before a section numeral or eyebrow — a "you-are-moving-forward" tick. | Dividers, section heads |
| 6 | **List bullet & flow indicator** | A small chevron (the official SVG as a mask, 10–14 px tall, Electric on light / Light Blue on dark) replaces every bullet dot. Also the page-number flow-tick. One consistent bullet across the whole system = craft signal. | Points lists, JDs, steering items, page numbers |

### 4.2 Discipline rules

- **One big gesture per surface.** Maximum ONE "big" chevron gesture (uses 1 and 3) per slide. Bullets (use 6) don't count.
- **Always point in the reading direction** (LTR → right, RTL → left with the left-pointing file). A chevron pointing against the read is a defect.
- **Only the official shape.** Recolour it through the fill under the mask. Never redraw it as a stroke, a caret or a text glyph in a design file.
- Chevrons are never scattered decoratively. If a chevron isn't doing one of the six jobs, it doesn't belong.

---

## 5. Layout & Spacing

### 5.1 Canvas & margins

- **Canvas:** 1920 × 1080 px, static frames. All values are absolute px on this canvas.
- **Outer margin:** 120 px left / 120 px right → **content width 1680 px.**
- **Vertical margin:** 88 px top / 80 px bottom → **content height 912 px** (y: 88–992).
- **Safe area:** 100 px on all sides — logos and client-supplied assets never cross it.
- **Full-bleed exception:** photography, gradient fields, and the chevron photo mask may bleed to 0 / 1920 / 1080. **Type and logos never bleed.**

### 5.2 Baseline grid & spacing scale

- **Baseline:** large layout steps keep an 8 px rhythm on the slide canvas. Finer steps from the scale below are allowed wherever they serve the content.
- **Spacing scale (v3.0.0, the design system's site scale; use only these values):**

```
0 · 2 · 4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64 · 80 · 96 · 120 · 160 · 200
```

These are the only permitted `itemSpacing` / padding values in components. The old "never 12, never 20" rule is retired, and 128 is no longer on the scale (use 120 or 160). Uniform "16px everywhere" is still an AI tell — vary deliberately within the scale.

### 5.3 Column system

- **12 columns**, gutter **24 px**, column width **118 px** → `12 × 118 + 11 × 24 = 1680`.
- Default body measure: **6 columns (732 px)**; **7 columns max (850 px)** — never wider (long measure reads cheap).
- Standard split layouts use the **5 / 7** break (text 5 cols / feature 7 cols) or **7 / 5** reversed.

### 5.4 Header / eyebrow zone

- Eyebrow baseline at **y = 88**, left edge x = 120.
- Title block starts at **y = 152** (one 64-step below eyebrow).
- On most content slides the title baseline lands by **y = 300**, leaving the lower two-thirds for content — deliberate top-weighting.

### 5.5 Footer zone (every slide except the cover)

- Footer band **y = 1000–1032.**
- **AZMX `Logo with Hamaa` mark:** bottom-left, left edge x = 120, optically centred on y = 1016, height **24 px** (White on dark, Navy Dark on light).
- **Page number:** bottom-right, right edge x = 1800, baseline y = 1016. Azm X Variable Medium 16 px, no tracking. Styled brand numeral — current page in Electric `#001AFF` (on light) / Light Blue `#5D8FFF` (on dark), total in 40% neutral, e.g. `12/66`. The colour sits on the numeral only: no underline or rule marks the current page. An 8 px chevron (the official SVG) sits 12 px left of the number as a forward-flow tick.
- Dividers, cover, and closing additionally carry the **PIF emblem** (separated from the AZMX mark by a neutral `border/subtle` hairline).
- The footer mark + page number are omitted **only on the cover.**

### 5.6 Slide-grid placement formula

Slides live on the `Playground` page, laid out in a 6-wide grid of 1920×1080 frames:

```
x = ((n − 1) % 6) * 2040
y = floor((n − 1) / 6) * 1200
```

(2040 = 1920 frame + 120 gutter; 1200 = 1080 frame + 120 gutter.)

### 5.7 Decorative kit (the whole kit)

Decoration is exactly three things: **chevron + gradient + neutral hairline.**

- **Hairlines (v3.0.0):** 1 px, the `border/subtle` token only — Neutral 200 `#E5E7EB` on light, white at 20 % on dark. Use them only where structure needs them: table rows, field outlines, a box's frame.
- **No coloured lines, ever.** No active rule, underline, side line, top bar or quote bar, in any colour, on any surface. Selected or important items are filled shapes: pills, tinted panels, a black active pill.
- **Flat by default.** Cards never take shadows. Only floating layers (menus, popovers, dialogs) take the design system's soft `shadow-menu` or `shadow-overlay`, and only the navigation takes the black glass (35 %, 30 px blur). No glows, no gradient-on-everything, no geometric scatter.
- Phosphor icons are permitted once confirmed with the user — see `icons.md`.

---

## 6. RTL (Right-to-Left) Implementation

**Arabic RTL rules for web templates (HTML, CSS, React).**

AZMX is a bilingual brand serving Arabic-speaking markets. Every web surface, component, and layout MUST support RTL (right-to-left) reading direction. These rules are non-negotiable and extracted from the production newsletter and email design system — they apply equally to web templates, landing pages, React components, and any HTML-based surface.

### 6.1 The `dir` attribute (foundational)

**Rule:** Every RTL surface MUST set `dir="rtl"` on the root `<html>` element AND `lang="ar"` for Arabic content.

```html
<!-- ✅ CORRECT -->
<html dir="rtl" lang="ar">
```

**For React/JSX components:** set `dir="rtl"` on the outermost container when rendering Arabic content:

```jsx
// ✅ CORRECT
<div dir="rtl" className="content-wrapper">
  {/* Arabic content */}
</div>
```

**Why this matters:** The `dir` attribute controls text flow, alignment, and the browser's bidi (bidirectional text) algorithm. Without it, layouts break, text aligns incorrectly, and chevrons mirror in the wrong direction.

### 6.2 CSS logical properties (modern approach)

**Preferred:** Use CSS logical properties for margin, padding, and positioning so layouts automatically adapt to RTL without duplicate styles:

| Physical property | Logical equivalent | Notes |
|---|---|---|
| `margin-left` | `margin-inline-start` | Start = left in LTR, right in RTL |
| `margin-right` | `margin-inline-end` | End = right in LTR, left in RTL |
| `padding-left` | `padding-inline-start` | — |
| `padding-right` | `padding-inline-end` | — |
| `left` | `inset-inline-start` | For positioned elements |
| `right` | `inset-inline-end` | — |
| `text-align: left` | `text-align: start` | Honors reading direction |
| `text-align: right` | `text-align: end` | — |

**Example:**

```css
/* ❌ WRONG — requires duplicate RTL override */
.card {
  margin-left: 24px;
  text-align: left;
}

/* ✅ CORRECT — works in both LTR and RTL */
.card {
  margin-inline-start: 24px;
  text-align: start;
}
```

**Fallback:** If browser support is a concern (legacy IE11), use physical properties with explicit RTL overrides via `[dir="rtl"]` selectors. Modern browsers (Safari 12.1+, Chrome 69+, Firefox 41+) fully support logical properties.

### 6.3 Flexbox and Grid direction

**Flexbox:** `flex-direction: row` and `row-reverse` automatically respect `dir="rtl"`. Items flow **right-to-left** in RTL contexts without additional CSS.

```css
/* ✅ CORRECT — auto-adapts to RTL */
.nav {
  display: flex;
  flex-direction: row; /* right-to-left in RTL */
  gap: 16px;
}
```

**Grid:** Use logical keywords for `grid-template-columns` start/end placement:

```css
/* ✅ CORRECT */
.layout {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 32px;
}
/* First column is rightmost in RTL, leftmost in LTR — automatic */
```

**Named grid areas** and `grid-column: 1 / 2` work as expected: column 1 is the **start** column (right in RTL, left in LTR).

### 6.4 Margin and padding mirroring

**The principle:** Asymmetric spacing (e.g. more space on one side of a card) MUST mirror in RTL layouts so the visual weight stays on the reading-direction side.

| LTR | RTL |
|---|---|
| `padding: 24px 32px 24px 56px;` (extra left) | `padding: 24px 56px 24px 32px;` (extra right) |
| Icon + text with `margin-left: 12px` on text | Icon + text with `margin-right: 12px` on text |

**With logical properties (preferred):**

```css
.card {
  padding-block: 24px; /* top/bottom, same in both */
  padding-inline-start: 56px; /* reading-start side */
  padding-inline-end: 32px; /* reading-end side */
}
/* Automatically: 56px left in LTR, 56px right in RTL */
```

**With physical properties (fallback):**

```css
.card {
  padding: 24px 32px 24px 56px; /* LTR: extra left */
}
[dir="rtl"] .card {
  padding: 24px 56px 24px 32px; /* RTL: extra right */
}
```

**Icon positioning:** Icons that lead or trail text MUST swap sides:

```css
/* LTR: icon on left */
.button {
  display: flex;
  gap: 8px;
}
.button-icon { order: 0; }
.button-text { order: 1; }

/* RTL: icon on right — automatic with flex+dir */
/* No override needed if using natural DOM order + flex */
```

### 6.5 Chevron positioning in RTL layouts

**The AZMX chevron is the only recurring graphic device** (§4). In RTL contexts, chevron direction MUST honor the reading flow.

> **v3.0.0:** on the web and in documents the chevron is the official SVG (41 : 58) used as a mask over a colour fill. Use `azmx-chevron-left.svg` in RTL and `azmx-chevron-right.svg` in LTR. Pick the matching file; don't flip one file with `scaleX(-1)`.
>
> ```css
> .chevron {
>   display: inline-block;
>   width: calc(1em * 41 / 58);   /* true ratio 41 : 58, never stretched */
>   height: 1em;
>   background-color: currentColor; /* any colour */
>   -webkit-mask: url("assets/chevron/azmx-chevron-left.svg") center / contain no-repeat;
>           mask: url("assets/chevron/azmx-chevron-left.svg") center / contain no-repeat;
> }
> ```
>
> The typed `‹` and `›` glyphs below are a fallback for places a mask can't run, such as email clients and plain text. Whether emails should move to images of the official chevron is still open.

#### 6.5.1 Chevron direction rule

- **In LTR:** Chevrons point **RIGHT** (`›` U+203A / `&#8250;`) to indicate forward motion.
- **In RTL:** Chevrons point **LEFT** (`‹` U+2039 / `&#8249;`) to indicate forward motion **in Arabic reading direction**.

**Critical:** The left-pointing single chevron `‹` is the CORRECT character for RTL. Do NOT use the right-pointing chevron mirrored via CSS `transform: scaleX(-1)` — this produces a brand defect (wrong optical weight).

#### 6.5.2 Bidi isolation for chevrons

**Problem:** The Unicode bidi algorithm can mirror isolated punctuation when it appears in RTL text. A bare `‹` in an RTL paragraph may render as `›`.

**Solution:** Wrap every chevron in a **bidi isolation span** to prevent mirroring:

```html
<!-- ✅ CORRECT — chevron isolated -->
<span dir="ltr">‹</span>
```

**In React/JSX:**

```jsx
// ✅ CORRECT
<span dir="ltr">‹</span>
```

**Full pattern** (chevron trio with tracking):

```html
<!-- LTR -->
<span style="letter-spacing: 4px;">›››</span>

<!-- RTL -->
<span dir="ltr" style="letter-spacing: 4px;">‹‹‹</span>
```

**Why `dir="ltr"` on the chevron?** It creates a bidi isolation boundary that locks the character direction, preventing the browser from mirroring it based on surrounding RTL context.

#### 6.5.3 Chevron in navigation / buttons

- **Next/Forward button in LTR:** label + chevron-right `›`
- **Next/Forward button in RTL:** chevron-left `‹` + label (order also swaps)

```jsx
// ✅ CORRECT — adapts to dir
<button className="next-btn" dir="rtl">
  <span dir="ltr">‹</span>
  <span>التالي</span>
</button>
```

**Spacing:** Maintain the 4–6px `letter-spacing` on chevron trios in both directions (§A1 email rule, applies equally to web).

### 6.6 Latin and numeric fragments in RTL text

**Rule:** Every Latin word, English name, URL, numeral, or date MUST be wrapped in `<span dir="ltr">` when embedded in RTL Arabic text.

**Why:** Without this, the bidi algorithm may reorder Latin characters incorrectly, or place punctuation on the wrong side of a number.

**Examples:**

```html
<!-- ✅ CORRECT -->
<p dir="rtl">
  تم التحديث في <span dir="ltr">13 July 2026</span>
</p>

<p dir="rtl">
  زيارة <span dir="ltr">www.azmx.sa</span>
</p>

<p dir="rtl">
  النتيجة: <span dir="ltr">95%</span>
</p>
```

**In React/JSX with dynamic content:**

```jsx
// ✅ CORRECT
<p dir="rtl">
  النتيجة: <span dir="ltr">{percentage}%</span>
</p>
```

**Numerals alone:** Even standalone Arabic-Indic numerals (٠–٩) vs. Western numerals (0–9) should be wrapped if they are Western, as some browsers may render them inconsistently in RTL without explicit direction.

### 6.7 Text alignment

**Default for RTL surfaces:**

```css
/* ✅ CORRECT */
[dir="rtl"] {
  text-align: right; /* or text-align: start */
}
```

**Use logical `start` / `end`** when possible:

```css
.content {
  text-align: start; /* right in RTL, left in LTR */
}
```

**Exception:** Centred content (cover titles, closing, full-width heroes) stays `text-align: center` in both directions.

### 6.8 Tailwind CSS RTL support

If using **Tailwind CSS**, enable RTL via the `dir` plugin or use Tailwind's built-in logical property utilities (v3.3+):

```js
// tailwind.config.js
module.exports = {
  plugins: [
    require('tailwindcss-rtl'),
  ],
}
```

**Logical utilities (Tailwind 3.3+):**

```jsx
// ✅ CORRECT — auto-adapts
<div className="ms-6 me-4"> {/* margin-inline-start: 24px, margin-inline-end: 16px */}
  <p className="text-start">content</p>
</div>
```

**RTL-specific overrides:**

```jsx
<div className="ml-6 rtl:mr-6 rtl:ml-0">
  {/* LTR: margin-left 24px; RTL: margin-right 24px, margin-left 0 */}
</div>
```

### 6.9 Kashida and letter-spacing

**Critical rule from §A1:** `letter-spacing` is **never** set on Arabic text. Arabic uses kashida (tatweel) for stretching, not character tracking.

```css
/* ❌ WRONG */
[dir="rtl"] h1 {
  letter-spacing: 2px; /* breaks Arabic typography */
}

/* ✅ CORRECT */
h1 {
  letter-spacing: 0; /* default for Arabic */
}

/* ✅ CORRECT — tracking only on Latin/chevrons */
.chevron-trio {
  letter-spacing: 4px; /* chevrons are Latin punctuation */
}
```

**Kashida-stretched wordmarks** (e.g. «وش صـــار؟») are **copy-pasted verbatim, never retyped**. The stretched forms are designed glyphs, not dynamically generated.

### 6.10 Testing RTL layouts

**Checklist before shipping any RTL web surface:**

1. **Visual inspection at 360 / 375 / 430 / 768 / 1440 px widths** — no horizontal overflow, no clipped content.
2. **Chevron direction sweep** — every chevron points LEFT (`‹`) in RTL, none mirrored to `›`.
3. **Latin/numeric fragments** — dates, URLs, percentages, English names all wrapped in `<span dir="ltr">`.
4. **Asymmetric spacing** — cards with more weight on one side correctly mirror (reading-start gets the emphasis).
5. **Icon positions** — leading icons move to the right in RTL, trailing icons to the left.
6. **Text alignment** — body text aligns right (or `start`), centred elements stay centred.
7. **No letter-spacing on Arabic text** — tracking only on chevrons and Latin fragments.

**Browser testing:** Safari (iOS + macOS), Chrome, Firefox. **Device testing:** iPhone 13/14/15 (375–430 px), iPad (768 px), desktop (1440 px).

### 6.11 Common RTL mistakes to avoid

| Mistake | Consequence | Fix |
|---|---|---|
| Omitting `dir="rtl"` on root or container | Text aligns left, layout breaks | Always set `dir="rtl"` on `<html>` or outermost container |
| Using `margin-left` / `margin-right` without logical properties | Asymmetric spacing doesn't mirror | Use `margin-inline-start` / `margin-inline-end` |
| Bare chevrons without `dir="ltr"` wrapper | Chevrons mirror to wrong direction (`›` instead of `‹`) | Wrap every chevron in `<span dir="ltr">‹</span>` |
| Unwrapped Latin/numeric fragments | Bidi reordering breaks readability | Wrap in `<span dir="ltr">` |
| `letter-spacing` on Arabic text | Destroys Arabic typographic rhythm | Never set tracking on Arabic; only on Latin/chevrons |
| Testing only in browser DevTools, not real devices | False clipping artifacts, missed overflow | Always test on real iOS/Android devices |

---

## 7. Components

Built on **Atoms → Molecules → Templates.** Token rule: every fill binds to a `Colors` variable, every font-family to a `Fonts` variable, every weight to a `font-weights/*` variable. No raw hex, no raw style strings inside components. Property-type legend: **T** = TEXT, **B** = BOOLEAN, **S** = INSTANCE_SWAP, **V** = VARIANT. "AL" = uses auto-layout internally.

Auto-layout policy in one sentence: **auto-layout owns the flow of editable content (rows, cards, tags, lists, tables, stat strips); absolute positioning owns the composition, the bleed, and the photo mask.** A single template legitimately mixes both.

### 6.1 Atoms

| Component | Purpose | Properties | Variants | AL | Used by |
|---|---|---|---|---|---|
| **Chevron-Tick** (A1) | The bullet / tick primitive; wraps the official chevron SVG as a mask over a colour fill (v3.0.0) | `Color` V, `Size` V | Color {Electric \| LightBlue \| White}; Size {12 \| 24 \| 48} | N | Every list bullet, page-number tick, section accent, connectors |
| **Eyebrow** (A2) | Header label in `label-lg`: Azm X Medium 14 px, accent colour, case as written, no tracking (v3.0.0) | `Label` T, `Surface` V | Surface {Light \| Dark} | Y | Header of every content slide, card eyebrows, cover |
| **Page-Number** (A3) | Footer page indicator | `Current` T, `Total` T, `Surface` V | Surface {Light \| Dark} | Y | Footer of slides 2–66 |
| **Brand-Numeral** (A4) | Serif section / card numeral | `Value` T, `Color` V, `Scale` V | Color {Electric \| LightBlue}; Scale {64 \| 96 \| 120} | N | TOC rows, exec cards, values, points lists, plan, divider numeral |
| **Hairline** (A5) | Neutral row / table rule, `border/subtle` only | `Surface` V | Surface {Light \| Dark}. The `Active-2` weight is retired (v3.0.0: no coloured lines) | N (FILL width) | Row dividers, table rules, footer separator. Not under eyebrows |
| **Stat-Figure** (A6) | Serif figure + sans suffix on one baseline | `Figure` T, `Suffix` T, `Color` V | Color {Electric \| LightBlue} | Y | Stat-Block, capability strip, case-study outcome, bio years |
| **RAG-Dot** (A7) | 10 px categorical risk dot | `Status` V | {High-Red \| Med-Yellow \| Low-Green} | N | Risks table (65) |
| **Logo-Cell** (A8) | Optically-centred logo holder | `Logo` S, `Surface` V | Surface {Light \| Blue50 \| Dark} | Y | Logo walls (20, 22), bio client logos, partnership logo |

> A1 wraps the official chevron (v3.0.0). Cover chevrons are the same official shape with a White fill, placed absolutely as compositional art. The old `Arrow Shape` Filled / Stroked / White-outline instances and the stroked arc chevrons are retired; replace them when you touch a slide.

### 6.2 Molecules

| Component | Purpose | Properties | AL | Used by |
|---|---|---|---|---|
| **Content-Header** (M1) | Top-left header block | `Eyebrow` T, `Title` T, `Surface` V, `Underline` B (retired v3.0.0: keep it off) | Y (VERTICAL) | Every content slide header |
| **Footer** (M2) | Footer band, logo + page number | `Page-Current` T, `Page-Total` T, `Surface` V, `Show-PIF` B | Y (HORIZONTAL, space-between) | Slides 2–66 |
| **Image-Placeholder** (M3) | Grey chevron-masked image stand-in | `Caption` T, `Sublabel` T, `Masked` B | Y label over absolute mask | Methodology (5–8), illustration (61), image stand-ins |
| **Stat-Block** (M4) | Figure + suffix + label | `Figure` T, `Suffix` T, `Label` T, `Color` V | Y (VERTICAL) | Capability strips (48, 49), case-study outcome, banner cells |
| **Numbered-Card** (M5) | Top-rule + numeral + title + body. The top rule is a neutral `border/subtle` hairline, never a coloured bar | `Number` T, `Title` T, `Body` T, `Surface` V, `Top-Rule` B | Y (VERTICAL) | Exec (3), values (10), plan (58), points lists (62, 64) |
| **Bio-Card** (M6) | Full-page bio | `Role` T, `Name` T, `Bio` T, `Years` T, `Surface` V, `Logos` B | Y text col + absolute portrait | Full-page bios (12–18) |
| **Team-Tile** (M7) | Grid person tile | `Portrait` S, `Name` T, `Role` T, `Hero` B | Y (VERTICAL) | Team grid (19); `Hero` scales cell 1.15× (CEO) |
| **Quote-Block** (M8) | Testimonial pull-quote | `Quote` T, `Name` T, `Title` T, `Surface` V | Y text + absolute glyph/portrait | Testimonials (27–30) |
| **Table-Row** (M9) | Data table row | `C1`–`C5` T, `Variant` V, `Has-RAG` B, `RAG` S | Y (HORIZONTAL) | Tables (51–53, 65) |
| **JD-Card** (M10) | Job description panel | `Role` T, `Seniority` T, `Items` (list slot) | Y (VERTICAL) | Job descriptions (55–57) |
| **Process-Step** (M11) | Stepped meeting card | `Cadence` T, `Title` T, `Attendees` T, `Step-Index` V | Y (VERTICAL) | Meetings (61); `Step-Index` sets +40 px staircase offset |
| **Case-Study** (M12) | Case study layout | `Eyebrow`, `Title`, `Body` T; `Tags` slot; `Stat-Figure`, `Stat-Label` T; `Device` S | Y left col + absolute right panel | Case studies (32–46) |
| **List** (M13) | Chevron-bullet list container | `Item-N` T per row | Y (VERTICAL) | Capability lists, JD responsibilities, steering bullets |
| **List-Item** (M13a) | One bullet row | `Text` T, `Surface` V | Y (HORIZONTAL) | Inside any List |
| **Method-Split** (M14) | Text + masked image split | `Eyebrow`, `Title`, `Lead`, `Image-Caption`, `Sublabel` T | Y text + absolute image | Methodology (5–8) |
| **Org-Node** (M15) | Org-chart label block | `Name` T, `Role` T, `Pivot` B | Y (VERTICAL) | Org chart (54); `Pivot` fills the node with a tinted panel (Blue-50 on light). The old 2 px Electric left rule is retired (v3.0.0) |
| **Tag-Chip** (M16) | Case-study method tag | `Label` T, `Surface` V | Y (HORIZONTAL) | Case-study method tags (in a HORIZONTAL+WRAP Tag-Row) |

**Asymmetry inside auto-layout (intentional, do not "fix"):**
- **Values columns** (10) are staggered 40 / 0 / 40 px via per-card *top padding*, not itemSpacing. The shared numeral hairline is a separate absolute Hairline.
- **Card counter-axis is HUG** so each card is exactly as tall as its copy — never equal height.
- **Points lists** (62, 64) are a 2-column GRID of Numbered-Cards (colGap 64, rowGap 40).

### 6.3 Templates (slide-level)

Templates are 1920×1080 component frames carrying the surface fill, the Footer instance, and absolute compositional art, exposing only copy as properties. Built only where ≥3 slides share a composition.

| Template | Properties (forwarded) | Covers |
|---|---|---|
| **Divider** (T1) | `Section`, `Word`, `Sub`, `Page` | Slides 4, 9, 21, 31, 47, 50, 59, 60, 63 (9×) |
| **Slide-Light** (T2) | `Header.Eyebrow`, `Header.Title`, `Page-Current` | Base for white content slides |
| **Slide-Dark** (T3) | as T2 + `Show-PIF` (default false) | Capability (48, 49), bios, testimonials |
| **Case-Study** (T4) | as M12 | 32–46 (15×) |
| **Bio** (T5) | as M6 | 12–18 (7×) |

> **Cover (1)** and **Closing (66)** are one-off absolute compositions — **not** componentised. They are unique paintings; a component adds overhead with zero reuse.

### 6.4 Built component registry (Figma node IDs)

These are the components actually built and live in the file, on the **`Proposal Components`** page. Reference by node ID (page-name-independent).

| Component | Node ID | Property keys |
|---|---|---|
| Divider | `72:7134` | Section `#72:0`, Word `#72:1`, Sub `#72:2`, Page `#72:3` |
| Footer / Light | `72:9960` | Page `#72:4` |
| Footer / Dark | `72:9981` | Page `#72:5` (includes PIF; hide `left.children[1..]` to drop PIF) |
| Content-Header | `72:10088` | Eyebrow `#72:6`, Title `#72:7` |
| TOC-Row | `72:10093` | Numeral `#72:8`, Title `#72:9`, PageRef `#72:10` |
| Bio | `72:10156` | Role `#72:11`, Name `#72:12`, Bio `#72:13`, Years `#72:14`, Page `#72:15` |
| Team-Tile | `72:15428` | Name `#72:18`, Role `#72:19` |

**Brand assets:**

| Asset | Node ID(s) | Notes |
|---|---|---|
| PIF Logo (COMPONENT_SET) | `72:3613` | Default `72:2545`, **White `72:3614`** (use white on dark) |
| Logo with Hamaa (AZMX) | White `2:116`, Navy `2:132`, Colored `2:37` | Variants: Colored / Navy Dark / White |
| Arrow Shape (chevron) | Filled `2:106`, Stroked `2:244`, White-outline `2:248` | **Retired (v3.0.0).** These are the drawn 1 : 1.3 caret. Use the official chevron SVG (`assets/chevron/`, 41 : 58) as a mask over a colour fill instead |

---

## 8. Slide Archetypes / Patterns

The deck composes from ~21 reusable archetypes. Each lists its surface and a one-line "when to use."

| # | Archetype | Surface | When to use |
|---|---|---|---|
| A | **Cover** | Gradient | The opening — hero display + stacked-motion chevrons + metadata row. One-off. |
| B | **Table of Contents** | White | Section index — serif brand numerals `01`–`06` on a 96 px rhythm. |
| C | **Section Divider** | Gradient | Open a section — big serif title, section numeral, one chevron tick. (The concentric arcs are retired.) |
| D | **Two-card Exec Summary** | White | Two parallel points — neutral top hairline + numeral + title + body, no boxes. |
| E | **Methodology Split + placeholder** | White (7/5) | A phase with a (client-supplied) image — text left, masked grey image right. |
| F | **3-column Values** | White | Three values side by side — staggered numbered columns. |
| G | **About intro + image** | White (5/7) | Company story — text + chevron-masked group photo + a serif pull-phrase. |
| H | **Full-page Bio** | Black | A leader — masked duotone portrait right third + giant "NN+ years" stat. |
| I | **Team Grid** | White | The whole team — 4×3 duotone tiles with chevron-notch corners; CEO at 1.15×. |
| J | **Logo Wall** | White / Blue-50 | Clients or qualifications — monochrome logos at equal *visual* mass. |
| K | **Partnership** | Black + photo | A partner — full-bleed chevron-cropped photo + text panel + partner logo. |
| L | **Testimonial** | Black or gradient | A quote — serif pull-quote + giant quote-mark glyph + attributor. No quote bar. Layouts A (flat black) / B (gradient). |
| M | **Case Study** | White + gradient panel | A project — text left, gradient feature panel with device mockup right. |
| N | **Dark Capability** | Black | A product (Anatomi / Colab) — value-prop + 4-stat strip + chevron-bullet lists. |
| O | **Data Table** | White | Tabular data — banner stat row + zebra rows, horizontal hairlines only, RAG dots. |
| P | **Org Chart** | White | Reporting structure — label nodes joined by chevron-tipped connectors. |
| Q | **Two-up Job Descriptions** | White | Two roles per slide — split panels, chevron-bullet responsibilities. |
| R | **Two-col Proposed Plan** | Blue-50 | A promise + two supporting columns + a spanning serif pull-line. |
| S | **Stepped Meetings + illustration** | White | Escalating cadence — three ascending stepped cards + chevron links. |
| T | **Points List** | White | Numbered points (steering, risks) — 2-column list with oversized hanging numerals. |
| U | **Closing "Love"** | Gradient | The release — the deck's only fully-centred composition. One-off. |

---

## 9. Implementation Notes (Figma)

### 9.1 How the system is encoded

- **File:** *New Direction Library*, fileKey `j8ugBpb1yUUyL8hfb6FHKR` — a Figma **design** file (not Slides). Slides live on the **`Playground`** page; components live on the **`Proposal Components`** page (renamed from `◆ Components`).
- **Every fill** is bound to a `Colors` variable. No raw hex inside components.
- **Every font family** is bound to `Fonts` Display (`1:980`) / Body (`1:979`).
- **Every font weight** is bound to a `font-weights/*` variable.

### 9.2 The font-weight PascalCase mapping (critical)

Figma's `fontName.style` requires the *installed* PascalCase style name. The `font-weights/*` variable **values** were therefore remapped from lowercase to the exact installed style strings, so `fontStyle` can bind to the variable and stay live:

| Variable | Old value | → New value |
|---|---|---|
| thin / extralight | "thin" / "extralight" | **ExtraLight** |
| light | "light" | **Light** |
| regular | "regular" | **Regular** |
| medium | "medium" | **Medium** |
| semibold | "semibold" | **SemiBold** |
| bold | "bold" | **Bold** |
| black | "black" | **Black** |

Rules:
- Only bind a weight var to a family that actually has that installed style — **serif (thmanyah):** Regular / Light / Medium / Bold / Black; **sans (Azm X Variable):** ExtraLight / Light / Regular / Medium / SemiBold / Bold / Black. Never cross a family with the other's style.
- `thin` maps to `ExtraLight` (Azm X has no separate Thin).
- Drive the mapping from `listAvailableFontsAsync()` output — never hand-type a style name (a "Semibold" vs "SemiBold" typo silently falls back to Regular).
- Before assigning any `fontName`, `await figma.loadFontAsync({ family, style })` with the **resolved** PascalCase value. Binding `fontStyle` to a variable does **not** auto-load the font.

### 9.3 Key engineering gotchas

- **Auto-layout `resize()` collapse.** Calling `resize()` on an auto-layout frame flips its sizing mode AUTO→FIXED, collapsing / clipping it. **Fix:** append all children first, **then** set `primaryAxisSizingMode` / `counterAxisSizingMode` **last.**
- **Bound-paint black fallback.** The bound-paint helper uses a **black** base color; if a variable binding fails to render, text shows BLACK. For white-on-dark text, give the paint a **WHITE** base. (This bit the testimonial quotes.)
- **No italics.** `thmanyah serif display` has **no** italic style; express emphasis via scale / weight / color only. Do not attempt to bind italic through `font-weights/*` — italic is a style, not a weight.
- **Page-number layers** are all named `page number` (one per slide, 2–66). Screenshot node IDs are session-stable but re-query by slide name if unsure (`pg.children.find(c => c.name.startsWith('NN '))`).

### 9.4 Build order (bottom-up)

Tokens → atoms → molecules (atom-dependent) → composite molecules / templates → one-off compositions (cover, closing). Validate each tier by screenshot before proceeding; confirm no raw hex / raw style strings remain. The single highest-leverage retrofit is swapping every hand-placed logo + page number for one **Footer** instance across slides 2–66 — the craft-consistency win.

---

## 10. Changelog

| Version | Date | Notes |
|---|---|---|
| **1.0** | 2026-06-09 | Initial authoritative AZMX Design System handbook. Consolidated from `MASTER-BRIEF.md`, `art-direction.md`, `component-architecture.md`, `SESSION-HANDOFF.md`, and the `azmx-brand-system` memory. Reflects the as-built state: 66 slides, fully tokenized, no-italics confirmed. |
| **1.1** | 2026-07-20 | Chevron background uses retired by owner decision: no oversized bleed ghosts (former use 2), no concentric arc backdrops (former use 4), no chevron art behind content. Functional chevron uses (photo mask, stacked-motion hero, tick, bullet) unchanged. |
| **skill v3.0.0** | 2026-10-27 | The AZM X Design System becomes the source for every deliverable. Rulings applied in place: black dark grounds, Neutral 900 headings, black-start gradient, the site spacing scale, the design system's radius names, `label-lg` eyebrows, the official chevron SVG only, no coloured lines, neutral `border/subtle` hairlines, flat cards, no tracking on labels. See the amendment at the top and `design-system-link.md`. |

---

*AZMX Design System v1.0 — "Restraint is the luxury."*
