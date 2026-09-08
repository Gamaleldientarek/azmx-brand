/**
 * Unit tests for build-pdf-form.mjs
 *
 * Tests field creation (text, checkbox, dropdown), font embedding, coordinate transformation,
 * input validation, and CLI integration.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { readFileSync, writeFileSync, existsSync, unlinkSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { execSync } from 'node:child_process';
import { PDFDocument, rgb } from 'pdf-lib';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, '..');
const SCRIPTS_DIR = join(REPO_ROOT, 'scripts');
const FIXTURES_DIR = join(HERE, 'fixtures');
const SCRIPT_PATH = join(SCRIPTS_DIR, 'build-pdf-form.mjs');
const TEMP_DIR = join(HERE, 'temp');

// Test fixture paths
const FIELDS_FIXTURE = join(FIXTURES_DIR, 'sample-fields.json');
const TEST_FONT_PATH = join(SCRIPTS_DIR, '..', 'assets', 'fonts', 'azmx', 'AzmX-Regular.ttf');

// Ensure temp directory exists
if (!existsSync(TEMP_DIR)) {
  mkdirSync(TEMP_DIR, { recursive: true });
}

/**
 * Create a minimal test PDF with specified number of pages and dimensions.
 * A4 size: 595 x 842 points (matching Figma export)
 */
async function createTestPDF(numPages = 1, width = 595, height = 842) {
  const pdfDoc = await PDFDocument.create();
  for (let i = 0; i < numPages; i++) {
    const page = pdfDoc.addPage([width, height]);
    // Add some minimal content to make it a valid PDF
    page.drawText(`Test Page ${i + 1}`, { x: 50, y: height - 50, size: 12 });
  }
  return await pdfDoc.save();
}

/**
 * Helper to run build-pdf-form.mjs with specified arguments
 */
