# AZMX Email Design System — Master Guideline (v1)

> **v3.0.0 amendment (27 Oct 2026).** The AZM X Design System is now the source for every AZM X deliverable, emails included. Read [`design-system-link.md`](design-system-link.md). There is **one email system, in the design system, with two designs**:
>
> - **Public emails** (website and marketing: confirmations, welcome and thank-you emails, campaigns) use the design system's email look: white cards, black buttons, the compact black footer card. Build them from the design system, not from this document.
> - **The internal newsletter** keeps its own design. This document and its two templates describe it. They are the starting point for a new newsletter design that comes later, with every ruling below already applied.
> - For a report or an announcement, the audience decides: public goes to the design system, internal stays here. Ask if it is unclear.
>
> What the rulings change here:
>
> - `{dark}` is pure black `#000000` in every theme: hero fallback, dark cards, footer. Navy `#040038` is no longer a ground.
> - Headings on light use `{text}` Neutral 900 `#111927`, not `{dark}`.
> - The C02 hero gradient starts at black: `#000000` → `{deep}` `#01006E` at 55 % → `{primary}`, 145°.
> - **No coloured lines.** The C14 quote bar, the 4 px top border on the C09 feature card, the gold top bar on C12, the outlined C07 badge, the tinted outline on the C16 calendar button and the C18-B gradient bar are gone. Emphasis is a filled shape: a tinted panel or a pill.
> - Hairlines are neutral `border/subtle`: `#E5E7EB` on light, white at 20 % on dark (`rgba(255,255,255,0.2)`; a client that drops `rgba` just shows no line, which is fine).
> - Flat: no shadow on the sheet, cards, buttons or the play button.
> - Eyebrows are `label-lg`: 14 px, weight 500, in the accent colour, case as written, no uppercase, no tracking.
> - Spacing: new work uses the design system's site scale (0, 2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 120, 160, 200) and radius names (xs 4, sm 8, md 12, lg 16, xl 24, full). The current newsletter markup still has some paddings and two radii (20 and 14) that are off the scale. The new newsletter design brings them onto it.
> - Fonts: Azm X v3 (3.007) when it's available, otherwise 2.004. thmanyah serif display is unchanged.
> - Chevrons: email clients can't apply a CSS mask, so these templates keep the typed `‹` glyph for now. Whether to replace it with images of the official chevron SVG is still open.

The generic design system for AZMX HTML emails: monthly newsletters, periodic
reports, annual reports, and announcements. Since v3.0.0 it is the internal newsletter's
design; public emails use the AZM X Design System (see the box above). Every rule and component here is **extracted
from the shipped production newsletter** — `Newsletter/June/AZMX-Newsletter-June-EMAIL.html`
— which remains the applied reference implementation.

Client's framing: *"same elements and direction as the current newsletter guideline, but
generic, with color theming."*

**Relationship to the newsletter docs** (`../Newsletter/docs/`): this system outranks them
in scope (it governs every email type); they outrank it in newsletter specifics. For the
newsletter's exact monthly slots, image specs, and QA flow, use:
`../Newsletter/docs/README.md` (`../Newsletter/docs/README.md` — in the separate AZMX Newsletter project, not shipped with this skill) ·
`../Newsletter/docs/monthly-issue-guide.md` (`monthly-issue-guide.md` — in the separate AZMX Newsletter project, not shipped with this skill) ·
`../Newsletter/docs/design-reference.md` (`design-reference.md` — in the separate AZMX Newsletter project, not shipped with this skill) ·
`../Newsletter/docs/technical-reference.md` (`technical-reference.md` — in the separate AZMX Newsletter project, not shipped with this skill) ·
`../Newsletter/docs/qa-checklist.md` (`qa-checklist.md` — in the separate AZMX Newsletter project, not shipped with this skill) ·
`../Newsletter/docs/template/ISSUE-TEMPLATE-REPORT.md` (`template/ISSUE-TEMPLATE-REPORT.md` — in the separate AZMX Newsletter project, not shipped with this skill).

Companion files in this folder:

- `starter-skeleton.html` (`starter-skeleton.html` — in the AZMX Newsletter project) — blank ready-to-fill email (default blue theme)
- `component-showcase.html` (`component-showcase.html` — in the AZMX Newsletter project) — every component rendered once, real copy-paste markup

**Snippet shorthand used in this document** (the HTML companions carry the real values):

- `[SANS]` = `'Azm X', 'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Tahoma, Arial, sans-serif`
- `[SERIF]` = `'Thmanyah Serif Display', 'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Tahoma, Arial, sans-serif`
- `{token}` = a theme color token (§B) — in real files this is a literal hex

---

## A. FOUNDATIONS — fixed for every email, theme-independent

### A1. Arabic RTL rules (non-negotiable)

1. `<html dir="rtl" lang="ar">`, and **`dir="rtl"` on every `<table>` AND every `<td>`**
   (Gmail drops it from parents; per-cell is the only reliable carrier).
2. **Chevrons always point LEFT** (`‹` U+2039 / `&#8249;`) and always live inside
   `<span dir="ltr">` — otherwise the bidi algorithm mirrors them to `›`, a brand defect.
