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


# ---------------------------------------------------------------------------
# --brand: sub-brand resolution, schema validation, typography overrides
# ---------------------------------------------------------------------------

import json
import subprocess

REPO_ROOT = Path(__file__).parent.parent
REAL_COLORS_MD = REPO_ROOT / "references" / "colors.md"
SCRIPT = REPO_ROOT / "scripts" / "brand-check.py"


def _run(*argv):
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)


def _fake_repo(tmp_path, configs: dict[str, dict], schema: bool = True) -> Path:
    """A minimal repo layout: references/colors.md + config/sub-brands/*.json (+ schema)."""
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "colors.md").write_text(
        (REPO_ROOT / "tests" / "fixtures" / "colors.md").read_text(encoding="utf-8"),
        encoding="utf-8")
    sb = tmp_path / "config" / "sub-brands"
    sb.mkdir(parents=True)
    for name, cfg in configs.items():
        (sb / f"{name}.json").write_text(json.dumps(cfg), encoding="utf-8")
    if schema:
        (tmp_path / "schemas").mkdir()
        (tmp_path / "schemas" / "sub-brand-config.schema.json").write_text(
            (REPO_ROOT / "schemas" / "sub-brand-config.schema.json").read_text(encoding="utf-8"),
            encoding="utf-8")
    return tmp_path / "references" / "colors.md"


def _majarah_config() -> dict:
    return json.loads((REPO_ROOT / "config" / "sub-brands" / "majarah.json").read_text(encoding="utf-8"))


