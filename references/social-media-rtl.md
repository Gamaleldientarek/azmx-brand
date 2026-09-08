# AZMX Social Media RTL Layout Guide

RTL layout rules for AZMX Arabic social media content across Instagram, LinkedIn, and Twitter/X. Every rule here extends the RTL foundation established in [`email-design-system.md`](email-design-system.md) §A1 to platform-native formats: image compositions, carousel slides, video overlays, and text-heavy graphics.

**Companion references:**

- [`email-design-system.md`](email-design-system.md) — foundational RTL rules (chevron direction, bidi wrapping, kashida handling)
- [`content-prompts.md`](content-prompts.md) — the social customization prompts that produce the copy these layouts display
- [`voice-and-tone.md`](voice-and-tone.md) — house rules: no emojis in copy, 3 hashtags maximum

**Scope:** this guide governs **designed graphics and video overlays** — static posts, carousel slides, story frames, video thumbnails, and text-on-image compositions. It does NOT govern plain-text-only posts (those follow platform defaults). For email RTL, use the email design system exclusively; these rules do not carry back to HTML email.

---

## A. UNIVERSAL RTL RULES — apply to every platform

### A1. Text direction and alignment (non-negotiable)

1. **All Arabic text is right-aligned.** Never center Arabic body text or paragraph blocks — centering is reserved for standalone headline moments (quote cards, hero titles) where symmetry is the design intent.

2. **Reading flow is right-to-left.** When text and image sit side-by-side, Arabic text occupies the RIGHT panel and the image occupies the LEFT. LTR layouts place text left and image right; RTL mirrors this.

3. **Visual hierarchy reads right-to-left.** The "primary" or "hero" element sits at the RIGHT edge; secondary/supporting content flows leftward. Example: a 2-card comparison layout places Card A (the main option) on the RIGHT, Card B (the alternative) on the LEFT.

4. **Chevrons, arrows, and directional glyphs point LEFT** (`‹` U+2039) and sit inside Unicode isolation markers to prevent the bidi algorithm from mirroring them. In design tools (Figma, Photoshop), this means:
   - Type the LEFT-POINTING SINGLE ANGLE QUOTATION MARK (`‹`) directly; do NOT type a right-pointing glyph and assume the canvas will auto-flip it.
   - Embed Latin/numeric fragments in LEFT-TO-RIGHT ISOLATE markers (U+2066 … U+2069) or set them as separate LTR text boxes to prevent run reversal.

5. **Kashida-stretched wordmarks are placed as image assets, never retyped.** If a graphic includes the AZMX wordmark or a stretched headline (e.g., «وش صـــار؟»), import the official vector or raster asset. Typing it by hand always produces wrong glyph joins.

6. **Numerals and dates are LTR, always.** Arabic content uses Western Arabic numerals (`0123456789`), and they are LEFT-TO-RIGHT even inside RTL text. A date formatted as `13 يوليو 2026` has the numeral `13` reading left-to-right (1 before 3), NOT right-to-left. Set numerals in a separate LTR text box or wrap them in LTR isolation markers.

### A2. Margin and padding mirroring

RTL layout requires mirroring the SPACING, not just the text alignment. If an LTR design specifies:

```
margin-left: 32px;
margin-right: 16px;
```

The RTL equivalent is:

```
margin-left: 16px;
margin-right: 32px;
```

**Applied to social graphics:**

- **Card padding:** if an LTR card has 24px padding on the left (away from the edge) and 16px on the right (near the edge), the RTL version has 16px left, 24px right.
- **Text inset from image edge:** LTR text sitting 40px from the left canvas edge should sit 40px from the RIGHT edge in RTL.
- **Icon-to-text gap:** an icon 12px to the LEFT of a text label in LTR sits 12px to the RIGHT of the label in RTL.

Figma and Photoshop do NOT auto-mirror padding. You must manually adjust every spacing value.

### A3. Font system (inherited from email)

Arabic social graphics use the same 2-tier fallback as email:

