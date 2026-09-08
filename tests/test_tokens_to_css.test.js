/**
 * Unit tests for tokens-to-css.mjs
 *
 * Tests the token resolution logic and CSS generation for all 12 palette-theme combinations.
 * Uses sample-tokens.json fixture which has 3 palettes × 2 themes = 6 combinations.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, '..');
const SCRIPTS_DIR = join(REPO_ROOT, 'scripts');
const FIXTURES_DIR = join(HERE, 'fixtures');
const SCRIPT_PATH = join(SCRIPTS_DIR, 'tokens-to-css.mjs');

// Load test fixture
const FIXTURE_PATH = join(FIXTURES_DIR, 'sample-tokens.json');
const TEST_DATA = JSON.parse(readFileSync(FIXTURE_PATH, 'utf8'));

// Extract token collections from fixture
const PALETTES = TEST_DATA['1b. Palette'].modes.map(m => m.toLowerCase());
const THEMES = TEST_DATA['2. Semantic'].modes.map(m => m.toLowerCase());
const prim = TEST_DATA['1. Primitives'].tokens;
const pal = TEST_DATA['1b. Palette'].tokens;
const sem = TEST_DATA['2. Semantic'].tokens;
const comp = TEST_DATA['3. Component'].tokens;
const canv = TEST_DATA['4. Canvas'].tokens;

/**
 * Resolve token references for testing.
 * This is a copy of the resolve() function from tokens-to-css.mjs for unit testing.
 */
function resolve(ref, paletteIdx, themeIdx, depth = 0) {
  if (depth > 12) throw new Error('alias loop at ' + ref);
  if (typeof ref !== 'string' || !ref.startsWith('@')) return ref;
  const name = ref.slice(1);

  if (name in prim) return prim[name];
  if (name in pal) return resolve(pal[name][paletteIdx], paletteIdx, themeIdx, depth + 1);
  if (name in sem) return resolve(sem[name][themeIdx], paletteIdx, themeIdx, depth + 1);
  if (name in comp) return resolve(comp[name], paletteIdx, themeIdx, depth + 1);
  if (name in canv) return resolve(canv[name], paletteIdx, themeIdx, depth + 1);
  throw new Error('unknown token: ' + name);
}

/**
 * Resolve all semantic, component, and canvas tokens for one combination.
 * This is a copy of the resolveAll() function from tokens-to-css.mjs for unit testing.
 */
function resolveAll(paletteIdx, themeIdx) {
  const out = {};
  for (const n of Object.keys(sem)) out[n] = resolve(sem[n][themeIdx], paletteIdx, themeIdx);
  for (const n of Object.keys(comp)) out[n] = resolve(comp[n], paletteIdx, themeIdx);
  for (const n of Object.keys(canv)) out[n] = resolve(canv[n], paletteIdx, themeIdx);
  return out;
}

