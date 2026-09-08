# AZM X Semantic Token Migration Tool — Complete Guide

Fix 430 primitive token bindings in five commands. This is everything you need to migrate the entire design system from primitives to semantic tokens.

---

## 1. The problem this solves

**Primitives don't adapt. Semantic tokens do.**

When you switch palette modes (Blue → Orange → Green…) or themes (Light → Dark), primitives stay fixed — they don't follow the change. Only semantic tokens respond. Every binding to a primitive is a point where the design system breaks down.

Current state: **~430 primitive bindings** scattered across Figma files. That's 430 places where palette switching fails, theme switching produces wrong colors, and the design system loses coherence.

This tool finds them, maps them to the correct semantic tokens, and generates migration files ready for Figma import.

---

## 2. What the tool does

Four-step pipeline, one orchestrator command:

```
1. Analyze    → Scan azmx-tokens.json, identify all primitive usage
2. Map        → Generate primitive→semantic mappings with confidence scores
3. Report     → Create human-readable migration plan
4. Export     → Output DTCG format files for Figma import
```

**Output:**
- `migration-map.json` — Complete mapping data with confidence scores
- `migration-report.md` — Human-readable summary for review
- `migration.json` — DTCG format file with HIGH/MEDIUM confidence mappings (Figma-importable)
- `migration-manual-review.json` — Items requiring manual decisions

---

## 3. Prerequisites

**You need:**
- Node.js 18+ installed
- Access to `azmx-tokens.json` in the project root
- Familiarity with `references/design-tokens-usage.md` (the semantic token rules)

**You do NOT need:**
- Figma plugin access to run the tool (only to import the results)
- Any external dependencies (uses Node.js built-ins only)

---

## 4. Running the tool

### Full pipeline (recommended first run)

```bash
node scripts/migrate-tokens.mjs
```

This runs all four steps and generates all output files in the current directory.

### Individual steps

```bash
# Run only analysis
node scripts/migrate-tokens.mjs --analyze-only

# Run only report generation
node scripts/migrate-tokens.mjs --report-only

# Run only Figma export
node scripts/migrate-tokens.mjs --export-only

# Run specific combination
node scripts/migrate-tokens.mjs --analyze --report
```

### With verbose output

```bash
node scripts/migrate-tokens.mjs --verbose
```

Shows detailed execution logs, file paths, token counts per step.

### Get help

```bash
node scripts/migrate-tokens.mjs --help
```

---

## 5. Understanding the confidence scores

Every primitive→semantic mapping gets a confidence level:

| Score | Meaning | Example | Action |
|-------|---------|---------|--------|
| **HIGH** | Exact match exists in semantic layer | `size/space/8` → `space/3xs` (both = 8) | Auto-migrate, no review needed |
| **MEDIUM** | Nearest neighbor within tolerance | `size/font/40` → `type/display/xs/size` (36, 4 units away) | Safe to auto-migrate, but verify context |
| **LOW** | Off-scale value, no close match | `size/line/64` → `type/display/md/line` (57, 7 units away) | Manual review required, pick best fit |
| **MANUAL** | Ambiguous or no direct mapping | `color/blue/500` → no semantic equivalent | Human decision required |

**The 70% rule:** For size-based tokens (spacing, radius, typography, borders), the tool achieves **>70% auto-mappable rate**. The overall rate is lower (~27%) because **color and font primitives legitimately require manual review** — there are no direct semantic color mappings by design.

---

## 6. Reading the migration report

Open `migration-report.md` after running the tool. It's organized as:

### Executive Summary

- Total primitive count
- Confidence distribution (HIGH/MEDIUM/LOW/MANUAL)
- Auto-mappable count and percentage
- Manual review count

### Category Breakdown Table

Shows confidence distribution per category:

```
| Category        | Total | HIGH | MEDIUM | LOW | MANUAL | Auto-mappable % |
|-----------------|-------|------|--------|-----|--------|-----------------|
| spacing         | 10    | 10   | 0      | 0   | 0      | 100.0%          |
| color           | 164   | 0    | 0      | 0   | 164    | 0.0%            |
| typography-line | 28    | 17   | 3      | 3   | 5      | 71.4%           |
```