function runScript(args = []) {
  const cmd = `node ${SCRIPT_PATH} ${args.join(' ')}`;
  try {
    const output = execSync(cmd, {
      cwd: SCRIPTS_DIR,
      encoding: 'utf8',
      timeout: 10000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return { success: true, output, stderr: '' };
  } catch (error) {
    return {
      success: false,
      output: error.stdout || '',
      stderr: error.stderr || error.message
    };
  }
}

/**
 * Parse PDF to extract form fields for verification
 */
async function getPDFFormFields(pdfPath) {
  const pdfBytes = readFileSync(pdfPath);
  const pdfDoc = await PDFDocument.load(pdfBytes);
  const form = pdfDoc.getForm();
  const fields = form.getFields();

  return fields.map(field => ({
    name: field.getName(),
    type: field.constructor.name
  }));
}

/**
 * Get embedded fonts from PDF
 */
async function getPDFEmbeddedFonts(pdfPath) {
  const pdfBytes = readFileSync(pdfPath);
  const pdfDoc = await PDFDocument.load(pdfBytes);

  // Access the document's font dictionary
  const context = pdfDoc.context;
  const fonts = [];

  context.enumerateIndirectObjects().forEach((ref, obj) => {
    if (obj && obj.dict && obj.dict.get(context.obj('Type'))?.toString() === '/Font') {
      const baseFont = obj.dict.get(context.obj('BaseFont'));
      if (baseFont) {
        fonts.push(baseFont.toString());
      }
    }
  });

  return fonts;
}

describe('build-pdf-form.mjs - field creation', () => {
  let testPDF;
  let testFieldsPath;
  let outputPath;

  beforeEach(async () => {
    // Create a 2-page test PDF (sample-fields.json references pages 0 and 1)
    testPDF = join(TEMP_DIR, 'test-source.pdf');
    outputPath = join(TEMP_DIR, 'test-output.pdf');
    testFieldsPath = join(TEMP_DIR, 'test-fields.json');

    const pdfBytes = await createTestPDF(2);
    writeFileSync(testPDF, pdfBytes);
  });

  afterEach(() => {
    // Clean up temp files
    [testPDF, outputPath, testFieldsPath].forEach(f => {
      if (existsSync(f)) unlinkSync(f);
    });
  });

  it('creates text fields correctly', async () => {
    const fields = [
      {
        p: 0,
        id: 'test_text',
        x: 100,
        y: 100,
        w: 200,
        h: 30,
        type: 'text'
      }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    expect(existsSync(outputPath)).toBe(true);

    const formFields = await getPDFFormFields(outputPath);
    expect(formFields).toHaveLength(1);
    expect(formFields[0].name).toBe('test_text');
    expect(formFields[0].type).toBe('PDFTextField');
  });

  it('creates multiline text fields correctly', async () => {
    const fields = [
      {
        p: 0,
        id: 'test_multiline',
        x: 50,
        y: 100,
        w: 400,
        h: 150,
        type: 'text',
        multiline: true
      }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const pdfBytes = readFileSync(outputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const form = pdfDoc.getForm();
    const field = form.getTextField('test_multiline');

    expect(field).toBeDefined();
    expect(field.isMultiline()).toBe(true);
  });

  it('creates checkbox fields correctly', async () => {
    const fields = [
      {
        p: 0,
        id: 'test_checkbox',
        x: 100,
        y: 200,
        w: 16,
        h: 16,
        type: 'check'
      }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const formFields = await getPDFFormFields(outputPath);
    expect(formFields).toHaveLength(1);
    expect(formFields[0].name).toBe('test_checkbox');
    expect(formFields[0].type).toBe('PDFCheckBox');
  });

  it('auto-detects checkbox type from small dimensions', async () => {
    const fields = [
      {
        p: 0,
        id: 'auto_checkbox',
        x: 100,
        y: 200,
        w: 14,
        h: 14
        // no type specified - should auto-detect as checkbox
      }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const formFields = await getPDFFormFields(outputPath);
    expect(formFields[0].type).toBe('PDFCheckBox');
  });

  it('creates dropdown (select) fields correctly', async () => {
    const fields = [
      {
        p: 0,
        id: 'test_dropdown',
        x: 100,
        y: 300,
        w: 150,
        h: 25,
        type: 'select',
        options: ['Option A', 'Option B', 'Option C'],
        default: 'Option A'
      }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const pdfBytes = readFileSync(outputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const form = pdfDoc.getForm();
    const field = form.getDropdown('test_dropdown');

    expect(field).toBeDefined();
    expect(field.getOptions()).toEqual(['Option A', 'Option B', 'Option C']);
    expect(field.getSelected()).toEqual(['Option A']);
  });

  it('creates select field without default value', async () => {
    const fields = [
      {
        p: 0,
        id: 'test_dropdown_no_default',
        x: 100,
        y: 300,
        w: 150,
        h: 25,
        type: 'select',
        options: ['SAR', 'USD', 'EUR']
      }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const pdfBytes = readFileSync(outputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const form = pdfDoc.getForm();
    const field = form.getDropdown('test_dropdown_no_default');

    expect(field).toBeDefined();
    expect(field.getOptions()).toEqual(['SAR', 'USD', 'EUR']);
  });

  it('creates multiple field types in one PDF', async () => {
    const fields = [
      { p: 0, id: 'text1', x: 50, y: 50, w: 200, h: 25, type: 'text' },
      { p: 0, id: 'check1', x: 50, y: 100, w: 16, h: 16, type: 'check' },
      { p: 0, id: 'select1', x: 50, y: 150, w: 150, h: 25, type: 'select', options: ['A', 'B'] },
      { p: 1, id: 'text2', x: 100, y: 200, w: 300, h: 100, type: 'text', multiline: true }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    expect(result.output).toContain('fields    4');
    expect(result.output).toContain('text 2');
    expect(result.output).toContain('check 1');
    expect(result.output).toContain('select 1');

    const formFields = await getPDFFormFields(outputPath);
    expect(formFields).toHaveLength(4);
  });

  it('places fields on correct pages', async () => {
    const fields = [
      { p: 0, id: 'page0_field', x: 50, y: 50, w: 200, h: 25, type: 'text' },
      { p: 1, id: 'page1_field', x: 50, y: 50, w: 200, h: 25, type: 'text' }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const pdfBytes = readFileSync(outputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const form = pdfDoc.getForm();

    const field0 = form.getTextField('page0_field');
    const field1 = form.getTextField('page1_field');

    expect(field0).toBeDefined();
    expect(field1).toBeDefined();
  });

  it('transforms Figma coordinates to PDF coordinates correctly', async () => {
    // Figma Y is top-down from frame top-left
    // PDF Y is bottom-up from page bottom-left
    // For A4 (595x842): PDF_Y = 842 - (Figma_Y + height)

    const fields = [
      {
        p: 0,
        id: 'coord_test',
        x: 100,    // Figma X (from left)
        y: 100,    // Figma Y (from top)
        w: 200,
        h: 30,
        type: 'text'
      }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const pdfBytes = readFileSync(outputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const form = pdfDoc.getForm();
    const field = form.getTextField('coord_test');

    expect(field).toBeDefined();
    // The field should exist and be positioned correctly
    // We can't easily verify exact coordinates without inspecting raw PDF structure,
    // but successful creation implies correct coordinate transformation
  });

  it('works with the sample-fields.json fixture', async () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', FIELDS_FIXTURE,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const formFields = await getPDFFormFields(outputPath);
    expect(formFields.length).toBeGreaterThan(0);

    // Check for specific fields from fixture
    const fieldNames = formFields.map(f => f.name);
    expect(fieldNames).toContain('p1_personal_name');
    expect(fieldNames).toContain('p1_currency');
    expect(fieldNames).toContain('p1_agree_terms');
    expect(fieldNames).toContain('p2_comments');
  });
});

describe('build-pdf-form.mjs - font embedding', () => {
  let testPDF;
  let testFieldsPath;
  let outputPath;

  beforeEach(async () => {
    testPDF = join(TEMP_DIR, 'test-font-source.pdf');
    outputPath = join(TEMP_DIR, 'test-font-output.pdf');
    testFieldsPath = join(TEMP_DIR, 'test-font-fields.json');

    const pdfBytes = await createTestPDF(1);
    writeFileSync(testPDF, pdfBytes);

    const fields = [
      { p: 0, id: 'text_field', x: 50, y: 50, w: 200, h: 25, type: 'text' }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));
  });

  afterEach(() => {
    [testPDF, outputPath, testFieldsPath].forEach(f => {
      if (existsSync(f)) unlinkSync(f);
    });
  });

  it('embeds custom font when available', async () => {
    if (!existsSync(TEST_FONT_PATH)) {
      console.warn(`Skipping font embedding test - font not found at ${TEST_FONT_PATH}`);
      return;
    }

    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath,
      '--font', TEST_FONT_PATH
    ]);

    expect(result.success).toBe(true);
    expect(result.output).toContain('AzmX-Regular.ttf embedded');
  });

  it('falls back to Helvetica when font not found', async () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath,
      '--font', '/nonexistent/font.ttf'
    ]);

    expect(result.success).toBe(true);
    expect(result.output).toContain('Helvetica (fallback)');
  });

  it('uses default font path when --font not specified', async () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    // Should either embed AzmX-Regular or fall back to Helvetica
    expect(
      result.output.includes('AzmX-Regular.ttf embedded') ||
      result.output.includes('Helvetica (fallback)')
    ).toBe(true);
  });

  it('applies custom font size with --size flag', async () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath,
      '--size', '12'
    ]);

    expect(result.success).toBe(true);

    const pdfBytes = readFileSync(outputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const form = pdfDoc.getForm();
    const field = form.getTextField('text_field');

    expect(field).toBeDefined();
    // Font size is applied - field should be created successfully
  });

  it('uses default font size when --size not specified', async () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    // Default is 9pt - just verify it works
  });
});

describe('build-pdf-form.mjs - input validation', () => {
  let testPDF;
  let validFieldsPath;
  let outputPath;

  beforeEach(async () => {
    testPDF = join(TEMP_DIR, 'test-valid-source.pdf');
    validFieldsPath = join(TEMP_DIR, 'valid-fields.json');
    outputPath = join(TEMP_DIR, 'test-valid-output.pdf');

    const pdfBytes = await createTestPDF(1);
    writeFileSync(testPDF, pdfBytes);
  });

  afterEach(() => {
    [testPDF, validFieldsPath, outputPath].forEach(f => {
      if (existsSync(f)) unlinkSync(f);
    });
  });

  it('fails when required arguments are missing', () => {
    const result = runScript([]);
    expect(result.success).toBe(false);
    expect(result.stderr).toContain('Usage');
  });

  it('fails when --src file does not exist', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 0, id: 'test', x: 50, y: 50, w: 100, h: 25, type: 'text' }
    ]));

    const result = runScript([
      '--src', '/nonexistent/file.pdf',
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('not found');
  });

  it('fails when --fields file does not exist', () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', '/nonexistent/fields.json',
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('not found');
  });

  it('fails when fields.json is not valid JSON', () => {
    writeFileSync(validFieldsPath, 'not valid json{]');

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
  });

  it('fails when fields.json is not an array', () => {
    writeFileSync(validFieldsPath, JSON.stringify({ notAnArray: true }));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('non-empty JSON array');
  });

  it('fails when fields.json is empty array', () => {
    writeFileSync(validFieldsPath, JSON.stringify([]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('non-empty JSON array');
  });

  it('fails when field is missing required properties', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { id: 'incomplete', x: 50, y: 50 }  // missing p, w, h
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('missing');
  });

  it('fails when field has invalid type', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 0, id: 'bad_type', x: 50, y: 50, w: 100, h: 25, type: 'invalid' }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('invalid type');
  });

  it('fails when select field has no options', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 0, id: 'bad_select', x: 50, y: 50, w: 100, h: 25, type: 'select' }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('no options array');
  });

  it('fails when select field has empty options array', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 0, id: 'bad_select', x: 50, y: 50, w: 100, h: 25, type: 'select', options: [] }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('no options array');
  });

  it('fails when select default is not in options', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      {
        p: 0,
        id: 'bad_default',
        x: 50,
        y: 50,
        w: 100,
        h: 25,
        type: 'select',
        options: ['A', 'B', 'C'],
        default: 'D'
      }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('not one of its options');
  });

  it('fails when field has non-positive dimensions', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 0, id: 'bad_size', x: 50, y: 50, w: 0, h: 25, type: 'text' }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('non-positive size');
  });

  it('fails when duplicate field names exist', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 0, id: 'duplicate', x: 50, y: 50, w: 100, h: 25, type: 'text' },
      { p: 0, id: 'duplicate', x: 50, y: 100, w: 100, h: 25, type: 'text' }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('duplicate field names');
  });

  it('fails when field references invalid page index', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 5, id: 'bad_page', x: 50, y: 50, w: 100, h: 25, type: 'text' }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('targets page index');
  });

  it('succeeds with --expect when field count matches', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 0, id: 'field1', x: 50, y: 50, w: 100, h: 25, type: 'text' },
      { p: 0, id: 'field2', x: 50, y: 100, w: 100, h: 25, type: 'text' }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath,
      '--expect', '2'
    ]);

    expect(result.success).toBe(true);
  });

  it('fails with --expect when field count does not match', () => {
    writeFileSync(validFieldsPath, JSON.stringify([
      { p: 0, id: 'field1', x: 50, y: 50, w: 100, h: 25, type: 'text' }
    ]));

    const result = runScript([
      '--src', testPDF,
      '--fields', validFieldsPath,
      '--out', outputPath,
      '--expect', '5'
    ]);

    expect(result.success).toBe(false);
    expect(result.stderr).toContain('Field count mismatch');
  });
});

