"""
Tests for font file integrity validation.

Validates that font directories exist, contain expected file types
(.ttf, .woff2, .otf), and that font files are readable.
"""

import os
import pytest


FONT_BASE_DIR = "assets/fonts"
FONT_DIRECTORIES = ["azmx", "thmanyah"]
EXPECTED_FILE_TYPES = [".ttf", ".woff2", ".otf"]

# Expected font files for each directory
AZMX_FONTS = [
    "AzmX-ExtraLight.ttf",
    "AzmX-Bold.ttf",
    "AzmX-SemiBold.ttf",
    "AzmX-Thin.ttf",
    "AzmX-Medium.ttf",
    "AzmX-Heavy.ttf",
    "AzmX-Regular.ttf",
    "AzmX-Light.ttf"
]

THMANYAH_FONTS = [
    "thmanyahserifdisplay-Black.woff2",
    "thmanyahserifdisplay-Regular.woff2",
    "thmanyahserifdisplay-Regular.otf",
    "thmanyahserifdisplay-Light.woff2",
    "thmanyahserifdisplay-Black.otf",
    "thmanyahserifdisplay-Light.otf",
    "thmanyahserifdisplay-Medium.otf",
    "thmanyahserifdisplay-Bold.woff2",
    "thmanyahserifdisplay-Medium.woff2",
    "thmanyahserifdisplay-Bold.otf"
]


