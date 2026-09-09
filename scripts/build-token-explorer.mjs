#!/usr/bin/env node
/*
 * AZM X Token Explorer Generator
 *
 *   node scripts/build-token-explorer.mjs --dry-run
 *   node scripts/build-token-explorer.mjs > docs/token-explorer.html
 *
 * Reads assets/tokens/azmx-tokens.json and generates an interactive HTML explorer.
 * The explorer provides visual browsing, search, filtering by category, and one-click
 * copy for token names or resolved values.
 *
 * Usage:
 *   --dry-run    Parse tokens and output statistics without generating HTML
 *   --help       Show this help message
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const TOKEN_PATH = join(HERE, '..', 'assets', 'tokens', 'azmx-tokens.json');

const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
const showHelp = args.includes('--help');
const testCategorization = args.includes('--test-categorization');
const testResolution = args.includes('--test-resolution');

// ---- help ----
if (showHelp) {
  console.log(`
AZM X Token Explorer Generator

Usage:
  node scripts/build-token-explorer.mjs [options]

Options:
  --dry-run              Parse tokens and output statistics without generating HTML
  --test-categorization  Test token categorization and display breakdown by type
  --test-resolution      Test token alias resolution for all palette/theme combinations
  --help                 Show this help message

Output:
  By default, generates interactive HTML explorer to stdout
  Redirect to file: > docs/token-explorer.html
`);
  process.exit(0);
}

// ---- read and parse tokens ----
let DATA;
try {
  DATA = JSON.parse(readFileSync(TOKEN_PATH, 'utf8'));
} catch (err) {
  console.error(`Error reading tokens file: ${err.message}`);
  process.exit(1);
}

// ---- extract sections ----
const sections = {};
const sectionOrder = [];

for (const [key, value] of Object.entries(DATA)) {
  if (key === '$meta') continue;
  if (typeof value === 'object' && value !== null && 'tokens' in value) {
    sections[key] = value;
    sectionOrder.push(key);
  }
}

// ---- alias resolution ----
// Extract palettes and themes for mode combinations
const PALETTES = DATA['1b. Palette']?.modes?.map(m => m.toLowerCase()) || [];
const THEMES = DATA['2. Semantic']?.modes?.map(m => m.toLowerCase()) || [];

// Token section references for resolution
const prim = DATA['1. Primitives']?.tokens || {};
const pal  = DATA['1b. Palette']?.tokens || {};
const sem  = DATA['2. Semantic']?.tokens || {};
const comp = DATA['3. Component']?.tokens || {};
const canv = DATA['4. Canvas']?.tokens || {};

/**
 * Resolve a token reference recursively.
 * Every token is either a literal value, or "@other/token" reference.
 * Palette tokens hold one value per palette; Semantic tokens one per theme.
 * Resolution therefore needs to know which palette and which theme it is resolving for.
 *
 * @param {string|number} ref - Token reference or literal value
 * @param {number} paletteIdx - Index of the current palette mode
 * @param {number} themeIdx - Index of the current theme mode
 * @param {number} depth - Recursion depth to detect circular references
 * @returns {string|number} Resolved token value
 */
function resolve(ref, paletteIdx, themeIdx, depth = 0) {
  if (depth > 12) throw new Error('alias loop at ' + ref);
  if (typeof ref !== 'string' || !ref.startsWith('@')) return ref;
  const name = ref.slice(1);

  if (name in prim) return prim[name];
  if (name in pal)  return resolve(pal[name][paletteIdx], paletteIdx, themeIdx, depth + 1);
  if (name in sem)  return resolve(sem[name][themeIdx],   paletteIdx, themeIdx, depth + 1);
  if (name in comp) return resolve(comp[name],            paletteIdx, themeIdx, depth + 1);
  if (name in canv) return resolve(canv[name],            paletteIdx, themeIdx, depth + 1);
  throw new Error('unknown token: ' + name);
}

/**
 * Resolve all semantic, component, and canvas tokens for one palette/theme combination.
 *
 * @param {number} paletteIdx - Index of the palette mode
 * @param {number} themeIdx - Index of the theme mode
 * @returns {Object} All resolved tokens for this combination
 */
