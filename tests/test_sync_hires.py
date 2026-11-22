#!/usr/bin/env python3
"""Tests for scripts/sync-hires.py: link originals that reached Drive after their web copy."""
import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

SYNC_PATH = Path(__file__).resolve().parent.parent / "scripts" / "sync-hires.py"
spec = importlib.util.spec_from_file_location("sync_hires", SYNC_PATH)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    meta_path = tmp_path / "image-meta.json"
    meta = {"$meta": {"cdn": "x"}, "images": {"blue": [
        {"f": "blue-114.jpg", "dom": "#000000", "tok": "x", "L": 0.1, "hi": {"pending": True}}]}}
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    root = tmp_path / "drive"
    (root / "blue").mkdir(parents=True)
    rebuilt = []
    monkeypatch.setattr(sync, "META_PATH", str(meta_path))
    monkeypatch.setattr(sync, "find_drive_root", lambda: root)
    monkeypatch.setattr(sync, "ID_READER", lambda p: "IDX")
    monkeypatch.setattr(sync, "ID_TIMEOUT", 0.01)
    monkeypatch.setattr(sync, "rebuild_gallery", lambda: rebuilt.append(1) or 0)
    return meta_path, root, rebuilt


def _entry(meta_path):
    return json.loads(meta_path.read_text(encoding="utf-8"))["images"]["blue"][0]


def test_sync_links_named_original(setup, capsys):
    meta_path, root, rebuilt = setup
    Image.new("RGB", (40, 30)).save(root / "blue" / "blue-114.tif")
    assert sync.main([]) == 0
    hi = _entry(meta_path)["hi"]
    assert hi["id"] == "IDX" and hi["w"] == 40 and hi["ext"] == "tif" and "src" not in hi
    assert "pending" not in hi
    assert rebuilt and "1 linked, 0 still pending" in capsys.readouterr().out


def test_sync_skips_ambiguous(setup, capsys):
    meta_path, root, rebuilt = setup
    Image.new("RGB", (40, 30)).save(root / "blue" / "blue-114.tif")
    Image.new("RGB", (40, 30)).save(root / "blue" / "blue-114.png")
    assert sync.main([]) == 0
    assert _entry(meta_path)["hi"] == {"pending": True}
    out = capsys.readouterr().out
    assert "blue-114.tif" in out and "blue-114.png" in out and "0 linked, 1 still pending" in out
    assert not rebuilt
