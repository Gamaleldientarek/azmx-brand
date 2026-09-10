#!/usr/bin/env python3
"""
brand-check.py — AZMX brand linter.

Checks .html / .css / .md / .svg files against the AZMX brand system:

  1. Hex colours outside the legal palette (nearest legal token suggested)
  2. Non-brand font-family declarations
  3. font-style: italic / oblique  (the serif has no italic; it renders faux-slanted)
  4. padding / margin / gap px values off the 8-16-24-40-64-96-128-160 scale
  5. Electric #001AFF as text on a dark surface, or as a large fill behind text
  6. Chevron / arrow art used as background decoration or at low opacity
  7. RTL (Right-to-Left) violations in Arabic email HTML:
     - Missing dir="rtl" on <table> or <td> elements
     - Chevrons (‹, ›, <, >) not wrapped in dir="ltr" spans
     - letter-spacing applied to Arabic text (breaks kashida)
     - Missing text-align:right in RTL context

  7. Emojis in prose content (when --copy flag is enabled)
  8. Hashtag counting per post with 3-max validation (when --copy flag is enabled)
  9. Banned intensifiers and corporate jargon (when --copy flag is enabled)
  10. AI-tell patterns: em-dash overuse, triads, exclamation marks, hedging (when --copy flag is enabled)

The legal palette is parsed from references/colors.md AT RUNTIME, so the linter
never goes stale when the brand changes. When --brand is specified, the linter
loads config/sub-brands/NAME.json (validated against
schemas/sub-brand-config.schema.json when jsonschema is installed), merges its
custom primitives into the palette and accepts its typography_overrides as
brand fonts for that run. An unknown name exits 2 and lists the available brands.

extract-metrics.py imports the palette parser, CSS parser and tone rule lists
from this file — it is the single source of truth for those rules.

Usage:
    python3 scripts/brand-check.py [file-or-dir ...] [OPTIONS]

Options:
    --quiet, -q       Suppress header and summary output
    --brand NAME      Add the selected sub-brand palette (colab, majarah, clix, anatomi)
    --copy            Enable prose/copy validation (emojis, hashtags, jargon, AI-tell patterns)
    --json            Output detailed findings as JSON (legacy; prefer --format json)
    --fix             Include word replacement suggestions for banned intensifiers
    --report          Output an aggregated compliance summary instead of detailed findings
    --format FORMAT   Output format: text, json, html, or markdown (default: text)
    --output PATH     Write report to file instead of stdout
    --with-trends     Include trend analysis comparing current vs historical reports (JSON format only)
    --save-history    Save current report to .brand-reports/ for future trend comparisons
    --help, -h        Show this help message

With no paths it scans the whole repo. Exits 1 if any blocker was found.
The --report flag outputs an aggregated compliance summary with statistics by severity,
violation type, and affected files.
The --format html flag generates a branded HTML report following AZMX design guidelines.
The --format markdown flag generates a markdown report.
The --with-trends flag adds historical comparison data to JSON output and saves the current
report for future trend analysis.
"""

from __future__ import annotations

import glob
import argparse
import bisect
import json
import os
import re
import sys
from datetime import datetime
from typing import NoReturn

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

SPACING_SCALE = (8, 16, 24, 40, 64, 96, 128, 160)

BRAND_FAMILIES = {
    "thmanyah serif display",
    "azm x",
    "azm x variable",
}

# Generic / keyword families that are always acceptable as a fallback tail.
GENERIC_FAMILIES = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy",
    "system-ui", "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded",
    "math", "emoji", "fangsong",
    "inherit", "initial", "unset", "revert", "revert-layer", "none",
}

SPACING_PROPS = re.compile(
    r"^(padding|margin)(-(top|right|bottom|left|inline|block)"
    r"(-(start|end))?)?$|^(row-|column-|grid-|grid-row-|grid-column-)?gap$"
)

CHEVRON_WORD = re.compile(r"chevron|caret|(?<![a-z])arrow", re.I)

# RTL validation patterns
# Detects Arabic script characters (basic Arabic block)
ARABIC_CHAR = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿ]")

# Left-pointing chevron (U+2039) and similar directional marks
LEFT_CHEVRON = re.compile(r"[‹←⇠⇽⬅]")  # ‹ ← ⇠ ⇽ ⬅

# Right-pointing chevron (should be wrapped in dir="ltr" in RTL context)
RIGHT_CHEVRON = re.compile(r"[›→⇢⇾➡]")  # › → ⇢ ⇾ ➡

# Detect <table> or <td> tags
TABLE_TAG = re.compile(r"<(table|td)\b([^>]*)>", re.I)

# Banned intensifiers and corporate jargon that dilute brand voice.
# This is the single source of truth for the tone rules: extract-metrics.py
# imports these regexes from here, so keep the list in one place.
BANNED_INTENSIFIER = re.compile(
    r"\b(truly|leverage|robust|seamlessly|effortlessly|empower|elevate|unlock|"
    r"delve|synergy|paradigm|"
    r"utilize|utilise|proactive|innovative|disruptive|game-?changing|"
    r"cutting-?edge|world-?class|best-?in-?class|revolutionary|"
    r"transformative|ecosystem|bandwidth|circle back|deep dive|"
    r"low-?hanging fruit|move the needle|touch base)\b",
    re.I
)

# Word suggestion engine: maps banned words to better alternatives
WORD_SUGGESTIONS = {
    "truly": ["genuinely", "actually", "really"],
    "leverage": ["use", "apply", "employ"],
    "robust": ["strong", "reliable", "solid"],
    "seamlessly": ["smoothly", "easily", "simply"],
    "effortlessly": ["easily", "simply", "quickly"],
    "empower": ["enable", "allow", "help"],
    "elevate": ["improve", "raise", "lift"],
    "unlock": ["open", "enable", "release"],
    "delve": ["look into", "examine", "explore"],
    "synergy": ["collaboration", "cooperation", "teamwork"],
    "paradigm": ["model", "approach", "pattern"],
    "utilize": ["use", "apply", "employ"],
    "utilise": ["use", "apply", "employ"],
    "proactive": ["forward-thinking", "prepared", "anticipatory"],
    "innovative": ["new", "novel", "original"],
    "disruptive": ["transformative", "groundbreaking", "novel"],
    "game-changing": ["significant", "important", "major"],
    "game changing": ["significant", "important", "major"],
    "cutting-edge": ["advanced", "modern", "latest"],
    "cutting edge": ["advanced", "modern", "latest"],
    "world-class": ["excellent", "outstanding", "superior"],
    "world class": ["excellent", "outstanding", "superior"],
    "best-in-class": ["leading", "top-tier", "superior"],
    "best in class": ["leading", "top-tier", "superior"],
    "revolutionary": ["groundbreaking", "transformative", "novel"],
    "transformative": ["significant", "impactful", "meaningful"],
    "ecosystem": ["environment", "platform", "system"],
    "bandwidth": ["capacity", "time", "resources"],
    "circle back": ["follow up", "return to", "revisit"],
    "deep dive": ["analysis", "examination", "investigation"],
    "low-hanging fruit": ["easy wins", "quick wins", "opportunities"],
    "low hanging fruit": ["easy wins", "quick wins", "opportunities"],
    "move the needle": ["make progress", "create impact", "advance"],
    "touch base": ["connect", "check in", "follow up"],
}

# Elements whose inline background is *data* (a sampled image colour, a RAG
# swatch, a palette chip) rather than a brand styling decision. Without this,
# a swatch gallery reports hundreds of false "off-palette" hits.
SWATCH_CLASS = re.compile(
    r"\b(sw|swatch|swatches|chip|dot|pdot|cdot|hexdot|color-?chip|color-?dot|"
    r"colour-?chip|colour-?dot|legend-?key)\b"
)

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".cache",
}
# Binary-ish / generated asset trees that hold no hand-authored CSS.
SKIP_PATH_PARTS = {
    os.path.join("assets", "images"),
    os.path.join("assets", "fonts"),
}

EXTENSIONS = {".html", ".htm", ".css", ".md", ".svg"}

SEVERITY_ORDER = {"blocker": 0, "major": 1, "minor": 2}

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
SEV_COLOR = {"blocker": "\033[31m", "major": "\033[33m", "minor": "\033[36m"}


# --------------------------------------------------------------------------
# Palette, parsed from references/colors.md at runtime
# --------------------------------------------------------------------------

HEX_RE = re.compile(r"#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3,4})\b")

# Emoji detection: matches Unicode emoji characters
# Covers common emoji ranges including:
# - Emoticons (U+1F600-U+1F64F)
# - Symbols & Pictographs (U+1F300-U+1F5FF)
# - Transport & Map (U+1F680-U+1F6FF)
# - Supplemental Symbols (U+1F900-U+1F9FF)
# - Other common emoji ranges
EMOJI_RE = re.compile(
    r"[\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F300-\U0001F5FF"   # Symbols & Pictographs
    r"\U0001F680-\U0001F6FF"   # Transport & Map
    r"\U0001F700-\U0001F77F"   # Alchemical Symbols
    r"\U0001F780-\U0001F7FF"   # Geometric Shapes Extended
    r"\U0001F800-\U0001F8FF"   # Supplemental Arrows-C
    r"\U0001F900-\U0001F9FF"   # Supplemental Symbols and Pictographs
    r"\U0001FA00-\U0001FA6F"   # Chess Symbols
    r"\U0001FA70-\U0001FAFF"   # Symbols and Pictographs Extended-A
    r"\U00002702-\U000027B0"   # Dingbats
    r"\U000024C2-\U0001F251"   # Enclosed characters
    r"]+"
)

# Hashtag detection: matches hashtags in prose content
# Pattern: # followed by one or more word characters (letters, numbers, underscores)
# Must not be preceded by another word character (to avoid matching inside words)
HASHTAG_RE = re.compile(r"(?<!\w)#\w+")
# A line that opens or closes a fenced code block in markdown
FENCE_LINE_RE = re.compile(r"^[ \t]*(?:```+|~~~+)", re.M)

# AI-tell pattern detection: em-dash overuse
# Em-dash (—) and en-dash (–) used as a clause break are both counted; AI
# copy overuses either, and copy editors treat them as the same tell.
EM_DASH_RE = re.compile(r"[—–]")

# AI-tell pattern detection: triads (lists of three items)
# Matches patterns like "X, Y, and Z" or "X, Y, & Z"
# Common in AI-generated content: "fast, simple, and powerful"
TRIAD_RE = re.compile(
    r"\b(\w+),\s+(\w+),\s+(?:and|&)\s+(\w+)\b",
    re.I
)

# AI-tell pattern detection: multiple exclamation marks
# Matches 2+ consecutive exclamation marks
MULTIPLE_EXCLAMATION_RE = re.compile(r"!{2,}")

# AI-tell pattern detection: hedging language
# Words and phrases that weaken statements and are common in AI output.
# Phrases are listed first so "might help" reports as one phrase, not "might".
HEDGING_RE = re.compile(
    r"\b(can help|may enable|might help|could enable|"
    r"might|perhaps|possibly|somewhat|relatively|fairly|"
    r"reasonably|arguably|potentially|seemingly|apparently|"
    r"presumably|conceivably|supposedly|allegedly)\b",
    re.I
)


def norm_hex(raw: str) -> str | None:
    """Normalise a hex token to #RRGGBB. Returns None if it carries alpha 0."""
    h = raw.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    elif len(h) in (6, 8):
        h = h[:6]
    else:
        return None
    return "#" + h.upper()


