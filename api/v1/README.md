# AZMX Brand API v1

**Version:** 1.0.0  
**Base URL:** `https://gamaleldientarek.github.io/azmx-brand/api/v1/`  
**Format:** JSON  
**Authentication:** None (public read-only)

## Overview

The AZMX Brand API provides programmatic access to AZMX brand guidelines, design tokens, voice rules, audience personas, and content templates. This versioned API enables external tools, integrations, and third-party developers to query brand data without parsing markdown documentation.

Every endpoint is a static JSON file generated from the reference documents by `scripts/build-api.sh`. Nothing in `api/v1/` is hand-edited; `api/v1/index.json` describes every endpoint with counts computed from the data.

### Key Features

- **587 Design Tokens** - Six collections: primitives, palette (six modes), semantic (Light/Dark), component, canvas, RTL
- **6 Color Palettes** - Blue with its 12-step ramp, plus five secondary palettes with signature, deep, and text-safe values
- **Typography System** - 2 font families, 7 weights, a 16-role type scale, and usage rules
- **Voice Guidelines** - The four voice dimensions, tone rules, no-AI-tells writing mechanics, and format-specific rules
- **8 Audience Personas** - Target segments with pain points and verbatim core messages
- **15 Content Prompt Templates** - Briefs, articles, case studies, social customisation, localisation, and more
- **240 Brand Images** - Catalogued image library with three concept tags per image

### Use Cases

- **Design Tool Plugins** - Sync AZMX tokens into Figma, Sketch, or Adobe XD
- **Content Management Systems** - Validate brand compliance in CMS workflows
- **Marketing Automation** - Generate on-brand content using voice guidelines and personas
- **Agency Integrations** - Provide brand data to external partners without sharing credentials
- **Internal Dashboards** - Display brand metrics and guidelines in custom tooling
- **AI Content Generation** - Feed brand voice and audience data to LLM systems

---

## Getting Started

### Quick Start

The AZMX Brand API is read-only, requires no authentication, and returns JSON. Start with a simple request:

```bash
curl https://gamaleldientarek.github.io/azmx-brand/api/v1/index.json
```

This returns the API index: `$meta` (version, base URL, contact) plus every endpoint with its description and data structure.

### Your First Integration

**Goal:** Fetch the AZMX blue palette and use it in your application.

**Step 1: Fetch the palettes**

```javascript
const response = await fetch('https://gamaleldientarek.github.io/azmx-brand/api/v1/palettes.json');
const data = await response.json();
```

**Step 2: Extract the blue palette**

```javascript
const bluePalette = data.palettes.find(p => p.name === 'Blue');
console.log('Blue palette ramp:', bluePalette.ramp);
// [ { step: "Blue 50", hex: "#F0F5FF", notes: "Soft light surface: ..." }, ..., { step: "Blue 1000", hex: "#040038", notes: "..." } ]
```

**Step 3: Apply to your CSS**

```javascript
const cssVars = bluePalette.ramp
  .map(({ step, hex }) => `  --blue-${step.split(' ')[1]}: ${hex};`)
  .join('\n');

const css = `:root {\n${cssVars}\n}`;
console.log(css);
```

**Output:**

```css
:root {
  --blue-50: #F0F5FF;
  --blue-100: #DDE8FF;
  --blue-200: #BFD5FF;
  /* ... */
  --blue-600: #001AFF;
  /* ... */
  --blue-1000: #040038;
}
```

### Common Patterns

#### Pattern 1: Load All Design Tokens

```javascript
const BASE_URL = 'https://gamaleldientarek.github.io/azmx-brand/api/v1';

async function loadBrandTokens() {
  const tokens = await fetch(`${BASE_URL}/tokens.json`).then(r => r.json());
  const palettes = await fetch(`${BASE_URL}/palettes.json`).then(r => r.json());
  const typography = await fetch(`${BASE_URL}/typography.json`).then(r => r.json());

  return { tokens, palettes, typography };
}
```

#### Pattern 2: Generate Content with Voice Guidelines

