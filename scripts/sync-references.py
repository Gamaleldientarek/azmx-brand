#!/usr/bin/env python3
"""
sync-references.py — Keep JSON reference files synchronized with their markdown counterparts.

Ensures image-tags.json stays in sync with references/image-index.md concept tags, and
recolor-prompts.json stays in sync with references/recolor-prompts.md. Runs in two modes:

  --check    Detect drift between JSON and markdown, exit non-zero if found (for CI)
  --sync     Update markdown from JSON (default), or JSON from markdown with --from-markdown

Usage:
    python3 scripts/sync-references.py --check
    python3 scripts/sync-references.py --sync
    python3 scripts/sync-references.py --sync --from-markdown

Exits 0 if synchronized, 1 if drift detected, 2 on error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Terminal colors
# --------------------------------------------------------------------------

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
RED, YELLOW, GREEN, CYAN = "\033[31m", "\033[33m", "\033[32m", "\033[36m"


# --------------------------------------------------------------------------
# File paths
# --------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_TAGS_JSON = os.path.join(ROOT, "scripts", "image-tags.json")
IMAGE_INDEX_MD = os.path.join(ROOT, "references", "image-index.md")
RECOLOR_PROMPTS_JSON = os.path.join(ROOT, "scripts", "recolor-prompts.json")
RECOLOR_PROMPTS_MD = os.path.join(ROOT, "references", "recolor-prompts.md")


# --------------------------------------------------------------------------
# Parsers: image tags
# --------------------------------------------------------------------------

def parse_image_tags_json(path: str) -> dict[str, list[str]]:
    """Parse image-tags.json into {filename: [tag1, tag2, tag3]}."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, PermissionError) as e:
        print(f"{RED}Error reading {path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"{RED}Error parsing {path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict):
        print(f"{RED}Error: {path} must be a JSON object{RESET}", file=sys.stderr)
        sys.exit(2)

    # Validate structure
    for filename, tags in data.items():
        if not isinstance(tags, list) or len(tags) != 3:
            print(f"{RED}Error: {filename} must have exactly 3 tags in {path}{RESET}", file=sys.stderr)
            sys.exit(2)

    return data


def parse_image_tags_markdown(path: str) -> dict[str, list[str]]:
    """Parse references/image-index.md table rows into {filename: [tag1, tag2, tag3]}."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, PermissionError) as e:
        print(f"{RED}Error reading {path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    tags = {}
    # Match table rows: | `filename.jpg` | tag1, tag2, tag3 | ... |
    for match in re.finditer(r'\|\s*`([^`]+\.jpg)`\s*\|\s*([^|]+?)\s*\|', content):
        filename = match.group(1)
        tags_str = match.group(2).strip()
        # Split by comma and clean whitespace
        tag_list = [t.strip() for t in tags_str.split(',')]
        if len(tag_list) == 3:
            tags[filename] = tag_list

    return tags


# --------------------------------------------------------------------------
# Parsers: recolor prompts
# --------------------------------------------------------------------------

def parse_recolor_prompts_json(path: str) -> dict:
    """Parse recolor-prompts.json into {model, note, prompts: [...]}."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, PermissionError) as e:
        print(f"{RED}Error reading {path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"{RED}Error parsing {path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    # Validate structure
    if not isinstance(data, dict):
        print(f"{RED}Error: {path} must be a JSON object{RESET}", file=sys.stderr)
        sys.exit(2)
    if "model" not in data or "note" not in data or "prompts" not in data:
        print(f"{RED}Error: {path} must have 'model', 'note', and 'prompts' fields{RESET}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data["prompts"], list):
        print(f"{RED}Error: 'prompts' must be an array in {path}{RESET}", file=sys.stderr)
        sys.exit(2)

    return data


def parse_recolor_prompts_markdown(path: str) -> dict:
    """Parse references/recolor-prompts.md into {model, note, prompts: [...]}."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, PermissionError) as e:
        print(f"{RED}Error reading {path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    # Extract model and note from the preamble
    model_match = re.search(r'\*\*Model:\*\*\s*(.+)', content)
    model = model_match.group(1).strip() if model_match else ""

    # Note is the multi-line paragraph after the first heading
    note_match = re.search(r'^For best results.+?(?=\n\n##|\n\n\*\*Model|\Z)', content, re.MULTILINE | re.DOTALL)
    note = note_match.group(0).strip() if note_match else ""

    prompts = []
    # Match each ## Header  `swatch` section
    for match in re.finditer(
        r'##\s+([^`\n]+?)\s+`(#[0-9A-Fa-f]{6})`\s*\n\n([^\n]+?)\s*\n\n```text\n(.*?)\n```',
        content,
        re.DOTALL
    ):
        label = match.group(1).strip()
        swatch = match.group(2).strip()
        summary = match.group(3).strip()
        text = match.group(4).strip()

        # Derive key from label (first word before /, lowercase)
        key = label.split("/")[0].strip().lower().replace(" ", "-")

        prompts.append({
            "key": key,
            "label": label,
            "swatch": swatch,
            "summary": summary,
            "text": text
        })

    return {"model": model, "note": note, "prompts": prompts}


# --------------------------------------------------------------------------
# Drift detection
# --------------------------------------------------------------------------

def compare_image_tags(json_tags: dict[str, list[str]], md_tags: dict[str, list[str]]) -> list[str]:
    """Compare image tags, return list of differences."""
    diffs = []

    # Check for missing/extra files
    json_files = set(json_tags.keys())
    md_files = set(md_tags.keys())

    if json_files != md_files:
        only_json = json_files - md_files
        only_md = md_files - json_files
        if only_json:
            diffs.append(f"Files only in JSON: {', '.join(sorted(only_json))}")
        if only_md:
            diffs.append(f"Files only in markdown: {', '.join(sorted(only_md))}")

    # Check tags for common files
    for filename in sorted(json_files & md_files):
        if json_tags[filename] != md_tags[filename]:
            diffs.append(
                f"{filename}:\n"
                f"  JSON: {', '.join(json_tags[filename])}\n"
                f"  Markdown: {', '.join(md_tags[filename])}"
            )

    return diffs


def compare_recolor_prompts(json_data: dict, md_data: dict) -> list[str]:
    """Compare recolor prompts, return list of differences."""
    diffs = []

    # Compare model and note
    if json_data.get("model") != md_data.get("model"):
        diffs.append(f"Model field differs:\n  JSON: {json_data.get('model')}\n  Markdown: {md_data.get('model')}")
    if json_data.get("note") != md_data.get("note"):
        diffs.append(f"Note field differs (lengths: JSON={len(json_data.get('note', ''))}, Markdown={len(md_data.get('note', ''))})")

    # Compare prompts
    json_prompts = {p["key"]: p for p in json_data.get("prompts", [])}
    md_prompts = {p["key"]: p for p in md_data.get("prompts", [])}

    if set(json_prompts.keys()) != set(md_prompts.keys()):
        only_json = set(json_prompts.keys()) - set(md_prompts.keys())
        only_md = set(md_prompts.keys()) - set(json_prompts.keys())
        if only_json:
            diffs.append(f"Prompts only in JSON: {', '.join(sorted(only_json))}")
        if only_md:
            diffs.append(f"Prompts only in markdown: {', '.join(sorted(only_md))}")

    # Compare fields for common prompts
    for key in sorted(set(json_prompts.keys()) & set(md_prompts.keys())):
        jp = json_prompts[key]
        mp = md_prompts[key]
        for field in ["label", "swatch", "summary", "text"]:
            if jp.get(field) != mp.get(field):
                diff_preview = (jp.get(field, "")[:50] + "..." if len(jp.get(field, "")) > 50 else jp.get(field, ""))
                diffs.append(f"{key}.{field} differs (JSON: '{diff_preview}'...)")

    return diffs


# --------------------------------------------------------------------------
# Sync: JSON → Markdown
# --------------------------------------------------------------------------

def sync_image_tags_to_markdown(json_tags: dict[str, list[str]], md_path: str, quiet: bool = False) -> None:
    """Update concept tags in markdown from JSON, preserving all other metadata."""
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, PermissionError) as e:
        print(f"{RED}Error reading {md_path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    def replace_tags(match):
        filename = match.group(1)
        if filename in json_tags:
            tags_str = ", ".join(json_tags[filename])
            # Preserve the rest of the row
            return f"| `{filename}` | {tags_str} |{match.group(2)}"
        return match.group(0)

    # Replace tags in table rows: | `filename.jpg` | OLD_TAGS | OTHER_COLS |
    new_content = re.sub(
        r'\|\s*`([^`]+\.jpg)`\s*\|[^|]+\|(.*?\|)',
        replace_tags,
        content
    )

    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except (PermissionError, OSError) as e:
        print(f"{RED}Error writing {md_path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    if not quiet:
        print(f"{GREEN}✓ Synced image tags to {md_path}{RESET}")


def sync_recolor_prompts_to_markdown(json_data: dict, md_path: str, quiet: bool = False) -> None:
    """Regenerate markdown from JSON."""
    prompts_md = []
    prompts_md.append("# AZMX Recolour Prompts\n")
    prompts_md.append(f"\n{json_data['note']}\n")
    prompts_md.append(f"\n**Model:** {json_data['model']}\n")
    prompts_md.append("\nFeed the source image to the model together with the prompt for the colour you want. Every prompt holds the same things constant: lighting direction, grain, the frosted highlight, composition, camera angle, and pure white staying pure white. That is what keeps a recoloured image recognisably part of the same set.\n")
    prompts_md.append("\nBrowse and copy these from the gallery too: https://gamaleldientarek.github.io/azmx-brand/#recolor\n")
    prompts_md.append("\n---\n")

    for p in json_data["prompts"]:
        prompts_md.append(f"\n## {p['label']}  `{p['swatch']}`\n")
        prompts_md.append(f"\n{p['summary']}\n")
        prompts_md.append(f"\n```text\n{p['text']}\n```\n")

    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("".join(prompts_md))
    except (PermissionError, OSError) as e:
        print(f"{RED}Error writing {md_path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    if not quiet:
        print(f"{GREEN}✓ Synced recolor prompts to {md_path}{RESET}")


# --------------------------------------------------------------------------
# Sync: Markdown → JSON
# --------------------------------------------------------------------------

def sync_image_tags_to_json(md_tags: dict[str, list[str]], json_path: str, quiet: bool = False) -> None:
    """Update JSON from markdown tags."""
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(md_tags, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")  # Trailing newline
    except (PermissionError, OSError) as e:
        print(f"{RED}Error writing {json_path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    if not quiet:
        print(f"{GREEN}✓ Synced image tags to {json_path}{RESET}")


def sync_recolor_prompts_to_json(md_data: dict, json_path: str, quiet: bool = False) -> None:
    """Update JSON from markdown."""
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(md_data, f, indent=2, ensure_ascii=False)
            f.write("\n")  # Trailing newline
    except (PermissionError, OSError) as e:
        print(f"{RED}Error writing {json_path}: {e}{RESET}", file=sys.stderr)
        sys.exit(2)

    if not quiet:
        print(f"{GREEN}✓ Synced recolor prompts to {json_path}{RESET}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync JSON reference files with markdown counterparts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/sync-references.py --check           # Detect drift, exit non-zero if found
  python3 scripts/sync-references.py --sync            # Update markdown from JSON
  python3 scripts/sync-references.py --sync --from-markdown  # Update JSON from markdown
"""
    )
    parser.add_argument("--check", action="store_true", help="Check for drift (exit 1 if found)")
    parser.add_argument("--sync", action="store_true", help="Synchronize files")
    parser.add_argument("--from-markdown", action="store_true", help="Sync from markdown to JSON (default: JSON to markdown)")
    parser.add_argument("--quiet", action="store_true", help="Suppress output (for CI)")

    args, unknown = parser.parse_known_args()

    # Validate arguments
    if unknown:
        print(f"{RED}Error: Unexpected arguments: {' '.join(unknown)}{RESET}", file=sys.stderr)
        print(f"{DIM}Usage: python3 scripts/sync-references.py [--check | --sync] [--from-markdown] [--quiet]{RESET}", file=sys.stderr)
        sys.exit(2)

    if not args.check and not args.sync:
        print(f"{RED}Error: Must specify either --check or --sync{RESET}", file=sys.stderr)
        parser.print_help()
        sys.exit(2)

    if args.check and args.sync:
        print(f"{RED}Error: Cannot use both --check and --sync{RESET}", file=sys.stderr)
        sys.exit(2)

    # Parse all files
    image_tags_json = parse_image_tags_json(IMAGE_TAGS_JSON)
    image_tags_md = parse_image_tags_markdown(IMAGE_INDEX_MD)
    recolor_json = parse_recolor_prompts_json(RECOLOR_PROMPTS_JSON)
    recolor_md = parse_recolor_prompts_markdown(RECOLOR_PROMPTS_MD)

    if args.check:
        # Drift detection mode
        has_drift = False
        image_diffs = compare_image_tags(image_tags_json, image_tags_md)
        recolor_diffs = compare_recolor_prompts(recolor_json, recolor_md)

        if image_diffs:
            has_drift = True
            if not args.quiet:
                print(f"{YELLOW}Image tags drift detected:{RESET}")
                for diff in image_diffs:
                    print(f"  {diff}")

        if recolor_diffs:
            has_drift = True
            if not args.quiet:
                print(f"{YELLOW}Recolor prompts drift detected:{RESET}")
                for diff in recolor_diffs:
                    print(f"  {diff}")

        if has_drift:
            if not args.quiet:
                print(f"\n{RED}✗ Reference files are out of sync{RESET}")
                print(f"{DIM}Run: python3 scripts/sync-references.py --sync{RESET}")
            sys.exit(1)
        else:
            if not args.quiet:
                print(f"{GREEN}✓ All reference files are synchronized{RESET}")
            sys.exit(0)

    elif args.sync:
        # Sync mode
        if args.from_markdown:
            # Markdown → JSON
            sync_image_tags_to_json(image_tags_md, IMAGE_TAGS_JSON, args.quiet)
            sync_recolor_prompts_to_json(recolor_md, RECOLOR_PROMPTS_JSON, args.quiet)
            if not args.quiet:
                print(f"{GREEN}✓ Synchronized JSON files from markdown{RESET}")
        else:
            # JSON → Markdown (default)
            sync_image_tags_to_markdown(image_tags_json, IMAGE_INDEX_MD, args.quiet)
            sync_recolor_prompts_to_markdown(recolor_json, RECOLOR_PROMPTS_MD, args.quiet)
            if not args.quiet:
                print(f"{GREEN}✓ Synchronized markdown files from JSON{RESET}")

        sys.exit(0)


if __name__ == "__main__":
    main()
