"""Unit tests for add-images.py script.

Tests the core functionality of the AZMX image addition tool:
- collect: Collecting image files from paths (files and directories)
- next_index: Determining the next available index for a section
- main: Image processing with sips mocking
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import importlib.util

import pytest

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


class TestNextIndex:
    """Test suite for the next_index function."""

    def test_next_index_empty_directory(self, temp_dir):
        """Test next_index when the section directory is empty."""
        section_dir = temp_dir / "blue"
        section_dir.mkdir()

        with patch('os.path.join', return_value=str(section_dir)):
            with patch('os.listdir', return_value=[]):
                result = next_index("blue")

        assert result == 1

    def test_next_index_with_existing_files(self, temp_dir):
        """Test next_index when section has existing numbered files."""
        section_dir = temp_dir / "blue"
        section_dir.mkdir()
        (section_dir / "blue-001.jpg").touch()
        (section_dir / "blue-002.jpg").touch()
        (section_dir / "blue-003.jpg").touch()

        with patch('os.path.join', return_value=str(section_dir)):
            with patch('os.listdir', return_value=["blue-001.jpg", "blue-002.jpg", "blue-003.jpg"]):
                result = next_index("blue")

        assert result == 4

    def test_next_index_non_sequential(self, temp_dir):
        """Test next_index with non-sequential numbering."""
        section_dir = temp_dir / "gradient"
        section_dir.mkdir()

        with patch('os.path.join', return_value=str(section_dir)):
            with patch('os.listdir', return_value=["gradient-001.jpg", "gradient-005.jpg", "gradient-010.jpg"]):
                result = next_index("gradient")

        # Should return max + 1 = 11
        assert result == 11

    def test_next_index_ignores_non_matching(self, temp_dir):
        """Test next_index ignores files that don't match the section pattern."""
        section_dir = temp_dir / "orange"
        section_dir.mkdir()

        files = [
            "orange-001.jpg",
            "orange-002.jpg",
            "other-file.jpg",
            "orange.jpg",
            "orange-abc.jpg",
            "README.md"
        ]

        with patch('os.path.join', return_value=str(section_dir)):
            with patch('os.listdir', return_value=files):
                result = next_index("orange")

        assert result == 3

    def test_next_index_creates_directory(self, temp_dir):
        """Test next_index creates section directory if it doesn't exist."""
        with patch('os.path.join', return_value=str(temp_dir / "purple")):
            with patch('os.makedirs') as mock_makedirs:
                with patch('os.listdir', return_value=[]):
                    result = next_index("purple")

                mock_makedirs.assert_called_once()
                assert result == 1

    def test_next_index_with_different_extensions(self, temp_dir):
        """Test next_index works with different file extensions."""
        section_dir = temp_dir / "red"
        section_dir.mkdir()

        files = [
            "red-001.jpg",
            "red-002.png",
            "red-003.webp"
        ]

        with patch('os.path.join', return_value=str(section_dir)):
            with patch('os.listdir', return_value=files):
                result = next_index("red")

        assert result == 4


