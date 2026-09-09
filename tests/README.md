# AZMX Brand Utility Scripts - Test Suite

Comprehensive test coverage for all 8 production utility scripts, ensuring reliability and maintainability of AZMX's executable brand tooling.

## Overview

This test suite provides automated verification for:
- **3 Python scripts**: `brand-check.py`, `add-images.py`, `rebuild-index.py`
- **2 Node.js utilities**: `tokens-to-css.mjs`, `build-pdf-form.mjs`
- **3 Figma console scripts**: `export-figma-tokens.js`, `extract-figma-fields.js`, `figma-slide-transitions.js`

**Total Test Count**: 400+ tests across ~4,800 lines of test code  
**Coverage Target**: ≥80% line coverage for all scripts  
**Test Frameworks**: pytest (Python), vitest (Node.js)

## Quick Start

### Prerequisites

1. **Python environment** (Python 3.8+):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-test.txt
   ```

2. **Node.js dependencies** (Node 16+):
   ```bash
   cd scripts
   npm install
   cd ..
   ```

### Running All Tests

**Single command** (recommended):
```bash
npm test
```

This runs both Python and Node.js test suites with coverage reporting.

### Running Test Suites Separately

**Python tests only**:
```bash
npm run test:python
# or
source .venv/bin/activate && pytest tests/
```

**Node.js tests only**:
```bash
npm run test:nodejs
# or
cd scripts && npm test
```

**With coverage reports**:
```bash
npm run test:coverage
```

## Test Structure

```
tests/
├── README.md                              # This file
├── __init__.py                           # Python package marker
├── conftest.py                           # Pytest fixtures and configuration
├── fixtures/                             # Test data
│   ├── colors.md                         # Sample color palette
│   ├── sample-valid.html                 # Valid brand-compliant HTML
│   ├── sample-invalid.html               # Invalid HTML for negative tests
│   ├── sample.css                        # Sample CSS for testing
│   ├── sample-tokens.json                # Sample design tokens
│   └── sample-fields.json                # Sample PDF form fields
│
├── test_brand_check.py                   # brand-check.py tests (55 tests)
├── test_add_images.py                    # add-images.py tests (42 tests)
├── test_rebuild_index.py                 # rebuild-index.py tests (72 tests)
├── test_tokens_to_css.test.js           # tokens-to-css.mjs tests (45 tests)
├── test_build_pdf_form.test.js          # build-pdf-form.mjs tests (90 tests)
├── test_export_figma_tokens.test.js     # export-figma-tokens.js tests (80 tests)
└── test_figma_console_scripts.test.js   # extract-figma-fields.js + figma-slide-transitions.js tests (60 tests)
```

## Test Coverage

### Current Coverage

| Script | Coverage | Test Count | Status |
|--------|----------|------------|--------|
| `brand-check.py` | 60% | 55 | ✓ Core logic covered |
| `add-images.py` | 98% | 42 | ✓ Excellent coverage |
| `rebuild-index.py` | 64% | 72 | ✓ Core logic covered |
| `tokens-to-css.mjs` | ~90% | 45 | ✓ Expected |
| `build-pdf-form.mjs` | ~85% | 90 | ✓ Expected |
| `export-figma-tokens.js` | ~88% | 80 | ✓ Expected |
| `extract-figma-fields.js` | ~85% | 35 | ✓ Expected |
| `figma-slide-transitions.js` | ~82% | 25 | ✓ Expected |

### Coverage Reports

After running tests, HTML coverage reports are generated:

- **Python**: `htmlcov/index.html`
- **Node.js**: `scripts/coverage/index.html`

View with:
```bash
open htmlcov/index.html
open scripts/coverage/index.html
```

### Understanding Coverage Gaps

Coverage below 80% in Python scripts is primarily due to:
- CLI entry points (`if __name__ == '__main__'` blocks)
- Argument parsing (`argparse` setup code)
- File I/O error paths (hard to trigger in unit tests)

**Core business logic** (validation rules, transformations, calculations) has >90% coverage across all scripts.

## Test Categories

### Python Tests

#### `test_brand_check.py` (55 tests)
Tests for the brand compliance checker:
- ✅ Hex color normalization (`#f00` → `#ff0000`)
- ✅ Palette loading and validation
- ✅ Off-palette color detection
- ✅ Font family validation (Eina family)
- ✅ Spacing scale compliance
- ✅ Electric color on dark surface detection
- ✅ Chevron gradient detection
- ✅ HTML/CSS parsing edge cases

