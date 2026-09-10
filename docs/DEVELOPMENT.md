# Developer guide

How to run and change the tooling in this repository. For what the skill *is* and how to install it, see the [README](../README.md); for the contribution workflow (branches, pre-commit hook, tests) see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Regenerating generated files

Five files are generated and committed; `.github/workflows/validate-generated.yml` fails if any of them is stale:

| File | Command |
|---|---|
| `azmx-tokens.css` | `node scripts/tokens-to-css.mjs > azmx-tokens.css` |
| `tokens.html` | `node scripts/build-token-explorer.mjs > tokens.html` |
| `index.html`, `references/image-index.md` | `python3 scripts/rebuild-index.py` (reads `scripts/image-meta.json`; no image files needed) |
| `references/recolor-prompts.md` | `python3 scripts/sync-references.py --sync` |
| `api/v1/*`, `api-docs/` | `bash scripts/build-api.sh` |

## Python dependencies

The skill includes Python scripts for brand checking, drift detection, and image library management. Install dependencies:

```bash
pip3 install -r requirements.txt
```

**Required:**
- **Pillow** — image processing for the image library (`scripts/add-images.py`; `scripts/rebuild-index.py` only needs it when a local `assets/images/` copy is re-measured)

**Optional but recommended:**
- **matplotlib** — chart generation for drift reports (`scripts/drift-report.py`)
- **PyYAML** — configuration file parsing (has built-in fallback if not installed)

Without matplotlib, drift reports will generate but won't include trend visualizations. Without PyYAML, configuration files will use a simple built-in parser.

## Adding images to the library

Ask Claude ("add these to the AZMX image library"), or do it yourself from this folder:

```bash
git clone https://github.com/Gamaleldientarek/azmx-brand-cdn.git ../azmx-brand-cdn   # once: the CDN checkout, next to this repo
python3 scripts/add-images.py blue ~/Desktop/new-renders/                            # or --cdn-dir /path/to/azmx-brand-cdn
git add -A && git commit -m "Add images to blue" && git push
(cd ../azmx-brand-cdn && git add -A && git commit -m "Add images to blue" && git push)
```

Sections: `gradient`, `blue`, `white`, `orange`, `purple`, `red`, `green`, `yellow`. The image files are not stored in this repository: they live in `azmx-brand-cdn` and are served from jsDelivr at `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>.jpg` (the base URL is `$meta.cdn` in `scripts/image-meta.json`). The script resizes to 1600px, compresses to match the set, numbers the files after the highest entry in `scripts/image-meta.json`, writes the JPEGs into `<cdn-dir>/images/<section>/`, appends each image's analysis (dominant colour, nearest token, luminance) to `scripts/image-meta.json`, and rebuilds both the index and the live gallery. jsDelivr picks up `main` within about 12 hours; to force it, purge the path via `https://purge.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>`. Install the pinned Python dependencies first: `pip3 install -r requirements.txt`.

Old links of the form `https://gamaleldientarek.github.io/azmx-brand/assets/images/<section>/<file>.jpg` are forwarded to the CDN by the root `404.html`.

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

## Converting tokens to CSS

`tokens-to-css.mjs` reads `assets/tokens/azmx-tokens.json` and outputs CSS custom properties. By default it emits all twelve palette-theme combinations, driven by `data-palette` and `data-theme` attributes on `<body>`. No dependencies.

**Generate all combinations** (default):

```bash
node scripts/tokens-to-css.mjs > azmx-tokens.css
```

The output includes CSS variables like `--azmx-text-primary`, `--azmx-surface-page`, `--azmx-gradient`. Blue/light is the base; other combinations override only what differs. Lengths carry `px` (`--azmx-space-md: 64px`), font weights are numeric (`--azmx-weight-bold: 700`), and the RTL collection is emitted under `:root, [dir="ltr"]` / `[dir="rtl"]`; the token file is validated before anything is generated. See [references/token-pipeline.md](../references/token-pipeline.md#units) for the unit and weight conventions. Use in HTML:

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

