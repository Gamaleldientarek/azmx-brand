#!/usr/bin/env python3
"""
extract-metrics.py — AZMX brand metrics extractor.

Extracts brand compliance metrics from HTML/CSS files by reusing brand-check.py
validation logic. Outputs metrics about colors, fonts, spacing, and other brand
elements used in the file.

Usage:
    python3 scripts/extract-metrics.py <file> [--json]

With --json, outputs structured JSON metrics. Otherwise, outputs human-readable text.
"""

from __future__ import annotations

import bisect
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Config (reused from brand-check.py)
# --------------------------------------------------------------------------

SPACING_SCALE = (8, 16, 24, 40, 64, 96, 128, 160)

BRAND_FAMILIES = {
    "thmanyah serif display",
    "azm x",
    "azm x variable",
}

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

SWATCH_CLASS = re.compile(
    r"\b(sw|swatch|swatches|chip|dot|pdot|cdot|hexdot|color-?chip|color-?dot|"
    r"colour-?chip|colour-?dot|legend-?key)\b"
)

# --------------------------------------------------------------------------
# Palette (reused from brand-check.py)
# --------------------------------------------------------------------------

HEX_RE = re.compile(r"#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3,4})\b")


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


class Palette:
    def __init__(self, legal: dict[str, str], source: str):
        self.legal = legal
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


def load_palette(colors_md: str) -> Palette:
    """Parse every hex in the markdown tables."""
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
        raise SystemExit(f"extract-metrics: no hex values found in {colors_md}")
    return Palette(legal, colors_md)


# --------------------------------------------------------------------------
# Source extraction (reused from brand-check.py)
# --------------------------------------------------------------------------

STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
STYLE_ATTR_RE = re.compile(r"""\bstyle\s*=\s*(["'])(.*?)\1""", re.S | re.I)
PRESENT_ATTR_RE = re.compile(
    r"""\b(fill|stroke|stop-color|flood-color|lighting-color|color|font-family|font-style)"""
    r"""\s*=\s*(["'])(.*?)\2""",
    re.S | re.I,
)


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
    """Return [(offset, source, kind, owner_tag)] regions of CSS-ish content."""
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

    return regions


# --------------------------------------------------------------------------
# CSS parsing (reused from brand-check.py)
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
    stack: list[tuple[int, bool]] = []
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
# Value helpers (reused from brand-check.py)
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
    """Every px length in the value."""
    return [(abs(float(m.group(1))), m.group(0))
            for m in re.finditer(r"(-?\d*\.?\d+)px\b", value)]


def is_swatch(owner_tag: str) -> bool:
    m = re.search(r"""\bclass\s*=\s*(["'])(.*?)\1""", owner_tag, re.I | re.S)
    return bool(m and SWATCH_CLASS.search(m.group(2)))


# --------------------------------------------------------------------------
# Tone/Voice analysis
# --------------------------------------------------------------------------

# Banned intensifiers and empty phrases from voice-and-tone.md
EMPTY_INTENSIFIERS = re.compile(
    r"\b(truly|seamlessly|effortlessly|robust|leverage|elevate|unlock|empower|delve)\b",
    re.I
)

# Hedging phrases
HEDGING_PHRASES = re.compile(r"\b(can help|may enable|might help|could enable)\b", re.I)

# Em-dash pattern
EM_DASH_RE = re.compile(r"[—–]")

# Triads: comma-separated 3-item lists
TRIAD_RE = re.compile(r"\b\w+,\s+\w+,\s+and\s+\w+\b")

# Emoji pattern (basic Unicode emoji ranges)
EMOJI_RE = re.compile(
    r"[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|"
    r"[\U0001F1E0-\U0001F1FF]|[\U00002700-\U000027BF]|[\U0001F900-\U0001F9FF]|"
    r"[\U0001FA70-\U0001FAFF]|[\U00002600-\U000026FF]"
)

# Hashtag pattern
HASHTAG_RE = re.compile(r"#\w+")

# Exclamation marks
EXCLAMATION_RE = re.compile(r"!")

# All-caps words (excluding single letters and common acronyms)
ALL_CAPS_RE = re.compile(r"\b[A-Z]{2,}\b")