```python
import requests

BASE_URL = "https://gamaleldientarek.github.io/azmx-brand/api/v1"

# Load voice and audience data
voice = requests.get(f"{BASE_URL}/voice.json").json()
audiences = requests.get(f"{BASE_URL}/audiences.json").json()

# Find specific persona
ceo_persona = next(p for p in audiences['personas'] if p['name'] == 'C-Suite')

# Build system prompt for LLM
system_prompt = f"""
Write in the AZMX voice. {voice['voice_summary']}
- Dimensions: {', '.join(d['dimension'] for d in voice['dimensions'])}
- Avoid: {'; '.join(voice['writing_mechanics'])}

Target: {ceo_persona['name']} ({ceo_persona['motion']})
Message: {ceo_persona['core_message']}
"""
```

#### Pattern 3: Validate Brand Compliance

```javascript
// Check if colors match the AZMX primitives (all ramps, neutrals, base colors)
async function validateBrandColors(colors) {
  const tokens = await fetch('https://gamaleldientarek.github.io/azmx-brand/api/v1/tokens.json')
    .then(r => r.json());

  const primitives = tokens.collections.find(c => c.name === '1. Primitives').tokens;
  const approvedColors = new Set(
    Object.entries(primitives)
      .filter(([name, value]) => name.startsWith('color/') && typeof value === 'string' && value.startsWith('#'))
      .map(([, value]) => value.toUpperCase())
  );

  const violations = colors.filter(c => !approvedColors.has(c.toUpperCase()));

  return {
    valid: violations.length === 0,
    violations,
    message: violations.length > 0
      ? `Found ${violations.length} off-brand colors: ${violations.join(', ')}`
      : 'All colors are on-brand'
  };
}

// Usage
const result = await validateBrandColors(['#001AFF', '#FFFFFF', '#FF00FF']);
console.log(result);
// { valid: false, violations: ['#FF00FF'], message: '...' }
```

#### Pattern 4: Select Brand Images by Tag

```bash
# Fetch all images tagged "focus"
curl -s https://gamaleldientarek.github.io/azmx-brand/api/v1/images.json | \
  jq '.images[] | select(.tags | contains(["focus"])) | {filename, tags}'
```

The image file itself lives in the repository at `assets/images/<prefix>/<filename>`, where the prefix is the part of the filename before the first dash (`blue-014.jpg` → `assets/images/blue/blue-014.jpg`):

```
https://github.com/Gamaleldientarek/azmx-brand/raw/main/assets/images/blue/blue-014.jpg
```

### Language-Specific Examples

#### JavaScript / TypeScript

```typescript
interface RampStep {
  step: string;   // "Blue 600"
  hex: string;    // "#001AFF"
  notes: string;
}

interface BluePalette {
  name: 'Blue';
  description: string;
  ramp: RampStep[];
}

interface SecondaryPalette {
  name: 'Orange' | 'Green' | 'Yellow' | 'Purple' | 'Red';
  signature: string;
  deep: string;
  text_safe_step: string;   // e.g. "color/orange/700"
  text_safe_hex: string;
  description: string;
}

type BrandPalette = BluePalette | SecondaryPalette;

async function getBrandPalette(name: string): Promise<BrandPalette | null> {
  const response = await fetch(
    'https://gamaleldientarek.github.io/azmx-brand/api/v1/palettes.json'
  );
  const data = await response.json();
  return data.palettes.find((p: BrandPalette) => p.name === name) || null;
}

// Usage
const orange = (await getBrandPalette('Orange')) as SecondaryPalette;
console.log(orange.signature); // "#F47A48"
```

#### Python

```python
import requests
from typing import Dict, List, Optional

BASE_URL = "https://gamaleldientarek.github.io/azmx-brand/api/v1"

class AZMXBrandAPI:
    def __init__(self):
        self.base_url = BASE_URL

    def get_palette(self, name: str) -> Optional[Dict]:
        response = requests.get(f"{self.base_url}/palettes.json")
        palettes = response.json()['palettes']
        return next((p for p in palettes if p['name'] == name), None)

    def get_personas(self, motion: str = None) -> List[Dict]:
        response = requests.get(f"{self.base_url}/audiences.json")
        personas = response.json()['personas']

        if motion:
            return [p for p in personas if p['motion'] == motion]
        return personas

# Usage
api = AZMXBrandAPI()
blue = api.get_palette('Blue')
blue_600 = next(r['hex'] for r in blue['ramp'] if r['step'] == 'Blue 600')  # "#001AFF"
b2g_personas = api.get_personas('B2G')
```

