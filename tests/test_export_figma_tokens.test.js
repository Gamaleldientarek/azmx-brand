/**
 * Tests for scripts/export-figma-tokens.js
 *
 * The script is pasted into the Figma plugin console, so it cannot be imported.
 * Each test evaluates the REAL source (see tests/helpers/figma-console.js) with
 * a mock `figma` global and asserts on what the script returned and on which
 * API calls it made. Nothing from the script is re-implemented here.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { runFigmaScript } from './helpers/figma-console.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT_PATH = join(HERE, '..', 'scripts', 'export-figma-tokens.js');

const NAMES = ['1. Primitives', '1b. Palette', '2. Semantic', '3. Component', '4. Canvas'];

/** Mock Figma data: five collections, aliases across tiers, every value type. */
function createMockFigmaData() {
  const collections = [
    { id: 'col1', name: '1. Primitives', modes: [{ modeId: 'mode1', name: 'Default' }] },
    {
      id: 'col2', name: '1b. Palette',
      modes: [
        { modeId: 'mode2a', name: 'Blue' },
        { modeId: 'mode2b', name: 'Orange' },
        { modeId: 'mode2c', name: 'Green' },
      ],
    },
    {
      id: 'col3', name: '2. Semantic',
      modes: [{ modeId: 'mode3a', name: 'Light' }, { modeId: 'mode3b', name: 'Dark' }],
    },
    { id: 'col4', name: '3. Component', modes: [{ modeId: 'mode4', name: 'Default' }] },
    { id: 'col5', name: '4. Canvas', modes: [{ modeId: 'mode5', name: 'Default' }] },
  ];

  const variables = [
    {
      id: 'var1', name: 'color/primary/electric', variableCollectionId: 'col1',
      resolvedType: 'COLOR', scopes: ['ALL_SCOPES'], hiddenFromPublishing: false,
      description: 'Primary electric blue',
      valuesByMode: { mode1: { r: 0, g: 0.102, b: 1, a: 1 } },
    },
    {
      id: 'var2', name: 'spacing/md', variableCollectionId: 'col1',
      resolvedType: 'FLOAT', scopes: ['ALL_SCOPES'], hiddenFromPublishing: false,
      description: 'Medium spacing',
      valuesByMode: { mode1: 16 },
    },
    {
      id: 'var3', name: 'surface/accent', variableCollectionId: 'col2',
      resolvedType: 'COLOR', scopes: ['ALL_SCOPES'], hiddenFromPublishing: false,
      description: 'Accent surface color',
      valuesByMode: {
        mode2a: { type: 'VARIABLE_ALIAS', id: 'var1' },   // Blue -> electric
        mode2b: { r: 0.957, g: 0.478, b: 0.282, a: 1 },    // Orange
        mode2c: { r: 0.133, g: 0.765, b: 0.435, a: 1 },    // Green
      },
    },
    {
      id: 'var4', name: 'text/primary', variableCollectionId: 'col3',
      resolvedType: 'COLOR', scopes: ['TEXT_FILL'], hiddenFromPublishing: false,
      description: 'Primary text color',
      valuesByMode: {
        mode3a: { r: 0, g: 0, b: 0, a: 1 },
        mode3b: { type: 'VARIABLE_ALIAS', id: 'var3' },   // Dark -> palette accent
      },
    },
    {
      id: 'var5', name: 'button/bg', variableCollectionId: 'col4',
      resolvedType: 'COLOR', scopes: ['FRAME_FILL'], hiddenFromPublishing: false,
      description: 'Button background',
      valuesByMode: { mode4: { r: 0, g: 0.102, b: 1, a: 0.8 } },
    },
    {
      id: 'var6', name: 'font/family/body', variableCollectionId: 'col1',
      resolvedType: 'STRING', scopes: ['FONT_FAMILY'], hiddenFromPublishing: false,
      description: 'Body font family',
      valuesByMode: { mode1: 'Inter' },
    },
    {
      id: 'var7', name: 'feature/dark-mode', variableCollectionId: 'col1',
      resolvedType: 'BOOLEAN', scopes: ['ALL_SCOPES'], hiddenFromPublishing: true,
      description: 'Dark mode feature flag',
      valuesByMode: { mode1: true },
    },
    {
      id: 'var8', name: 'slide/width', variableCollectionId: 'col5',
      resolvedType: 'FLOAT', scopes: ['WIDTH_HEIGHT'], hiddenFromPublishing: false,
      description: '',
      valuesByMode: { mode5: 1920 },
    },
  ];

  const paintStyles = [
    { name: 'Fills/Primary', description: 'Primary fill color', paints: [{ type: 'SOLID', color: { r: 0, g: 0.102, b: 1 } }] },
    {
      name: 'Fills/Gradient', description: 'Gradient fill',
      paints: [{
        type: 'GRADIENT_LINEAR',
        gradientStops: [
          { position: 0, color: { r: 0, g: 0.102, b: 1, a: 1 } },
          { position: 1, color: { r: 1, g: 0, b: 0, a: 1 } },
        ],
      }],
    },
  ];

  const textStyles = [
    {
      name: 'Text/Heading', description: 'Heading text style',
      fontName: { family: 'Inter', style: 'Bold' },
      fontSize: 24,
      lineHeight: { value: 32, unit: 'PIXELS' },
      letterSpacing: { value: 0, unit: 'PIXELS' },
      boundVariables: { fontFamily: { id: 'var6' } },
    },
  ];

  return { collections, variables, paintStyles, textStyles };
}