3. **Every Latin/numeric fragment** (numerals `01`, dates `13 July`, years `2026`, English
   names/URLs) sits in `<span dir="ltr">`.
4. **`letter-spacing` is never set on Arabic text** (kashida does the stretching; tracking
   is only used on the LTR chevron trio: 4–6px).
5. Kashida-stretched wordmarks (e.g. «وش صـــار؟») are **copy-pasted, never retyped**.
6. `text-align:right` inline on every RTL text cell; `align="right"` attribute as backup.

### A2. The 3-layer font system (verbatim from the newsletter)

**Voice rule: serif = personality** (heros, section titles, quotes) · **sans = information**
(body, pills, buttons, meta).

**Layer 1 — brand webfonts** (`@font-face` in `<style>`; render in Spark/Apple Mail/browser
preview; Gmail strips them — never load-bearing):

```css
@font-face { font-family:'Thmanyah Serif Display'; src:url('https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@9777d04/serif-regular.woff2') format('woff2'); font-weight:400; font-display:swap; }
@font-face { font-family:'Thmanyah Serif Display'; src:url('https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@9777d04/serif-medium.woff2') format('woff2'); font-weight:500; font-display:swap; }
@font-face { font-family:'Thmanyah Serif Display'; src:url('https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@9777d04/serif-bold.woff2') format('woff2'); font-weight:700; font-display:swap; }
@font-face { font-family:'Azm X'; src:url('https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@9777d04/sans-regular.woff2') format('woff2'); font-weight:400; font-display:swap; }
@font-face { font-family:'Azm X'; src:url('https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@9777d04/sans-medium.woff2') format('woff2'); font-weight:500; font-display:swap; }
@font-face { font-family:'Azm X'; src:url('https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@9777d04/sans-semibold.woff2') format('woff2'); font-weight:600; font-display:swap; }
@font-face { font-family:'Azm X'; src:url('https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@9777d04/sans-bold.woff2') format('woff2'); font-weight:700; font-display:swap; }
```

**Layer 2 — Google Fonts** IBM Plex Sans Arabic (a `<link>` + `@import`) — first fallback
for clients that keep `<style>` but block the brand CDN.

**Layer 3 — full inline stack on EVERY text element** (the only layer Gmail sees):

```text
[SERIF] font-family:'Thmanyah Serif Display', 'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Tahoma, Arial, sans-serif;
[SANS]  font-family:'Azm X', 'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Tahoma, Arial, sans-serif;
```

Gmail always renders system fonts (SF Arabic / Segoe UI). **This is physics, not a bug —
do not attempt to "fix" it.**

Reference type scale (from the newsletter; scale roles carry to all email types):
hero 56/700 serif · section title 28/700 serif · big card title 27–30/700 serif ·
pull-quote 26/700 serif · body 17/400 lh 1.8 · secondary body 15–16/400 · meta/pills
11–14 sans · light display numerals 20/300.

### A3. Layout architecture

- `<center>` → full-width bg table (`{tint-page}`) → outer td padding `24px 32px` →
  **the white sheet**: `width:100%; max-width:640px; margin:0 auto; background:#FFFFFF;
  border-radius:24px`. No shadow (v3.0.0: flat by default).
- Everything inside is `role="presentation"` tables, `cellpadding/cellspacing/border=0`,
  `width:100%` + percentage sub-columns (fluid at any width even without media queries).
- Card sections: outer td `0 20px`, card radius **20px**. Plain sections: td `0 32px 8px 32px`.
- Vertical gaps via **spacer rows only** (never margins):
  `<tr><td dir="rtl" height="20" style="height:20px; font-size:13px; line-height:20px;">&nbsp;</td></tr>`

### A4. Spacing / radius / shadow conventions

| Element | Value |
|---|---|
| Sheet | radius 24px (xl) |
| Section cards / hero / dark features | radius **20px** (off the scale; waits for the new newsletter design), padding 28–56px × 24–28px |
| Media (photos, video box) | radius **16px** (lg); 12px (md) inside dark feature |
| Inner cards (rows, avatar cards, agenda) | radius **14px** (off the scale; waits for the new newsletter design) |
| Chips (emoji, digest) | radius **12px** (md) |
| Pills, buttons | radius **999px** (full) |
| Shadow | **None.** Cards, buttons and overlays are flat (v3.0.0) |
| Separator paddings | A: `32px 32px` · B: an 80px open-space spacer row |

### A5. Email-safety rules

1. **All styles inline.** `<style>` holds ONLY: `@font-face`, hover tints
   (`.hov-chip/.hov-agenda/.lnk-on-dark/.soc`), and the `@media` kit — cosmetic layers.
2. **HTML file < ~100 KB** (Gmail clips at 102 KB). Images live on the CDN
   (`Gamaleldientarek/azmx-brand-cdn` via jsDelivr, **pinned to immutable commit shas** —
   new image = new commit = new sha in the HTML).
3. Send via **Brevo → "Code your own" → paste raw HTML source**. The footer MUST contain
   `href="{{ unsubscribe }}"` (Brevo requirement).
4. Every link: `target="_blank" rel="noopener"`.
5. Background-image cells carry the URL **twice**: `background=""` attribute AND inline
   `background-image:`, always over a solid `bgcolor` fallback.