#### Shell Script

```bash
#!/bin/bash
BASE_URL="https://gamaleldientarek.github.io/azmx-brand/api/v1"

# Fetch the Blue 600 (Electric) value
BLUE_600=$(curl -s "${BASE_URL}/palettes.json" | \
  jq -r '.palettes[] | select(.name == "Blue") | .ramp[] | select(.step == "Blue 600") | .hex')

echo "Blue 600: $BLUE_600"

# Get all B2B personas
curl -s "${BASE_URL}/audiences.json" | \
  jq '.personas[] | select(.motion == "B2B") | .name'
```

### Interactive Documentation

For live API exploration, visit the interactive documentation:

**https://gamaleldientarek.github.io/azmx-brand/api-docs/examples.html**

Includes:
- Live API request playground
- Copy-paste code examples in multiple languages
- Response previews
- Common use case templates

---

## Endpoints

Every endpoint (except the index) starts with the same envelope: `version` (the API version) and `description`, followed by the payload. Endpoints that return a list also carry a `count`.

### 1. Index

**GET** `/index.json`

Returns API metadata (`$meta`) and a list of all available endpoints with descriptions, computed data structure summaries, and size estimates.

**Response Structure:**
```json
{
  "$meta": {
    "name": "AZMX Brand API",
    "version": "1.0.0",
    "base_url": "https://gamaleldientarek.github.io/azmx-brand/api/v1",
    "docs_url": "https://gamaleldientarek.github.io/azmx-brand/api-docs/",
    "repository": "https://github.com/Gamaleldientarek/azmx-brand",
    "updated": "2026-09-10",
    "contact": { "organization": "AZMX", "email": "brand@azmx.sa" }
  },
  "endpoints": [
    { "path": "/tokens.json", "name": "Design Tokens", "description": "...", "data_structure": {...}, "example_url": "...", "size_estimate": "~40KB" }
  ],
  "usage": {...},
  "examples": [...],
  "resources": {...}
}
```

**Example:**
```bash
curl https://gamaleldientarek.github.io/azmx-brand/api/v1/index.json
```

---

### 2. Design Tokens

**GET** `/tokens.json`

Returns all 587 design tokens grouped into six collections. Single-mode collections map a token name to its value; multi-mode collections map it to an array with one value per mode (in `modes` order). A value starting with `@` aliases another token.

**Response Structure:**
```json
{
  "version": "1.0.0",
  "description": "AZM X Design Tokens - 587 design tokens across 6 collections",
  "name": "AZM X Design Tokens",
  "source": "New Direction Library | AZM X",
  "source_version": "2.0.0",
  "exported": "2026-08-08",
  "count": 587,
  "collections": [
    { "name": "1. Primitives", "modes": ["Mode 1"], "count": 285, "tokens": { "color/blue/200": "#BFD5FF", "...": "..." } },
    { "name": "1b. Palette", "modes": ["Blue", "Orange", "Green", "Yellow", "Purple", "Red"], "count": 19, "tokens": { "accent/base": ["@color/blue/600", "..."] } },
    { "name": "2. Semantic", "modes": ["Light", "Dark"], "count": 186, "tokens": { "surface/page": ["@color/base/white", "@accent/ground"] } },
    { "name": "3. Component", "modes": ["Mode 1"], "count": 56, "tokens": {} },
    { "name": "4. Canvas", "modes": ["Mode 1"], "count": 4, "tokens": {} },
    { "name": "RTL", "modes": ["LTR", "RTL"], "count": 37, "tokens": {} }
  ]
}
```

**Example:**
```javascript
fetch('https://gamaleldientarek.github.io/azmx-brand/api/v1/tokens.json')
  .then(res => res.json())
  .then(data => {
    const semantic = data.collections.find(c => c.name === '2. Semantic');
    const light = semantic.modes.indexOf('Light');
    console.log('Light mode page background:', semantic.tokens['surface/page'][light]); // "@color/base/white"
  });
```