def rgb(hex6: str) -> tuple[int, int, int]:
    h = hex6.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(hex6: str) -> float:
    """Relative luminance, 0-1."""
    def lin(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(hex6)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """WCAG contrast ratio between two hex colors."""
    l1, l2 = luminance(hex1), luminance(hex2)
    lighter, darker = (l1, l2) if l1 > l2 else (l2, l1)
    return (lighter + 0.05) / (darker + 0.05)


class Palette:
    def __init__(self, legal: dict[str, str], source: str):
        self.legal = legal              # #RRGGBB -> token name
        self.source = source

    def is_legal(self, hex6: str) -> bool:
        return hex6 in self.legal

    def name(self, hex6: str) -> str:
        return self.legal.get(hex6, hex6)

    def nearest(self, hex6: str) -> tuple[str, str, float]:
        r1, g1, b1 = rgb(hex6)
        best, bestd = None, 1e9
        for cand in self.legal:
            r2, g2, b2 = rgb(cand)
            d = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
            if d < bestd:
                best, bestd = cand, d
        return best, self.legal[best], bestd


def find_colors_md(start: str) -> str | None:
    """Walk up from a path looking for references/colors.md."""
    cur = os.path.abspath(start)
    if os.path.isfile(cur):
        cur = os.path.dirname(cur)
    while True:
        cand = os.path.join(cur, "references", "colors.md")
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def load_palette(colors_md: str, sub_brand: str | None = None) -> Palette:
    """
    Parse every hex in the markdown tables. Rows carrying exactly one hex also
    donate their first cell as the token name.

    If sub_brand is specified, load the sub-brand config and merge its
    custom_primitives into the palette.
    """
    legal: dict[str, str] = {}
    with open(colors_md, encoding="utf-8") as fh:
        for line in fh:
            hexes = [norm_hex(m.group(0)) for m in HEX_RE.finditer(line)]
            hexes = [h for h in hexes if h]
            if not hexes:
                continue
            token = None
            if line.lstrip().startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if cells:
                    token = re.sub(r"[`*]", "", cells[0]).strip()
                    if not token or HEX_RE.search(token):
                        token = None
            for h in hexes:
                if h not in legal or (token and len(hexes) == 1):
                    legal[h] = token if (token and len(hexes) == 1) else legal.get(h, h)
    if not legal:
        raise SystemExit(f"brand-check: no hex values found in {colors_md}")

    source = colors_md

    # Merge sub-brand custom primitives if specified
    if sub_brand:
        config_path = find_sub_brand_config(colors_md, sub_brand)
        custom_primitives = load_sub_brand_primitives(config_path)
        for token_name, hex_value in custom_primitives.items():
            normalized = norm_hex(hex_value)
            if normalized:
                legal[normalized] = token_name
        source = f"{colors_md} + {os.path.basename(config_path)}"

    return Palette(legal, source)


# --------------------------------------------------------------------------
# Sub-brand configs (config/sub-brands/*.json)
# --------------------------------------------------------------------------

def die(message: str, status: int = 2) -> NoReturn:
    """Print a usage/config error to stderr and exit (2 = bad invocation)."""
    print(message, file=sys.stderr)
    raise SystemExit(status)


def sub_brand_dir(colors_md: str) -> str:
    """config/sub-brands/ that sits next to the references/ holding colors.md."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(colors_md)))
    return os.path.join(repo_root, "config", "sub-brands")


def available_sub_brands(colors_md: str) -> list[str]:
    """Names accepted by --brand. Files starting with `_` are templates, not brands."""
    d = sub_brand_dir(colors_md)
    if not os.path.isdir(d):
        return []
    return sorted(
        os.path.splitext(f)[0] for f in os.listdir(d)
        if f.endswith(".json") and not f.startswith("_")
    )


def find_sub_brand_config(colors_md: str, brand: str) -> str:
    """
    Resolve --brand NAME to config/sub-brands/NAME.json.

    Exits with status 2 when the name is unknown (a silent fallback to the base
    palette would grade a file against the wrong brand). Template files whose
    name starts with `_` (e.g. _example-new-brand.json) are never selectable.
    """
    available = available_sub_brands(colors_md)
    if brand.startswith("_") or brand not in available:
        listing = ", ".join(available) if available else "(none found)"
        die(f"brand-check: unknown --brand {brand}; available: {listing}")
    return os.path.join(sub_brand_dir(colors_md), f"{brand}.json")


def find_sub_brand_schema(config_path: str) -> str | None:
    """schemas/sub-brand-config.schema.json relative to the config file, if present."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(config_path))))
    cand = os.path.join(repo_root, "schemas", "sub-brand-config.schema.json")
    return cand if os.path.isfile(cand) else None


def validate_sub_brand_config(config: dict, config_path: str) -> None:
    """
    Validate a loaded sub-brand config against schemas/sub-brand-config.schema.json.

    jsonschema is an optional runtime dependency (it is pinned in
    requirements-test.txt): when it is missing the check is skipped with a
    warning rather than failing the run. A config that fails validation exits
    with status 2 and a readable message naming the offending path.
    """
    schema_path = find_sub_brand_schema(config_path)
    if schema_path is None:
        return
    try:
        import jsonschema  # type: ignore
    except ImportError:
        print("brand-check: warning: jsonschema not installed; "
              f"skipping schema validation of {os.path.basename(config_path)} "
              "(pip install jsonschema)", file=sys.stderr)
        return
    try:
        with open(schema_path, encoding="utf-8") as fh:
            schema = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"brand-check: warning: could not load {schema_path}: {exc}", file=sys.stderr)
        return
    try:
        jsonschema.validate(config, schema)
    except jsonschema.ValidationError as exc:
        where = "/".join(str(p) for p in exc.absolute_path) or "(root)"
        die(f"brand-check: {os.path.basename(config_path)} fails "
            f"sub-brand-config.schema.json at {where}: {exc.message}")


def load_sub_brand_config(config_path: str) -> dict:
    """Load and validate a sub-brand config. Exits 2 when unreadable or invalid."""
    try:
        with open(config_path, encoding="utf-8") as fh:
            config = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        die(f"brand-check: could not load {config_path}: {exc}")
    if not isinstance(config, dict):
        die(f"brand-check: {config_path} must contain a JSON object")
    validate_sub_brand_config(config, config_path)
    return config


def load_sub_brand_primitives(config_path: str) -> dict[str, str]:
    """
    Load custom primitives from a sub-brand config.
    Returns dict of token_name -> hex_value.
    """
    token_overrides = load_sub_brand_config(config_path).get("token_overrides", {})
    return dict(token_overrides.get("custom_primitives", {}))


def sub_brand_font_families(config_path: str | None) -> set[str]:
    """
    Font families a --brand run accepts in addition to BRAND_FAMILIES.

    Reads token_overrides.typography_overrides.{display_font,body_font}; the
    names are lower-cased because the FONT check compares lower-cased families.
    """
    if not config_path:
        return set()
    typography = (load_sub_brand_config(config_path)
                  .get("token_overrides", {})
                  .get("typography_overrides", {}))
    return {
        str(typography[key]).strip().lower()
        for key in ("display_font", "body_font")
        if typography.get(key)
    }


def allowed_font_families(colors_md: str, sub_brand: str | None) -> set[str]:
    """BRAND_FAMILIES plus the sub-brand's typography overrides, as a new set."""
    families = set(BRAND_FAMILIES)
    if sub_brand:
        families |= sub_brand_font_families(find_sub_brand_config(colors_md, sub_brand))
    return families


# --------------------------------------------------------------------------
# Tokens — CSS variable name validation
# --------------------------------------------------------------------------

def var_name(token_name: str) -> str:
    """Convert a token name to a CSS variable name: 'text/primary' -> '--azmx-text-primary'"""
    return '--azmx-' + token_name.replace('/', '-')


def find_tokens_json(start: str) -> str | None:
    """Walk up from a path looking for assets/tokens/azmx-tokens.json."""
    cur = os.path.abspath(start)
    if os.path.isfile(cur):
        cur = os.path.dirname(cur)
    while True:
        cand = os.path.join(cur, "assets", "tokens", "azmx-tokens.json")
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def load_tokens(tokens_json: str) -> dict:
    """Load the design tokens from the JSON file."""
    with open(tokens_json, encoding="utf-8") as fh:
        return json.load(fh)


def valid_token_names(tokens: dict) -> set[str]:
    """
    Return the set of all valid CSS variable names from the token collections.
    Converts token names to CSS variables: 'text/primary' -> '--azmx-text-primary'
    """
    names = set()
    # Load all 5 token collections
    for collection_key in ['1. Primitives', '1b. Palette', '2. Semantic', '3. Component', '4. Canvas']:
        if collection_key in tokens and 'tokens' in tokens[collection_key]:
            for token_name in tokens[collection_key]['tokens'].keys():
                names.add(var_name(token_name))
    return names


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------

class Finding:
    __slots__ = ("path", "line", "severity", "code", "what", "fix")

    def __init__(self, path, line, severity, code, what, fix):
        self.path = path
        self.line = line
        self.severity = severity
        self.code = code
        self.what = what
        self.fix = fix


