"""
Tests for image gallery and index integrity validation.

Validates that image directories exist, all images are indexed,
the index markdown is properly formatted, and consistency between
actual images and the index.
"""

import os
import re
import pytest


IMAGE_BASE_DIR = "assets/images"
INDEX_FILE = "references/image-index.md"
EXPECTED_SECTIONS = ["gradient", "blue", "white", "purple", "orange", "red", "green", "yellow"]
EXPECTED_FILE_EXTENSION = ".jpg"
RAW_BASE_URL = "https://raw.githubusercontent.com/Gamaleldientarek/azmx-brand/main/assets/images"

# Section titles mapping
SECTION_TITLES = {
    "gradient": "Gradients",
    "blue": "Abstract Blue",
    "white": "White",
    "purple": "Purple",
    "orange": "Orange",
    "red": "Red",
    "green": "Green",
    "yellow": "Yellow"
}


class TestImageGallery:
    """Test suite for image gallery and index integrity validation."""

    def test_image_base_directory_exists(self):
        """Test that the base image directory exists."""
        assert os.path.exists(IMAGE_BASE_DIR), f"{IMAGE_BASE_DIR} does not exist"
        assert os.path.isdir(IMAGE_BASE_DIR), f"{IMAGE_BASE_DIR} is not a directory"

    def test_image_index_file_exists(self):
        """Test that the image index markdown file exists."""
        assert os.path.exists(INDEX_FILE), f"{INDEX_FILE} does not exist"
        assert os.path.isfile(INDEX_FILE), f"{INDEX_FILE} is not a file"

    def test_image_index_readable(self):
        """Test that the image index file is readable and not empty."""
        assert os.path.getsize(INDEX_FILE) > 0, f"{INDEX_FILE} is empty"

        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0, f"Cannot read {INDEX_FILE}"

    @pytest.mark.parametrize("section", EXPECTED_SECTIONS)
    def test_image_section_directory_exists(self, section):
        """Test that each expected image section directory exists."""
        full_path = os.path.join(IMAGE_BASE_DIR, section)
        assert os.path.exists(full_path), f"Image section directory {full_path} does not exist"
        assert os.path.isdir(full_path), f"{full_path} is not a directory"

    @pytest.mark.parametrize("section", EXPECTED_SECTIONS)
    def test_image_section_contains_jpg_files(self, section):
        """Test that each section directory contains JPG files."""
        full_path = os.path.join(IMAGE_BASE_DIR, section)
        files = os.listdir(full_path)
        jpg_files = [f for f in files if f.lower().endswith(EXPECTED_FILE_EXTENSION)]
        assert len(jpg_files) > 0, f"Image section {full_path} does not contain any JPG files"

    def test_total_image_count_matches_index(self):
        """Test that the total image count in the index matches actual files."""
        # Count actual JPG files
        actual_count = 0
        for section in EXPECTED_SECTIONS:
            section_path = os.path.join(IMAGE_BASE_DIR, section)
            if os.path.exists(section_path):
                files = os.listdir(section_path)
                actual_count += len([f for f in files if f.lower().endswith(EXPECTED_FILE_EXTENSION)])

        # Parse index file for total count
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for pattern like "242 total" in the first few lines
            match = re.search(r'\((\d+) total\)', content[:500])
            assert match, "Could not find total count in index file"
            index_count = int(match.group(1))

        assert actual_count == index_count, \
            f"Total image count mismatch: found {actual_count} files but index reports {index_count}"

    def test_index_has_all_section_headers(self):
        """Test that the index file contains headers for all expected sections."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        for section in EXPECTED_SECTIONS:
            section_title = SECTION_TITLES[section]
            # Look for section header with count, e.g., "## Gradients (34)"
            pattern = rf'## {re.escape(section_title)} \(\d+\)'
            assert re.search(pattern, content), \
                f"Index does not contain section header for '{section_title}'"

    def test_all_images_listed_in_index(self):
        """Test that all image files in directories are listed in the index."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index_content = f.read()

        for section in EXPECTED_SECTIONS:
            section_path = os.path.join(IMAGE_BASE_DIR, section)
            if not os.path.exists(section_path):
                continue

            files = [f for f in os.listdir(section_path) if f.lower().endswith(EXPECTED_FILE_EXTENSION)]
            for filename in files:
                # Check if filename is in index as a markdown cell
                assert f"`{filename}`" in index_content, \
                    f"Image {filename} from {section} is not listed in the index"

    def test_all_indexed_images_exist(self):
        """Test that all images listed in the index actually exist in directories."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse index for image filenames in markdown table cells
        # Pattern: | `filename.jpg` | ... |
        pattern = r'\| `([a-z0-9-]+\.jpg)` \|'
        indexed_files = re.findall(pattern, content)

        for filename in indexed_files:
            # Determine which section this file belongs to based on prefix
            found = False
            for section in EXPECTED_SECTIONS:
                section_path = os.path.join(IMAGE_BASE_DIR, section)
                file_path = os.path.join(section_path, filename)
                if os.path.exists(file_path):
                    found = True
                    break

            assert found, f"Indexed image {filename} does not exist in any section directory"

    def test_index_table_structure(self):
        """Test that the index has proper markdown table structure."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for table headers
        assert "| Image | Concept tags | Dominant | Text on top | Link |" in content, \
            "Index is missing proper table header"

        # Check for table separator
        assert "|---|---|---|---|---|" in content, \
            "Index is missing table separator row"

    def test_dominant_colors_format(self):
        """Test that dominant colors in the index are in valid hex format."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern for dominant color column: | `#RRGGBB` |
        pattern = r'\| `(#[0-9A-F]{6})` \| '
        colors = re.findall(pattern, content, re.IGNORECASE)

        assert len(colors) > 0, "No dominant colors found in index"

        # Verify each color is valid hex
        for color in colors:
            assert re.match(r'^#[0-9A-F]{6}$', color, re.IGNORECASE), \
                f"Invalid hex color format: {color}"

    def test_download_links_format(self):
        """Test that download links in the index are properly formatted."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern for download links: [download](https://raw.githubusercontent.com/...)
        pattern = r'\[download\]\(' + re.escape(RAW_BASE_URL) + r'/([a-z]+)/([a-z0-9-]+\.jpg)\)'
        links = re.findall(pattern, content)

        assert len(links) > 0, "No download links found in index"

        # Verify each link points to a valid section and filename
        for section, filename in links:
            assert section in EXPECTED_SECTIONS, \
                f"Download link references unknown section: {section}"

            file_path = os.path.join(IMAGE_BASE_DIR, section, filename)
            assert os.path.exists(file_path), \
                f"Download link points to non-existent file: {file_path}"

    def test_text_on_top_recommendations(self):
        """Test that 'Text on top' recommendations are present and valid."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        valid_recommendations = [
            "White + Light Blue accent",
            "White, test contrast",
            "Navy + Electric accent"
        ]

        # Check that the index contains text recommendations
        has_recommendations = any(rec in content for rec in valid_recommendations)
        assert has_recommendations, \
            "Index does not contain valid 'Text on top' recommendations"

    def test_concept_tags_present(self):
        """Test that concept tags are present for images in the index."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find lines that represent table rows (start with | ` and contain image names)
        image_rows = [line for line in lines if line.strip().startswith('| `')
                      and '.jpg`' in line]

        assert len(image_rows) > 0, "No image rows found in index"

        # Each row should have concept tags (or em dash for missing tags)
        # Format: | `filename.jpg` | tags or — | ...
        for row in image_rows:
            columns = row.split('|')
            assert len(columns) >= 6, f"Invalid table row format: {row.strip()}"

            # Concept tags are in the 3rd column (index 2)
            tags_column = columns[2].strip()
            assert len(tags_column) > 0, f"Missing concept tags column in row: {row.strip()}"

    def test_section_counts_match_files(self):
        """Test that section counts in headers match actual file counts."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        for section in EXPECTED_SECTIONS:
            section_path = os.path.join(IMAGE_BASE_DIR, section)
            if not os.path.exists(section_path):
                continue

            # Count actual files
            files = os.listdir(section_path)
            actual_count = len([f for f in files if f.lower().endswith(EXPECTED_FILE_EXTENSION)])

            # Parse section header for count
            section_title = SECTION_TITLES[section]
            pattern = rf'## {re.escape(section_title)} \((\d+)\)'
            match = re.search(pattern, content)

            if actual_count > 0:
                assert match, f"Section header not found for {section_title}"
                index_count = int(match.group(1))
                assert actual_count == index_count, \
                    f"Section {section} count mismatch: found {actual_count} files but index reports {index_count}"

    def test_image_files_minimum_size(self):
        """Test that image files are above a minimum size threshold (1KB)."""
        min_size = 1024  # 1KB in bytes

        for section in EXPECTED_SECTIONS:
            section_path = os.path.join(IMAGE_BASE_DIR, section)
            if not os.path.exists(section_path):
                continue

            files = [f for f in os.listdir(section_path)
                    if f.lower().endswith(EXPECTED_FILE_EXTENSION)]

            for image_file in files:
                file_path = os.path.join(section_path, image_file)
                file_size = os.path.getsize(file_path)
                assert file_size >= min_size, \
                    f"Image file {file_path} is too small ({file_size} bytes), expected at least {min_size} bytes"

    def test_image_files_have_library_dimensions(self):
        """Every image is a real 1600px-wide render, not a placeholder.

        Two 1x1-pixel JPEGs (713 bytes) shipped with the original export and
        went unnoticed for weeks; the size floor alone is not enough.
        """
        Image = pytest.importorskip("PIL.Image")
        bad = []
        for section in EXPECTED_SECTIONS:
            section_path = os.path.join(IMAGE_BASE_DIR, section)
            if not os.path.exists(section_path):
                continue
            for image_file in os.listdir(section_path):
                if not image_file.lower().endswith(EXPECTED_FILE_EXTENSION):
                    continue
                with Image.open(os.path.join(section_path, image_file)) as im:
                    width, height = im.size
                if width != 1600 or height < 400:
                    bad.append(f"{section}/{image_file}: {width}x{height}")
        assert not bad, "images outside the 1600px-wide library profile:\n  " + "\n  ".join(bad)

    def test_image_files_readable(self):
        """Test that image files are readable and have valid JPG headers."""
        # JPG files should start with FF D8 FF (JPG magic bytes)
        jpg_magic = b'\xFF\xD8\xFF'

        for section in EXPECTED_SECTIONS:
            section_path = os.path.join(IMAGE_BASE_DIR, section)
            if not os.path.exists(section_path):
                continue

            files = [f for f in os.listdir(section_path)
                    if f.lower().endswith(EXPECTED_FILE_EXTENSION)]

            for image_file in files:
                file_path = os.path.join(section_path, image_file)

                # Test that file can be opened and read
                with open(file_path, 'rb') as f:
                    header = f.read(3)
                    assert len(header) == 3, f"Cannot read image file {file_path}"
                    assert header == jpg_magic, \
                        f"Image file {file_path} does not have valid JPG header"

    def test_index_references_correct_base_url(self):
        """Test that the index references the correct GitHub raw content URL."""
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        assert RAW_BASE_URL in content, \
            f"Index does not reference the expected base URL: {RAW_BASE_URL}"

    def test_no_orphaned_sections(self):
        """Test that there are no empty section directories."""
        for section in EXPECTED_SECTIONS:
            section_path = os.path.join(IMAGE_BASE_DIR, section)
            if os.path.exists(section_path):
                files = [f for f in os.listdir(section_path)
                        if f.lower().endswith(EXPECTED_FILE_EXTENSION)]
                assert len(files) > 0, \
                    f"Section directory {section} exists but contains no JPG files"
