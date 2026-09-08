"""
Tests for SKILL.md structure validation.

Validates that SKILL.md exists, is not empty, and contains all required
sections for the AZMX brand skill.
"""

import os
import pytest


SKILL_FILE = "SKILL.md"
REQUIRED_SECTIONS = [
    "Core palette",
    "Typography",
    "The chevron",
    "Layout essentials"
]


class TestSkillStructure:
    """Test suite for SKILL.md structure validation."""

    def test_skill_file_exists(self):
        """Test that SKILL.md file exists in the repository."""
        assert os.path.exists(SKILL_FILE), f"{SKILL_FILE} does not exist"

    def test_skill_file_not_empty(self):
        """Test that SKILL.md is not empty."""
        assert os.path.getsize(SKILL_FILE) > 0, f"{SKILL_FILE} is empty"

    def test_skill_file_readable(self):
        """Test that SKILL.md can be read."""
        with open(SKILL_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        assert len(content) > 0, f"{SKILL_FILE} has no readable content"

    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_required_sections_present(self, section):
        """Test that all required sections are present in SKILL.md."""
        with open(SKILL_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for section as a markdown heading (## Section)
        assert f"## {section}" in content, f"Required section '## {section}' not found in {SKILL_FILE}"

    def test_skill_has_frontmatter(self):
        """Test that SKILL.md has valid frontmatter with name and description."""
        with open(SKILL_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check frontmatter exists
        assert content.startswith('---'), "SKILL.md should start with frontmatter (---)"

        # Check for required frontmatter fields
        lines = content.split('\n')
        frontmatter_end = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                frontmatter_end = i
                break

        assert frontmatter_end is not None, "Frontmatter closing marker (---) not found"

        frontmatter = '\n'.join(lines[1:frontmatter_end])
        assert 'name:' in frontmatter, "Frontmatter must contain 'name:' field"
        assert 'description:' in frontmatter, "Frontmatter must contain 'description:' field"

    def test_skill_minimum_length(self):
        """Test that SKILL.md contains substantial content (at least 10KB)."""
        file_size = os.path.getsize(SKILL_FILE)
        assert file_size >= 10000, f"{SKILL_FILE} is too short ({file_size} bytes), expected at least 10KB"