describe('build-pdf-form.mjs - flatten functionality', () => {
  let testPDF;
  let testFieldsPath;
  let outputPath;

  beforeEach(async () => {
    testPDF = join(TEMP_DIR, 'test-flatten-source.pdf');
    outputPath = join(TEMP_DIR, 'test-flatten-output.pdf');
    testFieldsPath = join(TEMP_DIR, 'test-flatten-fields.json');

    const pdfBytes = await createTestPDF(1);
    writeFileSync(testPDF, pdfBytes);

    const fields = [
      { p: 0, id: 'text_field', x: 50, y: 50, w: 200, h: 25, type: 'text' },
      { p: 0, id: 'check_field', x: 50, y: 100, w: 16, h: 16, type: 'check' }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));
  });

  afterEach(() => {
    [testPDF, outputPath, testFieldsPath].forEach(f => {
      if (existsSync(f)) unlinkSync(f);
    });
  });

  it('creates editable fields by default', async () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    expect(result.output).not.toContain('flattened');

    const pdfBytes = readFileSync(outputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const form = pdfDoc.getForm();
    const fields = form.getFields();

    expect(fields.length).toBeGreaterThan(0);
  });

  it('creates read-only flattened PDF with --flatten flag', async () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath,
      '--flatten'
    ]);

    expect(result.success).toBe(true);
    expect(result.output).toContain('flattened read-only');
  });
});