**Layer 1 — brand webfonts** (when exporting to SVG or web-rendered formats like HTML5 banners):

- **Serif** (personality): Thmanyah Serif Display, weights 400/500/700 — hero titles, pull-quotes, section headers
- **Sans** (information): Azm X, weights 400/500/600/700 — body, captions, labels, pills, buttons

**Layer 2 — system fallback** (when rasterizing to PNG/JPEG or exporting to platforms that strip webfonts):

- **IBM Plex Sans Arabic** (Google Fonts, preload it in design tools)
- **SF Arabic / Segoe UI** (final platform fallback)

**No letter-spacing on Arabic text.** Kashida does the stretching; tracking is only applied to the LTR chevron trio (4–6px) and Latin acronyms.

**Type scale** (from the email system, adapted to social):

| Use case | Size/weight | Font | Notes |
|---|---|---|---|
| Hero title (quote card, story header) | 48–72px / 700 | Serif | Mobile: scale to 36–52px |
| Section title / card header | 28–36px / 700 | Serif | The "big statement" |
| Body text / caption | 17–20px / 400 | Sans | Line-height 1.6–1.8 |
| Meta / pill / small label | 13–15px / 600 | Sans | Buttons, tags, eyebrows |
| Micro (legal, attribution) | 11–12px / 400 | Sans | Footer, credit lines |

**Color** follows the email design system's token map (§B1 in `email-design-system.md`). Default theme: `{dark}` #040038 for headlines, `{primary}` #001AFF for accents, `{text}` #111927 for body on light, `{on-dark}` #DDE8FF for body on dark.

### A4. Platform export specs

| Platform | Primary format | Size (px) | Ratio | Notes |
|---|---|---|---|---|
| **Instagram Feed** | JPEG / PNG | 1080×1080 | 1:1 | Also supports 4:5 (1080×1350) for vertical |
| **Instagram Story** | JPEG / PNG | 1080×1920 | 9:16 | Safe zone: 1080×1420 (top 250px, bottom 250px are UI) |
| **Instagram Carousel** | JPEG / PNG | 1080×1080 per slide | 1:1 | Max 10 slides |
| **LinkedIn Single Image** | JPEG / PNG | 1200×627 | ~1.91:1 | Also supports 1:1 (1200×1200) |
| **LinkedIn Carousel** | PDF | 1080×1080 per page | 1:1 | Upload as PDF, max 10 pages; also accepts native document |
| **Twitter/X Single Image** | JPEG / PNG | 1200×675 | 16:9 | Also supports 1:1 and 2:1 |
| **Twitter/X Card** | JPEG / PNG | 1200×628 | ~1.91:1 | Branded moment layout |

**File size:** keep under 5 MB for Instagram, 10 MB for LinkedIn/Twitter. **Color space:** sRGB, not Adobe RGB or Display P3 (platforms strip profiles and shift color). **Compression:** JPEG quality 80–85 for photos, PNG for graphics with text/transparency.

---

## B. PLATFORM-SPECIFIC RTL CONSIDERATIONS

### B1. Instagram — visual storytelling, text is accent not body

**Medium voice:** Instagram is VISUAL-FIRST. Text on the image is sparse — a headline, a stat, a pull-quote — and the caption carries the story. Dense paragraph blocks do NOT belong on an Instagram graphic.

**RTL layout patterns:**

**Pattern 1 — Quote card (1:1 feed post or 9:16 story):**

```
┌─────────────────────────────┐
│                             │
│             ‹ ‹ ‹           │ ← chevron trio, top-right or centered
│                             │
│  "‏اقتباس قصير ومؤثر"      │ ← serif 48–60px, right-aligned or centered, `{dark}` on light or white on dark
│                             │
│          — المصدر           │ ← attribution, sans 15px, centered or right-aligned
│                             │
└─────────────────────────────┘
```

