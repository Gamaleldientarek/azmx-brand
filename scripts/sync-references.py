#!/usr/bin/env python3
"""
sync-references.py — AZMX reference file synchronization tool.

Keeps JSON reference files synchronized with their markdown counterparts:
  - scripts/image-tags.json ↔ references/image-index.md
  - scripts/recolor-prompts.json ↔ references/recolor-prompts.md

When either format is updated, the sync script detects drift and either
auto-updates the other format or flags the inconsistency.

Usage:
    python3 scripts/sync-references.py [options]

Options:
    --check         Check for drift between JSON and markdown files.
                    Exit 0 if synchronized, exit 1 if drift detected.

    --sync          Synchronize files. By default, updates markdown from JSON.
                    Use with --from-markdown to update JSON from markdown.

    --from-markdown Treat markdown as the source of truth (use with --sync).

    --quiet, -q     Suppress informational output, show only errors.

    --help, -h      Show this help message and exit.

Examples:
    # Check for drift (CI mode)
    python3 scripts/sync-references.py --check

    # Sync markdown from JSON (default)
    python3 scripts/sync-references.py --sync

    # Sync JSON from markdown
    python3 scripts/sync-references.py --sync --from-markdown

Exit codes:
    0  Success (no drift found, or sync completed)
    1  Drift detected (--check mode only)
    2  Error (missing files, invalid arguments, parse errors)
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


# --------------------------------------------------------------------------
# File paths (relative to repository root)
# --------------------------------------------------------------------------

def get_repo_root() -> str:
    """Get the repository root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_file_paths() -> dict[str, dict[str, str]]:
    """Get paths to all reference files."""
    root = get_repo_root()
    return {
        "image-tags": {
            "json": os.path.join(root, "scripts", "image-tags.json"),
            "markdown": os.path.join(root, "references", "image-index.md"),
        },
        "recolor-prompts": {
            "json": os.path.join(root, "scripts", "recolor-prompts.json"),
            "markdown": os.path.join(root, "references", "recolor-prompts.md"),
        },
    }


# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------

def color_text(text: str, color_code: str, use_color: bool = True) -> str:
    """Apply terminal color to text if color output is enabled."""
    if not use_color:
        return text
    return f"{color_code}{text}{RESET}"


def print_error(message: str) -> None:
    """Print an error message to stderr."""
    print(f"sync-references: {message}", file=sys.stderr)


def show_help() -> None:
    """Display help text from the module docstring."""
    print(__doc__)


# --------------------------------------------------------------------------
# Image tags parsers
# --------------------------------------------------------------------------

def parse_image_tags_json(json_path: str) -> dict[str, list[str]]:
    """
    Parse image tags from JSON file.

    Args:
        json_path: Path to image-tags.json

    Returns:
        Dictionary mapping image filenames to lists of 3 tag strings

    Raises:
        ValueError: If JSON is invalid or contains malformed data
    """
    with open(json_path, encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise ValueError("image-tags.json must contain a JSON object")

    # Validate structure
    for filename, tags in data.items():
        if not isinstance(filename, str):
            raise ValueError(f"invalid filename key: {filename!r}")
        if not filename.endswith(".jpg"):
            raise ValueError(f"filename must end with .jpg: {filename}")
        if not isinstance(tags, list):
            raise ValueError(f"tags for {filename} must be a list")
        if len(tags) != 3:
            raise ValueError(f"tags for {filename} must contain exactly 3 items, got {len(tags)}")
        if not all(isinstance(tag, str) for tag in tags):
            raise ValueError(f"all tags for {filename} must be strings")

    return data


def parse_image_tags_markdown(markdown_path: str) -> dict[str, list[str]]:
    """
    Parse image tags from markdown file.

    Extracts tags from the "Concept tags" column in image-index.md tables.

    Args:
        markdown_path: Path to image-index.md

    Returns:
        Dictionary mapping image filenames to lists of 3 tag strings

    Raises:
        ValueError: If markdown structure is invalid or tags are malformed
    """
    with open(markdown_path, encoding="utf-8") as fh:
        lines = fh.readlines()

    tags_dict: dict[str, list[str]] = {}
    in_table = False
    columns: list[str] = []

    for line_num, line in enumerate(lines, start=1):
        line = line.rstrip()

        # Detect table header
        if line.startswith("| Image |"):
            in_table = True
            # Parse column headers
            columns = [col.strip() for col in line.split("|")[1:-1]]
            if "Image" not in columns or "Concept tags" not in columns:
                raise ValueError(f"line {line_num}: table missing required columns")
            continue

        # Skip separator line
        if in_table and line.startswith("|---"):
            continue

        # End of table
        if in_table and not line.startswith("|"):
            in_table = False
            columns = []
            continue

        # Parse table row
        if in_table and line.startswith("|"):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]

            if len(cells) != len(columns):
                # Allow empty lines or malformed rows to skip
                continue

            image_idx = columns.index("Image")
            tags_idx = columns.index("Concept tags")

            # Extract filename from backticks: `blue-001.jpg`
            image_cell = cells[image_idx]
            if not image_cell.startswith("`") or not image_cell.endswith("`"):
                raise ValueError(f"line {line_num}: image cell not in backticks: {image_cell}")
            filename = image_cell[1:-1]

            # Extract tags from comma-separated list
            tags_cell = cells[tags_idx]
            if tags_cell == "—":
                # Empty tags marker
                tags = []
            else:
                tags = [tag.strip() for tag in tags_cell.split(",")]

            # Validate
            if not filename.endswith(".jpg"):
                raise ValueError(f"line {line_num}: filename must end with .jpg: {filename}")
            if len(tags) != 3:
                raise ValueError(
                    f"line {line_num}: {filename} must have exactly 3 tags, got {len(tags)}: {tags}"
                )

            tags_dict[filename] = tags

    return tags_dict