class TestSubBrandResolution:
    """find_sub_brand_config / available_sub_brands."""

    def test_available_sub_brands_skips_underscore_templates(self):
        names = brand_check.available_sub_brands(str(REAL_COLORS_MD))
        assert {"colab", "majarah", "clix", "anatomi"} <= set(names)
        assert not any(n.startswith("_") for n in names)
        assert "_example-new-brand" not in names

    def test_unknown_brand_exits_2_in_process(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            brand_check.find_sub_brand_config(str(REAL_COLORS_MD), "nope")
        assert exc_info.value.code == 2
        err = capsys.readouterr().err
        assert "unknown --brand nope" in err
        assert "available:" in err and "majarah" in err

    def test_unknown_brand_exits_2_via_cli(self, sample_valid_html):
        result = _run("--brand", "nope", str(sample_valid_html), "--format", "json")
        assert result.returncode == 2, result.stderr
        assert "unknown --brand nope; available:" in result.stderr
        assert "colab" in result.stderr and "majarah" in result.stderr
        assert result.stdout == ""  # no report was produced against the wrong palette

    def test_template_config_is_not_selectable(self):
        assert (REPO_ROOT / "config" / "sub-brands" / "_example-new-brand.json").is_file()
        with pytest.raises(SystemExit) as exc_info:
            brand_check.find_sub_brand_config(str(REAL_COLORS_MD), "_example-new-brand")
        assert exc_info.value.code == 2

    def test_known_brand_resolves_to_its_file(self):
        path = brand_check.find_sub_brand_config(str(REAL_COLORS_MD), "majarah")
        assert path.endswith(os.path.join("config", "sub-brands", "majarah.json"))
        assert os.path.isfile(path)

    def test_load_palette_merges_custom_primitives(self):
        palette = load_palette(str(REAL_COLORS_MD), "majarah")
        assert palette.legal.get("#B366FF") == "brand/majarah/electric-purple"
        assert "majarah.json" in palette.source


class TestSubBrandSchemaValidation:
    """Configs are validated against schemas/sub-brand-config.schema.json."""

    def test_invalid_config_fails_with_readable_message(self, tmp_path, capsys):
        cfg = _majarah_config()
        cfg["token_overrides"]["inheritance_mode"] = "not-a-mode"
        colors_md = _fake_repo(tmp_path, {"broken": cfg})
        with pytest.raises(SystemExit) as exc_info:
            brand_check.load_sub_brand_primitives(
                brand_check.find_sub_brand_config(str(colors_md), "broken"))
        assert exc_info.value.code == 2
        err = capsys.readouterr().err
        assert "broken.json fails sub-brand-config.schema.json" in err
        assert "token_overrides/inheritance_mode" in err
        assert "not-a-mode" in err

    def test_invalid_config_fails_via_cli(self, tmp_path, sample_valid_html):
        cfg = _majarah_config()
        del cfg["archetype"]  # required by the schema
        colors_md = _fake_repo(tmp_path, {"broken": cfg})
        result = _run("--brand", "broken", str(colors_md), "--format", "json")
        assert result.returncode == 2, result.stderr
        assert "broken.json fails sub-brand-config.schema.json" in result.stderr
        assert "archetype" in result.stderr

    def test_valid_config_passes(self, tmp_path):
        colors_md = _fake_repo(tmp_path, {"majarah": _majarah_config()})
        prims = brand_check.load_sub_brand_primitives(
            brand_check.find_sub_brand_config(str(colors_md), "majarah"))
        assert prims["brand/majarah/electric-purple"] == "#B366FF"

    def test_shorthand_hex_primitives_are_valid_and_normalised(self, tmp_path):
        """The schema accepts every form norm_hex accepts (#RGB, #RGBA, #RRGGBB, #RRGGBBAA)."""
        cfg = _majarah_config()
        cfg["token_overrides"]["custom_primitives"] = {
            "brand/x/short": "#abc",
            "brand/x/short-alpha": "#abcf",
            "brand/x/long": "#112233",
            "brand/x/long-alpha": "#11223380",
        }
        colors_md = _fake_repo(tmp_path, {"x": cfg})
        palette = load_palette(str(colors_md), "x")
        assert palette.legal["#AABBCC"] == "brand/x/short-alpha"  # #abc and #abcf collapse
        assert palette.legal["#112233"] == "brand/x/long-alpha"

    def test_non_hex_primitive_is_rejected(self, tmp_path, capsys):
        cfg = _majarah_config()
        cfg["token_overrides"]["custom_primitives"] = {"brand/x/bad": "rgb(1,2,3)"}
        colors_md = _fake_repo(tmp_path, {"x": cfg})
        with pytest.raises(SystemExit):
            load_palette(str(colors_md), "x")
        assert "custom_primitives/brand/x/bad" in capsys.readouterr().err

    def test_missing_jsonschema_warns_and_continues(self, tmp_path, capsys, monkeypatch):
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("no jsonschema")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        cfg = _majarah_config()
        cfg["token_overrides"]["inheritance_mode"] = "not-a-mode"  # invalid, but unchecked
        colors_md = _fake_repo(tmp_path, {"x": cfg})
        palette = load_palette(str(colors_md), "x")
        assert "#B366FF" in palette.legal
        assert "jsonschema not installed" in capsys.readouterr().err

    def test_no_schema_file_skips_validation(self, tmp_path):
        cfg = _majarah_config()
        cfg["token_overrides"]["inheritance_mode"] = "not-a-mode"
        colors_md = _fake_repo(tmp_path, {"x": cfg}, schema=False)
        assert "#B366FF" in load_palette(str(colors_md), "x").legal

    def test_malformed_json_exits_2(self, tmp_path, capsys):
        colors_md = _fake_repo(tmp_path, {})
        (tmp_path / "config" / "sub-brands" / "bad.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            load_palette(str(colors_md), "bad")
        assert exc_info.value.code == 2
        assert "could not load" in capsys.readouterr().err


OSWALD_HTML = """<!DOCTYPE html>
<html><head><style>
  h1 { font-family: Oswald, serif; color: #040038; }
  p  { font-family: "Azm X", sans-serif; }
  .shorthand { font: 700 32px/1.1 "Oswald", serif; }
</style></head>
<body><h1>Majarah</h1><p>body</p></body></html>
"""


class TestTypographyOverrides:
    """typography_overrides.display_font / body_font are honoured per run."""

    def test_allowed_font_families_includes_override(self):
        fams = brand_check.allowed_font_families(str(REAL_COLORS_MD), "majarah")
        assert "oswald" in fams
        assert brand_check.BRAND_FAMILIES <= fams
        # the module global is never mutated
        assert "oswald" not in brand_check.BRAND_FAMILIES

    def test_allowed_font_families_without_brand_is_a_copy(self):
        fams = brand_check.allowed_font_families(str(REAL_COLORS_MD), None)
        assert fams == brand_check.BRAND_FAMILIES
        assert fams is not brand_check.BRAND_FAMILIES

    def test_oswald_is_a_blocker_without_brand(self, tmp_path):
        f = tmp_path / "majarah.html"
        f.write_text(OSWALD_HTML, encoding="utf-8")
        findings = check_file(str(f), load_palette(str(REAL_COLORS_MD)))
        fonts = [x for x in findings if x.code == "FONT"]
        assert fonts and all("Oswald" in x.what for x in fonts)
        assert any(x.severity == "blocker" for x in fonts)

    def test_oswald_has_no_font_finding_with_majarah(self, tmp_path):
        f = tmp_path / "majarah.html"
        f.write_text(OSWALD_HTML, encoding="utf-8")
        palette = load_palette(str(REAL_COLORS_MD), "majarah")
        fams = brand_check.allowed_font_families(str(REAL_COLORS_MD), "majarah")
        findings = check_file(str(f), palette, brand_families=fams)
        assert [x for x in findings if x.code == "FONT"] == []

    def test_oswald_has_no_font_finding_with_majarah_via_cli(self, tmp_path):
        f = tmp_path / "majarah.html"
        f.write_text(OSWALD_HTML, encoding="utf-8")
        result = _run("--brand", "majarah", str(f), "--format", "json")
        assert result.returncode == 0, result.stderr + result.stdout
        data = json.loads(result.stdout)
        assert [x for x in data["findings"] if x["code"] == "FONT"] == []
        # and the base run still flags it
        base = json.loads(_run(str(f), "--format", "json").stdout)
        assert any(x["code"] == "FONT" for x in base["findings"])

    def test_other_brands_do_not_inherit_majarah_fonts(self, tmp_path):
        f = tmp_path / "majarah.html"
        f.write_text(OSWALD_HTML, encoding="utf-8")
        result = _run("--brand", "colab", str(f), "--format", "json")
        data = json.loads(result.stdout)
        assert any(x["code"] == "FONT" for x in data["findings"])

    def test_body_font_override_is_honoured(self, tmp_path):
        cfg = _majarah_config()
        cfg["token_overrides"]["typography_overrides"] = {"display_font": "Oswald", "body_font": "Inter"}
        colors_md = _fake_repo(tmp_path, {"x": cfg})
        fams = brand_check.allowed_font_families(str(colors_md), "x")
        assert {"oswald", "inter"} <= fams
        f = tmp_path / "inter.css"
        f.write_text("p { font-family: Inter, sans-serif; }\n", encoding="utf-8")
        findings = check_file(str(f), load_palette(str(colors_md), "x"), brand_families=fams)
        assert [x for x in findings if x.code == "FONT"] == []


# ---------------------------------------------------------------------------
# Copy checks: reconciled tone rules and the HASHTAG line-number fix
# ---------------------------------------------------------------------------

class TestToneRuleLists:
    """brand-check.py is the single source of truth shared with extract-metrics.py."""

    @pytest.mark.parametrize("word", ["elevate", "unlock", "delve", "effortlessly",
                                      "truly", "leverage", "robust", "seamlessly", "empower"])
    def test_intensifier_superset(self, word):
        assert brand_check.BANNED_INTENSIFIER.search(f"We {word} things.")
        assert word in brand_check.WORD_SUGGESTIONS

    def test_hedging_phrases_report_as_one_match(self):
        hits = [t for _, t in brand_check.hedging_in("This can help and might help you.")]
        assert hits == ["can help", "might help"]

    def test_hedging_words_still_match(self):
        assert [t for _, t in brand_check.hedging_in("It might work, perhaps.")] == ["might", "perhaps"]

    def test_en_dash_counts_as_em_dash(self):
        assert len(brand_check.em_dashes_in("a — b – c")) == 2

    def test_triad_is_case_insensitive_and_accepts_ampersand(self):
        assert brand_check.triads_in("Fast, Simple, AND Powerful")
        assert brand_check.triads_in("fast, simple, & powerful")

    def test_new_intensifiers_are_findings(self, tmp_path):
        f = tmp_path / "copy.md"
        f.write_text("We elevate teams, unlock value and delve deep.\n", encoding="utf-8")
        findings = check_file(str(f), load_palette(str(REAL_COLORS_MD)), check_copy=True, fix_mode=True)
        words = sorted(x.what.split("'")[1] for x in findings if x.code == "INTENSIFIER")
        assert words == ["delve", "elevate", "unlock"]
        fixes = {x.what.split("'")[1]: x.fix for x in findings if x.code == "INTENSIFIER"}
        assert fixes["elevate"].startswith("replace 'elevate' with:")


class TestHashtagLineNumbers:
    """HASHTAG findings point at the first hashtag in the raw file, not at a prose offset."""

    def test_markdown_hashtag_line_is_the_real_line(self, tmp_path):
        f = tmp_path / "post.md"
        text = (
            "# A long heading that makes the prose offset diverge from the raw offset\n"
            "\n"
            "Some intro text with a [link](https://example.com/very/long/url/that/is/stripped) and **bold**.\n"
            "\n"
            "More filler prose. `inline code that is removed from prose` and ![img](https://x/y.png).\n"
            "\n"
            "Closing line #one #two #three #four #five\n"
        )
        f.write_text(text, encoding="utf-8")
        findings = check_file(str(f), load_palette(str(REAL_COLORS_MD)), check_copy=True)
        tags = [x for x in findings if x.code == "HASHTAG"]
        assert len(tags) == 1
        assert tags[0].line == 7
        assert "5 hashtags" in tags[0].what

    def test_html_hashtag_line_is_the_real_line(self, tmp_path):
        f = tmp_path / "post.html"
        text = (
            "<!DOCTYPE html>\n<html><head><style>body{color:#040038}</style>\n"
            "<script>var x = '#not #a #hash #tag #list';</script></head>\n"
            "<body>\n<p>Hello</p>\n"
            "<p>Tags: #one #two #three #four</p>\n"
            "</body></html>\n"
        )
        f.write_text(text, encoding="utf-8")
        findings = check_file(str(f), load_palette(str(REAL_COLORS_MD)), check_copy=True)
        tags = [x for x in findings if x.code == "HASHTAG"]
        assert len(tags) == 1
        assert tags[0].line == 6

    def test_second_post_maps_past_first_posts_hashtags(self, tmp_path):
        # Two posts (separated by a double blank line) that reuse the same tags:
        # the second post's finding must land on line 5, not on line 1's "#one".
        f = tmp_path / "posts.html"
        text = (
            "<p>First post #one #two</p>\n"
            "\n"
            "\n"
            "\n"
            "<p>Second post: #one #two #three #four</p>\n"
        )
        f.write_text(text, encoding="utf-8")
        findings = check_file(str(f), load_palette(str(REAL_COLORS_MD)), check_copy=True)
        tags = [x for x in findings if x.code == "HASHTAG"]
        assert [t.line for t in tags] == [5]


class TestCheckFileStructure:
    """Refactor guards: dead code gone, per-run font families, deterministic suggestions."""

    def test_check_copy_file_removed(self):
        assert not hasattr(brand_check, "check_copy_file")

    def test_check_file_does_not_mutate_brand_families(self, tmp_path):
        before = set(brand_check.BRAND_FAMILIES)
        f = tmp_path / "x.css"
        f.write_text("h1 { font-family: Oswald; }\n", encoding="utf-8")
        check_file(str(f), load_palette(str(REAL_COLORS_MD)), brand_families={"oswald"} | before)
        assert brand_check.BRAND_FAMILIES == before

    def test_token_ref_suggestions_are_sorted_deterministically(self, tmp_path):
        f = tmp_path / "x.css"
        f.write_text("h1 { color: var(--azmx-electric); }\n", encoding="utf-8")
        outs = set()
        for seed in ("0", "1", "2"):
            r = subprocess.run([sys.executable, str(SCRIPT), str(f), "--format", "json"],
                               capture_output=True, text=True,
                               env={**os.environ, "PYTHONHASHSEED": seed})
            outs.add(r.stdout)
        assert len(outs) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
