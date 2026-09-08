#!/usr/bin/env node
/*
 * AZM X migration report generator
 *
 *   node scripts/create-migration-report.mjs --output report.md
 *   node scripts/create-migration-report.mjs --output report.md --verbose
 *
 * Generates a human-readable migration report from the migration map data.
 * The report includes:
 * - Executive summary (total primitives, auto-mappable %, manual review %)
 * - Category breakdown
 * - High-priority manual reviews (off-scale values)
 * - Detailed mapping table
 */

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { execSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));

const args = process.argv.slice(2);
const flag = n => { const i = args.indexOf('--' + n); return i === -1 ? null : args[i + 1]; };
const outputPath = flag('output');
const verbose = args.includes('--verbose');
const inputPath = flag('input');

if (!outputPath) {
  console.error('Error: --output flag required');
  console.error('Usage: node scripts/create-migration-report.mjs --output report.md');
  process.exit(1);
}

// Get migration map data
let migrationData;

if (inputPath && existsSync(inputPath)) {
  // Read from file if provided
  migrationData = JSON.parse(readFileSync(inputPath, 'utf8'));
} else {
  // Generate fresh migration map
  try {
    const mapScript = join(HERE, 'generate-migration-map.mjs');
    const output = execSync(`node "${mapScript}" --json`, { encoding: 'utf8' });
    migrationData = JSON.parse(output);
  } catch (err) {
    console.error('Error: Failed to generate migration map');
    console.error(err.message);
    process.exit(1);
  }
}

const { stats, mappings } = migrationData;

// Helper to format percentages
const pct = (part, total) => total === 0 ? '0.0' : ((part / total) * 100).toFixed(1);

// Generate report content
const lines = [];

lines.push('# Token Migration Report');
lines.push('');
lines.push(`Generated: ${new Date().toISOString().split('T')[0]}`);
lines.push('');

// Executive Summary
lines.push('## Executive Summary');
lines.push('');
lines.push(`**Total primitive tokens analyzed:** ${stats.total}`);
lines.push('');

const autoMappable = stats.HIGH + stats.MEDIUM;
const manualReview = stats.LOW + stats.MANUAL;

lines.push('### Confidence Distribution');
lines.push('');
lines.push(`| Confidence | Count | Percentage | Description |`);
lines.push(`|------------|-------|------------|-------------|`);
lines.push(`| **HIGH** | ${stats.HIGH} | ${pct(stats.HIGH, stats.total)}% | Exact semantic match - safe to auto-migrate |`);
lines.push(`| **MEDIUM** | ${stats.MEDIUM} | ${pct(stats.MEDIUM, stats.total)}% | Nearest neighbor - review recommended |`);
lines.push(`| **LOW** | ${stats.LOW} | ${pct(stats.LOW, stats.total)}% | Off-scale value - manual review required |`);
lines.push(`| **MANUAL** | ${stats.MANUAL} | ${pct(stats.MANUAL, stats.total)}% | Ambiguous or no direct mapping - manual review required |`);
lines.push('');

lines.push('### Migration Readiness');
lines.push('');
lines.push(`- **Auto-mappable:** ${autoMappable} tokens (${pct(autoMappable, stats.total)}%)`);
lines.push(`  - ${stats.HIGH} exact matches (HIGH confidence)`);
lines.push(`  - ${stats.MEDIUM} nearest neighbors (MEDIUM confidence)`);
lines.push('');
lines.push(`- **Manual review required:** ${manualReview} tokens (${pct(manualReview, stats.total)}%)`);
lines.push(`  - ${stats.LOW} off-scale values (LOW confidence)`);
lines.push(`  - ${stats.MANUAL} ambiguous or unmappable (MANUAL)`);
lines.push('');

// Category Breakdown
lines.push('## Category Breakdown');
lines.push('');

const categories = Object.entries(stats.byCategory).sort((a, b) => b[1].total - a[1].total);

lines.push(`| Category | Total | HIGH | MEDIUM | LOW | MANUAL | Auto-mappable % |`);
lines.push(`|----------|-------|------|--------|-----|--------|-----------------|`);

for (const [cat, catStats] of categories) {
  const autoMap = catStats.HIGH + catStats.MEDIUM;
  const autoPct = pct(autoMap, catStats.total);
  lines.push(`| ${cat} | ${catStats.total} | ${catStats.HIGH} | ${catStats.MEDIUM} | ${catStats.LOW} | ${catStats.MANUAL} | ${autoPct}% |`);
}
lines.push('');

// High-Priority Manual Reviews
lines.push('## High-Priority Manual Reviews');
lines.push('');
lines.push('These primitives require manual review due to off-scale values or ambiguous mappings:');
lines.push('');

const manualItems = Object.entries(mappings)
  .filter(([_, m]) => m.confidence === 'LOW' || m.confidence === 'MANUAL')
  .sort((a, b) => {
    // Sort by confidence (LOW first, then MANUAL) and category
    if (a[1].confidence !== b[1].confidence) {
      return a[1].confidence === 'LOW' ? -1 : 1;
    }
    return a[1].category.localeCompare(b[1].category);
  });

