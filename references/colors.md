# AZMX Color Reference

Every tone in the system. Source of truth: `assets/tokens/azmx-tokens.json` (exported from the `Colors` Figma collection in the New Direction Library file, with the v3.0.0 rulings of 27 October 2026 applied), which the AZM X Design System also builds its colours from.

> **v3.0.0 (27 Oct 2026):** dark grounds are pure black `#000000` in every palette; headings on light are Neutral 900 `#111927`; the gradient starts at black; hairlines are the neutral `border/subtle` token; no coloured lines. Dark Navy `#040038` stays only as Blue 1000 and as the logo artwork's colour.

## Primary

| Token | Hex | Usage |
|---|---|---|
| Electric | `#001AFF` | Hero accent, call-to-attention, used like punctuation |
| Black | `#000000` | The dark ground: dark sections, dividers, closings, full-page bios, the email footer card |
| Neutral 900 | `#111927` | Body text and headings on light; the raised surface (cards, menus) on black |
| Light Blue | `#5D8FFF` | Dark-surface accent partner, safe for large soft fills |
| White | `#FFFFFF` | Editorial light workhorse surface, text on dark |

## Blue ramp (50 to 1000)

| Step | Hex | Notes |
|---|---|---|
| Blue 50 | `#F0F5FF` | Soft light surface: panels, table zebra, image backings |
| Blue 100 | `#DDE8FF` | Body text on dark |
| Blue 200 | `#BFD5FF` | Meta and caption text on dark |
| Blue 300 | `#93B6FF` | |
| Blue 400 | `#5D8FFF` | Equals Light Blue |
| Blue 500 | `#2661FF` | |
| Blue 600 | `#001AFF` | Equals Electric |
| Blue 700 | `#0200D3` | Gradient mid-alt stop |
| Blue 800 | `#01009B` | |
| Blue 900 | `#01006E` | Cover gradient mid-stop |
| Blue 950 | `#010040` | |
| Blue 1000 | `#040038` | Dark Navy: the logo artwork's colour. No longer a ground, a heading colour or the gradient start |

## Neutrals (25 to 950)

| Step | Hex | Notes |
|---|---|---|
| Neutral 25 | `#FCFCFD` | |
| Neutral 50 | `#F9FAFB` | |
| Neutral 100 | `#F3F4F6` | |
| Neutral 200 | `#E5E7EB` | Grey image-placeholder fill |
| Neutral 300 | `#D2D6DB` | |
| Neutral 400 | `#9DA4AE` | |
| Neutral 500 | `#6C737F` | |
| Neutral 600 | `#4D5761` | |
| Neutral 700 | `#384250` | |
| Neutral 800 | `#1F2A37` | |
| Neutral 900 | `#111927` | Body text and headings on light; raised surface on black |
| Neutral 950 | `#0D121C` | Deepest neutral |

## The five secondary palettes

These are **full palettes**, not accent colours. Any one of them can carry an entire deliverable — the Hospitals Report runs in orange end to end. A deck picks one palette, and its accent and gradient follow. The dark ground stays black in every palette. Never mix two palettes on one surface.

| Palette | Signature | Deep | First text-safe step on white | Tint (step 100), for soft panels |
|---|---|---|---|---|
| Orange | `#F47A48` | `#842C09` | `color/orange/700` `#A1502F` | `#FDECE5` |
| Green | `#22C36F` | `#012F02` | `color/green/700` `#168049` | `#E0F7EB` |
| Yellow | `#FED340` | `#693F02` | `color/yellow/800` `#895F0F` | `#FFF9E4` |
| Purple | `#C68FFF` | `#2E0068` | `color/purple/700` `#7341AD` | `#F7EFFF` |
| Red | `#FF2B3C` | `#640000` | `color/red/700` `#A81C27` | `#FFE1E4` |

A tinted panel is how a pull quote, a highlight or a key item stands out (never a coloured line).

Each runs a full twelve-step ramp, `color/{hue}/50` through `1000`, plus five `role-*` anchors holding the original palette-board values exactly.

**The signature is a fill colour, not a text colour.** Every secondary signature is a vivid light tone — white on yellow `#FED340` measures **1.44:1**. Blue is the exception because Electric is dark. In Figma the token system handles this: `surface/accent` gives the signature, `text/accent` gives the first legible step for whichever palette is active.

### RAG data dots

Separate from the palettes and unaffected by which one a deck runs in. 10px dots, no coloured labels.

| Token | Hex | Meaning |
|---|---|---|
| `color/rag/red` | `#FF2B3C` | High risk or impact |
| `color/rag/yellow` | `#FED340` | Medium |
| `color/rag/green` | `#22C36F` | Low |

### UI feedback

`color/feedback/{success|warning|danger|info|caution}/{tint|border|mid|deep}` — form and alert states, not brand colour, not a palette. Every text-on-background pairing clears 4.5:1 in both themes.

The complete live export of all 550 variables across the five collections is in `figma-tokens.md`. How to apply them is in `design-tokens-usage.md`.

## Surfaces

| Surface | Fill | Use for |
|---|---|---|
| Black | `#000000` | Dark sections, dividers, capability pages, closings, full-page bios, in every palette |
| Neutral 900 | `#111927` | A raised card or menu on a black section |
| White | `#FFFFFF` | Default content |
| Blue 50 | `#F0F5FF` | Secondary light panels, table zebra, soft section breaks (the palette tint in other palettes) |
| Gradient | `#000000` to `#001AFF` at 145 degrees, mid-stop `#01006E` at 55% | Event surfaces only: cover, dividers, closing. It always starts at black and ends at the palette's signature |

The azmx.sa footer animates the gradient (the `AZMXFooterGradient` component, WebGL on black, a 26-second loop that follows the cursor). Its still fallback is a radial gradient over black: `#B5D4E9` 0 %, `#267EE3` 35 %, `#052DB6` 55 %, `#000038` 76 %, transparent at 100 %, anchored bottom-left.

## Text color by surface

| Surface | Title | Body | Eyebrow | Meta / caption |
|---|---|---|---|---|
| Black or gradient | White `#FFFFFF` | Blue 100 `#DDE8FF` at 88% | Light Blue `#5D8FFF` | Blue 200 `#BFD5FF` at 70% |
| White | Neutral 900 `#111927` | Neutral 900 `#111927` | Electric `#001AFF` | Neutral 500 `#6C737F` |
| Blue 50 | Neutral 900 `#111927` | Neutral 900 `#111927` | Electric `#001AFF` | Neutral 500 `#6C737F` |

Eyebrows are the `label-lg` style: Azm X Medium 14 px, written as is, no UPPERCASE, no tracking.

## The two-blues rule

The most important color rule in the system:

- **Electric `#001AFF`** is the primary accent on light surfaces. Sparse and decisive, like punctuation. Never a large fill behind text (it vibrates), never small Electric text on black (contrast fails).
- **Light Blue `#5D8FFF`** is the accent on dark surfaces, where Electric would be too dim. Also fine for large soft fills.

## Hairlines

1 px, neutral, the `border/subtle` token: Neutral 200 `#E5E7EB` on light, white at 20 % on black. Only where structure needs them: table rows, field outlines, a box's frame.

**No coloured lines, ever** (owner decision, 27 Oct 2026): no Electric or Light Blue rule, side line, underline, top bar or quote bar on anything. Show the selected or important item as a filled shape instead: a black pill, a Neutral 100 pill, a tinted panel.
