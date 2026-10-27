#!/usr/bin/env node
// The skill's link to the private AZM X Design System (Gamaleldientarek/azmx-design-system).
//
//   node scripts/design-system.mjs status              can this person read the system? pinned and latest versions
//   node scripts/design-system.mjs fetch-tokens <dir>  the system's azmx-tokens.css (plain CSS variables) into <dir>
//   node scripts/design-system.mjs fetch-fonts <dir>   Azm X 3.007 and thmanyah (woff2, plus index.ts for next/font) into <dir>
//   node scripts/design-system.mjs drift               where the skill's tokens and the system's differ
//   --ref <tag>   another version than the pinned one in config/design-system.json
//
// The system is private and this skill is public, so nothing from the system is stored here.
// Every read uses the person's own GitHub sign-in: GITHUB_TOKEN, GH_TOKEN, or `gh auth login`.
// AZMX_DS_DIR=<local clone> reads from a clone instead (git show <ref>:<path>, so its working tree is never used).

import { readFileSync, writeFileSync, mkdirSync, realpathSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join, basename } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { compareVersions } from './check-update.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

export function loadConfig(root = ROOT) {
  return JSON.parse(readFileSync(join(root, 'config', 'design-system.json'), 'utf8'));
}

// ---- CSS variables -------------------------------------------------------------------------------

/** Every rule block of a stylesheet as { selector, vars }, comments removed. Nested blocks aren't used. */
export function parseCssBlocks(css) {
  const clean = css.replace(/\/\*[\s\S]*?\*\//g, '');
  const blocks = [];
  const re = /([^{}]+)\{([^{}]*)\}/g;
  let m;
  while ((m = re.exec(clean))) {
    const vars = {};
    for (const decl of m[2].split(';')) {
      const i = decl.indexOf(':');
      if (i < 0) continue;
      const name = decl.slice(0, i).trim();
      if (name.startsWith('--')) vars[name] = decl.slice(i + 1).trim();
    }
    blocks.push({ selector: m[1].trim().replace(/\s+/g, ' '), vars });
  }
  return blocks;
}

/** Resolves var(--x) and var(--x, fallback) through the map, recursively; loops are left as written. */
export function resolveVars(map) {
  const out = {};
  const resolveOne = (value, seen) =>
    value.replace(/var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*))?\)/g, (whole, name, fallback) => {
      if (seen.has(name)) return whole;
      if (name in map) return resolveOne(map[name], new Set([...seen, name]));
      return fallback !== undefined ? resolveOne(fallback.trim(), seen) : whole;
    });
  for (const [k, v] of Object.entries(map)) out[k] = resolveOne(v, new Set([k]));
  return out;
}

const merge = (blocks, test) => Object.assign({}, ...blocks.filter((b) => test(b.selector)).map((b) => b.vars));
const selectors = (s) => s.split(',').map((x) => x.trim());

/** The variables in force for a palette and a mode in the design system's dist/azmx-tokens.css. */
export function dsScope(blocks, palette, mode) {
  const base = merge(blocks, (s) => s === ':root');
  const pal = merge(blocks, (s) => selectors(s).includes(`[data-palette="${palette}"]`));
  const light = merge(blocks, (s) => selectors(s).includes('[data-palette]'));
  const dark = mode === 'dark' ? merge(blocks, (s) => selectors(s)[0] === '.dark') : {};
  return resolveVars({ ...base, ...pal, ...light, ...dark });
}

/** The variables in force for a palette and a mode in the skill's azmx-tokens.css. */
export function skillScope(blocks, palette, mode) {
  const has = (s, part) => s.includes(part);
  const theme = '[data-theme="dark"]';
  const pal = `[data-palette="${palette}"]`;
  return resolveVars(
    merge(blocks, (s) => {
      if (s === ':root' || s.startsWith(':root,')) return true;
      if (s === theme) return mode === 'dark';
      if (s === pal) return true;
      if (s === `${pal}${theme}`) return mode === 'dark';
      return has(s, '__never__');
    }),
  );
}

