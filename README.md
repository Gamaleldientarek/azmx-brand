![AZMX Brand Skill](assets/cover.jpg)

# AZMX Brand Skill

[![Brand Skill Validation](https://github.com/Gamaleldientarek/azmx-brand/actions/workflows/validate.yml/badge.svg)](https://github.com/Gamaleldientarek/azmx-brand/actions) [![Release](https://img.shields.io/github/v/release/Gamaleldientarek/azmx-brand)](https://github.com/Gamaleldientarek/azmx-brand/releases)

The AZMX brand and communication system as an Agent Skill. Install it once and every deliverable — decks, emails, reports, web pages, social posts, documents — comes out in the AZMX identity without re-briefing the agent: black grounds, electric blue, generous white space, serif personality, the chevron as the only graphic device. Since v3 it takes its components, blocks and tokens from the private **AZM X Design System** (installer: `npx @azmxsa/cli`); see [references/design-system-link.md](references/design-system-link.md). It also carries the Unified Communication Strategy: five brand voices, eight personas with approved messages, seven channels, the editorial cadence and ready-to-run content prompts.

## Install

Needs [Node.js](https://nodejs.org) and [Claude Code](https://claude.com/claude-code).

```bash
npx skills@latest add Gamaleldientarek/azmx-brand -g -a claude-code -y   # install
npx skills@latest update -g                                              # update later
```

Restart Claude Code; the skill loads on its own for anything AZMX-branded, or call it with `/azmx-brand`. For Cursor, Codex or Copilot use `-a cursor`, `-a codex` or `-a github-copilot` (`-a '*'` for every tool). Step-by-step without a terminal: [INSTALL.md](https://github.com/Gamaleldientarek/azmx/blob/main/INSTALL.md).

The skill doesn't update itself: run the update command when a release is out (the skill tells you at the start of AZM X work), then restart Claude Code. The AZM X Design System's components, blocks and tokens install with no sign-in, from its public npm package (`npx @azmxsa/cli init`). Only the licensed font files and the drift check read its private repository, with your own GitHub sign-in (ask the owner for access, then run `gh auth login` once). Anyone with an AZM X account can download the licensed fonts from the [AZM X fonts folder](https://drive.google.com/drive/folders/1lh63aC23umhBqmuHIj4aJ40sMf0ADsrG) on the company Google Drive.

## Explore

| | |
|---|---|
| 🖼 **[Image library](https://gamaleldientarek.github.io/azmx-brand/)** | all 240 brand images, tagged and downloadable |
| 🎛 **[Token explorer](https://gamaleldientarek.github.io/azmx-brand/tokens.html)** | 601 design tokens with live previews and copy-to-clipboard |
| 🔌 **[Brand API](https://gamaleldientarek.github.io/azmx-brand/api-docs/)** | read-only JSON: tokens, palettes, typography, voice, personas, prompts, images — [reference](api/v1/README.md) |

## What's inside

**Brand rules (what the agent reads)**

| File | Covers |
|---|---|
| `SKILL.md` | The condensed rules, loaded automatically |
| `references/design-system-link.md` | How the skill uses the AZM X Design System: access, the installer, what to take for each deliverable, and each skill concept's design-system part |
| `AZMX-Figma-SKILL.md` | Figma Design / Slides edition with the advanced design guides |
| `references/design-system.md` | The full brand handbook (v1.1, with the v3.0.0 amendments) |
| `references/colors.md` · `design-tokens-usage.md` · `figma-tokens.md` | Every tone and ramp; which token tier to bind to and why; the live Figma variable export |
| `references/voice-and-tone.md` · `sub-brand-voices.md` | How AZMX sounds in EN and AR; Colab, Majarah, Clix and Anatomi voices |
| `references/communication-strategy.md` · `audiences-and-messaging.md` · `editorial-calendar.md` · `content-prompts.md` | Channels, RACI, rituals; eight personas with verbatim core messages; cadence; fifteen tested prompts |
| `references/email-design-system.md` · `rtl-layout-guide.md` · `icons.md` · `pdf-forms.md` | Email system, RTL rules, the Phosphor icon system, the Figma → fillable-PDF pipeline |
| `references/image-library.md` · `image-index.md` · `recolor-prompts.md` | Image selection rules, the full tagged index with direct links, recolour prompts |
| `references/troubleshooting.md` | Real mistakes and their validated fixes, organised by symptom |

**Assets**

| Path | Covers |
|---|---|
| `assets/tokens/azmx-tokens.json` · `azmx-tokens.css` | 601 tokens as data (aliases preserved) and as CSS custom properties with units |
| `assets/fonts/` · `assets/fonts.css` | Azm X (EN/AR) and thmanyah serif display, with ready `@font-face` rules |
| `assets/logo/` · `assets/templates/` | Logo variants and favicon; email skeleton and component showcase |
| Image library | Served from `cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>.jpg`; `scripts/image-meta.json` is the catalogue |

**Tools** — `scripts/design-system.mjs` (design-system access, its tokens and fonts, and the drift check), `scripts/check-update.mjs` (tells people when a newer release is out), `scripts/icons.mjs` (finds any Phosphor icon by name or keyword and fetches only its SVG), `scripts/brand-check.py` (brand linter: palette, fonts, spacing, RTL, copy tone), `tokens-to-css.mjs`, `build-token-explorer.mjs`, `build-pdf-form.mjs`, `export-figma-tokens.js`, `sync-references.py`, `add-images.py`, the drift monitor (`brand-monitor.py` and friends) and the Brand API build (`build-api.sh`). Usage in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Palette at a glance

Blue is the house default; each secondary palette can carry a whole deliverable, never two on one surface. The signature is a fill colour — text drops to the safe step.

| Palette | Signature | Deep | Text-safe on white |
|---|---|---|---|
| **Blue** | Electric `#001AFF` | `#01006E` | `#001AFF` |
| **Orange** | `#F47A48` | `#842C09` | `#A1502F` |
| **Green** | `#22C36F` | `#012F02` | `#168049` |
| **Yellow** | `#FED340` | `#693F02` | `#895F0F` |
| **Purple** | `#C68FFF` | `#2E0068` | `#7341AD` |
| **Red** | `#FF2B3C` | `#640000` | `#A81C27` |

Dark grounds are black `#000000` in every palette. Supporting tones: Light Blue `#5D8FFF` (accent on black), Blue 50 `#F0F5FF` (quiet surfaces), Neutral 900 `#111927` (body text and headings). Full ramps and rules in `references/colors.md`; how to apply them in `references/design-tokens-usage.md`.

## Contributing and support

- Something broke? Start with the [Troubleshooting Guide](references/troubleshooting.md).
- Changing the tooling? [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) has the regeneration commands CI checks; [CONTRIBUTING.md](CONTRIBUTING.md) the workflow, pre-commit hook and tests.
- Security reports: see [SECURITY.md](SECURITY.md).

## License

The AZMX logo, brand assets and the thmanyah serif display and Azm X fonts belong to AZMX and its licensors and are licensed for AZMX work only. Viewing this repository grants no right to use them elsewhere or to redistribute the fonts.

Built by [gamaleldien.com](https://gamaleldien.com). Skill v3.2.0 · built on the AZM X Design System v1.3.0 · release notes in [CHANGELOG.md](CHANGELOG.md).
