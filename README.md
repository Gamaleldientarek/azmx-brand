![AZMX Brand Skill](assets/cover.jpg)

# AZMX Brand Skill

[![Brand Skill Validation](https://github.com/Gamaleldientarek/azmx-brand/actions/workflows/validate.yml/badge.svg)](https://github.com/Gamaleldientarek/azmx-brand/actions)

The official AZMX brand and communication system, packaged as an Agent Skill for Claude Code and other AI agents. Install it once and every deliverable (decks, emails, reports, web pages, social graphics, documents, articles, campaigns) comes out in the AZMX identity without re-briefing the agent.

Deep navy, electric blue, generous white space, serif personality, the chevron as the only graphic device. Restraint is the luxury.

As of v1.4.0 the skill also encodes the AZM X Unified Communication Strategy: five brand voices, eight audience personas with their approved core messages, seven channels with owners and metrics, the editorial cadence, and ready-to-run content prompts.

**[Browse the image library →](https://gamaleldientarek.github.io/azmx-brand/)** — all 240 brand images, click any one to download. No account needed.

**[Explore design tokens →](https://gamaleldientarek.github.io/azmx-brand/tokens.html)** — interactive token explorer with live previews, search, filtering, and copy-to-clipboard. Browse all 550 tokens across five collections.

## What's inside

- `SKILL.md`: the condensed brand rules the agent loads automatically
- `AZMX-Figma-SKILL.md`: Figma-specific edition with embedded advanced design and presentation guides for Figma Design and Figma Slides work
- `references/design-system.md`: the full AZMX Design System handbook (v1.1: chevrons banned as backgrounds)
- `references/colors.md`: every color tone — the blue ramp 50 to 1000, the five secondary palettes, neutrals, RAG dots, surfaces, text-by-surface
- `references/design-tokens-usage.md`: **read this before touching a Figma file.** The seven-step guide — which tier to bind to, choosing colour by job, type, spacing, and how to add a token
- `references/figma-tokens.md`: the complete live Figma variable export, 550 tokens across five collections — Primitives, Palette (six modes), Semantic (Light/Dark), Component, Canvas
- `tokens.html`: interactive design token explorer — search, filter, and browse all 550 tokens with live previews and one-click copying
- `references/email-design-system.md`: the AZMX Email Design System v1 (RTL rules, 3-layer fonts, themes, components)
- `references/voice-and-tone.md`: how AZMX sounds, EN and AR — the Four Dimensions, universal writing principles, the 6-point pre-publish checklist, and the no-AI-tells writing mechanics
- `references/communication-strategy.md`: the strategy spine — guiding principles, POEM, all seven channels, the RACI matrix, workflows, the three operating rituals, the creative effectiveness scale, and the briefing checklist
- `references/audiences-and-messaging.md`: three internal segments, three external motions, eight personas, each with its approved verbatim core message
- `references/sub-brand-voices.md`: voice profiles for Colab, Majarah, Clix, and Anatomi (voice only — the visual system in this skill is AZM X's alone)
- `references/editorial-calendar.md`: weekly themes, per-brand cadence, optimal posting times, the monthly SEO and PPC initiatives, and the 19 Arabic internal initiatives
- `references/content-prompts.md`: five tested prompts — long-form article, LinkedIn, Instagram, Twitter/X, and English-to-Arabic localisation
- `references/image-library.md`: catalogue, selection rules, and measured colour pairings for the image library
- `references/image-index.md`: every image with its three concept tags, dominant colour, safe text colour, and a direct download link
- `references/recolor-prompts.md`: tested prompts for converting an image to another colour theme, copyable from the gallery
- `references/icons.md`: the Phosphor icon system, the ask-before-you-use-icons rule, locked weights, sizes, and colours by surface
- `references/pdf-forms.md`: the validated Figma → export → pdf-lib pipeline for printed A4 documents and fillable PDF forms
- `references/troubleshooting.md`: common errors and validated fixes across the skill — PDF forms, tokens, images, and scripts
- `scripts/brand-check.py`: an automated brand QA linter. It parses the legal palette out of `references/colors.md` at runtime, then checks deliverables for off-palette colours, non-brand fonts, and off-scale spacing
- `scripts/sync-references.py`: keeps JSON reference files synchronized with their markdown counterparts. Detects drift between image-tags.json ↔ image-index.md and recolor-prompts.json ↔ recolor-prompts.md, with --check mode for CI/CD integration
- `scripts/build-pdf-form.mjs`: stamps AcroForm fields onto a designed PDF at exact coordinates, with the brand font embedded
- `scripts/extract-figma-fields.js`: reads the field rectangles out of a Figma design and emits the JSON spec
- `scripts/tokens-to-css.mjs`: turns the tokens into CSS custom properties. All twelve palette-theme combinations by default, or one flattened combination, or JSON. No dependencies
- `scripts/export-figma-tokens.js`: regenerates the token export from Figma, in raw and W3C DTCG form
- `assets/tokens/azmx-tokens.json`: all 550 tokens as data, aliases preserved so the palette and theme structure survives
- `assets/images/`: 240 AZMX-generated brand images in 8 sections (gradients, abstract blue, and recolored variants)
- `assets/templates/`: ready-to-fill email skeleton and the full email component showcase
- `assets/logo/`: the AZMX logo in Colored, Navy Dark, and White SVG variants, plus the chevron favicon
- `assets/fonts/`: Azm X (TTF, English and Arabic) and thmanyah serif display (woff2 for web, OTF for desktop)
- `assets/fonts.css`: ready-made @font-face rules plus CSS variables for the palette

## Install

One command. It needs [Node.js](https://nodejs.org) and [Claude Code](https://claude.com/claude-code).

```bash
npx skills@latest add Gamaleldientarek/azmx-brand -g -a claude-code -y
```


Restart Claude Code. Next time you ask for anything AZMX-branded the skill loads on its own, or call it directly with `/azmx-brand`.

To update later:

```bash
npx skills@latest update -g
```

Cursor, Codex or Copilot: same command with `-a cursor`, `-a codex` or `-a github-copilot`. Every tool on the machine at once: `-a '*'`. Prefer a plugin that updates itself: see the [hub README](https://github.com/Gamaleldientarek/azmx#install). Not comfortable in a terminal: [INSTALL.md](https://github.com/Gamaleldientarek/azmx/blob/main/INSTALL.md) walks through it step by step.

## Python dependencies

The skill includes Python scripts for brand checking, drift detection, and image library management. Install dependencies:

```bash
pip3 install -r requirements.txt
```

**Required:**
- **Pillow** — image processing for the image library (`scripts/add-images.py`, `scripts/rebuild-index.py`)

**Optional but recommended:**
- **matplotlib** — chart generation for drift reports (`scripts/drift-report.py`)
- **PyYAML** — configuration file parsing (has built-in fallback if not installed)

Without matplotlib, drift reports will generate but won't include trend visualizations. Without PyYAML, configuration files will use a simple built-in parser.

## Quick palette reference

**Blue is the house default.** Five secondary palettes can each carry a whole deliverable — the Hospitals Report runs entirely in orange. A deck picks one palette and its accent, dark ground and gradient all follow.

| Palette | Signature | Deep | Text-safe on white |
|---|---|---|---|
| **Blue** | Electric `#001AFF` | Dark Navy `#040038` | `#001AFF` |
| **Orange** | `#F47A48` | `#842C09` | `#A1502F` |
| **Green** | `#22C36F` | `#012F02` | `#168049` |
| **Yellow** | `#FED340` | `#693F02` | `#895F0F` |
| **Purple** | `#C68FFF` | `#2E0068` | `#7341AD` |
| **Red** | `#FF2B3C` | `#640000` | `#A81C27` |

Each runs a full twelve-step ramp, 50 to 1000. Never mix two palettes on one surface.

**The signature is a fill colour, not a text colour.** Blue is the exception because Electric is dark. Every secondary signature is a vivid light tone — white on yellow `#FED340` measures 1.44:1 — so text drops to the safe step in the last column. In Figma the tokens handle it: `surface/accent` for a fill, `text/accent` when it must be read.

Supporting tones:

| Token | Hex | Role |
|---|---|---|
| Light Blue | `#5D8FFF` | The accent on navy, where Electric fails contrast |
| Blue 50 | `#F0F5FF` | Quiet light surface, table zebra, panels |
| Neutral 900 | `#111927` | Body text on light |
| RAG dots | `#FF2B3C` `#FED340` `#22C36F` | Data only, separate from the palettes |

Full ramps and usage rules live in `references/colors.md`. How to apply them is in `references/design-tokens-usage.md`.

## Brand API

The brand rules are also published as a versioned, read-only JSON API — design tokens, palettes, typography, voice and tone, personas, content prompts, and the image catalogue — at `https://gamaleldientarek.github.io/azmx-brand/api/v1/` (start with `index.json`). Interactive Redoc docs and worked examples live at **[gamaleldientarek.github.io/azmx-brand/api-docs/](https://gamaleldientarek.github.io/azmx-brand/api-docs/)**; the full endpoint reference is in [`api/v1/README.md`](api/v1/README.md).

Everything under `api/v1/` is generated from the reference documents — run `bash scripts/build-api.sh` after editing them, and `python -m pytest tests/test_brand_api.py` fails if the committed JSON is stale.

## Adding images to the library

Ask Claude ("add these to the AZMX image library"), or do it yourself from this folder:

```bash
python3 scripts/add-images.py blue ~/Desktop/new-renders/
git add -A && git commit -m "Add images to blue" && git push
```

Sections: `gradient`, `blue`, `white`, `orange`, `purple`, `red`, `green`, `yellow`. The script resizes to 1600px, compresses to match the set, numbers the files, and rebuilds both the index and the live gallery. Install the pinned Python dependencies first: `pip3 install -r requirements.txt`.

## Keeping reference files in sync

The skill maintains reference data in two formats: structured JSON files (for programmatic use) and human-readable markdown (for agent context). The sync script keeps them consistent.

Two file pairs are synchronized:

- `scripts/image-tags.json` ↔ `references/image-index.md` (concept tags for the 240 images)
- `scripts/recolor-prompts.json` ↔ `references/recolor-prompts.md` (the 7 color recolor prompts)

**Check for drift** (exits non-zero if files are out of sync — use this in CI):

```bash
python3 scripts/sync-references.py --check
```

**Sync markdown from JSON** (the default direction, preserves metadata like dominant colors and download links):

```bash
python3 scripts/sync-references.py --sync
```

**Sync JSON from markdown** (if you've edited the markdown and want to update the JSON):

```bash
python3 scripts/sync-references.py --sync --from-markdown
```

When you update image tags or recolor prompts in either format, run the sync script to keep both files consistent. The --check mode is integrated into the GitHub Actions workflow at `.github/workflows/validate-references.yml` and runs automatically on PRs.

## Building a fillable PDF form

Design the form in Figma on A4 frames (595 × 842), name every input rectangle `FIELD · snake_case_id`, then:

```bash
cd ~/.claude/skills/azmx-brand/scripts && npm install   # once
node ~/.claude/skills/azmx-brand/scripts/build-pdf-form.mjs \
  --src merged.pdf --fields fields.json --out fillable.pdf --expect 99
```

Fields land at exact coordinates with readable names, so Acrobat's "Prepare Form" auto-detect is never needed. Full pipeline in `references/pdf-forms.md`.

## Troubleshooting

Hit an error? The **[Troubleshooting Guide](references/troubleshooting.md)** lists common mistakes and validated fixes — pdf-lib form field errors, coordinate mismatches, token import issues, and script failures. Organized by symptom so you can search by the exact error message. Every entry represents a real mistake someone made, so if you're blocked, start there.

## Contributing

Want to add features, fix bugs, or improve the documentation? See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full developer setup and contribution workflow.

Covers:

- **Prerequisites**: Node.js, Python, and Pillow installation
- **Development setup**: cloning, installing dependencies (critical: `npm install` runs in `scripts/` not the root)
- **Script execution**: which scripts run in Node.js vs Python vs Figma Console
- **Contribution workflow**: branching, committing, pull requests
- **Troubleshooting**: solutions to common setup issues

The guide is written for designers, marketers, and content strategists using AI agents — not just traditional developers. If something is unclear, that's a bug worth reporting.

## Converting tokens to CSS

`tokens-to-css.mjs` reads `assets/tokens/azmx-tokens.json` and outputs CSS custom properties. By default it emits all twelve palette-theme combinations, driven by `data-palette` and `data-theme` attributes on `<body>`. No dependencies.

**Generate all combinations** (default):

```bash
node scripts/tokens-to-css.mjs > azmx-tokens.css
```

The output includes CSS variables like `--azmx-text-primary`, `--azmx-surface-page`, `--azmx-gradient`. Blue/light is the base; other combinations override only what differs. Use in HTML:

```html
<body data-palette="orange" data-theme="dark">
  <div style="color: var(--azmx-text-primary); background: var(--azmx-surface-page);">Content</div>
</body>
```

**Flatten to a single combination:**

```bash
node scripts/tokens-to-css.mjs --palette orange --theme dark > orange-dark.css
```

Palettes: `blue` (default), `orange`, `green`, `yellow`, `purple`, `red`  
Themes: `light` (default), `dark`

**Export as JSON:**

```bash
node scripts/tokens-to-css.mjs --json > tokens.json
node scripts/tokens-to-css.mjs --palette orange --theme dark --json > orange-dark.json
```

Without `--palette`/`--theme`, JSON exports all twelve combinations keyed by `"palette/theme"`. With the flags it exports one flat object of resolved token values.

## License note

The AZMX logo, brand assets, and the thmanyah serif display and Azm X font files are the property of AZMX and its licensors, and are licensed for AZMX work only. Viewing this repo does not grant any right to use them in non-AZMX projects or to redistribute the fonts.

Built by [gamaleldien.com](https://gamaleldien.com). Skill v2.2.0, design system v1.1, encoded from the New Direction Library Figma file and the AZM X Unified Communication Strategy. Release notes in [CHANGELOG.md](CHANGELOG.md).
