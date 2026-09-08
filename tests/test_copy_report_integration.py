"""Regression coverage for merging copy checks with report output modes."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'brand-check.py'

@pytest.mark.parametrize('mode', ['legacy-json', 'json', 'html', 'markdown', 'text'])
def test_copy_findings_survive_report_modes(tmp_path, mode):
    source = tmp_path / 'copy with spaces.md'
    source.write_text('Our revolutionary service delivers results. 😀\n', encoding='utf-8')
    args = [sys.executable, str(SCRIPT), str(source), '--copy', '--fix']
    output = tmp_path / f'report with spaces.{mode}'
    if mode == 'legacy-json':
        args += ['--json']
    elif mode == 'text':
        args += ['--report']
    else:
        args += ['--format', mode, '--output', str(output)]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode in (0, 1), result.stderr
    content = result.stdout if mode in ('legacy-json', 'text') else output.read_text()
    if mode in ('legacy-json', 'json'):
        codes = {finding['code'] for finding in json.loads(content)['findings']}
        assert {'EMOJI', 'INTENSIFIER'} <= codes
    else:
        assert 'EMOJI' in content
        assert 'INTENSIFIER' in content
