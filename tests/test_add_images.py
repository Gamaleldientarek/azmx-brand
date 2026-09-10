"""Unit tests for add-images.py script.

Tests the core functionality of the AZMX image addition tool:
- collect: Collecting image files from paths (files and directories)
- next_index: Determining the next available index for a section from image-meta.json
- convert_image: Pillow resize/convert (the old sips call)
- main: end-to-end against real tiny PNGs in tmp_path, writing into a tmp CDN checkout
  (only the index rebuild is stubbed)
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import importlib.util

import pytest
from PIL import Image

# Import the add-images module (with hyphen in filename)
# We need to use importlib since hyphens aren't allowed in module names
add_images_path = Path(__file__).parent.parent / "scripts" / "add-images.py"
spec = importlib.util.spec_from_file_location("add_images", add_images_path)
add_images = importlib.util.module_from_spec(spec)
sys.modules["add_images"] = add_images
spec.loader.exec_module(add_images)

# Import the functions we need
collect = add_images.collect
next_index = add_images.next_index
convert_image = add_images.convert_image
main = add_images.main
SECTIONS = add_images.SECTIONS


class TestCollect:
    """Test suite for the collect function."""

    def test_collect_single_jpg_file(self, temp_dir):
        """Test collecting a single JPG file."""
        test_file = temp_dir / "test.jpg"
        test_file.touch()

        result = collect([str(test_file)])

        assert len(result) == 1
        assert result[0] == str(test_file)

    def test_collect_single_png_file(self, temp_dir):
        """Test collecting a single PNG file."""
        test_file = temp_dir / "test.png"
        test_file.touch()

        result = collect([str(test_file)])

        assert len(result) == 1
        assert result[0] == str(test_file)

    def test_collect_multiple_extensions(self, temp_dir):
        """Test collecting files with various valid image extensions."""
        extensions = [".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic"]
        files = []
        for i, ext in enumerate(extensions):
            f = temp_dir / f"test{i}{ext}"
            f.touch()
            files.append(str(f))

        result = collect(files)

        assert len(result) == len(extensions)

    def test_collect_mixed_case_extensions(self, temp_dir):
        """Test collecting files with mixed-case extensions."""
        test_file = temp_dir / "test.JPG"
        test_file.touch()

        result = collect([str(test_file)])

        assert len(result) == 1
        assert result[0] == str(test_file)

    def test_collect_directory(self, temp_dir):
        """Test collecting all images from a directory."""
        (temp_dir / "image1.jpg").touch()
        (temp_dir / "image2.png").touch()
        (temp_dir / "not-image.txt").touch()

        result = collect([str(temp_dir)])

        assert len(result) == 2
        assert any("image1.jpg" in r for r in result)
        assert any("image2.png" in r for r in result)
        assert not any("not-image.txt" in r for r in result)

    def test_collect_directory_sorted(self, temp_dir):
        """Test that directory files are sorted alphabetically."""
        (temp_dir / "c.jpg").touch()
        (temp_dir / "a.jpg").touch()
        (temp_dir / "b.jpg").touch()

        result = collect([str(temp_dir)])

        assert len(result) == 3
        assert "a.jpg" in result[0]
        assert "b.jpg" in result[1]
        assert "c.jpg" in result[2]

    def test_collect_ignores_non_images(self, temp_dir, capsys):
        """Test that non-image files are skipped with a message."""
        test_file = temp_dir / "document.txt"
        test_file.touch()

        result = collect([str(test_file)])

        assert len(result) == 0
        captured = capsys.readouterr()
        assert "skipped (not an image)" in captured.out

    def test_collect_mixed_files_and_dirs(self, temp_dir):
        """Test collecting from both files and directories."""
        dir1 = temp_dir / "dir1"
        dir1.mkdir()
        (dir1 / "img1.jpg").touch()

        file1 = temp_dir / "img2.png"
        file1.touch()

        result = collect([str(dir1), str(file1)])

        assert len(result) == 2

    def test_collect_empty_directory(self, temp_dir):
        """Test collecting from an empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        result = collect([str(empty_dir)])

        assert len(result) == 0

    def test_collect_nonexistent_path(self):
        """Test collecting from a nonexistent path."""
        result = collect(["/nonexistent/path/image.jpg"])

        # collect() doesn't validate file existence, only extension
        # It returns paths with valid extensions even if they don't exist
        assert len(result) == 1
        assert result[0] == "/nonexistent/path/image.jpg"

    def test_collect_expanduser(self, temp_dir):
        """Test that paths with ~ are expanded."""
        with patch('os.path.expanduser') as mock_expand:
            mock_expand.return_value = str(temp_dir / "test.jpg")
            (temp_dir / "test.jpg").touch()

            with patch('os.path.isdir', return_value=False):
                result = collect(["~/test.jpg"])

            mock_expand.assert_called_once_with("~/test.jpg")


