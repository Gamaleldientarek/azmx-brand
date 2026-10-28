# The skill and the AZM X Design System

Since azmx-brand v3.0.0 (27 October 2026), the AZM X Design System is the source for every AZM X design: code, Figma, documents, decks, emails, any UI and any screen. This page says how the skill reaches it, what to take from it for each kind of deliverable, and which part of the system matches each concept in this skill.

## What the design system is

- **The repository:** `Gamaleldientarek/azmx-design-system`. It's private, because the fonts are licensed for AZM X work only.
- **What's in it:** React, Tailwind CSS v4 and Radix components, page blocks and tokens, with every part working in Arabic (right to left) and English.
- **The dashboard:** https://azmx-design-system.vercel.app, behind a Vercel login. Each part has a page with a live preview, its code, its states, and its install command.
- **The installer:** `@azmxsa/cli` on npm. It's public, but it reads the private registry with the person's own GitHub sign-in, and it's pinned to its own release (`@azmxsa/cli` 1.2.3 installs `v1.2.3`).
- **The pinned release:** this skill is written against the release in `config/design-system.json` (`ref`). Newer releases add parts; `node scripts/design-system.mjs drift` says when one is out.

## Access

The skill is public, so it can't carry a key. Every read uses the person's own sign-in.

1. The owner adds the person's GitHub account to `azmx-design-system`.
2. The person runs `gh auth login` once on their computer, or sets `GITHUB_TOKEN` to a token that can read the repository.
3. `node scripts/design-system.mjs status` confirms access and shows the pinned and latest releases.

**Without access,** the skill still works: its own `azmx-tokens.css`, the Azm X 2.004 fonts in `assets/fonts/`, the official chevron in `assets/chevron/` and every rule in `SKILL.md` follow the same rulings. It can't install the system's parts, so say that once and carry on. For the licensed fonts, anyone with an AZM X account can download them from the **AZM X fonts folder** on the company Google Drive: https://drive.google.com/drive/folders/1lh63aC23umhBqmuHIj4aJ40sMf0ADsrG (also `fontsFolder` in `config/design-system.json`). Keep the files out of public repositories. Never ask anyone to paste a token into a chat.

## What to take, by deliverable

### React, Next.js and Tailwind

```bash
gh auth login                                   # once per computer
npx @azmxsa/cli init                            # adds the AZM X registry to components.json; a new project is set up on Radix
npx @azmxsa/cli add tokens                      # styles/tokens.css, theme.css and type.css
npx @azmxsa/cli list                            # every part and block the registry has
npx @azmxsa/cli add button page-header hero     # what the screen needs
node <skill>/scripts/design-system.mjs fetch-fonts src/fonts   # Azm X 3.007 and thmanyah, with index.ts for next/font
```

Without design-system access, put the files from the AZM X fonts folder in `src/fonts` and write `index.ts` as the design system's Install page shows.

- Import the three token files at the end of `globals.css`, after any `:root`, `.dark` and `@theme inline` blocks the project already has, so AZM X's values win. Replace the project's dark variant with `@custom-variant dark (&:where(.dark, .dark *));`.
- Load the fonts in the root layout: `import { azmx, thmanyah } from "@/fonts"` and put both `.variable` classes on `<html lang="ar" dir="rtl">`.
- In a project shadcn already set up, add `-o` so AZM X's `button.tsx` and `utils.ts` replace the stock ones.
- The installer stops on shadcn's Base UI styles (`base-nova` and the like), because shadcn would rewrite the Radix parts. Set `"style": "radix-nova"` in `components.json` and run it again.
- Pictures and logos aren't in the registry. Take them from the system's `public/brand`, `public/images`, `public/clients` and `public/logos`, or from the image library.
- Never hand-build a part the registry has. If a screen needs something the system doesn't have, build it from the system's tokens and parts in its look, and tell the person it's a candidate for the design system.

### Plain HTML: pages, one-page reports, emails, HTML-to-PDF

```bash
node <skill>/scripts/design-system.mjs fetch-tokens <folder>    # the system's azmx-tokens.css
```

- Link or inline that file and use its variables: `var(--surface-page)`, `var(--text-primary)`, `var(--text-heading)`, `var(--accent-base)`, `var(--border-subtle)`, `var(--radius)`.
- A section's palette is `data-palette="orange"` (blue is the default). A black section is `class="dark"`.
- **Without access,** link this skill's `azmx-tokens.css` instead. It has the same values under `--azmx-*` names (`var(--azmx-surface-page)`), with `data-palette` and `data-theme="dark"`.
- Fonts: the v3 files from `fetch-fonts`, or `assets/fonts.css` (2.004).

### Figma

- Bind to semantic tokens with the values in `SKILL.md` and `references/colors.md`. The design system names them the same way (`surface/page`, `text/heading`, `border/subtle`).
- The Figma library's variables still hold the values exported on 8 August 2026: navy grounds, navy headings, the old spacing names (`space/2xs`…) and the old radius names (`radius/sm` = 4). Until the library is updated, check each binding against the rulings and set the value by hand where they differ.
- Use the official chevron file from `assets/chevron/` as a mask. Never draw it.

