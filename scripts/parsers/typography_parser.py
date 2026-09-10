#!/usr/bin/env python3
"""
typography_parser.py — AZMX typography system parser.

Extracts structured typography data from references/design-system.md.

Usage:
    python scripts/parsers/typography_parser.py references/design-system.md

Outputs JSON with font families, weights, type scale, and usage rules.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .markdown_utils import parse_number, parse_table_row, strip_inline_md
except ImportError:  # run directly as a script
    from markdown_utils import parse_number, parse_table_row, strip_inline_md


def parse_typography_section(content: str) -> dict[str, Any]:
    """
    Parse the Typography section from design-system.md.

    Returns a dict with:
        - families: list of {role, family, variable, variable_id, notes}
        - weights: list of {weight, variable_id}
        - type_scale: list of {role, font, size, line_height, weight, tracking (number, px), case_style}
        - rules: list of usage rules
        - bilingual_note: string
    """
    lines = content.splitlines()

    result: dict[str, Any] = {
        "families": [],
        "weights": [],
        "type_scale": [],
        "rules": [],
        "bilingual_note": "",
    }

    current_section = None
    in_table = False
    table_headers = []

    # Find the Typography section
    typography_start = -1
    for i, line in enumerate(lines):
        if line.strip() == "## 3. Typography":
            typography_start = i
            break

    if typography_start == -1:
        return result

    # Find the end of Typography section (next ## heading)
    typography_end = len(lines)
    for i in range(typography_start + 1, len(lines)):
        if lines[i].strip().startswith("## ") and not lines[i].strip().startswith("## 3."):
            typography_end = i
            break

    # Parse only the Typography section
    for i in range(typography_start, typography_end):
        line = lines[i]
        stripped = line.strip()

        # Track subsections
        if stripped.startswith("### "):
            current_section = stripped[4:].lower()
            in_table = False
            continue

        # Track table headers
        if "|" in stripped and i + 1 < len(lines) and "---" in lines[i + 1]:
            table_headers = parse_table_row(stripped)
            in_table = True
            continue

        # Skip separator rows
        if stripped.startswith("|") and all(c in "-:|" for c in stripped.replace(" ", "")):
            continue

        # Parse table rows
        if not in_table or not stripped.startswith("|"):
            in_table = False

            # Capture rules of voice as bullet points
            if current_section == "3.4 rules of voice":
                if stripped.startswith("- **"):
                    result["rules"].append(strip_inline_md(stripped[2:]))

            # Capture bilingual note (skip headings and horizontal rules)
            if current_section == "3.5 bilingual note":
                if stripped and not stripped.startswith("#") and not re.fullmatch(r"-{3,}", stripped):
                    result["bilingual_note"] += strip_inline_md(stripped) + " "

            continue

        cells = parse_table_row(stripped)
        if not cells:
            continue

        # Extract data based on current section
        if current_section == "3.1 families":
            if len(cells) >= 4:
                result["families"].append({
                    "role": cells[0],
                    "family": cells[1],
                    "variable": cells[2] if len(cells) > 2 else "",
                    "variable_id": cells[3] if len(cells) > 3 else "",
                    "notes": cells[4] if len(cells) > 4 else "",
                })

        elif current_section == "3.2 weights":
            if len(cells) >= 2:
                result["weights"].append({
                    "weight": cells[0],
                    "variable_id": cells[1],
                })

        elif current_section == "3.3 type scale":
            if len(cells) >= 6:
                # Parse size/line-height (e.g., "168 / 156")
                size_line = cells[2].split("/")
                size = size_line[0].strip() if len(size_line) > 0 else ""
                line_height = size_line[1].strip() if len(size_line) > 1 else ""

                # Parse tracking (e.g., "−2 px" or "+2.4 px") into a number
                tracking = parse_number(re.sub(r"\s*px\s*", "", cells[4]))

                result["type_scale"].append({
                    "role": cells[0],
                    "font": cells[1],
                    "size": size,
                    "line_height": line_height,
                    "weight": cells[3],
                    "tracking": tracking,
                    "case_style": cells[5] if len(cells) > 5 else "",
                })

    # Clean up bilingual note
    result["bilingual_note"] = result["bilingual_note"].strip()

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python typography_parser.py <path-to-design-system.md>", file=sys.stderr)
        sys.exit(1)

    design_system_path = sys.argv[1]

    try:
        path = Path(design_system_path)
        if not path.exists():
            raise FileNotFoundError(f"design-system.md not found at {design_system_path}")

        content = path.read_text(encoding="utf-8")
        typography_data = parse_typography_section(content)
        print(json.dumps(typography_data, indent=2, ensure_ascii=False))

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing typography from design-system.md: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
