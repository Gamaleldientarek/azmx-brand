import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("case,expected", [
    ("valid", 0), ("unused_alias", 1), ("primitive_cycle", 1),
    ("bad_mode", 1), ("bad_count", 1), ("rtl_alias", 1), ("long_chain", 0),
])
def test_validator(tmp_path, case, expected):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "assets/tokens").mkdir(parents=True)
    shutil.copy(ROOT / "scripts/tokens-to-css.mjs", tmp_path / "scripts")
    data = json.loads((ROOT / "assets/tokens/azmx-tokens.json").read_text())
    prim = data["1. Primitives"]["tokens"]
    if case == "unused_alias":
        prim["test/broken"] = "@missing/token"
        data["1. Primitives"]["count"] += 1
    elif case == "primitive_cycle":
        prim["test/cycle"] = "@test/cycle"
        data["1. Primitives"]["count"] += 1
    elif case == "bad_mode":
        data["2. Semantic"]["tokens"][next(iter(data["2. Semantic"]["tokens"]))] = None
    elif case == "bad_count":
        data["RTL"]["count"] += 1
    elif case == "rtl_alias":
        data["RTL"]["tokens"]["direction/value"][1] = "@missing/token"
    elif case == "long_chain":
        for i in range(20):
            prim[f"test/{i}"] = f"@test/{i+1}" if i < 19 else 10
        data["1. Primitives"]["count"] += 20
    (tmp_path / "assets/tokens/azmx-tokens.json").write_text(json.dumps(data))
    result = subprocess.run(["node", str(tmp_path / "scripts/tokens-to-css.mjs"), "--validate"],
                            capture_output=True, text=True)
    assert result.returncode == expected, result.stderr
    assert "TypeError" not in result.stderr
    if expected:
        assert "SUMMARY:" in result.stderr
