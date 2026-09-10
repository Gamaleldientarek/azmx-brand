/**
 * Tests for the two Figma console scripts:
 *   scripts/extract-figma-fields.js     — form-field rectangles -> fields.json
 *   scripts/figma-slide-transitions.js  — wires Space/Backspace reactions on a deck
 *
 * Both run in Figma's plugin console (top-level await, bare return), so each
 * test evaluates the REAL source through tests/helpers/figma-console.js with a
 * mock `figma` global and asserts on the returned value and on what the script
 * did to the mock (pages selected, reactions set, flow start assigned).
 *
 * The scripts' "edit these" constants (PAGE_NAME, FRAME_PREFIX, ORDER) are
 * overridden per scenario via the harness; everything else runs as committed.
 */

import { describe, it, expect, vi } from 'vitest';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { runFigmaScript } from './helpers/figma-console.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPTS_DIR = join(HERE, '..', 'scripts');
const EXTRACT_FIELDS_PATH = join(SCRIPTS_DIR, 'extract-figma-fields.js');
const TRANSITIONS_PATH = join(SCRIPTS_DIR, 'figma-slide-transitions.js');

// ---------------------------------------------------------------------------
// extract-figma-fields.js
// ---------------------------------------------------------------------------

/** A rectangle child: { name, x, y, w, h } (w/h become width/height). */
function rect(name, x, y, w, h, extra = {}) {
  return { name, type: 'RECTANGLE', x, y, width: w, height: h, ...extra };
}

function frame(name, x, y, children = [], width = 595, height = 842) {
  return { name, type: 'FRAME', x, y, width, height, children };
}

function page(name, children = []) {
  return { name, type: 'PAGE', children };
}

function createFieldsFigma(pages) {
  return {
    root: { children: pages },
    loadAllPagesAsync: vi.fn(async () => {}),
    setCurrentPageAsync: vi.fn(async () => {}),
  };
}

// Defaults shipped in the script: PAGE_NAME 'HR', FRAME_PREFIX 'Employee Information'.
const HR = 'HR';
const PREFIX = 'Employee Information';

async function extract(pages, constants) {
  const figma = createFieldsFigma(pages);
  const { result } = await runFigmaScript(EXTRACT_FIELDS_PATH, figma, { constants });
  return { result, figma };
}

describe('extract-figma-fields.js - page selection', () => {
  it('loads all pages and switches to the configured page via setCurrentPageAsync', async () => {
    const hr = page(HR, [frame(`${PREFIX} 1`, 0, 0)]);
    const { figma } = await extract([page('Cover'), hr]);
    expect(figma.loadAllPagesAsync).toHaveBeenCalledTimes(1);
    expect(figma.setCurrentPageAsync).toHaveBeenCalledTimes(1);
    expect(figma.setCurrentPageAsync).toHaveBeenCalledWith(hr);
  });

  it('throws when the configured page does not exist', async () => {
    await expect(extract([page('Cover'), page('Legal')])).rejects.toThrow('Page not found: HR');
  });

  it('honours an overridden PAGE_NAME and FRAME_PREFIX', async () => {
    const forms = page('Forms', [frame('Onboarding A', 0, 0, [rect('FIELD · a', 1, 2, 100, 20)])]);
    const { result, figma } = await extract([page(HR), forms], { PAGE_NAME: 'Forms', FRAME_PREFIX: 'Onboarding' });
    expect(figma.setCurrentPageAsync).toHaveBeenCalledWith(forms);
    expect(result.fields.map(f => f.id)).toEqual(['a']);
  });
});