6. Images: photos = progressive JPEG q70–75 at 2× display width; transparency (designed
   cards, logos) = full-quality PNG at 2×. Pipeline:
   `../Newsletter/docs/template/IMAGE-SPECS.md` (`../Newsletter/docs/template/IMAGE-SPECS.md` — in the separate AZMX Newsletter project, not shipped with this skill).

### A6. The standard responsive kit (≤480px)

Extracted verbatim from the production newsletter — **this block ships in every AZMX
email** (honored by Gmail/Spark/Apple Mail when sent via ESP):

```css
@media only screen and (max-width:480px) {
  .rs-hero  { font-size:36px !important; line-height:1.25 !important; }
  .rs-sec   { font-size:22px !important; }
  .rs-big   { font-size:22px !important; }
  .rs-quote { font-size:20px !important; }
  .rs-ghost { font-size:52px !important; }
  .rs-col   { display:block !important; width:100% !important; padding:0 4px 8px 4px !important; }
  .rs-chip  { font-size:12px !important; padding-right:8px !important; }
  .rs-agd   { display:block !important; width:100% !important; padding:0 0 10px 0 !important; }
  .rs-agt   { display:block !important; width:100% !important; }
  .rs-ftlogo  { display:block !important; width:100% !important; text-align:center !important; }
  .rs-ftlogo img { margin:0 auto !important; }
  .rs-ftico   { display:block !important; width:100% !important; text-align:center !important; padding-top:16px !important; }
  .rs-ftmeta  { text-align:center !important; }
  .rs-ftmade  { display:block !important; width:100% !important; text-align:center !important; }
  .rs-ftunsub { display:block !important; width:100% !important; text-align:center !important; padding-top:12px !important; }
}
```

Class roles: `rs-hero/sec/big/quote/ghost` = type scaling · `rs-col` = 2-col→1-col grids ·
`rs-chip` = index-chip titles stay one line · `rs-agd`+`rs-agt` = pill-over-text stacking
for row cards · `rs-ft*` = footer stacks vertically fully centered. Full effect table:
`../Newsletter/docs/technical-reference.md` (`../Newsletter/docs/technical-reference.md` — in the separate AZMX Newsletter project, not shipped with this skill) §4.

### A7. QA

Before any send, run the newsletter QA flow —
`../Newsletter/docs/qa-checklist.md` (`../Newsletter/docs/qa-checklist.md` — in the separate AZMX Newsletter project, not shipped with this skill) — especially the
**iframe overflow harness at 360/375/430** (headless full-page screenshots of RTL pages show
a false right-edge clipping artifact; never trust them), chevron direction sweep, verbatim
Arabic copy check, size < 100 KB, and a real test-send to Gmail web + Gmail app + Apple
Mail/Spark.

---

## B. COLOR TOKENS & THEMING

### B1. Semantic tokens (roles) — DEFAULT THEME = the newsletter blues

| Token | Default (blue) | Role |
|---|---|---|
| `{dark}` | `#000000` | Dark surface: hero fallback, dark feature cards, footer. Black in every theme (v3.0.0); never a text colour |
| `{feature-black}` | `#000000` | The one "electric moment" surface. Same as `{dark}` since v3.0.0, with no top border |
| `{deep}` | `#01006E` | Middle stop of the C02 hero gradient (55 %); link hover in preview |
| `{primary}` | `#001AFF` | **Punctuation, never wallpaper**: pill text, numerals, date-pill fill, CTA text. Never a line or bar |
| `{accent-soft}` | `#5D8FFF` | Accent partner ON dark: eyebrows, chevrons, chip text on dark, footer meta |
| `{tint}` | `#F0F5FF` | Quiet light card fill, pills on white, emoji chips |
| `{tint-page}` | `#EDF2FB` | Page background behind the sheet |
| `{text}` | `#111927` | Body and headings on light (v3.0.0) |
| `{on-dark}` | `#DDE8FF` | Body text on dark surfaces |
| `{on-dark-meta}` | `#BFD5FF` | Secondary/meta text on dark |
| `{chip-on-dark}` | `#1A1553` | Pill/chip fill ON dark surfaces (also the C07 badge) |
| `{unsub}` | `#8FA3D8` | Unsubscribe link on dark |
| `{btn-bg}` | `#F8FAFF` | Small calendar-style button fill (its frame is the fixed `#E5E7EB` hairline) |

**Fixed neutrals (never themed):** `#FFFFFF` sheet/cards · `#E5E7EB` the `border/subtle`
hairline on light: separator A, borders, row dividers, the calendar button frame, image
placeholder · `rgba(255,255,255,0.2)` the hairline on black (white at 20 %) ·
`#6C737F` captions · `#9DA4AE` pipe `|` separators. There is no shadow token: emails are
flat (v3.0.0).

**Fixed semantics (never themed):** success pill `#E9F9F1` bg / `#22C36F` text («اكتمل»
pattern) · fun-award panel fill `#FFF9E4` (Yellow 100; it replaces the old gold top bar).

### B2. Theming rule

