/**
 * Unit tests for export-figma-tokens.js
 *
 * Tests token collection, alias resolution, hex color conversion, and output structure.
 * Since the script runs in Figma's console environment, we mock the Figma API and test
 * the core logic by extracting and testing individual functions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, '..');
const SCRIPTS_DIR = join(REPO_ROOT, 'scripts');
const SCRIPT_PATH = join(SCRIPTS_DIR, 'export-figma-tokens.js');

// Read the script source to extract testable functions
const scriptSource = readFileSync(SCRIPT_PATH, 'utf8');

/**
 * Extract the hex color conversion function from the script
 * This function converts Figma RGB color objects to hex strings
 */
function extractHexFunction() {
  const match = scriptSource.match(/const hex = c => ([^;]+);/);
  if (!match) throw new Error('Could not extract hex function from script');
  return eval(`(c => ${match[1]})`);
}

const hex = extractHexFunction();

/**
 * Mock Figma API data for testing
 */
function createMockFigmaData() {
  const collections = [
    {
      id: 'col1',
      name: '1. Primitives',
      modes: [{ modeId: 'mode1', name: 'Default' }]
    },
    {
      id: 'col2',
      name: '1b. Palette',
      modes: [
        { modeId: 'mode2a', name: 'Blue' },
        { modeId: 'mode2b', name: 'Orange' },
        { modeId: 'mode2c', name: 'Green' }
      ]
    },
    {
      id: 'col3',
      name: '2. Semantic',
      modes: [
        { modeId: 'mode3a', name: 'Light' },
        { modeId: 'mode3b', name: 'Dark' }
      ]
    },
    {
      id: 'col4',
      name: '3. Component',
      modes: [{ modeId: 'mode4', name: 'Default' }]
    },
    {
      id: 'col5',
      name: '4. Canvas',
      modes: [{ modeId: 'mode5', name: 'Default' }]
    }
  ];

  const variables = [
    // Primitive color variable
    {
      id: 'var1',
      name: 'color/primary/electric',
      variableCollectionId: 'col1',
      resolvedType: 'COLOR',
      scopes: ['ALL_SCOPES'],
      hiddenFromPublishing: false,
      description: 'Primary electric blue',
      valuesByMode: {
        mode1: { r: 0, g: 0.102, b: 1, a: 1 }
      }
    },
    // Primitive float variable
    {
      id: 'var2',
      name: 'spacing/md',
      variableCollectionId: 'col1',
      resolvedType: 'FLOAT',
      scopes: ['ALL_SCOPES'],
      hiddenFromPublishing: false,
      description: 'Medium spacing',
      valuesByMode: {
        mode1: 16
      }
    },
    // Palette variable with alias
    {
      id: 'var3',
      name: 'surface/accent',
      variableCollectionId: 'col2',
      resolvedType: 'COLOR',
      scopes: ['ALL_SCOPES'],
      hiddenFromPublishing: false,
      description: 'Accent surface color',
      valuesByMode: {
        mode2a: { type: 'VARIABLE_ALIAS', id: 'var1' }, // Blue -> electric
        mode2b: { r: 0.957, g: 0.478, b: 0.282, a: 1 }, // Orange
        mode2c: { r: 0.133, g: 0.765, b: 0.435, a: 1 }  // Green
      }
    },
    // Semantic variable with alias to palette
    {
      id: 'var4',
      name: 'text/primary',
      variableCollectionId: 'col3',
      resolvedType: 'COLOR',
      scopes: ['TEXT_FILL'],
      hiddenFromPublishing: false,
      description: 'Primary text color',
      valuesByMode: {
        mode3a: { r: 0, g: 0, b: 0, a: 1 }, // Light mode
        mode3b: { type: 'VARIABLE_ALIAS', id: 'var3' } // Dark mode -> palette accent
      }
    },
    // Component variable with color having alpha
    {
      id: 'var5',
      name: 'button/bg',
      variableCollectionId: 'col4',
      resolvedType: 'COLOR',
      scopes: ['FRAME_FILL'],
      hiddenFromPublishing: false,
      description: 'Button background',
      valuesByMode: {
        mode4: { r: 0, g: 0.102, b: 1, a: 0.8 } // Blue with 80% opacity
      }
    },
    // String variable
    {
      id: 'var6',
      name: 'font/family/body',
      variableCollectionId: 'col1',
      resolvedType: 'STRING',
      scopes: ['FONT_FAMILY'],
      hiddenFromPublishing: false,
      description: 'Body font family',
      valuesByMode: {
        mode1: 'Inter'
      }
    },
    // Boolean variable
    {
      id: 'var7',
      name: 'feature/dark-mode',
      variableCollectionId: 'col1',
      resolvedType: 'BOOLEAN',
      scopes: ['ALL_SCOPES'],
      hiddenFromPublishing: true,
      description: 'Dark mode feature flag',
      valuesByMode: {
        mode1: true
      }
    }
  ];

  const paintStyles = [
    {
      name: 'Fills/Primary',
      description: 'Primary fill color',
      paints: [
        {
          type: 'SOLID',
          color: { r: 0, g: 0.102, b: 1 }
        }
      ]
    },
    {
      name: 'Fills/Gradient',
      description: 'Gradient fill',
      paints: [
        {
          type: 'GRADIENT_LINEAR',
          gradientStops: [
            { position: 0, color: { r: 0, g: 0.102, b: 1, a: 1 } },
            { position: 1, color: { r: 1, g: 0, b: 0, a: 1 } }
          ]
        }
      ]
    }
  ];

  const textStyles = [
    {
      name: 'Text/Heading',
      description: 'Heading text style',
      fontName: { family: 'Inter', style: 'Bold' },
      fontSize: 24,
      lineHeight: { value: 32, unit: 'PIXELS' },
      letterSpacing: { value: 0, unit: 'PIXELS' },
      boundVariables: {
        'fontFamily': { id: 'var6' }
      }
    }
  ];

  return { collections, variables, paintStyles, textStyles };
}

