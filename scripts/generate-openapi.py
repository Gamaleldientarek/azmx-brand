#!/usr/bin/env python3
"""Generate OpenAPI 3.0 specification from AZMX Brand API endpoints.

Usage:
    python scripts/generate-openapi.py [--validate] [--api-dir DIR] [--output-dir DIR]

Introspects the JSON endpoints listed in api/v1/index.json and generates an
OpenAPI 3.0 specification (JSON) with inferred schemas and examples.
API metadata (name, version, base URL, contact) is read from index.json's
$meta block, which scripts/extract-api-data.py writes.

Options:
    --validate      Validate the generated spec with openapi-spec-validator
    --api-dir       Directory containing the API endpoint files (default: api/v1/)
    --output-dir    Directory for OpenAPI files (default: same as --api-dir)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any



ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Objects with more keys than this are treated as maps (additionalProperties)
# rather than having every key enumerated as a required property.
MAP_THRESHOLD = 20


def resolve_dir(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(ROOT) / p


def load_json_endpoint(filepath: Path) -> dict[str, Any] | None:
    """Load a JSON endpoint file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  ✗ Error loading {filepath}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Schema inference
# ---------------------------------------------------------------------------

def _key(schema: dict[str, Any]) -> str:
    return json.dumps(schema, sort_keys=True)


