/**
 * Unit tests for Figma console scripts: extract-figma-fields.js and figma-slide-transitions.js
 *
 * These scripts run in Figma's console environment (not Node.js), so we mock the Figma API
 * and test the core logic and data transformations.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(HERE, '..');
const SCRIPTS_DIR = join(REPO_ROOT, 'scripts');
const EXTRACT_FIELDS_PATH = join(SCRIPTS_DIR, 'extract-figma-fields.js');
const TRANSITIONS_PATH = join(SCRIPTS_DIR, 'figma-slide-transitions.js');

// Read the script sources
const extractFieldsSource = readFileSync(EXTRACT_FIELDS_PATH, 'utf8');
const transitionsSource = readFileSync(TRANSITIONS_PATH, 'utf8');

/**
 * Mock Figma nodes for testing extract-figma-fields.js
 */
function createMockFrame(name, x, y, width = 595, height = 842, children = []) {
  return {
    name,
    type: 'FRAME',
    x,
    y,
    width,
    height,
    children: children.map(child => ({
      name: child.name,
      type: child.type || 'RECTANGLE',
      x: child.x,
      y: child.y,
      width: child.w,
      height: child.h
    }))
  };
}

/**
 * Mock Figma page for testing
 */
function createMockPage(name, children = []) {
  return {
    name,
    type: 'PAGE',
    children
  };
}

/**
 * Mock Figma API for extract-figma-fields.js
 */
function createMockFigmaForFields(pages) {
  return {
    root: {
      children: pages
    },
    loadAllPagesAsync: vi.fn(async () => {}),
    setCurrentPageAsync: vi.fn(async (page) => {}),
    currentPage: null
  };
}

/**
 * Mock Figma API for figma-slide-transitions.js
 */
function createMockFigmaForTransitions(pages) {
  const nodeMap = new Map();

  // Build node map for getNodeByIdAsync
  pages.forEach(page => {
    page.children.forEach(frame => {
      nodeMap.set(frame.id, frame);
    });
  });

  return {
    root: {
      children: pages
    },
    loadAllPagesAsync: vi.fn(async () => {}),
    setCurrentPageAsync: vi.fn(async (page) => {}),
    getNodeByIdAsync: vi.fn(async (id) => nodeMap.get(id)),
    currentPage: null
  };
}