An email type MAY define its own theme by **swapping token VALUES while keeping every token
ROLE and contrast relationship**:

1. `{dark}` stays black `#000000` in every theme (v3.0.0). White + `{on-dark}` text must
   stay readable on it (WCAG AA at 17px).
2. `{primary}` stays **punctuation, not wallpaper** — small fills and text accents; never a
   large fill behind dense text, and never a line or bar.
3. `{tint}` stays quiet — barely-there fill that white cards can sit on.
4. `{accent-soft}` must read on `{dark}`; `{on-dark}`/`{on-dark-meta}` are lighter
   derivatives of the theme hue, not grey.
5. Neutrals and semantic green/gold never change.
6. The C02 hero gradient keeps its black start:
   `linear-gradient(145deg, #000000, {deep} 55%, {primary})`.

### B3. Worked example themes (token tables only — proof of system)

**Theme "Annual Report — deep green/gold":**

| Token | Value |
|---|---|
| `{dark}` / `{feature-black}` | `#000000` (fixed) |
| `{deep}` | `#06281C` |
| `{primary}` | `#0F7B4F` |
| `{accent-soft}` | `#D4AF37` |
| `{tint}` | `#EDF6F1` |
| `{tint-page}` | `#E6F0EA` |
| `{text}` | `#12211A` |
| `{on-dark}` | `#D7EFE3` |
| `{on-dark-meta}` | `#BFE3D2` |
| `{chip-on-dark}` | `#10402E` |
| `{unsub}` | `#8FC2A9` |
| `{btn-bg}` | `#F6FBF8` |

**Theme "Finance Report — graphite/teal":**

| Token | Value |
|---|---|
| `{dark}` / `{feature-black}` | `#000000` (fixed) |
| `{deep}` | `#14181D` |
| `{primary}` | `#0E7C86` |
| `{accent-soft}` | `#58C7CF` |
| `{tint}` | `#EEF5F6` |
| `{tint-page}` | `#E9EEF0` |
| `{text}` | `#161D21` |
| `{on-dark}` | `#D9E5E7` |
| `{on-dark-meta}` | `#B8CCCF` |
| `{chip-on-dark}` | `#232B31` |
| `{unsub}` | `#93A7AC` |
| `{btn-bg}` | `#F5FAFB` |

### B4. Applying a theme (inline styles ⇒ tokens are a find-replace map)

Emails use inline styles, so "theming" = replacing default hexes with the theme's hexes,
**case-insensitively, whole-hex only**, on a COPY of the skeleton. Example (green/gold):

```bash
python3 - <<'PY'
import re, pathlib
MAP = {  # default blue → Annual Report green/gold (black #000000 is never mapped)
 "#01006E":"#06281C", "#001AFF":"#0F7B4F", "#5D8FFF":"#D4AF37",
 "#F0F5FF":"#EDF6F1", "#EDF2FB":"#E6F0EA", "#111927":"#12211A", "#DDE8FF":"#D7EFE3",
 "#BFD5FF":"#BFE3D2", "#1A1553":"#10402E", "#8FA3D8":"#8FC2A9", "#F8FAFF":"#F6FBF8",
}
p = pathlib.Path("annual-report.html"); html = p.read_text(encoding="utf-8")
for old, new in MAP.items():
    html = re.sub(re.escape(old), new, html, flags=re.IGNORECASE)
p.write_text(html, encoding="utf-8"); print("themed:", p)
PY
```

Caveats: `#000000` (the dark ground), `#FFFFFF` and the neutral/semantic hexes
(`#E5E7EB`, `rgba(255,255,255,0.2)`, `#FFF9E4` and the rest) are NOT in the map by design; run the map **before** adding content so no content hex gets
caught; re-check contrast after swapping.

---

## C. COMPONENT LIBRARY

Every component below is extracted from the production newsletter — **never invent new
component HTML; copy from `component-showcase.html` (`component-showcase.html` — in the AZMX Newsletter project)** (real
default-theme markup) and re-theme via §B4. Snippets here use `[SANS]/[SERIF]/{token}`
shorthand. `[SLOT: …]` marks content that changes per email.

### C01 — Hero cover card (image background + overlaid title)

Use: the opening card of newsletters and reports when a strong cover photo exists.

```html
<td dir="rtl" align="right" bgcolor="{dark}" background="[SLOT: cover URL]"
    style="background-color:{dark}; background-image:url('[SLOT: cover URL]');
    background-size:cover; background-position:center; border-radius:20px;
    padding:56px 24px; text-align:right;">
  <!-- logo-white.png 94×28, margin:0 0 0 auto -->
  <!-- eyebrow (label-lg): [SANS] 14px/500 {accent-soft}, case as written, no tracking — [SLOT: email-type label] -->
  <!-- title td class="rs-hero": [SERIF] 56px/700 #FFFFFF lh1.15 — [SLOT: masthead] -->
  <!-- subtitle: [SANS] 16px/400 {on-dark} — [SLOT: month/period — tagline] -->
  <!-- chevron trio: <span dir="ltr"> [SERIF] 26px/700 {accent-soft} letter-spacing:4px -->
</td>
```

