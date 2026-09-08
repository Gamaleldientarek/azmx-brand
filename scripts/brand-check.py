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
  7. Emojis in prose content (when --copy flag is enabled)
  8. Hashtag counting per post with 3-max validation (when --copy flag is enabled)
  9. Banned intensifiers and corporate jargon (when --copy flag is enabled)
  10. AI-tell patterns: em-dash overuse, triads, exclamation marks, hedging (when --copy flag is enabled)

The legal palette is parsed from references/colors.md AT RUNTIME, so the linter
never goes stale when the brand changes.

Usage:
    python3 scripts/brand-check.py [file-or-dir ...] [--quiet] [--copy] [--json] [--fix]

Options:
    --quiet, -q    Suppress summary output
    --copy         Enable prose/copy validation (emoji, hashtags, intensifiers, AI-tell patterns)
    --json         Output findings as structured JSON
    --fix          Enable fix suggestions with specific word replacements

With no paths it scans the whole repo. Exits 1 if any blocker was found.
"""

from __future__ import annotations

import bisect
import json
import os
import re
import sys

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

# Banned intensifiers and corporate jargon that dilute brand voice
BANNED_INTENSIFIER = re.compile(
    r"\b(truly|leverage|robust|seamlessly|empower|synergy|paradigm|"
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
    "empower": ["enable", "allow", "help"],
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

# AI-tell pattern detection: em-dash overuse
# Em-dash (—) is often overused in AI-generated content
EM_DASH_RE = re.compile(r"—")

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
# Words that weaken statements and are common in AI output
HEDGING_RE = re.compile(
    r"\b(might|perhaps|possibly|somewhat|relatively|fairly|"
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


def load_palette(colors_md: str) -> Palette:
    """
    Parse every hex in the markdown tables. Rows carrying exactly one hex also
    donate their first cell as the token name.
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
    return Palette(legal, colors_md)


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