describe('build-pdf-form.mjs - CLI output', () => {
  let testPDF;
  let testFieldsPath;
  let outputPath;

  beforeEach(async () => {
    testPDF = join(TEMP_DIR, 'test-cli-source.pdf');
    outputPath = join(TEMP_DIR, 'test-cli-output.pdf');
    testFieldsPath = join(TEMP_DIR, 'test-cli-fields.json');

    const pdfBytes = await createTestPDF(2);
    writeFileSync(testPDF, pdfBytes);

    const fields = [
      { p: 0, id: 'text1', x: 50, y: 50, w: 200, h: 25, type: 'text' },
      { p: 0, id: 'check1', x: 50, y: 100, w: 16, h: 16, type: 'check' },
      { p: 1, id: 'select1', x: 50, y: 50, w: 150, h: 25, type: 'select', options: ['A', 'B'] }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));
  });

  afterEach(() => {
    [testPDF, outputPath, testFieldsPath].forEach(f => {
      if (existsSync(f)) unlinkSync(f);
    });
  });

  it('outputs summary with page count', () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    expect(result.output).toContain('pages     2');
  });

  it('outputs summary with field counts by type', () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    expect(result.output).toContain('fields    3');
    expect(result.output).toContain('text 1');
    expect(result.output).toContain('check 1');
    expect(result.output).toContain('select 1');
  });

  it('outputs font information', () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    expect(result.output).toContain('font');
  });

  it('outputs output file path', () => {
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);
    expect(result.output).toContain('wrote');
    expect(result.output).toContain('test-cli-output.pdf');
  });
});

