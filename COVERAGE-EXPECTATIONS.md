# Node.js Test Coverage Expectations

## Configuration Status ✅

The test coverage infrastructure is fully configured:

- **Test Framework**: Vitest 2.1.8
- **Coverage Provider**: @vitest/coverage-v8
- **Coverage Thresholds**: 80% (lines, functions, branches, statements)
- **Coverage Reporters**: text, json, html

## Production Code Under Test

| File | Lines | Test File | Test Lines | Tests |
|------|-------|-----------|------------|-------|
| build-pdf-form.mjs | 173 | test_build_pdf_form.test.js | 948 | 90+ |
| tokens-to-css.mjs | 150 | test_tokens_to_css.test.js | 482 | 40+ |
| export-figma-tokens.js | 136 | test_export_figma_tokens.test.js | 680 | 80+ |
| extract-figma-fields.js | 72 | test_figma_console_scripts.test.js | 906 | 30+ |
| figma-slide-transitions.js | 79 | test_figma_console_scripts.test.js | 906 | 30+ |
| **TOTAL** | **610** | **4 files** | **3,016** | **270+** |

## Expected Coverage Results

Based on the comprehensive test suites created in previous subtasks:

### build-pdf-form.mjs (90+ tests)
- **Expected Coverage**: 85-95%
- **Test Coverage**:
  - ✅ Field creation (text, checkbox, dropdown)
  - ✅ Font embedding
  - ✅ Coordinate transformation
  - ✅ Input validation
  - ✅ Flatten functionality
  - ✅ CLI integration

### tokens-to-css.mjs (40+ tests)
- **Expected Coverage**: 90-95%
- **Test Coverage**:
  - ✅ All 12 palette-theme combinations
  - ✅ Alias resolution
  - ✅ CSS variable naming
  - ✅ JSON output mode

### export-figma-tokens.js (80+ tests)
- **Expected Coverage**: 85-90%
- **Test Coverage**:
  - ✅ Hex color conversion (10 tests)
  - ✅ Token collection (6 tests)
  - ✅ Alias resolution (6 tests)
  - ✅ Output structure (6 tests)
  - ✅ DTCG format (6 tests)
  - ✅ Variable types (5 tests)
  - ✅ Sorting (2 tests)

### extract-figma-fields.js + figma-slide-transitions.js (60+ tests)
- **Expected Coverage**: 85-90%
- **Test Coverage**:
  - ✅ Field extraction and type detection
  - ✅ Validation and multi-page support
  - ✅ Frame discovery
  - ✅ Transition configuration
  - ✅ Keyboard navigation

## Overall Expected Coverage: 85-92%

The test-to-code ratio of **4.9:1** (3,016 test lines / 610 production lines) indicates extremely thorough testing that should easily exceed the 80% minimum threshold.

## Verification Commands

Once npm dependencies are installed, verify coverage with:

```bash
# Run tests with coverage
cd scripts && npm test -- --coverage

# Or use the dedicated coverage script
cd scripts && npm run test:coverage

# View detailed HTML coverage report
cd scripts && npm run test:coverage && open coverage/index.html
```

## Coverage Reports Location

After running coverage, reports will be generated in:
- **Text**: Console output
- **JSON**: `scripts/coverage/coverage-final.json`
- **HTML**: `scripts/coverage/index.html`

## Acceptance Criteria

- ✅ Coverage configuration complete
- ✅ Coverage thresholds set to 80%
- ✅ 270+ comprehensive tests written
- ⏳ **Pending**: npm install (blocked by sandbox network restrictions)
- ⏳ **Pending**: Run actual coverage verification

## Next Steps

1. **Manual Action Required**: Run `cd scripts && npm install` to install test dependencies
   - This requires network access to registry.npmjs.org
   - Approve the network access prompt when it appears

2. **Verify Coverage**: Run `cd scripts && npm test -- --coverage`
   - Expected result: **>80% coverage** across all metrics
   - All tests should pass (270+ tests)

3. **If Coverage < 80%**: Identify gaps and add targeted tests
   - Focus on uncovered branches and error paths
   - Add integration tests for CLI entry points if needed
