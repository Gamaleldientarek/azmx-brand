#!/usr/bin/env python3
"""
extract-metrics.py — AZMX brand metrics extractor.

Extracts brand compliance metrics from HTML/CSS files by importing brand-check.py
(palette, CSS parsing and the tone rule lists live there and only there). Outputs metrics about colors, fonts, spacing, and other brand
elements used in the file.

Usage:
    python3 scripts/extract-metrics.py <file> [--json]

With --json, outputs structured JSON metrics. Otherwise, outputs human-readable text.
"""

from __future__ import annotations

import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Shared rules and parsers — brand-check.py is the single source of truth
# --------------------------------------------------------------------------
#
# Everything palette-, CSS- and tone-related is imported from brand-check.py
# (scripts/brand_check.py is a symlink so the hyphenated file is importable).
# Nothing below duplicates a rule: when the brand changes, edit brand-check.py.

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brand_check  # noqa: E402
from brand_check import (  # noqa: E402
    BRAND_FAMILIES, GENERIC_FAMILIES, SPACING_SCALE, SPACING_PROPS, CHEVRON_WORD,
    FUNC_URL_RE,
    Palette, find_colors_md, norm_hex,
    css_regions, parse_blocks, parse_decls, Block,
    resolve_vars, hexes_in, split_families, px_values, is_swatch,
    BANNED_INTENSIFIER, HEDGING_RE, EM_DASH_RE, TRIAD_RE, EMOJI_RE, HASHTAG_RE,
)


def load_palette(colors_md: str) -> Palette:
    """Parse the legal palette from references/colors.md (delegates to brand-check.py)."""
    return brand_check.load_palette(colors_md)


# --------------------------------------------------------------------------
# Tone/Voice analysis
# --------------------------------------------------------------------------

# Tone rules come from brand-check.py so both tools flag the same words:
#   BANNED_INTENSIFIER  empty intensifiers + corporate jargon
#   HEDGING_RE          hedging words and phrases
#   EM_DASH_RE          em- and en-dashes used as clause breaks
#   TRIAD_RE            "X, Y, and Z" lists (case-insensitive, also "&")
#   EMOJI_RE            emoji runs
#   HASHTAG_RE          #tags not glued to a preceding word
# The two rules below are metric-only (rates, not findings) and stay local.

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
    intensifiers = BANNED_INTENSIFIER.findall(text)
    hedging = HEDGING_RE.findall(text)
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

    # The brand palette is the one shipped with this skill. Only fall back to a
    # colors.md found near the scanned file when the skill's own copy is missing,
    # otherwise a scanned tree could supply its own palette and grade itself compliant.
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    colors_md = find_colors_md(repo_root) or find_colors_md(path)
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