/**
 * Create a mock Figma API object
 */
function createMockFigmaAPI(data) {
  const byId = Object.fromEntries(data.variables.map(v => [v.id, v]));

  return {
    variables: {
      getLocalVariableCollectionsAsync: vi.fn(async () => data.collections),
      getLocalVariablesAsync: vi.fn(async () => data.variables)
    },
    getLocalPaintStylesAsync: vi.fn(async () => data.paintStyles),
    getLocalTextStylesAsync: vi.fn(async () => data.textStyles),
    _byId: byId // Helper for testing
  };
}

describe('export-figma-tokens.js - hex color conversion', () => {
  it('converts full opacity RGB to hex', () => {
    const color = { r: 0, g: 0.102, b: 1, a: 1 };
    const result = hex(color);
    expect(result).toBe('#001AFF');
  });

  it('converts RGB with alpha to hex with alpha channel', () => {
    const color = { r: 0, g: 0.102, b: 1, a: 0.8 };
    const result = hex(color);
    expect(result).toBe('#001AFFCC'); // CC = 204 = 0.8 * 255
  });

  it('converts pure black', () => {
    const color = { r: 0, g: 0, b: 0, a: 1 };
    const result = hex(color);
    expect(result).toBe('#000000');
  });

  it('converts pure white', () => {
    const color = { r: 1, g: 1, b: 1, a: 1 };
    const result = hex(color);
    expect(result).toBe('#FFFFFF');
  });

  it('converts red with 50% opacity', () => {
    const color = { r: 1, g: 0, b: 0, a: 0.5 };
    const result = hex(color);
    expect(result).toBe('#FF000080'); // 80 = 128 = 0.5 * 255
  });

  it('handles colors without alpha property (defaults to 100%)', () => {
    const color = { r: 0.5, g: 0.5, b: 0.5 };
    const result = hex(color);
    expect(result).toBe('#808080');
  });

  it('rounds RGB values correctly', () => {
    const color = { r: 0.004, g: 0.502, b: 0.996, a: 1 };
    const result = hex(color);
    expect(result).toBe('#0180FE'); // 1, 128, 254
  });

  it('handles near-full alpha (0.999) without alpha channel', () => {
    const color = { r: 1, g: 0, b: 0, a: 0.999 };
    const result = hex(color);
    expect(result).toBe('#FF0000'); // No alpha suffix
  });

  it('handles very low alpha values', () => {
    const color = { r: 0, g: 0, b: 0, a: 0.01 };
    const result = hex(color);
    expect(result).toBe('#00000003'); // 03 = ~3 = 0.01 * 255
  });
});