describe('extract-figma-fields.js - field extraction', () => {
  it('extracts a text field with page index, id, rounded geometry and type', async () => {
    const { result } = await extract([page(HR, [
      frame(`${PREFIX} 1`, 0, 0, [rect('FIELD · employee_name', 100, 50, 200, 30)]),
    ])]);
    expect(result.fields).toEqual([{ p: 0, id: 'employee_name', x: 100, y: 50, w: 200, h: 30, type: 'text' }]);
    expect(result.total).toBe(1);
    expect(result.checks).toBe(0);
    expect(result.perPage).toEqual({ p1: 1 });
    expect(result.warnings).toEqual([]);
  });

  it('classifies rectangles of 14x14 or smaller as checkboxes, larger as text', async () => {
    const { result } = await extract([page(HR, [frame(`${PREFIX} 1`, 0, 0, [
      rect('FIELD · exact', 0, 0, 14, 14),
      rect('FIELD · small', 0, 0, 12, 12),
      rect('FIELD · wide', 0, 0, 15, 14),
      rect('FIELD · tall', 0, 0, 14, 15),
      rect('FIELD · text', 0, 0, 200, 25),
    ])])]);
    expect(Object.fromEntries(result.fields.map(f => [f.id, f.type]))).toEqual({
      exact: 'check', small: 'check', wide: 'text', tall: 'text', text: 'text',
    });
    expect(result.checks).toBe(2);
    expect(result.total).toBe(5);
  });

  it('keeps fields in frame child order', async () => {
    const { result } = await extract([page(HR, [frame(`${PREFIX} 1`, 0, 0, [
      rect('FIELD · name', 50, 50, 200, 25),
      rect('FIELD · email', 50, 100, 200, 25),
      rect('FIELD · agree', 50, 150, 12, 12),
    ])])]);
    expect(result.fields.map(f => f.id)).toEqual(['name', 'email', 'agree']);
  });

  it('ignores children that are not named "FIELD · ..."', async () => {
    const { result } = await extract([page(HR, [frame(`${PREFIX} 1`, 0, 0, [
      rect('FIELD · valid_field', 50, 50, 200, 25),
      rect('Background', 0, 0, 595, 842),
      rect('Label Text', 50, 30, 100, 15, { type: 'TEXT' }),
      rect('FIELD·no_space', 50, 30, 100, 15),
      rect('field · lowercase', 50, 30, 100, 15),
    ])])]);
    expect(result.fields.map(f => f.id)).toEqual(['valid_field']);
  });

  it('only reads direct children of a frame: fields nested in groups are skipped', async () => {
    const group = { name: 'Group', type: 'GROUP', x: 0, y: 0, width: 300, height: 300,
      children: [rect('FIELD · nested', 10, 10, 100, 20)] };
    const { result } = await extract([page(HR, [frame(`${PREFIX} 1`, 0, 0, [
      group, rect('FIELD · direct', 10, 10, 100, 20),
    ])])]);
    expect(result.fields.map(f => f.id)).toEqual(['direct']);
  });

  it('rounds coordinates and sizes to two decimals', async () => {
    const { result } = await extract([page(HR, [frame(`${PREFIX} 1`, 0, 0, [
      rect('FIELD · t', 100.123456, 50.987654, 200.555555, 30.444444),
    ])])]);
    expect(result.fields[0]).toMatchObject({ x: 100.12, y: 50.99, w: 200.56, h: 30.44 });
  });

  it('trims whitespace after the prefix when forming the id', async () => {
    const { result } = await extract([page(HR, [frame(`${PREFIX} 1`, 0, 0, [
      rect('FIELD ·   padded_id  ', 0, 0, 100, 20),
    ])])]);
    expect(result.fields[0].id).toBe('padded_id');
    expect(result.warnings).toEqual([]);
  });
});