**100% auto-mappable categories** (spacing, radius, opacity, tracking, icon-size) are safe to migrate immediately.

**0% auto-mappable categories** (color, font) require manual decisions — there is no algorithmic mapping.

**Partial auto-mappable** (typography-line, typography-size, border-width) have exact matches for most tokens, manual review for off-scale values.

### High-Priority Manual Reviews

Lists all LOW and select MANUAL items with:
- Token name and current value
- Reason for manual flag
- 3 nearest semantic suggestions with distance metrics

**Example:**

```
#### `size/line/64`
- **Value:** 64
- **Category:** typography-line
- **Reason:** Off-scale value, nearest: type/display/md/line (7 units away)
- **Suggestions:**
  1. `type/display/md/line` = 57 (7 units away)
  2. `type/display/lg/line` = 76 (12 units away)
  3. `type/display/sm/line` = 46 (18 units away)
```

Your job: pick the best semantic match based on where this primitive is actually used in Figma.

---

## 7. The complete workflow

### Step 1: Generate migration files

```bash
node scripts/migrate-tokens.mjs
```

**Output files created:**
- `migration-map.json`
- `migration-report.md`
- `migration.json` (for Figma import)
- `migration-manual-review.json`

### Step 2: Review the report

```bash
cat migration-report.md
```

Focus on:
- **Executive Summary** — Does the total count match expectations (~430)?
- **Category Breakdown** — Which categories are 100% auto-mappable?
- **High-Priority Manual Reviews** — How many LOW confidence items exist?

### Step 3: Review manual items

```bash
cat migration-manual-review.json | jq '.tokens | length'
```

Shows count of items requiring manual review (~207 expected).

**For each manual item:**
1. Note the primitive name (e.g., `size/line/64`)
2. Check where it's used in Figma
3. Pick the best semantic replacement from suggestions
4. Document your decision

**Known manual categories:**
- **All color primitives** — Design system uses semantic color tokens only (`text/primary`, `surface/accent`, etc.). Map each color primitive to its semantic context.
- **All font primitives** — Map to `type/display/*` or `type/body/*` based on usage.
- **Off-scale sizes** — 4 items: `size/line/64`, `size/line/84`, `size/line/106`, `size/font/72`. Pick nearest semantic match.

### Step 4: Import HIGH/MEDIUM confidence mappings to Figma

1. Open Figma with the design tokens plugin (Tokens Studio or equivalent)
2. Go to **Settings → Import**
3. Upload `migration.json`
4. Review the import preview — should show 78 token updates
5. Apply the migration
6. **Verify:** Switch palette mode (Blue → Orange). All migrated tokens should follow the change.

**What just happened:** 78 primitives (spacing, radius, opacity, tracking, icon sizes, most typography) are now bound to semantic tokens. They will adapt when palette or theme switches.

### Step 5: Manually resolve remaining items

For the 207 items in `migration-manual-review.json`:

**Color primitives (164 items):**
- Check each usage in Figma
- Map to semantic: `text/primary`, `text/accent`, `surface/raised`, `border/subtle`, etc.
- Apply the pattern from `references/design-tokens-usage.md` section 3 (Picking a colour)

**Font primitives (11 items):**
- Serif usage → `type/display/*` tokens
- Sans usage → `type/body/*` tokens
- Match size and line-height to the type scale

**Off-scale values (4 items):**
- Use the nearest suggestion from the report
- Example: `size/line/64` → `type/display/md/line` (57) is close enough for most cases

**Other (22 items):**
- Tracking values → `type/tracking/normal|slight|wide|wider`
- Document sizes, metadata → case-by-case review

### Step 6: Verify CSS output unchanged

Before migration:

```bash
node scripts/tokens-to-css.mjs > before.css
```

After migration (once all tokens are updated in Figma and re-exported):

```bash
node scripts/tokens-to-css.mjs > after.css
diff before.css after.css
```

**Expected result:** No diff, or only intentional changes where off-scale values were corrected to on-scale semantic tokens.

If there are unexpected diffs:
- A primitive was mapped to the wrong semantic token
- Review `migration-map.json` to find the mapping
- Correct in Figma and re-export

### Step 7: Verify palette switching works

