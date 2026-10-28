#!/usr/bin/env node
// Any Phosphor icon, one at a time: find it by name or keyword, then fetch only its SVG.
//
//   node scripts/icons.mjs search <words…> [--limit 20]      matching icons, best first: name, React name, keywords
//   node scripts/icons.mjs url <name> [--weight light]        the SVG's address
//   node scripts/icons.mjs get <name> [--weight light] [--color #111927] [--out <file>]
//                                                            writes that one SVG (or prints it), optionally recoloured
//
// The names and keywords come from assets/icons/phosphor-index.json (scripts/build-icon-index.mjs), so the
// search works offline. Only `get` touches the network, for the one file, from jsDelivr, pinned to the
// index's version. Weights are Regular and Light only, as the brand allows; Fill, Duotone, Bold and Thin
// are refused. Names and keywords are English.

import { readFileSync, writeFileSync, realpathSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
export const WEIGHTS = ['regular', 'light'];

export function loadIndex(root = ROOT) {
  return JSON.parse(readFileSync(join(root, 'assets', 'icons', 'phosphor-index.json'), 'utf8'));
}

const flat = (s) => s.toLowerCase().replace(/[-\s]/g, '');

/** Every icon that matches all the words, best first: the exact name, then names that start with a word,
 *  then names that hold it, then keywords. "arrowright", "ArrowRight" and "arrow-right" find the same icon. */
export function searchIcons(icons, query) {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return icons;
  const whole = flat(query);
  const scored = [];
  for (const icon of icons) {
    const name = flat(icon[0]);
    const keywords = ` ${icon[2]} `;
    let score = name === whole ? 100 : 0;
    for (const w of words) {
      const f = flat(w);
      if (name.startsWith(f)) score += 3;
      else if (name.includes(f)) score += 2;
      else if (keywords.includes(` ${w}`)) score += 1;
      else {
        score = -1;
        break;
      }
    }
    if (score >= 0) scored.push([score, icon]);
  }
  return scored.sort((a, b) => b[0] - a[0] || a[1][0].localeCompare(b[1][0])).map(([, icon]) => icon);
}

/** The icon's index row, found by its kebab-case or React name; an unknown name throws with suggestions. */
export function findIcon(icons, name) {
  const hit = icons.find((i) => i[0] === name || i[1] === name || flat(i[0]) === flat(name));
  if (hit) return hit;
  const near = searchIcons(icons, name).slice(0, 5).map((i) => i[0]);
  throw new Error(`no Phosphor icon is called "${name}".${near.length ? ` Did you mean ${near.join(', ')}?` : ' Try: node scripts/icons.mjs search <word>'}`);
}

export function checkWeight(weight) {
  if (!WEIGHTS.includes(weight)) throw new Error(`weight "${weight}" isn't allowed: AZM X uses Regular, or Light on dark. Never Fill, Duotone, Bold or Thin.`);
  return weight;
}

/** The SVG of one icon on jsDelivr, pinned to the index's version. The light weight has its own file name. */
export function iconUrl(name, weight, version) {
  checkWeight(weight);
  return `https://cdn.jsdelivr.net/npm/@phosphor-icons/core@${version}/assets/${weight}/${weight === 'light' ? `${name}-light` : name}.svg`;
}

/** Phosphor draws in currentColor; a deck or a document may need a fixed colour instead. */
export function recolour(svg, colour) {
  if (!/^#[0-9a-fA-F]{6}$/.test(colour)) throw new Error(`"${colour}" isn't a #RRGGBB colour.`);
  return svg.replace(/currentColor/g, colour.toUpperCase());
}

function option(args, flag, fallback) {
  const at = args.indexOf(flag);
  if (at < 0) return fallback;
  const value = args[at + 1];
  if (value === undefined || value.startsWith('--')) throw new Error(`${flag} needs a value.`);
  args.splice(at, 2);
  return value;
}

async function main(argv) {
  const args = [...argv];
  const command = args.shift();
  const { version, icons } = loadIndex();
  if (command === 'search') {
    const limit = Number(option(args, '--limit', '20'));
    const found = searchIcons(icons, args.join(' '));
    if (!found.length) return console.log(`No Phosphor icon matches "${args.join(' ')}". Names and keywords are English.`);
    for (const [name, pascal, keywords] of found.slice(0, limit)) console.log(`${name}\t${pascal}\t${keywords}`);
    if (found.length > limit) console.log(`… ${found.length - limit} more; add --limit ${found.length} to see them all.`);
    return;
  }
  if (command === 'url' || command === 'get') {
    const weight = checkWeight(option(args, '--weight', 'regular'));
    const colour = option(args, '--color', undefined);
    const out = option(args, '--out', undefined);
    if (!args[0]) throw new Error(`name an icon: node scripts/icons.mjs ${command} <name>`);
    const [name, pascal] = findIcon(icons, args[0]);
    const url = iconUrl(name, weight, version);
    if (command === 'url') return console.log(url);
    const res = await fetch(url, { signal: AbortSignal.timeout(20000) });
    if (!res.ok) throw new Error(`${res.status} reading ${url}`);
    let svg = await res.text();
    if (colour) svg = recolour(svg, colour);
    if (!out) return process.stdout.write(svg.endsWith('\n') ? svg : `${svg}\n`);
    writeFileSync(out, svg);
    console.log(`Wrote ${out}: ${name} (React: ${pascal}), ${weight}${colour ? `, ${colour.toUpperCase()}` : ''}.`);
    return;
  }
  throw new Error('use search <words…>, url <name> or get <name>. See the top of scripts/icons.mjs.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href) {
  main(process.argv.slice(2)).catch((e) => {
    console.error(`icons: ${e.message}`);
    process.exit(1);
  });
}
