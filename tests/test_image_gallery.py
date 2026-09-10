"""
Tests for image gallery and index integrity validation.

The JPEGs live in the separate azmx-brand-cdn repository and are served from
jsDelivr; this repository keeps the catalogue, scripts/image-meta.json, and
generates index.html and references/image-index.md from it. These tests check
that catalogue and the generated outputs against each other:

- every meta entry is well formed (filename pattern, dominant hex, luminance, token)
- index.html and references/image-index.md reference every catalogued file
  exactly once, at its CDN URL
- scripts/image-tags.json and the catalogue describe the same set of files
- the counts quoted in README.md match the catalogue

The physical-file checks (size, dimensions, JPEG header) at the bottom run only
when a local assets/images/ working copy is present, so they still guard a
checkout that keeps the files for offline use.
"""

import json
import os
import re
from collections import Counter

import pytest


IMAGE_BASE_DIR = "assets/images"
INDEX_FILE = "references/image-index.md"
GALLERY_FILE = "index.html"
META_FILE = "scripts/image-meta.json"
TAGS_FILE = "scripts/image-tags.json"
README_FILE = "README.md"
EXPECTED_SECTIONS = ["gradient", "blue", "white", "purple", "orange", "red", "green", "yellow"]
EXPECTED_FILE_EXTENSION = ".jpg"

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