**Text placement:** quote sits in the RIGHT 75% of the canvas (for right-alignment) or dead center (for symmetry). Attribution sits BELOW the quote, never above. Chevrons are decorative punctuation at the top-right or centered above the quote.

**Pattern 2 — Stat highlight (single-number story):**

```
┌─────────────────────────────┐
│                             │
│                      ٪٨٥    │ ← numeral, LTR, serif 72–96px, `{primary}`, top-right quadrant
│                             │
│  من الشركات السعودية        │ ← explainer, sans 20px, right-aligned, `{text}`, middle-right
│    تعتمد على الحلول         │
│        الرقمية              │
│                             │
│         azmx.sa         [→] │ ← source/CTA, micro sans 12px, bottom-left (LTR element)
└─────────────────────────────┘
```

**RTL rule:** the BIG NUMBER sits at the TOP-RIGHT (the reading start). The Arabic explainer sits BELOW it, right-aligned. The Latin source/URL sits at BOTTOM-LEFT (it is an LTR element and does not participate in the RTL flow).

**Pattern 3 — Side-by-side text + image (carousel slide):**

```
┌─────────────────────────────┐
│  ┌──────────┐    ┌────────┐ │
│  │  Arabic  │    │ Image  │ │ ← text RIGHT, image LEFT
│  │  headline│    │        │ │
│  │  + body  │    │        │ │
│  └──────────┘    └────────┘ │
└─────────────────────────────┘
```

**RTL rule:** text occupies the RIGHT 50–60%, image occupies the LEFT 40–50%. If the design includes a vertical accent bar or color block, it sits on the RIGHT edge of the text panel (the "near" edge), not the left.

**Story safe zone (9:16):** top 250px and bottom 250px are occluded by the username bar and the CTA tray. Keep critical text (headlines, stats) within the middle 1080×1420 zone. The AZMX logo or attribution CAN sit in the bottom-250px zone (it will be partially covered but readable).

**Instagram-specific RTL gotchas:**