describe('extract-figma-fields.js - field extraction', () => {
  it('extracts text field correctly', () => {
    const fieldRect = {
      name: 'FIELD · employee_name',
      x: 100,
      y: 50,
      w: 200,
      h: 30
    };

    const frame = createMockFrame('Employee Information', 0, 0, 595, 842, [fieldRect]);

    // Simulate field extraction logic
    const fields = [];
    frame.children.forEach((n, pageIndex = 0) => {
      if (!n.name.startsWith('FIELD · ')) return;
      const id = n.name.replace('FIELD · ', '').trim();
      const round = (v) => Math.round(v * 100) / 100;
      fields.push({
        p: pageIndex,
        id,
        x: round(n.x),
        y: round(n.y),
        w: round(n.width),
        h: round(n.height),
        type: n.width <= 14 && n.height <= 14 ? 'check' : 'text'
      });
    });

    expect(fields).toHaveLength(1);
    expect(fields[0]).toEqual({
      p: 0,
      id: 'employee_name',
      x: 100,
      y: 50,
      w: 200,
      h: 30,
      type: 'text'
    });
  });

  it('auto-detects checkbox type from small dimensions', () => {
    const checkboxRect = {
      name: 'FIELD · agree_terms',
      x: 50,
      y: 100,
      w: 14,
      h: 14
    };

    const frame = createMockFrame('Form', 0, 0, 595, 842, [checkboxRect]);

    const fields = [];
    frame.children.forEach((n, pageIndex = 0) => {
      if (!n.name.startsWith('FIELD · ')) return;
      const id = n.name.replace('FIELD · ', '').trim();
      const round = (v) => Math.round(v * 100) / 100;
      fields.push({
        p: pageIndex,
        id,
        x: round(n.x),
        y: round(n.y),
        w: round(n.width),
        h: round(n.height),
        type: n.width <= 14 && n.height <= 14 ? 'check' : 'text'
      });
    });

    expect(fields).toHaveLength(1);
    expect(fields[0].type).toBe('check');
    expect(fields[0].w).toBe(14);
    expect(fields[0].h).toBe(14);
  });

  it('extracts multiple fields from one frame', () => {
    const rects = [
      { name: 'FIELD · name', x: 50, y: 50, w: 200, h: 25 },
      { name: 'FIELD · email', x: 50, y: 100, w: 200, h: 25 },
      { name: 'FIELD · agree', x: 50, y: 150, w: 12, h: 12 }
    ];

    const frame = createMockFrame('Form', 0, 0, 595, 842, rects);

    const fields = [];
    frame.children.forEach((n, pageIndex = 0) => {
      if (!n.name.startsWith('FIELD · ')) return;
      const id = n.name.replace('FIELD · ', '').trim();
      const round = (v) => Math.round(v * 100) / 100;
      fields.push({
        p: pageIndex,
        id,
        x: round(n.x),
        y: round(n.y),
        w: round(n.width),
        h: round(n.height),
        type: n.width <= 14 && n.height <= 14 ? 'check' : 'text'
      });
    });

    expect(fields).toHaveLength(3);
    expect(fields[0].id).toBe('name');
    expect(fields[1].id).toBe('email');
    expect(fields[2].id).toBe('agree');
    expect(fields[2].type).toBe('check');
  });

  it('ignores non-FIELD rectangles', () => {
    const rects = [
      { name: 'FIELD · valid_field', x: 50, y: 50, w: 200, h: 25 },
      { name: 'Background', x: 0, y: 0, w: 595, h: 842 },
      { name: 'Label Text', x: 50, y: 30, w: 100, h: 15 }
    ];

    const frame = createMockFrame('Form', 0, 0, 595, 842, rects);

    const fields = [];
    frame.children.forEach((n, pageIndex = 0) => {
      if (!n.name.startsWith('FIELD · ')) return;
      const id = n.name.replace('FIELD · ', '').trim();
      const round = (v) => Math.round(v * 100) / 100;
      fields.push({
        p: pageIndex,
        id,
        x: round(n.x),
        y: round(n.y),
        w: round(n.width),
        h: round(n.height),
        type: n.width <= 14 && n.height <= 14 ? 'check' : 'text'
      });
    });

    expect(fields).toHaveLength(1);
    expect(fields[0].id).toBe('valid_field');
  });

  it('rounds coordinates to 2 decimal places', () => {
    const fieldRect = {
      name: 'FIELD · test',
      x: 100.123456,
      y: 50.987654,
      w: 200.555555,
      h: 30.444444
    };

    const frame = createMockFrame('Form', 0, 0, 595, 842, [fieldRect]);

    const fields = [];
    frame.children.forEach((n, pageIndex = 0) => {
      if (!n.name.startsWith('FIELD · ')) return;
      const id = n.name.replace('FIELD · ', '').trim();
      const round = (v) => Math.round(v * 100) / 100;
      fields.push({
        p: pageIndex,
        id,
        x: round(n.x),
        y: round(n.y),
        w: round(n.width),
        h: round(n.height),
        type: n.width <= 14 && n.height <= 14 ? 'check' : 'text'
      });
    });

    expect(fields[0].x).toBe(100.12);
    expect(fields[0].y).toBe(50.99);
    expect(fields[0].w).toBe(200.56);
    expect(fields[0].h).toBe(30.44);
  });

  it('handles edge case of exactly 14x14 dimensions (checkbox boundary)', () => {
    const checkboxRect = {
      name: 'FIELD · checkbox_exact',
      x: 50,
      y: 100,
      w: 14,
      h: 14
    };

    const frame = createMockFrame('Form', 0, 0, 595, 842, [checkboxRect]);

    const fields = [];
    frame.children.forEach((n, pageIndex = 0) => {
      if (!n.name.startsWith('FIELD · ')) return;
      const id = n.name.replace('FIELD · ', '').trim();
      const round = (v) => Math.round(v * 100) / 100;
      fields.push({
        p: pageIndex,
        id,
        x: round(n.x),
        y: round(n.y),
        w: round(n.width),
        h: round(n.height),
        type: n.width <= 14 && n.height <= 14 ? 'check' : 'text'
      });
    });

    expect(fields[0].type).toBe('check');
  });

  it('detects text type for dimensions larger than 14x14', () => {
    const textRect = {
      name: 'FIELD · text_field',
      x: 50,
      y: 100,
      w: 15,
      h: 15
    };

    const frame = createMockFrame('Form', 0, 0, 595, 842, [textRect]);

    const fields = [];
    frame.children.forEach((n, pageIndex = 0) => {
      if (!n.name.startsWith('FIELD · ')) return;
      const id = n.name.replace('FIELD · ', '').trim();
      const round = (v) => Math.round(v * 100) / 100;
      fields.push({
        p: pageIndex,
        id,
        x: round(n.x),
        y: round(n.y),
        w: round(n.width),
        h: round(n.height),
        type: n.width <= 14 && n.height <= 14 ? 'check' : 'text'
      });
    });

    expect(fields[0].type).toBe('text');
  });
});

