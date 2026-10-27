/**
 * scripts/check-update.mjs: the skill tells people when a newer release is out.
 */

import { describe, it, expect } from 'vitest';
import { compareVersions, updateMessage, latestRelease, localVersion, UPDATE_COMMAND } from '../scripts/check-update.mjs';

describe('compareVersions', () => {
  it('orders versions numerically, with or without a leading v', () => {
    expect(compareVersions('2.2.0', '3.0.0')).toBe(-1);
    expect(compareVersions('v3.0.0', '3.0.0')).toBe(0);
    expect(compareVersions('3.10.0', '3.9.9')).toBe(1);
    expect(compareVersions('3.0', '3.0.0')).toBe(0);
  });

  it('sorts a pre-release before its release', () => {
    expect(compareVersions('3.0.0-beta.1', '3.0.0')).toBe(-1);
    expect(compareVersions('3.0.0', '3.0.0-beta.1')).toBe(1);
  });
});

describe('updateMessage', () => {
  it('says the copy is current when it matches or is ahead of the release', () => {
    expect(updateMessage('3.0.0', 'v3.0.0')).toMatch(/is the latest release/);
    expect(updateMessage('3.1.0', 'v3.0.0')).toMatch(/is the latest release/);
  });

  it('gives the update command when a newer release is out', () => {
    const line = updateMessage('2.2.0', 'v3.0.0');
    expect(line).toContain('out of date');
    expect(line).toContain('3.0.0 is out');
    expect(line).toContain(UPDATE_COMMAND);
  });

  it("says it couldn't check when the latest release is unknown", () => {
    expect(updateMessage('3.0.0', null)).toMatch(/couldn't check/);
  });
});

describe('latestRelease', () => {
  it('reads the tag of the latest GitHub release', async () => {
    const fake = async (url) => {
      expect(url).toBe('https://api.github.com/repos/Gamaleldientarek/azmx-brand/releases/latest');
      return { ok: true, json: async () => ({ tag_name: 'v3.0.0' }) };
    };
    expect(await latestRelease(fake)).toBe('v3.0.0');
  });

  it('returns null on an error status or a network failure, never throwing', async () => {
    expect(await latestRelease(async () => ({ ok: false, json: async () => ({}) }))).toBeNull();
    expect(await latestRelease(async () => { throw new Error('offline'); })).toBeNull();
  });
});

describe('localVersion', () => {
  it('reads the version the skill ships in its plugin manifest', () => {
    expect(localVersion()).toMatch(/^\d+\.\d+\.\d+/);
  });
});