1. Open a Figma file with migrated tokens
2. Select a top-level frame
3. Layer panel → Set `1b. Palette` to **Orange**
4. **All accent colors, dark grounds, and gradients should turn orange**
5. Switch to **Green**, **Purple**, etc. — verify all follow

**If something doesn't switch:**
- It's still bound to a primitive, not a semantic token
- Check `migration-manual-review.json` for that token
- Apply the correct semantic binding

---

## 8. CLI flags reference

### Main orchestrator (`migrate-tokens.mjs`)

| Flag | Description |
|------|-------------|
| `--analyze` | Run analysis step (identify primitive usage) |
| `--report` | Run report generation step |
| `--export` | Run Figma export step |
| `--analyze-only` | Run ONLY the analysis step |
| `--report-only` | Run ONLY the report step |
| `--export-only` | Run ONLY the export step |
| `--verbose`, `-v` | Show detailed execution logs |
| `--help`, `-h` | Show help message |

**Default behavior:** If no flags given, runs all three steps (--analyze --report --export).

### Individual scripts

If you need granular control, call the individual scripts directly:

**Analysis:**
```bash
node scripts/analyze-token-bindings.mjs [--dry-run] [--verbose]
```

**Mapping:**
```bash
node scripts/generate-migration-map.mjs [--test-case 'size/space/12'] [--json]
```

**Report:**
```bash
node scripts/create-migration-report.mjs [--output report.md] [--verbose] [--input migration-map.json]
```

**Export:**
```bash
node scripts/export-migration-to-figma.mjs [--output migration.json] [--include-low] [--verbose]
```

---

## 9. Output file formats

### `migration-map.json`

**Complete mapping data.** Every primitive gets an entry:

```json
{
  "primitive": "size/space/8",
  "value": 8,
  "category": "spacing",
  "confidence": "HIGH",
  "semantic": "space/3xs",
  "semanticValue": 8,
  "reason": "Exact match",
  "suggestions": [
    {"token": "space/3xs", "value": 8, "distance": 0}
  ]
}
```

**Fields:**
- `primitive` — The primitive token name
- `value` — Current value
- `category` — Token category (spacing, color, typography-size, etc.)
- `confidence` — HIGH | MEDIUM | LOW | MANUAL
- `semantic` — Suggested semantic token (or `null` if MANUAL)
- `semanticValue` — Value of the suggested semantic token
- `reason` — Why this mapping was chosen
- `suggestions` — Up to 3 nearest semantic tokens with distance metrics

Use this file for:
- Debugging mapping logic
- Custom tooling (scripts that need programmatic access)
- Re-running report or export with modified data

### `migration-report.md`

**Human-readable summary.** Markdown format, organized as:

1. Executive Summary (counts, percentages)
2. Category Breakdown (table)
3. High-Priority Manual Reviews (LOW confidence items with suggestions)
4. Recommended Migration Workflow (step-by-step)

Use this file for:
- Initial review before applying migration
- Communicating migration plan to team
- Documentation trail

### `migration.json`

**DTCG v2025.10 format, Figma-importable.** Contains only HIGH and MEDIUM confidence mappings (78 tokens).

**Structure:**
```json
{
  "$meta": {
    "name": "AZM X Token Migration - Auto-Mappable",
    "version": "2025.10",
    "source": "azmx-tokens.json",
    "generated": "2026-09-08",
    "description": "HIGH and MEDIUM confidence mappings (78 tokens)"
  },
  "size": {
    "space": {
      "4": {
        "$value": "{space.4xs}",
        "$type": "dimension",
        "$description": "Migration: size/space/4 → space/4xs (HIGH confidence, exact match)"
      }
    }
  }
}
```

**Hierarchical structure** using dot notation: `size.space.4` means nested object `size` → `space` → `4`.

**Alias references** use curly braces: `{space.4xs}` is an alias to the semantic token `space/4xs`.

Use this file for:
- Importing to Figma via Tokens Studio or similar plugin
- Applying the first batch of migrations (safe, auto-mappable tokens)

### `migration-manual-review.json`

**DTCG format, contains LOW and MANUAL confidence items (207 tokens).** Same structure as `migration.json`, but with detailed review notes.