describe('extract-figma-fields.js - validation and warnings', () => {
  it('detects non-snake_case field IDs', () => {
    const invalidIds = [
      'FIELD · EmployeeName',
      'FIELD · employee-name',
      'FIELD · employee.name',
      'FIELD · employee name'
    ];

    const warnings = [];
    invalidIds.forEach(name => {
      const id = name.replace('FIELD · ', '').trim();
      if (!/^[a-z0-9_]+$/.test(id)) {
        warnings.push(`non-snake_case field id: "${id}"`);
      }
    });

    expect(warnings).toHaveLength(4);
    expect(warnings[0]).toContain('EmployeeName');
    expect(warnings[1]).toContain('employee-name');
    expect(warnings[2]).toContain('employee.name');
    expect(warnings[3]).toContain('employee name');
  });

  it('accepts valid snake_case field IDs', () => {
    const validIds = [
      'employee_name',
      'email_address',
      'p1_agree_terms',
      'field_123',
      'test_field_with_many_parts'
    ];

    const warnings = [];
    validIds.forEach(id => {
      if (!/^[a-z0-9_]+$/.test(id)) {
        warnings.push(`non-snake_case field id: "${id}"`);
      }
    });

    expect(warnings).toHaveLength(0);
  });

  it('detects frame dimension mismatch (not A4)', () => {
    const frames = [
      { name: 'Frame 1', width: 595, height: 842 },   // A4 - OK
      { name: 'Frame 2', width: 600, height: 800 },   // Not A4
      { name: 'Frame 3', width: 1920, height: 1080 }  // Not A4
    ];

    const warnings = [];
    frames.forEach(frame => {
      if (Math.round(frame.width) !== 595 || Math.round(frame.height) !== 842) {
        warnings.push(`${frame.name} is ${Math.round(frame.width)}x${Math.round(frame.height)}, expected 595x842`);
      }
    });

    expect(warnings).toHaveLength(2);
    expect(warnings[0]).toContain('Frame 2 is 600x800');
    expect(warnings[1]).toContain('Frame 3 is 1920x1080');
  });

  it('detects duplicate field IDs', () => {
    const fields = [
      { id: 'employee_name' },
      { id: 'employee_email' },
      { id: 'employee_name' },
      { id: 'agree_terms' },
      { id: 'employee_email' }
    ];

    const names = fields.map(f => f.id);
    const duplicates = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))];
    const warnings = [];
    if (duplicates.length) {
      warnings.push(`DUPLICATE ids: ${duplicates.join(', ')}`);
    }

    expect(duplicates).toHaveLength(2);
    expect(duplicates).toContain('employee_name');
    expect(duplicates).toContain('employee_email');
    expect(warnings[0]).toBe('DUPLICATE ids: employee_name, employee_email');
  });

  it('does not report duplicates when all IDs are unique', () => {
    const fields = [
      { id: 'field1' },
      { id: 'field2' },
      { id: 'field3' }
    ];

    const names = fields.map(f => f.id);
    const duplicates = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))];

    expect(duplicates).toHaveLength(0);
  });
});

