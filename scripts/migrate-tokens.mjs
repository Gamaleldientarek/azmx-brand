#!/usr/bin/env node
/*
 * AZM X Token Migration Orchestrator
 *
 *   node scripts/migrate-tokens.mjs --analyze --report --export
 *   node scripts/migrate-tokens.mjs --analyze-only
 *   node scripts/migrate-tokens.mjs --report-only
 *   node scripts/migrate-tokens.mjs --export-only
 *
 * Orchestrates the full token migration pipeline:
 * 1. Analyze token bindings (identify primitive usage)
 * 2. Generate migration map (primitive → semantic mappings with confidence scores)
 * 3. Create migration report (human-readable summary)
 * 4. Export to Figma format (DTCG v2025.10)
 *
 * By default, runs all steps. Use individual flags to run specific steps.
 */

import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = '.';

const args = process.argv.slice(2);

// Parse CLI flags
const flags = {
  analyze: args.includes('--analyze') || args.includes('--analyze-only'),
  report: args.includes('--report') || args.includes('--report-only'),
  export: args.includes('--export') || args.includes('--export-only'),
  analyzeOnly: args.includes('--analyze-only'),
  reportOnly: args.includes('--report-only'),
  exportOnly: args.includes('--export-only'),
  verbose: args.includes('--verbose') || args.includes('-v'),
  help: args.includes('--help') || args.includes('-h')
};

// If no specific flags, run all steps
if (!flags.analyze && !flags.report && !flags.export) {
  flags.analyze = true;
  flags.report = true;
  flags.export = true;
}

// Help text
if (flags.help) {
  console.log(`
AZM X Token Migration Orchestrator

Usage:
  node scripts/migrate-tokens.mjs [options]

Options:
  --analyze          Run analysis step (identify primitive token usage)
  --report           Run report generation step
  --export           Run Figma export step
  --analyze-only     Run ONLY the analysis step
  --report-only      Run ONLY the report generation step
  --export-only      Run ONLY the export step
  --verbose, -v      Show detailed output
  --help, -h         Show this help message

Examples:
  # Run full pipeline
  node scripts/migrate-tokens.mjs

  # Run all steps with verbose output
  node scripts/migrate-tokens.mjs --analyze --report --export --verbose

  # Run only analysis
  node scripts/migrate-tokens.mjs --analyze-only

  # Run report and export
  node scripts/migrate-tokens.mjs --report --export

Output:
  All generated files are saved to the current directory:
  - migration-map.json         Migration mappings with confidence scores
  - migration-report.md        Human-readable migration report
  - migration-figma.json       DTCG format for Figma import
  - migration-manual-review.json  Manual review items
`);
  process.exit(0);
}

// Note: Output files will be created in the current directory

const log = (msg) => console.log(`\n${msg}`);
const step = (num, msg) => console.log(`\n[${'='.repeat(60)}]`);

// Execute a script and return output
function runScript(scriptName, args = '', captureOutput = false) {
  const scriptPath = join(HERE, scriptName);
  const cmd = `node "${scriptPath}" ${args}`;

  if (flags.verbose) {
    console.log(`\n→ Running: ${cmd}`);
  }

  try {
    const result = execSync(cmd, {
      encoding: 'utf8',
      stdio: captureOutput ? 'pipe' : 'inherit'
    });
    return result;
  } catch (err) {
    console.error(`\n✗ Error running ${scriptName}:`);
    console.error(err.message);
    process.exit(1);
  }
}

// ============================================================================
// STEP 1: Analyze Token Bindings
// ============================================================================
if (flags.analyze) {
  step(1, 'STEP 1: Analyzing Token Bindings');
  log('Scanning azmx-tokens.json for primitive token usage...');
  log('━'.repeat(60));

  runScript('analyze-token-bindings.mjs', flags.verbose ? '--verbose' : '');

  log('✓ Analysis complete');
}

// ============================================================================
// STEP 2: Generate Migration Map
// ============================================================================
if (flags.report || flags.export || !flags.analyzeOnly) {
  step(2, 'STEP 2: Generating Migration Map');
  log('Creating primitive → semantic token mappings with confidence scores...');

  const mapData = runScript('generate-migration-map.mjs', '--json', true);

  // Save migration map to file
  const mapPath = 'migration-map.json';
  try {
    writeFileSync(mapPath, mapData, 'utf8');
  } catch (err) {
    // Fallback to shell redirection if writeFileSync fails
    const scriptPath = join(HERE, 'generate-migration-map.mjs');
    execSync(`node "${scriptPath}" --json > "${mapPath}"`, {
      encoding: 'utf8',
      stdio: 'inherit'
    });
  }

  const stats = JSON.parse(mapData).stats;
  log(`✓ Migration map generated: ${mapPath}`);
  log(`  - Total primitives: ${stats.total}`);
  log(`  - HIGH confidence: ${stats.HIGH}`);
  log(`  - MEDIUM confidence: ${stats.MEDIUM}`);
  log(`  - LOW confidence: ${stats.LOW}`);
  log(`  - MANUAL review: ${stats.MANUAL}`);
}

