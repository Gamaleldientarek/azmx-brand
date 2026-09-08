# AZMX RTL Layout Guide — Cross-Format Master Reference (v1)

The complete right-to-left (RTL) layout system for **all** AZMX Arabic deliverables: HTML
emails, social media graphics, website components, PDF reports, and presentation decks.
Every rule here is **extracted from production AZMX work** — primarily the shipped
newsletter (`Newsletter/June/AZMX-Newsletter-June-EMAIL.html`) and existing social media
templates — and governs how Arabic content flows, aligns, and renders across every medium.

**Scope:** Arabic RTL only. English/LTR content follows reversed patterns (separate
documentation, not covered here). Mixed-language content follows the majority language's
direction with inline overrides for minority-language fragments.

**Relationship to format-specific docs:**

- Emails: [`email-design-system.md`](email-design-system.md) outranks this guide in
  email-specific details (HTML table architecture, ESP quirks); this guide outranks it in
  universal RTL principles.
- Social: Social-specific templates in `Social Media/templates/` govern platform specs;
  this guide governs text direction and alignment within those canvases.
- Website: Future web components inherit these rules (not yet implemented).
- Reports: PDF/presentation RTL follows the same principles with medium-specific rendering
  gotchas (§E).

**Companion references:**

- [`email-design-system.md`](email-design-system.md) — full email component library with RTL-specific HTML patterns
- [`../Newsletter/docs/qa-checklist.md`](../Newsletter/docs/qa-checklist.md) — email QA flow including RTL verification
- Social media templates (per-platform RTL canvases)

---

## A. UNIVERSAL RTL PRINCIPLES — non-negotiable across all formats

### A1. The 7 Core RTL Rules

These apply to **every** AZMX deliverable containing Arabic text, regardless of medium:

1. **Primary reading axis flows right-to-left**
   - Content starts at the top-right corner of the canvas
   - Eye flow: right → left, top → bottom
   - First element (hero, headline, logo) anchors top-right
   - Last element (footer, CTA, signature) anchors bottom-left

2. **Text alignment defaults to RIGHT**
   - All Arabic body text: `text-align: right` (CSS/HTML) or right-aligned (design tools)
   - Headings, subheadings, captions: right-aligned unless centered for symmetry
   - Left-alignment is ONLY used for Latin fragments inside `dir="ltr"` spans

3. **Directional marks always point LEFT**
   - Chevrons: `‹` (U+2039 LEFT-POINTING SINGLE QUOTATION MARK) or `&#8249;`
   - Arrows: `←` for "back/previous", `→` for "forward/next" (reversed from LTR)
   - Never use `>` or `›` in Arabic context — the bidi algorithm mirrors them incorrectly

4. **Mixed-script handling (Arabic + Latin/numerals)**
   - Every Latin fragment (names, URLs, English terms) wraps in `dir="ltr"` (HTML/email)
     or uses LTR override in design tools
   - Numerals: Arabic-Indic (٠–٩) for body text OR Western (0–9) in `dir="ltr"` spans —
     **never unprotected Western numerals in RTL flow** (they reorder incorrectly)
   - Dates in Latin format: `<span dir="ltr">13 July 2026</span>` or equivalent

5. **Kashida stretching, not letter-spacing**
   - Arabic text NEVER uses `letter-spacing` (breaks natural kashida ligatures)
   - Wordmark stretching (e.g., «وش صـــار؟») is **copy-pasted from approved assets**,
     never manually retyped with generic kashida (U+0640)
   - Latin fragments and chevron trios MAY use letter-spacing (4–6px for chevrons)

6. **Mirrored UI patterns**
   - Navigation: first item (home) top-right, last item (contact) top-left
   - Carousels/sliders: advance LEFT (next), retreat RIGHT (previous)
   - Progress bars/timelines: fill right-to-left (0% = left edge, 100% = right edge)
   - Icons: directional icons (arrows, chevrons) point left; symmetric icons (×, ✓) stay as-is

7. **Alignment hierarchy for mixed layouts**
   - Logo: top-right (primary anchor) OR centered (if symmetry is the design intent)
   - CTA buttons: right-aligned in text flow, centered in hero/banner contexts
   - Footer elements: metadata right-aligned, legal/unsubscribe left-aligned
   - Social icons: start from the right (first icon = rightmost)

### A2. Typography Rules for Arabic RTL

Consistent across email, web, social, and print:

1. **Font stacking**
   - Brand fonts first: `'Thmanyah Serif Display'` (personality) or `'Azm X'` (information)
   - Arabic fallback: `'IBM Plex Sans Arabic'` (Google Fonts, widely supported)
   - System fallbacks: `-apple-system` → `BlinkMacSystemFont` → `'Segoe UI'` → `Tahoma` → `Arial` → `sans-serif`
   - Full stack (copy-paste ready):
     ```
     'Azm X', 'IBM Plex Sans Arabic', -apple-system, BlinkMacSystemFont, 'Segoe UI', Tahoma, Arial, sans-serif
     ```

2. **Line-height for readability**
   - Body text: `1.7–1.8` (Arabic needs more leading than Latin)
   - Headings: `1.15–1.4` (tighter for impact)
   - UI/pills/meta: `1.5–1.7` (medium-tight)

3. **Punctuation direction**
   - Arabic uses `«…»` (guillemets) for quotes, opening at RIGHT: «هكذا»
   - Straight quotes `"…"` are acceptable (newsletter standard)
   - Em dashes `—` and ellipses `…` are direction-neutral
   - Parentheses in Arabic context: open RIGHT, close LEFT → `(نص)`

4. **Wordmark/logo text**
   - Kashida-stretched wordmarks are **SVG assets or carefully copy-pasted Unicode** —
     never manually stretched via CSS or design-tool character panel
   - Logo text in Figma/Illustrator: RIGHT-aligned text frame, LTR override OFF

### A3. Color and Contrast (direction-independent but worth stating)

RTL does not change color semantics, but contrast verification matters more in email/web:

- **WCAG AA minimum** for all text: 4.5:1 for body (17px), 3:1 for large text (24px+)
- Dark surfaces (`#040038` default): verify white text + `{on-dark}` (#DDE8FF) at 17px
- Light surfaces: verify `{text}` (#111927) on `#FFFFFF` and `{tint}` (#F0F5FF)
- Accent text (`{primary}` #001AFF): always punctuation (pills, numerals, bars), never
  large fills behind dense text (fails contrast)

---

## B. FORMAT-SPECIFIC RTL PATTERNS

### B1. HTML Email RTL (production-critical)

**Foundation:** HTML emails are the MOST fragile RTL environment (Gmail strips parent
`dir` attributes, Outlook has bidi bugs). Every rule here is battle-tested against
Gmail web, Gmail app (iOS/Android), Apple Mail, Outlook.com, and Spark.

**Core structure (verbatim from newsletter):**

```html
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; padding:0; background-color:#EDF2FB; direction:rtl;">
<center dir="rtl">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" dir="rtl"
       style="background-color:#EDF2FB; direction:rtl;">
  <tr><td dir="rtl" align="center" style="padding:24px 32px;">
    <!-- THE SHEET: max-width 640px, bg white, radius 24px -->
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" dir="rtl"
           style="max-width:640px; margin:0 auto; background-color:#FFFFFF; border-radius:24px;
           box-shadow:0 2px 8px rgba(4,0,56,.06); direction:rtl;">
      <!-- ALL CONTENT HERE: every <table> and EVERY <td> has dir="rtl" -->
    </table>
  </td></tr>
</table>
</center>
</body>
</html>
```

**Non-negotiable email RTL rules (in addition to §A):**

1. **`dir="rtl"` on EVERY `<table>` AND EVERY `<td>`**
   - Gmail drops `dir` from parent elements; per-cell is the ONLY reliable carrier
   - `<html dir="rtl">` + `<body dir="rtl">` help preview clients but are NOT enough
   - Even empty spacer cells get `<td dir="rtl">`

2. **`text-align:right` INLINE on every RTL text cell**
   - Attribute fallback: `align="right"` on the `<td>` (Outlook reads attributes first)
   - Example: `<td dir="rtl" align="right" style="text-align:right; font-size:17px; …">`

3. **Chevrons in `<span dir="ltr">` wrappers**
   - Raw `‹` in RTL context mirrors to `›` in some clients
   - Fix: `<span dir="ltr" style="font-weight:700; letter-spacing:4px;">&#8249;</span>`
   - Chevron trio (separator pattern): three chevrons in ONE `dir="ltr"` span

4. **Latin/numeric fragments in `<span dir="ltr">`**
   - Dates: `<span dir="ltr">13 July 2026</span>`
   - Numerals: `<span dir="ltr">01</span>` (Western) OR Arabic-Indic `٠١` unprotected
   - URLs: `<span dir="ltr">azmx.sa</span>` even if not hyperlinked

5. **`letter-spacing` ONLY on LTR spans**
   - Never set on Arabic text (breaks kashida)
   - Acceptable: chevron spans (`letter-spacing:4px–6px`), Latin all-caps labels (rare)

6. **Responsive mobile: RTL-aware class names**
   - Right-padding classes: `.rs-chip { padding-right:8px !important; }` (not left)
   - Text alignment stays right in mobile stack (do NOT center unless intentional)

**Common email RTL gotchas:**

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| Chevrons point right (`›`) | Missing `dir="ltr"` wrapper | Wrap chevron in `<span dir="ltr">&#8249;</span>` |
| Numbers render backwards (`6102` instead of `2016`) | Western numerals in RTL flow | Wrap in `<span dir="ltr">2016</span>` |
| Gmail shows left-aligned text | No inline `text-align:right` | Add `style="text-align:right;"` to `<td>` |
| Outlook ignores alignment | Missing attribute fallback | Add `align="right"` attribute to `<td>` |
| Text overlaps on mobile | Wrong padding side in responsive CSS | Use `padding-right` not `padding-left` in `.rs-*` classes |
| Kashida breaks (spaces appear) | `letter-spacing` set on Arabic | Remove `letter-spacing` from Arabic text cells |

**Email-specific RTL patterns (extracted from newsletter components):**

- **Hero card with RTL logo:** logo image `margin:0 0 0 auto` (pushes to RIGHT edge)
- **Two-column layouts:** right column = primary content, left column = secondary (reversed from LTR)
- **Agenda rows (pill + text):** pill `align="right"`, text fills remaining width
- **Footer social icons:** `dir="ltr"` table, icons LEFT-aligned within that LTR context
  (so the first icon visually appears on the RIGHT of the icon group)

**Full email RTL component library:** see [`email-design-system.md`](email-design-system.md) §A1–A7, §C.

### B2. Social Media Graphics RTL (static design)

**Context:** Social posts are raster/vector images (PNG, JPG, SVG) created in Figma,
Illustrator, or Photoshop. No HTML bidi issues, but layout and typography rules still apply.

**Platform canvas specs (always in portrait or square for Arabic content):**

| Platform | Optimal Canvas (px) | Safe Zone Inset | Notes |
|----------|---------------------|-----------------|-------|
| Instagram Post | 1080×1080 | 80px all sides | Square primary, 4:5 (1080×1350) for max feed height |
| Instagram Story | 1080×1920 | 120px top/bottom, 80px sides | Watch CTA placement (bottom ~300px) |
| Twitter/X Post | 1200×675 | 60px all sides | 16:9 landscape acceptable for infographics |
| LinkedIn Post | 1200×1200 | 80px all sides | Square safest; avoid extreme crops |
| Facebook Post | 1200×1200 | 80px all sides | Same as LinkedIn |

**RTL layout structure for social (top-to-bottom):**

1. **Top-right anchor:** Logo or wordmark (94×28 scale equivalent, or larger for solo graphics)
2. **Main content zone (right-aligned):**
   - Headline: right-aligned, max 2–3 lines
   - Body text: right-aligned, line-height 1.7–1.8
   - Supporting elements (icons, decorative shapes): flow from right
3. **Bottom-left anchor:** CTA, date, or account handle (if shown)

**Typography for social RTL:**

- **Figma/Illustrator setup:**
  - Text frame alignment: RIGHT (not left, not center unless full-width centered)
  - Paragraph direction: default (do NOT force LTR in Arabic frames)
  - Font: Azm X (sans) or Thmanyah Serif Display (personality), fallback IBM Plex Sans Arabic
  - Export as PNG: 2× resolution (2160px for 1080 designs) to preserve kashida rendering

- **Mixed-language posts (rare):**
  - Majority language (Arabic) sets overall direction
  - English fragment: separate text frame, LEFT-aligned, or small inline callout
  - Hashtags: keep in Arabic if possible; Latin hashtags at end in separate LTR line

**Social-specific RTL patterns:**

- **Quote graphics:** Large quote («…») right-aligned, 4px RIGHT border (quote bar),
  attribution small text bottom-right or bottom-center
- **Stat tiles (KPI cards):** Numeral top-right (large display), label below right-aligned
- **Carousel posts (multi-image):** First card = intro (right-heavy), subsequent cards =
  content (maintain right anchor), last card = CTA (centered acceptable)
- **Story sequences:** Consistent right-aligned headline position across all frames

**Common social RTL gotchas:**

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| Text too close to edge | Headline cut off in feed crop | Respect 80px safe zone inset |
| Kashida breaks in export | Spaces appear in stretched wordmarks | Use outline text or embed fonts in export |
| English hashtags look wrong | Mixed with Arabic in RTL line | Separate line for hashtags, or LTR text frame |
| Icon direction confusion | Arrow points wrong way | Use left-pointing arrows `←` for forward actions |
| Logo floats left | Text frame default alignment | Set text/group alignment to RIGHT in canvas |

### B3. Website/Web Components RTL (future, principles documented now)

**Status:** No live AZMX website yet, but principles established for future implementation.

**HTML structure (React/Vue/plain HTML):**

```html
<html dir="rtl" lang="ar">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * { direction: rtl; text-align: right; } /* Global reset for RTL */
    .ltr { direction: ltr; text-align: left; } /* Override for Latin content */
  </style>
</head>
<body>
  <!-- Content: right-aligned by default, LEFT-aligned only for .ltr class -->
</body>
</html>
```

**CSS conventions for web RTL:**

- **Logical properties (modern approach):**
  ```css
  /* Use margin-inline-start / margin-inline-end instead of margin-left/right */
  .card {
    margin-inline-start: 20px; /* RIGHT margin in RTL, LEFT in LTR */
    padding-inline-end: 16px;  /* LEFT padding in RTL, RIGHT in LTR */
    border-inline-start: 4px solid blue; /* RIGHT border in RTL */
  }
  ```

- **Fallback for older browsers (physical properties):**
  ```css
  .card {
    margin-right: 20px; /* Explicit RTL assumption */
    padding-left: 16px;
    border-right: 4px solid blue;
  }
  ```

**Framework-specific (React example):**

```jsx
// Component with mixed content
export function ArticleCard({ title, subtitle, link }) {
  return (
    <div className="card" dir="rtl">
      <h2 style={{ textAlign: 'right' }}>{title}</h2>
      <p style={{ textAlign: 'right' }}>{subtitle}</p>
      {link && (
        <a href={link} className="ltr" style={{ textAlign: 'left' }}>
          {link}
        </a>
      )}
    </div>
  );
}
```

**Responsive web RTL:**

- **Grid layouts:** `grid-template-columns` reads right-to-left (first column = rightmost)
- **Flexbox:** `flex-direction: row` flows RTL (first child = right), use `row-reverse` to flip
- **Media queries:** Same breakpoints as LTR (direction-independent), but padding/margin
  sides may need logical properties

**Web-specific RTL patterns:**

- **Navigation bar:** Logo top-right, menu items flow LEFT from logo
- **Sidebar layouts:** Primary sidebar RIGHT (not left), secondary sidebar left
- **Forms:** Labels right-aligned above inputs, inputs right-aligned text
- **Breadcrumbs:** Home (rightmost) → Category → Page (leftmost), separator `‹` points left

**Accessibility (web-only considerations):**

- `lang="ar"` on `<html>` (screen readers announce Arabic pronunciation)
- `dir="rtl"` on `<html>` AND any LTR override blocks (`dir="ltr"` on English sections)
- ARIA labels in Arabic: `aria-label="القائمة الرئيسية"` (not English "Main Menu")
- Keyboard navigation: Tab order still top-to-bottom, but visual order is right-to-left

### B4. PDF Reports RTL (print/export)

**Context:** Quarterly/annual reports exported from InDesign, Figma, or generated via
HTML-to-PDF tools. Static layout, no client rendering quirks, but text flow is locked.

**InDesign/Illustrator setup:**

1. **Document direction:** Set story direction to RTL in paragraph panel
2. **Text frames:** Right-aligned, text flows right-to-left
3. **Master pages:** Logo/header top-right, page numbers bottom-left (or center)
4. **Margins:** Binding edge = LEFT (for right-to-left page flip in print)

**HTML-to-PDF RTL (using tools like Puppeteer, Prince, WeasyPrint):**

```html
<html dir="rtl" lang="ar">
<head>
  <style>
    @page { margin: 2cm; }
    body { direction: rtl; font-family: 'IBM Plex Sans Arabic', sans-serif; }
    h1, h2, h3 { text-align: right; }
    p { text-align: right; line-height: 1.8; }
    .page-number { text-align: left; } /* Bottom-left corner */
  </style>
</head>
<body>
  <!-- Content with explicit RTL styling -->
</body>
</html>
```

**PDF-specific RTL patterns:**

- **Cover page:** Title right-aligned or centered, logo top-right, date bottom-left
- **Table of contents:** Chapter titles right-aligned, page numbers left-aligned (dots connect)
- **Body pages:** Running header top-right (chapter name), page number bottom-left
- **Tables/charts:** Headers right-aligned, data columns read right-to-left (first column = right)
- **Footnotes:** Right-aligned, anchored to right margin

**Common PDF RTL gotchas:**

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| Text renders LTR | PDF tool ignores `dir="rtl"` | Set explicit `direction: rtl` in CSS |
| Page numbers on wrong side | Template default LTR | Override page-number position in `@page` or master |
| Tables read left-to-right | Column order not reversed | Manually reorder columns in markup (right = first) |
| Font fallback to Latin | Arabic glyphs missing | Embed Arabic font in PDF (InDesign) or use web-safe in HTML-to-PDF |

### B5. Presentation Decks RTL (PowerPoint, Keynote, Google Slides)

**Context:** Internal/external presentations with Arabic content. Mostly centered layouts,
but text-heavy slides need RTL structure.

**Slide layout principles:**

- **Title slides:** Centered (most common) OR title top-right, subtitle below right-aligned
- **Content slides:** Bullet points right-aligned, images on LEFT (text wraps right)
- **Two-column slides:** Right column = primary (text), left column = supporting (image/chart)
- **Footer:** Logo bottom-right, slide number bottom-left (or center)

**PowerPoint/Keynote RTL setup:**

1. **Text box alignment:** Right-align text boxes by default
2. **Bullet direction:** Ensure bullets appear on the RIGHT of text (not left)
3. **Reading order:** Accessibility reading order = top-right → bottom-left

**Google Slides RTL:**

- Set slide text direction via Format → Text → Paragraph direction → Right-to-left
- Each text box needs manual RTL setting (no global document RTL mode as of 2026)

**Presentation-specific RTL patterns:**

- **Agenda slide:** Numbered items right-aligned, numbers on RIGHT (as bullets)
- **Quote slides:** Large centered quote acceptable, attribution right-aligned below
- **Closing slide:** CTA centered, contact info bottom-right

---

## C. CODE EXAMPLES BY USE CASE

### C1. Email: Hero Section with RTL Logo and Title

```html
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" dir="rtl">
  <tr>
    <td dir="rtl" align="right" bgcolor="#040038" background="https://cdn.example.com/hero.jpg"
        style="background-color:#040038; background-image:url('https://cdn.example.com/hero.jpg');
        background-size:cover; background-position:center; border-radius:20px;
        box-shadow:0 2px 8px rgba(4,0,56,.06); padding:56px 24px; text-align:right;">
      
      <!-- Logo: floats RIGHT -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" dir="rtl">
        <tr>
          <td dir="rtl" align="right" style="text-align:right; padding:0 0 24px 0;">
            <img src="https://cdn.example.com/logo-white.png" width="94" height="28" alt="عزم إكس"
                 style="display:block; margin:0 0 0 auto; border:0;">
          </td>
        </tr>
      </table>
      
      <!-- Eyebrow label -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" dir="rtl">
        <tr>
          <td dir="rtl" align="right" style="text-align:right; padding:0 0 12px 0;
              font-family:'Azm X', 'IBM Plex Sans Arabic', sans-serif; font-size:11px;
              font-weight:300; color:#5D8FFF; line-height:1.5;">النشرة الشهرية</td>
        </tr>
      </table>
      
      <!-- Hero title -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" dir="rtl">
        <tr>
          <td dir="rtl" align="right" class="rs-hero" style="text-align:right;
              font-family:'Thmanyah Serif Display', 'IBM Plex Sans Arabic', serif; font-size:56px;
              font-weight:700; color:#FFFFFF; line-height:1.15;">وش صـــار في <span dir="ltr">2026</span>؟</td>
        </tr>
      </table>
      
      <!-- Subtitle -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" dir="rtl">
        <tr>
          <td dir="rtl" align="right" style="text-align:right; padding:12px 0 0 0;
              font-family:'Azm X', 'IBM Plex Sans Arabic', sans-serif; font-size:16px;
              font-weight:400; color:#DDE8FF; line-height:1.6;">
            <span dir="ltr">يونيو 2026</span> — كل ما يهمك من أخبار وقصص
          </td>
        </tr>
      </table>
      
      <!-- Chevron trio -->
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" dir="rtl">
        <tr>
          <td dir="rtl" align="right" style="text-align:right; padding:24px 0 0 0;">
            <span dir="ltr" style="font-family:'Thmanyah Serif Display', serif; font-size:26px;
                  font-weight:700; color:#5D8FFF; letter-spacing:4px;">&#8249;&nbsp;&#8249;&nbsp;&#8249;</span>
          </td>
        </tr>
      </table>
      
    </td>
  </tr>
</table>
```

### C2. Social Media: Instagram Post RTL Layout (Figma pseudo-markup)

**Canvas:** 1080×1080px, safe zone 80px inset (content within 920×920px center)

**Layer structure (top-to-bottom in Figma layers panel):**

```
📁 Instagram Post — عزم إكس
  └─ 🎨 Background (#EDF2FB fill)
  └─ 📐 Safe Zone Guide (80px frame inset, stroke only, no fill)
  └─ 🖼️ Logo (top-right: x=900, y=80, size=94×28)
  └─ 📝 Headline
       • Position: x=160, y=200, w=760, h=auto (right-aligned text frame)
       • Font: Thmanyah Serif Display, 72pt, Bold
       • Alignment: Right
       • Fill: #040038
       • Text: "وش صـــار في يونيو؟"
  └─ 📝 Body
       • Position: x=160, y=350, w=700, h=auto (right-aligned text frame)
       • Font: Azm X, 32pt, Regular
       • Alignment: Right
       • Fill: #111927
       • Line height: 140%
       • Text: "كل ما يهمك من أخبار وقصص — اقرأ النشرة الكاملة"
  └─ 🔲 CTA Pill
       • Position: x=160, y=920, w=auto, h=56 (bottom-left anchor)
       • Background: #001AFF, radius 999px
       • Text: "اقرأ المزيد" + chevron ‹ (white, 28pt)
       • Padding: 16×36px
  └─ 📝 Account Handle (optional)
       • Position: x=80, y=1000, small text
       • Font: Azm X, 18pt, #6C737F
       • Text: "@byazmx"
```

### C3. Web: React Component with RTL Support

```jsx
// ArticleCard.jsx — RTL-aware component
import React from 'react';
import './ArticleCard.css';

export function ArticleCard({ title, excerpt, date, link, image }) {
  return (
    <article className="article-card" dir="rtl">
      {image && (
        <div className="article-card__image">
          <img src={image} alt="" />
        </div>
      )}
      <div className="article-card__content">
        <h2 className="article-card__title">{title}</h2>
        <p className="article-card__excerpt">{excerpt}</p>
        <div className="article-card__meta">
          <time className="ltr" dir="ltr">{date}</time>
          <a href={link} className="article-card__link">
            اقرأ المزيد <span dir="ltr" className="chevron">&#8249;</span>
          </a>
        </div>
      </div>
    </article>
  );
}
```

```css
/* ArticleCard.css — RTL layout styles */
.article-card {
  direction: rtl;
  text-align: right;
  background: #FFFFFF;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(4, 0, 56, 0.06);
  overflow: hidden;
}

.article-card__image img {
  width: 100%;
  height: auto;
  display: block;
}

.article-card__content {
  padding: 24px 28px;
}

.article-card__title {
  font-family: 'Thmanyah Serif Display', 'IBM Plex Sans Arabic', serif;
  font-size: 28px;
  font-weight: 700;
  color: #040038;
  line-height: 1.4;
  margin: 0 0 12px 0;
  text-align: right;
}

.article-card__excerpt {
  font-family: 'Azm X', 'IBM Plex Sans Arabic', sans-serif;
  font-size: 17px;
  font-weight: 400;
  color: #111927;
  line-height: 1.8;
  margin: 0 0 20px 0;
  text-align: right;
}

.article-card__meta {
  display: flex;
  justify-content: space-between; /* Date left, link right in RTL flex */
  align-items: center;
  flex-direction: row-reverse; /* Reverses visual order for RTL */
}

.article-card__meta time {
  font-size: 14px;
  color: #6C737F;
  direction: ltr; /* Force LTR for date format */
  text-align: left;
}

.article-card__link {
  font-family: 'Azm X', 'IBM Plex Sans Arabic', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #001AFF;
  text-decoration: none;
  text-align: right;
}

.article-card__link .chevron {
  font-weight: 700;
  letter-spacing: 0;
  margin-inline-start: 6px; /* RIGHT margin in RTL */
}

/* Responsive */
@media (max-width: 480px) {
  .article-card__title {
    font-size: 22px;
  }
  .article-card__content {
    padding: 20px;
  }
}
```

### C4. PDF: HTML-to-PDF Report Template

```html
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="utf-8">
  <title>تقرير عزم إكس الربع سنوي</title>
  <style>
    @page {
      size: A4;
      margin: 2.5cm 2cm;
      @bottom-left {
        content: counter(page);
        font-family: 'IBM Plex Sans Arabic', sans-serif;
        font-size: 11pt;
        color: #6C737F;
      }
    }
    
    body {
      direction: rtl;
      font-family: 'IBM Plex Sans Arabic', sans-serif;
      font-size: 12pt;
      line-height: 1.8;
      color: #111927;
      margin: 0;
      padding: 0;
    }
    
    h1 {
      font-family: 'Thmanyah Serif Display', serif;
      font-size: 36pt;
      font-weight: 700;
      color: #040038;
      text-align: right;
      margin: 0 0 0.5cm 0;
      line-height: 1.2;
    }
    
    h2 {
      font-family: 'Thmanyah Serif Display', serif;
      font-size: 24pt;
      font-weight: 700;
      color: #040038;
      text-align: right;
      margin: 1cm 0 0.5cm 0;
      line-height: 1.3;
      page-break-after: avoid;
    }
    
    p {
      text-align: right;
      margin: 0 0 0.5cm 0;
    }
    
    .ltr {
      direction: ltr;
      text-align: left;
      font-style: italic;
    }
    
    .cover {
      page-break-after: always;
      height: 24cm;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: flex-end; /* Align content to RIGHT */
    }
    
    .cover h1 {
      font-size: 48pt;
      margin: 0 0 0.3cm 0;
    }
    
    .cover .subtitle {
      font-size: 18pt;
      color: #6C737F;
      text-align: right;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 0.5cm 0;
      direction: rtl;
    }
    
    th, td {
      text-align: right;
      padding: 0.3cm 0.4cm;
      border: 1px solid #E5E7EB;
    }
    
    th {
      background-color: #F0F5FF;
      font-weight: 700;
      color: #040038;
    }
  </style>
</head>
<body>
  
  <!-- COVER PAGE -->
  <div class="cover">
    <h1>التقرير الربع سنوي</h1>
    <p class="subtitle"><span class="ltr">Q2 2026</span> — أبريل – يونيو</p>
    <p class="subtitle" style="margin-top:2cm; font-size:14pt;">عزم إكس — الرياض، المملكة العربية السعودية</p>
  </div>
  
  <!-- CONTENT PAGES -->
  <h2>نظرة عامة على الربع الثاني</h2>
  <p>
    شهد الربع الثاني من عام <span class="ltr">2026</span> نموًا ملحوظًا في جميع المؤشرات الرئيسية...
  </p>
  
  <h2>المؤشرات الرئيسية</h2>
  <table>
    <thead>
      <tr>
        <th>المؤشر</th>
        <th>القيمة</th>
        <th>النمو</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>عدد المشاريع المكتملة</td>
        <td><span class="ltr">42</span></td>
        <td><span class="ltr">+18%</span></td>
      </tr>
      <tr>
        <td>رضا العملاء</td>
        <td><span class="ltr">94%</span></td>
        <td><span class="ltr">+3%</span></td>
      </tr>
    </tbody>
  </table>
  
  <p>
    لمزيد من المعلومات، يرجى زيارة <span class="ltr">azmx.sa/reports</span>
  </p>
  
</body>
</html>
```

---

## D. COMMON RTL GOTCHAS — cross-format debugging guide

### D1. Text Direction Issues

| Symptom | Likely Cause | Fix | Format |
|---------|--------------|-----|--------|
| Chevrons point right (`›`) instead of left (`‹`) | Missing `dir="ltr"` wrapper | Wrap chevron in `<span dir="ltr">&#8249;</span>` | Email, Web |
| Numbers display backwards (e.g., `6102` for `2016`) | Western numerals in RTL flow without protection | Wrap in `<span dir="ltr">2016</span>` | Email, Web |
| Mixed Arabic/English lines look jumbled | No explicit direction on mixed-script blocks | Wrap Latin text in `dir="ltr"` spans | All formats |
| URL breaks across lines incorrectly | RTL line-breaking algorithm applied to Latin | Wrap URL in `<span dir="ltr" class="nowrap">` | Email, Web |
| Parentheses reversed `)(` | Bidi algorithm mirrors symmetric chars | Use actual RTL parentheses OR `<span dir="ltr">` for Latin content in parens | Email, Web |

### D2. Alignment and Layout Issues

| Symptom | Likely Cause | Fix | Format |
|---------|--------------|-----|--------|
| Text aligns left instead of right | Missing `text-align:right` or RTL direction | Add `text-align:right; direction:rtl;` inline (email) or in CSS (web) | Email, Web |
| Logo appears on left side | Default LTR positioning | Use `margin:0 0 0 auto` (email) or `align-self:flex-end` (web) | Email, Web |
| Two-column layout reversed | Columns coded in LTR order | Swap column order: right column first in markup | Email, Web |
| Button/CTA on wrong side | Default left-alignment | Align button container to right: `text-align:right` or `align="right"` | Email, Web |
| Social icons start from left | Icon container in LTR mode | Wrap icons in `dir="ltr"` container, then use `text-align:left` (icons appear right-to-left visually) | Email, Web |

### D3. Typography Issues

| Symptom | Likely Cause | Fix | Format |
|---------|--------------|-----|--------|
| Kashida stretching breaks (spaces appear) | `letter-spacing` applied to Arabic text | Remove `letter-spacing` from Arabic; apply only to LTR spans | All formats |
| Font renders as Latin fallback | Arabic font not loaded or embedded | Check font stack; ensure IBM Plex Sans Arabic is available | All formats |
| Line-height too tight, text overlaps | LTR line-height (1.2–1.4) used for Arabic | Increase to 1.7–1.8 for body text | All formats |
| Wordmark/logo text stretches incorrectly | Manual kashida addition via keyboard | Use approved SVG/PNG asset OR copy-paste exact Unicode from brand file | All formats |

### D4. Email-Specific Issues

| Symptom | Likely Cause | Fix | Format |
|---------|--------------|-----|--------|
| Gmail shows left-aligned text | No inline `text-align` (relies on `<style>` which Gmail strips) | Add `style="text-align:right;"` to every `<td>` with text | Email |
| Outlook ignores text direction | Missing `dir` attribute on cell | Add `dir="rtl"` to every `<td>` (not just parent `<table>`) | Email |
| Mobile text centers unexpectedly | Responsive CSS centers without RTL awareness | Use `text-align:right !important` in media queries | Email |
| Padding wrong side on mobile | LTR padding in responsive classes (e.g., `padding-left`) | Use `padding-right` for RTL | Email |
| Spacer rows collapse | Empty `&nbsp;` not respecting RTL direction | Add `dir="rtl"` to spacer `<td>` AND set `font-size` + `line-height` | Email |

### D5. Design Tool Issues (Figma, Illustrator)

| Symptom | Likely Cause | Fix | Format |
|---------|--------------|-----|--------|
| Text frame aligns left by default | Tool default is LTR | Set text frame alignment to RIGHT in properties panel | Social, PDF |
| Arabic text renders with broken ligatures | Font not installed or active | Install IBM Plex Sans Arabic or brand fonts; restart design tool | Social, PDF |
| Exported PNG shows wrong text direction | Text layer has LTR override set | Remove LTR paragraph setting; ensure frame is neutral or RTL | Social |
| Copy-pasted text loses direction | Pasted from LTR source | Re-type in RTL text frame OR paste then reset paragraph direction | Social, PDF |

---

## E. PLATFORM-SPECIFIC RENDERING QUIRKS

### E1. Email Clients

**Gmail (web + app):**
- Strips `<style>` tag (keeps `@font-face`, hover states, media queries but doesn't apply brand fonts)
- Drops `dir` attribute from parent elements (MUST be on every `<td>`)
- Forces system fonts (SF Arabic on iOS, Roboto Arabic on Android) — design with this in mind
- Clips HTML at ~102 KB (images must be on CDN, not inline base64)

**Apple Mail / iOS Mail:**
- Honors webfonts (`@font-face`) and media queries
- Best RTL rendering fidelity (respects parent `dir` more reliably)
- Watch for dark mode: ensure `{on-dark}` colors have enough contrast

**Outlook (Windows desktop):**
- Uses Word rendering engine (not a real browser)
- Reads `align="right"` attribute better than `text-align:right` CSS
- VML for background images (fallback `bgcolor` critical)
- No `border-radius` support (accept square corners in Outlook or use VML hacks)

**Outlook.com (web):**
- Better CSS support than desktop Outlook
- Honors `dir="rtl"` and `text-align` inline styles
- Strips some `<style>` rules (always inline critical styles)

### E2. Social Media Platforms

**Instagram:**
- Feed crops: 1:1 (square) shows full, 4:5 (portrait) maximizes height
- Story safe zones: 120px top/bottom (UI overlays), 80px sides
- Text in images: keep it large (min 40pt for readability on mobile)
- Export: PNG at 2× for text clarity

**Twitter/X:**
- 16:9 landscape is standard, but square (1:1) works for text-heavy posts
- Card previews crop unpredictably (keep critical text in center 80%)
- Alt text: write in Arabic if image text is Arabic (accessibility)

**LinkedIn:**
- Square (1:1) safest; portrait (4:5) acceptable
- Professional tone: avoid overly decorative fonts (stick to Azm X for body)
- Document posts (PDFs): LinkedIn preview may not render Arabic correctly — use image posts

### E3. Web Browsers

**Chrome/Edge (Chromium):**
- Excellent RTL support, honors `dir="rtl"` and logical CSS properties
- DevTools: test RTL by toggling `dir` attribute in Elements panel

**Safari (macOS/iOS):**
- Good RTL support, excellent Arabic font rendering
- Watch for flexbox `row-reverse` bugs in older Safari versions (use logical properties)

**Firefox:**
- Solid RTL support, good bidi algorithm
- DevTools has RTL layout debugging (show text direction boundaries)

**Older browsers (IE11, old mobile browsers):**
- Use physical properties (`margin-right`, `padding-left`) as fallback
- Avoid logical properties (`margin-inline-start`) without fallback

### E4. PDF Generators

**Puppeteer (headless Chrome):**
- Excellent RTL support (uses Chromium engine)
- Embed fonts via `@font-face` or `file://` URLs (check licensing)
- Set `preferCSSPageSize: true` in PDF options to honor `@page` rules

**Prince XML:**
- Professional PDF engine, strong RTL support
- Supports advanced CSS paged media (running headers, page numbers)
- Commercial license required for production use

**WeasyPrint (Python):**
- Open-source, good RTL support
- Font embedding: ensure Arabic fonts are in system font path or specify via CSS
- Some CSS3 features limited (check docs for `direction` and `unicode-bidi` support)

**InDesign (manual layout):**
- Full RTL paragraph support (World-Ready Composer)
- Set story direction in Paragraph panel (right-align + RTL)
- Export to PDF: embed fonts, check Arabic rendering in Acrobat before sending

---

## F. RTL QA CHECKLIST — pre-launch verification for any deliverable

### F1. Visual QA (all formats)

- [ ] **Content starts top-right**, flows right-to-left, ends bottom-left
- [ ] **All Arabic text is right-aligned** (or centered if symmetry is design intent)
- [ ] **Logo/wordmark anchors top-right** (or center if specified)
- [ ] **Chevrons point LEFT** (`‹`), never right (`›`)
- [ ] **Arrows point correctly:** `←` for forward, `→` for back (reversed from LTR)
- [ ] **Mixed-script content:** Latin/numerals are visually separated or in `dir="ltr"` spans
- [ ] **No `letter-spacing` on Arabic text** (kashida is natural, not forced)
- [ ] **Kashida-stretched wordmarks** match approved assets (not manually stretched)
- [ ] **Safe zones respected:** no text cut off at edges (80px inset for social, per-format margins for print)

### F2. Technical QA (HTML: email + web)

- [ ] **`<html dir="rtl" lang="ar">`** at document root
- [ ] **Every `<table>` has `dir="rtl"`** (email)
- [ ] **Every `<td>` has `dir="rtl"`** (email — critical for Gmail)
- [ ] **Every RTL text cell has `style="text-align:right;"`** inline (email)
- [ ] **Attribute fallback:** `align="right"` on `<td>` for Outlook (email)
- [ ] **Chevrons in `<span dir="ltr">` wrappers** (email + web)
- [ ] **Latin/numeric fragments in `<span dir="ltr">` spans** (email + web)
- [ ] **No `letter-spacing` in Arabic text styles** (email + web)
- [ ] **Font stack includes Arabic fallback** (IBM Plex Sans Arabic minimum)
- [ ] **Mobile responsive classes use RIGHT padding** (not left) for RTL spacing

### F3. Content QA (text accuracy)

- [ ] **Arabic copy is verbatim from approved source** (no typos, no ad-hoc edits)
- [ ] **Dates in Latin format are in `dir="ltr"` spans:** `<span dir="ltr">13 July 2026</span>`
- [ ] **Numerals protected:** Western numerals in LTR spans OR use Arabic-Indic (٠–٩) unprotected
- [ ] **URLs in `dir="ltr"` spans** (even if not hyperlinked)
- [ ] **English names/brands in `dir="ltr"` spans** for correct rendering
- [ ] **Quotes use Arabic guillemets `«…»`** OR straight quotes `"…"` (consistent per format)
- [ ] **Punctuation matches brand voice** (em dash `—`, ellipsis `…`, not multiple periods)

### F4. Accessibility QA (web + email where applicable)

- [ ] **`lang="ar"` attribute present** on `<html>` or RTL content blocks
- [ ] **`dir="rtl"` on all RTL containers** (not just root)
- [ ] **Alt text in Arabic** for images with Arabic text content
- [ ] **ARIA labels in Arabic** if using (e.g., `aria-label="القائمة الرئيسية"`)
- [ ] **Color contrast WCAG AA:** 4.5:1 for body (17px), 3:1 for large text (24px+)
- [ ] **Keyboard navigation order:** top-right → bottom-left (matches visual flow)

### F5. Cross-Client/Platform QA (email + web)

**Email test matrix (send test to these clients):**
- [ ] Gmail web (Chrome on desktop)
- [ ] Gmail app (iOS + Android)
- [ ] Apple Mail (macOS or iOS)
- [ ] Outlook.com web
- [ ] Outlook desktop (Windows) — accept degraded styling, verify RTL still works
- [ ] Spark or other client (optional, but recommended)

**Email-specific checks in test sends:**
- [ ] Text aligns right in ALL clients (especially Gmail)
- [ ] Chevrons point left in ALL clients
- [ ] Numbers/dates display correctly (not reversed)
- [ ] Mobile view (360px, 375px, 430px widths): text stays right-aligned, padding correct
- [ ] File size < 100 KB (check before sending; Gmail clips at ~102 KB)

**Web browser test matrix:**
- [ ] Chrome (latest, macOS/Windows)
- [ ] Safari (latest, macOS/iOS)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS, 375px and 430px widths)
- [ ] Chrome Mobile (Android)

**Social platform QA:**
- [ ] Upload test image to platform (Instagram/Twitter/LinkedIn)
- [ ] Verify text is legible at thumbnail size (Instagram feed preview)
- [ ] Check safe zones: no UI overlays cover critical text (Instagram Story)
- [ ] Export at 2× resolution (2160px for 1080 designs)

### F6. Brand Consistency QA

- [ ] **Color tokens match theme:** verify `{dark}`, `{primary}`, `{tint}`, `{on-dark}` per format
- [ ] **Typography matches scale:** hero/section/body sizes per [`email-design-system.md`](email-design-system.md) or format spec
- [ ] **Spacing/radius consistent:** 24px sheet radius (email), 20px cards, 16px media, 12px chips, 999px pills
- [ ] **Shadow consistent:** `0 2px 8px rgba(4,0,56,.06)` on cards (email, web)
- [ ] **Chevron trio spacing:** 4–6px `letter-spacing` in `dir="ltr"` span
- [ ] **Logo usage:** correct logo variant (white on dark, color on light), correct size (94×28 standard)

---

## G. MIGRATION NOTES — converting existing LTR assets to RTL

### G1. Email: LTR-to-RTL conversion steps

If starting from an LTR email template:

1. **Add `dir="rtl"` attributes:**
   - `<html dir="rtl" lang="ar">` (change `lang="en"` to `lang="ar"`)
   - Every `<table dir="rtl">` and every `<td dir="rtl">`

2. **Flip all alignments:**
   - Change `align="left"` to `align="right"` on `<td>` attributes
   - Change `text-align:left` to `text-align:right` in inline styles

3. **Reverse padding/margins:**
   - Swap `padding-left` ↔ `padding-right` in inline styles
   - Swap `margin-left` ↔ `margin-right`

4. **Update responsive CSS:**
   - In `@media` blocks, swap padding/margin sides
   - Ensure text alignment stays `right` in mobile stack (not center unless intentional)

5. **Wrap Latin content in `dir="ltr"` spans:**
   - All dates, URLs, numerals, English names

6. **Flip chevrons/arrows:**
   - Change `›` or `>` to `‹` (`&#8249;`)
   - Wrap in `<span dir="ltr">` to prevent mirroring

7. **Test in Gmail:** The `dir="rtl"` on every `<td>` is critical (Gmail drops parent `dir`).

### G2. Web: Adding RTL support to existing LTR site

**Option A — Separate RTL stylesheet (simple, for small sites):**

```html
<link rel="stylesheet" href="styles.css">
<link rel="stylesheet" href="styles-rtl.css"> <!-- Overrides for RTL -->
```

**styles-rtl.css** overrides LTR properties:
```css
[dir="rtl"] body { direction: rtl; text-align: right; }
[dir="rtl"] .header { /* flip paddings/margins */ }
/* ... etc */
```

**Option B — CSS logical properties (modern, scalable):**

Refactor all physical properties to logical:
- `margin-left` → `margin-inline-start` (left in LTR, right in RTL)
- `padding-right` → `padding-inline-end` (right in LTR, left in RTL)
- `border-left` → `border-inline-start`
- `text-align:left` → `text-align:start` (reads document direction)

**Option C — Framework-level RTL (React, Vue):**

Use a plugin/library:
- **React:** `react-with-direction`, `styled-components-rtl`
- **Vue:** `vue-i18n` with RTL direction switching
- **Tailwind CSS:** Built-in RTL support via `dir="rtl"` on `<html>` (utility classes auto-flip)

### G3. Social: Duplicating LTR design as RTL

In Figma/Illustrator:

1. **Duplicate artboard/canvas**
2. **Flip layout manually:**
   - Move logo from top-left to top-right
   - Re-align text frames from left to right
   - Move CTA from bottom-right to bottom-left
3. **Change text:**
   - Replace English copy with Arabic
   - Set text alignment to RIGHT in properties
4. **Change fonts:**
   - Swap Latin fonts to Arabic equivalents (Azm X, Thmanyah Serif Display, IBM Plex Sans Arabic)
5. **Flip arrows/chevrons:** Use `‹` and `←` for RTL

**Do NOT use horizontal flip:** Flipping the entire artboard mirrors text (unreadable).
Manual repositioning is required.

---

## H. RESOURCES AND TOOLING

### H1. Fonts (Arabic)

**AZMX Brand Fonts (hosted on CDN):**
- **Azm X** (sans-serif, information): Regular (400), Medium (500), SemiBold (600), Bold (700)
- **Thmanyah Serif Display** (serif, personality): Regular (400), Medium (500), Bold (700)
- CDN: `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@<commit-sha>/`

**Fallback Fonts (Google Fonts, free):**
- **IBM Plex Sans Arabic:** Excellent Arabic support, professional
  - `<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap" rel="stylesheet">`

**System Fonts (no download, acceptable degradation):**
- macOS/iOS: SF Arabic (SF Pro Text with Arabic glyphs)
- Android: Roboto Arabic / Noto Sans Arabic
- Windows: Segoe UI Arabic / Tahoma

### H2. Testing Tools

**Email testing:**
- **Litmus / Email on Acid:** Multi-client preview (Gmail, Outlook, Apple Mail, etc.)
- **Brevo (SendinBlue):** ESP with inline HTML editor (used for AZMX newsletters)
- **Manual test sends:** Create a test list with Gmail, iCloud, Outlook addresses

**RTL layout debugging:**
- **Browser DevTools:** Toggle `dir` attribute in Elements panel (Chrome/Firefox)
- **Responsively App:** Test multiple screen sizes simultaneously (https://responsively.app)
- **iframe harness (email):** Embed email HTML in iframe at 360px/375px/430px to catch overflow (see [`../Newsletter/docs/qa-checklist.md`](../Newsletter/docs/qa-checklist.md))

**Design tools:**
- **Figma:** Right-to-left text plugin (search "RTL" in Figma Community)
- **Illustrator:** Paragraph panel → set direction to RTL (World-Ready Composer)

### H3. Reference Documents (within AZMX brand repo)

- **Email system:** [`references/email-design-system.md`](email-design-system.md)
- **Newsletter QA:** [`Newsletter/docs/qa-checklist.md`](../Newsletter/docs/qa-checklist.md)
- **Newsletter tech ref:** [`Newsletter/docs/technical-reference.md`](../Newsletter/docs/technical-reference.md)
- **Social templates:** `Social Media/templates/` (platform-specific)
- **Brand CDN:** `Gamaleldientarek/azmx-brand-cdn` (GitHub repo, immutable commits)

### H4. Unicode References (for RTL characters)

| Character | Unicode | HTML Entity | Usage |
|-----------|---------|-------------|-------|
| Left-pointing chevron `‹` | U+2039 | `&#8249;` | Primary directional mark in RTL |
| Right-pointing chevron `›` | U+203A | `&#8250;` | LTR only (avoid in Arabic context) |
| Left arrow `←` | U+2190 | `&larr;` / `&#8592;` | "Forward" in RTL context |
| Right arrow `→` | U+2192 | `&rarr;` / `&#8594;` | "Back" in RTL context |
| Arabic comma `،` | U+060C | `&#1548;` | Preferred in Arabic text (optional) |
| Arabic question mark `؟` | U+061F | `&#1567;` | Preferred in Arabic text (optional) |
| Arabic-Indic digits `٠–٩` | U+0660–0669 | `&#1632;`–`&#1641;` | Alternative to Western 0–9 |
| Kashida (tatweel) `ـ` | U+0640 | `&#1600;` | Use sparingly; prefer copy-paste from assets |
| Zero-width joiner | U+200D | `&#8205;` | Force ligature connection (advanced) |
| Left-to-right mark (LRM) | U+200E | `&lrm;` / `&#8206;` | Force LTR at boundary (rare use) |
| Right-to-left mark (RLM) | U+200F | `&rlm;` / `&#8207;` | Force RTL at boundary (rare use) |

---

## I. CHANGELOG AND VERSION HISTORY

**v1.0 (2026-09-08)** — Initial master RTL guide
- Extracted universal RTL principles from production newsletter (June 2026 edition)
- Documented format-specific patterns for email, social, web, PDF, presentations
- Added cross-format code examples (email hero, social layout, React component, PDF template)
- Comprehensive gotchas table covering all common RTL rendering issues
- Platform-specific rendering quirks (Gmail, Outlook, Instagram, Chrome, etc.)
- QA checklist covering visual, technical, content, accessibility, and brand consistency
- Migration notes for converting LTR assets to RTL
- Tooling and resources section (fonts, testing tools, Unicode reference)

**Scope of v1:** Arabic RTL only. English/LTR patterns are OUT OF SCOPE (separate doc, future).

**Future additions (v2 roadmap, not yet implemented):**
- LTR English edition of this guide (mirrored rules)
- Web component RTL patterns (once AZMX website is live)
- Video/motion graphics RTL guidelines (title cards, lower-thirds, animations)
- Bilingual layouts (Arabic primary, English secondary in same deliverable)
- Advanced bidi edge cases (mixed nesting, complex math/code snippets in RTL context)

---

*This guide is the SOURCE OF TRUTH for RTL layout across all AZMX deliverables. Format-specific
docs (email-design-system.md, social templates) outrank it in their domain's details; this
guide outranks them in universal RTL principles. When in doubt, test in production clients
(Gmail for email, Instagram for social) — rendering reality beats theory.*

**Questions or RTL issues?** Check the QA checklist (§F) and gotchas table (§D) first. For
email-specific problems, cross-reference [`email-design-system.md`](email-design-system.md)
§A1 (Arabic RTL rules) and the newsletter QA flow. For new edge cases not covered here,
document them and propose an addition to this guide.
