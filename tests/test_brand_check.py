"""Unit tests for brand-check.py script.

Tests the core functionality of the AZMX brand linter:
- norm_hex: Hex color normalization
- load_palette: Palette loading from colors.md
- check_file: Color validation against the brand palette
"""

import os
import sys
import tempfile
from pathlib import Path
import importlib.util

import pytest

# Import the brand-check module (with hyphen in filename)
# We need to use importlib since hyphens aren't allowed in module names
brand_check_path = Path(__file__).parent.parent / "scripts" / "brand-check.py"
spec = importlib.util.spec_from_file_location("brand_check", brand_check_path)
brand_check = importlib.util.module_from_spec(spec)
sys.modules["brand_check"] = brand_check
spec.loader.exec_module(brand_check)

# Import the functions we need
norm_hex = brand_check.norm_hex
load_palette = brand_check.load_palette
check_file = brand_check.check_file
Palette = brand_check.Palette


class TestNormHex:
    """Test suite for the norm_hex function."""

    def test_six_char_hex_lowercase(self):
        """Test normalizing a 6-character lowercase hex."""
        result = norm_hex("#ff0000")
        assert result == "#FF0000"

    def test_six_char_hex_uppercase(self):
        """Test normalizing a 6-character uppercase hex."""
        result = norm_hex("#FF0000")
        assert result == "#FF0000"

    def test_six_char_hex_mixed_case(self):
        """Test normalizing a 6-character mixed case hex."""
        result = norm_hex("#fF00aB")
        assert result == "#FF00AB"

    def test_six_char_hex_without_hash(self):
        """Test normalizing a 6-character hex without hash prefix."""
        result = norm_hex("ff0000")
        assert result == "#FF0000"

    def test_three_char_hex(self):
        """Test normalizing a 3-character hex (shorthand)."""
        result = norm_hex("#f00")
        assert result == "#FF0000"

    def test_three_char_hex_expanded(self):
        """Test that 3-char hex #abc becomes #AABBCC."""
        result = norm_hex("#abc")
        assert result == "#AABBCC"

    def test_eight_char_hex_with_alpha(self):
        """Test normalizing an 8-character hex with alpha channel (ignores alpha)."""
        result = norm_hex("#ff0000ff")
        assert result == "#FF0000"

    def test_eight_char_hex_with_alpha_zero(self):
        """Test that 8-char hex with any alpha still returns RGB portion."""
        result = norm_hex("#ff000000")
        assert result == "#FF0000"

    def test_four_char_hex_with_alpha(self):
        """Test normalizing a 4-character hex with alpha (ignores alpha)."""
        result = norm_hex("#f00f")
        assert result == "#FF0000"

    def test_invalid_length(self):
        """Test that truly invalid hex length returns None."""
        # 4-char is actually valid (RGB+alpha), so test a truly invalid length
        result = norm_hex("#ff000")  # 5 chars is invalid
        assert result is None

    def test_empty_string(self):
        """Test that empty string returns None."""
        result = norm_hex("")
        assert result is None

    def test_hash_only(self):
        """Test that hash-only returns None."""
        result = norm_hex("#")
        assert result is None

    def test_brand_colors(self):
        """Test normalizing actual AZMX brand colors."""
        assert norm_hex("#001AFF") == "#001AFF"  # Electric
        assert norm_hex("#040038") == "#040038"  # Dark Navy
        assert norm_hex("#5D8FFF") == "#5D8FFF"  # Light Blue
        assert norm_hex("#FFFFFF") == "#FFFFFF"  # White


