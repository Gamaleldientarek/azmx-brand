#!/usr/bin/env python3
"""
AZMX Brand API Documentation Generator

Renders scripts/docs-template.html into a static Redoc documentation page
(api-docs/index.html). The page loads the OpenAPI spec in place from
api/v1/openapi.json (relative path) rather than carrying its own copy.

Site metadata (base URL, GitHub URL, version) is read from the index.json
that sits next to the spec, so scripts/extract-api-data.py stays the single
source of truth.

Usage:
    python scripts/generate-docs.py --output api-docs/
    python scripts/generate-docs.py --spec api/v1/openapi.json --output api-docs/
"""

import argparse
import html
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict

import yaml


ROOT = Path(__file__).resolve().parent.parent
FALLBACK_LOGO = ROOT / "assets" / "logo" / "azmx-logo-colored.svg"


def load_openapi_spec(spec_path: Path) -> Dict[str, Any]:
    """Load OpenAPI specification from a YAML or JSON file."""
    if not spec_path.exists():
        raise FileNotFoundError(f"OpenAPI spec not found: {spec_path}")

    with open(spec_path, 'r', encoding='utf-8') as f:
        if spec_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        if spec_path.suffix == '.json':
            return json.load(f)
        raise ValueError(f"Unsupported file format: {spec_path.suffix}")


def load_index_meta(spec_path: Path) -> Dict[str, Any]:
    """Read $meta from the index.json next to the spec (empty dict if absent)."""
    index_path = spec_path.parent / "index.json"
    if not index_path.exists():
        return {}
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f).get("$meta", {})


def load_template(template_path: Path) -> str:
    """Load HTML template file."""
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template: str, context: Dict[str, str]) -> str:
    """Render {{key}} placeholders, HTML-escaping every substituted value."""
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", html.escape(str(value), quote=True))
    return result


def resolve_logo(output_dir: Path) -> str:
    """Return the logo path (relative to output_dir) for the docs page.

    Uses the hand-placed PNG favicon in the output directory when present,
    otherwise copies the brand SVG logo from assets/ and uses that.
    """
    logo_dir = output_dir / "assets" / "logo"
    png = logo_dir / "azmx-favicon.png"
    if png.exists():
        return "assets/logo/azmx-favicon.png"

    if not FALLBACK_LOGO.exists():
        raise FileNotFoundError(f"No favicon PNG and fallback logo missing: {FALLBACK_LOGO}")

    logo_dir.mkdir(parents=True, exist_ok=True)
    dst = logo_dir / FALLBACK_LOGO.name
    shutil.copyfile(FALLBACK_LOGO, dst)
    print(f"  Favicon PNG missing - copied fallback logo: {dst}")
    return f"assets/logo/{FALLBACK_LOGO.name}"


def generate_documentation(
    spec_path: Path,
    template_path: Path,
    output_dir: Path,
    base_url: str = "",
    github_url: str = "",
) -> None:
    """Generate the API documentation page from the OpenAPI spec."""
    print(f"Loading OpenAPI spec from: {spec_path}")
    spec = load_openapi_spec(spec_path)
    meta = load_index_meta(spec_path)

    info = spec.get('info', {})
    title = info.get('title', 'API Documentation')
    description = info.get('description', 'API Reference Documentation')
    version = info.get('version', meta.get('version', '1.0.0'))

    base_url = base_url or meta.get('docs_url', '')
    github_url = github_url or meta.get('repository', '')

    print(f"Loading template from: {template_path}")
    template = load_template(template_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Redoc loads the spec in place - no copy in the docs directory.
    spec_rel = Path(os.path.relpath(spec_path.resolve(), output_dir.resolve())).as_posix()
    print(f"Spec path (relative to docs): {spec_rel}")

    logo_path = resolve_logo(output_dir)

    context = {
        'title': title,
        'description': description,
        'version': version,
        'spec_path': spec_rel,
        'spec_url': spec_rel,
        'base_url': base_url or '.',
        'github_url': github_url,
        'logo_path': logo_path,
        'favicon_path': logo_path,
    }

    print("Rendering documentation...")
    output_file = output_dir / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(render_template(template, context))

    print(f"✓ Documentation generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate API documentation site from OpenAPI specification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate-docs.py --output api-docs/
  python scripts/generate-docs.py --spec api/v1/openapi.json --output api-docs/
        """
    )
    parser.add_argument('--spec', type=Path, default=Path('api/v1/openapi.json'),
                        help='Path to OpenAPI specification (default: api/v1/openapi.json)')
    parser.add_argument('--template', type=Path, default=Path('scripts/docs-template.html'),
                        help='Path to HTML template (default: scripts/docs-template.html)')
    parser.add_argument('--output', type=Path, required=True,
                        help='Output directory for the generated documentation')
    parser.add_argument('--base-url', type=str, default='',
                        help='Documentation site URL (default: index.json $meta.docs_url)')
    parser.add_argument('--github-url', type=str, default='',
                        help='GitHub repository URL (default: index.json $meta.repository)')
    args = parser.parse_args()

    try:
        generate_documentation(
            spec_path=args.spec,
            template_path=args.template,
            output_dir=args.output,
            base_url=args.base_url,
            github_url=args.github_url,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