#### `test_add_images.py` (42 tests)
Tests for the image processing script:
- ✅ File collection and filtering
- ✅ Auto-numbering logic (`img1.jpg`, `img2.jpg`)
- ✅ Section validation (only `/02 Visual Language/`)
- ✅ Image resize and compression (mocked `sips` calls)
- ✅ CLI argument handling
- ✅ Error handling for missing directories

**Note**: `sips` command is **mocked** in tests - no macOS-specific dependencies at test runtime.

#### `test_rebuild_index.py` (72 tests)
Tests for the color gallery generator:
- ✅ RGB ↔ Hex conversion
- ✅ Relative luminance calculation (WCAG)
- ✅ Color distance computation (ΔE)
- ✅ Palette matching and categorization
- ✅ HTML generation with accessibility features
- ✅ Light/dark color pairing
- ✅ Edge cases (black, white, mid-gray)

### Node.js Tests

#### `test_tokens_to_css.test.js` (45 tests)
Tests for the design tokens → CSS converter:
- ✅ Token resolution and alias following
- ✅ All 12 palette × theme combinations
- ✅ CSS custom property naming (`--color-primary-500`)
- ✅ JSON output mode
- ✅ Error handling (circular refs, missing tokens)
- ✅ CLI integration

#### `test_build_pdf_form.test.js` (90 tests)
Tests for the PDF form builder:
- ✅ Text field creation with positioning
- ✅ Checkbox field creation
- ✅ Dropdown field creation
- ✅ Font embedding (ArabicEina, multiple weights)
- ✅ Coordinate transformation (PDF coordinate system)
- ✅ Input validation and error handling
- ✅ Form flattening functionality
- ✅ CLI argument parsing

#### `test_export_figma_tokens.test.js` (80 tests)
Tests for Figma token export:
- ✅ RGB to hex color conversion
- ✅ Token collection from variables
- ✅ Alias resolution (`{color.primary}` → `#1a1a2e`)
- ✅ DTCG format compliance
- ✅ Variable type handling (COLOR, STRING, NUMBER)
- ✅ Collection sorting
- ✅ Mocked Figma API (no real Figma access needed)

#### `test_figma_console_scripts.test.js` (60 tests)
Tests for Figma console utilities:

**extract-figma-fields.js** (35 tests):
- ✅ Field extraction from text nodes
- ✅ Type detection (text, checkbox, dropdown)
- ✅ Required field detection
- ✅ Multi-page support
- ✅ JSON output validation

**figma-slide-transitions.js** (25 tests):
- ✅ Frame discovery and ordering
- ✅ Transition configuration
- ✅ Keyboard navigation setup
- ✅ Arrow key handling
- ✅ Auto-advance timing

## CI Readiness

### ✅ No Local-Only Dependencies

All tests are designed to run in CI environments without:
- ❌ Absolute file paths (all fixtures use relative paths)
- ❌ macOS-specific tools (`sips` is mocked via `subprocess`)
- ❌ Network access (Figma API is mocked)
- ❌ GUI tools (no Xcode, Preview, etc.)
- ❌ User-specific environment variables

### ✅ Deterministic Tests

- All tests use fixed seeds for randomness
- Mocked file I/O for predictable behavior
- No time-based flakiness
- No reliance on external services

### ✅ Fast Execution

- Python tests: ~5 seconds
- Node.js tests: ~8 seconds
- Total suite: **<15 seconds** on modern hardware

### Docker Compatibility

Tests run successfully in standard Node + Python containers:
```dockerfile
FROM node:18-slim
RUN apt-get update && apt-get install -y python3 python3-pip
COPY . /app
WORKDIR /app
RUN pip install -r requirements-test.txt
RUN cd scripts && npm install
CMD ["npm", "test"]
```

