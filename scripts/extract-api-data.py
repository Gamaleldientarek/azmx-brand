#!/usr/bin/env python3
"""Extract API data from AZMX brand reference files.

Usage:
    python scripts/extract-api-data.py [--dry-run] [--output-dir DIR] [--api-dir DIR]

Orchestrates all parsers to extract structured data from markdown reference
files and existing JSON sources, then generates the versioned API endpoint
files (api/v1/*.json) including index.json, whose counts and descriptions are
computed from the generated data.

Options:
    --dry-run       Show what will be processed without running parsers
    --output-dir    Directory for intermediate JSON files (default: data/, gitignored)
    --api-dir       Directory for API endpoint files (default: api/v1/)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Single source of truth for API metadata. generate-openapi.py and
# generate-docs.py read these values back from api/v1/index.json ($meta).
# ---------------------------------------------------------------------------
API_VERSION = "1.0.0"
API_NAME = "AZMX Brand API"
API_DESCRIPTION = (
    "Versioned, programmatic API providing structured access to AZMX brand rules, "
    "design tokens, voice guidelines, and audience personas"
)
REPO_URL = "https://github.com/Gamaleldientarek/azmx-brand"
PAGES_URL = "https://gamaleldientarek.github.io/azmx-brand/"
BASE_URL = f"{PAGES_URL}api/v1"
DOCS_URL = f"{PAGES_URL}api-docs/"
CONTACT = {"organization": "AZMX", "email": "brand@azmx.sa"}
LICENSE = "Proprietary"


# Data source definitions (markdown parsed via scripts/parsers, JSON copied)
DATA_SOURCES = [
    {
        "name": "colors",
        "type": "markdown",
        "source": "references/colors.md",
        "parser": "scripts.parsers.colors_parser",
        "output": "colors.json",
    },
    {
        "name": "voice",
        "type": "markdown",
        "source": "references/voice-and-tone.md",
        "parser": "scripts.parsers.voice_parser",
        "output": "voice.json",
    },
    {
        "name": "audiences",
        "type": "markdown",
        "source": "references/audiences-and-messaging.md",
        "parser": "scripts.parsers.audiences_parser",
        "output": "audiences.json",
    },
    {
        "name": "prompts",
        "type": "markdown",
        "source": "references/content-prompts.md",
        "parser": "scripts.parsers.prompts_parser",
        "output": "prompts.json",
    },
    {
        "name": "typography",
        "type": "markdown",
        "source": "references/design-system.md",
        "parser": "scripts.parsers.typography_parser",
        "output": "typography.json",
    },
    {
        "name": "images",
        "type": "json",
        "source": "scripts/image-tags.json",
        "output": "images.json",
    },
]

TOKENS_SOURCE = "assets/tokens/azmx-tokens.json"


def show_dry_run() -> None:
    """Display all data sources that will be processed."""
    print("AZMX API Data Extraction - Dry Run")
    print("=" * 60)
    print(f"\nRoot directory: {ROOT}")
    print(f"\nData sources to process: {len(DATA_SOURCES) + 1}\n")

    for idx, source in enumerate(DATA_SOURCES, 1):
        source_path = os.path.join(ROOT, source["source"])
        exists = "✓" if os.path.exists(source_path) else "✗"
        print(f"{idx}. {source['name']} [{exists}]")
        print(f"   Type: {source['type']}")
        print(f"   Source: {source['source']}")
        if source["type"] == "markdown":
            print(f"   Parser: {source['parser']}")
        print(f"   Output: {source['output']}")
        print()

    exists = "✓" if os.path.exists(os.path.join(ROOT, TOKENS_SOURCE)) else "✗"
    print(f"{len(DATA_SOURCES) + 1}. tokens [{exists}]")
    print(f"   Type: json (read directly, no intermediate file)")
    print(f"   Source: {TOKENS_SOURCE}")
    print()
    print("=" * 60)
    print("\nTo run extraction: python scripts/extract-api-data.py")


def resolve_dir(path: str) -> Path:
    """Resolve a directory argument relative to the repo root (absolute paths kept)."""
    p = Path(path)
    return p if p.is_absolute() else Path(ROOT) / p


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  ✓ Wrote {path}")


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def process_markdown_source(source: dict[str, Any], output_dir: Path) -> bool:
    """Process a markdown data source using its parser."""
    source_path = os.path.join(ROOT, source["source"])

    if not os.path.exists(source_path):
        print(f"  ✗ Source file not found: {source['source']}")
        return False

    print(f"  → Parsing {source['source']}...")

    try:
        parser_script = source["parser"].replace(".", "/") + ".py"
        parser_path = os.path.join(ROOT, parser_script)

        if not os.path.exists(parser_path):
            print(f"  ✗ Parser script not found: {parser_script}")
            return False

        result = subprocess.run(
            [sys.executable, parser_path, source_path],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

        if result.returncode != 0:
            print(f"  ✗ Parser failed: {result.stderr}")
            return False

        data = json.loads(result.stdout)
        write_json(output_dir / source["output"], data)
        return True

    except json.JSONDecodeError as e:
        print(f"  ✗ Parser output is not valid JSON: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error processing {source['name']}: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_json_source(source: dict[str, Any], output_dir: Path) -> bool:
    """Process a JSON data source (copy with source metadata)."""
    source_path = os.path.join(ROOT, source["source"])

    if not os.path.exists(source_path):
        print(f"  ✗ Source file not found: {source['source']}")
        return False

    print(f"  → Copying {source['source']}...")

    try:
        data = read_json(Path(source_path))
        write_json(output_dir / source["output"], {"source": source["source"], "data": data})
        return True
    except Exception as e:
        print(f"  ✗ Error processing {source['name']}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# API endpoint generators. Each returns the generated payload (or None).
# ---------------------------------------------------------------------------

def _endpoint(description: str, **fields: Any) -> dict[str, Any]:
    """Standard API envelope: version + description, then the payload fields."""
    return {"version": API_VERSION, "description": description, **fields}


def generate_api_tokens(api_dir: Path) -> dict[str, Any] | None:
    """Generate tokens.json directly from assets/tokens/azmx-tokens.json.

    The Figma fileKey in $meta is deliberately not copied into the API.
    """
    source_path = Path(ROOT) / TOKENS_SOURCE
    if not source_path.exists():
        print(f"  ✗ Source file not found: {source_path}")
        return None

    print(f"  → Generating API tokens from {TOKENS_SOURCE}...")
    try:
        tokens_data = read_json(source_path)
        meta = tokens_data.get("$meta", {})

        collections = []
        for key, value in tokens_data.items():
            if key == "$meta" or not (isinstance(value, dict) and "tokens" in value):
                continue
            collections.append({
                "name": key,
                "modes": value.get("modes", []),
                "count": len(value["tokens"]),
                "tokens": value["tokens"],
            })

        total = sum(c["count"] for c in collections)
        payload = _endpoint(
            f"{meta.get('name', 'AZM X Design Tokens')} - {total} design tokens across "
            f"{len(collections)} collections",
            name=meta.get("name", "AZM X Design Tokens"),
            source=meta.get("source", ""),
            source_version=meta.get("version", ""),
            exported=meta.get("exported", ""),
            count=total,
            collections=collections,
        )
        write_json(api_dir / "tokens.json", payload)
        return payload
    except Exception as e:
        print(f"  ✗ Error generating API tokens: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_api_palettes(data_dir: Path, api_dir: Path) -> dict[str, Any] | None:
    """Generate palettes.json from parsed colors data."""
    source_path = data_dir / "colors.json"
    if not source_path.exists():
        print(f"  ✗ Source file not found: {source_path}")
        return None

    print(f"  → Generating API palettes from {source_path}...")
    try:
        colors_data = read_json(source_path)
        palettes = []

        blue_ramp = colors_data.get("blue_ramp", [])
        if blue_ramp:
            palettes.append({
                "name": "Blue",
                "description": "Primary brand palette with Electric (#001AFF) and Dark Navy (#040038)",
                "ramp": [
                    {"step": item["step"], "hex": item["hex"], "notes": item["notes"]}
                    for item in blue_ramp
                ],
            })

        for palette in colors_data.get("secondary_palettes", []):
            palettes.append({
                "name": palette["name"],
                "signature": palette["signature"],
                "deep": palette["deep"],
                "text_safe_step": palette["text_safe_step"],
                "text_safe_hex": palette["text_safe_hex"],
                "description": "Secondary palette - full 12-step ramp available in design tokens",
            })

        payload = _endpoint(
            "AZMX color palettes - one primary (Blue) and five secondary palettes",
            count=len(palettes),
            palettes=palettes,
        )
        write_json(api_dir / "palettes.json", payload)
        return payload
    except Exception as e:
        print(f"  ✗ Error generating API palettes: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_api_typography(data_dir: Path, api_dir: Path) -> dict[str, Any] | None:
    """Generate typography.json from parsed typography data."""
    source_path = data_dir / "typography.json"
    if not source_path.exists():
        print(f"  ✗ Source file not found: {source_path}")
        return None

    print(f"  → Generating API typography from {source_path}...")
    try:
        typography_data = read_json(source_path)
        payload = _endpoint(
            "AZMX typography system - font families, weights, type scale, and usage rules",
            families=typography_data.get("families", []),
            weights=typography_data.get("weights", []),
            type_scale=typography_data.get("type_scale", []),
            rules=typography_data.get("rules", []),
            bilingual_note=typography_data.get("bilingual_note", ""),
        )
        write_json(api_dir / "typography.json", payload)
        return payload
    except Exception as e:
        print(f"  ✗ Error generating API typography: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_api_voice(data_dir: Path, api_dir: Path) -> dict[str, Any] | None:
    """Generate voice.json from parsed voice-and-tone data."""
    source_path = data_dir / "voice.json"
    if not source_path.exists():
        print(f"  ✗ Source file not found: {source_path}")
        return None

    print(f"  → Generating API voice from {source_path}...")
    try:
        voice_data = read_json(source_path)
        payload = _endpoint(
            "AZMX voice and tone - brand language, tone rules, the four voice dimensions, "
            "writing mechanics, format rules, and platform-specific voice",
            **voice_data,
        )
        write_json(api_dir / "voice.json", payload)
        return payload
    except Exception as e:
        print(f"  ✗ Error generating API voice: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_api_audiences(data_dir: Path, api_dir: Path) -> dict[str, Any] | None:
    """Generate audiences.json from parsed audiences data."""
    source_path = data_dir / "audiences.json"
    if not source_path.exists():
        print(f"  ✗ Source file not found: {source_path}")
        return None

    print(f"  → Generating API audiences from {source_path}...")
    try:
        audiences_data = read_json(source_path)
        personas = audiences_data.get("personas", [])
        payload = _endpoint(
            f"AZMX audience personas and messaging - {len(personas)} external personas, "
            "internal audiences, external motions, and brands",
            count=len(personas),
            personas=personas,
            internal_audiences=audiences_data.get("internal_audiences", []),
            external_motions=audiences_data.get("external_motions", []),
            brands=audiences_data.get("brands", []),
        )
        write_json(api_dir / "audiences.json", payload)
        return payload
    except Exception as e:
        print(f"  ✗ Error generating API audiences: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_api_prompts(data_dir: Path, api_dir: Path) -> dict[str, Any] | None:
    """Generate prompts.json from parsed content-prompts data."""
    source_path = data_dir / "prompts.json"
    if not source_path.exists():
        print(f"  ✗ Source file not found: {source_path}")
        return None

    print(f"  → Generating API prompts from {source_path}...")
    try:
        prompts_data = read_json(source_path)
        prompts = prompts_data.get("prompts", [])
        payload = _endpoint(
            "AZMX content generation prompt templates - briefs, articles, case studies, "
            "social customisation, and localisation",
            count=len(prompts),
            prompts=prompts,
        )
        write_json(api_dir / "prompts.json", payload)
        return payload
    except Exception as e:
        print(f"  ✗ Error generating API prompts: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_api_images(data_dir: Path, api_dir: Path) -> dict[str, Any] | None:
    """Generate images.json from image-tags data."""
    source_path = data_dir / "images.json"
    if not source_path.exists():
        print(f"  ✗ Source file not found: {source_path}")
        return None

    print(f"  → Generating API images from {source_path}...")
    try:
        image_tags = read_json(source_path).get("data", {})
        images = [
            {"filename": filename, "tags": tags}
            for filename, tags in sorted(image_tags.items())
        ]
        payload = _endpoint(
            "AZMX brand images with conceptual tags",
            count=len(images),
            images=images,
        )
        write_json(api_dir / "images.json", payload)
        return payload
    except Exception as e:
        print(f"  ✗ Error generating API images: {e}")
        import traceback
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------------
# index.json - computed from the generated endpoint payloads
# ---------------------------------------------------------------------------

def _size_estimate(path: Path) -> str:
    kb = path.stat().st_size / 1024
    return f"~{round(kb)}KB"


def _join(names: list[str]) -> str:
    return ", ".join(names)


def build_index(api_dir: Path, payloads: dict[str, dict[str, Any]], updated: str) -> dict[str, Any]:
    """Build index.json with counts and descriptions derived from real data."""
    tokens = payloads["tokens"]
    palettes = payloads["palettes"]
    typography = payloads["typography"]
    voice = payloads["voice"]
    audiences = payloads["audiences"]
    prompts = payloads["prompts"]
    images = payloads["images"]

    blue = next((p for p in palettes["palettes"] if "ramp" in p), None)
    secondary = [p for p in palettes["palettes"] if "ramp" not in p]
    unique_tags = sorted({t for img in images["images"] for t in img["tags"]})

    endpoint_specs = [
        {
            "path": "/tokens.json",
            "name": "Design Tokens",
            "description": (
                f"Complete set of {tokens['count']} design tokens across "
                f"{len(tokens['collections'])} collections (primitives, palette modes, "
                f"semantic light/dark, component, canvas, RTL)"
            ),
            "data_structure": {
                c["name"]: f"{c['count']} tokens × {len(c['modes'])} mode(s) ({_join(c['modes'])})"
                for c in tokens["collections"]
            },
        },
        {
            "path": "/palettes.json",
            "name": "Color Palettes",
            "description": (
                f"{palettes['count']} brand color palettes: Blue with its "
                f"{len(blue['ramp']) if blue else 0}-step ramp, plus {len(secondary)} secondary "
                "palettes with signature, deep, and text-safe values"
            ),
            "data_structure": {
                "palettes": f"{palettes['count']} palettes ({_join([p['name'] for p in palettes['palettes']])})",
                "blue_ramp": (
                    f"{len(blue['ramp'])} steps ({blue['ramp'][0]['step']} to {blue['ramp'][-1]['step']}), "
                    "each with hex and usage notes"
                ) if blue else "n/a",
                "secondary": (
                    f"{len(secondary)} palettes with signature, deep, text_safe_step and text_safe_hex; "
                    "full ramps live in tokens.json"
                ),
            },
        },
        {
            "path": "/typography.json",
            "name": "Typography System",
            "description": "Font families, weights, type scale, and typographic rules for the AZMX brand",
            "data_structure": {
                "families": f"{len(typography['families'])} font families ({_join([f['family'] for f in typography['families']])})",
                "weights": f"{len(typography['weights'])} weights ({_join([w['weight'] for w in typography['weights']])})",
                "type_scale": f"{len(typography['type_scale'])} roles with size, line height, weight, tracking (px) and case",
                "rules": f"{len(typography['rules'])} usage rules plus a bilingual note",
            },
        },
        {
            "path": "/voice.json",
            "name": "Voice & Tone Guidelines",
            "description": "Brand language, tone rules, voice dimensions, writing mechanics, and format-specific guidelines",
            "data_structure": {
                "tone_rules": f"{len(voice['tone_rules'])} tone rules",
                "dimensions": f"{len(voice['dimensions'])} voice dimensions ({_join([d['dimension'] for d in voice['dimensions']])})",
                "calibration_examples": f"{len(voice['calibration_examples'])} calibration examples",
                "purpose_modes": f"{len(voice['purpose_modes'])} purpose modes",
                "writing_mechanics": f"{len(voice['writing_mechanics'])} banned patterns (the no-AI-tells rules)",
                "universal_principles": f"{len(voice['universal_principles'])} universal principles",
                "format_rules": f"{len(voice['format_rules'])} format rules",
                "platform_voice": f"{len(voice['platform_voice'])} platform voices ({_join([p['platform'] for p in voice['platform_voice']])})",
                "pre_publish_checklist": f"{len(voice['pre_publish_checklist'])} checklist items",
            },
        },
        {
            "path": "/audiences.json",
            "name": "Audience Personas",
            "description": (
                f"{audiences['count']} audience personas with pain points, core messages, "
                "motions, and brand associations"
            ),
            "data_structure": {
                "personas": f"{audiences['count']} personas ({_join([p['name'] for p in audiences['personas']])})",
                "motions": _join(sorted({p['motion'] for p in audiences['personas']})),
                "internal_audiences": f"{len(audiences['internal_audiences'])} internal segments",
                "external_motions": f"{len(audiences['external_motions'])} external motions",
                "brands": f"{len(audiences['brands'])} brands ({_join([b['name'] for b in audiences['brands']])})",
            },
        },
        {
            "path": "/prompts.json",
            "name": "Content Prompt Templates",
            "description": f"{prompts['count']} content generation prompt templates with full template text",
            "data_structure": {
                "prompts": f"{prompts['count']} prompts, each with id, number, title, description, deck_page, template, notes",
                "titles": _join([p["title"] for p in prompts["prompts"]]),
            },
        },
        {
            "path": "/images.json",
            "name": "Brand Image Library",
            "description": f"{images['count']} catalogued brand images, each with three concept tags",
            "data_structure": {
                "images": f"{images['count']} images with filename and tags",
                "tags": f"{len(unique_tags)} distinct concept tags",
                "download": "Image files: " + f"{REPO_URL}/raw/main/assets/images/<palette>/<filename>",
            },
        },
    ]

    endpoints = []
    for spec in endpoint_specs:
        file_path = api_dir / spec["path"].lstrip("/")
        endpoints.append({
            "path": spec["path"],
            "name": spec["name"],
            "description": spec["description"],
            "methods": ["GET"],
            "response_format": "JSON",
            "data_structure": spec["data_structure"],
            "example_url": f"{BASE_URL}{spec['path']}",
            "size_estimate": _size_estimate(file_path),
        })

    return {
        "$meta": {
            "name": API_NAME,
            "version": API_VERSION,
            "description": API_DESCRIPTION,
            "base_url": BASE_URL,
            "docs_url": DOCS_URL,
            "repository": REPO_URL,
            "license": LICENSE,
            "updated": updated,
            "contact": CONTACT,
        },
        "endpoints": endpoints,
        "usage": {
            "authentication": "None required (public read-only access)",
            "rate_limiting": "GitHub Pages CDN limits apply",
            "cors": "Enabled (GitHub Pages serves Access-Control-Allow-Origin: *)",
            "caching": "Recommended: 1 hour for production use",
            "versioning": "API version in URL path (/v1/). Breaking changes will increment version number.",
        },
        "examples": [
            {
                "description": "Fetch all design tokens",
                "request": f"GET {BASE_URL}/tokens.json",
                "language": "curl",
                "code": f"curl -H 'Accept: application/json' {BASE_URL}/tokens.json",
            },
            {
                "description": "Fetch color palettes",
                "request": f"GET {BASE_URL}/palettes.json",
                "language": "javascript",
                "code": (
                    f"fetch('{BASE_URL}/palettes.json')\n"
                    "  .then(res => res.json())\n"
                    "  .then(data => console.log(data.palettes));"
                ),
            },
            {
                "description": "Fetch audience personas",
                "request": f"GET {BASE_URL}/audiences.json",
                "language": "python",
                "code": (
                    "import requests\n"
                    f"response = requests.get('{BASE_URL}/audiences.json')\n"
                    "audiences = response.json()\n"
                    "for persona in audiences['personas']:\n"
                    "    print(f\"{persona['name']}: {persona['core_message']}\")"
                ),
            },
        ],
        "resources": {
            "documentation": DOCS_URL,
            "examples": f"{DOCS_URL}examples.html",
            "openapi_spec": f"{BASE_URL}/openapi.json",
            "repository": REPO_URL,
            "issues": f"{REPO_URL}/issues",
        },
    }


def extract_all(output_dir: str = "data", api_dir: str = "api/v1", updated: str | None = None) -> int:
    """Extract all data sources and generate the API endpoint files.

    Returns:
        Number of failures (0 = success)
    """
    print("AZMX API Data Extraction")
    print("=" * 60)
    print(f"\nRoot directory: {ROOT}")
    print(f"Intermediate directory: {output_dir}")
    print(f"API directory: {api_dir}\n")

    out_path = resolve_dir(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    api_path = resolve_dir(api_dir)
    api_path.mkdir(parents=True, exist_ok=True)

    failures = 0
    for idx, source in enumerate(DATA_SOURCES, 1):
        print(f"\n[{idx}/{len(DATA_SOURCES)}] Processing {source['name']}...")
        if source["type"] == "markdown":
            success = process_markdown_source(source, out_path)
        elif source["type"] == "json":
            success = process_json_source(source, out_path)
        else:
            print(f"  ✗ Unknown source type: {source['type']}")
            success = False
        if not success:
            failures += 1

    print("\n" + "=" * 60)
    print(f"\nExtraction complete: {len(DATA_SOURCES) - failures}/{len(DATA_SOURCES)} succeeded")

    if failures > 0:
        print(f"Failed: {failures}")
        return failures

    print("\nGenerating API endpoints...")
    generators = {
        "tokens": lambda: generate_api_tokens(api_path),
        "palettes": lambda: generate_api_palettes(out_path, api_path),
        "typography": lambda: generate_api_typography(out_path, api_path),
        "voice": lambda: generate_api_voice(out_path, api_path),
        "audiences": lambda: generate_api_audiences(out_path, api_path),
        "prompts": lambda: generate_api_prompts(out_path, api_path),
        "images": lambda: generate_api_images(out_path, api_path),
    }

    previous_payloads: dict[str, Any] = {}
    for name in generators:
        existing = api_path / f"{name}.json"
        if existing.exists():
            try:
                with open(existing, encoding="utf-8") as fh:
                    previous_payloads[name] = json.load(fh)
            except (OSError, ValueError):
                pass

    payloads: dict[str, dict[str, Any]] = {}
    for name, generate in generators.items():
        payload = generate()
        if payload is None:
            print(f"  ✗ Failed to generate API {name} endpoint")
            return 1
        payloads[name] = payload
    changed_payloads = [n for n, p in payloads.items() if previous_payloads.get(n) != p]

    print("\nGenerating API index...")
    # Keep the build reproducible: only move the `updated` stamp when an endpoint's
    # content actually changed, so a rebuild on a later day is a no-op in git.
    stamp = updated
    if stamp is None:
        previous_index = api_path / "index.json"
        previous_updated = None
        previous_endpoints = None
        if previous_index.exists():
            try:
                with open(previous_index, encoding="utf-8") as fh:
                    prev = json.load(fh)
                previous_updated = prev.get("$meta", {}).get("updated")
                previous_endpoints = {k: v for k, v in prev.items() if k != "$meta"}
            except (OSError, ValueError):
                pass
        candidate = build_index(api_path, payloads, previous_updated or "")
        current_endpoints = {k: v for k, v in candidate.items() if k != "$meta"}
        if previous_updated and current_endpoints == previous_endpoints and not changed_payloads:
            stamp = previous_updated
        else:
            stamp = _dt.date.today().isoformat()
    write_json(api_path / "index.json", build_index(api_path, payloads, stamp))
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Extract AZMX brand data for API endpoints")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what will be processed without running extraction")
    parser.add_argument("--output-dir", default="data",
                        help="Directory for intermediate JSON files (default: data/, gitignored)")
    parser.add_argument("--api-dir", default="api/v1",
                        help="Directory for API endpoint files (default: api/v1/)")
    parser.add_argument("--updated", default=None,
                        help="Override the build date stamped into index.json (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.dry_run:
        show_dry_run()
        return 0

    return extract_all(args.output_dir, args.api_dir, args.updated)


if __name__ == "__main__":
    sys.exit(main())