function resolveAll(paletteIdx, themeIdx) {
  const out = {};
  for (const n of Object.keys(sem))  out[n] = resolve(sem[n][themeIdx], paletteIdx, themeIdx);
  for (const n of Object.keys(comp)) out[n] = resolve(comp[n],          paletteIdx, themeIdx);
  for (const n of Object.keys(canv)) out[n] = resolve(canv[n],          paletteIdx, themeIdx);
  return out;
}

// ---- count tokens ----
function countTokens() {
  let totalTokens = 0;
  let totalSections = 0;
  const breakdown = {};

  for (const [name, section] of Object.entries(sections)) {
    const count = Object.keys(section.tokens).length;
    totalTokens += count;
    totalSections += 1;
    breakdown[name] = {
      count,
      modes: section.modes || ['Mode 1'],
      declaredCount: section.count
    };
  }

  return { totalTokens, totalSections, breakdown };
}

// ---- categorize tokens by type ----
function categorizeTokens() {
  const categories = {
    'Color': [],
    'Spacing': [],
    'Typography': [],
    'Border': [],
    'Effects': [],
    'Layout': []
  };

  const uncategorized = [];

  for (const [sectionName, section] of Object.entries(sections)) {
    for (const [tokenName, tokenValue] of Object.entries(section.tokens)) {
      const token = {
        name: tokenName,
        value: tokenValue,
        section: sectionName,
        modes: section.modes || ['Mode 1']
      };

      // Determine category based on token name patterns
      // Order matters: the specific numeric/typography prefixes (type/, size/, font/,
      // icon/size/) must win over the broad colour heuristics such as includes('/body').
      if (sectionName === 'RTL') {
        categories['Layout'].push(token);
      } else if (isTypographyToken(tokenName)) {
        categories['Typography'].push(token);
      } else if (isSpacingToken(tokenName)) {
        categories['Spacing'].push(token);
      } else if (isBorderToken(tokenName) && !isColorToken(tokenName)) {
        categories['Border'].push(token);
      } else if (isEffectsToken(tokenName)) {
        categories['Effects'].push(token);
      } else if (isColorToken(tokenName)) {
        categories['Color'].push(token);
      } else if (isBorderToken(tokenName)) {
        categories['Border'].push(token);
      } else if (isEffectsToken(tokenName)) {
        categories['Effects'].push(token);
      } else {
        uncategorized.push(token);
      }
    }
  }

  return { categories, uncategorized };
}

// ---- category detection helpers ----
function isColorToken(name) {
  // Direct color tokens
  if (name.startsWith('color/') ||
      name.startsWith('brand/') ||
      name.startsWith('accent/') ||
      name.startsWith('surface/') ||
      name.startsWith('text/') ||
      name.startsWith('icon/') ||
      name.startsWith('stroke/') ||
      name.startsWith('fill/') ||
      name.startsWith('status/') ||
      name.startsWith('action/') ||
      name.startsWith('overlay/') ||
      name.startsWith('gradient/') ||
      name.startsWith('interactive/') ||
      name.startsWith('state/') ||
      name.startsWith('heat/') ||
      name.startsWith('bg/') ||
      name.startsWith('logo/fill/')) {
    return true;
  }

  // Component tokens that end with color-related properties
  if (name.includes('/surface') ||
      name.includes('/mark') ||
      name.includes('/fill') ||
      name.includes('/track') ||
      name.includes('/eyebrow') ||
      name.includes('/title') ||
      name.includes('/lead') ||
      name.includes('/body') ||
      name.includes('/tags') ||
      name.includes('/logo') ||
      name.includes('/rule') ||
      name.includes('/page-number') ||
      name.includes('/mockup') ||
      name.includes('/frame') ||
      name.includes('/label') ||
      name.includes('/value')) {
    return true;
  }

  return false;
}

function isSpacingToken(name) {
  if (name.startsWith('size/space/') ||
      name.startsWith('size/icon/') ||
      name.startsWith('icon/size/') ||
      name.startsWith('size/doc/') ||
      name.startsWith('space/') ||
      name.startsWith('padding/') ||
      name.startsWith('margin/') ||
      name.startsWith('gap/') ||
      name.startsWith('slide/') ||
      name.startsWith('logo/clear-space')) {
    return true;
  }

  // Component tokens that end with spacing properties
  if (name.includes('/padding') ||
      name.includes('/margin') ||
      name.includes('/gap') ||
      name.includes('/height') ||
      name.includes('/width')) {
    return true;
  }

  return false;
}