/** A colour as #RRGGBB or #RRGGBBAA (opaque alpha dropped), or null when the value isn't a plain colour. */
export function normColour(value) {
  const v = String(value).trim().toLowerCase();
  const hex = v.match(/^#([0-9a-f]{3,8})$/);
  if (hex) {
    let h = hex[1];
    if (h.length === 3 || h.length === 4) h = [...h].map((c) => c + c).join('');
    if (h.length === 8 && h.endsWith('ff')) h = h.slice(0, 6);
    return h.length === 6 || h.length === 8 ? `#${h.toUpperCase()}` : null;
  }
  const rgb = v.match(/^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)\s*(?:[,/]\s*([\d.]+%?))?\s*\)$/);
  if (rgb) {
    const to2 = (n) => Math.round(Number(n)).toString(16).padStart(2, '0');
    let a = rgb[4];
    if (a === undefined) a = 1;
    else a = a.endsWith('%') ? parseFloat(a) / 100 : parseFloat(a);
    const alpha = a >= 1 ? '' : to2(a * 255);
    return `#${to2(rgb[1])}${to2(rgb[2])}${to2(rgb[3])}${alpha}`.toUpperCase();
  }
  if (v === 'white') return '#FFFFFF';
  if (v === 'black') return '#000000';
  return null;
}

/**
 * Colour tokens both files name the same way (`--surface-page` in the system, `--azmx-surface-page` in the
 * skill) whose values differ. Values that aren't plain colours on either side (color-mix, gradients) are skipped.
 */
export function compareColours(ds, skill, prefixes) {
  const diffs = [];
  for (const [name, value] of Object.entries(ds)) {
    const bare = name.slice(2);
    if (!prefixes.some((p) => bare.startsWith(p))) continue;
    const mine = skill[`--azmx-${bare}`];
    if (mine === undefined) continue;
    const a = normColour(value);
    const b = normColour(mine);
    if (a && b && a !== b) diffs.push({ token: bare, system: a, skill: b });
  }
  return diffs;
}

// ---- spacing and radius --------------------------------------------------------------------------

/** The skill's spacing scale and radius names from its token file (aliases resolved to numbers). */
export function skillScales(tokens) {
  const prim = tokens['1. Primitives'].tokens;
  const sem = tokens['2. Semantic'].tokens;
  const value = (alias) => prim[String(alias).replace(/^@/, '')];
  const spacing = Object.keys(prim)
    .filter((k) => k.startsWith('size/space/'))
    .map((k) => prim[k])
    .sort((a, b) => a - b);
  const radius = {};
  for (const [k, v] of Object.entries(sem)) if (k.startsWith('radius/')) radius[k.slice(7)] = value(v[0]);
  return { spacing, radius };
}

/** Differences between the system's site.json scales and the skill's. */
export function compareScales(site, skill) {
  const diffs = [];
  const sysSpacing = [...site.spacing].sort((a, b) => a - b);
  const missing = sysSpacing.filter((n) => !skill.spacing.includes(n));
  const extra = skill.spacing.filter((n) => !sysSpacing.includes(n));
  if (missing.length || extra.length) diffs.push({ token: 'spacing', system: sysSpacing.join(' '), skill: skill.spacing.join(' ') });
  for (const [name, raw] of Object.entries(site.radius)) {
    const px = parseInt(raw, 10);
    const mine = skill.radius[name];
    if (mine !== px) diffs.push({ token: `radius/${name}`, system: px, skill: mine ?? 'missing' });
  }
  for (const name of Object.keys(skill.radius)) {
    if (!(name in site.radius)) diffs.push({ token: `radius/${name}`, system: 'missing', skill: skill.radius[name] });
  }
  return diffs;
}

// ---- the drift report ----------------------------------------------------------------------------

/**
 * Everything that differs, sorted into errors (drift nobody ruled on), known (listed in the config with a
 * reason) and notes (a newer system release, a stale colour source in the system).
 */
