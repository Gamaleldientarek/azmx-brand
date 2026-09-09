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
import re
import sys
from typing import Any

# Concept tags are rendered verbatim into index.html — keep them to a safe charset.
TAG_RE = re.compile(r"[a-z0-9][a-z0-9 _-]{0,39}")


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
        IOError: If file cannot be read
        json.JSONDecodeError: If JSON is malformed
    """
    try:
        with open(json_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise ValueError(f"file not found: {json_path}")
    except PermissionError:
        raise ValueError(f"permission denied reading: {json_path}")
    except UnicodeDecodeError as e:
        raise ValueError(f"encoding error in {json_path}: {e}")

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
        if not all(TAG_RE.fullmatch(tag) for tag in tags):
            raise ValueError(f"tags for {filename} must match {TAG_RE.pattern!r}: {tags}")

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
        IOError: If file cannot be read
    """
    try:
        with open(markdown_path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        raise ValueError(f"file not found: {markdown_path}")
    except PermissionError:
        raise ValueError(f"permission denied reading: {markdown_path}")
    except UnicodeDecodeError as e:
        raise ValueError(f"encoding error in {markdown_path}: {e}")

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
            if not all(TAG_RE.fullmatch(tag) for tag in tags):
                raise ValueError(
                    f"line {line_num}: tags for {filename} must match {TAG_RE.pattern!r}: {tags}"
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
        IOError: If file cannot be read
        json.JSONDecodeError: If JSON is malformed
    """
    try:
        with open(json_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise ValueError(f"file not found: {json_path}")
    except PermissionError:
        raise ValueError(f"permission denied reading: {json_path}")
    except UnicodeDecodeError as e:
        raise ValueError(f"encoding error in {json_path}: {e}")

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
        IOError: If file cannot be read
    """
    try:
        with open(markdown_path, encoding="utf-8") as fh:
            content = fh.read()
    except FileNotFoundError:
        raise ValueError(f"file not found: {markdown_path}")
    except PermissionError:
        raise ValueError(f"permission denied reading: {markdown_path}")
    except UnicodeDecodeError as e:
        raise ValueError(f"encoding error in {markdown_path}: {e}")

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
        # The canonical JSON key for the White / Grey palette is white.
        if key == "white-grey":
            key = "white"

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
# Drift detection
# --------------------------------------------------------------------------

def compare_image_tags(
    json_data: dict[str, list[str]],
    markdown_data: dict[str, list[str]],
    use_color: bool = True
) -> list[str]:
    """
    Compare image tags from JSON and markdown.

    Args:
        json_data: Parsed image tags from JSON
        markdown_data: Parsed image tags from markdown
        use_color: Whether to use color in output

    Returns:
        List of difference messages (empty if no drift)
    """
    differences = []

    # Check for files only in JSON
    json_only = set(json_data.keys()) - set(markdown_data.keys())
    if json_only:
        for filename in sorted(json_only):
            differences.append(
                f"  {color_text(filename, YELLOW, use_color)}: "
                f"in JSON but not in markdown"
            )

    # Check for files only in markdown
    markdown_only = set(markdown_data.keys()) - set(json_data.keys())
    if markdown_only:
        for filename in sorted(markdown_only):
            differences.append(
                f"  {color_text(filename, YELLOW, use_color)}: "
                f"in markdown but not in JSON"
            )

    # Check for tag differences
    common_files = set(json_data.keys()) & set(markdown_data.keys())
    for filename in sorted(common_files):
        json_tags = json_data[filename]
        markdown_tags = markdown_data[filename]

        if json_tags != markdown_tags:
            differences.append(
                f"  {color_text(filename, YELLOW, use_color)}:"
            )
            differences.append(
                f"    JSON:     {', '.join(json_tags)}"
            )
            differences.append(
                f"    Markdown: {', '.join(markdown_tags)}"
            )

    return differences


def compare_recolor_prompts(
    json_data: dict[str, Any],
    markdown_data: dict[str, Any],
    use_color: bool = True
) -> list[str]:
    """
    Compare recolor prompts from JSON and markdown.

    Args:
        json_data: Parsed recolor prompts from JSON
        markdown_data: Parsed recolor prompts from markdown
        use_color: Whether to use color in output

    Returns:
        List of difference messages (empty if no drift)
    """
    differences = []

    # Compare model
    if json_data.get("model") != markdown_data.get("model"):
        differences.append(
            f"  {color_text('model', YELLOW, use_color)}: "
            f"JSON={json_data.get('model')!r}, "
            f"Markdown={markdown_data.get('model')!r}"
        )

    # Compare note
    if json_data.get("note") != markdown_data.get("note"):
        differences.append(
            f"  {color_text('note', YELLOW, use_color)}: text differs"
        )
        differences.append(
            f"    JSON:     {json_data.get('note')[:60]}..."
        )
        differences.append(
            f"    Markdown: {markdown_data.get('note')[:60]}..."
        )

    # Compare prompts
    json_prompts = {p["key"]: p for p in json_data.get("prompts", [])}
    markdown_prompts = {p["key"]: p for p in markdown_data.get("prompts", [])}

    # Check for prompts only in JSON
    json_only = set(json_prompts.keys()) - set(markdown_prompts.keys())
    if json_only:
        for key in sorted(json_only):
            differences.append(
                f"  {color_text(f'prompt {key}', YELLOW, use_color)}: "
                f"in JSON but not in markdown"
            )

    # Check for prompts only in markdown
    markdown_only = set(markdown_prompts.keys()) - set(json_prompts.keys())
    if markdown_only:
        for key in sorted(markdown_only):
            differences.append(
                f"  {color_text(f'prompt {key}', YELLOW, use_color)}: "
                f"in markdown but not in JSON"
            )

    # Check for prompt differences
    common_keys = set(json_prompts.keys()) & set(markdown_prompts.keys())
    for key in sorted(common_keys):
        json_prompt = json_prompts[key]
        markdown_prompt = markdown_prompts[key]

        prompt_diffs = []

        # Compare each field
        for field in ["label", "swatch", "summary", "text"]:
            json_val = json_prompt.get(field, "")
            markdown_val = markdown_prompt.get(field, "")

            if json_val != markdown_val:
                if field == "text":
                    # For long text, just indicate it differs
                    prompt_diffs.append(f"    {field}: text differs")
                else:
                    prompt_diffs.append(
                        f"    {field}: JSON={json_val!r}, Markdown={markdown_val!r}"
                    )

        if prompt_diffs:
            differences.append(
                f"  {color_text(f'prompt {key}', YELLOW, use_color)}:"
            )
            differences.extend(prompt_diffs)

    return differences


# --------------------------------------------------------------------------
# Sync functions
# --------------------------------------------------------------------------

def sync_image_tags_to_markdown(
    json_path: str,
    markdown_path: str,
    use_color: bool = True,
    quiet: bool = False
) -> None:
    """
    Update image-index.md tags column from image-tags.json.

    Preserves all other columns (dominant color, luminance, links) and only
    updates the "Concept tags" column with data from JSON.

    Args:
        json_path: Path to image-tags.json
        markdown_path: Path to image-index.md
        use_color: Whether to use color in output
        quiet: Whether to suppress informational output

    Raises:
        ValueError: If parsing fails or structure is invalid
    """
    # Load tags from JSON
    tags_dict = parse_image_tags_json(json_path)

    # Read existing markdown
    try:
        with open(markdown_path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        raise ValueError(f"file not found: {markdown_path}")
    except PermissionError:
        raise ValueError(f"permission denied reading: {markdown_path}")
    except UnicodeDecodeError as e:
        raise ValueError(f"encoding error in {markdown_path}: {e}")

    # Update tags in markdown tables
    output_lines = []
    in_table = False
    columns = []
    updated_count = 0

    for line in lines:
        stripped = line.rstrip()

        # Detect table header
        if stripped.startswith("| Image |"):
            in_table = True
            columns = [col.strip() for col in stripped.split("|")[1:-1]]
            output_lines.append(line)
            continue

        # Skip separator line
        if in_table and stripped.startswith("|---"):
            output_lines.append(line)
            continue

        # End of table
        if in_table and not stripped.startswith("|"):
            in_table = False
            columns = []
            output_lines.append(line)
            continue

        # Update table row
        if in_table and stripped.startswith("|"):
            cells = [cell.strip() for cell in stripped.split("|")[1:-1]]

            if len(cells) != len(columns):
                # Preserve malformed or empty rows as-is
                output_lines.append(line)
                continue

            try:
                image_idx = columns.index("Image")
                tags_idx = columns.index("Concept tags")
            except ValueError:
                # Missing required columns, preserve as-is
                output_lines.append(line)
                continue

            # Extract filename
            image_cell = cells[image_idx]
            if image_cell.startswith("`") and image_cell.endswith("`"):
                filename = image_cell[1:-1]

                # Update tags if we have data for this file
                if filename in tags_dict:
                    tags = tags_dict[filename]
                    cells[tags_idx] = ", ".join(tags)
                    updated_count += 1

            # Reconstruct line
            new_line = "| " + " | ".join(cells) + " |\n"
            output_lines.append(new_line)
        else:
            # Preserve all non-table lines as-is
            output_lines.append(line)

    # Write updated markdown
    try:
        with open(markdown_path, "w", encoding="utf-8") as fh:
            fh.writelines(output_lines)
    except PermissionError:
        raise ValueError(f"permission denied writing: {markdown_path}")
    except IOError as e:
        raise ValueError(f"I/O error writing {markdown_path}: {e}")

    if not quiet:
        print(
            f"{color_text('✓', GREEN, use_color)} "
            f"updated {updated_count} image tags in {os.path.basename(markdown_path)}"
        )


def sync_recolor_prompts_to_markdown(
    json_path: str,
    markdown_path: str,
    use_color: bool = True,
    quiet: bool = False
) -> None:
    """
    Generate recolor-prompts.md from recolor-prompts.json.

    Completely regenerates the markdown file from JSON data.

    Args:
        json_path: Path to recolor-prompts.json
        markdown_path: Path to recolor-prompts.md
        use_color: Whether to use color in output
        quiet: Whether to suppress informational output

    Raises:
        ValueError: If parsing fails or structure is invalid
    """
    # Load data from JSON
    data = parse_recolor_prompts_json(json_path)

    # Generate markdown content
    lines = [
        "# AZMX Recolor Prompts\n",
        "\n",
        f"{data['note']}\n",
        "\n",
        f"**Model:** {data['model']}\n",
        "\n",
        "---\n",
        "\n",
    ]

    # Add each prompt as a section
    for prompt in data["prompts"]:
        lines.extend([
            f"## {prompt['label']}  `{prompt['swatch']}`\n",
            "\n",
            f"{prompt['summary']}\n",
            "\n",
            "```text\n",
            f"{prompt['text']}\n",
            "```\n",
            "\n",
        ])

    # Write markdown
    try:
        with open(markdown_path, "w", encoding="utf-8") as fh:
            fh.writelines(lines)
    except PermissionError:
        raise ValueError(f"permission denied writing: {markdown_path}")
    except IOError as e:
        raise ValueError(f"I/O error writing {markdown_path}: {e}")

    if not quiet:
        print(
            f"{color_text('✓', GREEN, use_color)} "
            f"generated {os.path.basename(markdown_path)} "
            f"({len(data['prompts'])} prompts)"
        )


def sync_image_tags_to_json(
    markdown_path: str,
    json_path: str,
    use_color: bool = True,
    quiet: bool = False
) -> None:
    """
    Generate image-tags.json from image-index.md.

    Completely regenerates the JSON file from markdown data.

    Args:
        markdown_path: Path to image-index.md
        json_path: Path to image-tags.json
        use_color: Whether to use color in output
        quiet: Whether to suppress informational output

    Raises:
        ValueError: If parsing fails or structure is invalid
    """
    # Load tags from markdown
    tags_dict = parse_image_tags_markdown(markdown_path)

    # Write JSON with sorted keys for consistent output
    try:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(tags_dict, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")  # Add trailing newline
    except PermissionError:
        raise ValueError(f"permission denied writing: {json_path}")
    except IOError as e:
        raise ValueError(f"I/O error writing {json_path}: {e}")

    if not quiet:
        print(
            f"{color_text('✓', GREEN, use_color)} "
            f"generated {os.path.basename(json_path)} "
            f"({len(tags_dict)} images)"
        )


def sync_recolor_prompts_to_json(
    markdown_path: str,
    json_path: str,
    use_color: bool = True,
    quiet: bool = False
) -> None:
    """
    Generate recolor-prompts.json from recolor-prompts.md.

    Completely regenerates the JSON file from markdown data.

    Args:
        markdown_path: Path to recolor-prompts.md
        json_path: Path to recolor-prompts.json
        use_color: Whether to use color in output
        quiet: Whether to suppress informational output

    Raises:
        ValueError: If parsing fails or structure is invalid
    """
    # Load data from markdown
    data = parse_recolor_prompts_markdown(markdown_path)

    # Write JSON with consistent formatting
    try:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")  # Add trailing newline
    except PermissionError:
        raise ValueError(f"permission denied writing: {json_path}")
    except IOError as e:
        raise ValueError(f"I/O error writing {json_path}: {e}")

    if not quiet:
        print(
            f"{color_text('✓', GREEN, use_color)} "
            f"generated {os.path.basename(json_path)} "
            f"({len(data['prompts'])} prompts)"
        )


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

    # Check for unexpected positional arguments
    positional = [arg for arg in argv if not arg.startswith("-")]
    if positional:
        for arg in positional:
            print_error(f"unexpected argument: {arg}")
        print_error("this script does not accept positional arguments")
        print_error("use --help for usage information")
        return 2

    # Get file paths
    try:
        file_paths = get_file_paths()
    except Exception as e:
        print_error(f"error determining file paths: {e}")
        return 2

    # Verify files exist
    for ref_type, paths in file_paths.items():
        for file_type, path in paths.items():
            if not os.path.exists(path):
                print_error(f"file not found: {path}")
                return 2
            if not os.path.isfile(path):
                print_error(f"not a file: {path}")
                return 2
            if not os.access(path, os.R_OK):
                print_error(f"file not readable: {path}")
                return 2

    # Determine if we should use color output
    use_color = sys.stdout.isatty() and not quiet

    # Verify write permissions in sync mode
    if sync_mode:
        for ref_type, paths in file_paths.items():
            target_path = paths["markdown"] if not from_markdown else paths["json"]
            if not os.access(target_path, os.W_OK):
                print_error(f"file not writable: {target_path}")
                return 2

    # Check mode: detect and report drift
    if check_mode:
        if not quiet:
            print(color_text("sync-references: check mode", BOLD, use_color))
            print(color_text("checking for drift...", DIM, use_color))
            print()

        drift_detected = False
        all_differences = []

        # Check image-tags
        try:
            json_tags = parse_image_tags_json(file_paths["image-tags"]["json"])
            markdown_tags = parse_image_tags_markdown(file_paths["image-tags"]["markdown"])

            tag_diffs = compare_image_tags(json_tags, markdown_tags, use_color)
            if tag_diffs:
                drift_detected = True
                all_differences.append(
                    color_text("image-tags.json ↔ image-index.md", BOLD, use_color)
                )
                all_differences.extend(tag_diffs)
                all_differences.append("")  # Empty line for spacing
        except json.JSONDecodeError as e:
            print_error(f"invalid JSON in {file_paths['image-tags']['json']}: {e}")
            return 2
        except ValueError as e:
            print_error(f"error parsing image tags: {e}")
            return 2
        except UnicodeDecodeError as e:
            print_error(f"encoding error reading image tags: {e}")
            return 2
        except IOError as e:
            print_error(f"I/O error reading image tags: {e}")
            return 2
        except Exception as e:
            print_error(f"unexpected error parsing image tags: {e}")
            return 2

        # Check recolor-prompts
        try:
            json_prompts = parse_recolor_prompts_json(file_paths["recolor-prompts"]["json"])
            markdown_prompts = parse_recolor_prompts_markdown(file_paths["recolor-prompts"]["markdown"])

            prompt_diffs = compare_recolor_prompts(json_prompts, markdown_prompts, use_color)
            if prompt_diffs:
                drift_detected = True
                all_differences.append(
                    color_text("recolor-prompts.json ↔ recolor-prompts.md", BOLD, use_color)
                )
                all_differences.extend(prompt_diffs)
                all_differences.append("")  # Empty line for spacing
        except json.JSONDecodeError as e:
            print_error(f"invalid JSON in {file_paths['recolor-prompts']['json']}: {e}")
            return 2
        except ValueError as e:
            print_error(f"error parsing recolor prompts: {e}")
            return 2
        except UnicodeDecodeError as e:
            print_error(f"encoding error reading recolor prompts: {e}")
            return 2
        except IOError as e:
            print_error(f"I/O error reading recolor prompts: {e}")
            return 2
        except Exception as e:
            print_error(f"unexpected error parsing recolor prompts: {e}")
            return 2

        # Report results
        if drift_detected:
            if not quiet:
                print(color_text("✗ drift detected", RED + BOLD, use_color))
                print()
                for line in all_differences:
                    print(line)
            return 1
        else:
            if not quiet:
                print(color_text("✓ all reference files are synchronized", GREEN, use_color))
            return 0

    # Sync mode: update files
    else:
        if not quiet:
            direction = "markdown → JSON" if from_markdown else "JSON → markdown"
            print(color_text("sync-references: sync mode", BOLD, use_color))
            print(color_text(f"synchronizing {direction}...", DIM, use_color))
            print()

        # JSON → markdown sync
        if not from_markdown:
            try:
                # Sync image tags
                sync_image_tags_to_markdown(
                    file_paths["image-tags"]["json"],
                    file_paths["image-tags"]["markdown"],
                    use_color=use_color,
                    quiet=quiet
                )

                # Sync recolor prompts
                sync_recolor_prompts_to_markdown(
                    file_paths["recolor-prompts"]["json"],
                    file_paths["recolor-prompts"]["markdown"],
                    use_color=use_color,
                    quiet=quiet
                )

                if not quiet:
                    print()
                    print(color_text("✓ synchronization complete", GREEN, use_color))

                return 0

            except json.JSONDecodeError as e:
                print_error(f"invalid JSON in source file: {e}")
                return 2
            except ValueError as e:
                print_error(f"validation error during sync: {e}")
                return 2
            except UnicodeDecodeError as e:
                print_error(f"encoding error during sync: {e}")
                return 2
            except IOError as e:
                print_error(f"I/O error during sync: {e}")
                return 2
            except PermissionError as e:
                print_error(f"permission denied writing file: {e}")
                return 2
            except Exception as e:
                print_error(f"unexpected error during sync: {e}")
                return 2

        # Markdown → JSON sync
        else:
            try:
                # Sync image tags
                sync_image_tags_to_json(
                    file_paths["image-tags"]["markdown"],
                    file_paths["image-tags"]["json"],
                    use_color=use_color,
                    quiet=quiet
                )

                # Sync recolor prompts
                sync_recolor_prompts_to_json(
                    file_paths["recolor-prompts"]["markdown"],
                    file_paths["recolor-prompts"]["json"],
                    use_color=use_color,
                    quiet=quiet
                )

                if not quiet:
                    print()
                    print(color_text("✓ synchronization complete", GREEN, use_color))

                return 0

            except json.JSONDecodeError as e:
                print_error(f"invalid JSON generated or in source file: {e}")
                return 2
            except ValueError as e:
                print_error(f"validation error during sync: {e}")
                return 2
            except UnicodeDecodeError as e:
                print_error(f"encoding error during sync: {e}")
                return 2
            except IOError as e:
                print_error(f"I/O error during sync: {e}")
                return 2
            except PermissionError as e:
                print_error(f"permission denied writing file: {e}")
                return 2
            except Exception as e:
                print_error(f"unexpected error during sync: {e}")
                return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
