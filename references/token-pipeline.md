# Design Tokens — Figma to CSS

A validated, repeatable pipeline for maintaining the AZM X design token system. It transforms the five-collection Figma variable system into attribute-driven CSS custom properties, preserving aliases and supporting all twelve palette-theme combinations.

## Current local validation and scope

The repository also contains a 37-token RTL collection. The Figma exporter selects the five named original collections; it does not export this local RTL extension. Preserve that collection when reconciling a fresh export. The CSS generator currently emits the original palette/theme system, not RTL variables.

```bash
node scripts/tokens-to-css.mjs --validate
```

Validation checks all local collections, including unused aliases and RTL mode lengths. It reports broken links, cycles, and metadata-count mismatches. The export resolver still has a 12-hop limit; its depth-limit error alone does not prove a cycle. Validate first, then inspect the chain.

The exporter returns raw and DTCG representations. Neither is a drop-in replacement for the grouped local input: reconcile collection names, counts, mode order, literals and @name aliases before saving. Do not overwrite local extensions with a raw export.

The third project pipeline, Figma to fillable PDF, is documented in [PDF forms](pdf-forms.md). Image ingestion is documented in [Image pipeline](image-pipeline.md).

## The pipeline

| Stage | What happens | Tool |
|---|---|---|
| 1. Design | Five collections maintained in Figma: Primitives, Palette, Semantic, Component, Canvas | Figma Variables |
| 2. Export | Full token system extracted with aliases preserved, emitted in both raw and DTCG formats | `export-figma-tokens.js` via Figma Console |
| 3. Transform | Aliases resolved, twelve combinations flattened, CSS custom properties generated | `tokens-to-css.mjs` |
| 4. Integrate | CSS loaded into projects, controlled via `data-palette` and `data-theme` attributes | Standard HTML/CSS |

## Why a custom pipeline

No existing tool (Style Dictionary, Tokens Studio, Supernova) handles multi-mode aliasing the way AZM X needs it. The Palette collection has six modes (Blue, Orange, Green, Yellow, Purple, Red) and the Semantic collection has two modes (Light, Dark). A semantic token like `text/primary` aliases a palette token, which in turn aliases a primitive.

That chain must resolve differently for each of the twelve combinations (6 palettes × 2 themes). Standard tools either flatten modes prematurely or fail to resolve cross-collection aliases. This pipeline resolves every alias correctly, emits only what differs from the base (blue/light), and produces human-readable CSS that stays under 40 KB.

---

## Stage 1 — Design in Figma

### The five collections

| Collection | Modes | Purpose | Example tokens |
|---|---|---|---|
| **1. Primitives** | Mode 1 | Fixed foundation values: colors, sizes, font families | `color/blue/500`, `size/space/16`, `font/family/body` |
| **1b. Palette** | Blue, Orange, Green, Yellow, Purple, Red | Brand accent mapped per palette | `accent/base`, `accent/tint`, `gradient/start` |
| **2. Semantic** | Light, Dark | Theme-aware UI colors | `text/primary`, `surface/page`, `border/default` |
| **3. Component** | Mode 1 | Component-specific tokens | `button/bg-primary`, `card/shadow` |
| **4. Canvas** | Mode 1 | Document/presentation surface tokens | `canvas/fill`, `doc/text` |

### Naming convention

Use slash-separated paths that read like a hierarchy:

```
color/blue/500
size/space/16
text/primary
button/bg-primary
```

Never use camelCase or underscores. The export script transforms slashes into dots for DTCG (`color.blue.500`) and into kebab-case for CSS custom properties (`--azmx-color-blue-500`).

### Aliasing rules

Aliases flow downward through the collection hierarchy:

- **Primitives** → literals only, no aliases
- **Palette** → alias Primitives
- **Semantic** → alias Palette or Primitives
- **Component** → alias Semantic, Palette, or Primitives
- **Canvas** → alias Semantic, Palette, or Primitives

Never alias upward or sideways. A Palette token cannot reference a Semantic token. This prevents circular dependencies and makes resolution deterministic.

### The twelve combinations

The system produces twelve resolved outputs by crossing six palettes with two themes:

| Palette | Light theme | Dark theme |
|---|---|---|
| Blue (default) | `data-palette="blue" data-theme="light"` or plain `<body>` | `data-palette="blue" data-theme="dark"` |
| Orange | `data-palette="orange" data-theme="light"` | `data-palette="orange" data-theme="dark"` |
| Green | `data-palette="green" data-theme="light"` | `data-palette="green" data-theme="dark"` |
| Yellow | `data-palette="yellow" data-theme="light"` | `data-palette="yellow" data-theme="dark"` |
| Purple | `data-palette="purple" data-theme="light"` | `data-palette="purple" data-theme="dark"` |
| Red | `data-palette="red" data-theme="light"` | `data-palette="red" data-theme="dark"` |

