#!/usr/bin/env python3
"""Tests for scripts/move-image.py: move a catalogued image to another colour section."""
import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("move_image", SCRIPTS / "move-image.py")
mv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mv)


@pytest.fixture
def lib(tmp_path, monkeypatch):
    cdn, drive = tmp_path / "cdn", tmp_path / "drive"
    for sec in ("blue", "purple"):
        (cdn / "images" / sec).mkdir(parents=True)
        (drive / sec).mkdir(parents=True)
    Image.new("RGB", (16, 9), (80, 0, 160)).save(cdn / "images" / "blue" / "blue-127.jpg")
    Image.new("RGB", (32, 18), (80, 0, 160)).save(drive / "blue" / "blue-127.png")
    Image.new("RGB", (16, 9)).save(cdn / "images" / "purple" / "purple-025.jpg")
    meta = {"$meta": {"cdn": "x"}, "images": {
        "blue": [{"f": "blue-126.jpg", "dom": "#000000", "tok": "x", "L": 0.1},
                 {"f": "blue-127.jpg", "dom": "#5000A0", "tok": "x", "L": 0.1,
                  "hi": {"id": "ID7", "w": 32, "h": 18, "bytes": 1, "ext": "png"}}],
        "purple": [{"f": "purple-025.jpg", "dom": "#5000A0", "tok": "x", "L": 0.1}]}}
    tags = {"blue-126.jpg": ["a", "b", "c"], "blue-127.jpg": ["energy", "focus", "vitality"],
            "purple-025.jpg": ["d", "e", "f"]}
    (tmp_path / "image-meta.json").write_text(json.dumps(meta))
    (tmp_path / "image-tags.json").write_text(json.dumps(tags))
    monkeypatch.setattr(mv.add_images, "META_PATH", str(tmp_path / "image-meta.json"))
    monkeypatch.setattr(mv, "TAGS_PATH", str(tmp_path / "image-tags.json"))
    monkeypatch.setattr(mv.add_images, "find_drive_root", lambda: drive)
    monkeypatch.setattr(mv, "rebuild_gallery", lambda: 0)
    return tmp_path, cdn, drive


def test_move_renames_everywhere_and_keeps_drive_id(lib):
    tmp, cdn, drive = lib
    assert mv.main(["--cdn-dir", str(cdn), "blue-127", "purple"]) == 0
    assert not (cdn / "images" / "blue" / "blue-127.jpg").exists()
    assert (cdn / "images" / "purple" / "purple-026.jpg").is_file()
    assert not (drive / "blue" / "blue-127.png").exists()
    assert (drive / "purple" / "purple-026.png").is_file()
    meta = json.loads((tmp / "image-meta.json").read_text())
    assert [e["f"] for e in meta["images"]["blue"]] == ["blue-126.jpg"]
    moved = meta["images"]["purple"][-1]
    assert moved["f"] == "purple-026.jpg" and moved["hi"]["id"] == "ID7"
    tags = json.loads((tmp / "image-tags.json").read_text())
    assert "blue-127.jpg" not in tags and tags["purple-026.jpg"] == ["energy", "focus", "vitality"]


def test_move_unknown_image_changes_nothing(lib, capsys):
    tmp, cdn, drive = lib
    before = (tmp / "image-meta.json").read_text()
    assert mv.main(["--cdn-dir", str(cdn), "blue-999", "purple"]) == 1
    assert (tmp / "image-meta.json").read_text() == before
    assert "blue-999" in capsys.readouterr().out
