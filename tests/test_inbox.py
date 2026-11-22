#!/usr/bin/env python3
"""Tests for scripts/inbox.py: review a drop folder, then add only what was reviewed."""
import importlib.util
import json
import os
import time
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inbox = _load("inbox", "inbox.py")
hires = inbox.hires
add_images = inbox.add_images


def _art(path, size=(2944, 1648), seed=0, old=True):
    """A picture with structure (so fingerprints differ between seeds)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", size, (4, 6, 220))
    d = ImageDraw.Draw(im)
    w, h = size
    for i in range(6):
        x = (seed * 97 + i * 211) % w
        y = (seed * 53 + i * 131) % h
        d.ellipse([x, y, x + w // 5, y + h // 4], fill=(255 - i * 30, 40 * i % 255, 120))
    im.save(path)
    if old:
        t = time.time() - 600
        os.utime(path, (t, t))
    return path


@pytest.fixture
def env(tmp_path, monkeypatch):
    box = tmp_path / "inbox"
    box.mkdir()
    drive = tmp_path / "drive"
    drive.mkdir()
    cdn = tmp_path / "cdn"
    (cdn / "images").mkdir(parents=True)
    meta_path = tmp_path / "image-meta.json"
    meta_path.write_text(json.dumps({"$meta": {"cdn": "x"}, "images": {}}), encoding="utf-8")
    monkeypatch.setattr(add_images, "META_PATH", str(meta_path))
    monkeypatch.setattr(add_images, "ROOT", str(tmp_path))
    monkeypatch.setattr(add_images, "find_drive_root", lambda: drive)
    ids = iter(f"ID{n}" for n in range(1, 500))
    monkeypatch.setattr(add_images, "ID_READER", lambda p: next(ids))
    monkeypatch.setattr(add_images, "ID_TIMEOUT", 0.01)
    monkeypatch.setattr(add_images, "rebuild_gallery", lambda: 0)
    return box, drive, cdn, meta_path


def _plan(box):
    return json.loads((box / "_review" / "inbox-plan.json").read_text(encoding="utf-8"))


def _meta(meta_path):
    return json.loads(meta_path.read_text(encoding="utf-8"))


def test_fingerprint_survives_resize_and_reencode(tmp_path):
    a = _art(tmp_path / "a.png")
    b = tmp_path / "b.webp"
    with Image.open(a) as im:
        im.resize((1456, 816)).save(b, quality=60)
    c = _art(tmp_path / "c.png", seed=5)
    fa, fb, fc = (hires.fingerprint(p) for p in (a, b, c))
    assert len(fa) == 64
    assert hires.fp_distance(fa, fb) <= 10
    assert hires.fp_distance(fa, fc) > 20


def test_review_skips_unstable_files(env):
    box, *_ = env
    _art(box / "new.png", old=False)
    _art(box / "old.png", seed=1)
    assert inbox.main(["review", "--inbox", str(box)]) == 0
    assert [p["file"] for p in _plan(box)] == ["old.png"]
    assert (box / "_review" / "review.html").is_file()


def test_review_flags_duplicate_against_catalogue_and_batch(env):
    box, drive, cdn, meta_path = env
    again = _art(box / "again.png", seed=2)              # same picture as blue-001
    known = cdn / "images" / "blue" / "blue-001.jpg"
    known.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(again) as im:
        im.resize((1600, 896)).save(known, quality=70)
    meta = _meta(meta_path)
    meta["images"]["blue"] = [{"f": "blue-001.jpg", "dom": "#0406DC", "tok": "x", "L": 0.07,
                               "fp": hires.fingerprint(known)}]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    first = _art(box / "orig.png", seed=3)
    with Image.open(first) as im:                       # a smaller re-save of orig.png
        im.resize((1456, 816)).save(box / "orig copy.webp", quality=70)
    t = time.time() - 600
    os.utime(box / "orig copy.webp", (t, t))
    inbox.main(["review", "--inbox", str(box)])
    plan = {p["file"]: p for p in _plan(box)}
    assert "duplicate" in plan["again.png"]["flags"] and plan["again.png"]["dup_of"] == "blue/blue-001.jpg"
    assert "duplicate" in plan["orig copy.webp"]["flags"] and plan["orig copy.webp"]["dup_of"] == "orig.png"
    assert plan["orig.png"]["flags"] == []


def test_review_flags_small(env):
    box, *_ = env
    _art(box / "small.webp", size=(1456, 816))
    inbox.main(["review", "--inbox", str(box)])
    assert _plan(box)[0]["flags"] == ["small"]


def test_review_section_from_subfolder(env):
    box, *_ = env
    _art(box / "red" / "x.png", seed=4)
    inbox.main(["review", "--inbox", str(box)])
    (p,) = _plan(box)
    assert p["file"] == "red/x.png" and p["section"] == "red" and not p["guessed"]


def test_apply_only_planned_and_unchanged(env, capsys):
    box, drive, cdn, meta_path = env
    keep = _art(box / "a.png", seed=1)
    changed = _art(box / "b.png", seed=2)
    inbox.main(["review", "--inbox", str(box)])
    _art(box / "late.png", seed=3)                       # added after the review
    t = time.time() - 300
    os.utime(changed, (t, t))                           # touched after the review
    assert inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"]) == 0
    out = capsys.readouterr().out
    assert not keep.exists()
    assert changed.exists() and (box / "late.png").exists()
    assert "late.png" in out and "b.png" in out
    assert len([e for rows in _meta(meta_path)["images"].values() for e in rows]) == 1


def test_apply_moves_original_and_never_upscales(env):
    box, drive, cdn, meta_path = env
    _art(box / "blue" / "small.png", size=(1456, 816), seed=1)
    _art(box / "blue" / "big.png", size=(2944, 1648), seed=6)
    inbox.main(["review", "--inbox", str(box)])
    plan = _plan(box)
    for p in plan:
        p["ok"] = True
    (box / "_review" / "inbox-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    assert inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"]) == 0
    rows = {e["hi"]["src"]: e for e in _meta(meta_path)["images"]["blue"]}
    widths = {}
    for src, e in rows.items():
        with Image.open(cdn / "images" / "blue" / e["f"]) as im:
            widths[src] = im.size[0]
        assert (drive / "blue" / (e["f"][:-4] + ".png")).is_file()
        assert e["fp"] and e["hi"]["id"].startswith("ID")
    assert widths == {"small.png": 1456, "big.png": 1600}
    assert not list((box / "blue").glob("*.png"))


def test_apply_interrupted_leaves_file_in_inbox(env, monkeypatch):
    box, drive, cdn, meta_path = env
    _art(box / "blue" / "one.png", seed=1)
    _art(box / "blue" / "two.png", seed=6)
    inbox.main(["review", "--inbox", str(box)])
    real = hires.place_original
    calls = []

    def flaky(*a, **k):
        calls.append(1)
        if len(calls) == 2:
            raise OSError("Drive went away")
        return real(*a, **k)
    monkeypatch.setattr(hires, "place_original", flaky)
    inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"])
    assert not (box / "blue" / "one.png").exists()
    assert (box / "blue" / "two.png").exists()
    assert sorted(p.name for p in (cdn / "images" / "blue").iterdir()) == ["blue-001.jpg"]
    assert [e["hi"]["src"] for e in _meta(meta_path)["images"]["blue"]] == ["one.png"]


def test_rerun_apply_is_noop(env):
    box, drive, cdn, meta_path = env
    _art(box / "blue" / "one.png", seed=1)
    inbox.main(["review", "--inbox", str(box)])
    inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"])
    before = _meta(meta_path)
    inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"])
    assert _meta(meta_path) == before


def test_backfill_fp(env):
    box, drive, cdn, meta_path = env
    known = _art(cdn / "images" / "blue" / "blue-001.jpg", size=(1600, 896), seed=2)
    meta = _meta(meta_path)
    meta["images"]["blue"] = [{"f": "blue-001.jpg", "dom": "#0406DC", "tok": "x", "L": 0.07}]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    assert inbox.main(["backfill-fp", "--cdn-dir", str(cdn)]) == 0
    assert _meta(meta_path)["images"]["blue"][0]["fp"] == hires.fingerprint(known)
