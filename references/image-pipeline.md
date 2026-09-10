# Image Pipeline — Add to Publish

A validated, repeatable pipeline for adding AZMX brand images to the library and publishing them with measured color analysis. The pipeline has processed 240 images across 8 color sections, generating the agent-readable index, the public gallery, and the recolor prompts reference.

The JPEGs themselves are not stored in this repository. They live in the separate `azmx-brand-cdn` repository and are served from the jsDelivr CDN at `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>.jpg` (the base URL is `$meta.cdn` in `scripts/image-meta.json`). What this repository keeps is the catalogue, `scripts/image-meta.json`, with each image's measured analysis; the index and gallery are generated from it, so neither needs the image files.

## The pipeline

| Stage | What happens | Tool |
|---|---|---|
| 1. Add | Source images resized to 1600px, compressed to JPEG quality 70, sequentially numbered per section, written into the `azmx-brand-cdn` checkout | `add-images.py` (Pillow) |
| 2. Analyze | Dominant color extracted via Pillow quantization, luminance calculated, nearest brand token matched; result appended to `scripts/image-meta.json` | `analyse_image()` in `rebuild-index.py` + Pillow |
| 3. Generate | Three outputs written from `scripts/image-meta.json`: agent index, public gallery HTML, recolor prompts markdown | `rebuild-index.py` |
| 4. Commit | Both repositories pushed: this one (catalogue, index, gallery; GitHub Pages deploys the gallery) and `azmx-brand-cdn` (the files; jsDelivr serves `main`) | git |

## Why measure every image

The library ships with measured pairing data, not assumed rules. Every image carries its dominant hex, nearest brand token, and a safe text-color recommendation derived from calculated luminance. That measurement proved the headline finding: all sections except White are dark surfaces (luminance < 0.18), so Electric blue fails contrast as body text on 235 of 240 images.

Without that measurement, a designer might set Electric text over a gradient that reads bright to the eye but measures dark. The pipeline calculates it once, writes it to the index, and the pairing becomes a known fact instead of a judgment call.

---

## Stage 1 — Add images with `add-images.py`

```bash
python3 scripts/add-images.py [--cdn-dir PATH] blue ~/Desktop/new-renders/
```

| Argument | Meaning |
|---|---|
| `--cdn-dir PATH` | The `azmx-brand-cdn` checkout to write into. Default: `../azmx-brand-cdn` next to this repository; the script stops with a clear error if it does not exist |
| Section | One of: `gradient`, `blue`, `white`, `orange`, `purple`, `red`, `green`, `yellow` |
| Path(s) | Files or folders. Accepts `.jpg`, `.jpeg`, `.png`, `.webp`, `.tif`, `.tiff`, `.heic` |

**What it does:**

1. **Collects** all image files from the paths, recursively scanning folders.
2. **Numbers** each file with the next free index in the target section (`blue-113.jpg`, `blue-114.jpg`, ...), taken from the highest entry for that section in `scripts/image-meta.json` — not from a local folder, which may be partial or absent.
3. **Resizes** to 1600 px wide with Pillow (height follows the aspect ratio).
4. **Compresses** to JPEG quality 70, matching the existing library size profile (EXIF orientation applied, RGB flattened).
5. **Saves** into `<cdn-dir>/images/<section>/`.
6. **Measures** each new file with `analyse_image()` (imported from `rebuild-index.py`) and appends `{f, dom, tok, L}` to `scripts/image-meta.json`.
7. **Rebuilds** the index and gallery by calling `rebuild-index.py`.
8. **Reminds** you to commit and push the CDN checkout: jsDelivr picks up `main` within ~12 h, or purge a path via `https://purge.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>`.

### Naming convention

Files are named `{section}-{index:03d}.jpg`:

```
blue-001.jpg
blue-002.jpg
gradient-034.jpg
orange-028.jpg
```

Zero-padded three-digit indices keep files sorted naturally. The script finds the highest index recorded for the section in `scripts/image-meta.json` and starts numbering from `max + 1`, so adding to a section whose last entry is `blue-112.jpg` starts at `blue-113.jpg`.

### Compression target

JPEG quality 70 balances file size and visual fidelity. The original Figma exports totaled 204 MB; compressing to quality 70 brought the full library down to 53 MB with no visible artifacts. A 1600px image at quality 70 typically lands between 150 KB and 350 KB depending on complexity.

