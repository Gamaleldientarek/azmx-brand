/**
 * Test harness for the Figma console scripts in scripts/.
 *
 * export-figma-tokens.js, extract-figma-fields.js and figma-slide-transitions.js
 * are pasted into the Figma plugin console: they use top-level `await` and a
 * bare `return`, and they cannot contain `export`. To test the real source we
 * read the file, wrap it in an async IIFE and evaluate it with node:vm inside a
 * sandbox whose only `figma` is the mock the test supplies. The returned value
 * is whatever the script `return`ed.
 */

import { readFileSync } from 'node:fs';
import vm from 'node:vm';

/**
 * Run a console script against a mock `figma` global.
 *
 * @param {string} scriptPath absolute path of the script
 * @param {object} figma       mock Figma API
 * @param {object} [options]
 * @param {Record<string, unknown>} [options.constants]
 *        Override the script's "edit these" top-level constants
 *        (`const PAGE_NAME = ...;`) so scenarios other than the shipped defaults
 *        can be exercised. The substitution is a single line and the test fails
 *        loudly if the constant does not exist, so the rest of the file runs
 *        exactly as committed.
 * @returns {Promise<{ result: unknown, logs: unknown[][], errors: unknown[][] }>}
 */
export async function runFigmaScript(scriptPath, figma, { constants = {} } = {}) {
  let source = readFileSync(scriptPath, 'utf8');

  for (const [name, value] of Object.entries(constants)) {
    const pattern = new RegExp(`^const ${name} = [^;]*;`, 'm');
    if (!pattern.test(source)) {
      throw new Error(`${scriptPath} has no top-level "const ${name} = ...;" to override`);
    }
    source = source.replace(pattern, `const ${name} = ${JSON.stringify(value)};`);
  }

  const logs = [];
  const errors = [];
  const sandbox = {
    figma,
    console: {
      log: (...args) => logs.push(args),
      warn: (...args) => errors.push(args),
      error: (...args) => errors.push(args),
    },
    JSON,
    Promise,
    setTimeout,
    Set,
    Map,
    Array,
    Object,
    Math,
  };

  const wrapped = `(async () => {\n${source}\n})()`;
  const result = await vm.runInNewContext(wrapped, sandbox, { filename: scriptPath });
  return { result, logs, errors };
}