function isTypographyToken(name) {
  return name.startsWith('size/font/') ||
         name.startsWith('size/line/') ||
         name.startsWith('font/family/') ||
         name.startsWith('font/weight/') ||
         name.startsWith('font/') ||
         name.startsWith('size/tracking/') ||
         name.startsWith('typography/') ||
         name.startsWith('type/') ||
         name.startsWith('weight/') ||
         name.startsWith('text/size') ||
         name.startsWith('text/weight') ||
         name.startsWith('text/line');
}

function isBorderToken(name) {
  if (name.startsWith('size/radius/') ||
      name.startsWith('size/border/') ||
      name.startsWith('border/') ||
      name.startsWith('border-width/') ||
      name.startsWith('radius/') ||
      name.startsWith('outline/')) {
    return true;
  }

  // Component tokens that end with border properties
  if (name.includes('/border') ||
      name.includes('/radius')) {
    return true;
  }

  return false;
}

function isEffectsToken(name) {
  return name.startsWith('size/opacity/') ||
         name.startsWith('opacity/') ||
         name.startsWith('shadow/') ||
         name.startsWith('blur/') ||
         name.startsWith('elevation/') ||
         name.startsWith('effect/');
}

// ---- HTML escape helper ----
function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ---- render color token ----
function renderColorToken(token, paletteIdx = 0, themeIdx = 0) {
  let value = token.value;

  // Resolve if it's an array (multi-mode token)
  if (Array.isArray(value)) {
    value = token.section === '1b. Palette'
      ? resolve(value[paletteIdx], paletteIdx, themeIdx)
      : resolve(value[themeIdx], paletteIdx, themeIdx);
  } else if (typeof value === 'string' && value.startsWith('@')) {
    value = resolve(value, paletteIdx, themeIdx);
  }

  const displayValue = String(value).toUpperCase();
  const isHex = /^#[0-9A-F]{6}$/i.test(displayValue);

  // Encode token data for detail view
  const tokenData = JSON.stringify({
    name: token.name,
    section: token.section,
    type: 'Color',
    rawValue: token.value
  });

  return `<div class="token-card" data-token="${esc(tokenData)}">
  <div class="token-preview color-preview">
    <div class="color-swatch" style="background:${esc(displayValue)}"></div>
  </div>
  <div class="token-info">
    <div class="token-name">${esc(token.name)}</div>
    <div class="token-value">${esc(displayValue)}</div>
  </div>
  <button class="copy-btn" data-value="${esc(displayValue)}" aria-label="Copy ${esc(displayValue)}">
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="5.5" y="5.5" width="8" height="8" rx="1"/>
      <path d="M10.5 5.5v-2a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2"/>
    </svg>
  </button>
</div>`;
}

// ---- render typography token ----
function renderTypographyToken(token, paletteIdx = 0, themeIdx = 0) {
  let value = token.value;

  // Resolve if it's an array (multi-mode token)
  if (Array.isArray(value)) {
    value = token.section === '1b. Palette'
      ? resolve(value[paletteIdx], paletteIdx, themeIdx)
      : resolve(value[themeIdx], paletteIdx, themeIdx);
  } else if (typeof value === 'string' && value.startsWith('@')) {
    value = resolve(value, paletteIdx, themeIdx);
  }

  const displayValue = String(value);
  const isFontSize = token.name.includes('font') || token.name.includes('size');
  const isFontWeight = token.name.includes('weight');
  const isFontFamily = token.name.includes('family');
  const isLineHeight = token.name.includes('line');

  // Create a sample preview
  let previewStyle = '';
  let previewText = 'Aa';

  if (isFontSize) {
    previewStyle = `font-size:${displayValue}`;
    previewText = 'Ag';
  } else if (isFontWeight) {
    previewStyle = `font-weight:${displayValue}`;
    previewText = 'Abc 123';
  } else if (isFontFamily) {
    previewStyle = `font-family:${displayValue}`;
    previewText = 'The quick brown fox';
  } else if (isLineHeight) {
    previewStyle = `line-height:${displayValue}`;
    previewText = 'Line 1\nLine 2';
  }

  // Encode token data for detail view
  const tokenData = JSON.stringify({
    name: token.name,
    section: token.section,
    type: 'Typography',
    rawValue: token.value
  });

  return `<div class="token-card" data-token="${esc(tokenData)}">
  <div class="token-preview type-preview">
    <div class="type-sample" style="${esc(previewStyle)}">${esc(previewText)}</div>
  </div>
  <div class="token-info">
    <div class="token-name">${esc(token.name)}</div>
    <div class="token-value">${esc(displayValue)}</div>
  </div>
  <button class="copy-btn" data-value="${esc(displayValue)}" aria-label="Copy ${esc(displayValue)}">
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="5.5" y="5.5" width="8" height="8" rx="1"/>
      <path d="M10.5 5.5v-2a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2"/>
    </svg>
  </button>
</div>`;
}