describe('tokens-to-css.mjs - resolve()', () => {
  describe('resolves primitives', () => {
    it('resolves a primitive color token', () => {
      const result = resolve('@color/primary/electric', 0, 0);
      expect(result).toBe('#001AFF');
    });

    it('resolves a primitive spacing token', () => {
      const result = resolve('@spacing/md', 0, 0);
      expect(result).toBe('16px');
    });

    it('returns non-reference values unchanged', () => {
      expect(resolve('#FF0000', 0, 0)).toBe('#FF0000');
      expect(resolve('16px', 0, 0)).toBe('16px');
      expect(resolve(42, 0, 0)).toBe(42);
      expect(resolve('plain-string', 0, 0)).toBe('plain-string');
    });
  });

  describe('resolves palette tokens', () => {
    it('resolves palette token for Blue (index 0)', () => {
      const result = resolve('@surface/accent', 0, 0);
      expect(result).toBe('#001AFF');
    });

    it('resolves palette token for Orange (index 1)', () => {
      const result = resolve('@surface/accent', 1, 0);
      expect(result).toBe('#F47A48');
    });

    it('resolves palette token for Green (index 2)', () => {
      const result = resolve('@surface/accent', 2, 0);
      expect(result).toBe('#22C36F');
    });

    it('resolves nested palette token (palette token referencing primitive)', () => {
      const result = resolve('@surface/deep', 0, 0);
      expect(result).toBe('#040038');
    });
  });

  describe('resolves semantic tokens', () => {
    it('resolves semantic token for light theme (index 0)', () => {
      const result = resolve('@text/primary', 0, 0);
      expect(result).toBe('#111927');
    });

    it('resolves semantic token for dark theme (index 1)', () => {
      const result = resolve('@text/primary', 0, 1);
      expect(result).toBe('#FFFFFF');
    });

    it('resolves semantic token referencing another semantic token', () => {
      const result = resolve('@surface/page', 0, 0);
      expect(result).toBe('#FFFFFF');
    });

    it('resolves semantic token with different values per theme', () => {
      const lightResult = resolve('@text/accent', 0, 0);
      const darkResult = resolve('@text/accent', 0, 1);
      expect(lightResult).toBe('#001AFF');
      expect(darkResult).toBe('#5D8FFF');
    });
  });

  describe('resolves component tokens', () => {
    it('resolves component token referencing palette token', () => {
      // button/background -> @surface/accent -> palette-specific color
      const blueResult = resolve('@button/background', 0, 0);
      const orangeResult = resolve('@button/background', 1, 0);
      expect(blueResult).toBe('#001AFF');
      expect(orangeResult).toBe('#F47A48');
    });

    it('resolves component token referencing primitive', () => {
      const result = resolve('@button/text', 0, 0);
      expect(result).toBe('#FFFFFF');
    });

    it('resolves component token with direct value', () => {
      const result = resolve('@card/background', 0, 0);
      expect(result).toBe('#F0F5FF');
    });
  });

  describe('resolves canvas tokens', () => {
    it('resolves canvas token referencing semantic token', () => {
      // canvas/background -> @surface/page -> theme-specific
      const lightResult = resolve('@canvas/background', 0, 0);
      const darkResult = resolve('@canvas/background', 0, 1);
      expect(lightResult).toBe('#FFFFFF');
      expect(darkResult).toBe('#040038');
    });

    it('resolves canvas token referencing component token', () => {
      const result = resolve('@canvas/text', 0, 0);
      expect(result).toBe('#111927');
    });
  });

  describe('handles errors', () => {
    it('throws error for unknown token', () => {
      expect(() => resolve('@unknown/token', 0, 0)).toThrow('unknown token: unknown/token');
    });

    it('detects circular references', () => {
      // Create mock data with circular reference
      const mockPrim = {};
      const mockPal = {};
      const mockSem = {
        'circular/a': ['@circular/b', '@circular/b'],
        'circular/b': ['@circular/c', '@circular/c'],
        'circular/c': ['@circular/a', '@circular/a']
      };
      const mockComp = {};
      const mockCanv = {};

      // Override global test data temporarily
      const originalSem = sem;
      Object.assign(sem, mockSem);

      expect(() => resolve('@circular/a', 0, 0)).toThrow('alias loop at @circular/');

      // Restore original data
      Object.keys(mockSem).forEach(k => delete sem[k]);
      Object.assign(sem, originalSem);
    });
  });

  describe('handles all palette-theme combinations', () => {
    it('resolves correctly for all 6 combinations (3 palettes × 2 themes)', () => {
      // Expected values for text/primary across combinations
      const expectedValues = {
        'blue/light': '#111927',
        'blue/dark': '#FFFFFF',
        'orange/light': '#111927',
        'orange/dark': '#FFFFFF',
        'green/light': '#111927',
        'green/dark': '#FFFFFF',
      };

      PALETTES.forEach((palette, pIdx) => {
        THEMES.forEach((theme, tIdx) => {
          const result = resolve('@text/primary', pIdx, tIdx);
          const key = `${palette}/${theme}`;
          expect(result).toBe(expectedValues[key]);
        });
      });
    });

    it('resolves palette-specific tokens for all palettes', () => {
      const expectedAccentColors = {
        'blue': '#001AFF',
        'orange': '#F47A48',
        'green': '#22C36F'
      };

      PALETTES.forEach((palette, pIdx) => {
        const result = resolve('@surface/accent', pIdx, 0);
        expect(result).toBe(expectedAccentColors[palette]);
      });
    });
  });
});