// ============================================================================
// STEP 3: Create Migration Report
// ============================================================================
if (flags.report) {
  step(3, 'STEP 3: Creating Migration Report');
  log('Generating human-readable migration report...');

  const reportPath = 'migration-report.md';
  const scriptPath = join(HERE, 'create-migration-report.mjs');
  const reportArgs = `--output stdout --input migration-map.json${flags.verbose ? ' --verbose' : ''}`;

  try {
    execSync(`node "${scriptPath}" ${reportArgs} > "${reportPath}" 2>&1`, {
      encoding: 'utf8',
      stdio: 'inherit'
    });
    log(`✓ Report generated: ${reportPath}`);
  } catch (err) {
    console.error(`\n✗ Error running create-migration-report.mjs:`);
    console.error(err.message);
    process.exit(1);
  }
}

// ============================================================================
// STEP 4: Export to Figma Format
// ============================================================================
if (flags.export) {
  step(4, 'STEP 4: Exporting to Figma Format');
  log('Generating DTCG v2025.10 format for Figma import...');

  const figmaPath = 'migration.json';
  const scriptPath = join(HERE, 'export-migration-to-figma.mjs');
  const exportArgs = `--output stdout${flags.verbose ? ' --verbose' : ''}`;

  try {
    execSync(`node "${scriptPath}" ${exportArgs} > "${figmaPath}" 2>&1`, {
      encoding: 'utf8',
      stdio: 'inherit'
    });
    log(`✓ Figma migration file generated: ${figmaPath}`);
  } catch (err) {
    console.error(`\n✗ Error running export-migration-to-figma.mjs:`);
    console.error(err.message);
    process.exit(1);
  }

  // Generate manual review file from migration map
  try {
    const mapPath = 'migration-map.json';
    if (existsSync(mapPath)) {
      const mapData = JSON.parse(readFileSync(mapPath, 'utf8'));
      const manualItems = [];

      for (const [primName, mapping] of Object.entries(mapData.mappings)) {
        if (mapping.confidence === 'MANUAL' || mapping.confidence === 'LOW') {
          manualItems.push({
            primitive: primName,
            value: mapping.value,
            category: mapping.category,
            confidence: mapping.confidence,
            reason: mapping.reason,
            suggestions: mapping.suggestions.slice(0, 5)
          });
        }
      }

      const manualReviewPath = 'migration-manual-review.json';
      const manualReviewData = JSON.stringify({
        "$meta": {
          "name": "Manual Review Required",
          "description": "Tokens that require manual review before migration. These have MANUAL or LOW confidence and need human judgment.",
          "total": manualItems.length
        },
        "items": manualItems
      }, null, 2);

      // Use shell redirection to write the file
      execSync(`echo '${manualReviewData.replace(/'/g, "'\\''")}' > "${manualReviewPath}"`, {
        encoding: 'utf8',
        stdio: 'inherit'
      });

      log(`✓ Manual review file generated: ${manualReviewPath}`);
    }
  } catch (err) {
    console.error('\n⚠️  Warning: Could not generate manual review file');
    if (flags.verbose) {
      console.error(err.message);
    }
  }
}

// ============================================================================
// SUMMARY
// ============================================================================
if (!flags.analyzeOnly && !flags.reportOnly && !flags.exportOnly) {
  console.log(`\n${'='.repeat(60)}`);
  console.log('MIGRATION PIPELINE COMPLETE');
  console.log('='.repeat(60));
  console.log('\nGenerated files:');

  const reportPath = 'migration-report.md';
  if (existsSync(reportPath)) {
    console.log(`  ✓ ${reportPath}`);
  }

  const mapPath = 'migration-map.json';
  if (existsSync(mapPath)) {
    console.log(`  ✓ ${mapPath}`);
  }

  const figmaPath = 'migration.json';
  if (existsSync(figmaPath)) {
    console.log(`  ✓ ${figmaPath}`);
  }

  const manualPath = 'migration-manual-review.json';
  if (existsSync(manualPath)) {
    console.log(`  ✓ ${manualPath}`);
  }

  console.log('\nNext steps:');
  console.log('  1. Review the migration report: migration-report.md');
  console.log('  2. Check manual review items: migration-manual-review.json');
  console.log('  3. Import migration file to Figma: migration.json');
  console.log('  4. Verify tokens-to-css.mjs produces identical output post-migration\n');
}
