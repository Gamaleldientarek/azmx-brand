"""Repository hygiene guard.

Fails CI when something that should never be committed has slipped into the
tracked tree:

  * files that .gitignore says to ignore but are nevertheless tracked
  * agent / verification scratch output (verify_*.py, VERIFICATION_REPORT.md,
    .auto-claude/, .claude_settings.json, tarballs, patch files, caches, ...)
  * oversized files (> 2 MB for anything that is not an image, > 25 MB for
    anything at all)
  * text files that leak a local absolute path (/Users/...) or a GitHub token

The same checks run locally on staged files via scripts/hooks/pre-commit
(install once with `bash scripts/hooks/install.sh`). Keep the two in sync.

The whole module skips when the checkout is not a git repository (for example
when the skill is installed from a tarball).
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Patterns are matched against the repo-relative POSIX path AND against the
# basename, so `*.tgz` catches nested tarballs and `.claude` catches the file
# at the root.
SCRATCH_PATTERNS = [
    "verify_*.py",
    "test_csp_hash.py",
    "VERIFICATION_REPORT.md",
    "validation-summary.md",
    "*.tgz",
    "_*.diff",
    ".claude",
    ".claude_settings.json",
    ".auto-claude/*",
    "__pycache__",
    "__pycache__/*",
    "*.pyc",
    "node_modules/*",
]

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg", ".ico", ".bmp", ".tif", ".tiff"}
NON_IMAGE_LIMIT = 2 * 1024 * 1024
ANY_FILE_LIMIT = 25 * 1024 * 1024

# Binary-ish suffixes we never scan for text leaks.
BINARY_SUFFIXES = IMAGE_SUFFIXES | {
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".pdf", ".zip", ".gz", ".tgz",
    ".db", ".sqlite", ".mp4", ".mov", ".mp3", ".wav", ".pyc",
}

LEAK_PATTERNS = {
    "absolute /Users/ path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "GitHub token": re.compile(r"\b(?:gho_|ghp_|ghu_|ghs_|ghr_)[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}"),
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _inside_git_checkout() -> bool:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
    except (OSError, FileNotFoundError):
        return False
    return out.returncode == 0 and out.stdout.strip() == "true"


pytestmark = pytest.mark.skipif(
    not _inside_git_checkout(),
    reason="not inside a git checkout; repo hygiene checks need `git ls-files`",
)


@pytest.fixture(scope="module")
def tracked_files() -> list[str]:
    return [line for line in _git("ls-files", "-z").split("\0") if line]


def _matches_scratch(path: str) -> str | None:
    base = os.path.basename(path)
    for pattern in SCRATCH_PATTERNS:
        if fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(base, pattern):
            return pattern
        # `.auto-claude/*` should also catch deeper nesting and sub-directories
        # that appear anywhere in the tree (e.g. scripts/node_modules/x).
        if pattern.endswith("/*"):
            directory = pattern[:-2]
            if f"/{directory}/" in f"/{path}":
                return pattern
    return None


def test_no_tracked_files_that_gitignore_excludes():
    """`git ls-files -i -c --exclude-standard` lists tracked files that .gitignore
    says to ignore. Anything here was force-added or added before the ignore rule."""
    ignored = [line for line in _git("ls-files", "-i", "-c", "--exclude-standard").splitlines() if line]
    assert not ignored, (
        "Tracked files that .gitignore excludes (run `git rm --cached <file>`):\n  "
        + "\n  ".join(ignored)
    )


def test_no_scratch_files_tracked(tracked_files):
    offenders = []
    for path in tracked_files:
        pattern = _matches_scratch(path)
        if pattern:
            offenders.append(f"{path}  (matches {pattern})")
    assert not offenders, "Scratch / agent output is tracked:\n  " + "\n  ".join(offenders)


def test_no_oversized_files_tracked(tracked_files):
    offenders = []
    for path in tracked_files:
        full = REPO_ROOT / path
        if not full.is_file():
            continue  # submodule or symlink to a directory
        size = full.stat().st_size
        is_image = full.suffix.lower() in IMAGE_SUFFIXES
        if size > ANY_FILE_LIMIT:
            offenders.append(f"{path}: {size / 1024 / 1024:.1f} MB > 25 MB")
        elif not is_image and size > NON_IMAGE_LIMIT:
            offenders.append(f"{path}: {size / 1024 / 1024:.1f} MB > 2 MB (non-image)")
    assert not offenders, "Oversized files are tracked:\n  " + "\n  ".join(offenders)


def _is_text_file(full: Path) -> bool:
    if full.suffix.lower() in BINARY_SUFFIXES:
        return False
    try:
        with open(full, "rb") as fh:
            chunk = fh.read(8192)
    except OSError:
        return False
    return b"\0" not in chunk


def test_no_local_paths_or_tokens_in_tracked_text(tracked_files):
    offenders = []
    for path in tracked_files:
        full = REPO_ROOT / path
        if not full.is_file() or not _is_text_file(full):
            continue
        # This file necessarily mentions the patterns it looks for.
        if path == "tests/test_repo_hygiene.py" or path == "scripts/hooks/pre-commit":
            continue
        try:
            text = full.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for label, regex in LEAK_PATTERNS.items():
            match = regex.search(text)
            if match:
                line_no = text.count("\n", 0, match.start()) + 1
                offenders.append(f"{path}:{line_no}: {label} ({match.group(0)[:24]}...)")
    assert not offenders, "Tracked text files leak local paths or tokens:\n  " + "\n  ".join(offenders)