if (manualItems.length === 0) {
  lines.push('*No manual reviews required - all primitives have direct semantic mappings.*');
  lines.push('');
} else {
  lines.push(`### LOW Confidence (${stats.LOW} items)`);
  lines.push('');
  lines.push('Off-scale values with a nearest semantic option:');
  lines.push('');

  const lowItems = manualItems.filter(([_, m]) => m.confidence === 'LOW');
  if (lowItems.length === 0) {
    lines.push('*None*');
    lines.push('');
  } else {
    for (const [primName, mapping] of lowItems) {
      lines.push(`#### \`${primName}\``);
      lines.push(`- **Value:** ${mapping.value}`);
      lines.push(`- **Category:** ${mapping.category}`);
      lines.push(`- **Reason:** ${mapping.reason}`);
      if (mapping.suggestions.length > 0) {
        lines.push(`- **Suggestions:**`);
        mapping.suggestions.forEach((s, i) => {
          const marker = i === 0 ? '  1.' : `  ${i + 1}.`;
          lines.push(`${marker} \`${s.semantic}\` = ${s.semanticValue} (${s.distance} units away)`);
        });
      }
      lines.push('');
    }
  }

  lines.push(`### MANUAL Review (${stats.MANUAL} items)`);
  lines.push('');
  lines.push('Ambiguous mappings, colors, fonts, or categories without direct semantic equivalents:');
  lines.push('');

  const manualOnlyItems = manualItems.filter(([_, m]) => m.confidence === 'MANUAL');

  // Group by category for readability
  const byCategory = {};
  for (const [primName, mapping] of manualOnlyItems) {
    if (!byCategory[mapping.category]) {
      byCategory[mapping.category] = [];
    }
    byCategory[mapping.category].push([primName, mapping]);
  }

  for (const [cat, items] of Object.entries(byCategory).sort((a, b) => b[1].length - a[1].length)) {
    lines.push(`#### ${cat} (${items.length} items)`);
    lines.push('');

    if (verbose || items.length <= 10) {
      for (const [primName, mapping] of items) {
        lines.push(`- \`${primName}\` = ${mapping.value}`);
        lines.push(`  - ${mapping.reason}`);
      }
    } else {
      // Show first 5 examples if many items
      for (const [primName, mapping] of items.slice(0, 5)) {
        lines.push(`- \`${primName}\` = ${mapping.value}`);
        lines.push(`  - ${mapping.reason}`);
      }
      lines.push(`- *... and ${items.length - 5} more (use --verbose to see all)*`);
    }
    lines.push('');
  }
}

// Detailed Mapping Table
if (verbose) {
  lines.push('## Detailed Mapping Table');
  lines.push('');
  lines.push('Complete mapping for all primitives:');
  lines.push('');

  lines.push(`| Primitive | Value | Category | Confidence | Suggested Semantic | Semantic Value | Reason |`);
  lines.push(`|-----------|-------|----------|------------|--------------------|----------------|--------|`);

  const allItems = Object.entries(mappings).sort((a, b) => a[0].localeCompare(b[0]));

  for (const [primName, mapping] of allItems) {
    const suggested = mapping.suggestions.length > 0
      ? mapping.suggestions[0].semantic
      : '—';
    const suggestedValue = mapping.suggestions.length > 0
      ? mapping.suggestions[0].semanticValue
      : '—';
    const reason = mapping.reason.length > 60
      ? mapping.reason.substring(0, 57) + '...'
      : mapping.reason;

    lines.push(`| \`${primName}\` | ${mapping.value} | ${mapping.category} | **${mapping.confidence}** | \`${suggested}\` | ${suggestedValue} | ${reason} |`);
  }
  lines.push('');
}

// Summary Statistics
lines.push('## Migration Workflow');
lines.push('');
lines.push('### Recommended Approach');
lines.push('');
lines.push('1. **Auto-migrate HIGH confidence mappings** (exact matches)');
lines.push(`   - ${stats.HIGH} primitives with exact semantic equivalents`);
lines.push('   - Safe to migrate automatically');
lines.push('');
lines.push('2. **Review MEDIUM confidence mappings** (nearest neighbors)');
lines.push(`   - ${stats.MEDIUM} primitives with close semantic matches`);
lines.push('   - Quick review recommended to confirm appropriateness');
lines.push('');
lines.push('3. **Manually resolve LOW/MANUAL items**');
lines.push(`   - ${stats.LOW + stats.MANUAL} primitives requiring design decisions`);
lines.push('   - Review each case and choose appropriate semantic token');
lines.push('');

lines.push('### Next Steps');
lines.push('');
lines.push('1. Review this report and validate suggested mappings');
lines.push('2. For MANUAL items, make design decisions on appropriate semantic tokens');
lines.push('3. Generate Figma migration file: `node scripts/export-migration-to-figma.mjs`');
lines.push('4. Import migration file to Figma');
lines.push('5. Verify tokens-to-css.mjs produces identical output post-migration');
lines.push('');

// Footer
lines.push('---');
lines.push('');
lines.push(`*Report generated by create-migration-report.mjs*`);
lines.push(`*Source: ${migrationData.stats.total} primitives from azmx-tokens.json*`);

// Write report
const reportContent = lines.join('\n');
writeFileSync(outputPath, reportContent, 'utf8');

console.log(`✓ Migration report created: ${outputPath}`);
console.log(`  Total primitives: ${stats.total}`);
console.log(`  Auto-mappable: ${autoMappable} (${pct(autoMappable, stats.total)}%)`);
console.log(`  Manual review: ${manualReview} (${pct(manualReview, stats.total)}%)`);
console.log('');
console.log('Review the report for detailed mapping suggestions.');
if (!verbose) {
  console.log('Use --verbose for complete mapping table.');
}
