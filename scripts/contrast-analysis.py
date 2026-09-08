#!/usr/bin/env python3
"""
contrast-analysis.py — Calculate contrast ratios for AZMX neutral palette.

Analyzes the neutral palette (Neutral 25-950) against white background to
determine which colors meet WCAG AA requirements for text (4.5:1 contrast).

Usage:
    python3 scripts/contrast-analysis.py
"""

from __future__ import annotations


def rgb(hex6: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    h = hex6.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(hex6: str) -> float:
    """
    Relative luminance, 0-1.
    Uses WCAG 2.0 formula for relative luminance calculation.
    """
    def lin(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(hex6)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """
    Calculate WCAG 2.0 contrast ratio between two colors.
    Returns ratio as float (e.g., 4.5 for 4.5:1).
    """
    l1 = luminance(hex1)
    l2 = luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# Neutral palette from references/colors.md
NEUTRALS = {
    "Neutral 25": "#FCFCFD",
    "Neutral 50": "#F9FAFB",
    "Neutral 100": "#F3F4F6",
    "Neutral 200": "#E5E7EB",
    "Neutral 300": "#D2D6DB",
    "Neutral 400": "#9DA4AE",
    "Neutral 500": "#6C737F",
    "Neutral 600": "#4D5761",
    "Neutral 700": "#384250",
    "Neutral 800": "#1F2A37",
    "Neutral 900": "#111927",
    "Neutral 950": "#0D121C",
}

WHITE = "#FFFFFF"
WCAG_AA_NORMAL_TEXT = 4.5  # WCAG AA requirement for normal text
WCAG_AA_LARGE_TEXT = 3.0   # WCAG AA requirement for large text (18pt+)
WCAG_AAA_NORMAL_TEXT = 7.0 # WCAG AAA requirement for normal text


def main():
    print("AZMX Neutral Palette Contrast Analysis")
    print("=" * 70)
    print(f"Background: White {WHITE}")
    print(f"WCAG AA Normal Text Requirement: {WCAG_AA_NORMAL_TEXT}:1")
    print(f"WCAG AA Large Text Requirement: {WCAG_AA_LARGE_TEXT}:1")
    print(f"WCAG AAA Normal Text Requirement: {WCAG_AAA_NORMAL_TEXT}:1")
    print("=" * 70)
    print()

    compliant_aa_normal = []
    compliant_aa_large = []
    compliant_aaa_normal = []
    non_compliant = []

    print(f"{'Token':<15} {'Hex':<10} {'Luminance':<12} {'Ratio':<8} {'Status'}")
    print("-" * 70)

    for token, hex_color in NEUTRALS.items():
        lum = luminance(hex_color)
        ratio = contrast_ratio(hex_color, WHITE)

        # Determine compliance status
        if ratio >= WCAG_AAA_NORMAL_TEXT:
            status = "AAA ✓✓✓"
            compliant_aaa_normal.append((token, hex_color, ratio))
            compliant_aa_normal.append((token, hex_color, ratio))
            compliant_aa_large.append((token, hex_color, ratio))
        elif ratio >= WCAG_AA_NORMAL_TEXT:
            status = "AA ✓✓"
            compliant_aa_normal.append((token, hex_color, ratio))
            compliant_aa_large.append((token, hex_color, ratio))
        elif ratio >= WCAG_AA_LARGE_TEXT:
            status = "AA Large ✓"
            compliant_aa_large.append((token, hex_color, ratio))
        else:
            status = "FAIL ✗"
            non_compliant.append((token, hex_color, ratio))

        print(f"{token:<15} {hex_color:<10} {lum:<12.4f} {ratio:<8.2f} {status}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    print(f"✓ WCAG AA Normal Text (≥ {WCAG_AA_NORMAL_TEXT}:1): {len(compliant_aa_normal)} colors")
    for token, hex_color, ratio in compliant_aa_normal:
        print(f"  - {token:<15} {hex_color:<10} ({ratio:.2f}:1)")
    print()

    print(f"✓ WCAG AA Large Text Only (≥ {WCAG_AA_LARGE_TEXT}:1): {len(compliant_aa_large) - len(compliant_aa_normal)} colors")
    for token, hex_color, ratio in compliant_aa_large:
        if (token, hex_color, ratio) not in compliant_aa_normal:
            print(f"  - {token:<15} {hex_color:<10} ({ratio:.2f}:1)")
    print()

    print(f"✗ Non-compliant for body text (< {WCAG_AA_NORMAL_TEXT}:1): {len(non_compliant)} colors")
    for token, hex_color, ratio in non_compliant:
        print(f"  - {token:<15} {hex_color:<10} ({ratio:.2f}:1)")
    print()

    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print()
    print("For body text on white backgrounds, use:")
    for token, hex_color, ratio in compliant_aa_normal:
        print(f"  • {token} {hex_color} ({ratio:.2f}:1)")
    print()
    print("Avoid for body text (suitable for decorative/disabled states only):")
    for token, hex_color, ratio in non_compliant:
        print(f"  • {token} {hex_color} ({ratio:.2f}:1)")
    print()


if __name__ == "__main__":
    main()
