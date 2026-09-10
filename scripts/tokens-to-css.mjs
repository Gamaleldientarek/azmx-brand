#!/usr/bin/env node
/*
 * AZM X tokens → CSS custom properties
 *
 *   node scripts/tokens-to-css.mjs > azmx-tokens.css
 *   node scripts/tokens-to-css.mjs --palette orange --theme dark   # flatten one combination
 *   node scripts/tokens-to-css.mjs --json                          # resolved values as JSON
 *   node scripts/tokens-to-css.mjs --validate                      # check aliases only, emit nothing
 *
 * Reads assets/tokens/azmx-tokens.json and resolves every alias.
 *
 * Default output carries all twelve combinations, driven by attributes:
 *
 *   <body data-palette="orange" data-theme="dark">
 *
 * Palette defaults to blue, theme to light, so plain <body> gives the house look.
 * Direction tokens (the RTL collection) are emitted for `:root, [dir="ltr"]`
 * with `[dir="rtl"]` overrides.
 *
 * Units — decided by the PRIMITIVE a token resolves to, never by the name of the
 * alias, so `space/md` inherits `px` from `size/space/64`:
 *
 *   size/space, size/font, size/line, size/radius, size/border, size/icon,
 *   size/doc, size/tracking            → px   (Figma stores these as absolute px;
 *                                             tracking is px at the stated size,
 *                                             see references/design-system.md §Type)
 *   size/opacity                       → unitless (0–1)
 *   font/weight                        → numeric CSS weight (Regular → 400, …)
 *   font/family                        → quoted family name
 *   everything else (colours, RTL)     → as-is
 *
 * Validation (broken aliases, cycles, mode-count mismatches) always runs before
 * anything is generated, so a broken alias can never produce `--x: undefined;`.
 *
 * The module is import-safe: `resolve`, `resolveAll`, `loadTokens`, `cssValue`
 * and friends are named exports and the CLI only runs when this file is the entry
 * point.
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
export const DEFAULT_TOKEN_PATH = join(HERE, '..', 'assets', 'tokens', 'azmx-tokens.json');

// ---- unit rules ----
// Keyed by primitive-name prefix. `px` appends a unit to numeric values,
// `number` leaves them unitless, `weight` maps Figma style names to CSS weights,
// `family` quotes the family name. Anything not listed is emitted verbatim.
export const UNIT_RULES = {
  'size/space/':    'px',
  'size/font/':     'px',
  'size/line/':     'px',
  'size/radius/':   'px',
  'size/border/':   'px',
  'size/icon/':     'px',
  'size/doc/':      'px',
  'size/tracking/': 'px',
  'size/opacity/':  'number',
  'font/weight/':   'weight',
  'font/family/':   'family',
};

// Figma style name → CSS font-weight. Matched case-insensitively with spaces and
// hyphens removed, so "Extra Light", "extra-light" and "ExtraLight" all map to 200.
export const FONT_WEIGHTS = {
  thin: 100, hairline: 100,
  extralight: 200, ultralight: 200,
  light: 300,
  regular: 400, normal: 400, book: 400,
  medium: 500,
  semibold: 600, demibold: 600,
  bold: 700,
  extrabold: 800, ultrabold: 800,
  black: 900, heavy: 900,
};

const warned = new Set();
function warnOnce(msg) {
  if (warned.has(msg)) return;
  warned.add(msg);
  console.error('⚠ ' + msg);
}

/** CSS font-weight for a Figma style name, or null when the name is unknown. */
export function fontWeight(name) {
  if (typeof name === 'number') return name;
  if (typeof name !== 'string') return null;
  if (/^\d+$/.test(name.trim())) return Number(name);
  const key = name.toLowerCase().replace(/[\s_-]+/g, '');
  return key in FONT_WEIGHTS ? FONT_WEIGHTS[key] : null;
}

/** The unit rule that applies to a primitive name, or null. */
export function unitFor(primitiveName) {
  if (typeof primitiveName !== 'string') return null;
  for (const [prefix, rule] of Object.entries(UNIT_RULES))
    if (primitiveName.startsWith(prefix)) return rule;
  return null;
}