Theming: `{dark}` fallback, `{accent-soft}` eyebrow/chevrons, `{on-dark}` subtitle.
Mobile: `rs-hero` 56→36px. Cover: ~1200×510 JPEG, focal detail away from the text column.

### C02 — Typographic hero variant (gradient background, no photo)

Use: announcements/reports with no cover asset. Same inner anatomy as C01; the cell swaps
the image for the event gradient (v3.0.0: it starts at black) with a solid fallback:

```html
<td dir="rtl" align="right" bgcolor="{dark}"
    style="background-color:{dark}; background:linear-gradient(145deg, {dark} 0%, {deep} 55%, {primary} 100%);
    border-radius:20px; padding:56px 24px; text-align:right;">
```

(Gradient degrades to solid black `{dark}` in old Outlook — accepted.) Theming/mobile: as C01.

### C03 — Section header (numeral pill + emoji chip + title)

Use: opens every numbered section.

```html
<!-- kicker row -->
<span dir="ltr" style="display:inline-block; background-color:{tint}; color:{primary};
  [SANS] font-size:14px; font-weight:700; padding:6px 14px; border-radius:999px;">[SLOT: 01]</span>
<!-- header row: 14px gap between chip and title -->
<td dir="rtl" width="44" height="44" align="center" valign="middle" bgcolor="{tint}"
    style="width:44px; height:44px; background-color:{tint}; border-radius:12px;
    text-align:center; vertical-align:middle; font-size:22px; line-height:44px;">[SLOT: emoji]</td>
<td dir="rtl" align="right" valign="middle" class="rs-sec" style="padding:0 14px 0 0; text-align:right;
    [SERIF] font-size:28px; font-weight:700; color:{text}; line-height:1.4;">[SLOT: title]</td>
```

Surface inversions: on `{tint}` cards the pill/chip fill flips to `#FFFFFF`; on dark cards
to `{chip-on-dark}` with `{accent-soft}` text. **Flipped variant** (rhythm break, max once
per email): title first, 12px spacer td, then the chip — table `align="right"`, not 100%.
Mobile: `rs-sec` 28→22px.

### C04 — Digest / index chip grid (2-column)

Use: table of contents for newsletters and long reports (chapters). NOT clickable.

```html
<!-- {tint} card r20, no shadow, padding 20px 16px; badge pill «في هذا العدد» + [SERIF] 22px {text} title -->
<td dir="rtl" width="50%" valign="top" class="rs-col" style="width:50%; padding:0 4px 8px 6px; vertical-align:top;">
  <td dir="rtl" align="right" bgcolor="#FFFFFF" class="hov-chip"
      style="background-color:#FFFFFF; border-radius:12px; padding:9px 12px; text-align:right;">
    <span dir="ltr" style="display:inline-block; background-color:{tint}; color:{primary};
      [SANS] font-size:11px; font-weight:400; padding:3px 10px; border-radius:999px;">[SLOT: 01]</span>
    <span class="rs-chip" style="padding-right:10px; [SANS] font-size:14px; font-weight:400;
      color:{text}; line-height:1.5;">[SLOT: emoji + section title]</span>
  </td>
</td>
```

Chip titles MUST mirror section titles exactly (update as a pair). Gutter paddings
alternate `0 4px 8px 6px` / `0 6px 8px 4px` (last row bottom 0). Mobile: `rs-col` stacks
the grid; `rs-chip` keeps titles one line.

### C05 — Body text block

```html
<td dir="rtl" align="right" style="text-align:right; padding:18px 0 24px 0;
    [SANS] font-size:17px; font-weight:400; color:{text}; line-height:1.8;">[SLOT: body]</td>
```

On dark surfaces: color `{on-dark}`. Bold highlight: `<span style="font-weight:700;">`
(on dark add `color:#FFFFFF`). Small parenthetical caption:
`<span style="display:block; padding-top:6px; font-size:13px; color:#6C737F;">(…)</span>`.

### C06 — Full-width image card

```html
<td dir="rtl" align="center" style="border-radius:16px;">
  <img src="[SLOT: CDN URL]" width="100%" alt="[SLOT: alt]"
       style="display:block; width:100%; height:auto; border:0; border-radius:16px;">
</td>
```

Theming: none. Any ratio ~3:1 to 4:5; JPEG 2× display width. Wrap in
`<a … style="display:block;">` to make it clickable (see C09).

### C07 — Background-image card with overlay CTA (banner)

Use: launches, big announcements, report call-to-action moments. Everything centered.

```html
<td dir="rtl" align="center" bgcolor="{dark}" background="[SLOT: bg URL]"
    style="background-color:{dark}; background-image:url('[SLOT: bg URL]'); background-size:cover;
    background-position:center; border-radius:20px; padding:44px 28px; text-align:center;">
  <!-- badge: a filled pill, bg {chip-on-dark}, color {accent-soft}, 13px/700, no border (v3.0.0: no coloured outline) -->
  <!-- big emoji 44px → title class="rs-big" [SERIF] 27px/700 #FFFFFF → body 16px {on-dark} -->
  <!-- C17 primary button → sub-link 12px {accent-soft} with <span dir="ltr">URL</span> -->
</td>
```

