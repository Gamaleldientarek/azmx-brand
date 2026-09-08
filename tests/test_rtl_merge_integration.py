"""RTL checks remain active alongside the merged JSON report interface."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('kind', ['valid', 'invalid'])
def test_rtl_fixture_reports(tmp_path, kind):
    result = subprocess.run([
        sys.executable, str(ROOT / 'scripts/brand-check.py'),
        str(ROOT / f'scripts/test-rtl-{kind}.html'), '--format', 'json'
    ], capture_output=True, text=True)
    assert result.returncode in (0, 1), result.stderr
    findings = [f for f in json.loads(result.stdout)['findings'] if f['code'] == 'RTL']
    if kind == 'valid':
        assert not findings
    else:
        assert any('missing dir=' in f['what'] for f in findings)
        assert any('chevron' in f['what'] for f in findings)
        assert any('letter-spacing' in f['what'] for f in findings)
