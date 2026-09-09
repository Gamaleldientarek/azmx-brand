# Contributing to AZMX Brand Skill

Developer setup and contribution workflow for the AZMX brand skill. This guide covers prerequisites, environment setup, script usage, testing, and how to submit changes.

The skill targets designers, marketers, and content strategists using AI coding agents — many are not traditional developers. If something in this guide is unclear, that is a bug worth fixing.

---

## Prerequisites

Three environments. Install them once, forget about them until they break.

| Tool | Minimum | Where | Why |
|---|---|---|---|
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org) | Runs the build scripts, token export, CSS generation |
| **Python** | 3.11+ | Install separately if unavailable; [python.org](https://python.org) for Windows | Runs the brand checker, image tooling, index rebuild |
| **Pillow** | Latest | `python -m pip install Pillow` | Image processing (dominant color, resize, compress) |

**Check what you have:**

```bash
node --version   # Should show v18.0.0 or higher
python3 --version   # Should show 3.11 or higher
python3 -c "import PIL; print(PIL.__version__)"   # Should print a version, not an error
```

Create and activate the virtual environment below before installing Python packages. If Python reports `ModuleNotFoundError: No module named 'PIL'`, install Pillow:

```bash
python -m pip install Pillow
```

---

## Development setup

### 1. Clone the repository

```bash
git clone https://github.com/Gamaleldientarek/azmx-brand.git
cd azmx-brand
```

### 2. Create a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-test.txt
```

On Windows, activate with `.venv\Scripts\activate`. Image ingestion uses macOS `sips`; the existing add-images command does not run unchanged on Windows or Linux.

### 3. Install Node dependencies

**Critical: this MUST happen inside `scripts/`, not the project root.**

```bash
cd scripts
npm ci
cd ..
```

The root package.json provides test commands. Runtime dependencies for the PDF tool and Vitest are declared in scripts/package.json; install them there using its committed lockfile.

This is the dependency confusion issue that caused real problems in the past:

- **v2.0.1** (2026-08-08): Fixed a gitignored lockfile causing version drift. `scripts/package-lock.json` is now committed.
- **v1.2.0** (2026-07-18): Documented that `npm ci` must happen in `scripts/` not the root.

**What gets installed:**

```json
{
  "dependencies": {
    "@pdf-lib/fontkit": "^1.1.1",
    "pdf-lib": "^1.17.1"
  }
}
```

These power `build-pdf-form.mjs`. Development dependencies include Vitest. The token-to-CSS script uses Node built-ins only.

---

## Script execution environments

**Not all scripts run in Node.js.** This is the most important thing to know.

| Script | Runs where | How to execute |
|---|---|---|
| `build-pdf-form.mjs` | **Node.js**, locally | `node scripts/build-pdf-form.mjs --src ... --fields ... --out ...` |
| `tokens-to-css.mjs` | **Node.js**, locally | `node scripts/tokens-to-css.mjs` |
| `brand-check.py` | **Python**, locally | `python3 scripts/brand-check.py deliverable.html` |
| `rebuild-index.py` | **Python**, locally | `python3 scripts/rebuild-index.py` |
| `add-images.py` | **Python**, locally | `python3 scripts/add-images.py blue ~/Desktop/new-renders/` |
| `export-figma-tokens.js` | **Figma Console** | Paste into Claude Code with Figma MCP active |
| `extract-figma-fields.js` | **Figma Console** | Paste into Claude Code with Figma MCP active |
| `figma-slide-transitions.js` | **Figma Console** | Paste into Claude Code with Figma MCP active |

**The three Figma Console scripts cannot run in Node.js.** They call Figma plugin APIs (`figma.root`, `figma.currentPage`, `figma.variables`) which only exist inside the Figma Desktop Bridge sandbox. Running them in Node fails with `ReferenceError: figma is not defined`.

Figma Console scripts are invoked through Claude Code's Figma MCP server. You paste them into a conversation, the agent executes them through `figma_execute`, and the result comes back as JSON.

---

## Running the scripts

### Build a fillable PDF form

Design the form in Figma on A4 frames (595 × 842 px), name every input rectangle `FIELD · snake_case_id`, export to PDF, merge the pages, then:

```bash
node scripts/build-pdf-form.mjs \
  --src merged.pdf \
  --fields fields.json \
  --out fillable.pdf \
  --expect 99
```

| Flag | Meaning |
|---|---|
| `--src` | Source PDF, the merged designed document (required) |
| `--fields` | JSON field spec from `extract-figma-fields.js` (required) |
| `--out` | Output path (required) |
| `--font` | TTF to embed. Defaults to `assets/fonts/azmx/AzmX-Regular.ttf` |
| `--size` | Field font size in pt. Default 9 |
| `--expect` | Hard-fail unless exactly this many fields are written |
| `--flatten` | Write a read-only flattened copy instead of live fields |

Always pass `--expect` with the total the extractor reported. It turns a silently dropped section into a build failure.

Full pipeline documented in `references/pdf-forms.md`.

### Generate CSS custom properties from tokens

```bash
node scripts/tokens-to-css.mjs
```

Reads `assets/tokens/azmx-tokens.json` and emits CSS custom properties. Supports:

- All twelve palette-theme combinations (default)
- One flattened combination
- JSON output

Zero dependencies. Aliases resolve to literal values; palette and theme selectors retain the switching behavior.

### Check a deliverable for brand compliance

```bash
python3 scripts/brand-check.py deliverable.html
```

Parses the legal palette out of `references/colors.md` at runtime, then checks the deliverable for:

- Off-palette colors
- Non-brand fonts
- Off-scale spacing

### Rebuild the image index

```bash
python3 scripts/rebuild-index.py
```

Regenerates `references/image-index.md` and `index.html` from whatever is in `assets/images/`. Measures each image's dominant color and luminance. Run this after adding, removing, or replacing images.

### Add images to the library

```bash
python3 scripts/add-images.py blue ~/Desktop/new-renders/
```

Sections: `gradient`, `blue`, `white`, `orange`, `purple`, `red`, `green`, `yellow`. Resizes to 1600px, compresses to match the set, numbers the files, and rebuilds the index and gallery.

---

## Testing

Automated tests exist under `tests/`: pytest for Python and Vitest for JavaScript.

```bash
python -m pytest tests/
npm --prefix scripts test
node scripts/tokens-to-css.mjs --validate
python scripts/sync-references.py --check
```

Run the relevant subset while editing, then the broader suite before proposing a merge. A nonzero exit is a failure to investigate, not a result to suppress. Image-integrity checks may reveal damaged source assets; retrieve their originals rather than weakening assertions. See tests/README.md for scope and coverage limitations.

Manual verification complements automated checks:

| Change type | Verification |
|---|---|
| Brand rules | Run `brand-check.py` on a known-good deliverable, expect no violations |
| PDF form | Build a test form, open in Acrobat, fill every field, check field names in exported data |
| Token export | Diff the JSON, verify schema matches W3C DTCG format |
| CSS generation | Load in a browser, check computed values match token definitions |
| Image index | Open `index.html` locally, verify images load and metadata is correct |

---

## Contribution workflow

### 1. Branch from main

```bash
git checkout main
git pull
git checkout -b fix/your-descriptive-name
```

### 2. Make your changes

Follow existing patterns. If modifying:

- **Brand rules**: update `SKILL.md` and the relevant `references/*.md` file
- **Scripts**: match the style in the existing scripts, add usage documentation
- **Assets**: follow naming conventions (`gradient-01.jpg`, not `new_image_1.jpg`)
- **Tokens**: regenerate the CSS and update `references/figma-tokens.md`

### 3. Verify your changes

Run the relevant verification from the table above. If you modified a script, test it end-to-end with real inputs.

### 4. Commit

Write a clear commit message. No emoji, no "fix stuff", no AI tells ("I've updated..."). State what changed and why.

Good:

```
Add Orange palette support to brand-check.py

The checker only recognized Blue palette values. It now parses all six
palettes from colors.md and validates against whichever one is in use.
```

Bad:

```
update brand-check 🎨
```

### 5. Push and open a pull request

```bash
git push -u origin fix/your-descriptive-name
```

Open a pull request on GitHub. Describe:

- What you changed
- Why you changed it
- How to verify it works

If the change fixes a bug that was reported, link the issue.

---

## Common issues

### `ERR_MODULE_NOT_FOUND: Cannot find package 'pdf-lib'`

You ran `npm ci` in the project root instead of `scripts/`. Fix:

```bash
cd scripts
npm ci
cd ..
```

Then retry the command.

### `ModuleNotFoundError: No module named 'PIL'`

Pillow is not installed. Fix:

```bash
python -m pip install Pillow
```

### `ReferenceError: figma is not defined`

You tried to run a Figma Console script in Node.js. Those three scripts (`export-figma-tokens.js`, `extract-figma-fields.js`, `figma-slide-transitions.js`) only work inside the Figma Desktop Bridge sandbox, accessed through Claude Code's Figma MCP server.

To run them, paste the script into a Claude Code conversation with Figma MCP active. The agent will execute it through `figma_execute`.

### Script runs but produces wrong output

Check that you are using the correct inputs:

- `build-pdf-form.mjs`: Source PDF must be A4 (595 × 842 pt), fields JSON must match the design
- `tokens-to-css.mjs`: Reads from `assets/tokens/azmx-tokens.json`, not a custom path
- `brand-check.py`: Parses palette from `references/colors.md` — if you edited colors, verify the format matches

### YAML quoting bug (v2.1.1)

If adding YAML frontmatter anywhere, **quote values containing colons**:

```yaml
# ❌ Wrong — parser sees two keys
description: communication strategy: planning

# ✅ Correct
description: "communication strategy: planning"
```

This made the skill invisible to the CLI in v2.1.1.

---

## Project structure

```
azmx-brand/
├── SKILL.md                    # The condensed rules agents load automatically
├── README.md                   # End-user installation and quick reference
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # This file
├── references/                 # Full documentation
│   ├── design-system.md
│   ├── colors.md
│   ├── design-tokens-usage.md
│   ├── figma-tokens.md
│   ├── email-design-system.md
│   ├── voice-and-tone.md
│   ├── communication-strategy.md
│   ├── audiences-and-messaging.md
│   ├── sub-brand-voices.md
│   ├── editorial-calendar.md
│   ├── content-prompts.md
│   ├── image-library.md
│   ├── image-index.md
│   ├── recolor-prompts.md
│   ├── icons.md
│   ├── pdf-forms.md
│   └── presentation-transitions.md
├── scripts/                    # Build and validation tooling
│   ├── package.json            # Node runtime and test dependencies
│   ├── package-lock.json       # Committed as of v2.0.1
│   ├── build-pdf-form.mjs      # Node: stamps AcroForm fields
│   ├── tokens-to-css.mjs       # Node: generates CSS custom properties
│   ├── brand-check.py          # Python: brand compliance linter
│   ├── rebuild-index.py        # Python: regenerates image index
│   ├── add-images.py           # Python: adds images to library
│   ├── export-figma-tokens.js  # Figma Console: token export
│   ├── extract-figma-fields.js # Figma Console: field extraction
│   └── figma-slide-transitions.js # Figma Console: deck transitions
├── assets/
│   ├── tokens/                 # Design tokens as JSON
│   ├── images/                 # 242 brand images, 8 sections
│   ├── templates/              # Email skeleton and showcase
│   ├── logo/                   # Logo variants and favicon
│   ├── fonts/                  # Azm X and thmanyah serif
│   └── fonts.css               # @font-face rules
└── index.html                  # Public image gallery
```

---

## Questions

If this guide is unclear, incomplete, or wrong, open an issue or submit a pull request. The target audience includes non-developers using AI agents — if you had to ask, someone else will too.

Built by [gamaleldien.com](https://gamaleldien.com). Skill v2.1.2, design system v1.1.
