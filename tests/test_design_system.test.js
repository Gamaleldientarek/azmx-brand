/**
 * scripts/design-system.mjs: the skill's link to the private AZM X Design System.
 * Fixtures here are made up; the real system is private and never read in CI.
 */

import { describe, it, expect } from 'vitest';
import {
  parseCssBlocks,
  resolveVars,
  dsScope,
  skillScope,
  normColour,
  compareColours,
  skillScales,
  compareScales,
  driftReport,
  formatReport,
  githubToken,
  reader,
  loadConfig,
  NO_ACCESS,
} from '../scripts/design-system.mjs';

// The design system's shape: primitives in :root, accents per palette, semantics in [data-palette], .dark on top.
const DS_CSS = `
/* generated */
:root { --azmx-white: #FFFFFF; --azmx-neutral-900: #111927; --azmx-blue-600: #001AFF; --azmx-orange-500: #F47A48; }
:root, [data-palette="blue"] { --accent-base: var(--azmx-blue-600); --accent-ground: #000000; }
[data-palette="orange"] { --accent-base: var(--azmx-orange-500); --accent-ground: #000000; }
:root, [data-palette] { --surface-page: var(--azmx-white); --text-heading: var(--azmx-neutral-900); --gradient-start: var(--accent-ground); --gradient-end: var(--accent-base); --ring: var(--accent-base); }
.dark, .dark[data-palette], .dark [data-palette] { --surface-page: var(--accent-ground); --text-heading: var(--azmx-white); }
`;

// The skill's shape: resolved values per palette, [data-theme="dark"] for dark.
const SKILL_CSS = `
:root { --azmx-surface-page: #FFFFFF; --azmx-text-heading: #111927; --azmx-gradient-start: #000000; --azmx-gradient-end: #001AFF; }
[data-theme="dark"] { --azmx-surface-page: #000000; --azmx-text-heading: #FFFFFF; }
[data-palette="orange"] { --azmx-gradient-end: #F47A48; }
[data-palette="orange"][data-theme="dark"] { --azmx-surface-page: #000000; }
`;

const CONFIG = {
  ref: 'v1.2.3',
  compare: { prefixes: ['surface-', 'text-', 'gradient-'], palettes: ['blue', 'orange'], modes: ['light', 'dark'] },
  known: [],
};

const TOKENS = {
  '1. Primitives': { tokens: { 'size/space/0': 0, 'size/space/4': 4, 'size/space/8': 8, 'size/radius/0': 0, 'size/radius/8': 8 } },
  '2. Semantic': { tokens: { 'radius/none': ['@size/radius/0', '@size/radius/0'], 'radius/sm': ['@size/radius/8', '@size/radius/8'] } },
};
const SITE = { spacing: [0, 4, 8], radius: { none: '0px', sm: '8px' } };