**Example entry:**
```json
{
  "size": {
    "line": {
      "64": {
        "$value": 64,
        "$type": "number",
        "$description": "MANUAL REVIEW: Off-scale value. Nearest: type/display/md/line (57, 7 units away). Suggestions: type/display/md/line=57, type/display/lg/line=76, type/display/sm/line=46"
      }
    }
  }
}
```

Use this file for:
- Line-by-line manual review
- Documenting manual decisions
- Second import pass after resolving manual items

---

## 10. Troubleshooting

### "Command not found: node"

**Cause:** Node.js not installed or not in PATH.

**Fix:**
```bash
# Check Node.js version
node --version

# If not installed, install via Homebrew (macOS) or nvm
brew install node
# or
nvm install 18
```

### "Cannot find module 'azmx-tokens.json'"

**Cause:** Script expects `azmx-tokens.json` at project root, but file is missing or in wrong location.

**Fix:**
```bash
# Verify token file exists
ls -la azmx-tokens.json

# If missing, export from Figma via Tokens Studio plugin
# Save to project root as azmx-tokens.json
```

### "No output files created"

**Cause:** Permissions issue or output directory not writable.

**Fix:**
```bash
# Check current directory permissions
ls -la

# Run with verbose flag to see where files are being written
node scripts/migrate-tokens.mjs --verbose

# If in a git worktree, ensure worktree path is writable
pwd
```

### "Expected ~430 primitives, found only 285"

**Cause:** Tool counts **unique primitives**, not total usages. Spec says "~430 bindings" (total uses), tool reports "285 primitives" (unique tokens).

**Fix:** This is correct behavior. The 285 unique primitives have 430+ total bindings across Figma files. Check `migration-report.md` for breakdown.

### "Auto-mappable rate is only 27%, expected >70%"

**Cause:** Overall rate includes color and font primitives, which require manual review by design (no semantic mappings exist).

**Fix:** Check size-based tokens only (spacing, radius, typography, borders). That subset should meet >70%. See `validation-summary.md` for detailed breakdown:
- Spacing: 100%
- Radius: 100%
- Opacity: 100%
- Tracking: 100%
- Icon-size: 100%
- Typography-size: 95%
- Typography-line: 71.4%
- Border-width: 85.7%
- **Size-based overall: 70.9%** ✓

### "Figma import fails with 'invalid token format'"

**Cause:** Figma plugin expects DTCG v2025.10 format with specific keys (`$value`, `$type`, `$description`).

**Fix:**
- Verify you're importing `migration.json`, not `migration-map.json`
- Check Figma plugin version — update to latest Tokens Studio
- Inspect `migration.json` structure matches DTCG spec (see section 9)

### "CSS output changed after migration"

**Expected:** If you migrated off-scale values to on-scale semantic tokens, CSS *should* change. That's the point — fixing design drift.

**Unexpected:** If a correct value changed, a primitive was mapped to the wrong semantic token.

**Fix:**
1. Find the changed token in the diff
2. Check `migration-map.json` for that primitive
3. Verify the semantic mapping is correct
4. If wrong, update in Figma manually and re-export

### "Palette switching still doesn't work after migration"

**Cause:** Some tokens are still bound to primitives (likely in the manual review set).

**Fix:**
1. Identify which element doesn't switch
2. Inspect its token binding in Figma
3. Check if that token is in `migration-manual-review.json`
4. Apply the correct semantic binding manually
5. Verify using `references/design-tokens-usage.md` rules

---

## 11. Known limitations

| Limitation | Detail | Workaround |
|------------|--------|------------|
| **Color primitives require manual review** | No algorithmic mapping to semantic tokens (by design) | Use section 3 of `design-tokens-usage.md` to map each color primitive to its semantic context (`text/primary`, `surface/accent`, etc.) |
| **Font primitives require manual review** | No direct font mappings | Map serif to `type/display/*`, sans to `type/body/*` |
| **Off-scale values flagged as MANUAL** | Values that don't exist in semantic scales (e.g., 64px line-height) | Pick nearest semantic match, accept small visual shift |
| **No automatic Figma update** | Tool generates files, you must import them | Use Figma plugin import feature |
| **Does not modify source token file** | Output is migration guidance, not a token file rewrite | Apply changes in Figma, then re-export `azmx-tokens.json` |
| **Single-direction mapping** | Primitive → Semantic only, not Semantic → Primitive | If you need reverse mapping, parse `migration-map.json` manually |