---

### 3. Color Palettes

**GET** `/palettes.json`

Returns 6 brand color palettes. Blue carries its full 12-step ramp; the five secondary palettes expose their signature, deep, and text-safe colors (their full ramps are in `/tokens.json` under `1. Primitives`, e.g. `color/orange/500`).

**Response Structure:**
```json
{
  "version": "1.0.0",
  "description": "AZMX color palettes - one primary (Blue) and five secondary palettes",
  "count": 6,
  "palettes": [
    {
      "name": "Blue",
      "description": "Primary brand palette with Electric (#001AFF) and Dark Navy (#040038)",
      "ramp": [
        { "step": "Blue 50", "hex": "#F0F5FF", "notes": "Soft light surface: panels, table zebra, image backings" },
        { "step": "Blue 600", "hex": "#001AFF", "notes": "Equals Electric" },
        { "step": "Blue 1000", "hex": "#040038", "notes": "..." }
      ]
    },
    {
      "name": "Orange",
      "signature": "#F47A48",
      "deep": "#842C09",
      "text_safe_step": "color/orange/700",
      "text_safe_hex": "#A1502F",
      "description": "Secondary palette - full 12-step ramp available in design tokens"
    }
  ]
}
```

**Example:**
```python
import requests
response = requests.get('https://gamaleldientarek.github.io/azmx-brand/api/v1/palettes.json')
palettes = response.json()['palettes']
blue_palette = next(p for p in palettes if p['name'] == 'Blue')
ramp = {r['step']: r['hex'] for r in blue_palette['ramp']}
print(f"Blue 600: {ramp['Blue 600']}")  # #001AFF
```

---

### 4. Typography

**GET** `/typography.json`

Returns font families, weights, the type scale, and typographic rules. `tracking` is a number in px (negative values tighten).

**Response Structure:**
```json
{
  "version": "1.0.0",
  "description": "AZMX typography system - font families, weights, type scale, and usage rules",
  "families": [
    { "role": "Display / Titles", "family": "thmanyah serif display", "variable": "Display", "variable_id": "1:980", "notes": "..." },
    { "role": "Body / Information", "family": "Azm X Variable", "variable": "Body", "variable_id": "1:979", "notes": "..." }
  ],
  "weights": [ { "weight": "Regular", "variable_id": "1:975" } ],
  "type_scale": [
    { "role": "Cover hero display", "font": "thmanyah serif", "size": "168", "line_height": "156", "weight": "Regular", "tracking": -2, "case_style": "Mixed-case" }
  ],
  "rules": ["..."],
  "bilingual_note": "..."
}
```

---

### 5. Voice & Tone

**GET** `/voice.json`

Returns brand language, tone rules, the four voice dimensions, calibration examples, writing mechanics (the no-AI-tells rules), format rules, and platform-specific voice.

**Response Structure:**
```json
{
  "version": "1.0.0",
  "description": "...",
  "brand_language": { "tagline": "...", "philosophy": "...", "boilerplate": "..." },
  "voice_summary": "Confident, editorial, human, premium. ...",
  "tone_rules": [ { "number": "1", "heading": "Confident, not boastful.", "description": "..." } ],
  "dimensions": [ { "dimension": "Formality", "position": "Mid-Formal. ...", "we_are": "...", "we_are_not": "..." } ],
  "calibration_examples": [ { "dimension": "Formality", "wrong_formal": "...", "wrong_informal": "...", "azmx_voice": "..." } ],
  "purpose_modes": [ { "mode": "Inspirational — sharing the vision", "surfaces": "...", "goal": "...", "example": "..." } ],
  "writing_mechanics": ["Em-dashes as the default connector. ...", "..."],
  "universal_principles": [ { "principle": "Lead with value", "description": "..." } ],
  "format_rules": [ { "format": "Headlines and heroes", "rules": "..." } ],
  "platform_voice": [ { "platform": "LinkedIn", "voice": "...", "guidelines": "..." } ],
  "strategy_superseded": [ { "deck_says": "...", "azmx_voice": "..." } ],
  "pre_publish_checklist": [ { "number": "1", "heading": "On-brand?", "description": "..." } ],
  "quick_self_check": ["..."]
}
```

