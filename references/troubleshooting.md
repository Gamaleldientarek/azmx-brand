# Troubleshooting Guide

Common errors, non-obvious API behaviors, and validated fixes. Every entry here represents a real mistake someone made. Organized by symptom so you can search by the error message you're seeing, not by when it was discovered.

---

## PDF Forms & pdf-lib

### Error: "No /DA (default appearance) entry found"

**Area:** pdf-lib  
**Symptom:** Throws when stamping form fields with `setFontSize()`  
**Problem:** `setFontSize()` called before `addToPage()` on a text field  
**Solution:** Always call `addToPage()` first, then set font properties:

```js
const tf = form.createTextField(f.id);
tf.addToPage(page, { x, y, width, height });  // ← First
tf.setFontSize(size);                          // ← Second
```

This is the most likely error in the PDF form pipeline.

**Version:** v1.2.0

---

### Form coordinates don't match Figma design

**Area:** PDF forms  
**Symptom:** Fields appear shifted or scaled wrong in the output PDF  
**Problem:** A4 frame designed at wrong pixel dimensions (e.g., 1240 × 1754 or 2480 × 3508)  
**Solution:** Design A4 frames at exactly **595 × 842 px**. This maps 1:1 onto A4 in PDF points (595.28 × 841.89 pt), so Figma coordinates become PDF coordinates with no scale factor. Any other size forces a scale factor into every coordinate calculation.

**Version:** v1.2.0

---

### A4 form content overflows the page

**Area:** PDF forms  
**Symptom:** Dense form layout runs past the bottom margin, forcing multi-column grids  
**Problem:** 32 px row height feels safer for Acrobat but actually wastes vertical space  
**Solution:** Use **24 px rows** for all form inputs. 24 px ≈ 8.5 mm, a standard PDF form-field height. On the AZMX employee form, 32 px rows overflowed all three pages (−254 / −166 / −90 px), while 24 px rows fit with 18 / 54 / 55 px clearance. Row height is a cheaper lever than layout compression — reach for it first.

**Version:** v1.2.0

---

### pdf-lib import fails: "Cannot find module '@cantoo/pdf-lib'"

**Area:** Node.js  
**Symptom:** Script in `scripts/` directory fails with module-not-found error despite installing pdf-lib in project root  
**Problem:** Node resolves bare imports from the importing file's location, not the project root  
**Solution:** Run `npm install` inside `scripts/` directory. The `scripts/package.json` declares `pdf-lib` and `@pdf-lib/fontkit` — installing in the working project is not enough.

```bash
cd scripts/
npm install
```

**Version:** v1.2.0

---

### PDF form fields shift after skill update

**Area:** Dependencies  
**Symptom:** After updating the skill, stamped form fields appear at slightly different positions  
**Problem:** `scripts/package-lock.json` was `.gitignore`d, so `install.sh` using `rsync --delete` deleted your lockfile. Next `npm install` resolved different versions of `pdf-lib` and `@pdf-lib/fontkit` (pinned with carets), and PDF coordinate calculations shifted.  
**Solution:** The lockfile is now committed. If you have an existing checkout from before v2.0.1, run `npm ci --prefix scripts` to reinstall the versions recorded in the committed lockfile.

**Version:** v2.0.1

---

## Figma API & MCP

### Error: "Cannot assign to read-only property 'currentPage'"

**Area:** Figma plugin API  
**Symptom:** `figma.currentPage = page` throws when file opened with dynamic-page document access  
**Problem:** Files with dynamic pages reject direct assignment to `.currentPage`  
**Solution:** Use `setCurrentPageAsync()` instead:

```js
await figma.loadAllPagesAsync();
const page = figma.root.children.find(p => p.name === 'HR');
await figma.setCurrentPageAsync(page);  // ← Not figma.currentPage = page
```

**Version:** v1.2.0 (pdf-forms.md)

---

### Figma transition takes 10 minutes instead of 600 ms

**Area:** Figma Prototyping API  
**Symptom:** Smart Animate transition crawls for 10 minutes when you expected 0.6 seconds  
**Problem:** `duration` is in **seconds**, not milliseconds. Passing `600` asks for 600 seconds.  
**Solution:** 600 ms is `0.6`:

```js
transition: { type: 'SMART_ANIMATE', easing: { type: 'SLOW' }, duration: 0.6 }
```

**Version:** v2.1.0

---

### setReactionsAsync only keeps the last reaction

**Area:** Figma Prototyping API  
**Symptom:** Added Space and Backspace triggers separately, but only Backspace works  
**Problem:** `setReactionsAsync()` **replaces** every reaction on the frame  
**Solution:** Pass both Space and Backspace reactions in one array:

```js
await frame.setReactionsAsync([
  { trigger: { type: 'ON_KEY_DOWN', keyCodes: [32] }, actions: [...] },   // Space
  { trigger: { type: 'ON_KEY_DOWN', keyCodes: [8] }, actions: [...] }     // Backspace
]);
```

Calling it twice leaves only the second.

**Version:** v2.1.0

---

### Setting frame.reactions does nothing

**Area:** Figma Prototyping API  
**Symptom:** Assigning to `frame.reactions` has no effect  
**Problem:** Direct assignment to `.reactions` is deprecated and silently ignored in current builds  
**Solution:** Use `setReactionsAsync()` instead:

```js
await frame.setReactionsAsync([...]);  // ← Not frame.reactions = [...]
```

**Version:** v2.1.0

---

### Smart Animate hard-cuts instead of tweening

**Area:** Figma Prototyping  
**Symptom:** Slide transition cuts instead of moving elements smoothly  
**Problem:** Smart Animate matches layers by **name**. Two slides with layers called `Headline` and `Title` have nothing to tween.  
**Solution:** Give shared elements the **same layer name** on both frames. Two slides that both contain a layer called `Headline` will tween that headline's position, size, and color. This costs nothing at build time and is the whole difference between a deck that moves and one that flickers.

**Version:** v2.1.0

---

## File Handling

### Shell command fails: "No such file or directory" with visible filename

**Area:** Shell / File I/O  
**Symptom:** `ls`, `cp`, or other shell commands fail on a PDF filename you can see in Finder  
**Problem:** Filename contains U+2028 line separator characters, which break ordinary shell paths  
**Solution:** Copy the file to a safe name before processing:

```bash
python3 - <<'PYTHON'
from pathlib import Path
import shutil
matches = list(Path('.').glob('Problem*.pdf'))
if len(matches) != 1:
    raise SystemExit('Expected exactly one matching PDF; select the source explicitly.')
target = Path('safe-name.pdf')
if target.exists():
    raise SystemExit('safe-name.pdf already exists; choose another destination.')
shutil.copy2(matches[0], target)
PYTHON
```

Then work with `safe-name.pdf`. This happened with the source PDF for the communication strategy deck.

**Version:** v1.4.0

---

### Arabic text extracts in wrong order from PDF

**Area:** PDF text extraction  
**Symptom:** Extracting text from Arabic tables yields scrambled cell associations despite correct visual layout  
**Problem:** PDF text layer stores content in visual order but cell boundaries are lost  
**Solution:** For Arabic tables, transcribe from the rendered pages instead of relying on the text layer. Happened on pages 50–51 of the communication strategy deck's internal-initiative tables.

**Version:** v1.4.0

---

## Validation & Linting

### brand-check.py doesn't catch errors in reference docs

**Area:** Linting  
**Symptom:** `brand-check.py` passes but reference files contain banned patterns  
**Problem:** The script only parses fenced `css`/`html`/`svg` blocks, not prose  
**Solution:** This is by design — the linter ignores markdown prose so it doesn't flag the skill's own documentation, which legitimately quotes every banned word as examples. Reference prose is not mechanically validated. A future `--copy` mode could enforce rules on deliverable text with a scope switch.

**Version:** v1.4.0

---

### brand-check.py: "unknown --brand X; available: …" (exit 2)

**Area:** Linting  
**Symptom:** `brand-check.py --brand majara` (typo) stops with exit code 2 and lists the known brands  
**Problem:** Earlier versions silently fell back to the base AZM X palette when the name did not match a file in `config/sub-brands/`, so a typo produced a clean-looking report against the wrong brand  
**Solution:** Use one of the names printed after `available:` — they are the file stems in `config/sub-brands/*.json`. Files whose name starts with `_` (e.g. `_example-new-brand.json`) are templates and are never selectable; copy one to `config/sub-brands/<brand>.json` to add a brand.

**Version:** v2.2.0

---

### brand-check.py: "<brand>.json fails sub-brand-config.schema.json at …"

**Area:** Linting  
**Symptom:** `--brand` exits 2 with a message naming a JSON path and the schema complaint  
**Problem:** Every sub-brand config is validated against `schemas/sub-brand-config.schema.json` before it is used. The path after `at` (e.g. `token_overrides/custom_primitives/brand/x/accent`) is where the config disagrees with the schema  
**Solution:** Fix the config. `custom_primitives` values must be hex colours in any form `norm_hex` accepts (`#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`); alpha is dropped when the palette is built. If instead you see `warning: jsonschema not installed; skipping schema validation`, the check was skipped — `pip install jsonschema` (it is in `requirements-test.txt`) to enable it.

