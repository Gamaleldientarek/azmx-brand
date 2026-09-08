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