describe('tokens-to-css.mjs - resolveAll()', () => {
  it('resolves all tokens for blue/light combination', () => {
    const result = resolveAll(0, 0);

    expect(result).toHaveProperty('text/primary', '#111927');
    expect(result).toHaveProperty('surface/page', '#FFFFFF');
    expect(result).toHaveProperty('text/accent', '#001AFF');
    expect(result).toHaveProperty('canvas/background', '#FFFFFF');
    expect(result).toHaveProperty('canvas/text', '#111927');
  });

  it('resolves all tokens for blue/dark combination', () => {
    const result = resolveAll(0, 1);

    expect(result).toHaveProperty('text/primary', '#FFFFFF');
    expect(result).toHaveProperty('surface/page', '#040038');
    expect(result).toHaveProperty('text/accent', '#5D8FFF');
  });

  it('resolves all tokens for orange/light combination', () => {
    const result = resolveAll(1, 0);

    expect(result).toHaveProperty('text/primary', '#111927');
    expect(result).toHaveProperty('surface/page', '#FFFFFF');
    // Note: button/background references @surface/accent which is palette-specific
    expect(result).toHaveProperty('button/background', '#F47A48');
  });

  it('resolves all 6 combinations without errors', () => {
    PALETTES.forEach((palette, pIdx) => {
      THEMES.forEach((theme, tIdx) => {
        expect(() => resolveAll(pIdx, tIdx)).not.toThrow();
        const result = resolveAll(pIdx, tIdx);
        expect(typeof result).toBe('object');
        expect(Object.keys(result).length).toBeGreaterThan(0);
      });
    });
  });

  it('returns different values for different combinations', () => {
    const blueLight = resolveAll(0, 0);
    const blueDark = resolveAll(0, 1);
    const orangeLight = resolveAll(1, 0);

    // Theme difference
    expect(blueLight['text/primary']).not.toBe(blueDark['text/primary']);

    // Palette difference (for palette-dependent tokens)
    expect(blueLight['button/background']).not.toBe(orangeLight['button/background']);
  });
});