class TestLoadPalette:
    """Test suite for the load_palette function."""

    def test_load_palette_from_fixture(self, sample_colors_md):
        """Test loading palette from the fixture colors.md file."""
        palette = load_palette(str(sample_colors_md))

        assert isinstance(palette, Palette)
        assert len(palette.legal) > 0
        assert palette.source == str(sample_colors_md)

    def test_palette_contains_primary_colors(self, sample_colors_md):
        """Test that loaded palette contains AZMX primary colors."""
        palette = load_palette(str(sample_colors_md))

        # Check primary brand colors are in the palette
        assert "#001AFF" in palette.legal  # Electric
        assert "#040038" in palette.legal  # Dark Navy
        assert "#5D8FFF" in palette.legal  # Light Blue
        assert "#FFFFFF" in palette.legal  # White

    def test_palette_contains_blue_ramp(self, sample_colors_md):
        """Test that loaded palette contains blue ramp colors."""
        palette = load_palette(str(sample_colors_md))

        # Check some blue ramp colors
        assert "#F0F5FF" in palette.legal  # Blue 50
        assert "#DDE8FF" in palette.legal  # Blue 100
        assert "#BFD5FF" in palette.legal  # Blue 200

    def test_palette_contains_neutrals(self, sample_colors_md):
        """Test that loaded palette contains neutral colors."""
        palette = load_palette(str(sample_colors_md))

        # Check some neutral colors
        assert "#F3F4F6" in palette.legal  # Neutral 100
        assert "#E5E7EB" in palette.legal  # Neutral 200
        assert "#111927" in palette.legal  # Neutral 900

    def test_palette_contains_secondary_colors(self, sample_colors_md):
        """Test that loaded palette contains secondary palette colors."""
        palette = load_palette(str(sample_colors_md))

        # Check secondary palette colors
        assert "#F47A48" in palette.legal  # Orange signature
        assert "#22C36F" in palette.legal  # Green signature
        assert "#FED340" in palette.legal  # Yellow signature

    def test_palette_token_names(self, sample_colors_md):
        """Test that palette correctly extracts token names."""
        palette = load_palette(str(sample_colors_md))

        # Check that token names are correctly assigned
        # Note: #001AFF appears as both "Electric" and "Blue 600" - last wins
        assert palette.legal["#001AFF"] in ["Electric", "Blue 600"]
        # White appears only once so should have correct name
        assert palette.legal["#FFFFFF"] == "White"
        # Check blue ramp colors
        assert palette.legal["#F0F5FF"] == "Blue 50"
        assert palette.legal["#111927"] == "Neutral 900"

    def test_palette_is_legal_method(self, sample_colors_md):
        """Test the Palette.is_legal() method."""
        palette = load_palette(str(sample_colors_md))

        assert palette.is_legal("#001AFF") is True   # Electric - in palette
        assert palette.is_legal("#FF00FF") is False  # Not in palette

    def test_palette_name_method(self, sample_colors_md):
        """Test the Palette.name() method."""
        palette = load_palette(str(sample_colors_md))

        # #001AFF appears as both "Electric" and "Blue 600" - last wins
        assert palette.name("#001AFF") in ["Electric", "Blue 600"]
        assert palette.name("#FFFFFF") == "White"
        assert palette.name("#FF00FF") == "#FF00FF"  # Unknown color returns hex

    def test_palette_nearest_method(self, sample_colors_md):
        """Test the Palette.nearest() method."""
        palette = load_palette(str(sample_colors_md))

        # Test finding nearest color for an off-palette color
        nearest_hex, nearest_name, distance = palette.nearest("#001BFF")

        assert isinstance(nearest_hex, str)
        assert nearest_hex.startswith("#")
        assert isinstance(nearest_name, str)
        assert isinstance(distance, float)
        assert distance >= 0

    def test_palette_nearest_electric(self, sample_colors_md):
        """Test nearest color to something very close to Electric."""
        palette = load_palette(str(sample_colors_md))

        # Color very close to Electric #001AFF
        nearest_hex, nearest_name, distance = palette.nearest("#001BFE")

        # Should find #001AFF as the nearest (might be labeled Blue 600 or Electric)
        assert nearest_hex == "#001AFF"
        assert nearest_name in ["Electric", "Blue 600"]
        assert distance < 10  # Very close

    def test_load_palette_nonexistent_file(self):
        """Test that loading a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_palette("/nonexistent/path/colors.md")

    def test_load_palette_empty_file(self, temp_dir):
        """Test that loading a file with no hex values raises SystemExit."""
        empty_md = temp_dir / "empty.md"
        empty_md.write_text("# No colors here\n\nJust some text.\n")

        with pytest.raises(SystemExit) as exc_info:
            load_palette(str(empty_md))

        assert "no hex values found" in str(exc_info.value)


class TestCheckColors:
    """Test suite for color checking logic in check_file function."""

    def test_check_file_valid_colors(self, sample_colors_md, temp_dir):
        """Test that a file with only valid palette colors passes."""
        palette = load_palette(str(sample_colors_md))

        # Create a test HTML file with valid colors
        test_file = temp_dir / "valid.html"
        test_file.write_text("""
