"""Tests for the versioned Brand API (api/v1) and its build scripts.

1. Staleness guard: regenerates every endpoint into a temporary directory and
   asserts it equals the committed api/v1/*.json (parsed JSON, ignoring the
   build-date `updated` stamp in index.json).
2. Ground-truth values that must never drift from the reference documents.
3. OpenAPI spec validation with openapi-spec-validator.
4. Parser hygiene: no inline markdown leaks into API values.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from openapi_spec_validator import validate as validate_openapi

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "api" / "v1"
EXTRACT_SCRIPT = ROOT / "scripts" / "extract-api-data.py"
OPENAPI_SCRIPT = ROOT / "scripts" / "generate-openapi.py"

ENDPOINTS = [
    "index.json",
    "tokens.json",
    "palettes.json",
    "typography.json",
    "voice.json",
    "audiences.json",
    "prompts.json",
    "images.json",
]

API_VERSION = "1.0.0"
BASE_URL = "https://gamaleldientarek.github.io/azmx-brand/api/v1"


def load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def strip_updated(data: dict) -> dict:
    """Drop the build-date stamp so regenerated output compares equal."""
    if "$meta" in data:
        data = dict(data)
        data["$meta"] = {k: v for k, v in data["$meta"].items() if k != "updated"}
    return data


@pytest.fixture(scope="module")
def regenerated(tmp_path_factory) -> Path:
    """Run extract-api-data.py into a temporary directory and return the API dir."""
    tmp = tmp_path_factory.mktemp("brand-api")
    api_dir = tmp / "api"
    result = subprocess.run(
        [
            sys.executable,
            str(EXTRACT_SCRIPT),
            "--output-dir", str(tmp / "data"),
            "--api-dir", str(api_dir),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, f"extract-api-data.py failed:\n{result.stdout}\n{result.stderr}"
    return api_dir


@pytest.fixture(scope="module")
def committed() -> dict[str, dict]:
    return {name: load(API_DIR / name) for name in ENDPOINTS}


# ---------------------------------------------------------------------------
# 1. Staleness guard
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_committed_endpoint_matches_regenerated(regenerated, committed, endpoint):
    fresh = strip_updated(load(regenerated / endpoint))
    current = strip_updated(committed[endpoint])
    assert fresh == current, (
        f"api/v1/{endpoint} is stale - run `bash scripts/build-api.sh` and commit the result"
    )


def test_openapi_matches_regenerated(regenerated, tmp_path):
    """openapi.json must be regenerated from the current endpoints."""
    result = subprocess.run(
        [sys.executable, str(OPENAPI_SCRIPT), "--api-dir", str(regenerated), "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    fresh = load(tmp_path / "openapi.json")
    current = load(API_DIR / "openapi.json")
    # The index example carries the build date; ignore it.
    for spec in (fresh, current):
        for op in spec["paths"].values():
            example = op["get"]["responses"]["200"]["content"]["application/json"].get("example", {})
            if isinstance(example, dict) and "$meta" in example:
                example["$meta"].pop("updated", None)
    assert fresh == current, "api/v1/openapi.json is stale - run `bash scripts/build-api.sh`"


# ---------------------------------------------------------------------------
# 2. Ground truth
# ---------------------------------------------------------------------------

def test_index_meta(committed):
    meta = committed["index.json"]["$meta"]
    assert meta["version"] == API_VERSION
    assert meta["base_url"] == BASE_URL
    assert meta["repository"] == "https://github.com/Gamaleldientarek/azmx-brand"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta["updated"])
    paths = [e["path"] for e in committed["index.json"]["endpoints"]]
    assert paths == [f"/{name}" for name in ENDPOINTS if name != "index.json"]
    for endpoint in committed["index.json"]["endpoints"]:
        assert endpoint["example_url"] == f"{BASE_URL}{endpoint['path']}"


@pytest.mark.parametrize("endpoint", [e for e in ENDPOINTS if e != "index.json"])
def test_endpoint_envelope(committed, endpoint):
    data = committed[endpoint]
    assert data["version"] == API_VERSION
    assert isinstance(data["description"], str) and data["description"]


def test_blue_palette_values(committed):
    palettes = committed["palettes.json"]
    assert palettes["count"] == 6
    assert [p["name"] for p in palettes["palettes"]] == ["Blue", "Orange", "Green", "Yellow", "Purple", "Red"]

    blue = palettes["palettes"][0]
    ramp = {r["step"]: r["hex"] for r in blue["ramp"]}
    assert len(ramp) == 12
    assert ramp["Blue 600"] == "#001AFF"
    assert ramp["Blue 200"] == "#BFD5FF"
    assert ramp["Blue 1000"] == "#040038"

    # Only Blue carries a ramp; secondary palettes expose key colors
    for secondary in palettes["palettes"][1:]:
        assert "ramp" not in secondary
        assert re.fullmatch(r"#[0-9A-F]{6}", secondary["signature"])
        assert re.fullmatch(r"#[0-9A-F]{6}", secondary["text_safe_hex"])
    orange = palettes["palettes"][1]
    assert orange["signature"] == "#F47A48"


def test_tokens(committed):
    tokens = committed["tokens.json"]
    assert tokens["count"] == 587
    assert tokens["source_version"] == "2.0.0"
    assert "fileKey" not in json.dumps(tokens)
    assert sum(c["count"] for c in tokens["collections"]) == 587
    assert all(len(c["tokens"]) == c["count"] for c in tokens["collections"])
    by_name = {c["name"]: c for c in tokens["collections"]}
    assert by_name["1. Primitives"]["tokens"]["color/blue/200"] == "#BFD5FF"
    assert by_name["1. Primitives"]["tokens"]["color/blue/600"] == "#001AFF"
    assert by_name["3. Component"]["count"] == 56
    assert by_name["2. Semantic"]["modes"] == ["Light", "Dark"]
    assert by_name["1b. Palette"]["modes"] == ["Blue", "Orange", "Green", "Yellow", "Purple", "Red"]


def test_typography(committed):
    typography = committed["typography.json"]
    assert len(typography["families"]) == 2
    assert len(typography["weights"]) == 7
    assert all(isinstance(row["tracking"], (int, float)) for row in typography["type_scale"])
    hero = typography["type_scale"][0]
    assert hero["role"] == "Cover hero display"
    assert hero["tracking"] == -2


def test_prompts(committed):
    prompts = committed["prompts.json"]
    assert prompts["count"] == 15
    assert len(prompts["prompts"]) == 15
    assert [p["number"] for p in prompts["prompts"]] == list(range(1, 16))
    assert all(p["template"] for p in prompts["prompts"])


def test_personas(committed):
    audiences = committed["audiences.json"]
    assert audiences["count"] == 8
    assert [p["name"] for p in audiences["personas"]] == [
        "Directors / Heads", "Leads", "C-Suite", "Product / UX Heads",
        "Operations", "Researchers", "Designers", "Industry Professionals",
    ]
    assert {p["motion"] for p in audiences["personas"]} == {"B2G", "B2B", "B2C"}
    for persona in audiences["personas"]:
        assert persona["core_message"]
        assert persona["pain_points"]


def test_voice(committed):
    voice = committed["voice.json"]
    assert [d["dimension"] for d in voice["dimensions"]] == ["Formality", "Technicality", "Attitude", "Purpose"]
    assert len(voice["writing_mechanics"]) >= 5
    assert voice["format_rules"][0]["format"] == "Headlines and heroes"


def test_images(committed):
    images = committed["images.json"]
    assert images["count"] == 240 == len(images["images"])
    assert all(len(img["tags"]) == 3 for img in images["images"])


# ---------------------------------------------------------------------------
# 3. OpenAPI
# ---------------------------------------------------------------------------

def test_openapi_spec_is_valid():
    spec = load(API_DIR / "openapi.json")
    validate_openapi(spec)
    assert spec["servers"][0]["url"] == BASE_URL
    assert spec["info"]["version"] == API_VERSION
    assert set(spec["paths"]) == {f"/{name}" for name in ENDPOINTS if name != "index.json"}
    dumped = json.dumps(spec["components"])
    assert '"type": "null"' not in dumped
    assert '"required": null' not in dumped


def test_openapi_yaml_matches_json():
    yaml = pytest.importorskip("yaml")
    with open(API_DIR / "openapi.yaml", encoding="utf-8") as f:
        assert yaml.safe_load(f) == load(API_DIR / "openapi.json")


# ---------------------------------------------------------------------------
# 4. Parser hygiene and docs wiring
# ---------------------------------------------------------------------------

def _walk_strings(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_strings(v)
    elif isinstance(value, str):
        yield value


@pytest.mark.parametrize("endpoint", ["voice.json", "audiences.json", "palettes.json", "typography.json"])
def test_no_markdown_leaks(committed, endpoint):
    leaks = [s for s in _walk_strings(committed[endpoint]) if "**" in s or "`" in s]
    assert not leaks, f"inline markdown leaked into {endpoint}: {leaks[:3]}"


def test_no_stale_urls_in_api_and_docs():
    files = list(API_DIR.glob("*.json")) + [
        API_DIR / "README.md",
        ROOT / "api-docs" / "index.html",
        ROOT / "api-docs" / "examples.html",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "azmx-sa" not in text, f"stale repo owner in {path.name}"
        assert "raw.githubusercontent.com" not in text, f"stale raw URL in {path.name}"


def test_docs_page_wiring():
    html = (ROOT / "api-docs" / "index.html").read_text(encoding="utf-8")
    assert "../api/v1/openapi.json" in html
    assert "redoc@2." in html and "redoc/latest" not in html
    assert not (ROOT / "api-docs" / "openapi.json").exists(), "api-docs/openapi.json is a stale copy"
    examples = (ROOT / "api-docs" / "examples.html").read_text(encoding="utf-8")
    script = examples.split("<script>", 1)[1]
    assert re.search(r"\.innerHTML\s*=", script) is None, "examples.html must not assign innerHTML"
