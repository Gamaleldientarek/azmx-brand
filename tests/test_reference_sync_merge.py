"""Both synchronization directions preserve current reference content."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def test_reference_round_trip(tmp_path):
    names = ['scripts/sync-references.py', 'scripts/image-tags.json', 'scripts/recolor-prompts.json',
             'references/image-index.md', 'references/recolor-prompts.md']
    for name in names:
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    before = {name: json.loads((tmp_path / name).read_text()) for name in names if name.endswith('.json')}
    for args in [['--check'], ['--sync'], ['--check'], ['--sync', '--from-markdown'], ['--check']]:
        result = subprocess.run([sys.executable, str(tmp_path / 'scripts/sync-references.py'), *args],
                                cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    after = {name: json.loads((tmp_path / name).read_text()) for name in before}
    assert before == after