class ComplianceReport:
    """Aggregates brand-check findings across files."""

    def __init__(self, findings: list[Finding] | None = None):
        self.findings = findings or []

    def add(self, finding: Finding) -> None:
        """Add a single finding to the report."""
        self.findings.append(finding)

    def extend(self, findings: list[Finding]) -> None:
        """Add multiple findings to the report."""
        self.findings.extend(findings)

    def count_by_severity(self) -> dict[str, int]:
        """Return counts grouped by severity level."""
        counts = {"blocker": 0, "major": 0, "minor": 0}
        for f in self.findings:
            counts[f.severity] += 1
        return counts

    def count_by_code(self) -> dict[str, int]:
        """Return counts grouped by violation code."""
        counts: dict[str, int] = {}
        for f in self.findings:
            counts[f.code] = counts.get(f.code, 0) + 1
        return counts

    def by_file(self) -> dict[str, list[Finding]]:
        """Group findings by file path."""
        by_file: dict[str, list[Finding]] = {}
        for f in self.findings:
            by_file.setdefault(f.path, []).append(f)
        return by_file

    def has_blockers(self) -> bool:
        """Return True if any blocker-level findings exist."""
        return any(f.severity == "blocker" for f in self.findings)

    def total(self) -> int:
        """Return total number of findings."""
        return len(self.findings)

    def to_json(self, include_trends: bool = False) -> dict:
        """Serialize the report to a JSON-compatible dictionary."""
        data = {
            "total_findings": self.total(),
            "has_blockers": self.has_blockers(),
            "summary": {
                "by_severity": self.count_by_severity(),
                "by_code": self.count_by_code(),
            },
            "files_affected": len(self.by_file()),
            "findings": [
                {
                    "path": f.path,
                    "line": f.line,
                    "severity": f.severity,
                    "code": f.code,
                    "what": f.what,
                    "fix": f.fix,
                }
                for f in self.findings
            ],
        }

        if include_trends:
            data["trend"] = self._compute_trends()

        return data

    def _compute_trends(self) -> dict:
        """Compute trend analysis by comparing with historical data."""
        history = self._load_latest_history()

        if not history:
            return {
                "status": "no_history",
                "message": "No historical data available for comparison",
                "previous_report": None,
                "changes": None,
            }

        current_sev = self.count_by_severity()
        current_code = self.count_by_code()

        prev_sev = history.get("summary", {}).get("by_severity", {})
        prev_code = history.get("summary", {}).get("by_code", {})
        prev_total = history.get("total_findings", 0)

        # Calculate changes
        total_change = self.total() - prev_total
        sev_changes = {
            sev: current_sev.get(sev, 0) - prev_sev.get(sev, 0)
            for sev in ["blocker", "major", "minor"]
        }

        # Calculate code-level changes
        all_codes = set(current_code.keys()) | set(prev_code.keys())
        code_changes = {
            code: current_code.get(code, 0) - prev_code.get(code, 0)
            for code in all_codes
        }

        # Determine overall trend status
        if total_change < 0:
            status = "improved"
        elif total_change > 0:
            status = "degraded"
        else:
            status = "stable"

        return {
            "status": status,
            "message": self._trend_message(status, total_change, sev_changes),
            "previous_report": {
                "timestamp": history.get("timestamp"),
                "total_findings": prev_total,
                "by_severity": prev_sev,
                "by_code": prev_code,
            },
            "changes": {
                "total": total_change,
                "by_severity": sev_changes,
                "by_code": code_changes,
            },
        }

    def _trend_message(self, status: str, total_change: int, sev_changes: dict) -> str:
        """Generate a human-readable trend message."""
        if status == "improved":
            return f"Compliance improved: {abs(total_change)} fewer finding(s) than previous report"
        elif status == "degraded":
            blockers_up = sev_changes.get("blocker", 0)
            if blockers_up > 0:
                return f"Compliance degraded: {total_change} more finding(s), including {blockers_up} new blocker(s)"
            return f"Compliance degraded: {total_change} more finding(s) than previous report"
        else:
            return "Compliance stable: no change from previous report"

    def _load_latest_history(self) -> dict | None:
        """Load the most recent historical report."""
        history_dir = self._get_history_dir()
        if not os.path.exists(history_dir):
            return None

        history_files = sorted(
            [f for f in os.listdir(history_dir) if f.endswith(".json")],
            reverse=True
        )

        if not history_files:
            return None

        latest_file = os.path.join(history_dir, history_files[0])
        try:
            with open(latest_file, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None

    def save_to_history(self) -> None:
        """Save the current report to historical tracking."""
        history_dir = self._get_history_dir()
        os.makedirs(history_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"report-{timestamp}.json"
        filepath = os.path.join(history_dir, filename)

        report_data = self.to_json(include_trends=False)
        report_data["timestamp"] = datetime.now().isoformat()

        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(report_data, fh, indent=2)

        # Keep only the last 10 reports
        self._cleanup_old_reports(history_dir, keep=10)

    def _get_history_dir(self) -> str:
        """Get the directory path for storing historical reports."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(repo_root, ".brand-reports")

    def _cleanup_old_reports(self, history_dir: str, keep: int = 10) -> None:
        """Remove old reports, keeping only the most recent ones."""
        history_files = sorted(
            [f for f in os.listdir(history_dir) if f.endswith(".json")],
            reverse=True
        )

        for old_file in history_files[keep:]:
            try:
                os.remove(os.path.join(history_dir, old_file))
            except OSError:
                pass

    def to_html(self, scanned: int, palette_info: str) -> str:
        """Generate an HTML report following AZMX brand guidelines."""
        sev_counts = self.count_by_severity()
        code_counts = self.count_by_code()
        files_affected = self.by_file()

        status_class = "clean" if not self.has_blockers() else "has-blockers"
        status_text = "CLEAN — no brand violations found" if self.total() == 0 else \
                      f"{self.total()} finding(s) — {sev_counts['blocker']} blocker · {sev_counts['major']} major · {sev_counts['minor']} minor"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AZMX Brand Compliance Report</title>
<style>
:root{{--navy:#040038;--electric:#001AFF;--lightblue:#5D8FFF;--blue100:#DDE8FF;--blue200:#BFD5FF;--red:#FF2B3C;--orange:#F47A48;--green:#22C36F}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--navy);color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Tahoma,sans-serif;-webkit-font-smoothing:antialiased;padding:40px 24px}}
.container{{max-width:1200px;margin:0 auto}}
header{{margin-bottom:56px}}
.eyebrow{{color:var(--lightblue);text-transform:uppercase;letter-spacing:2.4px;font-size:14px;font-weight:600;margin:0 0 16px}}
h1{{font-family:Georgia,'Times New Roman',serif;font-size:clamp(32px,6vw,64px);font-weight:400;letter-spacing:-1.5px;line-height:1.1;margin:0 0 24px}}
.meta{{color:var(--blue200);opacity:.7;font-size:15px;margin:0;line-height:1.8}}
h2{{font-family:Georgia,serif;font-weight:500;font-size:clamp(24px,3vw,32px);margin:40px 0 16px;letter-spacing:-.5px;padding-top:24px;border-top:1px solid rgba(255,255,255,.14)}}
h2:first-of-type{{border-top:0;padding-top:0}}
.status{{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;margin:24px 0;font-size:15px;font-weight:600;border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.05)}}
.status.clean{{border-color:var(--green);background:rgba(34,195,111,.1);color:var(--green)}}
.status.has-blockers{{border-color:var(--red);background:rgba(255,43,60,.1);color:var(--red)}}
.summary-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:40px}}
.summary-card{{border:1px solid rgba(255,255,255,.14);padding:16px;background:rgba(255,255,255,.02)}}
.summary-card h3{{margin:0 0 8px;font-size:13px;letter-spacing:1.2px;text-transform:uppercase;color:var(--blue200);opacity:.7;font-weight:600}}
.summary-card .value{{font-size:28px;font-weight:600;font-variant-numeric:tabular-nums}}
.severity-blocker{{color:var(--red)}}
.severity-major{{color:var(--orange)}}
.severity-minor{{color:var(--lightblue)}}
.code-list{{list-style:none;padding:0;margin:0}}
.code-list li{{padding:8px 0;border-bottom:1px solid rgba(255,255,255,.08);display:flex;justify-content:space-between;align-items:center}}
.code-list li:last-child{{border-bottom:0}}
.code-name{{color:var(--blue100);font-size:14px}}
.code-count{{color:var(--blue200);font-size:13px;opacity:.8;font-variant-numeric:tabular-nums}}
.file-list{{list-style:none;padding:0;margin:0}}
.file-item{{margin-bottom:32px;padding:16px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.02)}}
.file-path{{font-size:16px;font-weight:600;margin:0 0 16px;color:var(--lightblue);word-break:break-all}}
.finding{{margin-bottom:16px;padding:12px;border-left:3px solid;background:rgba(255,255,255,.03)}}
.finding.blocker{{border-left-color:var(--red)}}
.finding.major{{border-left-color:var(--orange)}}
.finding.minor{{border-left-color:var(--lightblue)}}
.finding-header{{display:flex;gap:16px;margin-bottom:8px;flex-wrap:wrap}}
.finding-line{{color:var(--blue200);font-size:13px;opacity:.8;font-variant-numeric:tabular-nums}}
.finding-severity{{font-size:12px;letter-spacing:.8px;text-transform:uppercase;font-weight:600}}
.finding-code{{color:var(--blue100);font-size:13px;font-weight:600}}
.finding-what{{color:var(--blue100);font-size:14px;margin-bottom:8px;line-height:1.5}}
.finding-fix{{color:var(--blue200);font-size:13px;opacity:.8;line-height:1.6;padding-left:12px;border-left:1px solid rgba(255,255,255,.14)}}
code{{background:rgba(255,255,255,.08);padding:2px 6px;font-size:12px;color:var(--blue100)}}
footer{{margin-top:64px;padding-top:32px;border-top:1px solid rgba(255,255,255,.14);color:var(--blue200);font-size:13px;opacity:.6;text-align:center}}
@media(max-width:600px){{
  .summary-grid{{grid-template-columns:1fr}}
  .finding-header{{flex-direction:column;gap:4px}}
}}
</style>
</head>
<body>
<div class="container">
<header>
<p class="eyebrow">AZMX Brand Skill</p>
<h1>Brand Compliance Report</h1>
<p class="meta">{palette_info}</p>
<p class="meta">Scanned: {scanned} file(s)</p>
<div class="status {status_class}">{status_text}</div>
</header>

<h2>Summary by Severity</h2>
<div class="summary-grid">
<div class="summary-card">
<h3>Blocker</h3>
<div class="value severity-blocker">{sev_counts['blocker']}</div>
</div>
<div class="summary-card">
<h3>Major</h3>
<div class="value severity-major">{sev_counts['major']}</div>
</div>
<div class="summary-card">
<h3>Minor</h3>
<div class="value severity-minor">{sev_counts['minor']}</div>
</div>
<div class="summary-card">
<h3>Total Findings</h3>
<div class="value">{self.total()}</div>
</div>
</div>
"""

        if code_counts:
            html += """
<h2>Summary by Violation Type</h2>
<ul class="code-list">
"""
            for code in sorted(code_counts.keys()):
                html += f'<li><span class="code-name">{code}</span><span class="code-count">{code_counts[code]}</span></li>\n'
            html += "</ul>\n"

        if files_affected:
            html += f"""
<h2>Files Affected ({len(files_affected)})</h2>
<ul class="file-list">
"""
            for path in sorted(files_affected.keys()):
                rel_path = os.path.relpath(path)
                if rel_path.startswith(".."):
                    rel_path = os.path.abspath(path)
                findings_in_file = files_affected[path]

                html += f'<li class="file-item">\n'
                html += f'<h3 class="file-path">{self._escape_html(rel_path)}</h3>\n'

                for f in findings_in_file:
                    html += f'<div class="finding {f.severity}">\n'
                    html += f'<div class="finding-header">\n'
                    html += f'<span class="finding-line">Line {f.line}</span>\n'
                    html += f'<span class="finding-severity severity-{f.severity}">{f.severity}</span>\n'
                    html += f'<span class="finding-code">{f.code}</span>\n'
                    html += f'</div>\n'
                    html += f'<div class="finding-what">{self._escape_html(f.what)}</div>\n'
                    html += f'<div class="finding-fix">Fix: {self._escape_html(f.fix)}</div>\n'
                    html += f'</div>\n'

                html += '</li>\n'
            html += "</ul>\n"

        html += """
<footer>
Generated by AZMX brand-check.py
</footer>
</div>
</body>
</html>
"""
        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def to_markdown(self, scanned: int, palette_info: str) -> str:
        """Generate a markdown report."""
        sev_counts = self.count_by_severity()
        code_counts = self.count_by_code()
        files_affected = self.by_file()

        status_emoji = "✅" if self.total() == 0 else ("❌" if self.has_blockers() else "⚠️")
        status_text = "CLEAN — no brand violations found" if self.total() == 0 else \
                      f"{self.total()} finding(s) — {sev_counts['blocker']} blocker · {sev_counts['major']} major · {sev_counts['minor']} minor"

        md = f"""# AZMX Brand Compliance Report

**Status:** {status_emoji} {status_text}

**Palette:** {palette_info}
**Scanned:** {scanned} file(s)

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| 🔴 Blocker | {sev_counts['blocker']} |
| 🟠 Major | {sev_counts['major']} |
| 🔵 Minor | {sev_counts['minor']} |
| **Total** | **{self.total()}** |

"""

        if code_counts:
            md += """## Summary by Violation Type

| Violation Code | Count |
|----------------|-------|
"""
            for code in sorted(code_counts.keys()):
                md += f"| {code} | {code_counts[code]} |\n"
            md += "\n"

        if files_affected:
            md += f"""## Files Affected ({len(files_affected)})

"""
            for path in sorted(files_affected.keys()):
                rel_path = os.path.relpath(path)
                if rel_path.startswith(".."):
                    rel_path = os.path.abspath(path)
                findings_in_file = files_affected[path]

                md += f"### {rel_path}\n\n"
                md += f"**{len(findings_in_file)} finding(s)**\n\n"

                for f in findings_in_file:
                    severity_emoji = {"blocker": "🔴", "major": "🟠", "minor": "🔵"}[f.severity]
                    md += f"#### Line {f.line} {severity_emoji} {f.severity.upper()} — {f.code}\n\n"
                    md += f"**Issue:** {f.what}\n\n"
                    md += f"**Fix:** {f.fix}\n\n"
                    md += "---\n\n"

        md += """## Report Information

Generated by AZMX brand-check.py
"""
        return md


# --------------------------------------------------------------------------
# Source extraction: pull the CSS-bearing regions out of each file type
# --------------------------------------------------------------------------

STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
STYLE_ATTR_RE = re.compile(r"""\bstyle\s*=\s*(["'])(.*?)\1""", re.S | re.I)
PRESENT_ATTR_RE = re.compile(
    r"""\b(fill|stroke|stop-color|flood-color|lighting-color|color|font-family|font-style)"""
    r"""\s*=\s*(["'])(.*?)\2""",
    re.S | re.I,
)
FENCE_RE = re.compile(r"^([ \t]*)(```+|~~~+)", re.M)


def strip_comments(css: str) -> str:
    """Blank out /* */ comments, preserving offsets and newlines."""
    out = list(css)
    for m in re.finditer(r"/\*.*?\*/", css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != "\n":
                out[i] = " "
    return "".join(out)


def enclosing_tag(text: str, pos: int) -> str:
    """Return the opening-tag source that contains the offset `pos`."""
    start = text.rfind("<", max(0, pos - 2000), pos)
    if start == -1:
        return ""
    end = text.find(">", pos)
    return text[start: end + 1] if end != -1 else text[start: pos + 1]


def css_regions(text: str, ext: str) -> list[tuple[int, str, str, str]]:
    """
    Return [(offset, source, kind, owner_tag)] regions of CSS-ish content.
    kind: 'css' (rule blocks) | 'decls' (bare declaration list) | 'attr'
    """
    regions: list[tuple[int, str, str, str]] = []
    if ext == ".css":
        regions.append((0, text, "css", ""))
        return regions

    if ext in (".html", ".htm", ".svg"):
        for m in STYLE_BLOCK_RE.finditer(text):
            regions.append((m.start(1), m.group(1), "css", ""))
        for m in STYLE_ATTR_RE.finditer(text):
            regions.append((m.start(2), m.group(2), "decls", enclosing_tag(text, m.start())))
        for m in PRESENT_ATTR_RE.finditer(text):
            prop = m.group(1).lower()
            regions.append((m.start(3), f"{prop}:{m.group(3)}", "decls",
                            enclosing_tag(text, m.start())))
        return regions

    if ext == ".md":
        # Only fenced code blocks — prose and reference tables legitimately
        # quote hexes and font names, and flagging those is noise. Within the
        # fences, only markup languages are parsed: a ```bash or ```text block
        # can hold hexes as data (recolour maps, palette dumps) and is not a
        # styling decision.
        lines = text.splitlines(keepends=True)
        offset, inside, buf, buf_off, lang = 0, False, [], 0, ""
        for ln in lines:
            fence = re.match(r"^[ \t]*(?:```+|~~~+)[ \t]*([\w+-]*)", ln)
            if fence:
                if inside:
                    sub = _md_fence_ext(lang, "".join(buf))
                    if sub:
                        for off2, src2, kind2, own2 in css_regions("".join(buf), sub):
                            regions.append((buf_off + off2, src2, kind2, own2))
                    buf, inside, lang = [], False, ""
                else:
                    inside = True
                    lang = fence.group(1).lower()
                    buf_off = offset + len(ln)
            elif inside:
                buf.append(ln)
            offset += len(ln)
        return regions

    return regions


MARKUP_FENCE = {
    "css": ".css", "scss": ".css", "less": ".css",
    "html": ".html", "htm": ".html", "xml": ".html", "svg": ".svg",
}


def _md_fence_ext(lang: str, body: str) -> str | None:
    """Map a fence language to a parser, or None if the block is not markup."""
    if lang in MARKUP_FENCE:
        return MARKUP_FENCE[lang]
    if lang:
        return None                      # bash / text / json / py / jsx …
    # Untagged fence: accept only if it actually looks like CSS or HTML.
    if re.search(r"<[a-zA-Z][^>]*>", body):
        return ".html"
    if re.search(r"\{[^{}]*[\w-]+\s*:[^{};]+;", body, re.S):
        return ".css"
    return None


# --------------------------------------------------------------------------
# Text extraction: pull prose content from different file types
# --------------------------------------------------------------------------

def extract_prose_content(text: str, ext: str) -> str:
    """
    Extract readable prose content from text based on file type.
    Returns plain text with markup/tags removed.
    """
    if ext == ".md":
        return _extract_markdown_prose(text)
    if ext in (".html", ".htm"):
        return _extract_html_prose(text)
    return text


def _extract_markdown_prose(text: str) -> str:
    """Extract prose from markdown, removing syntax but keeping text."""
    prose = text

    # Remove fenced code blocks
    prose = re.sub(r"^[ \t]*(?:```+|~~~+).*?^[ \t]*(?:```+|~~~+)", "", prose, flags=re.M | re.S)

    # Remove inline code
    prose = re.sub(r"`[^`]+`", "", prose)

    # Remove HTML tags
    prose = re.sub(r"<[^>]+>", "", prose)

    # Remove markdown links but keep text: [text](url) -> text
    prose = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", prose)

    # Remove images: ![alt](url)
    prose = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", prose)

    # Remove reference-style links: [text][ref]
    prose = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", prose)

    # Remove headings markup but keep text
    prose = re.sub(r"^#+\s+", "", prose, flags=re.M)

    # Remove bold/italic markers but keep text
    prose = re.sub(r"\*\*([^*]+)\*\*", r"\1", prose)
    prose = re.sub(r"\*([^*]+)\*", r"\1", prose)
    prose = re.sub(r"__([^_]+)__", r"\1", prose)
    prose = re.sub(r"_([^_]+)_", r"\1", prose)

    # Remove blockquotes marker
    prose = re.sub(r"^>\s*", "", prose, flags=re.M)

    # Remove list markers
    prose = re.sub(r"^[\s*+-]*\s+", "", prose, flags=re.M)
    prose = re.sub(r"^\d+\.\s+", "", prose, flags=re.M)

    # Remove horizontal rules
    prose = re.sub(r"^[\s*-_]{3,}$", "", prose, flags=re.M)

    return prose.strip()


def _extract_html_prose(text: str) -> str:
    """Extract prose from HTML, removing tags and scripts."""
    prose = text

    # Remove script and style blocks
    prose = re.sub(r"<script\b[^>]*>.*?</script>", "", prose, flags=re.S | re.I)
    prose = re.sub(r"<style\b[^>]*>.*?</style>", "", prose, flags=re.S | re.I)

    # Remove HTML comments
    prose = re.sub(r"<!--.*?-->", "", prose, flags=re.S)

    # Remove all HTML tags
    prose = re.sub(r"<[^>]+>", "", prose)

    # Decode common HTML entities
    prose = prose.replace("&nbsp;", " ")
    prose = prose.replace("&lt;", "<")
    prose = prose.replace("&gt;", ">")
    prose = prose.replace("&amp;", "&")
    prose = prose.replace("&quot;", '"')
    prose = prose.replace("&apos;", "'")

    return prose.strip()


def parse_posts(text: str) -> list[tuple[int, int, str]]:
    """
    Detect post boundaries for hashtag counting and other per-post validation.
    Returns list of (start_offset, end_offset, post_text) tuples.

    Post boundaries are detected by:
      - Horizontal rules (---, ***, ___) on their own line
      - Double blank lines (two consecutive newlines with optional whitespace)
      - Single file = single post if no boundaries found

    Follows the pattern of parse_blocks: tracks offsets and returns structured data.
    """
    # Horizontal rule pattern: 3+ dashes, asterisks, or underscores on their own line
    hr_pattern = re.compile(r"^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*$", re.M)

    # Find all boundary positions
    boundaries = [0]  # Start of text

    # Find horizontal rules
    for m in hr_pattern.finditer(text):
        boundaries.append(m.start())

    # Find double blank lines (two or more consecutive newlines)
    double_newline = re.compile(r"\n[ \t]*\n[ \t]*\n")
    for m in double_newline.finditer(text):
        # Position after the double newline
        boundaries.append(m.end())

    boundaries.append(len(text))  # End of text

    # Sort and deduplicate boundaries
    boundaries = sorted(set(boundaries))

    # Build posts from boundaries
    posts = []
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        post_text = text[start:end].strip()

        # Skip empty posts
        if not post_text:
            continue

        # Skip posts that are just horizontal rules
        if hr_pattern.fullmatch(post_text):
            continue

        posts.append((start, end, post_text))

    # If no boundaries found, treat entire text as single post
    if not posts:
        posts.append((0, len(text), text.strip()))

    return posts


# --------------------------------------------------------------------------
# CSS block / declaration parsing
# --------------------------------------------------------------------------

class Decl:
    __slots__ = ("prop", "value", "offset")

    def __init__(self, prop, value, offset):
        self.prop = prop
        self.value = value
        self.offset = offset


class Block:
    __slots__ = ("selector", "decls", "offset", "owner_tag")

    def __init__(self, selector, decls, offset, owner_tag=""):
        self.selector = selector
        self.decls = decls
        self.offset = offset
        self.owner_tag = owner_tag


def parse_decls(body: str, base: int) -> list[Decl]:
    decls, pos = [], 0
    depth = 0
    start = 0
    # split on ';' at paren-depth 0
    for i, ch in enumerate(body):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            chunk, off = body[start:i], start
            d = _mk_decl(chunk, base + off)
            if d:
                decls.append(d)
            start = i + 1
    d = _mk_decl(body[start:], base + start)
    if d:
        decls.append(d)
    return decls


def _mk_decl(chunk: str, offset: int) -> Decl | None:
    if ":" not in chunk:
        return None
    lead = len(chunk) - len(chunk.lstrip())
    prop, _, value = chunk.partition(":")
    return Decl(prop.strip().lower(), value.strip(), offset + lead)


def parse_blocks(css: str, base: int, owner_tag: str = "") -> list[Block]:
    """Innermost brace blocks only, so @media wrappers do not swallow rules."""
    css = strip_comments(css)
    blocks: list[Block] = []
    stack: list[tuple[int, bool]] = []   # (open_pos, had_child)
    last_close = 0
    for i, ch in enumerate(css):
        if ch == "{":
            if stack:
                op, _ = stack[-1]
                stack[-1] = (op, True)
            stack.append((i, False))
        elif ch == "}":
            if not stack:
                continue
            op, had_child = stack.pop()
            if not had_child:
                sel_start = max(last_close, css.rfind("{", 0, op) + 1)
                sel_start = max(sel_start, css.rfind("}", 0, op) + 1)
                selector = " ".join(css[sel_start:op].split())
                body = css[op + 1:i]
                blocks.append(Block(selector, parse_decls(body, base + op + 1),
                                    base + sel_start, owner_tag))
            last_close = i + 1
    return blocks


# --------------------------------------------------------------------------
# Value helpers
# --------------------------------------------------------------------------

VAR_RE = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,([^()]*(?:\([^()]*\)[^()]*)*))?\)")
FUNC_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)


