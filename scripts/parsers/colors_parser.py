#!/usr/bin/env python3
"""
colors_parser.py — AZMX color palette parser.

Extracts structured palette data from references/colors.md.

Usage:
    python scripts/parsers/colors_parser.py references/colors.md

Outputs JSON with all palette information: primary colors, ramps, secondary
palettes, RAG dots, surfaces, and text color mappings.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .markdown_utils import parse_table_row, strip_inline_md
except ImportError:  # run directly as a script
    from markdown_utils import parse_table_row, strip_inline_md


HEX_RE = re.compile(r"#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3,4})\b")


def norm_hex(raw: str) -> str:
    """Normalise a hex token to #RRGGBB uppercase."""
    h = raw.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    elif len(h) in (6, 8):
        h = h[:6]
    else:
        return raw
    return "#" + h.upper()


def extract_hex_values(text: str) -> list[str]:
    """Extract and normalise all hex color values from text."""
    return [norm_hex(m.group(0)) for m in HEX_RE.finditer(text)]


def parse_colors_md(file_path: str) -> dict[str, Any]:
    """
    Parse references/colors.md into structured palette data.

    Returns a dict with:
        - primary: list of {token, hex, usage}
        - blue_ramp: list of {step, hex, notes}
        - neutrals: list of {step, hex, notes}
        - secondary_palettes: list of {name, signature, deep, text_safe_step, text_safe_hex}
        - rag_dots: list of {token, hex, meaning}
        - surfaces: list of {surface, fill, use_for}
        - text_by_surface: list of {surface, title, body, eyebrow, meta}
        - all_colors: dict mapping hex -> [token_names]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"colors.md not found at {file_path}")

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    result: dict[str, Any] = {
        "primary": [],
        "blue_ramp": [],
        "neutrals": [],
        "secondary_palettes": [],
        "rag_dots": [],
        "surfaces": [],
        "text_by_surface": [],
        "all_colors": {},
    }

    current_section = None
    in_table = False
    table_headers = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track sections (both level 2 and level 3 headings)
        if stripped.startswith("### "):
            current_section = stripped[4:].lower()
            in_table = False
            continue
        elif stripped.startswith("## "):
            current_section = stripped[3:].lower()
            in_table = False
            continue

        # Track table headers
        if "|" in stripped and "---" in lines[i + 1] if i + 1 < len(lines) else False:
            table_headers = parse_table_row(stripped)
            in_table = True
            continue

        # Skip separator rows
        if stripped.startswith("|") and all(c in "-:|" for c in stripped.replace(" ", "")):
            continue

        # Parse table rows
        if not in_table or not stripped.startswith("|"):
            in_table = False
            continue

        cells = parse_table_row(stripped)
        if not cells:
            continue

        # Extract data based on current section
        if current_section == "primary":
            if len(cells) >= 2:
                hexes = extract_hex_values(cells[1])
                result["primary"].append({
                    "token": cells[0],
                    "hex": hexes[0] if hexes else "",
                    "usage": cells[2] if len(cells) > 2 else "",
                })

        elif current_section == "blue ramp (50 to 1000)":
            if len(cells) >= 2:
                hexes = extract_hex_values(cells[1])
                result["blue_ramp"].append({
                    "step": cells[0],
                    "hex": hexes[0] if hexes else "",
                    "notes": cells[2] if len(cells) > 2 else "",
                })

        elif current_section == "neutrals (25 to 950)":
            if len(cells) >= 2:
                hexes = extract_hex_values(cells[1])
                result["neutrals"].append({
                    "step": cells[0],
                    "hex": hexes[0] if hexes else "",
                    "notes": cells[2] if len(cells) > 2 else "",
                })

        elif current_section == "the five secondary palettes":
            if len(cells) >= 4:
                sig_hexes = extract_hex_values(cells[1])
                deep_hexes = extract_hex_values(cells[2])
                safe_hexes = extract_hex_values(cells[3])

                result["secondary_palettes"].append({
                    "name": cells[0],
                    "signature": sig_hexes[0] if sig_hexes else "",
                    "deep": deep_hexes[0] if deep_hexes else "",
                    "text_safe_step": re.search(r"color/\w+/\d+", cells[3]).group(0) if re.search(r"color/\w+/\d+", cells[3]) else "",
                    "text_safe_hex": safe_hexes[0] if safe_hexes else "",
                })

        elif "rag data dots" in current_section:
            if len(cells) >= 2:
                hexes = extract_hex_values(cells[1])
                result["rag_dots"].append({
                    "token": cells[0],
                    "hex": hexes[0] if hexes else "",
                    "meaning": cells[2] if len(cells) > 2 else "",
                })

        elif current_section == "surfaces":
            if len(cells) >= 2:
                result["surfaces"].append({
                    "surface": cells[0],
                    "fill": cells[1],
                    "use_for": cells[2] if len(cells) > 2 else "",
                })

        elif current_section == "text color by surface":
            if len(cells) >= 2:
                result["text_by_surface"].append({
                    "surface": cells[0],
                    "title": cells[1] if len(cells) > 1 else "",
                    "body": cells[2] if len(cells) > 2 else "",
                    "eyebrow": cells[3] if len(cells) > 3 else "",
                    "meta": cells[4] if len(cells) > 4 else "",
                })

    # Build all_colors mapping: hex -> list of token names
    for item in result["primary"]:
        hex_val = item["hex"]
        token = item["token"]
        if hex_val:
            result["all_colors"].setdefault(hex_val, []).append(token)

    for item in result["blue_ramp"]:
        hex_val = item["hex"]
        token = item["step"]
        if hex_val:
            result["all_colors"].setdefault(hex_val, []).append(token)

    for item in result["neutrals"]:
        hex_val = item["hex"]
        token = item["step"]
        if hex_val:
            result["all_colors"].setdefault(hex_val, []).append(token)

    for item in result["secondary_palettes"]:
        for key in ["signature", "deep", "text_safe_hex"]:
            hex_val = item.get(key, "")
            if hex_val:
                token = f"{item['name']} {key}"
                result["all_colors"].setdefault(hex_val, []).append(token)

    for item in result["rag_dots"]:
        hex_val = item["hex"]
        token = item["token"]
        if hex_val:
            result["all_colors"].setdefault(hex_val, []).append(token)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python colors_parser.py <path-to-colors.md>", file=sys.stderr)
        sys.exit(1)

    colors_md_path = sys.argv[1]

    try:
        palette_data = parse_colors_md(colors_md_path)
        print(json.dumps(palette_data, indent=2))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing colors.md: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