<!DOCTYPE html>
<html>
<head>
    <style>
        .hero { background: #001AFF; color: #FFFFFF; }
        .surface { background: #040038; }
        .accent { color: #5D8FFF; }
    </style>
</head>
<body>
    <div class="hero">Electric and White</div>
</body>
</html>
        """)

        findings = check_file(str(test_file), palette)

        # Should have no COLOR findings (might have other findings)
        color_findings = [f for f in findings if f.code == "COLOR"]
        assert len(color_findings) == 0

    def test_check_file_invalid_color(self, sample_colors_md, temp_dir):
        """Test that a file with an off-palette color is flagged."""
        palette = load_palette(str(sample_colors_md))

        # Create a test HTML file with an invalid color
        test_file = temp_dir / "invalid.html"
        test_file.write_text("""
<!DOCTYPE html>
<html>
<head>
    <style>
        .bad { background: #FF00FF; }
    </style>
</head>
<body>
    <div class="bad">Off-palette magenta</div>
</body>
</html>
        """)

        findings = check_file(str(test_file), palette)

        # Should have at least one COLOR finding
        color_findings = [f for f in findings if f.code == "COLOR"]
        assert len(color_findings) > 0

        # Check the finding details
        finding = color_findings[0]
        assert finding.severity in ["minor", "major"]
        assert "#FF00FF" in finding.what or "ff00ff" in finding.what.lower()

    def test_check_file_css_file(self, sample_colors_md, temp_dir):
        """Test checking a CSS file for color violations."""
        palette = load_palette(str(sample_colors_md))

        # Create a test CSS file
        test_file = temp_dir / "test.css"
        test_file.write_text("""
.valid {
    background-color: #001AFF;
    color: #FFFFFF;
}

.invalid {
    background-color: #123456;
}
        """)

        findings = check_file(str(test_file), palette)

        # Should have COLOR findings for #123456
        color_findings = [f for f in findings if f.code == "COLOR"]
        assert len(color_findings) > 0
        assert any("#123456" in f.what or "123456" in f.what.lower()
                   for f in color_findings)

    def test_check_file_inline_styles(self, sample_colors_md, temp_dir):
        """Test checking inline style attributes."""
        palette = load_palette(str(sample_colors_md))

        # Create a test HTML file with inline styles
        test_file = temp_dir / "inline.html"
        test_file.write_text("""
<!DOCTYPE html>
<html>
<body>
    <div style="background: #001AFF;">Valid inline Electric</div>
    <div style="color: #BADC0D;">Invalid inline color</div>
</body>
</html>
        """)

        findings = check_file(str(test_file), palette)

        # Should have COLOR findings for #BADC0D (valid hex but not in palette)
        color_findings = [f for f in findings if f.code == "COLOR"]
        assert len(color_findings) > 0
        assert any("BADC0D" in f.what or "badc0d" in f.what.lower()
                   for f in color_findings)

    def test_check_file_svg_attributes(self, sample_colors_md, temp_dir):
        """Test checking SVG fill/stroke attributes."""
        palette = load_palette(str(sample_colors_md))

        # Create a test SVG file
        test_file = temp_dir / "test.svg"
        test_file.write_text("""
<svg xmlns="http://www.w3.org/2000/svg">
    <rect fill="#001AFF" width="100" height="100"/>
    <circle fill="#BADA55" cx="50" cy="50" r="20"/>
</svg>
        """)

        findings = check_file(str(test_file), palette)

        # Should have COLOR findings for #BADA55
        color_findings = [f for f in findings if f.code == "COLOR"]
        assert len(color_findings) > 0
        assert any("BADA55" in f.what or "bada55" in f.what.lower()
                   for f in color_findings)

    def test_check_file_shorthand_hex(self, sample_colors_md, temp_dir):
        """Test that shorthand hex colors are properly checked."""
        palette = load_palette(str(sample_colors_md))

        # Create a test file with shorthand hex
        test_file = temp_dir / "shorthand.css"
        test_file.write_text("""
.valid { color: #fff; }
.invalid { color: #f0f; }
        """)

        findings = check_file(str(test_file), palette)

        # #fff expands to #FFFFFF (White) - should be valid
        # #f0f expands to #FF00FF - should be invalid
        color_findings = [f for f in findings if f.code == "COLOR"]

        # Should only flag #f0f, not #fff
        assert any("f0f" in f.what.lower() or "FF00FF" in f.what
                   for f in color_findings)

    def test_check_file_swatch_exception(self, sample_colors_md, temp_dir):
        """Test that swatch/chip elements are exempted from color checks."""
        palette = load_palette(str(sample_colors_md))

        # Create a test HTML with swatch elements
        test_file = temp_dir / "swatches.html"
        test_file.write_text("""
<!DOCTYPE html>
<html>
<body>
    <div class="color-chip" style="background: #FF00FF;">Purple chip</div>
    <div class="swatch" style="background: #BADA55;">Green swatch</div>
    <div class="regular" style="background: #DECADE;">Should be flagged</div>
</body>
</html>
        """)

        findings = check_file(str(test_file), palette)

        # Should flag #DECADE but not the swatch colors
        color_findings = [f for f in findings if f.code == "COLOR"]

        # The swatch colors should be exempted
        swatch_violations = [f for f in color_findings
                             if "FF00FF" in f.what or "BADA55" in f.what]
        assert len(swatch_violations) == 0

        # But the regular div should be flagged
        regular_violations = [f for f in color_findings
                              if "DECADE" in f.what]
        assert len(regular_violations) > 0

    def test_check_file_near_miss_severity(self, sample_colors_md, temp_dir):
        """Test that near-miss colors get minor severity."""
        palette = load_palette(str(sample_colors_md))

        # Create a test with a color very close to Electric
        test_file = temp_dir / "near_miss.css"
        test_file.write_text("""
.almost { color: #001BFF; }
        """)

        findings = check_file(str(test_file), palette)

        color_findings = [f for f in findings if f.code == "COLOR"]
        assert len(color_findings) > 0

        # Near misses should be minor severity
        finding = color_findings[0]
        assert finding.severity == "minor"
        assert "near-miss" in finding.what.lower() or "snap" in finding.what.lower()

    def test_check_file_far_miss_severity(self, sample_colors_md, temp_dir):
        """Test that far-off colors get major severity."""
        palette = load_palette(str(sample_colors_md))

        # Create a test with a color far from any palette color
        test_file = temp_dir / "far_miss.css"
        test_file.write_text("""
.way-off { color: #FF00FF; }
        """)

        findings = check_file(str(test_file), palette)

        color_findings = [f for f in findings if f.code == "COLOR"]
        assert len(color_findings) > 0

        # Far misses should be major severity
        finding = color_findings[0]
        assert finding.severity == "major"

    def test_check_file_multiple_violations(self, sample_colors_md, temp_dir):
        """Test file with multiple color violations."""
        palette = load_palette(str(sample_colors_md))

        test_file = temp_dir / "multiple.css"
        test_file.write_text("""
.one { color: #FF00FF; }
.two { background: #BADA55; }
.three { border-color: #DECADE; }
        """)

        findings = check_file(str(test_file), palette)

        color_findings = [f for f in findings if f.code == "COLOR"]
        assert len(color_findings) >= 3

    def test_check_file_unreadable(self, sample_colors_md):
        """Test handling of unreadable files."""
        palette = load_palette(str(sample_colors_md))

        findings = check_file("/nonexistent/file.html", palette)

        # Should return an IO error finding
        assert len(findings) > 0
        assert findings[0].code == "IO"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