def resolve_vars(value: str, custom: dict[str, str], depth: int = 0) -> str:
    if depth > 6 or "var(" not in value:
        return value
    def sub(m):
        name, fallback = m.group(1), (m.group(2) or "").strip()
        if name in custom:
            return custom[name]
        return fallback
    return resolve_vars(VAR_RE.sub(sub, value), custom, depth + 1)


def hexes_in(value: str) -> list[tuple[str, str]]:
    """[(normalised, raw)] for every hex literal in a value."""
    out = []
    for m in HEX_RE.finditer(value):
        n = norm_hex(m.group(0))
        if n:
            out.append((n, m.group(0)))
    return out


def emojis_in(text: str) -> list[tuple[int, str]]:
    """[(offset, emoji_text)] for every emoji found in text."""
    out = []
    for m in EMOJI_RE.finditer(text):
        out.append((m.start(), m.group(0)))
    return out


def hashtags_in(text: str) -> list[tuple[int, str]]:
    """[(offset, hashtag_text)] for every hashtag found in text."""
    out = []
    for m in HASHTAG_RE.finditer(text):
        out.append((m.start(), m.group(0)))
    return out


def banned_intensifiers_in(text: str) -> list[tuple[int, str]]:
    """[(offset, word_text)] for every banned intensifier found in text."""
    out = []
    for m in BANNED_INTENSIFIER.finditer(text):
        out.append((m.start(), m.group(0)))
    return out