**Version:** v2.2.0

---

### --brand majarah still flags Oswald as a FONT blocker

**Area:** Linting  
**Symptom:** A Majarah deliverable using Oswald reports `non-brand font family "Oswald"` even though `majarah.json` declares it  
**Problem:** Versions before v2.2.0 ignored `token_overrides.typography_overrides` and only merged `custom_primitives`  
**Solution:** Update. `display_font` and `body_font` from the selected sub-brand config are now added to the accepted families for that run only (the base run and other brands still flag them). `extract-metrics.py` reads the same rule lists from `brand-check.py`, so the two tools always agree on banned words, hedging and dash counting.

**Version:** v2.2.0

---

### add-images.py: "FAILED to convert … : UnidentifiedImageError"

**Area:** Image pipeline  
**Symptom:** A file is skipped with the exception name and message printed after `FAILED to convert`  
**Problem:** Conversion now uses Pillow instead of the macOS-only `sips`, and reports the real error instead of a bare failure. `UnidentifiedImageError` means the file is not an image Pillow can open (HEIC needs the `pillow-heif` plugin); `ModuleNotFoundError: PIL` means Pillow is not installed  
**Solution:** `pip3 install -r requirements.txt`. Output is unchanged: 1600 px wide, aspect kept, RGB JPEG at quality 70, next free number in the section. A failed file does not consume a number, and the index rebuild only runs when at least one image was added.

**Version:** v2.2.0

---

## Configuration & Installation

### Skills CLI doesn't see the skill

**Area:** YAML parsing  
**Symptom:** `claude skills list` omits this skill, or skills CLI reports parse error  
**Problem:** Unquoted colon in `SKILL.md` frontmatter description: `communication strategy: communication planning` breaks strict YAML parsers  
**Solution:** Quote the description field:

```yaml
description: "Brand system for AZM X: visual identity, communication strategy: communication planning"
```

Fixed in v2.1.1 — update to latest.

**Version:** v2.1.1

---

## Known Limitations

### Purple and Yellow palette anchors are derived

**Area:** Design tokens  
**Symptom:** Purple/yellow `role-tint`, `role-border`, `role-mid` don't match an official palette board  
**Problem:** These six tokens are **derived** at ramp steps 50 / 400 / 600 (the median positions where orange, green, and red place real anchors), not sourced from a design deliverable  
**Solution:** These are documented as derived in their Figma descriptions. Replace with official values if a purple or yellow palette board is delivered. Do not treat them as canonical.

**Version:** v2.0.0

---

### text/subtle and icon/muted fail WCAG AA

**Area:** Design tokens  
**Symptom:** `text/subtle` and `icon/muted` measure 2.51:1 on white  
**Problem:** Inherited from existing designs; below WCAG AA (4.5:1)  
**Solution:** Fine for disabled states and decorative icons, **not acceptable for body text or functional UI**. Use `text/secondary` (4.86:1) or `text/primary` (15.3:1) for readable text.

**Version:** v2.0.0

---

## Content Strategy

### Cadence figures don't match weekly grids

**Area:** Editorial calendar  
**Symptom:** Monthly content count in recap doesn't match sum of weekly schedules  
**Problem:** The source deck's cadence recap disagrees with its own weekly grids. Example: Anatomi recap claims 1 Twitter + 1 YouTube long + 2 Shorts never scheduled in any week, while omitting 2 Instagram slots per week.  
**Solution:** Treat recap as **intended weighting** rather than audited count. Confirm against whoever holds the scheduling tool before finalizing a content calendar.

**Version:** v1.4.0

---

### Cadence numbers are monthly, not weekly

**Area:** Editorial calendar  
**Symptom:** "LinkedIn 3x" is ambiguous — per week or per month?  
**Problem:** The source deck never stated the unit  
**Solution:** Figures are **monthly**. Colab's row reconciles exactly against the grids on a monthly reading. Unqualified, "LinkedIn 3x" invites a fourfold planning error.

**Version:** v1.4.0

---

### CTA friction doesn't ramp over the month

**Area:** Editorial calendar  
**Symptom:** Expected monthly escalation in CTA friction, but week 2 is flat and week 4 ends low  
**Problem:** CTA friction is **per-surface** (blog vs. email), not a month-long progression  
**Solution:** The Sunday blog post is always low-friction. Escalation happens only on Tuesday and Thursday emails. No monthly ramp exists to follow.

**Version:** v1.4.0
