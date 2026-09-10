/**
 * Tests for scripts/tokens-to-css.mjs
 *
 * Two layers:
 *
 *   1. Unit tests import `resolve` / `resolveAll` straight from the script and
 *      exercise them against the committed assets/tokens/azmx-tokens.json —
 *      the exact code and data the CLI uses. Nothing is re-implemented here.
 *      The script exports `resolve`/`resolveAll` (raw values), `resolveAllCss`
 *      (CSS strings with units), `resolveRtl`, `resolveWithSource`, `cssValue`
 *      and `loadTokens(path)` (a context for fixture data), and only runs its
 *      CLI when executed directly (import.meta.url main guard).
 *
 *      Units: a resolved value's unit is decided by the terminal primitive —
 *      size/* → px (0 stays "0"), font/weight/* names → numeric weights,
 *      font/family/* → quoted strings, colours verbatim.
 *
 *   2. CLI tests spawn the script the way the README documents
 *      (`node scripts/tokens-to-css.mjs ...`) and check the emitted CSS / JSON,
 *      cross-checking the JSON against resolveAll() so the two paths agree.
 */

import { describe, it, expect } from 'vitest';
import { readFileSync, writeFileSync, copyFileSync, mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';

import { resolve, resolveAll, resolveAllCss, resolveRtl, resolveWithSource, cssValue, loadTokens } from '../scripts/tokens-to-css.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, '..');
const SCRIPTS_DIR = join(REPO_ROOT, 'scripts');
const SCRIPT_PATH = join(SCRIPTS_DIR, 'tokens-to-css.mjs');
const TOKENS_PATH = join(REPO_ROOT, 'assets', 'tokens', 'azmx-tokens.json');

// The same data file the script loads — used only to enumerate names/modes and
// to read literal primitive values, never to resolve anything.
const DATA = JSON.parse(readFileSync(TOKENS_PATH, 'utf8'));
const PALETTES = DATA['1b. Palette'].modes.map(m => m.toLowerCase());
const THEMES = DATA['2. Semantic'].modes.map(m => m.toLowerCase());
const DIRECTIONS = DATA.RTL.modes.map(m => m.toLowerCase());
const prim = DATA['1. Primitives'].tokens;
const pal = DATA['1b. Palette'].tokens;
const sem = DATA['2. Semantic'].tokens;
const comp = DATA['3. Component'].tokens;
const canv = DATA['4. Canvas'].tokens;

const BLUE = PALETTES.indexOf('blue');
const ORANGE = PALETTES.indexOf('orange');
const LIGHT = THEMES.indexOf('light');
const DARK = THEMES.indexOf('dark');

function runScript(args = []) {
  return execFileSync(process.execPath, [SCRIPT_PATH, ...args], {
    cwd: SCRIPTS_DIR,
    encoding: 'utf8',
    timeout: 10000,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
}

describe('tokens-to-css.mjs - module exports', () => {
  it('exports resolve() and resolveAll() as functions', () => {
    expect(typeof resolve).toBe('function');
    expect(typeof resolveAll).toBe('function');
  });

  it('importing the module does not run the CLI (no output, no exit code)', () => {
    // If the main guard were missing, importing would have printed the whole
    // stylesheet to stdout and possibly set process.exitCode. The import at the
    // top of this file already happened; assert its side effects are absent.
    expect(process.exitCode === undefined || process.exitCode === 0).toBe(true);
  });
});

describe('tokens-to-css.mjs - resolve()', () => {
  describe('primitives and literals', () => {
    it('resolves a primitive colour to its literal', () => {
      expect(resolve('@color/blue/50', BLUE, LIGHT)).toBe(prim['color/blue/50']);
      expect(resolve('@color/blue/50', BLUE, LIGHT)).toBe('#F0F5FF');
    });

    it('resolves a numeric primitive without stringifying it', () => {
      expect(resolve('@size/space/8', BLUE, LIGHT)).toBe(8);
      expect(typeof resolve('@size/space/8', BLUE, LIGHT)).toBe('number');
    });

    it('resolves a string primitive (font family)', () => {
      expect(resolve('@font/family/display', BLUE, LIGHT)).toBe(prim['font/family/display']);
    });

    it('returns non-reference values unchanged', () => {
      expect(resolve('#FF0000', BLUE, LIGHT)).toBe('#FF0000');
      expect(resolve('16px', BLUE, LIGHT)).toBe('16px');
      expect(resolve(42, BLUE, LIGHT)).toBe(42);
      expect(resolve(null, BLUE, LIGHT)).toBe(null);
      expect(resolve('plain-string', BLUE, LIGHT)).toBe('plain-string');
    });

    it('refuses an undefined reference instead of yielding undefined', () => {
      expect(() => resolve(undefined, BLUE, LIGHT)).toThrow(/unresolved value \(undefined\)/);
    });

    it('reports the terminal primitive alongside the raw value', () => {
      expect(resolveWithSource('@slide/width', BLUE, LIGHT)).toEqual({ value: 1920, primitive: 'size/doc/1920' });
      expect(resolveWithSource('@card/padding', BLUE, LIGHT)).toEqual({ value: 24, primitive: 'size/space/24' });
      expect(resolveWithSource('@text/primary', BLUE, LIGHT)).toEqual({ value: '#111927', primitive: 'color/neutral/900' });
      expect(resolveWithSource('#ABCDEF', BLUE, LIGHT)).toEqual({ value: '#ABCDEF', primitive: null });
    });

    it('formats values with the unit the terminal primitive implies', () => {
      expect(cssValue(1920, 'size/doc/1920')).toBe('1920px');
      expect(cssValue(0, 'size/space/0')).toBe('0');
      expect(cssValue('Regular', 'font/weight/regular')).toBe('400');
      expect(cssValue('Bold', 'font/weight/bold')).toBe('700');
      expect(cssValue('thmanyah serif display', 'font/family/display')).toBe('"thmanyah serif display"');
      expect(cssValue(0.5, 'size/opacity/50')).toBe('0.5');
      expect(cssValue('#111927', 'color/neutral/900')).toBe('#111927');
      expect(cssValue('#111927', null)).toBe('#111927');
    });

    it('primitives ignore the palette and theme indices', () => {
      PALETTES.forEach((_, p) => THEMES.forEach((__, t) => {
        expect(resolve('@color/base/white', p, t)).toBe('#FFFFFF');
      }));
    });
  });

  describe('palette tokens (one value per palette)', () => {
    it('picks the value for the requested palette index', () => {
      PALETTES.forEach((palette, p) => {
        const expected = prim[pal['accent/base'][p].slice(1)];
        expect(resolve('@accent/base', p, LIGHT)).toBe(expected);
      });
    });

    it('resolves blue and orange accent/base to different primitives', () => {
      expect(resolve('@accent/base', BLUE, LIGHT)).toBe('#001AFF');
      expect(resolve('@accent/base', ORANGE, LIGHT)).toBe('#F47A48');
    });

    it('palette tokens ignore the theme index', () => {
      expect(resolve('@accent/base', ORANGE, LIGHT)).toBe(resolve('@accent/base', ORANGE, DARK));
    });
  });

  describe('semantic tokens (one value per theme)', () => {
    it('resolves text/primary for light and dark', () => {
      expect(resolve('@text/primary', BLUE, LIGHT)).toBe('#111927');
      expect(resolve('@text/primary', BLUE, DARK)).toBe('#FFFFFF');
    });

    it('semantic -> palette -> primitive chain follows both indices', () => {
      // surface/accent is [@accent/base, @accent/on-dark]
      expect(resolve('@surface/accent', BLUE, LIGHT)).toBe('#001AFF');
      expect(resolve('@surface/accent', ORANGE, DARK)).toBe('#F79A74');
      expect(resolve('@surface/accent', ORANGE, DARK)).toBe(resolve('@accent/on-dark', ORANGE, DARK));
    });

    it('semantic token whose light value is a primitive alias', () => {
      expect(resolve('@surface/page', BLUE, LIGHT)).toBe('#FFFFFF');
      expect(resolve('@surface/page', ORANGE, DARK)).toBe('#2E170E');
    });
  });

  describe('component and canvas tokens (single mode)', () => {
    it('component token resolves through semantic to palette', () => {
      // card/surface -> @surface/raised -> [@accent/tint, @accent/deep]
      expect(resolve('@card/surface', BLUE, LIGHT)).toBe('#F0F5FF');
      expect(resolve('@card/surface', ORANGE, DARK)).toBe('#5A2D1B');
      expect(resolve('@card/surface', BLUE, LIGHT)).toBe(resolve('@surface/raised', BLUE, LIGHT));
    });

    it('canvas token resolves to a numeric primitive', () => {
      expect(resolve('@slide/width', BLUE, LIGHT)).toBe(1920);
      expect(resolve('@slide/height', BLUE, LIGHT)).toBe(1080);
    });
  });

  describe('errors', () => {
    it('throws for an unknown token name', () => {
      expect(() => resolve('@unknown/token', BLUE, LIGHT)).toThrow('unknown token: unknown/token');
    });

    // Cycle / depth-guard behaviour needs a broken token file; see the
    // "fixture harness" block below, which runs the real script against one.
  });

  describe('every combination', () => {
    it('resolves every semantic token to a literal for all palette/theme pairs', () => {
      PALETTES.forEach((_, p) => THEMES.forEach((__, t) => {
        for (const name of Object.keys(sem)) {
          const v = resolve('@' + name, p, t);
          expect(typeof v === 'string' && v.startsWith('@')).toBe(false);
          expect(v).not.toBeUndefined();
        }
      }));
    });
  });
});

describe('tokens-to-css.mjs - resolveAll()', () => {
  it('returns every semantic, component and canvas token and nothing else', () => {
    const result = resolveAll(BLUE, LIGHT);
    const expectedKeys = [...Object.keys(sem), ...Object.keys(comp), ...Object.keys(canv)].sort();
    expect(Object.keys(result).sort()).toEqual(expectedKeys);
    for (const primName of Object.keys(prim)) expect(result).not.toHaveProperty(primName);
    for (const palName of Object.keys(pal)) expect(result).not.toHaveProperty(palName);
  });

  it('never leaves an unresolved alias in any combination', () => {
    PALETTES.forEach((_, p) => THEMES.forEach((__, t) => {
      const result = resolveAll(p, t);
      for (const [name, v] of Object.entries(result)) {
        expect(v, `${name} @ ${PALETTES[p]}/${THEMES[t]}`).not.toBeUndefined();
        if (typeof v === 'string') expect(v.startsWith('@'), `${name} unresolved: ${v}`).toBe(false);
      }
    }));
  });

  it('agrees with resolve() token by token', () => {
    const result = resolveAll(ORANGE, DARK);
    for (const name of Object.keys(result)) {
      expect(result[name]).toBe(resolve('@' + name, ORANGE, DARK));
    }
  });

  it('blue/light values match the house look', () => {
    const r = resolveAll(BLUE, LIGHT);
    expect(r['text/primary']).toBe('#111927');
    expect(r['surface/page']).toBe('#FFFFFF');
    expect(r['surface/accent']).toBe('#001AFF');
    expect(r['card/surface']).toBe('#F0F5FF');
    expect(r['slide/width']).toBe(1920);
  });

  it('theme changes semantic values; palette changes accent values', () => {
    const blueLight = resolveAll(BLUE, LIGHT);
    const blueDark = resolveAll(BLUE, DARK);
    const orangeLight = resolveAll(ORANGE, LIGHT);
    expect(blueLight['text/primary']).not.toBe(blueDark['text/primary']);
    expect(blueLight['surface/accent']).not.toBe(orangeLight['surface/accent']);
    // canvas sizes are palette- and theme-independent
    expect(blueLight['slide/width']).toBe(orangeLight['slide/width']);
    expect(blueLight['slide/width']).toBe(blueDark['slide/width']);
  });
});

describe('tokens-to-css.mjs - CLI integration', () => {
  it('--json --palette --theme output equals resolveAll() for that combination', () => {
    const data = JSON.parse(runScript(['--json', '--palette', 'orange', '--theme', 'dark']));
    expect(data).toEqual(resolveAll(ORANGE, DARK));
  });

  it('--json alone emits every palette/theme combination plus both RTL directions', () => {
    const data = JSON.parse(runScript(['--json']));
    const expectedKeys = [];
    PALETTES.forEach(pn => THEMES.forEach(tn => expectedKeys.push(`${pn}/${tn}`)));
    DIRECTIONS.forEach(dn => expectedKeys.push(`direction/${dn}`));
    expect(Object.keys(data).sort()).toEqual(expectedKeys.sort());
    PALETTES.forEach((pn, p) => THEMES.forEach((tn, t) => {
      expect(data[`${pn}/${tn}`]).toEqual(resolveAll(p, t));
    }));
    DIRECTIONS.forEach((dn, d) => expect(data[`direction/${dn}`]).toEqual(resolveRtl(d)));
    // raw JSON keeps numbers unitless; the RTL trees carry real direction values
    expect(data['blue/light']['slide/width']).toBe(1920);
    expect(data['direction/ltr']['align/text']).toBe('left');
    expect(data['direction/rtl']['align/text']).toBe('right');
    expect(data['direction/ltr']['direction/value']).toBe('ltr');
    expect(data['direction/rtl']['direction/value']).toBe('rtl');
  });

  it('default output carries the header, primitives, base block and attribute overrides', () => {
    const output = runScript();
    expect(output).toContain(`AZM X Design Tokens v${DATA.$meta.version}`);
    expect(output).toContain('/* Primitives');
    expect(output).toContain('/* Semantic — blue / light */');
    expect(output).toContain('[data-palette="orange"]');
    expect(output).toContain('[data-theme="dark"]');
    expect(output).toContain('[data-palette="orange"][data-theme="dark"]');
    expect(output).toContain('--azmx-gradient: linear-gradient(');
    expect(output).toContain('--azmx-font-heading');
    expect(output).toContain('--azmx-font-text');
  });

  it('default output matches the committed azmx-tokens.css byte for byte', () => {
    const committed = readFileSync(join(REPO_ROOT, 'azmx-tokens.css'), 'utf8');
    expect(runScript()).toBe(committed);
  });

  it('base :root block contains the resolved blue/light values, with units', () => {
    const output = runScript();
    const base = resolveAllCss(BLUE, LIGHT);
    expect(output).toContain(`  --azmx-text-primary: ${base['text/primary']};`);
    expect(output).toContain(`  --azmx-surface-accent: ${base['surface/accent']};`);
    expect(output).toContain(`  --azmx-slide-width: ${base['slide/width']};`);
    // literal expectations so a regression in cssValue cannot hide behind resolveAllCss
    expect(output).toContain('  --azmx-text-primary: #111927;');
    expect(output).toContain('  --azmx-surface-accent: #001AFF;');
    expect(output).toContain('  --azmx-slide-width: 1920px;');
    expect(output).toContain('  --azmx-slide-height: 1080px;');
    expect(output).toContain('  --azmx-card-padding: 24px;');
    expect(output).toContain('  --azmx-weight-regular: 400;');
    expect(output).toContain('  --azmx-weight-bold: 700;');
    expect(output).toContain('  --azmx-font-family-display: "thmanyah serif display";');
    expect(output).toContain('  --azmx-font-family-body: "Azm X Variable";');
    // no unitless lengths or raw weight names leaked through
    expect(output).not.toMatch(/--azmx-slide-width: 1920;/);
    expect(output).not.toMatch(/--azmx-weight-[a-z]+: [A-Z]/);
  });

  it('emits RTL as a :root/[dir="ltr"] block and a [dir="rtl"] override block', () => {
    const output = runScript();
    const ltr = output.split(':root, [dir="ltr"] {')[1].split('}')[0];
    const rtl = output.split('[dir="rtl"] {')[1].split('}')[0];
    expect(ltr).toContain('--azmx-align-text: left;');
    expect(ltr).toContain('--azmx-direction-value: ltr;');
    expect(rtl).toContain('--azmx-align-text: right;');
    expect(rtl).toContain('--azmx-direction-value: rtl;');
    const ltrVals = resolveRtl(DIRECTIONS.indexOf('ltr'));
    for (const [name, value] of Object.entries(ltrVals)) expect(ltr).toContain(`--azmx-${name.replace(/\//g, '-')}: ${value};`);
  });

  it('[data-palette="orange"] block only lists tokens that differ from blue/light', () => {
    const output = runScript();
    const base = resolveAllCss(BLUE, LIGHT);
    const orange = resolveAllCss(ORANGE, LIGHT);
    const block = output.split('[data-palette="orange"] {')[1].split('}')[0];
    const lines = block.trim().split('\n').map(l => l.trim()).filter(Boolean);
    expect(lines.length).toBeGreaterThan(0);
    for (const line of lines) {
      const [, cssName, value] = line.match(/^--azmx-([\w-]+): (.+);$/);
      const tokenName = Object.keys(orange).find(n => n.replace(/\//g, '-') === cssName);
      expect(tokenName, `unknown variable --azmx-${cssName}`).toBeDefined();
      expect(orange[tokenName]).toBe(value);
      expect(base[tokenName]).not.toBe(value);
    }
    expect(output).not.toContain('--azmx-text/primary');
  });

  it('single-combination output flattens one palette/theme into :root', () => {
    const output = runScript(['--palette', 'orange', '--theme', 'dark']);
    const vals = resolveAllCss(ORANGE, DARK);
    expect(output).toContain('AZM X tokens — orange / dark');
    expect(output).toContain(':root {');
    expect(output).not.toContain('[data-palette=');
    expect(output).toContain(`  --azmx-surface-page: ${vals['surface/page']};`);
    expect(output).toContain('  --azmx-surface-page: #2E170E;');
    expect(output).toContain('  --azmx-slide-width: 1920px;');
    // the first :root block carries exactly one declaration per resolved token
    const rootBlock = output.split(':root {')[1].split('}')[0];
    const propertyLines = rootBlock.split('\n').filter(l => l.trim().startsWith('--azmx-'));
    expect(propertyLines.length).toBe(Object.keys(vals).length);
    propertyLines.forEach(line => {
      const [, cssName, value] = line.match(/^\s*--azmx-([\w-]+):\s*(.+);$/);
      const tokenName = Object.keys(vals).find(n => n.replace(/\//g, '-') === cssName);
      expect(tokenName, `unknown variable --azmx-${cssName}`).toBeDefined();
      expect(value).toBe(vals[tokenName]);
    });
    // and the RTL blocks follow it
    expect(output).toContain(':root, [dir="ltr"] {');
    expect(output).toContain('[dir="rtl"] {');
  });

  it('--palette alone defaults theme to light; --theme alone defaults palette to blue', () => {
    expect(runScript(['--palette', 'green'])).toContain('green / light');
    expect(runScript(['--theme', 'dark'])).toContain('blue / dark');
  });

  it('rejects an unknown palette or theme with a non-zero exit', () => {
    expect(() => runScript(['--palette', 'unknown'])).toThrow(/unknown palette/);
    expect(() => runScript(['--theme', 'unknown'])).toThrow(/unknown theme/);
  });

  it('--validate passes on the committed token file', () => {
    // stderr carries the summary; a non-zero exit would throw.
    const result = execFileSync(process.execPath, [SCRIPT_PATH, '--validate'], {
      cwd: SCRIPTS_DIR, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
    });
    expect(result).toBe('');
  });
});

describe('tokens-to-css.mjs - fixture harness (real script, broken token files)', () => {
  // The script locates its data as <script dir>/../assets/tokens/azmx-tokens.json.
  // Copying the script verbatim next to a fixture is the only way to feed it
  // other data without editing it, so these tests still run the real code.
  // Validation now runs before anything is generated, so the fixture must carry
  // the metadata the validator insists on (modes on every tier, counts matching).
  function wellFormed(f) {
    for (const tier of ['1. Primitives', '3. Component', '4. Canvas']) f[tier].modes = f[tier].modes || ['Mode 1'];
    return f;
  }
  function recount(f) {
    for (const tier of Object.values(f)) if (tier && tier.tokens && tier.count !== -1) tier.count = Object.keys(tier.tokens).length;
    return f;
  }

  function harness(mutate) {
    const dir = mkdtempSync(join(tmpdir(), 'azmx-tokens-'));
    mkdirSync(join(dir, 'scripts'), { recursive: true });
    mkdirSync(join(dir, 'assets', 'tokens'), { recursive: true });
    copyFileSync(SCRIPT_PATH, join(dir, 'scripts', 'tokens-to-css.mjs'));
    const fixture = wellFormed(JSON.parse(readFileSync(join(HERE, 'fixtures', 'sample-tokens.json'), 'utf8')));
    mutate(fixture);
    recount(fixture);
    writeFileSync(join(dir, 'assets', 'tokens', 'azmx-tokens.json'), JSON.stringify(fixture));
    const run = (args) => {
      const r = spawnSync(process.execPath, [join(dir, 'scripts', 'tokens-to-css.mjs'), ...args], {
        encoding: 'utf8', timeout: 10000,
      });
      return { code: r.status, stdout: r.stdout || '', stderr: r.stderr || '' };
    };
    return { run, cleanup: () => rmSync(dir, { recursive: true, force: true }) };
  }

  it('resolves the sample fixture (3 palettes x 2 themes) through the real CLI', () => {
    const h = harness(() => {});
    try {
      const r = h.run(['--json']);
      expect(r.code, r.stderr).toBe(0);
      const data = JSON.parse(r.stdout);
      // the fixture has no RTL collection, so no direction/* keys
      expect(Object.keys(data).sort()).toEqual(
        ['blue/dark', 'blue/light', 'green/dark', 'green/light', 'orange/dark', 'orange/light']);
      expect(data['blue/light']['text/primary']).toBe('#111927');
      expect(data['blue/dark']['text/primary']).toBe('#FFFFFF');
      expect(data['orange/light']['button/background']).toBe('#F47A48');
      expect(data['green/light']['button/background']).toBe('#22C36F');
      expect(data['blue/dark']['canvas/background']).toBe('#040038');

      const css = h.run(['--palette', 'orange', '--theme', 'dark']);
      expect(css.code, css.stderr).toBe(0);
      expect(css.stdout).toContain('/* AZM X tokens — orange / dark — v1.0.0-test */');
      expect(css.stdout).toContain('  --azmx-button-background: #F47A48;');
      expect(css.stdout).toContain('  --azmx-text-primary: #FFFFFF;');
      expect(css.stdout).not.toContain('[dir="rtl"]');
    } finally { h.cleanup(); }
  });

  it('loadTokens(path) gives resolve()/resolveAll() a fixture context without touching the real data', () => {
    const fx = loadTokens(join(HERE, 'fixtures', 'sample-tokens.json'));
    expect(fx.PALETTES).toEqual(['blue', 'orange', 'green']);
    expect(fx.THEMES).toEqual(['light', 'dark']);
    expect(resolve('@color/primary/electric', 0, 0, 0, fx)).toBe('#001AFF');
    expect(resolve('@spacing/md', 0, 0, 0, fx)).toBe('16px');   // fixture primitive is already a string
    expect(resolve('@surface/accent', 1, 0, 0, fx)).toBe('#F47A48');
    expect(resolve('@text/accent', 0, 1, 0, fx)).toBe('#5D8FFF');
    expect(resolveAll(2, 0, fx)).toMatchObject({ 'button/background': '#22C36F', 'canvas/text': '#111927' });
    expect(Object.keys(resolveAll(0, 0, fx)).sort()).toEqual(
      [...Object.keys(fx.sem), ...Object.keys(fx.comp), ...Object.keys(fx.canv)].sort());
    // the default context is untouched: the same reference is unknown in the real data
    expect(() => resolve('@color/primary/electric', BLUE, LIGHT)).toThrow(/unknown token/);
    expect(resolve('@slide/width', BLUE, LIGHT)).toBe(1920);
  });

  it('reports an alias loop and exits non-zero when tokens reference each other', () => {
    const h = harness(f => {
      f['3. Component'].tokens['loop/a'] = '@loop/b';
      f['3. Component'].tokens['loop/b'] = '@loop/a';
    });
    try {
      // validation runs first: the report is printed, nothing is generated
      const r = h.run(['--json', '--palette', 'blue', '--theme', 'light']);
      expect(r.code).toBe(1);
      expect(r.stdout).toBe('');
      expect(r.stderr).toContain('Circular references detected:');
      expect(r.stderr).toMatch(/3\. Component\/loop\/a \[blue\/light\/default\]: alias loop at loop\/a/);
      expect(r.stderr).toContain('Nothing generated: fix the token file (see --validate).');
    } finally { h.cleanup(); }
  });

  it('reports an unknown token and exits non-zero for a dangling alias', () => {
    const h = harness(f => { f['3. Component'].tokens['dangling'] = '@does/not/exist'; });
    try {
      const r = h.run(['--json', '--palette', 'blue', '--theme', 'light']);
      expect(r.code).toBe(1);
      expect(r.stdout).toBe('');
      expect(r.stderr).toContain('Broken aliases:');
      expect(r.stderr).toMatch(/3\. Component\/dangling \[blue\/light\/default\]: unknown token: does\/not\/exist/);
      expect(r.stderr).toContain('Nothing generated');
    } finally { h.cleanup(); }
  });

  it('--validate lists circular references and broken aliases per combination', () => {
    const h = harness(f => {
      f['3. Component'].tokens['loop/a'] = '@loop/b';
      f['3. Component'].tokens['loop/b'] = '@loop/a';
      f['3. Component'].tokens['dangling'] = '@does/not/exist';
    });
    try {
      const r = h.run(['--validate']);
      expect(r.code).toBe(1);
      expect(r.stderr).toContain('Token validation failed');
      expect(r.stderr).toContain('Circular references detected:');
      expect(r.stderr).toMatch(/3\. Component\/loop\/a \[blue\/light\/default\]: alias loop at loop\/a/);
      expect(r.stderr).toContain('Broken aliases:');
      expect(r.stderr).toContain('unknown token: does/not/exist');
      // 3 palettes x 2 themes x 1 direction, two looping tokens each
      expect(r.stderr).toContain('Total circular references: 12');
      expect(r.stderr).toContain('Total broken aliases: 6');
    } finally { h.cleanup(); }
  });

  it('--validate flags metadata count and mode-length mismatches', () => {
    const h = harness(f => {
      f['1. Primitives'].tokens['unused/extra'] = '#123456';
      f['1. Primitives'].count = -1;                       // sentinel: recount() leaves it, so declared != actual
      f['2. Semantic'].tokens['text/primary'] = ['#000'];  // 1 value for 2 modes
    });
    try {
      const r = h.run(['--validate']);
      expect(r.code).toBe(1);
      expect(r.stderr).toContain('1. Primitives: declared -1 tokens, found 11');
      expect(r.stderr).toContain('2. Semantic/text/primary: expected 2 values, got 1');
    } finally { h.cleanup(); }
  });

  it('--validate passes a well-formed fixture and warns about unreferenced primitives only', () => {
    const h = harness(() => {});
    try {
      const r = h.run(['--validate']);
      expect(r.code, r.stderr).toBe(0);
      expect(r.stderr).toContain('Token validation passed');
    } finally { h.cleanup(); }
  });
});

describe('tokens-to-css.mjs - CSS output quality', () => {
  const full = runScript();

  it('balances braces', () => {
    expect((full.match(/{/g) || []).length).toBe((full.match(/}/g) || []).length);
  });

  it('has no trailing commas before a closing brace', () => {
    expect(full).not.toMatch(/,\s*}/);
  });

  it('every declaration line is well-formed', () => {
    full.split('\n').filter(l => l.trim().startsWith('--azmx-')).forEach(line => {
      expect(line).toMatch(/^\s*--azmx-[\w-]+:\s*.+;$/);
    });
  });

  it('emits one gradient per palette', () => {
    const gradients = full.match(/--azmx-gradient: linear-gradient/g) || [];
    expect(gradients.length).toBe(PALETTES.length);
  });
});
