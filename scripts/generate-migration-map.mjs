#!/usr/bin/env node
/*
 * AZM X migration mapper
 *
 *   node scripts/generate-migration-map.mjs --test-case 'size/space/12'
 *   node scripts/generate-migration-map.mjs --json > migration-map.json
 *
 * Generates primitive-to-semantic mappings with confidence scores.
 * For each primitive binding identified by analyze-token-bindings.mjs,
 * suggests the appropriate semantic token replacement.
 *
 * Confidence levels:
 * - HIGH: Exact value match (primitive value === semantic resolved value)
 * - MEDIUM: Nearest neighbor on the scale (within reasonable distance)
 * - LOW: Far from scale but has a nearest option
 * - MANUAL: Ambiguous (multiple equidistant options, or very off-scale)
 */

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = JSON.parse(readFileSync(join(HERE, '..', 'assets', 'tokens', 'azmx-tokens.json'), 'utf8'));

const args = process.argv.slice(2);
const asJson = args.includes('--json');

let testCase = null;
const testCaseIdx = args.indexOf('--test-case');
if (testCaseIdx !== -1 && args[testCaseIdx + 1]) {
  testCase = args[testCaseIdx + 1];
} else {
  const testCaseArg = args.find(a => a.startsWith('--test-case='));
  if (testCaseArg) {
    testCase = testCaseArg.split('=')[1];
  }
}

// Token sections
const prim = DATA['1. Primitives'].tokens;
const pal  = DATA['1b. Palette'].tokens;
const sem  = DATA['2. Semantic'].tokens;
const comp = DATA['3. Component'].tokens;

// Resolve a token reference to its primitive value
function resolve(ref, paletteIdx = 0, themeIdx = 0, depth = 0) {
  if (depth > 12) throw new Error('alias loop at ' + ref);
  if (typeof ref !== 'string' || !ref.startsWith('@')) return ref;
  const name = ref.slice(1);

  if (name in prim) return prim[name];
  if (name in pal)  return resolve(pal[name][paletteIdx], paletteIdx, themeIdx, depth + 1);
  if (name in sem)  return resolve(sem[name][themeIdx],   paletteIdx, themeIdx, depth + 1);
  if (name in comp) return resolve(comp[name],            paletteIdx, themeIdx, depth + 1);
  throw new Error('unknown token: ' + name);
}

// Categorize a primitive by its prefix
function categorizePrimitive(primName) {
  if (primName.startsWith('size/space/')) return 'spacing';
  if (primName.startsWith('size/font/')) return 'typography-size';
  if (primName.startsWith('size/line/')) return 'typography-line';
  if (primName.startsWith('size/radius/')) return 'radius';
  if (primName.startsWith('size/border/')) return 'border-width';
  if (primName.startsWith('size/opacity/')) return 'opacity';
  if (primName.startsWith('size/tracking/')) return 'tracking';
  if (primName.startsWith('size/icon/')) return 'icon-size';
  if (primName.startsWith('color/')) return 'color';
  if (primName.startsWith('font/')) return 'font';
  return 'other';
}

// Get semantic tokens by category
function getSemanticTokensByCategory(category) {
  const tokens = [];
  for (const [name, value] of Object.entries(sem)) {
    switch (category) {
      case 'spacing':
        if (name.startsWith('space/')) tokens.push({ name, value });
        break;
      case 'typography-size':
        if (name.includes('/size')) tokens.push({ name, value });
        break;
      case 'typography-line':
        if (name.includes('/line')) tokens.push({ name, value });
        break;
      case 'radius':
        if (name.startsWith('radius/')) tokens.push({ name, value });
        break;
      case 'border-width':
        if (name.startsWith('border-width/')) tokens.push({ name, value });
        break;
      case 'opacity':
        if (name.startsWith('opacity/')) tokens.push({ name, value });
        break;
      case 'tracking':
        if (name.startsWith('type/tracking/')) tokens.push({ name, value });
        break;
      case 'icon-size':
        if (name.startsWith('icon/size/')) tokens.push({ name, value });
        break;
      default:
        break;
    }
  }
  return tokens;
}

