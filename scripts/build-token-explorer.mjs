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
const testCategorization = args.includes('--test-categorization');

// ---- help ----
if (showHelp) {
  console.log(`
AZM X Token Explorer Generator

Usage:
  node scripts/build-token-explorer.mjs [options]

Options:
  --dry-run              Parse tokens and output statistics without generating HTML
  --test-categorization  Test token categorization and display breakdown by type
  --help                 Show this help message

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

// ---- categorize tokens by type ----
function categorizeTokens() {
  const categories = {
    'Color': [],
    'Spacing': [],
    'Typography': [],
    'Border': [],
    'Effects': []
  };

  const uncategorized = [];

  for (const [sectionName, section] of Object.entries(sections)) {
    for (const [tokenName, tokenValue] of Object.entries(section.tokens)) {
      const token = {
        name: tokenName,
        value: tokenValue,
        section: sectionName,
        modes: section.modes || ['Mode 1']
      };

      // Determine category based on token name patterns
      if (isColorToken(tokenName)) {
        categories['Color'].push(token);
      } else if (isSpacingToken(tokenName)) {
        categories['Spacing'].push(token);
      } else if (isTypographyToken(tokenName)) {
        categories['Typography'].push(token);
      } else if (isBorderToken(tokenName)) {
        categories['Border'].push(token);
      } else if (isEffectsToken(tokenName)) {
        categories['Effects'].push(token);
      } else {
        uncategorized.push(token);
      }
    }
  }

  return { categories, uncategorized };
}

// ---- category detection helpers ----
function isColorToken(name) {
  // Direct color tokens
  if (name.startsWith('color/') ||
      name.startsWith('brand/') ||
      name.startsWith('accent/') ||
      name.startsWith('surface/') ||
      name.startsWith('text/') ||
      name.startsWith('icon/') ||
      name.startsWith('stroke/') ||
      name.startsWith('fill/') ||
      name.startsWith('status/') ||
      name.startsWith('action/') ||
      name.startsWith('overlay/') ||
      name.startsWith('gradient/') ||
      name.startsWith('interactive/') ||
      name.startsWith('state/') ||
      name.startsWith('heat/') ||
      name.startsWith('bg/') ||
      name.startsWith('logo/fill/')) {
    return true;
  }

  // Component tokens that end with color-related properties
  if (name.includes('/surface') ||
      name.includes('/mark') ||
      name.includes('/fill') ||
      name.includes('/track') ||
      name.includes('/eyebrow') ||
      name.includes('/title') ||
      name.includes('/lead') ||
      name.includes('/body') ||
      name.includes('/tags') ||
      name.includes('/logo') ||
      name.includes('/rule') ||
      name.includes('/page-number') ||
      name.includes('/mockup') ||
      name.includes('/frame') ||
      name.includes('/label') ||
      name.includes('/value')) {
    return true;
  }

  return false;
}

function isSpacingToken(name) {
  if (name.startsWith('size/space/') ||
      name.startsWith('size/icon/') ||
      name.startsWith('size/doc/') ||
      name.startsWith('space/') ||
      name.startsWith('padding/') ||
      name.startsWith('margin/') ||
      name.startsWith('gap/') ||
      name.startsWith('slide/') ||
      name.startsWith('logo/clear-space')) {
    return true;
  }

  // Component tokens that end with spacing properties
  if (name.includes('/padding') ||
      name.includes('/margin') ||
      name.includes('/gap') ||
      name.includes('/height') ||
      name.includes('/width')) {
    return true;
  }

  return false;
}

function isTypographyToken(name) {
  return name.startsWith('size/font/') ||
         name.startsWith('size/line/') ||
         name.startsWith('font/family/') ||
         name.startsWith('font/weight/') ||
         name.startsWith('font/') ||
         name.startsWith('size/tracking/') ||
         name.startsWith('typography/') ||
         name.startsWith('type/') ||
         name.startsWith('weight/') ||
         name.startsWith('text/size') ||
         name.startsWith('text/weight') ||
         name.startsWith('text/line');
}

function isBorderToken(name) {
  if (name.startsWith('size/radius/') ||
      name.startsWith('size/border/') ||
      name.startsWith('border/') ||
      name.startsWith('border-width/') ||
      name.startsWith('radius/') ||
      name.startsWith('outline/')) {
    return true;
  }

  // Component tokens that end with border properties
  if (name.includes('/border') ||
      name.includes('/radius')) {
    return true;
  }

  return false;
}

function isEffectsToken(name) {
  return name.startsWith('size/opacity/') ||
         name.startsWith('opacity/') ||
         name.startsWith('shadow/') ||
         name.startsWith('blur/') ||
         name.startsWith('elevation/') ||
         name.startsWith('effect/');
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

// ---- test categorization mode ----
if (testCategorization) {
  const { categories, uncategorized } = categorizeTokens();
  const stats = countTokens();

  console.log('Token Explorer - Categorization Test');
  console.log('='.repeat(50));
  console.log(`Version:        ${DATA.$meta.version}`);
  console.log(`Total Tokens:   ${stats.totalTokens}`);
  console.log('');
  console.log('Categorization Results:');
  console.log('-'.repeat(50));

  let totalCategorized = 0;
  const categoryKeys = Object.keys(categories).sort();

  for (const categoryName of categoryKeys) {
    const tokens = categories[categoryName];
    totalCategorized += tokens.length;
    console.log(`${categoryName}:`);
    console.log(`  Count: ${tokens.length}`);

    // Show sample tokens (first 5)
    if (tokens.length > 0) {
      console.log('  Samples:');
      const samples = tokens.slice(0, 5);
      for (const token of samples) {
        console.log(`    - ${token.name}`);
      }
      if (tokens.length > 5) {
        console.log(`    ... and ${tokens.length - 5} more`);
      }
    }
    console.log('');
  }

  // Show uncategorized tokens if any
  if (uncategorized.length > 0) {
    console.log('Uncategorized:');
    console.log(`  Count: ${uncategorized.length}`);
    console.log('  Samples:');
    const samples = uncategorized.slice(0, 50);
    for (const token of samples) {
      console.log(`    - ${token.name}`);
    }
    if (uncategorized.length > 50) {
      console.log(`    ... and ${uncategorized.length - 50} more`);
    }
    console.log('');
  }

  console.log('-'.repeat(50));
  console.log(`Total categorized: ${totalCategorized} / ${stats.totalTokens}`);
  console.log(`Categories found:  ${categoryKeys.length}`);
  console.log('');

  // Validation
  const expectedCategories = 5;
  const success = categoryKeys.length === expectedCategories && uncategorized.length === 0;

  if (success) {
    console.log(`✓ All ${expectedCategories} collections categorized correctly`);
    console.log(`✓ All tokens successfully categorized`);
    process.exit(0);
  } else {
    if (categoryKeys.length !== expectedCategories) {
      console.error(`✗ Expected ${expectedCategories} categories, found ${categoryKeys.length}`);
    }
    if (uncategorized.length > 0) {
      console.error(`✗ Not all tokens categorized: ${totalCategorized} / ${stats.totalTokens}`);
      console.error(`✗ ${uncategorized.length} tokens remain uncategorized`);
    }
    process.exit(1);
  }
}

// ---- generate HTML explorer ----
// (This will be implemented in subsequent subtasks)
console.error('HTML generation not yet implemented');
console.error('Run with --dry-run to verify token parsing');
process.exit(1);
