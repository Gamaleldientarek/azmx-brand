#!/usr/bin/env python3
"""
prompts_parser.py — AZMX content prompts parser.

Extracts prompt templates from references/content-prompts.md and outputs
structured JSON for programmatic access.

Each prompt template is parsed with:
  - ID (kebab-case identifier)
  - Number (1-5)
  - Title
  - Description
  - Deck page reference
  - Full template text
  - Optional notes

The parser reads the markdown file at runtime and extracts templates from
fenced code blocks, preserving all formatting and placeholder brackets.

Usage:
    python3 scripts/parsers/prompts_parser.py [path-to-prompts.md]

If no path is provided, defaults to references/content-prompts.md.
Outputs JSON to stdout. Exits 1 if parsing fails.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any


# --------------------------------------------------------------------------
# Prompt extraction
# --------------------------------------------------------------------------

PROMPT_HEADING_RE = re.compile(
    r"^##\s+(\d+)\.\s+(.+?)$", re.MULTILINE
)

CODE_BLOCK_RE = re.compile(
    r"```(?:text)?\n(.*?)\n```", re.DOTALL
)

DECK_PAGE_RE = re.compile(
    r"Deck page (\d+)", re.IGNORECASE
)


def kebab_case(text: str) -> str:
    """Convert text to kebab-case identifier."""
    # Remove "The" prefix and "Prompt" suffix
    text = re.sub(r"^The\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+Prompt$", "", text, flags=re.IGNORECASE)
    # Convert to lowercase and replace spaces/special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def extract_prompts(content: str) -> list[dict[str, Any]]:
    """
    Parse content-prompts.md and extract all prompt templates.

    Returns a list of prompt dictionaries, each containing:
      - id: kebab-case identifier
      - number: prompt number (1-5)
      - title: full title text
      - description: brief description from the line after the heading
      - deck_page: source page from the strategy deck
      - template: full prompt template text
      - notes: optional notes following the code block
    """
    prompts = []

    # Split content into sections by numbered headings
    sections = []
    heading_matches = list(PROMPT_HEADING_RE.finditer(content))

    for i, match in enumerate(heading_matches):
        start = match.start()
        end = heading_matches[i + 1].start() if i + 1 < len(heading_matches) else len(content)
        section_content = content[start:end]

        number = int(match.group(1))
        title = match.group(2).strip()

        sections.append({
            "number": number,
            "title": title,
            "content": section_content
        })

    # Extract details from each section
    for section in sections:
        # Extract description (first line after heading, before the code block)
        lines = section["content"].split("\n")
        description = ""
        deck_page = None

        # Find description and deck page from lines after heading
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            if line.startswith("```"):
                break

            # Check for deck page reference
            page_match = DECK_PAGE_RE.search(line)
            if page_match:
                deck_page = page_match.group(1)

            # Description is the first non-empty line
            if not description and not line.startswith("#"):
                # Remove "Deck page X." from description if present
                description = DECK_PAGE_RE.sub("", line).strip()
                description = description.rstrip(".")

        # Extract template from code block
        template = None
        code_match = CODE_BLOCK_RE.search(section["content"])
        if code_match:
            template = code_match.group(1).rstrip()

        # Extract notes (text after the code block, before next section or end)
        notes = None
        code_end = code_match.end() if code_match else -1
        if code_end > 0:
            remaining = section["content"][code_end:].strip()
            # Remove separator lines
            remaining = re.sub(r"^-{3,}\s*$", "", remaining, flags=re.MULTILINE).strip()
            if remaining:
                notes = remaining

        prompts.append({
            "id": kebab_case(section["title"]),
            "number": section["number"],
            "title": section["title"],
            "description": description,
            "deck_page": deck_page,
            "template": template,
            "notes": notes
        })

    return prompts


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    """Parse content prompts and output JSON."""
    # Determine input file
    if len(sys.argv) > 1:
        prompts_file = sys.argv[1]
    else:
        # Default to references/content-prompts.md relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(os.path.dirname(script_dir))
        prompts_file = os.path.join(repo_root, "references", "content-prompts.md")

    # Check file exists
    if not os.path.isfile(prompts_file):
        print(f"Error: file not found: {prompts_file}", file=sys.stderr)
        return 1

    # Read and parse
    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {prompts_file}: {e}", file=sys.stderr)
        return 1

    try:
        prompts = extract_prompts(content)
    except Exception as e:
        print(f"Error parsing prompts: {e}", file=sys.stderr)
        return 1

    if not prompts:
        print("Error: no prompts found in file", file=sys.stderr)
        return 1

    # Build output
    output = {
        "source_file": os.path.basename(prompts_file),
        "total_prompts": len(prompts),
        "prompts": prompts
    }

    # Output JSON
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