def check_file(path: str, palette: Palette, check_copy: bool = False, fix_mode: bool = False) -> list[Finding]:
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [Finding(path, 0, "major", "IO", f"cannot read: {exc}", "check the path")]

    nl = [i for i, c in enumerate(text) if c == "\n"]
    def line_of(off: int) -> int:
        return bisect.bisect_right(nl, off) + 1

    regions = css_regions(text, ext)

    # Pass 1 — gather custom properties and per-selector text colours.
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

    text_color_by_base: dict[str, str] = {}
    for b in all_blocks:
        if not b.selector:
            continue
        for d in b.decls:
            if d.prop == "color":
                h = first_color_hex(d.value, custom)
                if h:
                    text_color_by_base.setdefault(base_selector(b.selector), h)

    findings: list[Finding] = []
    seen: set[tuple[int, str, str]] = set()

    def add(off, severity, code, what, fix):
        ln = line_of(off)
        key = (ln, code, what)
        if key in seen:
            return
        seen.add(key)
        findings.append(Finding(path, ln, severity, code, what, fix))

    for b in all_blocks:
        swatch = is_swatch(b.owner_tag)
        bg_hex = None
        color_hex = None
        color_off = None
        bg_off = None

        for d in b.decls:
            prop, value = d.prop, d.value

            # ---- 1. palette -------------------------------------------------
            if not swatch:
                resolved_for_hex = value
                for norm, raw in hexes_in(resolved_for_hex):
                    if palette.is_legal(norm):
                        continue
                    near, near_name, dist = palette.nearest(norm)
                    sev = "minor" if dist <= 12 else "major"
                    tail = " (near-miss — snap it)" if sev == "minor" else ""
                    add(d.offset, sev, "COLOR",
                        f"{raw} in `{prop}` is not in the palette{tail}",
                        f"use {near_name} {near} (ΔRGB {dist:.0f}) "
                        f"or add the tone to references/colors.md")

            # ---- 2. fonts ---------------------------------------------------
            if prop == "font-family" or (prop.startswith("--") and "font" in prop):
                fams = split_families(resolve_vars(value, custom))
                if fams and not (len(fams) == 1 and fams[0].lower() in GENERIC_FAMILIES):
                    for idx, fam in enumerate(fams):
                        low = fam.lower()
                        if low in BRAND_FAMILIES or low in GENERIC_FAMILIES:
                            continue
                        if low.startswith("var(") or not low:
                            continue
                        primary = idx == 0
                        add(d.offset,
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
                    if fam.lower() not in BRAND_FAMILIES:
                        add(d.offset, "blocker", "FONT",
                            f"non-brand font family \"{fam}\" in the `font` shorthand",
                            "use \"thmanyah serif display\" or \"Azm X\".")

            # ---- 3. italics -------------------------------------------------
            if prop == "font-style" and re.search(r"\b(italic|oblique)\b", value, re.I):
                add(d.offset, "blocker", "ITALIC",
                    f"`font-style: {value.strip()}`",
                    "no italics anywhere — thmanyah serif display ships no italic, so "
                    "this renders a faux slant. Express emphasis with scale, weight, or colour.")

            # ---- 4. spacing scale -------------------------------------------
            if SPACING_PROPS.match(prop):
                for val, raw in px_values(resolve_vars(value, custom)):
                    if val == 0 or val in SPACING_SCALE:
                        continue
                    near = min(SPACING_SCALE, key=lambda s: abs(s - val))
                    add(d.offset, "minor", "SPACING",
                        f"`{prop}: … {raw} …` is off the spacing scale",
                        f"use {near}px. The only permitted values are "
                        f"{' · '.join(str(s) for s in SPACING_SCALE)}.")

            # ---- 5/6 collect for block-level checks -------------------------
            if prop in ("background", "background-color", "background-image"):
                h = first_color_hex(value, custom)
                if h and bg_hex is None:
                    bg_hex, bg_off = h, d.offset
            if prop == "color":
                h = first_color_hex(value, custom)
                if h and color_hex is None:
                    color_hex, color_off = h, d.offset

            # ---- 6. chevrons as decoration ----------------------------------
            if prop in ("background", "background-image", "mask", "mask-image",
                        "-webkit-mask", "-webkit-mask-image", "content", "list-style-image"):
                for m in FUNC_URL_RE.finditer(value):
                    if CHEVRON_WORD.search(m.group(2)):
                        add(d.offset, "blocker", "CHEVRON",
                            f"chevron/arrow asset used as a background in `{prop}`: {m.group(2)}",
                            "chevrons as background decoration are banned (design-system v1.1). "
                            "Backgrounds stay solid or gradient. Use the chevron functionally: "
                            "photo mask, section tick, or list bullet.")

        # low-opacity chevron field
        chevron_ctx = CHEVRON_WORD.search(b.selector or "") or \
            CHEVRON_WORD.search(b.owner_tag or "")
        if chevron_ctx:
            for d in b.decls:
                if d.prop == "opacity":
                    try:
                        o = float(d.value.strip().rstrip("%"))
                        if d.value.strip().endswith("%"):
                            o /= 100.0
                    except ValueError:
                        continue
                    if 0 < o < 0.5:
                        add(d.offset, "major", "CHEVRON",
                            f"chevron element at opacity {d.value.strip()} "
                            f"(selector `{b.selector or b.owner_tag[:40]}`)",
                            "ghost / low-opacity chevron field textures are banned. "
                            "Either make it a functional foreground chevron at full "
                            "strength, or remove it and use negative space.")

        # ---- 5. Electric on dark / Electric behind text ----------------------
        if not swatch:
            electric = "#001AFF"
            if color_hex == electric and bg_hex and luminance(bg_hex) < 0.35:
                add(color_off, "blocker", "ELECTRIC",
                    f"Electric #001AFF set as text over the dark surface {bg_hex} "
                    f"(selector `{b.selector or 'inline style'}`)",
                    "Electric fails contrast on dark. Use Light Blue #5D8FFF for the "
                    "accent on dark surfaces, White #FFFFFF for titles, "
                    "Blue 100 #DDE8FF for body.")
            if bg_hex == electric:
                inherited = text_color_by_base.get(base_selector(b.selector), None) \
                    if b.selector else None
                if color_hex or inherited:
                    add(bg_off, "major", "ELECTRIC",
                        f"Electric #001AFF used as a fill behind text "
                        f"(selector `{b.selector or 'inline style'}`)",
                        "Electric is punctuation, never a large fill behind text (it vibrates). "
                        "Fill with Dark Navy #040038 or Blue 50 #F0F5FF, and keep Electric "
                        "for the accent mark, rule, or single highlighted word.")

    # ---- 7. Emoji detection in prose content (copy validation mode) ----------
    if check_copy:
        prose = extract_prose_content(text, ext)
        for emoji_off, emoji_text in emojis_in(prose):
            # Map prose offset back to original text offset
            # For simplicity, scan original text for emojis
            pass

        # Scan original text for emojis with line references
        for emoji_off, emoji_text in emojis_in(text):
            # Skip emojis in code blocks for markdown
            if ext == ".md":
                # Check if emoji is in a fenced code block
                in_code_block = False
                lines_before = text[:emoji_off].split('\n')
                fence_count = 0
                for line in lines_before:
                    if re.match(r'^[ \t]*(?:```+|~~~+)', line):
                        fence_count += 1
                # If fence_count is odd, we're inside a code block
                if fence_count % 2 == 1:
                    in_code_block = True

                # Skip if in code block
                if in_code_block:
                    continue

            add(emoji_off, "major", "EMOJI",
                f"emoji '{emoji_text}' found in prose",
                "emojis are not part of the brand voice. Use descriptive text instead.")

    # ---- 8. Hashtag counting per post (copy validation mode) ------------------
    if check_copy:
        prose = extract_prose_content(text, ext)
        posts = parse_posts(prose)

        for post_start, post_end, post_text in posts:
            hashtags = hashtags_in(post_text)
            hashtag_count = len(hashtags)

            # Flag violation if more than 3 hashtags in a post
            if hashtag_count > 3:
                # Report at the position of the first hashtag in the post
                # Map back to original text offset
                first_hashtag_in_prose = post_start + hashtags[0][0] if hashtags else post_start

                # Find corresponding position in original text
                # For simplicity, use the post start position
                add(first_hashtag_in_prose, "major", "HASHTAG",
                    f"{hashtag_count} hashtags in post (max 3 allowed)",
                    f"reduce hashtag count to 3 or fewer. Found: {', '.join(h[1] for h in hashtags)}")

    # ---- 9. Banned intensifier detection (copy validation mode) ---------------
    if check_copy:
        prose = extract_prose_content(text, ext)

        # Scan original text for banned intensifiers with line references
        for word_off, word_text in banned_intensifiers_in(text):
            # Skip words in code blocks for markdown
            if ext == ".md":
                # Check if word is in a fenced code block
                in_code_block = False
                lines_before = text[:word_off].split('\n')
                fence_count = 0
                for line in lines_before:
                    if re.match(r'^[ \t]*(?:```+|~~~+)', line):
                        fence_count += 1
                # If fence_count is odd, we're inside a code block
                if fence_count % 2 == 1:
                    in_code_block = True

                # Skip if in code block
                if in_code_block:
                    continue

            # Generate fix suggestion
            if fix_mode:
                word_lower = word_text.lower()
                suggestions = WORD_SUGGESTIONS.get(word_lower, [])
                if suggestions:
                    fix_msg = f"replace '{word_text}' with: {', '.join(suggestions)}"
                else:
                    fix_msg = "avoid corporate jargon and intensifiers. Use direct, clear language instead."
            else:
                fix_msg = "avoid corporate jargon and intensifiers. Use direct, clear language instead."

            add(word_off, "major", "INTENSIFIER",
                f"banned intensifier '{word_text}' found in prose",
                fix_msg)

    # ---- 10. AI-tell pattern detection (copy validation mode) -----------------
    if check_copy:
        # Helper function to check if offset is in code block
        def is_in_code_block(offset: int) -> bool:
            if ext != ".md":
                return False
            lines_before = text[:offset].split('\n')
            fence_count = 0
            for line in lines_before:
                if re.match(r'^[ \t]*(?:```+|~~~+)', line):
                    fence_count += 1
            return fence_count % 2 == 1

        # Em-dash detection
        em_dashes = em_dashes_in(text)
        if len(em_dashes) > 2:
            # Flag if more than 2 em-dashes in the file
            first_em_off, first_em_text = em_dashes[0]
            if not is_in_code_block(first_em_off):
                add(first_em_off, "minor", "AI-TELL",
                    f"{len(em_dashes)} em-dashes found (common AI pattern)",
                    "em-dashes are overused in AI-generated content. Use sparingly or replace with periods.")

        # Triad detection
        for triad_off, triad_text in triads_in(text):
            if not is_in_code_block(triad_off):
                add(triad_off, "minor", "AI-TELL",
                    f"triad pattern '{triad_text}' (common AI pattern)",
                    "lists of three items are overused in AI-generated content. Vary sentence structure.")

        # Multiple exclamation marks
        for excl_off, excl_text in multiple_exclamations_in(text):
            if not is_in_code_block(excl_off):
                add(excl_off, "major", "AI-TELL",
                    f"multiple exclamation marks '{excl_text}' found",
                    "avoid multiple exclamation marks. Use one or none.")

        # Hedging language
        for hedge_off, hedge_text in hedging_in(text):
            if not is_in_code_block(hedge_off):
                add(hedge_off, "minor", "AI-TELL",
                    f"hedging word '{hedge_text}' (weakens brand voice)",
                    "avoid hedging language. Make direct, confident statements.")

    findings.sort(key=lambda f: (f.line, SEVERITY_ORDER[f.severity]))
    return findings


def check_copy_file(path: str, palette: Palette, fix_mode: bool = False) -> list[Finding]:
    """
    Check a text file for copy/prose validation issues only.
    This function focuses on prose content validation:
    - Emoji detection
    - Hashtag counting (max 3 per post)
    - Banned intensifiers and corporate jargon
    - AI-tell patterns (em-dashes, triads, exclamation marks, hedging)

    Follows the check_file() pattern but skips CSS/style checks.
    """
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        return [Finding(path, 0, "major", "IO", f"cannot read: {exc}", "check the path")]

    nl = [i for i, c in enumerate(text) if c == "\n"]
    def line_of(off: int) -> int:
        return bisect.bisect_right(nl, off) + 1

    findings: list[Finding] = []
    seen: set[tuple[int, str, str]] = set()

    def add(off, severity, code, what, fix):
        ln = line_of(off)
        key = (ln, code, what)
        if key in seen:
            return
        seen.add(key)
        findings.append(Finding(path, ln, severity, code, what, fix))

    # Helper function to check if offset is in code block (for markdown)
    def is_in_code_block(offset: int) -> bool:
        if ext != ".md":
            return False
        lines_before = text[:offset].split('\n')
        fence_count = 0
        for line in lines_before:
            if re.match(r'^[ \t]*(?:```+|~~~+)', line):
                fence_count += 1
        return fence_count % 2 == 1

    # ---- 1. Emoji detection in prose content ----------------------------------
    for emoji_off, emoji_text in emojis_in(text):
        # Skip emojis in code blocks for markdown
        if is_in_code_block(emoji_off):
            continue

        add(emoji_off, "major", "EMOJI",
            f"emoji '{emoji_text}' found in prose",
            "emojis are not part of the brand voice. Use descriptive text instead.")

    # ---- 2. Hashtag counting per post ------------------------------------------
    prose = extract_prose_content(text, ext)
    posts = parse_posts(prose)

    for post_start, post_end, post_text in posts:
        hashtags = hashtags_in(post_text)
        hashtag_count = len(hashtags)

        # Flag violation if more than 3 hashtags in a post
        if hashtag_count > 3:
            # Report at the position of the first hashtag in the post
            first_hashtag_in_prose = post_start + hashtags[0][0] if hashtags else post_start

            add(first_hashtag_in_prose, "major", "HASHTAG",
                f"{hashtag_count} hashtags in post (max 3 allowed)",
                f"reduce hashtag count to 3 or fewer. Found: {', '.join(h[1] for h in hashtags)}")

    # ---- 3. Banned intensifier detection ---------------------------------------
    for word_off, word_text in banned_intensifiers_in(text):
        # Skip words in code blocks for markdown
        if is_in_code_block(word_off):
            continue

        # Generate fix suggestion
        if fix_mode:
            word_lower = word_text.lower()
            suggestions = WORD_SUGGESTIONS.get(word_lower, [])
            if suggestions:
                fix_msg = f"replace '{word_text}' with: {', '.join(suggestions)}"
            else:
                fix_msg = "avoid corporate jargon and intensifiers. Use direct, clear language instead."
        else:
            fix_msg = "avoid corporate jargon and intensifiers. Use direct, clear language instead."

        add(word_off, "major", "INTENSIFIER",
            f"banned intensifier '{word_text}' found in prose",
            fix_msg)

    # ---- 4. AI-tell pattern detection ------------------------------------------
    # Em-dash detection
    em_dashes = em_dashes_in(text)
    if len(em_dashes) > 2:
        # Flag if more than 2 em-dashes in the file
        first_em_off, first_em_text = em_dashes[0]
        if not is_in_code_block(first_em_off):
            add(first_em_off, "minor", "AI-TELL",
                f"{len(em_dashes)} em-dashes found (common AI pattern)",
                "em-dashes are overused in AI-generated content. Use sparingly or replace with periods.")

    # Triad detection
    for triad_off, triad_text in triads_in(text):
        if not is_in_code_block(triad_off):
            add(triad_off, "minor", "AI-TELL",
                f"triad pattern '{triad_text}' (common AI pattern)",
                "lists of three items are overused in AI-generated content. Vary sentence structure.")

    # Multiple exclamation marks
    for excl_off, excl_text in multiple_exclamations_in(text):
        if not is_in_code_block(excl_off):
            add(excl_off, "major", "AI-TELL",
                f"multiple exclamation marks '{excl_text}' found",
                "avoid multiple exclamation marks. Use one or none.")

    # Hedging language
    for hedge_off, hedge_text in hedging_in(text):
        if not is_in_code_block(hedge_off):
            add(hedge_off, "minor", "AI-TELL",
                f"hedging word '{hedge_text}' (weakens brand voice)",
                "avoid hedging language. Make direct, confident statements.")

    findings.sort(key=lambda f: (f.line, SEVERITY_ORDER[f.severity]))
    return findings


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

    return 1 if findings else 0


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
    return 1 if findings else 0


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv or "-q" in argv
    check_copy = "--copy" in argv
    json_output = "--json" in argv
    fix_mode = "--fix" in argv
    paths = [a for a in argv if not a.startswith("-")]

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not paths:
        paths = [repo_root]

    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        for p in missing:
            print(f"brand-check: no such file or directory: {p}", file=sys.stderr)
        return 2

    colors_md = find_colors_md(paths[0]) or find_colors_md(repo_root)
    if not colors_md:
        print("brand-check: could not locate references/colors.md", file=sys.stderr)
        return 2
    palette = load_palette(colors_md)

    files = collect(paths)
    findings: list[Finding] = []
    for f in files:
        findings.extend(check_file(f, palette, check_copy, fix_mode))

    if json_output:
        return json_report(findings, len(files), palette)
    else:
        color = sys.stdout.isatty()
        return report(findings, len(files), palette, quiet, color, check_copy)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