def em_dashes_in(text: str) -> list[tuple[int, str]]:
    """[(offset, em_dash_text)] for every em-dash found in text."""
    out = []
    for m in EM_DASH_RE.finditer(text):
        out.append((m.start(), m.group(0)))
    return out


def triads_in(text: str) -> list[tuple[int, str]]:
    """[(offset, triad_text)] for every triad pattern found in text."""
    out = []
    for m in TRIAD_RE.finditer(text):
        out.append((m.start(), m.group(0)))
    return out


def multiple_exclamations_in(text: str) -> list[tuple[int, str]]:
    """[(offset, exclamation_text)] for every multiple exclamation mark found in text."""
    out = []
    for m in MULTIPLE_EXCLAMATION_RE.finditer(text):
        out.append((m.start(), m.group(0)))
    return out


def hedging_in(text: str) -> list[tuple[int, str]]:
    """[(offset, word_text)] for every hedging word found in text."""
    out = []
    for m in HEDGING_RE.finditer(text):
        out.append((m.start(), m.group(0)))
    return out


def first_color_hex(value: str, custom: dict[str, str]) -> str | None:
    resolved = resolve_vars(value, custom)
    hs = hexes_in(resolved)
    return hs[0][0] if hs else None


def split_families(value: str) -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip().strip("'\"").strip() for p in parts if p.strip()]


def px_values(value: str) -> list[tuple[float, str]]:
    """Every px length in the value, including inside clamp()/min()/max()/calc()."""
    return [(abs(float(m.group(1))), m.group(0))
            for m in re.finditer(r"(-?\d*\.?\d+)px\b", value)]


def base_selector(sel: str) -> str:
    """`.copy[data-copied="1"]:hover` -> `.copy` ; `.tagbar button:hover` -> `.tagbar button`"""
    sel = sel.split(",")[0]
    sel = re.sub(r"\[[^\]]*\]", "", sel)
    sel = re.sub(r"::?[\w-]+(\([^)]*\))?", "", sel)
    return " ".join(sel.split())


# --------------------------------------------------------------------------
# The checks
# --------------------------------------------------------------------------

def is_swatch(owner_tag: str) -> bool:
    m = re.search(r"""\bclass\s*=\s*(["'])(.*?)\1""", owner_tag, re.I | re.S)
    return bool(m and SWATCH_CLASS.search(m.group(2)))


class _CheckContext:
    """
    Everything the per-section check helpers share for one file: the raw text,
    the parsed CSS blocks, resolved custom properties, and the `add()` sink that
    de-duplicates findings on (line, code, what).
    """
    __slots__ = ("path", "text", "ext", "palette", "blocks", "custom",
                 "text_color_by_base", "valid_vars", "findings", "_nl", "_seen")

    def __init__(self, path: str, text: str, ext: str, palette: Palette):
        self.path = path
        self.text = text
        self.ext = ext
        self.palette = palette
        self.blocks: list[Block] = []
        self.custom: dict[str, str] = {}
        self.text_color_by_base: dict[str, str] = {}
        self.valid_vars: set[str] = set()
        self.findings: list[Finding] = []
        self._nl = [i for i, c in enumerate(text) if c == "\n"]
        self._seen: set[tuple[int, str, str]] = set()

    def line_of(self, off: int) -> int:
        return bisect.bisect_right(self._nl, off) + 1

    def add(self, off: int, severity: str, code: str, what: str, fix: str) -> None:
        ln = self.line_of(off)
        key = (ln, code, what)
        if key in self._seen:
            return
        self._seen.add(key)
        self.findings.append(Finding(self.path, ln, severity, code, what, fix))


def _load_style_context(ctx: _CheckContext) -> None:
    """Pass 1 — parse every CSS region, gather custom properties and per-selector text colours."""
    tokens_json = find_tokens_json(ctx.path)
    if tokens_json:
        try:
            ctx.valid_vars = valid_token_names(load_tokens(tokens_json))
        except (OSError, json.JSONDecodeError):
            pass  # TOKEN_REF check is skipped when tokens can't be loaded

    for off, src, kind, owner in css_regions(ctx.text, ctx.ext):
        if kind == "css":
            ctx.blocks.extend(parse_blocks(src, off, owner))
        else:
            ctx.blocks.append(Block("", parse_decls(src, off), off, owner))

    for b in ctx.blocks:
        for d in b.decls:
            if d.prop.startswith("--"):
                ctx.custom.setdefault(d.prop, d.value)
    for k in list(ctx.custom):
        ctx.custom[k] = resolve_vars(ctx.custom[k], ctx.custom)

    for b in ctx.blocks:
        if not b.selector:
            continue
        for d in b.decls:
            if d.prop == "color":
                h = first_color_hex(d.value, ctx.custom)
                if h:
                    ctx.text_color_by_base.setdefault(base_selector(b.selector), h)


# ---- colour checks ---------------------------------------------------------

def _check_palette(ctx: _CheckContext, d: Decl) -> None:
    """1. Every hex literal must be a palette tone (nearest legal token suggested)."""
    for norm, raw in hexes_in(d.value):
        if ctx.palette.is_legal(norm):
            continue
        near, near_name, dist = ctx.palette.nearest(norm)
        sev = "minor" if dist <= 12 else "major"
        tail = " (near-miss — snap it)" if sev == "minor" else ""
        ctx.add(d.offset, sev, "COLOR",
                f"{raw} in `{d.prop}` is not in the palette{tail}",
                f"use {near_name} {near} (ΔRGB {dist:.0f}) "
                f"or add the tone to references/colors.md")


def _block_color_pair(ctx: _CheckContext, b: Block):
    """First background hex and first text-colour hex declared in a block (with offsets)."""
    bg_hex = color_hex = None
    bg_off = color_off = None
    for d in b.decls:
        if d.prop in ("background", "background-color", "background-image"):
            h = first_color_hex(d.value, ctx.custom)
            if h and bg_hex is None:
                bg_hex, bg_off = h, d.offset
        if d.prop == "color":
            h = first_color_hex(d.value, ctx.custom)
            if h and color_hex is None:
                color_hex, color_off = h, d.offset
    return bg_hex, bg_off, color_hex, color_off


def _check_electric(ctx: _CheckContext, b: Block, bg_hex, bg_off, color_hex, color_off) -> None:
    """5. Electric as text on a dark surface, or as a large fill behind text."""
    electric = "#001AFF"
    if color_hex == electric and bg_hex and luminance(bg_hex) < 0.35:
        ctx.add(color_off, "blocker", "ELECTRIC",
                f"Electric #001AFF set as text over the dark surface {bg_hex} "
                f"(selector `{b.selector or 'inline style'}`)",
                "Electric fails contrast on dark. Use Light Blue #5D8FFF for the "
                "accent on dark surfaces, White #FFFFFF for titles, "
                "Blue 100 #DDE8FF for body.")
    if bg_hex == electric:
        inherited = ctx.text_color_by_base.get(base_selector(b.selector), None) \
            if b.selector else None
        if color_hex or inherited:
            ctx.add(bg_off, "major", "ELECTRIC",
                    f"Electric #001AFF used as a fill behind text "
                    f"(selector `{b.selector or 'inline style'}`)",
                    "Electric is punctuation, never a large fill behind text (it vibrates). "
                    "Fill with Dark Navy #040038 or Blue 50 #F0F5FF, and keep Electric "
                    "for the accent mark, rule, or single highlighted word.")


def _check_contrast(ctx: _CheckContext, b: Block, bg_hex, color_hex, color_off) -> None:
    """WCAG AA contrast (4.5:1) between a block's text colour and its background."""
    if not (color_hex and bg_hex and color_hex != bg_hex):
        return
    ratio = contrast_ratio(color_hex, bg_hex)
    if ratio >= 4.5:
        return
    if luminance(bg_hex) < 0.5:
        suggestions = "Use White #FFFFFF for titles, Blue 100 #DDE8FF for body, or Light Blue #5D8FFF for accents on dark surfaces."
    else:
        suggestions = "Use Dark Navy #040038 for titles, Neutral 900 #111927 for body, or Electric #001AFF for accents on light surfaces."
    ctx.add(color_off, "blocker", "CONTRAST",
            f"text color {ctx.palette.name(color_hex)} {color_hex} on background "
            f"{ctx.palette.name(bg_hex)} {bg_hex} has contrast ratio {ratio:.2f}:1 "
            f"(WCAG AA requires 4.5:1 for normal text) "
            f"in `{b.selector or 'inline style'}`",
            suggestions)


# ---- font checks -----------------------------------------------------------

def _check_fonts(ctx: _CheckContext, d: Decl, brand_families: set[str]) -> None:
    """2. font-family / font shorthand must name a brand family (or a generic keyword)."""
    prop, value = d.prop, d.value
    if prop == "font-family" or (prop.startswith("--") and "font" in prop):
        fams = split_families(resolve_vars(value, ctx.custom))
        if fams and not (len(fams) == 1 and fams[0].lower() in GENERIC_FAMILIES):
            for idx, fam in enumerate(fams):
                low = fam.lower()
                if low in brand_families or low in GENERIC_FAMILIES:
                    continue
                if low.startswith("var(") or not low:
                    continue
                primary = idx == 0
                ctx.add(d.offset,
                        "blocker" if primary else "minor",
                        "FONT",
                        f"non-brand font family \"{fam}\" "
                        f"{'set as the primary family' if primary else 'in the fallback stack'} "
                        f"in `{prop}`",
                        "the system has two families only: "
                        "\"thmanyah serif display\" (display) and \"Azm X\" (body). "
                        + ("replace it." if primary
                           else "drop the fallback or reduce it to the generic keyword."))
    elif prop == "font" and ("\"" in value or "'" in value):
        for fam in re.findall(r"""["']([^"']+)["']""", value):
            if fam.lower() not in brand_families:
                ctx.add(d.offset, "blocker", "FONT",
                        f"non-brand font family \"{fam}\" in the `font` shorthand",
                        "use \"thmanyah serif display\" or \"Azm X\".")


def _check_italic(ctx: _CheckContext, d: Decl) -> None:
    """3. No italics anywhere — the serif ships no italic face."""
    if d.prop == "font-style" and re.search(r"\b(italic|oblique)\b", d.value, re.I):
        ctx.add(d.offset, "blocker", "ITALIC",
                f"`font-style: {d.value.strip()}`",
                "no italics anywhere — thmanyah serif display ships no italic, so "
                "this renders a faux slant. Express emphasis with scale, weight, or colour.")


# ---- spacing / decoration / token checks -----------------------------------

def _check_spacing(ctx: _CheckContext, d: Decl) -> None:
    """4. padding / margin / gap px values must sit on the spacing scale."""
    if not SPACING_PROPS.match(d.prop):
        return
    for val, raw in px_values(resolve_vars(d.value, ctx.custom)):
        if val == 0 or val in SPACING_SCALE:
            continue
        near = min(SPACING_SCALE, key=lambda s: abs(s - val))
        ctx.add(d.offset, "minor", "SPACING",
                f"`{d.prop}: … {raw} …` is off the spacing scale",
                f"use {near}px. The only permitted values are "
                f"{' · '.join(str(s) for s in SPACING_SCALE)}.")


def _check_chevron_asset(ctx: _CheckContext, d: Decl) -> None:
    """6. Chevron / arrow art used as a background or mask."""
    if d.prop not in ("background", "background-image", "mask", "mask-image",
                      "-webkit-mask", "-webkit-mask-image", "content", "list-style-image"):
        return
    for m in FUNC_URL_RE.finditer(d.value):
        if CHEVRON_WORD.search(m.group(2)):
            ctx.add(d.offset, "blocker", "CHEVRON",
                    f"chevron/arrow asset used as a background in `{d.prop}`: {m.group(2)}",
                    "chevrons as background decoration are banned (design-system v1.1). "
                    "Backgrounds stay solid or gradient. Use the chevron functionally: "
                    "photo mask, section tick, or list bullet.")