def _meta(**sections):
    """Build an image-meta.json document with the given {section: [indices]}."""
    return {
        "$meta": {"cdn": "https://cdn.example/images", "sections": list(SECTIONS)},
        "images": {
            sec: [{"f": f"{sec}-{n:03d}.jpg", "dom": "#000000", "tok": "x", "L": 0.1} for n in idx]
            for sec, idx in sections.items()
        },
    }


class TestNextIndex:
    """next_index reads the highest number recorded in image-meta.json, not a local folder."""

    def test_next_index_empty_catalogue(self):
        assert next_index("blue", _meta()) == 1

    def test_next_index_section_missing(self):
        assert next_index("blue", _meta(gradient=[1, 2])) == 1

    def test_next_index_with_existing_entries(self):
        assert next_index("blue", _meta(blue=[1, 2, 3])) == 4

    def test_next_index_non_sequential(self):
        assert next_index("gradient", _meta(gradient=[1, 5, 10])) == 11

    def test_next_index_ignores_non_matching(self):
        meta = _meta(orange=[1, 2])
        meta["images"]["orange"] += [{"f": n, "dom": "#000000", "tok": "x", "L": 0.1}
                                     for n in ("other-file.jpg", "orange.jpg", "orange-abc.jpg")]
        assert next_index("orange", meta) == 3

    def test_next_index_reads_meta_file_by_default(self, temp_dir):
        meta_path = temp_dir / "image-meta.json"
        meta_path.write_text(json.dumps(_meta(red=[1, 2, 4])), encoding="utf-8")
        with patch.object(add_images, "META_PATH", str(meta_path)):
            assert next_index("red") == 5

    def test_next_index_missing_meta_file(self, temp_dir):
        with patch.object(add_images, "META_PATH", str(temp_dir / "missing.json")):
            assert next_index("purple") == 1


class TestConvertImage:
    """convert_image: Pillow replacement for the old `sips --resampleWidth 1600 …` call."""

    def test_resizes_to_1600_wide_keeping_aspect(self, temp_dir):
        src = temp_dir / "wide.png"
        Image.new("RGB", (400, 100), (0, 26, 255)).save(src)
        dest = temp_dir / "out.jpg"
        convert_image(str(src), str(dest))
        with Image.open(dest) as im:
            assert im.format == "JPEG"
            assert im.size == (1600, 400)
            assert im.mode == "RGB"

    def test_tall_image_is_also_1600_wide(self, temp_dir):
        """`sips --resampleWidth` pins the width, whatever the orientation."""
        src = temp_dir / "tall.png"
        Image.new("RGB", (200, 800), "white").save(src)
        dest = temp_dir / "out.jpg"
        convert_image(str(src), str(dest))
        with Image.open(dest) as im:
            assert im.size == (1600, 6400)

    def test_rgba_png_is_flattened_to_rgb(self, temp_dir):
        src = temp_dir / "alpha.png"
        Image.new("RGBA", (1600, 900), (4, 0, 56, 128)).save(src)
        dest = temp_dir / "out.jpg"
        convert_image(str(src), str(dest))
        with Image.open(dest) as im:
            assert im.mode == "RGB"
            assert im.size == (1600, 900)

    def test_palette_png_is_converted(self, temp_dir):
        src = temp_dir / "pal.png"
        Image.new("P", (32, 32)).save(src)
        dest = temp_dir / "out.jpg"
        convert_image(str(src), str(dest))
        with Image.open(dest) as im:
            assert im.mode == "RGB"

    def test_quality_is_70(self, temp_dir):
        """A lossier file at quality 70 is smaller than the same image at 95."""
        src = temp_dir / "noise.png"
        import random
        random.seed(1)
        im = Image.new("RGB", (1600, 200))
        im.putdata([(random.randrange(256), random.randrange(256), random.randrange(256))
                    for _ in range(1600 * 200)])
        im.save(src)
        q70, q95 = temp_dir / "q70.jpg", temp_dir / "q95.jpg"
        convert_image(str(src), str(q70))
        convert_image(str(src), str(q95), quality=95)
        assert q70.stat().st_size < q95.stat().st_size

    def test_unreadable_input_raises(self, temp_dir):
        src = temp_dir / "not-an-image.png"
        src.write_bytes(b"definitely not a png")
        with pytest.raises(Exception):
            convert_image(str(src), str(temp_dir / "out.jpg"))