function createMockFigmaAPI(data) {
  return {
    variables: {
      getLocalVariableCollectionsAsync: vi.fn(async () => data.collections),
      getLocalVariablesAsync: vi.fn(async () => data.variables),
    },
    getLocalPaintStylesAsync: vi.fn(async () => data.paintStyles),
    getLocalTextStylesAsync: vi.fn(async () => data.textStyles),
  };
}

/** Add a COLOR primitive with the given RGBA and return its name. */
function addColor(data, name, rgba, extra = {}) {
  data.variables.push({
    id: 'id_' + name, name, variableCollectionId: 'col1', resolvedType: 'COLOR',
    scopes: ['ALL_SCOPES'], hiddenFromPublishing: false, description: '',
    valuesByMode: { mode1: rgba }, ...extra,
  });
  return name;
}

function tokenNamed(result, collection, name) {
  return result.raw.tokens[collection].find(t => t.name === name);
}

describe('export-figma-tokens.js - Figma API usage', () => {
  let data, figma;
  beforeEach(() => { data = createMockFigmaData(); figma = createMockFigmaAPI(data); });

  it('reads collections, variables, paint styles and text styles exactly once each', async () => {
    await runFigmaScript(SCRIPT_PATH, figma);
    expect(figma.variables.getLocalVariableCollectionsAsync).toHaveBeenCalledTimes(1);
    expect(figma.variables.getLocalVariablesAsync).toHaveBeenCalledTimes(1);
    expect(figma.getLocalPaintStylesAsync).toHaveBeenCalledTimes(1);
    expect(figma.getLocalTextStylesAsync).toHaveBeenCalledTimes(1);
  });

  it('returns { raw, dtcg, bytes } where bytes is the serialised size of raw+dtcg', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(Object.keys(result).sort()).toEqual(['bytes', 'dtcg', 'raw']);
    expect(result.bytes).toBe(JSON.stringify({ raw: result.raw, dtcg: result.dtcg }).length);
  });

  it('does not log anything to the console', async () => {
    const { logs, errors } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(logs).toEqual([]);
    expect(errors).toEqual([]);
  });
});