// ---- render spacing token ----
function renderSpacingToken(token, paletteIdx = 0, themeIdx = 0) {
  let value = token.value;

  // Resolve if it's an array (multi-mode token)
  if (Array.isArray(value)) {
    value = token.section === '1b. Palette'
      ? resolve(value[paletteIdx], paletteIdx, themeIdx)
      : resolve(value[themeIdx], paletteIdx, themeIdx);
  } else if (typeof value === 'string' && value.startsWith('@')) {
    value = resolve(value, paletteIdx, themeIdx);
  }

  const displayValue = String(value);
  const pxValue = parseInt(displayValue);
  const maxWidth = 200;
  const rulerWidth = Math.min(pxValue, maxWidth);

  // Encode token data for detail view
  const tokenData = JSON.stringify({
    name: token.name,
    section: token.section,
    type: 'Spacing',
    rawValue: token.value
  });

  return `<div class="token-card" data-token="${esc(tokenData)}">
  <div class="token-preview spacing-preview">
    <div class="spacing-ruler" style="width:${rulerWidth}px">
      <div class="ruler-bar"></div>
      <div class="ruler-label">${esc(displayValue)}</div>
    </div>
  </div>
  <div class="token-info">
    <div class="token-name">${esc(token.name)}</div>
    <div class="token-value">${esc(displayValue)}</div>
  </div>
  <button class="copy-btn" data-value="${esc(displayValue)}" aria-label="Copy ${esc(displayValue)}">
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="5.5" y="5.5" width="8" height="8" rx="1"/>
      <path d="M10.5 5.5v-2a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2"/>
    </svg>
  </button>
</div>`;
}

// ---- render generic token (border, effects, etc) ----
function renderGenericToken(token, category, paletteIdx = 0, themeIdx = 0) {
  let value = token.value;

  // Resolve if it's an array (multi-mode token)
  if (Array.isArray(value)) {
    value = token.section === '1b. Palette'
      ? resolve(value[paletteIdx], paletteIdx, themeIdx)
      : resolve(value[themeIdx], paletteIdx, themeIdx);
  } else if (typeof value === 'string' && value.startsWith('@')) {
    value = resolve(value, paletteIdx, themeIdx);
  }

  const displayValue = String(value);

  // Encode token data for detail view
  const tokenData = JSON.stringify({
    name: token.name,
    section: token.section,
    type: category || 'Generic',
    rawValue: token.value
  });

  return `<div class="token-card" data-token="${esc(tokenData)}">
  <div class="token-preview generic-preview">
    <div class="generic-value">${esc(displayValue)}</div>
  </div>
  <div class="token-info">
    <div class="token-name">${esc(token.name)}</div>
    <div class="token-value">${esc(displayValue)}</div>
  </div>
  <button class="copy-btn" data-value="${esc(displayValue)}" aria-label="Copy ${esc(displayValue)}">
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="5.5" y="5.5" width="8" height="8" rx="1"/>
      <path d="M10.5 5.5v-2a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2"/>
    </svg>
  </button>
</div>`;
}