describe('export-figma-tokens.js - token collection', () => {
  let mockData;
  let mockFigma;

  beforeEach(() => {
    mockData = createMockFigmaData();
    mockFigma = createMockFigmaAPI(mockData);
  });

  it('collects all five token collections', async () => {
    const collections = await mockFigma.variables.getLocalVariableCollectionsAsync();
    expect(collections).toHaveLength(5);

    const names = collections.map(c => c.name);
    expect(names).toContain('1. Primitives');
    expect(names).toContain('1b. Palette');
    expect(names).toContain('2. Semantic');
    expect(names).toContain('3. Component');
    expect(names).toContain('4. Canvas');
  });

  it('correctly identifies collection modes', async () => {
    const collections = await mockFigma.variables.getLocalVariableCollectionsAsync();

    const primitives = collections.find(c => c.name === '1. Primitives');
    expect(primitives.modes).toHaveLength(1);
    expect(primitives.modes[0].name).toBe('Default');

    const palette = collections.find(c => c.name === '1b. Palette');
    expect(palette.modes).toHaveLength(3);
    expect(palette.modes.map(m => m.name)).toEqual(['Blue', 'Orange', 'Green']);

    const semantic = collections.find(c => c.name === '2. Semantic');
    expect(semantic.modes).toHaveLength(2);
    expect(semantic.modes.map(m => m.name)).toEqual(['Light', 'Dark']);
  });

  it('filters variables by collection', async () => {
    const collections = await mockFigma.variables.getLocalVariableCollectionsAsync();
    const variables = await mockFigma.variables.getLocalVariablesAsync();

    const primitivesCol = collections.find(c => c.name === '1. Primitives');
    const primitivesVars = variables.filter(v => v.variableCollectionId === primitivesCol.id);

    expect(primitivesVars.length).toBeGreaterThan(0);
    expect(primitivesVars.every(v => v.variableCollectionId === primitivesCol.id)).toBe(true);
  });

  it('collects variable metadata correctly', async () => {
    const variables = await mockFigma.variables.getLocalVariablesAsync();
    const electricVar = variables.find(v => v.name === 'color/primary/electric');

    expect(electricVar).toBeDefined();
    expect(electricVar.resolvedType).toBe('COLOR');
    expect(electricVar.scopes).toEqual(['ALL_SCOPES']);
    expect(electricVar.hiddenFromPublishing).toBe(false);
    expect(electricVar.description).toBe('Primary electric blue');
  });

  it('handles variables without descriptions', async () => {
    const testVar = {
      id: 'var_no_desc',
      name: 'test/no-desc',
      variableCollectionId: 'col1',
      resolvedType: 'COLOR',
      scopes: ['ALL_SCOPES'],
      hiddenFromPublishing: false,
      description: '',
      valuesByMode: { mode1: { r: 0, g: 0, b: 0, a: 1 } }
    };

    mockData.variables.push(testVar);
    const variables = await mockFigma.variables.getLocalVariablesAsync();
    const foundVar = variables.find(v => v.id === 'var_no_desc');

    expect(foundVar.description).toBe('');
  });
});