- **No dense paragraphs on the canvas.** If the copy is longer than 2 lines, move it to the caption. The image holds the HOOK, not the essay.
- **Hashtags live in the caption, never burned into the graphic.** (House rule: 3 maximum, at the end.)
- **Emoji ban applies to graphics AND captions.** The deck encouraged emojis on Instagram; `voice-and-tone.md` overrides this. No emojis anywhere.
- **Carousel slides read RIGHT-TO-LEFT.** Slide 1 is the rightmost position in the stack (Instagram's carousel UI is LTR, but the CONTENT flow is RTL for Arabic). Design the slides so the visual narrative progresses 1→2→3 as the user swipes LEFT.

### B2. LinkedIn — professional authority, text-heavy graphics allowed

**Medium voice:** LinkedIn tolerates MORE TEXT on the image than Instagram. A well-designed LinkedIn graphic can carry 3–4 short paragraphs, a bulleted list, or a multi-point framework — as long as it is READABLE and adds value.

**RTL layout patterns:**

**Pattern 1 — Insight card (1.91:1 single image or 1:1 carousel page):**

```
┌───────────────────────────────────────┐
│ ‹ ‹ ‹                                 │ ← eyebrow chevrons, top-right
│ عنوان رئيسي: نقطة رئيسية              │ ← serif 32–40px, right-aligned, `{dark}`
│                                       │
│ • النقطة الأولى من التحليل            │ ← sans 18px, right-aligned bullets
│ • النقطة الثانية                     │
│ • النقطة الثالثة                     │
│                                       │
│         [Logo]     azmx.sa            │ ← bottom-right: logo + URL
└───────────────────────────────────────┘
```

**RTL rule:** headline at top-right, bulleted list below it (right-aligned bullets: the bullet glyph sits to the RIGHT of the text, not the left — use a REVERSED bullet character `◂` or a custom SVG bullet if the design tool does not auto-mirror). Logo and URL anchor BOTTOM-RIGHT (the "end" position in RTL).

**Pattern 2 — Numbered framework (carousel: 1 intro + 3–5 point slides):**

```
Slide 1 (intro):
┌───────────────────────────────────────┐
│                                       │
│           ٥ خطوات لـ...               │ ← serif 48px, centered or right-aligned
│                                       │
│      اسحب لليسار لقراءة الخطوات      │ ← instruction, sans 16px, centered
│                   ←                   │ ← arrow pointing LEFT (swipe direction)
│                                       │
└───────────────────────────────────────┘

Slide 2 (point 1):
┌───────────────────────────────────────┐
│                                ١      │ ← numeral (LTR), top-right, `{primary}`, 64px
│                                       │
│ عنوان الخطوة الأولى                   │ ← serif 32px, right-aligned
│                                       │
│ شرح مختصر للنقطة، سطرين أو ثلاثة.     │ ← sans 18px, right-aligned, `{text}`
│                                       │
└───────────────────────────────────────┘
```

**RTL rule:** the NUMERAL sits at TOP-RIGHT (the reading start). The headline sits below it, right-aligned. Body text flows from right to left. Repeat for slides 3–6.

**Pattern 3 — Data comparison (side-by-side stats):**

```
┌───────────────────────────────────────┐
│                                       │
│   الخيار أ        |      الخيار ب     │ ← headers right-to-left (A is RIGHT/primary, B is LEFT/secondary)
│                                       │
│      ٪٨٥          |         ٪٦٢       │ ← numerals, `{primary}` for A, `{text}` for B
│                                       │
│    معدل النجاح    |      معدل النجاح  │ ← explainer labels
│                                       │
└───────────────────────────────────────┘
```

**RTL rule:** the PRIMARY stat (A) sits on the RIGHT, the SECONDARY stat (B) sits on the LEFT. The vertical divider is centered. If one option is "better," place it on the right.

**LinkedIn-specific RTL gotchas:**

- **Carousel PDFs auto-number pages TOP-LEFT.** LinkedIn burns "1 / 5" in the top-left corner of each page. Do NOT place critical Arabic text in the top-left 200×100px zone — it will be covered by the page counter.
- **Long captions are expected.** LinkedIn posts can carry 150–200 words of analysis in the caption. The graphic is the HOOK; the caption is the SUBSTANCE. (This is the inverse of Instagram, where the graphic IS the substance.)
- **Hashtags: 3 maximum, at the end of the caption.** The deck said 3–5; house voice caps it at 3.
- **No emojis,** even though LinkedIn's professional audience might tolerate them. House rule applies everywhere.

### B3. Twitter/X — speed and impact, minimal text on graphic

**Medium voice:** Twitter is FAST. A user scrolls past 100 tweets in a minute. The graphic must land its point in <1 second. If the text on the image requires more than a glance to parse, it is too long.

**RTL layout patterns:**

**Pattern 1 — Single-stat card (16:9 or 1:1):**

```
┌───────────────────────────────────────┐
│                                       │
│                              ٪٩٢      │ ← numeral, serif 80–96px, top-right, `{primary}`
│                                       │
│         من المستخدمين يفضلون...       │ ← explainer, sans 22px, right-aligned, middle-right
│                                       │
│                 @byazmx               │ ← handle, bottom-center or bottom-left (LTR)
└───────────────────────────────────────┘
```

**RTL rule:** BIG NUMBER top-right, explainer below it (right-aligned), handle/attribution bottom-center or bottom-left (it is Latin/LTR and does not flow RTL).

**Pattern 2 — Quote card (1:1, optimized for retweets):**

```
┌───────────────────────────────────────┐
│                                       │
│  "‏اقتباس قصير يُعاد تغريده"         │ ← serif 40–52px, right-aligned or centered, `{dark}`
│                                       │
│               — المصدر                │ ← attribution, sans 16px, centered or right-aligned
│                                       │
│  ‹ ‹ ‹                    @byazmx     │ ← chevrons bottom-right (decorative), handle bottom-left
└───────────────────────────────────────┘
```

**RTL rule:** quote is right-aligned or centered (centered is stronger for shareability — it reads as a "statement card"). Attribution sits below the quote. Decorative chevrons sit at BOTTOM-RIGHT (RTL reading end). Handle sits at BOTTOM-LEFT (LTR element).

**Pattern 3 — Announcement card (new feature, event, launch):**

```
┌───────────────────────────────────────┐
│ ‹                                     │ ← single left-pointing chevron, top-right (brand accent)
│ إعلان: عنوان الميزة الجديدة           │ ← serif 36–44px, right-aligned, top-right quadrant
│                                       │
│ سطر واحد يشرح الفائدة.                │ ← sans 18px, right-aligned
│                                       │
│ [→ اقرأ المزيد]    azmx.sa/feature    │ ← CTA pill + URL, bottom-left (LTR direction)
└───────────────────────────────────────┘
```

**RTL rule:** headline and body right-aligned, CTA and URL at bottom-left (they point OUT of the card, leftward, which aligns with LTR "next step" directionality).

**Twitter-specific RTL gotchas:**

- **280-character caption limit.** The tweet text must carry the FULL message; the graphic is a visual echo, not a supplement. Do NOT hide critical information in the graphic that is not also in the tweet text.
- **Native Twitter cropping:** single images are cropped to ~2:1 in the timeline; the full image only shows on click. Keep the critical text (headline, stat) in the CENTER-RIGHT zone, NOT the top-right corner or bottom-right corner (those may be cropped).
- **GIFs and videos:** overlaid Arabic text must be LARGE (28px minimum) and HIGH-CONTRAST (white on dark, or dark on a 40%+ opacity overlay). Video subtitles are right-aligned, top-third or bottom-third of the frame (never center-middle — that is where faces sit).
- **Hashtags: 3 maximum, at the end of the tweet, NOT woven into the sentence.** The deck encouraged integrated hashtags ("نحن #نبني المستقبل"); house voice places them at the end as a discrete group.
- **No emojis,** even though Twitter is emoji-heavy. House rule: no emojis in copy, on any channel.

---

## C. RTL QA CHECKLIST — run before publishing any Arabic graphic

Before exporting a social graphic for Arabic content, verify:

- [ ] **Text direction:** all Arabic text is right-aligned (or intentionally centered for symmetry), never left-aligned
- [ ] **Chevrons and arrows:** all point LEFT (`‹`), never right (`›`)
- [ ] **Numerals and dates:** set as LTR (the digits read left-to-right: `13` not `31`)
- [ ] **Latin fragments:** English words, URLs, handles, and acronyms are set LTR (not reversed)
- [ ] **Spacing mirrored:** if the LTR version has 32px left margin, the RTL version has 32px RIGHT margin
- [ ] **Hierarchy flows right-to-left:** the primary element is on the RIGHT, secondary elements flow leftward
- [ ] **No letter-spacing on Arabic text** (unless it is a Latin-only label)
- [ ] **Kashida wordmarks are placed assets, not retyped**
- [ ] **Font fallback:** if exporting to raster (PNG/JPEG), the preview uses IBM Plex Sans Arabic or SF Arabic, not a Latin font rendering Arabic as tofu
- [ ] **Color contrast:** text on background meets WCAG AA (4.5:1 for body, 3:1 for large titles)
- [ ] **Safe zones respected:** Instagram story (middle 1420px), LinkedIn carousel (avoid top-left 200×100px), Twitter crop zone (center-right focus)
- [ ] **No emojis in the graphic** (house rule, all platforms)
- [ ] **Hashtags NOT burned into the graphic** (they live in the caption, max 3, at the end)

**Common RTL defects to catch:**

| Defect | What it looks like | How to fix |
|---|---|---|
| **Left-aligned Arabic text** | Text hugs the left edge, reading flow is broken | Set text-align: right in CSS, or use right-alignment in design tool |
| **Right-pointing chevron** (`›`) | Glyph points right instead of left | Replace with U+2039 `‹` and wrap in LTR isolate marker |
| **Reversed numerals** | Date shows as `6202` instead of `2026` | Set numeral text box to LTR direction |
| **Mirrored logo** | AZMX logo is flipped horizontally | Logos are NEVER mirrored. Use the same logo asset in LTR and RTL |
| **Unmirrored spacing** | Text sits 40px from left edge (should be 40px from RIGHT edge) | Manually adjust padding/margin values to mirror the LTR layout |
| **Latin text reading right-to-left** | URL shows as `as.xmza` instead of `azmx.sa` | Set Latin text box to LTR direction or wrap in LTR isolate marker |

---

## D. WORKED EXAMPLES — 3 real-world graphics, LTR → RTL transformation

### Example 1: Instagram quote card (1:1 feed post)

**LTR version (English):**

```
┌─────────────────────────────┐
│                             │
│ › › ›                       │ ← chevrons top-left
│                             │
│ "A short, impactful quote   │ ← serif 52px, left-aligned, `{dark}`
│  that fits in two lines."   │
│                             │
│ — Source Name               │ ← attribution, sans 15px, left-aligned
│                             │
│               azmx.sa   [logo] │ ← URL bottom-left, logo bottom-right
└─────────────────────────────┘
```

**RTL version (Arabic):**

```
┌─────────────────────────────┐
│                             │
│           ‹ ‹ ‹             │ ← chevrons top-RIGHT (mirrored)
│                             │
│   "‏اقتباس قصير ومؤثر      │ ← serif 52px, RIGHT-aligned, `{dark}`
│      في سطرين."            │
│                             │
│           — اسم المصدر      │ ← attribution, sans 15px, RIGHT-aligned
│                             │
│ [logo]   azmx.sa            │ ← logo bottom-RIGHT, URL bottom-left (LTR element stays left)
└─────────────────────────────┘
```

**Transformation notes:**

- Chevrons: moved from top-left to top-RIGHT, glyph flipped from `›` to `‹`
- Text: re-aligned from left to RIGHT
- Logo: moved from bottom-right to bottom-LEFT (it anchors the RTL "end" position)
- URL: stays bottom-left (it is an LTR element; does not participate in RTL flow)

### Example 2: LinkedIn insight card (1.91:1 single image)

**LTR version (English):**

```
┌───────────────────────────────────────┐
│ › › ›                                 │ ← eyebrow chevrons, top-left
│ Key Insight: Main point here          │ ← serif 36px, left-aligned, `{dark}`
│                                       │
│ • First bullet point                  │ ← sans 18px, left-aligned bullets
│ • Second bullet point                 │
│ • Third bullet point                  │
│                                       │
│ azmx.sa     [Logo]                    │ ← bottom-left: URL, bottom-right: logo
└───────────────────────────────────────┘
```

**RTL version (Arabic):**

```
┌───────────────────────────────────────┐
│                                 ‹ ‹ ‹ │ ← eyebrow chevrons, top-RIGHT
│          نقطة رئيسية: رؤية أساسية     │ ← serif 36px, RIGHT-aligned, `{dark}`
│                                       │
│            • النقطة الأولى            │ ← sans 18px, RIGHT-aligned bullets (bullet glyph on the right)
│            • النقطة الثانية           │
│            • النقطة الثالثة           │
│                                       │
│         [Logo]     azmx.sa            │ ← bottom-RIGHT: logo, bottom-left: URL (LTR)
└───────────────────────────────────────┘
```

**Transformation notes:**

- Chevrons: top-left → top-RIGHT, `›` → `‹`
- Headline: left-aligned → RIGHT-aligned
- Bullets: left-aligned → RIGHT-aligned, bullet glyph position reversed (RIGHT of text, not left)
- Logo and URL: swapped positions (logo to bottom-right, URL to bottom-left)

### Example 3: Twitter stat card (16:9)

**LTR version (English):**

```
┌───────────────────────────────────────┐
│                                       │
│ 92%                                   │ ← numeral, serif 88px, top-left, `{primary}`
│                                       │
│ of users prefer...                    │ ← explainer, sans 24px, left-aligned, middle-left
│                                       │
│               @byazmx                 │ ← handle, bottom-center
└───────────────────────────────────────┘
```

**RTL version (Arabic):**

```
┌───────────────────────────────────────┐
│                                       │
│                              ٪٩٢      │ ← numeral, serif 88px, top-RIGHT, `{primary}` (NOTE: the % sign is AFTER the number in Arabic)
│                                       │
│         من المستخدمين يفضلون...       │ ← explainer, sans 24px, RIGHT-aligned, middle-right
│                                       │
│               @byazmx                 │ ← handle, bottom-center (unchanged; it is an LTR element)
└───────────────────────────────────────┘
```

**Transformation notes:**

- Numeral: top-left → top-RIGHT
- Percent sign: `92%` (LTR: number first) → `٪٩٢` (Arabic: symbol first — but note that the numeral itself `92` still reads left-to-right, NOT right-to-left)
- Explainer: left-aligned → RIGHT-aligned, middle-left → middle-right
- Handle: stays bottom-center (it is an @ mention, which is an LTR construct)

---

## E. DESIGN TOOL SETUP — Figma and Photoshop RTL configuration

### E1. Figma

**Enable RTL text direction:**

1. Select the text layer
2. In the right panel, Design tab → Text section → **Paragraph** dropdown → **Text direction** → set to **Right-to-left**
3. Text alignment will auto-flip to right; if it does not, manually set **Align right**

**Handling mixed LTR/RTL (e.g., Arabic text with English URL):**

- Arabic text layer: set to RTL, right-aligned
- English/numeral layer: set to LTR, left-aligned (or manually positioned)
- Do NOT mix Arabic and English in a single text box unless you are comfortable debugging bidi algorithm edge cases

**Auto Layout and RTL:**

- Figma's Auto Layout does NOT auto-mirror for RTL. If an LTR auto-layout frame has `padding-left: 32px`, you must manually change it to `padding-right: 32px` for the RTL version.
- Horizontal Auto Layout direction: LTR uses `→` (left-to-right stacking), RTL uses `←` (right-to-left stacking). Change the direction arrow in the Auto Layout settings.

**Plugins:**

- **RTL Auto Layout** (community plugin): semi-automates padding/direction mirroring. Install it, but ALWAYS manually verify the result; the plugin misses custom overrides.

### E2. Photoshop

**Enable RTL paragraph direction:**

1. Select the text layer with the Type tool (T)
2. Window → Paragraph panel → open the panel menu (≡) → **Middle Eastern and South Asian Layout** (if not visible, enable it in Preferences → Type → Show Indic Options)
3. In the Paragraph panel, set **Paragraph direction** to **Right-to-Left**
4. Text alignment: click the **Align right** button

**Handling Arabic text with English/numerals:**

- Use SEPARATE text layers for Arabic (RTL) and English/numerals (LTR)
- Do NOT rely on Photoshop's bidi algorithm; it is fragile and breaks when you copy-paste text

**Layer alignment and distribution:**

- If an LTR composition has layers aligned to the left edge, the RTL version aligns them to the RIGHT edge.
- Use **Align > Right Edges** and **Distribute Horizontal Center** (both in the Layer menu or via the Move tool options bar).

**Exporting:**

- File → Export → Export As → JPEG/PNG, sRGB color space, quality 80–85 for JPEG
- Verify the exported image in a platform preview tool (upload to Instagram/LinkedIn as a draft) before publishing — sometimes the platform re-compresses and shifts color

---

*This guide governs designed social media graphics only. For plain-text posts (no graphic), the platform's native RTL handling applies. For email RTL, use [`email-design-system.md`](email-design-system.md) exclusively. For the copy that FILLS these layouts, see [`content-prompts.md`](content-prompts.md).*
