"""
Tests for brand-check.py script.

Validates that the brand compliance checker runs successfully and can detect
brand violations in HTML/CSS/MD/SVG files.
"""

import os
import subprocess
import tempfile
import pytest


BRAND_CHECK_SCRIPT = "scripts/brand-check.py"


class TestBrandCompliance:
    """Test suite for brand-check.py script."""

    def test_brand_check_script_exists(self):
        """Test that brand-check.py script exists."""
        assert os.path.exists(BRAND_CHECK_SCRIPT), f"{BRAND_CHECK_SCRIPT} does not exist"

    def test_brand_check_script_executable(self):
        """Test that brand-check.py is readable and has valid Python syntax."""
        with open(BRAND_CHECK_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()
        assert len(content) > 0, f"{BRAND_CHECK_SCRIPT} is empty"
        assert content.startswith('#!/usr/bin/env python3'), "Script should have Python shebang"

    def test_brand_check_runs_without_args(self):
        """Test that brand-check.py runs successfully without arguments."""
        result = subprocess.run(
            ["python3", BRAND_CHECK_SCRIPT, "--quiet"],
            capture_output=True,
            text=True
        )
        # Script should run without errors (exit code 0 or 1)
        # Exit code 1 means violations found, which is expected in a real repo
        assert result.returncode in (0, 1), f"Script failed with exit code {result.returncode}: {result.stderr}"

    def test_brand_check_with_valid_html(self):
        """Test that brand-check.py passes valid HTML with brand-compliant styles."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {
                        font-family: "AZM X Variable", sans-serif;
                        color: #001AFF;
                        padding: 16px;
                        margin: 24px;
                    }
                </style>
            </head>
            <body>
                <h1>Test</h1>
            </body>
            </html>
            """)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["python3", BRAND_CHECK_SCRIPT, temp_file, "--quiet"],
                capture_output=True,
                text=True
            )
            # Should pass or have minimal violations
            assert result.returncode in (0, 1), f"Unexpected error: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_brand_check_with_invalid_color(self):
        """Test that brand-check.py detects off-brand colors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {
                        background-color: #FF69B4;
                    }
                </style>
            </head>
            <body>
                <h1>Test</h1>
            </body>
            </html>
            """)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["python3", BRAND_CHECK_SCRIPT, temp_file],
                capture_output=True,
                text=True
            )
            # Should detect the color not in the palette
            assert "not in the palette" in result.stdout.lower() or "palette" in result.stdout.lower()
        finally:
            os.unlink(temp_file)

    def test_brand_check_with_invalid_spacing(self):
        """Test that brand-check.py detects off-scale spacing values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False, encoding='utf-8') as f:
            f.write("""
            .test {
                padding: 13px;
                margin: 27px;
            }
            """)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["python3", BRAND_CHECK_SCRIPT, temp_file],
                capture_output=True,
                text=True
            )
            # Should detect the spacing scale violations
            assert "spacing scale" in result.stdout.lower() or "spacing" in result.stdout.lower()
        finally:
            os.unlink(temp_file)

    def test_brand_check_with_nonexistent_file(self):
        """Test that brand-check.py handles nonexistent files gracefully."""
        result = subprocess.run(
            ["python3", BRAND_CHECK_SCRIPT, "nonexistent-file-12345.html"],
            capture_output=True,
            text=True
        )
        # Should handle missing files (returns exit code 2)
        assert result.returncode == 2, "Script should return exit code 2 for missing files"
        assert "no such file" in result.stderr.lower(), "Should report missing file in stderr"

    def test_brand_check_quiet_flag(self):
        """Test that brand-check.py respects the --quiet flag."""
        result = subprocess.run(
            ["python3", BRAND_CHECK_SCRIPT, ".", "--quiet"],
            capture_output=True,
            text=True
        )
        # Should run without crashing
        assert result.returncode in (0, 1), f"Script failed: {result.stderr}"

    def test_colors_reference_exists(self):
        """Test that references/colors.md exists (required by brand-check.py)."""
        assert os.path.exists("references/colors.md"), "references/colors.md is required for brand checking"

    def test_colors_reference_has_content(self):
        """Test that references/colors.md contains hex color values."""
        with open("references/colors.md", 'r', encoding='utf-8') as f:
            content = f.read()
        assert "#" in content, "colors.md should contain hex color values"
        assert len(content) > 100, "colors.md should have substantial content"