Blue/Light is the house look — the default when no attributes are set.

### Figma file location

**File:** "New Direction Library | AZM X"  
**File key:** `j8ugBpb1yUUyL8hfb6FHKR`

All variables live in this one file. Never fragment the system across multiple Figma files — it breaks cross-collection aliasing.

---

## Stage 2 — Export from Figma

### Running the export script

The export script runs **inside the Figma Console**, accessed through the Figma MCP plugin. Never run it as a standalone Node script — it requires the Figma plugin sandbox API.

#### Route A (preferred) — `figma_execute`

```
mcp__plugin_figma_figma__execute
  fileKey: j8ugBpb1yUUyL8hfb6FHKR
  script: <paste the full contents of scripts/export-figma-tokens.js>
```

Returns the full export object: `{ raw, dtcg, bytes }`.

#### Route B — paste directly into plugin console

1. Open the Figma file
2. Launch the Figma Desktop Bridge plugin
3. Open its DevTools console (Plugins → Development → Open Console)
4. Paste the entire `scripts/export-figma-tokens.js` script
5. Copy the returned JSON

Route A is preferred — it runs in one tool call and avoids clipboard size limits.

### What gets exported

The script returns two formats in one object:

```js
{
  raw: {
    meta: { /* file info, export date, collection counts */ },
    tokens: {
      "1. Primitives": [ /* array of token objects */ ],
      "1b. Palette": [ /* array of token objects */ ],
      "2. Semantic": [ /* array of token objects */ ],
      "3. Component": [ /* array of token objects */ ],
      "4. Canvas": [ /* array of token objects */ ]
    },
    styles: {
      paint: [ /* Figma paint styles */ ],
      text: [ /* Figma text styles */ ]
    }
  },
  dtcg: {
    "1. Primitives": { /* nested DTCG tree */ },
    "1b. Palette [Blue]": { /* Blue mode as separate tree */ },
    "1b. Palette [Orange]": { /* Orange mode as separate tree */ },
    // ... one tree per mode
  },
  bytes: 142857  // JSON size for diagnostics
}
```

### Raw format

Mirrors Figma exactly, preserves multi-mode structure:

```json
{
  "name": "accent/base",
  "type": "COLOR",
  "scopes": ["ALL_SCOPES"],
  "modes": {
    "Blue": { "alias": "color/blue/600" },
    "Orange": { "alias": "color/orange/600" },
    "Green": { "alias": "color/green/600" }
  }
}
```

Aliases are preserved as **names**, not Figma's internal IDs, so the export is human-readable and survives token renames.

### DTCG format (W3C v2025.10)

The W3C Design Tokens Community Group format. Multi-mode collections are split into one tree per mode, since DTCG has no native mode concept:

```json
{
  "1b. Palette [Blue]": {
    "accent": {
      "base": {
        "$value": "{color.blue.600}",
        "$type": "color"
      }
    }
  }
}
```

Aliases use curly-brace syntax `{path.to.token}`, slashes become dots.

**Why emit both formats?**

- **Raw:** Best for round-tripping. If you need to re-import tokens into Figma or another tool that understands multi-mode variables, raw preserves the structure.
- **DTCG:** Standard interchange format. Tools like Style Dictionary, Penpot, and Supernova consume DTCG. Emit it even though we don't use it downstream — it proves the system is portable.

### Saving the export

Write the returned JSON to `assets/tokens/azmx-tokens.json`:

```js
const result = /* the return value from figma_execute */;

// Stamp the export date
result.raw.meta.exported = new Date().toISOString().split('T')[0];

// Flatten into the saved shape
const saved = {
  $meta: result.raw.meta,
  "1. Primitives": {
    modes: result.raw.meta.collections.find(c => c.name === "1. Primitives").modes,
    count: result.raw.meta.collections.find(c => c.name === "1. Primitives").count,
    tokens: Object.fromEntries(result.raw.tokens["1. Primitives"].map(t => [
      t.name, 
      t.modes["Mode 1"].value
    ]))
  },
  // ... repeat for each collection, preserving mode arrays for multi-mode ones
};

fs.writeFileSync('assets/tokens/azmx-tokens.json', JSON.stringify(saved, null, 2));
```

The saved format is **flattened for consumption by `tokens-to-css.mjs`**, not an exact mirror of the raw export. See `assets/tokens/azmx-tokens.json` for the canonical structure.