### How the conversion runs

The conversion is done in Python with Pillow (`convert_image()` in `scripts/add-images.py`), so it runs the same on macOS, Linux and CI. Equivalent one-liner:

```python
from PIL import Image, ImageOps
im = ImageOps.exif_transpose(Image.open("source.png")).convert("RGB")
im.resize((1600, round(im.height * 1600 / im.width))).save("dest.jpg", "JPEG", quality=70)
```

This takes any supported source format and produces a 1600px-wide JPEG at quality 70.

---

## Stage 2 — Analyze and generate with `rebuild-index.py`

```bash
python3 scripts/rebuild-index.py
```

No arguments and no image files needed. Reads `scripts/image-meta.json` and regenerates three outputs. If a local `assets/images/<section>/*.jpg` tree is present (an offline working copy), the images are re-measured instead and `scripts/image-meta.json` is rewritten from them (its `$meta` block, including the CDN base, is kept):

| Output | Path | Content |
|---|---|---|
| Agent index | `references/image-index.md` | Markdown table with filename, concept tags, dominant hex, text pairing, direct download link |
| Public gallery | `index.html` | Standalone HTML gallery with tag filtering, recolor prompts, copy buttons, and responsive layout |
| Recolor prompts | `references/recolor-prompts.md` | Markdown version of the AI recolor prompts from `recolor-prompts.json` |

### Color analysis — Pillow quantization

`analyse_image(path)` measures each image's **dominant color** and **average luminance** using Pillow. It runs when `add-images.py` adds a file, or when `rebuild-index.py` re-measures a local copy of the library.

```python
im = Image.open(path).convert("RGB").resize((80, 80))
q = im.quantize(colors=5, method=Image.MEDIANCUT).convert("RGB")
dom = sorted(q.getcolors(10000), reverse=True)[0][1]
```

**Why 80 × 80?** Fast to analyze, large enough to capture the overall character. A 1600px source resized to 80px drops from 2.56 million pixels to 6,400 — a 400× speedup.

**Why 5 colors?** `MEDIANCUT` quantization reduces the image to its five most representative colors, then `getcolors(10000)` counts how many pixels fall into each. The most frequent color is the dominant.

**Why this is robust:** It ignores small highlights and captures the color the eye reads as the background. A navy image with a thin white frost line still reports navy as dominant.

### Token matching — Euclidean distance in RGB

Once the dominant RGB is extracted, the script finds the nearest brand token by minimizing squared distance:

```python
TOKENS = {
    "Electric #001AFF": (0x00, 0x1A, 0xFF),
    "Dark Navy #040038": (0x04, 0x00, 0x38),
    "Blue 900 #01006E": (0x01, 0x00, 0x6E),
    # ... 19 total tokens
}

def nearest(rgb):
    return min(TOKENS.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(rgb, kv[1])))[0]
```

This maps the measured dominant to the closest named brand color, so the index can say "Blue 900 `#01006E`" rather than an arbitrary hex like `#05006B`.

### Luminance — WCAG relative luminance

Average luminance is calculated per the WCAG 2.1 formula:

```python
def luminance(rgb):
    def f(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
```

Returns a value from 0.0 (black) to 1.0 (white). This is the **same formula** WCAG uses for contrast calculation, so a measured luminance of 0.15 definitively tells you Electric blue text (L ≈ 0.15) fails the 4.5:1 contrast requirement.

### Text pairing decision

The script translates luminance into a text recommendation:

```python
def text_for(lum):
    if lum < 0.18:
        return "White + Light Blue accent"
    if lum < 0.5:
        return "White, test contrast"
    return "Navy + Electric accent"
```

- **< 0.18:** Dark surface, pair with White titles and Light Blue accents (the Navy/gradient row from `colors.md`).
- **0.18 – 0.5:** Ambiguous, needs testing.
- **≥ 0.5:** Light surface, pair with Navy titles and Electric accents (the White row).

That 0.18 threshold came from measuring the full library. The White section averaged 0.27; everything else clustered below 0.15. The gap is unambiguous.

---

## Supporting data files

Two JSON files feed into the pipeline.

### `scripts/image-tags.json`

Maps each filename to three concept tags:

```json
{
  "blue-001.jpg": ["structure", "scale", "foundation"],
  "blue-002.jpg": ["strategy", "hierarchy", "order"],
  "gradient-001.jpg": ["energy", "flow", "depth"]
}
```

**Rules:**

- Three tags per image, no more, no fewer.
- Tags describe the **abstract concept** the image can represent (`momentum`, `precision`, `calm`), never literal objects (`stairs`, `cube`, `gradient`).
- Color names are never tags — color is already handled by section and measured pairing data.
- Tags are drawn from a controlled vocabulary of 70 terms to keep the library searchable.

The rebuild script reads this file and injects the tags into:

- The index table (`| Image | Concept tags | ...`)
- The gallery filter buttons (one button per tag, sorted by frequency)
- Each image's `alt` text and `data-tags` attribute for client-side filtering

### `scripts/recolor-prompts.json`

Contains AI prompts for converting images from one color theme to another:

```json
{
  "model": "Seeddance Edit V5",
  "note": "For best results converting an image from one theme color to another...",
  "prompts": [
    {
      "key": "blue",
      "label": "Blue",
      "swatch": "#001AFF",
      "summary": "Render into AZMX brand blue",
      "text": "Render this image in rich deep blue tones. The background is..."
    }
  ]
}
```

The rebuild script generates:

1. A recolor section in `index.html` with copy buttons (44px minimum target, `aria-label`, live region announcing copy).
2. A markdown reference at `references/recolor-prompts.md`.

The gallery copy button implementation follows UX rules: always visible (not hover-only), 180ms state transition, screen-reader announcement via `aria-live="polite"`. See the gallery renderer in `rebuild-index.py` for the full pattern.

---

## Outputs

### `references/image-index.md`

Agent-readable markdown table:

```markdown
## Abstract Blue (113)
| Image | Concept tags | Dominant | Text on top | Link |
|---|---|---|---|---|
| `blue-001.jpg` | structure, scale, foundation | `#01006E` | White + Light Blue accent | [download](...) |
```

This is what Claude reads to choose images. A search for "momentum" surfaces all images tagged with that concept, grouped by section.

### `index.html`

Standalone public gallery. Features:

- Responsive layout with sticky sidebar navigation on desktop, collapsed horizontal nav on mobile.
- Tag filter buttons that toggle `hidden` on `<figure>` elements client-side.
- Recolor prompts with copy buttons and keyboard-accessible focus states.
- All images lazy-loaded with `loading="lazy"`.
- Dark navy background (`#040038`), AZMX brand typography, and accessible color pairings.
- Social meta tags for sharing: Open Graph and Twitter Card with a 1280×640 cover image.

No build step. The file is self-contained HTML + inline CSS + inline JS. Hosted via GitHub Pages at `https://gamaleldientarek.github.io/azmx-brand/`.

### `references/recolor-prompts.md`

Markdown version of the recolor prompts for quick reference and copy-paste:

```markdown
## Blue  `#001AFF`

Render into AZMX brand blue.

\```text
Render this image in rich deep blue tones. The background is...
\```
```

---

## Usage examples

### Add images from a folder

```bash
python3 scripts/add-images.py blue ~/Desktop/midjourney-exports/
```

Adds all images from that folder to the `blue` section, numbering from the next free index.

### Add images from Figma

The full Figma export procedure is in `image-library.md`, lines 99–106. Summary:

1. Use `figma_execute` to loop image nodes and export via `exportAsync({ format: 'JPG', constraint: { type: 'WIDTH', value: 1600 } })`.
2. POST each result to a local receiver on `http://localhost:9223`.
3. Compress to quality 70 (`add-images.py` does this with Pillow).
4. `add-images.py` numbers them, writes them into the `azmx-brand-cdn` checkout, and records their analysis in `scripts/image-meta.json`.
5. Commit and push both repositories.

### Rebuild without adding

After editing `image-tags.json` or `image-meta.json`:

```bash
python3 scripts/rebuild-index.py
```

Regenerates all three outputs from the catalogue. To remove an image, delete its entry from `scripts/image-meta.json` (and its tags from `image-tags.json`), delete the file in `azmx-brand-cdn`, then rebuild.

### Search for a concept

Open `references/image-index.md` and search for the concept tag (`⌘F momentum`). The index shows all images with that tag, their section, and a direct download link.

