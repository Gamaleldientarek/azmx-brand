#!/usr/bin/env node
// Writes assets/icons/phosphor-index.json: every Phosphor icon's name, React name and keywords, so
// scripts/icons.mjs can search them offline. It reads the pinned @phosphor-icons/core from npm into a
// temporary folder (nothing is installed), so run it by hand after changing PHOSPHOR_CORE_VERSION:
//   node scripts/build-icon-index.mjs
// Phosphor is MIT licensed; the index holds names and keywords only, and each SVG is fetched on demand.

import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync, realpathSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const PHOSPHOR_CORE_VERSION = '2.1.1';
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

/** One line per icon, [name, React name, keywords]: its tags (without markers like *new*) and categories. */
export function toIndex(icons, version) {
  const rows = icons.map((i) => {
    const words = [...new Set([...i.tags.filter((t) => !t.startsWith('*')), ...i.categories].map((w) => w.toLowerCase()))];
    return JSON.stringify([i.name, i.pascal_name, words.join(' ')]);
  });
  return `{"version":${JSON.stringify(version)},"icons":[\n${rows.join(',\n')}\n]}\n`;
}

async function main() {
  const dir = mkdtempSync(join(tmpdir(), 'phosphor-core-'));
  try {
    const win = process.platform === 'win32';
    execFileSync(win ? 'npm.cmd' : 'npm', ['pack', `@phosphor-icons/core@${PHOSPHOR_CORE_VERSION}`, '--silent'], { cwd: dir, shell: win });
    execFileSync('tar', ['-xzf', `phosphor-icons-core-${PHOSPHOR_CORE_VERSION}.tgz`], { cwd: dir });
    const { icons } = await import(pathToFileURL(join(dir, 'package', 'dist', 'index.mjs')).href);
    mkdirSync(join(ROOT, 'assets', 'icons'), { recursive: true });
    writeFileSync(join(ROOT, 'assets', 'icons', 'phosphor-index.json'), toIndex(icons, PHOSPHOR_CORE_VERSION));
    console.log(`Wrote assets/icons/phosphor-index.json: ${icons.length} icons from @phosphor-icons/core@${PHOSPHOR_CORE_VERSION}.`);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href) {
  main().catch((e) => {
    console.error(`build-icon-index: ${e.message}`);
    process.exit(1);
  });
}
