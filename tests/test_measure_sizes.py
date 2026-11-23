"""scripts/measure-sizes.py reads an image's pixel size from the start of the JPEG."""
import importlib.util
import io
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("measure_sizes", ROOT / "scripts" / "measure-sizes.py")
measure_sizes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure_sizes)


@pytest.mark.parametrize("size", [(1600, 897), (896, 1344), (40, 40)])
def test_jpeg_size_reads_the_frame_header(size):
    Image = pytest.importorskip("PIL.Image")
    buf = io.BytesIO()
    Image.new("RGB", size, (0, 26, 255)).save(buf, "JPEG")
    assert measure_sizes.jpeg_size(buf.getvalue()[:65536]) == size


def test_jpeg_size_progressive():
    Image = pytest.importorskip("PIL.Image")
    buf = io.BytesIO()
    Image.new("RGB", (300, 200), (0, 26, 255)).save(buf, "JPEG", progressive=True)
    assert measure_sizes.jpeg_size(buf.getvalue()) == (300, 200)


def test_jpeg_size_not_a_jpeg():
    assert measure_sizes.jpeg_size(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64) is None