Or use the live gallery: click a tag button to filter the grid client-side.

---

## Environment requirements

| Dependency | How to get it | Why |
|---|---|---|
| Python 3.11+ | Install Python and activate a virtual environment | Runs both scripts |
| Pillow | `pip3 install -r requirements.txt` | Resizing, JPEG compression, color quantization and luminance calculation (`add-images.py`; `rebuild-index.py` only when re-measuring a local copy) |
| `azmx-brand-cdn` checkout | `git clone https://github.com/Gamaleldientarek/azmx-brand-cdn.git ../azmx-brand-cdn` | Where `add-images.py` writes the JPEGs (`--cdn-dir` to point elsewhere). Not needed for `rebuild-index.py` |

No Node or npm is needed; running rebuild-index.py is the generation step. The pipeline is pure Python and runs on any platform.

---

## Gotchas

### 1. HEIC sources need a plugin

Pillow opens JPEG, PNG, WebP and TIFF out of the box. `.heic` exports from an iPhone need `pip3 install pillow-heif`; without it `add-images.py` reports `UnidentifiedImageError` for that file and skips it.

### 2. Pillow quantization is approximate

Quantization reduces a resized image to five colors. Treat the dominant color as a summary, not a guarantee of local contrast. Changes in source images or imaging-library versions can change the result.

### 3. Don't change the quality setting

`add-images.py` saves at JPEG quality 70. Saving at Pillow's default (75) or higher produces files 2–3× larger than the target profile. The first export before compression was 204 MB; at quality 70 the same set compressed to 53 MB with no visible loss.

### 4. Tag files as you add them

`image-tags.json` is maintained manually. When `add-images.py` adds `blue-114.jpg`, the file appears in the index with no tags (`—`). Tag it in `image-tags.json`:

```json
"blue-114.jpg": ["momentum", "direction", "energy"]
```

then re-run `rebuild-index.py`. The script does not auto-tag; a human assigns the three concept words.

### 5. Luminance measures the average, not the darkest region

A bright image with a small dark corner still measures bright. Luminance is calculated from the average RGB of all pixels, not the dominant color. That is correct: it tells you whether the overall surface is light or dark, which is what determines text contrast. A localized dark region does not make Electric text safe on a mostly-light surface.

### 6. The gallery is a static file

`index.html` is written once per rebuild. Changes to `image-tags.json` or `recolor-prompts.json` do not update the live gallery until you run `rebuild-index.py` and push. The gallery does not read from JSON at runtime; all data is baked into the HTML at build time.

### 7. GitHub Pages cache

After an authorized push, check the Pages deployment status before expecting the live gallery to change. Build failures, generated output, and caching can each explain missing updates. Hard-refresh the page (`⌘⇧R`) to bypass the browser cache.

### 8. jsDelivr cache

The image files are served by jsDelivr from the `main` branch of `azmx-brand-cdn`. A newly pushed file can take up to ~12 hours to appear at `@main`; purge the path to force it: `https://purge.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>`. Old GitHub Pages links (`gamaleldientarek.github.io/azmx-brand/assets/images/...`) are forwarded to the CDN by the root `404.html`.

---

## Reference synchronization

After changing tags or recolor prompts, regenerate the gallery and check reference consistency:

```bash
python3 scripts/rebuild-index.py
python3 scripts/sync-references.py --check
```

The sync script can synchronize JSON and Markdown, but does not rebuild index.html. Inspect generated diffs and image quality before publishing. The token pipeline is described in [Token pipeline](token-pipeline.md); the Figma-to-PDF pipeline is in [PDF forms](pdf-forms.md).

## Historical output counts

The catalogued set contains 240 images. Count the current entries in `scripts/image-meta.json` after a rebuild rather than treating these historical counts as assertions:

| Section | Count | CDN folder |
|---|---|---|
| Gradients | 34 | `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/gradient/` |
| Abstract Blue | 112 | `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/blue/` |
| White | 5 | `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/white/` |
| Purple | 24 | `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/purple/` |
| Orange | 28 | `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/orange/` |
| Red | 22 | `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/red/` |
| Green | 11 | `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/green/` |
| Yellow | 4 | `https://cdn.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/yellow/` |

Running `rebuild-index.py` prints these counts. Assert your count if automating the pipeline in CI.