**Example:**
```javascript
const voice = await fetch('https://gamaleldientarek.github.io/azmx-brand/api/v1/voice.json')
  .then(res => res.json());
console.log('Voice dimensions:', voice.dimensions.map(d => d.dimension));
// ["Formality", "Technicality", "Attitude", "Purpose"]
```

---

### 6. Audience Personas

**GET** `/audiences.json`

Returns the 8 external personas (grouped by B2G / B2B / B2C motion) with pain points, verbatim core messages, and brand associations, plus internal audiences, external motions, and the five brands.

**Response Structure:**
```json
{
  "version": "1.0.0",
  "description": "...",
  "count": 8,
  "personas": [
    {
      "name": "Directors / Heads",
      "motion": "B2G",
      "brands": ["AZM X"],
      "pain_points": "...",
      "core_message": "..."
    }
  ],
  "internal_audiences": [ { "segment": "...", "needs": "...", "core_message": "..." } ],
  "external_motions": [ { "motion": "B2G", "brands": ["..."], "needs": "...", "core_message": "..." } ],
  "brands": [ { "name": "AZM X", "description": "...", "motions": ["B2G", "B2B", "B2C"] } ]
}
```

Personas: Directors / Heads, Leads (B2G); C-Suite, Product / UX Heads, Operations (B2B); Researchers, Designers, Industry Professionals (B2C).

**Example:**
```bash
curl -s https://gamaleldientarek.github.io/azmx-brand/api/v1/audiences.json | \
  jq '.personas[] | select(.motion == "B2G") | .name'
```

---

### 7. Content Prompts

**GET** `/prompts.json`

Returns the 15 content generation prompt templates with their full template text.

**Response Structure:**
```json
{
  "version": "1.0.0",
  "description": "...",
  "count": 15,
  "prompts": [
    {
      "id": "blog-seo-brief",
      "number": 1,
      "title": "The Blog SEO Brief Prompt",
      "description": "...",
      "deck_page": "..." ,
      "template": "Your Role: ...",
      "notes": null
    }
  ]
}
```

`deck_page` and `notes` are `null` when the source document has none.

---

### 8. Brand Images

**GET** `/images.json`

Returns the catalogued library of 240 brand images, each with three concept tags. Image files are in the repository under `assets/images/<prefix>/` (see Pattern 4).

**Response Structure:**
```json
{
  "version": "1.0.0",
  "description": "AZMX brand images with conceptual tags",
  "count": 240,
  "images": [
    { "filename": "blue-001.jpg", "tags": ["structure", "scale", "foundation"] }
  ]
}
```

---

## Versioning

The API follows semantic versioning principles:

- **Major version** (v1, v2): Breaking changes to response structure
- **Minor updates**: New fields added (backward compatible)
- **Patch updates**: Data updates without schema changes

The API version is stamped as `version` in every endpoint (and `$meta.version` in the index); the Figma export version of the token source is exposed separately as `source_version` in `/tokens.json`. `$meta.updated` in the index is the build date.

### Version in URL Path

Always include the version in your request URL:
```
✅ https://gamaleldientarek.github.io/azmx-brand/api/v1/tokens.json
❌ https://gamaleldientarek.github.io/azmx-brand/api/tokens.json
```

### Backward Compatibility

We guarantee backward compatibility within a major version:
- Existing fields will not be removed or renamed
- Response structure will remain stable
- New optional fields may be added

### Migration Guide

When v2 is released, this documentation will include a migration guide detailing breaking changes.

---

## Best Practices

### Caching

GitHub Pages is CDN-backed. Recommended cache strategy:

```javascript
// Cache for 1 hour in production
const CACHE_TTL = 3600; // seconds

async function fetchWithCache(url) {
  const cached = localStorage.getItem(url);
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < CACHE_TTL * 1000) {
      return data;
    }
  }

  const data = await fetch(url).then(res => res.json());
  localStorage.setItem(url, JSON.stringify({ data, timestamp: Date.now() }));
  return data;
}
```

### Error Handling

Always handle network errors and invalid JSON:

```python
import requests
from requests.exceptions import RequestException

def fetch_brand_data(endpoint):
    url = f"https://gamaleldientarek.github.io/azmx-brand/api/v1/{endpoint}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Error fetching {endpoint}: {e}")
        return None
```

### CORS

GitHub Pages sends `Access-Control-Allow-Origin: *`, so browser-based requests work without a proxy:

```javascript
// Works directly in browser
fetch('https://gamaleldientarek.github.io/azmx-brand/api/v1/palettes.json')
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## Rate Limits

- **Authentication:** None required
- **Rate Limiting:** Subject to GitHub Pages CDN limits
- **Recommended:** Cache responses for at least 1 hour
- **Abuse Prevention:** Excessive requests may be throttled

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:

**JSON:** `https://gamaleldientarek.github.io/azmx-brand/api/v1/openapi.json`  

Interactive documentation: https://gamaleldientarek.github.io/azmx-brand/api-docs/

---

## Examples

### Figma Plugin Integration

```javascript
// Fetch AZMX tokens and sync the Light-mode semantic values to Figma variables
async function syncAZMXTokens() {
  const tokens = await fetch('https://gamaleldientarek.github.io/azmx-brand/api/v1/tokens.json')
    .then(res => res.json());

  const semantic = tokens.collections.find(c => c.name === '2. Semantic');
  const light = semantic.modes.indexOf('Light');
  const dark = semantic.modes.indexOf('Dark');

  for (const [name, values] of Object.entries(semantic.tokens)) {
    const lightValue = values[light]; // e.g. "@color/base/white" (alias) or a hex
    const darkValue = values[dark];

    // Resolve @aliases against '1. Primitives' / '1b. Palette', then create the variable:
    // figma.variables.createVariable(name, collection, 'COLOR');
  }
}
```

### Content Generation with Voice Guidelines

```python
import requests
import openai

BASE_URL = 'https://gamaleldientarek.github.io/azmx-brand/api/v1'

# Fetch AZMX voice guidelines
voice = requests.get(f'{BASE_URL}/voice.json').json()
audiences = requests.get(f'{BASE_URL}/audiences.json').json()

# Find target persona
target = next(p for p in audiences['personas'] if p['name'] == 'C-Suite')

# Generate on-brand content
system_prompt = f"""
You are writing for AZMX. {voice['voice_summary']}

Voice dimensions:
{chr(10).join(f"- {d['dimension']}: {d['position']}" for d in voice['dimensions'])}

Never: {'; '.join(voice['writing_mechanics'])}

Target audience: {target['name']}
Pain points: {target['pain_points']}
Core message: {target['core_message']}
"""

response = openai.chat.completions.create(
  model="gpt-4o",
  messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "Write a 2-paragraph intro for our new case study"}
  ]
)
```

### Design System Validation

```javascript
// Validate that all colors in a design use approved AZMX primitives
async function validateColors(designColors) {
  const tokens = await fetch('https://gamaleldientarek.github.io/azmx-brand/api/v1/tokens.json')
    .then(res => res.json());

  const primitives = tokens.collections.find(c => c.name === '1. Primitives').tokens;
  const approvedColors = Object.entries(primitives)
    .filter(([name, value]) => name.startsWith('color/') && typeof value === 'string' && value.startsWith('#'))
    .map(([, value]) => value.toUpperCase());

  const violations = designColors.filter(c =>
    !approvedColors.includes(c.toUpperCase())
  );

  if (violations.length > 0) {
    console.warn('Off-brand colors detected:', violations);
  }
}
```

---

## Building the API

```bash
bash scripts/build-api.sh          # extract -> OpenAPI -> docs -> validate
python -m pytest tests/test_brand_api.py -q   # staleness guard + ground-truth checks
```

`tests/test_brand_api.py` regenerates the endpoints into a temporary directory and fails if the committed `api/v1/*.json` differ, so the reference documents and the API cannot drift apart.

---

## Support

- **Documentation:** https://gamaleldientarek.github.io/azmx-brand/api-docs/
- **Issues:** https://github.com/Gamaleldientarek/azmx-brand/issues
- **Repository:** https://github.com/Gamaleldientarek/azmx-brand

---

## License

Proprietary - AZMX internal use and authorized partners only.
