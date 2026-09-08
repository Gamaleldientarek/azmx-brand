"""Detailed reports retain copy validation and history persistence."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('fmt', ['json', 'html', 'markdown'])
def test_detailed_report_with_copy_and_history(tmp_path, fmt):
    source = tmp_path / 'sample.md'
    source.write_text('A revolutionary service.')
    output = tmp_path / ('report.' + fmt)
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/brand-check.py'), str(source),
        '--copy', '--report', '--format', fmt, '--output', str(output), '--save-history'],
        cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode in (0, 1), result.stderr
    assert 'INTENSIFIER' in output.read_text()
    history = list((tmp_path / '.brand-reports').glob('*.json'))
    assert history
    if fmt == 'json':
        data = json.loads(output.read_text())
        assert data['total_findings'] > 0