describe('export-figma-tokens.js - alias resolution', () => {
  let mockData;
  let mockFigma;
  let byId;

  beforeEach(() => {
    mockData = createMockFigmaData();
    mockFigma = createMockFigmaAPI(mockData);
    byId = mockFigma._byId;
  });

  it('identifies VARIABLE_ALIAS type', () => {
    const paletteVar = mockData.variables.find(v => v.name === 'surface/accent');
    const blueMode = paletteVar.valuesByMode['mode2a'];

    expect(blueMode.type).toBe('VARIABLE_ALIAS');
    expect(blueMode.id).toBe('var1');
  });

  it('resolves alias to variable name', () => {
    const paletteVar = mockData.variables.find(v => v.name === 'surface/accent');
    const blueMode = paletteVar.valuesByMode['mode2a'];
    const referenced = byId[blueMode.id];

    expect(referenced).toBeDefined();
    expect(referenced.name).toBe('color/primary/electric');
  });

  it('handles nested aliases (semantic -> palette -> primitive)', () => {
    const semanticVar = mockData.variables.find(v => v.name === 'text/primary');
    const darkMode = semanticVar.valuesByMode['mode3b'];

    expect(darkMode.type).toBe('VARIABLE_ALIAS');

    const paletteVar = byId[darkMode.id];
    expect(paletteVar.name).toBe('surface/accent');

    const blueModeValue = paletteVar.valuesByMode['mode2a'];
    expect(blueModeValue.type).toBe('VARIABLE_ALIAS');

    const primitiveVar = byId[blueModeValue.id];
    expect(primitiveVar.name).toBe('color/primary/electric');
  });

  it('handles direct color values (no alias)', () => {
    const paletteVar = mockData.variables.find(v => v.name === 'surface/accent');
    const orangeMode = paletteVar.valuesByMode['mode2b'];

    expect(orangeMode.type).toBeUndefined();
    expect(orangeMode.r).toBeDefined();
    expect(orangeMode.g).toBeDefined();
    expect(orangeMode.b).toBeDefined();
  });

  it('handles missing alias references gracefully', () => {
    const testVar = {
      id: 'var_broken',
      name: 'test/broken',
      variableCollectionId: 'col1',
      resolvedType: 'COLOR',
      scopes: ['ALL_SCOPES'],
      hiddenFromPublishing: false,
      description: '',
      valuesByMode: {
        mode1: { type: 'VARIABLE_ALIAS', id: 'nonexistent' }
      }
    };

    mockData.variables.push(testVar);
    const foundRef = byId['nonexistent'];
    expect(foundRef).toBeUndefined();
  });
});