// ---- render token category section ----
function renderCategory(categoryName, tokens) {
  if (tokens.length === 0) return '';

  const anchor = categoryName.toLowerCase().replace(/\s+/g, '-');
  const renderFn = {
    'Color': renderColorToken,
    'Typography': renderTypographyToken,
    'Spacing': renderSpacingToken,
    'Border': (token, p, t) => renderGenericToken(token, 'Border', p, t),
    'Effects': (token, p, t) => renderGenericToken(token, 'Effects', p, t)
  }[categoryName] || ((token, p, t) => renderGenericToken(token, categoryName, p, t));

  const tokensHtml = tokens.map(token => renderFn(token)).join('\n');

  return `<section id="${anchor}">
<h2>${esc(categoryName)}</h2>
<p class="sub">${tokens.length} ${categoryName.toLowerCase()} tokens</p>
<div class="token-grid">
${tokensHtml}
</div>
</section>`;
}

// ---- HTML generation ----
function generateHTML(categories, categoryCounts, stats) {
  const totalTokens = stats.totalTokens;

  // Render all category sections
  const categorySections = Object.keys(categories)
    .map(catName => renderCategory(catName, categories[catName]))
    .join('\n');

  let template = readFileSync(join(HERE, 'templates', 'token-explorer.html'), 'utf8');
  const replacements = {
    CATEGORY_SECTIONS: categorySections,
    // \u003c keeps a token value containing '</script>' from terminating the inline script block
    TOKENS_JSON: JSON.stringify({ prim, pal, sem, comp, canv }).replace(/</g, '\\u003c'),
    TOTAL: totalTokens,
    CATEGORY_COUNT: Object.keys(categories).length,
    ...Object.fromEntries(Object.entries(categoryCounts).map(([name, count]) => ['COUNT_' + name, count]))
  };
  return template.replace(/\{\{([A-Z_a-z]+)\}\}/g, (match, key) =>
    key in replacements ? String(replacements[key]) : match);

}

// ---- dry run mode ----
if (isDryRun) {
  const stats = countTokens();

  console.log('Token Explorer - Parse Statistics');
  console.log('='.repeat(50));
  console.log(`Version:        ${DATA.$meta.version}`);
  console.log(`Source:         ${DATA.$meta.source}`);
  console.log(`Exported:       ${DATA.$meta.exported}`);
  console.log(`File Key:       ${DATA.$meta.fileKey}`);
  console.log('');
  console.log(`Total Sections: ${stats.totalSections}`);
  console.log(`Total Tokens:   ${stats.totalTokens}`);
  console.log('');
  console.log('Breakdown by Section:');
  console.log('-'.repeat(50));

  for (const [name, data] of Object.entries(stats.breakdown)) {
    const modes = data.modes.join(', ');
    console.log(`${name}:`);
    console.log(`  Tokens: ${data.count}`);
    console.log(`  Modes:  ${modes}`);
    if (data.declaredCount && data.declaredCount !== data.count) {
      console.log(`  Note:   Declared count (${data.declaredCount}) differs from actual (${data.count})`);
    }
  }

  console.log('');
  console.log('✓ Successfully parsed token file');
  console.log(`✓ Found ${stats.totalTokens} tokens across ${stats.totalSections} sections`);

  process.exit(0);
}

// ---- test categorization mode ----
if (testCategorization) {
  const { categories, uncategorized } = categorizeTokens();
  const stats = countTokens();

  console.log('Token Explorer - Categorization Test');
  console.log('='.repeat(50));
  console.log(`Version:        ${DATA.$meta.version}`);
  console.log(`Total Tokens:   ${stats.totalTokens}`);
  console.log('');
  console.log('Categorization Results:');
  console.log('-'.repeat(50));

  let totalCategorized = 0;
  const categoryKeys = Object.keys(categories).sort();

  for (const categoryName of categoryKeys) {
    const tokens = categories[categoryName];
    totalCategorized += tokens.length;
    console.log(`${categoryName}:`);
    console.log(`  Count: ${tokens.length}`);

    // Show sample tokens (first 5)
    if (tokens.length > 0) {
      console.log('  Samples:');
      const samples = tokens.slice(0, 5);
      for (const token of samples) {
        console.log(`    - ${token.name}`);
      }
      if (tokens.length > 5) {
        console.log(`    ... and ${tokens.length - 5} more`);
      }
    }
    console.log('');
  }

  // Show uncategorized tokens if any
  if (uncategorized.length > 0) {
    console.log('Uncategorized:');
    console.log(`  Count: ${uncategorized.length}`);
    console.log('  Samples:');
    const samples = uncategorized.slice(0, 50);
    for (const token of samples) {
      console.log(`    - ${token.name}`);
    }
    if (uncategorized.length > 50) {
      console.log(`    ... and ${uncategorized.length - 50} more`);
    }
    console.log('');
  }

  console.log('-'.repeat(50));
  console.log(`Total categorized: ${totalCategorized} / ${stats.totalTokens}`);
  console.log(`Categories found:  ${categoryKeys.length}`);
  console.log('');

  // Validation
  const expectedCategories = 6;
  const success = categoryKeys.length === expectedCategories && uncategorized.length === 0;

  if (success) {
    console.log(`✓ All ${expectedCategories} collections categorized correctly`);
    console.log(`✓ All tokens successfully categorized`);
    process.exit(0);
  } else {
    if (categoryKeys.length !== expectedCategories) {
      console.error(`✗ Expected ${expectedCategories} categories, found ${categoryKeys.length}`);
    }
    if (uncategorized.length > 0) {
      console.error(`✗ Not all tokens categorized: ${totalCategorized} / ${stats.totalTokens}`);
      console.error(`✗ ${uncategorized.length} tokens remain uncategorized`);
    }
    process.exit(1);
  }
}

