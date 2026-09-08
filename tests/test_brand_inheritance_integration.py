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