def extract_text_content(html: str) -> str:
    """Extract visible text content from HTML, excluding scripts, styles, and tags."""
    # Remove script and style blocks
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&mdash;", "—")
    text = text.replace("&ndash;", "–")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def analyze_tone_metrics(text: str) -> dict:
    """Analyze text for tone/voice compliance issues."""
    if not text:
        return {
            "total_words": 0,
            "total_sentences": 0,
            "issues": {},
        }

    # Count words and sentences
    words = text.split()
    total_words = len(words)
    sentences = re.split(r"[.!?]+", text)
    total_sentences = len([s for s in sentences if s.strip()])

    # Detect issues
    intensifiers = EMPTY_INTENSIFIERS.findall(text)
    hedging = HEDGING_PHRASES.findall(text)
    em_dashes = EM_DASH_RE.findall(text)
    triads = TRIAD_RE.findall(text)
    emojis = EMOJI_RE.findall(text)
    hashtags = HASHTAG_RE.findall(text)
    exclamations = EXCLAMATION_RE.findall(text)
    all_caps_words = ALL_CAPS_RE.findall(text)

    # Filter out common acronyms that are acceptable
    common_acronyms = {"AZMX", "AZM", "CSS", "HTML", "API", "UI", "UX", "CEO", "CTO", "USA", "UK"}
    problematic_caps = [w for w in all_caps_words if w not in common_acronyms]

    return {
        "total_words": total_words,
        "total_sentences": total_sentences,
        "issues": {
            "empty_intensifiers": {
                "count": len(intensifiers),
                "instances": intensifiers[:10],  # First 10 instances
            },
            "hedging_phrases": {
                "count": len(hedging),
                "instances": hedging[:10],
            },
            "em_dashes": {
                "count": len(em_dashes),
                "rate_per_100_words": (len(em_dashes) / total_words * 100) if total_words > 0 else 0,
            },
            "triads": {
                "count": len(triads),
                "instances": triads[:10],
            },
            "emojis": {
                "count": len(emojis),
                "instances": emojis[:10],
            },
            "hashtags": {
                "count": len(hashtags),
                "instances": hashtags,
                "over_limit": len(hashtags) > 3,
            },
            "exclamation_marks": {
                "count": len(exclamations),
                "rate_per_100_words": (len(exclamations) / total_words * 100) if total_words > 0 else 0,
            },
            "all_caps_words": {
                "count": len(problematic_caps),
                "instances": problematic_caps[:10],
            },
        },
        "compliance_score": calculate_tone_compliance_score(
            total_words,
            len(intensifiers),
            len(hedging),
            len(em_dashes),
            len(triads),
            len(emojis),
            len(exclamations),
            len(problematic_caps),
        ),
    }


def calculate_tone_compliance_score(
    total_words: int,
    intensifiers: int,
    hedging: int,
    em_dashes: int,
    triads: int,
    emojis: int,
    exclamations: int,
    caps_words: int,
) -> float:
    """Calculate overall tone compliance score (0-1, higher is better)."""
    if total_words == 0:
        return 1.0

    # Deduct points for each issue type
    score = 1.0

    # Empty intensifiers: -0.02 per occurrence (up to -0.2)
    score -= min(0.2, intensifiers * 0.02)

    # Hedging: -0.03 per occurrence (up to -0.15)
    score -= min(0.15, hedging * 0.03)

    # Em-dashes: -0.01 per dash if excessive (>1 per 100 words)
    em_dash_rate = (em_dashes / total_words * 100) if total_words > 0 else 0
    if em_dash_rate > 1:
        score -= min(0.15, (em_dash_rate - 1) * 0.03)

    # Triads: -0.03 per triad (up to -0.15)
    score -= min(0.15, triads * 0.03)

    # Emojis: -0.1 per emoji (severe penalty, banned in copy)
    score -= min(0.3, emojis * 0.1)

    # Exclamations: -0.01 per exclamation if excessive (>0.5 per 100 words)
    exclamation_rate = (exclamations / total_words * 100) if total_words > 0 else 0
    if exclamation_rate > 0.5:
        score -= min(0.1, (exclamation_rate - 0.5) * 0.02)

    # All-caps words: -0.02 per word (up to -0.1)
    score -= min(0.1, caps_words * 0.02)

    return max(0.0, score)


# --------------------------------------------------------------------------
# Metrics extraction
# --------------------------------------------------------------------------