Background must stay dark enough for white text at any crop. Mobile: `rs-big` 27→22px.

### C08 — Video box with play overlay

Use: any video link. **The whole box is the link** — no separate button outside it.

```html
<td dir="rtl" align="center" height="320" background="[SLOT: thumb URL]" bgcolor="#E5E7EB"
    style="background-color:#E5E7EB; background-image:url('[SLOT: thumb URL]'); background-size:cover;
    background-position:center; height:320px; border-radius:16px; text-align:center; vertical-align:middle;">
  <a href="[SLOT: video URL]" target="_blank" rel="noopener" style="display:block; text-decoration:none; padding:100px 0;">
    <span dir="ltr" style="display:inline-block; width:72px; height:72px; background-color:#FFFFFF;
      border-radius:50%; font-size:26px; line-height:72px;
      text-align:center; color:{primary};">&#9654;&#xFE0E;</span>
    <span style="display:block; padding-top:16px;"><span style="display:inline-block; background-color:#FFFFFF;
      color:{text}; [SANS] font-size:14px; font-weight:700; padding:8px 18px; border-radius:999px;">[SLOT: watch label]</span></span>
  </a>
</td>
```

Thumb: 16:9, center-safe. Theming: play glyph `{primary}`, label text `{text}`. No shadows
on the play button or label (v3.0.0); pick a thumb whose centre is dark or busy enough for
the white circle to read.

### C09 — Dark feature card (the "electric moment")

Use: THE one highlight per email — flagship achievement, headline KPI, annual-report
centerpiece. **Budgeted spectacle: max one per email.**

```html
<td dir="rtl" align="right" bgcolor="{feature-black}" style="background-color:{feature-black};
    border-radius:20px; padding:36px 24px; text-align:right;">
  <!-- no top border, no shadow (v3.0.0: no coloured lines, flat cards) -->
  <!-- header: eyebrow (label-lg) [SANS] 14px/500 {accent-soft} (right) + numeral chip 12px/700
       bg {chip-on-dark} color {accent-soft} in a 110px align-left td -->
  <!-- title class="rs-big": [SERIF] 30px/700 #FFFFFF -->
  <!-- body: 17px/400 {on-dark}; Latin names <span dir="ltr" style="font-weight:600; color:#FFFFFF"> -->
  <!-- link-wrapped full-width img, radius 12px (note: 12 on this surface, not 16) -->
  <!-- centered small arrow link (C17b) with class="lnk-on-dark" -->
</td>
```

Mobile: `rs-big`. Theming: all five dark-surface tokens.

### C10 — Item rows with side logos (project-row pattern)

Use: project lists, portfolio items, report line items with a partner mark.

```html
<td dir="rtl" align="right" bgcolor="{tint}" style="background-color:{tint}; border-radius:16px; padding:22px 20px; text-align:right;">
  <td dir="rtl" width="32" align="right" valign="middle" style="width:32px; padding:0 0 0 10px; text-align:right;">
    <span dir="ltr" style="[SANS] font-size:20px; font-weight:300; color:{primary}; line-height:1;">[SLOT: 01]</span></td>
  <td dir="rtl" align="right" valign="middle" style="text-align:right; [SANS] font-size:20px;
    font-weight:300; color:{text}; line-height:1.6;">[SLOT: item] <span style="color:#9DA4AE;">|</span> [SLOT: sub]</td>
  <td dir="rtl" width="[logo w + 6]" align="left" valign="middle" style="text-align:left; padding:0 6px 0 0;">
    <img src="[SLOT: logo PNG]" width="[w]" height="[h]" alt="[SLOT]" style="display:block; border:0; margin:0 auto 0 0;"></td>
</td>
```

Light 300 weight is the point — keep it. 20px spacer rows between cards. Logos: transparent
PNG at natural small size, explicit w/h + td width = logo width + 6.

### C11 — Status-pill rows («اكتمل» pattern)

Use: completed items, milestone lists, report status tables.

```html
<tr>
  <td dir="rtl" align="right" style="text-align:right; padding:22px 0 18px 0; [SANS] font-size:18px;
      font-weight:700; color:{text}; line-height:1.7;">[SLOT: item name]
    <span dir="ltr" style="display:block; padding-top:6px; font-size:13px; font-weight:400;
      color:#6C737F; text-align:right;">([SLOT: Latin sub-name])</span></td>
  <td dir="rtl" width="70" align="left" valign="top" style="width:70px; padding:22px 0 0 0; text-align:left;">
    <span style="display:inline-block; background-color:#E9F9F1; color:#22C36F; [SANS] font-size:13px;
      font-weight:700; padding:4px 12px; border-radius:999px;">[SLOT: status]</span></td>
</tr>
```

Rows 2+: `border-top:1px solid #E5E7EB` on both tds (a neutral structural hairline, the one
kind of line allowed), padding `18px 0` (last `18px 0 0 0`).
Status colors are fixed semantics (green = done); do not theme.

### C12 — Avatar card (44px circle + name row + full-width text row)

Use: people highlights — achievements, contributors, report credits.

