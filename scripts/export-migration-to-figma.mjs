#!/usr/bin/env node
/*
 * AZM X migration to Figma exporter
 *
 *   node scripts/export-migration-to-figma.mjs --output migration.json
 *   node scripts/export-migration-to-figma.mjs --include-low --output full-migration.json
 *
 * Generates DTCG format migration file for Figma import.
 * Only includes HIGH and MEDIUM confidence mappings by default.
 * Use --include-low to also include LOW confidence mappings.
 * MANUAL mappings are always exported to a separate review file.
 *
 * DTCG v2025.10 format:
 * - Hierarchical structure using dots (token.path.name)
 * - $value and $type keys
 * - References use curly braces {token.name}
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { execSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = JSON.parse(readFileSync(join(HERE, '..', 'assets', 'tokens', 'azmx-tokens.json'), 'utf8'));

const args = process.argv.slice(2);

// Parse CLI arguments
let outputPath = 'migration.json';
let includeLow = false;
let verbose = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--output' && args[i + 1]) {
    outputPath = args[i + 1];
    i++;
  } else if (args[i].startsWith('--output=')) {
    outputPath = args[i].split('=')[1];
  } else if (args[i] === '--include-low') {
    includeLow = true;
  } else if (args[i] === '--verbose' || args[i] === '-v') {
    verbose = true;
  }
}

// Generate migration map data
const mapScript = join(HERE, 'generate-migration-map.mjs');
const mapOutput = execSync(`node "${mapScript}" --json`, {
  encoding: 'utf8',
  shell: '/bin/bash'
});
const migrationData = JSON.parse(mapOutput);

// Type mapping for DTCG
const DTCG_TYPE = {
  'spacing': 'dimension',
  'typography-size': 'dimension',
  'typography-line': 'dimension',
  'radius': 'dimension',
  'border-width': 'dimension',
  'opacity': 'number',
  'tracking': 'dimension',
  'icon-size': 'dimension',
  'color': 'color',
  'font': 'fontFamily'
};

// Convert primitive token to DTCG path (replace / with .)
function toDTCGPath(tokenName) {
  return tokenName.replace(/\//g, '.');
}

// Convert semantic token reference to DTCG alias
function toAlias(tokenName) {
  return '{' + tokenName.replace(/\//g, '.') + '}';
}

// Build DTCG structure from mappings
function buildDTCGTree(mappings, confidenceLevels) {
  const tree = {};
  const stats = {
    included: 0,
    skipped: 0,
    byConfidence: {},
    byCategory: {}
  };

  for (const [primName, mapping] of Object.entries(mappings)) {
    // Skip if not in allowed confidence levels
    if (!confidenceLevels.includes(mapping.confidence)) {
      stats.skipped++;
      continue;
    }

    // Skip if no suggestions
    if (!mapping.suggestions || mapping.suggestions.length === 0) {
      stats.skipped++;
      continue;
    }

    // Take the top suggestion (first one, which has the smallest distance)
    const topSuggestion = mapping.suggestions[0];
    const semanticToken = topSuggestion.semantic;

    // Build nested structure
    const parts = primName.split('/');
    let node = tree;

    parts.forEach((part, i) => {
      if (i === parts.length - 1) {
        // Leaf node - create token definition
        node[part] = {
          $value: toAlias(semanticToken),
          $type: DTCG_TYPE[mapping.category] || 'other',
          $description: `Migration from ${primName} (${mapping.confidence} confidence${topSuggestion.exactMatch ? ', exact match' : ', ~' + topSuggestion.distance + ' away'})`
        };

        // Update stats
        stats.included++;
        stats.byConfidence[mapping.confidence] = (stats.byConfidence[mapping.confidence] || 0) + 1;
        stats.byCategory[mapping.category] = (stats.byCategory[mapping.category] || 0) + 1;
      } else {
        // Intermediate node - ensure object exists
        if (!node[part] || typeof node[part] !== 'object' || node[part].$value !== undefined) {
          node[part] = {};
        }
        node = node[part];
      }
    });
  }

  return { tree, stats };
}

// Build manual review file (MANUAL and optionally LOW confidence)
function buildManualReviewData(mappings) {
  const manualItems = [];

  for (const [primName, mapping] of Object.entries(mappings)) {
    if (mapping.confidence === 'MANUAL' || (!includeLow && mapping.confidence === 'LOW')) {
      manualItems.push({
        primitive: primName,
        value: mapping.value,
        category: mapping.category,
        confidence: mapping.confidence,
        reason: mapping.reason,
        suggestions: mapping.suggestions.slice(0, 5) // Top 5 suggestions
      });
    }
  }

  return manualItems;
}

// Main export logic
const confidenceLevels = includeLow ? ['HIGH', 'MEDIUM', 'LOW'] : ['HIGH', 'MEDIUM'];
const { tree: dtcgTree, stats: migrationStats } = buildDTCGTree(migrationData.mappings, confidenceLevels);
const manualReview = buildManualReviewData(migrationData.mappings);

// Create final DTCG output
const dtcgOutput = {
  "$meta": {
    "name": "AZM X Token Migration",
    "version": "1.0.0",
    "source": "Primitive to Semantic Token Migration",
    "generated": new Date().toISOString().split('T')[0],
    "description": "Migrated token mappings for Figma import. Only includes HIGH" + (includeLow ? ", MEDIUM, and LOW" : " and MEDIUM") + " confidence mappings."
  },
  "primitives": dtcgTree
};

// Write main migration file
const absoluteOutputPath = resolve(process.cwd(), outputPath);
writeFileSync(absoluteOutputPath, JSON.stringify(dtcgOutput, null, 2), 'utf8');

// Write manual review file
const reviewPath = absoluteOutputPath.replace(/\.json$/, '') + '-manual-review.json';
writeFileSync(reviewPath, JSON.stringify({
  "$meta": {
    "name": "Manual Review Required",
    "description": "Tokens that require manual review before migration. These have MANUAL or LOW confidence and need human judgment.",
    "total": manualReview.length
  },
  "items": manualReview
}, null, 2), 'utf8');

// Output summary
if (verbose) {
  console.log('\n# Figma Migration Export');
  console.log(`Source: ${DATA.$meta.source} v${DATA.$meta.version}\n`);
  console.log('## Migration Statistics');
  console.log(`Total primitives analyzed: ${migrationData.stats.total}`);
  console.log(`Included in migration file: ${migrationStats.included}`);
  console.log(`Skipped (manual review): ${migrationStats.skipped}\n`);

  console.log('## By Confidence');
  for (const [conf, count] of Object.entries(migrationStats.byConfidence)) {
    console.log(`  ${conf}: ${count}`);
  }

  console.log('\n## By Category');
  for (const [cat, count] of Object.entries(migrationStats.byCategory)) {
    console.log(`  ${cat}: ${count}`);
  }

  console.log(`\n## Output Files`);
  console.log(`  Migration file: ${absoluteOutputPath}`);
  console.log(`  Manual review: ${reviewPath}`);
  console.log(`  Manual review items: ${manualReview.length}`);
} else {
  console.log(`✓ Migration file created: ${absoluteOutputPath}`);
  console.log(`✓ Manual review file created: ${reviewPath}`);
  console.log(`  Included: ${migrationStats.included} tokens (${confidenceLevels.join(', ')} confidence)`);
  console.log(`  Manual review: ${manualReview.length} tokens`);
}