export function driftReport({ config, dsCss, skillCss, site, skillTokens, sourceMatches, latest }) {
  const known = new Map((config.known ?? []).map((k) => [k.token, k.why]));
  const dsBlocks = parseCssBlocks(dsCss);
  const skillBlocks = parseCssBlocks(skillCss);
  const errors = [];
  const accepted = [];
  const notes = [];
  for (const palette of config.compare.palettes) {
    for (const mode of config.compare.modes) {
      const diffs = compareColours(dsScope(dsBlocks, palette, mode), skillScope(skillBlocks, palette, mode), config.compare.prefixes);
      for (const d of diffs) {
        const row = { ...d, where: `${palette}/${mode}` };
        const why = known.get(d.token) ?? known.get(`${d.token}@${palette}/${mode}`);
        (why ? accepted : errors).push(why ? { ...row, why } : row);
      }
    }
  }
  for (const d of compareScales(site, skillScales(skillTokens))) {
    const why = known.get(d.token);
    (why ? accepted : errors).push(why ? { ...d, where: 'scale', why } : { ...d, where: 'scale' });
  }
  if (sourceMatches === false)
    notes.push("The system's colour source (tokens/source/azmx-tokens.json) is older than this skill's token file: run `npm run sync-brand && npm run tokens` in the design system.");
  if (latest && compareVersions(latest, config.ref) > 0)
    notes.push(`The design system has a newer release, ${latest}; this skill is pinned to ${config.ref} in config/design-system.json.`);
  return { errors, accepted, notes };
}

export function formatReport({ errors, accepted, notes }, ref) {
  const lines = [`Drift check against the AZM X Design System ${ref}`];
  const row = (d) => `  ${d.where.padEnd(14)} ${String(d.token).padEnd(28)} system ${d.system}  skill ${d.skill}`;
  if (errors.length) lines.push(`\n${errors.length} difference(s) nobody has ruled on:`, ...errors.map(row));
  if (accepted.length) lines.push(`\n${accepted.length} known difference(s):`, ...accepted.map((d) => `${row(d)}\n${' '.repeat(18)}${d.why}`));
  if (notes.length) lines.push('', ...notes.map((n) => `Note: ${n}`));
  if (!errors.length) lines.push('\nNo unexplained drift.');
  return lines.join('\n');
}

// ---- reading the private repository --------------------------------------------------------------

