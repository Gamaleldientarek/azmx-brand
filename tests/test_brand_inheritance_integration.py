"""Ensure brand selection coexists with copy validation and JSON reports."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('brand', ['colab', 'majarah', 'clix', 'anatomi'])
def test_brand_copy_report(tmp_path, brand):
    config = json.loads((ROOT / 'config/sub-brands' / f'{brand}.json').read_text())
    schema = json.loads((ROOT / 'schemas/sub-brand-config.schema.json').read_text())
    validate(config, schema)
    source = tmp_path / 'brand copy.md'
    source.write_text('A revolutionary service. 😀\n', encoding='utf-8')
    result = subprocess.run([
        sys.executable, str(ROOT / 'scripts/brand-check.py'), '--brand', brand,
        str(source), '--copy', '--format', 'json'
    ], capture_output=True, text=True)
    assert result.returncode in (0, 1), result.stderr
    data = json.loads(result.stdout)
    assert {'EMOJI', 'INTENSIFIER'} <= {item['code'] for item in data['findings']}


def test_template_config_is_not_a_brand(tmp_path):
    """_example-new-brand.json is a template: --brand must refuse it, not lint against it."""
    source = tmp_path / 'copy.md'
    source.write_text('Plain copy.\n', encoding='utf-8')
    result = subprocess.run([
        sys.executable, str(ROOT / 'scripts/brand-check.py'), '--brand', '_example-new-brand',
        str(source), '--format', 'json'
    ], capture_output=True, text=True)
    assert result.returncode == 2
    assert 'unknown --brand _example-new-brand' in result.stderr
    assert '_example' not in result.stderr.split('available:')[1]


def test_majarah_display_font_passes_font_check(tmp_path):
    """majarah.json declares Oswald as display_font, so --brand majarah must not flag it."""
    source = tmp_path / 'hero.css'
    source.write_text('h1 { font-family: Oswald, serif; }\n', encoding='utf-8')
    result = subprocess.run([
        sys.executable, str(ROOT / 'scripts/brand-check.py'), '--brand', 'majarah',
        str(source), '--format', 'json'
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not [f for f in json.loads(result.stdout)['findings'] if f['code'] == 'FONT']
