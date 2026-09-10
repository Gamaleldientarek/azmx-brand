"""Tests for extract-metrics.py.

extract-metrics.py must not carry its own copies of the palette parser, CSS
parser or tone rule lists: it imports them from brand-check.py so the two tools
can never drift apart again.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"

sys.path.insert(0, str(SCRIPTS))
import brand_check  # noqa: E402

_spec = importlib.util.spec_from_file_location("extract_metrics", SCRIPTS / "extract-metrics.py")
extract_metrics = importlib.util.module_from_spec(_spec)
sys.modules["extract_metrics"] = extract_metrics
_spec.loader.exec_module(extract_metrics)


class TestSharedWithBrandCheck:
    """Every shared rule is the very same object as brand-check.py's."""

    @pytest.mark.parametrize("name", [
        "BANNED_INTENSIFIER", "HEDGING_RE", "EM_DASH_RE", "TRIAD_RE", "EMOJI_RE", "HASHTAG_RE",
        "Palette", "find_colors_md", "norm_hex", "css_regions", "parse_blocks", "parse_decls",
        "resolve_vars", "hexes_in", "split_families", "px_values", "is_swatch",
        "BRAND_FAMILIES", "GENERIC_FAMILIES", "SPACING_SCALE", "SPACING_PROPS", "CHEVRON_WORD",
    ])
    def test_symbol_is_brand_checks(self, name):
        assert getattr(extract_metrics, name) is getattr(brand_check, name)

    def test_old_duplicate_rules_are_gone(self):
        for name in ("EMPTY_INTENSIFIERS", "HEDGING_PHRASES", "STYLE_BLOCK_RE", "HEX_RE",
                     "strip_comments", "enclosing_tag", "luminance", "rgb"):
            assert name not in vars(extract_metrics), f"{name} is still duplicated"

    def test_source_has_no_inline_rule_copies(self):
        src = (SCRIPTS / "extract-metrics.py").read_text(encoding="utf-8")
        assert "re.compile(r\"<style" not in src
        assert "def norm_hex" not in src
        assert "class Palette" not in src
        assert "truly|" not in src  # the intensifier list lives in brand-check.py only

    def test_load_palette_delegates(self):
        p = extract_metrics.load_palette(str(FIXTURES / "colors.md"))
        q = brand_check.load_palette(str(FIXTURES / "colors.md"))
        assert p.legal == q.legal


class TestToneAgreement:
    """Both tools flag the same words in the same text."""

    TEXT = ("We truly elevate and unlock value; let us delve in effortlessly. "
            "This can help — or might help – you. Fast, simple, and powerful!! 😀😀 "
            "#one #two #three #four not#five")

    def test_intensifiers_match_brand_check(self):
        tm = extract_metrics.analyze_tone_metrics(self.TEXT)
        ours = sorted(w.lower() for w in tm["issues"]["empty_intensifiers"]["instances"])
        theirs = sorted(w.lower() for _, w in brand_check.banned_intensifiers_in(self.TEXT))
        assert ours == theirs == ["delve", "effortlessly", "elevate", "truly", "unlock"]

    def test_hedging_matches_brand_check(self):
        tm = extract_metrics.analyze_tone_metrics(self.TEXT)
        assert tm["issues"]["hedging_phrases"]["instances"] == \
            [w for _, w in brand_check.hedging_in(self.TEXT)] == ["can help", "might help"]

    def test_dashes_triads_hashtags_match_brand_check(self):
        tm = extract_metrics.analyze_tone_metrics(self.TEXT)
        assert tm["issues"]["em_dashes"]["count"] == len(brand_check.em_dashes_in(self.TEXT)) == 2
        assert tm["issues"]["triads"]["count"] == len(brand_check.triads_in(self.TEXT)) == 1
        assert tm["issues"]["hashtags"]["instances"] == \
            [t for _, t in brand_check.hashtags_in(self.TEXT)] == ["#one", "#two", "#three", "#four"]
        assert tm["issues"]["hashtags"]["over_limit"] is True
        assert tm["issues"]["emojis"]["count"] == len(brand_check.emojis_in(self.TEXT))

    def test_empty_text(self):
        assert extract_metrics.analyze_tone_metrics("") == {
            "total_words": 0, "total_sentences": 0, "issues": {}}


class TestCli:
    @pytest.mark.parametrize("fixture", ["sample-valid.html", "sample-invalid.html"])
    def test_json_output_shape(self, fixture):
        r = subprocess.run([sys.executable, str(SCRIPTS / "extract-metrics.py"),
                            str(FIXTURES / fixture), "--json"],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert set(data) == {"file", "color_metrics", "font_metrics", "spacing_metrics",
                             "chevron_metrics", "tone_metrics"}
        assert 0.0 <= data["color_metrics"]["palette_compliance_rate"] <= 1.0
        assert 0.0 <= data["tone_metrics"]["compliance_score"] <= 1.0

    def test_invalid_fixture_has_illegal_colors_and_non_brand_fonts(self):
        palette = extract_metrics.load_palette(str(ROOT / "references" / "colors.md"))
        m = extract_metrics.extract_metrics(str(FIXTURES / "sample-invalid.html"), palette)
        assert m["color_metrics"]["illegal_colors"] > 0
        assert m["font_metrics"]["non_brand_fonts"] > 0
        assert m["spacing_metrics"]["off_scale_count"] > 0

    def test_runs_from_another_cwd(self, tmp_path):
        """The brand_check import must not depend on the caller's working directory."""
        r = subprocess.run([sys.executable, str(SCRIPTS / "extract-metrics.py"),
                            str(FIXTURES / "sample-valid.html"), "--json"],
                           capture_output=True, text=True, cwd=tmp_path)
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["file"].endswith("sample-valid.html")