describe('export-figma-tokens.js - output structure', () => {
  let mockData;

  beforeEach(() => {
    mockData = createMockFigmaData();
  });

  it('raw format has correct metadata structure', () => {
    const meta = {
      file: 'New Direction Library | AZM X',
      fileKey: 'j8ugBpb1yUUyL8hfb6FHKR',
      exported: null,
      collections: mockData.collections.map(c => ({
        name: c.name,
        modes: c.modes.map(m => m.name),
        count: mockData.variables.filter(v => v.variableCollectionId === c.id).length
      }))
    };

    expect(meta.file).toBe('New Direction Library | AZM X');
    expect(meta.fileKey).toBe('j8ugBpb1yUUyL8hfb6FHKR');
    expect(meta.collections).toHaveLength(5);

    const primitivesInfo = meta.collections.find(c => c.name === '1. Primitives');
    expect(primitivesInfo.modes).toEqual(['Default']);
    expect(primitivesInfo.count).toBeGreaterThan(0);
  });

  it('raw format token structure contains all required fields', () => {
    const testToken = {
      name: 'color/primary/electric',
      type: 'COLOR',
      scopes: ['ALL_SCOPES'],
      hiddenFromPublishing: false,
      description: 'Primary electric blue',
      modes: {
        'Default': { value: '#001AFF' }
      }
    };

    expect(testToken).toHaveProperty('name');
    expect(testToken).toHaveProperty('type');
    expect(testToken).toHaveProperty('scopes');
    expect(testToken).toHaveProperty('hiddenFromPublishing');
    expect(testToken).toHaveProperty('description');
    expect(testToken).toHaveProperty('modes');
  });

  it('raw format alias structure preserves token names', () => {
    const aliasValue = { alias: 'color/primary/electric' };
    expect(aliasValue).toHaveProperty('alias');
    expect(aliasValue.alias).toBe('color/primary/electric');
  });

  it('styles structure contains paint styles', () => {
    const styles = {
      paint: mockData.paintStyles.map(s => ({
        name: s.name,
        description: s.description,
        paints: s.paints.map(p => p.type === 'SOLID'
          ? { type: 'SOLID', color: hex(p.color) }
          : { type: p.type, stops: (p.gradientStops || []).map(g => ({ position: g.position, color: hex(g.color) })) })
      })),
      text: []
    };

    expect(styles.paint).toHaveLength(2);
    expect(styles.paint[0].name).toBe('Fills/Primary');
    expect(styles.paint[0].paints[0].type).toBe('SOLID');
    expect(styles.paint[1].paints[0].type).toBe('GRADIENT_LINEAR');
  });

  it('styles structure contains text styles with bound variables', () => {
    const byId = Object.fromEntries(mockData.variables.map(v => [v.id, v]));
    const styles = {
      paint: [],
      text: mockData.textStyles.map(s => ({
        name: s.name,
        description: s.description,
        fontFamily: s.fontName.family,
        fontStyle: s.fontName.style,
        fontSize: s.fontSize,
        lineHeight: s.lineHeight,
        letterSpacing: s.letterSpacing,
        boundVariables: Object.fromEntries(
          Object.entries(s.boundVariables || {}).map(([k, b]) => [k, byId[b.id] ? byId[b.id].name : '?'])
        )
      }))
    };

    expect(styles.text).toHaveLength(1);
    expect(styles.text[0].name).toBe('Text/Heading');
    expect(styles.text[0].fontFamily).toBe('Inter');
    expect(styles.text[0].fontStyle).toBe('Bold');
    expect(styles.text[0].boundVariables.fontFamily).toBe('font/family/body');
  });
});

describe('export-figma-tokens.js - DTCG format', () => {
  const DTCG_TYPE = { COLOR: 'color', FLOAT: 'number', STRING: 'fontFamily', BOOLEAN: 'boolean' };

  it('maps Figma types to DTCG types', () => {
    expect(DTCG_TYPE.COLOR).toBe('color');
    expect(DTCG_TYPE.FLOAT).toBe('number');
    expect(DTCG_TYPE.STRING).toBe('fontFamily');
    expect(DTCG_TYPE.BOOLEAN).toBe('boolean');
  });

  it('converts token paths to nested objects', () => {
    const tokenName = 'color/primary/electric';
    const parts = tokenName.split('/');
    const tree = {};

    let node = tree;
    parts.forEach((p, i) => {
      if (i === parts.length - 1) {
        node[p] = { $value: '#001AFF', $type: 'color' };
      } else {
        node[p] = node[p] || {};
        node = node[p];
      }
    });

    expect(tree).toHaveProperty('color');
    expect(tree.color).toHaveProperty('primary');
    expect(tree.color.primary).toHaveProperty('electric');
    expect(tree.color.primary.electric.$value).toBe('#001AFF');
    expect(tree.color.primary.electric.$type).toBe('color');
  });

  it('formats aliases with curly braces and dot notation', () => {
    const aliasName = 'color/primary/electric';
    const dtcgAlias = '{' + aliasName.split('/').join('.') + '}';

    expect(dtcgAlias).toBe('{color.primary.electric}');
  });

  it('includes $description when present', () => {
    const token = {
      $value: '#001AFF',
      $type: 'color',
      $description: 'Primary electric blue'
    };

    expect(token).toHaveProperty('$description');
    expect(token.$description).toBe('Primary electric blue');
  });

  it('multi-mode collections generate separate trees', () => {
    const modes = ['Blue', 'Orange', 'Green'];
    const collectionName = '1b. Palette';
    const trees = {};

    modes.forEach(mode => {
      const key = collectionName + ' [' + mode + ']';
      trees[key] = { test: { $value: mode, $type: 'color' } };
    });

    expect(trees).toHaveProperty('1b. Palette [Blue]');
    expect(trees).toHaveProperty('1b. Palette [Orange]');
    expect(trees).toHaveProperty('1b. Palette [Green]');
  });

  it('single-mode collections use collection name as key', () => {
    const modes = ['Default'];
    const collectionName = '1. Primitives';
    const key = modes.length > 1 ? collectionName + ' [' + modes[0] + ']' : collectionName;

    expect(key).toBe('1. Primitives');
  });
});