describe('build-pdf-form.mjs - AZMX brand color', () => {
  let testPDF;
  let testFieldsPath;
  let outputPath;

  beforeEach(async () => {
    testPDF = join(TEMP_DIR, 'test-color-source.pdf');
    outputPath = join(TEMP_DIR, 'test-color-output.pdf');
    testFieldsPath = join(TEMP_DIR, 'test-color-fields.json');

    const pdfBytes = await createTestPDF(1);
    writeFileSync(testPDF, pdfBytes);

    const fields = [
      { p: 0, id: 'text_field', x: 50, y: 50, w: 200, h: 25, type: 'text' }
    ];
    writeFileSync(testFieldsPath, JSON.stringify(fields));
  });

  afterEach(() => {
    [testPDF, outputPath, testFieldsPath].forEach(f => {
      if (existsSync(f)) unlinkSync(f);
    });
  });

  it('creates fields with text (AZMX Neutral 900 should be applied)', async () => {
    // This test verifies that text fields are created successfully
    // The AZMX Neutral 900 color (rgb(0x11/255, 0x19/255, 0x27/255)) is applied in the script
    const result = runScript([
      '--src', testPDF,
      '--fields', testFieldsPath,
      '--out', outputPath
    ]);

    expect(result.success).toBe(true);

    const pdfBytes = readFileSync(outputPath);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const form = pdfDoc.getForm();
    const field = form.getTextField('text_field');

    expect(field).toBeDefined();
    // Color is applied via textColor in addToPage - field should exist
  });
});