def extract_metrics(path: str, palette: Palette) -> dict:
    """Extract brand compliance metrics from a file."""
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return {"error": f"cannot read: {exc}"}

    regions = css_regions(text, ext)

    all_blocks: list[Block] = []
    for off, src, kind, owner in regions:
        if kind == "css":
            all_blocks.extend(parse_blocks(src, off, owner))
        else:
            all_blocks.append(Block("", parse_decls(src, off), off, owner))

    custom: dict[str, str] = {}
    for b in all_blocks:
        for d in b.decls:
            if d.prop.startswith("--"):
                custom.setdefault(d.prop, d.value)
    for k in list(custom):
        custom[k] = resolve_vars(custom[k], custom)

    # Color metrics
    colors_used: set[str] = set()
    colors_legal: set[str] = set()
    colors_illegal: set[str] = set()
    electric_usage_count = 0

    # Font metrics
    fonts_used: set[str] = set()
    brand_fonts_used: set[str] = set()
    non_brand_fonts_used: set[str] = set()
    italic_usage_count = 0

    # Spacing metrics
    spacing_values: list[float] = []
    off_scale_spacing: list[float] = []

    # Chevron metrics
    chevron_count = 0

    for b in all_blocks:
        swatch = is_swatch(b.owner_tag)

        for d in b.decls:
            prop, value = d.prop, d.value

            # Color extraction
            if not swatch:
                for norm, raw in hexes_in(value):
                    colors_used.add(norm)
                    if palette.is_legal(norm):
                        colors_legal.add(norm)
                    else:
                        colors_illegal.add(norm)
                    if norm == "#001AFF":
                        electric_usage_count += 1

            # Font extraction
            if prop == "font-family" or (prop.startswith("--") and "font" in prop):
                fams = split_families(resolve_vars(value, custom))
                for fam in fams:
                    low = fam.lower()
                    if not low or low.startswith("var(") or low in GENERIC_FAMILIES:
                        continue
                    fonts_used.add(fam)
                    if low in BRAND_FAMILIES:
                        brand_fonts_used.add(fam)
                    else:
                        non_brand_fonts_used.add(fam)
            elif prop == "font" and ("\"" in value or "'" in value):
                for fam in re.findall(r"""["']([^"']+)["']""", value):
                    fonts_used.add(fam)
                    if fam.lower() in BRAND_FAMILIES:
                        brand_fonts_used.add(fam)
                    else:
                        non_brand_fonts_used.add(fam)

            # Italic usage
            if prop == "font-style" and re.search(r"\b(italic|oblique)\b", value, re.I):
                italic_usage_count += 1

            # Spacing extraction
            if SPACING_PROPS.match(prop):
                for val, raw in px_values(resolve_vars(value, custom)):
                    spacing_values.append(val)
                    if val != 0 and val not in SPACING_SCALE:
                        off_scale_spacing.append(val)

            # Chevron detection
            if prop in ("background", "background-image", "mask", "mask-image",
                        "-webkit-mask", "-webkit-mask-image", "content", "list-style-image"):
                for m in FUNC_URL_RE.finditer(value):
                    if CHEVRON_WORD.search(m.group(2)):
                        chevron_count += 1

    # Tone/voice metrics (for HTML/text files)
    tone_metrics = {}
    if ext in (".html", ".htm", ".md", ".txt"):
        text_content = extract_text_content(text) if ext in (".html", ".htm") else text
        tone_metrics = analyze_tone_metrics(text_content)

    return {
        "file": path,
        "color_metrics": {
            "total_colors": len(colors_used),
            "legal_colors": len(colors_legal),
            "illegal_colors": len(colors_illegal),
            "colors_used": sorted(list(colors_used)),
            "legal_colors_list": sorted(list(colors_legal)),
            "illegal_colors_list": sorted(list(colors_illegal)),
            "electric_usage_count": electric_usage_count,
            "palette_compliance_rate": len(colors_legal) / len(colors_used) if colors_used else 1.0,
        },
        "font_metrics": {
            "total_fonts": len(fonts_used),
            "brand_fonts": len(brand_fonts_used),
            "non_brand_fonts": len(non_brand_fonts_used),
            "fonts_used": sorted(list(fonts_used)),
            "brand_fonts_list": sorted(list(brand_fonts_used)),
            "non_brand_fonts_list": sorted(list(non_brand_fonts_used)),
            "italic_usage_count": italic_usage_count,
            "brand_compliance_rate": len(brand_fonts_used) / len(fonts_used) if fonts_used else 1.0,
        },
        "spacing_metrics": {
            "total_spacing_values": len(spacing_values),
            "off_scale_count": len(off_scale_spacing),
            "spacing_values_used": sorted(list(set(spacing_values))),
            "off_scale_values": sorted(list(set(off_scale_spacing))),
            "spacing_compliance_rate": (len(spacing_values) - len(off_scale_spacing)) / len(spacing_values) if spacing_values else 1.0,
        },
        "chevron_metrics": {
            "chevron_usage_count": chevron_count,
        },
        "tone_metrics": tone_metrics,
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if not argv or "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0

    use_json = "--json" in argv
    args = [a for a in argv if not a.startswith("-")]

    if not args:
        print("extract-metrics: no file specified", file=sys.stderr)
        return 2

    path = args[0]
    if not os.path.isfile(path):
        print(f"extract-metrics: file not found: {path}", file=sys.stderr)
        return 2

    colors_md = find_colors_md(path)
    if not colors_md:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        colors_md = find_colors_md(repo_root)
    if not colors_md:
        print("extract-metrics: could not locate references/colors.md", file=sys.stderr)
        return 2

    palette = load_palette(colors_md)
    metrics = extract_metrics(path, palette)

    if use_json:
        print(json.dumps(metrics, indent=2))
    else:
        print(f"File: {metrics['file']}")
        print()
        print("Color Metrics:")
        print(f"  Total colors used: {metrics['color_metrics']['total_colors']}")
        print(f"  Legal colors: {metrics['color_metrics']['legal_colors']}")
        print(f"  Illegal colors: {metrics['color_metrics']['illegal_colors']}")
        print(f"  Palette compliance: {metrics['color_metrics']['palette_compliance_rate']:.1%}")
        print(f"  Electric usage: {metrics['color_metrics']['electric_usage_count']}")
        print()
        print("Font Metrics:")
        print(f"  Total fonts used: {metrics['font_metrics']['total_fonts']}")
        print(f"  Brand fonts: {metrics['font_metrics']['brand_fonts']}")
        print(f"  Non-brand fonts: {metrics['font_metrics']['non_brand_fonts']}")
        print(f"  Brand compliance: {metrics['font_metrics']['brand_compliance_rate']:.1%}")
        print(f"  Italic usage: {metrics['font_metrics']['italic_usage_count']}")
        print()
        print("Spacing Metrics:")
        print(f"  Total spacing values: {metrics['spacing_metrics']['total_spacing_values']}")
        print(f"  Off-scale values: {metrics['spacing_metrics']['off_scale_count']}")
        print(f"  Spacing compliance: {metrics['spacing_metrics']['spacing_compliance_rate']:.1%}")
        print()
        print("Chevron Metrics:")
        print(f"  Chevron usage: {metrics['chevron_metrics']['chevron_usage_count']}")

        if metrics.get('tone_metrics'):
            print()
            print("Tone/Voice Metrics:")
            tm = metrics['tone_metrics']
            print(f"  Total words: {tm['total_words']}")
            print(f"  Total sentences: {tm['total_sentences']}")
            print(f"  Compliance score: {tm['compliance_score']:.1%}")
            if tm['issues']:
                print("  Issues:")
                if tm['issues']['empty_intensifiers']['count'] > 0:
                    print(f"    Empty intensifiers: {tm['issues']['empty_intensifiers']['count']}")
                if tm['issues']['hedging_phrases']['count'] > 0:
                    print(f"    Hedging phrases: {tm['issues']['hedging_phrases']['count']}")
                if tm['issues']['em_dashes']['count'] > 0:
                    print(f"    Em-dashes: {tm['issues']['em_dashes']['count']}")
                if tm['issues']['triads']['count'] > 0:
                    print(f"    Triads: {tm['issues']['triads']['count']}")
                if tm['issues']['emojis']['count'] > 0:
                    print(f"    Emojis: {tm['issues']['emojis']['count']} (banned in copy)")
                if tm['issues']['hashtags']['count'] > 0:
                    print(f"    Hashtags: {tm['issues']['hashtags']['count']} (max 3)")
                if tm['issues']['exclamation_marks']['count'] > 0:
                    print(f"    Exclamation marks: {tm['issues']['exclamation_marks']['count']}")
                if tm['issues']['all_caps_words']['count'] > 0:
                    print(f"    All-caps words: {tm['issues']['all_caps_words']['count']}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