---

## Stage 3 — Transform to CSS

### Running tokens-to-css.mjs

The script reads `assets/tokens/azmx-tokens.json` and resolves all aliases.

#### Generate all twelve combinations (default)

```bash
node scripts/tokens-to-css.mjs > azmx-tokens.css
```

Produces attribute-driven CSS:

```css
/* Semantic — blue / light */
:root {
  --azmx-text-primary: #111927;
  --azmx-surface-page: #FFFFFF;
  /* ... */
}

/* orange / light — 47 overrides */
[data-palette="orange"] {
  --azmx-accent-base: #C8643B;
  --azmx-gradient: linear-gradient(145deg, #FCD7C8 0%, #F79A74 55%, #A1502F 100%);
  /* ... */
}

/* blue / dark — 89 overrides */
[data-theme="dark"] {
  --azmx-text-primary: #F9FAFB;
  --azmx-surface-page: #111927;
  /* ... */
}
```

The CSS emits only what differs from blue/light, so the file stays readable. Orange/light overrides ~47 variables, dark theme ~89 variables, and orange/dark combines both diffs.

#### Flatten one palette-theme combination

```bash
node scripts/tokens-to-css.mjs --palette orange --theme dark > orange-dark.css
```

Produces a single `:root` block with fully resolved values. Use this for embedding tokens in a static site that locks to one combination.

#### Output as JSON

```bash
node scripts/tokens-to-css.mjs --palette blue --theme light --json > resolved.json
```

Returns a flat object of resolved token values:

```json
{
  "text/primary": "#111927",
  "surface/page": "#FFFFFF",
  "accent/base": "#001AFF"
}
```

Useful for programmatic access or debugging alias resolution.

### CLI flags

| Flag | Argument | Effect |
|---|---|---|
| `--palette` | `blue` \| `orange` \| `green` \| `yellow` \| `purple` \| `red` | Flatten to one palette. Defaults to the light theme when --theme is omitted. |
| `--theme` | `light` \| `dark` | Flatten to one theme. Defaults to the blue palette when --palette is omitted. |
| `--json` | (none) | Output JSON instead of CSS. Works with or without `--palette`/`--theme`. |

Omit all flags to generate the full attribute-driven CSS (the default and recommended output).

### Alias resolution algorithm

Resolution is a recursive walk with loop detection:

```js
function resolve(ref, paletteIdx, themeIdx, depth = 0) {
  if (depth > 12) throw new Error('alias loop at ' + ref);
  if (typeof ref !== 'string' || !ref.startsWith('@')) return ref;
  
  const name = ref.slice(1);  // strip the @ prefix
  
  if (name in primitives) return primitives[name];
  if (name in palette)    return resolve(palette[name][paletteIdx], paletteIdx, themeIdx, depth + 1);
  if (name in semantic)   return resolve(semantic[name][themeIdx], paletteIdx, themeIdx, depth + 1);
  if (name in component)  return resolve(component[name], paletteIdx, themeIdx, depth + 1);
  if (name in canvas)     return resolve(canvas[name], paletteIdx, themeIdx, depth + 1);
  
  throw new Error('unknown token: ' + name);
}
```

**How it works:**

1. Literal values (strings, numbers, colors) return as-is
2. Aliases start with `@` and reference another token by name
3. Palette tokens are arrays — index by `paletteIdx` to pick the mode
4. Semantic tokens are arrays — index by `themeIdx` to pick the mode
5. Primitives, Component, and Canvas are single-mode — no indexing needed
6. Loop depth check prevents infinite recursion on circular references

**Example resolution chain:**

```
@text/primary                    (semantic token, mode Light)
  → @neutral/text-primary        (palette token, mode Blue)
    → @color/neutral/900         (primitive token)
      → "#111927"                (literal)
```

For orange/dark, the same semantic token resolves differently:

```
@text/primary                    (semantic token, mode Dark)
  → @neutral/text-primary-invert (palette token, mode Orange)
    → @color/neutral/50          (primitive token)
      → "#F9FAFB"                (literal)
```

---

## Stage 4 — Integrate into projects

### Loading the tokens

```html
<link rel="stylesheet" href="azmx-tokens.css">
```

Blue/light is the default. To switch palettes or themes:

```html
<body data-palette="orange" data-theme="dark">
```

The attributes cascade, so you can set palette at the root and toggle theme on a subtree:

```html
<body data-palette="green">
  <main data-theme="light">  <!-- green/light --></main>
  <aside data-theme="dark">  <!-- green/dark --></aside>
</body>
```

