"""Shared helpers for the markdown reference parsers."""

from __future__ import annotations

import re

_INLINE_MD_RE = re.compile(r"\*\*|\*|`")
_NUMBER_RE = re.compile(r"^[+\-−–]?\d+(?:\.\d+)?$")


def strip_inline_md(text: str) -> str:
    """Remove inline markdown emphasis markers (**, *, backticks) and trim."""
    return _INLINE_MD_RE.sub("", text).strip()


def parse_table_row(line: str) -> list[str]:
    """Split a markdown table row into cells with inline markdown stripped."""
    if not line.strip().startswith("|"):
        return []
    cells = line.strip().strip("|").split("|")
    return [strip_inline_md(cell) for cell in cells]


def parse_number(text: str) -> int | float | None:
    """Parse a numeric string such as "−2", "+2.4" or "0" into a number.

    Accepts the Unicode minus (U+2212) and en dash used in the reference files.
    Returns None when the text is not a plain number.
    """
    cleaned = text.strip().replace("−", "-").replace("–", "-")
    if not _NUMBER_RE.match(cleaned):
        return None
    value = float(cleaned)
    return int(value) if value.is_integer() else value