// Find semantic token mappings for a primitive
function findMappings(primName) {
  const primValue = prim[primName];
  const category = categorizePrimitive(primName);

  if (category === 'color' || category === 'font' || category === 'other') {
    // Colors and fonts don't have direct semantic mappings in the same way
    return {
      primitive: primName,
      value: primValue,
      category,
      suggestions: [],
      confidence: 'MANUAL',
      reason: `Category '${category}' requires manual review - no direct semantic mapping available`
    };
  }

  const candidates = getSemanticTokensByCategory(category);
  const matches = [];

  for (const candidate of candidates) {
    const resolved = resolve(candidate.value[0]); // Use light mode (index 0) for comparison

    if (typeof primValue === 'number' && typeof resolved === 'number') {
      const distance = Math.abs(resolved - primValue);
      const match = {
        semantic: candidate.name,
        semanticValue: resolved,
        distance,
        exactMatch: distance === 0
      };
      matches.push(match);
    } else if (primValue === resolved) {
      // Exact match for non-numeric values
      matches.push({
        semantic: candidate.name,
        semanticValue: resolved,
        distance: 0,
        exactMatch: true
      });
    }
  }

  // Sort by distance (closest first)
  matches.sort((a, b) => a.distance - b.distance);

  // Determine confidence
  let confidence, reason;
  const exactMatches = matches.filter(m => m.exactMatch);

  if (exactMatches.length > 0) {
    confidence = 'HIGH';
    reason = `Exact match found: ${exactMatches.map(m => m.semantic).join(', ')}`;
  } else if (matches.length === 0) {
    confidence = 'MANUAL';
    reason = 'No semantic tokens found in this category';
  } else {
    const nearest = matches[0];
    const secondNearest = matches[1];

    // Check if multiple tokens are equidistant (ambiguous)
    if (secondNearest && nearest.distance === secondNearest.distance) {
      confidence = 'MANUAL';
      reason = `Ambiguous - multiple equidistant options: ${matches.filter(m => m.distance === nearest.distance).map(m => m.semantic).join(', ')}`;
    } else if (nearest.distance <= 4) {
      // Close enough to scale
      confidence = 'MEDIUM';
      reason = `Nearest neighbor: ${nearest.semantic} (${nearest.distance} units away)`;
    } else if (nearest.distance <= 10) {
      // Further from scale
      confidence = 'LOW';
      reason = `Off-scale value, nearest: ${nearest.semantic} (${nearest.distance} units away)`;
    } else {
      // Very far from scale
      confidence = 'MANUAL';
      reason = `Very off-scale: nearest option ${nearest.distance} units away`;
    }
  }

  return {
    primitive: primName,
    value: primValue,
    category,
    suggestions: matches.slice(0, 3), // Top 3 suggestions
    confidence,
    reason
  };
}

// Test with a hypothetical value (for testing off-scale scenarios)
function findMappingsForHypothetical(tokenName, value) {
  const category = categorizePrimitive(tokenName);

  if (category === 'color' || category === 'font' || category === 'other') {
    return {
      primitive: tokenName,
      value,
      category,
      suggestions: [],
      confidence: 'MANUAL',
      reason: `Category '${category}' requires manual review - no direct semantic mapping available`
    };
  }

  const candidates = getSemanticTokensByCategory(category);
  const matches = [];

  for (const candidate of candidates) {
    const resolved = resolve(candidate.value[0]);

    if (typeof value === 'number' && typeof resolved === 'number') {
      const distance = Math.abs(resolved - value);
      matches.push({
        semantic: candidate.name,
        semanticValue: resolved,
        distance,
        exactMatch: distance === 0
      });
    }
  }

  matches.sort((a, b) => a.distance - b.distance);

  let confidence, reason;
  const exactMatches = matches.filter(m => m.exactMatch);

  if (exactMatches.length > 0) {
    confidence = 'HIGH';
    reason = `Exact match found: ${exactMatches.map(m => m.semantic).join(', ')}`;
  } else if (matches.length === 0) {
    confidence = 'MANUAL';
    reason = 'No semantic tokens found in this category';
  } else {
    const nearest = matches[0];
    const secondNearest = matches[1];

    if (secondNearest && nearest.distance === secondNearest.distance) {
      confidence = 'MANUAL';
      reason = `Ambiguous - multiple equidistant options: ${matches.filter(m => m.distance === nearest.distance).map(m => m.semantic).join(', ')}`;
    } else if (nearest.distance <= 4) {
      confidence = 'MEDIUM';
      reason = `Nearest neighbor: ${nearest.semantic} (${nearest.distance} units away)`;
    } else if (nearest.distance <= 10) {
      confidence = 'LOW';
      reason = `Off-scale value, nearest: ${nearest.semantic} (${nearest.distance} units away)`;
    } else {
      confidence = 'MANUAL';
      reason = `Very off-scale: nearest option ${nearest.distance} units away`;
    }
  }

  return {
    primitive: tokenName,
    value,
    category,
    suggestions: matches.slice(0, 3),
    confidence,
    reason,
    hypothetical: true
  };
}