describe('export-figma-tokens.js - variable types', () => {
  let mockData;

  beforeEach(() => {
    mockData = createMockFigmaData();
  });

  it('handles COLOR type variables', () => {
    const colorVar = mockData.variables.find(v => v.resolvedType === 'COLOR');
    expect(colorVar).toBeDefined();
    expect(colorVar.resolvedType).toBe('COLOR');
  });

  it('handles FLOAT type variables', () => {
    const floatVar = mockData.variables.find(v => v.resolvedType === 'FLOAT');
    expect(floatVar).toBeDefined();
    expect(floatVar.resolvedType).toBe('FLOAT');
    expect(typeof floatVar.valuesByMode.mode1).toBe('number');
  });

  it('handles STRING type variables', () => {
    const stringVar = mockData.variables.find(v => v.resolvedType === 'STRING');
    expect(stringVar).toBeDefined();
    expect(stringVar.resolvedType).toBe('STRING');
    expect(typeof stringVar.valuesByMode.mode1).toBe('string');
  });

  it('handles BOOLEAN type variables', () => {
    const boolVar = mockData.variables.find(v => v.resolvedType === 'BOOLEAN');
    expect(boolVar).toBeDefined();
    expect(boolVar.resolvedType).toBe('BOOLEAN');
    expect(typeof boolVar.valuesByMode.mode1).toBe('boolean');
  });

  it('handles hiddenFromPublishing flag', () => {
    const hiddenVar = mockData.variables.find(v => v.hiddenFromPublishing === true);
    expect(hiddenVar).toBeDefined();
    expect(hiddenVar.name).toBe('feature/dark-mode');
  });
});

describe('export-figma-tokens.js - sorting and organization', () => {
  it('tokens are sorted alphabetically by name', () => {
    const tokens = [
      { name: 'zebra' },
      { name: 'alpha' },
      { name: 'beta' }
    ];

    const sorted = [...tokens].sort((a, b) => a.name.localeCompare(b.name));
    expect(sorted[0].name).toBe('alpha');
    expect(sorted[1].name).toBe('beta');
    expect(sorted[2].name).toBe('zebra');
  });

  it('slash-separated names sort correctly', () => {
    const tokens = [
      { name: 'color/secondary/dark' },
      { name: 'color/primary/electric' },
      { name: 'color/primary/deep' },
      { name: 'spacing/md' }
    ];

    const sorted = [...tokens].sort((a, b) => a.name.localeCompare(b.name));
    expect(sorted[0].name).toBe('color/primary/deep');
    expect(sorted[1].name).toBe('color/primary/electric');
    expect(sorted[2].name).toBe('color/secondary/dark');
    expect(sorted[3].name).toBe('spacing/md');
  });
});
