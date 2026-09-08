#!/usr/bin/env node
/*
 * AZM X token binding analyzer
 *
 *   node scripts/analyze-token-bindings.mjs --dry-run
 *
 * Scans assets/tokens/azmx-tokens.json and identifies which tokens directly
 * reference primitives. Shows the dependency graph of primitive usage.
 *
 * Output shows:
 * - Which primitives are referenced directly
 * - Which tokens (palette/semantic/component/canvas) bind to each primitive
 * - Statistics on primitive usage
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = JSON.parse(readFileSync(join(HERE, '..', 'assets', 'tokens', 'azmx-tokens.json'), 'utf8'));

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const verbose = args.includes('--verbose');

// Token sections
const prim = DATA['1. Primitives'].tokens;
const pal  = DATA['1b. Palette'].tokens;
const sem  = DATA['2. Semantic'].tokens;
const comp = DATA['3. Component'].tokens;
const canv = DATA['4. Canvas'].tokens;

// Track which tokens reference which primitives
const primitiveBindings = new Map(); // primitive name -> [tokens that reference it]

/**
 * Extract all @references from a value (string or array)
 */
function extractReferences(value) {
  if (typeof value === 'string' && value.startsWith('@')) {
    return [value.slice(1)];
  }
  if (Array.isArray(value)) {
    return value.filter(v => typeof v === 'string' && v.startsWith('@'))
               .map(v => v.slice(1));
  }
  return [];
}

/**
 * Check if a reference points directly to a primitive
 */
function isPrimitiveReference(ref) {
  return ref in prim;
}

/**
 * Analyze a token section and track primitive bindings
 */
function analyzeSection(tokens, sectionName) {
  const bindings = [];

  for (const [tokenName, tokenValue] of Object.entries(tokens)) {
    const refs = extractReferences(tokenValue);

    for (const ref of refs) {
      if (isPrimitiveReference(ref)) {
        bindings.push({
          token: tokenName,
          primitive: ref,
          section: sectionName
        });

        if (!primitiveBindings.has(ref)) {
          primitiveBindings.set(ref, []);
        }
        primitiveBindings.get(ref).push({
          token: tokenName,
          section: sectionName
        });
      }
    }
  }

  return bindings;
}

// Analyze all sections
console.log('# Token Binding Analysis');
console.log(`Source: ${DATA.$meta.source} v${DATA.$meta.version}`);
console.log(`Exported: ${DATA.$meta.exported}\n`);

const paletteBindings = analyzeSection(pal, 'Palette');
const semanticBindings = analyzeSection(sem, 'Semantic');
const componentBindings = analyzeSection(comp, 'Component');
const canvasBindings = analyzeSection(canv, 'Canvas');

const allBindings = [
  ...paletteBindings,
  ...semanticBindings,
  ...componentBindings,
  ...canvasBindings
];

// Statistics
console.log('## Summary');
console.log(`Total primitive bindings found: ${allBindings.length}`);
console.log(`Unique primitives referenced: ${primitiveBindings.size}`);
console.log(`Total primitives defined: ${Object.keys(prim).length}`);
console.log(`Unreferenced primitives: ${Object.keys(prim).length - primitiveBindings.size}\n`);

console.log('### Bindings by Section');
console.log(`Palette:   ${paletteBindings.length} bindings`);
console.log(`Semantic:  ${semanticBindings.length} bindings`);
console.log(`Component: ${componentBindings.length} bindings`);
console.log(`Canvas:    ${canvasBindings.length} bindings\n`);

// Most referenced primitives
const sortedPrimitives = [...primitiveBindings.entries()]
  .sort((a, b) => b[1].length - a[1].length);

console.log('## Top 10 Most Referenced Primitives');
sortedPrimitives.slice(0, 10).forEach(([prim, refs]) => {
  console.log(`${prim} (${refs.length} references)`);
  if (verbose) {
    refs.forEach(ref => console.log(`  - ${ref.section}: ${ref.token}`));
  }
});
console.log('');

// Unreferenced primitives
const allPrimNames = new Set(Object.keys(prim));
const referencedPrimNames = new Set(primitiveBindings.keys());
const unreferenced = [...allPrimNames].filter(p => !referencedPrimNames.has(p));

if (unreferenced.length > 0) {
  console.log(`## Unreferenced Primitives (${unreferenced.length})`);
  if (unreferenced.length <= 20 || verbose) {
    unreferenced.forEach(p => console.log(`- ${p}: ${prim[p]}`));
  } else {
    unreferenced.slice(0, 10).forEach(p => console.log(`- ${p}: ${prim[p]}`));
    console.log(`... and ${unreferenced.length - 10} more (use --verbose to see all)`);
  }
  console.log('');
}

// Detailed bindings by primitive (verbose mode)
if (verbose) {
  console.log('## All Primitive Bindings');
  for (const [prim, refs] of sortedPrimitives) {
    console.log(`\n### ${prim}`);
    console.log(`Value: ${DATA['1. Primitives'].tokens[prim]}`);
    console.log(`Referenced by ${refs.length} token(s):`);
    refs.forEach(ref => {
      console.log(`  - [${ref.section}] ${ref.token}`);
    });
  }
}

// Exit message
if (dryRun) {
  console.log('\n✓ Analysis complete (dry-run mode)');
} else {
  console.log('\n✓ Analysis complete');
  console.log('  Use --verbose for detailed binding information');
}