describe('extract-figma-fields.js - validation and warnings', () => {
  it('warns about non-snake_case ids but still exports them', async () => {
    const { result } = await extract([page(HR, [frame(`${PREFIX} 1`, 0, 0, [
      rect('FIELD · EmployeeName', 0, 0, 100, 20),
      rect('FIELD · employee-name', 0, 0, 100, 20),
      rect('FIELD · employee.name', 0, 0, 100, 20),
      rect('FIELD · employee name', 0, 0, 100, 20),
      rect('FIELD · employee_name', 0, 0, 100, 20),
      rect('FIELD · p1_field_123', 0, 0, 100, 20),
    ])])]);
    expect(result.warnings).toEqual([
      'non-snake_case field id: "EmployeeName"',
      'non-snake_case field id: "employee-name"',
      'non-snake_case field id: "employee.name"',
      'non-snake_case field id: "employee name"',
    ]);
    expect(result.total).toBe(6);
  });

  it('warns when a frame is not A4 (595x842) and reports frame sizes', async () => {
    const { result } = await extract([page(HR, [
      frame(`${PREFIX} 1`, 0, 0, [], 595, 842),
      frame(`${PREFIX} 2`, 600, 0, [], 600, 800),
      frame(`${PREFIX} 3`, 1300, 0, [], 1920, 1080),
      frame(`${PREFIX} 4`, 3300, 0, [], 595.4, 841.6),   // rounds to A4, no warning
    ])]);
    expect(result.warnings).toEqual([
      `${PREFIX} 2 is 600x800, expected 595x842`,
      `${PREFIX} 3 is 1920x1080, expected 595x842`,
    ]);
    expect(result.frames).toEqual([
      { name: `${PREFIX} 1`, w: 595, h: 842 },
      { name: `${PREFIX} 2`, w: 600, h: 800 },
      { name: `${PREFIX} 3`, w: 1920, h: 1080 },
      { name: `${PREFIX} 4`, w: 595.4, h: 841.6 },
    ]);
  });

  it('reports duplicate ids once each, across pages', async () => {
    const { result } = await extract([page(HR, [
      frame(`${PREFIX} 1`, 0, 0, [
        rect('FIELD · employee_name', 0, 0, 100, 20),
        rect('FIELD · employee_email', 0, 0, 100, 20),
        rect('FIELD · employee_name', 0, 0, 100, 20),
      ]),
      frame(`${PREFIX} 2`, 600, 0, [
        rect('FIELD · agree_terms', 0, 0, 12, 12),
        rect('FIELD · employee_email', 0, 0, 100, 20),
        rect('FIELD · employee_email', 0, 0, 100, 20),
      ]),
    ])]);
    expect(result.warnings).toEqual(['DUPLICATE ids: employee_name, employee_email']);
    expect(result.total).toBe(6);
  });

  it('does not warn when every id is unique and snake_case on A4 frames', async () => {
    const { result } = await extract([page(HR, [frame(`${PREFIX} 1`, 0, 0, [
      rect('FIELD · field1', 0, 0, 100, 20), rect('FIELD · field2', 0, 0, 100, 20),
    ])])]);
    expect(result.warnings).toEqual([]);
  });
});

describe('extract-figma-fields.js - multi-page support', () => {
  it('orders pages by frame x position, not by canvas order', async () => {
    const { result } = await extract([page(HR, [
      frame(`${PREFIX} 3`, 1200, 0, [rect('FIELD · p3', 0, 0, 100, 20)]),
      frame(`${PREFIX} 1`, 0, 0, [rect('FIELD · p1', 0, 0, 100, 20)]),
      frame(`${PREFIX} 2`, 600, 0, [rect('FIELD · p2', 0, 0, 100, 20)]),
    ])]);
    expect(result.fields.map(f => [f.id, f.p])).toEqual([['p1', 0], ['p2', 1], ['p3', 2]]);
    expect(result.frames.map(f => f.name)).toEqual([`${PREFIX} 1`, `${PREFIX} 2`, `${PREFIX} 3`]);
  });

  it('counts fields per page and ignores frames without the prefix', async () => {
    const { result } = await extract([page(HR, [
      frame(`${PREFIX} 1`, 0, 0, [rect('FIELD · a', 0, 0, 100, 20), rect('FIELD · b', 0, 0, 100, 20), rect('FIELD · c', 0, 0, 12, 12)]),
      frame(`${PREFIX} 2`, 600, 0, [rect('FIELD · d', 0, 0, 100, 20), rect('FIELD · e', 0, 0, 100, 20)]),
      frame(`${PREFIX} 3`, 1200, 0, [rect('FIELD · f', 0, 0, 100, 20)]),
      frame('Scratch', 1800, 0, [rect('FIELD · ignored', 0, 0, 100, 20)]),
    ])]);
    expect(result.perPage).toEqual({ p1: 3, p2: 2, p3: 1 });
    expect(result.total).toBe(6);
    expect(result.checks).toBe(1);
    expect(result.fields.map(f => f.id)).not.toContain('ignored');
    expect(result.frames).toHaveLength(3);
  });

  it('returns an empty result for a page with no matching frames', async () => {
    const { result } = await extract([page(HR, [frame('Other', 0, 0, [rect('FIELD · x', 0, 0, 10, 10)])])]);
    expect(result).toEqual({ total: 0, checks: 0, perPage: {}, frames: [], warnings: [], fields: [] });
  });
});

// ---------------------------------------------------------------------------
// figma-slide-transitions.js
// ---------------------------------------------------------------------------