def _check_token_ref(ctx: _CheckContext, d: Decl) -> None:
    """7. var(--azmx-*) must reference a token that exists in azmx-tokens.json."""
    if not (ctx.valid_vars and "var(" in d.value):
        return
    for m in VAR_RE.finditer(d.value):
        var_ref = m.group(1)
        if not var_ref.startswith("--azmx-") or var_ref in ctx.valid_vars:
            continue
        # Name is the final tiebreak so the suggestion order does not depend
        # on set iteration order (it used to change with PYTHONHASHSEED).
        candidates = sorted(ctx.valid_vars, key=lambda v: (
            abs(len(v) - len(var_ref)),
            sum(a != b for a, b in zip(v, var_ref)),
            v,
        ))[:3]
        ctx.add(d.offset, "major", "TOKEN_REF",
                f"`var({var_ref})` in `{d.prop}` is not a valid design token",
                "use a valid token: " + ", ".join(candidates[:3]))


def _check_chevron_opacity(ctx: _CheckContext, b: Block) -> None:
    """Low-opacity chevron field textures."""
    if not (CHEVRON_WORD.search(b.selector or "") or CHEVRON_WORD.search(b.owner_tag or "")):
        return
    for d in b.decls:
        if d.prop != "opacity":
            continue
        try:
            o = float(d.value.strip().rstrip("%"))
            if d.value.strip().endswith("%"):
                o /= 100.0
        except ValueError:
            continue
        if 0 < o < 0.5:
            ctx.add(d.offset, "major", "CHEVRON",
                    f"chevron element at opacity {d.value.strip()} "
                    f"(selector `{b.selector or b.owner_tag[:40]}`)",
                    "ghost / low-opacity chevron field textures are banned. "
                    "Either make it a functional foreground chevron at full "
                    "strength, or remove it and use negative space.")


def _check_style_blocks(ctx: _CheckContext, brand_families: set[str]) -> None:
    """Pass 2 — run the declaration-level and block-level style checks over every block."""
    for b in ctx.blocks:
        swatch = is_swatch(b.owner_tag)
        bg_hex, bg_off, color_hex, color_off = _block_color_pair(ctx, b)

        for d in b.decls:
            if not swatch:
                _check_palette(ctx, d)
            _check_fonts(ctx, d, brand_families)
            _check_italic(ctx, d)
            _check_spacing(ctx, d)
            _check_chevron_asset(ctx, d)
            _check_token_ref(ctx, d)

        _check_chevron_opacity(ctx, b)

        if not swatch:
            _check_electric(ctx, b, bg_hex, bg_off, color_hex, color_off)
            _check_contrast(ctx, b, bg_hex, color_hex, color_off)


# ---- RTL checks ------------------------------------------------------------

def _check_rtl(ctx: _CheckContext) -> None:
    """7. RTL validation for HTML files that carry Arabic text."""
    text = ctx.text
    if ctx.ext not in (".html", ".htm") or not ARABIC_CHAR.search(text):
        return

    # <table> / <td> missing dir="rtl"
    for m in TABLE_TAG.finditer(text):
        tag_name = m.group(1).lower()
        if not re.search(r'\bdir\s*=\s*["\']?rtl["\']?', m.group(2), re.I):
            ctx.add(m.start(), "blocker", "RTL",
                    f"<{tag_name}> tag missing dir=\"rtl\" in Arabic email context",
                    f"add dir=\"rtl\" to every <{tag_name}> tag. Gmail drops dir from parent "
                    "elements, so per-element dir is the only reliable RTL carrier.")

    # Chevrons outside a <span dir="ltr"> wrapper
    for m in re.finditer(r"[‹›<>←→]", text):
        chevron = m.group(0)
        pos = m.start()
        preceding = text[max(0, pos - 200):pos]
        ltr_open = list(re.finditer(r'<span\s+dir\s*=\s*["\']ltr["\'][^>]*>', preceding, re.I))
        ltr_close = list(re.finditer(r'</span>', preceding, re.I))
        inside_ltr = len(ltr_open) > len(ltr_close)
        if re.search(r'<(style|script)\b', preceding[-50:], re.I):
            continue
        if not inside_ltr and chevron in "‹›":
            ctx.add(m.start(), "blocker", "RTL",
                    f"chevron '{chevron}' not wrapped in dir=\"ltr\" span",
                    "wrap chevrons in <span dir=\"ltr\">&#8249;</span> to prevent "
                    "bidi algorithm from mirroring them incorrectly in RTL context.")

    # letter-spacing next to Arabic text (breaks kashida)
    for b in ctx.blocks:
        letter_spacing_offset = None
        for d in b.decls:
            if d.prop == "letter-spacing" and d.value.strip() not in ("0", "0px", "normal"):
                letter_spacing_offset = d.offset
                break
        if letter_spacing_offset is None:
            continue
        nearby_text = text[max(0, letter_spacing_offset - 500):
                           min(len(text), letter_spacing_offset + 500)]
        if ARABIC_CHAR.search(nearby_text):
            # Exception: allow letter-spacing on elements marked as LTR
            if not re.search(r'\bdir\s*=\s*["\']?ltr["\']?', nearby_text, re.I):
                ctx.add(letter_spacing_offset, "major", "RTL",
                        "letter-spacing applied to Arabic text context",
                        "Arabic text uses kashida for stretching, not letter-spacing. "
                        "Remove letter-spacing or wrap Latin fragments in dir=\"ltr\" spans.")


# ---- copy / tone checks (--copy) -------------------------------------------

def _check_copy_emojis(ctx: _CheckContext, in_code) -> None:
    """7. Emojis in prose."""
    for emoji_off, emoji_text in emojis_in(ctx.text):
        if in_code(emoji_off):
            continue
        ctx.add(emoji_off, "major", "EMOJI",
                f"emoji '{emoji_text}' found in prose",
                "emojis are not part of the brand voice. Use descriptive text instead.")


def _raw_offset_of_hashtags(text: str, hashtags: list[tuple[int, str]], cursor: int) -> tuple[int | None, int]:
    """
    Map a post's hashtags (found in the *extracted prose*) back to the raw file.

    Prose extraction strips markup, so prose offsets do not line up with the raw
    text. Hashtags appear in the same order in both, so walking the raw text with
    a cursor and locating each tag in turn recovers the raw offset of the first
    one. Returns (raw offset of the first hashtag or None, advanced cursor).
    """
    first = None
    for _, tag in hashtags:
        m = re.compile(r"(?<!\w)" + re.escape(tag) + r"(?!\w)").search(text, cursor)
        if not m:
            break
        if first is None:
            first = m.start()
        cursor = m.end()
    return first, cursor


def _check_copy_hashtags(ctx: _CheckContext) -> None:
    """8. Max 3 hashtags per post."""
    prose = extract_prose_content(ctx.text, ctx.ext)
    cursor = 0
    for post_start, _post_end, post_text in parse_posts(prose):
        hashtags = hashtags_in(post_text)
        if not hashtags:
            continue
        raw_off, cursor = _raw_offset_of_hashtags(ctx.text, hashtags, cursor)
        if len(hashtags) > 3:
            off = raw_off if raw_off is not None else min(post_start, len(ctx.text))
            ctx.add(off, "major", "HASHTAG",
                    f"{len(hashtags)} hashtags in post (max 3 allowed)",
                    f"reduce hashtag count to 3 or fewer. Found: {', '.join(h[1] for h in hashtags)}")


def _check_copy_intensifiers(ctx: _CheckContext, in_code, fix_mode: bool) -> None:
    """9. Banned intensifiers and corporate jargon."""
    default_fix = "avoid corporate jargon and intensifiers. Use direct, clear language instead."
    for word_off, word_text in banned_intensifiers_in(ctx.text):
        if in_code(word_off):
            continue
        fix_msg = default_fix
        if fix_mode:
            suggestions = WORD_SUGGESTIONS.get(word_text.lower(), [])
            if suggestions:
                fix_msg = f"replace '{word_text}' with: {', '.join(suggestions)}"
        ctx.add(word_off, "major", "INTENSIFIER",
                f"banned intensifier '{word_text}' found in prose",
                fix_msg)


def _check_copy_ai_tells(ctx: _CheckContext, in_code) -> None:
    """10. AI-tell patterns: em-dash overuse, triads, exclamation runs, hedging."""
    text = ctx.text
    em_dashes = em_dashes_in(text)
    if len(em_dashes) > 2:
        first_em_off, _ = em_dashes[0]
        if not in_code(first_em_off):
            ctx.add(first_em_off, "minor", "AI-TELL",
                    f"{len(em_dashes)} em-dashes found (common AI pattern)",
                    "em-dashes are overused in AI-generated content. Use sparingly or replace with periods.")

    for triad_off, triad_text in triads_in(text):
        if not in_code(triad_off):
            ctx.add(triad_off, "minor", "AI-TELL",
                    f"triad pattern '{triad_text}' (common AI pattern)",
                    "lists of three items are overused in AI-generated content. Vary sentence structure.")

    for excl_off, excl_text in multiple_exclamations_in(text):
        if not in_code(excl_off):
            ctx.add(excl_off, "major", "AI-TELL",
                    f"multiple exclamation marks '{excl_text}' found",
                    "avoid multiple exclamation marks. Use one or none.")

    for hedge_off, hedge_text in hedging_in(text):
        if not in_code(hedge_off):
            ctx.add(hedge_off, "minor", "AI-TELL",
                    f"hedging word '{hedge_text}' (weakens brand voice)",
                    "avoid hedging language. Make direct, confident statements.")


def _check_copy(ctx: _CheckContext, fix_mode: bool) -> None:
    """Sections 7-10: prose validation, enabled by --copy."""
    # Fenced code blocks are computed once; every copy check asks in_code(offset)
    # which is a binary search instead of re-splitting the file per finding.
    fence_starts = ([m.start() for m in FENCE_LINE_RE.finditer(ctx.text)]
                    if ctx.ext == ".md" else [])

    def in_code(offset: int) -> bool:
        # Odd number of fence lines before the offset => inside a block
        return bisect.bisect_right(fence_starts, offset) % 2 == 1

    _check_copy_emojis(ctx, in_code)
    _check_copy_hashtags(ctx)
    _check_copy_intensifiers(ctx, in_code, fix_mode)
    _check_copy_ai_tells(ctx, in_code)


def check_file(path: str, palette: Palette, check_copy: bool = False, fix_mode: bool = False,
               brand_families: set[str] | None = None) -> list[Finding]:
    """
    Lint one file. `brand_families` is the set of accepted font families for
    this run (defaults to BRAND_FAMILIES; a --brand run adds the sub-brand's
    typography overrides) — it is passed in rather than read from a mutated
    module global so concurrent or repeated runs never leak fonts into each other.
    """
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [Finding(path, 0, "major", "IO", f"cannot read: {exc}", "check the path")]

    ctx = _CheckContext(path, text, ext, palette)
    families = set(BRAND_FAMILIES) if brand_families is None else set(brand_families)

    _load_style_context(ctx)
    _check_style_blocks(ctx, families)     # 1-7: colour, fonts, italics, spacing, chevrons, tokens
    _check_rtl(ctx)                        # RTL
    if check_copy:
        _check_copy(ctx, fix_mode)         # emojis, hashtags, intensifiers, AI tells

    ctx.findings.sort(key=lambda f: (f.line, SEVERITY_ORDER[f.severity]))
    return ctx.findings


# --------------------------------------------------------------------------
# Walking + reporting
# --------------------------------------------------------------------------

