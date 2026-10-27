#!/usr/bin/env node
// Tells the person whether this copy of the skill is the latest release.
// Usage: node scripts/check-update.mjs   (prints one line; never fails the caller)
//
// The skill is installed from GitHub and does not update itself, so SKILL.md runs this once at
// the start of AZM X work. Offline, rate-limited or blocked: it says it couldn't check and exits 0.
// AZMX_BRAND_SKIP_UPDATE_CHECK=1 turns it off.

import { readFileSync, realpathSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const REPO = 'Gamaleldientarek/azmx-brand';
export const UPDATE_COMMAND = 'npx skills@latest update -g';

const HERE = dirname(fileURLToPath(import.meta.url));

/** The installed version, from the plugin manifest that ships with the skill. */
export function localVersion(root = join(HERE, '..')) {
  return JSON.parse(readFileSync(join(root, '.claude-plugin', 'plugin.json'), 'utf8')).version;
}

/** -1, 0 or 1, comparing "v3.0.0" / "3.0.0" style versions numerically; a pre-release sorts first. */
export function compareVersions(a, b) {
  const parse = (v) => {
    const [core, pre] = String(v).trim().replace(/^v/i, '').split('-', 2);
    return { nums: core.split('.').map((n) => parseInt(n, 10) || 0), pre: pre ?? null };
  };
  const x = parse(a);
  const y = parse(b);
  for (let i = 0; i < Math.max(x.nums.length, y.nums.length); i++) {
    const d = (x.nums[i] ?? 0) - (y.nums[i] ?? 0);
    if (d) return Math.sign(d);
  }
  if (x.pre === y.pre) return 0;
  if (x.pre === null) return 1;
  if (y.pre === null) return -1;
  return x.pre < y.pre ? -1 : 1;
}

/** The line to show for an installed version and the latest release tag (or null when unknown). */
export function updateMessage(installed, latest) {
  if (!latest) return `azmx-brand ${installed}: couldn't check for a newer release (offline or GitHub unreachable).`;
  if (compareVersions(installed, latest) >= 0) return `azmx-brand ${installed} is the latest release.`;
  return `azmx-brand ${installed} is out of date: ${latest.replace(/^v/i, '')} is out. Run \`${UPDATE_COMMAND}\`, then restart Claude Code.`;
}

/** The latest release tag on GitHub, or null. The repository is public, so no sign-in is needed. */
export async function latestRelease(fetchImpl = globalThis.fetch, timeoutMs = 4000) {
  try {
    const res = await fetchImpl(`https://api.github.com/repos/${REPO}/releases/latest`, {
      headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'azmx-brand-update-check' },
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!res.ok) return null;
    const { tag_name: tag } = await res.json();
    return typeof tag === 'string' ? tag : null;
  } catch {
    return null;
  }
}

async function main() {
  if (process.env.AZMX_BRAND_SKIP_UPDATE_CHECK) return;
  let installed;
  try {
    installed = localVersion();
  } catch {
    console.log("azmx-brand: couldn't read the installed version.");
    return;
  }
  console.log(updateMessage(installed, await latestRelease()));
}

if (process.argv[1] && import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href) await main();