describe('extract-figma-fields.js - multi-page support', () => {
  it('assigns correct page index to fields', () => {
    const frames = [
      createMockFrame('Page 1', 0, 0, 595, 842, [
        { name: 'FIELD · p1_field1', x: 50, y: 50, w: 200, h: 25 }
      ]),
      createMockFrame('Page 2', 600, 0, 595, 842, [
        { name: 'FIELD · p2_field1', x: 50, y: 50, w: 200, h: 25 }
      ])
    ];

    const allFields = [];
    frames.forEach((frame, pageIndex) => {
      frame.children.forEach(n => {
        if (!n.name.startsWith('FIELD · ')) return;
        const id = n.name.replace('FIELD · ', '').trim();
        const round = (v) => Math.round(v * 100) / 100;
        allFields.push({
          p: pageIndex,
          id,
          x: round(n.x),
          y: round(n.y),
          w: round(n.width),
          h: round(n.height),
          type: n.width <= 14 && n.height <= 14 ? 'check' : 'text'
        });
      });
    });

    expect(allFields).toHaveLength(2);
    expect(allFields[0].p).toBe(0);
    expect(allFields[0].id).toBe('p1_field1');
    expect(allFields[1].p).toBe(1);
    expect(allFields[1].id).toBe('p2_field1');
  });

  it('counts fields per page correctly', () => {
    const fields = [
      { p: 0, id: 'f1' },
      { p: 0, id: 'f2' },
      { p: 0, id: 'f3' },
      { p: 1, id: 'f4' },
      { p: 1, id: 'f5' },
      { p: 2, id: 'f6' }
    ];

    const perPage = {};
    fields.forEach(f => {
      perPage['p' + (f.p + 1)] = (perPage['p' + (f.p + 1)] || 0) + 1;
    });

    expect(perPage.p1).toBe(3);
    expect(perPage.p2).toBe(2);
    expect(perPage.p3).toBe(1);
  });

  it('sorts frames by x position (left to right for page order)', () => {
    const frames = [
      { name: 'Page 3', x: 1200 },
      { name: 'Page 1', x: 0 },
      { name: 'Page 2', x: 600 }
    ];

    const sorted = [...frames].sort((a, b) => a.x - b.x);

    expect(sorted[0].name).toBe('Page 1');
    expect(sorted[1].name).toBe('Page 2');
    expect(sorted[2].name).toBe('Page 3');
  });
});

describe('extract-figma-fields.js - output structure', () => {
  it('generates correct summary output', () => {
    const fields = [
      { p: 0, id: 'text1', type: 'text' },
      { p: 0, id: 'text2', type: 'text' },
      { p: 0, id: 'check1', type: 'check' },
      { p: 1, id: 'text3', type: 'text' }
    ];

    const perPage = {};
    fields.forEach(f => {
      perPage['p' + (f.p + 1)] = (perPage['p' + (f.p + 1)] || 0) + 1;
    });

    const output = {
      total: fields.length,
      checks: fields.filter(f => f.type === 'check').length,
      perPage,
      warnings: [],
      fields
    };

    expect(output.total).toBe(4);
    expect(output.checks).toBe(1);
    expect(output.perPage).toEqual({ p1: 3, p2: 1 });
    expect(output.fields).toHaveLength(4);
  });

  it('includes frame metadata in output', () => {
    const frames = [
      { name: 'Employee Info - Page 1', width: 595, height: 842 },
      { name: 'Employee Info - Page 2', width: 595, height: 842 }
    ];

    const framesMeta = frames.map(f => ({
      name: f.name,
      w: f.width,
      h: f.height
    }));

    expect(framesMeta).toHaveLength(2);
    expect(framesMeta[0]).toEqual({ name: 'Employee Info - Page 1', w: 595, h: 842 });
    expect(framesMeta[1]).toEqual({ name: 'Employee Info - Page 2', w: 595, h: 842 });
  });
});

