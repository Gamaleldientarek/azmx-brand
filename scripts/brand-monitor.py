#!/usr/bin/env python3
"""
brand-monitor.py — AZMX brand drift monitoring CLI.

Scans configured directories for brand deliverables (HTML, CSS, MD, SVG files),
extracts brand metrics using extract-metrics.py, and stores results in the drift
database for trend analysis.

This tool is the entry point for continuous brand monitoring. It:
  1. Discovers files in configured watch paths
  2. Extracts brand metrics (colors, fonts, spacing, tone)
  3. Stores metrics in SQLite database with timestamps
  4. Detects changes via file hashing to avoid redundant scans

Usage:
    python3 scripts/brand-monitor.py --scan DIR [--dry-run]
    python3 scripts/brand-monitor.py --config FILE [--dry-run]
    python3 scripts/brand-monitor.py --config FILE --validate-config
    python3 scripts/brand-monitor.py --scan . --dry-run

Options:
    --scan DIR              Scan a specific directory for deliverables
    --config FILE           Use configuration file (YAML) for watch paths
    --validate-config       Validate configuration file and exit
    --dry-run               Preview what would be scanned without storing results
    --verbose               Show detailed progress information
    --quiet                 Suppress progress output (errors only)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    # Minimal YAML parser fallback for simple config files
    class SimpleYAML:
        """
        Minimal YAML parser for simple configuration files.
        Only supports basic key-value pairs, lists, and nested dictionaries.
        """
        @staticmethod
        def safe_load(stream):
            """Parse a simple YAML string or file object."""
            if hasattr(stream, 'read'):
                content = stream.read()
            else:
                content = stream

            lines = content.strip().split('\n')
            result = {}
            stack = [(result, -1)]  # (dict, indent_level)
            current_list_parent = None  # (dict, key, indent)

            for i, line in enumerate(lines):
                # Skip comments and empty lines
                line_stripped = line.split('#')[0].rstrip()
                if not line_stripped:
                    continue

                # Calculate indentation
                indent = len(line) - len(line.lstrip())

                # Pop stack to correct level based on indent
                while len(stack) > 1 and stack[-1][1] >= indent:
                    stack.pop()

                # Reset list parent if we've outdented
                if current_list_parent and indent <= current_list_parent[2]:
                    current_list_parent = None

                # Handle list items
                if line_stripped.lstrip().startswith('- '):
                    value = line_stripped.lstrip()[2:].strip().strip('"').strip("'")

                    # Find the list to add to
                    if current_list_parent:
                        parent_dict, list_key, list_indent = current_list_parent
                        if list_key in parent_dict and isinstance(parent_dict[list_key], list):
                            parent_dict[list_key].append(value)
                    continue

                # Handle key-value pairs
                if ':' in line_stripped:
                    parts = line_stripped.split(':', 1)
                    key = parts[0].strip()
                    value = parts[1].strip() if len(parts) > 1 else ''
                    value = value.strip('"').strip("'")

                    current_dict = stack[-1][0]

                    if not value:
                        # Look ahead to see if next line is a list item
                        is_list = False
                        for j in range(i + 1, len(lines)):
                            next_line = lines[j].split('#')[0].rstrip()
                            if next_line:
                                if next_line.lstrip().startswith('- '):
                                    is_list = True
                                break

                        if is_list:
                            current_dict[key] = []
                            current_list_parent = (current_dict, key, indent)
                        else:
                            new_dict = {}
                            current_dict[key] = new_dict
                            stack.append((new_dict, indent))
                            current_list_parent = None
                    else:
                        # Try to convert to appropriate type
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif '.' in value and value.replace('.', '', 1).replace('-', '', 1).isdigit():
                            value = float(value)

                        current_dict[key] = value
                        current_list_parent = None

            return result

    yaml = SimpleYAML()

# Import drift database functions from drift-db.py (hyphenated filename)
try:
    drift_db_path = Path(__file__).parent / "drift-db.py"
    if not drift_db_path.exists():
        raise ImportError(f"drift-db.py not found at {drift_db_path}")

    spec = importlib.util.spec_from_file_location("drift_db", drift_db_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {drift_db_path}")

    drift_db = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drift_db)

    # Extract the functions we need
    get_connection = drift_db.get_connection
    init_database = drift_db.init_database

except Exception as e:
    print(f"Error: Could not import drift-db.py: {e}", file=sys.stderr)
    print("Make sure drift-db.py exists in the scripts directory.", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# Database Helper Functions
# --------------------------------------------------------------------------

def insert_scan(
    conn: Any,
    file_path: str,
    file_hash: str,
    scan_duration_ms: int
) -> int:
    """
    Insert a scan record into the database.
    Returns the scan_id of the inserted record.
    """
    cursor = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Try to insert, skip if duplicate (same file_path and file_hash)
    cursor.execute(
        """
        INSERT OR IGNORE INTO scans (timestamp, file_path, file_hash, scan_duration_ms)
        VALUES (?, ?, ?, ?)
        """,
        (timestamp, file_path, file_hash, scan_duration_ms)
    )

    # Get the ID (either just inserted or existing)
    cursor.execute(
        "SELECT id FROM scans WHERE file_path = ? AND file_hash = ?",
        (file_path, file_hash)
    )
    row = cursor.fetchone()
    conn.commit()

    return row[0] if row else cursor.lastrowid


def insert_metric(
    conn: Any,
    scan_id: int,
    metric_type: str,
    value: float,
    metadata: Optional[str] = None
) -> None:
    """Insert a metric record into the database."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO metrics (scan_id, metric_type, value, metadata) VALUES (?, ?, ?, ?)",
        (scan_id, metric_type, value, metadata)
    )
    conn.commit()