def collect(paths: list[str]) -> list[str]:
    out: list[str] = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            rel = os.path.relpath(root, p)
            if any(rel.startswith(part) for part in SKIP_PATH_PARTS):
                dirs[:] = []
                continue
            for f in sorted(files):
                if os.path.splitext(f)[1].lower() in EXTENSIONS:
                    out.append(os.path.join(root, f))
    seen, uniq = set(), []
    for p in out:
        rp = os.path.realpath(p)
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def report(findings: list[Finding], scanned: int, palette: Palette,
           quiet: bool, color: bool, check_copy: bool = False) -> int:
    def c(s, code):
        return f"{code}{s}{RESET}" if color else s

    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.path, []).append(f)

    counts = {"blocker": 0, "major": 0, "minor": 0}
    for f in findings:
        counts[f.severity] += 1

    if not quiet:
        print(c("AZMX brand check", BOLD))
        print(c(f"palette: {len(palette.legal)} legal tones from "
                f"{os.path.relpath(palette.source)}", DIM))
        print(c(f"scanned: {scanned} file(s)", DIM))
        print()

    for path in sorted(by_file):
        rel = os.path.relpath(path)
        if rel.startswith(".."):
            rel = os.path.abspath(path)
        print(c(rel, BOLD))
        for f in by_file[path]:
            sev = c(f"{f.severity:<7}", SEV_COLOR[f.severity])
            print(f"  {f.line:>5}  {sev} {f.code:<8} {f.what}")
            print(f"         {c('fix:', DIM)} {f.fix}")
        print()

    # Pre-publish checklist for copy validation mode
    if check_copy and not quiet:
        print(c("PRE-PUBLISH CHECKLIST", BOLD))

        # Analyze findings by code to determine checklist status
        codes = {f.code for f in findings}

        # 1. No emojis
        has_emoji = "EMOJI" in codes
        emoji_status = "✗" if has_emoji else "✓"
        emoji_color = SEV_COLOR["major"] if has_emoji else "\033[32m"  # Green for pass
        print(f"  {c(emoji_status, emoji_color)} No emojis")

        # 2. Max 3 hashtags
        has_hashtag_violation = "HASHTAG" in codes
        hashtag_status = "✗" if has_hashtag_violation else "✓"
        hashtag_color = SEV_COLOR["major"] if has_hashtag_violation else "\033[32m"
        print(f"  {c(hashtag_status, hashtag_color)} Max 3 hashtags")

        # 3. No banned intensifiers
        has_intensifier = "INTENSIFIER" in codes
        intensifier_status = "✗" if has_intensifier else "✓"
        intensifier_color = SEV_COLOR["major"] if has_intensifier else "\033[32m"
        print(f"  {c(intensifier_status, intensifier_color)} No banned intensifiers")

        # 4. No AI-tell patterns (includes em-dashes, triads, hedging)
        # AI-tell patterns are marked with "AI-TELL" code, but exclude exclamation marks
        ai_tell_findings = [f for f in findings if f.code == "AI-TELL" and "exclamation" not in f.what.lower()]
        has_ai_tell = len(ai_tell_findings) > 0
        ai_tell_status = "✗" if has_ai_tell else "✓"
        ai_tell_color = SEV_COLOR["minor"] if has_ai_tell else "\033[32m"
        print(f"  {c(ai_tell_status, ai_tell_color)} No AI-tell patterns")

        # 5. No excessive exclamation marks
        exclamation_findings = [f for f in findings if f.code == "AI-TELL" and "exclamation" in f.what.lower()]
        has_exclamation = len(exclamation_findings) > 0
        exclamation_status = "✗" if has_exclamation else "✓"
        exclamation_color = SEV_COLOR["major"] if has_exclamation else "\033[32m"
        print(f"  {c(exclamation_status, exclamation_color)} No excessive exclamation marks")

        # 6. Clean mechanics (no style/design violations in copy context)
        # In copy mode, clean mechanics means no other issues (FONT, COLOR, SPACING, etc.)
        style_codes = {"COLOR", "FONT", "ITALIC", "SPACING", "ELECTRIC", "CHEVRON"}
        has_style_issues = bool(codes & style_codes)
        mechanics_status = "✗" if has_style_issues else "✓"
        mechanics_color = SEV_COLOR["major"] if has_style_issues else "\033[32m"
        print(f"  {c(mechanics_status, mechanics_color)} Clean mechanics")

        print()

    if not quiet:
        if findings:
            print(c(f"{counts['blocker']} blocker · {counts['major']} major · "
                    f"{counts['minor']} minor", BOLD))
        else:
            print(c("clean — no brand violations found", BOLD))

    # Same contract as every other output mode: only blockers fail the run
    return 1 if any(f.severity == "blocker" for f in findings) else 0