```html
<td dir="rtl" align="right" bgcolor="#FFFFFF" style="background-color:#FFFFFF; border:1px solid #E5E7EB;
    border-radius:14px; padding:16px 18px; text-align:right;">
  <table …><tr><!-- ROW 1: avatar + name -->
    <td dir="rtl" width="44" align="right" valign="top" style="width:44px; padding:2px 0 0 12px;">
      <img src="[SLOT: avatar]" width="44" height="44" alt="[SLOT: name]"
           style="display:block; width:44px; height:44px; border-radius:50%; border:0;"></td>
    <td dir="rtl" align="right" valign="top"><span style="display:block; text-align:right; [SANS]
      font-size:18px; font-weight:700; color:{text}; line-height:1.5;">[SLOT: name]</span></td>
  </tr><tr><!-- ROW 2: full-width text -->
    <td dir="rtl" colspan="2" align="right" valign="top"><span style="display:block; text-align:right;
      padding-top:4px; [SANS] font-size:15px; font-weight:400; color:{text}; line-height:1.8;">[SLOT: text]</span></td>
  </tr></table>
</td>
```

Variant: gold "fun" card swaps the white fill and frame for a Yellow 100 `#FFF9E4` panel
(`bgcolor` + `background-color`, no border). The old 3px gold top bar is retired (v3.0.0).
Fixed semantic; one per email, last position. Avatars: 160×160 source, face centered.
12px spacers between cards.

### C13 — Designed-image card (transparent PNG pattern)

Use: designed artwork with baked-in text (e.g. spotlight persona card) floating on a dark
card — the alpha IS the design.

```html
<td dir="rtl" align="center" style="border-radius:16px;">
  <img src="[SLOT: transparent PNG]" width="100%" alt="[SLOT: person/subject — role]"
       style="display:block; width:100%; height:auto; border:0; border-radius:16px;">
</td>
```

Rules: **never JPEG** (alpha flattens to a box); export 2× display (≥1104px wide for a
full-width slot); no HTML text overlay — the text is in the artwork; place on `{dark}`.

### C14 — Pull-quote (tinted panel)

```html
<td dir="rtl" align="right" bgcolor="{tint}" class="rs-quote" style="text-align:right;
    background-color:{tint}; border-radius:12px; padding:20px 24px; [SERIF] font-size:26px;
    font-weight:700; color:{text}; line-height:1.55;">&quot;[SLOT: quote]&quot;</td>
```

Straight `&quot;` quotes (the shipped standard). v3.0.0: the 4px `{primary}` side rule is
retired; the quote sits on a filled `{tint}` panel instead. Dark-surface variant: 30px,
`#FFFFFF`, class `rs-big`, no panel and no bar (the size carries it), followed by a 22px
spacer row. Mobile: `rs-quote` 26→20px.

### C15 — Q&A labeled blocks (spotlight pattern)

Use: interviews, FAQ, report commentary. Repeating unit on a `{dark}` card:

```html
<tr><td dir="rtl" align="right" style="text-align:right; border-top:1px solid rgba(255,255,255,0.2);
  padding:20px 0 10px 0;"><span style="display:inline-block; background-color:{chip-on-dark};
  color:{accent-soft}; [SANS] font-size:13px; font-weight:700; padding:6px 14px;
  border-radius:999px;">[SLOT: label]</span></td></tr>
<tr><td dir="rtl" align="right" style="text-align:right; padding:0 0 22px 0; [SANS] font-size:17px;
  font-weight:400; color:{on-dark}; line-height:1.8;">[SLOT: answer]</td></tr>
```

Variants: quote-answer = C14 dark variant · soft punchline answer = 15px `{on-dark-meta}`.

### C16 — Agenda row-card (date pill + calendar-link button)

Use: upcoming events, key dates, deadlines.

```html
<td dir="rtl" align="right" bgcolor="#FFFFFF" class="hov-agenda" style="background-color:#FFFFFF;
    border:1px solid #E5E7EB; border-radius:14px; padding:16px; text-align:right;">
  <td dir="rtl" width="95" align="right" valign="middle" class="rs-agd" style="width:95px; padding:0 0 0 12px; text-align:right;">
    <span dir="ltr" style="display:inline-block; background-color:{primary}; color:#FFFFFF; [SANS]
      font-size:14px; font-weight:400; padding:6px 14px; border-radius:999px; white-space:nowrap;">[SLOT: 13 July]</span></td>
  <td dir="rtl" align="right" valign="middle" class="rs-agt" style="text-align:right; [SANS] font-size:17px;
      font-weight:400; color:{text}; line-height:1.7;">[SLOT: emoji + event].
    <span style="display:block; padding-top:8px;">
      <a href="[SLOT: Google Calendar URL]" target="_blank" rel="noopener" style="display:inline-block;
        border:1px solid #E5E7EB; background-color:{btn-bg}; color:{primary}; [SANS] font-size:12px;
        font-weight:600; text-decoration:none; padding:5px 14px; border-radius:999px;">📅&nbsp;&nbsp;أضف للتقويم</a></span></td>
</td>
```

Calendar URL format: `…render?action=TEMPLATE&text=<enc title>&dates=YYYYMMDD/YYYYMMDD(+1)&details=<enc source line>&ctz=Asia/Riyadh`.
Mobile: `rs-agd/rs-agt` stack the pill ABOVE the text. 12px spacers between rows.