describe('export-figma-tokens.js - raw export', () => {
  let data, figma;
  beforeEach(() => { data = createMockFigmaData(); figma = createMockFigmaAPI(data); });

  it('exports all five collections with their modes and variable counts in meta', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.raw.meta.file).toBe('New Direction Library | AZM X');
    expect(result.raw.meta.fileKey).toBe('j8ugBpb1yUUyL8hfb6FHKR');
    expect(result.raw.meta.exported).toBeNull();
    expect(result.raw.meta.collections.map(c => c.name)).toEqual(NAMES);
    expect(result.raw.meta.collections).toEqual([
      { name: '1. Primitives', modes: ['Default'], count: 4 },
      { name: '1b. Palette', modes: ['Blue', 'Orange', 'Green'], count: 1 },
      { name: '2. Semantic', modes: ['Light', 'Dark'], count: 1 },
      { name: '3. Component', modes: ['Default'], count: 1 },
      { name: '4. Canvas', modes: ['Default'], count: 1 },
    ]);
    expect(Object.keys(result.raw.tokens)).toEqual(NAMES);
  });

  it('groups variables by collection and sorts each group by name', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.raw.tokens['1. Primitives'].map(t => t.name)).toEqual([
      'color/primary/electric', 'feature/dark-mode', 'font/family/body', 'spacing/md',
    ]);
    expect(result.raw.tokens['4. Canvas'].map(t => t.name)).toEqual(['slide/width']);
  });

  it('carries type, scopes, hiddenFromPublishing and description for each token', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(tokenNamed(result, '1. Primitives', 'color/primary/electric')).toEqual({
      name: 'color/primary/electric', type: 'COLOR', scopes: ['ALL_SCOPES'],
      hiddenFromPublishing: false, description: 'Primary electric blue',
      modes: { Default: { value: '#001AFF' } },
    });
    expect(tokenNamed(result, '1. Primitives', 'feature/dark-mode').hiddenFromPublishing).toBe(true);
  });

  it('normalises a missing description to an empty string', async () => {
    data.variables.find(v => v.name === 'slide/width').description = undefined;
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(tokenNamed(result, '4. Canvas', 'slide/width').description).toBe('');
  });

  it('keeps aliases as target names, per mode', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(tokenNamed(result, '1b. Palette', 'surface/accent').modes).toEqual({
      Blue: { alias: 'color/primary/electric' },
      Orange: { value: '#F47A48' },
      Green: { value: '#22C36F' },
    });
    // nested alias (semantic -> palette) is one hop, not flattened
    expect(tokenNamed(result, '2. Semantic', 'text/primary').modes).toEqual({
      Light: { value: '#000000' },
      Dark: { alias: 'surface/accent' },
    });
  });

  it('marks an alias whose target no longer exists as MISSING', async () => {
    data.variables.push({
      id: 'var_broken', name: 'test/broken', variableCollectionId: 'col1', resolvedType: 'COLOR',
      scopes: ['ALL_SCOPES'], hiddenFromPublishing: false, description: '',
      valuesByMode: { mode1: { type: 'VARIABLE_ALIAS', id: 'nonexistent' } },
    });
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(tokenNamed(result, '1. Primitives', 'test/broken').modes).toEqual({ Default: { alias: 'MISSING' } });
  });

  it('passes FLOAT, STRING and BOOLEAN values through untouched', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(tokenNamed(result, '1. Primitives', 'spacing/md').modes).toEqual({ Default: { value: 16 } });
    expect(tokenNamed(result, '1. Primitives', 'font/family/body').modes).toEqual({ Default: { value: 'Inter' } });
    expect(tokenNamed(result, '1. Primitives', 'feature/dark-mode').modes).toEqual({ Default: { value: true } });
  });

  it('records undefined for a mode the variable has no value for', async () => {
    delete data.variables.find(v => v.name === 'surface/accent').valuesByMode.mode2c;
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(tokenNamed(result, '1b. Palette', 'surface/accent').modes.Green).toEqual({ value: undefined });
  });
});

describe('export-figma-tokens.js - colour conversion (through variable values)', () => {
  let data, figma;
  beforeEach(() => { data = createMockFigmaData(); figma = createMockFigmaAPI(data); });

  const cases = [
    ['full opacity', { r: 0, g: 0.102, b: 1, a: 1 }, '#001AFF'],
    ['80% alpha appends CC', { r: 0, g: 0.102, b: 1, a: 0.8 }, '#001AFFCC'],
    ['pure black', { r: 0, g: 0, b: 0, a: 1 }, '#000000'],
    ['pure white', { r: 1, g: 1, b: 1, a: 1 }, '#FFFFFF'],
    ['red at 50%', { r: 1, g: 0, b: 0, a: 0.5 }, '#FF000080'],
    ['no alpha property', { r: 0.5, g: 0.5, b: 0.5 }, '#808080'],
    ['rounds channels', { r: 0.004, g: 0.502, b: 0.996, a: 1 }, '#0180FE'],
    ['alpha 0.999 treated as opaque', { r: 1, g: 0, b: 0, a: 0.999 }, '#FF0000'],
    ['very low alpha', { r: 0, g: 0, b: 0, a: 0.01 }, '#00000003'],
  ];

  it.each(cases)('%s', async (_label, rgba, expected) => {
    const name = addColor(data, 'test/colour', rgba);
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(tokenNamed(result, '1. Primitives', name).modes.Default).toEqual({ value: expected });
    expect(result.dtcg['1. Primitives'].test.colour.$value).toBe(expected);
  });
});