### Accessing tokens in CSS

```css
.card {
  background: var(--azmx-surface-card);
  color: var(--azmx-text-primary);
  border: 1px solid var(--azmx-border-default);
  border-radius: var(--azmx-radius-md);
}
```

Never hardcode colors or sizes. Every UI decision should map to a semantic token. If a token doesn't exist for your use case, add it to Figma and re-export — do not invent one-off values.

### JavaScript access

```js
const root = getComputedStyle(document.documentElement);
const primary = root.getPropertyValue('--azmx-text-primary').trim();
console.log(primary);  // "#111927"
```

Or set dynamically:

```js
document.documentElement.style.setProperty('--azmx-accent-base', '#FF0000');
```

This works but is rarely needed — prefer changing `data-palette` or `data-theme` to switch entire combinations atomically.

---

## Token categories

### Primitives (285 tokens)

The fixed foundation. Never alias these from outside the Primitives collection:

| Category | Example | Use |
|---|---|---|
| Colors | `color/blue/500`, `color/neutral/900` | Raw swatches, aliased by Palette |
| Spacing | `size/space/16`, `size/space/64` | Layout gaps, padding |
| Font sizes | `size/font/16`, `size/font/48` | Type scale |
| Line heights | `size/line/24`, `size/line/64` | Leading |
| Radii | `size/radius/8`, `size/radius/full` | Border radii |
| Opacity | `size/opacity/60`, `size/opacity/100` | Alpha values |
| Font families | `font/family/display`, `font/family/body` | Typefaces |

### Palette (19 tokens, 6 modes)

Brand accent, mapped per palette:

```
accent/tint     — lightest tint, background washes
accent/subtle   — soft fills
accent/soft     — muted accents
accent/on-dark  — accent on dark surfaces
accent/base     — primary brand color (Electric Blue #001AFF in Blue mode)
accent/strong   — saturated accent
accent/deep     — deepest shade

gradient/start  — brand gradient starting color
gradient/mid    — brand gradient midpoint
gradient/end    — brand gradient end
```

The gradient tokens resolve into a ready-made CSS gradient via `--azmx-gradient`, computed per palette.

### Semantic (120+ tokens, 2 modes)

UI building blocks that change between light and dark:

| Group | Examples |
|---|---|
| Text | `text/primary`, `text/secondary`, `text/disabled`, `text/inverse` |
| Surfaces | `surface/page`, `surface/card`, `surface/overlay` |
| Borders | `border/default`, `border/strong`, `border/focus` |
| States | `state/hover`, `state/active`, `state/disabled` |
| Feedback | `feedback/success`, `feedback/warning`, `feedback/danger`, `feedback/info` |
| Shadows | `shadow/sm`, `shadow/md`, `shadow/lg` |

### Component (56 tokens)

Component-specific overrides:

```
button/bg-primary
button/text-primary
card/shadow
input/border-focus
```

Use these when a component needs a token that doesn't fit the semantic set. If you find yourself adding many component tokens, the semantic layer may need expansion instead.

### Canvas (4 tokens)

Document and presentation surfaces, separate from UI:

```
canvas/fill             — page background for presentations
canvas/overlay          — scrim or overlay
doc/text                — document body text
doc/heading             — document headings
```

Canvas tokens exist because presentation decks and PDFs use different color decisions than interactive UI.

---

## Gotchas

### Figma plugin sandbox limitations

- **No `fs` module.** The script cannot write files. Always return JSON and save it outside the sandbox.
- **No `Date` constructor in some runtimes.** Stamp the `exported` date *after* receiving the result, not inside the script.
- **`figma.currentPage = page` fails with document access.** Use `await figma.setCurrentPageAsync(page)` instead.

### Alias format in saved JSON

The saved `azmx-tokens.json` uses `@token/name` for aliases, not Figma's internal IDs or DTCG's `{token.name}` syntax. The `@` prefix is the resolver's trigger — it's specific to this pipeline, not a standard.

### Mode order matters

Palette modes are saved as arrays in palette token order:

```json
"accent/base": [
  "@color/blue/600",
  "@color/orange/600",
  "@color/green/600",
  "@color/yellow/600",
  "@color/purple/600",
  "@color/red/600"
]
```

The first element is Blue (index 0), the second is Orange (index 1), etc. If you reorder modes in Figma, the export must preserve that order, or resolution breaks. The export script sorts modes by the `modes` array in the collection metadata to keep them stable.

### CSS variable name collisions

All tokens are prefixed `--azmx-` to avoid collisions with other libraries. Never strip the prefix — it's the namespace.

### Circular alias detection