const DECK_PAGE = 'Design V 1.1'; // default PAGE_NAME in the script
const SPACE = 32;
const BACKSPACE = 8;
const TRANSITION = { type: 'SMART_ANIMATE', easing: { type: 'SLOW' }, duration: 0.6 };

/** A slide frame at absolute (x, y). setReactionsAsync records what it received. */
function slide(id, name, x, y, { width = 1920, height = 1080, type = 'FRAME', children, fail } = {}) {
  const node = {
    id, name, type, width, height,
    absoluteTransform: [[1, 0, x], [0, 1, y]],
    reactions: null,
    setReactionsAsync: vi.fn(async (reactions) => {
      if (fail) throw new Error(fail);
      node.reactions = reactions;
    }),
  };
  if (children) node.children = children;
  return node;
}

function container(type, children) {
  return { id: 'c-' + type, name: type, type, width: 4000, height: 4000, children, absoluteTransform: [[1, 0, 0], [0, 1, 0]] };
}

function createDeckFigma(pages) {
  const nodes = new Map();
  const walk = (n) => { if (n.id) nodes.set(n.id, n); (n.children || []).forEach(walk); };
  pages.forEach(p => (p.children || []).forEach(walk));
  return {
    root: { children: pages },
    loadAllPagesAsync: vi.fn(async () => {}),
    setCurrentPageAsync: vi.fn(async () => {}),
    getNodeByIdAsync: vi.fn(async (id) => nodes.get(id) ?? null),
  };
}

async function wire(pages, constants) {
  const figma = createDeckFigma(pages);
  const { result } = await runFigmaScript(TRANSITIONS_PATH, figma, { constants });
  return { result, figma };
}

const spaceTo = (destinationId) => ({
  trigger: { type: 'ON_KEY_DOWN', device: 'KEYBOARD', keyCodes: [SPACE] },
  actions: [{ type: 'NODE', destinationId, navigation: 'NAVIGATE', transition: TRANSITION, preserveScrollPosition: false }],
});
const back = {
  trigger: { type: 'ON_KEY_DOWN', device: 'KEYBOARD', keyCodes: [BACKSPACE] },
  actions: [{ type: 'BACK' }],
};

describe('figma-slide-transitions.js - page handling', () => {
  it('loads pages and switches to the deck page', async () => {
    const deck = page(DECK_PAGE, [slide('s1', 'One', 0, 0), slide('s2', 'Two', 2000, 0)]);
    const { figma } = await wire([page('Archive'), deck]);
    expect(figma.loadAllPagesAsync).toHaveBeenCalledTimes(1);
    expect(figma.setCurrentPageAsync).toHaveBeenCalledWith(deck);
  });

  it('returns an error listing the available pages when the deck page is missing', async () => {
    const { result, figma } = await wire([page('Design V 1.0'), page('Archive')]);
    expect(result).toEqual({ error: 'page not found', pages: ['Design V 1.0', 'Archive'] });
    expect(figma.setCurrentPageAsync).not.toHaveBeenCalled();
  });

  it('uses an overridden PAGE_NAME', async () => {
    const deck = page('Deck', [slide('s1', 'One', 0, 0), slide('s2', 'Two', 2000, 0)]);
    const { result, figma } = await wire([page(DECK_PAGE), deck], { PAGE_NAME: 'Deck' });
    expect(figma.setCurrentPageAsync).toHaveBeenCalledWith(deck);
    expect(result.page).toBe('Deck');
    expect(result.slides).toBe(2);
  });
});

