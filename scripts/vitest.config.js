import { defineConfig } from 'vitest/config';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

export default defineConfig({
  resolve: { alias: { 'pdf-lib': require.resolve('pdf-lib') } },
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
      ],
      all: true
      // NOTE: no coverage thresholds here on purpose. The JS tests drive the
      // scripts through execFileSync, which v8 cannot instrument, so measured
      // coverage is ~0% regardless of real test depth. The previous top-level
      // lines/functions/branches/statements keys were silently ignored by Vitest
      // (they must live under coverage.thresholds) and never gated anything.
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