/** The person's GitHub token, the same way the @azmxsa/cli installer finds it. */
export function githubToken(env = process.env, run = execFileSync) {
  if (env.GITHUB_TOKEN) return env.GITHUB_TOKEN;
  if (env.GH_TOKEN) return env.GH_TOKEN;
  try {
    return run('gh', ['auth', 'token'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim() || undefined;
  } catch {
    return undefined;
  }
}

const REF = /^[A-Za-z0-9._-]+$/;

export function reader(config, ref, env = process.env) {
  if (!REF.test(ref) || ref.startsWith('.')) throw new Error(`"${ref}" is not a version tag or branch name.`);
  if (env.AZMX_DS_DIR) {
    const dir = env.AZMX_DS_DIR;
    return {
      where: dir,
      async text(path) {
        return execFileSync('git', ['-C', dir, 'show', `${ref}:${path}`], { encoding: 'utf8', maxBuffer: 64 << 20 });
      },
      async bytes(path) {
        return execFileSync('git', ['-C', dir, 'show', `${ref}:${path}`], { maxBuffer: 64 << 20 });
      },
      async list(path) {
        const out = execFileSync('git', ['-C', dir, 'ls-tree', '--name-only', `${ref}:${path}`], { encoding: 'utf8' });
        return out.split('\n').filter(Boolean);
      },
    };
  }
  const token = githubToken(env);
  if (!token) return null;
  const headers = { Authorization: `Bearer ${token}`, 'User-Agent': 'azmx-brand' };
  const raw = (path) => `https://raw.githubusercontent.com/${config.repo}/${ref}/${path}`;
  const get = async (url) => {
    const res = await fetch(url, { headers, signal: AbortSignal.timeout(20000) });
    if (!res.ok) throw new Error(`${res.status} reading ${url.replace(/\?.*/, '')}`);
    return res;
  };
  return {
    where: `github.com/${config.repo}`,
    async text(path) {
      return (await get(raw(path))).text();
    },
    async bytes(path) {
      return Buffer.from(await (await get(raw(path))).arrayBuffer());
    },
    async list(path) {
      const res = await get(`https://api.github.com/repos/${config.repo}/contents/${path}?ref=${ref}`);
      return (await res.json()).map((f) => f.name);
    },
  };
}

async function latestTag(config, env = process.env) {
  const token = githubToken(env);
  if (!token) return null;
  try {
    const res = await fetch(`https://api.github.com/repos/${config.repo}/releases/latest`, {
      headers: { Authorization: `Bearer ${token}`, 'User-Agent': 'azmx-brand' },
      signal: AbortSignal.timeout(8000),
    });
    return res.ok ? (await res.json()).tag_name : null;
  } catch {
    return null;
  }
}

const NO_ACCESS = (config) =>
  `No access to the AZM X Design System (${config.repo} is private). Ask the owner to add your GitHub account, ` +
  'then run `gh auth login` once. Until then, use the skill\'s own tokens (azmx-tokens.css) and Azm X 2.004 (assets/fonts/).';

async function main(argv) {
  const config = loadConfig();
  const args = [...argv];
  const command = args.shift() ?? 'status';
  const at = args.indexOf('--ref');
  const ref = at >= 0 ? args.splice(at, 2)[1] : config.ref;
  const read = reader(config, ref);

  if (command === 'status') {
    if (!read) return console.log(NO_ACCESS(config));
    try {
      await read.text('registry.json');
    } catch (e) {
      return console.log(`${NO_ACCESS(config)}\n(${e.message})`);
    }
    const latest = await latestTag(config);
    console.log(`Design system: readable from ${read.where}. Pinned ${config.ref}${latest ? `, latest release ${latest}` : ''}.`);
    console.log(`React and Tailwind: npx ${config.installer} init, then npx ${config.installer} add tokens <names…>; npx ${config.installer} list shows every part.`);
    return;
  }
  if (!read) {
    console.error(NO_ACCESS(config));
    process.exit(2);
  }
  if (command === 'fetch-tokens' || command === 'fetch-fonts') {
    const dir = args[0];
    if (!dir) throw new Error(`name a folder: node scripts/design-system.mjs ${command} <dir>`);
    mkdirSync(dir, { recursive: true });
    if (command === 'fetch-tokens') {
      writeFileSync(join(dir, 'azmx-tokens.css'), await read.text('dist/azmx-tokens.css'));
      console.log(`Wrote ${join(dir, 'azmx-tokens.css')} (design system ${ref}).`);
    } else {
      // The woff2 files and index.ts, which loads them with next/font/local in a Next.js app.
      const files = (await read.list('src/fonts')).filter((f) => f.endsWith('.woff2') || f === 'index.ts');
      for (const f of files) writeFileSync(join(dir, basename(f)), await read.bytes(`src/fonts/${f}`));
      console.log(`Wrote ${files.length} files to ${dir}: ${files.join(', ')}.`);
      console.log('Licensed for AZM X work only: keep them out of public repositories.');
    }
    return;
  }
  if (command === 'drift') {
    const [dsCss, siteText, sourceText] = await Promise.all([
      read.text('dist/azmx-tokens.css'),
      read.text('tokens/site.json'),
      read.text('tokens/source/azmx-tokens.json'),
    ]);
    const skillText = readFileSync(join(ROOT, 'assets', 'tokens', 'azmx-tokens.json'), 'utf8');
    const report = driftReport({
      config: { ...config, ref },
      dsCss,
      skillCss: readFileSync(join(ROOT, 'azmx-tokens.css'), 'utf8'),
      site: JSON.parse(siteText),
      skillTokens: JSON.parse(skillText),
      sourceMatches: JSON.stringify(JSON.parse(sourceText)) === JSON.stringify(JSON.parse(skillText)),
      latest: await latestTag(config),
    });
    console.log(formatReport(report, ref));
    process.exit(report.errors.length ? 1 : 0);
  }
  throw new Error(`unknown command "${command}". Use status, fetch-tokens, fetch-fonts or drift.`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href) {
  main(process.argv.slice(2)).catch((e) => {
    console.error(`design-system: ${e.message}`);
    process.exit(1);
  });
}