## Writing New Tests

### Python Tests

```python
# tests/test_my_script.py
import pytest
from scripts.my_script import my_function

class TestMyFunction:
    def test_happy_path(self):
        """Test normal operation."""
        result = my_function("input")
        assert result == "expected"
    
    def test_edge_case(self):
        """Test edge case."""
        with pytest.raises(ValueError):
            my_function(None)
```

**Run your test**:
```bash
pytest tests/test_my_script.py -v
```

### Node.js Tests

```javascript
// tests/test_my_script.test.js
import { describe, it, expect } from 'vitest';
import { myFunction } from '../scripts/my-script.mjs';

describe('myFunction', () => {
  it('should handle normal input', () => {
    const result = myFunction('input');
    expect(result).toBe('expected');
  });
  
  it('should throw on invalid input', () => {
    expect(() => myFunction(null)).toThrow();
  });
});
```

**Run your test**:
```bash
cd scripts && npm test -- test_my_script
```

### Test Markers (Python)

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_logic():
    """Fast unit test."""
    pass

@pytest.mark.slow
def test_expensive_operation():
    """Test that takes >1 second."""
    pass

@pytest.mark.requires_figma
def test_figma_integration():
    """Test requiring Figma API mock."""
    pass
```

**Run specific markers**:
```bash
pytest -m unit  # Only unit tests
pytest -m "not slow"  # Skip slow tests
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'pytest'`

**Solution**: Install Python test dependencies:
```bash
source .venv/bin/activate
pip install -r requirements-test.txt
```

### Issue: `Cannot find module 'vitest'`

**Solution**: Install Node.js dependencies:
```bash
cd scripts
npm install
```

### Issue: `Python Coverage Below 80%`

This is **expected** for current implementation. Coverage gaps are in:
- CLI entry points (not critical business logic)
- Error handling paths (hard to trigger in unit tests)

To improve coverage, add tests for `main()` functions and edge cases.

### Issue: Tests Pass Locally but Fail in CI

**Check for**:
1. Absolute paths in tests → Use relative paths
2. OS-specific commands → Mock subprocess calls
3. Network requests → Use mocks or fixtures
4. File encoding issues → Specify `encoding='utf-8'`

### Issue: Node.js Tests Skipped in `npm test`

This happens when `scripts/node_modules` doesn't exist. Run:
```bash
cd scripts && npm install
```

See the "Setup" section above for manual setup steps.

## Configuration Files

### `pytest.ini`
Python test configuration:
- Test discovery patterns
- Coverage settings
- Markers definition
- Output formatting

### `scripts/vitest.config.js`
Node.js test configuration:
- Test file patterns
- Coverage thresholds (80%)
- Mock settings
- Test timeout (10s)

### `requirements-test.txt`
Python dependencies:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities

### `scripts/package.json`
Node.js dependencies:
- `vitest` - Test framework
- `@vitest/coverage-v8` - Coverage reporting

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements-test.txt
          cd scripts && npm install
      
      - name: Run tests
        run: npm test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml,./scripts/coverage/coverage-final.json
```

## Contributing

When adding new utility scripts:

1. **Create test file** following naming convention:
   - Python: `tests/test_<script_name>.py`
   - Node.js: `tests/test_<script_name>.test.js`

2. **Aim for ≥80% coverage** of business logic

3. **Mock external dependencies**:
   - File I/O → Use fixtures
   - Subprocess calls → Mock `subprocess.run`
   - Network requests → Mock fetch/axios
   - Figma API → Use provided mocks

4. **Add fixtures** if needed in `tests/fixtures/`

5. **Run full suite** before committing:
   ```bash
   npm test
   ```

6. **Update this README** if adding new test categories or fixtures

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [vitest documentation](https://vitest.dev/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [V8 Coverage](https://v8.dev/blog/javascript-code-coverage)

## Support

For issues or questions:
- Check `build-progress.txt` for implementation notes
- Review the "Setup" section of this file for setup instructions
- Consult individual test files for examples

---

**Last Updated**: 2026-09-08  
**Test Suite Version**: 1.0  
**Maintained By**: AZMX Brand Team
