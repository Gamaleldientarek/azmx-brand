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
    'Effects': []
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
      if (isColorToken(tokenName)) {
        categories['Color'].push(token);
      } else if (isSpacingToken(tokenName)) {
        categories['Spacing'].push(token);
      } else if (isTypographyToken(tokenName)) {
        categories['Typography'].push(token);
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

  return `<div class="token-card">
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

  return `<div class="token-card">
  <div class="token-preview type-preview">
    <div class="type-sample" style="${previewStyle}">${previewText}</div>
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

  return `<div class="token-card">
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
function renderGenericToken(token, paletteIdx = 0, themeIdx = 0) {
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

  return `<div class="token-card">
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
    'Border': renderGenericToken,
    'Effects': renderGenericToken
  }[categoryName] || renderGenericToken;

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

  return `<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AZMX Token Explorer</title>
<meta name="description" content="AZMX design token explorer. Interactive browser for color, typography, spacing, border, and effect tokens.">
<link rel="icon" href="assets/logo/azmx-favicon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="AZMX Brand Skill">
<meta property="og:title" content="AZMX Token Explorer">
<meta property="og:description" content="AZMX design token explorer. Interactive browser for color, typography, spacing, border, and effect tokens.">
<meta property="og:url" content="https://gamaleldientarek.github.io/azmx-brand/tokens.html">
<meta property="og:image" content="https://gamaleldientarek.github.io/azmx-brand/assets/cover-social-1280x640.jpg">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="640">
<meta property="og:image:alt" content="AZMX Brand Skill">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AZMX Token Explorer">
<meta name="twitter:description" content="AZMX design token explorer. Interactive browser for color, typography, spacing, border, and effect tokens.">
<meta name="twitter:image" content="https://gamaleldientarek.github.io/azmx-brand/assets/cover-social-1280x640.jpg">
<style>
:root{--navy:#040038;--electric:#001AFF;--lightblue:#5D8FFF;--blue100:#DDE8FF;--blue200:#BFD5FF}
*{box-sizing:border-box}
body{margin:0;background:var(--navy);color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Tahoma,sans-serif;-webkit-font-smoothing:antialiased}
body{display:grid;grid-template-columns:230px minmax(0,1fr)}
aside{position:sticky;top:0;height:100vh;overflow-y:auto;padding:40px 0 40px 28px;
border-right:1px solid rgba(255,255,255,.12)}
.brand{display:flex;align-items:center;gap:9px;margin:0 0 36px;font-size:13px;font-weight:600;
letter-spacing:2px;text-transform:uppercase;color:var(--lightblue)}
.brand img{width:18px;height:18px}
aside nav{display:flex;flex-direction:column;gap:2px;padding:0}
aside nav a{display:flex;align-items:center;justify-content:space-between;gap:10px;
min-height:38px;padding:0 16px 0 12px;border:0;border-left:2px solid transparent;
color:var(--blue100);opacity:.72;text-decoration:none;font-size:14px;
transition:opacity .18s,border-color .18s,background .18s}
aside nav a:hover{opacity:1;background:rgba(255,255,255,.05)}
aside nav a.on{opacity:1;border-left-color:var(--electric);background:rgba(255,255,255,.05)}
aside nav a .n{font-size:12px;opacity:.55;font-variant-numeric:tabular-nums}
.navsep{margin:20px 12px 10px;font-size:11px;letter-spacing:1.6px;text-transform:uppercase;
color:var(--blue200);opacity:.45}
main{min-width:0}
header{padding:clamp(48px,9vw,120px) clamp(24px,5vw,64px) 56px;max-width:1200px}
@media(max-width:900px){
  body{grid-template-columns:1fr}
  aside{position:static;height:auto;border-right:0;border-bottom:1px solid rgba(255,255,255,.12);
  padding:24px 24px 20px}
  .brand{margin-bottom:18px}
  aside nav{flex-direction:row;flex-wrap:wrap;gap:8px}
  aside nav a{border-left:0;border:1px solid rgba(255,255,255,.18);padding:0 14px;min-height:44px}
  aside nav a.on{border-color:var(--electric);border-left-width:1px}
  .navsep{display:none}
}
.eyebrow{color:var(--lightblue);text-transform:uppercase;letter-spacing:2.4px;font-size:14px;font-weight:600;margin:0 0 28px}
h1{font-family:Georgia,'Times New Roman',serif;font-size:clamp(44px,7vw,96px);font-weight:400;letter-spacing:-2px;line-height:1.02;margin:0 0 28px}
.lede{color:var(--blue100);font-size:clamp(17px,2vw,21px);line-height:1.65;max-width:62ch;margin:0 0 12px;opacity:.88}
.meta{color:var(--blue200);opacity:.7;font-size:15px;margin:24px 0 0;font-variant-numeric:tabular-nums}
section{padding:0 clamp(24px,5vw,64px);margin-bottom:80px}
h2{font-family:Georgia,serif;font-weight:500;font-size:clamp(28px,3.4vw,40px);margin:40px 0 6px;
border-top:1px solid rgba(255,255,255,.14);padding-top:28px;letter-spacing:-.5px}
.sub{color:var(--blue200);opacity:.7;font-size:15px;margin:0 0 28px;max-width:60ch;line-height:1.6}
.token-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin-top:24px}
.token-card{border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.02);
padding:16px;display:flex;flex-direction:column;gap:12px;position:relative;
transition:border-color .18s,background .18s}
.token-card:hover{border-color:rgba(255,255,255,.24);background:rgba(255,255,255,.04)}
.token-preview{min-height:80px;display:flex;align-items:center;justify-content:center;
border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.03);padding:16px}
.color-swatch{width:100%;height:60px;border:1px solid rgba(255,255,255,.25);
box-shadow:0 2px 8px rgba(0,0,0,.3)}
.type-preview{background:rgba(255,255,255,.95);color:var(--navy);min-height:100px}
.type-sample{font-size:24px;text-align:center;white-space:pre-line}
.spacing-preview{background:transparent;justify-content:flex-start}
.spacing-ruler{position:relative;height:40px;display:flex;align-items:center}
.ruler-bar{position:absolute;top:50%;left:0;width:100%;height:2px;
background:var(--electric);transform:translateY(-50%)}
.ruler-bar::before,.ruler-bar::after{content:'';position:absolute;top:50%;
width:2px;height:12px;background:var(--electric);transform:translateY(-50%)}
.ruler-bar::before{left:0}
.ruler-bar::after{right:0}
.ruler-label{position:absolute;top:0;left:50%;transform:translateX(-50%);
font-size:11px;color:var(--blue200);font-variant-numeric:tabular-nums}
.generic-preview{background:rgba(255,255,255,.03)}
.generic-value{color:var(--blue100);font-size:15px;font-family:monospace;opacity:.9}
.token-info{display:flex;flex-direction:column;gap:4px}
.token-name{font-size:12.5px;color:var(--blue200);opacity:.72;word-break:break-word}
.token-value{font-size:14px;color:var(--blue100);font-family:monospace;
font-variant-numeric:tabular-nums;opacity:.95}
.copy-btn{position:absolute;top:10px;right:10px;min-height:32px;min-width:32px;
padding:6px;background:rgba(4,0,56,.82);color:#fff;border:1px solid rgba(255,255,255,.28);
cursor:pointer;opacity:0;transform:translateY(-4px);
transition:opacity .15s,transform .15s,background .15s,border-color .15s;
backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);display:flex;
align-items:center;justify-content:center}
.token-card:hover .copy-btn{opacity:1;transform:translateY(0)}
.copy-btn:hover{background:var(--electric);border-color:var(--electric)}
.copy-btn:focus-visible{outline:2px solid var(--lightblue);outline-offset:2px;opacity:1;transform:translateY(0)}
.copy-btn[data-copied="1"]{background:var(--electric);border-color:var(--electric)}
.copy-btn svg{width:14px;height:14px;flex:none}
@media (hover:none){.copy-btn{opacity:1;transform:none}}
footer{margin-top:88px;padding:56px clamp(24px,5vw,80px) 72px;border-top:1px solid rgba(255,255,255,.14);color:var(--blue200);font-size:15px;line-height:1.8;opacity:.75}
code{background:rgba(255,255,255,.08);padding:3px 8px;font-size:13px;white-space:nowrap}
a.link{color:var(--lightblue)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
<aside><p class="brand"><img src="assets/logo/azmx-favicon.png" alt="">AZMX</p><nav>
<a href="#top" class="on"><span>All tokens</span><span class="n">${totalTokens}</span></a>
<p class="navsep">Categories</p>
<a href="#color"><span>Color</span><span class="n">${categoryCounts['Color']}</span></a>
<a href="#spacing"><span>Spacing</span><span class="n">${categoryCounts['Spacing']}</span></a>
<a href="#typography"><span>Typography</span><span class="n">${categoryCounts['Typography']}</span></a>
<a href="#border"><span>Border</span><span class="n">${categoryCounts['Border']}</span></a>
<a href="#effects"><span>Effects</span><span class="n">${categoryCounts['Effects']}</span></a>
<p class="navsep">Tools</p>
<a href="index.html"><span>Image Library</span></a>
<a href="https://github.com/Gamaleldientarek/azmx-brand"><span>The brand skill</span></a>
</nav></aside>
<main>
<header>
<p class="eyebrow">AZMX Brand Skill</p>
<h1>Token Explorer</h1>
<p class="lede">Interactive browser for AZMX design tokens. Explore colors, typography, spacing, borders, and effects across all themes and palettes.</p>
<p class="meta">${totalTokens} tokens · ${Object.keys(categories).length} categories · Version ${DATA.$meta.version}</p>
</header>
${categorySections}
<footer>
<p>Generated from <code>${DATA.$meta.source}</code> · Exported ${DATA.$meta.exported}</p>
<p style="margin-top:12px">Part of the <a href="https://github.com/Gamaleldientarek/azmx-brand" class="link">AZMX Brand Skill</a></p>
</footer>
<p class="sr" role="status" aria-live="polite" id="copy-status"></p>
</main>
<script>
document.querySelectorAll('.copy-btn').forEach(function(btn){
  btn.addEventListener('click', function(){
    var value = btn.dataset.value;
    var done = function(){
      btn.dataset.copied = '1';
      document.getElementById('copy-status').textContent = value + ' copied to clipboard';
      setTimeout(function(){
        btn.removeAttribute('data-copied');
      }, 2000);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(value).then(done).catch(fallback);
    } else { fallback(); }
    function fallback(){
      var ta = document.createElement('textarea');
      ta.value = value; ta.setAttribute('readonly','');
      ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); }
      catch (e) {}
      document.body.removeChild(ta);
    }
  });
});
</script>`;
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
  const expectedCategories = 5;
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

// Count tokens in each category
const categoryCounts = {};
for (const [catName, tokens] of Object.entries(categories)) {
  categoryCounts[catName] = tokens.length;
}

// Generate HTML
const html = generateHTML(categories, categoryCounts, stats);
console.log(html);