def _png(path, size=(64, 48), color=(0, 26, 255), mode="RGB"):
    Image.new(mode, size, color).save(path)
    return path


@pytest.fixture
def library(temp_dir):
    """A tmp CDN checkout and image-meta.json for the script to write into; the index rebuild is stubbed."""
    cdn = temp_dir / "azmx-brand-cdn"
    (cdn / "images").mkdir(parents=True)
    meta_path = temp_dir / "image-meta.json"
    meta_path.write_text(json.dumps(_meta()), encoding="utf-8")
    with patch.object(add_images, "ROOT", str(temp_dir)), \
            patch.object(add_images, "META_PATH", str(meta_path)), \
            patch.object(add_images, "DEFAULT_CDN_DIR", str(cdn)), \
            patch("subprocess.run", return_value=MagicMock(returncode=0)) as rebuild:
        yield cdn / "images", rebuild


def _read_meta(temp_dir):
    return json.loads((temp_dir / "image-meta.json").read_text(encoding="utf-8"))


class TestMain:
    """Test suite for the main function, run against real files in tmp_path."""

    def test_main_no_arguments(self, capsys):
        """Test main with no arguments shows usage."""
        with patch('sys.argv', ['add-images.py']):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Usage:" in captured.out

    def test_main_invalid_section(self, capsys):
        """Test main with invalid section shows usage."""
        with patch('sys.argv', ['add-images.py', 'invalid-section', 'file.jpg']):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Usage:" in captured.out

    def test_main_no_files_found(self, temp_dir, capsys):
        """Test main when no image files are found."""
        with patch('sys.argv', ['add-images.py', 'blue', str(temp_dir / "notes.txt")]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "No images found" in captured.out

    def test_main_missing_cdn_dir_is_a_clear_error(self, temp_dir, library, capsys):
        img, rebuild = library
        src = _png(temp_dir / "test.png")
        with patch('sys.argv', ['add-images.py', '--cdn-dir', str(temp_dir / "nope"), 'blue', str(src)]):
            assert main() == 1
        out = capsys.readouterr().out
        assert "CDN checkout not found" in out and str(temp_dir / "nope") in out
        assert "--cdn-dir" in out
        rebuild.assert_not_called()
        assert _read_meta(temp_dir)["images"] == {}

    def test_main_successful_conversion(self, temp_dir, library, capsys):
        """A real PNG becomes <cdn>/images/blue/blue-001.jpg, 1600 px wide, meta is appended, index rebuilt."""
        img, rebuild = library
        src = _png(temp_dir / "test.png", size=(800, 400))

        with patch('sys.argv', ['add-images.py', 'blue', str(src)]):
            result = main()

        assert result == 0
        dest = img / "blue" / "blue-001.jpg"
        assert dest.is_file()
        with Image.open(dest) as im:
            assert im.format == "JPEG" and im.size == (1600, 800) and im.mode == "RGB"
        captured = capsys.readouterr()
        assert "added blue-001.jpg" in captured.out
        assert "<- test.png" in captured.out
        assert "1 image(s) added to blue. Rebuilding index and gallery" in captured.out
        assert "commit and push " + str(img.parent) in captured.out
        assert "purge.jsdelivr.net/gh/Gamaleldientarek/azmx-brand-cdn@main/images/<section>/<file>" in captured.out
        rebuild.assert_called_once()
        assert "rebuild-index.py" in str(rebuild.call_args)
        meta = _read_meta(temp_dir)
        assert meta["$meta"]["cdn"] == "https://cdn.example/images"  # $meta kept
        (entry,) = meta["images"]["blue"]
        assert entry["f"] == "blue-001.jpg"
        assert re.fullmatch(r"#[0-9A-F]{6}", entry["dom"])
        assert entry["tok"] == "Electric #001AFF"
        assert 0 <= entry["L"] <= 1

    def test_main_explicit_cdn_dir(self, temp_dir, library, capsys):
        other = temp_dir / "elsewhere"
        other.mkdir()
        src = _png(temp_dir / "test.png")
        with patch('sys.argv', ['add-images.py', '--cdn-dir', str(other), 'blue', str(src)]):
            assert main() == 0
        assert (other / "images" / "blue" / "blue-001.jpg").is_file()
        assert "commit and push " + str(other) in capsys.readouterr().out

    def test_main_failed_conversion_prints_real_error(self, temp_dir, library, capsys):
        """An unreadable input reports the actual exception, and nothing is added."""
        img, rebuild = library
        bad = temp_dir / "broken.png"
        bad.write_bytes(b"not a png at all")

        with patch('sys.argv', ['add-images.py', 'blue', str(bad)]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "FAILED to convert" in captured.out
        assert "broken.png" in captured.out
        assert "UnidentifiedImageError" in captured.out  # the real reason, not a bare FAILED
        assert not (img / "blue" / "blue-001.jpg").exists()
        rebuild.assert_not_called()
        assert _read_meta(temp_dir)["images"] == {}

    def test_main_bad_file_does_not_consume_an_index(self, temp_dir, library, capsys):
        """A failure in the middle leaves no gap in the numbering."""
        img, _ = library
        good1 = _png(temp_dir / "a.png")
        bad = temp_dir / "b.png"
        bad.write_bytes(b"nope")
        good2 = _png(temp_dir / "c.png")

        with patch('sys.argv', ['add-images.py', 'green', str(good1), str(bad), str(good2)]):
            result = main()

        assert result == 0
        assert sorted(p.name for p in (img / "green").iterdir()) == ["green-001.jpg", "green-002.jpg"]
        assert "2 image(s) added to green" in capsys.readouterr().out
        assert [e["f"] for e in _read_meta(temp_dir)["images"]["green"]] == ["green-001.jpg", "green-002.jpg"]

    def test_main_multiple_files(self, temp_dir, library, capsys):
        """Test main with multiple input files of different formats."""
        img, _ = library
        _png(temp_dir / "test1.png")
        Image.new("RGB", (30, 20), "red").save(temp_dir / "test2.jpg")
        Image.new("RGB", (30, 20), "red").save(temp_dir / "test3.webp")
        files = [temp_dir / "test1.png", temp_dir / "test2.jpg", temp_dir / "test3.webp"]

        with patch('sys.argv', ['add-images.py', 'gradient'] + [str(f) for f in files]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "3 image(s) added" in captured.out
        assert sorted(p.name for p in (img / "gradient").iterdir()) == \
            ["gradient-001.jpg", "gradient-002.jpg", "gradient-003.jpg"]

    def test_main_directory_input(self, temp_dir, library, capsys):
        img, _ = library
        folder = temp_dir / "exports"
        folder.mkdir()
        _png(folder / "b.png")
        _png(folder / "a.png")
        (folder / "README.txt").write_text("skip me")

        with patch('sys.argv', ['add-images.py', 'white', str(folder)]):
            assert main() == 0

        assert sorted(p.name for p in (img / "white").iterdir()) == ["white-001.jpg", "white-002.jpg"]

    def test_main_increments_index_from_meta_not_local_folder(self, temp_dir, library, capsys):
        """Numbering continues after the highest entry in image-meta.json, even when the
        CDN checkout holds fewer files (a partial clone) and the local folder is empty."""
        img, _ = library
        (temp_dir / "image-meta.json").write_text(json.dumps(_meta(orange=[1, 2, 4])), encoding="utf-8")
        files = [_png(temp_dir / f"test{i}.jpg") for i in range(3)]

        with patch('sys.argv', ['add-images.py', 'orange'] + [str(f) for f in files]):
            assert main() == 0

        captured = capsys.readouterr()
        assert "orange-005.jpg" in captured.out
        assert "orange-006.jpg" in captured.out
        assert "orange-007.jpg" in captured.out
        assert (img / "orange" / "orange-007.jpg").is_file()
        assert [e["f"] for e in _read_meta(temp_dir)["images"]["orange"]] == \
            ["orange-001.jpg", "orange-002.jpg", "orange-004.jpg",
             "orange-005.jpg", "orange-006.jpg", "orange-007.jpg"]

    def test_main_rebuild_failure_propagates(self, temp_dir, library, capsys):
        img, rebuild = library
        rebuild.return_value = MagicMock(returncode=3)
        src = _png(temp_dir / "x.png")

        with patch('sys.argv', ['add-images.py', 'red', str(src)]):
            assert main() == 3

        assert "Done. Now commit" not in capsys.readouterr().out
