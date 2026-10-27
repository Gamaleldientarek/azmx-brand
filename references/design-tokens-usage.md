# AZM X Design Tokens — How to use them

Five collections, 550 tokens, two independent switches. This is the whole system in one page.

> **v3.0.0 (27 Oct 2026): the AZM X Design System is the source for every AZM X design, Figma included** (see `design-system-link.md`). The token file now carries the owner's rulings: dark grounds are black in every palette, `text/heading` is Neutral 900, spacing is the site scale named by value (`space/0` … `space/200`), and radius uses the design system's names (`xs 4 · sm 8 · md 12 · lg 16 · xl 24 · full`). **The Figma library's variables still hold the old values** (navy grounds and headings, `space/2xs`…, `radius/sm` = 4) until the library is updated. Bind by the values on this page, not by the old names.

---

## 1. The rule that matters most

**Bind to Semantic. Never to Primitives.**

```
1. Primitives  →  1b. Palette  →  2. Semantic  →  3. Component
                                        ↑
                                  you bind here
```

Primitives are hidden from publishing and carry **no scopes**, so they will not appear in any Figma picker. That is deliberate. If you cannot find a colour in the picker, you are reaching for the wrong tier — the answer is a semantic token, or a new one, never a primitive.

Component tokens exist for the nine wired components. Use them **only inside those components' main definitions**, never on a loose layer.

---

## 2. The two switches

Any frame carries two settings that resolve independently:

| Switch | Options | Controls |
|---|---|---|
| **1b. Palette** | Blue · Orange · Green · Yellow · Purple · Red | Accents, dark grounds, the brand gradient |
| **2. Semantic** | Light · Dark | The theme |

Twelve combinations. One set of bindings. Nothing duplicated.

**To make a deck run in the orange palette:** select the top-level frame or section → Layer panel → set `1b. Palette` to `Orange`. Every accent, every dark ground and the gradient follow. Hospitals Report is already set this way.

**Blue is the default.** Whatever the palette, the dark ground is black.

---

## 3. Picking a colour

**All text tokens in this system meet WCAG AA contrast requirements (4.5:1) across all twelve palette-and-mode combinations.** This is validated by `brand-check.py` and enforced through automated checks. When adding new tokens or colour values, run the validator to ensure continued compliance.

### Surfaces

| Token | Light | Use |
|---|---|---|
| `surface/page` | White | The default ground |
| `surface/raised` | palette tint | Panels, table zebra |
| `surface/sunken` | Neutral 100 | Wells, recessed areas |
| `surface/inverse` | black | The dark surface, in every palette |
| `surface/accent` | palette signature | Accent fill. **Never behind body text** |
| `surface/accent-deep` | palette deep anchor | Heavy accent block, e.g. a stage header |
| `surface/accent-light` | palette light anchor | A full-bleed section cover |
| `surface/muted` · `subtle` · `lightest` · `dark` · `deep` | neutrals | Quieter grounds |

### Text

| Token | Light | Use |
|---|---|---|
| `text/heading` | Neutral 900 | Headlines. The same ink as `text/primary` on light, but bind headings to `text/heading` |
| `text/primary` | Neutral 900 | Body copy |
| `text/secondary` | Neutral 600 | Supporting copy |
| `text/muted` | Neutral 500 | Captions, metadata |
| `text/accent` | palette text-safe step | Eyebrows, key numerals, the one highlighted word |
| `text/inverse` | White | Text on an inverse surface |
| `text/on-accent` | computed | Text **on** an accent fill |
| `text/on-image` · `on-image-body` · `on-image-eyebrow` | White · Blue 100 · Light Blue | Text over photography |

**`text/accent` is not the signature colour.** Blue keeps Electric because Electric is dark and reads at 8.1:1. Every secondary drops to its first text-safe step, because their signatures are vivid *light* tones — white on yellow `#FED340` is 1.44:1. Use `surface/accent` when you want the signature as a fill; use `text/accent` when it has to be legible.

### Borders

`border/subtle` → `default` → `strong` → `dark`, plus `border/accent`, `accent-inverse`, `accent-deep`, `heading`, `inverse`, `faint`.

All border tokens are also valid as **fills**, because a hairline drawn as a 1px rectangle is still a border. That is why the HR forms tables work.

### Status

`status/{success|warning|danger|info|caution}/{text|bg|border|wash}`

Every text-on-bg pairing measures **4.5:1 or better in both themes**. `status/info/*` stays blue by definition and does **not** follow the palette — otherwise an orange deck's info state would be indistinguishable from its accent.

`status/dot/{red|yellow|green}` are the RAG data dots. Fixed in both modes. They are the only sanctioned AZM X use of red, yellow and green outside a palette.

---

## 4. Type

Two ramps. Never a third.

**Display** — thmanyah serif. Titles, stats, quotes, numerals. Leading ×0.95.

```
2xs 30/29   xs 36/34   sm 48/46   md 60/57   lg 80/76
xl 100/95   2xl 120/114   3xl 160/152   4xl 200/190   5xl 240/228
```

**Body** — Azm X Variable. Everything else. Leading ×1.5.

```
2xs 12/18   xs 14/22   sm 16/24   md 18/28   lg 20/30   xl 24/36   2xl 28/42
```

Each step is two tokens: `type/display/lg/size` and `type/display/lg/line`.

Tracking: use `type/tracking/normal` (0) everywhere (v3.0.0). Arabic is never tracked, and eyebrows are no longer tracked or UPPERCASE; they use the design system's `label-lg` (Azm X Medium 14 px). `slight`, `wide` and `wider` remain in the file for old layouts only.