describe('parsing and resolving CSS variables', () => {
  it('reads each block with its custom properties and drops comments', () => {
    const blocks = parseCssBlocks(DS_CSS);
    expect(blocks).toHaveLength(5);
    expect(blocks[1].selector).toBe(':root, [data-palette="blue"]');
    expect(blocks[1].vars['--accent-ground']).toBe('#000000');
  });

  it('resolves var() chains and fallbacks, and leaves loops as written', () => {
    const out = resolveVars({ '--a': 'var(--b)', '--b': 'var(--c, #123456)', '--x': 'var(--y)', '--y': 'var(--x)' });
    expect(out['--a']).toBe('#123456');
    expect(out['--x']).toMatch(/var\(--/);
  });
});

describe('scopes', () => {
  it('builds the design system palette and mode the way the cascade does', () => {
    const blocks = parseCssBlocks(DS_CSS);
    expect(dsScope(blocks, 'orange', 'light')['--gradient-end']).toBe('#F47A48');
    expect(dsScope(blocks, 'blue', 'dark')['--surface-page']).toBe('#000000');
    expect(dsScope(blocks, 'blue', 'light')['--surface-page']).toBe('#FFFFFF');
  });

  it("builds the skill's palette and mode", () => {
    const blocks = parseCssBlocks(SKILL_CSS);
    expect(skillScope(blocks, 'orange', 'light')['--azmx-gradient-end']).toBe('#F47A48');
    expect(skillScope(blocks, 'blue', 'dark')['--azmx-text-heading']).toBe('#FFFFFF');
  });
});

describe('normColour', () => {
  it('normalises hex, rgb() and rgba() to upper-case hex, dropping an opaque alpha', () => {
    expect(normColour('#fff')).toBe('#FFFFFF');
    expect(normColour('#FFFFFF33')).toBe('#FFFFFF33');
    expect(normColour('#000000ff')).toBe('#000000');
    expect(normColour('rgb(0 0 0 / 0.35)')).toBe('#00000059');
    expect(normColour('rgba(255, 255, 255, 0.2)')).toBe('#FFFFFF33');
  });

  it('returns null for values that are not a plain colour', () => {
    expect(normColour('color-mix(in srgb, red 20%, transparent)')).toBeNull();
    expect(normColour('16px')).toBeNull();
  });
});

describe('compareColours', () => {
  it('reports a token whose colour differs, by its shared name', () => {
    const ds = { '--surface-page': '#000000', '--ring': '#001AFF' };
    const skill = { '--azmx-surface-page': '#040038', '--azmx-ring': '#FF0000' };
    expect(compareColours(ds, skill, ['surface-'])).toEqual([{ token: 'surface-page', system: '#000000', skill: '#040038' }]);
  });
});

describe('spacing and radius', () => {
  it("reads the skill's scales from its token file", () => {
    expect(skillScales(TOKENS)).toEqual({ spacing: [0, 4, 8], radius: { none: 0, sm: 8 } });
  });

  it('flags a different spacing scale and a radius name that means another size', () => {
    const diffs = compareScales({ spacing: [0, 4, 8, 12], radius: { none: '0px', sm: '4px' } }, skillScales(TOKENS));
    expect(diffs.map((d) => d.token)).toEqual(['spacing', 'radius/sm']);
  });
});

describe('driftReport', () => {
  const base = { config: CONFIG, dsCss: DS_CSS, skillCss: SKILL_CSS, site: SITE, skillTokens: TOKENS, sourceMatches: true, latest: 'v1.2.3' };

  it('finds no drift when the skill matches the system', () => {
    const r = driftReport(base);
    expect(r.errors).toEqual([]);
    expect(formatReport(r, 'v1.2.3')).toContain('No unexplained drift');
  });

  it('reports navy where the system has black, per palette and mode', () => {
    const r = driftReport({ ...base, skillCss: SKILL_CSS.replace('--azmx-surface-page: #000000; --azmx-text-heading', '--azmx-surface-page: #040038; --azmx-text-heading') });
    expect(r.errors).toContainEqual({ token: 'surface-page', system: '#000000', skill: '#040038', where: 'blue/dark' });
  });

  it('moves a difference listed in config.known to the accepted list with its reason', () => {
    const skillCss = SKILL_CSS.replace('--azmx-text-heading: #111927', '--azmx-text-heading: #040038');
    const r = driftReport({ ...base, skillCss, config: { ...CONFIG, known: [{ token: 'text-heading', why: 'ruled' }] } });
    expect(r.errors).toEqual([]);
    expect(r.accepted.map((d) => d.why)).toContain('ruled');
  });

  it('notes a newer system release and a stale colour source without failing', () => {
    const r = driftReport({ ...base, latest: 'v1.3.0', sourceMatches: false });
    expect(r.errors).toEqual([]);
    expect(r.notes.join(' ')).toMatch(/v1\.3\.0/);
    expect(r.notes.join(' ')).toMatch(/sync-brand/);
  });
});

describe('access', () => {
  it('uses GITHUB_TOKEN, then GH_TOKEN, then the GitHub CLI', () => {
    expect(githubToken({ GITHUB_TOKEN: 'a', GH_TOKEN: 'b' }, () => 'c')).toBe('a');
    expect(githubToken({ GH_TOKEN: 'b' }, () => 'c')).toBe('b');
    expect(githubToken({}, () => 'c\n')).toBe('c');
    expect(githubToken({}, () => { throw new Error('no gh'); })).toBeUndefined();
  });

  it('refuses a ref that could change the address', () => {
    expect(() => reader(CONFIG, '../main', { AZMX_DS_DIR: '/tmp' })).toThrow(/not a version tag/);
  });
});

describe('config/design-system.json', () => {
  it('pins a release of the private design system and lists what to compare', () => {
    const config = loadConfig();
    expect(config.repo).toBe('Gamaleldientarek/azmx-design-system');
    expect(config.ref).toMatch(/^v\d+\.\d+\.\d+$/);
    expect(config.installer).toBe('@azmxsa/cli');
    expect(config.compare.palettes).toHaveLength(6);
    for (const k of config.known) expect(k.why, k.token).toBeTruthy();
  });

  it('links the AZM X fonts folder, and the no-access message points to it', () => {
    const config = loadConfig();
    expect(config.fontsFolder).toMatch(/^https:\/\/drive\.google\.com\/drive\/folders\/[\w-]+$/);
    expect(NO_ACCESS(config)).toContain(config.fontsFolder);
    expect(NO_ACCESS(config)).toContain('assets/fonts/');
  });
});