// Main logic
if (testCase) {
  // Test a specific case
  let result;

  if (testCase in prim) {
    result = findMappings(testCase);
  } else {
    // Check if it's a hypothetical test case (e.g., 'size/space/12')
    const match = testCase.match(/^size\/(space|font|radius|border)\/(\d+(?:\.\d+)?)$/);
    if (match) {
      const value = parseFloat(match[2]);
      result = findMappingsForHypothetical(testCase, value);
    } else {
      console.error(`Error: '${testCase}' is not a primitive token and cannot be parsed as a test value`);
      console.error(`Example test cases: size/space/12, size/font/40, size/radius/6`);
      process.exit(1);
    }
  }

  if (asJson) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(`\n# Migration Mapping: ${result.primitive}`);
    console.log(`Value: ${result.value}`);
    console.log(`Category: ${result.category}`);
    console.log(`Confidence: ${result.confidence}`);
    console.log(`\n${result.reason}\n`);

    if (result.suggestions.length > 0) {
      console.log('Suggestions:');
      result.suggestions.forEach((s, i) => {
        const marker = i === 0 ? '→' : ' ';
        const matchType = s.exactMatch ? '✓ EXACT' : `~${s.distance} away`;
        console.log(`  ${marker} ${s.semantic}: ${s.semanticValue} (${matchType})`);
      });
    } else {
      console.log('No semantic token suggestions available.');
    }
  }
} else {
  // Generate full migration map for all primitives
  const allMappings = {};
  const stats = {
    total: 0,
    HIGH: 0,
    MEDIUM: 0,
    LOW: 0,
    MANUAL: 0,
    byCategory: {}
  };

  for (const primName of Object.keys(prim)) {
    const mapping = findMappings(primName);
    allMappings[primName] = mapping;

    stats.total++;
    stats[mapping.confidence]++;

    const cat = mapping.category;
    if (!stats.byCategory[cat]) {
      stats.byCategory[cat] = { total: 0, HIGH: 0, MEDIUM: 0, LOW: 0, MANUAL: 0 };
    }
    stats.byCategory[cat].total++;
    stats.byCategory[cat][mapping.confidence]++;
  }

  if (asJson) {
    console.log(JSON.stringify({ stats, mappings: allMappings }, null, 2));
  } else {
    console.log(`\n# Migration Map Generated`);
    console.log(`Source: ${DATA.$meta.source} v${DATA.$meta.version}\n`);
    console.log(`## Summary`);
    console.log(`Total primitives analyzed: ${stats.total}`);
    console.log(`  HIGH confidence:   ${stats.HIGH} (${(stats.HIGH/stats.total*100).toFixed(1)}%)`);
    console.log(`  MEDIUM confidence: ${stats.MEDIUM} (${(stats.MEDIUM/stats.total*100).toFixed(1)}%)`);
    console.log(`  LOW confidence:    ${stats.LOW} (${(stats.LOW/stats.total*100).toFixed(1)}%)`);
    console.log(`  MANUAL review:     ${stats.MANUAL} (${(stats.MANUAL/stats.total*100).toFixed(1)}%)\n`);

    console.log(`## By Category`);
    for (const [cat, catStats] of Object.entries(stats.byCategory)) {
      console.log(`\n${cat}: ${catStats.total} tokens`);
      console.log(`  HIGH: ${catStats.HIGH}, MEDIUM: ${catStats.MEDIUM}, LOW: ${catStats.LOW}, MANUAL: ${catStats.MANUAL}`);
    }

    console.log(`\n✓ Use --json to export full mapping data`);
    console.log(`✓ Use --test-case 'primitive/name' to test individual mappings`);
  }
}
