/**
 * scripts/icons.mjs: any Phosphor icon by name, one SVG at a time.
 * The search runs on the shipped index; nothing here touches the network.
 */

import { describe, it, expect } from 'vitest';
import { loadIndex, searchIcons, findIcon, checkWeight, iconUrl, recolour } from '../scripts/icons.mjs';
import { PHOSPHOR_CORE_VERSION, toIndex } from '../scripts/build-icon-index.mjs';

const { version, icons } = loadIndex();

describe('the shipped index', () => {
  it('holds every icon of the pinned package, each name once', () => {
    expect(version).toBe(PHOSPHOR_CORE_VERSION);
    expect(icons).toHaveLength(1512);
    expect(new Set(icons.map((i) => i[0])).size).toBe(1512);
    for (const [name, pascal] of icons) {
      expect(name).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
      expect(pascal).toMatch(/^[A-Z][A-Za-z0-9]*$/);
    }
  });

  it('keeps tags and categories as keywords, without markers like *new*', () => {
    const out = toIndex([{ name: 'rocket', pascal_name: 'Rocket', tags: ['*new*', 'Launch', 'launch'], categories: ['objects'] }], '9.9.9');
    expect(JSON.parse(out)).toEqual({ version: '9.9.9', icons: [['rocket', 'Rocket', 'launch objects']] });
  });
});

describe('searchIcons', () => {
  it('puts the exact name first, in any spelling', () => {
    for (const q of ['arrow-right', 'ArrowRight', 'arrow right']) expect(searchIcons(icons, q)[0][0]).toBe('arrow-right');
  });

  it('finds icons by keyword and needs every word', () => {
    expect(searchIcons(icons, 'money').map((i) => i[0])).toEqual(expect.arrayContaining(['money', 'bank', 'coin']));
    expect(searchIcons(icons, 'rocket spaceship')[0][0]).toBe('rocket');
    expect(searchIcons(icons, 'zzqx')).toEqual([]);
  });
});

describe('findIcon', () => {
  it('takes the kebab-case or the React name', () => {
    expect(findIcon(icons, 'arrow-right')[1]).toBe('ArrowRight');
    expect(findIcon(icons, 'ArrowRight')[0]).toBe('arrow-right');
  });

  it('refuses an unknown name and suggests close ones', () => {
    expect(() => findIcon(icons, 'rocketship-x')).toThrow(/no Phosphor icon is called/);
    expect(() => findIcon(icons, 'arrow')).toThrow(/Did you mean arrow-/);
  });
});

describe('weights, addresses and colours', () => {
  it('allows Regular and Light only, as the brand does', () => {
    expect(checkWeight('regular')).toBe('regular');
    expect(checkWeight('light')).toBe('light');
    for (const w of ['fill', 'duotone', 'bold', 'thin']) expect(() => checkWeight(w)).toThrow(/isn't allowed/);
  });

  it('points at one SVG of the pinned package', () => {
    expect(iconUrl('rocket', 'regular', '2.1.1')).toBe('https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2.1.1/assets/regular/rocket.svg');
    expect(iconUrl('rocket', 'light', '2.1.1')).toBe('https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2.1.1/assets/light/rocket-light.svg');
  });

  it('swaps currentColor for a fixed #RRGGBB colour, and refuses anything else', () => {
    expect(recolour('<svg fill="currentColor"/>', '#111927')).toBe('<svg fill="#111927"/>');
    expect(() => recolour('<svg/>', 'red')).toThrow(/isn't a #RRGGBB colour/);
  });
});