// ---- test resolution mode ----
if (testResolution) {
  console.log('Token Explorer - Alias Resolution Test');
  console.log('='.repeat(50));
  console.log(`Version:        ${DATA.$meta.version}`);
  console.log(`Palettes:       ${PALETTES.join(', ')}`);
  console.log(`Themes:         ${THEMES.join(', ')}`);
  console.log(`Combinations:   ${PALETTES.length} × ${THEMES.length} = ${PALETTES.length * THEMES.length}`);
  console.log('');

  let totalResolved = 0;
  let totalErrors = 0;
  const errors = [];

  // Test each palette/theme combination
  PALETTES.forEach((pn, p) => THEMES.forEach((tn, t) => {
    const combo = `${pn}/${tn}`;
    try {
      const vals = resolveAll(p, t);
      const tokenCount = Object.keys(vals).length;
      totalResolved += tokenCount;
      console.log(`✓ ${combo.padEnd(20)} ${tokenCount} tokens resolved`);
    } catch (err) {
      totalErrors += 1;
      errors.push({ combo, error: err.message });
      console.error(`✗ ${combo.padEnd(20)} ERROR: ${err.message}`);
    }
  }));

  console.log('');
  console.log('-'.repeat(50));
  console.log(`Total combinations tested: ${PALETTES.length * THEMES.length}`);
  console.log(`Total tokens resolved:     ${totalResolved}`);
  console.log(`Errors:                    ${totalErrors}`);
  console.log('');

  if (totalErrors === 0) {
    console.log('✓ All palette/theme combinations resolve correctly');
    console.log(`✓ ${totalResolved} total tokens resolved across all modes`);
    process.exit(0);
  } else {
    console.error('✗ Resolution errors detected:');
    for (const { combo, error } of errors) {
      console.error(`  ${combo}: ${error}`);
    }
    process.exit(1);
  }
}

// ---- generate HTML explorer ----
const { categories, uncategorized } = categorizeTokens();
const stats = countTokens();

if (uncategorized.length > 0) {
  console.error(`✗ ${uncategorized.length} token(s) matched no category and would be silently dropped:`);
  for (const t of uncategorized.slice(0, 20)) console.error(`  ${t.name}`);
  process.exit(1);
}

// Token names end up in HTML attributes, ids and CSS custom properties: keep them to a safe charset.
const BAD_NAME = /[^A-Za-z0-9/_.\- ]/;
const badNames = Object.values(categories).flat().map(t => t.name).filter(n => BAD_NAME.test(n));
if (badNames.length > 0) {
  console.error(`✗ ${badNames.length} token name(s) contain characters outside [A-Za-z0-9/_.- ]:`);
  for (const n of badNames.slice(0, 20)) console.error(`  ${JSON.stringify(n)}`);
  process.exit(1);
}

// Count tokens in each category
const categoryCounts = {};
for (const [catName, tokens] of Object.entries(categories)) {
  categoryCounts[catName] = tokens.length;
}

// Generate HTML
const html = generateHTML(categories, categoryCounts, stats);
console.log(html);