HEX_RE = re.compile(r"^#[0-9A-F]{6}$")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def meta():
    assert os.path.isfile(META_FILE), f"{META_FILE} does not exist"
    with open(META_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def cdn(meta):
    return meta["$meta"]["cdn"].rstrip("/")


@pytest.fixture(scope="module")
def entries(meta):
    """[(section, entry), ...] for every catalogued image."""
    return [(sec, e) for sec, rows in meta["images"].items() for e in rows]


@pytest.fixture(scope="module")
def meta_files(entries):
    return [e["f"] for _, e in entries]


@pytest.fixture(scope="module")
def index_content():
    assert os.path.isfile(INDEX_FILE), f"{INDEX_FILE} does not exist"
    content = _read(INDEX_FILE)
    assert content, f"{INDEX_FILE} is empty"
    return content


@pytest.fixture(scope="module")
def gallery_content():
    assert os.path.isfile(GALLERY_FILE), f"{GALLERY_FILE} does not exist"
    return _read(GALLERY_FILE)


class TestImageMeta:
    """scripts/image-meta.json is the catalogue everything else is built from."""

    def test_meta_header(self, meta):
        head = meta["$meta"]
        assert head["cdn"].startswith("https://cdn.jsdelivr.net/gh/"), "images must be served from jsDelivr"
        assert not head["cdn"].endswith("/")
        assert head["sections"] == EXPECTED_SECTIONS
        assert set(meta["images"]) == set(EXPECTED_SECTIONS), "every section must be catalogued"

    @pytest.mark.parametrize("section", EXPECTED_SECTIONS)
    def test_section_is_non_empty(self, meta, section):
        assert meta["images"].get(section), f"section {section} has no images in {META_FILE}"

    def test_every_entry_is_well_formed(self, entries):
        bad = []
        for sec, e in entries:
            if set(e) != {"f", "dom", "tok", "L"}:
                bad.append(f"{e}: keys {sorted(e)}")
                continue
            if not re.fullmatch(rf"{sec}-\d{{3}}{re.escape(EXPECTED_FILE_EXTENSION)}", e["f"]):
                bad.append(f"{sec}: filename {e['f']!r} is not <section>-NNN.jpg")
            if not HEX_RE.match(e["dom"]):
                bad.append(f"{e['f']}: dom {e['dom']!r} is not #RRGGBB")
            if not (isinstance(e["L"], (int, float)) and 0 <= e["L"] <= 1):
                bad.append(f"{e['f']}: L {e['L']!r} outside [0, 1]")
            if not (isinstance(e["tok"], str) and e["tok"].strip()):
                bad.append(f"{e['f']}: empty tok")
        assert not bad, "malformed entries in image-meta.json:\n  " + "\n  ".join(bad)

    def test_filenames_are_unique_and_sorted(self, meta):
        for sec, rows in meta["images"].items():
            names = [e["f"] for e in rows]
            assert len(names) == len(set(names)), f"duplicate filenames in {sec}"
            assert names == sorted(names), f"{sec} entries are not in filename order"

    def test_tags_and_meta_describe_the_same_files(self, meta_files):
        with open(TAGS_FILE, encoding="utf-8") as f:
            tags = json.load(f)
        meta_set, tag_set = set(meta_files), set(tags)
        assert tag_set - meta_set == set(), f"tags for files not in the catalogue: {sorted(tag_set - meta_set)[:5]}"
        assert meta_set - tag_set == set(), f"catalogued files without tags: {sorted(meta_set - tag_set)[:5]}"


class TestImageIndex:
    """references/image-index.md is generated from the catalogue."""

    def test_total_count_matches_meta(self, index_content, meta_files):
        match = re.search(r'\((\d+) total\)', index_content[:500])
        assert match, "Could not find total count in index file"
        assert int(match.group(1)) == len(meta_files)

    def test_index_has_all_section_headers_with_counts(self, index_content, meta):
        for section in EXPECTED_SECTIONS:
            pattern = rf'## {re.escape(SECTION_TITLES[section])} \((\d+)\)'
            match = re.search(pattern, index_content)
            assert match, f"Index does not contain section header for '{SECTION_TITLES[section]}'"
            assert int(match.group(1)) == len(meta["images"][section]), \
                f"Section {section} count in index does not match {META_FILE}"

    def test_index_table_structure(self, index_content):
        assert "| Image | Concept tags | Dominant | Text on top | Link |" in index_content, \
            "Index is missing proper table header"
        assert "|---|---|---|---|---|" in index_content, "Index is missing table separator row"

    def test_every_meta_file_listed_exactly_once(self, index_content, meta_files):
        listed = Counter(re.findall(r'\| `([a-z0-9-]+\.jpg)` \|', index_content))
        assert set(listed) == set(meta_files), \
            f"index rows differ from catalogue: extra={sorted(set(listed) - set(meta_files))[:5]} " \
            f"missing={sorted(set(meta_files) - set(listed))[:5]}"
        dupes = [f for f, n in listed.items() if n != 1]
        assert not dupes, f"files listed more than once in the index: {dupes[:5]}"

    def test_every_download_link_is_the_cdn_url(self, index_content, entries, cdn):
        links = Counter(re.findall(r'\[download\]\(([^)]+)\)', index_content))
        expected = Counter(f"{cdn}/{sec}/{e['f']}" for sec, e in entries)
        assert links == expected, "download links must be exactly one CDN URL per catalogued file"
        assert "raw.githubusercontent.com" not in index_content
        assert "assets/images/" not in index_content

    def test_index_curl_example_uses_cdn(self, index_content, cdn):
        assert f'curl -L -O "{cdn}/blue/blue-001.jpg"' in index_content

    def test_dominant_colors_match_meta(self, index_content, entries):
        for _, e in entries:
            assert f"| `{e['f']}` |" in index_content
            row = re.search(rf"\| `{re.escape(e['f'])}` \|[^\n]*", index_content).group(0)
            assert f"| `{e['dom']}` |" in row, f"{e['f']}: index dominant colour differs from {META_FILE}"

    def test_text_on_top_recommendations(self, index_content):
        valid_recommendations = [
            "White + Light Blue accent",
            "White, test contrast",
            "Navy + Electric accent"
        ]
        rows = [line for line in index_content.splitlines() if line.startswith("| `") and ".jpg`" in line]
        assert rows, "No image rows found in index"
        for row in rows:
            assert any(rec in row for rec in valid_recommendations), f"row without a text-on-top value: {row}"

    def test_concept_tags_present(self, index_content):
        image_rows = [line for line in index_content.splitlines()
                      if line.strip().startswith('| `') and '.jpg`' in line]
        assert len(image_rows) > 0, "No image rows found in index"
        for row in image_rows:
            columns = row.split('|')
            assert len(columns) >= 6, f"Invalid table row format: {row.strip()}"
            assert columns[2].strip(), f"Missing concept tags column in row: {row.strip()}"


class TestGallery:
    """index.html is generated from the catalogue and links every image to the CDN."""

    def test_every_meta_file_shown_exactly_once(self, gallery_content, entries, cdn):
        srcs = Counter(re.findall(r'<img loading="lazy" src="([^"]+)"', gallery_content))
        expected = Counter(f"{cdn}/{sec}/{e['f']}" for sec, e in entries)
        assert srcs == expected, "gallery <img> sources must be exactly one CDN URL per catalogued file"

    def test_gallery_links_and_downloads_use_cdn(self, gallery_content, entries, cdn):
        for sec, e in entries:
            url = f"{cdn}/{sec}/{e['f']}"
            assert f'<a class="card" href="{url}"' in gallery_content, f"{e['f']}: card link is not the CDN URL"
            assert f'<a class="dl" href="{url}" download="{e["f"]}"' in gallery_content, \
                f"{e['f']}: download link is not the CDN URL"
        assert "assets/images/" not in gallery_content
        assert "raw.githubusercontent.com" not in gallery_content

    def test_gallery_counts(self, gallery_content, meta_files, meta):
        total = len(meta_files)
        assert f'<span>All images</span><span class="n">{total}</span>' in gallery_content
        assert f"{total} images · JPG · 1600px wide" in gallery_content
        for section in EXPECTED_SECTIONS:
            n = len(meta["images"][section])
            assert f'<a href="#{section}"><span>{SECTION_TITLES[section]}</span><span class="n">{n}</span></a>' \
                in gallery_content, f"sidebar count for {section} is not {n}"

    def test_gallery_footer_curl_uses_cdn(self, gallery_content, cdn):
        assert f'curl -L -O "{cdn}/blue/blue-001.jpg"' in gallery_content


class TestReadmeCounts:
    def test_readme_quotes_the_catalogue_count(self, meta_files):
        readme = _read(README_FILE)
        total = len(meta_files)
        assert f"all {total} brand images" in readme, f"README 'Browse the image library' line must say {total}"
        assert f"{total} AZMX-generated brand images" in readme, f"README asset list must say {total}"


# ---------------------------------------------------------------------------
# LOCAL-COPY-ONLY CHECKS. The JPEGs are not part of this repository; these
# tests run only when a checkout keeps an assets/images/ working copy (for
# offline use, or a clone from before the move to the CDN). They are skipped,
# not failed, when the directory is absent.
# ---------------------------------------------------------------------------

local_copy = pytest.mark.skipif(
    not os.path.isdir(IMAGE_BASE_DIR),
    reason=f"{IMAGE_BASE_DIR} is not present (images live on the CDN); local-file checks skipped",
)


def _local_files():
    for section in EXPECTED_SECTIONS:
        section_path = os.path.join(IMAGE_BASE_DIR, section)
        if not os.path.isdir(section_path):
            continue
        for f in sorted(os.listdir(section_path)):
            if f.lower().endswith(EXPECTED_FILE_EXTENSION):
                yield section, f, os.path.join(section_path, f)


@local_copy
class TestLocalImageFiles:
    """Guards for a local assets/images/ working copy (see the note above)."""

    def test_local_files_match_catalogue(self, meta):
        for section, f, _ in _local_files():
            assert f in {e["f"] for e in meta["images"].get(section, [])}, \
                f"{section}/{f} exists locally but is not in {META_FILE}; run scripts/rebuild-index.py"

    def test_image_files_minimum_size(self):
        min_size = 1024  # 1KB in bytes
        for _, _, file_path in _local_files():
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
        for section, image_file, file_path in _local_files():
            with Image.open(file_path) as im:
                width, height = im.size
            if width != 1600 or height < 400:
                bad.append(f"{section}/{image_file}: {width}x{height}")
        assert not bad, "images outside the 1600px-wide library profile:\n  " + "\n  ".join(bad)

    def test_image_files_readable(self):
        """Image files are readable and have valid JPG headers (FF D8 FF)."""
        jpg_magic = b'\xFF\xD8\xFF'
        for _, _, file_path in _local_files():
            with open(file_path, 'rb') as f:
                header = f.read(3)
            assert header == jpg_magic, f"Image file {file_path} does not have valid JPG header"

    def test_no_orphaned_sections(self):
        for section in EXPECTED_SECTIONS:
            section_path = os.path.join(IMAGE_BASE_DIR, section)
            if os.path.exists(section_path):
                files = [f for f in os.listdir(section_path) if f.lower().endswith(EXPECTED_FILE_EXTENSION)]
                assert files, f"Section directory {section} exists but contains no JPG files"