/** Quote a font family name as a CSS string. */
function cssString(s) {
  return '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
}

/**
 * Format a resolved value as a CSS value, given the primitive it resolved to
 * (null for literals that never touched a primitive, e.g. RTL tokens).
 */
export function cssValue(value, primitiveName = null) {
  if (value === undefined || value === null)
    throw new Error('cannot format undefined value' + (primitiveName ? ' for ' + primitiveName : ''));
  const rule = unitFor(primitiveName);
  switch (rule) {
    case 'px':
      if (typeof value === 'number') return value === 0 ? '0' : value + 'px';
      return String(value);
    case 'number':
      return String(value);
    case 'weight': {
      const w = fontWeight(value);
      if (w === null) {
        warnOnce(`unknown font weight "${value}" for ${primitiveName}; emitting raw value`);
        return String(value);
      }
      return String(w);
    }
    case 'family':
      return cssString(value);
    default:
      return typeof value === 'number' ? String(value) : String(value);
  }
}

/** Quote an RTL token value that is meant for `content:` (glyphs, quote marks). */
function rtlCssValue(name, value) {
  if (/^(quote|chevron|arrow)\//.test(name)) return cssString(value);
  return String(value);
}

// ---- loading ----
/**
 * Load a token file and build the resolution context.
 * Returns { DATA, prim, pal, sem, comp, canv, rtl, PALETTES, THEMES, DIRECTIONS }.
 */
export function loadTokens(path = DEFAULT_TOKEN_PATH) {
  const DATA = JSON.parse(readFileSync(path, 'utf8'));
  const get = k => (DATA[k] && DATA[k].tokens) || {};
  const ctx = {
    DATA,
    prim: get('1. Primitives'),
    pal:  get('1b. Palette'),
    sem:  get('2. Semantic'),
    comp: get('3. Component'),
    canv: get('4. Canvas'),
    rtl:  get('RTL'),
    PALETTES:   ((DATA['1b. Palette'] || {}).modes || []).map(m => m.toLowerCase()),
    THEMES:     ((DATA['2. Semantic'] || {}).modes || []).map(m => m.toLowerCase()),
    DIRECTIONS: ((DATA.RTL || {}).modes || []).map(m => m.toLowerCase()),
  };
  return ctx;
}

// The default context: the real token file. Loaded lazily so importing the module
// with a missing/broken token file only fails when something is actually resolved.
let defaultCtx = null;
function ctxOf(ctx) {
  if (ctx) return ctx;
  if (!defaultCtx) defaultCtx = loadTokens();
  return defaultCtx;
}

// ---- resolve ----
// Every token is either a literal, or "@other/token". Palette tokens hold one
// value per palette; Semantic tokens one per theme. Resolution therefore needs
// to know which palette and which theme it is resolving *for*.

function pick(arr, idx, name) {
  const v = arr[idx];
  if (v === undefined) throw new Error(`token ${name} has no value for mode index ${idx}`);
  return v;
}

/**
 * Resolve a reference to its literal value AND the primitive it landed on.
 * Returns { value, primitive } where primitive is null for pure literals.
 */
export function resolveWithSource(ref, paletteIdx, themeIdx, depth = 0, ctx = null) {
  const c = ctxOf(ctx);
  if (depth > 12) throw new Error('alias loop at ' + ref);
  if (typeof ref !== 'string' || !ref.startsWith('@')) {
    if (ref === undefined) throw new Error('unresolved value (undefined)');
    return { value: ref, primitive: null };
  }
  const name = ref.slice(1);
  const { prim, pal, sem, comp, canv } = c;

  if (name in prim) return { value: prim[name], primitive: name };
  if (name in pal)  return resolveWithSource(pick(pal[name], paletteIdx, name), paletteIdx, themeIdx, depth + 1, c);
  if (name in sem)  return resolveWithSource(pick(sem[name], themeIdx, name),   paletteIdx, themeIdx, depth + 1, c);
  if (name in comp) return resolveWithSource(comp[name],                        paletteIdx, themeIdx, depth + 1, c);
  if (name in canv) return resolveWithSource(canv[name],                        paletteIdx, themeIdx, depth + 1, c);
  throw new Error('unknown token: ' + name);
}

/** Resolve a reference to its literal value (signature kept for callers/tests). */
export function resolve(ref, paletteIdx, themeIdx, depth = 0, ctx = null) {
  return resolveWithSource(ref, paletteIdx, themeIdx, depth, ctx).value;
}

export const varName = n => '--azmx-' + n.replace(/\//g, '-');
export const fmt = v => typeof v === 'number' ? String(v) : v;

/** Every semantic + component + canvas token, resolved for one combination. */
export function resolveAll(paletteIdx, themeIdx, ctx = null) {
  const c = ctxOf(ctx);
  const out = {};
  for (const n of Object.keys(c.sem))  out[n] = resolve(pick(c.sem[n], themeIdx, n), paletteIdx, themeIdx, 0, c);
  for (const n of Object.keys(c.comp)) out[n] = resolve(c.comp[n],                   paletteIdx, themeIdx, 0, c);
  for (const n of Object.keys(c.canv)) out[n] = resolve(c.canv[n],                   paletteIdx, themeIdx, 0, c);
  return out;
}

/** Like resolveAll but every entry is a CSS-ready string (units applied). */
export function resolveAllCss(paletteIdx, themeIdx, ctx = null) {
  const c = ctxOf(ctx);
  const out = {};
  const put = (n, ref) => {
    if (n in out) throw new Error(`duplicate custom property ${varName(n)}: token ${n} is declared in two collections`);
    const { value, primitive } = resolveWithSource(ref, paletteIdx, themeIdx, 0, c);
    out[n] = cssValue(value, primitive);
  };
  for (const n of Object.keys(c.sem))  put(n, pick(c.sem[n], themeIdx, n));
  for (const n of Object.keys(c.comp)) put(n, c.comp[n]);
  for (const n of Object.keys(c.canv)) put(n, c.canv[n]);
  return out;
}

/** RTL collection for one direction index, as CSS-ready strings. */
export function resolveRtl(directionIdx, ctx = null) {
  const c = ctxOf(ctx);
  const out = {};
  for (const [n, v] of Object.entries(c.rtl)) {
    const raw = Array.isArray(v) ? pick(v, directionIdx, n) : v;
    const { value } = resolveWithSource(raw, 0, 0, 0, c);
    out[n] = rtlCssValue(n, value);
  }
  return out;
}

// ---- validation ----
/**
 * Validate every collection: metadata counts, mode lengths, broken aliases and
 * cycles across every palette/theme/direction combination. Returns a report;
 * never prints. `report.ok` is false when there are errors.
 */
export function validateTokens(ctx = null) {
  const c = ctxOf(ctx);
  const { DATA, prim, PALETTES, THEMES } = c;
  const brokenAliases = [];
  const circularRefs = [];
  const modeMismatches = [];
  const metadataCountMismatches = [];
  const duplicateNames = [];

  const tierChecks = Object.entries(DATA)
    .filter(([, collection]) => collection && collection.tokens)
    .map(([name, collection]) => ({ name, tokens: collection.tokens, label: name }));

  tierChecks.forEach(({ name, tokens, label }) => {
    const declaredCount = DATA[name]?.count;
    const actualCount = Object.keys(tokens).length;
    if (declaredCount === undefined) {
      metadataCountMismatches.push({ tier: label, issue: 'missing count field in metadata', declared: 'undefined', actual: actualCount });
    } else if (declaredCount !== actualCount) {
      metadataCountMismatches.push({ tier: label, declared: declaredCount, actual: actualCount });
    }
  });

  for (const { name, tokens } of tierChecks) {
    const modes = DATA[name].modes;
    if (!Array.isArray(modes) || modes.length === 0) {
      modeMismatches.push({ token: '*', tier: name, expected: 'nonempty modes', actual: 'invalid' });
      continue;
    }
    if (modes.length > 1) {
      for (const [token, value] of Object.entries(tokens)) {
        if (!Array.isArray(value) || value.length !== modes.length)
          modeMismatches.push({ token, tier: name, expected: modes.length, actual: Array.isArray(value) ? value.length : 'not an array' });
      }
    }
  }

  // Same token name in two collections would collide on one --azmx-* property.
  const owners = new Map();
  for (const { name: tier, tokens } of tierChecks)
    for (const name of Object.keys(tokens)) {
      if (owners.has(name)) duplicateNames.push({ token: name, tiers: [owners.get(name), tier] });
      else owners.set(name, tier);
    }

  const referencedPrimitives = new Set();
  function trackReferences(value) {
    if (typeof value === 'string' && value.startsWith('@')) {
      const refName = value.slice(1);
      if (refName in prim) referencedPrimitives.add(refName);
    } else if (Array.isArray(value)) {
      value.forEach(trackReferences);
    }
  }
  for (const { tokens } of tierChecks)
    for (const value of Object.values(tokens)) trackReferences(value);
  const unreferencedPrimitives = Object.keys(prim).filter(name => !referencedPrimitives.has(name));

  // Validate all tokens, including unused aliases, without a depth cutoff.
  const registry = new Map();
  for (const { name: tier, tokens } of tierChecks)
    for (const [name, value] of Object.entries(tokens))
      registry.set(name, { tier, value });

  function visit(name, p, t, direction, seen = new Set()) {
    if (seen.has(name)) throw new Error('alias loop at ' + name);
    const entry = registry.get(name);
    if (!entry) throw new Error('unknown token: ' + name);
    const next = new Set(seen); next.add(name);
    let value = entry.value;
    if (Array.isArray(value)) {
      const index = entry.tier === '1b. Palette' ? p : entry.tier === '2. Semantic' ? t : direction;
      value = value[index];
      if (value === undefined) throw new Error(`unknown token: ${name} has no value at mode index ${index}`);
    }
    if (value === undefined) throw new Error('unknown token: ' + name + ' is undefined');
    if (typeof value === 'string' && value.startsWith('@'))
      return visit(value.slice(1), p, t, direction, next);
    return value;
  }
  const paletteList = PALETTES.length ? PALETTES : ['default'];
  const themeList = THEMES.length ? THEMES : ['default'];
  paletteList.forEach((pn, p) => themeList.forEach((tn, t) => {
    (DATA.RTL?.modes || ['default']).forEach((direction, d) => {
      const combo = pn + '/' + tn + '/' + direction;
      for (const [name, { tier }] of registry) {
        try { visit(name, p, t, d); }
        catch (err) {
          const errors = err.message.startsWith('unknown token:') ? brokenAliases : circularRefs;
          errors.push({ token: name, combo, tier, error: err.message });
        }
      }
    });
  }));

  const errorCount = brokenAliases.length + circularRefs.length + modeMismatches.length + metadataCountMismatches.length + duplicateNames.length;
  return {
    ok: errorCount === 0,
    errorCount,
    brokenAliases, circularRefs, modeMismatches, metadataCountMismatches, duplicateNames,
    unreferencedPrimitives,
  };
}

/** Print a validation report to stderr in the historical format. */
export function printValidationReport(report) {
  const { brokenAliases, circularRefs, modeMismatches, metadataCountMismatches, duplicateNames, unreferencedPrimitives } = report;
  const hasErrors = !report.ok;
  const hasWarnings = unreferencedPrimitives.length > 0;

  if (hasErrors) {
    console.error('✗ Token validation failed\n');

    if (metadataCountMismatches.length > 0) {
      console.error('Metadata count mismatches:');
      metadataCountMismatches.forEach(({ tier, declared, actual, issue }) => {
        if (issue) console.error(`  ${tier}: ${issue} (actual: ${actual})`);
        else console.error(`  ${tier}: declared ${declared} tokens, found ${actual}`);
      });
      console.error(`\nTotal metadata count mismatches: ${metadataCountMismatches.length}\n`);
    }
    if (modeMismatches.length > 0) {
      console.error('Mode count mismatches:');
      modeMismatches.forEach(({ token, tier, expected, actual }) => {
        console.error(`  ${tier}/${token}: expected ${expected} values, got ${actual}`);
      });
      console.error(`\nTotal mode mismatches: ${modeMismatches.length}\n`);
    }
    if (duplicateNames.length > 0) {
      console.error('Duplicate token names across collections:');
      duplicateNames.forEach(({ token, tiers }) => console.error(`  ${token}: ${tiers.join(' and ')}`));
      console.error(`\nTotal duplicate names: ${duplicateNames.length}\n`);
    }
    if (circularRefs.length > 0) {
      console.error('Circular references detected:');
      circularRefs.forEach(({ token, combo, tier, error }) => console.error(`  ${tier}/${token} [${combo}]: ${error}`));
      console.error(`\nTotal circular references: ${circularRefs.length}\n`);
    }
    if (brokenAliases.length > 0) {
      console.error('Broken aliases:');
      brokenAliases.forEach(({ token, combo, tier, error }) => console.error(`  ${tier}/${token} [${combo}]: ${error}`));
      console.error(`\nTotal broken aliases: ${brokenAliases.length}\n`);
    }

    console.error('─'.repeat(60));
    console.error(`SUMMARY: ${report.errorCount} error(s) found`);
    if (metadataCountMismatches.length > 0) console.error(`  • Metadata mismatches: ${metadataCountMismatches.length}`);
    if (modeMismatches.length > 0) console.error(`  • Mode mismatches: ${modeMismatches.length}`);
    if (duplicateNames.length > 0) console.error(`  • Duplicate names: ${duplicateNames.length}`);
    if (circularRefs.length > 0) console.error(`  • Circular references: ${circularRefs.length}`);
    if (brokenAliases.length > 0) console.error(`  • Broken aliases: ${brokenAliases.length}`);
    console.error('─'.repeat(60));
    return;
  }

  if (hasWarnings) {
    console.error('⚠ Token validation warnings\n');
    console.error('Unreferenced primitives:');
    unreferencedPrimitives.forEach(name => console.error(`  primitives/${name}`));
    console.error(`\nTotal unreferenced primitives: ${unreferencedPrimitives.length}`);
    console.error('(Consider removing unused primitives or verify they are intended for future use)\n');
    console.error('─'.repeat(60));
    console.error(`SUMMARY: ${unreferencedPrimitives.length} warning(s) found`);
    console.error(`  • Unreferenced primitives: ${unreferencedPrimitives.length}`);
    console.error('─'.repeat(60));
    console.error('✓ Token validation passed: all combinations resolve successfully');
  } else {
    console.error('─'.repeat(60));
    console.error('✓ Token validation passed: all combinations resolve successfully');
    console.error('SUMMARY: 0 errors, 0 warnings');
    console.error('─'.repeat(60));
  }
}

// ---- CSS generation ----
/**
 * Tracks declared custom-property names per scope and throws on a duplicate.
 * Override blocks ([data-palette], [data-theme], [dir]) are separate scopes; the
 * base `:root` is one scope even though it is written as several blocks.
 */
class Declarations {
  constructor() { this.seen = new Map(); }
  /** Register a declaration and return it as `name: value;` (no indent). */
  register(scope, name, value) {
    if (value === undefined || value === null || String(value) === 'undefined')
      throw new Error(`refusing to emit ${name}: value is undefined (scope ${scope})`);
    let names = this.seen.get(scope);
    if (!names) { names = new Set(); this.seen.set(scope, names); }
    if (names.has(name)) throw new Error(`duplicate custom property ${name} in scope ${scope}`);
    names.add(name);
    return `${name}: ${value};`;
  }
  /** Register and return an indented declaration line. */
  add(scope, name, value) { return '  ' + this.register(scope, name, value); }
}

/** Flatten one combination to a `:root` block. */
export function generateSingleCss(paletteIdx, themeIdx, ctx = null) {
  const c = ctxOf(ctx);
  const decl = new Declarations();
  const vals = resolveAllCss(paletteIdx, themeIdx, c);
  const L = [];
  L.push(`/* AZM X tokens — ${c.PALETTES[paletteIdx]} / ${c.THEMES[themeIdx]} — v${c.DATA.$meta?.version ?? '0'} */`);
  L.push(':root {');
  for (const [n, v] of Object.entries(vals)) L.push(decl.add(':root', varName(n), v));
  L.push('}');
  if (c.DIRECTIONS.length) L.push('', ...rtlBlocks(c, decl));
  return L.join('\n');
}

function rtlBlocks(c, decl) {
  const L = [];
  const ltrIdx = Math.max(0, c.DIRECTIONS.indexOf('ltr'));
  const ltr = resolveRtl(ltrIdx, c);
  L.push(`/* Direction — ${c.DIRECTIONS[ltrIdx]} is the default; <html dir="rtl"> flips it */`);
  L.push(':root, [dir="ltr"] {');
  for (const [n, v] of Object.entries(ltr)) L.push(decl.add(':root', varName(n), v));
  L.push('}');
  c.DIRECTIONS.forEach((dn, d) => {
    if (d === ltrIdx) return;
    const vals = resolveRtl(d, c);
    L.push('');
    L.push(`/* ${dn} — ${Object.keys(vals).length} direction tokens */`);
    L.push(`[dir="${dn}"] {`);
    for (const [n, v] of Object.entries(vals)) L.push(decl.add(`[dir="${dn}"]`, varName(n), v));
    L.push('}');
  });
  return L;
}

/** The full attribute-driven stylesheet (all palettes × themes, plus direction). */
export function generateCss(ctx = null) {
  const c = ctxOf(ctx);
  const { DATA, prim, sem, PALETTES, THEMES } = c;
  const decl = new Declarations();
  const L = [];
  L.push(`/* AZM X Design Tokens v${DATA.$meta?.version ?? '0'} — generated, do not edit by hand */`);
  L.push(`/* Source: ${DATA.$meta?.source ?? ''} (${DATA.$meta?.fileKey ?? ''}), exported ${DATA.$meta?.exported ?? ''} */`);
  L.push('/*');
  L.push(' *   <body data-palette="orange" data-theme="dark">');
  L.push(' *   color: var(--azmx-text-primary);');
  L.push(' *   background: var(--azmx-surface-page);');
  L.push(' *   padding: var(--azmx-space-md);      lengths carry px');
  L.push(' *   font-weight: var(--azmx-weight-bold);  weights are numeric');
  L.push(' *');
  L.push(' * Palette defaults to blue, theme to light, direction to ltr (<html dir="rtl"> flips).');
  L.push(' */');
  L.push('');

  L.push('/* Primitives — reference only. Prefer the semantic variables below. */');
  L.push(':root {');
  for (const [n, v] of Object.entries(prim)) L.push(decl.add(':root', varName(n), cssValue(v, n)));
  L.push('}');
  L.push('');

  const base = resolveAllCss(0, 0, c);
  L.push(`/* Semantic — ${PALETTES[0]} / ${THEMES[0]} */`);
  L.push(':root {');
  for (const [n, v] of Object.entries(base)) L.push(decl.add(':root', varName(n), v));
  L.push('}');
  L.push('');

  // only emit what actually differs from base, so the file stays readable
  PALETTES.forEach((pn, p) => THEMES.forEach((tn, t) => {
    if (p === 0 && t === 0) return;
    const vals = resolveAllCss(p, t, c);
    const diff = Object.entries(vals).filter(([n, v]) => v !== base[n]);
    if (!diff.length) return;
    const sel = p === 0
      ? `[data-theme="${tn}"]`
      : (t === 0 ? `[data-palette="${pn}"]` : `[data-palette="${pn}"][data-theme="${tn}"]`);
    L.push(`/* ${pn} / ${tn} — ${diff.length} overrides */`);
    L.push(`${sel} {`);
    for (const [n, v] of diff) L.push(decl.add(sel, varName(n), v));
    L.push('}');
    L.push('');
  }));

  // the gradient, per palette, as a ready-made value
  const gradientStops = ['gradient/start', 'gradient/mid', 'gradient/mid-alt', 'gradient/end'];
  if (gradientStops.every(n => n in sem)) {
    L.push('/* Brand gradient — event surfaces only: covers, dividers, closings */');
    PALETTES.forEach((pn, p) => {
      const g = gradientStops.map(n => resolve(sem[n][0], p, 0, 0, c));
      const sel = p === 0 ? ':root' : `[data-palette="${pn}"]`;
      const line = decl.register(sel, '--azmx-gradient', `linear-gradient(145deg, ${g[0]} 0%, ${g[1]} 55%, ${g[3]} 100%)`);
      L.push(`${sel} { ${line} }`);
    });
    L.push('');
  }

  // Full font stacks. The bare family names live in --azmx-font-heading /
  // --azmx-font-text (semantic font/heading, font/text); these add fallbacks.
  if (prim['font/family/display'] || prim['font/family/body']) {
    L.push('/* Font stacks — family + fallbacks. Load the faces from assets/fonts.css */');
    L.push(':root {');
    if (prim['font/family/display'])
      L.push(decl.add(':root', '--azmx-font-stack-heading', `${cssString(prim['font/family/display'])}, Georgia, serif`));
    if (prim['font/family/body'])
      L.push(decl.add(':root', '--azmx-font-stack-text', `${cssString(prim['font/family/body'])}, system-ui, sans-serif`));
    L.push('}');
  }

  if (c.DIRECTIONS.length) {
    L.push('');
    L.push(...rtlBlocks(c, decl));
  }

  return L.join('\n');
}

// ---- CLI ----
export function main(argv = process.argv.slice(2)) {
  const args = argv;
  const flag = n => { const i = args.indexOf('--' + n); return i === -1 ? null : args[i + 1]; };
  const onlyPalette = flag('palette');
  const onlyTheme   = flag('theme');
  const asJson      = args.includes('--json');
  const validateOnly = args.includes('--validate');

  const c = ctxOf(null);
  const { PALETTES, THEMES, DIRECTIONS } = c;

  // Validation always runs first: a broken alias must never reach the CSS.
  const report = validateTokens(c);
  if (validateOnly) {
    printValidationReport(report);
    if (!report.ok) process.exitCode = 1;
    return;
  }
  if (!report.ok) {
    printValidationReport(report);
    console.error('\nNothing generated: fix the token file (see --validate).');
    process.exitCode = 1;
    return;
  }
  if (report.unreferencedPrimitives.length)
    console.error(`⚠ ${report.unreferencedPrimitives.length} unreferenced primitive(s); run --validate for the list`);

  // ---- single combination ----
  if (onlyPalette || onlyTheme) {
    const p = PALETTES.indexOf((onlyPalette || PALETTES[0] || 'blue').toLowerCase());
    const t = THEMES.indexOf((onlyTheme || THEMES[0] || 'light').toLowerCase());
    if (p === -1) { console.error('unknown palette. one of: ' + PALETTES.join(', ')); process.exitCode = 1; return; }
    if (t === -1) { console.error('unknown theme. one of: ' + THEMES.join(', ')); process.exitCode = 1; return; }
    if (asJson) { console.log(JSON.stringify(resolveAll(p, t, c), null, 2)); return; }
    console.log(generateSingleCss(p, t, c));
    return;
  }

  // ---- all combinations as JSON ----
  if (asJson) {
    const all = {};
    PALETTES.forEach((pn, p) => THEMES.forEach((tn, t) => { all[`${pn}/${tn}`] = resolveAll(p, t, c); }));
    DIRECTIONS.forEach((dn, d) => { all[`direction/${dn}`] = resolveRtl(d, c); });
    console.log(JSON.stringify(all, null, 2));
    return;
  }

  console.log(generateCss(c));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();
