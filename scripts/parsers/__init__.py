"""
AZMX Brand API Data Parsers

This package contains parsers that extract structured data from markdown
reference files into JSON format for the versioned brand API.

Each parser is a standalone script (run by scripts/extract-api-data.py) that
reads one reference document and prints JSON to stdout. Shared helpers for
table cells and inline markdown live in markdown_utils.
"""

from .markdown_utils import parse_number, parse_table_row, strip_inline_md

__all__ = ["parse_number", "parse_table_row", "strip_inline_md"]
