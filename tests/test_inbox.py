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
    assert len(fa) == 64 + 1 + 96
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
                               "fp": hires.fingerprint(known),
                               "hi": {"id": "X", "w": 1, "h": 1, "bytes": 1, "ext": "png"}}]
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
    widths = {}
    for e in _meta(meta_path)["images"]["blue"]:          # plan order: blue/big.png, blue/small.png
        with Image.open(cdn / "images" / "blue" / e["f"]) as im:
            widths[e["f"]] = im.size[0]
        assert (drive / "blue" / (e["f"][:-4] + ".png")).is_file()
        assert e["fp"] and e["hi"]["id"].startswith("ID")
    assert widths == {"blue-001.jpg": 1600, "blue-002.jpg": 1456}
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
    assert [e["f"] for e in _meta(meta_path)["images"]["blue"]] == ["blue-001.jpg"]


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


def _gradient(path, top, bottom, size=(800, 450)):
    im = Image.new("RGB", size)
    d = ImageDraw.Draw(im)
    for y in range(size[1]):
        t = y / (size[1] - 1)
        d.line([(0, y), (size[0], y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    im.save(path)
    return path


def test_recolour_is_not_a_duplicate(tmp_path):
    """The Orange/Purple/… sets are recolours of blue images: same shapes, other colours."""
    blue = _art(tmp_path / "blue.png", seed=3)
    with Image.open(blue) as im:
        r, g, b = im.split()
        Image.merge("RGB", (b, g, r)).save(tmp_path / "recoloured.png")   # blue <-> red
    assert hires.fp_distance(hires.fingerprint(blue), hires.fingerprint(tmp_path / "recoloured.png")) > 20


def test_smooth_gradients_of_other_colours_differ(tmp_path):
    a = _gradient(tmp_path / "a.png", (2, 0, 40), (30, 100, 217))
    b = _gradient(tmp_path / "b.png", (0, 1, 4), (114, 177, 243))
    assert hires.fp_distance(hires.fingerprint(a), hires.fingerprint(b)) > 20


def test_same_gradient_reencoded_is_duplicate(tmp_path):
    a = _gradient(tmp_path / "a.png", (2, 0, 40), (30, 100, 217))
    with Image.open(a) as im:
        im.resize((400, 225)).save(tmp_path / "a.jpg", quality=60)
    assert hires.fp_distance(hires.fingerprint(a), hires.fingerprint(tmp_path / "a.jpg")) <= 10


def test_gradient_variant_is_not_a_duplicate(tmp_path):
    """Library gradients that differ by ~5-8 levels per channel are separate images."""
    a = _gradient(tmp_path / "a.png", (2, 0, 40), (30, 100, 217))
    b = _gradient(tmp_path / "b.png", (8, 8, 52), (36, 110, 228))
    assert hires.fp_distance(hires.fingerprint(a), hires.fingerprint(b)) > 20


# ---------------------------------------------------------------------------
# Final review fixes
# ---------------------------------------------------------------------------

def test_interrupted_drive_wait_leaves_no_orphan_and_next_run_works(env, monkeypatch):
    box, drive, cdn, meta_path = env
    _art(box / "blue" / "one.png", seed=1)
    inbox.main(["review", "--inbox", str(box)])

    def stop(_):
        raise KeyboardInterrupt
    monkeypatch.setattr(add_images, "ID_READER", stop)
    with pytest.raises(KeyboardInterrupt):
        inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"])
    assert (box / "blue" / "one.png").exists()
    assert not list((drive / "blue").glob("*")) if (drive / "blue").exists() else True
    assert not list((cdn / "images" / "blue").glob("*.jpg"))
    monkeypatch.setattr(add_images, "ID_READER", lambda p: "IDOK")
    assert inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"]) == 0
    assert [e["hi"]["id"] for e in _meta(meta_path)["images"]["blue"]] == ["IDOK"]


def test_number_skips_files_already_on_disk(env):
    box, drive, cdn, meta_path = env
    _art(drive / "blue" / "blue-001.png", seed=9)        # an orphan from some earlier failure
    _art(box / "blue" / "one.png", seed=1)
    inbox.main(["review", "--inbox", str(box)])
    assert inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"]) == 0
    assert [e["f"] for e in _meta(meta_path)["images"]["blue"]] == ["blue-002.jpg"]


def test_apply_refuses_inbox_inside_drive(env):
    box, drive, cdn, meta_path = env
    inner = drive / "_inbox"
    _art(inner / "blue" / "one.png", seed=1)
    inbox.main(["review", "--inbox", str(inner)])
    assert inbox.main(["apply", "--inbox", str(inner), "--cdn-dir", str(cdn), "--no-commit"]) == 1
    assert (inner / "blue" / "one.png").exists()


def test_apply_keeps_original_when_drive_gives_no_id(env, monkeypatch, capsys):
    box, drive, cdn, meta_path = env
    monkeypatch.setattr(add_images, "ID_READER", lambda p: None)
    _art(box / "blue" / "one.png", seed=1)
    inbox.main(["review", "--inbox", str(box)])
    assert inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"]) == 0
    assert (box / "blue" / "one.png").exists()
    assert _meta(meta_path)["images"]["blue"][0]["hi"] == {"pending": True}
    assert "kept" in capsys.readouterr().out
    # once Drive is back, sync-hires links it; the inbox copy is just a spare


def test_review_lists_unreadable_and_continues(env, capsys):
    box, *_ = env
    bad = box / "broken.png"
    bad.write_bytes(b"not an image")
    t = time.time() - 600
    os.utime(bad, (t, t))
    _art(box / "good.png", seed=1)
    assert inbox.main(["review", "--inbox", str(box)]) == 0
    plan = {p["file"]: p for p in _plan(box)}
    assert plan["broken.png"]["flags"] == ["unreadable"]
    assert plan["good.png"]["flags"] == []
    assert "unreadable" in capsys.readouterr().out


def test_hi_keeps_no_original_file_name(env):
    """Midjourney names carry the account and prompt; the public catalogue must not."""
    box, drive, cdn, meta_path = env
    _art(box / "blue" / "azmx_designteam_secret_prompt_123.png", seed=1)
    inbox.main(["review", "--inbox", str(box)])
    inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"])
    assert "designteam" not in meta_path.read_text(encoding="utf-8")
    assert set(_meta(meta_path)["images"]["blue"][0]["hi"]) == {"id", "w", "h", "bytes", "ext"}


# ---------------------------------------------------------------------------
# Originals of images already in the library (23 Nov)
# ---------------------------------------------------------------------------

def _catalogue_image(env, seed, hi=None, section="purple", name="purple-010.jpg"):
    """Put a 1600 px web copy of _art(seed) in the CDN and the catalogue; return the full-size source."""
    box, drive, cdn, meta_path = env
    src = _art(box.parent / f"src-{seed}.png", seed=seed)
    web = cdn / "images" / section / name
    web.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im.resize((1600, 896)).save(web, quality=70)
    meta = _meta(meta_path)
    entry = {"f": name, "dom": "#300A57", "tok": "x", "L": 0.03, "fp": hires.fingerprint(web)}
    if hi:
        entry["hi"] = hi
    meta["images"].setdefault(section, []).append(entry)
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return src


def test_review_marks_original_for_library_image_without_hires(env):
    box, *_ = env
    src = _catalogue_image(env, seed=11)
    os.replace(src, box / "full.png")
    inbox.main(["review", "--inbox", str(box)])
    (row,) = _plan(box)
    assert row["flags"] == ["original"] and row["original_for"] == "purple/purple-010.jpg"


def test_review_keeps_duplicate_when_library_image_has_hires(env):
    box, *_ = env
    src = _catalogue_image(env, seed=12, hi={"id": "X", "w": 1, "h": 1, "bytes": 1, "ext": "png"})
    os.replace(src, box / "again.png")
    inbox.main(["review", "--inbox", str(box)])
    assert _plan(box)[0]["flags"] == ["duplicate"]


def test_review_narrow_original_stays_duplicate(env):
    box, *_ = env
    src = _catalogue_image(env, seed=13)
    with Image.open(src) as im:
        im.resize((1456, 816)).save(box / "narrow.png")
    t = time.time() - 600
    os.utime(box / "narrow.png", (t, t))
    inbox.main(["review", "--inbox", str(box)])
    assert "duplicate" in _plan(box)[0]["flags"]


def test_apply_attaches_original_to_existing_entry(env):
    box, drive, cdn, meta_path = env
    src = _catalogue_image(env, seed=14)
    os.replace(src, box / "full.png")
    inbox.main(["review", "--inbox", str(box)])
    assert inbox.main(["apply", "--inbox", str(box), "--cdn-dir", str(cdn), "--no-commit"]) == 0
    rows = _meta(meta_path)["images"]["purple"]
    assert len(rows) == 1 and rows[0]["hi"]["id"].startswith("ID") and rows[0]["hi"]["w"] == 2944
    assert (drive / "purple" / "purple-010.png").is_file()
    assert not (box / "full.png").exists()
    assert sorted(p.name for p in (cdn / "images" / "purple").iterdir()) == ["purple-010.jpg"]
