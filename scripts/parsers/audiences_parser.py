#!/usr/bin/env python3
"""
audiences_parser.py — AZMX audiences and messaging parser.

Extracts structured audience personas from references/audiences-and-messaging.md.

Usage:
    python scripts/parsers/audiences_parser.py references/audiences-and-messaging.md

Outputs JSON with audience personas including: persona name, motion (B2G/B2B/B2C),
brands served, pain points, and core messaging.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    from .markdown_utils import parse_table_row, strip_inline_md
except ImportError:  # run directly as a script
    from markdown_utils import parse_table_row, strip_inline_md


def parse_audiences_md(file_path: str) -> dict[str, Any]:
    """
    Parse references/audiences-and-messaging.md into structured audience data.

    Returns a dict with:
        - personas: list of {name, motion, brands, pain_points, core_message}
        - internal_audiences: list of {segment, needs, core_message}
        - external_motions: list of {motion, brands, needs, core_message}
        - brands: list of {name, description, motions}
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"audiences-and-messaging.md not found at {file_path}")

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    result: dict[str, Any] = {
        "personas": [],
        "internal_audiences": [],
        "external_motions": [],
        "brands": [],
    }

    current_section = None
    current_motion = None  # Track B2G, B2B, or B2C
    in_table = False
    table_headers = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Track H2 sections
        if stripped.startswith("## "):
            current_section = stripped[3:].lower()
            current_motion = None
            in_table = False
            table_headers = []
            i += 1
            continue

        # Track H3 subsections - these often indicate the motion
        if stripped.startswith("### "):
            subsection = stripped[4:].strip()
            # Extract motion from subsection like "B2G — government leaders..."
            if subsection.startswith("B2G"):
                current_motion = "B2G"
            elif subsection.startswith("B2B"):
                current_motion = "B2B"
            elif subsection.startswith("B2C"):
                current_motion = "B2C"
            else:
                current_motion = None
            i += 1
            continue

        # Track table headers
        if "|" in stripped and (i + 1 < len(lines) and "---" in lines[i + 1]):
            table_headers = parse_table_row(stripped)
            in_table = True
            i += 1
            continue

        # Skip separator rows
        if stripped.startswith("|") and all(c in "-:|" for c in stripped.replace(" ", "")):
            i += 1
            continue

        # Parse table rows based on current section
        if in_table and stripped.startswith("|"):
            cells = parse_table_row(stripped)
            if not cells or cells[0] in ["Brand", "Persona", "Segment", "Motion", "Tag", ""]:
                i += 1
                continue

            # Parse "The five brands" section
            if current_section == "the five brands":
                # Only parse the first table (avoid the "Brand to audience matrix")
                if "What it is" in table_headers and len(cells) >= 3:
                    result["brands"].append({
                        "name": cells[0],
                        "description": cells[1],
                        "motions": [m.strip() for m in cells[2].split("·") if m.strip()],
                    })

            # Parse internal audiences
            elif current_section == "internal audiences":
                if len(cells) >= 3:
                    result["internal_audiences"].append({
                        "segment": cells[0],
                        "needs": cells[1],
                        "core_message": cells[2],
                    })

            # Parse external motions
            elif current_section == "external motions":
                if len(cells) >= 4:
                    result["external_motions"].append({
                        "motion": cells[0],
                        "brands": [b.strip() for b in cells[1].split("·") if b.strip()],
                        "needs": cells[2],
                        "core_message": cells[3],
                    })

            # Parse persona tables under "The eight personas"
            elif current_section == "the eight personas" and current_motion:
                if len(cells) >= 4:
                    result["personas"].append({
                        "name": cells[0],
                        "motion": current_motion,
                        "brands": [b.strip() for b in cells[1].split("·") if b.strip()],
                        "pain_points": cells[2],
                        "core_message": cells[3],
                    })

            i += 1
            continue

        i += 1

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python audiences_parser.py <path-to-audiences-and-messaging.md>", file=sys.stderr)
        sys.exit(1)

    audiences_md_path = sys.argv[1]

    try:
        audiences_data = parse_audiences_md(audiences_md_path)
        print(json.dumps(audiences_data, indent=2, ensure_ascii=False))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing audiences-and-messaging.md: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