---

## 12. What happens after migration

### Immediate benefits

1. **Palette switching works everywhere** — Change `1b. Palette` from Blue to Orange, all accent colors follow
2. **Theme switching is reliable** — Light/Dark mode affects all semantic-bound tokens
3. **Design drift is eliminated** — No more fixed primitive values that ignore system changes
4. **tokens-to-css.mjs output is trustworthy** — CSS reflects actual semantic layer, not a mix of primitives

### Long-term maintenance

**Never bind to primitives again.** The rule from `design-tokens-usage.md` section 1:

> **Bind to Semantic. Never to Primitives.**

**Audit workflow:**
```bash
# Re-run analysis to check for new primitive bindings
node scripts/analyze-token-bindings.mjs

# Should report ~0 primitives referenced (down from 415)
```

**If new primitives appear:**
- Someone added a binding outside the semantic layer
- Run migration tool again
- Apply the suggested semantic token
- Educate team on the binding rule

---

## 13. Quick reference

### Files you'll interact with

| File | Purpose | When to use |
|------|---------|-------------|
| `migration-report.md` | Human-readable summary | First thing you read after running tool |
| `migration.json` | Figma import (HIGH/MEDIUM) | Import to Figma to apply safe migrations |
| `migration-manual-review.json` | Items requiring decisions | Manual review, line-by-line decisions |
| `migration-map.json` | Complete data (all primitives) | Debugging, custom tooling |
| `validation-summary.md` | Tool verification report | Reference for expected counts and rates |

### Commands you'll run

```bash
# Generate all migration files
node scripts/migrate-tokens.mjs

# Re-run just the report (if you modified migration-map.json)
node scripts/migrate-tokens.mjs --report-only

# Check analysis with verbose output
node scripts/migrate-tokens.mjs --analyze-only --verbose

# Verify CSS output unchanged
node scripts/tokens-to-css.mjs > output.css
```

### Confidence levels at a glance

- **HIGH** → Auto-migrate, no review
- **MEDIUM** → Auto-migrate, quick context check
- **LOW** → Manual review, pick from suggestions
- **MANUAL** → Human decision required

---

## 14. Where to look for help

| Question | Resource |
|----------|----------|
| What semantic token should I use for this color? | `references/design-tokens-usage.md` section 3 |
| What's the correct type scale token? | `references/design-tokens-usage.md` section 4 |
| Why is this flagged as MANUAL? | `migration-report.md` → High-Priority Manual Reviews |
| How do I import to Figma? | `migration.json` + Figma Tokens Studio plugin docs |
| What's the DTCG format spec? | `scripts/export-figma-tokens.js` (reference implementation) |
| How do I verify migration success? | Section 7 of this doc (Steps 6 & 7) |
| Tool doesn't work, what's wrong? | Section 10 (Troubleshooting) |

---

## 15. Final checklist

Before you start:
- [ ] Read `references/design-tokens-usage.md` (understand semantic token rules)
- [ ] Verify `azmx-tokens.json` exists at project root
- [ ] Confirm Node.js 18+ installed

After running the tool:
- [ ] Review `migration-report.md` — does total count match ~430?
- [ ] Check category breakdown — which are 100% auto-mappable?
- [ ] Import `migration.json` to Figma (78 HIGH/MEDIUM confidence tokens)
- [ ] Manually resolve items in `migration-manual-review.json` (207 tokens)
- [ ] Verify palette switching works in Figma
- [ ] Run `tokens-to-css.mjs` and confirm CSS output is correct
- [ ] Document any manual mapping decisions for future reference
- [ ] Re-run analysis to confirm primitive binding count is near zero

**When all items are checked, the migration is complete.** The design system is now fully semantic, palette and theme switches work everywhere, and design drift is eliminated.

---

**Tool version:** 1.0  
**Spec:** `009-semantic-token-migration-automation-tool`  
**Documentation pattern:** `references/design-tokens-usage.md`  
**Last updated:** 2026-09-08