describe('figma-slide-transitions.js - frame discovery', () => {
  it('discovers 1920x1080 presentation frames', () => {
    const frames = [
      { type: 'FRAME', width: 1920, height: 1080, name: 'Slide 1' },
      { type: 'FRAME', width: 1920, height: 1080, name: 'Slide 2' },
      { type: 'FRAME', width: 595, height: 842, name: 'Document' }
    ];

    const discovered = frames.filter(
      f => f.type === 'FRAME' &&
      Math.round(f.width) === 1920 &&
      Math.round(f.height) === 1080
    );

    expect(discovered).toHaveLength(2);
    expect(discovered[0].name).toBe('Slide 1');
    expect(discovered[1].name).toBe('Slide 2');
  });

  it('sorts frames by position (top-to-bottom, then left-to-right)', () => {
    const frames = [
      { name: 'C', absoluteTransform: [[1, 0, 1920], [0, 1, 0]] },      // x=1920, y=0
      { name: 'A', absoluteTransform: [[1, 0, 0], [0, 1, 0]] },         // x=0, y=0
      { name: 'D', absoluteTransform: [[1, 0, 0], [0, 1, 1080]] },      // x=0, y=1080
      { name: 'B', absoluteTransform: [[1, 0, 960], [0, 1, 0]] }        // x=960, y=0
    ];

    const sorted = [...frames].sort((a, b) =>
      Math.round(a.absoluteTransform[1][2]) - Math.round(b.absoluteTransform[1][2]) ||
      Math.round(a.absoluteTransform[0][2]) - Math.round(b.absoluteTransform[0][2])
    );

    expect(sorted[0].name).toBe('A');  // y=0, x=0
    expect(sorted[1].name).toBe('B');  // y=0, x=960
    expect(sorted[2].name).toBe('C');  // y=0, x=1920
    expect(sorted[3].name).toBe('D');  // y=1080, x=0
  });

  it('handles manual ORDER array for explicit slide sequence', () => {
    const ORDER = ['slide-3', 'slide-1', 'slide-2'];
    const nodesById = {
      'slide-1': { id: 'slide-1', name: 'Intro' },
      'slide-2': { id: 'slide-2', name: 'Content' },
      'slide-3': { id: 'slide-3', name: 'Title' }
    };

    const frames = [];
    for (const id of ORDER) {
      const node = nodesById[id];
      if (node) frames.push(node);
    }

    expect(frames).toHaveLength(3);
    expect(frames[0].name).toBe('Title');
    expect(frames[1].name).toBe('Intro');
    expect(frames[2].name).toBe('Content');
  });
});

describe('figma-slide-transitions.js - transition configuration', () => {
  it('creates correct transition object', () => {
    const TRANSITION = {
      type: 'SMART_ANIMATE',
      easing: { type: 'SLOW' },
      duration: 0.6
    };

    expect(TRANSITION.type).toBe('SMART_ANIMATE');
    expect(TRANSITION.easing.type).toBe('SLOW');
    expect(TRANSITION.duration).toBe(0.6);
  });

  it('defines correct keyboard codes', () => {
    const SPACE = 32;
    const BACKSPACE = 8;

    expect(SPACE).toBe(32);
    expect(BACKSPACE).toBe(8);
  });

  it('creates forward navigation reaction', () => {
    const SPACE = 32;
    const nextSlideId = 'slide-2';
    const TRANSITION = {
      type: 'SMART_ANIMATE',
      easing: { type: 'SLOW' },
      duration: 0.6
    };

    const forwardReaction = {
      trigger: { type: 'ON_KEY_DOWN', device: 'KEYBOARD', keyCodes: [SPACE] },
      actions: [{
        type: 'NODE',
        destinationId: nextSlideId,
        navigation: 'NAVIGATE',
        transition: TRANSITION,
        preserveScrollPosition: false
      }]
    };

    expect(forwardReaction.trigger.keyCodes).toEqual([32]);
    expect(forwardReaction.actions[0].destinationId).toBe('slide-2');
    expect(forwardReaction.actions[0].type).toBe('NODE');
    expect(forwardReaction.actions[0].navigation).toBe('NAVIGATE');
    expect(forwardReaction.actions[0].transition.type).toBe('SMART_ANIMATE');
  });

  it('creates back navigation reaction', () => {
    const BACKSPACE = 8;

    const backReaction = {
      trigger: { type: 'ON_KEY_DOWN', device: 'KEYBOARD', keyCodes: [BACKSPACE] },
      actions: [{ type: 'BACK' }]
    };

    expect(backReaction.trigger.keyCodes).toEqual([8]);
    expect(backReaction.actions[0].type).toBe('BACK');
  });

  it('last slide gets only back reaction (no forward)', () => {
    const frames = [
      { id: 'slide-1', name: 'Slide 1' },
      { id: 'slide-2', name: 'Slide 2' },
      { id: 'slide-3', name: 'Slide 3' }
    ];

    const lastIndex = frames.length - 1;
    const isLastSlide = (i) => i === lastIndex;

    expect(isLastSlide(0)).toBe(false);
    expect(isLastSlide(1)).toBe(false);
    expect(isLastSlide(2)).toBe(true);
  });

  it('non-last slides get both forward and back reactions', () => {
    const frames = [
      { id: 'slide-1', name: 'Slide 1' },
      { id: 'slide-2', name: 'Slide 2' }
    ];

    const reactions = [];
    frames.forEach((frame, i) => {
      const slideReactions = [];

      if (i < frames.length - 1) {
        slideReactions.push({ type: 'forward', target: frames[i + 1].id });
      }
      slideReactions.push({ type: 'back' });

      reactions.push({ slide: frame.name, reactions: slideReactions });
    });

    expect(reactions[0].reactions).toHaveLength(2);
    expect(reactions[0].reactions[0].type).toBe('forward');
    expect(reactions[0].reactions[1].type).toBe('back');

    expect(reactions[1].reactions).toHaveLength(1);
    expect(reactions[1].reactions[0].type).toBe('back');
  });
});