describe('figma-slide-transitions.js - auto-discovery', () => {
  it('finds 1920x1080 frames and orders them top-to-bottom then left-to-right', async () => {
    const c = slide('c', 'C', 1920, 0);
    const a = slide('a', 'A', 0, 0);
    const d = slide('d', 'D', 0, 1080);
    const b = slide('b', 'B', 960, 0);
    const { result } = await wire([page(DECK_PAGE, [c, a, d, b])]);
    expect(result.report.map(r => r.slide)).toEqual(['A', 'B', 'C', 'D']);
    expect(result.flowStart).toBe('A');
    expect(a.reactions).toEqual([spaceTo('b'), back]);
    expect(b.reactions).toEqual([spaceTo('c'), back]);
    expect(c.reactions).toEqual([spaceTo('d'), back]);
  });

  it('ignores frames that are not 1920x1080 and non-frame nodes', async () => {
    const s1 = slide('s1', 'One', 0, 0);
    const doc = slide('doc', 'A4', 0, 2000, { width: 595, height: 842 });
    const comp = slide('cmp', 'Component', 0, 4000, { type: 'COMPONENT' });
    const s2 = slide('s2', 'Two', 2000, 0);
    const { result } = await wire([page(DECK_PAGE, [s1, doc, comp, s2])]);
    expect(result.slides).toBe(2);
    expect(doc.setReactionsAsync).not.toHaveBeenCalled();
    expect(comp.setReactionsAsync).not.toHaveBeenCalled();
  });

  it('tolerates sub-pixel sizes by rounding', async () => {
    const s1 = slide('s1', 'One', 0, 0, { width: 1919.6, height: 1080.4 });
    const s2 = slide('s2', 'Two', 2000, 0);
    const { result } = await wire([page(DECK_PAGE, [s1, s2])]);
    expect(result.slides).toBe(2);
  });

  it('descends into sections and groups but not into instances', async () => {
    const inSection = slide('sec1', 'In section', 0, 0);
    const inGroup = slide('grp1', 'In group', 2000, 0);
    const inInstance = slide('inst1', 'In instance', 4000, 0);
    const top = slide('top', 'Top level', 6000, 0);
    const pageNode = page(DECK_PAGE, [
      container('SECTION', [inSection]),
      container('GROUP', [inGroup]),
      container('INSTANCE', [inInstance]),
      top,
    ]);
    const { result } = await wire([pageNode]);
    expect(result.report.map(r => r.slide)).toEqual(['In section', 'In group', 'Top level']);
    expect(inInstance.setReactionsAsync).not.toHaveBeenCalled();
  });

  it('returns an error when fewer than two slides are found', async () => {
    const only = slide('s1', 'One', 0, 0);
    const { result } = await wire([page(DECK_PAGE, [only])]);
    expect(result).toEqual({ error: 'need at least two slides', found: 1 });
    expect(only.setReactionsAsync).not.toHaveBeenCalled();
  });
});

describe('figma-slide-transitions.js - explicit ORDER', () => {
  it('resolves ORDER ids through getNodeByIdAsync and uses that sequence', async () => {
    const intro = slide('slide-1', 'Intro', 0, 0);
    const content = slide('slide-2', 'Content', 2000, 0);
    const title = slide('slide-3', 'Title', 4000, 0);
    const { result, figma } = await wire([page(DECK_PAGE, [intro, content, title])], { ORDER: ['slide-3', 'slide-1', 'slide-2'] });
    expect(figma.getNodeByIdAsync.mock.calls.map(c => c[0])).toEqual(['slide-3', 'slide-1', 'slide-2']);
    expect(result.report.map(r => r.slide)).toEqual(['Title', 'Intro', 'Content']);
    expect(result.flowStart).toBe('Title');
    expect(title.reactions).toEqual([spaceTo('slide-1'), back]);
    expect(intro.reactions).toEqual([spaceTo('slide-2'), back]);
    expect(content.reactions).toEqual([back]);
  });

  it('with ORDER set, does not filter by size — whatever ids are listed are used', async () => {
    const a = slide('a', 'A', 0, 0, { width: 1000, height: 500 });
    const b = slide('b', 'B', 0, 0, { width: 1000, height: 500 });
    const { result } = await wire([page(DECK_PAGE, [a, b])], { ORDER: ['a', 'b'] });
    expect(result.slides).toBe(2);
    expect(a.reactions).toEqual([spaceTo('b'), back]);
  });

  it('stops with an error naming the first id that cannot be found', async () => {
    const s1 = slide('slide-1', 'One', 0, 0);
    const s2 = slide('slide-2', 'Two', 2000, 0);
    const { result } = await wire([page(DECK_PAGE, [s1, s2])], { ORDER: ['slide-1', 'slide-2', 'slide-999'] });
    expect(result).toEqual({ error: 'frame id not found', id: 'slide-999' });
    expect(s1.setReactionsAsync).not.toHaveBeenCalled();
    expect(s2.setReactionsAsync).not.toHaveBeenCalled();
  });
});