class TestMain:
    """Test suite for the main function."""

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

    def test_main_no_files_found(self, capsys):
        """Test main when no image files are found."""
        with patch('sys.argv', ['add-images.py', 'blue', '/nonexistent/file.jpg']):
            with patch('add_images.collect', return_value=[]):
                result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "No images found" in captured.out

    def test_main_successful_conversion(self, temp_dir, capsys):
        """Test main with successful image conversion."""
        test_file = temp_dir / "test.png"
        test_file.touch()

        output_file = temp_dir / "assets" / "images" / "blue" / "blue-001.jpg"
        output_file.parent.mkdir(parents=True)

        with patch('sys.argv', ['add-images.py', 'blue', str(test_file)]):
            with patch('add_images.collect', return_value=[str(test_file)]):
                with patch('add_images.next_index', return_value=1):
                    with patch('os.path.join', return_value=str(output_file)):
                        with patch('subprocess.run') as mock_run:
                            # Mock successful sips conversion
                            mock_run.return_value = MagicMock(returncode=0)

                            with patch('os.path.exists', return_value=True):
                                with patch('os.path.getsize', return_value=50000):
                                    with patch('sys.executable', '/usr/bin/python3'):
                                        with patch('subprocess.run', side_effect=[
                                            MagicMock(returncode=0),  # sips call
                                            MagicMock(returncode=0)   # rebuild-index call
                                        ]) as mock_runs:
                                            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "added" in captured.out
        assert "Rebuilding index and gallery" in captured.out

    def test_main_sips_command_format(self, temp_dir):
        """Test that sips is called with correct arguments."""
        test_file = temp_dir / "test.png"
        test_file.touch()

        output_file = temp_dir / "blue-001.jpg"

        with patch('sys.argv', ['add-images.py', 'blue', str(test_file)]):
            with patch('add_images.collect', return_value=[str(test_file)]):
                with patch('add_images.next_index', return_value=1):
                    with patch('os.path.join', return_value=str(output_file)):
                        with patch('subprocess.run') as mock_run:
                            mock_run.return_value = MagicMock(returncode=0)

                            with patch('os.path.exists', return_value=True):
                                with patch('os.path.getsize', return_value=50000):
                                    with patch('sys.executable', '/usr/bin/python3'):
                                        with patch('subprocess.run', side_effect=[
                                            MagicMock(returncode=0),
                                            MagicMock(returncode=0)
                                        ]) as mock_runs:
                                            main()

                        # Check first call (sips)
                        sips_call = mock_runs.call_args_list[0]
                        sips_args = sips_call[0][0]

                        assert sips_args[0] == "sips"
                        assert "--resampleWidth" in sips_args
                        assert "1600" in sips_args
                        assert "-s" in sips_args
                        assert "format" in sips_args
                        assert "jpeg" in sips_args
                        assert "formatOptions" in sips_args
                        assert "70" in sips_args

    def test_main_failed_conversion(self, temp_dir, capsys):
        """Test main when sips conversion fails."""
        test_file = temp_dir / "test.png"
        test_file.touch()

        output_file = temp_dir / "blue-001.jpg"

        with patch('sys.argv', ['add-images.py', 'blue', str(test_file)]):
            with patch('add_images.collect', return_value=[str(test_file)]):
                with patch('add_images.next_index', return_value=1):
                    with patch('os.path.join', return_value=str(output_file)):
                        with patch('subprocess.run') as mock_run:
                            mock_run.return_value = MagicMock(returncode=1)

                            # Output file doesn't exist after failed conversion
                            with patch('os.path.exists', return_value=False):
                                result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "FAILED to convert" in captured.out

    def test_main_multiple_files(self, temp_dir, capsys):
        """Test main with multiple input files."""
        test_files = [
            temp_dir / "test1.png",
            temp_dir / "test2.jpg",
            temp_dir / "test3.webp"
        ]

        for f in test_files:
            f.touch()

        output_dir = temp_dir / "assets" / "images" / "gradient"
        output_dir.mkdir(parents=True)

        with patch('sys.argv', ['add-images.py', 'gradient'] + [str(f) for f in test_files]):
            with patch('add_images.collect', return_value=[str(f) for f in test_files]):
                with patch('add_images.next_index', return_value=1):
                    with patch('add_images.IMG', str(temp_dir / "assets" / "images")):
                        with patch('subprocess.run', return_value=MagicMock(returncode=0)):
                            with patch('os.path.exists', return_value=True):
                                with patch('os.path.getsize', return_value=50000):
                                    with patch('sys.executable', '/usr/bin/python3'):
                                        result = main()

        # Should process all files successfully
        captured = capsys.readouterr()
        assert "3 image(s) added" in captured.out

    def test_main_rebuild_index_called(self, temp_dir):
        """Test that rebuild-index.py is called after successful additions."""
        test_file = temp_dir / "test.png"
        test_file.touch()

        output_dir = temp_dir / "assets" / "images" / "blue"
        output_dir.mkdir(parents=True)
        output_file = output_dir / "blue-001.jpg"

        with patch('sys.argv', ['add-images.py', 'blue', str(test_file)]):
            with patch('add_images.collect', return_value=[str(test_file)]):
                with patch('add_images.next_index', return_value=1):
                    with patch('add_images.IMG', str(temp_dir / "assets" / "images")):
                        with patch('add_images.ROOT', str(temp_dir)):
                            with patch('os.path.exists', return_value=True):
                                with patch('os.path.getsize', return_value=50000):
                                    with patch('sys.executable', '/usr/bin/python3'):
                                        with patch('subprocess.run', side_effect=[
                                            MagicMock(returncode=0),  # sips
                                            MagicMock(returncode=0)   # rebuild-index
                                        ]) as mock_run:
                                            main()

                                    # Second call should be to rebuild-index.py
                                    rebuild_call = mock_run.call_args_list[1]
                                    assert "rebuild-index.py" in str(rebuild_call)

    def test_main_increments_index(self, temp_dir, capsys):
        """Test that index increments for each file."""
        test_files = [temp_dir / f"test{i}.jpg" for i in range(3)]
        for f in test_files:
            f.touch()

        output_dir = temp_dir / "assets" / "images" / "orange"
        output_dir.mkdir(parents=True)

        with patch('sys.argv', ['add-images.py', 'orange'] + [str(f) for f in test_files]):
            with patch('add_images.collect', return_value=[str(f) for f in test_files]):
                with patch('add_images.next_index', return_value=5):
                    with patch('add_images.IMG', str(temp_dir / "assets" / "images")):
                        with patch('subprocess.run', return_value=MagicMock(returncode=0)):
                            with patch('os.path.exists', return_value=True):
                                with patch('os.path.getsize', return_value=50000):
                                    with patch('sys.executable', '/usr/bin/python3'):
                                        main()

        # Check output for the sequential indices
        captured = capsys.readouterr()
        assert "orange-005.jpg" in captured.out
        assert "orange-006.jpg" in captured.out
        assert "orange-007.jpg" in captured.out