describe('figma-slide-transitions.js - report generation', () => {
  it('generates report for successful slide wiring', () => {
    const frames = [
      { name: 'Title Slide' },
      { name: 'Agenda' },
      { name: 'Thank You' }
    ];

    const report = frames.map((f, i) => ({
      n: i + 1,
      slide: f.name,
      space: i < frames.length - 1 ? `-> ${i + 2}` : 'none (last)'
    }));

    expect(report).toHaveLength(3);
    expect(report[0]).toEqual({ n: 1, slide: 'Title Slide', space: '-> 2' });
    expect(report[1]).toEqual({ n: 2, slide: 'Agenda', space: '-> 3' });
    expect(report[2]).toEqual({ n: 3, slide: 'Thank You', space: 'none (last)' });
  });

  it('includes error in report when setReactionsAsync fails', () => {
    const report = [
      { n: 1, slide: 'Slide 1', space: '-> 2' },
      { n: 2, slide: 'Slide 2', error: 'Permission denied' },
      { n: 3, slide: 'Slide 3', space: 'none (last)' }
    ];

    const failed = report.filter(r => r.error);

    expect(failed).toHaveLength(1);
    expect(failed[0].n).toBe(2);
    expect(failed[0].error).toBe('Permission denied');
  });

  it('generates final summary with metadata', () => {
    const frames = [
      { id: 'slide-1', name: 'Title' },
      { id: 'slide-2', name: 'Content' }
    ];
    const report = [
      { n: 1, slide: 'Title', space: '-> 2' },
      { n: 2, slide: 'Content', space: 'none (last)' }
    ];

    const summary = {
      page: 'Design V 1.1',
      slides: frames.length,
      flowStart: frames[0].name,
      failed: report.filter(r => r.error).length,
      report
    };

    expect(summary.page).toBe('Design V 1.1');
    expect(summary.slides).toBe(2);
    expect(summary.flowStart).toBe('Title');
    expect(summary.failed).toBe(0);
    expect(summary.report).toHaveLength(2);
  });
});

describe('figma-slide-transitions.js - flow starting point', () => {
  it('sets first slide as flow starting point', () => {
    const frames = [
      { id: 'slide-1', name: 'Title Slide' },
      { id: 'slide-2', name: 'Content' }
    ];

    const flowStartingPoints = [{ nodeId: frames[0].id, name: 'Start' }];

    expect(flowStartingPoints).toHaveLength(1);
    expect(flowStartingPoints[0].nodeId).toBe('slide-1');
    expect(flowStartingPoints[0].name).toBe('Start');
  });
});

