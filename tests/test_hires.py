#!/usr/bin/env python3
"""Tests for scripts/hires.py: finding, placing and identifying high-res originals."""
import importlib.util
import os
import time
from pathlib import Path

import pytest
from PIL import Image

HIRES_PATH = Path(__file__).resolve().parent.parent / "scripts" / "hires.py"


def load_hires():
    spec = importlib.util.spec_from_file_location("hires", HIRES_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hires = load_hires()
GALLERY_REL = Path("Library/CloudStorage/GoogleDrive-someone@azmx.sa/Shared drives/AZM X/Branding/Brand Images Gallery")


def _png(path, size=(20, 20), color=(0, 26, 255)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
    return path


class TestDriveRoot:
    def test_drive_root_env_wins(self, tmp_path):
        target = tmp_path / "anywhere"
        target.mkdir()
        (tmp_path / GALLERY_REL).mkdir(parents=True)
        assert hires.drive_root(env={"AZMX_HIRES_DIR": str(target)}, home=tmp_path) == target

    def test_drive_root_globs_azmx_account(self, tmp_path):
        (tmp_path / GALLERY_REL).mkdir(parents=True)
        (tmp_path / "Library/CloudStorage/GoogleDrive-other@gmail.com/Shared drives").mkdir(parents=True)
        assert hires.drive_root(env={}, home=tmp_path) == tmp_path / GALLERY_REL

    def test_drive_root_none_when_missing(self, tmp_path):
        assert hires.drive_root(env={}, home=tmp_path) is None


class TestReadDriveId:
    def test_read_drive_id_polls_until_value(self, tmp_path):
        answers = iter([None, None, "ID9"])
        assert hires.read_drive_id(tmp_path, timeout=5, poll=0.001, reader=lambda p: next(answers)) == "ID9"

    def test_read_drive_id_times_out(self, tmp_path):
        assert hires.read_drive_id(tmp_path, timeout=0.05, poll=0.01, reader=lambda p: None) is None


class TestFindAndPlace:
    def test_find_new_originals_sections_and_root(self, tmp_path):
        _png(tmp_path / "a.png")
        _png(tmp_path / "blue" / "صورة 1.PNG")
        _png(tmp_path / "blue" / "blue-001.png")
        (tmp_path / ".DS_Store").write_bytes(b"x")
        assert hires.find_new_originals(tmp_path) == [
            (tmp_path / "a.png", None), (tmp_path / "blue" / "صورة 1.PNG", "blue")]

    def test_is_catalogued_name(self):
        assert hires.is_catalogued_name("blue-114.png")
        assert not hires.is_catalogued_name("blue-114 copy.png")
        assert not hires.is_catalogued_name("teal-001.png")

    def test_place_original_moves_and_lowercases_ext(self, tmp_path):
        src = _png(tmp_path / "blue" / "صورة 1.PNG")
        out = hires.place_original(src, tmp_path, "blue", 114)
        assert out == tmp_path / "blue" / "blue-114.png" and out.is_file()
        assert not src.exists()

    def test_place_original_copies_from_outside_root(self, tmp_path):
        root = tmp_path / "drive"
        src = _png(tmp_path / "inbox" / "x.webp")
        out = hires.place_original(src, root, "red", 7)
        assert out == root / "red" / "red-007.webp" and out.is_file()
        assert src.exists()

    def test_place_original_refuses_overwrite(self, tmp_path):
        _png(tmp_path / "blue" / "blue-114.png")
        src = _png(tmp_path / "new.png")
        with pytest.raises(FileExistsError):
            hires.place_original(src, tmp_path, "blue", 114)


class TestGuessAndInfo:
    @pytest.mark.parametrize("dom,lum,section", [
        ("#0406DC", 0.07, "blue"), ("#F26D18", 0.09, "orange"), ("#EAEAED", 0.45, "white"),
        ("#3F007F", 0.03, "purple"), ("#049445", 0.15, "green"), ("#8F6106", 0.15, "yellow"),
        ("#AF021C", 0.07, "red"), ("#111113", 0.103, "white"), ("#000000", 0.014, "blue"),
        ("#701601", 0.07, "orange")])
    def test_guess_section(self, dom, lum, section):
        assert hires.guess_section(dom, lum) == section

    def test_original_info(self, tmp_path):
        p = _png(tmp_path / "صورة.PNG", size=(30, 12))
        info = hires.original_info(p)
        assert info == {"w": 30, "h": 12, "bytes": os.path.getsize(p), "ext": "png", "src": "صورة.PNG"}

    def test_original_info_large_image(self, tmp_path):
        p = _png(tmp_path / "big.png")
        Image.MAX_IMAGE_PIXELS = 100            # a 20x20 image would now trip Pillow's bomb check…
        try:
            mod = load_hires()                  # …unless the module raises the limit itself
            assert mod.original_info(p)["w"] == 20
            assert Image.MAX_IMAGE_PIXELS == 400_000_000
        finally:
            Image.MAX_IMAGE_PIXELS = 400_000_000