**Twelve text styles** are already bound to these tokens — `Display/Hero`, `Display/Title`, `Display/Section`, `Display/Stat`, `Body/Default`, `Label/Eyebrow` and so on. **Use the text style, not the raw tokens**, unless you need something the styles do not cover. The styles are why the scale cannot drift again.

Serif carries personality, sans carries information. Never body copy in serif, never a hero in sans.

---

## 5. Spacing, radius, borders

**Spacing: the site scale, named by value. These are the only permitted values.**

```
space/0 · 2 · 4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64 · 80 · 96 · 120 · 160 · 200
```

It's the AZM X Design System's scale, taken from azmx.sa (owner decision, 27 Oct 2026). The old t-shirt names (`space/2xs` = 16, `space/md` = 64…) and the "never 12, never 20" rule are retired. Section padding on the web is 120 / 48 on desktop and 80 / 32 or 80 / 20 on smaller screens; heroes start at 160 or 200.

**Radius:** `none 0 · xs 4 · sm 8 · md 12 · lg 16 · xl 24 · full`, the design system's names. Buttons, fields, tabs and small media use `sm` (8); cards and panels use `md` (12). The 2 px step is gone, and `pill` is now `full`.

**Border width:** `none 0 · thin 0.5 · hairline 1 · medium 2 · thick 4 · heavy 8`
The brand's 1px rule is `border-width/hairline`, in the neutral `border/subtle` colour, only where structure needs it. `thin` renders inconsistently below 1×, so prefer hairline. **No coloured lines**: `border/accent` and its variants are never a side line, underline or bar (owner decision, 27 Oct 2026); the footer and case-study rule tokens now point at `border/subtle`.

---

## 6. Icons

Phosphor Icons, weight Regular. Ask before adding any.

`icon/default` · `accent` · `secondary` · `muted` · `inverse` · `on-image`
`icon/size/inline` 20 · `standalone` 24 · `feature` 32

`icon/accent` uses the text-safe step, not the signature, for the same reason as `text/accent`. On dark it drops to the light accent — **Electric never appears as an icon on a dark ground.**

---

## 7. The gradient

`gradient/start` → `mid` → `mid-alt` → `end`, 145°, event surfaces only: covers, dividers, closings. Never behind body copy.

It follows the palette:

```
Blue     #000000 → #01006E → #0200D3 → #001AFF
Orange   #000000 → #5A2D1B → #A1502F → #F47A48
Green    #000000 → #0D4829 → #168049 → #22C36F
Yellow   #000000 → #693F02 → #895F0F → #FED340
Purple   #000000 → #2E0068 → #7341AD → #C68FFF
Red      #000000 → #5E1016 → #A81C27 → #FF2B3C
```

Every palette starts at black (v3.0.0). The azmx.sa footer animates the blue version: see "The animated footer gradient" in `SKILL.md`.

There is also a paint style, `Brand/Gradient · Event surfaces`, holding the blue version at the canonical angle. Its first stop is still navy in the Figma library; set it to black when the library is updated.

---

## 8. What is out of bounds

**`brand/colab/*` and `brand/majarah/*`** live in Primitives so the sub-brand files can share one source. **Never apply them to an AZM X surface.** Load `colab-design` or `majarah-design` for that work. Colab's Electric and Jade greens are banned on light grounds (1.34:1 and 1.29:1).

**`color/feedback/*`** is UI state, not brand colour. It is not a palette.

**`color/rag/*`** is data dots only.

---

## 9. Adding a token

1. Does a semantic token already resolve to what you need? Use it.
2. If not, is the *value* in Primitives? Add a **semantic** that aliases it. Never bind the primitive.
3. If the value does not exist, add the primitive first, then the semantic.
4. Give it Light **and** Dark. A semantic with the same value in both modes is fine, but state why in the description.
5. Set scopes. An unscoped semantic will not appear in the picker and the migration tooling will not find it.
6. Measure contrast before you commit. Every text pairing in this system clears 4.5:1 in all twelve combinations, and that is worth keeping true. `text/subtle` and `icon/muted` have been updated to meet WCAG AA (4.5:1) and are now safe for all body text use.

---

## 10. Known gaps

| Gap | Detail |
|---|---|
| Purple and yellow `role-tint`, `role-border`, `role-mid` | **Derived**, not from the palette board. Marked as such in their descriptions. Replace if official values exist. |
| Off-scale values in the wild | 40px font size (51 uses). The 12px gaps are on the scale since v3.0.0 |
| Figma library | Still holds the pre-v3 values: navy grounds and headings, `space/2xs`… and `radius/sm` = 4, the gradient style's navy start. Update before the next export, or the export will undo the rulings |
| Unwired component groups | `card`, `meter`, `star-tile`, `heat` (Hospitals Report), `bg` (Gradient & Bks) — tokens exist, mains not yet bound |
| `Rating` component | A 16-colour CSAT/NPS ramp, still raw hex by decision |
| Line-height on Hospitals Report | AUTO and percentage throughout, so it cannot be tokenized without changing layout |

---

## 11. Where to look in Figma

The **Design Tokens** page carries the live documentation, all read from the variables themselves:

| Frame | What it shows |
|---|---|
| MAP · How the tokens link | Five lanes, every link a live alias, red dashed = unwired |
| PALETTES · Six hues, one structure | All six ramps, role anchors, and what each palette resolves to |
| CHAINS · A token walking all three tiers | Concrete chains with live values |
| FORK · Where Light and Dark split | Exactly where the theme branches |
| VALUES · Space, radius, border, opacity | Every value drawn at real size |
| VALUES · Type scale | Both ramps as live specimens |
| TEST / CARD TEST | The same bindings rendered in both modes |