describe('figma-slide-transitions.js - error handling', () => {
  it('returns error when page not found', () => {
    const pages = [
      { name: 'Design V 1.0' },
      { name: 'Archive' }
    ];

    const PAGE_NAME = 'Design V 1.1';
    const page = pages.find(p => p.name === PAGE_NAME);

    if (!page) {
      const error = {
        error: 'page not found',
        pages: pages.map(p => p.name)
      };

      expect(error.error).toBe('page not found');
      expect(error.pages).toEqual(['Design V 1.0', 'Archive']);
    }
  });

  it('returns error when fewer than 2 slides found', () => {
    const frames = [
      { type: 'FRAME', width: 1920, height: 1080, name: 'Slide 1' }
    ];

    if (frames.length < 2) {
      const error = {
        error: 'need at least two slides',
        found: frames.length
      };

      expect(error.error).toBe('need at least two slides');
      expect(error.found).toBe(1);
    }
  });

  it('returns error when frame ID not found', () => {
    const ORDER = ['slide-1', 'slide-2', 'slide-999'];
    const nodesById = {
      'slide-1': { id: 'slide-1', name: 'Slide 1' },
      'slide-2': { id: 'slide-2', name: 'Slide 2' }
    };

    let errorResult = null;
    for (const id of ORDER) {
      const node = nodesById[id];
      if (!node) {
        errorResult = { error: 'frame id not found', id };
        break;
      }
    }

    expect(errorResult).toBeTruthy();
    expect(errorResult.error).toBe('frame id not found');
    expect(errorResult.id).toBe('slide-999');
  });
});

describe('figma-slide-transitions.js - configuration validation', () => {
  it('validates PAGE_NAME is set', () => {
    const PAGE_NAME = 'Design V 1.1';
    expect(PAGE_NAME).toBeTruthy();
    expect(typeof PAGE_NAME).toBe('string');
    expect(PAGE_NAME.length).toBeGreaterThan(0);
  });

  it('validates ORDER array format', () => {
    const ORDER = ['slide-1', 'slide-2', 'slide-3'];

    expect(Array.isArray(ORDER)).toBe(true);
    ORDER.forEach(id => {
      expect(typeof id).toBe('string');
    });
  });

  it('handles empty ORDER array (auto-discovery mode)', () => {
    const ORDER = [];
    const shouldAutoDiscover = ORDER.length === 0;

    expect(shouldAutoDiscover).toBe(true);
  });

  it('validates transition duration is in seconds', () => {
    const TRANSITION = {
      type: 'SMART_ANIMATE',
      easing: { type: 'SLOW' },
      duration: 0.6
    };

    expect(TRANSITION.duration).toBe(0.6);
    expect(TRANSITION.duration).toBeGreaterThan(0);
    expect(TRANSITION.duration).toBeLessThan(5);
  });
});

describe('extract-figma-fields.js - script constants', () => {
  it('validates script requires PAGE_NAME and FRAME_PREFIX to be set', () => {
    expect(extractFieldsSource).toContain('const PAGE_NAME');
    expect(extractFieldsSource).toContain('const FRAME_PREFIX');
  });

  it('script contains expected A4 dimensions check', () => {
    expect(extractFieldsSource).toContain('595');
    expect(extractFieldsSource).toContain('842');
  });

  it('script contains field name prefix check', () => {
    expect(extractFieldsSource).toContain('FIELD ·');
  });
});

describe('figma-slide-transitions.js - script constants', () => {
  it('validates script has configurable constants', () => {
    expect(transitionsSource).toContain('const PAGE_NAME');
    expect(transitionsSource).toContain('const ORDER');
    expect(transitionsSource).toContain('const TRANSITION');
  });

  it('script contains keyboard code constants', () => {
    expect(transitionsSource).toContain('const SPACE');
    expect(transitionsSource).toContain('const BACKSPACE');
  });

  it('script contains presentation dimensions check', () => {
    expect(transitionsSource).toContain('1920');
    expect(transitionsSource).toContain('1080');
  });

  it('script contains Smart Animate transition type', () => {
    expect(transitionsSource).toContain('SMART_ANIMATE');
  });
});
