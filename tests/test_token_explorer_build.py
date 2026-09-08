"""Rebuilding the explorer preserves controls and every source token."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def test_generated_explorer_retains_controls_and_tokens():
    result = subprocess.run(['node', str(ROOT / 'scripts/build-token-explorer.mjs')], capture_output=True, text=True, check=True)
    html = result.stdout
    data = json.loads((ROOT / 'assets/tokens/azmx-tokens.json').read_text())
    expected_count = sum(len(section['tokens']) for section in data.values()
                         if isinstance(section, dict) and 'tokens' in section)
    assert 'id="search-input"' in html
    assert 'class="palette-btn' in html
    assert 'class="theme-btn' in html
    assert 'id="layout"' in html
    assert '{{' not in html
    assert html.count('class="token-card"') == expected_count
    assert 'String(data.rawValue).toLowerCase()' in html
    assert 'refreshTokenValues();' in html