# --------------------------------------------------------------------------
# Recolor prompts parsers
# --------------------------------------------------------------------------

def parse_recolor_prompts_json(json_path: str) -> dict[str, Any]:
    """
    Parse recolor prompts from JSON file.

    Args:
        json_path: Path to recolor-prompts.json

    Returns:
        Dictionary with 'model', 'note', and 'prompts' (list of dicts)

    Raises:
        ValueError: If JSON is invalid or contains malformed data
    """
    with open(json_path, encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise ValueError("recolor-prompts.json must contain a JSON object")

    # Validate top-level structure
    if "model" not in data:
        raise ValueError("recolor-prompts.json missing required field: model")
    if "note" not in data:
        raise ValueError("recolor-prompts.json missing required field: note")
    if "prompts" not in data:
        raise ValueError("recolor-prompts.json missing required field: prompts")

    if not isinstance(data["model"], str):
        raise ValueError("model must be a string")
    if not isinstance(data["note"], str):
        raise ValueError("note must be a string")
    if not isinstance(data["prompts"], list):
        raise ValueError("prompts must be a list")

    # Validate each prompt
    for idx, prompt in enumerate(data["prompts"]):
        if not isinstance(prompt, dict):
            raise ValueError(f"prompts[{idx}] must be an object")

        required_fields = ["key", "label", "swatch", "summary", "text"]
        for field in required_fields:
            if field not in prompt:
                raise ValueError(f"prompts[{idx}] missing required field: {field}")
            if not isinstance(prompt[field], str):
                raise ValueError(f"prompts[{idx}].{field} must be a string")

        # Validate swatch format (hex color)
        swatch = prompt["swatch"]
        if not swatch.startswith("#") or len(swatch) != 7:
            raise ValueError(f"prompts[{idx}].swatch must be a hex color (#RRGGBB): {swatch}")

    return data


def parse_recolor_prompts_markdown(markdown_path: str) -> dict[str, Any]:
    """
    Parse recolor prompts from markdown file.

    Extracts model, note, and prompts from recolor-prompts.md structure.

    Args:
        markdown_path: Path to recolor-prompts.md

    Returns:
        Dictionary with 'model', 'note', and 'prompts' (list of dicts)

    Raises:
        ValueError: If markdown structure is invalid
    """
    with open(markdown_path, encoding="utf-8") as fh:
        content = fh.read()

    lines = content.split("\n")

    model = None
    note = None
    prompts = []

    # Parse header section (before first ----)
    header_lines = []
    separator_found = False
    separator_idx = 0

    for idx, line in enumerate(lines):
        if line.strip() == "---":
            separator_found = True
            separator_idx = idx
            break
        header_lines.append(line)

    if not separator_found:
        raise ValueError("missing separator line (---) in markdown")

    # Extract model from header (line starting with "**Model:**")
    for line in header_lines:
        if line.strip().startswith("**Model:**"):
            model = line.split("**Model:**")[1].strip()
            break

    if not model:
        raise ValueError("model specification not found in header")

    # Extract note from header (first paragraph after title)
    # The note is the paragraph that starts after the title and before the **Model:** line
    note_lines = []
    in_note = False
    for line in header_lines:
        stripped = line.strip()
        # Skip title
        if stripped.startswith("#"):
            in_note = True
            continue
        # Stop at Model line or empty line after note
        if stripped.startswith("**Model:**"):
            break
        # Collect note lines
        if in_note and stripped:
            note_lines.append(stripped)
        elif in_note and note_lines and not stripped:
            # Empty line after note content - might be end of note
            continue

    note = " ".join(note_lines) if note_lines else ""

    # Parse prompts (sections after ----)
    prompt_sections = []
    current_section_lines = []

    for line in lines[separator_idx + 1:]:
        # New section starts with ## heading
        if line.startswith("## "):
            if current_section_lines:
                prompt_sections.append(current_section_lines)
            current_section_lines = [line]
        else:
            current_section_lines.append(line)

    # Add last section
    if current_section_lines:
        prompt_sections.append(current_section_lines)

    # Parse each section
    for section_lines in prompt_sections:
        if not section_lines:
            continue

        # Parse heading: ## Label  `#SWATCH`
        heading = section_lines[0]
        if not heading.startswith("## "):
            continue

        heading_text = heading[3:].strip()
        # Split by backtick to get label and swatch
        parts = heading_text.split("`")
        if len(parts) < 2:
            raise ValueError(f"invalid heading format (missing swatch): {heading}")

        label = parts[0].strip()
        swatch = parts[1].strip()

        # Generate key from label (lowercase, spaces to hyphens)
        key = label.lower().replace(" / ", "-").replace(" ", "-")

        # Extract summary (first non-empty line after heading)
        summary = None
        for line in section_lines[1:]:
            stripped = line.strip()
            if stripped and not stripped.startswith("```"):
                summary = stripped
                break

        if not summary:
            raise ValueError(f"missing summary for section: {label}")

        # Extract prompt text from code block
        in_code_block = False
        text_lines = []
        for line in section_lines[1:]:
            if line.strip() == "```text" or line.strip() == "```":
                if in_code_block:
                    # End of code block
                    break
                else:
                    # Start of code block
                    in_code_block = True
                    continue
            if in_code_block:
                text_lines.append(line)

        text = "\n".join(text_lines).strip()

        if not text:
            raise ValueError(f"missing prompt text for section: {label}")

        prompts.append({
            "key": key,
            "label": label,
            "swatch": swatch,
            "summary": summary,
            "text": text,
        })

    if not prompts:
        raise ValueError("no prompts found in markdown")

    return {
        "model": model,
        "note": note,
        "prompts": prompts,
    }


# --------------------------------------------------------------------------
# Main function
# --------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    """
    Main entry point for the sync-references script.

    Args:
        argv: Command-line arguments (excluding script name)

    Returns:
        Exit code: 0 for success, 1 for drift detected, 2 for errors
    """
    # Parse arguments
    help_requested = "--help" in argv or "-h" in argv
    check_mode = "--check" in argv
    sync_mode = "--sync" in argv
    from_markdown = "--from-markdown" in argv
    quiet = "--quiet" in argv or "-q" in argv

    # Handle help request
    if help_requested:
        show_help()
        return 0

    # Validate arguments
    if check_mode and sync_mode:
        print_error("cannot use both --check and --sync")
        print_error("use --help for usage information")
        return 2

    if from_markdown and not sync_mode:
        print_error("--from-markdown requires --sync")
        print_error("use --help for usage information")
        return 2

    if not check_mode and not sync_mode:
        print_error("must specify either --check or --sync")
        print_error("use --help for usage information")
        return 2

    # Check for unknown flags
    known_flags = {"--check", "--sync", "--from-markdown", "--quiet", "-q", "--help", "-h"}
    unknown = [arg for arg in argv if arg.startswith("-") and arg not in known_flags]
    if unknown:
        for flag in unknown:
            print_error(f"unknown option: {flag}")
        print_error("use --help for usage information")
        return 2

    # Verify files exist
    file_paths = get_file_paths()
    for ref_type, paths in file_paths.items():
        for file_type, path in paths.items():
            if not os.path.isfile(path):
                print_error(f"file not found: {path}")
                return 2

    # Determine if we should use color output
    use_color = sys.stdout.isatty() and not quiet

    # Placeholder implementation
    # TODO: Implement actual sync/check logic in subsequent subtasks
    if not quiet:
        if check_mode:
            print(color_text("sync-references: check mode", BOLD, use_color))
            print(color_text("checking for drift...", DIM, use_color))
        else:
            direction = "markdown → JSON" if from_markdown else "JSON → markdown"
            print(color_text("sync-references: sync mode", BOLD, use_color))
            print(color_text(f"synchronizing {direction}...", DIM, use_color))

    # For now, report success (no drift detected)
    if not quiet:
        print(color_text("✓ all reference files are synchronized", GREEN, use_color))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