describe('figma-slide-transitions.js - reactions', () => {
  it('gives every slide but the last Space -> next plus Backspace -> back, in one call', async () => {
    const s1 = slide('s1', 'Title', 0, 0);
    const s2 = slide('s2', 'Agenda', 2000, 0);
    const s3 = slide('s3', 'Thank you', 4000, 0);
    const { result } = await wire([page(DECK_PAGE, [s1, s2, s3])]);
    for (const s of [s1, s2, s3]) expect(s.setReactionsAsync).toHaveBeenCalledTimes(1);
    expect(s1.reactions).toEqual([spaceTo('s2'), back]);
    expect(s2.reactions).toEqual([spaceTo('s3'), back]);
    expect(result.failed).toBe(0);
  });

  it('gives the last slide Back only', async () => {
    const s1 = slide('s1', 'Title', 0, 0);
    const s2 = slide('s2', 'End', 2000, 0);
    await wire([page(DECK_PAGE, [s1, s2])]);
    expect(s2.reactions).toEqual([back]);
    expect(s2.reactions.some(r => r.trigger.keyCodes.includes(SPACE))).toBe(false);
  });

  it('uses Smart animate / Slow / 600 ms for every forward transition', async () => {
    const s = [slide('s1', 'A', 0, 0), slide('s2', 'B', 2000, 0), slide('s3', 'C', 4000, 0)];
    await wire([page(DECK_PAGE, s)]);
    for (const node of s.slice(0, -1)) {
      const forward = node.reactions.find(r => r.trigger.keyCodes.includes(SPACE));
      expect(forward.actions[0].transition).toEqual(TRANSITION);
      expect(forward.actions[0].preserveScrollPosition).toBe(false);
      expect(forward.actions[0].navigation).toBe('NAVIGATE');
    }
  });

  it('sets the first slide as the flow starting point named "Start"', async () => {
    const deck = page(DECK_PAGE, [slide('s1', 'Title', 0, 0), slide('s2', 'Two', 2000, 0)]);
    const { result } = await wire([deck]);
    expect(deck.flowStartingPoints).toEqual([{ nodeId: 's1', name: 'Start' }]);
    expect(result.flowStart).toBe('Title');
  });
});

describe('figma-slide-transitions.js - report', () => {
  it('describes each slide and its Space target', async () => {
    const { result } = await wire([page(DECK_PAGE, [
      slide('s1', 'Title Slide', 0, 0), slide('s2', 'Agenda', 2000, 0), slide('s3', 'Thank You', 4000, 0),
    ])]);
    expect(result).toEqual({
      page: DECK_PAGE, slides: 3, flowStart: 'Title Slide', failed: 0,
      report: [
        { n: 1, slide: 'Title Slide', space: '-> 2' },
        { n: 2, slide: 'Agenda', space: '-> 3' },
        { n: 3, slide: 'Thank You', space: 'none (last)' },
      ],
    });
  });

  it('records a setReactionsAsync failure for that slide and keeps going', async () => {
    const s1 = slide('s1', 'One', 0, 0);
    const s2 = slide('s2', 'Two', 2000, 0, { fail: 'Permission denied' });
    const s3 = slide('s3', 'Three', 4000, 0);
    const deck = page(DECK_PAGE, [s1, s2, s3]);
    const { result } = await wire([deck]);
    expect(result.failed).toBe(1);
    expect(result.report[1]).toEqual({ n: 2, slide: 'Two', error: 'Error: Permission denied' });
    expect(result.report[0]).toEqual({ n: 1, slide: 'One', space: '-> 2' });
    expect(result.report[2]).toEqual({ n: 3, slide: 'Three', space: 'none (last)' });
    expect(s3.reactions).toEqual([back]);
    // flow start is still assigned after a partial failure
    expect(deck.flowStartingPoints).toEqual([{ nodeId: 's1', name: 'Start' }]);
  });

  it('truncates long error text to 160 characters', async () => {
    const long = 'x'.repeat(500);
    const s1 = slide('s1', 'One', 0, 0, { fail: long });
    const s2 = slide('s2', 'Two', 2000, 0);
    const { result } = await wire([page(DECK_PAGE, [s1, s2])]);
    expect(result.report[0].error).toHaveLength(160);
    expect(result.report[0].error.startsWith('Error: xxxx')).toBe(true);
  });
});