### C17 — Primary button pill + small arrow link

**a. Primary CTA** (on dark/banner surfaces):

```html
<a href="[SLOT]" target="_blank" rel="noopener" style="display:inline-block; background-color:#FFFFFF;
   color:{primary}; [SANS] font-size:16px; font-weight:700; text-decoration:none; padding:14px 36px;
   border-radius:999px;"><span dir="ltr" style="font-weight:700;">&#8249;</span>&nbsp;&nbsp;[SLOT: label]</a>
```

**b. Small arrow link** (trailing left chevron; on dark add `class="lnk-on-dark"` → hovers white in preview):

```html
<a class="lnk-on-dark" href="[SLOT]" target="_blank" rel="noopener" style="[SANS] font-size:14px;
   font-weight:600; color:{on-dark}; text-decoration:none;">[SLOT: label]&nbsp;&nbsp;<span dir="ltr"
   style="color:{accent-soft}; font-weight:700;">&#8249;</span></a>
```

On light surfaces variant b uses `color:{primary}` and no hover class. One primary CTA per
banner; arrow links for secondary actions.

### C18 — Separators (two variants)

**A — hairline + chevron trio** (between regular sections): two flexible 1px `#E5E7EB`
(`border/subtle`) cells around a fixed 110px center:

```html
<span dir="ltr" style="[SANS] font-size:16px; font-weight:700; letter-spacing:6px;"><span
  style="color:{accent-soft};">&#8249;</span>&nbsp;<span style="color:{primary};">&#8249;</span>&nbsp;<span
  style="color:{accent-soft};">&#8249;</span></span>
```

**B — open space** (before "big moment" sections only; also the chapter divider in annual
reports): an empty 80px spacer row,
`<tr><td dir="rtl" height="80" style="height:80px; font-size:1px; line-height:80px;">&nbsp;</td></tr>`.
v3.0.0: the old 96×4px `{primary}` → `{accent-soft}` gradient bar is retired with the
no-coloured-lines ruling.

### C19 — Footer card

Use: every email, always last. Desktop: logo 94×28 top-RIGHT · three 29×29 icon images
top-LEFT (`dir="ltr"` td, 8px gaps) · «عزم إكس — [SLOT: period]» right, [SANS] 12px
`{accent-soft}` · «صُنعت بحب في الرياض ❤️» right, 12px `{on-dark-meta}` · underlined
«إلغاء الاشتراك من النشرة» bottom-left, 11px `{unsub}`, `white-space:nowrap`,
`href="{{ unsubscribe }}"` (**merge tag must survive every edit**).

Card: `{dark}` (black `#000000`), radius 20px, no shadow, padding `30px 28px 24px 28px`. Social links:
`x.com/byazmx` · `instagram.com/byazmx` · `linkedin.com/company/azmx`.
Mobile: `rs-ftlogo/rs-ftico/rs-ftmeta/rs-ftmade/rs-ftunsub` stack everything vertically,
**fully centered**. Full markup in the showcase/skeleton.

---

## D. EMAIL-TYPE PATTERNS (compositions from the library)

**D1. Monthly newsletter** (as shipped — the reference):
C01 hero → C04 digest → [A] → repeating sections (C03 header + C05 body + C06/C08 media),
surface rota light/tint/dark → C07 banner for the launch moment → [B] → C09 dark feature →
C10/C11 project rows → C12 avatar cards → [B] → C13+C15 spotlight on `{dark}` card → [B] →
C16 agenda → [A] → C19 footer. Full slot map:
`../Newsletter/docs/template/ISSUE-TEMPLATE-REPORT.md` (`../Newsletter/docs/template/ISSUE-TEMPLATE-REPORT.md` — in the separate AZMX Newsletter project, not shipped with this skill).

**D2. Periodic report** (monthly/quarterly):
C01/C02 hero (period as subtitle) → KPI/stat rows: C10 without logos, using the 20/300
numeral style for the FIGURES (light display numerals = the KPI voice) → [A] → 2–4 sections
(C03 + C05 + C06/C14) → C11 status rows for deliverables → optional C09 for the headline
result → C17b closing link or C16 key dates → C19.

**D3. Annual report** (chaptered, long):
C02 typographic hero (year as masthead) → C04 as chapter index → per chapter: **[B] open
space as chapter divider** + C03 flipped-header variant for chapter openers → C05/C06/C14
content → one C09 centerpiece for the year's headline → C12 credits wall → C13 leadership
designed card → C19. Theme candidate: the green/gold table in §B3. Watch the 100 KB budget —
long emails: keep images on CDN, prune spacer bloat.

**D4. Short announcement:**
C02 hero (or C01 with event art) → ONE card: C07 banner with C17a CTA (or C05 + C06 + C17a)
→ optional single C16 row if there's a date → C19. No digest, no separators beyond one [A].

---

*v1 scope: Arabic RTL only. An EN/LTR edition would flip every `dir`, all alignments, and
the chevron direction (`›` right-pointing, mirrored padding) — a separate v2 effort, not a
find-replace. Do not ship LTR emails from this kit.*