# --------------------------------------------------------------------------
# Configuration Loading
# --------------------------------------------------------------------------

def load_config(config_path: str) -> dict[str, Any]:
    """
    Load configuration from YAML file.
    Returns dictionary with configuration settings.

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is missing required fields
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Invalid YAML in config file: {e}")

    if config is None:
        raise ValueError("Configuration file is empty")

    return config


def validate_config(config: dict[str, Any]) -> list[str]:
    """
    Validate configuration structure and required fields.
    Returns list of validation errors (empty if valid).
    """
    errors = []

    # Check required top-level keys
    if "watch_paths" not in config:
        errors.append("Missing required field: watch_paths")
    elif not isinstance(config["watch_paths"], list):
        errors.append("watch_paths must be a list")
    elif len(config["watch_paths"]) == 0:
        errors.append("watch_paths must contain at least one path")

    # Check optional fields have correct types
    if "extensions" in config:
        if not isinstance(config["extensions"], list):
            errors.append("extensions must be a list")
        else:
            for ext in config["extensions"]:
                if not isinstance(ext, str) or not ext.startswith("."):
                    errors.append(f"Invalid extension '{ext}' - must start with '.'")

    if "skip_directories" in config and not isinstance(config["skip_directories"], list):
        errors.append("skip_directories must be a list")

    if "skip_path_patterns" in config and not isinstance(config["skip_path_patterns"], list):
        errors.append("skip_path_patterns must be a list")

    if "database" in config:
        if not isinstance(config["database"], dict):
            errors.append("database must be a dictionary")
        elif "path" in config["database"] and not isinstance(config["database"]["path"], str):
            errors.append("database.path must be a string")

    if "scan" in config:
        if not isinstance(config["scan"], dict):
            errors.append("scan must be a dictionary")
        else:
            if "timeout" in config["scan"]:
                if not isinstance(config["scan"]["timeout"], (int, float)):
                    errors.append("scan.timeout must be a number")
                elif config["scan"]["timeout"] <= 0:
                    errors.append("scan.timeout must be positive")

            if "skip_unchanged" in config["scan"]:
                if not isinstance(config["scan"]["skip_unchanged"], bool):
                    errors.append("scan.skip_unchanged must be a boolean")

    return errors


def apply_config(config: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    """
    Apply configuration settings and return (extensions, skip_dirs, skip_patterns).
    Uses defaults from module constants if not specified in config.
    """
    # Extensions
    if "extensions" in config:
        extensions = {ext.lower() for ext in config["extensions"]}
    else:
        extensions = EXTENSIONS.copy()

    # Skip directories
    if "skip_directories" in config:
        skip_dirs = set(config["skip_directories"])
    else:
        skip_dirs = SKIP_DIRS.copy()

    # Skip path patterns
    if "skip_path_patterns" in config:
        skip_patterns = set(config["skip_path_patterns"])
    else:
        skip_patterns = SKIP_PATH_PARTS.copy()

    return extensions, skip_dirs, skip_patterns


# --------------------------------------------------------------------------
# Configuration Defaults
# --------------------------------------------------------------------------

EXTENSIONS = {".html", ".htm", ".css", ".md", ".svg", ".txt"}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".cache", ".auto-claude",
}

SKIP_PATH_PARTS = {
    os.path.join("assets", "images"),
    os.path.join("assets", "fonts"),
    ".auto-claude",
}

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

# --------------------------------------------------------------------------
# File Discovery
# --------------------------------------------------------------------------

def should_skip_path(
    path: str,
    scan_root: str,
    skip_dirs: set[str],
    skip_patterns: set[str]
) -> bool:
    """
    Check if a path should be skipped based on configured exclusions.
    Only checks the path relative to the scan root.
    """
    # Get path relative to scan root
    try:
        rel_path = os.path.relpath(path, scan_root)
    except ValueError:
        # Different drives on Windows or other edge case
        rel_path = path

    parts = Path(rel_path).parts

    # Skip if any part is in skip_dirs
    for part in parts:
        if part in skip_dirs:
            return True

    # Skip if path contains any of the skip patterns
    for skip_part in skip_patterns:
        if skip_part in rel_path:
            return True

    return False


def discover_files(
    scan_dir: str,
    extensions: set[str],
    skip_dirs: set[str],
    skip_patterns: set[str],
    verbose: bool = False
) -> list[str]:
    """
    Recursively discover scannable files in a directory.
    Returns list of absolute file paths.
    """
    files = []
    scan_path = Path(scan_dir).resolve()

    if not scan_path.exists():
        print(f"Error: Directory does not exist: {scan_dir}", file=sys.stderr)
        return []

    if not scan_path.is_dir():
        print(f"Error: Not a directory: {scan_dir}", file=sys.stderr)
        return []

    for root, dirs, filenames in os.walk(scan_path):
        # Filter out skip directories in-place to prevent descent
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for filename in filenames:
            file_path = os.path.join(root, filename)

            # Check extension
            if Path(filename).suffix.lower() not in extensions:
                continue

            # Check skip patterns (relative to scan root)
            if should_skip_path(file_path, str(scan_path), skip_dirs, skip_patterns):
                continue

            files.append(file_path)

    if verbose:
        print(f"{CYAN}Discovered {len(files)} scannable files{RESET}")

    return sorted(files)


# --------------------------------------------------------------------------
# File Hashing
# --------------------------------------------------------------------------

def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of file contents."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Warning: Could not hash {file_path}: {e}", file=sys.stderr)
        return ""


# --------------------------------------------------------------------------
# Metrics Extraction
# --------------------------------------------------------------------------

def extract_metrics(file_path: str, verbose: bool = False) -> dict[str, Any] | None:
    """
    Extract brand metrics from a file using extract-metrics.py.
    Returns parsed JSON metrics or None on error.
    """
    scripts_dir = Path(__file__).parent
    extractor = scripts_dir / "extract-metrics.py"

    if not extractor.exists():
        print(f"Error: extract-metrics.py not found at {extractor}", file=sys.stderr)
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(extractor), file_path, "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            if verbose:
                print(f"Warning: extract-metrics.py failed for {file_path}", file=sys.stderr)
                print(f"  {result.stderr}", file=sys.stderr)
            return None

        metrics = json.loads(result.stdout)
        return metrics

    except subprocess.TimeoutExpired:
        print(f"Warning: Metrics extraction timed out for {file_path}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON from extract-metrics.py for {file_path}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Warning: Failed to extract metrics for {file_path}: {e}", file=sys.stderr)
        return None


# --------------------------------------------------------------------------
# Scan Processing
# --------------------------------------------------------------------------

def process_file(
    file_path: str,
    dry_run: bool = False,
    verbose: bool = False,
    conn: Any = None,
) -> bool:
    """
    Process a single file: extract metrics and store in database.
    Returns True if successfully processed, False otherwise.
    """
    rel_path = os.path.relpath(file_path)

    if dry_run:
        print(f"Would scan: {rel_path}")
        return True

    # Compute file hash
    file_hash = compute_file_hash(file_path)
    if not file_hash:
        return False

    # Extract metrics
    start_time = datetime.now(timezone.utc)
    metrics = extract_metrics(file_path, verbose=verbose)
    end_time = datetime.now(timezone.utc)

    if metrics is None:
        if verbose:
            print(f"{YELLOW}Skipped: {rel_path} (extraction failed){RESET}")
        return False

    # Calculate scan duration
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Store in database
    try:
        scan_id = insert_scan(
            conn=conn,
            file_path=rel_path,
            file_hash=file_hash,
            scan_duration_ms=duration_ms,
        )

        # Store metrics
        metrics_stored = 0

        # Color metrics
        if "color_metrics" in metrics:
            color_data = metrics["color_metrics"]
            for key, value in color_data.items():
                if isinstance(value, (int, float)):
                    insert_metric(
                        conn=conn,
                        scan_id=scan_id,
                        metric_type=f"color.{key}",
                        value=float(value),
                        metadata=None,
                    )
                    metrics_stored += 1

        # Font metrics
        if "font_metrics" in metrics:
            font_data = metrics["font_metrics"]
            for key, value in font_data.items():
                if isinstance(value, (int, float)):
                    insert_metric(
                        conn=conn,
                        scan_id=scan_id,
                        metric_type=f"font.{key}",
                        value=float(value),
                        metadata=None,
                    )
                    metrics_stored += 1

        # Spacing metrics
        if "spacing_metrics" in metrics:
            spacing_data = metrics["spacing_metrics"]
            for key, value in spacing_data.items():
                if isinstance(value, (int, float)):
                    insert_metric(
                        conn=conn,
                        scan_id=scan_id,
                        metric_type=f"spacing.{key}",
                        value=float(value),
                        metadata=None,
                    )
                    metrics_stored += 1

        # Tone metrics
        if "tone_metrics" in metrics:
            tone_data = metrics["tone_metrics"]
            for key, value in tone_data.items():
                if isinstance(value, (int, float)):
                    insert_metric(
                        conn=conn,
                        scan_id=scan_id,
                        metric_type=f"tone.{key}",
                        value=float(value),
                        metadata=None,
                    )
                    metrics_stored += 1

        if verbose:
            print(f"{GREEN}Scanned: {rel_path} ({metrics_stored} metrics stored){RESET}")
        else:
            print(f"Scanned: {rel_path}")

        return True

    except Exception as e:
        print(f"Error storing metrics for {rel_path}: {e}", file=sys.stderr)
        return False


def scan_directory(
    scan_dir: str,
    extensions: set[str],
    skip_dirs: set[str],
    skip_patterns: set[str],
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
) -> tuple[int, int]:
    """
    Scan a directory and process all discovered files.
    Returns (files_processed, files_failed) counts.
    """
    # Discover files
    files = discover_files(
        scan_dir,
        extensions=extensions,
        skip_dirs=skip_dirs,
        skip_patterns=skip_patterns,
        verbose=verbose and not quiet
    )

    if not files:
        if not quiet:
            print(f"No scannable files found in {scan_dir}")
        return 0, 0

    if dry_run:
        if not quiet:
            print(f"\n{BOLD}Dry run mode - no changes will be made{RESET}\n")

    # Initialize database connection (unless dry-run)
    conn = None
    if not dry_run:
        try:
            # Ensure database is initialized
            init_database()
            # Get connection
            conn = get_connection()
        except Exception as e:
            print(f"Error: Failed to initialize database: {e}", file=sys.stderr)
            return 0, len(files)

    # Process files
    processed = 0
    failed = 0

    try:
        for file_path in files:
            success = process_file(
                file_path=file_path,
                dry_run=dry_run,
                verbose=verbose,
                conn=conn,
            )
            if success:
                processed += 1
            else:
                failed += 1
    finally:
        if conn:
            conn.close()

    return processed, failed


# --------------------------------------------------------------------------
# CLI Interface
# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="AZMX brand drift monitoring CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1] if "Usage:" in __doc__ else "",
    )

    parser.add_argument(
        "--scan",
        metavar="DIR",
        help="Scan a specific directory for deliverables",
    )

    parser.add_argument(
        "--config",
        metavar="FILE",
        help="Use configuration file (YAML) for watch paths",
    )

    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration file and exit",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be scanned without storing results",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress information",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output (errors only)",
    )

    args = parser.parse_args()

    # Load configuration
    config = None
    extensions = EXTENSIONS
    skip_dirs = SKIP_DIRS
    skip_patterns = SKIP_PATH_PARTS
    watch_paths = []

    if args.config:
        try:
            config = load_config(args.config)

            # Validate config
            validation_errors = validate_config(config)
            if validation_errors:
                print(f"Error: Configuration validation failed:", file=sys.stderr)
                for error in validation_errors:
                    print(f"  - {error}", file=sys.stderr)
                return 1

            # If --validate-config, just validate and exit
            if args.validate_config:
                print(f"{GREEN}Configuration is valid{RESET}")
                return 0

            # Apply configuration
            extensions, skip_dirs, skip_patterns = apply_config(config)

            # Get watch paths (resolve relative to config file location)
            config_dir = Path(args.config).parent.resolve()
            watch_paths = [
                str((config_dir / path).resolve())
                for path in config["watch_paths"]
            ]

        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error loading configuration: {e}", file=sys.stderr)
            return 1

    elif args.validate_config:
        parser.error("--validate-config requires --config FILE")

    # Determine scan directories
    if args.scan:
        scan_dirs = [args.scan]
    elif watch_paths:
        scan_dirs = watch_paths
    else:
        parser.error("Must specify either --scan DIR or --config FILE")

    # Run scans
    total_processed = 0
    total_failed = 0

    for scan_dir in scan_dirs:
        if not args.quiet and len(scan_dirs) > 1:
            print(f"{BOLD}AZMX Brand Monitor{RESET}")
            print(f"Scanning: {scan_dir}\n")
        elif not args.quiet:
            print(f"{BOLD}AZMX Brand Monitor{RESET}")
            print(f"Scanning: {scan_dir}\n")

        processed, failed = scan_directory(
            scan_dir=scan_dir,
            extensions=extensions,
            skip_dirs=skip_dirs,
            skip_patterns=skip_patterns,
            dry_run=args.dry_run,
            verbose=args.verbose,
            quiet=args.quiet,
        )

        total_processed += processed
        total_failed += failed

        if not args.quiet and len(scan_dirs) > 1:
            print(f"  Processed: {processed}")
            if failed > 0:
                print(f"  Failed: {failed}")
            print()

    # Override with totals
    processed = total_processed
    failed = total_failed

    # Summary
    if not args.quiet:
        print(f"\n{BOLD}Summary{RESET}")
        print(f"Processed: {processed}")
        if failed > 0:
            print(f"Failed: {failed}")

        if not args.dry_run and processed > 0:
            print(f"\nMetrics stored in .brand-drift.db")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