describe('export-figma-tokens.js - styles', () => {
  let data, figma;
  beforeEach(() => { data = createMockFigmaData(); figma = createMockFigmaAPI(data); });

  it('exports solid and gradient paint styles with hex colours', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.raw.styles.paint).toEqual([
      { name: 'Fills/Primary', description: 'Primary fill color', paints: [{ type: 'SOLID', color: '#001AFF' }] },
      {
        name: 'Fills/Gradient', description: 'Gradient fill',
        paints: [{ type: 'GRADIENT_LINEAR', stops: [{ position: 0, color: '#001AFF' }, { position: 1, color: '#FF0000' }] }],
      },
    ]);
  });

  it('tolerates a non-solid paint without gradientStops', async () => {
    data.paintStyles.push({ name: 'Fills/Image', description: '', paints: [{ type: 'IMAGE' }] });
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.raw.styles.paint[2]).toEqual({ name: 'Fills/Image', description: '', paints: [{ type: 'IMAGE', stops: [] }] });
  });

  it('exports text styles with bound variables resolved to names', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.raw.styles.text).toEqual([{
      name: 'Text/Heading', description: 'Heading text style',
      fontFamily: 'Inter', fontStyle: 'Bold', fontSize: 24,
      lineHeight: { value: 32, unit: 'PIXELS' }, letterSpacing: { value: 0, unit: 'PIXELS' },
      boundVariables: { fontFamily: 'font/family/body' },
    }]);
  });

  it('uses "?" for a bound variable that cannot be found and {} when none are bound', async () => {
    data.textStyles[0].boundVariables = { fontSize: { id: 'gone' } };
    data.textStyles.push({
      name: 'Text/Body', description: '', fontName: { family: 'Inter', style: 'Regular' },
      fontSize: 16, lineHeight: { unit: 'AUTO' }, letterSpacing: { value: 0, unit: 'PERCENT' },
    });
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.raw.styles.text[0].boundVariables).toEqual({ fontSize: '?' });
    expect(result.raw.styles.text[1].boundVariables).toEqual({});
  });
});

