"""The merged linter reports explicit low-contrast text through JSON output."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/brand-check.py'

@pytest.mark.parametrize('foreground, expected', [('#999999', True), ('#111927', False)])
def test_contrast_json_report(tmp_path, foreground, expected):
    source = tmp_path / 'contrast sample.html'
    source.write_text(f'<p style="color:{foreground};background-color:#FFFFFF">Sample</p>')
    result = subprocess.run([sys.executable, str(SCRIPT), str(source), '--format', 'json'], capture_output=True, text=True)
    assert result.returncode in (0, 1), result.stderr
    findings = json.loads(result.stdout)['findings']
    assert any(f['code'] == 'CONTRAST' for f in findings) == expected
