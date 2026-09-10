#!/usr/bin/env python3
"""
voice_parser.py — AZMX voice and tone parser.

Extracts structured voice guidelines from references/voice-and-tone.md.

Usage:
    python scripts/parsers/voice_parser.py references/voice-and-tone.md

Outputs JSON with voice and tone guidelines including: brand language, tone rules,
dimensions, writing mechanics, principles, platform-specific voice, and checklists.
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


def extract_bullet_list(lines: list[str], start_idx: int) -> tuple[list[str], int]:
    """
    Extract a bullet list starting from start_idx.
    Returns (list_items, next_line_index).
    """
    items = []
    idx = start_idx

    while idx < len(lines):
        line = lines[idx].strip()

        # Check if it's a bullet point
        match = re.match(r"^[-*+]\s+(.+)$", line)
        if match:
            items.append(strip_inline_md(match.group(1)))
            idx += 1
        elif not line:
            # Empty line, continue to see if list resumes
            idx += 1
            if idx < len(lines) and not re.match(r"^[-*+]\s+", lines[idx].strip()):
                break
        else:
            # Not a bullet, end of list
            break

    return items, idx


def extract_numbered_list(lines: list[str], start_idx: int) -> tuple[list[dict[str, str]], int]:
    """
    Extract a numbered list with bold headings.
    Returns (list_items, next_line_index).
    Each item is {number, heading, description}.
    """
    items = []
    idx = start_idx

    while idx < len(lines):
        line = lines[idx].strip()

        # Match numbered item with optional bold heading
        match = re.match(r"^(\d+)\.\s+\*\*([^*]+)\*\*\s*(.*)$", line)
        if match:
            items.append({
                "number": match.group(1),
                "heading": match.group(2).strip(),
                "description": strip_inline_md(match.group(3))
            })
            idx += 1
        elif not line:
            idx += 1
            if idx < len(lines) and not re.match(r"^\d+\.\s+", lines[idx].strip()):
                break
        else:
            break

    return items, idx


def extract_key_value(text: str, key: str) -> str:
    """Extract value after a key pattern like '**Tagline territory:**'."""
    pattern = rf"\*\*{key}:?\*\*\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def parse_voice_md(file_path: str) -> dict[str, Any]:
    """
    Parse references/voice-and-tone.md into structured voice guidelines.

    Returns a dict with:
        - brand_language: {tagline, philosophy, boilerplate}
        - voice_summary: one-line description
        - tone_rules: list of {number, heading, description}
        - dimensions: list of {dimension, position, we_are, we_are_not}
        - calibration_examples: list of {dimension, wrong_formal, wrong_informal, azmx_voice}
        - purpose_modes: list of {mode, surfaces, goal, example}
        - writing_mechanics: list of banned patterns/words
        - universal_principles: list of {principle, description}
        - format_rules: list of {format, rules}
        - platform_voice: list of {platform, voice, guidelines}
        - strategy_superseded: list of {deck_says, azmx_voice}
        - pre_publish_checklist: list of steps
        - quick_self_check: list of questions
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"voice-and-tone.md not found at {file_path}")

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    result: dict[str, Any] = {
        "brand_language": {},
        "voice_summary": "",
        "tone_rules": [],
        "dimensions": [],
        "calibration_examples": [],
        "purpose_modes": [],
        "writing_mechanics": [],
        "universal_principles": [],
        "format_rules": [],
        "platform_voice": [],
        "strategy_superseded": [],
        "pre_publish_checklist": [],
        "quick_self_check": [],
    }

    current_section = None
    current_subsection = None
    current_table_type = None  # Track which table we're currently in
    in_table = False
    table_headers = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Track sections (H2)
        if stripped.startswith("## "):
            current_section = stripped[3:].lower()
            current_subsection = None
            current_table_type = None
            in_table = False
            i += 1
            continue

        # Track subsections (H3)
        if stripped.startswith("### "):
            current_subsection = stripped[4:].lower()
            current_table_type = None
            in_table = False
            i += 1
            continue

        # Track bold markers within sections (like **Calibration examples** or **Purpose modes:**)
        if stripped.startswith("**") and stripped.endswith(("**", ":**")):
            marker = stripped.strip("*:").lower()
            if "calibration" in marker:
                current_table_type = "calibration"
            elif "purpose" in marker:
                current_table_type = "purpose_modes"
            i += 1
            continue

        # The voice in one line section
        if current_section == "the voice in one line":
            if stripped and not stripped.startswith("#"):
                result["voice_summary"] = stripped
                current_section = None
            i += 1
            continue

        # Brand language section
        if current_section == "brand language":
            if "Tagline territory" in stripped:
                result["brand_language"]["tagline"] = extract_key_value(stripped, "Tagline territory")
            elif "Philosophy line" in stripped:
                # Extract the full line including "client-locked" part
                match = re.search(r"\*\*Philosophy line[^:]*:\*\*\s*(.+)", stripped)
                if match:
                    result["brand_language"]["philosophy"] = match.group(1).strip()
            elif "Boilerplate" in stripped:
                result["brand_language"]["boilerplate"] = extract_key_value(stripped, "Boilerplate")
            i += 1
            continue

        # Tone rules section (numbered list with bold headings)
        if current_section == "tone rules":
            if re.match(r"^\d+\.\s+\*\*", stripped):
                items, next_idx = extract_numbered_list(lines, i)
                result["tone_rules"] = items
                i = next_idx
                continue
            i += 1
            continue

        # Writing mechanics section
        if current_section == "writing mechanics (the no-ai-tells rules)":
            if stripped.startswith("-"):
                items, next_idx = extract_bullet_list(lines, i)
                result["writing_mechanics"] = items
                i = next_idx
                continue
            i += 1
            continue

        # Pre-publish checklist
        if current_section == "pre-publish checklist":
            if re.match(r"^\d+\.\s+\*\*", stripped):
                items, next_idx = extract_numbered_list(lines, i)
                result["pre_publish_checklist"] = items
                i = next_idx
                continue
            i += 1
            continue

        # Quick self-check
        if current_section == "quick self-check before shipping copy":
            if re.match(r"^\d+\.", stripped):
                items = []
                idx = i
                while idx < len(lines):
                    line = lines[idx].strip()
                    match = re.match(r"^\d+\.\s+(.+)$", line)
                    if match:
                        items.append(match.group(1))
                        idx += 1
                    elif not line:
                        idx += 1
                        if idx < len(lines) and not re.match(r"^\d+\.", lines[idx].strip()):
                            break
                    else:
                        break
                result["quick_self_check"] = items
                i = idx
                continue
            i += 1
            continue

        # Track table headers
        if "|" in stripped and (i + 1 < len(lines) and "---" in lines[i + 1]):
            table_headers = parse_table_row(stripped)
            in_table = True
            # Auto-detect table type from headers (order matters - most specific first)
            if "Wrong, one direction" in table_headers or "Wrong, the other direction" in table_headers:
                current_table_type = "calibration"
            elif "Mode" in table_headers:
                current_table_type = "purpose_modes"
            elif "Dimension" in table_headers and "Position" in table_headers:
                current_table_type = "dimensions"
            elif "Platform" in table_headers and "Voice" in table_headers:
                current_table_type = "platform"
            elif "Principle" in table_headers:
                current_table_type = "principles"
            elif "The deck says" in table_headers:
                current_table_type = "superseded"
            i += 1
            continue

        # Skip separator rows
        if stripped.startswith("|") and all(c in "-:|" for c in stripped.replace(" ", "")):
            i += 1
            continue

        # Parse table rows
        if in_table and stripped.startswith("|"):
            cells = parse_table_row(stripped)
            if not cells:
                i += 1
                continue

            # Route to appropriate parser based on current_table_type
            if current_table_type == "dimensions":
                if len(cells) >= 4 and cells[0] not in ["Dimension", ""]:
                    result["dimensions"].append({
                        "dimension": cells[0],
                        "position": cells[1],
                        "we_are": cells[2],
                        "we_are_not": cells[3],
                    })

            elif current_table_type == "calibration":
                if len(cells) >= 4 and cells[0] not in ["Dimension", ""]:
                    result["calibration_examples"].append({
                        "dimension": cells[0],
                        "wrong_formal": cells[1],
                        "wrong_informal": cells[2],
                        "azmx_voice": cells[3],
                    })

            elif current_table_type == "purpose_modes":
                if len(cells) >= 4 and cells[0] not in ["Mode", ""]:
                    result["purpose_modes"].append({
                        "mode": cells[0],
                        "surfaces": cells[1],
                        "goal": cells[2],
                        "example": cells[3],
                    })

            elif current_table_type == "principles":
                if len(cells) >= 2 and cells[0] not in ["Principle", ""]:
                    result["universal_principles"].append({
                        "principle": cells[0],
                        "description": cells[1],
                    })

            elif current_table_type == "platform":
                if len(cells) >= 3 and cells[0] not in ["Platform", ""]:
                    result["platform_voice"].append({
                        "platform": cells[0],
                        "voice": cells[1],
                        "guidelines": cells[2],
                    })

            elif current_table_type == "superseded":
                if len(cells) >= 2 and cells[0] not in ["The deck says", ""]:
                    result["strategy_superseded"].append({
                        "deck_says": cells[0],
                        "azmx_voice": cells[1],
                    })

            i += 1
            continue

        # By format section - extract format-specific rules
        if current_section == "by format":
            if stripped.startswith("-") and ":" in stripped:
                # Format-specific rule like "- **Headlines and heroes:** description"
                match = re.match(r"^-\s+\*\*([^*]+)\*\*:?\s*(.+)$", stripped)
                if match:
                    result["format_rules"].append({
                        "format": match.group(1).strip().rstrip(":"),
                        "rules": strip_inline_md(match.group(2)),
                    })
            i += 1
            continue

        i += 1

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python voice_parser.py <path-to-voice-and-tone.md>", file=sys.stderr)
        sys.exit(1)

    voice_md_path = sys.argv[1]

    try:
        voice_data = parse_voice_md(voice_md_path)
        print(json.dumps(voice_data, indent=2, ensure_ascii=False))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing voice-and-tone.md: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