class TestFontIntegrity:
    """Test suite for font file integrity validation."""

    def test_font_base_directory_exists(self):
        """Test that the base font directory exists."""
        assert os.path.exists(FONT_BASE_DIR), f"{FONT_BASE_DIR} does not exist"
        assert os.path.isdir(FONT_BASE_DIR), f"{FONT_BASE_DIR} is not a directory"

    @pytest.mark.parametrize("font_dir", FONT_DIRECTORIES)
    def test_font_directory_exists(self, font_dir):
        """Test that each font directory exists."""
        full_path = os.path.join(FONT_BASE_DIR, font_dir)
        assert os.path.exists(full_path), f"Font directory {full_path} does not exist"
        assert os.path.isdir(full_path), f"{full_path} is not a directory"

    @pytest.mark.parametrize("font_dir", FONT_DIRECTORIES)
    def test_font_directory_not_empty(self, font_dir):
        """Test that each font directory contains files."""
        full_path = os.path.join(FONT_BASE_DIR, font_dir)
        files = os.listdir(full_path)
        assert len(files) > 0, f"Font directory {full_path} is empty"

    @pytest.mark.parametrize("font_dir", FONT_DIRECTORIES)
    def test_font_directory_has_expected_file_types(self, font_dir):
        """Test that each font directory contains expected file types."""
        full_path = os.path.join(FONT_BASE_DIR, font_dir)
        files = os.listdir(full_path)

        # Get file extensions
        extensions = set(os.path.splitext(f)[1] for f in files if os.path.isfile(os.path.join(full_path, f)))

        # Check that at least one expected file type is present
        has_expected_type = any(ext in EXPECTED_FILE_TYPES for ext in extensions)
        assert has_expected_type, f"Font directory {full_path} does not contain any expected file types {EXPECTED_FILE_TYPES}"

    @pytest.mark.parametrize("font_file", AZMX_FONTS)
    def test_azmx_font_exists(self, font_file):
        """Test that expected AzmX font files exist."""
        full_path = os.path.join(FONT_BASE_DIR, "azmx", font_file)
        assert os.path.exists(full_path), f"AzmX font file {full_path} does not exist"
        assert os.path.isfile(full_path), f"{full_path} is not a file"

    @pytest.mark.parametrize("font_file", AZMX_FONTS)
    def test_azmx_font_readable(self, font_file):
        """Test that AzmX font files are readable and not empty."""
        full_path = os.path.join(FONT_BASE_DIR, "azmx", font_file)
        assert os.path.getsize(full_path) > 0, f"AzmX font file {full_path} is empty"

        # Test that file can be opened in binary mode
        with open(full_path, 'rb') as f:
            data = f.read(4)  # Read first 4 bytes to verify readability
            assert len(data) > 0, f"Cannot read AzmX font file {full_path}"

    @pytest.mark.parametrize("font_file", THMANYAH_FONTS)
    def test_thmanyah_font_exists(self, font_file):
        """Test that expected Thmanyah font files exist."""
        full_path = os.path.join(FONT_BASE_DIR, "thmanyah", font_file)
        assert os.path.exists(full_path), f"Thmanyah font file {full_path} does not exist"
        assert os.path.isfile(full_path), f"{full_path} is not a file"

    @pytest.mark.parametrize("font_file", THMANYAH_FONTS)
    def test_thmanyah_font_readable(self, font_file):
        """Test that Thmanyah font files are readable and not empty."""
        full_path = os.path.join(FONT_BASE_DIR, "thmanyah", font_file)
        assert os.path.getsize(full_path) > 0, f"Thmanyah font file {full_path} is empty"

        # Test that file can be opened in binary mode
        with open(full_path, 'rb') as f:
            data = f.read(4)  # Read first 4 bytes to verify readability
            assert len(data) > 0, f"Cannot read Thmanyah font file {full_path}"

    def test_azmx_fonts_are_ttf(self):
        """Test that AzmX fonts are in TTF format."""
        font_dir = os.path.join(FONT_BASE_DIR, "azmx")
        files = [f for f in os.listdir(font_dir) if os.path.isfile(os.path.join(font_dir, f))]

        ttf_files = [f for f in files if f.endswith('.ttf')]
        assert len(ttf_files) > 0, "AzmX directory should contain TTF font files"

        # Check that all AzmX fonts are TTF
        for font_file in files:
            assert font_file.endswith('.ttf'), f"AzmX font {font_file} is not a TTF file"

    def test_thmanyah_fonts_are_otf_or_woff2(self):
        """Test that Thmanyah fonts are in OTF or WOFF2 format."""
        font_dir = os.path.join(FONT_BASE_DIR, "thmanyah")
        files = [f for f in os.listdir(font_dir) if os.path.isfile(os.path.join(font_dir, f))]

        expected_ext_files = [f for f in files if f.endswith('.otf') or f.endswith('.woff2')]
        assert len(expected_ext_files) > 0, "Thmanyah directory should contain OTF or WOFF2 font files"

        # Check that all Thmanyah fonts are OTF or WOFF2
        for font_file in files:
            assert font_file.endswith('.otf') or font_file.endswith('.woff2'), \
                f"Thmanyah font {font_file} is not an OTF or WOFF2 file"

    def test_azmx_has_all_weights(self):
        """Test that AzmX font family has all expected weights."""
        expected_weights = ["Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "Heavy"]
        font_dir = os.path.join(FONT_BASE_DIR, "azmx")
        files = os.listdir(font_dir)

        for weight in expected_weights:
            matching_files = [f for f in files if weight in f]
            assert len(matching_files) > 0, f"AzmX font family is missing '{weight}' weight"

    def test_thmanyah_has_all_weights(self):
        """Test that Thmanyah font family has all expected weights."""
        expected_weights = ["Light", "Regular", "Medium", "Bold", "Black"]
        font_dir = os.path.join(FONT_BASE_DIR, "thmanyah")
        files = os.listdir(font_dir)

        for weight in expected_weights:
            matching_files = [f for f in files if weight in f]
            assert len(matching_files) > 0, f"Thmanyah font family is missing '{weight}' weight"

    def test_font_files_minimum_size(self):
        """Test that font files are above a minimum size threshold (10KB)."""
        min_size = 10 * 1024  # 10KB in bytes

        for font_dir in FONT_DIRECTORIES:
            full_path = os.path.join(FONT_BASE_DIR, font_dir)
            files = [f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))]

            for font_file in files:
                file_path = os.path.join(full_path, font_file)
                file_size = os.path.getsize(file_path)
                assert file_size >= min_size, \
                    f"Font file {file_path} is too small ({file_size} bytes), expected at least {min_size} bytes"