describe('tokens-to-css.mjs - CLI integration', () => {
  // Helper to run the script with the test fixture
  function runScript(args = [], useTestFixture = true) {
    const cwd = SCRIPTS_DIR;
    const env = { ...process.env };

    // If using test fixture, temporarily replace the real tokens file


    // For test fixture, we need to modify the script to use our fixture
    // Since we can't modify the script, we'll run it with the real data
    // and just verify the structure/format

    try {
      const output = execFileSync(process.execPath, [SCRIPT_PATH, ...args], {
        cwd,
        env,
        encoding: 'utf8',
        timeout: 5000
      });
      return output;
    } catch (error) {
      // If the script exits with error code, return the error
      throw new Error(`Script failed: ${error.message}\n${error.stderr}`);
    }
  }

  it('generates CSS for all combinations by default', () => {
    const output = runScript([], false);

    // Should contain the header comment
    expect(output).toContain('AZM X Design Tokens');

    // Should contain base :root selector
    expect(output).toContain(':root {');

    // Should contain CSS custom properties
    expect(output).toContain('--azmx-');

    // Should contain attribute selectors for different combinations
    expect(output).toContain('[data-palette=');
    expect(output).toContain('[data-theme=');
  });

  it('generates CSS for single palette with --palette flag', () => {
    const output = runScript(['--palette', 'orange'], false);

    expect(output).toContain('orange');
    expect(output).toContain(':root {');
    expect(output).toContain('--azmx-');

    // Should NOT contain attribute selectors (single combination)
    expect(output).not.toContain('[data-palette=');
  });

  it('generates CSS for single theme with --theme flag', () => {
    const output = runScript(['--theme', 'dark'], false);

    expect(output).toContain('dark');
    expect(output).toContain(':root {');
    expect(output).toContain('--azmx-');
  });

  it('generates CSS for specific combination with both flags', () => {
    const output = runScript(['--palette', 'blue', '--theme', 'light'], false);

    expect(output).toContain('blue');
    expect(output).toContain('light');
    expect(output).toContain(':root {');
  });

  it('outputs JSON with --json flag', () => {
    const output = runScript(['--json', '--palette', 'blue', '--theme', 'light'], false);

    // Should be valid JSON
    expect(() => JSON.parse(output)).not.toThrow();

    const data = JSON.parse(output);
    expect(typeof data).toBe('object');

    // Should contain resolved token values
    expect(Object.keys(data).length).toBeGreaterThan(0);
  });

  it('outputs all combinations as JSON with --json flag alone', () => {
    const output = runScript(['--json'], false);

    const data = JSON.parse(output);

    // Should have keys for each combination
    expect(data).toHaveProperty('blue/light');
    expect(data).toHaveProperty('blue/dark');
    expect(data).toHaveProperty('orange/light');
    expect(data).toHaveProperty('orange/dark');

    // Each combination should be an object
    expect(typeof data['blue/light']).toBe('object');
  });

  it('generates valid CSS custom property names', () => {
    const output = runScript(['--palette', 'blue', '--theme', 'light'], false);

    // Should contain properly formatted CSS variables
    expect(output).toMatch(/--azmx-[\w-]+:/);

    // Variable names should use hyphens, not slashes
    expect(output).toContain('--azmx-text-primary');
    expect(output).not.toContain('--azmx-text/primary');
  });

  it('includes primitives in full output', () => {
    const output = runScript([], false);

    // Should have a primitives section
    expect(output).toContain('Primitives');
  });

  it('includes gradient definitions', () => {
    const output = runScript([], false);

    expect(output).toContain('--azmx-gradient');
    expect(output).toContain('linear-gradient');
  });

  it('includes font definitions', () => {
    const output = runScript([], false);

    expect(output).toContain('--azmx-font-heading');
    expect(output).toContain('--azmx-font-text');
  });

  it('handles unknown palette gracefully', () => {
    expect(() => runScript(['--palette', 'unknown'])).toThrow();
  });

  it('handles unknown theme gracefully', () => {
    expect(() => runScript(['--theme', 'unknown'])).toThrow();
  });

  it('formats numeric values correctly', () => {
    const output = runScript(['--palette', 'blue', '--theme', 'light'], false);

    // Numeric values should be stringified (if any exist)
    // The script has a fmt() function that converts numbers to strings
    expect(output).toMatch(/:\s*[\w#]+;/);
  });
});

describe('tokens-to-css.mjs - CSS output quality', () => {
  it('generates minification-friendly CSS (no trailing commas)', () => {
    const output = execFileSync(process.execPath, [SCRIPT_PATH, '--palette', 'blue', '--theme', 'light'], {
      cwd: SCRIPTS_DIR,
      encoding: 'utf8'
    });

    // Should not have trailing commas in CSS
    expect(output).not.toMatch(/,\s*}/);
  });

  it('generates properly closed selectors and blocks', () => {
    const output = execFileSync(process.execPath, [SCRIPT_PATH], {
      cwd: SCRIPTS_DIR,
      encoding: 'utf8'
    });

    // Count opening and closing braces - they should match
    const openBraces = (output.match(/{/g) || []).length;
    const closeBraces = (output.match(/}/g) || []).length;
    expect(openBraces).toBe(closeBraces);
  });

  it('generates valid CSS property syntax', () => {
    const output = execFileSync(process.execPath, [SCRIPT_PATH, '--palette', 'blue', '--theme', 'light'], {
      cwd: SCRIPTS_DIR,
      encoding: 'utf8'
    });

    // Each property line should have format: --azmx-name: value;
    const propertyLines = output.split('\n').filter(line => line.trim().startsWith('--azmx-'));
    propertyLines.forEach(line => {
      expect(line).toMatch(/^\s*--azmx-[\w-]+:\s*.+;$/);
    });
  });

  it('includes version metadata in output', () => {
    const output = execFileSync(process.execPath, [SCRIPT_PATH], {
      cwd: SCRIPTS_DIR,
      encoding: 'utf8'
    });

    expect(output).toMatch(/v\d+\.\d+\.\d+/);
  });

  it('includes usage instructions in comment', () => {
    const output = execFileSync(process.execPath, [SCRIPT_PATH], {
      cwd: SCRIPTS_DIR,
      encoding: 'utf8'
    });

    expect(output).toContain('data-palette');
    expect(output).toContain('data-theme');
  });
});