The export resolver stops after 12 alias hops, whether the chain is cyclic or simply too long:

```
Error: alias loop at text/primary
```

Use --validate to distinguish a real cycle from a long chain. A real cycle must be removed from the source token relationships.

### Dark theme != inverted colors

Dark theme is not a programmatic inversion of light. Many tokens stay the same between modes (radii, spacing, most feedback colors). The set of changed tokens depends on the source data. Always design both modes in Figma — never generate dark by flipping light values.

### File size

Measure the generated file for the current data; sizes vary as tokens change. Use the full file when runtime palette/theme switching is needed.

---

## Verification checklist

After export and transform, confirm:

| Check | How | Expect |
|---|---|---|
| Collection count | Each top-level collection’s `count` and actual `tokens` length | 285 primitives, 19 palette, 186 semantic, 56 component, 4 canvas, 37 RTL |
| Modes preserved | Each top-level collection’s `modes` | Palette has 6 modes, Semantic has 2 |
| Alias syntax | Grep for `"@` in saved JSON | All aliases use `@token/name`, not Figma IDs |
| No unresolved | Run `tokens-to-css.mjs`, check stderr | No `unknown token` errors |
| CSS output | Inspect generated CSS | Nonempty, with resolved values and selectors |
| Blue/light default | Open the CSS, check `:root` block | Should define all semantic tokens |
| Attribute overrides | Check `[data-palette="orange"]` block | Should override values that differ from blue/light |
| Gradient correct | Inspect `--azmx-gradient` in orange mode | Should use orange gradient stops, not blue |

---

## Workflow summary

**When to re-export:**

- Any token value changed in Figma
- A token added or removed
- A token renamed
- Modes reordered

**When NOT to re-export:**

- CSS structure changed but tokens unchanged
- You only need one palette-theme combination (re-run `tokens-to-css.mjs` with flags instead)

**Re-export procedure:**

1. Ensure all changes are saved and published in Figma
2. Run `scripts/export-figma-tokens.js` via `figma_execute`
3. Flatten and save the result to `assets/tokens/azmx-tokens.json`
4. Run `node scripts/tokens-to-css.mjs > azmx-tokens.css`
5. Verify output size and spot-check a few token values
6. Commit both `azmx-tokens.json` and `tokens.css`

**Development iteration:**

While building a new feature, you rarely need to re-export. Load `azmx-tokens.css` and reference tokens by name. If a token is missing, note it, finish the feature using a placeholder, then batch-add missing tokens to Figma and re-export once.

---

## Reusable scripts

Both scripts are versioned in `scripts/`:

| Script | Runs where | Purpose |
|---|---|---|
| `export-figma-tokens.js` | Figma plugin sandbox | Extracts all variables and styles, emits raw + DTCG |
| `tokens-to-css.mjs` | Node, locally | Resolves aliases, generates attribute-driven CSS or JSON |

The token-to-CSS script needs no npm packages. Install the PDF tool and test dependencies separately:

```bash
npm ci --prefix scripts
```

No dependencies needed for `export-figma-tokens.js` — it runs entirely in the Figma sandbox.

---

## Worked example — typical export

**Starting state:**

- 5 collections, 285 primitives, 19 palette (6 modes), 127 semantic (2 modes), 34 component, 12 canvas
- Last export: 2026-08-08
- Today: 2026-09-08

**Change:** Added three new semantic tokens for a new `toast/` component group: `toast/bg`, `toast/text`, `toast/border`. Each aliases existing semantic tokens differently per theme.

**Steps:**

1. Open "New Direction Library | AZM X" in Figma Desktop
2. Verify the three tokens exist in the Semantic collection, both Light and Dark modes
3. Run `figma_execute` with `scripts/export-figma-tokens.js`
4. Receive JSON with `bytes: 146820` (slightly larger than before)
5. Flatten and write to `assets/tokens/azmx-tokens.json`, stamp `exported: "2026-09-08"`
6. Run `node scripts/tokens-to-css.mjs > azmx-tokens.css`
7. Check file size: 39124 bytes (38 KB, up from 38712 — the three new tokens added ~400 bytes)
8. Spot-check one new token: `--azmx-toast-bg` is `#FFFFFF` in `:root`, `#1F2A37` in `[data-theme="dark"]`
9. Commit:

```bash
git add assets/tokens/azmx-tokens.json azmx-tokens.css
git commit -m "tokens: add toast component semantic tokens (toast/bg, toast/text, toast/border)"
```

**Result:** The toast component can now reference `var(--azmx-toast-bg)` and it will resolve correctly in both themes, without hardcoding colors.