def json_report(findings: list[Finding], scanned: int, palette: Palette) -> int:
    """Output findings as structured JSON."""
    counts = {"blocker": 0, "major": 0, "minor": 0}
    for f in findings:
        counts[f.severity] += 1

    output = {
        "summary": {
            "scanned": scanned,
            "palette_source": os.path.relpath(palette.source),
            "palette_size": len(palette.legal),
            "total_findings": len(findings),
            "blockers": counts["blocker"],
            "major": counts["major"],
            "minor": counts["minor"]
        },
        "findings": [
            {
                "path": os.path.relpath(f.path),
                "line": f.line,
                "severity": f.severity,
                "code": f.code,
                "what": f.what,
                "fix": f.fix
            }
            for f in findings
        ]
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 1 if any(f.severity == "blocker" for f in findings) else 0


def report_aggregated(report_obj: ComplianceReport, scanned: int, palette: Palette,
                      color: bool) -> int:
    """Output an aggregated compliance report with summary statistics."""
    def c(s, code):
        return f"{code}{s}{RESET}" if color else s

    print(c("AZMX Brand Compliance Report", BOLD))
    print(c(f"palette: {len(palette.legal)} legal tones from "
            f"{os.path.relpath(palette.source)}", DIM))
    print(c(f"scanned: {scanned} file(s)", DIM))
    print()

    # Summary by severity
    sev_counts = report_obj.count_by_severity()
    print(c("Summary by Severity:", BOLD))
    for sev in ["blocker", "major", "minor"]:
        count = sev_counts[sev]
        sev_label = c(sev.upper(), SEV_COLOR[sev])
        print(f"  {sev_label:>15s}: {count}")
    print()

    # Summary by violation code
    code_counts = report_obj.count_by_code()
    if code_counts:
        print(c("Summary by Violation Type:", BOLD))
        for code in sorted(code_counts.keys()):
            print(f"  {code:<10s}: {code_counts[code]}")
        print()

    # Files affected
    files_affected = report_obj.by_file()
    print(c(f"Files Affected: {len(files_affected)}", BOLD))
    for path in sorted(files_affected.keys()):
        rel = os.path.relpath(path)
        if rel.startswith(".."):
            rel = os.path.abspath(path)
        findings_count = len(files_affected[path])
        print(f"  {rel}: {findings_count} finding(s)")
    print()

    # Final status
    if report_obj.total() > 0:
        print(c(f"Total: {report_obj.total()} finding(s) — "
                f"{sev_counts['blocker']} blocker · {sev_counts['major']} major · "
                f"{sev_counts['minor']} minor", BOLD))
    else:
        print(c("Status: CLEAN — no brand violations found", BOLD))

    return 1 if report_obj.has_blockers() else 0



class DetailedComplianceReport:
    """Aggregates brand compliance findings across multiple files."""
    __slots__ = (
        'total_files', 'pass_count', 'fail_count', 'findings_by_category',
        'severity_counts', 'top_violations', 'per_file_results', 'scan_timestamp'
    )

    def __init__(self):
        self.total_files = 0
        self.pass_count = 0  # files with no findings
        self.fail_count = 0  # files with findings
        self.findings_by_category = {}  # code -> count dict
        self.severity_counts = {"blocker": 0, "major": 0, "minor": 0}
        self.top_violations = []  # list of (code, count) tuples
        self.per_file_results = {}  # path -> list of Finding objects
        self.scan_timestamp = None

    def add_findings(self, findings: list[Finding], files_scanned: int):
        """Aggregate findings from a batch of files."""
        self.total_files = files_scanned
        self.scan_timestamp = datetime.now().isoformat()

        # Count files with/without findings
        files_with_findings = set()
        for f in findings:
            files_with_findings.add(f.path)
            self.per_file_results.setdefault(f.path, []).append(f)
            self.severity_counts[f.severity] += 1
            self.findings_by_category[f.code] = self.findings_by_category.get(f.code, 0) + 1

        self.fail_count = len(files_with_findings)
        self.pass_count = files_scanned - self.fail_count

        # Compute top violations
        violation_list = [(code, count) for code, count in self.findings_by_category.items()]
        self.top_violations = sorted(violation_list, key=lambda x: x[1], reverse=True)[:5]

    def to_json(self, include_trends=False):
        """Generate JSON report."""
        data = {
            "total_findings": sum(self.severity_counts.values()),
            "has_blockers": self.severity_counts["blocker"] > 0,
            "summary": {
                "by_severity": self.severity_counts,
                "by_code": self.findings_by_category
            },
            "files_affected": len(self.per_file_results),
            "findings": [
                {
                    "path": f.path,
                    "line": f.line,
                    "severity": f.severity,
                    "code": f.code,
                    "what": f.what,
                    "fix": f.fix
                }
                for path in sorted(self.per_file_results.keys())
                for f in self.per_file_results[path]
            ],
            "scan_timestamp": self.scan_timestamp
        }

        if include_trends:
            data["trend"] = self._compute_trends()

        return json.dumps(data, indent=2)

    def to_html(self):
        """Generate HTML report with AZMX brand styling."""
        def escape(text):
            """Escape HTML special characters."""
            return (str(text)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&#x27;"))

        total_findings = sum(self.severity_counts.values())

        # Build findings HTML
        findings_html = ""
        for path in sorted(self.per_file_results.keys()):
            findings_html += f'    <div class="file-section">\n'
            findings_html += f'      <h3>{escape(path)} ({len(self.per_file_results[path])} issues)</h3>\n'
            findings_html += f'      <ul class="findings-list">\n'
            for f in self.per_file_results[path]:
                findings_html += f'        <li class="finding {escape(f.severity)}">\n'
                findings_html += f'          <span class="severity-badge">{escape(f.severity).upper()}</span>\n'
                findings_html += f'          <span class="code">[{escape(f.code)}]</span>\n'
                findings_html += f'          Line {f.line}: {escape(f.what)}<br>\n'
                findings_html += f'          <span class="fix">Fix: {escape(f.fix)}</span>\n'
                findings_html += f'        </li>\n'
            findings_html += f'      </ul>\n'
            findings_html += f'    </div>\n'

        # Build top violations HTML
        top_violations_html = ""
        for code, count in self.top_violations:
            top_violations_html += f'      <li><strong>{escape(code)}</strong>: {count} occurrences</li>\n'

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AZMX Brand Compliance Report</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: system-ui, -apple-system, sans-serif;
      line-height: 1.6;
      color: #1a1a1a;
      background: #f5f5f5;
      padding: 24px;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 40px;
    }}

    h1 {{
      color: #001AFF;
      font-size: 32px;
      margin-bottom: 8px;
    }}

    .timestamp {{
      color: #666;
      font-size: 14px;
      margin-bottom: 32px;
    }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 40px;
    }}

    .stat-card {{
      background: #f8f9fa;
      padding: 24px;
      border-radius: 8px;
      border-left: 4px solid #001AFF;
    }}

    .stat-card h2 {{
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #666;
      margin-bottom: 8px;
    }}

    .stat-card .value {{
      font-size: 36px;
      font-weight: bold;
      color: #1a1a1a;
    }}

    .section {{
      margin-bottom: 40px;
    }}

    .section h2 {{
      font-size: 24px;
      margin-bottom: 16px;
      color: #1a1a1a;
      border-bottom: 2px solid #e0e0e0;
      padding-bottom: 8px;
    }}

    .severity-breakdown {{
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
    }}

    .severity-item {{
      flex: 1;
      min-width: 150px;
      padding: 16px;
      border-radius: 8px;
      text-align: center;
    }}

    .severity-item.blocker {{
      background: #ffe5e5;
      color: #c00;
    }}

    .severity-item.major {{
      background: #fff3cd;
      color: #856404;
    }}

    .severity-item.minor {{
      background: #e7f3ff;
      color: #004085;
    }}

    .severity-item .count {{
      font-size: 32px;
      font-weight: bold;
    }}

    .severity-item .label {{
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-top: 4px;
    }}

    .file-section {{
      margin-bottom: 32px;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 16px;
    }}

    .file-section h3 {{
      font-size: 18px;
      margin-bottom: 12px;
      color: #001AFF;
    }}

    .findings-list {{
      list-style: none;
    }}

    .finding {{
      padding: 12px;
      margin-bottom: 8px;
      border-radius: 4px;
      border-left: 4px solid;
    }}

    .finding.blocker {{
      background: #ffe5e5;
      border-left-color: #c00;
    }}

    .finding.major {{
      background: #fff3cd;
      border-left-color: #856404;
    }}

    .finding.minor {{
      background: #e7f3ff;
      border-left-color: #004085;
    }}

    .severity-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: bold;
      margin-right: 8px;
    }}

    .finding.blocker .severity-badge {{
      background: #c00;
      color: white;
    }}

    .finding.major .severity-badge {{
      background: #856404;
      color: white;
    }}

    .finding.minor .severity-badge {{
      background: #004085;
      color: white;
    }}

    .code {{
      font-family: monospace;
      color: #666;
      margin-right: 8px;
    }}

    .fix {{
      display: block;
      margin-top: 4px;
      font-size: 14px;
      color: #666;
      font-style: italic;
    }}

    ul {{
      margin-left: 24px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>AZMX Brand Compliance Report</h1>
    <div class="timestamp">Generated: {escape(self.scan_timestamp)}</div>

    <div class="summary">
      <div class="stat-card">
        <h2>Total Files</h2>
        <div class="value">{self.total_files}</div>
      </div>
      <div class="stat-card">
        <h2>Files Passed</h2>
        <div class="value">{self.pass_count}</div>
      </div>
      <div class="stat-card">
        <h2>Files Failed</h2>
        <div class="value">{self.fail_count}</div>
      </div>
      <div class="stat-card">
        <h2>Total Issues</h2>
        <div class="value">{total_findings}</div>
      </div>
    </div>

    <div class="section">
      <h2>Severity Breakdown</h2>
      <div class="severity-breakdown">
        <div class="severity-item blocker">
          <div class="count">{self.severity_counts["blocker"]}</div>
          <div class="label">Blockers</div>
        </div>
        <div class="severity-item major">
          <div class="count">{self.severity_counts["major"]}</div>
          <div class="label">Major</div>
        </div>
        <div class="severity-item minor">
          <div class="count">{self.severity_counts["minor"]}</div>
          <div class="label">Minor</div>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>Top Violations</h2>
      <ul>
{top_violations_html}      </ul>
    </div>

    <div class="section">
      <h2>Detailed Findings</h2>
{findings_html}    </div>
  </div>
</body>
</html>'''

        return html

    def to_markdown(self):
        """Generate markdown report."""
        total_findings = sum(self.severity_counts.values())

        # Emoji indicators
        severity_emoji = {
            "blocker": "🔴",
            "major": "🟡",
            "minor": "🔵"
        }

        md = f"# AZMX Brand Compliance Report\n\n"
        md += f"**Generated:** {self.scan_timestamp}\n\n"
        md += f"---\n\n"

        # Summary stats
        md += f"## Summary\n\n"
        md += f"| Metric | Value |\n"
        md += f"|--------|-------|\n"
        md += f"| Total Files Scanned | {self.total_files} |\n"
        md += f"| Files Passed | {self.pass_count} |\n"
        md += f"| Files Failed | {self.fail_count} |\n"
        md += f"| Total Issues | {total_findings} |\n"
        md += f"\n"

        # Severity breakdown
        md += f"## Severity Breakdown\n\n"
        md += f"| Severity | Count |\n"
        md += f"|----------|-------|\n"
        md += f"| {severity_emoji['blocker']} Blockers | {self.severity_counts['blocker']} |\n"
        md += f"| {severity_emoji['major']} Major | {self.severity_counts['major']} |\n"
        md += f"| {severity_emoji['minor']} Minor | {self.severity_counts['minor']} |\n"
        md += f"\n"

        # Top violations
        md += f"## Top Violations\n\n"
        for i, (code, count) in enumerate(self.top_violations, 1):
            md += f"{i}. **{code}**: {count} occurrences\n"
        md += f"\n"

        # Detailed findings
        md += f"## Detailed Findings\n\n"
        for path in sorted(self.per_file_results.keys()):
            md += f"### {path}\n\n"
            md += f"**Issues:** {len(self.per_file_results[path])}\n\n"
            for f in self.per_file_results[path]:
                emoji = severity_emoji.get(f.severity, "")
                md += f"- {emoji} **{f.severity.upper()}** [{f.code}] Line {f.line}\n"
                md += f"  - **What:** {f.what}\n"
                md += f"  - **Fix:** {f.fix}\n"
            md += f"\n"

        return md

    def _get_history_dir(self):
        """Get directory for storing historical reports."""
        return ".brand-reports"

    def _load_latest_history(self):
        """Load most recent historical report from .brand-reports/ directory."""
        history_dir = self._get_history_dir()
        if not os.path.exists(history_dir):
            return None

        reports = glob.glob(os.path.join(history_dir, "*.json"))
        if not reports:
            return None

        # Sort by modification time, get most recent
        reports.sort(key=os.path.getmtime, reverse=True)

        try:
            with open(reports[0], 'r') as f:
                return json.load(f)
        except:
            return None

    def _compute_trends(self):
        """Compare current report with historical report."""
        prev = self._load_latest_history()

        if not prev:
            return {
                "status": "no_history",
                "message": "No historical data available for comparison",
                "previous_report": None,
                "changes": None
            }

        current_total = sum(self.severity_counts.values())
        prev_total = prev.get("total_findings", 0)
        delta = current_total - prev_total

        if delta < 0:
            status = "improved"
            message = f"Violations decreased by {abs(delta)} ({prev_total} → {current_total})"
        elif delta > 0:
            status = "degraded"
            message = f"Violations increased by {delta} ({prev_total} → {current_total})"
        else:
            status = "stable"
            message = f"No change in total violations ({current_total})"

        return {
            "status": status,
            "message": message,
            "previous_report": {
                "timestamp": prev.get("scan_timestamp"),
                "total_findings": prev_total,
                "by_severity": prev.get("summary", {}).get("by_severity", {}),
                "by_code": prev.get("summary", {}).get("by_code", {})
            },
            "changes": {
                "total": delta,
                "by_severity": {
                    sev: self.severity_counts[sev] - prev.get("summary", {}).get("by_severity", {}).get(sev, 0)
                    for sev in ("blocker", "major", "minor")
                },
                "by_code": {
                    code: self.findings_by_category.get(code, 0) - prev.get("summary", {}).get("by_code", {}).get(code, 0)
                    for code in set(list(self.findings_by_category.keys()) + list(prev.get("summary", {}).get("by_code", {}).keys()))
                }
            }
        }

    def save_to_history(self):
        """Save current report to .brand-reports/ directory for future comparisons."""
        history_dir = self._get_history_dir()
        os.makedirs(history_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = self.scan_timestamp.replace(":", "-").replace(".", "-")
        filename = os.path.join(history_dir, f"report-{timestamp}.json")

        # Save as JSON
        with open(filename, 'w') as f:
            f.write(self.to_json(include_trends=False))

        # Cleanup old reports (keep last 10)
        self._cleanup_old_reports()

    def _cleanup_old_reports(self):
        """Keep only the 10 most recent reports."""
        history_dir = self._get_history_dir()
        reports = glob.glob(os.path.join(history_dir, "*.json"))

        if len(reports) > 10:
            # Sort by modification time
            reports.sort(key=os.path.getmtime, reverse=True)
            # Remove old reports
            for old_report in reports[10:]:
                os.remove(old_report)

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="AZMX brand linter — checks files against the brand system",
        epilog="With no paths, scans the whole repo. Exits 1 if any blocker found."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="files or directories to check (default: whole repo)"
    )
    parser.add_argument(
        "--brand",
        metavar="NAME",
        help="sub-brand to validate against (colab, majarah, clix, anatomi). "
             "Loads brand-specific custom primitives in addition to base palette."
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="suppress header and summary output"
    )

    parser.add_argument("--copy", action="store_true", help="enable prose validation")
    parser.add_argument("--json", action="store_true", help="output detailed JSON findings")
    parser.add_argument("--fix", action="store_true", help="include replacement suggestions")
    parser.add_argument("--report", action="store_true", help="output aggregated summary")
    parser.add_argument("--with-trends", action="store_true", help="include historical trends")
    parser.add_argument("--format", choices=["text", "json", "html", "markdown"], default="text")
    parser.add_argument("--output", help="write report to a file")
    parser.add_argument("--save-history", action="store_true", help="save compliance report history")
    args = parser.parse_intermixed_args(argv)
    quiet = args.quiet
    check_copy = args.copy
    json_output = args.json
    fix_mode = args.fix
    use_report = args.report
    with_trends = args.with_trends
    output_format = args.format
    output_path = args.output

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = args.paths if args.paths else [repo_root]

    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        for p in missing:
            print(f"brand-check: no such file or directory: {p}", file=sys.stderr)
        return 2

    colors_md = find_colors_md(paths[0]) or find_colors_md(repo_root)
    if not colors_md:
        print("brand-check: could not locate references/colors.md", file=sys.stderr)
        return 2

    palette = load_palette(colors_md, args.brand)
    families = allowed_font_families(colors_md, args.brand)

    files = collect(paths)
    findings: list[Finding] = []
    for f in files:
        findings.extend(check_file(f, palette, check_copy, fix_mode, families))

    if json_output and "--format" not in argv:
        return json_report(findings, len(files), palette)

    if use_report and output_format != "text":
        detailed = DetailedComplianceReport()
        detailed.add_findings(findings, len(files))
        if output_format == "json":
            output = detailed.to_json(include_trends=with_trends)
        elif output_format == "html":
            output = detailed.to_html()
        else:
            output = detailed.to_markdown()
        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(output)
        else:
            print(output)
        if with_trends or args.save_history:
            detailed.save_to_history()
        return 1 if detailed.severity_counts["blocker"] else 0

    color = sys.stdout.isatty()

    # Handle JSON output format
    if output_format == "json":
        compliance = ComplianceReport(findings)
        json_data = compliance.to_json(include_trends=with_trends)
        json_output = json.dumps(json_data, indent=2)

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(json_output)
        else:
            print(json_output)

        # Save to history if trends were requested
        if with_trends:
            compliance.save_to_history()

        return 1 if compliance.has_blockers() else 0

    # Handle HTML output format
    if output_format == "html":
        compliance = ComplianceReport(findings)
        palette_info = f"{len(palette.legal)} legal tones from {os.path.relpath(palette.source)}"
        html_output = compliance.to_html(len(files), palette_info)

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(html_output)
        else:
            print(html_output)

        return 1 if compliance.has_blockers() else 0

    # Handle Markdown output format
    if output_format == "markdown":
        compliance = ComplianceReport(findings)
        palette_info = f"{len(palette.legal)} legal tones from {os.path.relpath(palette.source)}"
        markdown_output = compliance.to_markdown(len(files), palette_info)

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(markdown_output)
        else:
            print(markdown_output)

        return 1 if compliance.has_blockers() else 0

    # Handle text output format
    if use_report:
        compliance = ComplianceReport(findings)
        return report_aggregated(compliance, len(files), palette, color)
    else:
        return report(findings, len(files), palette, quiet, color, check_copy)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