def merge_schemas(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge schemas inferred from sibling values (array items / map values).

    Objects are merged property-wise with `required` reduced to the keys present
    in every sibling; heterogeneous types become a `oneOf`.
    """
    expanded: list[dict[str, Any]] = []
    for s in schemas:
        if not s:
            continue
        if "oneOf" in s:  # flatten previously merged unions
            expanded.extend(s["oneOf"])
            if s.get("nullable"):
                expanded.append({"type": "string", "nullable": True})
        else:
            expanded.append(s)
    schemas = expanded
    if not schemas:
        return {}

    nullable = any(s.get("nullable") for s in schemas)
    # A null placeholder ({"type": "string", "nullable": true}) must not override a real type
    non_null = [s for s in schemas if not s.get("nullable")] or schemas

    types = {s.get("type") for s in non_null}
    if types == {"integer", "number"}:  # integers are numbers
        types = {"number"}
    if len(types) == 1:
        t = next(iter(types))
        if t == "object":
            merged = _merge_objects(non_null)
        elif t == "array":
            merged = {"type": "array", "items": merge_schemas([s.get("items", {}) for s in non_null])}
        else:
            merged = {"type": t}
        if nullable:
            merged["nullable"] = True
        return merged

    distinct: dict[str, dict[str, Any]] = {}
    for s in non_null:
        s = dict(s)
        s.pop("nullable", None)
        distinct.setdefault(_key(s), s)
    merged = {"oneOf": list(distinct.values())}
    if nullable:
        merged["nullable"] = True
    return merged


def _merge_objects(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    if any("additionalProperties" in s for s in schemas):
        # Sibling maps: merge value schemas (enumerated siblings contribute their property schemas)
        values = []
        for s in schemas:
            if "additionalProperties" in s:
                values.append(s["additionalProperties"])
            else:
                values.extend(s.get("properties", {}).values())
        return {"type": "object", "additionalProperties": merge_schemas(values)}

    props: dict[str, list[dict[str, Any]]] = {}
    for s in schemas:
        for k, v in s.get("properties", {}).items():
            props.setdefault(k, []).append(v)

    required = None
    for s in schemas:
        r = set(s.get("required", []))
        required = r if required is None else required & r

    merged: dict[str, Any] = {
        "type": "object",
        "properties": {k: merge_schemas(v) for k, v in props.items()},
    }
    if required:
        merged["required"] = [k for k in merged["properties"] if k in required]
    return merged


def infer_schema_from_value(value: Any) -> dict[str, Any]:
    """Infer an OpenAPI 3.0 schema from a JSON value."""
    if value is None:
        # OpenAPI 3.0 has no null type; a nullable string is the closest fit.
        return {"type": "string", "nullable": True}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}
        return {"type": "array", "items": merge_schemas([infer_schema_from_value(v) for v in value])}
    if isinstance(value, dict):
        if len(value) > MAP_THRESHOLD:
            return {
                "type": "object",
                "additionalProperties": merge_schemas([infer_schema_from_value(v) for v in value.values()]),
            }
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {k: infer_schema_from_value(v) for k, v in value.items()},
        }
        if value:
            schema["required"] = list(value.keys())
        return schema
    return {"type": "string"}


def create_schema_from_endpoint(endpoint_data: dict[str, Any]) -> dict[str, Any]:
    """Create an OpenAPI schema definition from endpoint JSON data."""
    schema = infer_schema_from_value(endpoint_data)
    if isinstance(endpoint_data.get("description"), str):
        schema["description"] = endpoint_data["description"]
    return schema


# ---------------------------------------------------------------------------
# Spec generation
# ---------------------------------------------------------------------------

def generate_openapi_spec(api_dir: Path) -> dict[str, Any]:
    """Generate complete OpenAPI 3.0 specification from the API directory."""
    index_data = load_json_endpoint(api_dir / "index.json")
    if not index_data:
        print(f"  ✗ Could not load {api_dir / 'index.json'}", file=sys.stderr)
        sys.exit(1)

    meta = index_data.get("$meta", {})
    base_url = meta.get("base_url")
    if not base_url:
        print("  ✗ index.json $meta.base_url is missing", file=sys.stderr)
        sys.exit(1)

    spec: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {
            "title": meta.get("name", "AZMX Brand API"),
            "version": meta.get("version", "1.0.0"),
            "description": meta.get("description", "API for AZMX brand data"),
            "contact": {
                "name": meta.get("contact", {}).get("organization", "AZMX"),
                "email": meta.get("contact", {}).get("email", "brand@azmx.sa"),
            },
            "license": {"name": meta.get("license", "Proprietary")},
        },
        "externalDocs": {
            "description": "API documentation",
            "url": meta.get("docs_url", base_url),
        },
        "servers": [
            {"url": base_url, "description": "Production API (GitHub Pages)"},
        ],
        "paths": {},
        "components": {"schemas": {}},
    }

    for endpoint in index_data.get("endpoints", []):
        path = endpoint.get("path", "")
        endpoint_name = endpoint.get("name", path.replace("/", "").replace(".json", ""))
        description = endpoint.get("description", "")

        endpoint_data = load_json_endpoint(api_dir / path.lstrip("/"))
        if not endpoint_data:
            print(f"  ⚠ Skipping {path} - could not load file", file=sys.stderr)
            continue

        schema_name = endpoint_name.replace(" ", "").replace("&", "And")
        spec["components"]["schemas"][schema_name] = create_schema_from_endpoint(endpoint_data)

        spec["paths"][path] = {
            "get": {
                "summary": endpoint_name,
                "description": description,
                "operationId": f"get{schema_name}",
                "tags": [endpoint_name.split()[0]],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{schema_name}"},
                                "example": endpoint_data,
                            }
                        },
                    },
                    "404": {"description": "Endpoint not found"},
                },
            }
        }

    return spec


def validate_openapi_spec(spec: dict[str, Any]) -> bool:
    """Validate the spec with openapi-spec-validator."""
    try:
        from openapi_spec_validator import validate
    except ImportError:
        print("  ✗ openapi-spec-validator is not installed (pip install openapi-spec-validator)",
              file=sys.stderr)
        return False
    try:
        validate(spec)
    except Exception as e:  # OpenAPIValidationError and friends
        print(f"  ✗ {e}", file=sys.stderr)
        return False
    print("  ✓ OpenAPI specification is valid")
    return True


def write_openapi_files(spec: dict[str, Any], output_dir: Path) -> None:
    """Write the spec as openapi.json (the single committed form of the spec)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "openapi.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  ✓ Wrote {json_path}")



def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OpenAPI 3.0 specification from AZMX Brand API")
    parser.add_argument("--validate", action="store_true", help="Validate the generated OpenAPI spec")
    parser.add_argument("--api-dir", default="api/v1", help="Directory with API endpoint files (default: api/v1/)")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: same as --api-dir)")
    args = parser.parse_args()

    api_dir = resolve_dir(args.api_dir)
    output_dir = resolve_dir(args.output_dir) if args.output_dir else api_dir

    print("AZMX OpenAPI Schema Generator")
    print("=" * 60)

    print("\n→ Generating OpenAPI specification...")
    spec = generate_openapi_spec(api_dir)
    print(f"  ✓ Generated spec with {len(spec['paths'])} endpoints and "
          f"{len(spec['components']['schemas'])} schemas")

    if args.validate:
        print("\n→ Validating OpenAPI specification...")
        if not validate_openapi_spec(spec):
            print("\n✗ Validation failed")
            return 1

    print(f"\n→ Writing OpenAPI files to {output_dir}...")
    write_openapi_files(spec, output_dir)

    print("\n" + "=" * 60)
    print("✓ OpenAPI generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
