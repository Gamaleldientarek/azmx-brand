#!/usr/bin/env node
/*
 * AZM X Token Explorer Generator
 *
 *   node scripts/build-token-explorer.mjs --dry-run
 *   node scripts/build-token-explorer.mjs > docs/token-explorer.html
 *
 * Reads assets/tokens/azmx-tokens.json and generates an interactive HTML explorer.
 * The explorer provides visual browsing, search, filtering by category, and one-click
 * copy for token names or resolved values.
 *
 * Usage:
 *   --dry-run    Parse tokens and output statistics without generating HTML
 *   --help       Show this help message
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const TOKEN_PATH = join(HERE, '..', 'assets', 'tokens', 'azmx-tokens.json');

const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
const showHelp = args.includes('--help');

// ---- help ----
if (showHelp) {
  console.log(`
AZM X Token Explorer Generator

Usage:
  node scripts/build-token-explorer.mjs [options]

Options:
  --dry-run    Parse tokens and output statistics without generating HTML
  --help       Show this help message

Output:
  By default, generates interactive HTML explorer to stdout
  Redirect to file: > docs/token-explorer.html
`);
  process.exit(0);
}

// ---- read and parse tokens ----
let DATA;
try {
  DATA = JSON.parse(readFileSync(TOKEN_PATH, 'utf8'));
} catch (err) {
  console.error(`Error reading tokens file: ${err.message}`);
  process.exit(1);
}

// ---- extract sections ----
const sections = {};
const sectionOrder = [];

for (const [key, value] of Object.entries(DATA)) {
  if (key === '$meta') continue;
  if (typeof value === 'object' && value !== null && 'tokens' in value) {
    sections[key] = value;
    sectionOrder.push(key);
  }
}

// ---- count tokens ----
function countTokens() {
  let totalTokens = 0;
  let totalSections = 0;
  const breakdown = {};

  for (const [name, section] of Object.entries(sections)) {
    const count = Object.keys(section.tokens).length;
    totalTokens += count;
    totalSections += 1;
    breakdown[name] = {
      count,
      modes: section.modes || ['Mode 1'],
      declaredCount: section.count
    };
  }

  return { totalTokens, totalSections, breakdown };
}

// ---- dry run mode ----
if (isDryRun) {
  const stats = countTokens();

  console.log('Token Explorer - Parse Statistics');
  console.log('='.repeat(50));
  console.log(`Version:        ${DATA.$meta.version}`);
  console.log(`Source:         ${DATA.$meta.source}`);
  console.log(`Exported:       ${DATA.$meta.exported}`);
  console.log(`File Key:       ${DATA.$meta.fileKey}`);
  console.log('');
  console.log(`Total Sections: ${stats.totalSections}`);
  console.log(`Total Tokens:   ${stats.totalTokens}`);
  console.log('');
  console.log('Breakdown by Section:');
  console.log('-'.repeat(50));

  for (const [name, data] of Object.entries(stats.breakdown)) {
    const modes = data.modes.join(', ');
    console.log(`${name}:`);
    console.log(`  Tokens: ${data.count}`);
    console.log(`  Modes:  ${modes}`);
    if (data.declaredCount && data.declaredCount !== data.count) {
      console.log(`  Note:   Declared count (${data.declaredCount}) differs from actual (${data.count})`);
    }
  }

  console.log('');
  console.log('✓ Successfully parsed token file');
  console.log(`✓ Found ${stats.totalTokens} tokens across ${stats.totalSections} sections`);

  process.exit(0);
}

// ---- generate HTML explorer ----
// (This will be implemented in subsequent subtasks)
console.error('HTML generation not yet implemented');
console.error('Run with --dry-run to verify token parsing');
process.exit(1);
