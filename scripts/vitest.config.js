// Vitest 5 — requires Node 22.12+ (see package.json engines).
import { defineConfig } from 'vitest/config';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

export default defineConfig({
  resolve: { alias: { '@cantoo/pdf-lib': require.resolve('@cantoo/pdf-lib') } },
  test: {
    // Test file patterns
    include: ['../tests/**/*.test.js'],

    // Environment
    environment: 'node',

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['*.mjs', '*.js'],
      exclude: [
        'vitest.config.js',
        'node_modules/**',
        '../tests/**'
      ]
      // Vitest >= 3 always reports every file matched by coverage.include, so
      // the old `all: true` flag is gone (it was removed from the config schema).
      //
      // NOTE: no coverage thresholds here on purpose. Most JS tests drive the
      // scripts through execFileSync or node:vm, which v8 cannot instrument, so
      // measured coverage understates real test depth. Only the functions
      // imported directly (tokens-to-css.mjs resolve/resolveAll) register.
    },

    // Global test settings
    globals: false,
    testTimeout: 10000,

    // Mock configuration
    mockReset: true,
    restoreMocks: true,
    clearMocks: true
  }
});