### Decks, Word, PowerPoint and PDF documents

Apply the same tokens and rules by hand:
- black dark grounds and a gradient that starts at black;
- Neutral 900 headings;
- the site spacing scale and the radius names;
- `label-lg` eyebrows;
- the official chevron;
- no coloured lines;
- no shadows.

The 1920 × 1080 slide geometry in `references/design-system.md` still applies.

### Emails

One system, two designs.
- **Public emails** (website confirmations, welcome, thank-you, marketing) start from the design system's Emails section (dashboard: `/docs/emails`).
- **The internal newsletter** uses `references/email-design-system.md` and `assets/templates/`, with the v3 rulings applied.

## Concept to part

The dashboard page for a component is `/docs/components/<name>`, and for a block `/docs/blocks/<name>`. Install either with `npx @azmxsa/cli add <name>`.

| In this skill | In the design system | Notes |
|---|---|---|
| Eyebrow (A2) | text style `label-lg`; the `eyebrow` prop of `page-header` and the `split` block | 14 px Medium, accent colour, as written, no tracking |
| Content-Header (M1) | `page-header` | breadcrumb, eyebrow, title, lead, meta and actions |
| Chevron-Tick (A1), list bullet | `chevron` (library), `list` | the official mask; mirrors in Arabic |
| Stat-Figure (A6), Stat-Block (M4) | `stat` | serif figure, sans label |
| Brand-Numeral (A4), Numbered-Card (M5) | `numbered-card` | five tones that follow the palette |
| Hairline (A5) | `separator` | neutral only, `border/subtle` |
| Page-Number (A3) | `pagination` (the current page is a filled pill), `pager` | decks keep a numeral, never a line |
| Logo-Cell (A8), logo walls | `logo-wall` (block), `logo-carousel`, `logo-stack` | logos in one colour or as they are |
| Footer (M2) | `footer` (site), `app-footer` (products) | the animated footer gradient isn't in the system yet |
| Quote-Block (M8), testimonials | `quote-card`, `testimonials` (block) | no quote bar; a pull quote is a soft panel |
| Table-Row (M9) | `table`, `data-table` | zebra rows, neutral hairlines |
| Tag-Chip (M16) | `tag`, `badge` | grey pill |
| List (M13), List-Item (M13a) | `list` | bullet, number, check and icon |
| Org-Node (M15) | `org-chart` | the key person is a filled card, never a side rule |
| Process-Step (M11) | `steps`, `timeline` | |
| Method-Split (M14) | `split` (block) | text beside a clean picture |
| Case-Study (M12) | `showcase-card` | picture, label, title and a headline figure |
| Bio-Card (M6), Team-Tile (M7) | `avatar`, `info-card`, `panel` | build the bio layout from these |
| RAG-Dot (A7) | `badge` with a dot, or the `status/dot/*` tokens | data dots stay red, yellow and green |
| JD-Card (M10) | `panel` with `list` | |
| Image-Placeholder (M3) | `skeleton` while loading; the `chevron` mask over the real picture | |
| Divider, cover, closing (T1) | `hero`, `cta` (blocks) on a black or gradient section | the gradient starts at black |
| FAQ | `accordion`, `faq` (block) | |
| Contact | `contact-card`, `contact` (block) | |
| Navigation | `header`, `mobile-menu`, `language-switcher` | black glass on scroll |
| Selected tab, filter, view switch | `tabs`, `segmented-control` | filled pills, never an underline |
| Forms | `field`, `label`, `input`, `textarea`, `select`, `checkbox`, `radio-group`, `form-message` | 8 px radius, accent focus ring, errors stay visible |
| Callouts and notes | `callout` | no side bar |
| Scroll-in motion | `reveal`, `motion` (library) | plays once; respects reduced motion |

**Foundations** (dashboard `/docs/foundations/<page>`): colour, typography, radius, spacing, borders and shadows, motion, icons, imagery, breakpoints and charts. **Install** (`/docs/install`) has every setup step, and **Tokens** (`/docs/tokens`) lists every variable with its value.

## Keeping the two in step

- **Colours flow from this skill to the system.** The system's colour primitives come from this skill's `assets/tokens/azmx-tokens.json` (its `npm run sync-brand`), so a colour changes here first.
- **Everything else flows from the system to this skill:** the parts, the spacing and radius scales, the text styles, and the decisions.
- `node scripts/design-system.mjs drift` compares this skill's 88 shared colour tokens (all six palettes, light and dark), its spacing scale and its radius names with the system's pinned release.
  - It exits with 1 when something differs that nobody has ruled on.
  - Ruled exceptions go in `known` in `config/design-system.json`, each with its reason.
  - It also notes a newer system release, and a colour source in the system that's older than this skill's.
- `AZMX_DS_DIR=<a local clone>` makes the scripts read that clone with `git show <ref>:<path>` instead of GitHub, so a clone's unfinished work is never read.
- The drift check needs access, so it runs on a team member's machine, not in this public repository's CI.
