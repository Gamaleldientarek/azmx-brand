/**
 * Units, font weights, duplicate detection and RTL emission in tokens-to-css.mjs.
 *
 * Also a small CSS validator: every `--azmx-*` declaration in the generated
 * stylesheet must carry a value that is valid for its type (length with unit,
 * hex colour, numeric weight, quoted font family, ...).
 */

import { describe, it, expect } from 'vitest';
import { readFileSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { execFileSync } from 'node:child_process';

import {
  loadTokens,
  resolve,
  resolveAll,
  resolveAllCss,
  resolveRtl,
  resolveWithSource,
  cssValue,
  fontWeight,
  unitFor,
  validateTokens,
  generateCss,
  generateSingleCss,
  UNIT_RULES,
  FONT_WEIGHTS,
} from '../scripts/tokens-to-css.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const SCRIPT = join(ROOT, 'scripts', 'tokens-to-css.mjs');
const EXPLORER = join(ROOT, 'scripts', 'build-token-explorer.mjs');

const CTX = loadTokens();
const CSS = generateCss(CTX);

// ---- helpers ----

/** Parse `selector { decls }` blocks into [{selector, decls:[{name,value}]}]. */
function parseBlocks(css) {
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, '');
  const blocks = [];
  const re = /([^{}]+)\{([^{}]*)\}/g;
  let m;
  while ((m = re.exec(stripped))) {
    const selector = m[1].trim();
    const decls = m[2].split(';').map(s => s.trim()).filter(Boolean).map(d => {
      const i = d.indexOf(':');
      return { name: d.slice(0, i).trim(), value: d.slice(i + 1).trim() };
    });
    blocks.push({ selector, decls });
  }
  return blocks;
}