describe('export-figma-tokens.js - DTCG export', () => {
  let data, figma;
  beforeEach(() => { data = createMockFigmaData(); figma = createMockFigmaAPI(data); });

  it('emits one tree per mode for multi-mode collections and a plain key for single-mode ones', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(Object.keys(result.dtcg).sort()).toEqual([
      '1. Primitives', '1b. Palette [Blue]', '1b. Palette [Green]', '1b. Palette [Orange]',
      '2. Semantic [Dark]', '2. Semantic [Light]', '3. Component', '4. Canvas',
    ].sort());
  });

  it('nests slash-separated names into objects with $value/$type', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.dtcg['1. Primitives'].color.primary.electric).toEqual({
      $value: '#001AFF', $type: 'color', $description: 'Primary electric blue',
    });
    expect(result.dtcg['1. Primitives'].spacing.md).toEqual({ $value: 16, $type: 'number', $description: 'Medium spacing' });
    expect(result.dtcg['1. Primitives'].font.family.body).toEqual({ $value: 'Inter', $type: 'fontFamily', $description: 'Body font family' });
    expect(result.dtcg['1. Primitives'].feature['dark-mode']).toEqual({ $value: true, $type: 'boolean', $description: 'Dark mode feature flag' });
  });

  it('omits $description when the variable has none', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.dtcg['4. Canvas'].slide.width).toEqual({ $value: 1920, $type: 'number' });
  });

  it('writes aliases as {dot.path} references, per mode', async () => {
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.dtcg['1b. Palette [Blue]'].surface.accent.$value).toBe('{color.primary.electric}');
    expect(result.dtcg['1b. Palette [Orange]'].surface.accent.$value).toBe('#F47A48');
    expect(result.dtcg['2. Semantic [Dark]'].text.primary.$value).toBe('{surface.accent}');
    expect(result.dtcg['2. Semantic [Light]'].text.primary.$value).toBe('#000000');
  });

  it('writes null for an alias whose target is missing', async () => {
    data.variables.push({
      id: 'var_broken', name: 'test/broken', variableCollectionId: 'col1', resolvedType: 'COLOR',
      scopes: [], hiddenFromPublishing: false, description: '',
      valuesByMode: { mode1: { type: 'VARIABLE_ALIAS', id: 'nonexistent' } },
    });
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.dtcg['1. Primitives'].test.broken.$value).toBeNull();
  });

  it('maps an unknown Figma type to $type "other"', async () => {
    addColor(data, 'test/weird', 42, { resolvedType: 'SOMETHING_NEW' });
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.dtcg['1. Primitives'].test.weird).toEqual({ $value: 42, $type: 'other' });
  });

  it('merges sibling tokens under a shared prefix', async () => {
    addColor(data, 'color/primary/deep', { r: 0, g: 0, b: 0.2, a: 1 });
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(Object.keys(result.dtcg['1. Primitives'].color.primary).sort()).toEqual(['deep', 'electric']);
  });
});

describe('export-figma-tokens.js - degraded files', () => {
  it('handles an empty file: no collections, no variables, no styles', async () => {
    const figma = createMockFigmaAPI({ collections: [], variables: [], paintStyles: [], textStyles: [] });
    const { result } = await runFigmaScript(SCRIPT_PATH, figma);
    expect(result.raw.meta.collections).toEqual(NAMES.map(name => ({ name, modes: [], count: 0 })));
    expect(result.raw.tokens).toEqual({});
    expect(result.raw.styles).toEqual({ paint: [], text: [] });
    expect(result.dtcg).toEqual({});
    expect(result.bytes).toBe(JSON.stringify({ raw: result.raw, dtcg: result.dtcg }).length);
  });

  it('skips a collection that is missing from the file but still lists it in meta', async () => {
    const data = createMockFigmaData();
    data.collections = data.collections.filter(c => c.name !== '4. Canvas');
    const { result } = await runFigmaScript(SCRIPT_PATH, createMockFigmaAPI(data));
    expect(result.raw.meta.collections.find(c => c.name === '4. Canvas')).toEqual({ name: '4. Canvas', modes: [], count: 0 });
    expect(result.raw.tokens).not.toHaveProperty('4. Canvas');
    expect(result.dtcg).not.toHaveProperty('4. Canvas');
    expect(Object.keys(result.raw.tokens)).toEqual(NAMES.filter(n => n !== '4. Canvas'));
  });

  it('ignores variables that belong to a collection outside the five AZMX tiers', async () => {
    const data = createMockFigmaData();
    data.collections.push({ id: 'colX', name: 'Scratch', modes: [{ modeId: 'mx', name: 'Default' }] });
    data.variables.push({
      id: 'vx', name: 'scratch/thing', variableCollectionId: 'colX', resolvedType: 'FLOAT',
      scopes: [], hiddenFromPublishing: false, description: '', valuesByMode: { mx: 1 },
    });
    const { result } = await runFigmaScript(SCRIPT_PATH, createMockFigmaAPI(data));
    expect(Object.keys(result.raw.tokens)).toEqual(NAMES);
    expect(JSON.stringify(result)).not.toContain('scratch/thing');
  });

  it('propagates a rejected Figma API call', async () => {
    const figma = createMockFigmaAPI(createMockFigmaData());
    figma.variables.getLocalVariablesAsync.mockRejectedValue(new Error('plugin sandbox timeout'));
    await expect(runFigmaScript(SCRIPT_PATH, figma)).rejects.toThrow('plugin sandbox timeout');
  });
});