const HEX = /^#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8}|[0-9A-Fa-f]{3,4})$/;
const LENGTH = /^(?:0|-?\d+(?:\.\d+)?px)$/;
const NUMBER = /^-?\d+(?:\.\d+)?$/;
const QUOTED = /^"(?:[^"\\]|\\.)*"$/;
const FONT_LIST = /^"(?:[^"\\]|\\.)*"(?:,\s*(?:"(?:[^"\\]|\\.)*"|[A-Za-z][\w-]*))*$/;
const GRADIENT = /^linear-gradient\(\d+deg(?:,\s*#[0-9A-Fa-f]{6,8}\s+\d+%){3}\)$/;
const IDENT = /^[a-zA-Z][\w-]*$/;
const TRANSFORM = /^(?:scaleX\(-?1\)|rotate\(\d+deg\))$/;

/** Classify a --azmx-* property by name so the validator knows what to expect. */
function expectedKind(name) {
  const n = name.replace(/^--azmx-/, '');
  if (n === 'gradient') return 'gradient';
  if (n.startsWith('font-stack-')) return 'font-list';
  if (n.startsWith('font-family-') || n === 'font-heading' || n === 'font-text') return 'quoted';
  if (n.startsWith('font-weight-') || n.startsWith('weight-')) return 'weight';
  if (n.startsWith('size-opacity-') || n.startsWith('opacity-')) return 'number';
  if (/^(size-(space|font|line|radius|border|icon|doc|tracking)|space|radius|border-width|icon-size|slide|type-|logo-height|logo-clear-space|card-radius|card-padding|meter-radius|meter-height|star-tile-radius)/.test(n)
      && !/^border-(inline|block)-/.test(n) && !/^radius-(start|end)-/.test(n)) return 'length';
  if (/^(quote|chevron|arrow)-/.test(n)) return 'quoted';
  if (/^transform-/.test(n)) return 'transform';
  if (/^(direction|align|float|margin|padding|border-(inline|block)|inset|radius-(start|end))-/.test(n)) return 'ident';
  return 'color';
}

function isValid(kind, value) {
  switch (kind) {
    case 'gradient':  return GRADIENT.test(value);
    case 'font-list': return FONT_LIST.test(value);
    case 'quoted':    return QUOTED.test(value);
    case 'weight':    return NUMBER.test(value) && Number(value) >= 1 && Number(value) <= 1000;
    case 'number':    return NUMBER.test(value);
    case 'length':    return LENGTH.test(value);
    case 'ident':     return IDENT.test(value);
    case 'transform': return TRANSFORM.test(value);
    case 'color':     return HEX.test(value);
    default:          return false;
  }
}

// ---- module exports ----

describe('tokens-to-css.mjs exports', () => {
  it('importing the module has no side effects (nothing printed, no exit code)', () => {
    // A subprocess that only imports the module must print nothing to stdout.
    const out = execFileSync(process.execPath, ['--input-type=module', '-e',
      `import(${JSON.stringify(SCRIPT)}).then(m => process.stdout.write(String(typeof m.resolve)))`],
      { encoding: 'utf8' });
    expect(out).toBe('function');
  });

  it('exports resolve/resolveAll with their historical signatures', () => {
    expect(resolve('@size/space/16', 0, 0)).toBe(16);
    expect(resolve('#123456', 0, 0)).toBe('#123456');
    const all = resolveAll(0, 0);
    expect(all['space/md']).toBe(64);
    expect(all['text/primary']).toMatch(HEX);
  });

  it('loadTokens accepts a custom path and resolve/resolveAll accept a context', () => {
    const fx = loadTokens(join(HERE, 'fixtures', 'sample-tokens.json'));
    expect(fx.PALETTES).toEqual(['blue', 'orange', 'green']);
    expect(resolve('@color/primary/electric', 0, 0, 0, fx)).toBe('#001AFF');
    expect(Object.keys(resolveAll(0, 0, fx)).length).toBeGreaterThan(0);
  });

  it('resolveWithSource reports the terminal primitive', () => {
    expect(resolveWithSource('@space/md', 0, 0)).toEqual({ value: 64, primitive: 'size/space/64' });
    expect(resolveWithSource('@card/padding', 0, 0)).toEqual({ value: 24, primitive: 'size/space/24' });
    expect(resolveWithSource('left', 0, 0)).toEqual({ value: 'left', primitive: null });
  });

  it('throws on broken aliases and on missing mode values instead of yielding undefined', () => {
    expect(() => resolve('@nope/missing', 0, 0)).toThrow(/unknown token/);
    expect(() => resolve('@accent/base', 99, 0)).toThrow(/no value for mode index/);
    expect(() => cssValue(undefined, 'size/space/16')).toThrow(/undefined/);
  });
});

// ---- units ----

describe('unit rules', () => {
  it('lengths get px, opacity stays unitless, decided by the primitive', () => {
    expect(cssValue(16, 'size/space/16')).toBe('16px');
    expect(cssValue(0, 'size/space/0')).toBe('0');
    expect(cssValue(0.5, 'size/border/0-5')).toBe('0.5px');
    expect(cssValue(2, 'size/tracking/2')).toBe('2px');
    expect(cssValue(28, 'size/line/28')).toBe('28px');
    expect(cssValue(1920, 'size/doc/1920')).toBe('1920px');
    expect(cssValue(0.4, 'size/opacity/40')).toBe('0.4');
    expect(cssValue(16, null)).toBe('16');
    expect(unitFor('size/icon/24')).toBe('px');
    expect(unitFor('color/blue/600')).toBeNull();
  });

  it('semantic and component aliases inherit the unit of their primitive', () => {
    const css = resolveAllCss(0, 0);
    expect(css['space/md']).toBe('64px');
    expect(css['type/body/md/size']).toBe('18px');
    expect(css['type/body/md/line']).toBe('28px');
    expect(css['type/tracking/wide']).toBe('2px');
    expect(css['radius/pill']).toBe('9999px');
    expect(css['border-width/thin']).toBe('0.5px');
    expect(css['icon/size/inline']).toBe('20px');
    expect(css['opacity/muted']).toBe('0.4');
    expect(css['card/padding']).toBe('24px');
    expect(css['meter/height']).toBe('8px');
    expect(css['slide/width']).toBe('1920px');
  });

  it('string values from another token file are left untouched', () => {
    const fx = loadTokens(join(HERE, 'fixtures', 'sample-tokens.json'));
    const { value, primitive } = resolveWithSource('@spacing/md', 0, 0, 0, fx);
    expect(cssValue(value, primitive)).toBe('16px');
  });

  it('exposes the rule table for other generators', () => {
    expect(UNIT_RULES['size/space/']).toBe('px');
    expect(UNIT_RULES['size/opacity/']).toBe('number');
    expect(FONT_WEIGHTS.regular).toBe(400);
  });
});

// ---- font weights ----

describe('font weights', () => {
  it('maps Figma style names to CSS weights, case- and separator-insensitively', () => {
    const cases = {
      Thin: 100, 'Extra Light': 200, 'extra-light': 200, UltraLight: 200, Light: 300,
      Regular: 400, normal: 400, Medium: 500, SemiBold: 600, 'Demi Bold': 600,
      Bold: 700, ExtraBold: 800, UltraBold: 800, Black: 900, Heavy: 900, '700': 700,
    };
    for (const [name, w] of Object.entries(cases)) expect(fontWeight(name), name).toBe(w);
    expect(fontWeight('Wobbly')).toBeNull();
  });

  it('emits numeric weights for every weight token', () => {
    const css = resolveAllCss(0, 0);
    expect(css['weight/regular']).toBe('400');
    expect(css['weight/semibold']).toBe('600');
    expect(css['weight/heavy']).toBe('900');
    expect(cssValue('Bold', 'font/weight/bold')).toBe('700');
  });

  it('keeps an unknown weight name raw and warns on stderr', () => {
    const calls = [];
    const orig = console.error;
    console.error = (...a) => calls.push(a.join(' '));
    try {
      expect(cssValue('Wobbly', 'font/weight/wobbly')).toBe('Wobbly');
    } finally { console.error = orig; }
    expect(calls.some(l => /unknown font weight/.test(l))).toBe(true);
  });
});

// ---- duplicates, fonts, RTL ----

describe('generated stylesheet', () => {
  const blocks = parseBlocks(CSS);
  const rootDecls = blocks.filter(b => b.selector.split(',').map(s => s.trim()).includes(':root')).flatMap(b => b.decls);

  it('declares no custom property twice in the :root scope', () => {
    const seen = new Map();
    for (const { name } of rootDecls) seen.set(name, (seen.get(name) || 0) + 1);
    const dupes = [...seen].filter(([, n]) => n > 1).map(([k]) => k);
    expect(dupes).toEqual([]);
  });

  it('declares no custom property twice inside any single block', () => {
    for (const b of blocks) {
      const names = b.decls.map(d => d.name);
      expect(new Set(names).size, b.selector).toBe(names.length);
    }
  });

  it('keeps the semantic font tokens and names the stacks --azmx-font-stack-*', () => {
    const byName = Object.fromEntries(rootDecls.map(d => [d.name, d.value]));
    expect(byName['--azmx-font-heading']).toBe('"thmanyah serif display"');
    expect(byName['--azmx-font-text']).toBe('"Azm X Variable"');
    expect(byName['--azmx-font-stack-heading']).toBe('"thmanyah serif display", Georgia, serif');
    expect(byName['--azmx-font-stack-text']).toBe('"Azm X Variable", system-ui, sans-serif');
  });

  it('emits the RTL collection under :root/[dir="ltr"] and [dir="rtl"]', () => {
    const rtlCount = Object.keys(CTX.rtl).length;
    expect(rtlCount).toBe(37);
    const ltrBlock = blocks.find(b => b.selector === ':root, [dir="ltr"]');
    const rtlBlock = blocks.find(b => b.selector === '[dir="rtl"]');
    expect(ltrBlock, 'ltr block').toBeDefined();
    expect(rtlBlock, 'rtl block').toBeDefined();
    expect(ltrBlock.decls.length).toBe(rtlCount);
    expect(rtlBlock.decls.length).toBe(rtlCount);
    const ltr = Object.fromEntries(ltrBlock.decls.map(d => [d.name, d.value]));
    const rtl = Object.fromEntries(rtlBlock.decls.map(d => [d.name, d.value]));
    expect(ltr['--azmx-direction-value']).toBe('ltr');
    expect(rtl['--azmx-direction-value']).toBe('rtl');
    expect(ltr['--azmx-align-start']).toBe('left');
    expect(rtl['--azmx-align-start']).toBe('right');
    expect(ltr['--azmx-quote-open']).toBe('"\\""');
    expect(rtl['--azmx-quote-open']).toBe('"«"');
    expect(rtl['--azmx-transform-flip-x']).toBe('scaleX(-1)');
    expect(resolveRtl(1)['arrow/forward']).toBe('"←"');
  });

  it('never emits the word undefined', () => {
    expect(CSS).not.toMatch(/\bundefined\b/);
  });

  it('every --azmx-* declaration is a valid CSS value for its type', () => {
    const bad = [];
    let checked = 0;
    for (const b of blocks) for (const { name, value } of b.decls) {
      expect(name).toMatch(/^--azmx-[a-z0-9-]+$/);
      const kind = expectedKind(name);
      checked += 1;
      if (!isValid(kind, value)) bad.push(`${b.selector} ${name}: ${value} (expected ${kind})`);
    }
    expect(checked).toBeGreaterThan(1500);
    expect(bad).toEqual([]);
  });

  it('carries units for every numeric length primitive (no bare numbers except 0 / opacity / weight)', () => {
    const bare = rootDecls.filter(d => NUMBER.test(d.value) && d.value !== '0')
      .filter(d => !/^--azmx-(size-opacity|opacity|font-weight|weight)-/.test(d.name));
    expect(bare.map(d => `${d.name}: ${d.value}`)).toEqual([]);
  });

  it('single-combination output also carries units and direction tokens', () => {
    const one = generateSingleCss(1, 1, CTX);
    expect(one).toContain('--azmx-space-md: 64px;');
    expect(one).toContain('--azmx-weight-bold: 700;');
    expect(one).toContain('[dir="rtl"]');
  });

  it('CLI output matches the module output and the committed azmx-tokens.css', () => {
    const cli = execFileSync(process.execPath, [SCRIPT], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    expect(cli.trimEnd()).toBe(CSS.trimEnd());
    const committed = readFileSync(join(ROOT, 'azmx-tokens.css'), 'utf8');
    expect(committed.trimEnd()).toBe(CSS.trimEnd());
  });
});

// ---- validation ----

describe('validation', () => {
  it('the real token file validates cleanly', () => {
    const r = validateTokens(CTX);
    expect(r.ok).toBe(true);
    expect(r.duplicateNames).toEqual([]);
  });

  it('CLI refuses to generate from a broken token file', () => {
    // Break one alias in a temp copy and point the loader at it via a wrapper script.
    const dir = mkdtempSync(join(tmpdir(), 'azmx-tokens-'));
    const data = JSON.parse(readFileSync(join(ROOT, 'assets', 'tokens', 'azmx-tokens.json'), 'utf8'));
    data['2. Semantic'].tokens['text/primary'][0] = '@does/not/exist';
    const broken = join(dir, 'broken.json');
    writeFileSync(broken, JSON.stringify(data));
    const r = validateTokens(loadTokens(broken));
    expect(r.ok).toBe(false);
    expect(r.brokenAliases.some(e => e.token === 'text/primary')).toBe(true);
  });

  it('detects the same token name declared in two collections', () => {
    const dir = mkdtempSync(join(tmpdir(), 'azmx-tokens-'));
    const data = JSON.parse(readFileSync(join(ROOT, 'assets', 'tokens', 'azmx-tokens.json'), 'utf8'));
    data['3. Component'].tokens['space/md'] = '@size/space/16';
    data['3. Component'].count += 1;
    const dup = join(dir, 'dup.json');
    writeFileSync(dup, JSON.stringify(data));
    const ctx = loadTokens(dup);
    expect(validateTokens(ctx).duplicateNames).toEqual([{ token: 'space/md', tiers: ['2. Semantic', '3. Component'] }]);
    expect(() => generateCss(ctx)).toThrow(/duplicate custom property --azmx-space-md/);
  });
});

// ---- explorer ----

describe('token explorer', () => {
  it('shows the same unit-bearing values as the stylesheet and labels RTL modes LTR / RTL', () => {
    const html = execFileSync(process.execPath, [EXPLORER], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
    expect(html).toContain('token-value">64px<');
    expect(html).toContain('token-value">18px<');
    expect(html).toContain('token-value">400<');
    expect(html).not.toMatch(/token-value">Regular</);
    expect(html).toContain('"directions":["ltr","rtl"]');
    expect(html).toContain('"unitRules":');
    expect(html).toContain("direction.toUpperCase()");
  });
});
